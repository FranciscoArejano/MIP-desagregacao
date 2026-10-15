"""Checagens das identidades contábeis de uma MIP (Etapa 2)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .estrutura import COLUNAS_DF, IDX_DISCREP, ITENS_IMPOSTOS_PRODUTOS, ITENS_PRIMARIOS, ITENS_SATELITE, MIP


def residuo_linha(mip: MIP) -> np.ndarray:
    """Σ Z + Σ demanda final (inclui discrepância) − total da linha."""
    return mip.Z.sum(axis=1) + mip.F.sum(axis=1) - mip.total_linha


def residuo_coluna(mip: MIP) -> np.ndarray:
    """Σ Z (coluna) + importações + impostos sobre produtos + VA − VBP."""
    impostos = sum(mip.primario(it) for it in ITENS_IMPOSTOS_PRODUTOS)
    return mip.Z.sum(axis=0) + mip.primario("importacoes") + impostos + mip.primario("va") - mip.X


def residuo_va(mip: MIP) -> np.ndarray:
    """VA − (remunerações + EOB + impostos sobre a produção)."""
    return mip.primario("va") - (
        mip.primario("remuneracoes") + mip.primario("eob") + mip.primario("impostos_producao")
    )


def residuo_total_df(mip: MIP) -> np.ndarray:
    """Para cada coluna de demanda final: Σ linhas dos setores + importações + impostos − total (linha 156)."""
    return mip.F.sum(axis=0) + mip.V_df.sum(axis=0) - mip.X_df


def _rotulo(mip: MIP, i: int) -> str:
    s = mip.setores.iloc[i]
    return f"{s['regiao']} {s['codigo']}"


def celulas_negativas(mip: MIP, tol: float = 0.0) -> pd.DataFrame:
    """Lista todas as células negativas (Z, demanda final, insumos primários, satélite, VBP)."""
    regs = []
    ids = mip.setores["regiao"] + " " + mip.setores["codigo"]
    for i, j in zip(*np.nonzero(mip.Z < -tol)):
        regs.append(("Z", ids[i], ids[j], mip.Z[i, j]))
    for i, j in zip(*np.nonzero(mip.F < -tol)):
        regs.append(("demanda_final", ids[i], COLUNAS_DF["codigo"][j], mip.F[i, j]))
    for k, it in enumerate(ITENS_PRIMARIOS):
        for j in np.flatnonzero(mip.V[k] < -tol):
            regs.append(("insumos_primarios", it, ids[j], mip.V[k, j]))
    for k, it in enumerate(ITENS_SATELITE):
        for j in np.flatnonzero(mip.S[k] < -tol):
            regs.append(("satelite", it, ids[j], mip.S[k, j]))
    for j in np.flatnonzero(mip.X < -tol):
        regs.append(("vbp", "vbp", ids[j], mip.X[j]))
    return pd.DataFrame(regs, columns=["bloco", "linha", "coluna", "valor"])


def validar_identidades(mip: MIP) -> pd.DataFrame:
    """Roda as checagens da Etapa 2 e devolve uma tabela (checagem, esperado, obtido, detalhe)."""
    linhas = []

    r = residuo_linha(mip)
    i = int(np.argmax(np.abs(r)))
    linhas.append(
        (
            "Linha: Σ Z + Σ demanda final (EK:EU) − total (EV)",
            "diferença máxima ≈ 7e-10",
            f"{np.abs(r).max():.3e}",
            f"máximo em {_rotulo(mip, i)}",
        )
    )

    c = residuo_coluna(mip)
    i = int(np.argmax(np.abs(c)))
    outros = np.abs(np.delete(c, i)).max()
    linhas.append(
        (
            "Coluna: Σ Z + importações + impostos (147–149) + VA (151) − VBP (156)",
            "diferença máxima ≈ 0.0095 (RB S40 Construção); demais ≈ 0",
            f"{c[i]:.6f}",
            f"máximo em {_rotulo(mip, i)} ({mip.setores['nome'][i]}); "
            f"maior dos demais = {outros:.4f} ({_rotulo(mip, int(np.argsort(np.abs(c))[-2]))}); "
            f"mediana |dif| = {np.median(np.abs(c)):.1e}; setores com |dif| > 1e-3: "
            f"{int((np.abs(c) > 1e-3).sum())}, > 1e-6: {int((np.abs(c) > 1e-6).sum())}; "
            f"maior |dif|/VBP = {np.max(np.abs(c) / np.where(mip.X > 0, mip.X, 1)):.1e}",
        )
    )

    v = residuo_va(mip)
    linhas.append(
        (
            "VA − (remunerações + EOB + impostos sobre a produção)",
            "≈ 1e-10",
            f"{np.abs(v).max():.3e}",
            f"máximo em {_rotulo(mip, int(np.argmax(np.abs(v))))}",
        )
    )

    d = mip.X - mip.total_linha
    linhas.append(
        (
            "VBP (linha 156) − total da linha (EV), por setor",
            "0",
            f"{np.abs(d).max():.3e}",
            "máximo da diferença absoluta",
        )
    )

    zeros = [_rotulo(mip, k) for k in np.flatnonzero(mip.X == 0)]
    linhas.append(
        (
            "Setores com VBP = 0",
            "RS S05, RS S06, RS S07, RS S20",
            ", ".join(zeros),
            "linhas e colunas desses setores: "
            + (
                "todas zeradas"
                if all(
                    np.all(mip.Z[k] == 0) and np.all(mip.Z[:, k] == 0) and np.all(mip.F[k] == 0)
                    for k in np.flatnonzero(mip.X == 0)
                )
                else "HÁ VALORES NÃO NULOS"
            ),
        )
    )

    neg = celulas_negativas(mip)
    eu = neg[(neg["bloco"] == "demanda_final") & (neg["coluna"] == COLUNAS_DF["codigo"][IDX_DISCREP])]
    outros_neg = neg.drop(eu.index)
    desc_outros = "; ".join(
        f"{b} {l} {c} ({v:.2f})" for b, l, c, v in outros_neg.itertuples(index=False)
    )
    linhas.append(
        (
            "Valores negativos",
            "coluna EU (65 células; mínimo −5987.45); linha 153 EOB (RS S09, RB S09); "
            "linha 154 (RS S01, RB S01)",
            f"coluna EU: {len(eu)} células, mínimo {eu['valor'].min():.2f}; demais: {len(outros_neg)} células",
            desc_outros,
        )
    )

    # checagens adicionais (informativas)
    t = residuo_total_df(mip)
    linhas.append(
        (
            "[extra] Colunas de DF: Σ linhas + importações + impostos − total (linha 156)",
            "(não informado)",
            f"{np.abs(t).max():.4f}",
            "; ".join(f"{cod}: {x:.4f}" for cod, x in zip(COLUNAS_DF["codigo"], t)),
        )
    )
    soma_ev = {it: mip.primario(it).sum() for it in ITENS_PRIMARIOS}
    for it in ["importacoes", *ITENS_IMPOSTOS_PRODUTOS]:
        soma_ev[it] += mip.primario_df(it).sum()
    # EV156 = Σ VBP dos setores + importações e impostos sobre produtos de todas as colunas (oferta total)
    soma_ev["vbp"] = mip.X.sum() + sum(soma_ev[it] for it in ["importacoes", *ITENS_IMPOSTOS_PRODUTOS])
    dif_ev = {it: mip.totais_ev[it] - soma_ev[it] for it in soma_ev}
    linhas.append(
        (
            "[extra] Coluna EV das linhas 144–156 − soma da linha (EV156 = Σ VBP + importações + impostos)",
            "(não informado)",
            f"{max(abs(x) for x in dif_ev.values()):.3e}",
            "; ".join(f"{k}: {x:.2e}" for k, x in dif_ev.items()),
        )
    )
    linhas.append(
        (
            "[extra] Totais das contas satélite",
            "(não informado)",
            "; ".join(f"{it}: {mip.satelite(it).sum():.2f}" for it in ITENS_SATELITE),
            "soma das 136 colunas",
        )
    )
    return pd.DataFrame(linhas, columns=["checagem", "esperado", "obtido", "detalhe"])
