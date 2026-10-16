"""EPE, Balanço Energético Nacional 2020 (ano-base 2019): geração de serviço público por fonte (Tabela 5.4).

Rodada 03, decisão D8: o total do Brasil por fonte vem do BEN (a mesma base do SEEG); o RS vem do ONS; RB = Brasil − RS.
A transcrição da Tabela 5.4 está em `dados/externos/epe/ben2020_tabela_5_4_v01.csv` (colunas fonte_ben, geracao_gwh_2019,
consumo_mil_tep_2019, subsetor_s38, observacao).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from mip.externos.ons import ORDEM_SUBSETORES_GERACAO

# D8 (Rodada 03, Seção 2.1): "outras não renováveis" (405 GWh) vão para o PET, com nota.
FONTE_BEN_PARA_SUBSETOR_D8 = {
    "HIDRÁULICA": "S38_HID",
    "EÓLICA": "S38_EOL",
    "SOLAR": "S38_SOL",
    "URÂNIO CONTIDO NO UO2": "S38_NUC",
    "LENHA": "S38_BIO",
    "BIODIESEL": "S38_BIO",
    "OUTRAS RENOVÁVEIS": "S38_BIO",
    "CARVÃO VAPOR": "S38_CAR",
    "GÁS NATURAL": "S38_GN",
    "ÓLEO DIESEL": "S38_PET",
    "ÓLEO COMBUSTÍVEL": "S38_PET",
    "OUTRAS NÃO RENOVÁVEIS": "S38_PET",
}

# Referência das instruções da Rodada 03, Seção 2.1 (GWh; tolerância 0.5)
REFERENCIA_D8_BRASIL = {"S38_HID": 378450, "S38_EOL": 55954, "S38_SOL": 4978, "S38_NUC": 16129, "S38_BIO": 1840,
                        "S38_CAR": 13823, "S38_GN": 47597, "S38_PET": 5174}
REFERENCIA_D8_RS = {"S38_HID": 14542.6, "S38_EOL": 5266.9, "S38_CAR": 2625.2, "S38_GN": 174.6, "S38_BIO": 68.2,
                    "S38_SOL": 0.0, "S38_PET": 0.0, "S38_NUC": 0.0}
REFERENCIA_D8_RB = {"S38_HID": 363907.4, "S38_EOL": 50687.1, "S38_SOL": 4978, "S38_BIO": 1771.8, "S38_CAR": 11197.8,
                    "S38_GN": 47422.4, "S38_PET": 5174, "S38_NUC": 16129}
TOLERANCIA_GWH = 0.5


def ler_tabela_5_4(caminho: str | Path) -> pd.DataFrame:
    tab = pd.read_csv(caminho)
    faltam = {"fonte_ben", "geracao_gwh_2019"} - set(tab.columns)
    if faltam:
        raise ValueError(f"{caminho}: colunas ausentes {sorted(faltam)}")
    return tab


def geracao_brasil_por_subsetor(tab54: pd.DataFrame) -> pd.Series:
    """GWh de serviço público por subsetor do S38 (D8). Erro se alguma fonte do BEN não tiver destino."""
    t = tab54[tab54["fonte_ben"] != "TOTAL"]
    sem = sorted(set(t["fonte_ben"]) - set(FONTE_BEN_PARA_SUBSETOR_D8))
    if sem:
        raise ValueError(f"fontes do BEN sem subsetor na D8: {sem}")
    s = t.assign(subsetor=t["fonte_ben"].map(FONTE_BEN_PARA_SUBSETOR_D8)).groupby("subsetor")["geracao_gwh_2019"].sum()
    return s.reindex(ORDEM_SUBSETORES_GERACAO, fill_value=0.0).astype(float)


def geracao_rs_ons(usinas: pd.DataFrame) -> pd.Series:
    """GWh do RS pelo ONS (usinas já classificadas; autoprodução fora do S38, Canoas → GN, como na 02b)."""
    rs = usinas[(usinas["regiao"] == "RS") & usinas["subsetor"].isin(ORDEM_SUBSETORES_GERACAO)]
    return rs.groupby("subsetor")["gwh"].sum().reindex(ORDEM_SUBSETORES_GERACAO, fill_value=0.0).astype(float)


def geracao_d8(tab54: pd.DataFrame, usinas: pd.DataFrame) -> pd.DataFrame:
    """Tabela região × subsetor (GWh) da D8: BRASIL (BEN), RS (ONS) e RB = BRASIL − RS. Erro se algum RB < 0."""
    br = geracao_brasil_por_subsetor(tab54)
    rs = geracao_rs_ons(usinas)
    rb = br - rs
    if (rb < -1e-9).any():
        raise ValueError(f"D8: RB negativo (o RS do ONS passa o Brasil do BEN): {rb[rb < 0].to_dict()}")
    linhas = []
    for regiao, origem, s in (("RS", "ONS (SIN), sem autoprodução", rs),
                              ("RB", "BEN 2020 (Tabela 5.4) − RS (ONS)", rb),
                              ("BRASIL", "BEN 2020, Tabela 5.4, serviço público", br)):
        d = {"regiao": regiao, "origem": origem}
        d.update({c: float(s[c]) for c in ORDEM_SUBSETORES_GERACAO})
        d["Total"] = float(s.sum())
        linhas.append(d)
    return pd.DataFrame(linhas)


def comparar_com_referencia_d8(tab: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for regiao, ref in (("BRASIL", REFERENCIA_D8_BRASIL), ("RS", REFERENCIA_D8_RS), ("RB", REFERENCIA_D8_RB)):
        obt = tab[tab["regiao"] == regiao].iloc[0]
        for c in ORDEM_SUBSETORES_GERACAO:
            e, o = float(ref[c]), float(obt[c])
            linhas.append({"grupo": f"{regiao} (D8)", "item": c, "esperado_gwh": e, "obtido_gwh": o,
                           "diferenca": o - e, "tolerancia": TOLERANCIA_GWH, "confere": abs(o - e) <= TOLERANCIA_GWH})
    return pd.DataFrame(linhas)


def consumo_especifico_d8(tab54: pd.DataFrame) -> pd.DataFrame:
    """Consumo específico (mil tep ÷ GWh → tep/MWh) por subsetor térmico com o mapeamento da D8.

    Diferença para a v01 (Rodada 02b): o PET inclui as 'outras não renováveis' (405 GWh, 137 mil tep), como a
    geração do PET na D8; assim a energia do satélite e os GWh usam a mesma base.
    """
    t = tab54.copy()
    t["subsetor"] = t["fonte_ben"].map(FONTE_BEN_PARA_SUBSETOR_D8)
    t = t[t["subsetor"].notna() & t["consumo_mil_tep_2019"].notna()]
    g = t.groupby("subsetor")[["consumo_mil_tep_2019", "geracao_gwh_2019"]].sum()
    g["tep_por_mwh"] = g["consumo_mil_tep_2019"] / g["geracao_gwh_2019"]
    g["fontes_ben"] = t.groupby("subsetor")["fonte_ben"].agg(" + ".join)
    return g.reset_index()


def ler_matriz_consolidada(caminho: str | Path) -> pd.DataFrame:
    """Aba Consolidada da matriz do BEN 2020 (ano-base 2019): linhas = fluxos, colunas = fontes (mil tep)."""
    bruto = pd.read_excel(caminho, sheet_name="Consolidada", header=None)
    nomes = [f"{a or ''} {b or ''}".replace("- ", "").replace("-", "").strip()
             for a, b in zip(bruto.iloc[1].fillna(""), bruto.iloc[2].fillna(""))]
    tab = bruto.iloc[3:].copy()
    tab.columns = ["fluxo"] + nomes[1:]
    tab["fluxo"] = tab["fluxo"].astype(str).str.strip()
    return tab.set_index("fluxo")
