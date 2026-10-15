"""Rodada 01 — regenera todas as saídas da rodada.

Uso (na raiz do repositório):
    python scripts/rodada01.py

Saídas:
- dados/intermediarios/mip_original_longo.csv              (Etapa 2)
- resultados/rodada01/validacao_mip_original_v01.csv        (Etapa 2)
- resultados/rodada01/replicacao_v01.xlsx                   (Etapa 3)
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from mip import referencia as ref  # noqa: E402
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


def main():
    mip = etapa2()
    etapa3(mip)


if __name__ == "__main__":
    main()
