"""Rodada 02 / 02b — tratamento dos dados coletados (sem rede).

Uso (na raiz do repositório):
    python scripts/rodada02_coleta.py      # 1) baixa as fontes (precisa de rede; registra o acesso)
    python scripts/rodada02.py             # 2) trata o que foi baixado → dados/intermediarios/
    python scripts/rodada02_parametros.py  # 3) parâmetros → parametros/*_v01
    python scripts/rodada02_mip.py         # 4) MIP v01, variantes, quadro e prévia → resultados/rodada02/

Saídas deste script (Rodada 02b; os arquivos _v01 da Rodada 02 não são sobrescritos):
- dados/intermediarios/geracao_2019_usina_v02.csv             ONS por usina, sem autoprodução (02b, Seção 2)
- dados/intermediarios/geracao_2019_regiao_subsetor_v02.csv   GWh por região × subsetor (ONS + sistemas isolados)
- dados/intermediarios/precos_2019_subsetor_v01.csv            preços de leilão corrigidos pelo IPCA (+ nuclear)
- dados/intermediarios/precos_2019_detalhe_v01.csv             cada leilão usado
- dados/intermediarios/cempre_2019_composicao_v01.csv          pessoal ocupado e salários por subsetor
- dados/intermediarios/seeg_2019_emissoes_v01.csv              emissões 2019 por região × combustível e × subsetor
- dados/intermediarios/siga_divergencias_ons_v01.csv           usinas com rótulo ONS ≠ classificação SIGA (informativo)
- dados/intermediarios/ben_2019_gas_natural_por_setor_v01.csv  BEN 2020: consumo final de gás natural por setor (mil tep)
- dados/intermediarios/ben_2019_consumo_especifico_v01.csv     BEN 2020 (Tabela 5.4): consumo de combustível ÷ geração
- resultados/rodada02/reconciliacao_epe_v01.csv                Seção 4 da 02b: BEN (serviço público) × RS + RB montado
- resultados/rodada02/comparacao_referencias_v02.csv           esperado × obtido × diferença (todas as fontes)
- resultados/rodada02/situacao_fontes_v02.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import pandas as pd  # noqa: E402

from mip.caminhos import PASTA_EXTERNOS, PASTA_INTERMEDIARIOS, PASTA_RESULTADOS  # noqa: E402
from mip.externos import cempre, leiloes, ons, seeg, siga  # noqa: E402

PASTA_SAIDA = PASTA_RESULTADOS / "rodada02"
BRUTOS = PASTA_EXTERNOS / "brutos"
INT = PASTA_INTERMEDIARIOS

# fonte → nome do arquivo gravado por scripts/rodada02_coleta.py. O arquivo fica em
# dados/externos/brutos/<fonte>/ (> 20 MB, fora do git) ou em dados/externos/<fonte>/ (≤ 20 MB).
NOMES = {
    "ons": "GERACAO_USINA-2_2019.parquet",
    "siga": "siga-empreendimentos-geracao.csv",
    "leiloes": "resultado-leiloes-geracao.csv",
    "ipca": "ipca_1737.json",
    "seeg": "Dados-nacionais-13.0.xlsx",
    "cempre": "cempre_6450.json",
}
RECORTE_SEEG = PASTA_EXTERNOS / "seeg" / "seeg13_2019_recorte_geracao_sf6_v01.csv"  # versionado (pequeno)
SISTEMAS_ISOLADOS = PASTA_EXTERNOS / "epe" / "sistemas_isolados_2019_v01.csv"  # EPE (Seção 3 da 02b)


def localizar(fonte: str) -> Path:
    """Caminho do bruto da fonte: na pasta versionada ou em brutos/ (o que existir; senão, o versionado)."""
    for pasta in (PASTA_EXTERNOS / fonte, BRUTOS / fonte):
        if (pasta / NOMES[fonte]).exists():
            return pasta / NOMES[fonte]
    return PASTA_EXTERNOS / fonte / NOMES[fonte]


ARQUIVOS = {f: localizar(f) for f in NOMES}
OBRIGATORIAS = {"ons": "5.1", "leiloes": "5.4", "ipca": "5.4", "seeg": "5.7", "cempre": "5.8"}


def _comp(df: pd.DataFrame, fonte: str, esperado: str, obtido: str, item: str, grupo: str | None = None,
          tolerancia="tolerancia", confere="confere") -> pd.DataFrame:
    out = pd.DataFrame({
        "fonte": fonte,
        "grupo": df[grupo] if grupo else "",
        "item": df[item].astype(str),
        "esperado": df[esperado],
        "obtido": df[obtido],
    })
    out["diferenca"] = out["obtido"] - out["esperado"]
    out["tolerancia"] = df[tolerancia] if tolerancia in df else None
    out["confere"] = df[confere] if confere in df else None
    return out


# ---------------------------------------------------------------------------------------------
# 5.1 / 5.2 / 5.3 — geração
# ---------------------------------------------------------------------------------------------
def tratar_geracao():
    """ONS por usina (com SIGA e a tabela de reclassificação/exclusão) + sistemas isolados da EPE."""
    df = ons.ler_ons(ARQUIVOS["ons"])
    reclass = ons.ler_reclassificacao(PASTA_EXTERNOS / "ons" / "reclassificacao_usinas_v01.csv")
    cl = siga.classificar_siga(siga.ler_siga(ARQUIVOS["siga"])) if ARQUIVOS["siga"].exists() else None
    usinas = ons.geracao_por_usina(df, reclass, cl)
    usinas.to_csv(INT / "geracao_2019_usina_v02.csv", index=False)
    tab = ons.geracao_por_regiao_subsetor(usinas)
    tab.insert(1, "origem", "ONS (SIN)")
    if SISTEMAS_ISOLADOS.exists():  # Seção 3 da 02b: soma os sistemas isolados ao RB
        iso = pd.read_csv(SISTEMAS_ISOLADOS)
        linha = {"regiao": "RB", "origem": "EPE (sistemas isolados)"}
        for c in ons.ORDEM_SUBSETORES_GERACAO:
            linha[c] = 0.0
            for x in iso[iso["subsetor"] == c].itertuples(index=False):
                if x.metodo == "isolados":  # opção 1: geração dos sistemas isolados por fonte
                    linha[c] += float(x.gwh)
                elif x.metodo == "nacional_menos_ons":  # opção 2: nacional (serviço público) − ONS (RS + RB)
                    ons_c = float(tab.loc[tab["regiao"].isin(["RS", "RB"]), c].sum())
                    linha[c] += float(x.gwh) - ons_c
                else:
                    raise SystemExit(f"{SISTEMAS_ISOLADOS}: método desconhecido {x.metodo!r}")
                if linha[c] < 0:
                    raise SystemExit(f"sistemas isolados {c}: geração negativa ({linha[c]:.1f} GWh)")
        linha["Total"] = sum(linha[c] for c in ons.ORDEM_SUBSETORES_GERACAO)
        tab = pd.concat([tab, pd.DataFrame([linha])], ignore_index=True)
    tab.to_csv(INT / "geracao_2019_regiao_subsetor_v02.csv", index=False)
    comps = [
        _comp(ons.comparar_com_referencia(usinas), "ONS (R02, Seção 5.1)", "esperado_gwh", "obtido_gwh", "item", "grupo"),
        _comp(ons.comparar_com_referencia_02b(usinas), "ONS (R02b, Seção 2)", "esperado_gwh", "obtido_gwh", "item", "grupo"),
    ]
    if cl is not None:
        casado = siga.classificar_usinas_ons(usinas[["ceg", "nom_usina"]], cl)
        div = usinas.assign(subsetor_siga=casado["subsetor_siga"], regra_siga=casado["regra_siga"])
        div = div[div["subsetor_siga"].notna() & (div["subsetor_siga"] != div["subsetor"])
                  & ~div["subsetor"].isin([ons.FORA_S38])]
        div.sort_values("gwh", ascending=False).to_csv(INT / "siga_divergencias_ons_v01.csv", index=False)
    print(f"[geração] {len(usinas)} usinas; excluídas (autoprodução): "
          f"{usinas.loc[usinas['subsetor'] == ons.FORA_S38, 'gwh'].sum():.1f} GWh; "
          f"isolados: {'sim' if SISTEMAS_ISOLADOS.exists() else 'não'}")
    return usinas, tab, pd.concat(comps, ignore_index=True)


# ---------------------------------------------------------------------------------------------
# EPE, BEN 2020 — gás por setor (5.6), consumo específico (5.10) e reconciliação (Seção 4 da 02b)
# ---------------------------------------------------------------------------------------------
BEN_MATRIZ = PASTA_EXTERNOS / "epe" / "ben_2020" / "BEN2020_Matriz_ab2019.xlsx"
BEN_TAB54 = PASTA_EXTERNOS / "epe" / "ben2020_tabela_5_4_v01.csv"  # transcrição da Tabela 5.4 (p. 112 do PDF)
FONTE_BEN_MATRIZ = ("EPE, BEN 2020 (ano-base 2019), Matriz ab2019.xlsx, aba Consolidada (mil tep), coluna GÁS NATURAL; "
                    "acesso 2026-10-15T19:38:26Z")
FONTE_BEN_TAB54 = "EPE, BEN 2020, Tabela 5.4 – Centrais Elétricas de Serviço Público (p. 112); acesso 2026-10-15T19:38:26Z"


def _ben_consolidada() -> pd.DataFrame:
    """Aba Consolidada da matriz do BEN 2019: linhas = fluxos, colunas = fontes (mil tep)."""
    bruto = pd.read_excel(BEN_MATRIZ, sheet_name="Consolidada", header=None)
    nomes = [f"{a or ''} {b or ''}".replace("- ", "").replace("-", "").strip()
             for a, b in zip(bruto.iloc[1].fillna(""), bruto.iloc[2].fillna(""))]
    tab = bruto.iloc[3:].copy()
    tab.columns = ["fluxo"] + nomes[1:]
    tab["fluxo"] = tab["fluxo"].astype(str).str.strip()
    return tab.set_index("fluxo")


def tratar_ben(tab_geracao: pd.DataFrame):
    if not BEN_MATRIZ.exists():
        print("[BEN] matriz do BEN 2020 ausente: gás por setor e consumo específico ficam no fallback")
        return None
    cons = _ben_consolidada()
    gn = [c for c in cons.columns if c.startswith("GÁS NA")][0]
    setores = ["CONSUMO FINAL NÃO ENERGÉTICO", "SETOR ENERGÉTICO", "RESIDENCIAL", "COMERCIAL", "PÚBLICO", "AGROPECUÁRIO",
               "RODOVIÁRIO", "FERROVIÁRIO", "AÉREO", "HIDROVIÁRIO", "CIMENTO", "FERRO GUSA E AÇO", "FERRO LIGAS",
               "MINERAÇÃO E PELOTIZAÇÃO", "NÃO FERROSOS E OUT. METALURG.", "QUÍMICA", "ALIMENTOS E BEBIDAS", "TÊXTIL",
               "PAPEL E CELULOSE", "CERÂMICA", "OUTRAS INDÚSTRIAS", "CONSUMO NÃO IDENTIFICADO"]
    gas = pd.DataFrame({"setor_ben": setores, "gas_natural_mil_tep": [float(cons.loc[x, gn]) for x in setores]})
    gas["fonte"] = FONTE_BEN_MATRIZ
    total_cf = float(cons.loc["CONSUMO FINAL", gn])
    gas.to_csv(INT / "ben_2019_gas_natural_por_setor_v01.csv", index=False)
    comps = [pd.DataFrame([{"fonte": "BEN 2020 (consistência)", "grupo": "gás natural",
                            "item": "Σ setores = consumo final (mil tep)", "esperado": total_cf,
                            "obtido": gas["gas_natural_mil_tep"].sum(), "tolerancia": 0.5}])]
    # Tabela 5.4: consumo específico das centrais de serviço público e conferência com a matriz
    t54 = pd.read_csv(BEN_TAB54)
    sp = cons.loc["CENTRAIS. ELET. SERV. PÚBLICO"]
    conf = {"GÁS NATURAL": gn, "CARVÃO VAPOR": [c for c in cons.columns if c.startswith("CARVÃO VAPOR")][0],
            "URÂNIO CONTIDO NO UO2": [c for c in cons.columns if c.startswith("URÂNIO C/UO2")][0],
            "ÓLEO DIESEL": [c for c in cons.columns if c.startswith("ÓLEO DIESEL")][0],
            "ÓLEO COMBUSTÍVEL": [c for c in cons.columns if c.startswith("ÓLEO COMB")][0],
            "LENHA": [c for c in cons.columns if c.startswith("LENHA")][0]}
    for fonte_ben, col in conf.items():
        esperado = float(t54.loc[t54["fonte_ben"] == fonte_ben, "consumo_mil_tep_2019"].iloc[0])
        comps.append(pd.DataFrame([{"fonte": "BEN 2020 (Tabela 5.4 × matriz)", "grupo": "centrais de serviço público",
                                    "item": f"consumo {fonte_ben} (mil tep)", "esperado": esperado,
                                    "obtido": -float(sp[col]), "tolerancia": 0.5}]))
    t = t54[t54["subsetor_s38"].notna() & t54["consumo_mil_tep_2019"].notna()]
    ce = t.groupby("subsetor_s38")[["consumo_mil_tep_2019", "geracao_gwh_2019"]].sum()
    ce["tep_por_mwh"] = ce["consumo_mil_tep_2019"] / ce["geracao_gwh_2019"]
    ce["fonte"] = FONTE_BEN_TAB54 + ": consumo de combustível ÷ geração, por fonte"
    ce = ce.reset_index().rename(columns={"subsetor_s38": "subsetor"})
    ce.to_csv(INT / "ben_2019_consumo_especifico_v01.csv", index=False)
    # Seção 4 da 02b: geração de serviço público (BEN) × RS + RB montado (ONS − autoprodução + isolados)
    t = t54[t54["subsetor_s38"].notna()]
    ben = t.groupby("subsetor_s38")["geracao_gwh_2019"].sum()
    nos = tab_geracao[tab_geracao["regiao"].isin(["RS", "RB"])]
    linhas = []
    for c in ons.ORDEM_SUBSETORES_GERACAO:
        rs = float(nos.loc[nos["regiao"] == "RS", c].sum())
        rb_sin = float(nos.loc[(nos["regiao"] == "RB") & (nos["origem"] == "ONS (SIN)"), c].sum())
        rb_iso = float(nos.loc[(nos["regiao"] == "RB") & (nos["origem"] != "ONS (SIN)"), c].sum())
        b = float(ben.get(c, 0.0))
        linhas.append({"subsetor": c, "ben_servico_publico_gwh": b, "rs_gwh": rs, "rb_sin_gwh": rb_sin,
                       "rb_isolados_gwh": rb_iso, "rs_mais_rb_gwh": rs + rb_sin + rb_iso,
                       "diferenca_gwh (montado − BEN)": rs + rb_sin + rb_iso - b,
                       "diferenca_pct": (rs + rb_sin + rb_iso - b) / b * 100 if b else None})
    outras = float(t54.loc[t54["fonte_ben"] == "OUTRAS NÃO RENOVÁVEIS", "geracao_gwh_2019"].iloc[0])
    linhas.append({"subsetor": "outras não renováveis (BEN)", "ben_servico_publico_gwh": outras, "rs_gwh": 0.0,
                   "rb_sin_gwh": 0.0, "rb_isolados_gwh": 0.0, "rs_mais_rb_gwh": 0.0,
                   "diferenca_gwh (montado − BEN)": -outras, "diferenca_pct": -100.0})
    rec = pd.DataFrame(linhas)
    tot = rec.drop(columns=["subsetor"]).sum(numeric_only=True)
    tot["diferenca_pct"] = tot["diferenca_gwh (montado − BEN)"] / tot["ben_servico_publico_gwh"] * 100
    rec = pd.concat([rec, pd.DataFrame([{"subsetor": "Total", **tot.to_dict()}])], ignore_index=True)
    rec["fonte_ben"] = FONTE_BEN_TAB54
    rec.to_csv(PASTA_SAIDA / "reconciliacao_epe_v01.csv", index=False)
    comp = pd.concat(comps, ignore_index=True)
    comp["diferenca"] = comp["obtido"] - comp["esperado"]
    comp["confere"] = comp["diferenca"].abs() <= comp["tolerancia"]
    print(f"[BEN] gás por setor ({len(gas)} setores; consumo final {total_cf:.1f} mil tep); consumo específico: "
          + ", ".join(f"{r.subsetor} {r.tep_por_mwh:.4f}" for r in ce.itertuples()))
    return comp


# ---------------------------------------------------------------------------------------------
# 5.4 — preços
# ---------------------------------------------------------------------------------------------
def tratar_precos():
    lei = leiloes.ler_leiloes(ARQUIVOS["leiloes"])
    ipca = leiloes.ler_ipca_sidra(ARQUIVOS["ipca"])
    res = leiloes.precos_medios_2019(lei, ipca)
    tab = leiloes.acrescentar_nuclear(res.tabela)
    tab.to_csv(INT / "precos_2019_subsetor_v01.csv", index=False)
    res.detalhe.to_csv(INT / "precos_2019_detalhe_v01.csv", index=False)
    comp = leiloes.comparar_com_referencia(tab)
    out = _comp(comp, "Leilões ANEEL + IPCA (5.4)", "esperado", "obtido", "subsetor", tolerancia="_", confere="dentro_tolerancia")
    out["tolerancia"] = leiloes.TOLERANCIA_REFERENCIA
    ipca_ref = pd.DataFrame([{"fonte": "IPCA SIDRA 1737 (5.4)", "grupo": "", "item": "média do índice em 2019",
                              "esperado": leiloes.REFERENCIA_IPCA_MEDIA_2019, "obtido": res.media_ipca_2019}])
    ipca_ref["diferenca"] = ipca_ref["obtido"] - ipca_ref["esperado"]
    ipca_ref["tolerancia"] = 0.01
    ipca_ref["confere"] = ipca_ref["diferenca"].abs() <= 0.01
    print(f"[preços] {res.contagens}; média IPCA 2019 = {res.media_ipca_2019:.4f}")
    return tab, pd.concat([out, ipca_ref], ignore_index=True)


# ---------------------------------------------------------------------------------------------
# 5.8 — CEMPRE
# ---------------------------------------------------------------------------------------------
def tratar_cempre():
    df = cempre.ler_cempre_sidra(ARQUIVOS["cempre"])
    comp = cempre.composicao_cempre(df)
    comp.to_csv(INT / "cempre_2019_composicao_v01.csv", index=False)
    ref = cempre.comparar_com_referencia(df)
    ref = ref[~ref["esperado_sigiloso"]]
    out = _comp(ref.assign(item=ref["cnae"] + " " + ref["item"] + " " + ref["variavel"]), "CEMPRE (5.8)",
                "esperado", "obtido", "item", "territorio", tolerancia="_", confere="dentro_tolerancia")
    out["tolerancia"] = 0.5
    return comp, out


# ---------------------------------------------------------------------------------------------
# 5.7 — SEEG
# ---------------------------------------------------------------------------------------------
def tratar_seeg(gwh_rs: dict):
    if RECORTE_SEEG.exists():
        filtrado = pd.read_csv(RECORTE_SEEG)
    else:
        filtrado = seeg.ler_seeg_filtrado(ARQUIVOS["seeg"], ano=2019)
        filtrado.to_csv(RECORTE_SEEG, index=False)
    por_reg = seeg.emissoes_por_regiao(filtrado)
    por_sub = seeg.emissoes_por_subsetor(filtrado, gwh_rs)
    a = por_reg["por_combustivel"].copy()
    a.insert(0, "tabela", "por_combustivel_mil_t")
    b = (por_sub / 1000.0).reset_index()
    b.insert(0, "tabela", "por_subsetor_mil_t_(PET_RS_realocado)")
    linhas_sf6 = pd.DataFrame([{"tabela": "sf6_nacional_mil_t", "regiao": "Brasil", "valor": por_reg["sf6_nacional_mil_t"]}])
    out = pd.concat([a, b, linhas_sf6], ignore_index=True)
    out.to_csv(INT / "seeg_2019_emissoes_v01.csv", index=False)
    comp = seeg.comparar_com_referencia(por_reg)
    out = _comp(comp, "SEEG 13.0 (5.7), mil t CO2e", "esperado_mil_t", "obtido_mil_t", "item", "regiao",
                tolerancia="_", confere="dentro_tolerancia")
    out["tolerancia"] = seeg.TOLERANCIA_REFERENCIA
    print(f"[SEEG] PET do RS realocado: {por_sub.attrs.get('pet_rs_realocado_t', 0):.1f} t; "
          f"não alocado → RB: {por_sub.attrs.get('nao_alocado_para_rb_t', 0):.1f} t; não mapeados: {por_sub.attrs.get('nao_mapeados_t')}")
    return por_reg, por_sub, out


def situacao_fontes() -> pd.DataFrame:
    linhas = []
    for fonte, caminho in ARQUIVOS.items():
        linhas.append({
            "fonte": fonte,
            "secao": OBRIGATORIAS.get(fonte, "5.2" if fonte == "siga" else ""),
            "obrigatoria": fonte in OBRIGATORIAS,
            "arquivo": caminho.relative_to(RAIZ).as_posix(),
            "disponivel": caminho.exists(),
        })
    return pd.DataFrame(linhas)


def main():
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    INT.mkdir(parents=True, exist_ok=True)
    sit = situacao_fontes()
    sit.to_csv(PASTA_SAIDA / "situacao_fontes_v02.csv", index=False)
    comps = []
    usinas, tab, c = tratar_geracao()
    comps.append(c)
    c = tratar_ben(tab)
    if c is not None:
        comps.append(c[["fonte", "grupo", "item", "esperado", "obtido", "diferenca", "tolerancia", "confere"]])
    _, c = tratar_precos()
    comps.append(c)
    _, c = tratar_cempre()
    comps.append(c)
    rs = usinas[usinas["regiao"] == "RS"].groupby("subsetor")["gwh"].sum()
    _, _, c = tratar_seeg({"S38_CAR": float(rs.get("S38_CAR", 0.0)), "S38_GN": float(rs.get("S38_GN", 0.0))})
    comps.append(c)
    comp = pd.concat(comps, ignore_index=True)
    comp.to_csv(PASTA_SAIDA / "comparacao_referencias_v02.csv", index=False)
    print(f"[referências] {int(comp['confere'].fillna(False).astype(bool).sum())}/{len(comp)} conferem; "
          f"divergências: {comp.loc[~comp['confere'].fillna(False).astype(bool), ['fonte', 'item', 'esperado', 'obtido']].to_dict('records')}")


if __name__ == "__main__":
    main()
