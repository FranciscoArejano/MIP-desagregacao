"""Etapa 4 — diagnóstico do S38: valores de referência das instruções."""
import pytest

from mip import diagnostico as diag
from mip import referencia as ref
from mip.leitura import ler_mip_original


@pytest.fixture(scope="module")
def mip():
    return ler_mip_original()


def test_valores_chave_s38(mip):
    obt = diag.valores_chave(mip, "S38")
    for r in ref.DIAGNOSTICO_S38.itertuples(index=False):
        assert obt["RS"][r.item] == pytest.approx(r[1], abs=r.tolerancia), ("RS", r.item)
        assert obt["RB"][r.item] == pytest.approx(r[2], abs=r.tolerancia), ("RB", r.item)


def test_bloco_s38(mip):
    bloco, _ = diag.bloco_intrassetorial(mip, "S38")
    for (a, b), esperado in ref.BLOCO_S38.items():
        valor = bloco.set_index("fluxo (R$ mi)").loc[f"vende S38-{a}", f"compra S38-{b}"]
        assert valor == pytest.approx(esperado, abs=0.05)


def test_estruturas_somam_totais(mip):
    for reg in ("RS", "RB"):
        j = mip.indice(reg, "S38")
        ins = diag.estrutura_insumos(mip, reg, "S38", ref.INSUMOS_ENERGETICOS)
        assert ins["valor (R$ mi)"].sum() == pytest.approx(mip.Z[:, j].sum())
        assert set(ins.loc[ins["insumo_energetico"] == "SIM", "setor_origem"]) == set(ref.INSUMOS_ENERGETICOS)
        ven = diag.estrutura_vendas(mip, reg, "S38")
        assert ven["valor (R$ mi)"].sum() == pytest.approx(mip.X[j])
