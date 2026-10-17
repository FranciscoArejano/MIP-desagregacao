"""Rodada 05 — simulações finais na MIP v04 (blocos A0, A0_E4, A1, A2 e B), robustez nas 8 variantes.

Uso (na raiz do repositório, depois de scripts/rodada05_mip.py):
    python scripts/rodada05_simulacoes.py

Blocos (os da Rodada 04, Seção 4 das instruções da Rodada 05; choques de R$ 1000 mi na demanda final do RS):
- A0: MIP original, os 9 cenários do artigo (inclui R4a e R4b) — replicação.
- A0_E4: MIP original com os valores da E4 retirados do S38 de cada região e somados a S19, S05 e S04 (Seção 3.2).
- A1: v04, o S38 da cesta repartido entre DIS-RS e GAS-RS na proporção das vendas à demanda final.
- A2: v04, o S38 da cesta remapeado: renováveis → 100% EOL-RS (D12); fósseis → CAR-RS e GN-RS na proporção do VBP de
  2019 na v04 (D13, recalculada); E1 como no A1 (D14). Sensibilidades: 50% EOL + 50% SOL; 2/3 EOL + 1/3 TRA;
  100% CAR; 100% GN.
- B: operação por tecnologia: R$ 1000 mi em EOL, SOL (latente, com a D18), HID, BIO, CAR, GN e DIS do RS; e 1 TWh de
  cada tecnologia ao R$/MWh da versão (SOL-RS: R$/MWh do SOL-RB).
Robustez: todos os cenários nas variantes _P2, _E2, _E3, _E4, _gas4dist, _rap_media, _k060 e _eta005 (vetor do A2
fóssil fixo, o da v04; B por TWh ao R$/MWh de cada variante).

Saídas: parametros/cenarios_v04.csv; resultados/rodada05/simulacoes_v04.xlsx.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from mip import cenarios as cen  # noqa: E402
from mip.caminhos import PASTA_PARAMETROS, PASTA_RESULTADOS  # noqa: E402
from mip.desagregacao import ler_especificacao, realocar_emissoes_original  # noqa: E402
from mip.exportacao import salvar_tabelas  # noqa: E402
from mip.leitura import ler_mip, ler_mip_longo, ler_mip_original  # noqa: E402

_spec = importlib.util.spec_from_file_location("r04s", RAIZ / "scripts" / "rodada04_simulacoes.py")
r04s = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r04s)  # funções das simulações da Rodada 04 (não grava nada)

SAIDA = PASTA_RESULTADOS / "rodada05"
NOME = "MIP_RS_RB_2019_S38_11sub"
V = "v04"
CEN_ARTIGO, TECS, NOME_TEC, ROTULOS = r04s.CEN_ARTIGO, r04s.TECS, dict(r04s.NOME_TEC), r04s.ROTULOS
NOME_TEC["S38_SOL"] = "Solar (latente, TUST do RS)"
VARIANTES = ["_P2", "_E2", "_E3", "_E4", "_gas4dist", "_rap_media", "_k060", "_eta005"]
CEN_ROBUSTEZ = ["A2_E1", "A2_R1", "A2_F1"] + [f"B_TWh_{s.replace('S38_', '')}" for s in TECS]
LIMITACAO = ("LIMITAÇÃO: HID, EOL e SOL têm a mesma estrutura de insumos não energéticos (não há dado de custo por "
             "tecnologia); as diferenças entre elas vêm do VBP (R$/MWh) e, no SOL-RS, da coluna latente (coeficientes "
             "do SOL-RB, com a TUST por MWh do RS — D18, HIPÓTESE), e não de tecnologia.")


def tabela_twh(tab_b: dict, versao: str) -> pd.DataFrame:
    """B por TWh: t CO₂e por TWh, g CO₂e/kWh e emissões evitadas em relação ao carvão e ao gás natural."""
    imp = tab_b["impactos"]
    imp = imp[(imp["versao"] == versao) & imp["cenario"].str.startswith("B_TWh_")].set_index("cenario")
    car, gn = imp.loc["B_TWh_CAR", "co2e_total"], imp.loc["B_TWh_GN", "co2e_total"]
    linhas = []
    for s in TECS:
        x = imp.loc[f"B_TWh_{s.replace('S38_', '')}"]
        linhas.append({"versao": versao, "tecnologia": NOME_TEC[s], "subsetor (RS)": s,
                       "R$/MWh = choque de 1 TWh (R$ mi)": x["dY_total"], "ΔX total (R$ mi)": x["dX_total"],
                       "t CO₂e por TWh (total)": x["co2e_total"], "diretas": x["co2e_diretas"],
                       "indiretas": x["co2e_indiretas"], "g CO₂e/kWh": x["co2e_total"] / 1000,
                       "% indiretas": x["pct_indiretas"], "% no RB": x["pct_co2e_RB"],
                       "evitadas por TWh se substituir o carvão (t)": car - x["co2e_total"],
                       "evitadas por TWh se substituir o gás natural (t)": gn - x["co2e_total"]})
    return pd.DataFrame(linhas)


def robustez(por_versao: dict[str, dict]) -> pd.DataFrame:
    """Faixa mín–máx de CO₂e, IC e % no RB nos cenários da robustez, na v04 e nas variantes."""
    imp = pd.concat([t["impactos"] for t in por_versao.values()], ignore_index=True)
    imp = imp[imp["cenario"].isin(CEN_ROBUSTEZ)]
    linhas = []
    for c in CEN_ROBUSTEZ:
        g = imp[imp["cenario"] == c].set_index("versao")
        d = {"cenario": c, "versões": len(g)}
        for k, rot in (("co2e_total", "CO₂e total (t)"), ("IC", "IC"), ("pct_co2e_RB", "% no RB")):
            d[f"{rot} {V}"] = g.loc[V, k]
            d[f"{rot} mín"], d[f"{rot} máx"] = g[k].min(), g[k].max()
            d[f"{rot} versão do mín"], d[f"{rot} versão do máx"] = g[k].idxmin(), g[k].idxmax()
            d[f"{rot} amplitude ÷ {V} (%)"] = 100 * (g[k].max() - g[k].min()) / g.loc[V, k]
        linhas.append(d)
    return pd.DataFrame(linhas)


def desvios(tab: pd.DataFrame, base: pd.DataFrame, rotulo: str) -> pd.DataFrame:
    """Indicadores de uma versão com a variação (%) em relação à base (mesmo cenário)."""
    cols = ["CO₂e total (t)", "IC (t CO₂e por R$ mi)", "% CO₂e no RB", "% indiretas", "ΔX total (R$ mi)"]
    b = base.set_index("cenario")
    out = tab.copy()
    for c in cols:
        ref = out["cenario"].map(b[c])
        out[f"{c} {rotulo}"] = ref
        out[f"variação de {c} (%)"] = 100 * (out[c] - ref) / ref.abs()
    return out


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    G = r04s.gwh_v03()  # GWh da D8 (o mesmo arquivo da v03)
    m0 = ler_mip_original()
    m04 = ler_mip(SAIDA / f"{NOME}_{V}.xlsx")
    todos = r04s.cenarios(m04, G)  # D13 pelo VBP da v04
    with open(PASTA_PARAMETROS / f"cenarios_{V}.csv", "w", encoding="utf-8") as f:
        f.write("# Rodada 05 — cenários das simulações finais na v04 (choques em R$ mi na demanda final de setores do RS).\n"
                "# Prefixos: A0_ (MIP original; também na A0_E4), A1_ (v04; S38 agregado → DIS/GAS ∝ vendas à demanda "
                "final), A2_ (v04; S38 por tecnologia: renováveis → EOL, fósseis → CAR e GN ∝ VBP da v04; E1 como no A1), "
                "A2_<c>_<sens> (sensibilidades do A2), B_ (R$ 1 bi por tecnologia), B_TWh_ (1 TWh ao R$/MWh da v04; nas "
                "variantes, ao R$/MWh de cada variante).\n# Gerado por scripts/rodada05_simulacoes.py.\n")
        todos.to_csv(f, index=False, float_format="%.17g")
    sel = lambda p: todos[todos["cenario"].str.startswith(p)]  # noqa: E731
    a0 = cen.executar(m0, sel("A0_"), "original")
    e4 = ler_especificacao(PASTA_PARAMETROS / f"especificacao_{V}_E4.yaml").realocacao_emissoes
    m0_e4 = realocar_emissoes_original(m0, e4, "S38")
    a0_e4 = cen.executar(m0_e4, sel("A0_"), "original_E4")
    a1 = cen.executar(m04, sel("A1_"), V)
    a2_todos = cen.executar(m04, sel("A2_"), V)
    a2 = {k: (v[v["cenario"].isin([f"A2_{c}" for c in CEN_ARTIGO])] if "cenario" in v.columns else v)
          for k, v in a2_todos.items()}
    b = cen.executar(m04, sel("B_"), V)
    base = r04s.indicadores({"impactos": pd.concat([a2_todos["impactos"], b["impactos"]], ignore_index=True),
                             "participacao_setor": pd.concat([a2_todos["participacao_setor"], b["participacao_setor"]])})
    # variantes: todos os cenários do A2 e do B (B por TWh ao R$/MWh de cada variante)
    por_versao = {V: {"impactos": pd.concat([a2_todos["impactos"], b["impactos"]], ignore_index=True)}}
    tw = [tabela_twh(b, V)]
    detalhe = [base]
    abas_var = {}
    for suf in VARIANTES:
        nome = f"{V}{suf}"
        mv = ler_mip_longo(SAIDA / f"{NOME}_{nome}_longo.csv")
        cv = pd.concat([sel("A2_"), sel("B_")[~sel("B_")["cenario"].str.startswith("B_TWh_")], r04s.b_twh(mv, G)],
                       ignore_index=True)
        t = cen.executar(mv, cv, nome)
        por_versao[nome] = t
        tw.append(tabela_twh(t, nome))
        ind = r04s.indicadores(t)
        detalhe.append(ind)
        if suf in ("_E4", "_rap_media"):
            abas_var[suf.lstrip("_")] = desvios(ind, base, "na v04")
    rob = robustez(por_versao)
    tw = pd.concat(tw, ignore_index=True)
    b1 = r04s.indicadores(b, "B_")
    b1 = b1[~b1["cenario"].str.startswith("B_TWh_")].copy()
    b1.insert(2, "tecnologia", [NOME_TEC[f"S38_{c[2:]}"] for c in b1["cenario"]])
    b1["t CO₂e por R$ mi demandado"] = b1["CO₂e total (t)"] / 1000
    comp = []
    for c in ("E1", "R1", "F1"):
        for bloco, t in (("A0 (artigo, MIP original)", a0), ("A0_E4 (MIP original com a E4)", a0_e4),
                         ("A1 (v04, S38 → DIS/GAS)", a1), ("A2 (v04, S38 por tecnologia)", a2)):
            x = r04s.indicadores(t)
            x = x[x["cenario"].str.endswith(f"_{c}")].iloc[0]
            comp.append({"cenario": c, "bloco": bloco, **{k: x[k] for k in list(ROTULOS.values())}})
    comp = pd.DataFrame(comp)
    art = r04s.tabelas_artigo(a2)
    ind_a0 = r04s.indicadores(a0)
    abas = {"A0": ind_a0, "A0_E4": desvios(r04s.indicadores(a0_e4), ind_a0, "no A0"), "A1": r04s.indicadores(a1),
            "A2": r04s.indicadores(a2), "A2_sens": r04s.indicadores(a2_todos), "B_RS1bi": b1, "B_TWh": tw,
            "robustez": rob, "robustez_detalhe": pd.concat(detalhe, ignore_index=True), **abas_var,
            "comparacao_artigo": comp, **art,
            "top10_A0": a0["top10"], "top10_A0_E4": a0_e4["top10"], "top10_A1": a1["top10"],
            "top10_A2": a2_todos["top10"], "top10_B": b["top10"],
            "diretas_indiretas": pd.concat([a0["diretas_indiretas"], a0_e4["diretas_indiretas"], a1["diretas_indiretas"],
                                            a2_todos["diretas_indiretas"], b["diretas_indiretas"]], ignore_index=True),
            "participacao_S38": pd.concat([a0["participacao_setor"], a0_e4["participacao_setor"],
                                           a1["participacao_setor"], a2_todos["participacao_setor"],
                                           b["participacao_setor"]], ignore_index=True),
            "regioes": pd.concat([a0["regioes"], a0_e4["regioes"], a1["regioes"], a2_todos["regioes"], b["regioes"]],
                                 ignore_index=True),
            "reparticao_S38": pd.concat([a1["reparticao"], a2_todos["reparticao"]], ignore_index=True),
            "cenarios": todos}
    salvar_tabelas(SAIDA / f"simulacoes_{V}.xlsx", abas, leiame=[
        "Rodada 05 — simulações finais na MIP v04 (choques de R$ 1000 mi na demanda final de setores do RS, salvo o "
        "bloco B por TWh).",
        "A0: MIP original (replicação; inclui R4a e R4b). A0_E4: MIP original com os valores da E4 (refino, exploração "
        "de petróleo e gás e mineração de carvão do SEEG 13.0) retirados do S38 e somados a S19, S05 e S04 da mesma "
        "região; variação em relação ao A0. A1: v04, S38 → DIS e GAS do RS ∝ vendas à demanda final. A2: v04, S38 por "
        "tecnologia (renováveis → 100% EOL-RS; fósseis → CAR-RS e GN-RS ∝ VBP de 2019 na v04; E1 como no A1). "
        "A2_sens: sensibilidades (50% EOL + 50% SOL; 2/3 EOL + 1/3 TRA; 100% CAR; 100% GN).",
        "B_RS1bi: R$ 1000 mi por tecnologia do RS. B_TWh: 1 TWh de cada tecnologia; na linha v04 ao R$/MWh da v04, nas "
        "linhas das variantes ao R$/MWh de cada variante (SOL-RS latente: R$/MWh do SOL-RB da mesma versão, com a TUST "
        "por MWh do RS — D18); g CO₂e/kWh = t por TWh ÷ 1000; 'evitadas' = CO₂e do carvão (ou do gás natural) − CO₂e "
        "da tecnologia, por TWh.",
        LIMITACAO,
        "robustez: A2 (E1, R1, F1) e B por TWh na v04 e nas 8 variantes (_P2, _E2, _E3, _E4, _gas4dist, _rap_media, "
        "_k060, _eta005): faixa mín–máx de CO₂e total, IC e % no RB; robustez_detalhe: todos os cenários em cada "
        "versão; E4 e rap_media: os cenários dessas variantes com a variação em relação à v04.",
        "tabela1_artigo a tabela4_artigo: as tabelas da Rodada 04 (formato de trabalho); as tabelas no formato do "
        "artigo saem de scripts/rodada05_artigo.py (pasta artigo/).",
        "Emissões diretas = e · ΔY (setores chocados); indiretas = total − diretas (eq. 12–14 do modelo).",
        "Gerado por scripts/rodada05_simulacoes.py."])
    a2i = r04s.indicadores(a2).set_index("cenario")
    print(f"[simulações v04] {todos['cenario'].nunique()} cenários; {len(abas)} abas; A2 E1/R1/F1 CO₂e: "
          f"{a2i.loc[['A2_E1', 'A2_R1', 'A2_F1'], 'CO₂e total (t)'].round(1).to_dict()}; B por TWh: "
          f"{tw[tw['versao'] == V].set_index('subsetor (RS)')['t CO₂e por TWh (total)'].round(1).to_dict()}")


if __name__ == "__main__":
    main()
