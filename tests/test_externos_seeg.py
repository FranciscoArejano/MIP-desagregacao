"""Testes do leitor/agregador do SEEG 13.0 (mip.externos.seeg) — Seção 5.7.

Só dados SINTÉTICOS: as planilhas e os valores abaixo são inventados para o teste
(o arquivo real não estava acessível quando o módulo foi escrito).
"""
import math
import warnings

import numpy as np
import openpyxl
import pandas as pd
import pytest

from mip.externos.seeg import (
    BIO,
    CAR,
    COLUNA_VALOR,
    COLUNAS_TEXTO,
    GN,
    PET,
    REFERENCIA_MIL_T,
    comparar_com_referencia,
    emissoes_por_regiao,
    emissoes_por_subsetor,
    filtrar_seeg,
    identificar_combustivel,
    ler_seeg_filtrado,
    mapear_combustivel,
    regiao_do_estado,
)

GAS = "CO2e (t) GWP-AR5"
GER = "Geração de eletricidade (serviço público)"
SF6 = "Uso de SF6 em equipamentos elétricos"

CABECALHO_TEXTO = [
    "Emissão/Remoção/Bunker", "Gás", "Setor de emissão", "Categoria emissora", "Sub-categoria emissora",
    "Produto ou sistema", "Detalhamento", "Recorte", "Atividade geral", "Estado", "Bioma",
]


def _linha(estado, combustivel, v2019, *, gas=GAS, cat=GER, sub="Geração de eletricidade",
           setor="Energia", produto="Termelétrica", v2018=999.0, v2020=111.0):
    """Linha sintética: o combustível fica em 'Detalhamento' ('Produto ou sistema' não traz combustível)."""
    return ["Emissão", gas, setor, cat, sub, produto, combustivel, "Recorte X", "Atividade Y", estado, None,
            v2018, v2019, v2020]


# (t CO2e no ano de 2019; v2018/v2020 servem para provar que a coluna certa é lida)
LINHAS = [
    # --- passam no filtro: geração (serviço público) ---
    _linha("RS", "Carvão mineral", 1000.0),
    _linha("Rio Grande do Sul", "Gás natural seco", 300.0),
    _linha(" rs ", "Diesel de petróleo", 50.0),
    _linha("RS", "Óleo combustível", "30,0"),  # texto com decimal vírgula
    _linha("SP", "CARVÃO  MINERAL", 2000.0),  # maiúsculas e espaço duplo: mesmo combustível
    _linha("Minas Gerais", "Gás natural úmido", 500.0),
    _linha("AM", "Diesel de petróleo", 400.0),
    _linha("Não Alocado", "Gás de refinaria", 70.0),
    _linha("NÃO ALOCADO", "Lenha", 5.0),
    _linha("RJ", "Biodiesel", None),  # vazio → 0 (contado)
    _linha("SP", "Alcatrão", 10.0),
    # --- não passam ---
    _linha("RS", "Carvão mineral", 777.0, gas="CO2 (t)"),
    _linha("RS", "Carvão mineral", 888.0, gas="CO2e (t) GWP-AR6"),
    _linha("RS", "Carvão mineral", 555.0, cat="Geração de eletricidade (autoprodução)"),
    _linha("SP", "Diesel de petróleo", 666.0, cat="Transportes"),
    # --- SF6 (Processos Industriais): pela categoria e pela sub-categoria ---
    _linha("SP", None, 100.0, cat=SF6, sub="Equipamentos", setor="Processos Industriais", produto=None),
    _linha("RS", None, 23.0, cat="Emissões de HFCs e SF6", sub="Uso de SF6 em Equipamentos Elétricos",
           setor="Processos Industriais", produto=None),
    _linha("SP", None, 1.0, gas="SF6 (t)", cat=SF6, setor="Processos Industriais", produto=None),  # outro gás
]

GWH_RS = {"S38_CAR": 3.0, "S38_GN": 1.0}


def _escrever_xlsx(caminho, linhas=LINHAS, ano_2019=2019, cabecalho_texto=CABECALHO_TEXTO,
                   preambulo=3, aba="Dados"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = aba
    ws.append(["SEEG 13.0 — Dados nacionais (sintético)"])
    for _ in range(preambulo - 1):
        ws.append([])
    ws.append(list(cabecalho_texto) + [2018, ano_2019, "2020"])
    for l in linhas:
        ws.append(l)
    wb.create_sheet("Notas").append(["nada aqui"])
    wb.save(caminho)
    return caminho


@pytest.fixture
def xlsx(tmp_path):
    return _escrever_xlsx(tmp_path / "seeg_sintetico.xlsx")


@pytest.fixture
def filtrado(xlsx):
    return ler_seeg_filtrado(xlsx)


# --------------------------------------------------------------------------------------------
# 1) ler_seeg_filtrado
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("ano_2019", [2019, 2019.0, "2019", " 2019 "])
def test_le_xlsx_com_cabecalho_do_ano_int_float_ou_texto(tmp_path, ano_2019):
    df = ler_seeg_filtrado(_escrever_xlsx(tmp_path / "s.xlsx", ano_2019=ano_2019))
    assert list(df.columns) == list(COLUNAS_TEXTO) + [COLUNA_VALOR, "grupo"]
    assert (df["grupo"] == "geracao").sum() == 11
    assert (df["grupo"] == "sf6").sum() == 2
    assert df.loc[df["grupo"] == "geracao", COLUNA_VALOR].sum() == pytest.approx(4365.0)
    assert df.loc[df["grupo"] == "sf6", COLUNA_VALOR].sum() == pytest.approx(123.0)
    assert df.attrs["n_valores_vazios"] == 1
    assert df.attrs["n_linhas_lidas"] == len(LINHAS)
    assert df.attrs["ano"] == 2019
    assert df.attrs["colunas_ausentes"] == []
    # nada das linhas que não deveriam passar
    assert not df[COLUNA_VALOR].isin([777.0, 888.0, 555.0, 666.0, 1.0]).any()


def test_outro_ano_le_outra_coluna(xlsx):
    df = ler_seeg_filtrado(xlsx, ano=2018)
    assert df[COLUNA_VALOR].sum() == pytest.approx(999.0 * 13)
    assert df.attrs["n_valores_vazios"] == 0


def test_ano_ausente_levanta_erro(xlsx):
    with pytest.raises(ValueError, match="2030"):
        ler_seeg_filtrado(xlsx, ano=2030)


def test_progresso_escreve_em_stderr(xlsx, capsys):
    ler_seeg_filtrado(xlsx, progresso=5)
    assert "linhas lidas" in capsys.readouterr().err


def test_nomes_de_colunas_e_aba_com_variacoes(tmp_path):
    cab = [" emissao/remocao/bunker ", "GAS", "Setor de Emissão", "CATEGORIA EMISSORA", "Subcategoria emissora",
           "Produto ou Sistema", "detalhamento", "Recorte", "Atividade Geral", "  estado ", "BIOMA"]
    caminho = _escrever_xlsx(tmp_path / "v.xlsx", cabecalho_texto=cab, aba=" dados ", preambulo=1)
    df = ler_seeg_filtrado(caminho)
    assert len(df) == 13
    assert df.attrs["colunas_ausentes"] == []


def test_coluna_obrigatoria_ausente_lista_colunas(tmp_path):
    cab = [c if c != "Estado" else "Município" for c in CABECALHO_TEXTO]
    cab[1] = "Gás"
    # sem 'Estado' o cabeçalho nem é reconhecido; com 'Estado' mas sem 'Categoria emissora' → erro de coluna
    caminho = _escrever_xlsx(tmp_path / "a.xlsx", cabecalho_texto=cab)
    with pytest.raises(ValueError, match="cabeçalho"):
        ler_seeg_filtrado(caminho)
    cab2 = [c if c != "Categoria emissora" else "Outra coisa" for c in CABECALHO_TEXTO]
    caminho2 = _escrever_xlsx(tmp_path / "b.xlsx", cabecalho_texto=cab2)
    with pytest.raises(ValueError, match=r"Categoria emissora.*Colunas disponíveis.*Outra coisa"):
        ler_seeg_filtrado(caminho2)


def test_cabecalho_alem_da_linha_20_nao_e_encontrado(tmp_path):
    caminho = _escrever_xlsx(tmp_path / "c.xlsx", preambulo=25)
    with pytest.raises(ValueError, match="primeiras 20 linhas"):
        ler_seeg_filtrado(caminho)


def test_aba_inexistente(xlsx):
    with pytest.raises(ValueError, match="Abas disponíveis"):
        ler_seeg_filtrado(xlsx, aba="Planilha1")


def test_filtrar_dataframe_igual_ao_streaming(filtrado):
    bruto = pd.DataFrame([l for l in LINHAS], columns=CABECALHO_TEXTO + [2018, "2019", 2020.0])
    df = filtrar_seeg(bruto)
    pd.testing.assert_frame_equal(df.reset_index(drop=True), filtrado.reset_index(drop=True))


@pytest.mark.parametrize("encoding", ["latin-1", "utf-8", "utf-8-sig"])
def test_csv_mesmo_resultado_do_xlsx(tmp_path, filtrado, encoding):
    def fmt(v):
        if v is None:
            return ""
        if isinstance(v, float):
            return f"{v:.1f}".replace(".", ",")
        return str(v)

    texto = "SEEG 13.0 - sintético\n\n" + ";".join(CABECALHO_TEXTO + ["2018", "2019", "2020"]) + "\n"
    texto += "".join(";".join(fmt(v) for v in l) + "\n" for l in LINHAS)
    caminho = tmp_path / "seeg.csv"
    caminho.write_bytes(texto.encode(encoding))
    df = ler_seeg_filtrado(caminho)
    assert df.attrs["separador"] == ";"
    assert df.attrs["n_valores_vazios"] == 1
    pd.testing.assert_series_equal(df[COLUNA_VALOR], filtrado[COLUNA_VALOR])
    pd.testing.assert_series_equal(df["Estado"], filtrado["Estado"])


# --------------------------------------------------------------------------------------------
# 2) e 3) combustível
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "nome, esperado",
    [
        ("Carvão mineral", CAR), ("CARVAO MINERAL", CAR), ("  alcatrão ", CAR),
        ("Gás natural seco", GN), ("gas natural umido", GN), ("Gás Natural Úmido", GN),
        ("Diesel de petróleo", PET), ("Óleo combustível", PET), ("Gás de refinaria", PET),
        ("Outros energéticos de petróleo", PET),
        ("Biodiesel", BIO), ("Biogás", BIO), ("LENHA", BIO), ("Outras biomassas", BIO),
        ("Carvão vegetal", None), ("Eletricidade", None), ("", None), (None, None), (float("nan"), None),
    ],
)
def test_mapear_combustivel(nome, esperado):
    assert mapear_combustivel(nome) == esperado


def test_identificar_combustivel_procura_na_ordem(filtrado):
    comb = identificar_combustivel(filtrado)
    # 'Produto ou sistema' só tem 'Termelétrica' → usa 'Detalhamento'
    assert comb.attrs["coluna_combustivel"] == "Detalhamento"
    assert comb.attrs["cobertura_por_coluna"]["Produto ou sistema"] == 0.0
    assert comb.attrs["cobertura_por_coluna"]["Detalhamento"] == 1.0
    assert comb[filtrado["grupo"] == "sf6"].isna().all()
    assert comb.iloc[4] == "CARVÃO MINERAL"  # espaço duplo colapsado, grafia original mantida

    # quando 'Produto ou sistema' traz combustível, ela vence (primeira na ordem)
    df = filtrado.copy()
    df["Produto ou sistema"] = df["Detalhamento"]
    df["Detalhamento"] = "Outra coisa"
    assert identificar_combustivel(df).attrs["coluna_combustivel"] == "Produto ou sistema"


def test_identificar_combustivel_sem_coluna_reconhecida():
    df = pd.DataFrame({"Produto ou sistema": ["X"], "Detalhamento": ["Y"], "grupo": ["geracao"]})
    with pytest.raises(ValueError, match="combustíveis conhecidos"):
        identificar_combustivel(df)


# --------------------------------------------------------------------------------------------
# 4) emissoes_por_regiao
# --------------------------------------------------------------------------------------------
def test_regiao_do_estado():
    assert regiao_do_estado("RS") == "RS"
    assert regiao_do_estado("rio grande do sul") == "RS"
    assert regiao_do_estado("Não Alocado") == "Não alocado"
    assert regiao_do_estado("SP") == "RB"
    assert regiao_do_estado("Rio Grande do Norte") == "RB"


def test_emissoes_por_regiao(filtrado):
    r = emissoes_por_regiao(filtrado)
    t = r["por_combustivel"]
    assert list(t.index) == ["RS", "RB", "Não alocado"]
    assert list(t.columns) == [
        "Carvão mineral", "Alcatrão", "Gás natural seco", "Gás natural úmido", "Diesel de petróleo",
        "Óleo combustível", "Gás de refinaria", "Biodiesel", "Lenha",
    ]
    esperado = {
        ("RS", "Carvão mineral"): 1.0, ("RS", "Gás natural seco"): 0.3, ("RS", "Diesel de petróleo"): 0.05,
        ("RS", "Óleo combustível"): 0.03,
        ("RB", "Carvão mineral"): 2.0, ("RB", "Alcatrão"): 0.01, ("RB", "Gás natural úmido"): 0.5,
        ("RB", "Diesel de petróleo"): 0.4, ("RB", "Biodiesel"): 0.0,
        ("Não alocado", "Gás de refinaria"): 0.07, ("Não alocado", "Lenha"): 0.005,
    }
    for (reg, comb), v in esperado.items():
        assert t.loc[reg, comb] == pytest.approx(v)
    assert t.to_numpy().sum() == pytest.approx(4.365)
    assert r["sf6_nacional_mil_t"] == pytest.approx(0.123)
    assert r["nao_mapeados"] == {}
    assert r["coluna_combustivel"] == "Detalhamento"
    assert r["n_linhas"] == {"geracao": 11, "sf6": 2}
    assert set(r["estados_por_regiao"]["RS"]) == {"RS", "Rio Grande do Sul", "rs"}
    assert r["estados_nao_reconhecidos"] == []


def test_combustivel_nao_mapeado_e_estado_nao_reconhecido(filtrado):
    extra = filtrado.iloc[[0]].copy()
    extra["Detalhamento"] = "Carvão vegetal"
    extra["Estado"] = "Brasil"
    extra[COLUNA_VALOR] = 42.0
    df = pd.concat([filtrado, extra], ignore_index=True)
    with pytest.warns(UserWarning, match="Brasil"):
        r = emissoes_por_regiao(df)
    assert r["nao_mapeados"] == {"Carvão vegetal": pytest.approx(0.042)}
    assert r["por_combustivel"].columns[-1] == "Carvão vegetal"
    assert r["subsetor_por_combustivel"]["Carvão vegetal"] is None
    assert r["estados_nao_reconhecidos"] == ["Brasil"]

    with pytest.warns(UserWarning, match="sem mapeamento"):
        sub = emissoes_por_subsetor(df, GWH_RS)
    assert sub.attrs["nao_mapeados_t"] == {"Carvão vegetal": 42.0}
    assert sub.to_numpy().sum() == pytest.approx(4365.0)  # o não mapeado ficou de fora


# --------------------------------------------------------------------------------------------
# 5) emissoes_por_subsetor
# --------------------------------------------------------------------------------------------
def test_emissoes_por_subsetor_realoca_pet_do_rs(filtrado):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        sub = emissoes_por_subsetor(filtrado, GWH_RS)
    assert list(sub.index) == ["RS", "RB"]
    assert list(sub.columns) == [CAR, GN, PET, BIO]
    # PET do RS = diesel 50 + óleo 30 = 80 t → CAR 3/4 = 60, GN 1/4 = 20
    assert sub.attrs["pet_rs_realocado_t"] == pytest.approx(80.0)
    assert sub.attrs["realocacao_pet_rs_t"] == {CAR: pytest.approx(60.0), GN: pytest.approx(20.0)}
    assert sub.loc["RS", CAR] == pytest.approx(1060.0)
    assert sub.loc["RS", GN] == pytest.approx(320.0)
    assert sub.loc["RS", PET] == 0.0
    assert sub.loc["RS", BIO] == 0.0
    # RB inclui o 'Não alocado' (gás de refinaria 70 → PET; lenha 5 → BIO)
    assert sub.loc["RB", CAR] == pytest.approx(2010.0)
    assert sub.loc["RB", GN] == pytest.approx(500.0)
    assert sub.loc["RB", PET] == pytest.approx(470.0)
    assert sub.loc["RB", BIO] == pytest.approx(5.0)
    assert sub.attrs["nao_alocado_para_rb_t"] == pytest.approx(75.0)
    # SF6 não entra; total da geração preservado
    assert sub.to_numpy().sum() == pytest.approx(4365.0)


def test_emissoes_por_subsetor_aceita_chaves_curtas(filtrado):
    sub = emissoes_por_subsetor(filtrado, {"CAR": 1.0, "GN": 1.0})
    assert sub.loc["RS", CAR] == pytest.approx(1040.0)
    assert sub.loc["RS", GN] == pytest.approx(340.0)


def test_emissoes_por_subsetor_erros(filtrado):
    with pytest.raises(ValueError, match="GWh"):
        emissoes_por_subsetor(filtrado, {"S38_CAR": 0.0, "S38_GN": 0.0})
    with pytest.raises(ValueError, match="S38_GN"):
        emissoes_por_subsetor(filtrado, {"S38_CAR": 1.0})
    with pytest.raises(ValueError, match="inválido"):
        emissoes_por_subsetor(filtrado, {"S38_CAR": -1.0, "S38_GN": 1.0})


# --------------------------------------------------------------------------------------------
# 6) referência
# --------------------------------------------------------------------------------------------
def test_constantes_de_referencia_sao_consistentes():
    ref = {(r, i): v for r, i, v, _ in REFERENCIA_MIL_T}
    for reg in ("RS", "RB"):
        partes = sum(ref[(reg, i)] for i in ("Carvão", "Gás natural", "Diesel", "Óleo combustível", "Outros"))
        assert partes == pytest.approx(ref[(reg, "Total")], abs=0.5)
    na = sum(ref[("Não alocado", i)] for i in ("Gás de refinaria", "Lenha", "Outras biomassas", "Biogás"))
    assert na == pytest.approx(ref[("Não alocado", "Total")], abs=0.5)
    assert ref[("RS", "Diesel")] + ref[("RS", "Óleo combustível")] == pytest.approx(ref[("RS", "Petróleo (PET) realocado")])


def _resultado_igual_a_referencia() -> dict:
    """Tabela sintética montada com os valores de referência (só para testar a comparação)."""
    t = pd.DataFrame(
        0.0,
        index=["RS", "RB", "Não alocado"],
        columns=["Carvão mineral", "Gás natural seco", "Diesel de petróleo", "Óleo combustível",
                 "Gás de refinaria", "Biodiesel", "Biogás", "Lenha", "Outras biomassas"],
    )
    t.loc["RS", ["Carvão mineral", "Gás natural seco", "Diesel de petróleo", "Óleo combustível"]] = [3749.6, 75.1, 8.6, 9.2]
    t.loc["RB", ["Carvão mineral", "Gás natural seco", "Diesel de petróleo", "Óleo combustível", "Biodiesel"]] = [
        9708.2, 20513.0, 3102.8, 855.8, 1.2]
    t.loc["Não alocado", ["Gás de refinaria", "Lenha", "Outras biomassas", "Biogás"]] = [333.0, 6.5, 4.0, 0.5]
    return {"por_combustivel": t, "sf6_nacional_mil_t": 323.1}


def test_comparar_com_referencia():
    res = _resultado_igual_a_referencia()
    cmp = comparar_com_referencia(res)
    assert list(cmp.columns) == ["regiao", "item", "esperado_mil_t", "obtido_mil_t", "diferenca_mil_t",
                                 "dentro_tolerancia", "observacao"]
    assert len(cmp) == len(REFERENCIA_MIL_T)
    assert cmp["dentro_tolerancia"].all(), cmp[~cmp["dentro_tolerancia"]]
    assert np.allclose(cmp["diferenca_mil_t"], 0.0, atol=1e-6)

    res["por_combustivel"].loc["RS", "Carvão mineral"] += 1.0
    cmp = comparar_com_referencia(res).set_index(["regiao", "item"])
    assert not cmp.loc[("RS", "Carvão"), "dentro_tolerancia"]
    assert cmp.loc[("RS", "Carvão"), "diferenca_mil_t"] == pytest.approx(1.0)
    assert not cmp.loc[("RS", "Total"), "dentro_tolerancia"]
    assert cmp.loc[("RB", "Total"), "dentro_tolerancia"]

    # só a tabela: SF6 sem valor obtido
    cmp2 = comparar_com_referencia(res["por_combustivel"]).set_index(["regiao", "item"])
    assert math.isnan(cmp2.loc[("Nacional", "SF6 em equipamentos elétricos"), "obtido_mil_t"])


def test_comparar_resultado_sintetico_do_xlsx(filtrado):
    cmp = comparar_com_referencia(emissoes_por_regiao(filtrado)).set_index(["regiao", "item"])
    assert cmp.loc[("RS", "Carvão"), "obtido_mil_t"] == pytest.approx(1.0)
    assert cmp.loc[("RS", "Petróleo (PET) realocado"), "obtido_mil_t"] == pytest.approx(0.08)
    assert cmp.loc[("RB", "Carvão"), "obtido_mil_t"] == pytest.approx(2.01)  # carvão mineral + alcatrão
    assert cmp.loc[("Não alocado", "Total"), "obtido_mil_t"] == pytest.approx(0.075)
    assert cmp.loc[("Nacional", "SF6 em equipamentos elétricos"), "obtido_mil_t"] == pytest.approx(0.123)
