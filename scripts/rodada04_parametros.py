"""Rodada 04 — parâmetros da MIP v03 (V1, V2, V3) a partir dos parâmetros v02 (Rodada 03).

Uso (na raiz do repositório, depois de scripts/rodada03_parametros.py):
    python scripts/rodada04_parametros.py

Mudanças em relação à v02 (instruções da Rodada 04, Seção 2):
- V1: a TUST paga pela geração de cada região compradora é repartida entre as fontes na proporção do MWh gerado no
  SIN (= mínimo entre o GWh da D8 e o GWh do ONS, sem autoprodução; isolados, latentes e zerados não pagam), e não
  mais pelo VBP (`pesos_tust_geracao_v03.csv`). Remunerações e ocupações da geração (CEMPRE) passam a ser repartidas
  entre as fontes na proporção de (VBP − combustível) (regra `fixa_por_tipo_sem_combustivel`). Piso κ = 0.70 e
  reequilíbrio η = 0.10; a extensão de viabilidade do piso só fica ligada se o T9 não passar sem ela.
- V2: VBP do GAS-RB pelo preço da Sulgás (19421.0; a regra da variante _gas_sulgas da v02); as 4 distribuidoras
  (26990.1) viram a variante _gas4dist.
- V3: RAP 2019 = 24883.4 na principal (o texto da REH 2.565/2019 enviado na Rodada 04 não traz o total; ver
  valores_documentais_v03.csv); variante _rap_ons com a transmissão = encargos de uso faturados pelo ONS no ano civil
  de 2019 (22935.6 R$ mi, SEAMSE).

Saídas em parametros/ (todas com coluna `fonte`): especificacao_v03.yaml e as variantes _P2, _E2, _E3, _gas4dist,
_rap_ons, _k060 e _eta005; subsetores_v03.csv, participacoes_vbp_v03.csv (e _P2), componentes_v03.csv (e _gas4dist,
_rap_ons), regras_coluna_v03.csv, regras_linha_v03.csv (e _gas4dist), regras_primarios_v03.csv (e _gas4dist,
_rap_ons), latentes_espelho_v03.csv, pesos_tust_geracao_v03.csv; quadro_parametros_v03.xlsx.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from mip.caminhos import PASTA_EXTERNOS, PASTA_INTERMEDIARIOS, PASTA_PARAMETROS  # noqa: E402
from mip.desagregacao import EspecificacaoInvalida, desagregar, ler_especificacao  # noqa: E402
from mip.exportacao import salvar_tabelas  # noqa: E402
from mip.leitura import ler_mip_original  # noqa: E402

_spec = importlib.util.spec_from_file_location("r03p", RAIZ / "scripts" / "rodada03_parametros.py")
r03 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r03)  # constantes da Rodada 03 (κ, η, combustíveis, fontes); não grava nada

PAR = PASTA_PARAMETROS
INT = PASTA_INTERMEDIARIOS
DOCS = PASTA_EXTERNOS / "valores_documentais_v03.csv"
V = "v03"
REGIOES = r03.REGIOES
GERACAO = r03.GERACAO
KAPPA, ETA = r03.KAPPA, r03.ETA
ALERTA_INSUMOS = 0.05  # T12 (Seção 2.4 das instruções da Rodada 04)
# Seção 2.1 das instruções: MWh no SIN do RB (GWh), para conferência
REFERENCIA_SIN_RB = {"S38_HID": 363907.4, "S38_EOL": 48122.9, "S38_SOL": 4384.6, "S38_BIO": 1771.8,
                     "S38_CAR": 11197.8, "S38_GN": 46474.0, "S38_PET": 1974.3, "S38_NUC": 16128.8}
FONTE_SIN = ("V1 (Rodada 04): MWh no SIN = mínimo entre o GWh da D8 (geracao_2019_regiao_subsetor_v03.csv) e o GWh do "
             "ONS 2019 por rótulo, sem autoprodução e sem Itaipu (geracao_2019_usina_v02.csv); sistemas isolados, "
             "latentes e zerados não pagam TUST")

quadro = []


def anotar(grupo, regiao, item, valor, unidade, fonte, calculo=""):
    quadro.append({"grupo": grupo, "regiao": regiao, "item": item, "valor": valor, "unidade": unidade,
                   "fonte": fonte, "calculo": calculo})
    return valor


def ler(nome: str) -> pd.DataFrame:
    return pd.read_csv(PAR / nome, dtype=str, keep_default_na=False)


def gravar(df: pd.DataFrame, nome: str) -> str:
    df.to_csv(PAR / nome, index=False)
    return nome


def geracao_sin() -> pd.DataFrame:
    d8 = pd.read_csv(INT / "geracao_2019_regiao_subsetor_v03.csv").set_index("regiao")
    us = pd.read_csv(INT / "geracao_2019_usina_v02.csv")
    ons = us[us["regiao"].isin(REGIOES)].groupby(["regiao", "subsetor"])["gwh"].sum()
    linhas = []
    for r in REGIOES:
        for c in GERACAO:
            g8 = float(d8.loc[r, c])
            go = float(ons.get((r, c), 0.0))
            latente = r == "RS" and c in r03.LATENTES_RS + ["S38_NUC"]
            sin = 0.0 if latente else min(g8, go)
            linhas.append({"regiao": r, "subsetor": c, "gwh_d8": g8, "gwh_ons": go, "gwh_sin": sin})
    t = pd.DataFrame(linhas)
    for c, ref in REFERENCIA_SIN_RB.items():
        obt = float(t.loc[(t["regiao"] == "RB") & (t["subsetor"] == c), "gwh_sin"].iloc[0])
        if abs(obt - ref) > 0.5:
            raise SystemExit(f"MWh no SIN do RB {c}: {obt:.1f} ≠ referência {ref} (Seção 2.1 da Rodada 04)")
    return t


def primarios(base: pd.DataFrame, T: dict, vbp_gas: dict, X: dict, F: dict, share_X: dict) -> pd.DataFrame:
    """Regras de primários da v03 a partir das da v02: remunerações e ocupações da geração ∝ (VBP − combustível) (V1)
    e SF6 entre TRA e DIS refeito com o VBP da transmissão e do GAS da variante."""
    p = base.copy()
    rem = p["item"].isin(["remuneracoes", "ocupacoes"])
    p.loc[rem, "regra"] = "fixa_por_tipo_sem_combustivel"
    p.loc[rem & (p["subsetor"] == "geracao"), "fonte"] = p.loc[rem & (p["subsetor"] == "geracao"), "fonte"].str.replace(
        "repartida entre as fontes na proporção do VBP final",
        "repartida entre as fontes na proporção de (VBP − combustível) (V1, Rodada 04: o combustível é repasse e não "
        "exige mão de obra proporcional)", regex=False)
    em = pd.read_csv(INT / "seeg_2019_emissoes_v01.csv")
    sf6 = float(em.loc[em["tabela"] == "sf6_nacional_mil_t", "valor"].iloc[0]) * 1000
    sf6_lin = (p["item"] == "co2e") & p["subsetor"].isin(["S38_TRA", "S38_DIS"])
    p = p[~sf6_lin].copy()
    novas = []
    for r in REGIOES:
        vbp_dis = X[r] - F[r] - vbp_gas[r]  # = X − E − T − GAS, com E = F − T (G = 0)
        sf6_r = sf6 * share_X[r]
        for sub, v in (("S38_TRA", sf6_r * T[r] / (T[r] + vbp_dis)), ("S38_DIS", sf6_r * vbp_dis / (T[r] + vbp_dis))):
            novas.append({"regiao": r, "item": "co2e", "regra": "niveis", "subsetor": sub, "valor": repr(float(v)),
                          "fonte": f"SF6 nacional ({r03.FONTE_SEEG}) × participação de {r} no VBP do S38 "
                                   f"({share_X[r]:.4f}) × participação do {sub} no VBP de TRA + DIS"})
    return pd.concat([p, pd.DataFrame(novas)], ignore_index=True)


def main():
    mip = ler_mip_original()
    X = {r: float(mip.X[mip.indice(r, "S38")]) for r in REGIOES}
    F = {r: float(sum(mip.Z[mip.indice(r, "S38"), mip.indice(q, "S38")] for q in REGIOES)) for r in REGIOES}
    share_X = {r: X[r] / sum(X.values()) for r in REGIOES}
    r03.DOCS = DOCS
    D = r03.docs()

    # ---- V3: RAP ------------------------------------------------------------------------------------
    rap_1819, f1819 = r03.exigir(D, "rap_total_ciclo_2018_2019")
    rap_1920, f1920 = r03.exigir(D, "rap_total_ciclo_2019_2020")
    rap = (rap_1819 + rap_1920) / 2
    anotar("V3 — transmissão", "Brasil", "RAP 2019 (principal)", rap, "R$ mi",
           f"média dos ciclos 2018-2019 ({f1819}) e 2019-2020 ({f1920} — FONTE SECUNDÁRIA)")
    ons, fons = r03.exigir(D, "ons_encargos_uso_ano_civil_2019")
    anotar("V3 — transmissão", "Brasil", "encargos de uso faturados pelo ONS no ano civil de 2019 (_rap_ons)", ons,
           "R$ mi", fons, "(jun/2019 − dez/2018) + dez/2019, SEAMSE")
    anotar("V3 — transmissão", "Brasil", "diferença _rap_ons − principal", ons - rap, "R$ mi", "cálculo",
           f"{ons:.4f} − {rap:.4f}")
    T = {r: rap * share_X[r] for r in REGIOES}
    T_ons = {r: ons * share_X[r] for r in REGIOES}

    # ---- V2: GAS-RB pelo preço da Sulgás ------------------------------------------------------------
    comp_sul = ler("componentes_v02_gas_sulgas.csv")
    comp_4d = ler("componentes_v02.csv")

    def vbp_gas(comp):
        c = comp[comp["componente"] == "vbp_gas"].set_index("regiao")["valor"].astype(float)
        return {r: float(c[r]) for r in REGIOES}

    g_sul, g_4d = vbp_gas(comp_sul), vbp_gas(comp_4d)
    for r in REGIOES:
        anotar("V2 — gás", r, "VBP do GAS (principal: preço da Sulgás no RB)", g_sul[r], "R$ mi",
               comp_sul.loc[(comp_sul["componente"] == "vbp_gas") & (comp_sul["regiao"] == r), "fonte"].iloc[0])
    anotar("V2 — gás", "RB", "VBP do GAS-RB com o preço médio das 4 distribuidoras (_gas4dist)", g_4d["RB"], "R$ mi",
           comp_4d.loc[(comp_4d["componente"] == "vbp_gas") & (comp_4d["regiao"] == "RB"), "fonte"].iloc[0])
    comp_ons = comp_sul.copy()
    for r in REGIOES:
        m = (comp_ons["componente"] == "vbp_transmissao") & (comp_ons["regiao"] == r)
        comp_ons.loc[m, "valor"] = repr(T_ons[r])
        comp_ons.loc[m, "fonte"] = (f"V3 (_rap_ons): encargos de uso faturados pelo ONS no ano civil de 2019 ({fons}) "
                                    f"× participação no VBP do S38 ({share_X[r]:.6f})")
    lin_sul, lin_4d = ler("regras_linha_v02_gas_sulgas.csv"), ler("regras_linha_v02.csv")
    for nome, lin in (("principal (Sulgás)", lin_sul), ("_gas4dist", lin_4d)):
        g = lin[lin["subsetor"] == "S38_GAS"]
        for r in REGIOES:
            v = g[g["regiao"] == r]["valor"].astype(float)
            n = int((v >= r03.W_MAX_GAS - 1e-9).sum())
            anotar("V2 — gás por comprador", r, f"compradores no teto de {r03.W_MAX_GAS} ({nome})", n, "nº",
                   ", ".join(g[(g["regiao"] == r) & (g["valor"].astype(float) >= r03.W_MAX_GAS - 1e-9)]["comprador"]) or "nenhum",
                   f"participação máxima do gás {v.max():.4f}")

    # ---- V1: TUST por MWh no SIN; remunerações ∝ (VBP − combustível) --------------------------------
    sin = geracao_sin()
    pesos = sin.rename(columns={"gwh_sin": "valor"})[["regiao", "subsetor", "valor"]].copy()
    pesos["fonte"] = [f"{FONTE_SIN}: D8 {a:.1f} GWh, ONS {b:.1f} GWh" for a, b in zip(sin["gwh_d8"], sin["gwh_ons"])]
    for x in sin.itertuples(index=False):
        anotar("V1 — MWh no SIN (peso da TUST da geração)", x.regiao, x.subsetor, x.gwh_sin, "GWh", FONTE_SIN,
               f"min(D8 {x.gwh_d8:.1f}; ONS {x.gwh_ons:.1f})")
    pri_base_sul, pri_base_4d = ler("regras_primarios_v02_gas_sulgas.csv"), ler("regras_primarios_v02.csv")
    pri = primarios(pri_base_sul, T, g_sul, X, F, share_X)
    pri_4d = primarios(pri_base_4d, T, g_4d, X, F, share_X)
    pri_ons = primarios(pri_base_sul, T_ons, g_sul, X, F, share_X)

    # ---- gravação --------------------------------------------------------------------------------
    def copia(nome_v02, nota):
        df = ler(nome_v02)
        if "fonte" in df.columns:
            df["fonte"] = df["fonte"] + f" [{nota}]"
        return df

    arq = {
        "subsetores": gravar(ler("subsetores_v02.csv"), f"subsetores_{V}.csv"),
        "participacoes_vbp": gravar(copia("participacoes_vbp_v02.csv", "igual à v02"), f"participacoes_vbp_{V}.csv"),
        "componentes": gravar(comp_sul, f"componentes_{V}.csv"),
        "regras_coluna": gravar(ler("regras_coluna_v02.csv"), f"regras_coluna_{V}.csv"),
        "regras_linha": gravar(lin_sul, f"regras_linha_{V}.csv"),
        "regras_primarios": gravar(pri, f"regras_primarios_{V}.csv"),
        "latentes_espelho": gravar(ler("latentes_espelho_v02.csv"), f"latentes_espelho_{V}.csv"),
        "pesos_tust_geracao": gravar(pesos, f"pesos_tust_geracao_{V}.csv"),
    }
    arq_p2 = arq | {"participacoes_vbp": gravar(copia("participacoes_vbp_v02_P2.csv", "igual à v02"),
                                                f"participacoes_vbp_{V}_P2.csv")}
    arq_4d = arq | {"componentes": gravar(comp_4d, f"componentes_{V}_gas4dist.csv"),
                    "regras_linha": gravar(lin_4d, f"regras_linha_{V}_gas4dist.csv"),
                    "regras_primarios": gravar(pri_4d, f"regras_primarios_{V}_gas4dist.csv")}
    arq_ons = arq | {"componentes": gravar(comp_ons, f"componentes_{V}_rap_ons.csv"),
                     "regras_primarios": gravar(pri_ons, f"regras_primarios_{V}_rap_ons.csv")}

    def piso(kappa, eta_v):
        d = {"kappa": kappa, "combustiveis": r03.COMBUSTIVEIS, "max_iter": 50}
        if eta_v is not None:
            d["viabilidade_eta"] = eta_v
        return d

    def reeq(eta, se_inviavel="erro"):
        return {"eta": eta, "linhas_fixas": r03.LINHAS_COMBUSTIVEL,
                "primarios_ajustaveis": ["ipi", "icms", "outros_impostos"], "importacoes": "fixas",
                "se_inviavel": se_inviavel}

    def cfg(nome, modo, arqs, kappa, eta, viab):
        return {"nome": nome,
                "descricao": "Parâmetros da Rodada 04 (D1=C, D2=D3=D4=D6=D7=A, D5=E1, D8=A, D9=a+b+f+r, D10=Sulgás, "
                             "V1, V2, V3); gerado por scripts/rodada04_parametros.py; fontes em cada linha dos CSVs e "
                             "em quadro_parametros_v03.xlsx",
                "setor_alvo": "S38", "regioes": REGIOES, "bloco_intrassetorial": "roteamento_por_componentes",
                "modo_vbp": "ancora_componentes", "subsetor_termica_gas": "S38_GN",
                "ras": {"tolerancia": 1.0e-8, "max_iter": 20000},
                "niveis": {"co2e": {"modo": modo, "residuo_para": ["S38_DIS", "S38_GAS"]}},
                "piso_vbp": piso(kappa, eta if viab else None), "reequilibrio": reeq(eta),
                "alerta_multiplicador_producao": r03.ALERTA_MULTIPLICADOR,
                "alerta_insumos_nao_energeticos": ALERTA_INSUMOS, "arquivos": arqs}

    def gravar_yaml(suf, c):
        with open(PAR / f"especificacao_{V}{suf}.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(c, f, allow_unicode=True, sort_keys=False)
        return PAR / f"especificacao_{V}{suf}.yaml"

    # a extensão de viabilidade só fica ligada se o T9 não passar sem ela (Seção 2.1, item 3)
    def viavel_sem_extensao(arqs, kappa, eta):
        caminho = gravar_yaml("_teste_viabilidade", cfg("teste", "residuo", arqs, kappa, eta, False))
        try:
            desagregar(mip, ler_especificacao(caminho), estrito=True)
            return True, ""
        except EspecificacaoInvalida as e:
            return False, str(e).splitlines()[0][:300]
        finally:
            caminho.unlink()

    variantes = {
        "": ("MIP RS×RB 2019 — S38 em 11 subsetores — v03 (P1 + E1 + D9 + V1 + V2; κ = 0.70, η = 0.10; principal)",
             "residuo", arq, KAPPA, ETA),
        "_P2": ("v03 — sensibilidade P2 (preços iguais) + E1", "residuo", arq_p2, KAPPA, ETA),
        "_E2": ("v03 — sensibilidade P1 + E2 (emissões na proporção do SEEG)", "proporcional", arq, KAPPA, ETA),
        "_E3": ("v03 — sensibilidade P1 + E3 (só níveis do SEEG; NÃO preserva o total da base)", "sem_residuo", arq,
                KAPPA, ETA),
        "_gas4dist": ("v03 — sensibilidade V2: VBP do GAS-RB pelo preço médio das 4 distribuidoras (26990.1)", "residuo",
                      arq_4d, KAPPA, ETA),
        "_rap_ons": ("v03 — sensibilidade V3: transmissão = encargos de uso faturados pelo ONS em 2019 (22935.6)",
                     "residuo", arq_ons, KAPPA, ETA),
        "_k060": ("v03 — sensibilidade κ = 0.60", "residuo", arq, 0.60, ETA),
        "_eta005": ("v03 — sensibilidade η = 0.05", "residuo", arq, KAPPA, 0.05),
    }
    decisao = []
    for suf, (nome, modo, arqs, kappa, eta) in variantes.items():
        ok, motivo = viavel_sem_extensao(arqs, kappa, eta)
        decisao.append({"especificacao": f"especificacao_{V}{suf}.yaml", "kappa": kappa, "eta": eta,
                        "T9 sem a extensão de viabilidade": "passa" if ok else "não passa",
                        "extensao_de_viabilidade": "desligada" if ok else "ligada", "motivo": motivo})
        gravar_yaml(suf, cfg(nome + ("" if ok else "; com a extensão de viabilidade (o T9 não passa sem ela)"),
                             modo, arqs, kappa, eta, not ok))
        anotar("V1 — extensão de viabilidade", "*", f"especificacao_{V}{suf}.yaml",
               "desligada" if ok else "ligada", "", "Seção 2.1, item 3: desliga se o T9 passar sem ela", motivo)
    anotar("D9", "*", "κ", KAPPA, "fração", "HIPÓTESE das instruções da Rodada 03 (D9-f); variante 0.60")
    anotar("D9", "*", "η", ETA, "fração", "HIPÓTESE das instruções da Rodada 03 (D9-r); variante 0.05")
    anotar("T12", "*", "insumos não energéticos ÷ VBP mínimos (ALERTA abaixo)", ALERTA_INSUMOS, "fração",
           "Seção 2.4 das instruções da Rodada 04")
    q = pd.DataFrame(quadro)
    salvar_tabelas(
        PAR / f"quadro_parametros_{V}.xlsx",
        {"quadro": q, "viabilidade": pd.DataFrame(decisao), "geracao_sin": sin, "pesos_tust_geracao": pesos,
         "componentes": comp_sul, "componentes_gas4dist": comp_4d, "componentes_rap_ons": comp_ons,
         "regras_primarios": pri, "valores_documentais": D},
        leiame=["Rodada 04 — quadro de parâmetros da MIP v03 (S38 em 11 subsetores), para revisão.",
                "A v03 parte dos parâmetros v02 (Rodada 03; regras de linha e de coluna, participações e componentes) "
                "e muda: V1 (TUST da geração por MWh no SIN; remunerações e ocupações da geração ∝ VBP − combustível), "
                "V2 (GAS-RB pelo preço da Sulgás) e V3 (variante _rap_ons).",
                "Aba viabilidade: se cada especificação passa no T9 sem a extensão de viabilidade do piso.",
                "Gerado por scripts/rodada04_parametros.py. Hipóteses marcadas como HIPÓTESE."],
    )
    print(f"[parâmetros v03] RAP {rap:.2f}; ONS {ons:.2f}; GAS-RB {g_sul['RB']:.2f}; "
          f"viabilidade: {[(d['especificacao'], d['extensao_de_viabilidade']) for d in decisao]}")


if __name__ == "__main__":
    main()
