"""Modelo de Leontief genérico (serve para qualquer MIP: original ou desagregada).

- A = Z · diag(X)⁻¹ (coluna zero onde X_j = 0); L = (I − A)⁻¹
- e_j = CO₂e_j / X_j (zero onde X_j = 0)
- ΔX = L · ΔY; emissões por setor = e ∘ ΔX; total = soma
- IC = CO₂e total / Σ ΔX (t CO₂e por R$ milhão)
- emissões diretas = e · ΔY; indiretas = total − diretas
- recorte regional: soma pela região de origem do setor

Subsetores latentes (produção-base zero) podem receber uma coluna de coeficientes técnicos e
intensidades fornecidas à parte (MIP.coef_latentes); elas entram em A e em e somente no modelo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .estrutura import ITENS_SATELITE, MIP


# ---------------------------------------------------------------------------------------------
# Funções básicas
# ---------------------------------------------------------------------------------------------
def _dividir_por_x(M: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Divide cada coluna (ou elemento, se vetor) por X, com zero onde X = 0."""
    X = np.asarray(X, dtype=float)
    seguro = np.where(X != 0, X, 1.0)
    return np.where(X != 0, np.asarray(M, dtype=float) / seguro, 0.0)


def coeficientes_tecnicos(
    Z: np.ndarray, X: np.ndarray, colunas_extras: dict[int, np.ndarray] | None = None
) -> np.ndarray:
    """A = Z · diag(X)⁻¹, com coluna zero onde X_j = 0.

    `colunas_extras` substitui colunas inteiras de A (uso: subsetores latentes, cuja coluna de
    coeficientes é dada externamente porque a produção-base é zero).
    """
    A = _dividir_por_x(Z, X)
    for j, col in (colunas_extras or {}).items():
        A[:, j] = col
    return A


def inversa_leontief(A: np.ndarray) -> np.ndarray:
    """L = (I − A)⁻¹."""
    n = A.shape[0]
    return np.linalg.solve(np.eye(n) - A, np.eye(n))


def intensidades(v: np.ndarray, X: np.ndarray, extras: dict[int, float] | None = None) -> np.ndarray:
    """Coeficiente por unidade de produção (v_j / X_j), zero onde X_j = 0; `extras` para latentes."""
    e = _dividir_por_x(v, X)
    for j, val in (extras or {}).items():
        e[j] = val
    return e


def soma_por_regiao(v: np.ndarray, regioes: np.ndarray) -> dict[str, float]:
    """Soma um vetor por região de origem do setor (ordem de primeira ocorrência)."""
    regioes = np.asarray(regioes)
    return {r: float(v[regioes == r].sum()) for r in dict.fromkeys(regioes)}


def vetor_choque(setores: pd.DataFrame, choques: dict) -> np.ndarray:
    """Monta ΔY a partir de {(regiao, codigo): valor}. Códigos inexistentes geram erro."""
    dY = np.zeros(len(setores))
    chave = list(zip(setores["regiao"], setores["codigo"]))
    pos = {k: i for i, k in enumerate(chave)}
    for k, v in choques.items():
        if k not in pos:
            raise KeyError(f"choque em setor inexistente: {k}")
        dY[pos[k]] += v
    return dY


def colunas_latentes(mip: MIP) -> tuple[dict[int, np.ndarray], dict[str, dict[int, float]]]:
    """Converte MIP.coef_latentes (formato longo) em colunas de A e intensidades satélite.

    Colunas esperadas em coef_latentes: regiao, subsetor, tipo_linha ('setor' | 'satelite'),
    regiao_linha, codigo_linha, coeficiente.
    """
    cols: dict[int, np.ndarray] = {}
    ints: dict[str, dict[int, float]] = {it: {} for it in ITENS_SATELITE}
    cl = mip.coef_latentes
    if cl is None or len(cl) == 0:
        return cols, ints
    for (reg, sub), g in cl.groupby(["regiao", "subsetor"], sort=False):
        j = mip.indice(reg, sub)
        if mip.X[j] != 0:
            raise ValueError(f"subsetor latente {reg} {sub} tem produção-base não nula ({mip.X[j]})")
        col = np.zeros(mip.n)
        for r in g.itertuples(index=False):
            if r.tipo_linha == "setor":
                col[mip.indice(r.regiao_linha, r.codigo_linha)] += float(r.coeficiente)
            elif r.tipo_linha == "satelite":
                if r.codigo_linha not in ints:
                    raise ValueError(f"item satélite desconhecido em coef_latentes: {r.codigo_linha}")
                ints[r.codigo_linha][j] = float(r.coeficiente)
            else:
                raise ValueError(f"tipo_linha desconhecido em coef_latentes: {r.tipo_linha}")
        cols[j] = col
    return cols, ints


# ---------------------------------------------------------------------------------------------
# Modelo e resultados de cenários
# ---------------------------------------------------------------------------------------------
@dataclass
class ResultadoCenario:
    """Resultado de um choque ΔY: produção e emissões induzidas por setor-região."""

    nome: str
    setores: pd.DataFrame
    dY: np.ndarray
    dX: np.ndarray
    e: np.ndarray  # intensidade de emissão (t CO2e por R$ milhão)
    outros: dict = field(default_factory=dict)  # outros itens satélite induzidos (ocupações, água, energia)

    @property
    def emissoes(self) -> np.ndarray:
        return self.e * self.dX

    @property
    def diretas(self) -> float:
        return float(self.e @ self.dY)

    def resumo(self) -> dict:
        reg = self.setores["regiao"].to_numpy()
        dx_reg = soma_por_regiao(self.dX, reg)
        em_reg = soma_por_regiao(self.emissoes, reg)
        dx_tot = float(self.dX.sum())
        em_tot = float(self.emissoes.sum())
        r = {"cenario": self.nome, "dX_total": dx_tot}
        r.update({f"dX_{k}": v for k, v in dx_reg.items()})
        r["co2e_total"] = em_tot
        r.update({f"co2e_{k}": v for k, v in em_reg.items()})
        r["IC"] = em_tot / dx_tot if dx_tot else float("nan")
        for k, v in em_reg.items():
            r[f"pct_co2e_{k}"] = 100 * v / em_tot if em_tot else float("nan")
        r["co2e_diretas"] = self.diretas
        r["co2e_indiretas"] = em_tot - self.diretas
        r["pct_indiretas"] = 100 * (em_tot - self.diretas) / em_tot if em_tot else float("nan")
        return r

    def tabela_setorial(self) -> pd.DataFrame:
        """ΔY, ΔX e emissões por setor-região (uma linha por setor)."""
        em = self.emissoes
        tot = em.sum()
        df = self.setores[["regiao", "codigo", "nome"]].copy()
        df["dY (R$ mi)"] = self.dY
        df["dX (R$ mi)"] = self.dX
        df["intensidade (t CO2e/R$ mi)"] = self.e
        df["CO2e induzido (t)"] = em
        df["CO2e direto (t)"] = self.e * self.dY
        df["% do CO2e total"] = 100 * em / tot if tot else np.nan
        for item, v in self.outros.items():
            df[f"{item} induzido"] = v
        return df


class ModeloLeontief:
    """Modelo de Leontief com contas satélite para uma MIP qualquer."""

    def __init__(self, mip: MIP, item_emissao: str = "co2e"):
        self.mip = mip
        cols, ints = colunas_latentes(mip)
        self.A = coeficientes_tecnicos(mip.Z, mip.X, cols)
        self.L = inversa_leontief(self.A)
        self.intensidades = {
            it: intensidades(mip.satelite(it), mip.X, ints.get(it)) for it in ITENS_SATELITE
        }
        self.item_emissao = item_emissao
        self.e = self.intensidades[item_emissao]

    def simular(self, dY: np.ndarray, nome: str = "") -> ResultadoCenario:
        dX = self.L @ dY
        outros = {
            it: self.intensidades[it] * dX for it in ITENS_SATELITE if it != self.item_emissao
        }
        return ResultadoCenario(nome=nome, setores=self.mip.setores, dY=dY, dX=dX, e=self.e, outros=outros)

    def simular_choques(self, choques: dict, nome: str = "") -> ResultadoCenario:
        return self.simular(vetor_choque(self.mip.setores, choques), nome)


def ranking_setorial(res: ResultadoCenario, n: int = 10, coluna: str = "CO2e induzido (t)") -> pd.DataFrame:
    """Os n setores-região com maior valor na coluna indicada (padrão: emissões induzidas)."""
    df = res.tabela_setorial().sort_values(coluna, ascending=False).head(n).reset_index(drop=True)
    df.insert(0, "#", np.arange(1, len(df) + 1))
    return df
