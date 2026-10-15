"""Preços médios de geração por fonte: leilões da ANEEL corrigidos pelo IPCA (Seção 5.4, Rodada 02).

Fontes
------
- ANEEL, resultado dos leilões de geração (CSV em Latin-1, separador ';', decimal vírgula):
  `URL_LEILOES`. Campos usados: `DatLeilao` (data do leilão), `DscFonteEnergia` (fonte),
  `VlrPrecoLeilao` (R$/MWh na data do leilão) e `VlrEnergiaVendida` (MWmed).
- IBGE, SIDRA, tabela 1737, variável 2266 (IPCA, número-índice, dez/1993 = 100): `URL_IPCA_SIDRA`.

Método (Seção 5.4 das instruções da Rodada 02)
----------------------------------------------
1. Usam-se os leilões com data até 31/12/2018 (`data_corte`).
2. Registros com preço ou energia ausente ou não positivo são descartados (e contados).
3. Preço corrigido = `VlrPrecoLeilao` × (média do índice nos 12 meses de 2019 ÷ índice do mês do leilão).
4. Média ponderada por `VlrEnergiaVendida`, por subsetor de geração (fonte mapeada por
   `mapear_fonte_leilao`). Um preço nacional por fonte, o mesmo nas duas regiões.
5. NUC não tem leilão: usa-se a tarifa de Angra 1 e 2 para 2019 (`PRECO_NUCLEAR_2019`),
   acrescentada à tabela por `acrescentar_nuclear`.

ATENÇÃO — leitores ainda NÃO validados com os arquivos reais
------------------------------------------------------------
Quando este módulo foi escrito, o proxy do ambiente devolvia 403 para *.gov.br, de modo que
nem o CSV da ANEEL nem o JSON do SIDRA puderam ser baixados. O código foi escrito contra o
formato documentado nas instruções e testado só com dados sintéticos
(`tests/test_externos_leiloes.py`). Hipóteses sobre o formato real, a conferir no primeiro uso:

- CSV dos leilões: cabeçalho na primeira linha; nomes de coluna comparados sem acento, sem
  diferença de maiúsculas e ignorando espaços/sublinhados; encoding testado na ordem
  utf-8-sig → utf-8 → cp1252 → latin-1 (cp1252 é o "Latin-1" do Windows e só difere nos
  bytes 0x80–0x9F); separador detectado no cabeçalho (';' por padrão).
- Números: decimal vírgula com '.' de milhar opcional ("1.234,56"). A convenção é detectada
  nas colunas de preço e energia em conjunto; sem nenhuma vírgula, assume-se ponto decimal
  (com aviso se houver valores como "1.234", ambíguos). Pode ser forçada com `decimal=`.
- Datas: dd/mm/aaaa ou aaaa-mm-dd, com ou sem hora; a hora é descartada (só o dia importa).
- Cada linha do CSV é um registro de venda (leilão × produto/empreendimento) com preço e
  energia próprios; a ponderação é feita registro a registro.
- SIDRA: lista JSON cujo primeiro elemento é o cabeçalho (chaves 'V', 'D1C', ... →
  descrições); o mês vem no campo cuja descrição é "Mês (Código)", no formato AAAAMM.
- O texto de `DscFonteEnergia` usa os nomes das fontes (Hidrelétrica, PCH, Eólica, Biomassa,
  Gás Natural, Óleo Diesel...). Descrições que não casam com nenhuma regra, ou que casam com
  mais de uma (fontes híbridas), ficam como "não mapeadas" e são listadas no resultado.
"""
from __future__ import annotations

import io
import json
import re
import unicodedata
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------------
# Fontes e constantes de método
# --------------------------------------------------------------------------------------------
URL_LEILOES = (
    "https://dadosabertos.aneel.gov.br/dataset/593537c6-9e0e-4ed9-817a-2c5d5de05147/resource/"
    "a1328fc1-f06b-437d-8893-57ac2c8103df/download/resultado-leiloes-geracao.csv"
)
URL_IPCA_SIDRA = "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all"

ENCODINGS_CANDIDATOS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
SEPARADORES_CANDIDATOS = (";", ",", "\t", "|")

# coluna do arquivo da ANEEL → coluna padronizada
COLUNAS_LEILOES = {
    "DatLeilao": "data_leilao",
    "DscFonteEnergia": "fonte_energia",
    "VlrPrecoLeilao": "preco_rs_mwh",
    "VlrEnergiaVendida": "energia_mwmed",
}
COLUNAS_PADRAO = list(COLUNAS_LEILOES.values())

# Subsetores de geração, na ordem da tabela da Seção 3
SUBSETORES_GERACAO = (
    "S38_HID", "S38_EOL", "S38_SOL", "S38_BIO", "S38_CAR", "S38_GN", "S38_PET", "S38_NUC",
)

DATA_CORTE_PADRAO = "2018-12-31"  # Seção 5.4: leilões até 31/12/2018
ANO_BASE = 2019
VARIAVEL_IPCA = "2266"  # SIDRA 1737, variável 2266: IPCA, número-índice

# Valores do SIDRA que não são número (sigilo, não disponível, zero absoluto não resultante de
# arredondamento etc.); tratados como ausentes.
VALORES_AUSENTES = {"", "-", "--", "...", "..", "x", "nan", "none", "null", "na", "n/a"}

MESES_PT = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}

# --- NUC: não há leilão; tarifa de Angra 1 e 2 para 2019 (Seção 5.4) ---
PRECO_NUCLEAR_2019 = 247.47  # R$/MWh
FONTE_PRECO_NUCLEAR = (
    "Tarifa de Angra 1 e 2 para 2019 = R$ 247,47/MWh, fixada pela ANEEL em dezembro de 2018 "
    "(resolução da ANEEL a confirmar; fonte secundária: IstoÉ Dinheiro/Estadão Conteúdo, "
    "18/12/2018)"
)

# --- Valores de referência: só para comparação, nunca como dado ---
# valor de referência das instruções da Rodada 02, Seção 5.4 (R$/MWh de 2019; tolerância 1)
REFERENCIA_PRECOS = {
    "S38_HID": 166.4,
    "S38_EOL": 173.2,
    "S38_SOL": 260.6,
    "S38_BIO": 203.0,
    "S38_CAR": 251.1,
    "S38_GN": 246.7,
    "S38_PET": 260.0,
    "S38_NUC": 247.47,
}
# valor de referência das instruções da Rodada 02, Seção 5.4 (média do índice IPCA em 2019)
REFERENCIA_IPCA_MEDIA_2019 = 5213.61
# tolerância das instruções da Rodada 02, Seção 5.4
TOLERANCIA_REFERENCIA = 1.0
ROTULO_IPCA_MEDIA = "IPCA_MEDIA_2019"

# --- Mapeamento DscFonteEnergia → subsetor ---
# Regras aplicadas ao texto sem acento, minúsculo, com pontuação trocada por espaço.
# Seção 5.4: Hidro→HID, Eólica→EOL, Solar→SOL, Biomassa e Resíduos Sólidos Urbanos→BIO,
# Carvão→CAR, Gás→GN, Óleo→PET (+ instruções do orquestrador: PCH/CGH/UHE, Fotovoltaica,
# Bagaço, Biogás, GNL, diesel, Nuclear). Acréscimos tirados de outras seções das instruções:
# lenha e biodiesel → BIO (5.7); licor negro → BIO (5.1); floresta, agroindustriais, resíduos
# animais e biocombustíveis → BIO (5.2); gás de alto-forno/coqueria → CAR e gás de refinaria e
# petróleo → PET (5.2). Siglas usuais da ANEEL para eólica (EOL) e fotovoltaica (UFV) também
# são aceitas. Uma descrição que casa com mais de um subsetor (ex.: híbrida) fica sem mapa.
_REGRAS_FONTE: tuple[tuple[str, re.Pattern], ...] = (
    ("S38_HID", re.compile(r"\b(hidr(?!ogeni)\w*|pch|cgh|uhe)\b")),
    ("S38_EOL", re.compile(r"\b(eolic\w*|eolio\w*|eol)\b")),
    ("S38_SOL", re.compile(r"\b(solar\w*|fotovoltaic\w*|ufv)\b")),
    ("S38_BIO", re.compile(
        r"\b(biomassa\w*|bagaco\w*|biogas\w*|biodiesel|biocombustive\w*|lenha|licor negro"
        r"|residuos? solidos? urbanos?|florest\w*|agroindustria\w*|residuos? anima\w*)\b"
    )),
    ("S38_CAR", re.compile(r"\b(carvao|alto forno|coqueria)\b")),
    ("S38_GN", re.compile(r"\bgas\b(?! de (alto forno|coqueria|refinaria))|\bgnl\b")),
    ("S38_PET", re.compile(r"\b(oleo(?! vegetal)|diesel|petroleo|refinaria)\b")),
    ("S38_NUC", re.compile(r"\bnuclear\b")),
)


# --------------------------------------------------------------------------------------------
# Utilitários de texto, números e datas
# --------------------------------------------------------------------------------------------
def _sem_acento(texto) -> str:
    """Texto sem acento, minúsculo, sem espaços nas pontas e com espaços internos simples."""
    t = unicodedata.normalize("NFKD", str(texto))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().lower()


def _chave_coluna(nome) -> str:
    """Chave de comparação de nomes de coluna: sem acento, minúscula, só letras e dígitos."""
    return re.sub(r"[^a-z0-9]", "", _sem_acento(nome))


def _ler_texto(caminho: str | Path, encoding: str | None = None) -> tuple[str, str]:
    """Lê o arquivo como texto, testando os encodings candidatos em ordem. Devolve (texto, encoding)."""
    dados = Path(caminho).read_bytes()
    candidatos = (encoding,) if encoding else ENCODINGS_CANDIDATOS
    for enc in candidatos:
        try:
            return dados.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise ValueError(f"não foi possível decodificar {caminho} com {candidatos}")


def _detectar_separador(texto: str) -> str:
    """Separador mais frequente na primeira linha não vazia (';' em caso de empate ou ausência)."""
    primeira = next((ln for ln in texto.splitlines() if ln.strip()), "")
    contagens = {s: primeira.count(s) for s in SEPARADORES_CANDIDATOS}
    melhor = max(contagens, key=lambda s: (contagens[s], s == ";"))
    return melhor if contagens[melhor] > 0 else ";"


def _localizar_colunas(colunas: Iterable, exigidas: dict[str, str], descricao: str) -> dict[str, str]:
    """Casa as colunas exigidas com as do arquivo (sem acento/maiúsculas/espaços).

    Devolve {coluna_no_arquivo: coluna_padronizada}. Levanta ValueError se faltar alguma.
    """
    colunas = list(colunas)
    por_chave: dict[str, str] = {}
    for c in colunas:
        por_chave.setdefault(_chave_coluna(c), c)
    mapa, faltando = {}, []
    for original, padrao in exigidas.items():
        achada = por_chave.get(_chave_coluna(original))
        if achada is None:
            faltando.append(original)
        else:
            mapa[achada] = padrao
    if faltando:
        raise ValueError(
            f"{descricao}: coluna(s) obrigatória(s) ausente(s): {faltando}. "
            f"Colunas disponíveis: {[str(c) for c in colunas]}"
        )
    return mapa


def _limpar_numero(texto) -> str:
    """Tira espaços (inclusive não separáveis) e o símbolo R$ de um valor numérico em texto."""
    t = str(texto).replace(" ", "").replace(" ", "")
    t = re.sub(r"(?i)r\$", "", t)
    return re.sub(r"\s+", "", t)


def _detectar_decimal(valores: Iterable[str]) -> str:
    """Convenção decimal de um conjunto de valores em texto: ',' (padrão ANEEL) ou '.'.

    Votos: "1.234,56" e "166,40" → vírgula; "1,234.56" e "1,234,567" → ponto; "1.234.567" →
    vírgula (pontos só podem ser milhar). Sem nenhuma vírgula nem pontos repetidos → ponto,
    com aviso se houver valores como "1.234" (ambíguos: podem ser milhar).
    """
    virgula = ponto = 0
    ambiguos = []
    for v in valores:
        v = _limpar_numero(v)
        if _sem_acento(v) in VALORES_AUSENTES:
            continue
        if "," in v and "." in v:
            if v.rfind(",") > v.rfind("."):
                virgula += 1
            else:
                ponto += 1
        elif "," in v:
            if v.count(",") == 1:
                virgula += 1
            else:
                ponto += 1
        elif v.count(".") > 1:
            virgula += 1
        elif re.fullmatch(r"-?\d{1,3}\.\d{3}", v):
            ambiguos.append(v)
    if virgula >= ponto and virgula > 0:
        return ","
    if ambiguos and ponto == 0:
        warnings.warn(
            "nenhuma vírgula decimal encontrada; assumindo ponto decimal, mas há valores ambíguos "
            f"(ex.: {ambiguos[:3]}) que poderiam ter '.' como separador de milhar. "
            "Use decimal=',' se for o caso.",
            stacklevel=3,
        )
    return "."


def _converter_numeros(serie: pd.Series, decimal: str) -> tuple[pd.Series, int]:
    """Converte texto em float na convenção dada. Devolve (série, nº de valores não numéricos)."""
    texto = serie.fillna("").astype(str).map(_limpar_numero)
    ausente = texto.map(lambda v: _sem_acento(v) in VALORES_AUSENTES)
    if decimal == ",":
        texto = texto.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    else:
        texto = texto.str.replace(",", "", regex=False)
    numeros = pd.to_numeric(texto.where(~ausente, None), errors="coerce").astype(float)
    nao_numericos = int((numeros.isna() & ~ausente).sum())
    return numeros, nao_numericos


def _texto_para_float(valor) -> float:
    """Converte um valor isolado (ex.: 'V' do SIDRA) em float; ausentes viram NaN.

    Com vírgula e ponto, o último é o decimal; só vírgula → vírgula decimal; só ponto → ponto.
    """
    if valor is None:
        return np.nan
    if isinstance(valor, (int, float, np.integer, np.floating)) and not isinstance(valor, bool):
        return float(valor)
    v = _limpar_numero(valor)
    if _sem_acento(v) in VALORES_AUSENTES:
        return np.nan
    if "," in v and "." in v:
        v = v.replace(".", "").replace(",", ".") if v.rfind(",") > v.rfind(".") else v.replace(",", "")
    elif "," in v:
        v = v.replace(",", ".") if v.count(",") == 1 else v.replace(",", "")
    try:
        return float(v)
    except ValueError:
        return np.nan


def _converter_datas(serie: pd.Series) -> pd.Series:
    """Datas em dd/mm/aaaa ou aaaa-mm-dd (com ou sem hora) → datetime (só o dia; inválidas → NaT)."""
    texto = serie.fillna("").astype(str).str.strip()
    iso = texto.str.extract(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?:\D|$)")
    br = texto.str.extract(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:\D|$)")
    ano = iso[0].fillna(br[2])
    mes = iso[1].fillna(br[1])
    dia = iso[2].fillna(br[0])
    montada = ano + "-" + mes.str.zfill(2) + "-" + dia.str.zfill(2)
    return pd.to_datetime(montada, format="%Y-%m-%d", errors="coerce")


def _periodo_mensal(valor) -> pd.Period:
    """Converte um mês em Period mensal: Period, Timestamp, 'AAAAMM', 'AAAA-MM' ou 'AAAA-MM-DD'."""
    if isinstance(valor, pd.Period):
        return valor.asfreq("M")
    if isinstance(valor, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(valor).to_period("M")
    if isinstance(valor, (int, np.integer)) and not isinstance(valor, bool):
        valor = str(valor)
    t = str(valor).strip()
    m = re.fullmatch(r"(\d{4})(\d{2})", t) or re.match(r"^(\d{4})[-/](\d{1,2})(?:[-/]\d{1,2})?$", t)
    if m:
        ano, mes = int(m.group(1)), int(m.group(2))
        if 1 <= mes <= 12:
            return pd.Period(year=ano, month=mes, freq="M")
    raise ValueError(f"mês inválido: {valor!r} (esperado AAAAMM, AAAA-MM ou Period mensal)")


# --------------------------------------------------------------------------------------------
# 1) Leilões da ANEEL
# --------------------------------------------------------------------------------------------
def ler_leiloes(
    caminho: str | Path,
    *,
    encoding: str | None = None,
    separador: str | None = None,
    decimal: str | None = None,
    manter_colunas: bool = False,
) -> pd.DataFrame:
    """Lê o CSV de resultado dos leilões de geração da ANEEL.

    Devolve um DataFrame com `data_leilao` (datetime, só o dia), `fonte_energia` (texto original,
    sem espaços nas pontas), `preco_rs_mwh` (float, R$/MWh na data do leilão) e `energia_mwmed`
    (float, MWmed vendidos). Encoding, separador e convenção decimal são detectados, salvo se
    informados. Com `manter_colunas=True`, as demais colunas do arquivo vêm em seguida (nomes
    originais, como texto) e uma coluna `linha_arquivo` (nº da linha no CSV, cabeçalho = 1).

    Linhas totalmente vazias nas quatro colunas são ignoradas. Valores não convertíveis viram
    NaN/NaT e são contados em `df.attrs` (`valores_nao_numericos`, `datas_invalidas`), junto com
    `encoding`, `separador` e `decimal` usados. Levanta ValueError se faltar coluna obrigatória.
    """
    texto, enc = _ler_texto(caminho, encoding)
    sep = separador or _detectar_separador(texto)
    bruto = pd.read_csv(
        io.StringIO(texto), sep=sep, dtype=str, keep_default_na=False, skipinitialspace=True
    )
    bruto.columns = [str(c).strip() for c in bruto.columns]
    mapa = _localizar_colunas(bruto.columns, COLUNAS_LEILOES, "CSV de leilões da ANEEL")
    por_padrao = {padrao: original for original, padrao in mapa.items()}
    bruto = bruto.apply(lambda s: s.fillna("").astype(str).str.strip())
    bruto["linha_arquivo"] = np.arange(len(bruto)) + 2

    vazias = (bruto[list(mapa)] == "").all(axis=1)
    bruto = bruto.loc[~vazias].reset_index(drop=True)

    col_preco, col_energia = por_padrao["preco_rs_mwh"], por_padrao["energia_mwmed"]
    dec = decimal or _detectar_decimal(list(bruto[col_preco]) + list(bruto[col_energia]))
    if dec not in (",", "."):
        raise ValueError(f"decimal deve ser ',' ou '.', não {dec!r}")
    preco, n_preco_nn = _converter_numeros(bruto[col_preco], dec)
    energia, n_energia_nn = _converter_numeros(bruto[col_energia], dec)
    datas = _converter_datas(bruto[por_padrao["data_leilao"]])
    datas_invalidas = int((datas.isna() & (bruto[por_padrao["data_leilao"]] != "")).sum())

    df = pd.DataFrame(
        {
            "data_leilao": datas,
            "fonte_energia": bruto[por_padrao["fonte_energia"]],
            "preco_rs_mwh": preco,
            "energia_mwmed": energia,
        }
    )
    if manter_colunas:
        extras = [c for c in bruto.columns if c not in mapa and c != "linha_arquivo"]
        for c in extras:
            df[c] = bruto[c]
        df["linha_arquivo"] = bruto["linha_arquivo"].astype(int)
    df.attrs = {
        "fonte": "ANEEL, resultado dos leilões de geração",
        "encoding": enc,
        "separador": sep,
        "decimal": dec,
        "colunas_originais": dict(por_padrao),
        "valores_nao_numericos": {"preco_rs_mwh": n_preco_nn, "energia_mwmed": n_energia_nn},
        "datas_invalidas": datas_invalidas,
    }
    return df


# --------------------------------------------------------------------------------------------
# 2) IPCA, SIDRA 1737 / variável 2266
# --------------------------------------------------------------------------------------------
def _carregar_json_sidra(fonte) -> list:
    """Aceita caminho de arquivo JSON, texto JSON ou a lista já carregada."""
    if isinstance(fonte, list):
        return fonte
    if isinstance(fonte, str) and fonte.lstrip().startswith(("[", "{")):
        return json.loads(fonte)
    if isinstance(fonte, (str, Path)):
        texto, _ = _ler_texto(fonte)
        return json.loads(texto)
    raise TypeError(f"esperado caminho de arquivo JSON ou lista do SIDRA, não {type(fonte).__name__}")


def _chave_por_descricao(cabecalho: dict[str, str], criterio: Callable[[str], bool]) -> str | None:
    """Primeira chave do cabeçalho do SIDRA cuja descrição (normalizada) atende ao critério."""
    for chave, descricao in cabecalho.items():
        if criterio(_sem_acento(descricao)):
            return chave
    return None


def _mes_por_nome(texto) -> pd.Period:
    """'janeiro 2019' → Period('2019-01')."""
    m = re.fullmatch(r"([a-z]+)\s*(?:de\s+)?(\d{4})", _sem_acento(texto))
    if not m or m.group(1) not in MESES_PT:
        raise ValueError(f"mês inválido: {texto!r}")
    return pd.Period(year=int(m.group(2)), month=MESES_PT[m.group(1)], freq="M")


def ler_ipca_sidra(fonte, *, variavel: str | None = VARIAVEL_IPCA) -> pd.DataFrame:
    """Lê o IPCA número-índice da API de valores do SIDRA (tabela 1737, variável 2266).

    `fonte`: caminho de arquivo JSON (ou o texto JSON) ou a lista já carregada. O primeiro
    elemento é o cabeçalho (chave → descrição); o mês é o campo cuja descrição contém "Mês" e
    "Código" (formato AAAAMM) e o valor é o campo "Valor" ('V'). Se houver o campo "Variável
    (Código)" e `variavel` não for None, só os registros dessa variável são usados.

    Devolve DataFrame com `mes` (Period mensal) e `indice` (float; '...', '-', 'X' → NaN),
    ordenado por mês. Levanta ValueError se o mês ou o valor não forem identificados ou se um
    mês aparecer com valores diferentes.
    """
    registros = _carregar_json_sidra(fonte)
    if not isinstance(registros, list) or not registros or not isinstance(registros[0], dict):
        raise ValueError("JSON do SIDRA vazio ou fora do formato esperado (lista de dicionários)")

    primeiro = registros[0]
    tem_cabecalho = _sem_acento(primeiro.get("V", "")) == "valor"
    cabecalho = {str(k): str(v) for k, v in primeiro.items()} if tem_cabecalho else {}
    dados = [r for r in (registros[1:] if tem_cabecalho else registros) if isinstance(r, dict)]

    chave_valor = _chave_por_descricao(cabecalho, lambda d: d == "valor") or "V"
    chave_mes = _chave_por_descricao(
        cabecalho, lambda d: bool(re.search(r"\bmes\b", d)) and "codigo" in d
    )
    chave_mes_nome = None
    if chave_mes is None:
        chave_mes_nome = _chave_por_descricao(cabecalho, lambda d: d == "mes")
    if chave_mes is None and chave_mes_nome is None and not cabecalho:
        # sem cabeçalho: procura um campo de código cujos valores sejam todos AAAAMM
        chaves = sorted({k for r in dados for k in r if str(k).endswith("C")})
        for k in chaves:
            vals = [str(r.get(k, "")) for r in dados]
            if vals and all(re.fullmatch(r"(19|20)\d{2}(0[1-9]|1[0-2])", v) for v in vals):
                chave_mes = k
                break
    if chave_mes is None and chave_mes_nome is None:
        raise ValueError(
            "JSON do SIDRA: campo do mês não encontrado (esperado descrição 'Mês (Código)'). "
            f"Cabeçalho disponível: {cabecalho or sorted({k for r in dados for k in r})}"
        )
    if dados and not any(chave_valor in r for r in dados):
        raise ValueError(
            f"JSON do SIDRA: campo de valor {chave_valor!r} ausente. "
            f"Campos disponíveis: {sorted({k for r in dados for k in r})}"
        )

    chave_var = _chave_por_descricao(cabecalho, lambda d: d.startswith("variavel") and "codigo" in d)
    if chave_var is not None and variavel is not None:
        dados = [r for r in dados if str(r.get(chave_var, "")).strip() == str(variavel)]
        if not dados:
            raise ValueError(f"JSON do SIDRA: nenhum registro da variável {variavel}")

    meses, valores = [], []
    for r in dados:
        meses.append(
            _periodo_mensal(r.get(chave_mes, "")) if chave_mes else _mes_por_nome(r.get(chave_mes_nome, ""))
        )
        valores.append(_texto_para_float(r.get(chave_valor)))
    df = pd.DataFrame({"mes": pd.PeriodIndex(meses, freq="M"), "indice": np.array(valores, dtype=float)})
    df = df.sort_values("mes").reset_index(drop=True)

    dup = df[df["mes"].duplicated(keep=False)]
    if not dup.empty:
        conflitos = dup.groupby("mes")["indice"].nunique(dropna=False)
        if (conflitos > 1).any():
            raise ValueError(f"JSON do SIDRA: meses com valores diferentes: {list(conflitos[conflitos > 1].index.astype(str))}")
        df = df.drop_duplicates("mes").reset_index(drop=True)
    df.attrs = {"fonte": "IBGE, SIDRA, tabela 1737, variável 2266 (IPCA, número-índice)"}
    return df


def _serie_ipca(ipca) -> pd.Series:
    """Padroniza o IPCA (DataFrame mes/indice ou Series indexada por mês) em Series por Period."""
    if isinstance(ipca, pd.Series):
        meses, valores = list(ipca.index), ipca.to_numpy()
    else:
        mapa = _localizar_colunas(ipca.columns, {"mes": "mes", "indice": "indice"}, "tabela do IPCA")
        por_padrao = {p: o for o, p in mapa.items()}
        meses, valores = list(ipca[por_padrao["mes"]]), ipca[por_padrao["indice"]].to_numpy()
    serie = pd.Series(
        pd.to_numeric(pd.Series(valores), errors="coerce").to_numpy(dtype=float),
        index=pd.PeriodIndex([_periodo_mensal(m) for m in meses], freq="M"),
        name="indice",
    )
    if serie.index.duplicated().any():
        raise ValueError(f"IPCA com meses repetidos: {list(serie.index[serie.index.duplicated()].astype(str))}")
    return serie.sort_index()


def media_indice_ano(ipca, ano: int = ANO_BASE) -> float:
    """Média simples do número-índice nos 12 meses do ano. Exige os 12 meses com valor."""
    serie = _serie_ipca(ipca)
    do_ano = serie[serie.index.year == ano].dropna()
    faltando = sorted(set(range(1, 13)) - set(do_ano.index.month))
    if faltando:
        raise ValueError(f"IPCA sem valor em {ano} para o(s) mês(es) {faltando}")
    return float(do_ano.mean())


# --------------------------------------------------------------------------------------------
# 3) Mapeamento da fonte do leilão
# --------------------------------------------------------------------------------------------
def mapear_fonte_leilao(dsc) -> str | None:
    """Mapeia `DscFonteEnergia` no subsetor de geração (ex.: 'Hidrelétrica' → 'S38_HID').

    Comparação sem acento e sem diferença de maiúsculas. Devolve None se a descrição for vazia,
    não casar com nenhuma regra ou casar com mais de um subsetor (ex.: projeto híbrido).
    """
    if dsc is None or (isinstance(dsc, float) and np.isnan(dsc)):
        return None
    texto = re.sub(r"[^a-z0-9]+", " ", _sem_acento(dsc)).strip()
    if not texto:
        return None
    achados = [sub for sub, regra in _REGRAS_FONTE if regra.search(texto)]
    return achados[0] if len(achados) == 1 else None


# --------------------------------------------------------------------------------------------
# 4) Preços médios de 2019 por subsetor
# --------------------------------------------------------------------------------------------
@dataclass
class ResultadoPrecos:
    """Resultado de `precos_medios_2019`.

    Desempacota como `(tabela, detalhe)`; os demais campos ficam como atributos:
    - `tabela`: subsetor, preco_2019_rs_mwh, energia_mwmed_total, n_registros, primeiro_leilao,
      ultimo_leilao, origem;
    - `detalhe`: cada registro usado, com mês, índice do mês, fator de correção e preço de 2019;
    - `media_ipca_2019`: média do índice nos 12 meses do ano-base;
    - `fontes_nao_mapeadas`: fonte_energia, n_registros, energia_mwmed_total (registros válidos
      até a data de corte que não casaram com nenhum subsetor);
    - `descartados`: registros até a data de corte (ou sem data) descartados, com o motivo;
    - `contagens`: nº de registros lidos, sem data, após o corte, com preço/energia inválidos,
      com fonte não mapeada e usados (lidos = sem_data + apos_corte + invalidos + nao_mapeados + usados).
    """

    tabela: pd.DataFrame
    detalhe: pd.DataFrame
    media_ipca_2019: float
    fontes_nao_mapeadas: pd.DataFrame
    descartados: pd.DataFrame
    contagens: dict[str, int]
    data_corte: pd.Timestamp
    ano_base: int = ANO_BASE

    def __iter__(self) -> Iterator[pd.DataFrame]:
        return iter((self.tabela, self.detalhe))


def _ordem_subsetor(subsetores: pd.Series) -> pd.Series:
    ordem = {s: i for i, s in enumerate(SUBSETORES_GERACAO)}
    return subsetores.map(lambda s: ordem.get(s, len(ordem)))


def precos_medios_2019(
    leiloes: pd.DataFrame,
    ipca,
    data_corte: str | pd.Timestamp = DATA_CORTE_PADRAO,
    *,
    ano_base: int = ANO_BASE,
) -> ResultadoPrecos:
    """Preço médio de 2019 por subsetor de geração, a partir dos leilões da ANEEL (Seção 5.4).

    `leiloes`: saída de `ler_leiloes` (data_leilao, fonte_energia, preco_rs_mwh, energia_mwmed;
    outras colunas são repassadas ao detalhe). `ipca`: saída de `ler_ipca_sidra` (mes, indice).

    Passos: (1) registros com data_leilao ≤ data_corte (comparação por dia); (2) descarta preço
    ou energia ausente ou ≤ 0; (3) mapeia a fonte (`mapear_fonte_leilao`; não mapeadas vão para
    `fontes_nao_mapeadas`); (4) preço de 2019 = preco_rs_mwh × média do índice no ano-base ÷
    índice do mês do leilão; (5) média ponderada por energia_mwmed, por subsetor.

    Devolve `ResultadoPrecos`, que desempacota como `(tabela, detalhe)`. Levanta ValueError se
    faltar coluna, se o IPCA não tiver os 12 meses do ano-base ou o mês de algum leilão usado.
    """
    faltando = [c for c in COLUNAS_PADRAO if c not in leiloes.columns]
    if faltando:
        raise ValueError(
            f"leilões: coluna(s) ausente(s) {faltando}. Colunas disponíveis: {list(leiloes.columns)}"
        )
    corte = pd.Timestamp(data_corte).normalize()
    serie_ipca = _serie_ipca(ipca)
    media = media_indice_ano(serie_ipca, ano_base)

    df = pd.DataFrame(leiloes).copy().reset_index(drop=True)
    df.attrs = {}
    df["data_leilao"] = pd.to_datetime(df["data_leilao"], errors="coerce")
    df["preco_rs_mwh"] = pd.to_numeric(df["preco_rs_mwh"], errors="coerce").astype(float)
    df["energia_mwmed"] = pd.to_numeric(df["energia_mwmed"], errors="coerce").astype(float)

    sem_data = df["data_leilao"].isna()
    apos_corte = ~sem_data & (df["data_leilao"].dt.normalize() > corte)
    na_janela = ~sem_data & ~apos_corte
    preco_inv = ~(df["preco_rs_mwh"] > 0)  # NaN também é inválido
    energia_inv = ~(df["energia_mwmed"] > 0)
    invalido = na_janela & (preco_inv | energia_inv)

    # --- descartados (sem data, ou na janela com preço/energia inválidos) ---
    motivo = pd.Series("", index=df.index, dtype=object)
    motivo[na_janela & preco_inv & energia_inv] = "preço e energia ausentes ou não positivos"
    motivo[na_janela & preco_inv & ~energia_inv] = "preço ausente ou não positivo"
    motivo[na_janela & ~preco_inv & energia_inv] = "energia ausente ou não positiva"
    motivo[sem_data] = "data do leilão ausente ou inválida"
    descartados = df.loc[sem_data | invalido].copy()
    descartados["motivo"] = motivo[sem_data | invalido]
    descartados = descartados.reset_index(drop=True)

    # --- válidos: mapeia a fonte ---
    validos = df.loc[na_janela & ~invalido].copy()
    validos["subsetor"] = validos["fonte_energia"].map(mapear_fonte_leilao)
    nao_mapeado = validos["subsetor"].isna()
    nm = validos.loc[nao_mapeado]
    fontes_nao_mapeadas = (
        nm.assign(fonte_energia=nm["fonte_energia"].fillna("").astype(str))
        .groupby("fonte_energia", as_index=False)
        .agg(n_registros=("energia_mwmed", "size"), energia_mwmed_total=("energia_mwmed", "sum"))
        .sort_values(["energia_mwmed_total", "fonte_energia"], ascending=[False, True])
        .reset_index(drop=True)
    )

    # --- correção pelo IPCA ---
    usados = validos.loc[~nao_mapeado].copy()
    usados["mes_leilao"] = usados["data_leilao"].dt.to_period("M")
    indice_por_mes = serie_ipca.dropna().to_dict()
    usados["indice_mes_leilao"] = usados["mes_leilao"].map(lambda m: indice_por_mes.get(m, np.nan)).astype(float)
    sem_indice = usados.loc[usados["indice_mes_leilao"].isna(), "mes_leilao"]
    if not sem_indice.empty:
        raise ValueError(
            f"IPCA sem valor para o(s) mês(es) de leilão {sorted(set(sem_indice.astype(str)))}"
        )
    usados[f"indice_medio_{ano_base}"] = media
    usados["fator_correcao"] = media / usados["indice_mes_leilao"]
    usados["preco_2019_rs_mwh"] = usados["preco_rs_mwh"] * usados["fator_correcao"]
    usados = (
        usados.assign(_ordem=_ordem_subsetor(usados["subsetor"]))
        .sort_values(["_ordem", "data_leilao"], kind="stable")
        .drop(columns="_ordem")
        .reset_index(drop=True)
    )
    calculadas = ["subsetor", "mes_leilao", "indice_mes_leilao", f"indice_medio_{ano_base}",
                  "fator_correcao", "preco_2019_rs_mwh"]
    outras = [c for c in usados.columns if c not in COLUNAS_PADRAO and c not in calculadas]
    detalhe = usados[COLUNAS_PADRAO + calculadas + outras]

    # --- média ponderada por subsetor ---
    origem = (
        f"Leilões de geração ANEEL até {corte:%d/%m/%Y}, preços corrigidos pelo IPCA "
        f"(SIDRA 1737, var. 2266; média de {ano_base} ÷ índice do mês do leilão), "
        "média ponderada pela energia vendida (MWmed)"
    )
    linhas = []
    for sub, g in detalhe.groupby("subsetor", sort=False):
        energia = g["energia_mwmed"].to_numpy(dtype=float)
        preco = g["preco_2019_rs_mwh"].to_numpy(dtype=float)
        linhas.append(
            {
                "subsetor": sub,
                "preco_2019_rs_mwh": float(np.sum(preco * energia) / np.sum(energia)),
                "energia_mwmed_total": float(np.sum(energia)),
                "n_registros": int(len(g)),
                "primeiro_leilao": g["data_leilao"].min(),
                "ultimo_leilao": g["data_leilao"].max(),
                "origem": origem,
            }
        )
    colunas_tabela = ["subsetor", "preco_2019_rs_mwh", "energia_mwmed_total", "n_registros",
                      "primeiro_leilao", "ultimo_leilao", "origem"]
    tabela = pd.DataFrame(linhas, columns=colunas_tabela)
    tabela["n_registros"] = tabela["n_registros"].astype(int)

    contagens = {
        "n_registros_lidos": int(len(df)),
        "n_sem_data": int(sem_data.sum()),
        "n_apos_corte": int(apos_corte.sum()),
        "n_preco_invalido": int((na_janela & preco_inv).sum()),
        "n_energia_invalida": int((na_janela & energia_inv).sum()),
        "n_preco_ou_energia_invalidos": int(invalido.sum()),
        "n_fonte_nao_mapeada": int(nao_mapeado.sum()),
        "n_usados": int(len(detalhe)),
    }
    return ResultadoPrecos(
        tabela=tabela,
        detalhe=detalhe,
        media_ipca_2019=media,
        fontes_nao_mapeadas=fontes_nao_mapeadas,
        descartados=descartados,
        contagens=contagens,
        data_corte=corte,
        ano_base=ano_base,
    )


# --------------------------------------------------------------------------------------------
# 5) Nuclear e comparação com a referência
# --------------------------------------------------------------------------------------------
def acrescentar_nuclear(
    tabela: pd.DataFrame, preco: float = PRECO_NUCLEAR_2019, origem: str = FONTE_PRECO_NUCLEAR
) -> pd.DataFrame:
    """Devolve a tabela de preços com a linha S38_NUC (tarifa de Angra 1 e 2; não há leilão).

    Levanta ValueError se a tabela já tiver S38_NUC (não sobrescreve).
    """
    if "subsetor" not in tabela.columns:
        raise ValueError(f"tabela sem coluna 'subsetor'. Colunas disponíveis: {list(tabela.columns)}")
    if (tabela["subsetor"] == "S38_NUC").any():
        raise ValueError("a tabela já tem S38_NUC")
    nova = {c: pd.NA for c in tabela.columns}
    nova.update(
        {
            "subsetor": "S38_NUC",
            "preco_2019_rs_mwh": float(preco),
            "energia_mwmed_total": np.nan,
            "n_registros": 0,
            "primeiro_leilao": pd.NaT,
            "ultimo_leilao": pd.NaT,
            "origem": origem,
        }
    )
    linha = pd.DataFrame([nova])
    partes = [t for t in (tabela, linha) if not t.empty]
    saida = pd.concat(partes, ignore_index=True) if len(partes) > 1 else linha
    saida = saida.assign(_ordem=_ordem_subsetor(saida["subsetor"]))
    saida = saida.sort_values("_ordem", kind="stable").drop(columns="_ordem").reset_index(drop=True)
    for c in ("primeiro_leilao", "ultimo_leilao"):
        if c in saida.columns:
            saida[c] = pd.to_datetime(saida[c])
    if "n_registros" in saida.columns:
        saida["n_registros"] = saida["n_registros"].astype(int)
    return saida


def comparar_com_referencia(
    tabela,
    referencia: dict[str, float] | None = None,
    tolerancia: float = TOLERANCIA_REFERENCIA,
    media_ipca_2019: float | None = None,
) -> pd.DataFrame:
    """Compara os preços obtidos com os de referência da Seção 5.4.

    `tabela`: DataFrame com `subsetor` e `preco_2019_rs_mwh` (ou um `ResultadoPrecos`, cuja
    média do IPCA também é comparada). Devolve subsetor, esperado, obtido, diferenca (obtido −
    esperado) e dentro_tolerancia (|diferença| ≤ tolerância; False se faltar valor). Subsetores
    da tabela fora da referência aparecem com esperado NaN. Se `media_ipca_2019` for dada,
    acrescenta a linha `IPCA_MEDIA_2019` comparada com `REFERENCIA_IPCA_MEDIA_2019`.
    """
    if isinstance(tabela, ResultadoPrecos):
        if media_ipca_2019 is None:
            media_ipca_2019 = tabela.media_ipca_2019
        tabela = tabela.tabela
    referencia = REFERENCIA_PRECOS if referencia is None else referencia
    faltando = [c for c in ("subsetor", "preco_2019_rs_mwh") if c not in tabela.columns]
    if faltando:
        raise ValueError(f"tabela sem {faltando}. Colunas disponíveis: {list(tabela.columns)}")
    if tabela["subsetor"].duplicated().any():
        raise ValueError("tabela com subsetor repetido")
    obtidos = dict(zip(tabela["subsetor"], tabela["preco_2019_rs_mwh"].astype(float)))

    linhas = [(s, float(v), obtidos.get(s, np.nan)) for s, v in referencia.items()]
    linhas += [(s, np.nan, v) for s, v in obtidos.items() if s not in referencia]
    if media_ipca_2019 is not None:
        linhas.append((ROTULO_IPCA_MEDIA, REFERENCIA_IPCA_MEDIA_2019, float(media_ipca_2019)))
    saida = pd.DataFrame(linhas, columns=["subsetor", "esperado", "obtido"])
    saida["diferenca"] = saida["obtido"] - saida["esperado"]
    saida["dentro_tolerancia"] = (saida["diferenca"].abs() <= tolerancia).fillna(False).astype(bool)
    return saida
