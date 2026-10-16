"""Rodada 03 — MIP v02 (D8 + D9 + D10), variantes, quadro por subsetor e prévia.

Uso (na raiz do repositório, depois de scripts/rodada03.py e scripts/rodada03_parametros.py):
    python scripts/rodada03_mip.py

Saídas em resultados/rodada03/:
- MIP_RS_RB_2019_S38_11sub_v02.xlsx (+ _longo.csv)       principal: P1 + E1 + D9 (κ = 0.70, η = 0.10)
- MIP_RS_RB_2019_S38_11sub_v02_P2 / _E2 / _E3             sensibilidades (.xlsx e _longo.csv)
- MIP_RS_RB_2019_S38_11sub_v02_k060 / _k080 / _eta005 / _sem_viabilidade   só _longo.csv (+ _coef_latentes.csv)
- checagens_v02.csv                                      checagens de todas as versões
- quadro_subsetores_v02.xlsx                             quadro por subsetor + abas v01_x_v02, reequilibrio_RAS,
                                                         pisos_atingidos e variantes
- previa_multiplicadores_v02.xlsx                        PRÉVIA — NÃO É RESULTADO DO ARTIGO
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from mip import cenarios as cen  # noqa: E402
from mip.caminhos import PASTA_INTERMEDIARIOS, PASTA_PARAMETROS, PASTA_RESULTADOS  # noqa: E402
from mip.desagregacao import desagregar, ler_especificacao, tipo_canonico  # noqa: E402
from mip.estrutura import ITENS_PRIMARIOS, ITENS_SATELITE  # noqa: E402
from mip.exportacao import exportar_longo, salvar_tabelas  # noqa: E402
from mip.leitura import ler_mip, ler_mip_original  # noqa: E402
from mip.modelo import ModeloLeontief  # noqa: E402

SAIDA = PASTA_RESULTADOS / "rodada03"
NOME = "MIP_RS_RB_2019_S38_11sub"
V01_XLSX = PASTA_RESULTADOS / "rodada02" / f"{NOME}_v01.xlsx"
COMPLETAS = {"v02": "", "v02_P2": "_P2", "v02_E2": "_E2", "v02_E3": "_E3"}  # .xlsx + CSV longo
SO_LONGO = {"v02_k060": "_k060", "v02_k080": "_k080", "v02_eta005": "_eta005", "v02_sem_viabilidade": "_sem_viabilidade"}
LIMITE_XLSX_MB = 50
# faixas de plausibilidade E1 (t CO2e/MWh) — Seção 4 da Rodada 03
FAIXAS_E1 = {"S38_CAR": (0.8, 1.6), "S38_GN": (0.35, 0.65), "S38_PET": (0.65, 1.1), "S38_BIO": (0.0, 0.1),
             "S38_HID": (0.0, 0.0), "S38_EOL": (0.0, 0.0), "S38_SOL": (0.0, 0.0), "S38_NUC": (0.0, 0.0)}
ALERTA_MULT = 2.2
ip = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}
ks = {it: k for k, it in enumerate(ITENS_SATELITE)}


def gerar(mip):
    res = {}
    for nome, suf in (COMPLETAS | SO_LONGO).items():
        r = desagregar(mip, ler_especificacao(PASTA_PARAMETROS / f"especificacao_v02{suf}.yaml"), estrito=False)
        res[nome] = r
        print(f"[{nome}] {r.mip.n} setores-região; checagens {r.checagens['status'].value_counts().to_dict()}")
        if nome in COMPLETAS:
            destino = SAIDA / f"{NOME}_{nome}.xlsx"
            r.exportar(destino, SAIDA / f"{NOME}_{nome}_longo.csv")
            if destino.stat().st_size > LIMITE_XLSX_MB * 1e6:
                destino.unlink()
                print(f"  .xlsx acima de {LIMITE_XLSX_MB} MB: mantido só o CSV longo")
        else:
            exportar_longo(r.mip, SAIDA / f"{NOME}_{nome}_longo.csv")
            if r.mip.coef_latentes is not None:
                r.mip.coef_latentes.to_csv(SAIDA / f"{NOME}_{nome}_coef_latentes.csv", index=False)
    return res


def gwh() -> dict:
    g = pd.read_csv(PASTA_INTERMEDIARIOS / "geracao_2019_regiao_subsetor_v03.csv").set_index("regiao")
    return {r: g.loc[r].drop(["origem", "Total"]).astype(float).to_dict() for r in ("RS", "RB")}


def multiplicadores(m) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(produção, emissões totais, emissões diretas) por R$ 1 mi de demanda final em cada coluna."""
    mod = ModeloLeontief(m)
    return mod.L.sum(axis=0), mod.e @ mod.L, mod.e


def tabela_subsetores(r, nome, G, res_em=None) -> pd.DataFrame:
    """Uma linha por região × subsetor: VBP, GWh, R$/MWh, CO2e, fatores, EOB, multiplicadores e alertas."""
    m2 = r.mip
    mp, me, md = multiplicadores(m2)
    sub = r.mapa[r.mapa["desagregado"]]
    linhas = []
    for row in sub.itertuples(index=False):
        j, reg, c = row.indice_novo, row.regiao, row.codigo_novo
        x = m2.X[j]
        xs = m2.X[sub[sub["regiao"] == reg]["indice_novo"].to_numpy()].sum()
        g = G[reg].get(c, np.nan) if c in FAIXAS_E1 else np.nan
        mwh = g * 1000 if pd.notna(g) else np.nan
        lat = m2.coef_latentes is not None and ((m2.coef_latentes["regiao"] == reg) & (m2.coef_latentes["subsetor"] == c)).any()
        d = {"versao": nome, "regiao": reg, "subsetor": c, "tipo": tipo_canonico(row.tipo_subsetor), "VBP (R$ mi)": x,
             "% do VBP do S38": 100 * x / xs, "GWh": g,
             "R$/MWh implícito": (x * 1e6 / mwh) if (pd.notna(mwh) and mwh > 0) else np.nan}
        for v, rot in (res_em or [(r, "E1")]):
            mm = v.mip
            co2 = mm.S[ks["co2e"], j]
            d[f"CO2e {rot} (t)"] = co2
            d[f"t CO2e/MWh {rot}"] = co2 / mwh if (pd.notna(mwh) and mwh > 0) else np.nan
            d[f"t CO2e/R$ mi {rot}"] = co2 / x if x else np.nan
        d["ocupações"] = m2.S[ks["ocupacoes"], j]
        d["remunerações (R$ mi)"] = m2.V[ip["remuneracoes"], j]
        d["CI/VBP"] = m2.Z[:, j].sum() / x if x else np.nan
        d["EOB/VBP"] = m2.V[ip["eob"], j] / x if x else np.nan
        d["multiplicador de produção"] = mp[j] if (x > 0 or lat) else np.nan
        d["multiplicador de emissões (t/R$ mi)"] = me[j] if (x > 0 or lat) else np.nan
        d["  das quais diretas"] = md[j] if (x > 0 or lat) else np.nan
        col = m2.Z[:, j]
        top = np.argsort(-col)[:5]
        d["5 maiores insumos (R$ mi)"] = "; ".join(f"{m2.setores['id'][k]} {col[k]:.1f}" for k in top if col[k] > 0)
        alertas = []
        if x == 0:
            alertas.append("produção zero" + (" (latente)" if lat else ""))
        if x > 0 and m2.V[ip["eob"], j] < 0:
            alertas.append("EOB negativo")
        rot1 = "E1"
        if c in FAIXAS_E1 and pd.notna(d.get(f"t CO2e/MWh {rot1}")):
            lo, hi = FAIXAS_E1[c]
            if not (lo - 1e-9 <= d[f"t CO2e/MWh {rot1}"] <= hi + 1e-9):
                alertas.append(f"E1 fora da faixa [{lo}, {hi}] t/MWh")
        if pd.notna(d["multiplicador de produção"]) and d["multiplicador de produção"] > ALERTA_MULT:
            alertas.append(f"multiplicador de produção {d['multiplicador de produção']:.3f} > {ALERTA_MULT}")
        pis = r.extras.get("pisos_vbp")
        if pis is not None:
            p = pis[(pis["regiao"] == reg) & (pis["subsetor"] == c) & pis["piso_atingido"]]
            if len(p):
                alertas.append(f"piso de VBP atingido ({p['piso_que_manda'].iloc[0]})")
        d["alertas"] = "; ".join(alertas)
        linhas.append(d)
    return pd.DataFrame(linhas)


def agregado_original(mip) -> pd.DataFrame:
    mp, me, md = multiplicadores(mip)
    ag = []
    for r in ("RS", "RB"):
        j = mip.indice(r, "S38")
        ag.append({"versao": "original", "regiao": r, "subsetor": "S38 (agregado, original)", "VBP (R$ mi)": mip.X[j],
                   "CO2e E1 (t)": mip.satelite("co2e")[j], "t CO2e/R$ mi E1": mip.satelite("co2e")[j] / mip.X[j],
                   "ocupações": mip.satelite("ocupacoes")[j], "CI/VBP": mip.Z[:, j].sum() / mip.X[j],
                   "EOB/VBP": mip.primario("eob")[j] / mip.X[j], "multiplicador de produção": mp[j],
                   "multiplicador de emissões (t/R$ mi)": me[j], "  das quais diretas": md[j]})
    return pd.DataFrame(ag)


def v01_x_v02(q01: pd.DataFrame, q02: pd.DataFrame) -> pd.DataFrame:
    cols = ["VBP (R$ mi)", "GWh", "R$/MWh implícito", "t CO2e/MWh E1", "t CO2e/R$ mi E1", "EOB/VBP",
            "multiplicador de produção", "multiplicador de emissões (t/R$ mi)"]
    a = q01.set_index(["regiao", "subsetor"])[cols]
    b = q02.set_index(["regiao", "subsetor"])[cols]
    out = pd.DataFrame(index=b.index)
    for c in cols:
        out[f"{c} v01"] = a[c]
        out[f"{c} v02"] = b[c]
        out[f"{c} Δ"] = b[c] - a[c]
    return out.reset_index()


def previa(res, mip_orig, mip_v01) -> dict:
    """PRÉVIA: multiplicadores do RS e os 9 cenários (choque do S38 repartido entre DIS e GAS) na v01 e na v02."""
    m2 = res["v02"].mip
    mods = {"v02": ModeloLeontief(m2), "v01": ModeloLeontief(mip_v01), "original": ModeloLeontief(mip_orig)}
    linhas = []
    for c in res["v02"].especificacao.subsetores["codigo"]:
        lat = m2.coef_latentes is not None and ((m2.coef_latentes["regiao"] == "RS") & (m2.coef_latentes["subsetor"] == c)).any()
        if m2.X[m2.indice("RS", c)] == 0 and not lat:
            continue  # Nuclear-RS: zerado, sem latente
        d = {"setor": f"RS {c}", "latente": bool(lat)}
        for v in ("v02", "v01"):
            mod = mods[v]
            s = mod.simular_choques({("RS", c): 1.0})
            d[f"multiplicador de produção {v}"] = s.dX.sum()
            d[f"emissões totais (t/R$ mi) {v}"] = s.emissoes.sum()
            d[f"  diretas {v}"] = s.diretas
            d[f"  indiretas {v}"] = s.emissoes.sum() - s.diretas
        linhas.append(d)
    s = mods["original"].simular_choques({("RS", "S38"): 1.0})
    linhas.append({"setor": "RS S38 agregado (original)", "latente": False,
                   **{f"multiplicador de produção {v}": s.dX.sum() for v in ("v02", "v01")},
                   **{f"emissões totais (t/R$ mi) {v}": s.emissoes.sum() for v in ("v02", "v01")},
                   **{f"  diretas {v}": s.diretas for v in ("v02", "v01")},
                   **{f"  indiretas {v}": s.emissoes.sum() - s.diretas for v in ("v02", "v01")}})
    tab = cen.executar_versoes({"original": mip_orig, "v01": mip_v01, "v02": m2}, cen.cenarios_da_rodada01())
    sens = tab["sensibilidade"]
    comp = sens[sens["indicador"].isin(["dX_total", "co2e_total", "co2e_RS", "co2e_RB", "IC", "pct_indiretas"])]
    return {"multiplicadores_RS": pd.DataFrame(linhas), "cenarios": comp, "reparticao_choque_S38": tab["reparticao"],
            "top10": tab["top10"]}


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    mip = ler_mip_original()
    res = gerar(mip)
    chk = pd.concat([r.checagens.assign(versao=n) for n, r in res.items()], ignore_index=True)
    chk.to_csv(SAIDA / "checagens_v02.csv", index=False)
    G = gwh()
    q02 = tabela_subsetores(res["v02"], "v02", G, [(res["v02"], "E1"), (res["v02_E2"], "E2"), (res["v02_E3"], "E3")])
    q = pd.concat([q02, agregado_original(mip)], ignore_index=True)
    # v01 (Rodada 02b), para o comparativo; GWh da v01 = ONS + isolados (02b)
    mip_v01 = ler_mip(V01_XLSX)
    g01 = pd.read_csv(PASTA_INTERMEDIARIOS / "geracao_2019_regiao_subsetor_v02.csv")
    G01 = {r: g01[g01["regiao"] == r].drop(columns=["regiao", "origem"]).sum(numeric_only=True).to_dict() for r in ("RS", "RB")}
    r01 = desagregar(mip, ler_especificacao(RAIZ / "parametros" / "especificacao_v01.yaml"), estrito=False)
    q01 = tabela_subsetores(r01, "v01", G01)
    comp = v01_x_v02(q01, q02)
    variantes = pd.concat([tabela_subsetores(res[n], n, G) for n in res if n != "v02"], ignore_index=True)
    resumo_var = []
    for n, r in res.items():
        c = r.checagens
        eob = r.extras["reequilibrio_RAS"]
        resumo_var.append({"versao": n, "especificacao": r.especificacao.nome,
                           "checagens": str(c["status"].value_counts().to_dict()),
                           "EOB/VBP mínimo (subsetores com produção)": float(eob.loc[eob["VBP"] > 0, "EOB/VBP_depois"].min()),
                           "VBP GN-RB": float(r.mip.X[r.mip.indice("RB", "S38_GN")]),
                           "VBP PET-RB": float(r.mip.X[r.mip.indice("RB", "S38_PET")]),
                           "VBP GN-RS": float(r.mip.X[r.mip.indice("RS", "S38_GN")]),
                           "multiplicador de produção máximo": float(
                               variantes.loc[variantes["versao"] == n, "multiplicador de produção"].max()
                               if n != "v02" else q02["multiplicador de produção"].max())})
    salvar_tabelas(
        SAIDA / "quadro_subsetores_v02.xlsx",
        {"quadro": q, "v01_x_v02": comp, "reequilibrio_RAS": res["v02"].extras["reequilibrio_RAS"],
         "reequilibrio_insumos": res["v02"].extras["reequilibrio_insumos"],
         "pisos_atingidos": res["v02"].extras["pisos_vbp"], "variantes_resumo": pd.DataFrame(resumo_var),
         "variantes_subsetores": variantes, "checagens": chk,
         "componentes_bloco": res["v02"].extras["componentes_bloco"],
         "niveis_emissoes": pd.concat([r.extras["niveis"].assign(versao=n) for n, r in res.items() if "niveis" in r.extras],
                                      ignore_index=True)},
        leiame=["Rodada 03 — quadro por subsetor da MIP v02 (principal: P1 + E1 + D9 com κ = 0.70 e η = 0.10).",
                "GWh (D8): Brasil pelo BEN 2020 (Tabela 5.4, serviço público), RS pelo ONS, RB = Brasil − RS "
                "(dados/intermediarios/geracao_2019_regiao_subsetor_v03.csv).",
                "Faixas de E1 (t CO2e/MWh): CAR 0.8–1.6, GN 0.35–0.65, PET 0.65–1.1, BIO ≤ 0.1, demais 0; alerta para "
                f"multiplicador de produção > {ALERTA_MULT}.",
                "Abas: v01_x_v02 (comparativo por subsetor), reequilibrio_RAS (EOB antes e depois; D9-r), reequilibrio_insumos "
                "(valor movido por insumo), pisos_atingidos (D9-f), variantes_resumo e variantes_subsetores (P2, E2, E3, "
                "κ = 0.60 e 0.80, η = 0.05, sem extensão de viabilidade), checagens de todas as versões.",
                "Gerado por scripts/rodada03_mip.py."])
    p = previa(res, mip, mip_v01)
    salvar_tabelas(SAIDA / "previa_multiplicadores_v02.xlsx", p,
                   leiame=["PRÉVIA — NÃO É RESULTADO DO ARTIGO.",
                           "Multiplicadores tipo I do RS (produção e emissões, diretas e indiretas, inclui latentes) na v02 e na v01, "
                           "e o S38 agregado da MIP original.",
                           "Os 9 cenários da Rodada 01 (executor de cenários): choque do S38 repartido entre DIS e GAS na proporção "
                           "das vendas de cada um à demanda final, na v01 e na v02; diferença para a original.",
                           "PRÉVIA — NÃO É RESULTADO DO ARTIGO."])
    print(f"[quadro] {len(q)} linhas; alertas: "
          f"{q.loc[q['alertas'].fillna('') != '', ['regiao', 'subsetor', 'alertas']].to_dict('records')}")


if __name__ == "__main__":
    main()
