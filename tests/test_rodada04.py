"""Rodada 04 — MIP v03 (V1, V2, V3), T12 e simulações do artigo (blocos A0, A1, A2 e B).

Os testes com a especificação real são pulados se os parâmetros v03 ainda não tiverem sido gerados
(scripts/rodada04_parametros.py); os das simulações, se parametros/cenarios_v03.csv não existir.
"""
import numpy as np
import pandas as pd
import pytest

from mip import cenarios as cen
from mip import referencia as ref
from mip.caminhos import PASTA_EXTERNOS, PASTA_PARAMETROS, PASTA_RESULTADOS
from mip.desagregacao import (
    EspecificacaoInvalida,
    _combustivel_nas_colunas,
    agregar,
    desagregar,
    insumos_nao_energeticos,
    ler_especificacao,
)
from mip.estrutura import ITENS_PRIMARIOS, ITENS_SATELITE
from mip.leitura import ler_mip_original

TOL = 1e-6
ARRAYS = ["Z", "F", "X", "total_linha", "V", "V_df", "X_df"]
VARIANTES = ["", "_P2", "_E2", "_E3", "_gas4dist", "_rap_ons", "_k060", "_eta005"]
IP = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}
GER = ["S38_HID", "S38_EOL", "S38_SOL", "S38_BIO", "S38_CAR", "S38_GN", "S38_PET", "S38_NUC"]


@pytest.fixture(scope="module")
def mip():
    return ler_mip_original()


def _espec(suf=""):
    caminho = PASTA_PARAMETROS / f"especificacao_v03{suf}.yaml"
    if not caminho.exists():
        pytest.skip(f"{caminho.name} ainda não foi gerado (scripts/rodada04_parametros.py)")
    return ler_especificacao(caminho)


@pytest.fixture(scope="module")
def v03(mip):
    return desagregar(mip, _espec(""))


@pytest.mark.parametrize("suf", VARIANTES)
def test_t2_reagregacao_v03(mip, suf):
    res = desagregar(mip, _espec(suf), estrito=False)
    ag = agregar(res.mip, res.mapa, mip.setores)
    for nome in ARRAYS:
        np.testing.assert_allclose(getattr(ag, nome), getattr(mip, nome), rtol=0, atol=TOL, err_msg=f"{suf}: {nome}")
    outros = [k for k, it in enumerate(ITENS_SATELITE) if it != "co2e" or suf != "_E3"]
    np.testing.assert_allclose(ag.S[outros], mip.S[outros], rtol=0, atol=TOL)
    assert not (res.checagens["status"] == "FALHA").any()
    assert res.especificacao.piso_vbp.get("viabilidade_eta") is None  # extensão desligada em todas (V1)


def test_t9_v03_sem_extensao(mip, v03):
    m = v03.mip
    sub = v03.mapa[v03.mapa["desagregado"]]
    for k in sub["indice_novo"]:
        if m.X[k] > 0:
            assert m.V[IP["eob"], k] >= 0.1 * m.X[k] - TOL, m.setores["id"][k]
    for r in ("RS", "RB"):
        ks = sub.loc[sub["regiao"] == r, "indice_novo"].to_numpy()
        assert m.V[IP["eob"], ks].sum() == pytest.approx(mip.V[IP["eob"], mip.indice(r, "S38")], abs=TOL)
    p = v03.extras["pisos_vbp"]
    assert set(p.loc[p["piso_atingido"], "piso_que_manda"]) == {"kappa"}
    for r, s in (("RB", "S38_GN"), ("RB", "S38_PET"), ("RS", "S38_GN")):
        x = p[(p["regiao"] == r) & (p["subsetor"] == s)].iloc[0]
        assert x["combustivel / VBP_final"] == pytest.approx(0.70, rel=1e-6)


def test_t12_insumos_nao_energeticos(mip, v03):
    t = insumos_nao_energeticos(v03).set_index(["regiao", "subsetor"])
    baixo = set(t.index[t["insumos_nao_energeticos / VBP"] < 0.05])
    assert baixo == {("RS", "S38_GN"), ("RB", "S38_GN")}  # ALERTA explicado no relatório
    c = v03.checagens.set_index("checagem")
    assert c.loc["insumos_nao_energeticos_minimo", "status"] == "ALERTA"
    assert "RS_S38_GN (0.0200)" in c.loc["insumos_nao_energeticos_minimo", "detalhe"]
    k060 = desagregar(mip, _espec("_k060"), estrito=False)
    assert k060.checagens.set_index("checagem").loc["insumos_nao_energeticos_minimo", "status"] == "OK"


def test_v1_tust_por_mwh_no_sin(v03):
    m, e = v03.mip, v03.especificacao
    pesos = e.pesos_tust_geracao
    tra = [m.indice(q, "S38_TRA") for q in ("RS", "RB")]
    for r in ("RS", "RB"):
        pr = pesos[pesos["regiao"] == r].set_index("subsetor")["valor"]
        tust = np.array([m.Z[tra, m.indice(r, s)].sum() for s in GER])
        w = np.array([pr.get(s, 0.0) for s in GER])
        np.testing.assert_allclose(tust / tust.sum(), w / w.sum(), atol=1e-9, err_msg=r)
    assert m.Z[tra, m.indice("RB", "S38_PET")].sum() / m.Z[tra, m.indice("RB", "S38_GN")].sum() == pytest.approx(1974.3 / 46474.0, rel=1e-4)


def test_v1_remuneracoes_vbp_menos_combustivel(v03):
    m, mapa = v03.mip, v03.mapa
    ip = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}
    for r in ("RS", "RB"):
        idx = [m.indice(r, s) for s in GER if m.X[m.indice(r, s)] > 0]
        comb = _combustivel_nas_colunas(v03.especificacao, m.Z, m.V, mapa, idx, ip)
        base = m.X[idx] - comb
        for item, mat in (("remuneracoes", m.V[ip["remuneracoes"]]), ("ocupacoes", m.S[ITENS_SATELITE.index("ocupacoes")])):
            razao = mat[idx] / base
            np.testing.assert_allclose(razao, razao[0], rtol=1e-9, err_msg=f"{r} {item}")


def test_v2_gas_rb_pelo_preco_da_sulgas(v03):
    m = v03.mip
    assert m.X[m.indice("RB", "S38_GAS")] == pytest.approx(19421.0454, abs=1e-3)
    lin = pd.read_csv(PASTA_PARAMETROS / "regras_linha_v03.csv")
    g = lin[(lin["subsetor"] == "S38_GAS") & (lin["regiao"] == "RB")]["valor"]
    assert g.max() < 0.90 - 1e-6  # no RB nenhum comprador encosta no teto


def test_v3_rap_ons(mip):
    d = pd.read_csv(PASTA_EXTERNOS / "valores_documentais_v03.csv").set_index("parametro")["valor"]
    assert d["ons_encargos_uso_ciclo1819_jul_dez_2018"] == pytest.approx(10576.54416201)
    assert d["ons_encargos_uso_ciclo1819_jul2018_jun2019"] == pytest.approx(21367.05829217)
    assert d["ons_encargos_uso_ciclo1920_jul_dez_2019"] == pytest.approx(12145.09004499)
    ano = d["ons_encargos_uso_ciclo1819_jul2018_jun2019"] - d["ons_encargos_uso_ciclo1819_jul_dez_2018"] + \
        d["ons_encargos_uso_ciclo1920_jul_dez_2019"]
    assert ano == pytest.approx(d["ons_encargos_uso_ano_civil_2019"]) and ano == pytest.approx(22935.6, abs=0.05)
    r = desagregar(mip, _espec("_rap_ons"), estrito=False)
    xs = {q: mip.X[mip.indice(q, "S38")] for q in ("RS", "RB")}
    for q in ("RS", "RB"):
        assert r.mip.X[r.mip.indice(q, "S38_TRA")] == pytest.approx(ano * xs[q] / sum(xs.values()), rel=1e-9)


def test_pesos_sin_referencia():
    p = pd.read_csv(PASTA_PARAMETROS / "pesos_tust_geracao_v03.csv").set_index(["regiao", "subsetor"])["valor"]
    for s, v in {"S38_HID": 363907.4, "S38_EOL": 48122.9, "S38_SOL": 4384.6, "S38_BIO": 1771.8, "S38_CAR": 11197.8,
                 "S38_GN": 46474.0, "S38_PET": 1974.3, "S38_NUC": 16128.8}.items():
        assert p[("RB", s)] == pytest.approx(v, abs=0.5)
    for s in ("S38_SOL", "S38_PET", "S38_NUC"):  # latentes e zerados não pagam TUST
        assert p[("RS", s)] == 0


def test_validacao_pesos_tust(mip):
    e = _espec("")
    pt = e.pesos_tust_geracao.copy()
    e.pesos_tust_geracao = pd.concat([pt, pd.DataFrame([{"regiao": "RS", "subsetor": "S38_DIS", "valor": 1.0, "fonte": "x"}])])
    with pytest.raises(EspecificacaoInvalida, match="só subsetores de geração"):
        desagregar(mip, e, estrito=False)
    e = _espec("")
    pt = e.pesos_tust_geracao.copy()
    pt.loc[(pt["regiao"] == "RS") & (pt["subsetor"] == "S38_SOL"), "valor"] = 10.0
    e.pesos_tust_geracao = pt
    with pytest.raises(EspecificacaoInvalida, match="sem produção"):
        desagregar(mip, e, estrito=False)


# ---------------------------------------------------------------------------------------------
# simulações
# ---------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def cenarios_v03():
    caminho = PASTA_PARAMETROS / "cenarios_v03.csv"
    if not caminho.exists():
        pytest.skip("cenarios_v03.csv ainda não foi gerado (scripts/rodada04_simulacoes.py)")
    return cen.ler_cenarios(caminho)


def test_a0_reproduz_o_artigo(mip, cenarios_v03):
    a0 = cenarios_v03[cenarios_v03["cenario"].str.startswith("A0_")]
    imp = cen.executar(mip, a0, "original")["impactos"].set_index("cenario")
    esp = ref.ESPERADO.set_index("cenario")
    for c in esp.index:
        for ind, tol in ref.TOLERANCIAS.items():
            assert imp.loc[f"A0_{c}", ind] == pytest.approx(esp.loc[c, ind], abs=tol), (c, ind)


def test_cenarios_v03_estrutura(v03, cenarios_v03):
    tot = cenarios_v03.groupby("cenario")["valor_R$mi"].sum()
    for c, v in tot.items():
        if not c.startswith("B_TWh_"):
            assert v == pytest.approx(1000.0), c
    assert "A0_R4b" in tot.index and "A1_R4b" not in tot.index and "A2_R4b" not in tot.index  # D11
    c = cenarios_v03.set_index(["cenario", "setor"])["valor_R$mi"]
    assert c[("A2_R1", "S38_EOL")] == pytest.approx(300.0)  # D12
    m = v03.mip
    xc, xg = m.X[m.indice("RS", "S38_CAR")], m.X[m.indice("RS", "S38_GN")]
    assert c[("A2_F1", "S38_CAR")] / c[("A2_F1", "S38_GN")] == pytest.approx(xc / xg)  # D13
    assert c[("A2_E1", "S38")] == pytest.approx(1000.0)  # D14: como no A1
    # B por TWh: choque = R$/MWh (1 TWh); SOL-RS latente ao R$/MWh do SOL-RB
    g = pd.read_csv(PASTA_PARAMETROS.parent / "dados" / "intermediarios" / "geracao_2019_regiao_subsetor_v03.csv").set_index("regiao")
    assert c[("B_TWh_EOL", "S38_EOL")] == pytest.approx(m.X[m.indice("RS", "S38_EOL")] * 1e6 / (g.loc["RS", "S38_EOL"] * 1e3))
    assert c[("B_TWh_SOL", "S38_SOL")] == pytest.approx(m.X[m.indice("RB", "S38_SOL")] * 1e6 / (g.loc["RB", "S38_SOL"] * 1e3))


def test_a1_e1_igual_a2_e1_e_participacao(v03, cenarios_v03):
    sel = cenarios_v03[cenarios_v03["cenario"].isin(["A1_E1", "A2_E1"])]
    t = cen.executar(v03.mip, sel, "v03")
    imp = t["impactos"].set_index("cenario")
    assert imp.loc["A1_E1", "co2e_total"] == pytest.approx(imp.loc["A2_E1", "co2e_total"])
    p = t["participacao_setor"]
    p1 = p[p["cenario"] == "A1_E1"]
    assert p1.loc[p1["codigo"] == "S38 (total)", "co2e"].iloc[0] == pytest.approx(p1.loc[p1["codigo"] != "S38 (total)", "co2e"].sum())


def test_b_twh_fator_direto_do_carvao(v03, cenarios_v03):
    sel = cenarios_v03[cenarios_v03["cenario"] == "B_TWh_CAR"]
    imp = cen.executar(v03.mip, sel, "v03")["impactos"].iloc[0]
    m = v03.mip
    k = m.indice("RS", "S38_CAR")
    g = pd.read_csv(PASTA_PARAMETROS.parent / "dados" / "intermediarios" / "geracao_2019_regiao_subsetor_v03.csv").set_index("regiao")
    fator = m.S[ITENS_SATELITE.index("co2e"), k] / (g.loc["RS", "S38_CAR"] * 1e3)  # t por MWh (E1)
    assert imp["co2e_diretas"] == pytest.approx(fator * 1e6, rel=1e-9)  # 1 TWh = 1e6 MWh


def test_simulacoes_publicadas():
    caminho = PASTA_RESULTADOS / "rodada04" / "simulacoes_v03.xlsx"
    if not caminho.exists():
        pytest.skip("simulações ainda não geradas")
    abas = pd.ExcelFile(caminho).sheet_names
    for a in ("A0", "A1", "A2", "A2_sens", "B_RS1bi", "B_TWh", "robustez", "tabela1_artigo", "tabela2_artigo",
              "tabela3_artigo", "tabela4_artigo", "comparacao_artigo"):
        assert a in abas
    assert any(a.startswith("top10_") for a in abas)
    for f in ("fig1_top10_R1_A2.png", "fig2_diretas_indiretas_A0_A2.png", "fig3_emissoes_por_TWh_B.png"):
        assert (PASTA_RESULTADOS / "rodada04" / "figuras" / f).exists()
