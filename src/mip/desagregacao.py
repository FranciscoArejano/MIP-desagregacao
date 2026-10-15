"""Motor genérico de desagregação de um setor da MIP em subsetores (Etapa 5).

Entrada: a MIP original + uma `Especificacao` (lida de `parametros/*.yaml` + CSVs). Saída: a MIP
desagregada, que preserva exatamente todos os totais da original (a soma dos subsetores reproduz
cada célula da original), mais o mapa de setores, os pesos usados e as checagens.

Blocos da nova matriz (t = setor-alvo; "fora do bloco" = setores ≠ t e colunas de demanda final):
- fora × fora ......................... cópia da original
- fornecedor fora → subsetores (coluna) .... regras de coluna: proporcional_vbp | fixa | indicador
- subsetores → comprador fora (linha) ...... regras de linha: proporcional_vbp | somente_rede_e_gas
                                             | fixa_por_comprador (+ RAS para fechar as linhas)
- subsetores → subsetores (bloco t→t) ...... proporcional | geracao_vende_para_rede
- insumos primários e contas satélite ...... proporcional_vbp | fixa | indicador; EOB = resíduo
- subsetores latentes ...................... produção-base zero + coluna de coeficientes dada à parte

Regiões não desagregadas ficam com o setor agregado (tratado como um grupo de um único "subsetor").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .estrutura import (
    COLUNAS_DF,
    ITENS_IMPOSTOS_PRODUTOS,
    ITENS_PRIMARIOS,
    ITENS_SATELITE,
    MIP,
)
from .modelo import ModeloLeontief

TIPOS_SUBSETOR = ("geracao", "rede", "gas_utilidades")
REGRAS_COLUNA = ("proporcional_vbp", "fixa", "indicador")
REGRAS_LINHA = ("proporcional_vbp", "somente_rede_e_gas", "fixa_por_comprador")
REGRAS_PRIMARIOS = ("proporcional_vbp", "fixa", "indicador")
OPCOES_BLOCO = ("proporcional", "geracao_vende_para_rede")
MODOS_VBP = ("participacoes", "ancora_bloco")
# Itens repartidos por regra; EOB é o resíduo e VA = remunerações + EOB + impostos sobre a produção
ITENS_PRIMARIOS_REPARTIVEIS = ["importacoes", "ipi", "icms", "outros_impostos", "remuneracoes", "impostos_producao"]
ITENS_REPARTIVEIS = ITENS_PRIMARIOS_REPARTIVEIS + ITENS_SATELITE
CURINGA = "*"
TOL_SOMA = 1e-9
TOL_REAGREGACAO = 1e-6

COLS_SUBSETORES = ["codigo", "nome", "tipo"]
COLS_PARTICIPACOES = ["regiao", "subsetor", "participacao", "fonte"]
COLS_REGRAS_COLUNA = ["regiao", "fornecedor", "regiao_fornecedor", "regra", "subsetor", "valor", "fonte"]
COLS_REGRAS_LINHA = ["regiao", "comprador", "regiao_comprador", "regra", "subsetor", "valor", "fixar_no_ras", "fonte"]
COLS_REGRAS_PRIMARIOS = ["regiao", "item", "regra", "subsetor", "valor", "fonte"]
COLS_COEF_LATENTES = ["regiao", "subsetor", "tipo_linha", "regiao_linha", "codigo_linha", "coeficiente", "fonte"]


class EspecificacaoInvalida(ValueError):
    """A especificação é incoerente (erro de parâmetros, não de código)."""


class DesagregacaoInvalida(RuntimeError):
    """A verificação final encontrou FALHA (só levantada com estrito=True)."""


# =============================================================================================
# Especificação
# =============================================================================================
def _tabela(df: pd.DataFrame | None, colunas: list[str]) -> pd.DataFrame:
    """Normaliza uma tabela de parâmetros: garante as colunas, textos sem NaN e espaços."""
    if df is None:
        df = pd.DataFrame(columns=colunas)
    df = df.copy()
    for c in colunas:
        if c not in df.columns:
            df[c] = np.nan
    numericas = {"participacao", "valor", "coeficiente"}
    for c in colunas:
        if c in numericas:
            df[c] = pd.to_numeric(df[c].replace("", np.nan), errors="raise")
        elif c == "fixar_no_ras":
            df[c] = df[c].map(
                lambda v: str(v).strip().lower() in {"1", "true", "sim", "s", "verdadeiro", "yes"}
                if pd.notna(v) else False
            )
        else:
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else str(v).strip())
    return df[colunas].reset_index(drop=True)


@dataclass
class Especificacao:
    """Parâmetros de uma desagregação (ver parametros/LEIAME_parametros.md)."""

    nome: str
    setor_alvo: str
    regioes: list
    subsetores: pd.DataFrame
    participacoes: pd.DataFrame
    bloco: str = "proporcional"
    modo_vbp: str = "participacoes"
    regras_coluna: pd.DataFrame | None = None
    regras_linha: pd.DataFrame | None = None
    regras_primarios: pd.DataFrame | None = None
    coef_latentes: pd.DataFrame | None = None
    ras_tolerancia: float = 1e-8
    ras_max_iter: int = 10000
    aviso: str | None = None
    descricao: str = ""
    arquivos: dict = field(default_factory=dict)

    def __post_init__(self):
        self.regioes = list(self.regioes)
        self.subsetores = _tabela(self.subsetores, COLS_SUBSETORES)
        self.participacoes = _tabela(self.participacoes, COLS_PARTICIPACOES)
        self.regras_coluna = _tabela(self.regras_coluna, COLS_REGRAS_COLUNA)
        self.regras_linha = _tabela(self.regras_linha, COLS_REGRAS_LINHA)
        self.regras_primarios = _tabela(self.regras_primarios, COLS_REGRAS_PRIMARIOS)
        if self.coef_latentes is not None:
            self.coef_latentes = _tabela(self.coef_latentes, COLS_COEF_LATENTES)


def _relativo(caminho: Path) -> str:
    """Caminho relativo à raiz do repositório (para registro), se possível."""
    from .caminhos import RAIZ

    try:
        return Path(caminho).resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        return str(caminho)


def ler_especificacao(caminho_yaml: str | Path) -> Especificacao:
    """Lê a especificação: um YAML com as opções e os nomes dos CSVs (relativos à pasta do YAML)."""
    caminho_yaml = Path(caminho_yaml)
    with open(caminho_yaml, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    pasta = caminho_yaml.parent
    arqs = cfg.get("arquivos", {})

    def ler(chave):
        if not arqs.get(chave):
            return None
        return pd.read_csv(pasta / arqs[chave], dtype=str, keep_default_na=False, comment="#")

    ras = cfg.get("ras", {}) or {}
    return Especificacao(
        nome=cfg["nome"],
        setor_alvo=cfg["setor_alvo"],
        regioes=cfg["regioes"],
        subsetores=ler("subsetores"),
        participacoes=ler("participacoes_vbp"),
        bloco=cfg.get("bloco_intrassetorial", "proporcional"),
        modo_vbp=cfg.get("modo_vbp", "participacoes"),
        regras_coluna=ler("regras_coluna"),
        regras_linha=ler("regras_linha"),
        regras_primarios=ler("regras_primarios"),
        coef_latentes=ler("coef_latentes"),
        ras_tolerancia=float(ras.get("tolerancia", 1e-8)),
        ras_max_iter=int(ras.get("max_iter", 10000)),
        aviso=cfg.get("aviso"),
        descricao=cfg.get("descricao", ""),
        arquivos={k: _relativo(pasta / v) for k, v in arqs.items() if v} | {"especificacao": _relativo(caminho_yaml)},
    )


def validar_especificacao(espec: Especificacao, mip: MIP) -> None:
    """Confere a coerência interna da especificação (levanta EspecificacaoInvalida)."""
    erros = []
    t = espec.setor_alvo
    regs_mip = mip.lista_regioes
    if t not in set(mip.setores["codigo"]):
        erros.append(f"setor-alvo {t} não existe na MIP")
    for r in espec.regioes:
        if r not in regs_mip:
            erros.append(f"região {r} não existe na MIP")
    subs = espec.subsetores
    if len(subs) == 0:
        erros.append("lista de subsetores vazia")
    if subs["codigo"].duplicated().any():
        erros.append("códigos de subsetor repetidos")
    if set(subs["codigo"]) & set(mip.setores["codigo"]):
        erros.append("código de subsetor coincide com código de setor existente")
    tipos_inv = set(subs["tipo"]) - set(TIPOS_SUBSETOR)
    if tipos_inv:
        erros.append(f"tipos de subsetor inválidos: {sorted(tipos_inv)} (válidos: {TIPOS_SUBSETOR})")
    if espec.bloco not in OPCOES_BLOCO:
        erros.append(f"bloco_intrassetorial inválido: {espec.bloco} (válidos: {OPCOES_BLOCO})")
    if espec.modo_vbp not in MODOS_VBP:
        erros.append(f"modo_vbp inválido: {espec.modo_vbp} (válidos: {MODOS_VBP})")
    if espec.modo_vbp == "ancora_bloco" and espec.bloco != "geracao_vende_para_rede":
        erros.append("modo_vbp = ancora_bloco exige bloco_intrassetorial = geracao_vende_para_rede")
    if espec.bloco == "geracao_vende_para_rede":
        if (subs["tipo"] == "rede").sum() != 1:
            erros.append("geracao_vende_para_rede exige exatamente um subsetor do tipo 'rede'")
        if (subs["tipo"] == "geracao").sum() < 1:
            erros.append("geracao_vende_para_rede exige ao menos um subsetor do tipo 'geracao'")
    # participações: uma por (região, subsetor), não negativas, somando 1 em cada região
    p = espec.participacoes
    codigos = set(subs["codigo"])
    for r in espec.regioes:
        pr = p[p["regiao"] == r]
        if set(pr["subsetor"]) != codigos or pr["subsetor"].duplicated().any():
            erros.append(f"participações da região {r}: é preciso exatamente uma linha por subsetor")
            continue
        if (pr["participacao"] < 0).any():
            erros.append(f"participações negativas na região {r}")
        if abs(pr["participacao"].sum() - 1) > TOL_SOMA:
            erros.append(f"participações da região {r} somam {pr['participacao'].sum():.12f} (≠ 1)")
    if set(p["regiao"]) - set(espec.regioes):
        erros.append(f"participações para regiões não desagregadas: {sorted(set(p['regiao']) - set(espec.regioes))}")
    # regras: nomes válidos e subsetores existentes
    for nome, tab, validas in (
        ("regras_coluna", espec.regras_coluna, REGRAS_COLUNA),
        ("regras_linha", espec.regras_linha, REGRAS_LINHA),
        ("regras_primarios", espec.regras_primarios, REGRAS_PRIMARIOS),
    ):
        inv = set(tab["regra"]) - set(validas)
        if inv:
            erros.append(f"{nome}: regras inválidas {sorted(inv)} (válidas: {validas})")
        subs_inv = set(tab["subsetor"]) - codigos - {""}
        if subs_inv:
            erros.append(f"{nome}: subsetores inexistentes {sorted(subs_inv)}")
    itens_inv = set(espec.regras_primarios["item"]) - set(ITENS_REPARTIVEIS) - {CURINGA}
    if itens_inv:
        erros.append(
            f"regras_primarios: itens inválidos {sorted(itens_inv)} (válidos: {ITENS_REPARTIVEIS}; "
            "EOB é o resíduo e VA é calculado, não recebem regra)"
        )
    if espec.coef_latentes is not None and len(espec.coef_latentes):
        cl = espec.coef_latentes
        for (r, s) in cl[["regiao", "subsetor"]].drop_duplicates().itertuples(index=False):
            linha = p[(p["regiao"] == r) & (p["subsetor"] == s)]
            if r not in espec.regioes or s not in codigos:
                erros.append(f"coef_latentes: subsetor {r} {s} não faz parte da desagregação")
            elif espec.modo_vbp == "participacoes" and len(linha) and linha["participacao"].iloc[0] != 0:
                erros.append(f"coef_latentes: subsetor {r} {s} tem participação não nula (latente exige produção zero)")
        tl_inv = set(cl["tipo_linha"]) - {"setor", "satelite"}
        if tl_inv:
            erros.append(f"coef_latentes: tipo_linha inválido {sorted(tl_inv)}")
    if erros:
        raise EspecificacaoInvalida("especificação inválida:\n  - " + "\n  - ".join(erros))


# =============================================================================================
# Resolução das regras
# =============================================================================================
@dataclass
class _Grupo:
    """Um grupo de regras com a mesma chave (ex.: região RS, fornecedor S04, qualquer região)."""

    chave: dict
    regra: str
    valores: dict
    fonte: str
    fixar: bool = False


def _agrupar(tab: pd.DataFrame, chave_cols: list[str], nome: str) -> list[_Grupo]:
    grupos = []
    if len(tab) == 0:
        return grupos
    for chave, g in tab.groupby(chave_cols, sort=False):
        chave = dict(zip(chave_cols, chave if isinstance(chave, tuple) else (chave,)))
        regras = g["regra"].unique()
        if len(regras) != 1:
            raise EspecificacaoInvalida(f"{nome}: chave {chave} com mais de uma regra: {list(regras)}")
        valores = {}
        for s, v in zip(g["subsetor"], g["valor"]):
            if s:
                if s in valores:
                    raise EspecificacaoInvalida(f"{nome}: chave {chave}: subsetor {s} repetido")
                valores[s] = float(v)
        fontes = "; ".join(dict.fromkeys(f for f in g["fonte"] if f))
        fixar = bool(g["fixar_no_ras"].any()) if "fixar_no_ras" in g else False
        grupos.append(_Grupo(chave, regras[0], valores, fontes, fixar))
    return grupos


def _escolher(grupos: list[_Grupo], pontuar, descricao: str) -> _Grupo | None:
    """Regra aplicável mais específica (maior pontuação); empate entre regras diferentes = erro."""
    melhores, melhor = [], -1
    for g in grupos:
        p = pontuar(g.chave)
        if p is None:
            continue
        if p > melhor:
            melhores, melhor = [g], p
        elif p == melhor:
            melhores.append(g)
    if not melhores:
        return None
    if len(melhores) > 1:
        raise EspecificacaoInvalida(
            f"{descricao}: regras ambíguas (mesma especificidade): {[g.chave for g in melhores]}"
        )
    return melhores[0]


def _casa(valor_regra: str, *aceitos) -> bool:
    return valor_regra in (CURINGA, "") or valor_regra in aceitos


@dataclass
class _GrupoAlvo:
    """Subsetores do setor-alvo numa região (ou o setor agregado, se a região não é desagregada)."""

    regiao: str
    idx_orig: int
    idx_novo: list
    codigos: list
    tipos: list
    s: np.ndarray  # participações efetivas no VBP
    desagregado: bool


def _pesos(grupo: _Grupo | None, ga: _GrupoAlvo, descricao: str) -> tuple[np.ndarray, str, str]:
    """Pesos de repartição entre os subsetores (somam 1). Devolve (pesos, regra, fonte)."""
    s = ga.s
    if not ga.desagregado:
        return np.ones(1), "agregado", ""
    regra = grupo.regra if grupo else "proporcional_vbp"
    fonte = grupo.fonte if grupo else "padrão (proporcional ao VBP)"
    if regra == "proporcional_vbp":
        w = s / s.sum()
    elif regra in ("fixa", "fixa_por_comprador"):
        w = np.array([grupo.valores.get(c, 0.0) for c in ga.codigos])
        if (w < 0).any() or abs(w.sum() - 1) > TOL_SOMA:
            raise EspecificacaoInvalida(f"{descricao}: participações fixas devem ser ≥ 0 e somar 1 (soma = {w.sum()})")
    elif regra == "indicador":
        faltam = [c for c, sk in zip(ga.codigos, s) if sk > 0 and c not in grupo.valores]
        if faltam:
            raise EspecificacaoInvalida(f"{descricao}: indicador sem valor para {faltam}")
        ind = np.array([grupo.valores.get(c, 0.0) for c in ga.codigos])
        if (ind < 0).any():
            raise EspecificacaoInvalida(f"{descricao}: indicador negativo")
        base = s * ind
        if base.sum() <= 0:
            raise EspecificacaoInvalida(f"{descricao}: Σ VBP × indicador = 0")
        w = base / base.sum()
    elif regra == "somente_rede_e_gas":
        m = np.isin(ga.tipos, ["rede", "gas_utilidades"])
        base = np.where(m, s, 0.0)
        if base.sum() <= 0:
            raise EspecificacaoInvalida(f"{descricao}: somente_rede_e_gas, mas rede e gás têm VBP zero")
        w = base / base.sum()
    else:  # pragma: no cover - validado antes
        raise EspecificacaoInvalida(f"{descricao}: regra desconhecida {regra}")
    if ((w > 0) & (s == 0)).any():
        zerados = [c for c, wk, sk in zip(ga.codigos, w, s) if wk > 0 and sk == 0]
        raise EspecificacaoInvalida(
            f"{descricao}: regra '{regra}' atribui valor a subsetor com produção zero: {zerados}"
        )
    return w, regra, fonte


# =============================================================================================
# RAS (biproporcional)
# =============================================================================================
@dataclass
class InfoRAS:
    contexto: str
    necessario: bool
    convergiu: bool
    iteracoes: int
    erro_max: float
    erro_inicial: float


def ras(
    M0: np.ndarray,
    alvo_linhas: np.ndarray,
    alvo_colunas: np.ndarray,
    fixas: np.ndarray | None = None,
    tol: float = 1e-8,
    max_iter: int = 10000,
    contexto: str = "",
) -> tuple[np.ndarray, InfoRAS]:
    """Ajuste biproporcional: escala linhas e colunas de M0 até bater com os totais-alvo.

    Células marcadas em `fixas` não mudam (seus valores são descontados dos alvos). Células livres
    devem ser ≥ 0; zeros continuam zero. Devolve a matriz ajustada e o relatório de convergência.
    """
    M0 = np.asarray(M0, dtype=float)
    fixas = np.zeros_like(M0, dtype=bool) if fixas is None else np.asarray(fixas, dtype=bool)
    livre = np.where(fixas, 0.0, M0)
    if (livre < 0).any():
        raise ValueError("RAS: células livres negativas (marque-as como fixas)")
    F = np.where(fixas, M0, 0.0)
    u = np.asarray(alvo_linhas, dtype=float) - F.sum(axis=1)
    v = np.asarray(alvo_colunas, dtype=float) - F.sum(axis=0)

    def erro(M):
        return max(np.abs(M.sum(axis=1) - u).max(initial=0.0), np.abs(M.sum(axis=0) - v).max(initial=0.0))

    M = livre.copy()
    e0 = erro(M)
    if e0 <= tol:
        return M + F, InfoRAS(contexto, False, True, 0, e0, e0)
    it = 0
    for it in range(1, max_iter + 1):
        rs = M.sum(axis=1)
        M *= np.where(rs > 0, u / np.where(rs > 0, rs, 1.0), 1.0)[:, None]
        cs = M.sum(axis=0)
        M *= np.where(cs > 0, v / np.where(cs > 0, cs, 1.0), 1.0)[None, :]
        e = erro(M)
        if e <= tol:
            return M + F, InfoRAS(contexto, True, True, it, e, e0)
    return M + F, InfoRAS(contexto, True, False, it, erro(M), e0)


# =============================================================================================
# Resultado
# =============================================================================================
@dataclass
class ResultadoDesagregacao:
    mip: MIP
    original: MIP
    especificacao: Especificacao
    mapa: pd.DataFrame
    pesos: pd.DataFrame
    info_ras: pd.DataFrame
    checagens: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def ok(self) -> bool:
        return not (self.checagens["status"] == "FALHA").any()

    @property
    def alertas(self) -> pd.DataFrame:
        return self.checagens[self.checagens["status"] == "ALERTA"]

    def leiame(self) -> list[str]:
        e = self.especificacao
        linhas = []
        if e.aviso:
            linhas += [e.aviso, ""]
        linhas += [
            f"MIP desagregada — especificação: {e.nome}",
            e.descricao,
            f"Setor desagregado: {e.setor_alvo}, nas regiões {', '.join(e.regioes)}; "
            f"subsetores: {', '.join(e.subsetores['codigo'])}.",
            f"Bloco intrassetorial: {e.bloco}; modo do VBP: {e.modo_vbp}.",
            "A soma dos subsetores reproduz cada célula da MIP original (ver aba checagens).",
            "EOB de cada subsetor = resíduo que fecha a coluna (EOB negativo é sinalizado em checagens, não corrigido).",
            "Aba principal: mesmo layout da planilha original, com os subsetores no lugar do setor-alvo.",
            "Abas: mapa_setores (original → novo), parametros (todos os pesos usados, com fonte), "
            "checagens, ras (conciliação das linhas), coef_latentes (se houver subsetores latentes).",
            "Subsetores latentes: produção-base zero; a coluna de coeficientes técnicos fica na aba coef_latentes "
            "(não aparece como fluxo) e é usada pelo modelo para simular choques nesses subsetores.",
            f"Arquivos de parâmetros: {'; '.join(f'{k}={v}' for k, v in e.arquivos.items())}",
        ]
        if e.aviso:
            linhas += ["", e.aviso]
        return linhas

    def exportar(self, caminho_xlsx: str | Path, caminho_csv: str | Path | None = None) -> None:
        from .exportacao import exportar_longo, exportar_xlsx

        abas = {
            "mapa_setores": self.mapa,
            "parametros": self.pesos,
            "checagens": self.checagens,
            "ras": self.info_ras,
        }
        if self.mip.coef_latentes is not None and len(self.mip.coef_latentes):
            abas["coef_latentes"] = self.mip.coef_latentes
        sub_ids = list(self.mapa.loc[self.mapa["desagregado"], "id_novo"])
        exportar_xlsx(
            self.mip,
            caminho_xlsx,
            aviso_topo=self.especificacao.aviso,
            leiame=self.leiame(),
            abas_extras=abas,
            destacar_setores=sub_ids,
        )
        if caminho_csv is not None:
            exportar_longo(self.mip, caminho_csv)


# =============================================================================================
# Desagregação
# =============================================================================================
def _participacoes_efetivas(espec: Especificacao, mip: MIP, idx_alvo: dict) -> dict[str, np.ndarray]:
    """Participações no VBP de cada região desagregada (modo 'participacoes' ou 'ancora_bloco')."""
    subs = espec.subsetores
    tipos = subs["tipo"].to_numpy()
    saida = {}
    for r in espec.regioes:
        p = espec.participacoes[espec.participacoes["regiao"] == r].set_index("subsetor")["participacao"]
        s = p.reindex(subs["codigo"]).to_numpy(dtype=float)
        if espec.modo_vbp == "ancora_bloco":
            i = idx_alvo[r]
            G = sum(mip.Z[i, idx_alvo[r2]] for r2 in idx_alvo)  # vendas ao setor-alvo de todas as regiões
            Xr = mip.X[i]
            ger = tipos == "geracao"
            sg, sn = s[ger].sum(), s[~ger].sum()
            if (G > 0 and sg <= 0) or (Xr - G > 0 and sn <= 0):
                raise EspecificacaoInvalida(f"ancora_bloco na região {r}: grupo sem participação positiva")
            novo = np.zeros_like(s)
            novo[ger] = (G / Xr) * s[ger] / sg if sg > 0 else 0.0
            novo[~ger] = ((Xr - G) / Xr) * s[~ger] / sn if sn > 0 else 0.0
            s = novo
        saida[r] = s
    return saida


def _matriz_agregacao(mapa: pd.DataFrame, n_orig: int, n_novo: int) -> np.ndarray:
    P = np.zeros((n_orig, n_novo))
    P[mapa["indice_original"].to_numpy(), mapa["indice_novo"].to_numpy()] = 1.0
    return P


def agregar(mip_novo: MIP, mapa: pd.DataFrame, setores_originais: pd.DataFrame) -> MIP:
    """Re-agrega a MIP desagregada (soma os subsetores) para a classificação original."""
    P = _matriz_agregacao(mapa, len(setores_originais), mip_novo.n)
    return MIP(
        setores=setores_originais[["regiao", "codigo", "nome"]].copy(),
        Z=P @ mip_novo.Z @ P.T,
        F=P @ mip_novo.F,
        total_linha=P @ mip_novo.total_linha,
        X=P @ mip_novo.X,
        V=mip_novo.V @ P.T,
        V_df=mip_novo.V_df.copy(),
        X_df=mip_novo.X_df.copy(),
        S=mip_novo.S @ P.T,
        totais_ev=dict(mip_novo.totais_ev),
        titulo=mip_novo.titulo,
    )


def desagregar(mip: MIP, espec: Especificacao, estrito: bool = True) -> ResultadoDesagregacao:
    """Desagrega `espec.setor_alvo` em subsetores e verifica o resultado.

    Com estrito=True, levanta DesagregacaoInvalida se alguma checagem der FALHA
    (ALERTA, como EOB negativo, não interrompe: fica registrado nas checagens).
    """
    validar_especificacao(espec, mip)
    t = espec.setor_alvo
    regs = mip.lista_regioes
    subs = espec.subsetores
    K = len(subs)
    idx_alvo = {r: mip.indice(r, t) for r in regs}
    s_ef = _participacoes_efetivas(espec, mip, idx_alvo)

    # ---- nova lista de setores e mapa ----------------------------------------------------------
    novos, grupos = [], {}
    for i, s in enumerate(mip.setores.itertuples(index=False)):
        if s.codigo == t and s.regiao in espec.regioes:
            ini = len(novos)
            for k, sub in enumerate(subs.itertuples(index=False)):
                novos.append((s.regiao, sub.codigo, sub.nome, i, s.codigo, s.nome, sub.tipo, s_ef[s.regiao][k], True))
            grupos[s.regiao] = _GrupoAlvo(
                s.regiao, i, list(range(ini, ini + K)), list(subs["codigo"]), list(subs["tipo"]), s_ef[s.regiao], True
            )
        else:
            novos.append((s.regiao, s.codigo, s.nome, i, s.codigo, s.nome, "", 1.0, False))
            if s.codigo == t:
                grupos[s.regiao] = _GrupoAlvo(s.regiao, i, [len(novos) - 1], [s.codigo], ["agregado"], np.ones(1), False)
    mapa = pd.DataFrame(
        novos,
        columns=["regiao", "codigo_novo", "nome_novo", "indice_original", "codigo_original", "nome_original",
                 "tipo_subsetor", "participacao_vbp", "desagregado"],
    )
    mapa.insert(0, "indice_novo", np.arange(len(mapa)))
    mapa["id_original"] = mapa["regiao"] + "_" + mapa["codigo_original"]
    mapa["id_novo"] = mapa["regiao"] + "_" + mapa["codigo_novo"]
    n2 = len(mapa)
    setores2 = mapa[["regiao", "codigo_novo", "nome_novo"]].rename(columns={"codigo_novo": "codigo", "nome_novo": "nome"})

    fora = np.array([i for i in range(mip.n) if mip.setores["codigo"][i] != t])  # índices originais fora do bloco
    fora2 = mapa.set_index("indice_original").loc[fora, "indice_novo"].to_numpy()  # (únicos: não são alvo)

    reg_orig = mip.setores["regiao"].to_numpy()
    cod_orig = mip.setores["codigo"].to_numpy()
    pesos_reg = []  # registro de todos os pesos usados

    def registrar(dimensao, ga, chave, regra, fonte, w, etapa="regra"):
        if not ga.desagregado:
            return
        linha = {"dimensao": dimensao, "regiao": ga.regiao, "chave": chave, "regra": regra, "etapa": etapa, "fonte": fonte}
        linha.update({c: float(x) for c, x in zip(ga.codigos, w)})
        pesos_reg.append(linha)

    for r, ga in grupos.items():
        registrar("vbp", ga, "participacao_vbp", espec.modo_vbp,
                  "; ".join(dict.fromkeys(espec.participacoes.loc[espec.participacoes["regiao"] == r, "fonte"])), ga.s)

    # ---- Z, F, X -------------------------------------------------------------------------------
    Z2 = np.zeros((n2, n2))
    F2 = np.zeros((n2, len(COLUNAS_DF)))
    X2 = np.zeros(n2)
    T2 = np.zeros(n2)
    Z2[np.ix_(fora2, fora2)] = mip.Z[np.ix_(fora, fora)]
    F2[fora2] = mip.F[fora]
    X2[fora2] = mip.X[fora]
    T2[fora2] = mip.total_linha[fora]
    for ga in grupos.values():
        X2[ga.idx_novo] = ga.s * mip.X[ga.idx_orig]
        T2[ga.idx_novo] = ga.s * mip.total_linha[ga.idx_orig]

    # colunas (insumos de fornecedores fora do bloco)
    g_col = _agrupar(espec.regras_coluna, ["regiao", "fornecedor", "regiao_fornecedor"], "regras_coluna")
    for r, ga in grupos.items():
        j = ga.idx_orig
        for i, i2 in zip(fora, fora2):
            def pont(ch, r=r, i=i):
                if not (_casa(ch["regiao"], r) and _casa(ch["fornecedor"], cod_orig[i]) and _casa(ch["regiao_fornecedor"], reg_orig[i])):
                    return None
                return (ch["regiao"] not in ("", CURINGA)) + 2 * (ch["fornecedor"] not in ("", CURINGA)) + (ch["regiao_fornecedor"] not in ("", CURINGA))
            g = _escolher(g_col, pont, f"coluna {r} {t} ← {reg_orig[i]} {cod_orig[i]}") if ga.desagregado else None
            w, regra, fonte = _pesos(g, ga, f"coluna {r} {t} ← {reg_orig[i]} {cod_orig[i]}")
            Z2[i2, ga.idx_novo] = w * mip.Z[i, j]
            registrar("coluna", ga, f"{reg_orig[i]} {cod_orig[i]}", regra, fonte, w)

    # bloco intrassetorial
    bloco_linhas = {r: np.zeros(len(ga.idx_novo)) for r, ga in grupos.items()}
    for r, gv in grupos.items():
        for r2, gc in grupos.items():
            B = mip.Z[gv.idx_orig, gc.idx_orig]
            if espec.bloco == "proporcional":
                wv, wc = gv.s, gc.s
            else:  # geracao_vende_para_rede
                if gv.desagregado:
                    ger = np.array(gv.tipos) == "geracao"
                    sg = gv.s[ger].sum()
                    if sg <= 0 and B != 0:
                        raise EspecificacaoInvalida(f"geracao_vende_para_rede: {r} sem geração com VBP > 0, mas fluxo {r}→{r2} = {B}")
                    wv = np.where(ger, gv.s / sg, 0.0) if sg > 0 else np.zeros(len(gv.s))
                else:
                    wv = np.ones(1)
                if gc.desagregado:
                    wc = (np.array(gc.tipos) == "rede").astype(float)
                    if gc.s[wc == 1].sum() <= 0 and B != 0:
                        raise EspecificacaoInvalida(f"geracao_vende_para_rede: rede de {r2} com VBP zero não pode comprar {B}")
                else:
                    wc = np.ones(1)
            cel = np.outer(wv, wc) * B
            Z2[np.ix_(gv.idx_novo, gc.idx_novo)] = cel
            bloco_linhas[r] += cel.sum(axis=1)
            if gv.desagregado:
                for k, cod in enumerate(gv.codigos):
                    if gv.s[k] > 0 or cel[k].any():
                        linha = {"dimensao": "bloco", "regiao": r, "chave": f"{r}→{r2}: vendedor {cod}",
                                 "regra": espec.bloco, "etapa": "regra", "fonte": "fração do fluxo original"}
                        linha.update({c: float(x) for c, x in zip(gc.codigos, cel[k] / B if B else cel[k] * 0)})
                        pesos_reg.append(linha)

    # linhas (vendas a compradores fora do bloco e à demanda final) + RAS
    g_lin = _agrupar(espec.regras_linha, ["regiao", "comprador", "regiao_comprador"], "regras_linha")
    infos = []
    ndf = len(COLUNAS_DF)
    for r, ga in grupos.items():
        i = ga.idx_orig
        m = len(fora) + ndf
        alvo_col = np.concatenate([mip.Z[i, fora], mip.F[i]])
        M0 = np.zeros((len(ga.idx_novo), m))
        fix = np.zeros_like(M0, dtype=bool)
        chaves = []
        for jj in range(m):
            if jj < len(fora):
                j = fora[jj]
                cj, rj = cod_orig[j], reg_orig[j]
                desc = f"linha {r} {t} → {rj} {cj}"

                def pont(ch, r=r, cj=cj, rj=rj):
                    if not (_casa(ch["regiao"], r) and _casa(ch["comprador"], cj, "CI") and _casa(ch["regiao_comprador"], rj)):
                        return None
                    c = ch["comprador"]
                    return (ch["regiao"] not in ("", CURINGA)) + (3 if c == cj else 1 if c == "CI" else 0) + (ch["regiao_comprador"] not in ("", CURINGA))
                chave = f"{rj} {cj}"
            else:
                d = COLUNAS_DF.iloc[jj - len(fora)]
                desc = f"linha {r} {t} → {d.codigo}"

                def pont(ch, r=r, d=d):
                    if not (_casa(ch["regiao"], r) and _casa(ch["comprador"], d.codigo, d.tipo, "DF") and _casa(ch["regiao_comprador"], d.regiao)):
                        return None
                    c = ch["comprador"]
                    return (ch["regiao"] not in ("", CURINGA)) + (3 if c == d.codigo else 2 if c == d.tipo else 1 if c == "DF" else 0) + (ch["regiao_comprador"] not in ("", CURINGA))
                chave = d.codigo
            g = _escolher(g_lin, pont, desc) if ga.desagregado else None
            w, regra, fonte = _pesos(g, ga, desc)
            M0[:, jj] = w * alvo_col[jj]
            fix[:, jj] = (alvo_col[jj] < 0) or (g is not None and g.fixar)
            chaves.append(chave)
            registrar("linha", ga, chave, regra, fonte, w)
        alvo_lin = X2[ga.idx_novo] - bloco_linhas[r]
        if ga.desagregado:
            # inviabilidade estrutural: linha sem células livres com total ≠ 0
            livres = np.where(fix, 0.0, M0).sum(axis=1)
            resid = alvo_lin - np.where(fix, M0, 0.0).sum(axis=1)
            tol_inv = max(espec.ras_tolerancia, 1e-9 * mip.X[i])
            for k in np.flatnonzero(resid < -tol_inv):
                raise EspecificacaoInvalida(
                    f"linha de {r} {ga.codigos[k]}: o VBP ({X2[ga.idx_novo[k]]:.4f}) é menor que as vendas já "
                    f"fixadas (bloco {bloco_linhas[r][k]:.4f} + células fixas); resta {resid[k]:.4f} < 0. "
                    "Ajuste as participações no VBP (ou use modo_vbp = ancora_bloco)."
                )
            for k in np.flatnonzero((livres <= 0) & (np.abs(resid) > tol_inv)):
                raise EspecificacaoInvalida(
                    f"linha de {r} {ga.codigos[k]}: o VBP ({X2[ga.idx_novo[k]]:.4f}) menos as vendas no bloco "
                    f"({bloco_linhas[r][k]:.4f}) deixa {resid[k]:.4f} a vender, mas as regras de linha não lhe permitem "
                    "vender a nenhum comprador fora do bloco. Ajuste as participações (ou use modo_vbp = ancora_bloco)."
                )
            tol = max(espec.ras_tolerancia, 1e-14 * mip.X[i])  # piso: precisão numérica das somas
            M, info = ras(M0, alvo_lin, alvo_col, fix, tol=tol, max_iter=espec.ras_max_iter, contexto=f"linhas {r} {t}")
            infos.append(info)
            if info.necessario:
                for jj, chave in enumerate(chaves):
                    if alvo_col[jj] != 0:
                        w_real = M[:, jj] / alvo_col[jj]
                        registrar("linha", ga, chave, "realizado_apos_RAS", "RAS", w_real, etapa="apos_RAS")
        else:
            M = M0
        Z2[np.ix_(ga.idx_novo, fora2)] = M[:, : len(fora)]
        F2[ga.idx_novo] = M[:, len(fora):]

    # ---- insumos primários e contas satélite -------------------------------------------------
    V2 = np.zeros((len(ITENS_PRIMARIOS), n2))
    S2 = np.zeros((len(ITENS_SATELITE), n2))
    V2[:, fora2] = mip.V[:, fora]
    S2[:, fora2] = mip.S[:, fora]
    g_pri = _agrupar(espec.regras_primarios, ["regiao", "item"], "regras_primarios")
    ip = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}
    isat = {it: k for k, it in enumerate(ITENS_SATELITE)}
    for r, ga in grupos.items():
        j = ga.idx_orig
        if not ga.desagregado:
            V2[:, ga.idx_novo[0]] = mip.V[:, j]
            S2[:, ga.idx_novo[0]] = mip.S[:, j]
            continue
        for item in ITENS_REPARTIVEIS:
            def pont(ch, r=r, item=item):
                if not (_casa(ch["regiao"], r) and _casa(ch["item"], item)):
                    return None
                return (ch["regiao"] not in ("", CURINGA)) + 2 * (ch["item"] not in ("", CURINGA))
            g = _escolher(g_pri, pont, f"{item} {r} {t}")
            w, regra, fonte = _pesos(g, ga, f"{item} {r} {t}")
            if item in ip:
                V2[ip[item], ga.idx_novo] = w * mip.V[ip[item], j]
            else:
                S2[isat[item], ga.idx_novo] = w * mip.S[isat[item], j]
            registrar("primarios_satelite", ga, item, regra, fonte, w)
        # EOB = resíduo da coluna; o resíduo contábil original do setor é repartido pelo VBP
        idx = ga.idx_novo

        def custos(Zc, Vc, cols):
            return (Zc[:, cols].sum(axis=0) + Vc[ip["importacoes"], cols]
                    + sum(Vc[ip[x], cols] for x in ITENS_IMPOSTOS_PRODUTOS)
                    + Vc[ip["remuneracoes"], cols] + Vc[ip["impostos_producao"], cols])

        rho = mip.V[ip["eob"], j] - (mip.X[j] - custos(mip.Z, mip.V, [j])[0])
        V2[ip["eob"], idx] = X2[idx] - custos(Z2, V2, idx) + ga.s * rho
        eps = mip.V[ip["va"], j] - (mip.V[ip["remuneracoes"], j] + mip.V[ip["eob"], j] + mip.V[ip["impostos_producao"], j])
        V2[ip["va"], idx] = V2[ip["remuneracoes"], idx] + V2[ip["eob"], idx] + V2[ip["impostos_producao"], idx] + ga.s * eps
        registrar("primarios_satelite", ga, "eob", "residuo", "fecha a coluna", V2[ip["eob"], idx] / mip.V[ip["eob"], j] if mip.V[ip["eob"], j] else V2[ip["eob"], idx] * 0)

    # ---- coeficientes latentes ---------------------------------------------------------------
    coef_lat = None
    if espec.coef_latentes is not None and len(espec.coef_latentes):
        coef_lat = espec.coef_latentes.copy()
        ids2 = set(zip(setores2["regiao"], setores2["codigo"]))
        for rr in coef_lat.itertuples(index=False):
            if rr.tipo_linha == "setor" and (rr.regiao_linha, rr.codigo_linha) not in ids2:
                raise EspecificacaoInvalida(f"coef_latentes: linha {rr.regiao_linha} {rr.codigo_linha} não existe na MIP desagregada")
            if rr.tipo_linha == "satelite" and rr.codigo_linha not in ITENS_SATELITE:
                raise EspecificacaoInvalida(f"coef_latentes: item satélite {rr.codigo_linha} inválido")
        for (r, s) in coef_lat[["regiao", "subsetor"]].drop_duplicates().itertuples(index=False):
            k = list(grupos[r].codigos).index(s)
            if grupos[r].s[k] != 0:
                raise EspecificacaoInvalida(f"coef_latentes: {r} {s} tem produção-base não nula")

    mip2 = MIP(
        setores=setores2,
        Z=Z2,
        F=F2,
        total_linha=T2,
        X=X2,
        V=V2,
        V_df=mip.V_df.copy(),
        X_df=mip.X_df.copy(),
        S=S2,
        totais_ev=dict(mip.totais_ev),
        coef_latentes=coef_lat,
        titulo=mip.titulo,
    )
    pesos = pd.DataFrame(pesos_reg)
    info_ras = pd.DataFrame([vars(x) for x in infos])
    res = ResultadoDesagregacao(mip2, mip, espec, mapa, pesos, info_ras)
    res.checagens = verificar(res)
    if estrito and not res.ok:
        falhas = res.checagens[res.checagens["status"] == "FALHA"]
        raise DesagregacaoInvalida("verificação falhou:\n" + falhas.to_string(index=False))
    return res


# =============================================================================================
# Verificação
# =============================================================================================
def verificar(res: ResultadoDesagregacao) -> pd.DataFrame:
    """Checagens obrigatórias ao final da desagregação. Status: OK | ALERTA | FALHA."""
    m2, m1, mapa = res.mip, res.original, res.mapa
    linhas = []

    def add(nome, ok, valor, tol, detalhe="", alerta=False):
        status = "OK" if ok else ("ALERTA" if alerta else "FALHA")
        linhas.append((nome, status, valor, tol, detalhe))

    # 1) re-agregação
    ag = agregar(m2, mapa, m1.setores)
    for nome in ["Z", "F", "X", "total_linha", "V", "S", "V_df", "X_df"]:
        d = float(np.abs(getattr(ag, nome) - getattr(m1, nome)).max())
        add(f"reagregacao_{nome}", d <= TOL_REAGREGACAO, d, TOL_REAGREGACAO, "máx |Σ subsetores − original|")
    d = max((abs(m2.totais_ev[k] - m1.totais_ev[k]) for k in m1.totais_ev), default=0.0)
    add("reagregacao_totais_EV", d <= TOL_REAGREGACAO, d, TOL_REAGREGACAO)

    sub = mapa.loc[mapa["desagregado"], "indice_novo"].to_numpy()
    orig_de = mapa["indice_original"].to_numpy()
    if len(sub) == 0:
        return pd.DataFrame(linhas, columns=["checagem", "status", "valor", "tolerancia", "detalhe"])
    s = mapa["participacao_vbp"].to_numpy()

    # 2) balanço de linha e de coluna de cada subsetor
    rl = m2.Z.sum(axis=1) + m2.F.sum(axis=1) - m2.X
    rl1 = m1.Z.sum(axis=1) + m1.F.sum(axis=1) - m1.X
    lim = TOL_REAGREGACAO + np.abs(s * rl1[orig_de])
    d = np.abs(rl[sub]) - lim[sub]
    add("balanco_linha_subsetores", (d <= 0).all(), float(np.abs(rl[sub]).max()), TOL_REAGREGACAO,
        "máx |Σ vendas − VBP| nos subsetores (tolerância + resíduo original × participação)")
    ip = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}

    def res_col(m):
        return (m.Z.sum(axis=0) + m.V[ip["importacoes"]] + sum(m.V[ip[x]] for x in ITENS_IMPOSTOS_PRODUTOS)
                + m.V[ip["va"]] - m.X)

    rc, rc1 = res_col(m2), res_col(m1)
    d = np.abs(rc[sub] - s[sub] * rc1[orig_de[sub]])
    add("balanco_coluna_subsetores", (d <= TOL_REAGREGACAO).all(), float(d.max()), TOL_REAGREGACAO,
        "máx |resíduo da coluna − participação × resíduo original| (o resíduo original é repartido pelo VBP)")
    dva = np.abs(m2.V[ip["va"]] - m2.V[ip["remuneracoes"]] - m2.V[ip["eob"]] - m2.V[ip["impostos_producao"]])
    dva1 = np.abs(m1.V[ip["va"]] - m1.V[ip["remuneracoes"]] - m1.V[ip["eob"]] - m1.V[ip["impostos_producao"]])
    add("identidade_VA_subsetores", (dva[sub] <= TOL_REAGREGACAO + dva1[orig_de[sub]]).all(), float(dva[sub].max()),
        TOL_REAGREGACAO, "VA − (remunerações + EOB + impostos sobre a produção)")

    # 3) não negatividade (exceto onde a original já tem negativos)
    neg = []
    Zo = m1.Z[np.ix_(orig_de, orig_de)]
    for (a, b) in zip(*np.nonzero((m2.Z < -1e-12) & (Zo >= 0))):
        neg.append(f"Z[{m2.setores['id'][a]},{m2.setores['id'][b]}]")
    Fo = m1.F[orig_de]
    for (a, b) in zip(*np.nonzero((m2.F < -1e-12) & (Fo >= 0))):
        neg.append(f"F[{m2.setores['id'][a]},{COLUNAS_DF['codigo'][b]}]")
    for it in ITENS_PRIMARIOS:
        if it in ("eob", "va"):
            continue
        k = ip[it]
        for b in np.flatnonzero((m2.V[k] < -1e-12) & (m1.V[k, orig_de] >= 0)):
            neg.append(f"{it}[{m2.setores['id'][b]}]")
    for k, it in enumerate(ITENS_SATELITE):
        for b in np.flatnonzero((m2.S[k] < -1e-12) & (m1.S[k, orig_de] >= 0)):
            neg.append(f"{it}[{m2.setores['id'][b]}]")
    for b in np.flatnonzero(m2.X < 0):
        neg.append(f"VBP[{m2.setores['id'][b]}]")
    add("nao_negatividade", not neg, len(neg), 0,
        "negativos só onde a original já tem (coluna de discrepância, EOB, impostos sobre a produção); "
        + (", ".join(neg[:20]) if neg else "nenhum negativo novo"))

    # 4) totais das contas satélite preservados (por região e setor original)
    for k, it in enumerate(ITENS_SATELITE):
        d = float(np.abs(m2.S[k] @ _matriz_agregacao(mapa, m1.n, m2.n).T - m1.S[k]).max())
        add(f"satelite_{it}_preservado", d <= TOL_REAGREGACAO, d, TOL_REAGREGACAO)

    # 5) EOB ≥ 0 em todos os subsetores com produção (sinalizado, não corrigido)
    eob = m2.V[ip["eob"]]
    neg_eob = [f"{m2.setores['id'][b]} ({eob[b]:.4f})" for b in sub if eob[b] < -1e-9]
    add("EOB_nao_negativo_subsetores", not neg_eob, float(eob[sub].min()), 0,
        "EOB negativo (sinalizado, NÃO corrigido): " + ", ".join(neg_eob) if neg_eob else "todos ≥ 0", alerta=True)

    # 6) subsetores com produção zero: linha e coluna zeradas
    zeros = [b for b in sub if m2.X[b] == 0]
    ruins = [m2.setores["id"][b] for b in zeros
             if m2.Z[b].any() or m2.Z[:, b].any() or m2.F[b].any() or m2.V[:, b].any() or m2.S[:, b].any()]
    add("subsetores_producao_zero_zerados", not ruins, len(zeros), 0,
        ("com valores: " + ", ".join(ruins)) if ruins else
        f"{len(zeros)} subsetor(es) com produção zero: " + ", ".join(m2.setores["id"][b] for b in zeros))

    # 7) L ≥ 0 e diagonal ≥ 1 (inclui colunas latentes)
    mod = ModeloLeontief(m2)
    add("L_nao_negativa", mod.L.min() >= -1e-10, float(mod.L.min()), -1e-10)
    add("L_diagonal_maior_igual_1", np.diag(mod.L).min() >= 1 - 1e-10, float(np.diag(mod.L).min()), 1.0)
    cs = mod.A.sum(axis=0)
    add("A_soma_colunas_menor_1", (cs < 1).all(), float(cs.max()), 1.0, "Σ coeficientes técnicos de cada coluna", alerta=True)

    # 8) RAS
    if len(res.info_ras):
        ok = bool(res.info_ras["convergiu"].all())
        add("RAS_convergencia", ok, int(res.info_ras["iteracoes"].max()), res.especificacao.ras_max_iter,
            "; ".join(f"{r.contexto}: {'necessário' if r.necessario else 'não necessário'}, "
                      f"{'convergiu' if r.convergiu else 'NÃO convergiu'} em {r.iteracoes} iterações, "
                      f"erro {r.erro_max:.2e} (inicial {r.erro_inicial:.2e})" for r in res.info_ras.itertuples()))

    # 9) latentes
    if m2.coef_latentes is not None and len(m2.coef_latentes):
        lat = m2.coef_latentes[["regiao", "subsetor"]].drop_duplicates()
        add("subsetores_latentes", True, len(lat), 0,
            "colunas de coeficientes guardadas à parte: " + ", ".join(f"{a}_{b}" for a, b in lat.itertuples(index=False)))
    return pd.DataFrame(linhas, columns=["checagem", "status", "valor", "tolerancia", "detalhe"])
