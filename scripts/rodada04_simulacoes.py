"""Rodada 04 — simulações do artigo na MIP v03 (blocos A0, A1, A2 e B), robustez nas variantes, tabelas e figuras.

Uso (na raiz do repositório, depois de scripts/rodada04_mip.py):
    python scripts/rodada04_simulacoes.py

Blocos (Seção 3 das instruções da Rodada 04; choques de R$ 1000 mi na demanda final de setores do RS):
- A0: MIP original, os 9 cenários do artigo (inclui R4a e R4b) — replicação.
- A1: v03, o S38 da cesta repartido entre DIS-RS e GAS-RS na proporção das vendas à demanda final (regra do executor).
- A2: v03, o S38 da cesta remapeado para tecnologias: cestas renováveis (R1, R2, R3, R4a) → 100% EOL-RS (D12);
  cestas fósseis (F1, F2, F3) → CAR-RS e GN-RS na proporção do VBP de 2019 na v03 (D13); E1 como no A1 (D14).
  Sensibilidades: 50% EOL + 50% SOL-RS; 2/3 EOL + 1/3 TRA-RS; 100% CAR-RS; 100% GN-RS.
- B: operação por tecnologia: R$ 1000 mi em EOL, SOL (latente), HID, BIO, CAR, GN e DIS do RS; e 1 TWh de cada
  tecnologia, valorado ao R$/MWh da MIP (SOL-RS latente: R$/MWh do SOL-RB).
Robustez: A2 (R1, F1, E1) e B por TWh nas variantes _P2, _E2, _E3, _gas4dist, _rap_ons, _k060 e _eta005.

Saídas: parametros/cenarios_v03.csv; resultados/rodada04/simulacoes_v03.xlsx; resultados/rodada04/figuras/*.png.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from mip import cenarios as cen  # noqa: E402
from mip import referencia as ref  # noqa: E402
from mip.caminhos import PASTA_INTERMEDIARIOS, PASTA_PARAMETROS, PASTA_RESULTADOS  # noqa: E402
from mip.exportacao import salvar_tabelas  # noqa: E402
from mip.leitura import ler_mip, ler_mip_longo, ler_mip_original  # noqa: E402

SAIDA = PASTA_RESULTADOS / "rodada04"
FIG = SAIDA / "figuras"
NOME = "MIP_RS_RB_2019_S38_11sub"
CEN_ARTIGO = ["E1", "R1", "F1", "R2", "R3", "R4a", "F2", "F3"]  # D11: R4b só no A0
RENOV, FOSS = ["R1", "R2", "R3", "R4a"], ["F1", "F2", "F3"]
TECS = ["S38_EOL", "S38_SOL", "S38_HID", "S38_BIO", "S38_CAR", "S38_GN"]
NOME_TEC = {"S38_EOL": "Eólica", "S38_SOL": "Solar (latente)", "S38_HID": "Hidráulica", "S38_BIO": "Biomassa",
            "S38_CAR": "Carvão", "S38_GN": "Gás natural", "S38_DIS": "Distribuição (mix da rede de 2019)"}
VERSAO_SOL = "v03 (SOL-RS com a TUST/MWh do RS)"
VARIANTES = ["_P2", "_E2", "_E3", "_gas4dist", "_rap_ons", "_k060", "_eta005"]
SENS_RENOV = {"EOL50SOL50": {"S38_EOL": 0.5, "S38_SOL": 0.5}, "EOL67TRA33": {"S38_EOL": 2 / 3, "S38_TRA": 1 / 3}}
SENS_FOSS = {"CAR100": {"S38_CAR": 1.0}, "GN100": {"S38_GN": 1.0}}
LIMITACAO = ("LIMITAÇÃO: HID, EOL e SOL têm a mesma estrutura de insumos não energéticos (não há dado de custo por "
             "tecnologia); as diferenças entre elas vêm do VBP (R$/MWh) e, no SOL-RS, da coluna latente (espelho do "
             "SOL-RB), e não de tecnologia.")
ROTULOS = {"dY_total": "Choque (R$ mi)", "dX_total": "ΔX total (R$ mi)", "dX_RS": "ΔX RS (R$ mi)",
           "dX_RB": "ΔX RB (R$ mi)", "co2e_total": "CO₂e total (t)", "co2e_RS": "CO₂e RS (t)", "co2e_RB": "CO₂e RB (t)",
           "IC": "IC (t CO₂e por R$ mi)", "producao_por_mil_t": "Produção por mil t CO₂e (R$ mi)",
           "pct_co2e_RB": "% CO₂e no RB", "co2e_diretas": "CO₂e diretas (t)", "co2e_indiretas": "CO₂e indiretas (t)",
           "pct_indiretas": "% indiretas", "pct_S38": "% das emissões no S38 (subsetores)"}


# ---------------------------------------------------------------------------------------------
# cenários
# ---------------------------------------------------------------------------------------------
def gwh_v03() -> dict:
    g = pd.read_csv(PASTA_INTERMEDIARIOS / "geracao_2019_regiao_subsetor_v03.csv").set_index("regiao")
    return {r: g.loc[r].drop(["origem", "Total"]).astype(float).to_dict() for r in ("RS", "RB")}


def preco_mwh(m, G) -> dict:
    """R$/MWh de cada tecnologia do RS na MIP m (SOL-RS latente: o do SOL-RB)."""
    out = {}
    for s in TECS:
        r = "RB" if s == "S38_SOL" else "RS"
        out[s] = m.X[m.indice(r, s)] * 1e6 / (G[r][s] * 1000)
    return out


def cenarios(m03, G) -> pd.DataFrame:
    """Todos os cenários da rodada no formato do executor (cenario, regiao, setor, valor_R$mi)."""
    linhas = []

    def add(nome, setor, v):
        linhas.append((nome, "RS", setor, float(v)))

    for c, d in ref.CENARIOS_RS.items():  # A0 (original; S38 agregado)
        for s, v in d.items():
            add(f"A0_{c}", s, v)
    for c in CEN_ARTIGO:  # A1 (v03; S38 agregado → DIS e GAS ∝ vendas à demanda final)
        for s, v in ref.CENARIOS_RS[c].items():
            add(f"A1_{c}", s, v)
    xr = {s: m03.X[m03.indice("RS", s)] for s in ("S38_CAR", "S38_GN")}
    foss = {s: x / sum(xr.values()) for s, x in xr.items()}  # D13: ∝ VBP de 2019 na v03

    def remap(c, pesos, nome):
        for s, v in ref.CENARIOS_RS[c].items():
            if s != "S38":
                add(nome, s, v)
            elif pesos is None:
                add(nome, "S38", v)  # E1 (D14): como no A1
            else:
                for sub, w in pesos.items():
                    add(nome, sub, v * w)

    for c in CEN_ARTIGO:  # A2
        remap(c, {"S38_EOL": 1.0} if c in RENOV else foss if c in FOSS else None, f"A2_{c}")
    for c in RENOV:  # A2, sensibilidades
        for k, p in SENS_RENOV.items():
            remap(c, p, f"A2_{c}_{k}")
    for c in FOSS:
        for k, p in SENS_FOSS.items():
            remap(c, p, f"A2_{c}_{k}")
    for s in TECS + ["S38_DIS"]:  # B, R$ 1 bi
        add(f"B_{s.replace('S38_', '')}", s, 1000.0)
    for s, p in preco_mwh(m03, G).items():  # B, 1 TWh
        add(f"B_TWh_{s.replace('S38_', '')}", s, p)
    return pd.DataFrame(linhas, columns=cen.COLUNAS)


def b_twh(m, G) -> pd.DataFrame:
    return pd.DataFrame([(f"B_TWh_{s.replace('S38_', '')}", "RS", s, p) for s, p in preco_mwh(m, G).items()],
                        columns=cen.COLUNAS)


def sol_com_tust_do_rs(m, G):
    """Hipótese alternativa (revisão R04, #1): a coluna latente do SOL-RS é o espelho do SOL-RB, e paga a TUST por
    MWh do RB; aqui as linhas S38_TRA da coluna latente são multiplicadas para que o SOL-RS pague a TUST por MWh
    das fontes do RS (a mesma em todas, V1). Só o modelo muda (a MIP não tem produção de SOL-RS)."""
    import copy

    tra = [m.indice(q, "S38_TRA") for q in ("RS", "RB")]
    tust_rs = m.Z[tra, m.indice("RS", "S38_EOL")].sum() * 1e6 / (G["RS"]["S38_EOL"] * 1000)  # R$/MWh
    cl = m.coef_latentes
    sel = (cl["regiao"] == "RS") & (cl["subsetor"] == "S38_SOL") & (cl["tipo_linha"] == "setor") & \
        (cl["codigo_linha"] == "S38_TRA")
    tust_lat = cl.loc[sel, "coeficiente"].sum() * preco_mwh(m, G)["S38_SOL"]
    m2 = copy.copy(m)
    m2.coef_latentes = cl.copy()
    m2.coef_latentes.loc[sel, "coeficiente"] *= tust_rs / tust_lat
    return m2, {"TUST do RS (R$/MWh)": tust_rs, "TUST do SOL-RS latente (R$/MWh)": tust_lat,
                "fator nas linhas S38_TRA": tust_rs / tust_lat}


# ---------------------------------------------------------------------------------------------
# tabelas
# ---------------------------------------------------------------------------------------------
def indicadores(tab: dict, prefixo: str | None = None) -> pd.DataFrame:
    imp = tab["impactos"].copy()
    part = tab["participacao_setor"]
    s38 = part[part["codigo"] == "S38 (total)"].set_index(["versao", "cenario"])["pct_co2e_total"]
    imp["pct_S38"] = [s38.get((v, c), np.nan) for v, c in zip(imp["versao"], imp["cenario"])]
    if prefixo is not None:
        imp = imp[imp["cenario"].str.startswith(prefixo)]
    cols = ["versao", "cenario"] + list(ROTULOS)
    return imp[cols].rename(columns=ROTULOS)


def rotulo_cenario(nome: str) -> str:
    base = nome.split("_")[1] if nome.count("_") >= 1 else nome
    return f"{base} — {ref.NOMES_CENARIOS.get(base, '')}".rstrip(" —")


def tabelas_artigo(tab_a2: dict) -> dict:
    """Tabelas 1–4 do artigo refeitas com o A2 (ordem e rótulos inferidos: ver o relatório)."""
    imp = tab_a2["impactos"].set_index("cenario")
    nomes = [f"A2_{c}" for c in CEN_ARTIGO]
    t1 = pd.DataFrame({"Cenário": [rotulo_cenario(n) for n in nomes],
                       "ΔX total": imp.loc[nomes, "dX_total"].values, "ΔX RS": imp.loc[nomes, "dX_RS"].values,
                       "ΔX RB": imp.loc[nomes, "dX_RB"].values, "CO₂e total": imp.loc[nomes, "co2e_total"].values,
                       "CO₂e RS": imp.loc[nomes, "co2e_RS"].values, "CO₂e RB": imp.loc[nomes, "co2e_RB"].values,
                       "IC": imp.loc[nomes, "IC"].values, "% CO₂e no RB": imp.loc[nomes, "pct_co2e_RB"].values,
                       "% indiretas": imp.loc[nomes, "pct_indiretas"].values,
                       "Produção por mil t CO₂e": imp.loc[nomes, "producao_por_mil_t"].values})
    top = tab_a2["top10"]
    t2 = top[top["cenario"] == "A2_R1"].drop(columns=["versao", "cenario"]).copy()
    reg = tab_a2["regioes"].set_index(["cenario", "regiao"])
    t3 = pd.DataFrame([{"Cenário": rotulo_cenario(n),
                        "ΔX RS": reg.loc[(n, "RS"), "dX"], "ΔX RB": reg.loc[(n, "RB"), "dX"],
                        "% ΔX no RB": reg.loc[(n, "RB"), "pct_dX"],
                        "CO₂e RS": reg.loc[(n, "RS"), "co2e"], "CO₂e RB": reg.loc[(n, "RB"), "co2e"],
                        "% CO₂e no RB": reg.loc[(n, "RB"), "pct_co2e"],
                        "IC RS": reg.loc[(n, "RS"), "IC"], "IC RB": reg.loc[(n, "RB"), "IC"]} for n in nomes])
    di = tab_a2["diretas_indiretas"].set_index("cenario")
    t4 = pd.DataFrame({"Cenário": [rotulo_cenario(n) for n in nomes],
                       "CO₂e total": di.loc[nomes, "co2e_total"].values, "Diretas": di.loc[nomes, "co2e_diretas"].values,
                       "Indiretas": di.loc[nomes, "co2e_indiretas"].values, "% diretas": di.loc[nomes, "pct_diretas"].values,
                       "% indiretas": di.loc[nomes, "pct_indiretas"].values})
    return {"tabela1_artigo": t1, "tabela2_artigo": t2, "tabela3_artigo": t3, "tabela4_artigo": t4}


def tabela_twh(tab_b: dict, versao: str) -> pd.DataFrame:
    imp = tab_b["impactos"]
    imp = imp[(imp["versao"] == versao) & imp["cenario"].str.startswith("B_TWh_")].set_index("cenario")
    car = imp.loc["B_TWh_CAR", "co2e_total"]
    linhas = []
    for s in TECS:
        n = f"B_TWh_{s.replace('S38_', '')}"
        x = imp.loc[n]
        linhas.append({"versao": versao, "tecnologia": NOME_TEC[s], "subsetor (RS)": s,
                       "R$/MWh = choque de 1 TWh (R$ mi)": x["dY_total"], "ΔX total (R$ mi)": x["dX_total"],
                       "t CO₂e por TWh (total)": x["co2e_total"], "diretas": x["co2e_diretas"],
                       "indiretas": x["co2e_indiretas"], "% indiretas": x["pct_indiretas"], "% no RB": x["pct_co2e_RB"],
                       "evitadas por TWh se substituir o carvão (t)": car - x["co2e_total"]})
    return pd.DataFrame(linhas)


def robustez(por_versao: dict[str, dict]) -> pd.DataFrame:
    cen_r = ["A2_R1", "A2_F1", "A2_E1"] + [f"B_TWh_{s.replace('S38_', '')}" for s in TECS]
    imp = pd.concat([t["impactos"] for t in por_versao.values()], ignore_index=True)
    imp = imp[imp["cenario"].isin(cen_r)]
    linhas = []
    for c in cen_r:
        g = imp[imp["cenario"] == c].set_index("versao")
        d = {"cenario": c, "versões": len(g)}
        for k, rot in (("co2e_total", "CO₂e total (t)"), ("IC", "IC"), ("pct_co2e_RB", "% no RB")):
            d[f"{rot} v03"] = g.loc["v03", k]
            d[f"{rot} mín"], d[f"{rot} máx"] = g[k].min(), g[k].max()
            d[f"{rot} versão do mín"], d[f"{rot} versão do máx"] = g[k].idxmin(), g[k].idxmax()
            d[f"{rot} amplitude ÷ v03 (%)"] = 100 * (g[k].max() - g[k].min()) / g.loc["v03", k]
        linhas.append(d)
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------------------------
# figuras (RASCUNHO) — paleta categórica de referência: slot 1 azul, slot 2 laranja (validada: 2 slots, claro)
# ---------------------------------------------------------------------------------------------
COR = {"s1": "#2a78d6", "s2": "#eb6834", "fundo": "#fcfcfb", "texto": "#0b0b0b", "texto2": "#52514e", "grade": "#e4e3df"}


def _eixo(ax):
    ax.set_facecolor(COR["fundo"])
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(COR["grade"])
    ax.tick_params(colors=COR["texto2"], labelsize=9)
    ax.grid(axis="x" if ax.get_label() == "h" else "y", color=COR["grade"], linewidth=0.8)
    ax.set_axisbelow(True)


def _fmt(v):
    return f"{v:,.0f}".replace(",", " ")


def figuras(tab_a0: dict, tab_a2: dict, tw: pd.DataFrame) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": COR["texto"], "axes.labelcolor": COR["texto2"]})
    saidas = []

    # Fig. 1 — top-10 emissores na cesta renovável R1 (A2), barras horizontais; cor = região
    top = tab_a2["top10"]
    top = top[top["cenario"] == "A2_R1"].sort_values("CO2e induzido (t)")
    fig, ax = plt.subplots(figsize=(8, 5), facecolor=COR["fundo"])
    ax.set_label("h")
    _eixo(ax)
    cores = [COR["s1"] if r == "RS" else COR["s2"] for r in top["regiao"]]
    rot = [f"{r} {c}" for r, c in zip(top["regiao"], top["codigo"])]
    ax.barh(rot, top["CO2e induzido (t)"], color=cores, height=0.6, edgecolor=COR["fundo"], linewidth=0.5)
    for y, (v, p) in enumerate(zip(top["CO2e induzido (t)"], top["% do CO2e total"])):
        ax.text(v, y, f"  {_fmt(v)} t ({p:.1f}%)", va="center", fontsize=8.5, color=COR["texto2"])
    ax.set_xlabel("CO₂e induzido (t) por R$ 1 bi na cesta R1")
    ax.set_xlim(0, top["CO2e induzido (t)"].max() * 1.32)
    from matplotlib.patches import Patch

    ax.legend(handles=[Patch(color=COR["s1"], label="setor do RS"), Patch(color=COR["s2"], label="setor do RB")],
              frameon=False, loc="lower right", fontsize=9)
    ax.set_title("RASCUNHO — Fig. 1: 10 setores que mais emitem na cesta renovável R1 (A2, v03)",
                 loc="left", fontsize=11, color=COR["texto"])
    fig.tight_layout()
    saidas.append(FIG / "fig1_top10_R1_A2.png")
    fig.savefig(saidas[-1], dpi=150, facecolor=COR["fundo"])
    plt.close(fig)

    # Fig. 2 — diretas × indiretas por cenário, A0 × A2 (barras empilhadas lado a lado)
    d0 = tab_a0["diretas_indiretas"].set_index("cenario")
    d2 = tab_a2["diretas_indiretas"].set_index("cenario")
    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=COR["fundo"])
    _eixo(ax)
    larg = 0.36
    x = np.arange(len(CEN_ARTIGO))
    for desl, d, pref in ((-larg / 2 - 0.02, d0, "A0"), (larg / 2 + 0.02, d2, "A2")):
        dir_ = np.array([d.loc[f"{pref}_{c}", "co2e_diretas"] for c in CEN_ARTIGO]) / 1000
        ind = np.array([d.loc[f"{pref}_{c}", "co2e_indiretas"] for c in CEN_ARTIGO]) / 1000
        ax.bar(x + desl, dir_, larg, color=COR["s1"], edgecolor=COR["fundo"], linewidth=0.5)
        ax.bar(x + desl, ind, larg, bottom=dir_, color=COR["s2"], edgecolor=COR["fundo"], linewidth=0.5)
        for xi, t in zip(x + desl, dir_ + ind):
            ax.text(xi, t, f"{pref}\n{t:.0f}", ha="center", va="bottom", fontsize=7.5, color=COR["texto2"])
    ax.set_xticks(x, CEN_ARTIGO)
    ax.set_ylabel("mil t CO₂e por R$ 1 bi")
    ax.set_ylim(0, max(d0["co2e_total"].max(), d2["co2e_total"].max()) / 1000 * 1.18)
    from matplotlib.patches import Patch

    ax.legend(handles=[Patch(color=COR["s1"], label="diretas"), Patch(color=COR["s2"], label="indiretas")],
              frameon=False, loc="upper right", fontsize=9)
    ax.set_title("RASCUNHO — Fig. 2: emissões diretas e indiretas por cenário — A0 (MIP original) × A2 (v03, "
                 "S38 por tecnologia)", loc="left", fontsize=10.5, color=COR["texto"])
    fig.tight_layout()
    saidas.append(FIG / "fig2_diretas_indiretas_A0_A2.png")
    fig.savefig(saidas[-1], dpi=150, facecolor=COR["fundo"])
    plt.close(fig)

    # Fig. 3 — t CO₂e por TWh por tecnologia (B), empilhado diretas + indiretas; dois painéis lineares (fósseis e
    # demais), porque as escalas diferem em duas ordens de grandeza (sem escala log em barras)
    t = tw[tw["versao"] == "v03"].set_index("subsetor (RS)")
    from matplotlib.patches import Patch

    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.6), facecolor=COR["fundo"], gridspec_kw={"width_ratios": [1, 1]})
    for ax, grupo, titulo in ((axs[0], ["S38_GN", "S38_CAR"], "Fósseis (mil t CO₂e por TWh)"),
                              (axs[1], ["S38_HID", "S38_SOL", "S38_EOL", "S38_BIO"], "Demais fontes (mil t CO₂e por TWh)")):
        ax.set_label("h")
        _eixo(ax)
        sub = t.loc[grupo]
        y = np.arange(len(sub))
        d, i_ = sub["diretas"] / 1000, sub["indiretas"] / 1000
        ax.barh(y, d, 0.55, color=COR["s1"], edgecolor=COR["fundo"], linewidth=0.5)
        ax.barh(y, i_, 0.55, left=d, color=COR["s2"], edgecolor=COR["fundo"], linewidth=0.5)
        tot = (d + i_).to_numpy()
        for yi, v in zip(y, tot):
            ax.text(v, yi, f"  {v:,.1f}".replace(",", " "), va="center", fontsize=8.5, color=COR["texto2"])
        ax.set_yticks(y, sub["tecnologia"])
        ax.set_xlim(0, tot.max() * 1.25)
        ax.set_title(titulo, loc="left", fontsize=9.5, color=COR["texto2"])
    axs[1].legend(handles=[Patch(color=COR["s1"], label="diretas"), Patch(color=COR["s2"], label="indiretas")],
                  frameon=False, loc="lower right", fontsize=9)
    fig.suptitle("RASCUNHO — Fig. 3: emissões por TWh demandado, por tecnologia do RS (bloco B, v03)",
                 x=0.01, ha="left", fontsize=11, color=COR["texto"])
    fig.text(0.01, 0.01, "Escalas diferentes nos dois painéis. HID, EOL e SOL têm a mesma estrutura de insumos "
             "(sem dado de custo por tecnologia); SOL-RS é latente (espelho do SOL-RB, com a TUST/MWh do RB: hipótese).", fontsize=7.5, color=COR["texto2"])
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    saidas.append(FIG / "fig3_emissoes_por_TWh_B.png")
    fig.savefig(saidas[-1], dpi=150, facecolor=COR["fundo"])
    plt.close(fig)
    return saidas


# ---------------------------------------------------------------------------------------------
def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    G = gwh_v03()
    m0 = ler_mip_original()
    m03 = ler_mip(SAIDA / f"{NOME}_v03.xlsx")
    todos = cenarios(m03, G)
    with open(PASTA_PARAMETROS / "cenarios_v03.csv", "w", encoding="utf-8") as f:
        f.write("# Rodada 04 — cenários das simulações na v03 (choques em R$ mi na demanda final de setores do RS).\n"
                "# Prefixos: A0_ (MIP original), A1_ (v03; S38 agregado → DIS/GAS ∝ vendas à demanda final), A2_ (v03; "
                "S38 por tecnologia: renováveis → EOL, fósseis → CAR e GN ∝ VBP da v03; E1 como no A1), A2_<c>_<sens> "
                "(sensibilidades do A2), B_ (R$ 1 bi por tecnologia), B_TWh_ (1 TWh ao R$/MWh da v03; nas variantes, "
                "ao R$/MWh de cada variante).\n# Gerado por scripts/rodada04_simulacoes.py.\n")
        todos.to_csv(f, index=False, float_format="%.17g")
    sel = lambda p: todos[todos["cenario"].str.startswith(p)]  # noqa: E731
    a0 = cen.executar(m0, sel("A0_"), "original")
    a1 = cen.executar(m03, sel("A1_"), "v03")
    a2_todos = cen.executar(m03, sel("A2_"), "v03")
    a2 = {k: (v[v["cenario"].isin([f"A2_{c}" for c in CEN_ARTIGO])] if "cenario" in v.columns else v)
          for k, v in a2_todos.items()}
    b = cen.executar(m03, sel("B_"), "v03")
    # robustez nas variantes (A2: R1, F1, E1; B por TWh ao R$/MWh de cada variante)
    por_versao = {"v03": {"impactos": pd.concat([a2_todos["impactos"], b["impactos"]], ignore_index=True)}}
    sens_imp = []
    for suf in VARIANTES:
        mv = ler_mip_longo(SAIDA / f"{NOME}_v03{suf}_longo.csv")
        cv = pd.concat([todos[todos["cenario"].isin(["A2_R1", "A2_F1", "A2_E1"])], b_twh(mv, G)], ignore_index=True)
        t = cen.executar(mv, cv, f"v03{suf}")
        por_versao[f"v03{suf}"] = t
        sens_imp.append(t)
    rob = robustez(por_versao)
    m_sol, info_sol = sol_com_tust_do_rs(m03, G)
    alt = tabela_twh(cen.executar(m_sol, b_twh(m03, G), VERSAO_SOL), VERSAO_SOL)
    alt = alt[alt["subsetor (RS)"] == "S38_SOL"].assign(**{k: v for k, v in info_sol.items()})
    tw = pd.concat([tabela_twh(b, "v03")] + [tabela_twh(t, f"v03{s}") for s, t in zip(VARIANTES, sens_imp)] + [alt],
                   ignore_index=True)
    b1 = indicadores(b, "B_")
    b1 = b1[~b1["cenario"].str.startswith("B_TWh_")].copy()
    b1.insert(2, "tecnologia", [NOME_TEC[f"S38_{c[2:]}"] for c in b1["cenario"]])
    b1["t CO₂e por R$ mi demandado"] = b1["CO₂e total (t)"] / 1000
    # comparação com o artigo (E1, R1, F1): A0 × A1 × A2
    comp = []
    for c in ("E1", "R1", "F1"):
        for bloco, t in (("A0 (artigo, MIP original)", a0), ("A1 (v03, S38 → DIS/GAS)", a1), ("A2 (v03, S38 por tecnologia)", a2)):
            x = indicadores(t)
            x = x[x["cenario"].str.endswith(f"_{c}")].iloc[0]
            comp.append({"cenario": c, "bloco": bloco, **{k: x[k] for k in list(ROTULOS.values())}})
    comp = pd.DataFrame(comp)
    art = tabelas_artigo(a2)
    abas = {"A0": indicadores(a0), "A1": indicadores(a1), "A2": indicadores(a2),
            "A2_sens": indicadores(a2_todos), "B_RS1bi": b1, "B_TWh": tw, "robustez": rob,
            "robustez_detalhe": pd.concat([indicadores(t) for t in sens_imp] + [indicadores({"impactos": por_versao["v03"]["impactos"], "participacao_setor": pd.concat([a2_todos["participacao_setor"], b["participacao_setor"]])})],
                                          ignore_index=True),
            "comparacao_artigo": comp, **art,
            "top10_A0": a0["top10"], "top10_A1": a1["top10"], "top10_A2": a2_todos["top10"], "top10_B": b["top10"],
            "participacao_S38": pd.concat([a0["participacao_setor"], a1["participacao_setor"],
                                           a2_todos["participacao_setor"], b["participacao_setor"]], ignore_index=True),
            "regioes": pd.concat([a0["regioes"], a1["regioes"], a2_todos["regioes"], b["regioes"]], ignore_index=True),
            "reparticao_S38": pd.concat([a1["reparticao"], a2_todos["reparticao"]], ignore_index=True),
            "cenarios": todos}
    salvar_tabelas(SAIDA / "simulacoes_v03.xlsx", abas, leiame=[
        "Rodada 04 — simulações do artigo na MIP v03 (choques de R$ 1000 mi na demanda final de setores do RS, salvo "
        "o bloco B por TWh).",
        "A0: MIP original (replicação; inclui R4a e R4b). A1: v03, S38 → DIS e GAS do RS ∝ vendas à demanda final. "
        "A2: v03, S38 por tecnologia (renováveis → 100% EOL-RS; fósseis → CAR-RS e GN-RS ∝ VBP de 2019 na v03; E1 "
        "como no A1). A2_sens: sensibilidades (50% EOL + 50% SOL; 2/3 EOL + 1/3 TRA; 100% CAR; 100% GN).",
        "B_RS1bi: R$ 1000 mi por tecnologia do RS. B_TWh: 1 TWh de cada tecnologia; na linha v03 ao R$/MWh da v03, "
        "nas linhas das variantes ao R$/MWh de cada variante (SOL-RS latente: R$/MWh do SOL-RB da mesma versão); "
        "'evitadas' = CO₂e do carvão − CO₂e da tecnologia, por TWh.",
        f"B_TWh, versão '{VERSAO_SOL}': HIPÓTESE ALTERNATIVA para o SOL-RS latente. Na v03 a coluna latente é o "
        "espelho do SOL-RB e paga a TUST por MWh do RB (cerca de 21 R$/MWh); nesta linha as linhas S38_TRA da coluna "
        "são multiplicadas para que pague a TUST por MWh das fontes do RS (cerca de 35 R$/MWh).",
        LIMITACAO,
        "robustez: A2 (R1, F1, E1) e B por TWh nas variantes _P2, _E2, _E3, _gas4dist, _rap_ons, _k060 e _eta005 "
        "(faixa mín–máx de CO₂e total, IC e % no RB); robustez_detalhe: os valores de cada variante.",
        "tabela1_artigo a tabela4_artigo: as tabelas do artigo refeitas com o A2. ORDEM E RÓTULOS INFERIDOS (o artigo "
        "não foi recebido): 1 = impactos totais; 2 = top-10 da cesta R1; 3 = RS × RB; 4 = diretas × indiretas.",
        "Emissões diretas = e · ΔY (setores chocados); indiretas = total − diretas (eq. 12–14 do modelo).",
        "Gerado por scripts/rodada04_simulacoes.py."])
    figs = figuras(a0, a2, tw)
    print(f"[simulações] {todos['cenario'].nunique()} cenários; {len(abas)} abas; figuras: {[p.name for p in figs]}")


if __name__ == "__main__":
    main()
