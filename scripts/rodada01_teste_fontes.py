"""Rodada 01 — Etapa 6: teste de acesso a fontes de dados externas.

Uso (na raiz do repositório):
    python scripts/rodada01_teste_fontes.py

Para cada fonte faz uma requisição leve. Se a fonte responder, salva uma amostra pequena (catálogo)
em dados/externos/rodada01_teste/<fonte>/. O resultado vai para
dados/externos/rodada01_teste/acesso_fontes_rodada01.csv. NENHUM dado baixado aqui é usado em cálculo.
Depende da rede: por isso fica separado de scripts/rodada01.py.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "dados" / "externos" / "rodada01_teste"
LIMITE_BYTES = 1_000_000  # só amostras pequenas

# (identificador, fonte, URL testada, extensão da amostra, uso previsto na Rodada 2)
FONTES = [
    ("aneel", "ANEEL – Dados Abertos (SIGA)",
     "https://dadosabertos.aneel.gov.br/api/3/action/package_search?q=siga&rows=1", "json",
     "usinas: potência, fonte, UF"),
    ("ons", "ONS – Dados Abertos",
     "https://dados.ons.org.br/api/3/action/package_list", "json", "geração por usina/fonte e UF"),
    ("ccee", "CCEE – Dados Abertos",
     "https://dadosabertos.ccee.org.br/api/3/action/package_list", "json",
     "geração, consumo por ramo, preços"),
    ("epe", "EPE (Anuário Estatístico de Energia Elétrica; BEN)",
     "https://www.epe.gov.br/", "html", "geração e consumo por fonte e UF, 2019"),
    ("ibge_sidra", "IBGE – API SIDRA",
     "https://apisidra.ibge.gov.br/values/t/6579/n1/all/p/2019", "json",
     "pessoal ocupado e salários por CNAE e UF"),
    ("seeg", "SEEG", "https://seeg.eco.br/", "html", "emissões por UF e fonte"),
    ("basedosdados", "Base dos Dados (RAIS)", "https://basedosdados.org/", "html",
     "emprego por CNAE subclasse e UF (só verificar se responde; sem credenciais)"),
    ("pypi", "PyPI", "https://pypi.org/simple/openpyxl/", None, "instalação de pacotes"),
]


def testar(url: str, timeout: float = 25.0) -> tuple[bool, str, str, bytes]:
    """Devolve (acessível, status HTTP, mensagem de erro, conteúdo truncado)."""
    req = urllib.request.Request(url, headers={"User-Agent": "MIP-desagregacao/rodada01 (teste de acesso)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            corpo = r.read(LIMITE_BYTES + 1)
            return True, str(r.status), "", corpo
    except urllib.error.HTTPError as e:
        return False, str(e.code), f"HTTPError: {e.reason}", b""
    except Exception as e:  # noqa: BLE001 - registrar qualquer falha de rede
        return False, "", f"{type(e).__name__}: {e}", b""


def main() -> int:
    PASTA.mkdir(parents=True, exist_ok=True)
    registros = []
    for ident, nome, url, ext, uso in FONTES:
        quando = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ok, status, erro, corpo = testar(url)
        arquivo, nbytes, sha = "", "", ""
        if ok and ext and len(corpo) <= LIMITE_BYTES:
            destino = PASTA / ident  # uma pasta nova por fonte
            destino.mkdir(parents=True, exist_ok=True)
            caminho = destino / f"amostra.{ext}"
            caminho.write_bytes(corpo)
            arquivo = caminho.relative_to(RAIZ).as_posix()
            nbytes = str(len(corpo))
            sha = hashlib.sha256(corpo).hexdigest()
        registros.append(
            {
                "fonte": nome,
                "url_testada": url,
                "data_acesso_utc": quando,
                "acessivel": "sim" if ok else "não",
                "status_http": status,
                "erro": erro,
                "arquivo_salvo": arquivo,
                "bytes": nbytes,
                "sha256": sha,
                "uso_previsto": uso,
            }
        )
        print(f"{nome:55s} {'OK ' if ok else 'NÃO'} {status:4s} {erro[:90]}")
    with open(PASTA / "acesso_fontes_rodada01.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(registros[0]))
        w.writeheader()
        w.writerows(registros)
    return 0


if __name__ == "__main__":
    sys.exit(main())
