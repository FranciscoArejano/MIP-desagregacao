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
SISTEMAS_ISOLADOS = PASTA_EXTERNOS / "epe" / "sistemas_isolados_2019_v01.csv"  # gerado a partir do anuário da EPE


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
            linha[c] = float(iso.loc[iso["subsetor"] == c, "gwh"].sum())
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
