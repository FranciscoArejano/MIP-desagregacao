"""Emprego e salários do setor 35 (eletricidade e gás): IBGE, CEMPRE 2019 (Seção 5.8, Rodada 02).

Fonte
-----
IBGE, Cadastro Central de Empresas (CEMPRE) 2019, SIDRA tabela 6450, pela API de valores
(`URL_CEMPRE_SIDRA`). Variável 707 = pessoal ocupado total (pessoas); 662 = salários e outras
remunerações (R$ mil). Níveis: n1 = Brasil; n3/43 = Rio Grande do Sul. Classificação c12762 =
CNAE 2.0: divisão 35, grupos 35.1, 35.2 e 35.3 e as classes 35.11-5 (geração), 35.12-3
(transmissão), 35.13-1 (comércio atacadista de energia), 35.14-0 (distribuição), 35.20-4 (gás) e
35.30-1 (vapor e ar condicionado).

Uso (Seção 5.8 das instruções da Rodada 02)
-------------------------------------------
Só a composição (não o nível), para repartir as ocupações da base NEREUS e as remunerações da
MIP entre os subsetores do S38:

- 35.11-5 geração → `geracao` (todos os subsetores de geração; a repartição entre fontes, na
  proporção do VBP, é feita fora deste módulo);
- 35.12-3 transmissão → `S38_TRA`;
- 35.13-1 comércio atacadista de energia + 35.14-0 distribuição → `S38_DIS`;
- 35.20-4 gás + 35.30-1 vapor → `S38_GAS`.

Sigilo no RS (Seção 5.8): as classes sigilosas ("X") são obtidas por diferença:
35.1 − geração − distribuição = transmissão + comércio; 35 − 35.1 = gás + vapor. Cada soma é
repartida pela proporção nacional (Brasil) das duas classes, na mesma variável. Se só uma das
duas classes do par for sigilosa, ela é obtida diretamente pela diferença (sem proporção). O
RB é Brasil − RS, classe a classe e variável a variável. A coluna `metodo` registra a origem
de cada valor.

ATENÇÃO — leitor ainda NÃO validado com o arquivo real
------------------------------------------------------
Quando este módulo foi escrito, o proxy do ambiente devolvia 403 para *.gov.br, de modo que o
JSON do SIDRA não pôde ser baixado. O código foi escrito contra o formato documentado da API de
valores do SIDRA e testado só com dados sintéticos (`tests/test_externos_cempre.py`).
Hipóteses sobre o formato real, a conferir no primeiro uso:

- Lista JSON de dicionários; o primeiro elemento é o cabeçalho (chave → descrição: 'V' →
  'Valor', 'D1C' → 'Brasil (Código)', 'D2N' → 'Variável', 'D3N' → 'Ano', 'D4N' →
  'Classificação Nacional de Atividades Econômicas (CNAE 2.0)' etc.). As dimensões são
  identificadas pela descrição (sem acento, sem diferença de maiúsculas), não pela posição.
  Sem cabeçalho, são identificadas pelo conteúdo (códigos de variável, anos, códigos CNAE,
  nomes de territórios).
- A classe CNAE é identificada pelo NOME da categoria (que traz o código, ex.: '35.11-5
  Geração de energia elétrica'), nunca pelo código numérico do SIDRA (117297...). Aceitam-se
  '35.11-5', '35.115', '3511-5', '35115', '35.11' (dígito verificador completado por
  `DV_CLASSES`), o código depois de 'Classe'/'Divisão'/'Grupo' ou entre parênteses no fim.
- O território vem no nome (D?N: 'Brasil', 'Rio Grande do Sul') ou no código (D?C: '1', '43').
- 'V' é texto: número com ponto decimal; 'X' = sigiloso; '-' = zero absoluto; '..' e '...' =
  não se aplica / não disponível (NaN, sem marca de sigilo). Vírgula decimal também é aceita.
- A unidade dos salários é "Mil Reais" (campo 'Unidade de Medida'); outra unidade gera aviso.
- Também se aceita um CSV "longo" com as descrições do cabeçalho como nomes de coluna
  (separador ';' detectado, decimal vírgula) ou um DataFrame já carregado (ex.: sidrapy).
- O RS tem a divisão 35, o grupo 35.1 e as classes de geração e distribuição publicados
  (valores de referência da Seção 5.8); se isso mudar, o cálculo por diferença levanta
  ValueError dizendo o que falta.
"""
from __future__ import annotations

import io
import json
import math
import re
import unicodedata
import warnings
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------------
# Fonte e constantes de método
# --------------------------------------------------------------------------------------------
URL_CEMPRE_SIDRA = (
    "https://apisidra.ibge.gov.br/values/t/6450/n1/all/n3/43/v/707,662/p/2019/c12762/"
    "117297,117298,117299,117300,117301,117302,117303,117304,117305,117306"
)
TABELA_SIDRA = "6450"
ANO_BASE = 2019
FONTE_CEMPRE = (
    "IBGE, Cadastro Central de Empresas (CEMPRE) 2019, SIDRA tabela 6450, variáveis 707 "
    "(pessoal ocupado total) e 662 (salários e outras remunerações, R$ mil), CNAE 2.0 divisão 35"
)

ENCODINGS_CANDIDATOS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
SEPARADORES_CANDIDATOS = (";", "\t", ",", "|")

# Variáveis do SIDRA → nome padronizado
VARIAVEIS_SIDRA = {"707": "pessoal_ocupado", "662": "salarios_mil"}
VARIAVEIS_PADRAO = ("pessoal_ocupado", "salarios_mil")

# Territórios: códigos do SIDRA (n1 = Brasil, código 1; n3 = UF, RS = 43)
CODIGO_BRASIL = "1"
CODIGO_UF_RS = "43"
TERRITORIOS = ("Brasil", "RS", "RB")

# Códigos CNAE 2.0 usados (forma normalizada)
DIVISAO_35 = "35"
GRUPO_35_1 = "35.1"

# componente → (classe CNAE, grupo equivalente ou None). Os grupos 35.2 e 35.3 têm uma só
# classe cada (35.20-4 e 35.30-1), de modo que o grupo substitui a classe se esta faltar.
CLASSES_CEMPRE: dict[str, tuple[str, str | None]] = {
    "geracao": ("35.11-5", None),
    "transmissao": ("35.12-3", None),
    "comercio": ("35.13-1", None),
    "distribuicao": ("35.14-0", None),
    "gas": ("35.20-4", "35.2"),
    "vapor": ("35.30-1", "35.3"),
}
COMPONENTES = tuple(CLASSES_CEMPRE)

# Dígito verificador das classes CNAE 2.0 usadas (para completar '35.11' → '35.11-5').
DV_CLASSES = {"35.11": "5", "35.12": "3", "35.13": "1", "35.14": "0", "35.20": "4", "35.30": "1"}

# Pares sigilosos obtidos por diferença (Seção 5.8):
# (componentes do par, código do agregado, códigos subtraídos do agregado)
PARES_POR_DIFERENCA: tuple[tuple[tuple[str, str], str, tuple[str, ...]], ...] = (
    (("transmissao", "comercio"), GRUPO_35_1, ("35.11-5", "35.14-0")),
    (("gas", "vapor"), DIVISAO_35, (GRUPO_35_1,)),
)

# Agregação nos subsetores do motor (Seções 3 e 5.8). 'geracao' reúne todos os subsetores de
# geração; a repartição entre fontes é feita fora deste módulo.
SUBSETORES_MOTOR: dict[str, tuple[str, ...]] = {
    "geracao": ("geracao",),
    "S38_TRA": ("transmissao",),
    "S38_DIS": ("comercio", "distribuicao"),
    "S38_GAS": ("gas", "vapor"),
}

# Rótulos da coluna `metodo`
METODO_DIRETO = "direto"
METODO_DIRETO_GRUPO = "direto_grupo"
METODO_DIFERENCA = "diferenca"
METODO_DIFERENCA_PROPORCAO = "diferenca_proporcao_nacional"
METODO_BRASIL_MENOS_RS = "brasil_menos_rs"
METODOS_POR_DIFERENCA = (METODO_DIFERENCA, METODO_DIFERENCA_PROPORCAO)

# Símbolos do SIDRA em 'V'
SIMBOLOS_SIGILO = {"x"}
# '-' é o símbolo do SIDRA; travessões (en/em dash) aparecem em cópias de planilhas
SIMBOLOS_ZERO = {"-", "–", "—"}
SIMBOLOS_NAO_DISPONIVEL = {"", "..", "...", "nan", "none", "null", "na", "n/a"}

# --- Valores de referência: só para comparação, nunca como dado ---
# valor de referência das instruções da Rodada 02, Seção 5.8 (pessoal ocupado, salários R$ mil)
REFERENCIA_CEMPRE: dict[str, dict[str, tuple[float, float]]] = {
    "Brasil": {
        "35.11-5": (39913, 5171106),
        "35.12-3": (16084, 1657692),
        "35.13-1": (3146, 346415),
        "35.14-0": (74946, 5204004),
        "35.20-4": (4575, 524127),
        "35.30-1": (756, 34747),
    },
    "RS": {
        "35": (12509, 862439),
        "35.1": (12146, 834364),
        "35.11-5": (2217, 203958),
        "35.14-0": (9087, 518275),
    },
}
# valor de referência das instruções da Rodada 02, Seção 5.8 ("demais classes sigilosas" no RS)
REFERENCIA_RS_SIGILOSAS = ("35.12-3", "35.13-1", "35.20-4", "35.30-1")
# As instruções não fixam tolerância para a Seção 5.8; os valores publicados são inteiros,
# então se admite só a diferença de arredondamento (escolha deste módulo).
TOLERANCIA_REFERENCIA = 0.5

COLUNAS_LONGO = ["territorio", "variavel", "cnae", "descricao", "valor", "sigiloso"]


# --------------------------------------------------------------------------------------------
# Utilitários de texto e números
# --------------------------------------------------------------------------------------------
def _sem_acento(texto) -> str:
    """Texto sem acento, minúsculo, sem espaços nas pontas e com espaços internos simples."""
    if texto is None:
        return ""
    t = unicodedata.normalize("NFKD", str(texto))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().lower()


def _chave_coluna(nome) -> str:
    """Chave de comparação de nomes de coluna: sem acento, minúscula, só letras e dígitos."""
    return re.sub(r"[^a-z0-9]", "", _sem_acento(nome))


def _vazio(valor) -> bool:
    """True para None, NaN e texto vazio."""
    if valor is None or valor is pd.NA or valor is pd.NaT:
        return True
    if isinstance(valor, float) and math.isnan(valor):
        return True
    return isinstance(valor, str) and not valor.strip()


def _texto(valor) -> str:
    """Valor como texto aparado ('' se vazio)."""
    return "" if _vazio(valor) else re.sub(r"\s+", " ", str(valor)).strip()


def _ler_texto(caminho: str | Path) -> str:
    """Lê o arquivo como texto, testando os encodings candidatos em ordem."""
    dados = Path(caminho).read_bytes()
    for enc in ENCODINGS_CANDIDATOS:
        try:
            return dados.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"não foi possível decodificar {caminho} com {ENCODINGS_CANDIDATOS}")


def _fmt(x: float) -> str:
    """Número para o texto de `detalhe`: inteiro sem casas; senão até 12 algarismos."""
    return f"{x:.12g}"


def _detectar_separador(texto: str) -> str:
    """Separador mais frequente na primeira linha não vazia (';' em caso de empate ou ausência)."""
    primeira = next((ln for ln in texto.splitlines() if ln.strip()), "")
    contagens = {s: primeira.count(s) for s in SEPARADORES_CANDIDATOS}
    melhor = max(contagens, key=lambda s: (contagens[s], s == ";"))
    return melhor if contagens[melhor] > 0 else ";"


def _valor_sidra(bruto) -> tuple[float, bool, bool]:
    """Converte o campo 'V' do SIDRA. Devolve (valor, sigiloso, reconhecido).

    'X' → (NaN, sigiloso); '-' → 0 (zero absoluto); '..', '...', vazio → NaN. Números com ponto
    ou vírgula decimal (com vírgula e ponto juntos, o último é o decimal; vários pontos sem
    vírgula são separadores de milhar). Um único ponto sem vírgula ('12.509') é lido como
    decimal, como na API do SIDRA (que não usa separador de milhar). Texto não numérico
    fora desses símbolos → (NaN, False, False).
    """
    if _vazio(bruto):
        return np.nan, False, True
    if isinstance(bruto, (bool, np.bool_)):
        return np.nan, False, False
    if isinstance(bruto, (int, float, np.integer, np.floating)):
        return float(bruto), False, True
    t = re.sub(r"[\s ]+", "", str(bruto))
    n = _sem_acento(t)
    if n in SIMBOLOS_SIGILO:
        return np.nan, True, True
    if n in SIMBOLOS_ZERO:
        return 0.0, False, True
    if n in SIMBOLOS_NAO_DISPONIVEL:
        return np.nan, False, True
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".") if t.count(",") == 1 else t.replace(",", "")
    elif t.count(".") > 1:
        # vários pontos e nenhuma vírgula: só podem ser separadores de milhar ('1.234.567')
        t = t.replace(".", "")
    try:
        return float(t), False, True
    except ValueError:
        return np.nan, False, False


# --------------------------------------------------------------------------------------------
# Normalização de códigos CNAE, territórios e variáveis
# --------------------------------------------------------------------------------------------
_RE_CODIGO_CNAE = re.compile(
    r"(?<![\d.,])"
    r"(?P<div>\d{2})"
    r"(?:\.?(?P<grp>\d)"
    r"(?:(?P<cls>\d)"
    r"(?:\s*-?\s*(?P<dv>\d)"
    r"(?:\s*/\s*(?P<sub>\d{2}))?"
    r")?)?)?"
    r"(?!\d)"
)
_RE_PREFIXO_CNAE = re.compile(
    r"^(?:(?:cnae(?:\s*2\.0)?|secao|divisao|grupo|classe|subclasse|codigo)\s*[:\-]?\s*)*"
)


def _formatar_cnae(m: re.Match) -> str:
    div, grp, cls, dv, sub = (m.group(k) for k in ("div", "grp", "cls", "dv", "sub"))
    if grp is None:
        return div
    if cls is None:
        return f"{div}.{grp}"
    classe = f"{div}.{grp}{cls}"
    if dv is None:
        dv = DV_CLASSES.get(classe)
        return f"{classe}-{dv}" if dv is not None else classe
    conhecido = DV_CLASSES.get(classe)
    if conhecido is not None and conhecido != dv:
        warnings.warn(
            f"CNAE {classe}-{dv}: dígito verificador difere do esperado ({classe}-{conhecido})",
            stacklevel=4,
        )
    if sub is not None:
        return f"{div}{grp}{cls}-{dv}/{sub}"
    return f"{classe}-{dv}"


def normalizar_cnae(texto) -> str | None:
    """Extrai e normaliza o código CNAE 2.0 de um nome de categoria do SIDRA.

    '35 Eletricidade, gás...' → '35'; '35.1 Geração, transmissão...' → '35.1';
    '35.11-5 Geração de energia elétrica', '35.115', '3511-5', '35115', 'Classe 35.11-5' ou
    'Geração de energia elétrica (35.11-5)' → '35.11-5'; '35.11' → '35.11-5' se a classe estiver
    em `DV_CLASSES` (senão '35.11'). Subclasse '3511-5/01' → '3511-5/01'. Sem código → None.
    O código é procurado no começo do texto (após 'Divisão', 'Grupo', 'Classe'...), depois entre
    parênteses; por fim aceita-se um único código em qualquer posição.
    """
    t = _sem_acento(texto)
    if not t:
        return None
    resto = _RE_PREFIXO_CNAE.sub("", t, count=1)
    m = _RE_CODIGO_CNAE.match(resto)
    if m:
        return _formatar_cnae(m)
    for parenteses in re.findall(r"\(([^()]*)\)", t):
        m = _RE_CODIGO_CNAE.fullmatch(_RE_PREFIXO_CNAE.sub("", parenteses.strip(), count=1))
        if m:
            return _formatar_cnae(m)
    achados = list(_RE_CODIGO_CNAE.finditer(t))
    if len(achados) == 1:
        return _formatar_cnae(achados[0])
    return None


def _normalizar_territorio(codigo, nome) -> str:
    """'Brasil' (ou código 1) → 'Brasil'; 'Rio Grande do Sul'/'RS' (ou código 43) → 'RS'.

    'RB'/'Restante do Brasil' → 'RB'. Outros territórios mantêm o nome original.
    """
    n, c = _sem_acento(nome), _texto(codigo)
    # o código ('1' Brasil, '43' RS) também é aceito na posição do nome (ex.: DataFrame com
    # a coluna territorio preenchida pelos códigos do SIDRA)
    if n in ("brasil", "br", CODIGO_BRASIL) or (not n and c == CODIGO_BRASIL):
        return "Brasil"
    if re.fullmatch(r"rio grande do sul(?:\s*\(rs\))?|rs|43", n) or (not n and c == CODIGO_UF_RS):
        return "RS"
    if n in ("rb", "restante do brasil", "resto do brasil"):
        return "RB"
    return _texto(nome) or c


def _normalizar_variavel(codigo, nome) -> str | None:
    """Variável 707 / 'Pessoal ocupado total' → 'pessoal_ocupado'; 662 / 'Salários e outras
    remunerações' → 'salarios_mil'. Outras (ex.: pessoal ocupado assalariado) → None."""
    c = _texto(codigo)
    if c in VARIAVEIS_SIDRA:
        return VARIAVEIS_SIDRA[c]
    n = _sem_acento(nome).replace("_", " ")
    if n in VARIAVEIS_SIDRA:
        return VARIAVEIS_SIDRA[n]
    if n in ("pessoal ocupado", "pessoal ocupado total") or n.startswith("pessoal ocupado total"):
        return "pessoal_ocupado"
    if n in ("salarios", "salarios mil") or n.startswith("salarios e outras remuneracoes"):
        return "salarios_mil"
    return None


# --------------------------------------------------------------------------------------------
# 1) Leitura do JSON do SIDRA (tabela 6450)
# --------------------------------------------------------------------------------------------
_CHAVES_FIXAS_SIDRA = {"NC", "NN", "MC", "MN", "V"}


def _e_arquivo(texto: str) -> bool:
    """True se o texto for o caminho de um arquivo existente."""
    try:
        return len(texto) < 4096 and Path(texto).is_file()
    except (OSError, ValueError):
        return False


def _registros_csv(texto: str) -> list[dict]:
    """CSV 'longo' (descrições do SIDRA como nomes de coluna) → lista de registros (texto)."""
    sep = _detectar_separador(texto)
    df = pd.read_csv(io.StringIO(texto), sep=sep, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    return df.to_dict("records")


def _carregar_registros(fonte) -> tuple[dict[str, str], list[dict]]:
    """Carrega a fonte e separa o cabeçalho (chave → descrição) dos registros de dados.

    Aceita caminho (JSON ou CSV), texto JSON, lista já carregada ou DataFrame. Se o primeiro
    registro tiver 'V' = 'Valor', ele é o cabeçalho do SIDRA. Se as chaves já forem descrições
    (ex.: coluna 'Valor' num CSV), cada chave é a sua própria descrição. Sem nada disso, o
    cabeçalho volta vazio e as dimensões são identificadas pelo conteúdo.
    """
    if isinstance(fonte, pd.DataFrame):
        registros = fonte.astype(object).where(fonte.notna(), None).to_dict("records")
    elif isinstance(fonte, list):
        registros = fonte
    elif isinstance(fonte, (str, Path)):
        if (
            isinstance(fonte, str)
            and fonte.lstrip("\ufeff \t\r\n").startswith(("[", "{"))
            and not _e_arquivo(fonte)
        ):
            texto = fonte
        else:
            texto = _ler_texto(fonte)
        texto = texto.lstrip("\ufeff")
        if texto.lstrip().startswith(("[", "{")):
            registros = json.loads(texto)
        else:
            registros = _registros_csv(texto)
    else:
        raise TypeError(
            f"esperado caminho de arquivo, texto JSON, lista ou DataFrame do SIDRA, não {type(fonte).__name__}"
        )
    if not isinstance(registros, list) or not registros or not all(isinstance(r, dict) for r in registros):
        raise ValueError("SIDRA: conteúdo vazio ou fora do formato esperado (lista de dicionários)")
    registros = [{str(k).strip(): v for k, v in r.items()} for r in registros]

    primeiro = registros[0]
    if _sem_acento(primeiro.get("V")) == "valor":
        cabecalho = {k: _texto(v) for k, v in primeiro.items()}
        return cabecalho, registros[1:]
    chaves = list(dict.fromkeys(k for r in registros for k in r))
    if any(_sem_acento(k) == "valor" for k in chaves):
        return {k: k for k in chaves}, registros
    return {}, registros


def _papel_por_descricao(d: str) -> str | None:
    """Papel de uma dimensão a partir da descrição do cabeçalho (sem acento, minúscula)."""
    if not d:
        return None
    if d.startswith("variavel"):
        return "variavel"
    if d.startswith(("ano", "periodo")):
        return "periodo"
    if "cnae" in d or "atividades economicas" in d or d.startswith("classificacao"):
        return "cnae"
    if re.search(r"brasil|unidade da federacao|municipio|regiao|territori|\buf\b", d):
        return "territorio"
    return None


def _papel_por_conteudo(codigos: list[str], nomes: list[str]) -> str | None:
    """Papel de uma dimensão a partir dos valores (usado quando não há cabeçalho)."""
    cods = {c for c in codigos if c}
    noms = [n for n in nomes if n]
    if (cods and all(re.fullmatch(r"(19|20)\d{2}", c) for c in cods)) or (
        not cods and noms and all(re.fullmatch(r"(19|20)\d{2}", n) for n in noms)
    ):
        return "periodo"
    if (cods and cods <= set(VARIAVEIS_SIDRA)) or (
        noms and all(_normalizar_variavel(None, n) is not None for n in noms)
    ):
        return "variavel"
    if noms and sum(normalizar_cnae(n) is not None for n in noms) >= 0.5 * len(noms):
        return "cnae"
    if any(_sem_acento(n) in ("brasil", "rio grande do sul") for n in noms) or (
        cods and cods <= {CODIGO_BRASIL, CODIGO_UF_RS}
    ):
        return "territorio"
    return None


def _dimensoes(cabecalho: dict[str, str], dados: list[dict]) -> dict[str, dict[str, str | None]]:
    """Identifica as dimensões (territorio, variavel, periodo, cnae) e as chaves de código e nome.

    Devolve {papel: {"codigo": chave | None, "nome": chave | None}}.
    """
    chaves = list(dict.fromkeys(list(cabecalho) + [k for r in dados for k in r]))
    grupos: dict[str, dict] = {}
    for k in chaves:
        desc = _sem_acento(cabecalho.get(k, ""))
        m = re.fullmatch(r"D(\d+)([CN])", k)
        if m:
            gid, tipo = "D" + m.group(1), m.group(2)
        else:
            if k in _CHAVES_FIXAS_SIDRA:
                continue
            d = desc or _sem_acento(k)
            if d == "valor" or d.startswith(("nivel territorial", "unidade de medida")):
                continue
            tipo = "C" if re.search(r"\(\s*codigo\s*\)", d) else "N"
            gid = re.sub(r"\s*\(\s*codigo\s*\)\s*$", "", d).strip()
        g = grupos.setdefault(gid, {"codigo": None, "nome": None, "descricao": ""})
        g["codigo" if tipo == "C" else "nome"] = k
        base = re.sub(r"\s*\(\s*codigo\s*\)\s*$", "", desc).strip()
        if base and not g["descricao"]:
            g["descricao"] = base

    papeis: dict[str, dict[str, str | None]] = {}
    sem_papel = []
    for g in grupos.values():
        papel = _papel_por_descricao(g["descricao"])
        if papel and papel not in papeis:
            papeis[papel] = {"codigo": g["codigo"], "nome": g["nome"]}
        elif not papel:
            sem_papel.append(g)
    for g in sem_papel:
        codigos = [_texto(r.get(g["codigo"])) for r in dados] if g["codigo"] else []
        nomes = [_texto(r.get(g["nome"])) for r in dados] if g["nome"] else []
        papel = _papel_por_conteudo(codigos, nomes)
        if papel and papel not in papeis:
            papeis[papel] = {"codigo": g["codigo"], "nome": g["nome"]}

    faltando = [p for p in ("territorio", "variavel", "cnae") if p not in papeis]
    if faltando:
        disponiveis = cabecalho or {k: "" for k in chaves}
        raise ValueError(
            f"SIDRA 6450: dimensão(ões) não identificada(s): {faltando}. "
            f"Campos disponíveis: {disponiveis}"
        )
    if papeis["cnae"]["nome"] is None:
        raise ValueError(
            "SIDRA 6450: falta o nome (descrição textual) da categoria CNAE, necessário para "
            f"identificar a classe. Campos disponíveis: {cabecalho or chaves}"
        )
    return papeis


def _chave_por_descricao(cabecalho: dict[str, str], alvo: str, padrao: str | None) -> str | None:
    for k, d in cabecalho.items():
        if _sem_acento(d) == alvo:
            return k
    return padrao


def _ano(codigo, nome) -> int | None:
    for t in (_texto(codigo), _texto(nome)):
        m = re.search(r"(?<!\d)((?:19|20)\d{2})(?!\d)", t)
        if m:
            return int(m.group(1))
    return None


def _ordenar_longo(df: pd.DataFrame) -> pd.DataFrame:
    ordem_t = {t: i for i, t in enumerate(TERRITORIOS)}
    ordem_v = {v: i for i, v in enumerate(VARIAVEIS_PADRAO)}
    chave = pd.DataFrame(
        {
            "t": df["territorio"].map(lambda t: ordem_t.get(t, len(ordem_t))),
            "t2": df["territorio"].astype(str),
            "v": df["variavel"].map(lambda v: ordem_v.get(v, len(ordem_v))),
            "c": df["cnae"].astype(str),
        },
        index=df.index,
    )
    idx = chave.sort_values(["t", "t2", "v", "c"]).index
    return df.loc[idx].reset_index(drop=True)


def ler_cempre_sidra(fonte, *, ano: int | None = ANO_BASE) -> pd.DataFrame:
    """Lê o CEMPRE (SIDRA, tabela 6450) da API de valores do SIDRA em formato longo.

    `fonte`: caminho do arquivo JSON (ou CSV longo), texto JSON, lista já carregada ou
    DataFrame. `ano`: período a manter (None = não filtra; levanta erro se houver mais de um).

    Devolve DataFrame com: territorio ('Brasil', 'RS'; outros mantêm o nome), variavel
    ('pessoal_ocupado' ou 'salarios_mil'), cnae (código normalizado: '35', '35.1', '35.11-5'),
    descricao (nome da categoria no SIDRA), valor (float; NaN se sigiloso ou não disponível),
    sigiloso (bool), e ainda codigo_sidra (código da categoria no SIDRA, só informativo),
    unidade e valor_original (texto de 'V').

    Registros de outras variáveis e categorias sem código CNAE são descartados com aviso.
    Levanta ValueError se faltar dimensão obrigatória (listando os campos disponíveis), se o
    ano pedido não existir ou se a mesma célula aparecer com valores diferentes.
    """
    cabecalho, dados = _carregar_registros(fonte)
    if not dados:
        raise ValueError("SIDRA 6450: nenhum registro de dados além do cabeçalho")
    dims = _dimensoes(cabecalho, dados)
    chave_valor = _chave_por_descricao(cabecalho, "valor", "V")
    if not any(chave_valor in r for r in dados):
        raise ValueError(
            f"SIDRA 6450: campo de valor {chave_valor!r} ausente. "
            f"Campos disponíveis: {sorted({k for r in dados for k in r})}"
        )
    chave_unidade = _chave_por_descricao(cabecalho, "unidade de medida", "MN")

    def campo(r: dict, papel: str, tipo: str):
        k = dims.get(papel, {}).get(tipo)
        return r.get(k) if k else None

    linhas, outras_var, sem_cnae, nao_numericos = [], set(), set(), []
    for r in dados:
        variavel = _normalizar_variavel(campo(r, "variavel", "codigo"), campo(r, "variavel", "nome"))
        if variavel is None:
            outras_var.add(_texto(campo(r, "variavel", "nome")) or _texto(campo(r, "variavel", "codigo")))
            continue
        descricao = _texto(campo(r, "cnae", "nome"))
        cnae = normalizar_cnae(descricao)
        if cnae is None:
            sem_cnae.add(descricao)
            continue
        bruto = r.get(chave_valor)
        valor, sigiloso, reconhecido = _valor_sidra(bruto)
        if not reconhecido:
            nao_numericos.append(_texto(bruto))
        linhas.append(
            {
                "territorio": _normalizar_territorio(
                    campo(r, "territorio", "codigo"), campo(r, "territorio", "nome")
                ),
                "variavel": variavel,
                "cnae": cnae,
                "descricao": descricao,
                "valor": valor,
                "sigiloso": bool(sigiloso),
                "codigo_sidra": _texto(campo(r, "cnae", "codigo")),
                "unidade": _texto(r.get(chave_unidade)) if chave_unidade else "",
                "valor_original": _texto(bruto),
                "ano": _ano(campo(r, "periodo", "codigo"), campo(r, "periodo", "nome")),
            }
        )
    if outras_var:
        warnings.warn(f"SIDRA 6450: variáveis ignoradas: {sorted(outras_var)}", stacklevel=2)
    if sem_cnae:
        warnings.warn(f"SIDRA 6450: categorias sem código CNAE ignoradas: {sorted(sem_cnae)}", stacklevel=2)
    if nao_numericos:
        warnings.warn(
            f"SIDRA 6450: {len(nao_numericos)} valor(es) não numérico(s) tratados como NaN: "
            f"{sorted(set(nao_numericos))[:5]}",
            stacklevel=2,
        )
    if not linhas:
        raise ValueError("SIDRA 6450: nenhum registro de pessoal ocupado (707) ou salários (662)")
    df = pd.DataFrame(linhas)

    anos = sorted({int(a) for a in df["ano"] if a is not None and not pd.isna(a)})
    if ano is not None and anos:
        df = df[df["ano"] == ano]
        if df.empty:
            raise ValueError(f"SIDRA 6450: ano {ano} ausente. Anos disponíveis: {anos}")
    elif ano is None and len(anos) > 1:
        raise ValueError(f"SIDRA 6450: mais de um ano ({anos}); informe `ano`")
    df = df.drop(columns="ano")

    unid_sal = {u for u in df.loc[df["variavel"] == "salarios_mil", "unidade"] if u}
    if any("mil" not in _sem_acento(u) for u in unid_sal):
        warnings.warn(
            f"SIDRA 6450: unidade dos salários {sorted(unid_sal)} diferente de 'Mil Reais'; "
            "os valores NÃO foram convertidos",
            stacklevel=2,
        )

    df = _remover_duplicatas(df)
    df = _ordenar_longo(df)
    df = df[COLUNAS_LONGO + ["codigo_sidra", "unidade", "valor_original"]]
    df.attrs = {"fonte": FONTE_CEMPRE}
    return df


def _remover_duplicatas(df: pd.DataFrame) -> pd.DataFrame:
    """Remove repetições idênticas de (territorio, variavel, cnae); valores diferentes → erro."""
    chave = ["territorio", "variavel", "cnae"]
    dup = df[df.duplicated(chave, keep=False)]
    if not dup.empty:
        conflitos = []
        for k, g in dup.groupby(chave, sort=False):
            vals = {("X" if s else ("nan" if pd.isna(v) else float(v))) for v, s in zip(g["valor"], g["sigiloso"])}
            if len(vals) > 1:
                conflitos.append(k)
        if conflitos:
            raise ValueError(f"CEMPRE: células repetidas com valores diferentes: {conflitos}")
        df = df.drop_duplicates(chave)
    return df.reset_index(drop=True)


# --------------------------------------------------------------------------------------------
# 2) Composição por componente e por subsetor do motor
# --------------------------------------------------------------------------------------------
def _padronizar_longo(dados) -> pd.DataFrame:
    """Aceita a saída de `ler_cempre_sidra` (ou equivalente) ou qualquer fonte que ela leia.

    Linha marcada como sigilosa tem o valor descartado (NaN), mesmo que traga um número
    (ex.: 'X' preenchido com 0): o valor sigiloso é sempre obtido por diferença.
    """
    if not isinstance(dados, pd.DataFrame):
        return ler_cempre_sidra(dados)
    exigidas = ["territorio", "variavel", "cnae", "valor"]
    por_chave: dict[str, str] = {}
    for c in dados.columns:
        por_chave.setdefault(_chave_coluna(c), c)
    faltando = [c for c in exigidas if _chave_coluna(c) not in por_chave]
    if faltando and "V" in {str(c).strip() for c in dados.columns}:
        # DataFrame no formato bruto da API do SIDRA (ex.: sidrapy): lê como `ler_cempre_sidra`
        return ler_cempre_sidra(dados)
    if faltando:
        raise ValueError(
            f"CEMPRE: coluna(s) obrigatória(s) ausente(s): {faltando}. "
            f"Colunas disponíveis: {[str(c) for c in dados.columns]}"
        )
    col = {c: por_chave[_chave_coluna(c)] for c in exigidas}
    col_sig = por_chave.get(_chave_coluna("sigiloso"))
    col_desc = por_chave.get(_chave_coluna("descricao"))

    linhas = []
    for _, r in dados.iterrows():
        valor, sigiloso, _ = _valor_sidra(r[col["valor"]])
        if col_sig is not None and not _vazio(r[col_sig]):
            sigiloso = sigiloso or _sem_acento(r[col_sig]) in ("true", "1", "sim", "x")
        if sigiloso:
            valor = np.nan
        bruto_cnae = r[col["cnae"]]
        cnae = normalizar_cnae(bruto_cnae)
        if cnae is None:
            continue
        variavel = _normalizar_variavel(None, r[col["variavel"]]) or _texto(r[col["variavel"]])
        linhas.append(
            {
                "territorio": _normalizar_territorio(None, r[col["territorio"]]),
                "variavel": variavel,
                "cnae": cnae,
                "descricao": _texto(r[col_desc]) if col_desc is not None else _texto(bruto_cnae),
                "valor": valor,
                "sigiloso": bool(sigiloso),
            }
        )
    if not linhas:
        raise ValueError("CEMPRE: nenhuma linha com código CNAE reconhecível")
    return _remover_duplicatas(pd.DataFrame(linhas))


def _resolver_territorio(
    territorio: str,
    variavel: str,
    valores: dict[tuple[str, str, str], float],
    proporcao: dict[str, float] | None,
) -> dict[str, tuple[float, str, str]]:
    """Valor de cada componente num território: {componente: (valor, metodo, detalhe)}.

    Ordem: classe publicada; grupo equivalente (35.2, 35.3); diferença do par (Seção 5.8).
    `proporcao`: valores nacionais dos componentes (None no próprio Brasil).
    """

    def bruto(cnae: str) -> float | None:
        v = valores.get((territorio, variavel, cnae))
        return None if v is None or pd.isna(v) else float(v)

    res: dict[str, tuple[float, str, str]] = {}
    for comp, (classe, grupo) in CLASSES_CEMPRE.items():
        x = bruto(classe)
        if x is not None:
            res[comp] = (x, METODO_DIRETO, classe)
        elif grupo is not None and bruto(grupo) is not None:
            res[comp] = (bruto(grupo), METODO_DIRETO_GRUPO, f"grupo {grupo} (classe única {classe})")

    for (a, b), pai, subtrair in PARES_POR_DIFERENCA:
        faltam = [c for c in (a, b) if c not in res]
        if not faltam:
            continue
        rotulo = f"{territorio}/{variavel}"
        partes = [bruto(pai)] + [bruto(s) for s in subtrair]
        formula = " − ".join([pai, *subtrair])
        if any(p is None for p in partes):
            ausentes = [c for c, p in zip([pai, *subtrair], partes) if p is None]
            raise ValueError(
                f"CEMPRE {rotulo}: {faltam} sigiloso(s)/ausente(s) e a diferença {formula} não "
                f"pode ser calculada (falta {ausentes})"
            )
        total = partes[0] - sum(partes[1:])
        if total < 0:
            raise ValueError(f"CEMPRE {rotulo}: diferença {formula} negativa ({_fmt(total)})")
        if len(faltam) == 1:
            falta = faltam[0]
            conhecido = b if falta == a else a
            x = total - res[conhecido][0]
            if x < 0:
                raise ValueError(
                    f"CEMPRE {rotulo}: {falta} por diferença negativo "
                    f"(({formula}) − {CLASSES_CEMPRE[conhecido][0]} = {_fmt(x)})"
                )
            res[falta] = (x, METODO_DIFERENCA, f"({formula}) − {CLASSES_CEMPRE[conhecido][0]}")
            continue
        if proporcao is None:
            raise ValueError(
                f"CEMPRE {rotulo}: {faltam} sigilosos e sem proporção nacional para repartir {formula}"
            )
        pa, pb = proporcao[a], proporcao[b]
        soma = pa + pb
        if soma <= 0:
            if total == 0:
                res[a] = (0.0, METODO_DIFERENCA_PROPORCAO, f"({formula}) = 0")
                res[b] = (0.0, METODO_DIFERENCA_PROPORCAO, f"({formula}) = 0")
                continue
            raise ValueError(f"CEMPRE {rotulo}: proporção nacional de {a}+{b} nula; não há como repartir")
        ca, cb = CLASSES_CEMPRE[a][0], CLASSES_CEMPRE[b][0]
        res[a] = (total * pa / soma, METODO_DIFERENCA_PROPORCAO,
                  f"({formula}) × Brasil {ca} / ({ca} + {cb}) = {_fmt(total)} × {_fmt(pa)}/{_fmt(soma)}")
        res[b] = (total * pb / soma, METODO_DIFERENCA_PROPORCAO,
                  f"({formula}) × Brasil {cb} / ({ca} + {cb}) = {_fmt(total)} × {_fmt(pb)}/{_fmt(soma)}")

    faltam = [c for c in COMPONENTES if c not in res]
    if faltam:
        raise ValueError(
            f"CEMPRE {territorio}/{variavel}: sem valor para {faltam} "
            f"(classes {[CLASSES_CEMPRE[c][0] for c in faltam]})"
        )
    return res


def _juntar_metodos(metodos: Iterable[str]) -> str:
    unicos = list(dict.fromkeys(metodos))
    return unicos[0] if len(unicos) == 1 else " + ".join(unicos)


def composicao_cempre(dados) -> pd.DataFrame:
    """Valores e composição do CEMPRE por componente e por subsetor do motor (Seção 5.8).

    `dados`: saída de `ler_cempre_sidra` (DataFrame longo com territorio, variavel, cnae, valor
    e, de preferência, sigiloso) ou qualquer fonte aceita por ela.

    Para Brasil, RS e RB (= Brasil − RS) e cada variável presente (pessoal_ocupado,
    salarios_mil), devolve DataFrame longo com:
    - territorio, variavel;
    - nivel: 'classe' (geracao, transmissao, comercio, distribuicao, gas, vapor) ou 'subsetor'
      (geracao, S38_TRA, S38_DIS, S38_GAS);
    - item, cnae (classe ou classes somadas);
    - valor;
    - metodo: 'direto' (classe publicada), 'direto_grupo' (grupo 35.2/35.3 no lugar da classe),
      'diferenca' (par com uma classe publicada), 'diferenca_proporcao_nacional' (soma por
      diferença repartida pela proporção do Brasil), 'brasil_menos_rs' (RB); no RB e nos
      subsetores, os métodos dos componentes são indicados;
    - por_diferenca: True se o valor depende de classe sigilosa obtida por diferença no RS;
    - detalhe: a conta feita;
    - participacao: valor ÷ total do território × variável × nível (soma 1).

    Levanta ValueError se faltar Brasil ou RS, se uma classe sigilosa não puder ser obtida
    por diferença, ou se algum valor resultar negativo.
    """
    df = _padronizar_longo(dados)
    valores: dict[tuple[str, str, str], float] = {
        (t, v, c): x for t, v, c, x in zip(df["territorio"], df["variavel"], df["cnae"], df["valor"])
    }
    faltam_t = [t for t in ("Brasil", "RS") if t not in set(df["territorio"])]
    if faltam_t:
        raise ValueError(
            f"CEMPRE: território(s) ausente(s): {faltam_t}. Disponíveis: {sorted(set(df['territorio']))}"
        )
    variaveis = [v for v in VARIAVEIS_PADRAO if v in set(df["variavel"])]
    if not variaveis:
        raise ValueError(
            f"CEMPRE: nenhuma das variáveis {list(VARIAVEIS_PADRAO)}. "
            f"Disponíveis: {sorted(set(df['variavel'].astype(str)))}"
        )

    linhas, conferencia = [], []
    for v in variaveis:
        br = _resolver_territorio("Brasil", v, valores, proporcao=None)
        rs = _resolver_territorio("RS", v, valores, proporcao={c: br[c][0] for c in COMPONENTES})
        rb = {}
        for c in COMPONENTES:
            x = br[c][0] - rs[c][0]
            if x < -1e-9:
                raise ValueError(f"CEMPRE RB/{v}: {c} negativo (Brasil {_fmt(br[c][0])} − RS {_fmt(rs[c][0])})")
            metodo = METODO_BRASIL_MENOS_RS
            if rs[c][1] != METODO_DIRETO:
                metodo += f" (RS: {rs[c][1]})"
            rb[c] = (max(x, 0.0), metodo, f"Brasil − RS = {_fmt(br[c][0])} − {_fmt(rs[c][0])}")

        for t, res in (("Brasil", br), ("RS", rs), ("RB", rb)):
            por_dif = {c: any(m in res[c][1] for m in METODOS_POR_DIFERENCA) for c in COMPONENTES}
            for c in COMPONENTES:
                linhas.append({
                    "territorio": t, "variavel": v, "nivel": "classe", "item": c,
                    "cnae": CLASSES_CEMPRE[c][0], "valor": res[c][0], "metodo": res[c][1],
                    "por_diferenca": por_dif[c], "detalhe": res[c][2],
                })
            for sub, comps in SUBSETORES_MOTOR.items():
                linhas.append({
                    "territorio": t, "variavel": v, "nivel": "subsetor", "item": sub,
                    "cnae": " + ".join(CLASSES_CEMPRE[c][0] for c in comps),
                    "valor": float(sum(res[c][0] for c in comps)),
                    "metodo": _juntar_metodos(res[c][1] for c in comps),
                    "por_diferenca": any(por_dif[c] for c in comps),
                    "detalhe": " + ".join(comps),
                })
            # conferência: soma das classes × divisão 35 publicada
            div = valores.get((t, v, DIVISAO_35))
            if t != "RB" and div is not None and not pd.isna(div):
                soma = float(sum(res[c][0] for c in COMPONENTES))
                conferencia.append({"territorio": t, "variavel": v, "divisao_35": float(div),
                                    "soma_classes": soma, "diferenca": soma - float(div)})
                if abs(soma - float(div)) > 0.5 * len(COMPONENTES):
                    warnings.warn(
                        f"CEMPRE {t}/{v}: soma das classes ({_fmt(soma)}) difere da divisão 35 ({_fmt(float(div))})",
                        stacklevel=2,
                    )

    saida = pd.DataFrame(linhas)
    totais = saida.groupby(["territorio", "variavel", "nivel"], sort=False)["valor"].transform("sum")
    saida["participacao"] = np.where(totais > 0, saida["valor"] / totais.where(totais > 0, 1.0), np.nan)
    saida.attrs = {"fonte": FONTE_CEMPRE, "conferencia_divisao_35": conferencia}
    return saida


def participacoes_subsetores(composicao: pd.DataFrame) -> pd.DataFrame:
    """Tabela larga dos subsetores do motor: territorio, subsetor, valores e participações.

    `composicao`: saída de `composicao_cempre`. Colunas: territorio, subsetor e, para cada
    variável presente, `<variavel>` (valor) e `part_<variavel>` (participação).
    """
    faltando = [c for c in ("territorio", "variavel", "nivel", "item", "valor", "participacao")
                if c not in composicao.columns]
    if faltando:
        raise ValueError(f"composição sem {faltando}. Colunas disponíveis: {list(composicao.columns)}")
    sub = composicao[composicao["nivel"] == "subsetor"]
    largo = sub.pivot(index=["territorio", "item"], columns="variavel", values=["valor", "participacao"])
    variaveis = [v for v in VARIAVEIS_PADRAO if v in set(sub["variavel"])]
    saida = pd.DataFrame(index=largo.index)
    for v in variaveis:
        saida[v] = largo[("valor", v)]
    for v in variaveis:
        saida[f"part_{v}"] = largo[("participacao", v)]
    saida = saida.reset_index().rename(columns={"item": "subsetor"})
    ordem_t = {t: i for i, t in enumerate(TERRITORIOS)}
    ordem_s = {s: i for i, s in enumerate(SUBSETORES_MOTOR)}
    saida = saida.sort_values(
        by=["territorio", "subsetor"],
        key=lambda s: s.map(ordem_t) if s.name == "territorio" else s.map(ordem_s),
    ).reset_index(drop=True)
    saida.columns.name = None
    return saida


# --------------------------------------------------------------------------------------------
# 3) Comparação com os valores de referência da Seção 5.8
# --------------------------------------------------------------------------------------------
def _nome_item(cnae: str) -> str:
    for comp, (classe, grupo) in CLASSES_CEMPRE.items():
        if cnae in (classe, grupo):
            return comp
    return {DIVISAO_35: "divisao_35", GRUPO_35_1: "grupo_35_1"}.get(cnae, cnae)


def comparar_com_referencia(dados, tolerancia: float = TOLERANCIA_REFERENCIA) -> pd.DataFrame:
    """Compara os valores lidos com os de referência da Seção 5.8 (esperado × obtido × diferença).

    `dados`: saída de `ler_cempre_sidra` (ou fonte que ela leia). Para cada território, classe
    e variável de `REFERENCIA_CEMPRE`: esperado, obtido, diferenca (obtido − esperado) e
    dentro_tolerancia (|diferença| ≤ tolerância). No Brasil, gás e vapor usam o grupo 35.2/35.3
    se a classe faltar. Para as classes que a referência dá como sigilosas no RS
    (`REFERENCIA_RS_SIGILOSAS`), esperado é NaN, esperado_sigiloso é True e
    dentro_tolerancia indica se o valor veio de fato sigiloso.
    """
    df = _padronizar_longo(dados)
    celulas = {
        (t, v, c): (x, bool(s))
        for t, v, c, x, s in zip(df["territorio"], df["variavel"], df["cnae"], df["valor"], df["sigiloso"])
    }

    def obter(t: str, v: str, cnae: str) -> tuple[float, bool]:
        x = celulas.get((t, v, cnae))
        if x is None:
            grupo = next((g for cl, g in CLASSES_CEMPRE.values() if cl == cnae and g), None)
            x = celulas.get((t, v, grupo)) if grupo else None
        return x if x is not None else (np.nan, False)

    linhas = []
    for t, refs in REFERENCIA_CEMPRE.items():
        for cnae, esperados in refs.items():
            for v, esperado in zip(VARIAVEIS_PADRAO, esperados):
                obtido, sig = obter(t, v, cnae)
                dif = obtido - esperado
                linhas.append({
                    "territorio": t, "cnae": cnae, "item": _nome_item(cnae), "variavel": v,
                    "esperado": float(esperado), "obtido": obtido, "diferenca": dif,
                    "esperado_sigiloso": False, "obtido_sigiloso": sig,
                    "dentro_tolerancia": bool(not pd.isna(dif) and abs(dif) <= tolerancia),
                })
    for cnae in REFERENCIA_RS_SIGILOSAS:
        for v in VARIAVEIS_PADRAO:
            obtido, sig = obter("RS", v, cnae)
            linhas.append({
                "territorio": "RS", "cnae": cnae, "item": _nome_item(cnae), "variavel": v,
                "esperado": np.nan, "obtido": obtido, "diferenca": np.nan,
                "esperado_sigiloso": True, "obtido_sigiloso": sig, "dentro_tolerancia": bool(sig),
            })
    return pd.DataFrame(linhas)
