"""Diagnóstico de um setor nas duas regiões (Etapa 4): insumos, vendas, bloco intrassetorial,
insumos primários e contas satélite, peso nas emissões dos cenários."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .estrutura import (
    COLUNAS_DF,
    ITENS_IMPOSTOS_PRODUTOS,
    ITENS_PRIMARIOS,
    ITENS_SATELITE,
    MIP,
    NOMES_ITENS,
    UNIDADES,
)
from .modelo import ResultadoCenario


def estrutura_insumos(mip: MIP, regiao: str, codigo: str, energeticos: list[str] | None = None) -> pd.DataFrame:
    """Coluna do setor em Z: valor, coeficiente técnico e região de origem de cada insumo."""
    j = mip.indice(regiao, codigo)
    col = mip.Z[:, j]
    ci = col.sum()
    df = mip.setores[["regiao", "codigo", "nome"]].rename(
        columns={"regiao": "regiao_origem", "codigo": "setor_origem", "nome": "nome_origem"}
    )
    df["valor (R$ mi)"] = col
    df["coef_tecnico (por R$ de VBP)"] = col / mip.X[j] if mip.X[j] else 0.0
    df["% do consumo intermediário"] = 100 * col / ci if ci else 0.0
    df["ranking"] = (-col).argsort().argsort() + 1
    df["insumo_energetico"] = np.where(df["setor_origem"].isin(energeticos or []), "SIM", "")
    return df


def estrutura_vendas(mip: MIP, regiao: str, codigo: str) -> pd.DataFrame:
    """Linha do setor: vendas a cada setor-região (Z) e a cada coluna da demanda final."""
    i = mip.indice(regiao, codigo)
    ci = mip.setores[["regiao", "codigo", "nome"]].rename(
        columns={"regiao": "regiao_destino", "codigo": "destino", "nome": "nome_destino"}
    )
    ci.insert(0, "tipo", "consumo intermediário")
    ci["valor (R$ mi)"] = mip.Z[i]
    df_ = pd.DataFrame(
        {
            "tipo": "demanda final",
            "regiao_destino": COLUNAS_DF["regiao"],
            "destino": COLUNAS_DF["codigo"],
            "nome_destino": COLUNAS_DF["nome"],
            "valor (R$ mi)": mip.F[i],
        }
    )
    df = pd.concat([ci, df_], ignore_index=True)
    total = mip.total_linha[i]
    df["% das vendas totais"] = 100 * df["valor (R$ mi)"] / total if total else 0.0
    df["ranking"] = (-df["valor (R$ mi)"].to_numpy()).argsort().argsort() + 1
    return df


def bloco_intrassetorial(mip: MIP, codigo: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Bloco codigo→codigo entre as regiões e a soma das vendas de cada região ao setor (todas as regiões)."""
    regs = mip.lista_regioes
    idx = {r: mip.indice(r, codigo) for r in regs}
    bloco = pd.DataFrame(
        [[mip.Z[idx[a], idx[b]] for b in regs] for a in regs],
        index=[f"vende {codigo}-{a}" for a in regs],
        columns=[f"compra {codigo}-{b}" for b in regs],
    )
    bloco = bloco.reset_index().rename(columns={"index": "fluxo (R$ mi)"})
    linhas = []
    for a in regs:
        i = idx[a]
        vendas = sum(mip.Z[i, idx[b]] for b in regs)
        compras = sum(mip.Z[idx[b], i] for b in regs)
        linhas.append(
            (
                f"{codigo}-{a}",
                mip.X[i],
                vendas,
                100 * vendas / mip.X[i],
                compras,
                100 * compras / mip.X[i],
            )
        )
    resumo = pd.DataFrame(
        linhas,
        columns=[
            "setor",
            "VBP (R$ mi)",
            f"vendas ao {codigo} das duas regiões (R$ mi)",
            "vendas como % do VBP",
            f"compras do {codigo} das duas regiões (R$ mi)",
            "compras como % do VBP",
        ],
    )
    return bloco, resumo


def primarios_satelite(mip: MIP, regiao: str, codigo: str) -> pd.DataFrame:
    """Insumos primários e contas satélite do setor, com intensidade por R$ milhão de VBP."""
    j = mip.indice(regiao, codigo)
    x = mip.X[j]
    linhas = [("vbp", NOMES_ITENS["vbp"], x, "R$ mi")]
    linhas.append(("ci", "Consumo intermediário (Σ coluna de Z)", mip.Z[:, j].sum(), "R$ mi"))
    for k, it in enumerate(ITENS_PRIMARIOS):
        linhas.append((it, NOMES_ITENS[it], mip.V[k, j], "R$ mi"))
    linhas.append(
        (
            "impostos_produtos",
            "Impostos sobre produtos (IPI + ICMS + outros)",
            sum(mip.primario(it)[j] for it in ITENS_IMPOSTOS_PRODUTOS),
            "R$ mi",
        )
    )
    for k, it in enumerate(ITENS_SATELITE):
        linhas.append((it, NOMES_ITENS[it], mip.S[k, j], UNIDADES[it]))
    df = pd.DataFrame(linhas, columns=["item", "descricao", "valor", "unidade"])
    df["intensidade (por R$ mi de VBP)"] = df["valor"] / x if x else np.nan
    df.insert(0, "setor", f"{codigo}-{regiao}")
    return df


def peso_nas_emissoes(
    resultados: dict[str, ResultadoCenario], mip: MIP, codigo: str, esperado: dict | None = None
) -> pd.DataFrame:
    """Emissões induzidas no setor (cada região e soma) como % do total de cada cenário."""
    regs = mip.lista_regioes
    idx = {r: mip.indice(r, codigo) for r in regs}
    linhas = []
    for nome, res in resultados.items():
        em = res.emissoes
        tot = em.sum()
        reg = {r: em[idx[r]] for r in regs}
        linha = {"cenario": nome, "CO2e total (t)": tot}
        for r in regs:
            linha[f"CO2e {codigo}-{r} (t)"] = reg[r]
            linha[f"% {codigo}-{r}"] = 100 * reg[r] / tot
        linha[f"% {codigo} ({' + '.join(regs)})"] = 100 * sum(reg.values()) / tot
        if esperado is not None:
            linha["% esperado"] = esperado.get(nome, np.nan)
            linha["diferenca (p.p.)"] = linha[f"% {codigo} ({' + '.join(regs)})"] - linha["% esperado"]
        linhas.append(linha)
    return pd.DataFrame(linhas)


def valores_chave(mip: MIP, codigo: str) -> dict[str, dict[str, float]]:
    """Números-chave do setor em cada região (mesmos itens da tabela de referência da Etapa 4)."""
    _, bloco_res = bloco_intrassetorial(mip, codigo)
    bres = bloco_res.set_index("setor")
    saida = {}
    for reg in mip.lista_regioes:
        j = mip.indice(reg, codigo)
        b = bres.loc[f"{codigo}-{reg}"]
        saida[reg] = {
            "VBP": mip.X[j],
            "Consumo intermediário (soma da coluna em Z)": mip.Z[:, j].sum(),
            "Importações": mip.primario("importacoes")[j],
            "VA": mip.primario("va")[j],
            "CO2e (t)": mip.satelite("co2e")[j],
            "t CO2e por R$ mi": mip.satelite("co2e")[j] / mip.X[j] if mip.X[j] else np.nan,
            "Ocupações": mip.satelite("ocupacoes")[j],
            "Energia (mil tep)": mip.satelite("energia")[j],
            "Água (hm3)": mip.satelite("agua")[j],
            f"Vendas ao {codigo} das duas regiões": b.iloc[1],
            f"Vendas ao {codigo} das duas regiões (% do VBP)": b.iloc[2],
        }
    return saida
