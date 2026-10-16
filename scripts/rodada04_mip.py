"""Rodada 04 — MIP v03 (V1 + V2; variante V3), variantes, quadro por subsetor e comparativo v02 × v03.

Uso (na raiz do repositório, depois de scripts/rodada04_parametros.py):
    python scripts/rodada04_mip.py

Saídas em resultados/rodada04/:
- MIP_RS_RB_2019_S38_11sub_v03.xlsx (+ _longo.csv + _coef_latentes.csv)   principal
- MIP_RS_RB_2019_S38_11sub_v03_<variante>_longo.csv (+ _coef_latentes.csv)  _P2, _E2, _E3, _gas4dist, _rap_ons, _k060,
                                                                             _eta005
- checagens_v03.csv                checagens de todas as versões
- quadro_subsetores_v03.xlsx       quadro por subsetor, v02_x_v03, passos v02 → v03 (efeito de V1, V2 e V3), insumos
                                   não energéticos (T12), TUST da geração, pisos, reequilíbrio, variantes, gás por
                                   comprador e checagens
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from mip.caminhos import PASTA_PARAMETROS, PASTA_RESULTADOS  # noqa: E402
from mip.desagregacao import desagregar, insumos_nao_energeticos, ler_especificacao  # noqa: E402
from mip.estrutura import ITENS_PRIMARIOS  # noqa: E402
from mip.exportacao import exportar_longo, salvar_tabelas  # noqa: E402
from mip.leitura import caminho_coef_latentes_ao_lado, ler_mip_original  # noqa: E402

_spec = importlib.util.spec_from_file_location("r03m", RAIZ / "scripts" / "rodada03_mip.py")
r03m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r03m)  # funções do quadro por subsetor da Rodada 03 (não grava nada)

SAIDA = PASTA_RESULTADOS / "rodada04"
NOME = "MIP_RS_RB_2019_S38_11sub"
VARIANTES = ["_P2", "_E2", "_E3", "_gas4dist", "_rap_ons", "_k060", "_eta005"]
ROTULO_EMISSOES = {"v03_E2": "E2", "v03_E3": "E3"}
IP = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}
TERMICAS_V1 = [("RB", "S38_GN"), ("RB", "S38_PET"), ("RS", "S38_GN")]


def espec(suf, versao="v03"):
    return ler_especificacao(PASTA_PARAMETROS / f"especificacao_{versao}{suf}.yaml")


def gerar(mip) -> dict:
    res = {}
    for suf in [""] + VARIANTES:
        nome = f"v03{suf}"
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


def comparar(qa: pd.DataFrame, qb: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    cols = ["VBP (R$ mi)", "GWh", "R$/MWh implícito", "t CO2e/MWh E1", "t CO2e/R$ mi E1", "EOB/VBP", "CI/VBP",
            "multiplicador de produção", "multiplicador de emissões (t/R$ mi)"]
    x, y = qa.set_index(["regiao", "subsetor"])[cols], qb.set_index(["regiao", "subsetor"])[cols]
    out = pd.DataFrame(index=y.index)
    for c in cols:
        out[f"{c} {a}"], out[f"{c} {b}"], out[f"{c} Δ"] = x[c], y[c], y[c] - x[c]
    return out.reset_index()


def tust_geracao(r, nome) -> pd.DataFrame:
    """Compras de cada subsetor de geração à transmissão (TRA das duas regiões): a TUST da geração."""
    m2, mapa = r.mip, r.mapa
    tra = [m2.indice(q, "S38_TRA") for q in ("RS", "RB")]
    linhas = []
    for row in mapa[mapa["desagregado"]].itertuples(index=False):
        if r03m.tipo_canonico(row.tipo_subsetor) != "geracao":
            continue
        k = int(row.indice_novo)
        x = m2.X[k]
        v = float(m2.Z[tra, k].sum())
        linhas.append({"versao": nome, "regiao": row.regiao, "subsetor": row.codigo_novo, "VBP": x, "TUST": v,
                       "TUST / VBP": v / x if x else np.nan,
                       "remuneracoes / VBP": m2.V[IP["remuneracoes"], k] / x if x else np.nan})
    return pd.DataFrame(linhas)


def indicadores_passo(r, nome, G) -> dict:
    """Indicadores para a tabela de passos v02 → v03."""
    q = r03m.tabela_subsetores(r, nome, G).set_index(["regiao", "subsetor"])
    ne = insumos_nao_energeticos(r).set_index(["regiao", "subsetor"])
    tu = tust_geracao(r, nome).set_index(["regiao", "subsetor"])
    d = {}
    for reg, s in TERMICAS_V1 + [("RB", "S38_HID"), ("RB", "S38_GAS"), ("RB", "S38_DIS"), ("RS", "S38_GAS"),
                                 ("RS", "S38_CAR"), ("RB", "S38_CAR")]:
        k = (reg, s)
        d[f"VBP {reg} {s}"] = q.loc[k, "VBP (R$ mi)"]
        if pd.notna(q.loc[k, "R$/MWh implícito"]):
            d[f"R$/MWh {reg} {s}"] = q.loc[k, "R$/MWh implícito"]
        if k in tu.index:
            d[f"TUST / VBP {reg} {s}"] = tu.loc[k, "TUST / VBP"]
            d[f"remunerações / VBP {reg} {s}"] = tu.loc[k, "remuneracoes / VBP"]
        d[f"EOB/VBP {reg} {s}"] = q.loc[k, "EOB/VBP"]
        if k in ne.index:
            d[f"insumos não energéticos / VBP {reg} {s}"] = ne.loc[k, "insumos_nao_energeticos / VBP"]
    for s in ("S38_GN", "S38_PET", "S38_CAR", "S38_GAS", "S38_DIS", "S38_HID", "S38_EOL"):
        d[f"multiplicador de produção RS {s}"] = q.loc[("RS", s), "multiplicador de produção"]
        d[f"multiplicador de emissões (t/R$ mi) RS {s}"] = q.loc[("RS", s), "multiplicador de emissões (t/R$ mi)"]
    d["checagens (OK/ALERTA/FALHA)"] = "/".join(str((r.checagens["status"] == x).sum()) for x in ("OK", "ALERTA", "FALHA"))
    pv = r.especificacao.piso_vbp
    d["extensão de viabilidade"] = "ligada" if pv.get("viabilidade_eta") is not None else "desligada"
    return d


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    mip = ler_mip_original()
    res = gerar(mip)
    chk = pd.concat([r.checagens.assign(versao=n) for n, r in res.items()], ignore_index=True)
    chk.to_csv(SAIDA / "checagens_v03.csv", index=False)
    G = r03m.gwh()
    q03 = r03m.tabela_subsetores(res["v03"], "v03", G, [(res["v03"], "E1"), (res["v03_E2"], "E2"), (res["v03_E3"], "E3")])
    q = pd.concat([q03, r03m.agregado_original(mip)], ignore_index=True)
    # v02 publicada (Rodada 03) e os passos v02 → v03
    v02 = desagregar(mip, espec("", "v02"), estrito=False)
    q02 = r03m.tabela_subsetores(v02, "v02", G)
    passos = {
        "v02": v02,
        "v02 + V2 (= v02_gas_sulgas)": desagregar(mip, espec("_gas_sulgas", "v02"), estrito=False),
        "v02 + V1 (= v03_gas4dist)": res["v03_gas4dist"],
        "v03 = v02 + V1 + V2": res["v03"],
        "v03 + V3 (= v03_rap_ons)": res["v03_rap_ons"],
    }
    tab_passos = pd.DataFrame({n: indicadores_passo(r, n, G) for n, r in passos.items()})
    tab_passos.index.name = "indicador"
    ne = pd.concat([insumos_nao_energeticos(r).assign(versao=n) for n, r in (("v02", v02), ("v03", res["v03"]))],
                   ignore_index=True)
    tust = pd.concat([tust_geracao(r, n) for n, r in (("v02", v02), ("v03", res["v03"]))], ignore_index=True)
    variantes = pd.concat([r03m.tabela_subsetores(res[n], n, G, [(res[n], ROTULO_EMISSOES.get(n, "E1"))])
                           for n in res if n != "v03"], ignore_index=True)
    resumo = []
    for n, r in res.items():
        eob = r.extras["reequilibrio_RAS"]
        nei = insumos_nao_energeticos(r)
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
                       "multiplicador de produção máximo": float(r03m.tabela_subsetores(r, n, G)["multiplicador de produção"].max())})
    gas = pd.concat([r03m.gas_realizado(res[n], n) for n in ("v03", "v03_gas4dist")], ignore_index=True)
    gas_grupos = (gas.groupby(["versao", "regiao", "grupo"])["gas (GAS)"].sum()
                  / gas.groupby(["versao", "regiao"])["gas (GAS)"].sum()).rename("participacao_nas_vendas_do_GAS").reset_index()
    salvar_tabelas(
        SAIDA / "quadro_subsetores_v03.xlsx",
        {"quadro": q, "v02_x_v03": comparar(q02, q03, "v02", "v03"), "passos_v02_v03": tab_passos.reset_index(),
         "insumos_nao_energeticos": ne, "tust_geracao": tust,
         "pisos_vbp": res["v03"].extras["pisos_vbp"], "reequilibrio_RAS": res["v03"].extras["reequilibrio_RAS"],
         "reequilibrio_insumos": res["v03"].extras["reequilibrio_insumos"], "variantes_resumo": pd.DataFrame(resumo),
         "variantes_subsetores": variantes, "gas_por_comprador": gas, "gas_por_grupo": gas_grupos, "checagens": chk,
         "componentes_bloco": res["v03"].extras["componentes_bloco"],
         "niveis_emissoes": pd.concat([r.extras["niveis"].assign(versao=n) for n, r in res.items() if "niveis" in r.extras],
                                      ignore_index=True)},
        leiame=["Rodada 04 — quadro por subsetor da MIP v03 (principal: P1 + E1 + D9 + V1 + V2; κ = 0.70, η = 0.10).",
                "V1: TUST da geração na proporção do MWh gerado no SIN; remunerações e ocupações da geração na proporção "
                "de (VBP − combustível). V2: VBP do GAS-RB pelo preço da Sulgás. V3 só na variante _rap_ons.",
                "Abas: v02_x_v03 (comparativo por subsetor), passos_v02_v03 (efeito de V1, V2 e V3), "
                "insumos_nao_energeticos (T12: compras fora do bloco, exceto combustíveis, ÷ VBP; v02 e v03), "
                "tust_geracao (TUST e remunerações ÷ VBP da geração; v02 e v03), pisos_vbp, reequilibrio_RAS, "
                "reequilibrio_insumos, variantes_resumo e variantes_subsetores, gas_por_comprador e gas_por_grupo "
                "(v03 e _gas4dist), checagens de todas as versões.",
                "GWh (D8): Brasil pelo BEN 2020 (Tabela 5.4), RS pelo ONS, RB = Brasil − RS.",
                "Gerado por scripts/rodada04_mip.py."])
    print(f"[quadro v03] {len(q)} linhas; alertas: "
          f"{q.loc[q['alertas'].fillna('') != '', ['regiao', 'subsetor', 'alertas']].to_dict('records')}")


if __name__ == "__main__":
    main()
