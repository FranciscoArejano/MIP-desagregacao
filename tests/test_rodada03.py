"""Rodada 03 — MIP v02: T2 (re-agregação com a especificação v02), T9 (EOB mínimo), T10 (geração por fonte = BEN),
T11 (executor de cenários) e testes das peças novas do motor (piso de VBP, reequilíbrio, fixa_por_tipo, leitor longo)
e das correções da revisão adversarial (teto do gás por comprador, validações, executor, latentes no formato longo).

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
VARIANTES = ["", "_P2", "_E2", "_E3", "_k060", "_k080", "_eta005", "_sem_viabilidade", "_gas_sulgas"]
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



# ---------------------------------------------------------------------------------------------
# Revisão adversarial da Rodada 03
# ---------------------------------------------------------------------------------------------
def _vendas_s38(res, r):
    """{comprador: (compras ao S38-r, venda da DIS-r, venda do GAS-r)} para setores e famílias da região r."""
    from mip.estrutura import COLUNAS_DF

    m = res.mip
    dfc = list(COLUNAS_DF["codigo"])
    lin = res.mapa.loc[(res.mapa["regiao"] == r) & res.mapa["desagregado"], "indice_novo"].to_numpy()
    dis, gas = m.indice(r, "S38_DIS"), m.indice(r, "S38_GAS")
    out = {}
    for c in m.setores.loc[m.setores["regiao"] == r, "codigo"]:
        if not c.startswith("S38"):
            j = m.indice(r, c)
            out[c] = (m.Z[lin, j].sum(), m.Z[dis, j], m.Z[gas, j])
    f = dfc.index(f"FAM_{r}")
    out["FAM"] = (m.F[lin, f].sum(), m.F[dis, f], m.F[gas, f])
    return out


@pytest.mark.parametrize("suf", ["", "_gas_sulgas"])
def test_todo_comprador_de_s38_compra_eletricidade(mip, suf):
    """Teto do gás: ninguém que compra do S38 fica sem eletricidade (antes, S17, S21–S24 e S27 do RB ficavam)."""
    res = desagregar(mip, _espec(suf), estrito=False)
    w_max = 0.90
    for r in ("RS", "RB"):
        for c, (tot, dis, gas) in _vendas_s38(res, r).items():
            if tot > 1e-9:
                assert dis > 0, (suf, r, c)
                assert gas <= w_max * tot * (1 + 1e-4) + 1e-6, (suf, r, c, gas / tot)


def test_teto_gas_preserva_total_e_grupo():
    import importlib.util

    from mip.caminhos import RAIZ

    spec = importlib.util.spec_from_file_location("r03p", RAIZ / "scripts" / "rodada03_parametros.py")
    r03p = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r03p)
    compra = {"A": 10.0, "B": 100.0, "C": 100.0, "D": 50.0}
    contrib = {"ind": {"A": 12.0, "B": 20.0, "C": 30.0}, "serv": {"D": 48.0}}
    c, presos = r03p.teto_gas(contrib, compra, 0.9)
    tot = lambda k: sum(d.get(k, 0.0) for d in c.values())  # noqa: E731
    assert presos == {"A", "D"}
    assert tot("A") == pytest.approx(9.0) and tot("D") == pytest.approx(45.0)
    assert sum(c["ind"].values()) == pytest.approx(62.0)  # o excedente de A fica no grupo
    assert c["ind"]["B"] / c["ind"]["C"] == pytest.approx((20 + 3 * 20 / 50) / (30 + 3 * 30 / 50))
    assert sum(c["serv → demais (grupo no teto)"].values()) == pytest.approx(3.0)  # grupo inteiro no teto → demais
    assert sum(tot(k) for k in compra) == pytest.approx(110.0)
    with pytest.raises(SystemExit, match="não cabe"):
        r03p.teto_gas({"g": {"A": 50.0}}, {"A": 10.0}, 0.9)


def test_d10_rs_sem_consumo_nao_energetico():
    gc = pd.read_excel(PASTA_PARAMETROS / "quadro_parametros_v02.xlsx", sheet_name="gas_grupos_teto")
    rs = gc[gc["regiao"] == "RS"].set_index("grupo")
    seg = pd.read_csv(PASTA_EXTERNOS / "gas" / "sulgas_segmentos_2019_v01.csv").set_index("segmento")["receita_liquida_rs"]
    assert rs.loc["indústria + cogeração", "participacao_original"] == pytest.approx(
        (seg["Industrial"] + seg["Cogeração"]) / seg.sum())
    lin = pd.read_csv(PASTA_PARAMETROS / "regras_linha_v02.csv")
    fonte = lin[(lin["regiao"] == "RS") & (lin["subsetor"] == "S38_GAS")]["fonte"].iloc[0]
    assert "sem o consumo final não energético" in fonte


def test_consumo_especifico_d8_pet():
    ce = pd.read_csv(PASTA_INTERMEDIARIOS / "ben_2019_consumo_especifico_v02.csv").set_index("subsetor")
    assert ce.loc["S38_PET", "tep_por_mwh"] == pytest.approx((999 + 267 + 137) / 5174)
    assert ce.loc["S38_BIO", "tep_por_mwh"] == pytest.approx((72 + 108 + 254) / 1840)


def test_validacoes_novas(mip):
    e = _espec("")
    e.reequilibrio = dict(e.reequilibrio, importacoes="ajustaveis")
    with pytest.raises(EspecificacaoInvalida, match="importacoes"):
        desagregar(mip, e, estrito=False)
    e = _espec("")
    e.piso_vbp = dict(e.piso_vbp, viabilidade_eta=0.05)
    with pytest.raises(EspecificacaoInvalida, match="viabilidade_eta"):
        desagregar(mip, e, estrito=False)
    e = _espec("")
    e.reequilibrio = {}
    with pytest.raises(EspecificacaoInvalida, match="exige o bloco reequilibrio"):
        desagregar(mip, e, estrito=False)


def test_reequilibrio_nao_mexe_nos_fixos_e_registra_pesos(v02):
    c = v02.checagens.set_index("checagem")
    assert c.loc["reequilibrio_insumos_fixos", "status"] == "OK"
    p = v02.pesos
    apos = p[p["etapa"] == "apos_reequilibrio"]
    assert len(apos) and {"coluna", "primarios_satelite"} <= set(apos["dimensao"])
    eob = apos[(apos["chave"] == "eob") & (apos["regiao"] == "RB")].iloc[0]
    m = v02.mip
    assert eob["S38_GN"] * v02.original.V[IP["eob"], v02.original.indice("RB", "S38")] == pytest.approx(
        m.V[IP["eob"], m.indice("RB", "S38_GN")])
    assert any("reequilíbrio" in x for x in v02.leiame())


def test_variantes_kappa_atuam(mip, v02):
    """As variantes κ (só o piso κ) mudam os VBPs; com a viabilidade ligada, κ = 0.80 não mudaria nada."""
    k = v02.mip.indice("RB", "S38_GN")
    x = {suf: desagregar(mip, _espec(suf), estrito=False).mip.X[k] for suf in ("_k060", "_sem_viabilidade", "_k080")}
    assert x["_k060"] > x["_sem_viabilidade"] > x["_k080"]


def test_longo_publicado_tem_latentes(v02):
    from mip.caminhos import PASTA_RESULTADOS

    caminho = PASTA_RESULTADOS / "rodada03" / "MIP_RS_RB_2019_S38_11sub_v02_longo.csv"
    if not caminho.exists():
        pytest.skip("MIP v02 ainda não exportada (scripts/rodada03_mip.py)")
    m = ler_mip_longo(caminho)
    assert m.coef_latentes is not None and len(m.coef_latentes)
    for s in ("S38_SOL", "S38_PET"):
        a = ModeloLeontief(m).simular_choques({("RS", s): 1.0})
        b = ModeloLeontief(v02.mip).simular_choques({("RS", s): 1.0})
        assert a.dX.sum() == pytest.approx(b.dX.sum()) and a.emissoes.sum() == pytest.approx(b.emissoes.sum())
    with pytest.raises(FileNotFoundError):
        ler_mip_longo(caminho, caminho_coef_latentes=caminho.with_name("nao_existe.csv"))


def test_exportar_grava_latentes_ao_lado(tmp_path, v02):
    v02.exportar(tmp_path / "y.xlsx", tmp_path / "y_longo.csv")
    assert (tmp_path / "y_coef_latentes.csv").exists()
    assert ler_mip_longo(tmp_path / "y_longo.csv").coef_latentes is not None


def test_executor_recusa_entradas_invalidas(tmp_path, mip, v02):
    um = lambda s, v=1.0: pd.DataFrame({"cenario": ["X"], "regiao": ["RS"], "setor": [s], "valor_R$mi": [v]})  # noqa: E731
    with pytest.raises(cen.CenarioInvalido, match="produção zero"):
        cen.resolver_choques(v02.mip, um("S38_NUC"))
    with pytest.raises(cen.CenarioInvalido, match="produção zero"):
        cen.resolver_choques(mip, um("S05"))
    cen.resolver_choques(v02.mip, um("S38_SOL"))  # latente: aceito
    with pytest.raises(cen.CenarioInvalido, match="negativos"):
        cen.resolver_choques(v02.mip, um("S38"), {"S38_DIS": 1.0, "S38_GAS": -0.5})
    with pytest.raises(cen.CenarioInvalido, match="inexistentes"):
        cen.resolver_choques(v02.mip, um("S38"), {"S38_DIS": 0.5, "S38_GAs": 0.5})
    with pytest.raises(cen.CenarioInvalido, match="produção zero"):
        cen.resolver_choques(v02.mip, um("S38"), {"S38_NUC": 1.0})
    csv = tmp_path / "c.csv"
    csv.write_text("cenario,regiao,setor,valor_R$mi\nE1,RS,S38,1000\nE1,RS,S43,\n,RS,S19,500\n", encoding="utf-8")
    with pytest.raises(cen.CenarioInvalido, match="vazia"):
        cen.ler_cenarios(csv)


def test_cli_cenarios_valida_argumentos(tmp_path):
    import importlib.util

    from mip.caminhos import RAIZ

    spec = importlib.util.spec_from_file_location("rc", RAIZ / "scripts" / "rodar_cenarios.py")
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)
    csv = tmp_path / "c.csv"
    csv.write_text("cenario,regiao,setor,valor_R$mi\nE1,RS,S43,1000\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        rc.main(["--cenarios", str(csv), "--mip", "original", "--mip", "original=x.xlsx", "--saida", str(tmp_path / "o.xlsx")])
    with pytest.raises(SystemExit):
        rc.main(["--cenarios", str(csv), "--mip", "original", "--reparticao", "S38_DIS=0.5,,S38_GAS=0.5",
                 "--saida", str(tmp_path / "o.xlsx")])
    rc.main(["--cenarios", str(csv), "--mip", "original", "--reparticao", " S43=0.5, S44=0.5 ",  # espaços são aceitos
             "--saida", str(tmp_path / "o.xlsx")])
    assert (tmp_path / "o.xlsx").exists()



def test_reparticao_explicita_com_a_original(mip, v02):
    """A mesma repartição serve à original (S38 agregado, sem repartir) e à v02 (verificação das correções)."""
    tab = cen.executar_versoes({"original": mip, "v02": v02.mip}, cen.cenarios_da_rodada01(), {"S38_DIS": 0.9, "S38_GAS": 0.1})
    rep = tab["reparticao"]
    e1 = rep[(rep["versao"] == "v02") & (rep["cenario"] == "E1")].set_index("subsetor")["valor_R$mi"]
    assert e1["S38_DIS"] == pytest.approx(900.0) and e1["S38_GAS"] == pytest.approx(100.0)


def test_latentes_com_csv_de_outro_nome(tmp_path, v02):
    from mip.leitura import caminho_coef_latentes_ao_lado

    v02.exportar(tmp_path / "z.xlsx", tmp_path / "z.csv")
    assert caminho_coef_latentes_ao_lado(tmp_path / "z.csv").name == "z_coef_latentes.csv"
    assert caminho_coef_latentes_ao_lado(tmp_path / "z_longo.csv").name == "z_coef_latentes.csv"
    assert ler_mip_longo(tmp_path / "z.csv").coef_latentes is not None


def test_fonte_do_gas_separa_o_transbordo():
    lin = pd.read_csv(PASTA_PARAMETROS / "regras_linha_v02.csv")
    fam = lin[(lin["regiao"] == "RS") & (lin["comprador"] == "FAM") & (lin["subsetor"] == "S38_GAS")]["fonte"].iloc[0]
    assert "grupo 'serviço' inteiro no teto" in fam and "próprio grupo" not in fam
    s21 = lin[(lin["regiao"] == "RS") & (lin["comprador"] == "S21") & (lin["subsetor"] == "S38_GAS")]["fonte"].iloc[0]
    assert "próprio grupo" in s21 and "inteiro no teto" in s21
