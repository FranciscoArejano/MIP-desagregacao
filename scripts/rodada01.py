"""Rodada 01 — regenera todas as saídas da rodada.

Uso (na raiz do repositório):
    python scripts/rodada01.py

Saídas:
- dados/intermediarios/mip_original_longo.csv              (Etapa 2)
- resultados/rodada01/validacao_mip_original_v01.csv        (Etapa 2)
- resultados/rodada01/replicacao_v01.xlsx                   (Etapa 3)
- resultados/rodada01/diagnostico_S38_v01.xlsx              (Etapa 4)
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from mip import referencia as ref  # noqa: E402
from mip import diagnostico as diag  # noqa: E402
from mip.caminhos import PASTA_INTERMEDIARIOS, PASTA_RESULTADOS  # noqa: E402
from mip.exportacao import salvar_tabelas  # noqa: E402
from mip.leitura import formato_longo, ler_mip_original  # noqa: E402
from mip.modelo import ModeloLeontief, ranking_setorial  # noqa: E402
from mip.validacao import validar_identidades  # noqa: E402

PASTA_SAIDA = PASTA_RESULTADOS / "rodada01"


def etapa2():
    """Leitura da MIP, formato longo e validação das identidades."""
    mip = ler_mip_original()
    PASTA_INTERMEDIARIOS.mkdir(parents=True, exist_ok=True)
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    formato_longo(mip).to_csv(PASTA_INTERMEDIARIOS / "mip_original_longo.csv", index=False)
    val = validar_identidades(mip)
    val.to_csv(PASTA_SAIDA / "validacao_mip_original_v01.csv", index=False)
    print("[Etapa 2] validação da MIP original:")
    for r in val.itertuples(index=False):
        print(f"  - {r.checagem}: obtido {r.obtido} (esperado {r.esperado})")
    return mip


def comparar_com_referencia(obtido: pd.DataFrame) -> pd.DataFrame:
    """Tabela longa esperado × obtido × diferença para os 9 cenários."""
    linhas = []
    for cen in ref.ESPERADO["cenario"]:
        esp = ref.ESPERADO.set_index("cenario").loc[cen]
        obt = obtido.set_index("cenario").loc[cen]
        for ind, tol in ref.TOLERANCIAS.items():
            dif = obt[ind] - esp[ind]
            linhas.append((cen, ref.NOMES_CENARIOS[cen], ind, esp[ind], obt[ind], dif, tol, abs(dif) <= tol))
    return pd.DataFrame(
        linhas,
        columns=["cenario", "nome", "indicador", "esperado", "obtido", "diferenca", "tolerancia", "confere"],
    )


def etapa3(mip):
    """Reprodução dos 9 cenários de referência."""
    modelo = ModeloLeontief(mip)
    resultados = {c: modelo.simular_choques(ref.choques(c), c) for c in ref.CENARIOS_RS}
    obtido = pd.DataFrame([r.resumo() for r in resultados.values()])
    comp = comparar_com_referencia(obtido)

    top = ranking_setorial(resultados["R1"], 10)
    top_cmp = ref.TOP10_R1.copy()
    top_cmp["regiao_obtida"] = top["regiao"]
    top_cmp["codigo_obtido"] = top["codigo"]
    top_cmp["dX_obtido"] = top["dX (R$ mi)"]
    top_cmp["co2e_obtido"] = top["CO2e induzido (t)"]
    top_cmp["pct_obtido"] = top["% do CO2e total"]
    top_cmp["confere"] = (
        (top_cmp["regiao"] == top_cmp["regiao_obtida"])
        & (top_cmp["codigo"] == top_cmp["codigo_obtido"])
        & (np.abs(top_cmp["dX_obtido"] - top_cmp["dX"]) <= 0.05)
        & (np.abs(top_cmp["co2e_obtido"] - top_cmp["co2e"]) <= 0.05)
        & (np.abs(top_cmp["pct_obtido"] - top_cmp["pct_total"]) <= 0.05)
    )

    resumo = obtido.copy()
    resumo.insert(1, "nome", resumo["cenario"].map(ref.NOMES_CENARIOS))
    choques_tab = pd.DataFrame(
        [(c, ref.NOMES_CENARIOS[c], "RS", s, v) for c, d in ref.CENARIOS_RS.items() for s, v in d.items()],
        columns=["cenario", "nome", "regiao", "setor", "choque (R$ mi)"],
    )
    abas = {"resumo_esperado_obtido": comp, "resumo_obtido": resumo, "top10_R1": top_cmp, "choques": choques_tab}
    for c, r in resultados.items():
        abas[c] = r.tabela_setorial()
    leiame = [
        "Rodada 01 — Etapa 3: reprodução dos resultados de referência com a MIP original (RS × RB, 2019).",
        "Modelo: A = Z·diag(X)^-1; L = (I − A)^-1; ΔX = L·ΔY; emissões = e ∘ ΔX, com e = CO2e/X (zero onde X = 0).",
        "IC = CO2e total / Σ ΔX (t CO2e por R$ milhão). Diretas = e·ΔY; indiretas = total − diretas.",
        "Recorte regional pela região de origem do setor. Choques em R$ milhões na demanda final de setores do RS.",
        "Aba resumo_esperado_obtido: esperado × obtido × diferença (tolerâncias: 0.01 R$ mi; 1 t CO2e; 0.005 em IC e %).",
        "Abas por cenário: ΔY, ΔX e emissões por setor-região. R4a e R4b são duas versões do mesmo cenário (ambas reportadas).",
        "Gerado por scripts/rodada01.py.",
    ]
    salvar_tabelas(PASTA_SAIDA / "replicacao_v01.xlsx", abas, leiame=leiame)
    n_ok = int(comp["confere"].sum())
    print(f"[Etapa 3] {n_ok}/{len(comp)} comparações dentro da tolerância; "
          f"maior |dif| = {comp['diferenca'].abs().max():.4f}; top-10 R1 confere: {bool(top_cmp['confere'].all())}")
    return resultados, comp, top_cmp


def valores_diagnostico(mip, codigo: str = "S38") -> pd.DataFrame:
    """Valores-chave do diagnóstico, comparados com a referência das instruções."""
    obt = diag.valores_chave(mip, codigo)
    linhas = []
    for r in ref.DIAGNOSTICO_S38.itertuples(index=False):
        for reg, esp in (("RS", r[1]), ("RB", r[2])):
            o = obt[reg][r.item]
            linhas.append((r.item, f"{codigo}-{reg}", esp, o, o - esp, r.tolerancia, abs(o - esp) <= r.tolerancia))
    for (a, b), esp in ref.BLOCO_S38.items():
        o = mip.Z[mip.indice(a, codigo), mip.indice(b, codigo)]
        linhas.append((f"Bloco {codigo}→{codigo}: {a}→{b}", "", esp, o, o - esp, 0.05, abs(o - esp) <= 0.05))
    return pd.DataFrame(
        linhas, columns=["item", "setor", "esperado", "obtido", "diferenca", "tolerancia", "confere"]
    )


def etapa4(mip, resultados):
    """Diagnóstico do S38 nas duas regiões."""
    cod = "S38"
    resumo = valores_diagnostico(mip, cod)
    bloco, bloco_res = diag.bloco_intrassetorial(mip, cod)
    ins = {r: diag.estrutura_insumos(mip, r, cod, ref.INSUMOS_ENERGETICOS) for r in mip.lista_regioes}
    ven = {r: diag.estrutura_vendas(mip, r, cod) for r in mip.lista_regioes}
    prim = pd.concat([diag.primarios_satelite(mip, r, cod) for r in mip.lista_regioes], ignore_index=True)
    peso = diag.peso_nas_emissoes(resultados, mip, cod, ref.PESO_S38_CENARIOS)
    abas = {"resumo_referencia": resumo}
    for r in mip.lista_regioes:
        abas[f"insumos_{cod}_{r}"] = ins[r]
    for r in mip.lista_regioes:
        abas[f"vendas_{cod}_{r}"] = ven[r]
    abas[f"bloco_{cod}_{cod}"] = bloco
    abas[f"bloco_{cod}_resumo"] = bloco_res
    abas["primarios_satelite"] = prim
    abas["peso_nas_emissoes"] = peso
    destacar = {f"insumos_{cod}_{r}": ins[r]["insumo_energetico"] == "SIM" for r in mip.lista_regioes}
    leiame = [
        "Rodada 01 — Etapa 4: diagnóstico do S38 (Energia elétrica, gás natural e outras utilidades) no RS e no RB.",
        "resumo_referencia: valores-chave comparados com a referência das instruções.",
        "insumos_S38_*: coluna do S38 em Z — valor, coeficiente técnico (valor/VBP), região de origem; "
        "insumos energéticos (S01, S03, S04, S05, S09, S16, S19, S20) destacados em amarelo (coluna insumo_energetico = SIM).",
        "vendas_S38_*: linha do S38 — vendas a cada setor-região e a cada coluna da demanda final (% das vendas totais = % do VBP).",
        "bloco_S38_S38: fluxos RS→RS, RS→RB, RB→RS, RB→RB (linha = região vendedora; coluna = região compradora).",
        "bloco_S38_resumo: vendas do S38 de cada região ao S38 das duas regiões, como % do VBP "
        "(candidata a âncora do valor da geração elétrica — decisão D3, do Francisco); idem para as compras.",
        "primarios_satelite: importações, impostos, VA e componentes, ocupações, CO2e, água e energia, com intensidade por R$ mi de VBP.",
        "peso_nas_emissoes: emissões induzidas no S38-RS e no S38-RB como % do total em cada cenário da Etapa 3.",
        "Valores em R$ milhões (2019); CO2e em t; água em hm3; energia em mil tep. Gerado por scripts/rodada01.py.",
    ]
    salvar_tabelas(PASTA_SAIDA / f"diagnostico_{cod}_v01.xlsx", abas, leiame=leiame, destacar=destacar)
    print(f"[Etapa 4] diagnóstico do {cod}: {int(resumo['confere'].sum())}/{len(resumo)} valores conferem; "
          f"peso do S38 confere em {int((peso['diferenca (p.p.)'].abs() <= 0.05).sum())}/{len(peso)} cenários")
    return resumo, bloco_res, peso


def main():
    mip = etapa2()
    resultados, _, _ = etapa3(mip)
    etapa4(mip, resultados)


if __name__ == "__main__":
    main()
