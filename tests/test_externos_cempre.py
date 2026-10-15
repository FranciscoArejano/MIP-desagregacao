"""Seção 5.8 — CEMPRE 2019 (SIDRA 6450): testes com dados SINTÉTICOS.

O JSON abaixo imita o formato da API de valores do SIDRA (primeiro elemento = cabeçalho) e usa
os valores de referência da Seção 5.8 das instruções da Rodada 02. Os agregados do Brasil que a
referência não traz (divisão 35, grupos 35.1, 35.2 e 35.3) são montados aqui como somas das
classes, só para o teste. Os códigos de categoria do SIDRA (117297...) são atribuídos em ordem
embaralhada de propósito: o leitor tem de identificar a classe pelo nome. O leitor ainda não
foi validado com o arquivo real (rede bloqueada).
"""
import json
import warnings

import numpy as np
import pandas as pd
import pytest

from mip.externos.cempre import (
    CLASSES_CEMPRE,
    REFERENCIA_CEMPRE,
    comparar_com_referencia,
    composicao_cempre,
    ler_cempre_sidra,
    normalizar_cnae,
    participacoes_subsetores,
)

TOL = 1e-9

# --------------------------------------------------------------------------------------------
# Dados sintéticos
# --------------------------------------------------------------------------------------------
CABECALHO = {
    "NC": "Nível Territorial (Código)",
    "NN": "Nível Territorial",
    "MC": "Unidade de Medida (Código)",
    "MN": "Unidade de Medida",
    "V": "Valor",
    "D1C": "Brasil (Código)",
    "D1N": "Brasil",
    "D2C": "Variável (Código)",
    "D2N": "Variável",
    "D3C": "Ano (Código)",
    "D3N": "Ano",
    "D4C": "Classificação Nacional de Atividades Econômicas (CNAE 2.0) (Código)",
    "D4N": "Classificação Nacional de Atividades Econômicas (CNAE 2.0)",
}

NOMES = {
    "35": "35 Eletricidade, gás e outras utilidades",
    "35.1": "35.1 Geração, transmissão e distribuição de energia elétrica",
    "35.11-5": "35.11-5 Geração de energia elétrica",
    "35.12-3": "35.12-3 Transmissão de energia elétrica",
    "35.13-1": "35.13-1 Comércio atacadista de energia elétrica",
    "35.14-0": "35.14-0 Distribuição de energia elétrica",
    "35.2": "35.2 Produção e distribuição de combustíveis gasosos por redes urbanas",
    "35.20-4": "35.20-4 Produção de gás; processamento de gás natural; distribuição de combustíveis gasosos por redes urbanas",
    "35.3": "35.3 Produção e distribuição de vapor, água quente e ar condicionado",
    "35.30-1": "35.30-1 Produção e distribuição de vapor, água quente e ar condicionado",
}
# códigos do SIDRA embaralhados (não correspondem à ordem real; o leitor não pode depender deles)
CODIGO_SIDRA = dict(zip(NOMES, ["117306", "117300", "117297", "117304", "117299",
                                "117302", "117298", "117305", "117301", "117303"]))
VARIAVEIS = [("707", "Pessoal ocupado total", "Pessoas"),
             ("662", "Salários e outras remunerações", "Mil Reais")]

BR = REFERENCIA_CEMPRE["Brasil"]
RS = REFERENCIA_CEMPRE["RS"]


def valores_brasil() -> dict[str, tuple[float, float]]:
    """Classes da referência + agregados montados como somas (só para o teste)."""
    v = dict(BR)

    def soma(*cs):
        return tuple(sum(BR[c][i] for c in cs) for i in range(2))

    v["35.1"] = soma("35.11-5", "35.12-3", "35.13-1", "35.14-0")
    v["35.2"] = BR["35.20-4"]
    v["35.3"] = BR["35.30-1"]
    v["35"] = soma(*BR)
    return v


def valores_rs() -> dict[str, tuple]:
    v = dict(RS)
    for c in ("35.12-3", "35.13-1", "35.2", "35.20-4", "35.3", "35.30-1"):
        v[c] = ("X", "X")
    return v


def registro(terr: str, var: tuple, cnae: str, valor, ano: str = "2019") -> dict:
    cod_var, nome_var, unidade = var
    if terr == "Brasil":
        nc, nn, d1c, d1n = "1", "Brasil", "1", "Brasil"
    else:
        nc, nn, d1c, d1n = "3", "Unidade da Federação", "43", "Rio Grande do Sul"
    return {
        "NC": nc, "NN": nn, "MC": "0", "MN": unidade, "V": str(valor),
        "D1C": d1c, "D1N": d1n, "D2C": cod_var, "D2N": nome_var, "D3C": ano, "D3N": ano,
        "D4C": CODIGO_SIDRA[cnae], "D4N": NOMES[cnae],
    }


def json_sidra(com_cabecalho: bool = True, rs: dict | None = None, br: dict | None = None) -> list[dict]:
    br = valores_brasil() if br is None else br
    rs = valores_rs() if rs is None else rs
    dados = []
    for terr, vals in (("Brasil", br), ("RS", rs)):
        for i, var in enumerate(VARIAVEIS):
            for cnae, par in vals.items():
                dados.append(registro(terr, var, cnae, par[i]))
    return ([dict(CABECALHO)] if com_cabecalho else []) + dados


def valor(comp: pd.DataFrame, terr: str, var: str, nivel: str, item: str, col: str = "valor"):
    sel = comp[(comp["territorio"] == terr) & (comp["variavel"] == var)
               & (comp["nivel"] == nivel) & (comp["item"] == item)]
    assert len(sel) == 1, (terr, var, nivel, item)
    return sel.iloc[0][col]


# --------------------------------------------------------------------------------------------
# normalizar_cnae
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("35 Eletricidade, gás e outras utilidades", "35"),
        ("35.1 Geração, transmissão e distribuição de energia elétrica", "35.1"),
        ("35.11-5 Geração de energia elétrica", "35.11-5"),
        ("  35.11-5   Geração de energia elétrica ", "35.11-5"),
        ("35.115 Geração de energia elétrica", "35.11-5"),
        ("3511-5 Geração de energia elétrica", "35.11-5"),
        ("35115 Geração de energia elétrica", "35.11-5"),
        ("35.11 Geração de energia elétrica", "35.11-5"),
        ("35.11 - 5 - Geração de energia elétrica", "35.11-5"),
        ("Classe 35.14-0 - Distribuição de energia elétrica", "35.14-0"),
        ("DIVISÃO 35 - ELETRICIDADE E GÁS", "35"),
        ("Geração de energia elétrica (35.11-5)", "35.11-5"),
        ("351 Geração, transmissão e distribuição", "35.1"),
        ("35.20-4 Produção de gás; processamento de gás natural", "35.20-4"),
        ("3530 Produção e distribuição de vapor", "35.30-1"),
        ("3511-5/01 Geração de energia elétrica", "3511-5/01"),
        ("Total", None),
        ("", None),
        (None, None),
    ],
)
def test_normalizar_cnae(texto, esperado):
    assert normalizar_cnae(texto) == esperado


# --------------------------------------------------------------------------------------------
# ler_cempre_sidra
# --------------------------------------------------------------------------------------------
def test_ler_formato_longo_e_sigilo():
    df = ler_cempre_sidra(json_sidra())
    assert list(df.columns[:6]) == ["territorio", "variavel", "cnae", "descricao", "valor", "sigiloso"]
    assert len(df) == 2 * 2 * 10
    assert set(df["territorio"]) == {"Brasil", "RS"}
    assert set(df["variavel"]) == {"pessoal_ocupado", "salarios_mil"}
    assert set(df["cnae"]) == set(NOMES)
    idx = df.set_index(["territorio", "variavel", "cnae"])
    assert idx.loc[("Brasil", "pessoal_ocupado", "35.11-5"), "valor"] == 39913
    assert idx.loc[("Brasil", "salarios_mil", "35.30-1"), "valor"] == 34747
    assert idx.loc[("RS", "salarios_mil", "35.1"), "valor"] == 834364
    assert idx.loc[("RS", "pessoal_ocupado", "35.11-5"), "descricao"] == NOMES["35.11-5"]
    # classes sigilosas no RS: NaN e marcadas
    for c in ("35.12-3", "35.13-1", "35.20-4", "35.30-1"):
        assert np.isnan(idx.loc[("RS", "pessoal_ocupado", c), "valor"])
        assert bool(idx.loc[("RS", "pessoal_ocupado", c), "sigiloso"])
    assert not df.loc[df["territorio"] == "Brasil", "sigiloso"].any()
    # o código numérico do SIDRA é só informativo (embaralhado aqui)
    assert idx.loc[("Brasil", "pessoal_ocupado", "35.11-5"), "codigo_sidra"] == CODIGO_SIDRA["35.11-5"]
    assert df.attrs["fonte"].startswith("IBGE")


def test_ler_simbolos_especiais():
    rs = valores_rs()
    rs["35.12-3"] = ("-", "-")       # zero absoluto
    rs["35.13-1"] = ("..", "...")    # não se aplica / não disponível
    df = ler_cempre_sidra(json_sidra(rs=rs)).set_index(["territorio", "variavel", "cnae"])
    assert df.loc[("RS", "pessoal_ocupado", "35.12-3"), "valor"] == 0.0
    assert not df.loc[("RS", "pessoal_ocupado", "35.12-3"), "sigiloso"]
    assert np.isnan(df.loc[("RS", "pessoal_ocupado", "35.13-1"), "valor"])
    assert not df.loc[("RS", "pessoal_ocupado", "35.13-1"), "sigiloso"]
    assert np.isnan(df.loc[("RS", "salarios_mil", "35.13-1"), "valor"])


@pytest.mark.parametrize(
    "bruto, esperado, sigiloso",
    [
        ("12509", 12509.0, False),
        (" 12509 ", 12509.0, False),
        ("862439,5", 862439.5, False),
        ("1.234.567", 1234567.0, False),       # separador de milhar
        ("1.234.567,5", 1234567.5, False),
        ("x", np.nan, True),
        (" X ", np.nan, True),
        ("–", 0.0, False),                # travessão como zero
    ],
)
def test_valor_sidra_formatos(bruto, esperado, sigiloso):
    from mip.externos.cempre import _valor_sidra

    v, s, reconhecido = _valor_sidra(bruto)
    assert reconhecido
    assert s is sigiloso
    if np.isnan(esperado):
        assert np.isnan(v)
    else:
        assert v == esperado


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "latin-1"])
def test_ler_arquivo_com_encodings(tmp_path, encoding):
    arq = tmp_path / "cempre.json"
    arq.write_bytes(json.dumps(json_sidra(), ensure_ascii=False).encode(encoding))
    df = ler_cempre_sidra(arq)
    ref = ler_cempre_sidra(json_sidra())
    pd.testing.assert_frame_equal(df, ref)
    # também como texto JSON e como str do caminho
    pd.testing.assert_frame_equal(ler_cempre_sidra(str(arq)), ref)
    pd.testing.assert_frame_equal(ler_cempre_sidra(json.dumps(json_sidra())), ref)


def test_ler_sem_cabecalho_identifica_pelo_conteudo():
    com = ler_cempre_sidra(json_sidra())
    sem = ler_cempre_sidra(json_sidra(com_cabecalho=False))
    pd.testing.assert_frame_equal(com[["territorio", "variavel", "cnae", "valor", "sigiloso"]],
                                  sem[["territorio", "variavel", "cnae", "valor", "sigiloso"]])


def test_ler_cabecalho_sem_acento_e_maiusculas_e_dimensoes_em_outra_ordem():
    # cabeçalho em maiúsculas e sem acento; CNAE em D1 e território em D4
    troca = {"D1": "D4", "D4": "D1"}

    def renomear(k: str) -> str:
        return troca.get(k[:2], k[:2]) + k[2:] if k[:2] in troca else k

    registros = []
    for i, r in enumerate(json_sidra()):
        novo = {renomear(k): v for k, v in r.items()}
        if i == 0:
            novo = {k: v.upper().replace("Í", "I").replace("Ç", "C").replace("Õ", "O")
                    .replace("Ô", "O").replace("Á", "A").replace("Ó", "O").replace("Ê", "E")
                    for k, v in novo.items()}
            novo["V"] = "  VALOR "
        registros.append(novo)
    df = ler_cempre_sidra(registros)
    ref = ler_cempre_sidra(json_sidra())
    pd.testing.assert_frame_equal(df[["territorio", "variavel", "cnae", "valor"]],
                                  ref[["territorio", "variavel", "cnae", "valor"]])


def test_ler_csv_longo_com_separador_ponto_e_virgula_e_decimal_virgula(tmp_path):
    registros = json_sidra()
    cab, dados = registros[0], registros[1:]
    tabela = pd.DataFrame(dados).rename(columns=cab)  # descrições como nomes de coluna
    tabela["Valor"] = tabela["Valor"].map(lambda v: v if v in ("X", "-", "..", "...") else v + ",0")
    arq = tmp_path / "cempre.csv"
    # o nome da classe 35.20-4 tem ';' e sai entre aspas
    arq.write_bytes(tabela.to_csv(sep=";", index=False).encode("latin-1"))
    df = ler_cempre_sidra(arq)
    ref = ler_cempre_sidra(json_sidra())
    pd.testing.assert_frame_equal(df[["territorio", "variavel", "cnae", "valor", "sigiloso"]],
                                  ref[["territorio", "variavel", "cnae", "valor", "sigiloso"]])


def test_ler_filtra_ano_e_ignora_outras_variaveis():
    registros = json_sidra()
    extra = registro("Brasil", VARIAVEIS[0], "35.11-5", 1, ano="2018")
    outra_var = registro("Brasil", ("708", "Pessoal ocupado assalariado", "Pessoas"), "35.11-5", 5)
    with pytest.warns(UserWarning, match="variáveis ignoradas"):
        df = ler_cempre_sidra(registros + [extra, outra_var])
    assert len(df) == 40
    with pytest.raises(ValueError, match="ano 2020 ausente"):
        ler_cempre_sidra(registros, ano=2020)


def test_ler_erros_de_formato():
    registros = json_sidra()
    # sem a dimensão CNAE
    sem_cnae = [{k: v for k, v in r.items() if not k.startswith("D4")} for r in registros]
    with pytest.raises(ValueError, match="cnae.*Campos disponíveis"):
        ler_cempre_sidra(sem_cnae)
    # célula repetida com valores diferentes
    dup = registro("Brasil", VARIAVEIS[0], "35.11-5", 1)
    with pytest.raises(ValueError, match="repetidas"):
        ler_cempre_sidra(registros + [dup])
    with pytest.raises(ValueError):
        ler_cempre_sidra([])


# --------------------------------------------------------------------------------------------
# composicao_cempre
# --------------------------------------------------------------------------------------------
@pytest.fixture
def comp() -> pd.DataFrame:
    return composicao_cempre(ler_cempre_sidra(json_sidra()))


@pytest.mark.parametrize("i, var", [(0, "pessoal_ocupado"), (1, "salarios_mil")])
def test_rs_por_diferenca_e_proporcao_nacional(comp, i, var):
    tra_com = RS["35.1"][i] - RS["35.11-5"][i] - RS["35.14-0"][i]
    gas_vap = RS["35"][i] - RS["35.1"][i]
    br_tra, br_com = BR["35.12-3"][i], BR["35.13-1"][i]
    br_gas, br_vap = BR["35.20-4"][i], BR["35.30-1"][i]
    esperado = {
        "geracao": RS["35.11-5"][i],
        "distribuicao": RS["35.14-0"][i],
        "transmissao": tra_com * br_tra / (br_tra + br_com),
        "comercio": tra_com * br_com / (br_tra + br_com),
        "gas": gas_vap * br_gas / (br_gas + br_vap),
        "vapor": gas_vap * br_vap / (br_gas + br_vap),
    }
    for item, x in esperado.items():
        assert valor(comp, "RS", var, "classe", item) == pytest.approx(x, abs=TOL)
    # proporção nacional preservada dentro de cada par
    assert valor(comp, "RS", var, "classe", "transmissao") / valor(comp, "RS", var, "classe", "comercio") \
        == pytest.approx(br_tra / br_com, rel=1e-12)
    # métodos
    for item in ("geracao", "distribuicao"):
        assert valor(comp, "RS", var, "classe", item, "metodo") == "direto"
        assert not valor(comp, "RS", var, "classe", item, "por_diferenca")
    for item in ("transmissao", "comercio", "gas", "vapor"):
        assert valor(comp, "RS", var, "classe", item, "metodo") == "diferenca_proporcao_nacional"
        assert valor(comp, "RS", var, "classe", item, "por_diferenca")
    # a soma das seis classes reproduz a divisão 35 do RS
    soma = comp[(comp["territorio"] == "RS") & (comp["variavel"] == var) & (comp["nivel"] == "classe")]["valor"].sum()
    assert soma == pytest.approx(RS["35"][i], abs=TOL)


def test_valores_numericos_da_reparticao(comp):
    # pessoal ocupado: 842 = 12146 − 2217 − 9087; 363 = 12509 − 12146
    assert valor(comp, "RS", "pessoal_ocupado", "classe", "transmissao") == pytest.approx(842 * 16084 / 19230)
    assert valor(comp, "RS", "pessoal_ocupado", "classe", "vapor") == pytest.approx(363 * 756 / 5331)
    # salários: 112131 = 834364 − 203958 − 518275; 28075 = 862439 − 834364
    assert valor(comp, "RS", "salarios_mil", "classe", "comercio") == pytest.approx(112131 * 346415 / 2004107)
    assert valor(comp, "RS", "salarios_mil", "classe", "gas") == pytest.approx(28075 * 524127 / 558874)


@pytest.mark.parametrize("i, var", [(0, "pessoal_ocupado"), (1, "salarios_mil")])
def test_brasil_direto_e_rb_por_diferenca(comp, i, var):
    for item, (classe, _) in CLASSES_CEMPRE.items():
        br = valor(comp, "Brasil", var, "classe", item)
        assert br == BR[classe][i]
        assert valor(comp, "Brasil", var, "classe", item, "metodo") == "direto"
        rs = valor(comp, "RS", var, "classe", item)
        assert valor(comp, "RB", var, "classe", item) == pytest.approx(br - rs, abs=TOL)
        assert valor(comp, "RB", var, "classe", item, "metodo").startswith("brasil_menos_rs")
    assert valor(comp, "RB", var, "classe", "geracao") == BR["35.11-5"][i] - RS["35.11-5"][i]
    assert valor(comp, "RB", var, "classe", "transmissao", "por_diferenca")
    assert not valor(comp, "RB", var, "classe", "geracao", "por_diferenca")


@pytest.mark.parametrize("terr", ["Brasil", "RS", "RB"])
@pytest.mark.parametrize("var", ["pessoal_ocupado", "salarios_mil"])
def test_subsetores_do_motor_e_participacoes(comp, terr, var):
    def cl(item):
        return valor(comp, terr, var, "classe", item)

    assert valor(comp, terr, var, "subsetor", "geracao") == pytest.approx(cl("geracao"))
    assert valor(comp, terr, var, "subsetor", "S38_TRA") == pytest.approx(cl("transmissao"))
    assert valor(comp, terr, var, "subsetor", "S38_DIS") == pytest.approx(cl("comercio") + cl("distribuicao"))
    assert valor(comp, terr, var, "subsetor", "S38_GAS") == pytest.approx(cl("gas") + cl("vapor"))
    for nivel in ("classe", "subsetor"):
        sel = comp[(comp["territorio"] == terr) & (comp["variavel"] == var) & (comp["nivel"] == nivel)]
        assert sel["participacao"].sum() == pytest.approx(1.0, abs=1e-12)
        assert (sel["participacao"] >= 0).all()
        assert (sel["valor"] >= 0).all()


def test_participacoes_subsetores_tabela_larga(comp):
    tab = participacoes_subsetores(comp)
    assert list(tab.columns) == ["territorio", "subsetor", "pessoal_ocupado", "salarios_mil",
                                 "part_pessoal_ocupado", "part_salarios_mil"]
    assert len(tab) == 3 * 4
    assert list(tab["territorio"].unique()) == ["Brasil", "RS", "RB"]
    assert list(tab["subsetor"].iloc[:4]) == ["geracao", "S38_TRA", "S38_DIS", "S38_GAS"]
    somas = tab.groupby("territorio")[["part_pessoal_ocupado", "part_salarios_mil"]].sum()
    assert np.allclose(somas.to_numpy(), 1.0)


def test_uma_classe_do_par_publicada_usa_diferenca_direta():
    rs = valores_rs()
    rs["35.12-3"] = (700, 100000)  # transmissão publicada; comércio continua sigiloso
    comp = composicao_cempre(json_sidra(rs=rs))  # aceita a fonte bruta diretamente
    assert valor(comp, "RS", "pessoal_ocupado", "classe", "transmissao", "metodo") == "direto"
    assert valor(comp, "RS", "pessoal_ocupado", "classe", "comercio") == pytest.approx(842 - 700)
    assert valor(comp, "RS", "pessoal_ocupado", "classe", "comercio", "metodo") == "diferenca"
    assert valor(comp, "RS", "salarios_mil", "classe", "comercio") == pytest.approx(112131 - 100000)


def test_grupo_substitui_classe_de_gas_e_vapor():
    br = valores_brasil()
    del br["35.20-4"]
    del br["35.30-1"]
    rs = valores_rs()
    rs["35.2"] = (300, 20000)   # grupo publicado no RS; classe 35.20-4 sigilosa
    comp = composicao_cempre(json_sidra(br=br, rs=rs))
    assert valor(comp, "Brasil", "pessoal_ocupado", "classe", "gas") == BR["35.20-4"][0]
    assert valor(comp, "Brasil", "pessoal_ocupado", "classe", "gas", "metodo") == "direto_grupo"
    assert valor(comp, "RS", "pessoal_ocupado", "classe", "gas", "metodo") == "direto_grupo"
    assert valor(comp, "RS", "pessoal_ocupado", "classe", "vapor") == pytest.approx(363 - 300)
    assert valor(comp, "RS", "pessoal_ocupado", "classe", "vapor", "metodo") == "diferenca"


def test_composicao_aceita_dataframe_com_rotulos_variados():
    longo = ler_cempre_sidra(json_sidra())
    variado = pd.DataFrame({
        "Território": longo["territorio"].replace({"RS": "Rio Grande do Sul"}),
        "VARIAVEL": longo["variavel"].replace({"pessoal_ocupado": "Pessoal ocupado total"}),
        " CNAE ": longo["descricao"],
        "Valor": longo["valor"].map(lambda x: "X" if np.isnan(x) else f"{x:.0f}".replace(".", ",")),
    })
    a = composicao_cempre(variado)
    b = composicao_cempre(longo)
    pd.testing.assert_frame_equal(a.drop(columns="detalhe"), b.drop(columns="detalhe"))


def test_sigiloso_com_numero_de_preenchimento_e_ignorado():
    # 'X' preenchido com 0 numa planilha: o flag sigiloso manda e o valor sai por diferença
    longo = ler_cempre_sidra(json_sidra())
    preenchido = longo.copy()
    preenchido.loc[preenchido["sigiloso"], "valor"] = 0.0
    a = composicao_cempre(preenchido)
    b = composicao_cempre(longo)
    pd.testing.assert_frame_equal(a, b)
    assert valor(a, "RS", "pessoal_ocupado", "classe", "transmissao") == pytest.approx(842 * 16084 / 19230)


def test_composicao_aceita_codigos_de_territorio_e_dataframe_bruto_do_sidra():
    longo = ler_cempre_sidra(json_sidra())
    ref = composicao_cempre(longo)
    codigos = longo.assign(territorio=longo["territorio"].map({"Brasil": "1", "RS": "43"}))
    pd.testing.assert_frame_equal(composicao_cempre(codigos), ref)
    # DataFrame no formato bruto da API (ex.: sidrapy: cabeçalho na primeira linha)
    bruto = pd.DataFrame(json_sidra())
    pd.testing.assert_frame_equal(composicao_cempre(bruto), ref)
    cmp = comparar_com_referencia(bruto)
    assert cmp["dentro_tolerancia"].all()


def test_conferencia_com_divisao_35():
    comp = composicao_cempre(ler_cempre_sidra(json_sidra()))
    conf = pd.DataFrame(comp.attrs["conferencia_divisao_35"])
    assert set(conf["territorio"]) == {"Brasil", "RS"}
    assert np.allclose(conf["diferenca"], 0.0)
    # gás e vapor publicados no RS com soma (450 / 31000) diferente de 35 − 35.1 (363 / 28075):
    # a soma das classes deixa de bater com a divisão 35 e isso gera aviso
    rs = valores_rs()
    rs["35.20-4"] = (400, 30000)
    rs["35.30-1"] = (50, 1000)
    with pytest.warns(UserWarning, match="difere da divisão 35"):
        composicao_cempre(json_sidra(rs=rs))


def test_composicao_erros():
    longo = ler_cempre_sidra(json_sidra())
    with pytest.raises(ValueError, match="Colunas disponíveis"):
        composicao_cempre(longo.drop(columns="cnae"))
    with pytest.raises(ValueError, match="território"):
        composicao_cempre(longo[longo["territorio"] == "Brasil"])
    # sem 35.1 no RS não há como obter transmissão + comércio
    sem_grupo = longo[~((longo["territorio"] == "RS") & (longo["cnae"] == "35.1"))]
    with pytest.raises(ValueError, match="não\\s+pode ser calculada"):
        composicao_cempre(sem_grupo)
    # diferença negativa: 35.1 menor que geração + distribuição
    rs = valores_rs()
    rs["35.1"] = (100, 100)
    with pytest.raises(ValueError, match="negativ"):
        composicao_cempre(json_sidra(rs=rs))


# --------------------------------------------------------------------------------------------
# comparar_com_referencia
# --------------------------------------------------------------------------------------------
def test_comparar_com_referencia_confere():
    cmp = comparar_com_referencia(ler_cempre_sidra(json_sidra()))
    assert {"territorio", "cnae", "variavel", "esperado", "obtido", "diferenca",
            "dentro_tolerancia"} <= set(cmp.columns)
    n_valores = 2 * (len(BR) + len(RS))
    assert len(cmp) == n_valores + 2 * 4
    assert cmp["dentro_tolerancia"].all()
    assert (cmp["diferenca"].dropna() == 0).all()
    sig = cmp[cmp["esperado_sigiloso"]]
    assert set(sig["cnae"]) == {"35.12-3", "35.13-1", "35.20-4", "35.30-1"}
    assert sig["obtido_sigiloso"].all()


def test_comparar_com_referencia_aponta_diferenca():
    br = valores_brasil()
    br["35.11-5"] = (39900, 5171106)
    rs = valores_rs()
    rs["35.13-1"] = (10, 10)  # deixou de ser sigiloso
    cmp = comparar_com_referencia(json_sidra(br=br, rs=rs)).set_index(["territorio", "cnae", "variavel"])
    assert cmp.loc[("Brasil", "35.11-5", "pessoal_ocupado"), "diferenca"] == -13
    assert not cmp.loc[("Brasil", "35.11-5", "pessoal_ocupado"), "dentro_tolerancia"]
    assert cmp.loc[("Brasil", "35.11-5", "salarios_mil"), "dentro_tolerancia"]
    assert not cmp.loc[("RS", "35.13-1", "pessoal_ocupado"), "dentro_tolerancia"]
    assert cmp.loc[("RS", "35.12-3", "pessoal_ocupado"), "dentro_tolerancia"]


def test_sem_avisos_no_caso_padrao():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        composicao_cempre(ler_cempre_sidra(json_sidra()))
