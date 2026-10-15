"""Rodada 02 — Etapa 2: download das fontes externas (precisa de rede).

Uso (na raiz do repositório):
    python scripts/rodada02_coleta.py                         # todas as fontes
    python scripts/rodada02_coleta.py --fontes ons,siga,ipca  # só as fontes indicadas
    python scripts/rodada02_coleta.py --forcar                # baixa de novo mesmo que o arquivo já exista

Fontes (identificador → URL) estão na lista FONTES abaixo. Há dois modos:
- "arquivo": baixa o arquivo inteiro (em streaming, direto para o disco) e registra;
- "teste": só testa o acesso (GET simples); o corpo da resposta é descartado.

Regras de armazenamento (Rodada 02, Seção 2, regra 1):
- O download é feito com User-Agent de navegador (o CloudFront do SEEG devolve 403 sem isso),
  timeout generoso e em streaming, calculando SHA-256 e tamanho durante a escrita.
- Bruto com MAIS DE 20 MB (20.000.000 bytes) → dados/externos/brutos/<fonte>/<arquivo>.
  Essa pasta está no .gitignore: o bruto NÃO vai para o git (o GitHub recusa > 100 MB; o SEEG tem 185 MB).
- Bruto com até 20 MB → dados/externos/<fonte>/<arquivo> (vai para o git).
- Em qualquer caso, dados/externos/<fonte>/DOWNLOAD.txt registra URL, data e hora UTC do acesso,
  tamanho, SHA-256 e caminho do arquivo. O DOWNLOAD.txt VAI para o git mesmo quando o bruto não vai:
  é o que permite conferir que o bruto baixado de novo é o mesmo (pelo SHA-256).
- dados/externos/rodada02_acesso_fontes.csv (vai para o git) tem UMA linha por fonte
  (fonte, url, data_acesso_utc, acessivel, status_http, erro, arquivo, bytes, sha256); cada execução
  acrescenta a linha da fonte ou substitui a linha anterior da mesma fonte. Fontes não processadas
  nesta execução mantêm a linha que já tinham.

Comportamento:
- Erro numa fonte não interrompe o script: o erro é registrado no CSV e o script segue para a próxima.
  Em caso de erro, o arquivo e o DOWNLOAD.txt que já existiam ficam intactos.
- Se o arquivo já existir (em qualquer das duas pastas) e --forcar não for dado, ele NÃO é baixado de novo:
  o SHA-256 e o tamanho são recalculados a partir do arquivo local, e o acesso à URL é apenas conferido
  com um HEAD (sem baixar o corpo).
- Com --forcar, o arquivo é baixado para um temporário em dados/externos/brutos/<fonte>/ e só substitui
  o anterior se o download terminar sem erro e o conteúdo tiver o formato esperado; o SHA-256 anterior
  fica registrado no DOWNLOAD.txt quando muda.
- Conferência mínima de conteúdo (para não guardar uma página de erro como se fosse dado):
  parquet começa e termina com "PAR1"; xlsx começa com "PK"; json precisa ser JSON válido;
  csv/json não podem ser uma página HTML.

Só biblioteca padrão (urllib): o proxy do ambiente é lido das variáveis de ambiente (HTTPS_PROXY etc.).
NENHUM número é tratado aqui: o tratamento fica em scripts/rodada02.py e em src/mip/externos/.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

RAIZ = Path(__file__).resolve().parents[1]

# Limite para versionar o bruto: acima disso o arquivo vai para dados/externos/brutos/ (fora do git).
LIMITE_GIT_BYTES = 20_000_000  # "mais de 20 MB" (Rodada 02, Seção 2, regra 1)

# User-Agent de navegador: o SEEG (CloudFront) devolve 403 sem isso (Rodada 02, Seção 2, regra 4).
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
CABECALHOS = {
    "User-Agent": USER_AGENT,
    "Accept": "*/*",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}
TIMEOUT_PADRAO = 180.0  # segundos sem resposta (por operação de rede, não total)
BLOCO = 1024 * 1024  # 1 MiB por leitura no streaming
LIMITE_TESTE = 64 * 1024  # no modo "teste", lê no máximo isto e descarta

COLUNAS_CSV = [
    "fonte", "url", "data_acesso_utc", "acessivel", "status_http", "erro", "arquivo", "bytes", "sha256",
]


@dataclass(frozen=True)
class Fonte:
    """Uma fonte da Rodada 02.

    ident: identificador curto (nome da pasta em dados/externos/).
    url: endereço exato acessado.
    modo: "arquivo" (baixa e guarda) ou "teste" (só testa o acesso).
    arquivo: nome do arquivo salvo; vazio → nome final da URL.
    formato: formato esperado do conteúdo ("parquet", "csv", "json", "xlsx"), para a conferência mínima.
    descricao: instituição/conjunto e seção das instruções.
    """

    ident: str
    url: str
    modo: str = "arquivo"
    arquivo: str = ""
    formato: str = ""
    descricao: str = ""


FONTES: list[Fonte] = [
    Fonte("ons",
          "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/GERACAO_USINA-2_2019.parquet",
          formato="parquet", descricao="ONS — geração por usina em base horária, 2019 (Seção 5.1)"),
    Fonte("siga",
          "https://dadosabertos.aneel.gov.br/dataset/6d90b77c-c5f5-4d81-bdec-7bc619494bb9/resource/"
          "11ec447d-698d-4ab8-977f-b424d5deee6a/download/siga-empreendimentos-geracao.csv",
          formato="csv", descricao="ANEEL — SIGA, empreendimentos de geração (Seção 5.2)"),
    Fonte("leiloes",
          "https://dadosabertos.aneel.gov.br/dataset/593537c6-9e0e-4ed9-817a-2c5d5de05147/resource/"
          "a1328fc1-f06b-437d-8893-57ac2c8103df/download/resultado-leiloes-geracao.csv",
          formato="csv", descricao="ANEEL — resultado dos leilões de geração (Seção 5.4)"),
    Fonte("ipca",
          "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all",
          arquivo="ipca_1737.json", formato="json",
          descricao="IBGE SIDRA — tabela 1737, variável 2266, IPCA número-índice (Seção 5.4)"),
    Fonte("seeg",
          "https://seeg.eco.br/wp-content/uploads/2025/12/Dados-nacionais-13.0.xlsx",
          formato="xlsx", descricao="SEEG 13.0 — dados nacionais (Seção 5.7)"),
    Fonte("cempre",
          "https://apisidra.ibge.gov.br/values/t/6450/n1/all/n3/43/v/707,662/p/2019/"
          "c12762/117297,117298,117299,117300,117301,117302,117303,117304,117305,117306",
          arquivo="cempre_6450.json", formato="json",
          descricao="IBGE SIDRA — tabela 6450, CEMPRE 2019, Brasil e RS (Seção 5.8)"),
    Fonte("comex", "https://api-comexstat.mdic.gov.br/general", modo="teste",
          descricao="MDIC — API do Comex Stat (Seção 5.9; só teste de acesso)"),
    Fonte("epe", "https://www.epe.gov.br/", modo="teste", descricao="EPE (só teste de acesso)"),
    Fonte("sulgas", "https://www.sulgas.rs.gov.br/", modo="teste", descricao="Sulgás (só teste de acesso)"),
    Fonte("aneel_rap", "https://www.gov.br/aneel/pt-br", modo="teste",
          descricao="ANEEL — portal gov.br, RAP (Seção 5.5; só teste de acesso)"),
    Fonte("anp", "https://www.gov.br/anp/pt-br", modo="teste", descricao="ANP — portal gov.br (só teste de acesso)"),
]


# ---------------------------------------------------------------------------------------------
# utilitários
# ---------------------------------------------------------------------------------------------
def agora_utc() -> str:
    """Data e hora UTC atuais no formato ISO 8601 com 'Z' (ex.: 2026-10-15T10:30:12Z)."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mtime_utc(caminho: Path) -> str:
    """Data de modificação do arquivo, em UTC, no mesmo formato de agora_utc()."""
    t = dt.datetime.fromtimestamp(caminho.stat().st_mtime, tz=dt.timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def nome_arquivo(fonte: Fonte) -> str:
    """Nome do arquivo salvo: o indicado na fonte ou, se vazio, o nome final da URL (se tiver extensão)."""
    if fonte.arquivo:
        return fonte.arquivo
    nome = PurePosixPath(urllib.parse.unquote(urllib.parse.urlparse(fonte.url).path)).name
    if not nome or "." not in nome:
        raise ValueError(f"fonte {fonte.ident!r}: a URL não termina em nome com extensão; indique 'arquivo'")
    return nome


def relativo(caminho: Path, raiz: Path) -> str:
    """Caminho relativo à raiz do repositório, com '/' (para registros portáveis)."""
    try:
        return caminho.resolve().relative_to(raiz.resolve()).as_posix()
    except ValueError:
        return caminho.as_posix()


def sha256_arquivo(caminho: Path) -> tuple[int, str]:
    """Tamanho em bytes e SHA-256 (hex) de um arquivo, lido em blocos."""
    h = hashlib.sha256()
    n = 0
    with open(caminho, "rb") as f:
        while True:
            bloco = f.read(BLOCO)
            if not bloco:
                break
            h.update(bloco)
            n += len(bloco)
    return n, h.hexdigest()


def descrever_erro(e: BaseException) -> tuple[str, str]:
    """(status HTTP, mensagem) de uma exceção de rede. Status vazio quando não houve resposta do servidor
    (ex.: 403 do proxy do ambiente, que aparece como 'Tunnel connection failed: 403 Forbidden')."""
    if isinstance(e, urllib.error.HTTPError):
        return str(e.code), f"HTTPError {e.code}: {e.reason}"
    return "", f"{type(e).__name__}: {e}"


def requisicao(url: str, metodo: str = "GET") -> urllib.request.Request:
    """Request com os cabeçalhos de navegador."""
    return urllib.request.Request(url, headers=dict(CABECALHOS), method=metodo)


def remover_pasta_se_vazia(pasta: Path) -> None:
    """Remove a pasta se ela existir e estiver vazia (limpeza de pastas criadas para temporários)."""
    try:
        if pasta.is_dir() and not any(pasta.iterdir()):
            pasta.rmdir()
    except OSError:
        pass


# ---------------------------------------------------------------------------------------------
# rede
# ---------------------------------------------------------------------------------------------
def baixar(url: str, destino: Path, timeout: float = TIMEOUT_PADRAO) -> tuple[str, int, str]:
    """Baixa `url` em streaming para `destino` e devolve (status HTTP, bytes, SHA-256).

    A pasta de `destino` só é criada depois que o servidor responde. Levanta a exceção de rede original
    em caso de falha (quem chama registra). Confere o Content-Length, quando o servidor o informa.
    """
    with urllib.request.urlopen(requisicao(url), timeout=timeout) as r:
        status = str(r.status)
        esperado = r.headers.get("Content-Length")
        destino.parent.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha256()
        n = 0
        with open(destino, "wb") as f:
            while True:
                bloco = r.read(BLOCO)
                if not bloco:
                    break
                f.write(bloco)
                h.update(bloco)
                n += len(bloco)
    if esperado is not None and esperado.strip().isdigit() and int(esperado) != n:
        raise OSError(f"download incompleto: {n} de {int(esperado)} bytes")
    return status, n, h.hexdigest()


def conferir_acesso(url: str, timeout: float = TIMEOUT_PADRAO) -> tuple[bool, str, str]:
    """Confere o acesso sem baixar o arquivo: HEAD; se o servidor recusar HEAD (403/405/501),
    tenta GET lendo só 1 byte. Devolve (acessível, status HTTP, erro)."""
    try:
        with urllib.request.urlopen(requisicao(url, "HEAD"), timeout=timeout) as r:
            return True, str(r.status), ""
    except urllib.error.HTTPError as e:
        if e.code not in (403, 405, 501):
            status, msg = descrever_erro(e)
            return False, status, msg
    except Exception as e:  # noqa: BLE001 - registrar qualquer falha de rede
        status, msg = descrever_erro(e)
        return False, status, msg
    return testar_get(url, timeout, limite=1)


def testar_get(url: str, timeout: float = TIMEOUT_PADRAO, limite: int = LIMITE_TESTE) -> tuple[bool, str, str]:
    """GET simples; lê no máximo `limite` bytes e descarta. Devolve (acessível, status HTTP, erro)."""
    try:
        with urllib.request.urlopen(requisicao(url), timeout=timeout) as r:
            r.read(limite)
            return True, str(r.status), ""
    except Exception as e:  # noqa: BLE001 - registrar qualquer falha de rede
        status, msg = descrever_erro(e)
        return False, status, msg


# ---------------------------------------------------------------------------------------------
# conferência mínima de conteúdo
# ---------------------------------------------------------------------------------------------
def conferir_conteudo(caminho: Path, formato: str) -> str:
    """Confere se o arquivo tem cara do formato esperado. Devolve "" se estiver ok ou a descrição do problema.

    Não valida o conteúdo dos dados (isso é do tratamento); só evita guardar uma página de erro como dado.
    """
    tamanho = caminho.stat().st_size
    if tamanho == 0:
        return "arquivo vazio"
    with open(caminho, "rb") as f:
        inicio = f.read(2048)
        f.seek(max(0, tamanho - 4))
        fim = f.read(4)
    cabeca = inicio.lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    parece_html = cabeca.startswith((b"<!doctype html", b"<html", b"<?xml", b"<head", b"<body"))
    if formato == "parquet":
        if not (inicio[:4] == b"PAR1" and fim == b"PAR1"):
            return "não parece parquet (assinatura PAR1 ausente)" + (" — veio HTML" if parece_html else "")
    elif formato == "xlsx":
        if inicio[:2] != b"PK":
            return "não parece xlsx (assinatura ZIP 'PK' ausente)" + (" — veio HTML" if parece_html else "")
    elif formato in ("csv", "json"):
        if parece_html:
            return f"não parece {formato}: o servidor devolveu uma página HTML"
        if formato == "json":
            for enc in ("utf-8-sig", "latin-1"):
                try:
                    with open(caminho, encoding=enc) as f:
                        json.load(f)
                    break
                except UnicodeDecodeError:
                    continue
                except json.JSONDecodeError as e:
                    return f"JSON inválido: {e}"
    return ""


# ---------------------------------------------------------------------------------------------
# registros: DOWNLOAD.txt e CSV de acesso
# ---------------------------------------------------------------------------------------------
def pasta_versionada(raiz: Path, fonte: Fonte) -> Path:
    """dados/externos/<fonte>/ (vai para o git)."""
    return raiz / "dados" / "externos" / fonte.ident


def pasta_brutos(raiz: Path, fonte: Fonte) -> Path:
    """dados/externos/brutos/<fonte>/ (fora do git)."""
    return raiz / "dados" / "externos" / "brutos" / fonte.ident


def destino_por_tamanho(raiz: Path, fonte: Fonte, nbytes: int) -> Path:
    """Caminho final do arquivo pela regra dos 20 MB."""
    pasta = pasta_brutos(raiz, fonte) if nbytes > LIMITE_GIT_BYTES else pasta_versionada(raiz, fonte)
    return pasta / nome_arquivo(fonte)


def localizar_existente(raiz: Path, fonte: Fonte) -> list[Path]:
    """Cópias já existentes do arquivo da fonte (brutos primeiro, depois a pasta versionada)."""
    nome = nome_arquivo(fonte)
    candidatos = [pasta_brutos(raiz, fonte) / nome, pasta_versionada(raiz, fonte) / nome]
    return [c for c in candidatos if c.is_file()]


def ler_download_txt(caminho: Path) -> dict[str, str]:
    """Lê um DOWNLOAD.txt no formato 'chave: valor' (linhas com '#' são comentário)."""
    dados: dict[str, str] = {}
    if not caminho.is_file():
        return dados
    for linha in caminho.read_text(encoding="utf-8", errors="replace").splitlines():
        if not linha.strip() or linha.lstrip().startswith("#") or ":" not in linha:
            continue
        chave, valor = linha.split(":", 1)
        dados[chave.strip()] = valor.strip()
    return dados


def escrever_download_txt(caminho: Path, campos: dict[str, str]) -> None:
    """Escreve o DOWNLOAD.txt (sobrescreve o registro anterior da mesma fonte, que é refeito a cada coleta)."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    linhas = [
        "# Registro de download — gerado por scripts/rodada02_coleta.py (não editar à mão).",
        "# Este arquivo vai para o git mesmo quando o bruto (> 20 MB, em dados/externos/brutos/) não vai.",
        "# Para conferir um bruto baixado de novo, compare o SHA-256 abaixo.",
    ]
    linhas += [f"{k}: {v}" for k, v in campos.items()]
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def atualizar_csv_acesso(caminho: Path, registros: list[dict[str, str]], ordem: list[str]) -> None:
    """Acrescenta ou substitui a linha de cada fonte em `registros` no CSV de acesso.

    Linhas de fontes que não estão em `registros` ficam como estavam. Ordem: a de `ordem`
    (lista de identificadores), com fontes desconhecidas no fim, na ordem em que já estavam.
    """
    existentes: dict[str, dict[str, str]] = {}
    if caminho.is_file():
        with open(caminho, encoding="utf-8-sig", newline="") as f:
            for linha in csv.DictReader(f):
                if linha.get("fonte"):
                    existentes[linha["fonte"]] = {c: (linha.get(c) or "") for c in COLUNAS_CSV}
    for reg in registros:
        existentes[reg["fonte"]] = {c: str(reg.get(c, "")) for c in COLUNAS_CSV}
    chaves = [f for f in ordem if f in existentes] + [f for f in existentes if f not in ordem]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS_CSV)
        w.writeheader()
        for k in chaves:
            w.writerow(existentes[k])


# ---------------------------------------------------------------------------------------------
# processamento de uma fonte
# ---------------------------------------------------------------------------------------------
def processar_fonte(fonte: Fonte, raiz: Path, forcar: bool = False,
                    timeout: float = TIMEOUT_PADRAO) -> tuple[dict[str, str], str]:
    """Baixa (ou testa) uma fonte e devolve (linha do CSV de acesso, situação em texto curto).

    Nunca levanta exceção de rede: qualquer falha vira linha com acessivel = "não" e o erro.
    """
    reg = {c: "" for c in COLUNAS_CSV}
    reg.update(fonte=fonte.ident, url=fonte.url, data_acesso_utc=agora_utc())

    # --- modo "teste": só GET simples, corpo descartado ---
    if fonte.modo == "teste":
        ok, status, erro = testar_get(fonte.url, timeout)
        reg.update(acessivel="sim" if ok else "não", status_http=status, erro=erro)
        return reg, "acessível (só teste)" if ok else "falhou"

    txt = pasta_versionada(raiz, fonte) / "DOWNLOAD.txt"
    anterior = ler_download_txt(txt)
    existentes = localizar_existente(raiz, fonte)

    # --- arquivo já existe e não pediram --forcar: não baixa; recalcula hash e confere acesso (HEAD) ---
    if existentes and not forcar:
        local = existentes[0]
        nbytes, sha = sha256_arquivo(local)
        ok, status, erro = conferir_acesso(fonte.url, timeout)
        problema = conferir_conteudo(local, fonte.formato) if fonte.formato else ""
        avisos = []
        if len(existentes) > 1:
            avisos.append("há cópias em brutos/ e na pasta versionada; usada " + relativo(local, raiz))
        if problema:
            avisos.append(f"arquivo local: {problema}")
        reg.update(acessivel="sim" if ok else "não", status_http=status,
                   erro="; ".join([e for e in [erro] + avisos if e]),
                   arquivo=relativo(local, raiz), bytes=str(nbytes), sha256=sha)
        if anterior.get("sha256") == sha and anterior.get("data_acesso_utc"):
            data, origem = anterior["data_acesso_utc"], anterior.get("origem_data_acesso", "")
        else:
            data = mtime_utc(local)
            origem = ("data de modificação do arquivo local (o arquivo já existia e não foi baixado de novo; "
                      "a hora exata do download original não foi registrada)")
            if anterior.get("sha256") and anterior.get("sha256") != sha:
                avisos.append("SHA-256 diferente do registrado no DOWNLOAD.txt anterior")
                reg["erro"] = "; ".join([e for e in [erro] + avisos if e])
        escrever_download_txt(txt, montar_campos(fonte, raiz, local, nbytes, sha, data, origem,
                                                 anterior_sha=_sha_anterior(anterior, sha)))
        return reg, "já existia (não baixado de novo; hash recalculado)" + (f" — AVISO: {'; '.join(avisos)}"
                                                                            if avisos else "")

    # --- download (primeira vez ou --forcar) ---
    nome = nome_arquivo(fonte)
    tmp = pasta_brutos(raiz, fonte) / f".{nome}.parcial"
    try:
        status, nbytes, sha = baixar(fonte.url, tmp, timeout)
    except Exception as e:  # noqa: BLE001 - registrar e seguir para a próxima fonte
        status, msg = descrever_erro(e)
        tmp.unlink(missing_ok=True)
        remover_pasta_se_vazia(tmp.parent)
        reg.update(acessivel="não", status_http=status, erro=msg)
        return reg, "falhou"

    problema = conferir_conteudo(tmp, fonte.formato) if fonte.formato else ""
    if problema:
        tmp.unlink(missing_ok=True)
        remover_pasta_se_vazia(tmp.parent)
        reg.update(acessivel="não", status_http=status, erro=f"conteúdo inesperado: {problema}")
        return reg, "falhou (conteúdo inesperado; nada salvo)"

    destino = destino_por_tamanho(raiz, fonte, nbytes)
    destino.parent.mkdir(parents=True, exist_ok=True)
    os.replace(tmp, destino)
    remover_pasta_se_vazia(tmp.parent)
    avisos = []
    for velho in existentes:  # cópia antiga na outra pasta (o tamanho cruzou os 20 MB): remove
        if velho.resolve() != destino.resolve() and velho.is_file():
            velho.unlink()
            avisos.append(f"cópia antiga removida: {relativo(velho, raiz)}")
            remover_pasta_se_vazia(velho.parent)
    reg.update(acessivel="sim", status_http=status, arquivo=relativo(destino, raiz),
               bytes=str(nbytes), sha256=sha)
    escrever_download_txt(txt, montar_campos(fonte, raiz, destino, nbytes, sha, reg["data_acesso_utc"],
                                             "download feito nesta execução",
                                             anterior_sha=_sha_anterior(anterior, sha)))
    situacao = "baixado" + (" (--forcar)" if forcar and existentes else "")
    return reg, situacao + (f" — {'; '.join(avisos)}" if avisos else "")


def _sha_anterior(anterior: dict[str, str], sha: str) -> str:
    """SHA-256 do registro anterior, se for diferente do atual (senão, vazio)."""
    velho = anterior.get("sha256", "")
    return velho if velho and velho != sha else ""


def montar_campos(fonte: Fonte, raiz: Path, arquivo: Path, nbytes: int, sha: str,
                  data: str, origem: str, anterior_sha: str = "") -> dict[str, str]:
    """Campos do DOWNLOAD.txt, na ordem em que são gravados."""
    fora_git = nbytes > LIMITE_GIT_BYTES
    campos = {
        "fonte": fonte.ident,
        "descricao": fonte.descricao,
        "url": fonte.url,
        "data_acesso_utc": data,
        "origem_data_acesso": origem,
        "bytes": str(nbytes),
        "sha256": sha,
        "arquivo": relativo(arquivo, raiz),
        "versionado_no_git": (f"não (mais de {LIMITE_GIT_BYTES / 1e6:.0f} MB; dados/externos/brutos/ "
                              "está no .gitignore)" if fora_git
                              else f"sim (até {LIMITE_GIT_BYTES / 1e6:.0f} MB)"),
        "user_agent": USER_AGENT,
    }
    if anterior_sha:
        campos["sha256_anterior"] = anterior_sha
    return campos


# ---------------------------------------------------------------------------------------------
# linha de comando
# ---------------------------------------------------------------------------------------------
def escolher_fontes(texto: str | None) -> list[Fonte]:
    """Fontes pedidas em --fontes (separadas por vírgula); None ou vazio → todas."""
    if not texto:
        return list(FONTES)
    por_id = {f.ident: f for f in FONTES}
    pedidas = [t.strip().lower() for t in texto.split(",") if t.strip()]
    desconhecidas = [p for p in pedidas if p not in por_id]
    if desconhecidas:
        raise ValueError(f"fonte(s) desconhecida(s): {', '.join(desconhecidas)}. "
                         f"Disponíveis: {', '.join(por_id)}")
    return [por_id[p] for p in dict.fromkeys(pedidas)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Rodada 02 — download das fontes externas.")
    ap.add_argument("--fontes", help="identificadores separados por vírgula (padrão: todas). "
                                     f"Disponíveis: {','.join(f.ident for f in FONTES)}")
    ap.add_argument("--forcar", action="store_true", help="baixa de novo mesmo que o arquivo já exista")
    ap.add_argument("--timeout", type=float, default=TIMEOUT_PADRAO,
                    help=f"timeout de rede em segundos (padrão {TIMEOUT_PADRAO:.0f})")
    ap.add_argument("--raiz", type=Path, default=RAIZ, help=argparse.SUPPRESS)  # para testes
    args = ap.parse_args(argv)
    try:
        fontes = escolher_fontes(args.fontes)
    except ValueError as e:
        ap.error(str(e))
    raiz: Path = args.raiz
    csv_acesso = raiz / "dados" / "externos" / "rodada02_acesso_fontes.csv"

    registros = []
    for fonte in fontes:
        print(f"[{fonte.ident}] {fonte.url}", flush=True)
        try:
            reg, situacao = processar_fonte(fonte, raiz, forcar=args.forcar, timeout=args.timeout)
        except Exception as e:  # noqa: BLE001 - falha inesperada (ex.: disco): registra e segue
            reg = {c: "" for c in COLUNAS_CSV}
            reg.update(fonte=fonte.ident, url=fonte.url, data_acesso_utc=agora_utc(), acessivel="não",
                       erro=f"falha local: {type(e).__name__}: {e}")
            situacao = "falhou (erro local)"
        registros.append(reg)
        # grava a cada fonte: se o script for interrompido, o que já foi feito fica registrado
        atualizar_csv_acesso(csv_acesso, [reg], [f.ident for f in FONTES])
        extra = f" {reg['bytes']} bytes sha256={reg['sha256'][:12]}…" if reg["sha256"] else ""
        print(f"    {situacao}; acessível={reg['acessivel']} status={reg['status_http'] or '-'}"
              f"{extra}{' erro=' + reg['erro'] if reg['erro'] else ''}", flush=True)

    ok = sum(r["acessivel"] == "sim" for r in registros)
    print(f"\n{ok} de {len(registros)} fonte(s) acessível(is). Registro: {relativo(csv_acesso, raiz)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
