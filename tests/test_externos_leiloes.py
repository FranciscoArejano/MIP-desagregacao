"""Seção 5.4 — preços médios por fonte (leilões da ANEEL + IPCA): testes com dados SINTÉTICOS.

Nenhum número aqui é dado real: índices, preços e energias foram escolhidos para permitir o
cálculo à mão. Os leitores ainda não foram validados com os arquivos reais (rede bloqueada).
"""
import json
import warnings

import numpy as np
import pandas as pd
import pytest

from mip.externos.leiloes import (
    PRECO_NUCLEAR_2019,
    REFERENCIA_IPCA_MEDIA_2019,
    REFERENCIA_PRECOS,
    ResultadoPrecos,
    acrescentar_nuclear,
    comparar_com_referencia,
    ler_ipca_sidra,
    ler_leiloes,
    mapear_fonte_leilao,
    media_indice_ano,
    precos_medios_2019,
)

TOL = 1e-9

# --------------------------------------------------------------------------------------------
# Dados sintéticos
# --------------------------------------------------------------------------------------------
# IPCA fictício: 2019 = 100, 101, ..., 111 (média 105.5); jun/2018 = 50; dez/2018 = 95;
# demais meses de 2018 = 90.
MEDIA_2019 = 105.5


def indices_sinteticos() -> dict[str, float]:
    ind = {f"2018{m:02d}": 90.0 for m in range(1, 13)}
    ind["201806"] = 50.0
    ind["201812"] = 95.0
    ind.update({f"2019{m:02d}": 99.0 + m for m in range(1, 13)})
    return ind


def ipca_df() -> pd.DataFrame:
    ind = indices_sinteticos()
    return pd.DataFrame({"mes": list(ind), "indice": list(ind.values())})


CABECALHO_SIDRA = {
    "NC": "Nível Territorial (Código)",
    "NN": "Nível Territorial",
    "MC": "Unidade de Medida (Código)",
    "MN": "Unidade de Medida",
    "V": "Valor",
    "D1C": "Brasil (Código)",
    "D1N": "Brasil",
    "D2C": "Mês (Código)",
    "D2N": "Mês",
    "D3C": "Variável (Código)",
    "D3N": "Variável",
}
NOMES_MES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
             "setembro", "outubro", "novembro", "dezembro"]


def registro_sidra(codigo_mes: str, valor: str, variavel: str = "2266") -> dict:
    return {
        "NC": "1", "NN": "Brasil", "MC": "30", "MN": "Número-índice", "V": valor,
        "D1C": "1", "D1N": "Brasil",
        "D2C": codigo_mes, "D2N": f"{NOMES_MES[int(codigo_mes[4:]) - 1]} {codigo_mes[:4]}",
        "D3C": variavel, "D3N": "IPCA - Número-índice (base: dezembro de 1993 = 100)",
    }


def lista_sidra() -> list[dict]:
    regs = [CABECALHO_SIDRA]
    regs += [registro_sidra(m, f"{v:.2f}") for m, v in indices_sinteticos().items()]
    # outra variável (deve ser filtrada) e um mês sem valor ('...')
    regs.append(registro_sidra("201901", "0.32", variavel="63"))
    regs.append(registro_sidra("202001", "..."))
    return regs


def leiloes_df() -> pd.DataFrame:
    """Leilões sintéticos; valores esperados calculados à mão nos testes."""
    return pd.DataFrame(
        [
            # data, fonte, preço (R$/MWh), energia (MWmed)
            ("2018-06-15", "Hidrelétrica", 100.0, 10.0),      # 100 × 105.5/50 = 211
            ("2018-12-10", "PCH", 95.0, 30.0),                # 95 × 105.5/95 = 105.5
            ("2018-06-01", "Eólica", 80.0, 5.0),              # 80 × 2.11 = 168.8
            ("2018-12-31", "Biomassa - Bagaço", 190.0, 2.0),  # 190 × 105.5/95 = 211 (no corte)
            ("2019-01-15", "Eólica", 999.0, 99.0),            # após o corte
            ("2018-06-20", "Gás Natural", 0.0, 50.0),         # preço não positivo
            ("2018-06-20", "Solar", 300.0, np.nan),           # energia ausente
            ("2018-06-20", "Termelétrica", 100.0, 7.0),       # fonte não mapeada
            (None, "Carvão", 200.0, 4.0),                     # sem data
        ],
        columns=["data_leilao", "fonte_energia", "preco_rs_mwh", "energia_mwmed"],
    ).assign(data_leilao=lambda d: pd.to_datetime(d["data_leilao"]))


# --------------------------------------------------------------------------------------------
# Mapeamento da fonte
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "dsc, esperado",
    [
        ("Hidrelétrica", "S38_HID"),
        ("HIDRÁULICA", "S38_HID"),
        ("  hidro  ", "S38_HID"),
        ("PCH", "S38_HID"),
        ("cgh", "S38_HID"),
        ("UHE", "S38_HID"),
        ("Eólica", "S38_EOL"),
        ("EOLICA", "S38_EOL"),
        ("Solar", "S38_SOL"),
        ("Solar Fotovoltaica", "S38_SOL"),
        ("Fotovoltaica", "S38_SOL"),
        ("Biomassa", "S38_BIO"),
        ("Biomassa - Bagaço de Cana", "S38_BIO"),
        ("Bagaço de cana", "S38_BIO"),
        ("Resíduos Sólidos Urbanos", "S38_BIO"),
        ("Biogás", "S38_BIO"),           # contém "gás", mas é BIO
        ("Biodiesel", "S38_BIO"),        # contém "diesel", mas é BIO
        ("Carvão Mineral", "S38_CAR"),
        ("CARVAO", "S38_CAR"),
        ("Gás Natural", "S38_GN"),
        ("Gás", "S38_GN"),
        ("GNL", "S38_GN"),
        ("Gás Natural Liquefeito", "S38_GN"),
        ("Óleo Combustível", "S38_PET"),
        ("Óleo Diesel", "S38_PET"),
        ("oleo diesel", "S38_PET"),
        ("Diesel", "S38_PET"),
        ("Nuclear", "S38_NUC"),
        ("Termelétrica", None),
        ("Eólica + Solar", None),         # híbrida: ambígua, fica sem mapa
        ("Hidrogênio", None),
        ("", None),
        (None, None),
        (float("nan"), None),
    ],
)
def test_mapear_fonte_leilao(dsc, esperado):
    assert mapear_fonte_leilao(dsc) == esperado


# --------------------------------------------------------------------------------------------
# Leitura do CSV da ANEEL
# --------------------------------------------------------------------------------------------
CSV_LATIN1 = (
    "DatLeilao;DscFonteEnergia;VlrPrecoLeilao;VlrEnergiaVendida;NomLeilao\n"
    "15/06/2018;Hidrelétrica;1.000,50;1.234,5;Leilão A-6\n"
    "2018-12-10 00:00:00;PCH;95,00;30;Leilão A-4\n"
    "31/12/2018 14:30;Biomassa - Bagaço de Cana;190;2,0;Leilão A-6\n"
    ";;;;\n"
    "15/01/2019;Eólica;80,0;5;Leilão A-4 2019\n"
    "xx/yy;Solar;-;12,5;Leilão A-3\n"
)


def test_ler_leiloes_latin1_decimal_virgula_milhar(tmp_path):
    caminho = tmp_path / "leiloes.csv"
    caminho.write_bytes(CSV_LATIN1.encode("latin-1"))
    df = ler_leiloes(caminho)

    assert list(df.columns) == ["data_leilao", "fonte_energia", "preco_rs_mwh", "energia_mwmed"]
    assert len(df) == 5  # a linha vazia é ignorada
    assert df.attrs["encoding"] in ("cp1252", "latin-1")
    assert df.attrs["separador"] == ";"
    assert df.attrs["decimal"] == ","
    # acentos decodificados corretamente
    assert df["fonte_energia"].tolist() == [
        "Hidrelétrica", "PCH", "Biomassa - Bagaço de Cana", "Eólica", "Solar"
    ]
    # decimal vírgula com milhar
    assert df["preco_rs_mwh"].iloc[0] == pytest.approx(1000.5)
    assert df["energia_mwmed"].iloc[0] == pytest.approx(1234.5)
    assert df["preco_rs_mwh"].iloc[1] == pytest.approx(95.0)
    assert df["energia_mwmed"].iloc[2] == pytest.approx(2.0)
    assert np.isnan(df["preco_rs_mwh"].iloc[4])  # '-' → ausente
    # datas em vários formatos; a hora é descartada
    assert pd.api.types.is_datetime64_any_dtype(df["data_leilao"])
    assert df["data_leilao"].iloc[0] == pd.Timestamp("2018-06-15")
    assert df["data_leilao"].iloc[1] == pd.Timestamp("2018-12-10")
    assert df["data_leilao"].iloc[2] == pd.Timestamp("2018-12-31")
    assert pd.isna(df["data_leilao"].iloc[4])
    assert df.attrs["datas_invalidas"] == 1


def test_ler_leiloes_manter_colunas(tmp_path):
    caminho = tmp_path / "leiloes.csv"
    caminho.write_bytes(CSV_LATIN1.encode("latin-1"))
    df = ler_leiloes(caminho, manter_colunas=True)
    assert df["NomLeilao"].iloc[0] == "Leilão A-6"
    assert df["linha_arquivo"].tolist() == [2, 3, 4, 6, 7]


def test_ler_leiloes_utf8_bom_nomes_de_coluna_variantes(tmp_path):
    texto = (
        " datleilao ; DSCFONTEENERGIA;Vlr Preço Leilão ;vlr_energia_vendida\n"
        "2018-06-15;Eólica;98,5;10\n"
        "2018-06-16;Gás Natural;1.234.567,8;2.500\n"
    )
    caminho = tmp_path / "leiloes_utf8.csv"
    caminho.write_bytes(texto.encode("utf-8-sig"))
    df = ler_leiloes(caminho)
    assert df.attrs["encoding"] == "utf-8-sig"
    assert df["fonte_energia"].tolist() == ["Eólica", "Gás Natural"]
    assert df["preco_rs_mwh"].tolist() == pytest.approx([98.5, 1234567.8])
    assert df["energia_mwmed"].tolist() == pytest.approx([10.0, 2500.0])


def test_ler_leiloes_ponto_decimal_e_separador_virgula(tmp_path):
    texto = (
        "DatLeilao,DscFonteEnergia,VlrPrecoLeilao,VlrEnergiaVendida\n"
        '2018-06-15,"Hidrelétrica",166.40,10\n'
    )
    caminho = tmp_path / "leiloes_ponto.csv"
    caminho.write_text(texto, encoding="utf-8")
    df = ler_leiloes(caminho)
    assert df.attrs["separador"] == ","
    assert df.attrs["decimal"] == "."
    assert df["preco_rs_mwh"].iloc[0] == pytest.approx(166.40)


def test_ler_leiloes_milhar_sem_virgula_avisa(tmp_path):
    texto = "DatLeilao;DscFonteEnergia;VlrPrecoLeilao;VlrEnergiaVendida\n2018-06-15;Eólica;1.234;10\n"
    caminho = tmp_path / "ambiguo.csv"
    caminho.write_text(texto, encoding="utf-8")
    with pytest.warns(UserWarning, match="ambíguos"):
        ler_leiloes(caminho)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        df = ler_leiloes(caminho, decimal=",")
    assert df["preco_rs_mwh"].iloc[0] == pytest.approx(1234.0)


def test_ler_leiloes_coluna_faltando(tmp_path):
    caminho = tmp_path / "ruim.csv"
    caminho.write_text("DatLeilao;DscFonteEnergia;VlrPrecoLeilao\n2018-06-15;Eólica;10\n", encoding="utf-8")
    with pytest.raises(ValueError, match="VlrEnergiaVendida") as exc:
        ler_leiloes(caminho)
    assert "Colunas disponíveis" in str(exc.value)
    assert "DscFonteEnergia" in str(exc.value)


# --------------------------------------------------------------------------------------------
# Leitura do IPCA (SIDRA)
# --------------------------------------------------------------------------------------------
def test_ler_ipca_sidra_lista_com_cabecalho():
    df = ler_ipca_sidra(lista_sidra())
    assert list(df.columns) == ["mes", "indice"]
    assert isinstance(df["mes"].dtype, pd.PeriodDtype)
    assert len(df) == 25  # 24 meses de 2018–2019 + jan/2020 sem valor; variável 63 filtrada
    assert df["mes"].is_monotonic_increasing
    linha = df.set_index("mes")["indice"]
    assert linha[pd.Period("2018-06", freq="M")] == pytest.approx(50.0)
    assert linha[pd.Period("2019-01", freq="M")] == pytest.approx(100.0)  # não 0.32 (var. 63)
    assert np.isnan(linha[pd.Period("2020-01", freq="M")])  # '...' → NaN


def test_ler_ipca_sidra_arquivo_json(tmp_path):
    caminho = tmp_path / "ipca.json"
    caminho.write_text(json.dumps(lista_sidra(), ensure_ascii=False), encoding="utf-8")
    df_arq = ler_ipca_sidra(caminho)
    df_str = ler_ipca_sidra(str(caminho))
    pd.testing.assert_frame_equal(df_arq, ler_ipca_sidra(lista_sidra()))
    pd.testing.assert_frame_equal(df_str, df_arq)
    assert media_indice_ano(df_arq, 2019) == pytest.approx(MEDIA_2019)


def test_ler_ipca_sidra_sem_mes_no_cabecalho():
    cab = {k: v for k, v in CABECALHO_SIDRA.items() if not k.startswith("D2")}
    regs = [cab] + [{k: v for k, v in r.items() if not k.startswith("D2")} for r in lista_sidra()[1:]]
    with pytest.raises(ValueError, match="Mês"):
        ler_ipca_sidra(regs)


def test_media_indice_ano_exige_12_meses():
    df = ipca_df()
    df = df[df["mes"] != "201907"]
    with pytest.raises(ValueError, match=r"\[7\]"):
        media_indice_ano(df, 2019)


# --------------------------------------------------------------------------------------------
# Preços médios de 2019
# --------------------------------------------------------------------------------------------
def test_precos_medios_correcao_ipca_e_ponderacao_a_mao():
    res = precos_medios_2019(leiloes_df(), ipca_df())
    assert isinstance(res, ResultadoPrecos)
    assert res.media_ipca_2019 == pytest.approx(MEDIA_2019)

    tab = res.tabela.set_index("subsetor")
    assert list(res.tabela["subsetor"]) == ["S38_HID", "S38_EOL", "S38_BIO"]
    # HID: 100 × 105.5/50 = 211 (10 MWmed) e 95 × 105.5/95 = 105.5 (30 MWmed)
    #      → (211 × 10 + 105.5 × 30) / 40 = 5275 / 40 = 131.875
    assert tab.loc["S38_HID", "preco_2019_rs_mwh"] == pytest.approx(131.875, abs=TOL)
    assert tab.loc["S38_HID", "energia_mwmed_total"] == pytest.approx(40.0)
    assert tab.loc["S38_HID", "n_registros"] == 2
    assert tab.loc["S38_HID", "primeiro_leilao"] == pd.Timestamp("2018-06-15")
    assert tab.loc["S38_HID", "ultimo_leilao"] == pd.Timestamp("2018-12-10")
    # EOL: 80 × 105.5/50 = 168.8 (o leilão de 2019 fica fora)
    assert tab.loc["S38_EOL", "preco_2019_rs_mwh"] == pytest.approx(168.8, abs=TOL)
    assert tab.loc["S38_EOL", "n_registros"] == 1
    # BIO: leilão em 31/12/2018 entra; 190 × 105.5/95 = 211
    assert tab.loc["S38_BIO", "preco_2019_rs_mwh"] == pytest.approx(211.0, abs=TOL)

    det = res.detalhe
    assert len(det) == 4
    hid = det[det["subsetor"] == "S38_HID"].reset_index(drop=True)
    assert hid["indice_mes_leilao"].tolist() == pytest.approx([50.0, 95.0])
    assert hid["fator_correcao"].tolist() == pytest.approx([2.11, 105.5 / 95.0])
    assert hid["preco_2019_rs_mwh"].tolist() == pytest.approx([211.0, 105.5])
    assert det["mes_leilao"].iloc[0] == pd.Period("2018-06", freq="M")


def test_precos_medios_contagens_descartes_e_nao_mapeadas():
    res = precos_medios_2019(leiloes_df(), ipca_df())
    c = res.contagens
    assert c == {
        "n_registros_lidos": 9,
        "n_sem_data": 1,
        "n_apos_corte": 1,
        "n_preco_invalido": 1,
        "n_energia_invalida": 1,
        "n_preco_ou_energia_invalidos": 2,
        "n_fonte_nao_mapeada": 1,
        "n_usados": 4,
    }
    assert c["n_registros_lidos"] == (
        c["n_sem_data"] + c["n_apos_corte"] + c["n_preco_ou_energia_invalidos"]
        + c["n_fonte_nao_mapeada"] + c["n_usados"]
    )
    assert set(res.descartados["fonte_energia"]) == {"Gás Natural", "Solar", "Carvão"}
    assert "motivo" in res.descartados.columns
    nm = res.fontes_nao_mapeadas
    assert nm["fonte_energia"].tolist() == ["Termelétrica"]
    assert nm["energia_mwmed_total"].tolist() == pytest.approx([7.0])
    assert nm["n_registros"].tolist() == [1]


def test_precos_medios_corte_de_data():
    # com corte em 30/06/2018 só entram os leilões de junho
    res = precos_medios_2019(leiloes_df(), ipca_df(), data_corte="2018-06-30")
    tab = res.tabela.set_index("subsetor")
    assert tab.loc["S38_HID", "preco_2019_rs_mwh"] == pytest.approx(211.0)
    assert "S38_BIO" not in tab.index
    assert res.contagens["n_apos_corte"] == 3
    # leilão com hora no último dia do corte entra
    leiloes = leiloes_df()
    leiloes.loc[3, "data_leilao"] = pd.Timestamp("2018-12-31 23:59")
    assert "S38_BIO" in set(precos_medios_2019(leiloes, ipca_df()).tabela["subsetor"])


def test_precos_medios_desempacota_em_tabela_e_detalhe():
    tabela, detalhe = precos_medios_2019(leiloes_df(), ipca_df())
    assert {"subsetor", "preco_2019_rs_mwh", "energia_mwmed_total", "n_registros",
            "primeiro_leilao", "ultimo_leilao"} <= set(tabela.columns)
    assert "preco_2019_rs_mwh" in detalhe.columns


def test_precos_medios_mes_sem_indice():
    ipca = ipca_df()
    ipca = ipca[ipca["mes"] != "201806"]
    with pytest.raises(ValueError, match="2018-06"):
        precos_medios_2019(leiloes_df(), ipca)


def test_precos_medios_coluna_faltando():
    with pytest.raises(ValueError, match="energia_mwmed"):
        precos_medios_2019(leiloes_df().drop(columns="energia_mwmed"), ipca_df())


def test_fluxo_completo_a_partir_dos_arquivos(tmp_path):
    csv = (
        "DatLeilao;DscFonteEnergia;VlrPrecoLeilao;VlrEnergiaVendida\n"
        "15/06/2018 00:00:00;Hidrelétrica;100,00;10,0\n"
        "10/12/2018;PCH;95,00;30\n"
        "15/01/2019;Eólica;80,0;5\n"
    )
    arq_csv = tmp_path / "leiloes.csv"
    arq_csv.write_bytes(csv.encode("latin-1"))
    arq_json = tmp_path / "ipca.json"
    arq_json.write_text(json.dumps(lista_sidra()), encoding="utf-8")

    res = precos_medios_2019(ler_leiloes(arq_csv), ler_ipca_sidra(arq_json))
    assert res.tabela["subsetor"].tolist() == ["S38_HID"]
    assert res.tabela["preco_2019_rs_mwh"].iloc[0] == pytest.approx(131.875)
    assert res.contagens["n_apos_corte"] == 1


# --------------------------------------------------------------------------------------------
# Nuclear e comparação com a referência
# --------------------------------------------------------------------------------------------
def test_constantes_de_referencia():
    assert PRECO_NUCLEAR_2019 == pytest.approx(247.47)
    assert REFERENCIA_PRECOS["S38_NUC"] == pytest.approx(PRECO_NUCLEAR_2019)
    assert set(REFERENCIA_PRECOS) == {
        "S38_HID", "S38_EOL", "S38_SOL", "S38_BIO", "S38_CAR", "S38_GN", "S38_PET", "S38_NUC"
    }
    assert REFERENCIA_IPCA_MEDIA_2019 == pytest.approx(5213.61)


def test_acrescentar_nuclear():
    tabela, _ = precos_medios_2019(leiloes_df(), ipca_df())
    com_nuc = acrescentar_nuclear(tabela)
    assert com_nuc["subsetor"].tolist() == ["S38_HID", "S38_EOL", "S38_BIO", "S38_NUC"]
    nuc = com_nuc.set_index("subsetor").loc["S38_NUC"]
    assert nuc["preco_2019_rs_mwh"] == pytest.approx(247.47)
    assert nuc["n_registros"] == 0
    assert "Angra" in nuc["origem"]
    with pytest.raises(ValueError, match="S38_NUC"):
        acrescentar_nuclear(com_nuc)


def test_comparar_com_referencia():
    # tabela com exatamente os valores de referência (só para testar a comparação)
    tabela = pd.DataFrame(
        {"subsetor": list(REFERENCIA_PRECOS), "preco_2019_rs_mwh": list(REFERENCIA_PRECOS.values())}
    )
    tabela.loc[tabela["subsetor"] == "S38_HID", "preco_2019_rs_mwh"] += 1.5
    tabela = tabela[tabela["subsetor"] != "S38_PET"]
    comp = comparar_com_referencia(tabela, media_ipca_2019=5213.0).set_index("subsetor")
    assert list(comp.columns) == ["esperado", "obtido", "diferenca", "dentro_tolerancia"]
    assert comp.loc["S38_HID", "diferenca"] == pytest.approx(1.5)
    assert not comp.loc["S38_HID", "dentro_tolerancia"]
    assert comp.loc["S38_EOL", "diferenca"] == pytest.approx(0.0)
    assert comp.loc["S38_EOL", "dentro_tolerancia"]
    assert np.isnan(comp.loc["S38_PET", "obtido"])
    assert not comp.loc["S38_PET", "dentro_tolerancia"]
    assert comp.loc["IPCA_MEDIA_2019", "esperado"] == pytest.approx(5213.61)
    assert comp.loc["IPCA_MEDIA_2019", "dentro_tolerancia"]


def test_comparar_com_referencia_aceita_resultado():
    res = precos_medios_2019(leiloes_df(), ipca_df())
    comp = comparar_com_referencia(res).set_index("subsetor")
    assert comp.loc["S38_HID", "obtido"] == pytest.approx(131.875)
    assert comp.loc["IPCA_MEDIA_2019", "obtido"] == pytest.approx(MEDIA_2019)
    assert not comp.loc["IPCA_MEDIA_2019", "dentro_tolerancia"]  # dados sintéticos
