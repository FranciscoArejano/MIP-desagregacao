"""Cadastro de empreendimentos de geração da ANEEL (SIGA) — Seção 5.2 das instruções da Rodada 02.

Fonte: ANEEL, Dados Abertos, SIGA (Sistema de Informações de Geração da ANEEL), arquivo
`siga-empreendimentos-geracao.csv` (UTF-8, separador ';'):
https://dadosabertos.aneel.gov.br/dataset/6d90b77c-c5f5-4d81-bdec-7bc619494bb9/resource/11ec447d-698d-4ab8-977f-b424d5deee6a/download/siga-empreendimentos-geracao.csv

Uso no projeto: classificar as usinas nos subsetores de geração do S38 (S38_HID ... S38_NUC)
pelo campo `DscFonteCombustivel` (e por `NomFonteCombustivel` / `NomEmpreendimento` quando
preciso) e casar o cadastro com a geração por usina do ONS (Seção 5.1) pelo núcleo numérico
do CEG (6 dígitos): no SIGA é `IdeNucleoCEG`; no ONS sai da coluna `ceg`
(ex.: 'UTE.GN.RS.028038-0.01' → '028038').

ATENÇÃO: este leitor AINDA NÃO FOI VALIDADO COM O ARQUIVO REAL. O domínio dadosabertos.aneel.gov.br
estava bloqueado no ambiente em que o módulo foi escrito; o código segue o formato documentado
nas instruções e foi testado só com dados sintéticos (tests/test_externos_siga.py). Hipóteses
sobre o arquivo real:
- cabeçalho na primeira linha; colunas `IdeNucleoCEG` (núcleo do CEG, às vezes sem zeros à
  esquerda), `DscFonteCombustivel`, `NomFonteCombustivel`, `NomEmpreendimento` e, opcionalmente,
  `CodCEG` (CEG completo) e `SigUFPrincipal`. Variações de grafia, acento, maiúsculas e espaços
  nos nomes das colunas são aceitas (veja `ALIASES_COLUNAS`);
- encoding UTF-8 (com ou sem BOM); Windows-1252/Latin-1 também são aceitos;
- separador ';' (',', tabulação e '|' são detectados se aparecerem no cabeçalho);
- colunas numéricas (`Mda*`, `NumCoord*`) com decimal vírgula; se alguma célula tiver vírgula,
  o ponto só é aceito como separador de milhar ('1.500,25'); '-', 'X', '...' viram ausente.
  Coluna que não converte inteira fica como texto (essas colunas não são usadas na classificação).

Regras de classificação (Seção 5.2), aplicadas a `DscFonteCombustivel` sem acento/maiúsculas:
  Carvão mineral → S38_CAR; Gás natural → S38_GN; Petróleo → S38_PET;
  Outros Fósseis → pelo nome do combustível (`NomFonteCombustivel`) e, se não decidir, pelo
    nome do empreendimento: gás de alto-forno, de coqueria, de aciaria ou siderúrgico → S38_CAR;
    gás de refinaria ou derivados de petróleo → S38_PET; caso contrário fica pendente (None);
  Agroindustriais, Floresta, Resíduos sólidos urbanos, Resíduos animais,
    Biocombustíveis líquidos → S38_BIO;
  Potencial hidráulico → S38_HID; Cinética do vento → S38_EOL; Radiação solar → S38_SOL;
  Urânio (nuclear) → S38_NUC.
Se `DscFonteCombustivel` estiver vazio ou não for reconhecido, há uma regra de reserva
(desligável) por palavras-chave de `NomFonteCombustivel` — "se precisar", como dizem as
instruções; a coluna `regra` deixa explícito quando ela foi usada.
"""
from __future__ import annotations

import io
import math
import numbers
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------------
# Códigos dos subsetores de geração (Seção 3 das instruções da Rodada 02)
# --------------------------------------------------------------------------------------------
HID, EOL, SOL, BIO, CAR, GN, PET, NUC = (
    "S38_HID", "S38_EOL", "S38_SOL", "S38_BIO", "S38_CAR", "S38_GN", "S38_PET", "S38_NUC",
)
SUBSETORES_GERACAO = (HID, EOL, SOL, BIO, CAR, GN, PET, NUC)

# --------------------------------------------------------------------------------------------
# Nomes de colunas: nome canônico (o documentado) → variações aceitas.
# A comparação é feita sem acento, sem maiúsculas e só com letras e dígitos
# (' Nom Empreendimento ' ≡ 'nomempreendimento').
# --------------------------------------------------------------------------------------------
ALIASES_COLUNAS: dict[str, tuple[str, ...]] = {
    "IdeNucleoCEG": ("IdeNucleoCEG", "NucleoCEG", "IdNucleoCEG", "IdeNucleo", "NumNucleoCEG"),
    "CodCEG": ("CodCEG", "CEG", "CodigoCEG"),
    "DscFonteCombustivel": ("DscFonteCombustivel", "DescFonteCombustivel", "DscFonte", "FonteCombustivel"),
    "NomFonteCombustivel": ("NomFonteCombustivel", "NomeFonteCombustivel", "NomCombustivel", "Combustivel"),
    "NomEmpreendimento": (
        "NomEmpreendimento", "NomeEmpreendimento", "Empreendimento", "NomUsina", "NomeUsina", "Usina",
        "NomEmpreendimentoUsina",
    ),
    "SigUFPrincipal": ("SigUFPrincipal", "SigUF", "UFPrincipal", "UF", "SiglaUF"),
}

# Colunas numéricas (prefixo do nome normalizado): potências/garantia física e coordenadas.
_PREFIXOS_NUMERICOS = ("mda", "numcoord")

# --------------------------------------------------------------------------------------------
# Regras de classificação (Seção 5.2). Padrões aplicados ao texto normalizado
# (minúsculas, sem acento, pontuação → espaço). Ordem importa: vence o primeiro que casar.
# --------------------------------------------------------------------------------------------
_OUTROS_FOSSEIS = "outros_fosseis"  # marcador interno: decide pelo nome

REGRAS_DSC_FONTE: tuple[tuple[str, str], ...] = (
    (r"\boutros? fosseis?\b", _OUTROS_FOSSEIS),
    (r"\bcarvao mineral\b", CAR),
    (r"\bgas natural\b", GN),
    (r"\bpetroleo\b", PET),
    (r"\bagroindustria", BIO),
    (r"\bflorest", BIO),
    (r"\bresiduos? solidos? urbanos?\b", BIO),
    (r"\bresiduos? animais?\b", BIO),
    (r"\bbiocombustive", BIO),
    (r"\bpotencial hidraulico\b", HID),
    (r"\bcinetica do vento\b", EOL),
    (r"\bradiacao solar\b", SOL),
    (r"\buranio\b", NUC),
    (r"\bnuclear\b", NUC),
    # variações de grafia da mesma categoria
    (r"\bhidraulic", HID),
    (r"\beolic", EOL),
    (r"\bfotovoltaic", SOL),
)

# "Outros Fósseis": gás de alto-forno / coqueria / aciaria / siderúrgico → CAR;
# gás de refinaria / derivados de petróleo → PET.
REGRAS_OUTROS_FOSSEIS: tuple[tuple[str, str], ...] = (
    (r"\balto ?forno\b", CAR),
    (r"\bcoqueria\b", CAR),
    (r"\bgas de coque\b", CAR),
    (r"\baciaria\b", CAR),
    (r"\bsiderurg", CAR),
    (r"\brefinaria\b", PET),
    (r"\bderivad", PET),
    (r"\bpetroleo\b", PET),
    (r"\bdiesel\b", PET),
    (r"\boleo combustivel\b", PET),
)

# Reserva por `NomFonteCombustivel` quando `DscFonteCombustivel` está vazio ou não é reconhecido.
# Biomassa vem primeiro: "Gás de Alto Forno - Biomassa" e "Carvão - RU" (resíduos urbanos) são BIO.
REGRAS_NOM_FONTE_RESERVA: tuple[tuple[str, str], ...] = (
    (r"\bbiomassa\b", BIO),
    (r"\bbagaco\b", BIO),
    (r"\blicor negro\b", BIO),
    (r"\blenha\b", BIO),
    (r"\bbiogas\b", BIO),
    (r"\bcarvao vegetal\b", BIO),
    (r"\bresiduos? florest", BIO),
    (r"\bcasca\b", BIO),
    (r"\bcapim\b", BIO),
    (r"\betanol\b", BIO),
    (r"\boleos? vegeta", BIO),
    (r"\b(?:ru|rsu)\b", BIO),
    (r"\balto ?forno\b", CAR),
    (r"\bcoqueria\b", CAR),
    (r"\baciaria\b", CAR),
    (r"\bsiderurg", CAR),
    (r"\bcarvao\b", CAR),
    (r"\bgas natural\b", GN),
    (r"\brefinaria\b", PET),
    (r"\bdiesel\b", PET),
    (r"\boleo combustivel\b", PET),
    (r"\bpetroleo\b", PET),
    (r"\bderivad", PET),
    (r"\bhidraulic", HID),
    (r"\buranio\b", NUC),
    (r"\bnuclear\b", NUC),
    (r"\bvento\b", EOL),
    (r"\beolic", EOL),
    (r"\bsolar\b", SOL),
    (r"\bfotovoltaic", SOL),
)

# CEG: <tipo>.<combustível>.<UF>.<núcleo de 6 dígitos>-<dígito>.<versão>, ex.: UTE.GN.RS.028038-0.01
_RE_CEG_COMPLETO = re.compile(r"^[A-Z]{2,4}\.[A-Z0-9]{1,4}\.[A-Z]{2}\.(\d{6})-\d(?:\.\d{1,2})?$")
_RE_CEG_NUCLEO = re.compile(r"^(\d{6})-\d(?:\.\d{1,2})?$")  # só '028038-0' ou '028038-0.01'
# '28038', '028038', '28038.0' (float lido como texto) ou '28038,00' (decimal vírgula). Só 1 ou 2 zeros
# depois do separador: com 3 dígitos ('123.000') seria ambíguo com separador de milhar.
_RE_SO_DIGITOS = re.compile(r"^(\d{1,6})(?:[.,]0{1,2})?$")
# '28.038' ou '128.038': número formatado com separador de milhar pt-BR (núcleo é inteiro, então
# 3 dígitos depois do ponto só podem ser milhar).
_RE_MILHAR = re.compile(r"^(\d{1,3})\.(\d{3})$")
_RE_TRACOS = re.compile(r"[\u2010-\u2015\u2212]")  # hífens/travessões Unicode → '-'
_RE_SEPARA_CEGS = re.compile(r"[,;|/]+")
_VAZIOS = {"", "-", "--", "nan", "none", "null", "na", "n/a"}
# Marcadores de valor ausente/sigiloso em colunas numéricas.
_MARCADORES_AUSENTE = _VAZIOS | {"x", "...", "\u2026", "*"}


# --------------------------------------------------------------------------------------------
# Normalização de texto e de nomes de colunas
# --------------------------------------------------------------------------------------------
def _vazio(valor) -> bool:
    """True para None, NaN/NA e strings vazias."""
    if valor is None:
        return True
    try:
        if pd.isna(valor):
            return True
    except (TypeError, ValueError):
        return False
    return isinstance(valor, str) and valor.strip() == ""


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def normalizar_texto(valor) -> str:
    """Texto para comparação: minúsculas, sem acento, pontuação → espaço, espaços colapsados."""
    if _vazio(valor):
        return ""
    t = _sem_acento(str(valor)).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return t.strip()


def _chave_coluna(nome) -> str:
    """Nome de coluna para comparação: só letras e dígitos, minúsculas, sem acento."""
    return re.sub(r"[^a-z0-9]", "", _sem_acento(str(nome)).lower())


def _limpar_nome_coluna(nome) -> str:
    return str(nome).replace("\ufeff", "").strip().strip('"').strip("'").strip()


def _texto_ou_none(valor) -> str | None:
    if _vazio(valor):
        return None
    return re.sub(r"\s+", " ", str(valor)).strip()


def _localizar_coluna(df: pd.DataFrame, nomes: tuple[str, ...]) -> str | None:
    """Primeira coluna de `df` cujo nome normalizado coincide com algum de `nomes`."""
    por_chave: dict[str, str] = {}
    for c in df.columns:
        por_chave.setdefault(_chave_coluna(c), c)
    for nome in nomes:
        achada = por_chave.get(_chave_coluna(nome))
        if achada is not None:
            return achada
    return None


def _erro_colunas(fonte: str, faltando: list[str], df: pd.DataFrame) -> ValueError:
    return ValueError(
        f"{fonte}: coluna(s) obrigatória(s) ausente(s): {', '.join(faltando)}. "
        f"Colunas disponíveis: {[str(c) for c in df.columns]}"
    )


def _colunas_siga(df: pd.DataFrame) -> dict[str, str | None]:
    """Mapeia os nomes canônicos do SIGA às colunas presentes em `df` (None se ausente)."""
    return {canon: _localizar_coluna(df, aliases) for canon, aliases in ALIASES_COLUNAS.items()}


# --------------------------------------------------------------------------------------------
# 1) Núcleo do CEG
# --------------------------------------------------------------------------------------------
def _nucleo_de_inteiro(v: int) -> str | None:
    return str(v).zfill(6) if 1 <= v <= 999_999 else None


def nucleo_ceg(ceg) -> str | None:
    """Núcleo numérico de 6 dígitos do CEG, como texto com zeros à esquerda.

    Aceita:
    - o CEG completo, como vem no ONS: 'UTE.GN.RS.028038-0.01' → '028038'
      (maiúsculas/minúsculas e espaços são ignorados);
    - só o núcleo com dígito verificador: '028038-0' ou '028038-0.01' → '028038';
    - o `IdeNucleoCEG` do SIGA como número ou texto, com ou sem zeros à esquerda:
      28038, '28038', '028038', 28038.0, '28038.0', '28038,00', '28.038' (milhar pt-BR) → '028038'.
    Vários CEGs na mesma célula (separados por ',', ';', '|' ou '/') só são aceitos se todos
    tiverem o mesmo núcleo. Devolve None para vazio, '-', NaN, zero, número com mais de
    6 dígitos ou qualquer formato não reconhecido.
    """
    if isinstance(ceg, (bool, np.bool_)) or _vazio(ceg):
        return None
    if isinstance(ceg, numbers.Integral):
        return _nucleo_de_inteiro(int(ceg))
    if isinstance(ceg, numbers.Real):
        v = float(ceg)
        if math.isfinite(v) and v.is_integer():
            return _nucleo_de_inteiro(int(v))
        return None
    if not isinstance(ceg, str):
        return None

    texto = _RE_TRACOS.sub("-", ceg.strip())
    if texto.lower() in _VAZIOS:
        return None
    # número inteiro escrito como texto (antes de separar por ',': '28038,0' é decimal vírgula)
    compacto = re.sub(r"\s+", "", texto)
    m = _RE_SO_DIGITOS.match(compacto)
    if m:
        return _nucleo_de_inteiro(int(m.group(1)))
    m = _RE_MILHAR.match(compacto)
    if m:
        return _nucleo_de_inteiro(int(m.group(1) + m.group(2)))
    nucleos: set[str] = set()
    for pedaco in _RE_SEPARA_CEGS.split(texto):
        pedaco = re.sub(r"\s+", "", pedaco).upper()
        if pedaco.lower() in _VAZIOS:
            continue
        m = _RE_SO_DIGITOS.match(pedaco)
        if m:
            n = _nucleo_de_inteiro(int(m.group(1)))
            if n is None:
                return None
            nucleos.add(n)
            continue
        m = _RE_CEG_COMPLETO.match(pedaco) or _RE_CEG_NUCLEO.match(pedaco)
        if not m:
            return None  # formato inválido
        nucleos.add(m.group(1))
    return nucleos.pop() if len(nucleos) == 1 else None


def _nucleos_da_tabela(df: pd.DataFrame, col_nucleo: str | None, col_ceg: str | None) -> pd.Series:
    """Núcleo por linha: do `IdeNucleoCEG`; onde faltar, do `CodCEG` (se existir)."""
    vazio = [None] * len(df)
    a = [nucleo_ceg(v) for v in df[col_nucleo].tolist()] if col_nucleo else vazio
    b = [nucleo_ceg(v) for v in df[col_ceg].tolist()] if col_ceg else vazio
    return pd.Series([x if x is not None else y for x, y in zip(a, b)], index=df.index, dtype=object)


# --------------------------------------------------------------------------------------------
# 2) Leitura do CSV
# --------------------------------------------------------------------------------------------
def _decodificar(dados: bytes) -> tuple[str, str]:
    """Decodifica o arquivo: BOM → utf-8-sig; senão utf-8, cp1252 e, por fim, latin-1."""
    if dados.startswith(b"\xef\xbb\xbf"):
        return dados.decode("utf-8-sig"), "utf-8-sig"
    for enc in ("utf-8", "cp1252"):
        try:
            return dados.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return dados.decode("latin-1"), "latin-1"


def _detectar_separador(texto: str) -> str:
    """Separador mais frequente na linha de cabeçalho (padrão ';')."""
    cabecalho = next((linha for linha in texto.splitlines() if linha.strip()), "")
    contagens = {sep: cabecalho.count(sep) for sep in (";", ",", "\t", "|")}
    melhor = max(contagens, key=lambda s: (contagens[s], s == ";"))
    return melhor if contagens[melhor] > 0 else ";"


_RE_MILHAR_PONTO = re.compile(r"^[+-]?\d{1,3}(?:\.\d{3})+$")


def _para_numero(serie: pd.Series) -> pd.Series | None:
    """Converte texto numérico com decimal vírgula ou ponto; None se alguma célula não converter.

    Marcadores de ausente/sigiloso ('-', 'X', '...', '…', '*') viram NaN. Se a coluna tiver
    alguma vírgula, ela é o separador decimal e o ponto só é aceito como separador de milhar
    ('1.500,25', '1.500'); uma célula como '1500.25' nessa coluna é ambígua e deixa a coluna
    como texto (em vez de virar 150025 sem aviso).
    """
    def limpar(v):
        if _vazio(v):
            return None
        t = str(v).strip().replace(" ", "")
        return None if t.lower() in _MARCADORES_AUSENTE else t

    s = serie.astype(object).map(limpar)
    preenchidos = s.notna()
    if not preenchidos.any():
        return None
    if s[preenchidos].map(lambda v: "," in v).any():
        def de_virgula(v):
            if not isinstance(v, str):
                return v
            if "," in v:
                return v.replace(".", "").replace(",", ".")
            if "." in v:
                return v.replace(".", "") if _RE_MILHAR_PONTO.match(v) else "ambiguo"
            return v
        s = s.map(de_virgula)
    num = pd.to_numeric(s, errors="coerce")
    if num[preenchidos].isna().any():
        return None
    return num.astype(float)


def ler_siga(caminho: str | Path) -> pd.DataFrame:
    """Lê o CSV do SIGA e acrescenta a coluna `nucleo_ceg` (texto de 6 dígitos ou None).

    - detecta o encoding (utf-8-sig, utf-8, cp1252, latin-1) e o separador (';' por padrão);
    - limpa os nomes das colunas (BOM, aspas, espaços) e renomeia as variações reconhecidas
      para os nomes documentados (`IdeNucleoCEG`, `DscFonteCombustivel`, `NomFonteCombustivel`,
      `NomEmpreendimento`, `CodCEG`, `SigUFPrincipal`); as demais colunas ficam como vieram;
    - lê tudo como texto (preserva zeros à esquerda), tira espaços das células e converte as
      colunas `Mda*`/`NumCoord*` para número, aceitando decimal vírgula;
    - `nucleo_ceg` vem de `IdeNucleoCEG` (zfill(6)); onde faltar, do `CodCEG`.
    Obrigatórias: `DscFonteCombustivel` e `IdeNucleoCEG` ou `CodCEG` (senão, ValueError com
    a lista de colunas disponíveis). O encoding e o separador usados ficam em `df.attrs`.
    """
    caminho = Path(caminho)
    texto, encoding = _decodificar(caminho.read_bytes())
    sep = _detectar_separador(texto)
    df = pd.read_csv(
        io.StringIO(texto), sep=sep, dtype=str, keep_default_na=False, na_values=[""],
        skipinitialspace=True,
    )
    df.columns = [_limpar_nome_coluna(c) for c in df.columns]

    # variações de nome → nome documentado
    renomear = {}
    for canon, achada in _colunas_siga(df).items():
        if achada is not None and achada != canon and canon not in df.columns:
            renomear[achada] = canon
    df = df.rename(columns=renomear)

    faltando = []
    if "DscFonteCombustivel" not in df.columns:
        faltando.append("DscFonteCombustivel")
    if "IdeNucleoCEG" not in df.columns and "CodCEG" not in df.columns:
        faltando.append("IdeNucleoCEG (ou CodCEG)")
    if faltando:
        raise _erro_colunas(f"SIGA ({caminho.name})", faltando, df)

    # células de texto: sem espaços nas pontas; vazio → ausente
    for c in df.columns:
        df[c] = df[c].astype(object).map(_texto_ou_none)
    for c in df.columns:
        if _chave_coluna(c).startswith(_PREFIXOS_NUMERICOS):
            num = _para_numero(df[c])
            if num is not None:
                df[c] = num

    df["nucleo_ceg"] = _nucleos_da_tabela(
        df, "IdeNucleoCEG" if "IdeNucleoCEG" in df.columns else None,
        "CodCEG" if "CodCEG" in df.columns else None,
    )
    df.attrs["encoding"] = encoding
    df.attrs["separador"] = sep
    df.attrs["arquivo"] = str(caminho)
    return df


# --------------------------------------------------------------------------------------------
# 3) Classificação por fonte
# --------------------------------------------------------------------------------------------
def _procurar(regras: tuple[tuple[str, str], ...], texto_norm: str) -> tuple[str, str] | None:
    """(destino, palavra-chave encontrada) da primeira regra que casar, ou None."""
    for padrao, destino in regras:
        m = re.search(padrao, texto_norm)
        if m:
            return destino, m.group(0)
    return None


def classificar_fonte(
    dsc_fonte, nom_fonte=None, nome_empreendimento=None, usar_reserva_nom_fonte: bool = True
) -> tuple[str | None, str]:
    """Aplica as regras da Seção 5.2 a uma usina; devolve (subsetor ou None, regra aplicada).

    `regra` diz qual campo e qual palavra-chave decidiram (ou por que ficou pendente).
    """
    dsc, nom, nome = _texto_ou_none(dsc_fonte), _texto_ou_none(nom_fonte), _texto_ou_none(nome_empreendimento)
    achado = _procurar(REGRAS_DSC_FONTE, normalizar_texto(dsc))

    if achado is not None and achado[0] != _OUTROS_FOSSEIS:
        sub, palavra = achado
        return sub, f"DscFonteCombustivel='{dsc}' (palavra-chave '{palavra}') -> {sub}"

    if achado is not None:  # Outros Fósseis: decide pelo nome do combustível e, depois, da usina
        for campo, valor in (("NomFonteCombustivel", nom), ("NomEmpreendimento", nome)):
            r = _procurar(REGRAS_OUTROS_FOSSEIS, normalizar_texto(valor))
            if r is not None:
                sub, palavra = r
                tipo = "gás siderúrgico" if sub == CAR else "gás de refinaria/derivados de petróleo"
                return sub, (
                    f"DscFonteCombustivel='{dsc}' -> decidido por {campo}='{valor}' "
                    f"(palavra-chave '{palavra}', {tipo}) -> {sub}"
                )
        return None, (
            f"DscFonteCombustivel='{dsc}': nenhuma palavra-chave de gás siderúrgico (alto-forno, "
            f"coqueria, aciaria, siderúrgico) ou de petróleo (refinaria, derivados, diesel, óleo "
            f"combustível) em NomFonteCombustivel='{nom}' nem em NomEmpreendimento='{nome}' "
            f"-> pendente (classificar manualmente)"
        )

    motivo = "vazio" if dsc is None else f"'{dsc}' não mapeado nas regras da Seção 5.2"
    if usar_reserva_nom_fonte:
        r = _procurar(REGRAS_NOM_FONTE_RESERVA, normalizar_texto(nom))
        if r is not None:
            sub, palavra = r
            return sub, (
                f"DscFonteCombustivel {motivo}; reserva por NomFonteCombustivel='{nom}' "
                f"(palavra-chave '{palavra}') -> {sub}"
            )
    return None, (
        f"DscFonteCombustivel {motivo}; NomFonteCombustivel='{nom}' sem palavra-chave reconhecida "
        f"-> sem subsetor"
    )


def classificar_siga(df: pd.DataFrame, usar_reserva_nom_fonte: bool = True) -> pd.DataFrame:
    """Classifica cada linha do SIGA num subsetor de geração (Seção 5.2).

    Entrada: o DataFrame de `ler_siga` ou um DataFrame bruto com as colunas do SIGA (nomes
    comparados sem acento/maiúsculas). Obrigatórias: `DscFonteCombustivel` e o núcleo do CEG
    (`nucleo_ceg`, `IdeNucleoCEG` ou `CodCEG`). `NomFonteCombustivel`, `NomEmpreendimento` e
    `SigUFPrincipal` são opcionais (ausentes → None).

    Saída (mesmo índice da entrada): `nucleo_ceg`, `nome`, `fonte_dsc`, `fonte_nom`,
    `subsetor` (código S38_* ou None), `regra` (texto com o campo e a palavra-chave que
    decidiram) e `uf`.
    """
    cols = _colunas_siga(df)
    col_nucleo_pronto = _localizar_coluna(df, ("nucleo_ceg",))
    faltando = []
    if cols["DscFonteCombustivel"] is None:
        faltando.append("DscFonteCombustivel")
    if col_nucleo_pronto is None and cols["IdeNucleoCEG"] is None and cols["CodCEG"] is None:
        faltando.append("nucleo_ceg (ou IdeNucleoCEG ou CodCEG)")
    if faltando:
        raise _erro_colunas("SIGA", faltando, df)

    def coluna(canon: str) -> list:
        c = cols[canon]
        return [_texto_ou_none(v) for v in df[c].tolist()] if c else [None] * len(df)

    if col_nucleo_pronto is not None:
        nucleos = pd.Series([nucleo_ceg(v) for v in df[col_nucleo_pronto].tolist()], index=df.index, dtype=object)
        # completa o que faltar a partir das colunas originais
        if nucleos.isna().any() and (cols["IdeNucleoCEG"] or cols["CodCEG"]):
            outros = _nucleos_da_tabela(df, cols["IdeNucleoCEG"], cols["CodCEG"])
            nucleos = pd.Series(
                [a if a is not None else b for a, b in zip(nucleos.tolist(), outros.tolist())],
                index=df.index, dtype=object,
            )
    else:
        nucleos = _nucleos_da_tabela(df, cols["IdeNucleoCEG"], cols["CodCEG"])

    dsc, nom, nome, uf = (coluna(c) for c in ("DscFonteCombustivel", "NomFonteCombustivel", "NomEmpreendimento", "SigUFPrincipal"))
    resultados = [classificar_fonte(d, n, e, usar_reserva_nom_fonte) for d, n, e in zip(dsc, nom, nome)]

    def obj(valores) -> pd.Series:
        return pd.Series(list(valores), index=df.index, dtype=object)

    return pd.DataFrame(
        {
            "nucleo_ceg": obj(nucleos.tolist()),
            "nome": obj(nome),
            "fonte_dsc": obj(dsc),
            "fonte_nom": obj(nom),
            "subsetor": obj(r[0] for r in resultados),
            "regra": obj(r[1] for r in resultados),
            "uf": obj(uf),
        },
        index=df.index,
    )


# --------------------------------------------------------------------------------------------
# 4) Casamento com as usinas do ONS
# --------------------------------------------------------------------------------------------
def _tabela_por_nucleo(siga: pd.DataFrame) -> dict[str, tuple[str | None, str, str | None]]:
    """núcleo → (subsetor, regra, nome no SIGA), resolvendo núcleos repetidos no SIGA.

    Repetidos com o mesmo subsetor → um só registro (a regra registra quantas linhas havia).
    Repetidos com subsetores distintos (inclusive pendente × classificado) → subsetor None e
    regra descrevendo o conflito.
    """
    col_n = _localizar_coluna(siga, ("nucleo_ceg",))
    col_s = _localizar_coluna(siga, ("subsetor",))
    col_r = _localizar_coluna(siga, ("regra",))
    faltando = [n for n, c in (("nucleo_ceg", col_n), ("subsetor", col_s), ("regra", col_r)) if c is None]
    if faltando:
        raise _erro_colunas("SIGA classificado", faltando, siga)
    col_nome = _localizar_coluna(siga, ("nome",))

    grupos: dict[str, list[tuple[str | None, str, str | None]]] = {}
    nomes = siga[col_nome].tolist() if col_nome else [None] * len(siga)
    for n, s, r, nome in zip(siga[col_n].tolist(), siga[col_s].tolist(), siga[col_r].tolist(), nomes):
        nuc = nucleo_ceg(n)
        if nuc is None:
            continue
        grupos.setdefault(nuc, []).append((_texto_ou_none(s), _texto_ou_none(r) or "", _texto_ou_none(nome)))

    tabela: dict[str, tuple[str | None, str, str | None]] = {}
    for nuc, linhas in grupos.items():
        subs = {s for s, _, _ in linhas}
        nomes_distintos = list(dict.fromkeys(nm for _, _, nm in linhas if nm))
        nome = " | ".join(nomes_distintos) if nomes_distintos else None
        if len(linhas) == 1:
            tabela[nuc] = linhas[0]
        elif len(subs) == 1:
            s, r, _ = linhas[0]
            tabela[nuc] = (s, f"{r} [{len(linhas)} linhas no SIGA com o núcleo {nuc}, todas -> {s or 'pendente'}]", nome)
        else:
            rotulos = ", ".join(sorted(s or "pendente" for s in subs))
            tabela[nuc] = (
                None,
                f"conflito no SIGA: núcleo {nuc} em {len(linhas)} linhas com subsetores distintos "
                f"({rotulos}) -> pendente (classificar manualmente)",
                nome,
            )
    return tabela


def classificar_usinas_ons(usinas: pd.DataFrame, siga_classificado: pd.DataFrame) -> pd.DataFrame:
    """Casa as usinas do ONS com o SIGA classificado pelo núcleo do CEG.

    `usinas`: DataFrame com a coluna `ceg` (no formato do ONS; normalmente também `nom_usina`,
    que é mantida como está). `siga_classificado`: saída de `classificar_siga`.
    Devolve uma cópia de `usinas` (mesmo índice e ordem das linhas) com as colunas
    `nucleo_ceg`, `subsetor_siga`, `regra_siga` e `nome_siga` (nome do empreendimento no SIGA,
    para conferência do casamento). Sem casamento (CEG '-', vazio, inválido ou núcleo ausente
    do SIGA) → `subsetor_siga`, `regra_siga` e `nome_siga` = None.
    Funciona também com a tabela horária do ONS: o núcleo é calculado uma vez por CEG distinto.
    """
    col_ceg = _localizar_coluna(usinas, ("ceg",))
    if col_ceg is None:
        raise _erro_colunas("usinas do ONS", ["ceg"], usinas)
    tabela = _tabela_por_nucleo(siga_classificado)

    codigos, unicos = pd.factorize(usinas[col_ceg], use_na_sentinel=True)
    nuc_u, sub_u, reg_u, nome_u = [], [], [], []
    for v in list(unicos):
        nuc = nucleo_ceg(v)
        sub, reg, nome = tabela.get(nuc, (None, None, None)) if nuc is not None else (None, None, None)
        nuc_u.append(nuc)
        sub_u.append(sub)
        reg_u.append(reg)
        nome_u.append(nome)

    def expandir(valores: list) -> pd.Series:
        arr = np.empty(len(valores) + 1, dtype=object)
        arr[:-1] = valores
        arr[-1] = None  # código -1 (CEG ausente) aponta para o último elemento
        return pd.Series(arr[codigos], index=usinas.index, dtype=object)

    saida = usinas.copy()
    saida["nucleo_ceg"] = expandir(nuc_u)
    saida["subsetor_siga"] = expandir(sub_u)
    saida["regra_siga"] = expandir(reg_u)
    saida["nome_siga"] = expandir(nome_u)
    return saida
