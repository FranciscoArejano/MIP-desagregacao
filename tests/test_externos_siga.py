"""Testes do leitor/classificador do cadastro ANEEL SIGA (mip.externos.siga) — Seção 5.2.

Só dados SINTÉTICOS: nomes de usinas e núcleos de CEG abaixo são inventados para o teste
(o arquivo real não estava acessível quando o módulo foi escrito).
"""
import numpy as np
import pandas as pd
import pytest

from mip.externos.siga import (
    BIO,
    CAR,
    EOL,
    GN,
    HID,
    NUC,
    PET,
    SOL,
    classificar_fonte,
    classificar_siga,
    classificar_usinas_ons,
    ler_siga,
    nucleo_ceg,
)

CABECALHO = (
    "DatGeracaoConjuntoDados;NomEmpreendimento;IdeNucleoCEG;CodCEG;SigUFPrincipal;"
    "DscOrigemCombustivel;DscFonteCombustivel;NomFonteCombustivel;MdaPotenciaOutorgadaKw"
)
LINHAS = [
    "2026-01-01;Usina Teste Carvão;1001;UTE.CM.RS.001001-0.01;RS;Fóssil;Carvão mineral;Carvão Mineral;1.500,25",
    "2026-01-01;Usina Teste Gás;28038;UTE.GN.RS.028038-0.01;RS;Fóssil;Gás natural;Gás Natural;30000",
    "2026-01-01;Usina Teste Óleo;012345;UTE.PE.SP.012345-1.01;SP;Fóssil;Petróleo;Óleo Diesel;250,5",
    "2026-01-01;Usina Teste Hídrica;300001;UHE.PH.RS.300001-2.01;RS;Hídrica;Potencial hidráulico;Potencial hidráulico;",
]


def _csv(linhas=LINHAS, cabecalho=CABECALHO, sep=";") -> str:
    texto = "\n".join([cabecalho] + linhas) + "\n"
    return texto.replace(";", sep) if sep != ";" else texto


def _siga_bruto(registros: list[dict]) -> pd.DataFrame:
    """DataFrame no formato bruto do SIGA (colunas documentadas)."""
    base = {"IdeNucleoCEG": None, "NomEmpreendimento": None, "DscFonteCombustivel": None, "NomFonteCombustivel": None}
    return pd.DataFrame([{**base, **r} for r in registros])


# --------------------------------------------------------------------------------------------
# 1) nucleo_ceg
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("UTE.GN.RS.028038-0.01", "028038"),
        ("  ute.gn.rs.028038-0.01 ", "028038"),
        ("UHE.PH.MG.000018-2.01", "000018"),
        ("EOL.CV.RS.123456-7", "123456"),
        ("028038-0.01", "028038"),
        ("UTE.GN.RS.028038-0.01, UTE.GN.RS.028038-0.02", "028038"),  # mesmo núcleo repetido
        (28038, "028038"),
        (np.int64(28038), "028038"),
        (28038.0, "028038"),
        ("28038", "028038"),
        ("028038", "028038"),
        ("28038.0", "028038"),
        (" 18 ", "000018"),
        (999999, "999999"),
    ],
)
def test_nucleo_ceg_validos(entrada, esperado):
    assert nucleo_ceg(entrada) == esperado


@pytest.mark.parametrize(
    "entrada",
    [
        "-", "", "   ", None, np.nan, pd.NA, "abc", "UTE.GN.RS.28038-0.01", "UTE.GN.RS.0280380-0.01",
        "1234567", 1234567, 0, "0", -5, 28038.5, True, "UTE.GN.RS.028038-0.01, UTE.GN.RS.028039-0.01",
        "UTE.GN.RS.028038-0.01 lixo",
    ],
)
def test_nucleo_ceg_invalidos(entrada):
    assert nucleo_ceg(entrada) is None


# --------------------------------------------------------------------------------------------
# 2) ler_siga
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "latin-1", "cp1252"])
def test_ler_siga_encodings(tmp_path, encoding):
    arq = tmp_path / f"siga_{encoding}.csv"
    arq.write_bytes(_csv().encode(encoding))
    df = ler_siga(arq)
    # acentos decodificados corretamente e BOM fora do nome da primeira coluna
    assert df.columns[0] == "DatGeracaoConjuntoDados"
    assert df["DscFonteCombustivel"].tolist() == ["Carvão mineral", "Gás natural", "Petróleo", "Potencial hidráulico"]
    assert df["NomEmpreendimento"].iloc[2] == "Usina Teste Óleo"
    # núcleo com e sem zeros à esquerda → 6 dígitos
    assert df["nucleo_ceg"].tolist() == ["001001", "028038", "012345", "300001"]
    assert df.attrs["separador"] == ";"
    assert df.attrs["encoding"] in ("utf-8", "utf-8-sig", "cp1252", "latin-1")
    if encoding == "utf-8-sig":
        assert df.attrs["encoding"] == "utf-8-sig"


def test_ler_siga_decimal_virgula_e_vazios(tmp_path):
    arq = tmp_path / "siga.csv"
    arq.write_text(_csv(), encoding="utf-8")
    df = ler_siga(arq)
    pot = df["MdaPotenciaOutorgadaKw"]
    assert pot.iloc[0] == pytest.approx(1500.25)
    assert pot.iloc[1] == pytest.approx(30000.0)
    assert pot.iloc[2] == pytest.approx(250.5)
    assert pd.isna(pot.iloc[3])


def test_ler_siga_separador_virgula(tmp_path):
    linhas = [l.replace("1.500,25", "1500").replace("250,5", "250") for l in LINHAS]
    arq = tmp_path / "siga_virgula.csv"
    arq.write_text(_csv(linhas, sep=","), encoding="utf-8")
    df = ler_siga(arq)
    assert df.attrs["separador"] == ","
    assert df["nucleo_ceg"].tolist() == ["001001", "028038", "012345", "300001"]


def test_ler_siga_nomes_de_coluna_variados(tmp_path):
    cab = (
        ' "Data" ; Nome Empreendimento ; ide_nucleo_ceg ;SIG UF PRINCIPAL;'
        " dsc fonte combustível ; NOM FONTE COMBUSTIVEL "
    )
    linhas = ["2026;  Usina   Teste  ;  7  ;RS;  GÁS NATURAL  ;Gás Natural"]
    arq = tmp_path / "siga.csv"
    arq.write_text("\n".join([cab] + linhas), encoding="utf-8")
    df = ler_siga(arq)
    for c in ("NomEmpreendimento", "IdeNucleoCEG", "SigUFPrincipal", "DscFonteCombustivel", "NomFonteCombustivel"):
        assert c in df.columns
    assert df["NomEmpreendimento"].iloc[0] == "Usina Teste"
    assert df["nucleo_ceg"].iloc[0] == "000007"
    assert classificar_siga(df)["subsetor"].iloc[0] == GN


def test_ler_siga_nucleo_pelo_codceg_quando_falta_idenucleo(tmp_path):
    cab = "NomEmpreendimento;CodCEG;DscFonteCombustivel"
    linhas = ["Usina X;UTE.GN.RS.028038-0.01;Gás natural", "Usina Y;-;Gás natural"]
    arq = tmp_path / "siga.csv"
    arq.write_text("\n".join([cab] + linhas), encoding="utf-8")
    df = ler_siga(arq)
    assert df["nucleo_ceg"].tolist() == ["028038", None]


def test_ler_siga_coluna_faltando(tmp_path):
    arq = tmp_path / "siga.csv"
    arq.write_text("NomEmpreendimento;IdeNucleoCEG;NomFonteCombustivel\nUsina;1;Gás Natural\n", encoding="utf-8")
    with pytest.raises(ValueError) as erro:
        ler_siga(arq)
    msg = str(erro.value)
    assert "DscFonteCombustivel" in msg
    assert "NomEmpreendimento" in msg and "NomFonteCombustivel" in msg  # lista as disponíveis


def test_ler_siga_sem_nucleo(tmp_path):
    arq = tmp_path / "siga.csv"
    arq.write_text("NomEmpreendimento;DscFonteCombustivel\nUsina;Gás natural\n", encoding="utf-8")
    with pytest.raises(ValueError, match="IdeNucleoCEG"):
        ler_siga(arq)


# --------------------------------------------------------------------------------------------
# 3) classificar_siga — uma linha por regra da Seção 5.2
# --------------------------------------------------------------------------------------------
CASOS = [
    # (DscFonteCombustivel, NomFonteCombustivel, NomEmpreendimento, subsetor esperado, trecho da regra)
    ("Carvão mineral", "Carvão Mineral", "Usina A", CAR, "carvao mineral"),
    ("CARVAO MINERAL", "Calor de Processo - CM", "Usina A2", CAR, "carvao mineral"),
    ("Gás natural", "Gás Natural", "Usina B", GN, "gas natural"),
    ("  gás   NATURAL ", None, "Usina B2", GN, "gas natural"),
    ("Petróleo", "Óleo Diesel", "Usina C", PET, "petroleo"),
    ("Petróleo", "Óleo Combustível", "Usina C2", PET, "petroleo"),
    ("Outros Fósseis", "Gás de Alto Forno", "Usina D", CAR, "NomFonteCombustivel"),
    ("Outros Fósseis", "Gás de Coqueria", "Usina D2", CAR, "coqueria"),
    ("Outros Fósseis", "Calor de Processo - OF", "Usina Siderúrgica Teste", CAR, "NomEmpreendimento"),
    ("Outros Fósseis", "Calor de Processo - OF", "Usina Gás de Aciaria", CAR, "aciaria"),
    ("Outros Fósseis", "Gás de Refinaria", "Usina E", PET, "refinaria"),
    ("Outros Fósseis", "Outros Derivados", "Usina E2", PET, "derivad"),
    ("Outros Fósseis", "Calor de Processo - OF", "Usina F", None, "pendente"),
    ("Agroindustriais", "Bagaço de Cana de Açúcar", "Usina G", BIO, "agroindustria"),
    ("Floresta", "Licor Negro", "Usina H", BIO, "florest"),
    ("Floresta", "Gás de Alto Forno - Biomassa", "Usina H2", BIO, "florest"),
    ("Resíduos sólidos urbanos", "Biogás - RU", "Usina I", BIO, "residuos solidos urbanos"),
    ("Resíduos animais", "Biogás - RA", "Usina J", BIO, "residuos animais"),
    ("Biocombustíveis líquidos", "Óleos vegetais", "Usina K", BIO, "biocombustive"),
    ("Potencial hidráulico", "Potencial hidráulico", "Usina L", HID, "potencial hidraulico"),
    ("Cinética do vento", "Cinética do vento", "Usina M", EOL, "cinetica do vento"),
    ("Radiação solar", "Radiação solar", "Usina N", SOL, "radiacao solar"),
    ("Urânio", "Urânio", "Usina O", NUC, "uranio"),
    ("Nuclear", None, "Usina O2", NUC, "nuclear"),
    # DscFonte vazio → reserva por NomFonteCombustivel
    (None, "Óleo Diesel", "Usina P", PET, "reserva"),
    ("", "Gás de Alto Forno - Biomassa", "Usina P2", BIO, "reserva"),
    (None, "Carvão - RU", "Usina P3", BIO, "reserva"),
    # não mapeado
    ("Cinética da água", "Cinética da água", "Usina Q", None, "sem subsetor"),
    (None, None, "Usina R", None, "vazio"),
]


def test_classificar_siga_regras():
    df = _siga_bruto(
        [
            {"IdeNucleoCEG": 100 + i, "DscFonteCombustivel": d, "NomFonteCombustivel": n, "NomEmpreendimento": e}
            for i, (d, n, e, _, _) in enumerate(CASOS)
        ]
    )
    out = classificar_siga(df)
    assert list(out.columns) == ["nucleo_ceg", "nome", "fonte_dsc", "fonte_nom", "subsetor", "regra", "uf"]
    assert out.index.equals(df.index)
    for i, (d, n, e, esperado, trecho) in enumerate(CASOS):
        linha = out.iloc[i]
        assert linha["subsetor"] == esperado, (d, n, e, linha["regra"])
        if esperado is None:
            assert linha["subsetor"] is None
        assert trecho in linha["regra"], (trecho, linha["regra"])
        assert linha["nucleo_ceg"] == str(100 + i).zfill(6)
        assert linha["nome"] == e
    assert out["uf"].isna().all()  # SigUFPrincipal ausente → None


def test_classificar_siga_regra_registra_campo_e_palavra():
    sub, regra = classificar_fonte("Outros Fósseis", "Gás de Alto-Forno", "Usina D")
    assert sub == CAR
    assert "NomFonteCombustivel='Gás de Alto-Forno'" in regra and "'alto forno'" in regra
    sub, regra = classificar_fonte("Outros Fósseis", "Calor de Processo - OF", "Usina F")
    assert sub is None and "pendente" in regra and "Usina F" in regra


def test_classificar_siga_sem_reserva():
    sub, regra = classificar_fonte(None, "Óleo Diesel", "Usina P", usar_reserva_nom_fonte=False)
    assert sub is None and "sem subsetor" in regra


def test_classificar_siga_a_partir_do_ler_siga(tmp_path):
    arq = tmp_path / "siga.csv"
    arq.write_bytes(_csv().encode("latin-1"))
    out = classificar_siga(ler_siga(arq))
    assert out["subsetor"].tolist() == [CAR, GN, PET, HID]
    assert out["uf"].tolist() == ["RS", "RS", "SP", "RS"]
    assert out["nucleo_ceg"].tolist() == ["001001", "028038", "012345", "300001"]


def test_classificar_siga_coluna_faltando():
    df = pd.DataFrame({"IdeNucleoCEG": [1], "NomFonteCombustivel": ["Gás Natural"]})
    with pytest.raises(ValueError, match="DscFonteCombustivel") as erro:
        classificar_siga(df)
    assert "NomFonteCombustivel" in str(erro.value)
    df = pd.DataFrame({"DscFonteCombustivel": ["Gás natural"]})
    with pytest.raises(ValueError, match="nucleo_ceg"):
        classificar_siga(df)


# --------------------------------------------------------------------------------------------
# 4) classificar_usinas_ons
# --------------------------------------------------------------------------------------------
def _siga_classificado() -> pd.DataFrame:
    df = _siga_bruto(
        [
            {"IdeNucleoCEG": 28038, "DscFonteCombustivel": "Gás natural", "NomEmpreendimento": "Usina Gás"},
            {"IdeNucleoCEG": "001001", "DscFonteCombustivel": "Carvão mineral", "NomEmpreendimento": "Usina Carvão"},
            {"IdeNucleoCEG": 5555, "DscFonteCombustivel": "Outros Fósseis", "NomFonteCombustivel": "Gás de Alto Forno",
             "NomEmpreendimento": "Usina Alto-Forno"},
            # núcleo repetido com o mesmo subsetor
            {"IdeNucleoCEG": 7777, "DscFonteCombustivel": "Floresta", "NomEmpreendimento": "Usina Licor"},
            {"IdeNucleoCEG": "007777", "DscFonteCombustivel": "Floresta", "NomEmpreendimento": "Usina Licor"},
            # núcleo repetido com subsetores distintos
            {"IdeNucleoCEG": 8888, "DscFonteCombustivel": "Gás natural", "NomEmpreendimento": "Usina Z"},
            {"IdeNucleoCEG": 8888, "DscFonteCombustivel": "Petróleo", "NomEmpreendimento": "Usina Z"},
        ]
    )
    return classificar_siga(df)


def test_classificar_usinas_ons_casamento():
    usinas = pd.DataFrame(
        {
            "nom_usina": ["Usina Gás", "Usina Carvão", "Usina AF", "Sem CEG", "Fora do SIGA", "Licor", "Conflito", "Nulo"],
            "ceg": [
                "UTE.GN.RS.028038-0.01", "UTE.CM.RS.001001-0.01", "UTE.OF.ES.005555-3.01", "-",
                "UTE.GN.RJ.999998-0.01", "UTE.FL.PR.007777-1.01", "UTE.GN.BA.008888-0.01", None,
            ],
            "val_geracao": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        },
        index=[10, 11, 12, 13, 14, 15, 16, 17],
    )
    out = classificar_usinas_ons(usinas, _siga_classificado())
    # colunas de entrada preservadas, mesmo índice e ordem, nenhuma linha a mais
    assert list(out.columns[:3]) == ["nom_usina", "ceg", "val_geracao"]
    assert {"nucleo_ceg", "subsetor_siga", "regra_siga"} <= set(out.columns)
    assert out.index.equals(usinas.index)
    pd.testing.assert_frame_equal(out[usinas.columns], usinas)

    assert out["nucleo_ceg"].tolist() == ["028038", "001001", "005555", None, "999998", "007777", "008888", None]
    assert out["subsetor_siga"].tolist() == [GN, CAR, CAR, None, None, BIO, None, None]
    assert "alto forno" in out.loc[12, "regra_siga"]
    assert out.loc[13, "regra_siga"] is None and out.loc[14, "regra_siga"] is None
    assert out.loc[17, "regra_siga"] is None
    assert "2 linhas no SIGA" in out.loc[15, "regra_siga"]
    assert "conflito" in out.loc[16, "regra_siga"]
    assert out.loc[10, "nome_siga"] == "Usina Gás"
    assert usinas.columns.tolist() == ["nom_usina", "ceg", "val_geracao"]  # entrada não alterada


def test_classificar_usinas_ons_tabela_horaria():
    """Várias linhas por usina (como no arquivo horário do ONS): casamento linha a linha."""
    usinas = pd.DataFrame(
        {"nom_usina": ["Usina Gás", "Usina Carvão"] * 3, "ceg": ["UTE.GN.RS.028038-0.01", "UTE.CM.RS.001001-0.01"] * 3}
    )
    out = classificar_usinas_ons(usinas, _siga_classificado())
    assert len(out) == 6
    assert out["subsetor_siga"].tolist() == [GN, CAR] * 3


def test_classificar_usinas_ons_coluna_faltando():
    with pytest.raises(ValueError, match="ceg") as erro:
        classificar_usinas_ons(pd.DataFrame({"nom_usina": ["X"], "codigo": [1]}), _siga_classificado())
    assert "nom_usina" in str(erro.value)
    with pytest.raises(ValueError, match="subsetor"):
        classificar_usinas_ons(pd.DataFrame({"ceg": ["-"]}), pd.DataFrame({"nucleo_ceg": ["000001"], "regra": ["x"]}))
