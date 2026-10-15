"""Etapa 2 — leitura da MIP e identidades contábeis (valores de referência das instruções)."""
import numpy as np
import pytest

from mip.estrutura import COLUNAS_DF, IDX_DISCREP
from mip.leitura import formato_longo, ler_mip_original
from mip.validacao import (
    celulas_negativas,
    residuo_coluna,
    residuo_linha,
    residuo_total_df,
    residuo_va,
)


@pytest.fixture(scope="module")
def mip():
    return ler_mip_original()


def test_dimensoes_e_rotulos(mip):
    assert mip.n == 136
    assert mip.Z.shape == (136, 136) and mip.F.shape == (136, 11)
    assert list(mip.setores["regiao"][:68]) == ["RS"] * 68
    assert list(mip.setores["regiao"][68:]) == ["RB"] * 68
    assert mip.indice("RS", "S38") == 37  # linha 44 / coluna AP
    assert mip.indice("RB", "S38") == 105  # linha 112 / coluna DF
    assert mip.setores["nome"][37] == "Energia elétrica, gás natural e outras utilidades"


def test_identidade_de_linha(mip):
    assert np.abs(residuo_linha(mip)).max() < 1e-9  # esperado ≈ 7e-10


def test_identidade_de_coluna(mip):
    c = residuo_coluna(mip)
    i = int(np.argmax(np.abs(c)))
    assert (mip.setores["regiao"][i], mip.setores["codigo"][i]) == ("RB", "S40")
    assert c[i] == pytest.approx(0.0095, abs=1e-4)
    # demais: resíduos de arredondamento, pequenos em relação ao VBP
    assert np.max(np.abs(c) / np.where(mip.X > 0, mip.X, 1)) < 1e-7


def test_identidade_va(mip):
    assert np.abs(residuo_va(mip)).max() < 1e-9  # esperado ≈ 1e-10


def test_vbp_igual_total_da_linha(mip):
    assert np.array_equal(mip.X, mip.total_linha)


def test_setores_com_vbp_zero(mip):
    zeros = [f"{r} {c}" for r, c in mip.setores.loc[mip.X == 0, ["regiao", "codigo"]].itertuples(index=False)]
    assert zeros == ["RS S05", "RS S06", "RS S07", "RS S20"]
    for k in np.flatnonzero(mip.X == 0):
        assert not mip.Z[k].any() and not mip.Z[:, k].any() and not mip.F[k].any()


def test_valores_negativos(mip):
    neg = celulas_negativas(mip)
    eu = neg[(neg["bloco"] == "demanda_final") & (neg["coluna"] == COLUNAS_DF["codigo"][IDX_DISCREP])]
    assert len(eu) == 65
    assert eu["valor"].min() == pytest.approx(-5987.45, abs=0.005)
    outros = neg.drop(eu.index)
    assert sorted(zip(outros["linha"], outros["coluna"])) == [
        ("eob", "RB S09"),
        ("eob", "RS S09"),
        ("impostos_producao", "RB S01"),
        ("impostos_producao", "RS S01"),
    ]


def test_totais_das_colunas_de_demanda_final(mip):
    # informativo: diferença pequena entre a soma e o total da linha 156 nas colunas de DF
    assert np.abs(residuo_total_df(mip)).max() < 0.05


def test_formato_longo_reconstroi_z(mip):
    longo = formato_longo(mip)
    z = longo[longo["bloco"] == "Z"]
    assert len(z) == 136 * 136
    assert z["valor"].sum() == pytest.approx(mip.Z.sum())
    rs38 = z[(z["regiao_origem"] == "RS") & (z["setor_origem"] == "S38") & (z["regiao_destino"] == "RS") & (z["setor_ou_coluna_destino"] == "S38")]
    assert rs38["valor"].item() == mip.Z[37, 37]
