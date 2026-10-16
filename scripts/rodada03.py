"""Rodada 03 — tratamento dos dados para a MIP v02 (sem rede).

Uso (na raiz do repositório, depois de scripts/rodada02.py):
    python scripts/rodada03.py             # 1) dados → dados/intermediarios/*_v03 e resultados/rodada03/
    python scripts/rodada03_parametros.py  # 2) parâmetros v02
    python scripts/rodada03_mip.py         # 3) MIP v02, variantes, quadro e prévia

Saídas:
- dados/intermediarios/geracao_2019_regiao_subsetor_v03.csv  D8: BRASIL (BEN 2020, Tabela 5.4), RS (ONS), RB = BRASIL − RS
- resultados/rodada03/comparacao_referencias_v03.csv         referências da Seção 2.1 da Rodada 03
- resultados/rodada03/reconciliacao_epe_v02.csv              BEN × montagem da 02b (ONS + isolados) × D8
- dados/intermediarios/ben_2019_consumo_especifico_v02.csv   consumo específico com o mapeamento da D8 (PET com
                                                             'outras não renováveis')
- dados/intermediarios/ben_2019_gas_eletricidade_por_setor_v01.csv  BEN 2020, consumo final de gás natural e de
                                                             eletricidade por setor (evidência do teto do gás por comprador)
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import pandas as pd  # noqa: E402

from mip.caminhos import PASTA_EXTERNOS, PASTA_INTERMEDIARIOS, PASTA_RESULTADOS  # noqa: E402
from mip.externos import ben  # noqa: E402
from mip.externos.ons import ORDEM_SUBSETORES_GERACAO  # noqa: E402

INT = PASTA_INTERMEDIARIOS
SAIDA = PASTA_RESULTADOS / "rodada03"
TAB54 = PASTA_EXTERNOS / "epe" / "ben2020_tabela_5_4_v01.csv"
BEN_MATRIZ = PASTA_EXTERNOS / "epe" / "ben_2020" / "BEN2020_Matriz_ab2019.xlsx"
FONTE_TAB54 = "EPE, BEN 2020, Tabela 5.4 – Centrais Elétricas de Serviço Público (p. 112); acesso 2026-10-15T19:38:26Z"
FONTE_MATRIZ = "EPE, BEN 2020 (ano-base 2019), Matriz ab2019.xlsx, aba Consolidada (mil tep); acesso 2026-10-15T19:38:26Z"
SETORES_BEN = ["CONSUMO FINAL NÃO ENERGÉTICO", "SETOR ENERGÉTICO", "RESIDENCIAL", "COMERCIAL", "PÚBLICO", "AGROPECUÁRIO",
               "RODOVIÁRIO", "FERROVIÁRIO", "AÉREO", "HIDROVIÁRIO", "CIMENTO", "FERRO GUSA E AÇO", "FERRO LIGAS",
               "MINERAÇÃO E PELOTIZAÇÃO", "NÃO FERROSOS E OUT. METALURG.", "QUÍMICA", "ALIMENTOS E BEBIDAS", "TÊXTIL",
               "PAPEL E CELULOSE", "CERÂMICA", "OUTRAS INDÚSTRIAS", "CONSUMO NÃO IDENTIFICADO"]


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    tab54 = ben.ler_tabela_5_4(TAB54)
    usinas = pd.read_csv(INT / "geracao_2019_usina_v02.csv")
    d8 = ben.geracao_d8(tab54, usinas)
    d8.to_csv(INT / "geracao_2019_regiao_subsetor_v03.csv", index=False)

    comp = ben.comparar_com_referencia_d8(d8)
    comp.insert(0, "fonte", "D8 (Rodada 03, Seção 2.1)")
    comp.to_csv(SAIDA / "comparacao_referencias_v03.csv", index=False)

    # reconciliação: BEN × montagem da 02b (ONS RS + ONS RB + isolados) × D8 (por construção, igual ao BEN)
    v02 = pd.read_csv(INT / "geracao_2019_regiao_subsetor_v02.csv")
    v02 = v02[v02["regiao"].isin(["RS", "RB"])]
    linhas = []
    br = d8[d8["regiao"] == "BRASIL"].iloc[0]
    for c in ORDEM_SUBSETORES_GERACAO:
        montado_02b = float(v02[c].sum())
        rs = float(d8.loc[d8["regiao"] == "RS", c].iloc[0])
        rb = float(d8.loc[d8["regiao"] == "RB", c].iloc[0])
        linhas.append({"subsetor": c, "ben_servico_publico_gwh": float(br[c]), "montado_02b_gwh (ONS + isolados)": montado_02b,
                       "diferenca_02b_gwh": montado_02b - float(br[c]), "rs_d8_gwh": rs, "rb_d8_gwh": rb,
                       "rs_mais_rb_d8_gwh": rs + rb, "diferenca_d8_gwh": rs + rb - float(br[c])})
    rec = pd.DataFrame(linhas)
    tot = rec.drop(columns="subsetor").sum()
    rec = pd.concat([rec, pd.DataFrame([{"subsetor": "Total", **tot.to_dict()}])], ignore_index=True)
    rec["nota"] = ("BEN 2020, Tabela 5.4; PET inclui 'outras não renováveis' (405 GWh) e BIO = lenha + biodiesel + "
                   "outras renováveis (D8). A montagem da 02b usava ONS + isolados (diesel e óleo).")
    rec.to_csv(SAIDA / "reconciliacao_epe_v02.csv", index=False)

    # consumo específico com o mapeamento da D8 (revisão da Rodada 03: o PET passa a incluir 'outras não renováveis')
    ce = ben.consumo_especifico_d8(tab54)
    ce["fonte"] = FONTE_TAB54 + ": consumo de combustível ÷ geração, por fonte, com o mapeamento da D8 (" + ce.pop("fontes_ben") + ")"
    ce.to_csv(INT / "ben_2019_consumo_especifico_v02.csv", index=False)
    # gás natural e eletricidade por setor (mil tep): evidência para o teto do gás por comprador
    cons = ben.ler_matriz_consolidada(BEN_MATRIZ)
    gn = [c for c in cons.columns if c.startswith("GÁS NA")][0]
    el = [c for c in cons.columns if c.startswith("ELETRICIDADE")][0]
    ge = pd.DataFrame({"setor_ben": SETORES_BEN, "gas_natural_mil_tep": [float(cons.loc[x, gn]) for x in SETORES_BEN],
                       "eletricidade_mil_tep": [float(cons.loc[x, el]) for x in SETORES_BEN]})
    ge["fonte"] = FONTE_MATRIZ + ", colunas GÁS NATURAL e ELETRICIDADE"
    ge.to_csv(INT / "ben_2019_gas_eletricidade_por_setor_v01.csv", index=False)

    ok = int(comp["confere"].sum())
    print(f"[D8] RS {d8.loc[d8.regiao == 'RS', 'Total'].iloc[0]:.1f} GWh; RB {d8.loc[d8.regiao == 'RB', 'Total'].iloc[0]:.1f}; "
          f"BRASIL {br['Total']:.1f}; referências {ok}/{len(comp)}")
    if ok < len(comp):
        print(comp[~comp["confere"]].to_string())


if __name__ == "__main__":
    main()
