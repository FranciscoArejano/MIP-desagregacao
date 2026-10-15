"""Rodada 02 — motor com 11 subsetores: testes T6 (roteamento), T7 (latentes), T8 (emissões) e complementares.

Usa uma especificação com valores FICTÍCIOS (tests/auxiliares.py: espec_11_ficticia), pois os parâmetros
reais dependem das fontes externas. O T2 com a especificação real está em tests/test_especificacao_real_v01.py (Rodada 02b).
"""
import numpy as np
import pandas as pd
import pytest

from auxiliares import FONTE, GERACAO_11, NIVEIS_CO2E_FICT, espec_11_ficticia, espec_neutra
from mip import referencia as ref
from mip.desagregacao import (
    Especificacao,
    EspecificacaoInvalida,
    _alocar_com_teto,
    _Grupo,
    _GrupoAlvo,
    _pontua_comprador,
    agregar,
    desagregar,
    tipo_canonico,
)
from mip.estrutura import ITENS_SATELITE
from mip.leitura import ler_mip_original
from mip.modelo import ModeloLeontief

TOL = 1e-6
ARRAYS = ["Z", "F", "X", "total_linha", "V", "V_df", "X_df"]


@pytest.fixture(scope="module")
def mip():
    return ler_mip_original()


@pytest.fixture(scope="module")
def res_e1(mip):
    return desagregar(mip, espec_11_ficticia("residuo"))


def _idx(res, regiao, codigo):
    return res.mip.indice(regiao, codigo)


def _bloco(res, regiao=None):
    m = res.mapa[res.mapa["desagregado"]]
    if regiao:
        m = m[m["regiao"] == regiao]
    return m["indice_novo"].to_numpy()


# ---------------------------------------------------------------------------------------------
# T2 / T3 com 11 subsetores
# ---------------------------------------------------------------------------------------------
def test_t2_reagregacao_11_subsetores(mip, res_e1):
    assert res_e1.mip.n == 156  # 78 setores por região
    ag = agregar(res_e1.mip, res_e1.mapa, mip.setores)
    for nome in ARRAYS:
        np.testing.assert_allclose(getattr(ag, nome), getattr(mip, nome), rtol=0, atol=TOL, err_msg=nome)
    np.testing.assert_allclose(ag.S, mip.S, rtol=0, atol=TOL)
    assert res_e1.ok


def test_t3_neutra_continua_passando(mip):
    res = desagregar(mip, espec_neutra(11, np.random.default_rng(7)))
    base = ModeloLeontief(mip).simular_choques(ref.choques("E1"))
    ch = {("RS", c): 1000.0 / 11 for c in res.especificacao.subsetores["codigo"]}
    nova = ModeloLeontief(res.mip).simular_choques(ch)
    for ind in ["dX_total", "co2e_total", "co2e_RS", "co2e_RB", "co2e_diretas"]:
        assert nova.resumo()[ind] == pytest.approx(base.resumo()[ind], abs=TOL)


# ---------------------------------------------------------------------------------------------
# T6 — roteamento por componentes
# ---------------------------------------------------------------------------------------------
def test_t6_roteamento_por_componentes(mip, res_e1):
    m2, e = res_e1.mip, res_e1.especificacao
    comp = res_e1.extras["componentes_bloco"].set_index("regiao")
    regs = ["RS", "RB"]
    B = {(a, b): mip.Z[mip.indice(a, "S38"), mip.indice(b, "S38")] for a in regs for b in regs}
    for r in regs:
        F = B[(r, "RS")] + B[(r, "RB")]
        T = e.componente(r, "vbp_transmissao")
        G = e.componente(r, "gas_termicas")
        E = F - T - G
        assert comp.loc[r, "E_r (energia = VBP da geração)"] == pytest.approx(E)
        ger = [_idx(res_e1, r, c) for c in GERACAO_11]
        tra = _idx(res_e1, r, "S38_TRA")
        # as vendas da geração de r somam E_r (e são todas à distribuição)
        assert m2.Z[ger].sum() + m2.F[ger].sum() == pytest.approx(E, abs=TOL)
        dis = [_idx(res_e1, q, "S38_DIS") for q in regs]
        assert m2.Z[np.ix_(ger, dis)].sum() == pytest.approx(E, abs=TOL)
        # o VBP da geração é E_r (âncora por componentes)
        assert m2.X[ger].sum() == pytest.approx(E, abs=TOL)
        # as vendas da transmissão de r somam T_r, tudo dentro do bloco
        assert m2.Z[tra].sum() + m2.F[tra].sum() == pytest.approx(T, abs=TOL)
        assert m2.Z[tra, _bloco(res_e1)].sum() == pytest.approx(T, abs=TOL)
        assert m2.X[tra] == pytest.approx(T)
        for q in regs:
            frac = B[(r, q)] / F
            ger_q = [_idx(res_e1, q, c) for c in GERACAO_11]
            # 50/50: metade para a distribuição de q, metade para a geração de q (na proporção do VBP)
            assert m2.Z[tra, _idx(res_e1, q, "S38_DIS")] == pytest.approx(0.5 * T * frac, abs=TOL)
            assert m2.Z[tra, ger_q].sum() == pytest.approx(0.5 * T * frac, abs=TOL)
            xg = m2.X[ger_q]
            np.testing.assert_allclose(m2.Z[tra, ger_q], 0.5 * T * frac * xg / xg.sum(), atol=TOL)
            # energia de r → distribuição de q na proporção F_rq / F_r
            assert m2.Z[np.ix_(ger, [_idx(res_e1, q, "S38_DIS")])].sum() == pytest.approx(E * frac, abs=TOL)
            # os quatro fluxos RS↔RB originais são respeitados
            assert m2.Z[np.ix_(_bloco(res_e1, r), _bloco(res_e1, q))].sum() == pytest.approx(B[(r, q)], abs=TOL)
    # latentes e zerados não pagam transmissão
    for c in ("S38_SOL", "S38_PET", "S38_NUC"):
        assert m2.Z[:, _idx(res_e1, "RS", c)].sum() == 0


def test_t6_gas_as_termicas(mip):
    res = desagregar(mip, espec_11_ficticia("residuo", gas_termicas=100.0), estrito=False)
    m2 = res.mip
    for r in ("RS", "RB"):
        F = sum(mip.Z[mip.indice(r, "S38"), mip.indice(q, "S38")] for q in ("RS", "RB"))
        gas = _idx(res, r, "S38_GAS")
        gns = [_idx(res, q, "S38_GN") for q in ("RS", "RB")]
        assert m2.Z[gas, gns].sum() == pytest.approx(100.0, abs=TOL)
        ger = [_idx(res, r, c) for c in GERACAO_11]
        assert m2.Z[ger].sum() == pytest.approx(F - res.especificacao.componente(r, "vbp_transmissao") - 100.0, abs=TOL)


def test_t6_energia_negativa_da_erro(mip):
    e = espec_11_ficticia()
    e.componentes.loc[(e.componentes["regiao"] == "RS") & (e.componentes["componente"] == "vbp_transmissao"), "valor"] = 6000.0
    with pytest.raises(EspecificacaoInvalida, match="E_r"):
        desagregar(mip, e)


# ---------------------------------------------------------------------------------------------
# T7 — latentes (Solar-RS e Petróleo-RS, espelhos do RB)
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("sub", ["S38_SOL", "S38_PET"])
def test_t7_latentes(mip, res_e1, sub):
    m2 = res_e1.mip
    j = _idx(res_e1, "RS", sub)
    # fluxos-base zero
    assert m2.X[j] == 0
    assert not m2.Z[j].any() and not m2.Z[:, j].any() and not m2.F[j].any()
    assert not m2.V[:, j].any() and not m2.S[:, j].any()
    # coeficientes: somando as origens, iguais aos do espelho (mesmo subsetor no RB)
    jm = _idx(res_e1, "RB", sub)
    a_esp = pd.Series(m2.Z[:, jm] / m2.X[jm], index=m2.setores["codigo"]).groupby(level=0).sum()
    cl = m2.coef_latentes
    cl = cl[(cl["regiao"] == "RS") & (cl["subsetor"] == sub)]
    set_ = cl[cl["tipo_linha"] == "setor"]
    a_lat = set_.groupby("codigo_linha")["coeficiente"].sum()
    a_esp = a_esp[a_esp != 0]
    pd.testing.assert_series_equal(a_lat.sort_index(), a_esp.sort_index(), check_names=False, atol=1e-12, rtol=0)
    # origem de cada insumo: participação das origens na coluna original do S38-RS
    j0 = mip.indice("RS", "S38")
    for cod in ["S05", "S42", "S53"]:
        compras = np.array([mip.Z[mip.indice(q, cod), j0] for q in ("RS", "RB")])
        w = compras / compras.sum()
        lin = set_[set_["codigo_linha"] == cod].set_index("regiao_linha")["coeficiente"]
        tot = lin.sum()
        for q, wq in zip(("RS", "RB"), w):
            assert lin.get(q, 0.0) == pytest.approx(tot * wq, rel=1e-12, abs=1e-15)
    # transmissão: origens pelo bloco S38→S38-RS
    bloco_in = np.array([mip.Z[mip.indice(q, "S38"), j0] for q in ("RS", "RB")])
    lin = set_[set_["codigo_linha"] == "S38_TRA"].set_index("regiao_linha")["coeficiente"]
    assert lin.sum() > 0
    np.testing.assert_allclose([lin.get("RS", 0), lin.get("RB", 0)], lin.sum() * bloco_in / bloco_in.sum(), rtol=1e-12)
    # intensidades satélite = as do espelho
    sat = cl[cl["tipo_linha"] == "satelite"].set_index("codigo_linha")["coeficiente"]
    for k, it in enumerate(ITENS_SATELITE):
        assert sat[it] == pytest.approx(m2.S[k, jm] / m2.X[jm])
    # multiplicador calculável: choque unitário → ΔX próprio = 1, total = Σ coluna de (I − A)^-1
    mod = ModeloLeontief(m2)
    r = mod.simular_choques({("RS", sub): 1.0})
    assert r.dX[j] == pytest.approx(1.0)
    A = mod.A.copy()
    dx = np.linalg.solve(np.eye(m2.n) - A, np.eye(m2.n)[:, j])
    np.testing.assert_allclose(r.dX, dx, atol=1e-12)
    assert r.dX.sum() > 1.0 and mod.L.min() >= -1e-12


def test_t7_nuclear_rs_zerado_sem_latente(res_e1):
    m2 = res_e1.mip
    j = _idx(res_e1, "RS", "S38_NUC")
    assert m2.X[j] == 0 and not m2.Z[:, j].any() and not m2.Z[j].any()
    cl = m2.coef_latentes
    assert not ((cl["regiao"] == "RS") & (cl["subsetor"] == "S38_NUC")).any()
    assert ModeloLeontief(m2).A[:, j].sum() == 0


# ---------------------------------------------------------------------------------------------
# T8 — emissões: E1 e E2 preservam o total; E3 difere exatamente pelo resíduo
# ---------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def variantes(mip):
    return {m: desagregar(mip, espec_11_ficticia(m)) for m in ("residuo", "proporcional", "sem_residuo")}


def test_t8_emissoes(mip, variantes):
    k = ITENS_SATELITE.index("co2e")
    for r in ("RS", "RB"):
        base = mip.S[k, mip.indice(r, "S38")]
        ident = sum(NIVEIS_CO2E_FICT[r].values())
        R = base - ident
        for modo, res in variantes.items():
            idx = _bloco(res, r)
            tot = res.mip.S[k, idx].sum()
            if modo == "sem_residuo":
                assert tot == pytest.approx(base - R, rel=1e-12)  # difere da base exatamente pelo resíduo
            else:
                assert tot == pytest.approx(base, rel=1e-12)
        # E1: níveis do SEEG na geração/SF6; resíduo para DIS e GAS na proporção do VBP
        e1 = variantes["residuo"]
        for c, v in NIVEIS_CO2E_FICT[r].items():
            extra = 0.0
            if c in ("S38_DIS", "S38_GAS"):
                xs = {s: e1.mip.X[_idx(e1, r, s)] for s in ("S38_DIS", "S38_GAS")}
                extra = R * xs[c] / sum(xs.values())
            assert e1.mip.S[k, _idx(e1, r, c)] == pytest.approx(v + extra, rel=1e-12)
        assert e1.mip.S[k, _idx(e1, r, "S38_HID")] == 0
        # E2: total da base na proporção dos níveis (renováveis ficam com zero)
        e2 = variantes["proporcional"]
        for c, v in NIVEIS_CO2E_FICT[r].items():
            assert e2.mip.S[k, _idx(e2, r, c)] == pytest.approx(base * v / ident, rel=1e-12)
        assert e2.mip.S[k, _idx(e2, r, "S38_GAS")] == 0
    # E3 é marcada como "não preserva" e o resto continua re-agregando
    chk = variantes["sem_residuo"].checagens.set_index("checagem")
    assert chk.loc["satelite_co2e_preservado", "status"] == "ALERTA"
    assert "NÃO PRESERVA" in chk.loc["satelite_co2e_preservado", "detalhe"]
    assert chk.loc["reagregacao_S", "status"] == "OK"


def test_t8_residuo_negativo_reduz_identificados(mip):
    grande = {r: {c: v * 10 for c, v in niv.items()} for r, niv in NIVEIS_CO2E_FICT.items()}
    res = desagregar(mip, espec_11_ficticia("residuo", niveis=grande))
    k = ITENS_SATELITE.index("co2e")
    for r in ("RS", "RB"):
        base = mip.S[k, mip.indice(r, "S38")]
        f = base / sum(grande[r].values())
        assert f < 1
        assert res.mip.S[k, _bloco(res, r)].sum() == pytest.approx(base, rel=1e-12)
        assert res.mip.S[k, _idx(res, r, "S38_CAR")] == pytest.approx(grande[r]["S38_CAR"] * f, rel=1e-12)
    assert res.checagens.set_index("checagem").loc["niveis_residuo_nao_negativo", "status"] == "ALERTA"


# ---------------------------------------------------------------------------------------------
# Complementares
# ---------------------------------------------------------------------------------------------
def test_tetos(mip, res_e1):
    tet = res_e1.extras["tetos_atingidos"]
    m2, e = res_e1.mip, res_e1.especificacao
    # PET-RS é latente: todo o refino (S19) comprado pelo S38-RS vai aos demais, na proporção do VBP
    j_pet = _idx(res_e1, "RS", "S38_PET")
    assert ((tet["regiao"] == "RS") & (tet["subsetor"] == "S38_PET")).any()
    for q in ("RS", "RB"):
        assert m2.Z[m2.indice(q, "S19"), j_pet] == 0
    # o teto vale sobre o TOTAL do insumo (todas as origens; S03 + S09 dividem o mesmo teto)
    grupos = {"S04": ["S04"], "S05": ["S05"], "S19": ["S19"], "lenha_bagaco": ["S03", "S09"]}
    tetos = {"S04": ("S38_CAR", 0.40), "S05": ("S38_GN", 0.60), "S19": ("S38_PET", 0.60), "lenha_bagaco": ("S38_BIO", 0.40)}
    for r in ("RS", "RB"):
        for chave, cods in grupos.items():
            sub, frac = tetos[chave]
            j = _idx(res_e1, r, sub)
            total = sum(m2.Z[m2.indice(q, c), j] for q in ("RS", "RB") for c in cods)
            assert total <= frac * m2.X[j] + 1e-9, (r, chave)
            hit = tet[(tet["regiao"] == r) & (tet["insumo_ou_grupo"] == chave) & (tet["subsetor"] == sub)]
            if len(hit):
                assert total == pytest.approx(hit["teto"].item(), abs=1e-9)
                assert hit["valor_pela_regra"].item() > hit["teto"].item()
    # cada fornecedor continua inteiro (re-agregação)
    for q in ("RS", "RB"):
        for c in ("S03", "S04", "S05", "S09", "S19"):
            i = m2.indice(q, c)
            for r in ("RS", "RB"):
                assert m2.Z[i, _bloco(res_e1, r)].sum() == pytest.approx(mip.Z[mip.indice(q, c), mip.indice(r, "S38")])
    assert e.regras_coluna.loc[e.regras_coluna["fornecedor"].isin(["S03", "S09"]), "grupo_teto"].eq("lenha_bagaco").all()


def test_alocar_com_teto_unitario():
    ga = _GrupoAlvo("RS", 0, [0, 1, 2], ["A", "B", "C"], ["geracao", "geracao", "distribuicao"], np.array([0.1, 0.3, 0.6]), True)
    g = _Grupo({}, "fixa_com_teto", {"A": 1.0}, "t", tetos={"A": 0.4})
    X = np.array([10.0, 30.0, 60.0])
    aloc, ating = _alocar_com_teto(g, ga, 100.0, X, "t")
    # A recebe 0.4 × 10 = 4; o excedente (96) vai a B e C na proporção do VBP (30:60)
    np.testing.assert_allclose(aloc, [4.0, 32.0, 64.0])
    assert len(ating) == 1 and ating[0]["excedente"] == pytest.approx(96.0)
    g2 = _Grupo({}, "fixa_com_teto", {"A": 0.5, "C": 0.5}, "t", tetos={"A": 0.4}, destino="sem_teto")
    aloc, _ = _alocar_com_teto(g2, ga, 100.0, X, "t")
    np.testing.assert_allclose(aloc, [4.0, 0.0, 96.0])  # excedente só para C (sem teto na regra)


def test_pontua_comprador():
    assert _pontua_comprador("*", "S10") == 0
    assert _pontua_comprador("S10", "S10") == 3
    assert _pontua_comprador("S08:S37", "S10") == 2
    assert _pontua_comprador("S08:S37", "S43") is None
    assert _pontua_comprador("S08:S37|S43|FAM", "S43") == 2
    assert _pontua_comprador("S08:S37|S43|FAM", "FAM_RS", "FAM") == 2
    assert _pontua_comprador("S08:S37|S43|FAM", "INV_RS", "INV") is None
    assert _pontua_comprador("CI", "S10") == 1 and _pontua_comprador("CI", "FAM_RS", "FAM") is None
    assert _pontua_comprador("DF", "EXP_RB", "EXP") == 1


def test_vendas_fora_do_bloco(res_e1):
    m2 = res_e1.mip
    fora = np.setdiff1d(np.arange(m2.n), _bloco(res_e1))
    for r in ("RS", "RB"):
        for c in GERACAO_11 + ["S38_TRA"]:
            i = _idx(res_e1, r, c)
            assert not m2.Z[i, fora].any() and not m2.F[i].any()  # geração e TRA não vendem fora do bloco
        gas = _idx(res_e1, r, "S38_GAS")
        # o gás só vende à indústria de transformação, ao S43, às famílias e à discrepância
        compradores = {m2.setores["codigo"][j] for j in fora if m2.Z[gas, j] > 0}
        assert compradores <= {f"S{k:02d}" for k in range(8, 38)} | {"S43"}
        from mip.estrutura import COLUNAS_DF

        tipos_df = COLUNAS_DF["tipo"].to_numpy()
        # na demanda final, o gás só vende às famílias e à discrepância (investimento e exportação → DIS)
        assert not m2.F[gas, ~np.isin(tipos_df, ["FAM", "DISCREP"])].any()
        assert m2.F[gas, tipos_df == "FAM"].sum() > 0
        dis = _idx(res_e1, r, "S38_DIS")
        assert m2.F[dis, np.isin(tipos_df, ["INV", "EXP"])].sum() == pytest.approx(
            res_e1.original.F[res_e1.original.indice(r, "S38"), np.isin(tipos_df, ["INV", "EXP"])].sum(), abs=TOL)
        assert m2.X[gas] == pytest.approx(res_e1.especificacao.componente(r, "vbp_gas"), abs=TOL)


def test_tipo_rede_continua_compativel():
    assert tipo_canonico("rede") == "distribuicao"
    assert tipo_canonico("transmissao") == "transmissao"


def test_ancora_componentes_distribuicao_negativa_da_erro(mip):
    e = espec_11_ficticia()
    e.componentes.loc[(e.componentes["regiao"] == "RS") & (e.componentes["componente"] == "vbp_gas"), "valor"] = 16000.0
    with pytest.raises(EspecificacaoInvalida, match="distribuição"):
        desagregar(mip, e)


def test_niveis_sem_configuracao_da_erro(mip):
    e = espec_11_ficticia()
    e.niveis = {}
    with pytest.raises(EspecificacaoInvalida, match="niveis"):
        desagregar(mip, e)


def test_exportacao_11_subsetores(tmp_path, res_e1):
    from mip.leitura import ler_mip

    res_e1.exportar(tmp_path / "m.xlsx", tmp_path / "m.csv")
    lida = ler_mip(tmp_path / "m.xlsx")
    assert lida.n == 156
    np.testing.assert_allclose(lida.Z, res_e1.mip.Z, rtol=1e-14, atol=1e-12)
    import openpyxl

    nomes = openpyxl.load_workbook(tmp_path / "m.xlsx", read_only=True).sheetnames
    for aba in ("componentes_bloco", "tetos_atingidos", "niveis", "coef_latentes", "checagens"):
        assert aba in nomes


# ---------------------------------------------------------------------------------------------
# Regressões dos achados da revisão adversarial (Rodada 02)
# ---------------------------------------------------------------------------------------------
def test_roteamento_com_regiao_nao_desagregada(mip):
    """D2 = só RS: o roteamento manda a parte do RB ao S38-RB agregado e as checagens não acusam FALHA falsa."""
    e = espec_11_ficticia()
    e.regioes = ["RS"]
    e.participacoes = e.participacoes[e.participacoes["regiao"] == "RS"].reset_index(drop=True)
    e.componentes = e.componentes[e.componentes["regiao"] != "RB"].reset_index(drop=True)
    e.regras_primarios = e.regras_primarios[e.regras_primarios["regiao"] != "RB"].reset_index(drop=True)
    e.latentes_espelho = e.latentes_espelho.iloc[0:0]
    res = desagregar(mip, e)  # estrito: não pode levantar
    chk = res.checagens.set_index("checagem")
    assert chk.loc["roteamento_fracao_transmissao", "status"] == "OK"
    m2 = res.mip
    tra = _idx(res, "RS", "S38_TRA")
    T = e.componente("RS", "vbp_transmissao")
    F = sum(mip.Z[mip.indice("RS", "S38"), mip.indice(q, "S38")] for q in ("RS", "RB"))
    frac_rb = mip.Z[mip.indice("RS", "S38"), mip.indice("RB", "S38")] / F
    assert m2.Z[tra, m2.indice("RB", "S38")] == pytest.approx(T * frac_rb)
    assert m2.Z[tra, _idx(res, "RS", "S38_DIS")] == pytest.approx(0.5 * T * (1 - frac_rb))


def test_roteamento_detecta_geracao_vendendo_fora_do_bloco(mip):
    """Geração ou transmissão com venda fora do bloco (ex.: parcela negativa da discrepância) dá FALHA."""
    e = espec_11_ficticia()
    e.regras_linha = e.regras_linha[e.regras_linha["comprador"] != "DISCREP"].reset_index(drop=True)
    e.regras_linha.loc[e.regras_linha["comprador"] == "*", ["regra", "subsetor", "valor"]] = ["proporcional_vbp", "", np.nan]
    res = desagregar(mip, e, estrito=False)
    chk = res.checagens.set_index("checagem")
    assert chk.loc["roteamento_geracao_e_transmissao_nao_vendem_fora", "status"] == "FALHA"


def test_e3_continua_verificando_o_resto(mip, variantes):
    """Na E3 só o S38 pode diferir da base (pelo resíduo); um erro em outro setor continua dando FALHA."""
    from mip.desagregacao import verificar

    res = variantes["sem_residuo"]
    chk = res.checagens.set_index("checagem")
    assert "exatamente o resíduo" in chk.loc["satelite_co2e_preservado", "detalhe"]
    assert chk.loc["reagregacao_S", "status"] == "OK"
    k = ITENS_SATELITE.index("co2e")
    j = res.mip.indice("RS", "S10")
    original = res.mip.S[k, j]
    try:
        res.mip.S[k, j] = original + 1000.0
        chk2 = verificar(res).set_index("checagem")
        assert chk2.loc["reagregacao_S", "status"] == "FALHA"
    finally:
        res.mip.S[k, j] = original
