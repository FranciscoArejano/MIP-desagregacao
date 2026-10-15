"""Etapa 3 — reprodução dos resultados de referência (9 cenários + top-10 do R1)."""
import numpy as np
import pandas as pd
import pytest

from mip import referencia as ref
from mip.leitura import ler_mip_original
from mip.modelo import ModeloLeontief, coeficientes_tecnicos, inversa_leontief, ranking_setorial


@pytest.fixture(scope="module")
def modelo():
    return ModeloLeontief(ler_mip_original())


@pytest.fixture(scope="module")
def resultados(modelo):
    return {c: modelo.simular_choques(ref.choques(c), c) for c in ref.CENARIOS_RS}


@pytest.mark.parametrize("cenario", list(ref.CENARIOS_RS))
def test_cenario_confere_com_referencia(resultados, cenario):
    obtido = resultados[cenario].resumo()
    esperado = ref.ESPERADO.set_index("cenario").loc[cenario]
    for ind, tol in ref.TOLERANCIAS.items():
        assert obtido[ind] == pytest.approx(esperado[ind], abs=tol), ind


def test_choques_somam_1_bilhao():
    for c, d in ref.CENARIOS_RS.items():
        assert sum(d.values()) == pytest.approx(1000.0), c


def test_top10_r1(resultados):
    top = ranking_setorial(resultados["R1"], 10)
    exp = ref.TOP10_R1
    assert list(top["regiao"]) == list(exp["regiao"])
    assert list(top["codigo"]) == list(exp["codigo"])
    np.testing.assert_allclose(top["dX (R$ mi)"], exp["dX"], atol=0.05)
    np.testing.assert_allclose(top["CO2e induzido (t)"], exp["co2e"], atol=0.05)
    np.testing.assert_allclose(top["% do CO2e total"], exp["pct_total"], atol=0.05)


def test_propriedades_de_l(modelo):
    assert modelo.L.min() >= -1e-12
    assert np.diag(modelo.L).min() >= 1 - 1e-12


def test_coluna_zero_onde_x_zero():
    Z = np.array([[1.0, 0.0], [2.0, 0.0]])
    X = np.array([10.0, 0.0])
    A = coeficientes_tecnicos(Z, X)
    assert np.allclose(A, [[0.1, 0.0], [0.2, 0.0]])
    assert np.allclose(inversa_leontief(A) @ (np.eye(2) - A), np.eye(2))


def test_peso_s38_nas_emissoes(resultados, modelo):
    i_rs = modelo.mip.indice("RS", "S38")
    i_rb = modelo.mip.indice("RB", "S38")
    for c, esperado in ref.PESO_S38_CENARIOS.items():
        em = resultados[c].emissoes
        assert 100 * (em[i_rs] + em[i_rb]) / em.sum() == pytest.approx(esperado, abs=0.05), c
