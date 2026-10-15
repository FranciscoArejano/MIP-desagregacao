"""Emissões do setor elétrico — SEEG 13.0 (Seção 5.7 das instruções da Rodada 02).

Fonte: SEEG 13.0, "Dados nacionais" (xlsx de ~185 MB; não versionar o bruto):
https://seeg.eco.br/wp-content/uploads/2025/12/Dados-nacionais-13.0.xlsx

Aba `Dados`; colunas de texto 'Emissão/Remoção/Bunker', 'Gás', 'Setor de emissão',
'Categoria emissora', 'Sub-categoria emissora', 'Produto ou sistema', 'Detalhamento', 'Recorte',
'Atividade geral', 'Estado', 'Bioma' e uma coluna por ano de 1970 a 2024.

Filtros (Seção 5.7):
- Gás = 'CO2e (t) GWP-AR5'; ano 2019;
- grupo 'geracao': Categoria emissora = 'Geração de eletricidade (serviço público)';
- grupo 'sf6': Categoria emissora OU Sub-categoria emissora = 'Uso de SF6 em equipamentos
  elétricos' (setor Processos Industriais) — usado só como valor nacional.

Mapeamento combustível → subsetor (Seção 5.7):
  Carvão mineral, Alcatrão → S38_CAR; Gás natural seco, Gás natural úmido → S38_GN;
  Diesel de petróleo, Óleo combustível, Gás de refinaria, Outros energéticos de petróleo → S38_PET;
  Biodiesel, Biogás, Lenha, Outras biomassas → S38_BIO.
Região: Estado 'RS' / 'Rio Grande do Sul' → RS; 'Não Alocado' → 'Não alocado' (que vai para o RB
na tabela por subsetor); demais estados → RB.
Petróleo no RS: o PET-RS é latente, então as emissões PET do RS (diesel, óleo combustível e demais
PET; 17.8 mil t na referência) vão para S38_CAR e S38_GN do RS na proporção do GWh de cada um.
SF6: não entra na tabela por subsetor — o rateio (TRA e DIS de cada região, pelo VBP) é do motor.

ATENÇÃO: este leitor AINDA NÃO FOI VALIDADO COM O ARQUIVO REAL. O domínio seeg.eco.br estava
bloqueado (403 no proxy) no ambiente em que o módulo foi escrito; o código segue o formato
documentado nas instruções e foi testado só com dados sintéticos (tests/test_externos_seeg.py).
Hipóteses sobre o arquivo real:
- a linha de cabeçalho está entre as 20 primeiras linhas da aba e contém as células 'Gás' e
  'Estado' (comparação sem acento/maiúsculas/espaços; ver `ALIASES_COLUNAS`);
- o cabeçalho de cada ano pode ser int (2019), float (2019.0) ou texto ('2019');
- os valores são números (t CO2e); células vazias contam como 0 (e são contadas); texto numérico
  ('1.234,5' ou '1234.5') é aceito;
- o combustível de cada linha de geração está em uma de 'Produto ou sistema', 'Detalhamento',
  'Atividade geral' ou 'Sub-categoria emissora' (a primeira, nessa ordem, que tiver nomes de
  combustíveis conhecidos — a coluna usada fica registrada);
- o estado vem como sigla ('RS') ou nome ('Rio Grande do Sul'); 'Não Alocado' (ou 'NA', ou vazio)
  significa emissão sem estado;
- não há linhas de subtotal na aba (cada linha é uma combinação única de atributos).
Também é aceito um CSV com o mesmo layout (encoding utf-8-sig/utf-8/latin-1 detectado, separador
';' por padrão, decimal vírgula) — útil se o SEEG for exportado em texto.
"""
from __future__ import annotations

import codecs
import functools
import math
import numbers
import re
import sys
import time
import unicodedata
import warnings
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------------
# Constantes do método (Seção 5.7 das instruções da Rodada 02)
# --------------------------------------------------------------------------------------------
GAS_CO2E = "CO2e (t) GWP-AR5"
CATEGORIA_GERACAO = "Geração de eletricidade (serviço público)"
CATEGORIA_SF6 = "Uso de SF6 em equipamentos elétricos"
ANO_PADRAO = 2019

GRUPO_GERACAO = "geracao"
GRUPO_SF6 = "sf6"
COLUNA_VALOR = "valor_t_co2e"
COLUNA_GRUPO = "grupo"

REGIAO_RS = "RS"
REGIAO_RB = "RB"
REGIAO_NAO_ALOCADO = "Não alocado"
REGIOES = (REGIAO_RS, REGIAO_RB, REGIAO_NAO_ALOCADO)

CAR, GN, PET, BIO = "S38_CAR", "S38_GN", "S38_PET", "S38_BIO"
SUBSETORES_EMISSORES = (CAR, GN, PET, BIO)

SEM_COMBUSTIVEL = "(sem combustível)"

# Colunas de texto da aba 'Dados' (nomes canônicos, como documentados) e variações aceitas.
# A comparação é feita sem acento, sem maiúsculas e só com letras e dígitos.
COLUNAS_TEXTO: tuple[str, ...] = (
    "Emissão/Remoção/Bunker",
    "Gás",
    "Setor de emissão",
    "Categoria emissora",
    "Sub-categoria emissora",
    "Produto ou sistema",
    "Detalhamento",
    "Recorte",
    "Atividade geral",
    "Estado",
    "Bioma",
)
ALIASES_COLUNAS: dict[str, tuple[str, ...]] = {
    "Emissão/Remoção/Bunker": ("Emissão/Remoção/Bunker", "Emissão/Remoção/Bunkers", "Emissão/Remoção"),
    "Gás": ("Gás", "Gases"),
    "Setor de emissão": ("Setor de emissão", "Setor emissor", "Setor"),
    "Categoria emissora": ("Categoria emissora", "Categoria"),
    "Sub-categoria emissora": ("Sub-categoria emissora", "Sub-categoria", "Subcategoria"),
    "Produto ou sistema": ("Produto ou sistema", "Produto/sistema", "Produto"),
    "Detalhamento": ("Detalhamento",),
    "Recorte": ("Recorte",),
    "Atividade geral": ("Atividade geral",),
    "Estado": ("Estado", "UF", "Estado (UF)"),
    "Bioma": ("Bioma",),
}
COLUNAS_OBRIGATORIAS: tuple[str, ...] = ("Gás", "Categoria emissora", "Estado")

# Ordem de busca da coluna que traz o combustível (instruções da tarefa).
COLUNAS_CANDIDATAS_COMBUSTIVEL: tuple[str, ...] = (
    "Produto ou sistema",
    "Detalhamento",
    "Atividade geral",
    "Sub-categoria emissora",
)

# Combustível (nome do SEEG, Seção 5.7) → subsetor. A ordem define a ordem das colunas das tabelas.
COMBUSTIVEIS_SUBSETOR: tuple[tuple[str, str], ...] = (
    ("Carvão mineral", CAR),
    ("Alcatrão", CAR),
    ("Gás natural seco", GN),
    ("Gás natural úmido", GN),
    ("Diesel de petróleo", PET),
    ("Óleo combustível", PET),
    ("Gás de refinaria", PET),
    ("Outros energéticos de petróleo", PET),
    ("Biodiesel", BIO),
    ("Biogás", BIO),
    ("Lenha", BIO),
    ("Outras biomassas", BIO),
)
# Variações de grafia aceitas (mesmo combustível, mesmo subsetor). Nada além disso é mapeado:
# o que não casar aparece em 'nao_mapeados' para decisão explícita.
VARIANTES_COMBUSTIVEL: dict[str, str] = {
    # rótulo do SEEG 13.0 (conferido no arquivo real, Rodada 02b): "Carvão mineral sem especificação"
    "carvao mineral sem especificacao": "Carvão mineral",
    "gas natural": "Gás natural seco",  # rótulo genérico → GN
    "oleo diesel": "Diesel de petróleo",
    "outros energeticos do petroleo": "Outros energéticos de petróleo",
    "outra biomassa": "Outras biomassas",
}

# --------------------------------------------------------------------------------------------
# Valores de referência das instruções da Rodada 02, Seção 5.7 (mil t CO2e, 2019; tolerância 0.5).
# Usados APENAS para comparação (comparar_com_referencia), nunca como dado.
# 'Carvão' = combustíveis de S38_CAR; 'Gás natural' = de S38_GN; 'Outros' = Total menos
# (Carvão + Gás natural + Diesel + Óleo combustível).
# --------------------------------------------------------------------------------------------
TOLERANCIA_REFERENCIA = 0.5
REFERENCIA_MIL_T: tuple[tuple[str, str, float, str], ...] = (
    # (região, item, valor, observação)
    (REGIAO_RS, "Carvão", 3749.6, ""),
    (REGIAO_RS, "Gás natural", 75.1, ""),
    (REGIAO_RS, "Diesel", 8.6, ""),
    (REGIAO_RS, "Óleo combustível", 9.2, ""),
    (REGIAO_RS, "Outros", 0.0, ""),
    (REGIAO_RS, "Total", 3842.5, ""),
    (REGIAO_RS, "Petróleo (PET) realocado", 17.8, "diesel + óleo combustível do RS, vão para CAR e GN"),
    (REGIAO_RB, "Carvão", 9708.2, ""),
    (REGIAO_RB, "Gás natural", 20513.0, ""),
    (REGIAO_RB, "Diesel", 3102.8, ""),
    (REGIAO_RB, "Óleo combustível", 855.8, ""),
    (REGIAO_RB, "Outros", 1.2, "na referência, só biodiesel"),
    (REGIAO_RB, "Biodiesel", 1.2, ""),
    (REGIAO_RB, "Total", 34181.0, ""),
    (REGIAO_NAO_ALOCADO, "Gás de refinaria", 333.0, ""),
    (REGIAO_NAO_ALOCADO, "Lenha", 6.5, ""),
    (REGIAO_NAO_ALOCADO, "Outras biomassas", 4.0, ""),
    (REGIAO_NAO_ALOCADO, "Biogás", 0.5, ""),
    (REGIAO_NAO_ALOCADO, "Total", 344.0, ""),
    ("Nacional", "SF6 em equipamentos elétricos", 323.1, "valor nacional, rateado no motor"),
)

# Unidades da Federação (sigla → nome), para reconhecer o Estado como sigla ou nome e apontar
# valores que não são UF (ex.: um eventual total 'Brasil', que causaria dupla contagem).
UFS: dict[str, str] = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará",
    "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
    "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}
_TEXTOS_NAO_ALOCADO = {"", "nao alocado", "nao alocada", "nao alocados", "na", "n a"}

_LINHAS_BUSCA_CABECALHO = 20
_PROGRESSO_PADRAO = 200_000


# --------------------------------------------------------------------------------------------
# Normalização de textos e nomes de colunas
# --------------------------------------------------------------------------------------------
def _vazio(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    if v is pd.NA or v is pd.NaT:
        return True
    return isinstance(v, str) and not v.strip()


@functools.lru_cache(maxsize=65536)
def _norm_str(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return s.strip()


def _norm(v) -> str:
    """Texto normalizado: minúsculas, sem acento, pontuação → espaço, espaços colapsados."""
    if _vazio(v):
        return ""
    return _norm_str(v if isinstance(v, str) else str(v))


def _chave_coluna(nome) -> str:
    """Chave de comparação de nome de coluna: só letras e dígitos ('Sub-categoria' ≡ 'subcategoria')."""
    return _norm(nome).replace(" ", "")


def _texto_limpo(v):
    """Texto sem espaços nas pontas e com espaços internos colapsados; vazio → None."""
    if _vazio(v):
        return None
    if isinstance(v, str):
        return re.sub(r"\s+", " ", v).strip()
    return v


_CHAVES_ALIAS = {
    canonico: {_chave_coluna(a) for a in (canonico,) + aliases} for canonico, aliases in ALIASES_COLUNAS.items()
}


def _mapear_colunas(nomes: Iterable) -> dict[str, int]:
    """Nome canônico → posição da coluna. Colunas ausentes ficam de fora.

    Primeiro procura o nome canônico (sem acento/maiúsculas/pontuação); só depois as variações
    de `ALIASES_COLUNAS`. Cada coluna do arquivo é usada no máximo uma vez.
    """
    chaves = [_chave_coluna(n) for n in nomes]
    mapa: dict[str, int] = {}
    for rodada in ("canonico", "alias"):
        for canonico in COLUNAS_TEXTO:
            if canonico in mapa:
                continue
            aceitas = {_chave_coluna(canonico)} if rodada == "canonico" else _CHAVES_ALIAS[canonico]
            for i, ch in enumerate(chaves):
                if ch and ch in aceitas and i not in mapa.values():
                    mapa[canonico] = i
                    break
    return mapa


def _erro_colunas(faltando: list[str], disponiveis: Iterable) -> ValueError:
    disp = [str(c) for c in disponiveis if not _vazio(c)]
    return ValueError(
        f"SEEG: coluna(s) obrigatória(s) ausente(s): {faltando}. Colunas disponíveis: {disp}"
    )


def _ano_do_cabecalho(v) -> int | None:
    """Cabeçalho de ano: 2019, 2019.0 ou '2019' → 2019; outra coisa → None."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, numbers.Integral):
        ano = int(v)
    elif isinstance(v, numbers.Real):
        if math.isnan(float(v)) or float(v) != int(v):
            return None
        ano = int(v)
    elif isinstance(v, str):
        m = re.fullmatch(r"\s*(\d{4})(?:\.0+)?\s*", v)
        if not m:
            return None
        ano = int(m.group(1))
    else:
        return None
    return ano if 1900 <= ano <= 2100 else None


def _coluna_do_ano(nomes: list, ano: int) -> int:
    for i, n in enumerate(nomes):
        if _ano_do_cabecalho(n) == ano:
            return i
    anos = sorted({a for a in (_ano_do_cabecalho(n) for n in nomes) if a is not None})
    faixa = f"{anos[0]}–{anos[-1]}" if anos else "nenhum"
    raise ValueError(f"SEEG: coluna do ano {ano} não encontrada no cabeçalho (anos encontrados: {faixa}).")


def _e_cabecalho(celulas: Iterable) -> bool:
    chaves = {_chave_coluna(c) for c in celulas if not _vazio(c)}
    return bool(chaves & _CHAVES_ALIAS["Gás"]) and bool(chaves & _CHAVES_ALIAS["Estado"])


# --------------------------------------------------------------------------------------------
# Valores numéricos
# --------------------------------------------------------------------------------------------
_TEXTOS_VAZIOS = {"", "-", "--", "nan", "na", "n a", "none", "null"}


def _parse_valor(v, decimal: str | None = None) -> float | None:
    """Converte uma célula de valor em float; vazia → None.

    `decimal`: ',' (texto com decimal vírgula; ponto é milhar), '.' (decimal ponto; vírgula é
    milhar) ou None (automático: só vírgula → decimal vírgula; só ponto → decimal ponto; os dois
    → o último é o decimal). Números (int/float) passam direto.
    """
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, numbers.Real):
        f = float(v)
        return None if math.isnan(f) else f
    if v is pd.NA:
        return None
    s = str(v).strip().replace(" ", "").replace(" ", "")
    if s.lower() in _TEXTOS_VAZIOS:
        return None
    dec = decimal
    if dec is None:
        if "," in s and "." in s:
            dec = "," if s.rfind(",") > s.rfind(".") else "."
        else:
            dec = "," if "," in s else "."
    if dec == ",":
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"SEEG: valor não numérico na coluna do ano: {v!r}") from None


# --------------------------------------------------------------------------------------------
# Filtro de linhas
# --------------------------------------------------------------------------------------------
_GAS_ALVO = _norm(GAS_CO2E)
_RE_GERACAO = re.compile(r"geracao de (?:eletricidade|energia eletrica) servico publico")
_SF6_ALVO = _norm(CATEGORIA_SF6)
_RE_SF6 = re.compile(r"\bsf6\b")
_RE_EQUIP_ELETRICO = re.compile(r"\bequipamentos? eletricos?\b")


def _e_sf6(n: str) -> bool:
    return n == _SF6_ALVO or bool(_RE_SF6.search(n) and _RE_EQUIP_ELETRICO.search(n))


def _grupo_da_linha(gas, categoria, subcategoria) -> str | None:
    """'geracao', 'sf6' ou None (linha fora do filtro). Só aceita o gás 'CO2e (t) GWP-AR5'."""
    if _norm(gas) != _GAS_ALVO:
        return None
    cat = _norm(categoria)
    if _RE_GERACAO.fullmatch(cat):
        return GRUPO_GERACAO
    if _e_sf6(cat) or _e_sf6(_norm(subcategoria)):
        return GRUPO_SF6
    return None


_UF_POR_CHAVE = {_norm(s): s for s in UFS} | {_norm(n): s for s, n in UFS.items()}


def uf_do_estado(estado) -> str | None:
    """Sigla da UF a partir de sigla ou nome ('rio grande do sul' → 'RS'); não reconhecido → None."""
    return _UF_POR_CHAVE.get(_norm(estado))


def regiao_do_estado(estado) -> str:
    """'RS'/'Rio Grande do Sul' → 'RS'; 'Não Alocado' (ou 'NA', ou vazio) → 'Não alocado'; demais → 'RB'.

    Valores que não são UF nem 'Não Alocado' também vão para 'RB'; `emissoes_por_regiao` os lista
    em 'estados_nao_reconhecidos' e emite aviso.
    """
    n = _norm(estado)
    if n in _TEXTOS_NAO_ALOCADO:
        return REGIAO_NAO_ALOCADO
    return REGIAO_RS if uf_do_estado(estado) == "RS" else REGIAO_RB


def _montar_saida(registros: list[list], ano: int, n_lidas: int, n_vazios: int, ausentes: list[str]) -> pd.DataFrame:
    df = pd.DataFrame(registros, columns=list(COLUNAS_TEXTO) + [COLUNA_VALOR, COLUNA_GRUPO])
    df[COLUNA_VALOR] = df[COLUNA_VALOR].astype(float)
    df.attrs.update(
        {
            "ano": ano,
            "n_linhas_lidas": n_lidas,
            "n_linhas_selecionadas": len(df),
            "n_valores_vazios": n_vazios,  # células vazias no ano, somadas como 0
            "colunas_ausentes": ausentes,
        }
    )
    return df


def filtrar_seeg(df_bruto: pd.DataFrame, ano: int = ANO_PADRAO, decimal: str | None = None) -> pd.DataFrame:
    """Aplica os filtros da Seção 5.7 a um DataFrame já carregado (cabeçalho = linha de títulos da aba).

    Devolve o mesmo formato de `ler_seeg_filtrado`: as 11 colunas de texto (nomes canônicos;
    colunas ausentes no arquivo ficam com None), 'valor_t_co2e' (do `ano`; vazio → 0) e 'grupo'
    ('geracao' ou 'sf6'). Em `attrs`: ano, linhas lidas/selecionadas, valores vazios e colunas ausentes.
    """
    nomes = list(df_bruto.columns)
    mapa = _mapear_colunas(nomes)
    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in mapa]
    if faltando:
        raise _erro_colunas(faltando, nomes)
    i_ano = _coluna_do_ano(nomes, ano)

    def col(canonico: str) -> pd.Series:
        if canonico in mapa:
            return df_bruto.iloc[:, mapa[canonico]]
        return pd.Series([None] * len(df_bruto), index=df_bruto.index, dtype=object)

    gas, cat, sub = col("Gás"), col("Categoria emissora"), col("Sub-categoria emissora")
    grupos = [_grupo_da_linha(g, c, s) for g, c, s in zip(gas, cat, sub)]
    sel = np.array([g is not None for g in grupos], dtype=bool)

    registros: list[list] = []
    n_vazios = 0
    valores = df_bruto.iloc[:, i_ano]
    textos = {c: col(c) for c in COLUNAS_TEXTO}
    for pos in np.flatnonzero(sel):
        v = _parse_valor(valores.iloc[pos], decimal)
        if v is None:
            n_vazios += 1
            v = 0.0
        registros.append([_texto_limpo(textos[c].iloc[pos]) for c in COLUNAS_TEXTO] + [v, grupos[pos]])
    ausentes = [c for c in COLUNAS_TEXTO if c not in mapa]
    return _montar_saida(registros, ano, len(df_bruto), n_vazios, ausentes)


# --------------------------------------------------------------------------------------------
# Leitura em modo streaming (xlsx) ou em blocos (csv)
# --------------------------------------------------------------------------------------------
def _escolher_aba(nomes: list[str], aba: str) -> str:
    if aba in nomes:
        return aba
    alvo = _chave_coluna(aba)
    for n in nomes:
        if _chave_coluna(n) == alvo:
            return n
    raise ValueError(f"SEEG: aba {aba!r} não encontrada. Abas disponíveis: {nomes}")


def _intervalo_progresso(progresso: bool | int) -> int | None:
    if progresso is True:
        return _PROGRESSO_PADRAO
    if not progresso:
        return None
    return int(progresso)


def _avisar_progresso(n_lidas: int, n_sel: int, t0: float) -> None:
    print(f"SEEG: {n_lidas:,} linhas lidas, {n_sel:,} selecionadas ({time.time() - t0:.0f} s)",
          file=sys.stderr, flush=True)


def _ler_xlsx_filtrado(caminho: Path, ano: int, aba: str, progresso: bool | int) -> pd.DataFrame:
    import openpyxl  # importação local: só necessária para xlsx

    intervalo = _intervalo_progresso(progresso)
    t0 = time.time()
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    try:
        ws = wb[_escolher_aba(wb.sheetnames, aba)]
        # As dimensões gravadas no arquivo podem estar erradas; sem elas, cada linha vem com o
        # tamanho real (tratado abaixo com acesso seguro por índice).
        ws.reset_dimensions()
        linhas = ws.iter_rows(values_only=True)

        cabecalho = None
        primeiras = []
        for _ in range(_LINHAS_BUSCA_CABECALHO):
            linha = next(linhas, None)
            if linha is None:
                break
            primeiras.append(linha)
            if _e_cabecalho(linha):
                cabecalho = list(linha)
                break
        if cabecalho is None:
            raise ValueError(
                f"SEEG: linha de cabeçalho (com 'Gás' e 'Estado') não encontrada nas primeiras "
                f"{_LINHAS_BUSCA_CABECALHO} linhas da aba {ws.title!r}. Primeiras linhas: "
                f"{[[c for c in l if c is not None][:6] for l in primeiras[:5]]}"
            )
        mapa = _mapear_colunas(cabecalho)
        faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in mapa]
        if faltando:
            raise _erro_colunas(faltando, cabecalho)
        i_ano = _coluna_do_ano(cabecalho, ano)
        i_gas, i_cat = mapa["Gás"], mapa["Categoria emissora"]
        i_sub = mapa.get("Sub-categoria emissora")
        idx_textos = [mapa.get(c) for c in COLUNAS_TEXTO]

        cache_gas: dict = {}
        registros: list[list] = []
        n_lidas = n_vazios = 0
        for linha in linhas:
            n_lidas += 1
            if intervalo and n_lidas % intervalo == 0:
                _avisar_progresso(n_lidas, len(registros), t0)
            n = len(linha)
            gas = linha[i_gas] if i_gas < n else None
            ok = cache_gas.get(gas)
            if ok is None:
                ok = cache_gas[gas] = _norm(gas) == _GAS_ALVO
            if not ok:
                continue
            cat = linha[i_cat] if i_cat < n else None
            sub = linha[i_sub] if i_sub is not None and i_sub < n else None
            grupo = _grupo_da_linha(gas, cat, sub)
            if grupo is None:
                continue
            v = _parse_valor(linha[i_ano] if i_ano < n else None)
            if v is None:
                n_vazios += 1
                v = 0.0
            textos = [_texto_limpo(linha[i]) if i is not None and i < n else None for i in idx_textos]
            registros.append(textos + [v, grupo])
    finally:
        wb.close()
    if intervalo:
        _avisar_progresso(n_lidas, len(registros), t0)
    ausentes = [c for c in COLUNAS_TEXTO if c not in mapa]
    return _montar_saida(registros, ano, n_lidas, n_vazios, ausentes)


def _detectar_encoding(amostra: bytes) -> str:
    if amostra.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    try:
        codecs.getincrementaldecoder("utf-8")().decode(amostra, final=False)
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def _ler_csv_filtrado(caminho: Path, ano: int, progresso: bool | int, decimal: str) -> pd.DataFrame:
    with open(caminho, "rb") as f:
        amostra = f.read(1 << 20)
    encoding = _detectar_encoding(amostra)
    texto = codecs.getincrementaldecoder(encoding)(errors="replace").decode(amostra, final=False)
    linhas_txt = [l.rstrip("\r") for l in texto.split("\n")[:_LINHAS_BUSCA_CABECALHO]]
    i_cab = sep = None
    for i, l in enumerate(linhas_txt):
        for s in (";", "\t", "|", ","):
            if s in l and _e_cabecalho(l.split(s)):
                i_cab, sep = i, s
                break
        if i_cab is not None:
            break
    if i_cab is None:
        raise ValueError(
            f"SEEG: linha de cabeçalho (com 'Gás' e 'Estado') não encontrada nas primeiras "
            f"{_LINHAS_BUSCA_CABECALHO} linhas de {caminho.name}."
        )
    intervalo = _intervalo_progresso(progresso)
    t0 = time.time()
    partes, n_lidas, n_vazios, ausentes = [], 0, 0, []
    leitor = pd.read_csv(
        caminho, sep=sep, encoding=encoding, skiprows=i_cab, header=0, dtype=str,
        keep_default_na=False, chunksize=_PROGRESSO_PADRAO,
    )
    for bloco in leitor:
        parte = filtrar_seeg(bloco, ano=ano, decimal=decimal)
        n_lidas += parte.attrs["n_linhas_lidas"]
        n_vazios += parte.attrs["n_valores_vazios"]
        ausentes = parte.attrs["colunas_ausentes"]
        partes.append(parte)
        if intervalo:
            _avisar_progresso(n_lidas, sum(len(p) for p in partes), t0)
    df = pd.concat(partes, ignore_index=True) if partes else _montar_saida([], ano, 0, 0, [])
    out = _montar_saida(df.values.tolist(), ano, n_lidas, n_vazios, ausentes)
    out.attrs.update({"encoding": encoding, "separador": sep})
    return out


def ler_seeg_filtrado(
    caminho_xlsx: str | Path,
    ano: int = ANO_PADRAO,
    aba: str = "Dados",
    progresso: bool | int = False,
    decimal_csv: str = ",",
) -> pd.DataFrame:
    """Lê o SEEG (xlsx em modo streaming) e guarda só as linhas dos dois filtros da Seção 5.7.

    - xlsx: `openpyxl.load_workbook(read_only=True, data_only=True)` + `iter_rows(values_only=True)`;
      o cabeçalho é procurado nas 20 primeiras linhas (linha com 'Gás' e 'Estado');
    - csv/txt (mesmo layout): encoding detectado, separador detectado no cabeçalho (';' em geral),
      decimal `decimal_csv` (vírgula por padrão), lido em blocos.

    Devolve DataFrame com as 11 colunas de texto (nomes canônicos), 'valor_t_co2e' (t CO2e no
    `ano`; células vazias somadas como 0) e 'grupo' ('geracao' ou 'sf6'). Em `attrs`: ano,
    n_linhas_lidas, n_linhas_selecionadas, n_valores_vazios, colunas_ausentes.
    `progresso`: True (a cada 200 mil linhas) ou um inteiro (intervalo); mensagens em stderr.
    """
    caminho = Path(caminho_xlsx)
    if caminho.suffix.lower() in (".csv", ".txt"):
        return _ler_csv_filtrado(caminho, ano, progresso, decimal_csv)
    return _ler_xlsx_filtrado(caminho, ano, aba, progresso)


# --------------------------------------------------------------------------------------------
# Combustíveis
# --------------------------------------------------------------------------------------------
_COMBUSTIVEL_POR_CHAVE: dict[str, str] = {_norm(nome): nome for nome, _ in COMBUSTIVEIS_SUBSETOR}
_COMBUSTIVEL_POR_CHAVE.update({k: v for k, v in VARIANTES_COMBUSTIVEL.items()})
_SUBSETOR_POR_NOME = dict(COMBUSTIVEIS_SUBSETOR)
_ORDEM_COMBUSTIVEL = {nome: i for i, (nome, _) in enumerate(COMBUSTIVEIS_SUBSETOR)}


def _combustivel_canonico(nome) -> str | None:
    """Nome canônico (Seção 5.7) do combustível, ou None se não for um combustível conhecido."""
    return _COMBUSTIVEL_POR_CHAVE.get(_norm(nome))


def mapear_combustivel(nome) -> str | None:
    """Combustível do SEEG → subsetor ('S38_CAR', 'S38_GN', 'S38_PET', 'S38_BIO') ou None.

    Comparação sem acento, sem maiúsculas e com espaços normalizados; só nomes exatos da Seção 5.7
    (e as variações de `VARIANTES_COMBUSTIVEL`). Ex.: 'CARVÃO MINERAL' → 'S38_CAR';
    'Carvão vegetal' → None.
    """
    canonico = _combustivel_canonico(nome)
    return _SUBSETOR_POR_NOME[canonico] if canonico else None


def _resolver_coluna_df(df: pd.DataFrame, canonico: str) -> str | None:
    if canonico in df.columns:
        return canonico
    aceitas = _CHAVES_ALIAS.get(canonico, {_chave_coluna(canonico)})
    for c in df.columns:
        if _chave_coluna(c) in aceitas:
            return c
    return None


def _mascara_geracao(df: pd.DataFrame) -> pd.Series:
    if COLUNA_GRUPO in df.columns:
        return df[COLUNA_GRUPO].map(lambda g: _norm(g) == GRUPO_GERACAO).astype(bool)
    return pd.Series(True, index=df.index)


def identificar_combustivel(df: pd.DataFrame) -> pd.Series:
    """Combustível de cada linha de geração (Series 'combustivel', alinhada a `df`).

    Procura, nesta ordem, em 'Produto ou sistema', 'Detalhamento', 'Atividade geral' e
    'Sub-categoria emissora' a primeira coluna em que algum valor (nas linhas do grupo
    'geracao'; todas as linhas se não houver coluna 'grupo') seja um combustível conhecido.
    O valor original (sem espaços extras) é devolvido; linhas fora da geração ficam None.
    Em `attrs`: 'coluna_combustivel' (a coluna usada) e 'cobertura_por_coluna' (fração das linhas
    de geração com combustível reconhecido em cada coluna candidata — para auditoria).
    Levanta ValueError se há linhas de geração e nenhuma coluna candidata tem combustível conhecido.
    """
    mascara = _mascara_geracao(df)
    n_ger = int(mascara.sum())
    cobertura: dict[str, float] = {}
    escolhida = None
    for canonico in COLUNAS_CANDIDATAS_COMBUSTIVEL:
        c = _resolver_coluna_df(df, canonico)
        if c is None:
            continue
        reconhecidos = df.loc[mascara, c].map(lambda v: _combustivel_canonico(v) is not None)
        cobertura[canonico] = float(reconhecidos.mean()) if n_ger else 0.0
        if escolhida is None and bool(reconhecidos.any()):
            escolhida = c
    saida = pd.Series([None] * len(df), index=df.index, dtype=object, name="combustivel")
    if n_ger and escolhida is None:
        exemplos = {
            c: df.loc[mascara, c].dropna().astype(str).unique()[:5].tolist()
            for c in (_resolver_coluna_df(df, k) for k in COLUNAS_CANDIDATAS_COMBUSTIVEL) if c is not None
        }
        raise ValueError(
            "SEEG: nenhuma coluna candidata traz nomes de combustíveis conhecidos nas linhas de geração. "
            f"Exemplos de valores: {exemplos}"
        )
    if escolhida is not None:
        saida.loc[mascara] = df.loc[mascara, escolhida].map(_texto_limpo)
    saida.attrs["coluna_combustivel"] = escolhida
    saida.attrs["cobertura_por_coluna"] = cobertura
    return saida


# --------------------------------------------------------------------------------------------
# Agregações
# --------------------------------------------------------------------------------------------
def _preparar(df_filtrado: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    """Cópia com colunas auxiliares: _valor, _grupo, _regiao, _combustivel, _rotulo, _subsetor."""
    if COLUNA_VALOR not in df_filtrado.columns:
        raise _erro_colunas([COLUNA_VALOR], df_filtrado.columns)
    col_estado = _resolver_coluna_df(df_filtrado, "Estado")
    if col_estado is None:
        raise _erro_colunas(["Estado"], df_filtrado.columns)
    df = df_filtrado.copy()
    if COLUNA_GRUPO not in df.columns:
        cols = {k: _resolver_coluna_df(df, k) for k in ("Gás", "Categoria emissora", "Sub-categoria emissora")}
        faltando = [k for k in ("Gás", "Categoria emissora") if cols[k] is None]
        if faltando:
            raise _erro_colunas(faltando + [COLUNA_GRUPO], df.columns)
        sub = df[cols["Sub-categoria emissora"]] if cols["Sub-categoria emissora"] else [None] * len(df)
        df[COLUNA_GRUPO] = [_grupo_da_linha(g, c, s) for g, c, s in zip(df[cols["Gás"]], df[cols["Categoria emissora"]], sub)]
        df = df[df[COLUNA_GRUPO].notna()].copy()
    df["_grupo"] = df[COLUNA_GRUPO].map(_norm)
    df["_valor"] = [0.0 if (x := _parse_valor(v)) is None else x for v in df[COLUNA_VALOR]]
    df["_regiao"] = df[col_estado].map(regiao_do_estado)
    comb = identificar_combustivel(df)
    df["_combustivel"] = comb
    # Rótulo de coluna: o primeiro nome original visto para cada combustível (sem acento/maiúsculas).
    rotulos: dict[str, str] = {}
    for v in df.loc[df["_grupo"] == GRUPO_GERACAO, "_combustivel"]:
        chave = _norm(v)
        rotulos.setdefault(chave, v if chave else SEM_COMBUSTIVEL)
    df["_rotulo"] = df["_combustivel"].map(lambda v: rotulos.get(_norm(v)))
    df["_subsetor"] = df["_combustivel"].map(mapear_combustivel)
    return df, comb.attrs.get("coluna_combustivel")


def _ordem_rotulo(rotulo: str) -> tuple:
    canonico = _combustivel_canonico(rotulo)
    if canonico is None:
        return (1, 0, _norm(rotulo))
    return (0, _ORDEM_COMBUSTIVEL[canonico], "")


def emissoes_por_regiao(df_filtrado: pd.DataFrame) -> dict:
    """Emissões da geração (serviço público) por região × combustível e SF6 nacional.

    Devolve dict com:
    - 'por_combustivel': DataFrame (mil t CO2e), linhas 'RS', 'RB', 'Não alocado' e uma coluna
      por combustível (nome original do SEEG, na ordem da Seção 5.7; não mapeados no fim);
    - 'sf6_nacional_mil_t': soma nacional das linhas de SF6 (mil t CO2e);
    - 'nao_mapeados': {combustível: mil t} dos combustíveis sem subsetor e com valor ≠ 0;
    - 'coluna_combustivel': coluna de onde saiu o combustível;
    - 'subsetor_por_combustivel': {combustível: subsetor ou None};
    - 'estados_por_regiao': {região: valores originais da coluna Estado} (auditoria);
    - 'estados_nao_reconhecidos': valores de Estado que não são UF nem 'Não Alocado' (contados no
      RB, com aviso — podem indicar um total 'Brasil' e dupla contagem);
    - 'n_linhas': {'geracao': n, 'sf6': n}.
    """
    df, coluna = _preparar(df_filtrado)
    ger = df[df["_grupo"] == GRUPO_GERACAO]
    sf6 = df[df["_grupo"] == GRUPO_SF6]

    tab = ger.groupby(["_regiao", "_rotulo"], sort=False)["_valor"].sum().unstack("_rotulo") if len(ger) else pd.DataFrame()
    colunas = sorted(tab.columns, key=_ordem_rotulo) if len(tab.columns) else []
    tab = (tab.reindex(index=list(REGIOES), columns=colunas).fillna(0.0) / 1000.0).astype(float)
    tab.index.name = "regiao"
    tab.columns.name = "combustivel"

    subsetor = {r: mapear_combustivel(r) for r in colunas}
    nao_mapeados = {r: float(tab[r].sum()) for r in colunas if subsetor[r] is None and tab[r].abs().sum() > 0}
    col_estado = _resolver_coluna_df(df, "Estado")
    estados = {
        reg: sorted({str(e) for e in ger.loc[ger["_regiao"] == reg, col_estado].map(_texto_limpo) if e is not None})
        for reg in REGIOES
    }
    nao_reconhecidos = sorted(
        {str(e) for e in df[col_estado].map(_texto_limpo) if e is not None
         and uf_do_estado(e) is None and _norm(e) not in _TEXTOS_NAO_ALOCADO}
    )
    if nao_reconhecidos:
        warnings.warn(
            f"SEEG: valores de Estado que não são UF nem 'Não Alocado' (contados no RB): {nao_reconhecidos}",
            UserWarning, stacklevel=2,
        )
    return {
        "por_combustivel": tab,
        "sf6_nacional_mil_t": float(sf6["_valor"].sum()) / 1000.0,
        "nao_mapeados": nao_mapeados,
        "coluna_combustivel": coluna,
        "subsetor_por_combustivel": subsetor,
        "estados_por_regiao": estados,
        "estados_nao_reconhecidos": nao_reconhecidos,
        "n_linhas": {GRUPO_GERACAO: int(len(ger)), GRUPO_SF6: int(len(sf6))},
    }


def _gwh(gwh_rs: dict, subsetor: str) -> float:
    curto = subsetor.replace("S38_", "")
    for k, v in gwh_rs.items():
        if str(k).strip().upper() in (subsetor, curto):
            f = float(v)
            if not math.isfinite(f) or f < 0:
                raise ValueError(f"SEEG: GWh inválido para {subsetor} no RS: {v!r}")
            return f
    raise ValueError(f"SEEG: gwh_rs precisa da chave {subsetor!r}; recebido: {list(gwh_rs)}")


def emissoes_por_subsetor(df_filtrado: pd.DataFrame, gwh_rs: dict) -> pd.DataFrame:
    """Emissões da geração por região (RS, RB) × subsetor (t CO2e), com as regras da Seção 5.7.

    - 'Não alocado' → RB;
    - PET do RS (diesel, óleo combustível e demais PET) → S38_CAR e S38_GN do RS, na proporção
      de `gwh_rs = {'S38_CAR': GWh, 'S38_GN': GWh}` (o PET-RS fica 0);
    - SF6 não entra (o rateio é feito no motor);
    - combustíveis sem mapeamento ficam de fora, com aviso (UserWarning) e registro em `attrs`.
    Em `attrs`: 'pet_rs_realocado_t', 'realocacao_pet_rs_t' ({subsetor: t}), 'nao_alocado_para_rb_t',
    'nao_mapeados_t' ({combustível: t}), 'coluna_combustivel', 'gwh_rs'.
    """
    gwh_car, gwh_gn = _gwh(gwh_rs, CAR), _gwh(gwh_rs, GN)
    df, coluna = _preparar(df_filtrado)
    ger = df[df["_grupo"] == GRUPO_GERACAO].copy()

    sem_mapa = ger[ger["_subsetor"].isna()]
    nao_mapeados = {
        str(k): float(v) for k, v in sem_mapa.groupby("_rotulo")["_valor"].sum().items() if v != 0
    }
    if nao_mapeados:
        warnings.warn(
            f"SEEG: combustíveis sem mapeamento ficaram fora da tabela por subsetor (t CO2e): {nao_mapeados}",
            UserWarning, stacklevel=2,
        )
    ger = ger[ger["_subsetor"].notna()]
    nao_alocado_t = float(ger.loc[ger["_regiao"] == REGIAO_NAO_ALOCADO, "_valor"].sum())
    ger["_regiao_mip"] = ger["_regiao"].where(ger["_regiao"] == REGIAO_RS, REGIAO_RB)

    tab = ger.groupby(["_regiao_mip", "_subsetor"])["_valor"].sum().unstack("_subsetor") if len(ger) else pd.DataFrame()
    tab = tab.reindex(index=[REGIAO_RS, REGIAO_RB], columns=list(SUBSETORES_EMISSORES)).fillna(0.0).astype(float)

    pet_rs = float(tab.loc[REGIAO_RS, PET])
    realocacao = {CAR: 0.0, GN: 0.0}
    if pet_rs != 0.0:
        soma = gwh_car + gwh_gn
        if soma <= 0:
            raise ValueError(
                f"SEEG: há {pet_rs:.1f} t CO2e de PET no RS para realocar, mas GWh(CAR) + GWh(GN) do RS = {soma}."
            )
        realocacao = {CAR: pet_rs * gwh_car / soma, GN: pet_rs * gwh_gn / soma}
        tab.loc[REGIAO_RS, CAR] += realocacao[CAR]
        tab.loc[REGIAO_RS, GN] += realocacao[GN]
        tab.loc[REGIAO_RS, PET] = 0.0

    tab.index.name = "regiao"
    tab.columns.name = "subsetor"
    tab.attrs.update(
        {
            "unidade": "t CO2e",
            "pet_rs_realocado_t": pet_rs,
            "realocacao_pet_rs_t": realocacao,
            "nao_alocado_para_rb_t": nao_alocado_t,
            "nao_mapeados_t": nao_mapeados,
            "coluna_combustivel": coluna,
            "gwh_rs": {CAR: gwh_car, GN: gwh_gn},
        }
    )
    return tab


# --------------------------------------------------------------------------------------------
# Comparação com a referência da Seção 5.7
# --------------------------------------------------------------------------------------------
_CHAVES_DIESEL = {_norm("Diesel de petróleo"), "oleo diesel"}
_CHAVES_OLEO = {_norm("Óleo combustível")}


def _soma(tab: pd.DataFrame, regiao: str, filtro) -> float:
    if regiao not in tab.index:
        return 0.0
    cols = [c for c in tab.columns if filtro(c)]
    return float(tab.loc[regiao, cols].sum()) if cols else 0.0


def _itens_obtidos(tab: pd.DataFrame, regiao: str) -> dict[str, float]:
    carvao = _soma(tab, regiao, lambda c: mapear_combustivel(c) == CAR)
    gas = _soma(tab, regiao, lambda c: mapear_combustivel(c) == GN)
    diesel = _soma(tab, regiao, lambda c: _norm(c) in _CHAVES_DIESEL)
    oleo = _soma(tab, regiao, lambda c: _norm(c) in _CHAVES_OLEO)
    total = _soma(tab, regiao, lambda c: True)
    itens = {
        "Carvão": carvao,
        "Gás natural": gas,
        "Diesel": diesel,
        "Óleo combustível": oleo,
        "Outros": total - (carvao + gas + diesel + oleo),
        "Total": total,
        "Petróleo (PET) realocado": _soma(tab, regiao, lambda c: mapear_combustivel(c) == PET),
    }
    for nome, _ in COMBUSTIVEIS_SUBSETOR:
        chave = _norm(nome)
        itens[nome] = _soma(tab, regiao, lambda c, k=chave: _norm(_combustivel_canonico(c) or c) == k)
    return itens


def comparar_com_referencia(resultado, tolerancia: float = TOLERANCIA_REFERENCIA) -> pd.DataFrame:
    """Compara o resultado de `emissoes_por_regiao` com a referência da Seção 5.7 (mil t CO2e).

    `resultado`: o dict de `emissoes_por_regiao` (ou só a tabela 'por_combustivel'; nesse caso o
    SF6 fica sem valor obtido). Devolve DataFrame com regiao, item, esperado_mil_t, obtido_mil_t,
    diferenca_mil_t (obtido − esperado), dentro_tolerancia e observacao.
    """
    if isinstance(resultado, dict):
        tab = resultado["por_combustivel"]
        sf6 = resultado.get("sf6_nacional_mil_t")
    elif isinstance(resultado, pd.DataFrame):
        tab, sf6 = resultado, None
    else:
        raise TypeError("comparar_com_referencia espera o dict de emissoes_por_regiao ou a tabela por_combustivel")

    obtidos = {r: _itens_obtidos(tab, r) for r in REGIOES}
    linhas = []
    for regiao, item, esperado, obs in REFERENCIA_MIL_T:
        if regiao == "Nacional":
            obtido = np.nan if sf6 is None else float(sf6)
        else:
            obtido = obtidos[regiao].get(item, np.nan)
        dif = obtido - esperado
        linhas.append(
            {
                "regiao": regiao,
                "item": item,
                "esperado_mil_t": esperado,
                "obtido_mil_t": obtido,
                "diferenca_mil_t": dif,
                "dentro_tolerancia": bool(np.isfinite(dif) and abs(dif) <= tolerancia + 1e-9),
                "observacao": obs,
            }
        )
    return pd.DataFrame(linhas)
