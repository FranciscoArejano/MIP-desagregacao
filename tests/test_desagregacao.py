"""Etapa 5 — motor de desagregação: testes obrigatórios T2–T5 e testes complementares.

(T1, hash da planilha original, está em test_t1_hash.py.)
"""
import numpy as np
import pandas as pd
import pytest

from auxiliares import espec_aleatoria, espec_neutra, mip_pequena, participacoes, subsetores
from mip import referencia as ref
from mip.caminhos import PASTA_PARAMETROS
from mip.desagregacao import (
    DesagregacaoInvalida,
    Especificacao,
    EspecificacaoInvalida,
    agregar,
    desagregar,
    ler_especificacao,
    ras,
)
from mip.leitura import ler_mip_original
from mip.modelo import ModeloLeontief

TOL = 1e-6
ARRAYS = ["Z", "F", "X", "total_linha", "V", "S", "V_df", "X_df"]


@pytest.fixture(scope="module")
def mip():
    return ler_mip_original()


@pytest.fixture(scope="module")
def modelo_original(mip):
    return ModeloLeontief(mip)


@pytest.fixture(scope="module")
def res_teste(mip):
    return desagregar(mip, ler_especificacao(PASTA_PARAMETROS / "TESTE_especificacao.yaml"))


def _assert_reagrega(res, mip):
    ag = agregar(res.mip, res.mapa, mip.setores)
    for nome in ARRAYS:
        np.testing.assert_allclose(getattr(ag, nome), getattr(mip, nome), rtol=0, atol=TOL, err_msg=nome)
    assert res.ok, res.checagens[res.checagens["status"] == "FALHA"]


# ---------------------------------------------------------------------------------------------
# T2 — re-agregação exata para qualquer especificação válida
# ---------------------------------------------------------------------------------------------
def test_t2_reagregacao_especificacao_teste(mip, res_teste):
    _assert_reagrega(res_teste, mip)


@pytest.mark.parametrize("semente", range(8))
def test_t2_reagregacao_especificacoes_aleatorias(mip, semente):
    rng = np.random.default_rng(semente)
    espec = espec_aleatoria(rng, mip)
    res = desagregar(mip, espec)
    _assert_reagrega(res, mip)


@pytest.mark.parametrize("regioes", [("RS",), ("RB",), ("RS", "RB")])
def test_t2_reagregacao_regioes_desagregadas(mip, regioes):
    """D2: o motor aceita desagregar só no RS, só no RB ou nas duas regiões."""
    rng = np.random.default_rng(42)
    espec = espec_aleatoria(rng, mip, regioes=regioes)
    res = desagregar(mip, espec)
    _assert_reagrega(res, mip)
    assert res.mip.n == mip.n + len(regioes) * (len(espec.subsetores) - 1)


# ---------------------------------------------------------------------------------------------
# T3 — desagregação neutra reproduz exatamente os 9 cenários
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("K,semente", [(2, 0), (5, 1), (8, 2)])
def test_t3_desagregacao_neutra(mip, modelo_original, K, semente):
    rng = np.random.default_rng(semente)
    res = desagregar(mip, espec_neutra(K, rng))
    _assert_reagrega(res, mip)
    mod = ModeloLeontief(res.mip)
    codigos = list(res.especificacao.subsetores["codigo"])
    for cen in ref.CENARIOS_RS:
        base = modelo_original.simular_choques(ref.choques(cen), cen)
        ch = ref.choques(cen)
        v = ch.pop(("RS", "S38"))
        w = rng.dirichlet(np.ones(K)) * (rng.random(K) < 0.7)  # repartição arbitrária (pode zerar subsetores)
        w = w / w.sum() if w.sum() > 0 else np.eye(K)[0]
        for c, wk in zip(codigos, w):
            ch[("RS", c)] = v * wk
        nova = mod.simular_choques(ch, cen)
        rb, rn = base.resumo(), nova.resumo()
        for ind in ["dX_total", "dX_RS", "dX_RB", "co2e_total", "co2e_RS", "co2e_RB",
                    "co2e_diretas", "co2e_indiretas", "IC", "pct_indiretas"]:
            assert rn[ind] == pytest.approx(rb[ind], abs=TOL), (cen, ind)


# ---------------------------------------------------------------------------------------------
# T4 — subsetor latente num exemplo de 3 setores (multiplicador calculado à mão)
# ---------------------------------------------------------------------------------------------
def test_t4_subsetor_latente():
    """S03 vira S03_A (participação 1) + S03_B (latente, produção zero, coluna dada).

    Coluna de coeficientes de S03_B: a = [S01: 0.063, S02: 0.063, S03_A: 0.05, S03_B: 0]; e_B = 2.
    Ninguém compra de S03_B (produção zero), então um choque unitário em S03_B dá ΔX_B = 1 e,
    para os demais, ΔX = (I − A₃)⁻¹ · a, com A₃ a matriz original:
      bloco S01/S02: [[0.8, −0.1], [−0.1, 0.8]]⁻¹ = (1/0.63)·[[0.8, 0.1], [0.1, 0.8]]
      ΔX_S01 = (0.8·0.063 + 0.1·0.063)/0.63 = 0.09;  ΔX_S02 = 0.09;  ΔX_S03_A = 0.05/(1 − 0.5) = 0.1
    Multiplicador de produção = 0.09 + 0.09 + 0.1 + 1 = 1.28.
    Emissões (e = CO2e/X = [0.1, 0.2, 0.6] e e_B = 2): 0.1·0.09 + 0.2·0.09 + 0.6·0.1 + 2·1 = 2.087.
    """
    mip = mip_pequena()
    subs = pd.DataFrame({"codigo": ["S03_A", "S03_B"], "nome": ["a", "b (latente)"], "tipo": ["rede", "geracao"]})
    part = participacoes(subs, {"RS": np.array([1.0, 0.0])})
    lat = pd.DataFrame(
        [
            ("RS", "S03_B", "setor", "RS", "S01", 0.063, "à mão"),
            ("RS", "S03_B", "setor", "RS", "S02", 0.063, "à mão"),
            ("RS", "S03_B", "setor", "RS", "S03_A", 0.05, "à mão"),
            ("RS", "S03_B", "satelite", "", "co2e", 2.0, "à mão"),
        ],
        columns=["regiao", "subsetor", "tipo_linha", "regiao_linha", "codigo_linha", "coeficiente", "fonte"],
    )
    espec = Especificacao(nome="T4", setor_alvo="S03", regioes=["RS"], subsetores=subs, participacoes=part,
                          coef_latentes=lat)
    res = desagregar(mip, espec)
    m2 = res.mip
    # fluxos-base inalterados: S03_A = S03 original; S03_B zerado
    np.testing.assert_allclose(m2.Z[:3, :3], mip.Z, atol=1e-12)
    np.testing.assert_allclose(m2.X, [100, 100, 50, 0], atol=1e-12)
    assert not m2.Z[3].any() and not m2.Z[:, 3].any() and not m2.F[3].any() and not m2.S[:, 3].any()
    _assert_reagrega(res, mip)
    # multiplicador do subsetor latente
    mod = ModeloLeontief(m2)
    r = mod.simular_choques({("RS", "S03_B"): 1.0})
    np.testing.assert_allclose(r.dX, [0.09, 0.09, 0.1, 1.0], atol=1e-12)
    assert r.dX.sum() == pytest.approx(1.28, abs=1e-12)
    assert r.emissoes.sum() == pytest.approx(2.087, abs=1e-12)
    # os multiplicadores dos setores existentes não mudam
    base = ModeloLeontief(mip)
    np.testing.assert_allclose(mod.L[:3, :3], base.L, atol=1e-12)


# ---------------------------------------------------------------------------------------------
# T5 — geração vende somente para a rede
# ---------------------------------------------------------------------------------------------
def test_t5_geracao_vende_para_rede(mip, res_teste):
    m2, mapa = res_teste.mip, res_teste.mapa
    tipos = dict(zip(res_teste.especificacao.subsetores["codigo"], res_teste.especificacao.subsetores["tipo"]))
    sub = mapa[mapa["desagregado"]]
    bloco = sub["indice_novo"].to_numpy()
    fora = np.setdiff1d(np.arange(m2.n), bloco)
    ger = sub[sub["codigo_novo"].map(tipos) == "geracao"]
    rede = sub[sub["codigo_novo"].map(tipos) == "rede"]
    for r in ("RS", "RB"):
        g = ger[ger["regiao"] == r]["indice_novo"].to_numpy()
        # soma das vendas da geração = vendas originais do S38 da região ao S38 das duas regiões
        orig = sum(mip.Z[mip.indice(r, "S38"), mip.indice(r2, "S38")] for r2 in ("RS", "RB"))
        assert m2.Z[g].sum() + m2.F[g].sum() == pytest.approx(orig, abs=TOL)
        # não vendem a nenhum outro setor nem à demanda final
        assert np.abs(m2.Z[np.ix_(g, fora)]).max() == 0
        assert np.abs(m2.F[g]).max() == 0
        # dentro do bloco, vendem só à rede das duas regiões, respeitando os quatro fluxos RS↔RB
        nao_rede = np.setdiff1d(bloco, rede["indice_novo"])
        assert np.abs(m2.Z[np.ix_(g, nao_rede)]).max() == 0
        for r2 in ("RS", "RB"):
            j = rede[rede["regiao"] == r2]["indice_novo"].item()
            esperado = mip.Z[mip.indice(r, "S38"), mip.indice(r2, "S38")]
            assert m2.Z[g, j].sum() == pytest.approx(esperado, abs=TOL)
            # a rede compra toda essa energia: o bloco r→r2 inteiro está na coluna da rede
            assert m2.Z[np.ix_(sub[sub["regiao"] == r]["indice_novo"], [j])].sum() == pytest.approx(esperado, abs=TOL)
        # cada gerador fecha a linha (VBP = vendas à rede)
        np.testing.assert_allclose(m2.Z[g].sum(axis=1), m2.X[g], atol=TOL)


# ---------------------------------------------------------------------------------------------
# Testes complementares
# ---------------------------------------------------------------------------------------------
def test_ras_converge_e_respeita_celulas_fixas():
    M0 = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    fixas = np.zeros_like(M0, dtype=bool)
    fixas[0, 0] = True
    alvo_l = np.array([8.0, 16.0])
    alvo_c = np.array([6.0, 8.0, 10.0])
    M, info = ras(M0, alvo_l, alvo_c, fixas, tol=1e-10)
    assert info.necessario and info.convergiu and info.iteracoes > 0
    np.testing.assert_allclose(M.sum(axis=1), alvo_l, atol=1e-9)
    np.testing.assert_allclose(M.sum(axis=0), alvo_c, atol=1e-9)
    assert M[0, 0] == 1.0


def test_ras_inviavel_reporta_nao_convergencia():
    M0 = np.array([[1.0, 0.0], [0.0, 1.0]])
    M, info = ras(M0, np.array([2.0, 1.0]), np.array([1.0, 2.0]), max_iter=50)
    assert info.necessario and not info.convergiu and info.iteracoes == 50


def test_ras_nao_necessario(mip):
    res = desagregar(mip, espec_neutra(3, np.random.default_rng(0)))
    assert not res.info_ras["necessario"].any()


def test_eob_negativo_e_sinalizado_nao_corrigido(mip):
    rng = np.random.default_rng(3)
    espec = espec_neutra(3, rng)
    espec.participacoes.loc[espec.participacoes["regiao"] == "RB", "participacao"] = [0.01, 0.5, 0.49]
    # todo o petróleo e gás (S05) comprado pelo S38-RB vai para o subsetor pequeno → EOB negativo
    espec.regras_coluna = pd.DataFrame(
        [("RB", "S05", "*", "fixa", espec.subsetores["codigo"][0], 1.0, "teste", )],
        columns=["regiao", "fornecedor", "regiao_fornecedor", "regra", "subsetor", "valor", "fonte"],
    )
    espec.__post_init__()
    res = desagregar(mip, espec)  # estrito=True não interrompe por ALERTA
    al = res.checagens.set_index("checagem").loc["EOB_nao_negativo_subsetores"]
    assert al["status"] == "ALERTA" and al["valor"] < 0
    assert "RB_S38_00" in al["detalhe"]
    _assert_reagrega(res, mip)  # mesmo com EOB negativo, os totais continuam preservados


def test_especificacao_invalida(mip):
    rng = np.random.default_rng(0)
    e = espec_neutra(3, rng)
    e.participacoes.loc[0, "participacao"] += 0.1
    with pytest.raises(EspecificacaoInvalida, match="somam"):
        desagregar(mip, e)
    # regra fixa que dá valor a subsetor com produção zero
    e = espec_neutra(3, rng)
    e.participacoes.loc[e.participacoes["regiao"] == "RS", "participacao"] = [0.0, 0.6, 0.4]
    e.regras_coluna = pd.DataFrame(
        [("RS", "S04", "*", "fixa", "S38_00", 1.0, "t")],
        columns=["regiao", "fornecedor", "regiao_fornecedor", "regra", "subsetor", "valor", "fonte"],
    )
    e.__post_init__()
    with pytest.raises(EspecificacaoInvalida, match="produção zero"):
        desagregar(mip, e)
    # regras ambíguas (mesma especificidade, chaves diferentes)
    e = espec_neutra(3, rng)
    e.regras_primarios = pd.DataFrame(
        [("RS", "*", "proporcional_vbp", "", np.nan, "t"), ("*", "co2e", "proporcional_vbp", "", np.nan, "t")],
        columns=["regiao", "item", "regra", "subsetor", "valor", "fonte"],
    )
    e.regras_primarios.loc[1, "regiao"] = "*"
    e.__post_init__()
    desagregar(mip, e)  # item específico (2) vence região específica (1): sem ambiguidade
    e.regras_primarios = pd.DataFrame(
        [("RS", "co2e", "proporcional_vbp", "", np.nan, "t"), ("RS", "co2e", "fixa", "S38_00", 1.0, "t")],
        columns=["regiao", "item", "regra", "subsetor", "valor", "fonte"],
    )
    e.__post_init__()
    with pytest.raises(EspecificacaoInvalida, match="mais de uma regra"):
        desagregar(mip, e)


def test_geracao_vende_para_rede_inconsistente_da_erro_claro(mip):
    """Participações da geração abaixo da âncora + geração sem vendas fora do bloco: erro explicativo."""
    subs = subsetores(3, ["geracao", "rede", "gas_utilidades"])
    part = participacoes(subs, {"RS": np.array([0.1, 0.8, 0.1]), "RB": np.array([0.1, 0.8, 0.1])})
    regras_linha = pd.DataFrame(
        [("*", "*", "*", "somente_rede_e_gas", "", np.nan, False, "t")],
        columns=["regiao", "comprador", "regiao_comprador", "regra", "subsetor", "valor", "fixar_no_ras", "fonte"],
    )
    e = Especificacao(nome="x", setor_alvo="S38", regioes=["RS", "RB"], subsetores=subs, participacoes=part,
                      bloco="geracao_vende_para_rede", regras_linha=regras_linha)
    with pytest.raises(EspecificacaoInvalida, match="ancora_bloco"):
        desagregar(mip, e)
    # com a âncora, a mesma especificação fecha
    e.modo_vbp = "ancora_bloco"
    res = desagregar(mip, e)
    _assert_reagrega(res, mip)
    for r in ("RS", "RB"):
        i = mip.indice(r, "S38")
        ancora = sum(mip.Z[i, mip.indice(r2, "S38")] for r2 in ("RS", "RB")) / mip.X[i]
        s = res.mapa[(res.mapa["regiao"] == r) & res.mapa["desagregado"]]["participacao_vbp"].to_numpy()
        assert s[0] == pytest.approx(ancora)


def test_latente_na_mip_real(res_teste):
    """Subsetor latente da especificação de teste (S38_SOL no RS): choque unitário dá ΔX próprio = 1."""
    m2 = res_teste.mip
    j = m2.indice("RS", "S38_SOL")
    assert m2.X[j] == 0
    mod = ModeloLeontief(m2)
    r = mod.simular_choques({("RS", "S38_SOL"): 1.0})
    assert r.dX[j] == pytest.approx(1.0)
    assert mod.A[m2.indice("RB", "S30"), j] == pytest.approx(0.08)
    assert r.dX.sum() > 1.0


def test_desagregacao_estrita_levanta_em_falha(mip, monkeypatch):
    import mip.desagregacao as d

    def verificar_falso(res):
        return pd.DataFrame([("x", "FALHA", 1.0, 0.0, "forçado")],
                            columns=["checagem", "status", "valor", "tolerancia", "detalhe"])

    monkeypatch.setattr(d, "verificar", verificar_falso)
    with pytest.raises(DesagregacaoInvalida):
        d.desagregar(mip, espec_neutra(2, np.random.default_rng(0)))
