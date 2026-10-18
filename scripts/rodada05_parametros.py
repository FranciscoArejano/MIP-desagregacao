"""Rodada 05 — parâmetros da MIP v04 (versão final) a partir dos parâmetros v03 (Rodada 04).

Uso (na raiz do repositório, depois de scripts/rodada04_parametros.py e scripts/rodada05_diagnostico_seeg.py):
    python scripts/rodada05_parametros.py

Mudanças em relação à v03 (instruções da Rodada 05, Seção 2):
- D17: VBP da transmissão = encargos de uso do sistema de transmissão faturados pelo ONS no ano civil de 2019
  (22935.6 R$ mi; SEAMSE dez/2018, jun/2019 e dez/2019), repartido entre RS e RB pela participação no VBP do S38
  (a variante _rap_ons da v03 promovida a principal). A transmissão da v03 (RAP 24883.4) vira a variante _rap_media.
- D18: TUST das colunas latentes (SOL-RS e PET-RS) = TUST por MWh das fontes do RS no SIN (τ_RS, regra da V1) ao
  R$/MWh do espelho do RB (p_k = VBP ÷ GWh da D8), com a repartição entre as linhas de transmissão mantida
  (`tust_latentes` no YAML; o motor calcula τ_RS e p_k na própria versão).
- D19: κ = 0.70 (ALERTA do T12 aceito); D21: E1 na principal, E3 e E4 como sensibilidades.
- E4 (Seção 3.2): parte do resíduo de emissões E1 sai de DIS e GAS (na proporção do resíduo de cada um) para S19,
  S04 e S05 da mesma região, pelos valores do SEEG 13.0 (dados/externos/seeg/seeg13_2019_componentes_e4_v04.csv,
  gerado por scripts/rodada05_diagnostico_seeg.py) — `realocacao_emissoes_v04_E4.csv`.

Saídas em parametros/ (todas com coluna `fonte`): especificacao_v04.yaml e as variantes _P2, _E2, _E3, _E4,
_gas4dist, _rap_media, _k060 e _eta005; os CSVs _v04 e quadro_parametros_v04.xlsx.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from mip.caminhos import PASTA_EXTERNOS, PASTA_INTERMEDIARIOS, PASTA_PARAMETROS  # noqa: E402
from mip.desagregacao import EspecificacaoInvalida, desagregar, ler_especificacao  # noqa: E402
from mip.exportacao import salvar_tabelas  # noqa: E402
from mip.leitura import ler_mip_original  # noqa: E402

_spec = importlib.util.spec_from_file_location("r04p", RAIZ / "scripts" / "rodada04_parametros.py")
r04 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r04)  # funções e constantes da Rodada 04 (e, por ela, da Rodada 03); não grava nada
r03 = r04.r03

PAR = PASTA_PARAMETROS
INT = PASTA_INTERMEDIARIOS
DOCS = PASTA_EXTERNOS / "valores_documentais_v03.csv"
E4_SEEG = PASTA_EXTERNOS / "seeg" / "seeg13_2019_componentes_e4_v04.csv"
V = "v04"
REGIOES = r03.REGIOES
KAPPA, ETA = r03.KAPPA, r03.ETA
FONTE_D17 = ("D17: encargos de uso do sistema de transmissão faturados pelo ONS no ano civil de 2019 (SEAMSE dez/2018, "
             "jun/2019 e dez/2019); sem PIS/Pasep e Cofins; inclui o orçamento do ONS")
FONTE_D18 = ("HIPÓTESE (D18, Rodada 05): as colunas latentes do RS pagam a TUST por MWh das fontes do RS no SIN (regra da "
             "V1), ao R$/MWh do espelho do RB (VBP do espelho ÷ GWh da D8, geracao_2019_regiao_subsetor_v03.csv), e não "
             "a TUST por real do espelho")
HIPOTESE_E4 = ("HIPÓTESE (E4, sensibilidade; Rodada 05, Seção 3.2): a conta-satélite da NEREUS incluiria no S38 estas "
               "emissões do SEEG (indício do diagnóstico NEREUS × SEEG, não prova); se elas já estiverem nos setores de "
               "destino, a E4 as conta duas vezes (no S19-RS, por exemplo) —")
# Seção 3.2 das instruções da Rodada 05 (mil t CO2e), para conferência dos valores lidos do SEEG
REFERENCIA_E4 = {("RS", "S19"): 1812.1, ("RS", "S04"): 88.1, ("RB", "S19"): 18088.8, ("RB", "S05"): 23499.2,
                 ("RB", "S04"): 1155.4}

quadro = []
anotar = r04.anotar
r04.quadro = quadro  # anotar() da Rodada 04 grava no quadro desta rodada


def ler(nome: str) -> pd.DataFrame:
    return pd.read_csv(PAR / nome, dtype=str, keep_default_na=False)


def gravar(df: pd.DataFrame, nome: str) -> str:
    df.to_csv(PAR / nome, index=False)
    return nome


def com_transmissao(comp: pd.DataFrame, T: dict, fonte: dict) -> pd.DataFrame:
    c = comp.copy()
    for r in REGIOES:
        m = (c["componente"] == "vbp_transmissao") & (c["regiao"] == r)
        c.loc[m, "valor"] = repr(float(T[r]))
        c.loc[m, "fonte"] = fonte[r]
    return c


def realocacao_e4() -> pd.DataFrame:
    if not E4_SEEG.exists():
        raise SystemExit(f"{E4_SEEG.relative_to(RAIZ)} não existe: rode antes scripts/rodada05_diagnostico_seeg.py")
    e = pd.read_csv(E4_SEEG, dtype={"regiao": str, "setor_destino": str})
    g = e.groupby(["regiao", "setor_destino"], sort=False).agg(valor=("valor_t", "sum"),
                                                                 componente=("componente", " + ".join),
                                                                 fonte=("fonte", "first")).reset_index()
    for (r, s), ref in REFERENCIA_E4.items():
        x = g[(g["regiao"] == r) & (g["setor_destino"] == s)]
        if len(x) != 1 or abs(float(x["valor"].iloc[0]) / 1000 - ref) > 0.1:  # referência = soma de 2 parcelas arredondadas
            raise SystemExit(f"E4 {r} {s}: {x['valor'].tolist()} t ≠ referência {ref} mil t (Seção 3.2)")
    if len(g) != len(REFERENCIA_E4):
        raise SystemExit(f"E4: esperadas {len(REFERENCIA_E4)} linhas, há {len(g)}")
    return pd.DataFrame({"regiao": g["regiao"], "item": "co2e", "setor_destino": g["setor_destino"],
                         "valor": [repr(float(v)) for v in g["valor"]],
                         "fonte": [f"{HIPOTESE_E4} {c} — {f}" for c, f in zip(g["componente"], g["fonte"])]})


def main():
    mip = ler_mip_original()
    X = {r: float(mip.X[mip.indice(r, "S38")]) for r in REGIOES}
    F = {r: float(sum(mip.Z[mip.indice(r, "S38"), mip.indice(q, "S38")] for q in REGIOES)) for r in REGIOES}
    share_X = {r: X[r] / sum(X.values()) for r in REGIOES}
    r03.DOCS = DOCS
    D = r03.docs()

    # ---- D17: transmissão pelos encargos do ONS ------------------------------------------------------
    ons, _ = r03.exigir(D, "ons_encargos_uso_ano_civil_2019")
    seamse = D.set_index("parametro").loc[["ons_encargos_uso_ciclo1819_jul_dez_2018",
                                           "ons_encargos_uso_ciclo1819_jul2018_jun2019",
                                           "ons_encargos_uso_ciclo1920_jul_dez_2019"]]
    fons = ("ano civil 2019 = (jun/2019 − dez/2018) + dez/2019 = " + " ; ".join(
        f"{x.documento}, {x.localizacao}, {x.url}, SHA-256 {str(x.sha256)[:12]}…" for x in seamse.itertuples()))
    rap_1819, f1819 = r03.exigir(D, "rap_total_ciclo_2018_2019")
    rap_1920, f1920 = r03.exigir(D, "rap_total_ciclo_2019_2020")
    rap = (rap_1819 + rap_1920) / 2
    anotar("D17 — transmissão", "Brasil", "encargos de uso faturados pelo ONS no ano civil de 2019 (principal)", ons,
           "R$ mi", f"{FONTE_D17} ({fons})", "(jun/2019 − dez/2018) + dez/2019, SEAMSE")
    anotar("D17 — transmissão", "Brasil", "RAP 2019 da v03 (variante _rap_media)", rap, "R$ mi",
           f"média dos ciclos 2018-2019 ({f1819}) e 2019-2020 ({f1920} — FONTE SECUNDÁRIA)")
    T = {r: ons * share_X[r] for r in REGIOES}
    T_media = {r: rap * share_X[r] for r in REGIOES}
    for r in REGIOES:
        anotar("D17 — transmissão", r, "VBP da transmissão (principal)", T[r], "R$ mi", FONTE_D17,
               f"{ons:.4f} × participação de {r} no VBP do S38 ({share_X[r]:.6f})")
    fonte_T = {r: f"{FONTE_D17} ({fons}) × participação de {r} no VBP do S38 ({share_X[r]:.6f})" for r in REGIOES}
    fonte_Tm = {r: (f"variante _rap_media (D17): RAP 2019 da v03 = média dos ciclos 2018-2019 e 2019-2020 ({rap:.4f}; "
                    f"o ciclo 2019-2020 por FONTE SECUNDÁRIA) × participação de {r} no VBP do S38 ({share_X[r]:.6f})")
                for r in REGIOES}

    comp_v03, comp_v03_4d = ler("componentes_v03.csv"), ler("componentes_v03_gas4dist.csv")
    comp = com_transmissao(comp_v03, T, fonte_T)
    comp_media = com_transmissao(comp_v03, T_media, fonte_Tm)
    comp_4d = com_transmissao(comp_v03_4d, T, fonte_T)

    def vbp_gas(c):
        g = c[c["componente"] == "vbp_gas"].set_index("regiao")["valor"].astype(float)
        return {r: float(g[r]) for r in REGIOES}

    g_sul, g_4d = vbp_gas(comp), vbp_gas(comp_4d)
    # SF6 entre TRA e DIS refeito com a transmissão e o GAS de cada especificação (regra da v03)
    pri_v02_sul, pri_v02_4d = ler("regras_primarios_v02_gas_sulgas.csv"), ler("regras_primarios_v02.csv")
    pri = r04.primarios(pri_v02_sul, T, g_sul, X, F, share_X)
    pri_media = r04.primarios(pri_v02_sul, T_media, g_sul, X, F, share_X)
    pri_4d = r04.primarios(pri_v02_4d, T, g_4d, X, F, share_X)

    # ---- D18: TUST das colunas latentes -------------------------------------------------------------
    d8 = pd.read_csv(INT / "geracao_2019_regiao_subsetor_v03.csv").set_index("regiao")
    esp = ler("latentes_espelho_v03.csv")
    gwh = {}
    for x in esp.itertuples(index=False):
        gwh[x.subsetor] = float(d8.loc[x.regiao_espelho, x.subsetor])
        anotar("D18 — TUST das latentes", x.regiao_espelho, f"GWh do espelho de {x.regiao} {x.subsetor} (D8)",
               gwh[x.subsetor], "GWh", "geracao_2019_regiao_subsetor_v03.csv (D8)",
               "p_k = VBP do espelho na versão ÷ este GWh (o motor calcula)")
    tust_latentes = {"gwh_espelho": gwh, "fonte": FONTE_D18}

    # ---- E4 ------------------------------------------------------------------------------------------
    e4 = realocacao_e4()
    for x in e4.itertuples(index=False):
        anotar("E4 — realocação de emissões", x.regiao, f"para {x.setor_destino}", float(x.valor), "t CO2e", x.fonte,
               "retirado de S38_DIS e S38_GAS da região na proporção do resíduo E1 de cada um")

    # ---- gravação --------------------------------------------------------------------------------
    def copia(nome_v03, nota):
        df = ler(nome_v03)
        if "fonte" in df.columns:
            df["fonte"] = df["fonte"] + f" [{nota}]"
        return df

    arq = {
        "subsetores": gravar(ler("subsetores_v03.csv"), f"subsetores_{V}.csv"),
        "participacoes_vbp": gravar(copia("participacoes_vbp_v03.csv", "igual à v03"), f"participacoes_vbp_{V}.csv"),
        "componentes": gravar(comp, f"componentes_{V}.csv"),
        "regras_coluna": gravar(ler("regras_coluna_v03.csv"), f"regras_coluna_{V}.csv"),
        "regras_linha": gravar(ler("regras_linha_v03.csv"), f"regras_linha_{V}.csv"),
        "regras_primarios": gravar(pri, f"regras_primarios_{V}.csv"),
        "latentes_espelho": gravar(esp, f"latentes_espelho_{V}.csv"),
        "pesos_tust_geracao": gravar(ler("pesos_tust_geracao_v03.csv"), f"pesos_tust_geracao_{V}.csv"),
    }
    arq_p2 = arq | {"participacoes_vbp": gravar(copia("participacoes_vbp_v03_P2.csv", "igual à v03"),
                                                f"participacoes_vbp_{V}_P2.csv")}
    arq_4d = arq | {"componentes": gravar(comp_4d, f"componentes_{V}_gas4dist.csv"),
                    "regras_linha": gravar(ler("regras_linha_v03_gas4dist.csv"), f"regras_linha_{V}_gas4dist.csv"),
                    "regras_primarios": gravar(pri_4d, f"regras_primarios_{V}_gas4dist.csv")}
    arq_media = arq | {"componentes": gravar(comp_media, f"componentes_{V}_rap_media.csv"),
                       "regras_primarios": gravar(pri_media, f"regras_primarios_{V}_rap_media.csv")}
    arq_e4 = arq | {"realocacao_emissoes": gravar(e4, f"realocacao_emissoes_{V}_E4.csv")}

    def piso(kappa, eta_v):
        d = {"kappa": kappa, "combustiveis": r03.COMBUSTIVEIS, "max_iter": 50}
        if eta_v is not None:
            d["viabilidade_eta"] = eta_v
        return d

    def reeq(eta):
        return {"eta": eta, "linhas_fixas": r03.LINHAS_COMBUSTIVEL,
                "primarios_ajustaveis": ["ipi", "icms", "outros_impostos"], "importacoes": "fixas",
                "se_inviavel": "erro"}

    def cfg(nome, modo, arqs, kappa, eta, viab):
        return {"nome": nome,
                "descricao": "Parâmetros da Rodada 05 (D1=C, D2=D3=D4=D6=D7=A, D5=E1, D8=A, D9=a+b+f+r, D10=Sulgás, "
                             "V1, V2, D17=A, D18=A, D19=A, D21=A); gerado por scripts/rodada05_parametros.py; fontes em "
                             "cada linha dos CSVs e em quadro_parametros_v04.xlsx",
                "setor_alvo": "S38", "regioes": REGIOES, "bloco_intrassetorial": "roteamento_por_componentes",
                "modo_vbp": "ancora_componentes", "subsetor_termica_gas": "S38_GN",
                "ras": {"tolerancia": 1.0e-8, "max_iter": 20000},
                "niveis": {"co2e": {"modo": modo, "residuo_para": ["S38_DIS", "S38_GAS"]}},
                "piso_vbp": piso(kappa, eta if viab else None), "reequilibrio": reeq(eta),
                "tust_latentes": tust_latentes,
                "alerta_multiplicador_producao": r03.ALERTA_MULTIPLICADOR,
                "alerta_insumos_nao_energeticos": r04.ALERTA_INSUMOS, "arquivos": arqs}

    def gravar_yaml(suf, c):
        with open(PAR / f"especificacao_{V}{suf}.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(c, f, allow_unicode=True, sort_keys=False)
        return PAR / f"especificacao_{V}{suf}.yaml"

    def viavel_sem_extensao(arqs, modo, kappa, eta):
        caminho = gravar_yaml("_teste_viabilidade", cfg("teste", modo, arqs, kappa, eta, False))
        try:
            desagregar(mip, ler_especificacao(caminho), estrito=True)
            return True, ""
        except EspecificacaoInvalida as e:
            return False, str(e).splitlines()[0][:300]
        finally:
            caminho.unlink()

    principal = "MIP RS×RB 2019 — S38 em 11 subsetores — v04 final (P1 + E1 + D9 + V1 + V2 + D17 + D18; κ = 0.70, η = 0.10)"
    variantes = {
        "": (principal, "residuo", arq, KAPPA, ETA),
        "_P2": ("v04 — sensibilidade P2 (preços iguais) + E1", "residuo", arq_p2, KAPPA, ETA),
        "_E2": ("v04 — sensibilidade P1 + E2 (emissões na proporção do SEEG)", "proporcional", arq, KAPPA, ETA),
        "_E3": ("v04 — sensibilidade P1 + E3 (só níveis do SEEG; NÃO preserva o total da base)", "sem_residuo", arq,
                KAPPA, ETA),
        "_E4": ("v04 — sensibilidade E4 (E1 com refino, exploração de petróleo e gás e mineração de carvão do SEEG "
                "realocados de DIS e GAS para S19, S05 e S04; preserva só o total da economia)", "residuo", arq_e4,
                KAPPA, ETA),
        "_gas4dist": ("v04 — sensibilidade V2: VBP do GAS-RB pelo preço médio das 4 distribuidoras (26990.1)", "residuo",
                      arq_4d, KAPPA, ETA),
        "_rap_media": ("v04 — sensibilidade D17: transmissão da v03 (RAP 2019 = 24883.4)", "residuo", arq_media, KAPPA,
                       ETA),
        "_k060": ("v04 — sensibilidade κ = 0.60", "residuo", arq, 0.60, ETA),
        "_eta005": ("v04 — sensibilidade η = 0.05", "residuo", arq, KAPPA, 0.05),
    }
    decisao = []
    for suf, (nome, modo, arqs, kappa, eta) in variantes.items():
        ok, motivo = viavel_sem_extensao(arqs, modo, kappa, eta)
        decisao.append({"especificacao": f"especificacao_{V}{suf}.yaml", "kappa": kappa, "eta": eta,
                        "T9 sem a extensão de viabilidade": "passa" if ok else "não passa",
                        "extensao_de_viabilidade": "desligada" if ok else "ligada", "motivo": motivo})
        gravar_yaml(suf, cfg(nome + ("" if ok else "; com a extensão de viabilidade (o T9 não passa sem ela)"),
                             modo, arqs, kappa, eta, not ok))
    anotar("D19", "*", "κ", KAPPA, "fração", "D19 = A (Rodada 05): κ = 0.70; ALERTA do T12 aceito; variante 0.60")
    anotar("D9", "*", "η", ETA, "fração", "HIPÓTESE das instruções da Rodada 03 (D9-r); variante 0.05")
    q = pd.DataFrame(quadro)
    salvar_tabelas(
        PAR / f"quadro_parametros_{V}.xlsx",
        {"quadro": q, "viabilidade": pd.DataFrame(decisao), "componentes": comp, "componentes_rap_media": comp_media,
         "componentes_gas4dist": comp_4d, "regras_primarios": pri, "realocacao_emissoes_E4": e4,
         "valores_documentais": D},
        leiame=["Rodada 05 — quadro de parâmetros da MIP v04 (versão final; S38 em 11 subsetores), para revisão.",
                "A v04 parte dos parâmetros v03 e muda: D17 (transmissão = encargos de uso faturados pelo ONS em 2019, "
                "22935.6 R$ mi; a RAP da v03 vira _rap_media) e D18 (TUST das colunas latentes pela TUST por MWh das "
                "fontes do RS; HIPÓTESE). Variante nova _E4 (Seção 3.2).",
                "Aba viabilidade: se cada especificação passa no T9 sem a extensão de viabilidade do piso.",
                "Gerado por scripts/rodada05_parametros.py. Hipóteses marcadas como HIPÓTESE."],
    )
    print(f"[parâmetros v04] transmissão {ons:.2f} (RS {T['RS']:.2f}, RB {T['RB']:.2f}); _rap_media {rap:.2f}; "
          f"GWh espelho {gwh}; E4 {[(x.regiao, x.setor_destino, round(float(x.valor) / 1000, 1)) for x in e4.itertuples()]}; "
          f"viabilidade: {[(d['especificacao'], d['extensao_de_viabilidade']) for d in decisao]}")


if __name__ == "__main__":
    main()
