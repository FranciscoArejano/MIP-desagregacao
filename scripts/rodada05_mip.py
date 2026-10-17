"""Rodada 05 — MIP v04 (versão final: v03 + D17 + D18), variantes, quadro por subsetor e comparativo v03 × v04.

Uso (na raiz do repositório, depois de scripts/rodada05_parametros.py):
    python scripts/rodada05_mip.py

Saídas em resultados/rodada05/:
- MIP_RS_RB_2019_S38_11sub_v04.xlsx (+ _longo.csv + _coef_latentes.csv)   principal (versão final)
- MIP_RS_RB_2019_S38_11sub_v04_<variante>_longo.csv (+ _coef_latentes.csv)  _P2, _E2, _E3, _E4, _gas4dist, _rap_media,
                                                                             _k060, _eta005
- checagens_v04.csv                checagens de todas as versões
- quadro_subsetores_v04.xlsx       quadro por subsetor (E1, E2, E3 e E4), v03_x_v04, passos v03 → v04 (efeito de D17 e
                                   D18), D18 nas colunas latentes, realocação da E4, insumos não energéticos (T12), TUST
                                   da geração, pisos, reequilíbrio, variantes, gás por comprador e checagens
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import pandas as pd  # noqa: E402

from mip.caminhos import PASTA_PARAMETROS, PASTA_RESULTADOS  # noqa: E402
from mip.desagregacao import desagregar, insumos_nao_energeticos, ler_especificacao  # noqa: E402
from mip.exportacao import exportar_longo, salvar_tabelas  # noqa: E402
from mip.leitura import caminho_coef_latentes_ao_lado, ler_mip_original  # noqa: E402


def _modulo(nome, arquivo):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / "scripts" / arquivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


r04m = _modulo("r04m", "rodada04_mip.py")  # funções do quadro (Rodadas 03 e 04); não grava nada
r03m = r04m.r03m

SAIDA = PASTA_RESULTADOS / "rodada05"
NOME = "MIP_RS_RB_2019_S38_11sub"
VARIANTES = ["_P2", "_E2", "_E3", "_E4", "_gas4dist", "_rap_media", "_k060", "_eta005"]
ROTULO_EMISSOES = {"v04_E2": "E2", "v04_E3": "E3", "v04_E4": "E4"}
LATENTES = [("RS", "S38_SOL"), ("RS", "S38_PET")]


def espec(suf, versao="v04"):
    return ler_especificacao(PASTA_PARAMETROS / f"especificacao_{versao}{suf}.yaml")


def gerar(mip) -> dict:
    res = {}
    for suf in [""] + VARIANTES:
        nome = f"v04{suf}"
        r = desagregar(mip, espec(suf), estrito=False)
        res[nome] = r
        print(f"[{nome}] {r.mip.n} setores-região; checagens {r.checagens['status'].value_counts().to_dict()}")
        longo = SAIDA / f"{NOME}_{nome}_longo.csv"
        if suf == "":
            r.exportar(SAIDA / f"{NOME}_{nome}.xlsx", longo)  # grava também o _coef_latentes.csv
        else:
            exportar_longo(r.mip, longo)
            if r.mip.coef_latentes is not None and len(r.mip.coef_latentes):
                r.mip.coef_latentes.to_csv(caminho_coef_latentes_ao_lado(longo), index=False)
    return res


def efeito_d18(mip, r04, G) -> pd.DataFrame:
    """D18: τ_RS, p_k, coeficiente de TUST e multiplicadores das colunas latentes, sem e com a D18 (mesma v04)."""
    sem = desagregar(mip, replace(r04.especificacao, tust_latentes={}), estrito=False)
    q_sem = r03m.tabela_subsetores(sem, "v04 sem D18", G).set_index(["regiao", "subsetor"])
    q_com = r03m.tabela_subsetores(r04, "v04", G).set_index(["regiao", "subsetor"])
    t = r04.extras["tust_latentes"].set_index(["regiao", "subsetor"])
    linhas = []
    for k in LATENTES:
        d = {"regiao": k[0], "subsetor": k[1]} | t.loc[k].to_dict()
        for col in ("multiplicador de produção", "multiplicador de emissões (t/R$ mi)", "  das quais diretas"):
            d[f"{col.strip()} sem D18"] = q_sem.loc[k, col]
            d[f"{col.strip()} com D18"] = q_com.loc[k, col]
        linhas.append(d)
    return pd.DataFrame(linhas)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    mip = ler_mip_original()
    res = gerar(mip)
    chk = pd.concat([r.checagens.assign(versao=n) for n, r in res.items()], ignore_index=True)
    chk.to_csv(SAIDA / "checagens_v04.csv", index=False)
    G = r03m.gwh()
    q04 = r03m.tabela_subsetores(res["v04"], "v04", G, [(res["v04"], "E1"), (res["v04_E2"], "E2"),
                                                       (res["v04_E3"], "E3"), (res["v04_E4"], "E4")])
    q = pd.concat([q04, r03m.agregado_original(mip)], ignore_index=True)
    # v03 publicada (Rodada 04) e os passos v03 → v04
    v03 = desagregar(mip, espec("", "v03"), estrito=False)
    q03 = r03m.tabela_subsetores(v03, "v03", G)
    passos = {
        "v03": v03,
        "v03 + D17 (= v03_rap_ons)": desagregar(mip, espec("_rap_ons", "v03"), estrito=False),
        "v03 + D18 (= v04_rap_media)": res["v04_rap_media"],
        "v04 = v03 + D17 + D18": res["v04"],
    }
    tab_passos = pd.DataFrame({n: r04m.indicadores_passo(r, n, G) for n, r in passos.items()})
    for n, r in passos.items():
        ql = r03m.tabela_subsetores(r, n, G).set_index(["regiao", "subsetor"])
        for k in LATENTES:
            tab_passos.loc[f"multiplicador de produção {k[0]} {k[1]} (latente)", n] = ql.loc[k, "multiplicador de produção"]
            tab_passos.loc[f"multiplicador de emissões (t/R$ mi) {k[0]} {k[1]} (latente)", n] = \
                ql.loc[k, "multiplicador de emissões (t/R$ mi)"]
    tab_passos.index.name = "indicador"
    d18 = efeito_d18(mip, res["v04"], G)
    ne = pd.concat([insumos_nao_energeticos(r).assign(versao=n) for n, r in (("v03", v03), ("v04", res["v04"]))],
                   ignore_index=True)
    tust = pd.concat([r04m.tust_geracao(r, n) for n, r in (("v03", v03), ("v04", res["v04"]))], ignore_index=True)
    variantes = pd.concat([r03m.tabela_subsetores(res[n], n, G, [(res[n], ROTULO_EMISSOES.get(n, "E1"))])
                           for n in res if n != "v04"], ignore_index=True)
    resumo = []
    for n, r in res.items():
        eob = r.extras["reequilibrio_RAS"]
        nei = insumos_nao_energeticos(r)
        tl = r.extras["tust_latentes"].set_index("subsetor")
        resumo.append({"versao": n, "especificacao": r.especificacao.nome,
                       "checagens": str(r.checagens["status"].value_counts().to_dict()),
                       "extensão de viabilidade": "ligada" if r.especificacao.piso_vbp.get("viabilidade_eta") is not None
                       else "desligada",
                       "EOB/VBP mínimo": float(eob.loc[eob["VBP"] > 0, "EOB/VBP_depois"].min()),
                       "insumos não energéticos / VBP mínimo": float(nei["insumos_nao_energeticos / VBP"].min()),
                       "VBP GN-RB": float(r.mip.X[r.mip.indice("RB", "S38_GN")]),
                       "VBP PET-RB": float(r.mip.X[r.mip.indice("RB", "S38_PET")]),
                       "VBP GN-RS": float(r.mip.X[r.mip.indice("RS", "S38_GN")]),
                       "VBP GAS-RB": float(r.mip.X[r.mip.indice("RB", "S38_GAS")]),
                       "VBP TRA-RS": float(r.mip.X[r.mip.indice("RS", "S38_TRA")]),
                       "VBP TRA-RB": float(r.mip.X[r.mip.indice("RB", "S38_TRA")]),
                       "τ_RS (R$/MWh)": float(tl["tau (R$/MWh)"].iloc[0]),
                       "coeficiente de TUST SOL-RS": float(tl.loc["S38_SOL", "coeficiente de TUST depois"]),
                       "multiplicador de produção máximo": float(r03m.tabela_subsetores(r, n, G)["multiplicador de produção"].max())})
    gas = pd.concat([r03m.gas_realizado(res[n], n) for n in ("v04", "v04_gas4dist")], ignore_index=True)
    gas_grupos = (gas.groupby(["versao", "regiao", "grupo"])["gas (GAS)"].sum()
                  / gas.groupby(["versao", "regiao"])["gas (GAS)"].sum()).rename("participacao_nas_vendas_do_GAS").reset_index()
    salvar_tabelas(
        SAIDA / "quadro_subsetores_v04.xlsx",
        {"quadro": q, "v03_x_v04": r04m.comparar(q03, q04, "v03", "v04"), "passos_v03_v04": tab_passos.reset_index(),
         "d18_latentes": d18, "tust_latentes_versoes": pd.concat(
             [r.extras["tust_latentes"].assign(versao=n) for n, r in res.items()], ignore_index=True),
         "realocacao_E4": res["v04_E4"].extras["realocacao_emissoes"],
         "insumos_nao_energeticos": ne, "tust_geracao": tust,
         "pisos_vbp": res["v04"].extras["pisos_vbp"], "reequilibrio_RAS": res["v04"].extras["reequilibrio_RAS"],
         "reequilibrio_insumos": res["v04"].extras["reequilibrio_insumos"], "variantes_resumo": pd.DataFrame(resumo),
         "variantes_subsetores": variantes, "gas_por_comprador": gas, "gas_por_grupo": gas_grupos, "checagens": chk,
         "componentes_bloco": res["v04"].extras["componentes_bloco"],
         "niveis_emissoes": pd.concat([r.extras["niveis"].assign(versao=n) for n, r in res.items() if "niveis" in r.extras],
                                      ignore_index=True)},
        leiame=["Rodada 05 — quadro por subsetor da MIP v04, a versão final (P1 + E1 + D9 + V1 + V2 + D17 + D18; κ = 0.70, "
                "η = 0.10).",
                "D17: transmissão = encargos de uso faturados pelo ONS no ano civil de 2019 (22935.6 R$ mi). D18 "
                "(HIPÓTESE): as colunas latentes SOL-RS e PET-RS pagam a TUST por MWh das fontes do RS no SIN.",
                "Abas: v03_x_v04 (comparativo por subsetor), passos_v03_v04 (efeito de D17 e D18), d18_latentes (τ_RS, "
                "p_k, coeficiente de TUST e multiplicadores das latentes sem e com a D18), tust_latentes_versoes, "
                "realocacao_E4 (valores movidos na variante _E4), insumos_nao_energeticos (T12), tust_geracao, pisos_vbp, "
                "reequilibrio_RAS, reequilibrio_insumos, variantes_resumo e variantes_subsetores, gas_por_comprador e "
                "gas_por_grupo, checagens de todas as versões, niveis_emissoes.",
                "GWh (D8): Brasil pelo BEN 2020 (Tabela 5.4), RS pelo ONS, RB = Brasil − RS.",
                "Gerado por scripts/rodada05_mip.py."])
    print(f"[quadro v04] {len(q)} linhas; D18: {d18[['regiao', 'subsetor', 'tau (R$/MWh)', 'p (R$/MWh)', 'coeficiente de TUST antes', 'coeficiente de TUST depois']].round(4).to_dict('records')}; "
          f"alertas: {q.loc[q['alertas'].fillna('') != '', ['regiao', 'subsetor', 'alertas']].to_dict('records')}")


if __name__ == "__main__":
    main()
