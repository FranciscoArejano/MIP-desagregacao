"""Rodada 02b — T2 (re-agregação exata) e checagens com a especificação REAL v01 e as variantes.

Os parâmetros são gerados por scripts/rodada02_parametros.py (parametros/especificacao_v01*.yaml). Se ainda não
existirem, os testes são pulados (não falham): rode antes scripts/rodada02.py e scripts/rodada02_parametros.py.
"""
import numpy as np
import pytest

from mip.caminhos import PASTA_PARAMETROS
from mip.desagregacao import agregar, desagregar, ler_especificacao
from mip.estrutura import ITENS_SATELITE
from mip.leitura import ler_mip_original

TOL = 1e-6
ARRAYS = ["Z", "F", "X", "total_linha", "V", "V_df", "X_df"]
VARIANTES = ["", "_P2", "_E2", "_E3"]


@pytest.fixture(scope="module")
def mip():
    return ler_mip_original()


def _espec(suf):
    caminho = PASTA_PARAMETROS / f"especificacao_v01{suf}.yaml"
    if not caminho.exists():
        pytest.skip(f"{caminho.name} ainda não foi gerado (scripts/rodada02_parametros.py)")
    return ler_especificacao(caminho)


@pytest.mark.parametrize("suf", VARIANTES)
def test_t2_reagregacao_especificacao_real(mip, suf):
    res = desagregar(mip, _espec(suf))
    assert res.mip.n == 156
    ag = agregar(res.mip, res.mapa, mip.setores)
    for nome in ARRAYS:
        np.testing.assert_allclose(getattr(ag, nome), getattr(mip, nome), rtol=0, atol=TOL, err_msg=f"{suf}: {nome}")
    if suf != "_E3":  # E3 não preserva o total de CO2e da base (por construção)
        np.testing.assert_allclose(ag.S, mip.S, rtol=0, atol=TOL)
    else:
        outros = [k for k, it in enumerate(ITENS_SATELITE) if it != "co2e"]
        np.testing.assert_allclose(ag.S[outros], mip.S[outros], rtol=0, atol=TOL)
    assert res.ok, res.checagens[res.checagens["status"] == "FALHA"]


def test_especificacao_real_vbp_positivo_e_geracao_so_no_bloco(mip):
    res = desagregar(mip, _espec(""))
    m = res.mapa[res.mapa["desagregado"]]
    for r in ("RS", "RB"):
        sub = m[m["regiao"] == r]
        X = res.mip.X[sub["indice_novo"].to_numpy()]
        assert (X >= 0).all()
        for cod in ("S38_TRA", "S38_DIS", "S38_GAS"):
            assert res.mip.X[res.mip.indice(r, cod)] > 0, f"{r} {cod}"
    bloco = m["indice_novo"].to_numpy()
    fora = np.setdiff1d(np.arange(res.mip.n), bloco)
    for _, x in m.iterrows():
        if x["codigo_novo"] not in ("S38_DIS", "S38_GAS"):
            i = x["indice_novo"]
            assert abs(res.mip.Z[i, fora]).sum() < 1e-6 and abs(res.mip.F[i]).sum() < 1e-6, x["codigo_novo"]
