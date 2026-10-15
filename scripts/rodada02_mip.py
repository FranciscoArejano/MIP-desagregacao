"""Rodada 02 / 02b — Etapas 5 e 6: MIP desagregada v01, variantes, quadro-diagnóstico e prévia.

Uso (na raiz do repositório, depois de scripts/rodada02_parametros.py):
    python scripts/rodada02_mip.py

Saídas em resultados/rodada02/:
- MIP_RS_RB_2019_S38_11sub_v01.xlsx (+ _longo.csv)          principal: P1 + E1
- MIP_RS_RB_2019_S38_11sub_v01_P2 / _v01_E2 / _v01_E3        sensibilidades (.xlsx e _longo.csv)
- checagens_v01.csv                                          checagens de todas as versões
- quadro_subsetores_v01.xlsx                                 Etapa 6a (obrigatória)
- previa_multiplicadores_v01.xlsx                            Etapa 6b — PRÉVIA, não é resultado do artigo
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from mip import referencia as ref  # noqa: E402
from mip.caminhos import PASTA_INTERMEDIARIOS, PASTA_PARAMETROS, PASTA_RESULTADOS  # noqa: E402
from mip.desagregacao import desagregar, ler_especificacao, tipo_canonico  # noqa: E402
from mip.estrutura import COLUNAS_DF, ITENS_PRIMARIOS, ITENS_SATELITE  # noqa: E402
from mip.exportacao import salvar_tabelas  # noqa: E402
from mip.leitura import ler_mip_original  # noqa: E402
from mip.modelo import ModeloLeontief  # noqa: E402

SAIDA = PASTA_RESULTADOS / "rodada02"
NOME = "MIP_RS_RB_2019_S38_11sub"
VARIANTES = {"v01": "", "v01_P2": "_P2", "v01_E2": "_E2", "v01_E3": "_E3"}
LIMITE_XLSX_MB = 50
# faixas de plausibilidade da emissão direta em E1 (t CO2e/MWh): Rodada 02, Seção 9a; CAR ajustado na 02b (Seção 2)
FAIXAS_E1 = {"S38_CAR": (0.8, 1.6), "S38_GN": (0.35, 0.65), "S38_PET": (0.65, 1.1), "S38_BIO": (0.0, 0.1),
             "S38_HID": (0.0, 0.0), "S38_EOL": (0.0, 0.0), "S38_SOL": (0.0, 0.0), "S38_NUC": (0.0, 0.0)}


def gerar_variantes(mip):
    res = {}
    for nome, suf in VARIANTES.items():
        espec = ler_especificacao(PASTA_PARAMETROS / f"especificacao_v01{suf}.yaml")
        r = desagregar(mip, espec, estrito=False)
        res[nome] = r
        st = r.checagens["status"].value_counts().to_dict()
        print(f"[{nome}] {r.mip.n} setores-região; checagens {st}")
        destino = SAIDA / f"{NOME}_{nome}.xlsx"
        r.exportar(destino, SAIDA / f"{NOME}_{nome}_longo.csv")
        if destino.stat().st_size > LIMITE_XLSX_MB * 1e6:
            destino.unlink()
            print(f"  .xlsx acima de {LIMITE_XLSX_MB} MB: mantido só o CSV longo")
    return res


def gwh_por_subsetor() -> dict:
    g = pd.read_csv(PASTA_INTERMEDIARIOS / "geracao_2019_regiao_subsetor_v02.csv")
    return {r: g[g["regiao"] == r].drop(columns=["regiao", "origem"]).sum(numeric_only=True).to_dict() for r in ("RS", "RB")}


def quadro(res: dict) -> pd.DataFrame:
    """Etapa 6a: uma linha por região × subsetor."""
    principal = res["v01"]
    m2 = principal.mip
    gwh = gwh_por_subsetor()
    ip = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}
    ks = {it: k for k, it in enumerate(ITENS_SATELITE)}
    sub = principal.mapa[principal.mapa["desagregado"]]
    tet = principal.extras.get("tetos_atingidos")
    linhas = []
    for row in sub.itertuples(index=False):
        j, r, c = row.indice_novo, row.regiao, row.codigo_novo
        x = m2.X[j]
        xs = m2.X[sub[sub["regiao"] == r]["indice_novo"].to_numpy()].sum()
        g = gwh[r].get(c, np.nan) if c in FAIXAS_E1 else np.nan
        mwh = g * 1000 if pd.notna(g) else np.nan
        d = {"regiao": r, "subsetor": c, "tipo": tipo_canonico(row.tipo_subsetor), "VBP (R$ mi)": x,
             "% do VBP do S38": 100 * x / xs, "GWh": g,
             "R$/MWh implícito": (x * 1e6 / mwh) if (pd.notna(mwh) and mwh > 0) else np.nan}
        for v in ("v01", "v01_E2", "v01_E3"):
            co2 = res[v].mip.S[ks["co2e"], j]
            rot = {"v01": "E1", "v01_E2": "E2", "v01_E3": "E3"}[v]
            d[f"CO2e {rot} (t)"] = co2
            d[f"t CO2e/MWh {rot}"] = co2 / mwh if (pd.notna(mwh) and mwh > 0) else np.nan
            d[f"t CO2e/R$ mi {rot}"] = co2 / x if x else np.nan
        d["ocupações"] = m2.S[ks["ocupacoes"], j]
        d["remunerações (R$ mi)"] = m2.V[ip["remuneracoes"], j]
        d["CI/VBP"] = m2.Z[:, j].sum() / x if x else np.nan
        d["EOB/VBP"] = m2.V[ip["eob"], j] / x if x else np.nan
        col = m2.Z[:, j]
        top = np.argsort(-col)[:5]
        d["5 maiores insumos (R$ mi)"] = "; ".join(f"{m2.setores['id'][k]} {col[k]:.1f}" for k in top if col[k] > 0)
        alertas = []
        if x == 0:
            alertas.append("produção zero" + (" (latente)" if m2.coef_latentes is not None and
                                              ((m2.coef_latentes["regiao"] == r) & (m2.coef_latentes["subsetor"] == c)).any() else ""))
        if x > 0 and m2.V[ip["eob"], j] < 0:
            alertas.append("EOB negativo")
        if c in FAIXAS_E1 and pd.notna(d["t CO2e/MWh E1"]):
            lo, hi = FAIXAS_E1[c]
            if not (lo - 1e-9 <= d["t CO2e/MWh E1"] <= hi + 1e-9):
                alertas.append(f"E1 fora da faixa [{lo}, {hi}] t/MWh")
        if tet is not None and len(tet[(tet["regiao"] == r) & (tet["subsetor"] == c)]):
            t = tet[(tet["regiao"] == r) & (tet["subsetor"] == c)]
            alertas.append("teto atingido: " + ", ".join(f"{a.insumo_ou_grupo} (excedente {a.excedente:.1f})" for a in t.itertuples()))
        d["alertas"] = "; ".join(alertas)
        linhas.append(d)
    q = pd.DataFrame(linhas)
    # comparação com o S38 agregado (original)
    mip = principal.original
    ag = []
    for r in ("RS", "RB"):
        j = mip.indice(r, "S38")
        ag.append({"regiao": r, "subsetor": "S38 (agregado, original)", "VBP (R$ mi)": mip.X[j],
                   "CO2e E1 (t)": mip.satelite("co2e")[j], "t CO2e/R$ mi E1": mip.satelite("co2e")[j] / mip.X[j],
                   "ocupações": mip.satelite("ocupacoes")[j], "CI/VBP": mip.Z[:, j].sum() / mip.X[j],
                   "EOB/VBP": mip.primario("eob")[j] / mip.X[j]})
    return pd.concat([q, pd.DataFrame(ag)], ignore_index=True)


def previa(res: dict) -> dict:
    """Etapa 6b (PRÉVIA): multiplicadores tipo I do RS e os 9 cenários na v01."""
    r1 = res["v01"]
    m2, m1 = r1.mip, r1.original
    mod2, mod1 = ModeloLeontief(m2), ModeloLeontief(m1)
    linhas = []
    for c in r1.especificacao.subsetores["codigo"]:
        j = m2.indice("RS", c)
        if m2.X[j] == 0 and not (m2.coef_latentes is not None and
                                 ((m2.coef_latentes["regiao"] == "RS") & (m2.coef_latentes["subsetor"] == c)).any()):
            continue  # zerado sem latente (Nuclear-RS)
        s = mod2.simular_choques({("RS", c): 1.0})
        linhas.append({"setor": f"RS {c}", "latente": m2.X[j] == 0, "multiplicador de produção": s.dX.sum(),
                       "multiplicador de emissões (t CO2e por R$ mi)": s.emissoes.sum(),
                       "das quais diretas": s.diretas})
    s = mod1.simular_choques({("RS", "S38"): 1.0})
    linhas.append({"setor": "RS S38 agregado (original)", "latente": False, "multiplicador de produção": s.dX.sum(),
                   "multiplicador de emissões (t CO2e por R$ mi)": s.emissoes.sum(), "das quais diretas": s.diretas})
    mult = pd.DataFrame(linhas)
    # 9 cenários: choque do S38 repartido entre DIS e GAS ∝ vendas do S38-RS à demanda final na v01
    fd = {c: m2.F[m2.indice("RS", c)].sum() for c in ("S38_DIS", "S38_GAS")}
    w = {c: v / sum(fd.values()) for c, v in fd.items()}
    cen = []
    for nome in ref.CENARIOS_RS:
        base = mod1.simular_choques(ref.choques(nome), nome).resumo()
        ch = ref.choques(nome)
        v = ch.pop(("RS", "S38"))
        ch.update({("RS", c): v * wc for c, wc in w.items()})
        nova = mod2.simular_choques(ch, nome).resumo()
        for ind in ("dX_total", "co2e_total", "co2e_RS", "co2e_RB", "IC", "pct_indiretas"):
            cen.append({"cenario": nome, "indicador": ind, "original": base[ind], "v01": nova[ind],
                        "diferenca": nova[ind] - base[ind], "dif_%": 100 * (nova[ind] - base[ind]) / base[ind] if base[ind] else np.nan})
    pesos = pd.DataFrame([{"subsetor": c, "vendas à DF (R$ mi)": fd[c], "peso no choque do S38": w[c]} for c in fd])
    return {"multiplicadores_RS": mult, "cenarios_v01": pd.DataFrame(cen), "reparticao_choque_S38": pesos}


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    mip = ler_mip_original()
    res = gerar_variantes(mip)
    chk = pd.concat([r.checagens.assign(versao=n) for n, r in res.items()], ignore_index=True)
    chk.to_csv(SAIDA / "checagens_v01.csv", index=False)
    q = quadro(res)
    salvar_tabelas(SAIDA / "quadro_subsetores_v01.xlsx",
                   {"quadro": q, "checagens": chk, "tetos_atingidos": res["v01"].extras.get("tetos_atingidos", pd.DataFrame()),
                    "componentes_bloco": res["v01"].extras["componentes_bloco"], "niveis_emissoes": pd.concat(
                        [r.extras["niveis"].assign(versao=n) for n, r in res.items() if "niveis" in r.extras], ignore_index=True)},
                   leiame=["Rodada 02/02b — Etapa 6a: quadro-diagnóstico dos 11 subsetores do S38, por região (versão principal v01 = P1 + E1).",
                           "CO2e em E1, E2 e E3; t/MWh e t/R$ mi; faixas de plausibilidade de E1 (t/MWh): CAR 0.8–1.6, GN 0.35–0.65, "
                           "PET 0.65–1.1, BIO ≤ 0.1, HID/EOL/SOL/NUC = 0 (fora da faixa → coluna alertas).",
                           "GWh: ONS (SIN, sem autoprodução) + EPE (sistemas isolados) — dados/intermediarios/geracao_2019_regiao_subsetor_v02.csv.",
                           "Gerado por scripts/rodada02_mip.py."])
    p = previa(res)
    salvar_tabelas(SAIDA / "previa_multiplicadores_v01.xlsx", p,
                   leiame=["PRÉVIA — NÃO É RESULTADO DO ARTIGO.",
                           "Multiplicadores tipo I (produção e emissões por R$ 1 milhão de demanda final) dos subsetores do RS na v01 "
                           "(inclui latentes), comparados com o S38 agregado da MIP original.",
                           "Os 9 cenários da Rodada 01 na v01: choque do S38 repartido entre DIS e GAS na proporção das vendas do S38-RS "
                           "à demanda final (mede só o efeito da desagregação, sem remapear as cestas para tecnologias).",
                           "PRÉVIA — NÃO É RESULTADO DO ARTIGO."])
    print(f"[quadro] {len(q)} linhas; alertas: {q.loc[q['alertas'].fillna('') != '', ['regiao', 'subsetor', 'alertas']].to_dict('records')}")


if __name__ == "__main__":
    main()
