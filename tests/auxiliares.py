"""Funções auxiliares dos testes do motor de desagregação."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mip.desagregacao import Especificacao
from mip.estrutura import COLUNAS_DF, ITENS_PRIMARIOS, ITENS_PRIMARIOS_DF, ITENS_SATELITE, MIP

FONTE = "teste automático"


def subsetores(K: int, tipos: list[str] | None = None, prefixo: str = "S38") -> pd.DataFrame:
    tipos = tipos or (["geracao"] * (K - 2) + ["rede", "gas_utilidades"] if K >= 3 else ["geracao", "rede"][:K])
    return pd.DataFrame(
        {"codigo": [f"{prefixo}_{k:02d}" for k in range(K)], "nome": [f"sub {k}" for k in range(K)], "tipo": tipos}
    )


def participacoes(subs: pd.DataFrame, por_regiao: dict[str, np.ndarray]) -> pd.DataFrame:
    linhas = []
    for r, s in por_regiao.items():
        for c, v in zip(subs["codigo"], s):
            linhas.append((r, c, float(v), FONTE))
    return pd.DataFrame(linhas, columns=["regiao", "subsetor", "participacao", "fonte"])


def espec_neutra(K: int, rng: np.random.Generator, regioes=("RS", "RB"), setor="S38") -> Especificacao:
    """Desagregação neutra: participações positivas arbitrárias e todas as regras proporcionais."""
    subs = subsetores(K, prefixo=setor)
    part = participacoes(subs, {r: rng.dirichlet(np.ones(K)) for r in regioes})
    return Especificacao(
        nome="neutra", setor_alvo=setor, regioes=list(regioes), subsetores=subs, participacoes=part,
        bloco="proporcional",
    )


def espec_aleatoria(rng: np.random.Generator, mip: MIP, regioes=("RS", "RB")) -> Especificacao:
    """Especificação válida aleatória, usando todos os tipos de regra."""
    K = int(rng.integers(3, 8))
    tipos = ["geracao"] * (K - 2) + ["rede", "gas_utilidades"]
    subs = subsetores(K, tipos)
    cod = list(subs["codigo"])
    ger = np.array(tipos) == "geracao"
    bloco = str(rng.choice(["proporcional", "geracao_vende_para_rede"]))
    modo = "participacoes"
    s = {}
    for r in regioes:
        p = rng.dirichlet(np.ones(K))
        if bloco == "geracao_vende_para_rede":
            # geração com participação ≥ 40% (acima da âncora de ~30%) para que as linhas fechem
            p[ger] = 0.4 * p[ger] / p[ger].sum() + 0.2 * p[ger]
            p[~ger] = p[~ger] / p[~ger].sum() * (1 - p[ger].sum())
        s[r] = p
    part = participacoes(subs, s)
    # regras de coluna
    col = [("*", "*", "*", "proporcional_vbp", "", np.nan)]
    for forn in rng.choice([f"S{k:02d}" for k in range(1, 69) if k != 38], size=4, replace=False):
        w = rng.dirichlet(np.ones(K))
        for c, v in zip(cod, w):
            col.append(("*", forn, "*", "fixa", c, v))
    forn = "S04"
    for c in cod:
        col.append(("RS", forn, "RB", "indicador", c, float(rng.uniform(0.5, 3))))
    regras_coluna = pd.DataFrame(col, columns=["regiao", "fornecedor", "regiao_fornecedor", "regra", "subsetor", "valor"])
    regras_coluna["fonte"] = FONTE
    # regras de linha
    lin = [("*", "*", "*", "proporcional_vbp", "", np.nan, False)]
    # participações fixas nas Famílias perto das participações no VBP (±20%), para a linha ser viável
    for r in regioes:
        w = s[r] * rng.uniform(0.8, 1.2, K)
        w = w / w.sum()
        # com geracao_vende_para_rede a margem da geração fora do bloco é pequena: não fixar no RAS
        fixar = bool(rng.random() < 0.5) and bloco == "proporcional"
        for c, v in zip(cod, w):
            lin.append((r, "FAM", "*", "fixa_por_comprador", c, v, fixar))
    lin.append(("RB", "S42", "RS", "somente_rede_e_gas", "", np.nan, False))
    regras_linha = pd.DataFrame(lin, columns=["regiao", "comprador", "regiao_comprador", "regra", "subsetor", "valor", "fixar_no_ras"])
    regras_linha["fonte"] = FONTE
    # regras de primários e satélite
    pri = [("*", "*", "proporcional_vbp", "", np.nan)]
    w = rng.dirichlet(np.ones(K))
    for c, v in zip(cod, w):
        pri.append(("*", "co2e", "fixa", c, v))
    for c in cod:
        pri.append(("RS", "energia", "indicador", c, float(rng.uniform(0.5, 3))))
    regras_primarios = pd.DataFrame(pri, columns=["regiao", "item", "regra", "subsetor", "valor"])
    regras_primarios["fonte"] = FONTE
    return Especificacao(
        nome="aleatória", setor_alvo="S38", regioes=list(regioes), subsetores=subs, participacoes=part,
        bloco=bloco, modo_vbp=modo, regras_coluna=regras_coluna, regras_linha=regras_linha,
        regras_primarios=regras_primarios,
    )


def mip_pequena() -> MIP:
    """MIP de 3 setores (uma região) com A conhecido.

    A = [[0.2, 0.1, 0.0],
         [0.1, 0.2, 0.0],
         [0.0, 0.0, 0.5]],  X = [100, 100, 50]
    """
    X = np.array([100.0, 100.0, 50.0])
    A = np.array([[0.2, 0.1, 0.0], [0.1, 0.2, 0.0], [0.0, 0.0, 0.5]])
    Z = A * X[None, :]
    F = np.zeros((3, len(COLUNAS_DF)))
    F[:, list(COLUNAS_DF["codigo"]).index("FAM_RS")] = X - Z.sum(axis=1)
    va = X - Z.sum(axis=0)
    V = np.zeros((len(ITENS_PRIMARIOS), 3))
    V[ITENS_PRIMARIOS.index("va")] = va
    V[ITENS_PRIMARIOS.index("remuneracoes")] = 0.4 * va
    V[ITENS_PRIMARIOS.index("eob")] = 0.6 * va
    S = np.zeros((len(ITENS_SATELITE), 3))
    S[ITENS_SATELITE.index("co2e")] = [10.0, 20.0, 30.0]  # e = [0.1, 0.2, 0.6]
    S[ITENS_SATELITE.index("ocupacoes")] = [5.0, 5.0, 5.0]
    setores = pd.DataFrame({"regiao": ["RS"] * 3, "codigo": ["S01", "S02", "S03"], "nome": ["um", "dois", "três"]})
    return MIP(
        setores=setores, Z=Z, F=F, total_linha=X.copy(), X=X, V=V,
        V_df=np.zeros((len(ITENS_PRIMARIOS_DF), len(COLUNAS_DF))), X_df=F.sum(axis=0),
        S=S, totais_ev={},
    )
