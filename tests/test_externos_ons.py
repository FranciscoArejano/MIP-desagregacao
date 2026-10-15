"""ONS (Seção 5.1): tratamento da geração por usina. Usa dados sintéticos; se o bruto real estiver
em dados/externos/brutos/ons/ (fora do git), confere também os valores de referência."""
import numpy as np
import pandas as pd
import pytest

from mip.caminhos import PASTA_EXTERNOS
from mip.externos import ons

BRUTO = PASTA_EXTERNOS / "brutos" / "ons" / "GERACAO_USINA-2_2019.parquet"
RECLASS = PASTA_EXTERNOS / "ons" / "reclassificacao_usinas_v01.csv"


def _sintetico():
    linhas = []
    for usina, ceg, uf, comb, mw in [
        ("Hidro RS", "UHE.PH.RS.000001-1.01", "RS", "Hidráulica", 10.0),
        ("Canoas", "UTE.GN.RS.028038-0.01", "RS", "Óleo Diesel", 2.0),
        ("Itaipu 50Hz", "UHE.PH.PR.000002-2.01", "I", "Hidráulica", 5.0),
        ("Residuo X", "UTE.OF.ES.123456-7.01", "ES", "Resíduos Industriais", 3.0),
        ("Eol RB", "-", "BA", "Eólica", 4.0),
    ]:
        for h in range(3):
            linhas.append((pd.Timestamp("2019-01-01") + pd.Timedelta(hours=h), uf, "TIPO I", comb, usina, ceg,
                           None if (usina == "Eol RB" and h == 2) else mw))
    df = pd.DataFrame(linhas, columns=ons.COLUNAS)
    df["val_geracao"] = pd.to_numeric(df["val_geracao"])
    return df


def test_nucleo_ceg():
    assert ons.nucleo_ceg("UTE.GN.RS.028038-0.01") == "028038"
    assert ons.nucleo_ceg("-") is None and ons.nucleo_ceg(None) is None and ons.nucleo_ceg(np.nan) is None


def test_regioes_subsetores_e_reclassificacao():
    reclass = pd.DataFrame([("Canoas", "RS", "", "S38_GN", "gás natural pelo CEG", "teste")],
                           columns=["nom_usina", "id_estado", "ceg", "subsetor", "justificativa", "fonte"])
    u = ons.geracao_por_usina(_sintetico(), reclass)
    g = u.set_index("nom_usina")
    assert g.loc["Hidro RS", "regiao"] == "RS" and g.loc["Hidro RS", "subsetor"] == "S38_HID"
    assert g.loc["Hidro RS", "gwh"] == pytest.approx(0.030)  # 3 h × 10 MWmed = 30 MWh
    assert g.loc["Canoas", "subsetor"] == "S38_GN" and g.loc["Canoas", "regra"].startswith("reclassificação")
    assert g.loc["Itaipu 50Hz", "regiao"] == "IMPORTACAO"
    assert g.loc["Residuo X", "subsetor"] == ons.PENDENTE  # sem SIGA: fica pendente, nada é suposto
    assert g.loc["Eol RB", "gwh"] == pytest.approx(0.008)  # hora sem valor conta como zero
    assert u.attrs["horas_com_valor_nulo"] == 1
    tab = ons.geracao_por_regiao_subsetor(u).set_index("regiao")
    assert tab.loc["RB", "PENDENTE"] == pytest.approx(0.009)


def test_siga_classifica_residuos_industriais():
    siga = pd.DataFrame({"nucleo_ceg": ["123456"], "subsetor": ["S38_CAR"], "nome": ["Residuo X"],
                         "regra": ["teste"], "fonte_dsc": ["Outros Fósseis"], "fonte_nom": ["Gás de Alto Forno"]})
    u = ons.geracao_por_usina(_sintetico(), None, siga)
    assert u.set_index("nom_usina").loc["Residuo X", "subsetor"] == "S38_CAR"


def test_reclassificacao_de_usina_inexistente_da_erro():
    reclass = pd.DataFrame([("Nao Existe", "RS", "", "S38_GN", "x", "x")],
                           columns=["nom_usina", "id_estado", "ceg", "subsetor", "justificativa", "fonte"])
    with pytest.raises(ValueError, match="não encontradas"):
        ons.geracao_por_usina(_sintetico(), reclass)


@pytest.mark.skipif(not BRUTO.exists(), reason="bruto do ONS fora do git (rode scripts/rodada02_coleta.py)")
def test_referencias_secao_5_1_com_o_arquivo_real():
    u = ons.geracao_por_usina(ons.ler_ons(BRUTO), ons.ler_reclassificacao(RECLASS))
    comp = ons.comparar_com_referencia(u)
    assert comp["confere"].all(), comp[~comp["confere"]]
