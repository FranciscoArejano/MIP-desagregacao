"""Rodada 03 — MIP v02: T2 (re-agregação com a especificação v02), T9 (EOB mínimo), T10 (geração por fonte = BEN),
T11 (executor de cenários) e testes das peças novas do motor (piso de VBP, reequilíbrio, fixa_por_tipo, leitor longo).

Os testes com a especificação real são pulados se os parâmetros v02 ainda não tiverem sido gerados
(scripts/rodada03.py e scripts/rodada03_parametros.py).
"""
import numpy as np
import pandas as pd
import pytest

from mip import cenarios as cen
from mip import referencia as ref
from mip.caminhos import PASTA_EXTERNOS, PASTA_INTERMEDIARIOS, PASTA_PARAMETROS
from mip.desagregacao import (
    EspecificacaoInvalida,
    _desagregar_passo,
    _redistribuir_com_piso,
    agregar,
    desagregar,
    ler_especificacao,
)
from mip.estrutura import ITENS_PRIMARIOS, ITENS_SATELITE
from mip.exportacao import exportar_longo
from mip.externos import ben
from mip.leitura import ler_mip_longo, ler_mip_original
from mip.modelo import ModeloLeontief, ranking_setorial

TOL = 1e-6
ARRAYS = ["Z", "F", "X", "total_linha", "V", "V_df", "X_df"]
VARIANTES = ["", "_P2", "_E2", "_E3", "_k060", "_k080", "_eta005", "_sem_viabilidade"]
IP = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}


@pytest.fixture(scope="module")
def mip():
    return ler_mip_original()


def _espec(suf=""):
    caminho = PASTA_PARAMETROS / f"especificacao_v02{suf}.yaml"
    if not caminho.exists():
        pytest.skip(f"{caminho.name} ainda não foi gerado (scripts/rodada03_parametros.py)")
    return ler_especificacao(caminho)


@pytest.fixture(scope="module")
def v02(mip):
    return desagregar(mip, _espec(""))


# ---------------------------------------------------------------------------------------------
# T2 — re-agregação exata com a especificação v02 (todas as variantes)
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("suf", VARIANTES)
def test_t2_reagregacao_v02(mip, suf):
    res = desagregar(mip, _espec(suf), estrito=False)
    assert res.mip.n == 156
    ag = agregar(res.mip, res.mapa, mip.setores)
    for nome in ARRAYS:
        np.testing.assert_allclose(getattr(ag, nome), getattr(mip, nome), rtol=0, atol=TOL, err_msg=f"{suf}: {nome}")
    outros = [k for k, it in enumerate(ITENS_SATELITE) if it != "co2e" or suf != "_E3"]
    np.testing.assert_allclose(ag.S[outros], mip.S[outros], rtol=0, atol=TOL)  # inclui CO2e na E1 e na E2
    falhas = res.checagens[res.checagens["status"] == "FALHA"]
    assert not len(falhas), falhas


# ---------------------------------------------------------------------------------------------
# T9 — EOB ≥ η × VBP na principal; soma dos EOB de cada região igual à da v01; RAS convergido
# ---------------------------------------------------------------------------------------------
def test_t9_eob_minimo(mip, v02):
    eta = float(v02.especificacao.reequilibrio["eta"])
    m = v02.mip
    sub = v02.mapa[v02.mapa["desagregado"]]
    for k in sub["indice_novo"]:
        if m.X[k] > 0:
            assert m.V[IP["eob"], k] >= eta * m.X[k] - TOL, m.setores["id"][k]
    v01 = PASTA_PARAMETROS / "especificacao_v01.yaml"
    r01 = desagregar(mip, ler_especificacao(v01), estrito=False) if v01.exists() else None
    for r in ("RS", "RB"):
        ks = sub.loc[sub["regiao"] == r, "indice_novo"].to_numpy()
        soma = m.V[IP["eob"], ks].sum()
        assert soma == pytest.approx(mip.V[IP["eob"], mip.indice(r, "S38")], abs=TOL)
        if r01 is not None:
            s01 = r01.mapa[r01.mapa["desagregado"] & (r01.mapa["regiao"] == r)]["indice_novo"].to_numpy()
            assert soma == pytest.approx(r01.mip.V[IP["eob"], s01].sum(), abs=TOL)
    assert v02.info_ras["convergiu"].all()
    assert v02.info_ras["contexto"].str.startswith("reequilibrio_EOB").sum() == 2
    tab = v02.extras["reequilibrio_RAS"]
    assert (tab.loc[tab["VBP"] > 0, "EOB/VBP_depois"] >= eta - 1e-9).all()


def test_t9_sem_viabilidade_fica_abaixo_e_avisa(mip):
    res = desagregar(mip, _espec("_sem_viabilidade"), estrito=False)
    c = res.checagens.set_index("checagem")
    assert c.loc["EOB_minimo_eta", "status"] == "ALERTA"
    m = res.mip
    for r, s in (("RB", "S38_GN"), ("RB", "S38_PET")):
        k = m.indice(r, s)
        assert 0 <= m.V[IP["eob"], k] < 0.1 * m.X[k]


def test_reequilibrio_inviavel_da_erro(mip):
    e = _espec("_sem_viabilidade")
    e.reequilibrio = dict(e.reequilibrio, se_inviavel="erro")
    with pytest.raises(EspecificacaoInvalida, match="custos fixos"):
        desagregar(mip, e, estrito=False)


# ---------------------------------------------------------------------------------------------
# D9-f — piso de VBP
# ---------------------------------------------------------------------------------------------
def test_piso_vbp(v02):
    p = v02.extras["pisos_vbp"]
    kappa = float(v02.especificacao.piso_vbp["kappa"])
    m = v02.mip
    for x in p.itertuples():
        assert m.X[m.indice(x.regiao, x.subsetor)] >= x.combustivel / kappa - TOL
    # E_r da geração não muda com os pisos
    comp = v02.extras["componentes_bloco"].set_index("regiao")
    for r in ("RS", "RB"):
        assert p[p["regiao"] == r]["VBP_final"].sum() == pytest.approx(comp.loc[r, "E_r (energia = VBP da geração)"], rel=1e-12)
    assert v02.checagens.set_index("checagem").loc["piso_vbp_combustivel", "status"] == "OK"
    atingidos = set(p.loc[p["piso_atingido"], "subsetor"] + "-" + p.loc[p["piso_atingido"], "regiao"])
    assert {"S38_GN-RB", "S38_PET-RB", "S38_GN-RS"} <= atingidos


def test_redistribuir_com_piso():
    g = np.array([50.0, 30.0, 20.0])
    piso = np.array([0.0, 45.0, 0.0])
    novo = _redistribuir_com_piso(g, piso, 100.0, "teste")
    assert novo.sum() == pytest.approx(100.0)
    assert novo[1] == pytest.approx(45.0)
    assert novo[0] / novo[2] == pytest.approx(50 / 20)  # os demais caem na proporção do VBP
    # cascata: quem cai abaixo do próprio piso também é preso
    novo = _redistribuir_com_piso(np.array([50.0, 30.0, 20.0]), np.array([0.0, 45.0, 19.0]), 100.0, "teste")
    assert novo[2] == pytest.approx(19.0) and novo[0] == pytest.approx(36.0)
    with pytest.raises(EspecificacaoInvalida):
        _redistribuir_com_piso(g, np.array([60.0, 50.0, 0.0]), 100.0, "teste")


def test_combustiveis_integrais(v02):
    m = v02.mip
    for r in ("RS", "RB"):
        for forn, sub in (("S04", "S38_CAR"), ("S03", "S38_BIO"), ("S09", "S38_BIO")):
            tot = sum(m.Z[m.indice(q, forn), m.indice(r, s)] for q in ("RS", "RB")
                      for s in v02.especificacao.subsetores["codigo"])
            no_sub = sum(m.Z[m.indice(q, forn), m.indice(r, sub)] for q in ("RS", "RB"))
            assert no_sub == pytest.approx(tot, abs=TOL), (r, forn)
    # D9-a: importações do S38-RS só na DIS
    imp = m.V[IP["importacoes"]]
    rs = [m.indice("RS", s) for s in v02.especificacao.subsetores["codigo"]]
    assert imp[m.indice("RS", "S38_DIS")] == pytest.approx(imp[rs].sum(), abs=TOL)


def test_fixa_por_tipo_segue_o_vbp(v02):
    m = v02.mip
    for r in ("RS", "RB"):
        ger = [m.indice(r, s) for s in ("S38_HID", "S38_EOL", "S38_CAR", "S38_GN")]
        rem = m.V[IP["remuneracoes"], ger]
        np.testing.assert_allclose(rem / rem.sum(), m.X[ger] / m.X[ger].sum(), rtol=1e-10)


def test_gas_rb_por_volume(v02):
    comp = v02.extras["componentes_bloco"].set_index("regiao")
    d = pd.read_csv(PASTA_EXTERNOS / "valores_documentais_v02.csv").set_index("parametro")["valor"]
    preco = float(d["gas_preco_medio_4_distribuidoras_2019"])
    vol = (float(d["mme_gas_distribuidoras_sem_termeletrico_2019"]) - float(d["mme_gas_sulgas_2019"])) * 365
    assert comp.loc["RB", "VBP_gas"] == pytest.approx(preco * vol, rel=1e-12)
    assert comp.loc["RS", "VBP_gas"] == pytest.approx(float(d["sulgas_receita_liquida_2019"]), rel=1e-12)


def test_alerta_multiplicador(v02):
    c = v02.checagens.set_index("checagem")
    assert c.loc["multiplicador_producao_subsetores", "tolerancia"] == pytest.approx(2.2)
    mult = ModeloLeontief(v02.mip).L.sum(axis=0)
    sub = v02.mapa.loc[v02.mapa["desagregado"], "indice_novo"].to_numpy()
    assert (c.loc["multiplicador_producao_subsetores", "status"] == "ALERTA") == bool((mult[sub] > 2.2).any())


# ---------------------------------------------------------------------------------------------
# T10 — geração por fonte: RS + RB = BEN (Tabela 5.4), por fonte
# ---------------------------------------------------------------------------------------------
def test_t10_geracao_rs_mais_rb_igual_ben():
    caminho = PASTA_INTERMEDIARIOS / "geracao_2019_regiao_subsetor_v03.csv"
    if not caminho.exists():
        pytest.skip("rode scripts/rodada03.py")
    g = pd.read_csv(caminho).set_index("regiao")
    br = ben.geracao_brasil_por_subsetor(ben.ler_tabela_5_4(PASTA_EXTERNOS / "epe" / "ben2020_tabela_5_4_v01.csv"))
    for c in br.index:
        assert g.loc["RS", c] + g.loc["RB", c] == pytest.approx(br[c], abs=0.5), c
        assert br[c] == pytest.approx(ben.REFERENCIA_D8_BRASIL[c], abs=0.5), c
        assert g.loc["RB", c] == pytest.approx(ben.REFERENCIA_D8_RB[c], abs=0.5), c
        assert g.loc["RS", c] == pytest.approx(ben.REFERENCIA_D8_RS[c], abs=0.5), c


def test_d8_pet_inclui_outras_nao_renovaveis():
    tab = pd.DataFrame({"fonte_ben": ["ÓLEO DIESEL", "ÓLEO COMBUSTÍVEL", "OUTRAS NÃO RENOVÁVEIS", "TOTAL"],
                        "geracao_gwh_2019": [10.0, 5.0, 1.0, 16.0]})
    s = ben.geracao_brasil_por_subsetor(tab)
    assert s["S38_PET"] == 16.0 and s.drop("S38_PET").sum() == 0
    with pytest.raises(ValueError, match="sem subsetor"):
        ben.geracao_brasil_por_subsetor(pd.DataFrame({"fonte_ben": ["NOVA"], "geracao_gwh_2019": [1.0]}))


# ---------------------------------------------------------------------------------------------
# T11 — executor de cenários reproduz os 9 cenários da Rodada 01 na MIP original
# ---------------------------------------------------------------------------------------------
def test_t11_executor_reproduz_rodada01(mip):
    df = cen.ler_cenarios(PASTA_PARAMETROS / "cenarios_exemplo.csv")
    assert sorted(df["cenario"].unique()) == sorted(ref.CENARIOS_RS)
    tab = cen.executar(mip, df, "original")
    imp = tab["impactos"].set_index("cenario")
    esp = ref.ESPERADO.set_index("cenario")
    for c in esp.index:
        for ind, tol in ref.TOLERANCIAS.items():
            assert imp.loc[c, ind] == pytest.approx(esp.loc[c, ind], abs=tol), (c, ind)
        assert imp.loc[c, "producao_por_mil_t"] == pytest.approx(imp.loc[c, "dX_total"] / imp.loc[c, "co2e_total"] * 1000)
    top = tab["top10"][tab["top10"]["cenario"] == "R1"]
    assert list(top["codigo"]) == list(ref.TOP10_R1["codigo"])
    np.testing.assert_allclose(top["CO2e induzido (t)"], ref.TOP10_R1["co2e"], atol=0.05)
    regs = tab["regioes"]
    for c in esp.index:
        assert regs[regs["cenario"] == c]["co2e"].sum() == pytest.approx(imp.loc[c, "co2e_total"])


def test_executor_reparte_s38_na_mip_desagregada(v02):
    df = cen.cenarios_da_rodada01()
    choques, rep = cen.resolver_choques(v02.mip, df[df["cenario"] == "E1"])
    assert sum(choques.values()) == pytest.approx(1000.0)
    m = v02.mip
    fd = {s: m.F[m.indice("RS", s)].sum() for s in v02.especificacao.subsetores["codigo"]}
    pos = {s: v for s, v in fd.items() if v > 0}
    for s, v in choques.items():
        assert v == pytest.approx(1000.0 * pos[s[1]] / sum(pos.values()))
    with pytest.raises(cen.CenarioInvalido):
        cen.resolver_choques(v02.mip, pd.DataFrame({"cenario": ["X"], "regiao": ["RS"], "setor": ["S99"], "valor_R$mi": [1.0]}))
    ch, _ = cen.resolver_choques(v02.mip, df[df["cenario"] == "E1"], {"S38_DIS": 3.0, "S38_GAS": 1.0})
    assert ch[("RS", "S38_DIS")] == pytest.approx(750.0) and ch[("RS", "S38_GAS")] == pytest.approx(250.0)


def test_sensibilidade_entre_versoes(mip, v02):
    tab = cen.executar_versoes({"original": mip, "v02": v02.mip}, cen.cenarios_da_rodada01())
    s = tab["sensibilidade"]
    assert set(s["versao"]) == {"original", "v02"}
    base = s[s["versao"] == "original"]
    assert np.allclose(base["diferenca"], 0)
    # dY total é o mesmo nas duas versões (o choque é só repartido)
    dy = s[s["indicador"] == "dY_total"]
    assert np.allclose(dy["diferenca"], 0, atol=1e-9)


# ---------------------------------------------------------------------------------------------
# leitor do formato longo (variantes só em CSV)
# ---------------------------------------------------------------------------------------------
def test_ler_mip_longo_ida_e_volta(tmp_path, v02):
    destino = tmp_path / "x_longo.csv"
    exportar_longo(v02.mip, destino)
    v02.mip.coef_latentes.to_csv(tmp_path / "x_coef_latentes.csv", index=False)
    m = ler_mip_longo(destino)
    for nome in ["Z", "F", "X", "V", "V_df", "X_df", "S"]:
        np.testing.assert_allclose(getattr(m, nome), getattr(v02.mip, nome), rtol=1e-13, atol=1e-9, err_msg=nome)
    assert list(m.setores["codigo"]) == list(v02.mip.setores["codigo"])
    a = ModeloLeontief(m).simular_choques({("RS", "S38_PET"): 1.0}).emissoes.sum()
    b = ModeloLeontief(v02.mip).simular_choques({("RS", "S38_PET"): 1.0}).emissoes.sum()
    assert a == pytest.approx(b)  # latente lido do arquivo ao lado


def test_passo_sem_reequilibrio_tem_eob_negativo(mip):
    """Sem (r), os pisos sozinhos não bastam (é o que justifica o reequilíbrio)."""
    from dataclasses import replace

    e = _espec("")
    r = _desagregar_passo(mip, replace(e, reequilibrio={}), reequilibrar=False)
    k = r.mip.indice("RB", "S38_GN")
    assert r.mip.V[IP["eob"], k] < 0
