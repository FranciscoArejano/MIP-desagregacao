"""Funções auxiliares dos testes do motor de desagregação."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mip.desagregacao import Especificacao
from mip.estrutura import COLUNAS_DF, ITENS_PRIMARIOS, ITENS_PRIMARIOS_DF, ITENS_SATELITE, MIP

FONTE = "teste automático"


def subsetores(K: int, tipos: list[str] | None = None, prefixo: str = "S38") -> pd.DataFrame:
    tipos = tipos or (["geracao"] * (K - 2) + ["rede", "gas_utilidades"] if K >= 3 else ["geracao", "rede"][:K])
    return pd.DataFrame(
        {"codigo": [f"{prefixo}_{k:02d}" for k in range(K)], "nome": [f"sub {k}" for k in range(K)], "tipo": tipos}
    )


def participacoes(subs: pd.DataFrame, por_regiao: dict[str, np.ndarray]) -> pd.DataFrame:
    linhas = []
    for r, s in por_regiao.items():
        for c, v in zip(subs["codigo"], s):
            linhas.append((r, c, float(v), FONTE))
    return pd.DataFrame(linhas, columns=["regiao", "subsetor", "participacao", "fonte"])


def espec_neutra(K: int, rng: np.random.Generator, regioes=("RS", "RB"), setor="S38") -> Especificacao:
    """Desagregação neutra: participações positivas arbitrárias e todas as regras proporcionais."""
    subs = subsetores(K, prefixo=setor)
    part = participacoes(subs, {r: rng.dirichlet(np.ones(K)) for r in regioes})
    return Especificacao(
        nome="neutra", setor_alvo=setor, regioes=list(regioes), subsetores=subs, participacoes=part,
        bloco="proporcional",
    )


def espec_aleatoria(rng: np.random.Generator, mip: MIP, regioes=("RS", "RB")) -> Especificacao:
    """Especificação válida aleatória, usando todos os tipos de regra."""
    K = int(rng.integers(3, 8))
    tipos = ["geracao"] * (K - 2) + ["rede", "gas_utilidades"]
    subs = subsetores(K, tipos)
    cod = list(subs["codigo"])
    ger = np.array(tipos) == "geracao"
    bloco = str(rng.choice(["proporcional", "geracao_vende_para_rede"]))
    modo = "participacoes"
    s = {}
    for r in regioes:
        p = rng.dirichlet(np.ones(K))
        if bloco == "geracao_vende_para_rede":
            # geração com participação ≥ 40% (acima da âncora de ~30%) para que as linhas fechem
            p[ger] = 0.4 * p[ger] / p[ger].sum() + 0.2 * p[ger]
            p[~ger] = p[~ger] / p[~ger].sum() * (1 - p[ger].sum())
        s[r] = p
    part = participacoes(subs, s)
    # regras de coluna
    col = [("*", "*", "*", "proporcional_vbp", "", np.nan)]
    for forn in rng.choice([f"S{k:02d}" for k in range(1, 69) if k != 38], size=4, replace=False):
        w = rng.dirichlet(np.ones(K))
        for c, v in zip(cod, w):
            col.append(("*", forn, "*", "fixa", c, v))
    forn = "S04"
    for c in cod:
        col.append(("RS", forn, "RB", "indicador", c, float(rng.uniform(0.5, 3))))
    regras_coluna = pd.DataFrame(col, columns=["regiao", "fornecedor", "regiao_fornecedor", "regra", "subsetor", "valor"])
    regras_coluna["fonte"] = FONTE
    # regras de linha
    lin = [("*", "*", "*", "proporcional_vbp", "", np.nan, False)]
    # participações fixas nas Famílias perto das participações no VBP (±20%), para a linha ser viável
    for r in regioes:
        w = s[r] * rng.uniform(0.8, 1.2, K)
        w = w / w.sum()
        # com geracao_vende_para_rede a margem da geração fora do bloco é pequena: não fixar no RAS
        fixar = bool(rng.random() < 0.5) and bloco == "proporcional"
        for c, v in zip(cod, w):
            lin.append((r, "FAM", "*", "fixa_por_comprador", c, v, fixar))
    lin.append(("RB", "S42", "RS", "somente_rede_e_gas", "", np.nan, False))
    regras_linha = pd.DataFrame(lin, columns=["regiao", "comprador", "regiao_comprador", "regra", "subsetor", "valor", "fixar_no_ras"])
    regras_linha["fonte"] = FONTE
    # regras de primários e satélite
    pri = [("*", "*", "proporcional_vbp", "", np.nan)]
    w = rng.dirichlet(np.ones(K))
    for c, v in zip(cod, w):
        pri.append(("*", "co2e", "fixa", c, v))
    for c in cod:
        pri.append(("RS", "energia", "indicador", c, float(rng.uniform(0.5, 3))))
    regras_primarios = pd.DataFrame(pri, columns=["regiao", "item", "regra", "subsetor", "valor"])
    regras_primarios["fonte"] = FONTE
    return Especificacao(
        nome="aleatória", setor_alvo="S38", regioes=list(regioes), subsetores=subs, participacoes=part,
        bloco=bloco, modo_vbp=modo, regras_coluna=regras_coluna, regras_linha=regras_linha,
        regras_primarios=regras_primarios,
    )


def mip_pequena() -> MIP:
    """MIP de 3 setores (uma região) com A conhecido.

    A = [[0.2, 0.1, 0.0],
         [0.1, 0.2, 0.0],
         [0.0, 0.0, 0.5]],  X = [100, 100, 50]
    """
    X = np.array([100.0, 100.0, 50.0])
    A = np.array([[0.2, 0.1, 0.0], [0.1, 0.2, 0.0], [0.0, 0.0, 0.5]])
    Z = A * X[None, :]
    F = np.zeros((3, len(COLUNAS_DF)))
    F[:, list(COLUNAS_DF["codigo"]).index("FAM_RS")] = X - Z.sum(axis=1)
    va = X - Z.sum(axis=0)
    V = np.zeros((len(ITENS_PRIMARIOS), 3))
    V[ITENS_PRIMARIOS.index("va")] = va
    V[ITENS_PRIMARIOS.index("remuneracoes")] = 0.4 * va
    V[ITENS_PRIMARIOS.index("eob")] = 0.6 * va
    S = np.zeros((len(ITENS_SATELITE), 3))
    S[ITENS_SATELITE.index("co2e")] = [10.0, 20.0, 30.0]  # e = [0.1, 0.2, 0.6]
    S[ITENS_SATELITE.index("ocupacoes")] = [5.0, 5.0, 5.0]
    setores = pd.DataFrame({"regiao": ["RS"] * 3, "codigo": ["S01", "S02", "S03"], "nome": ["um", "dois", "três"]})
    return MIP(
        setores=setores, Z=Z, F=F, total_linha=X.copy(), X=X, V=V,
        V_df=np.zeros((len(ITENS_PRIMARIOS_DF), len(COLUNAS_DF))), X_df=F.sum(axis=0),
        S=S, totais_ev={},
    )


# ---------------------------------------------------------------------------------------------
# Rodada 02: especificação de 11 subsetores com valores FICTÍCIOS (só para testar o motor)
# ---------------------------------------------------------------------------------------------
SUBSETORES_11 = [
    ("S38_HID", "Geração hidrelétrica", "geracao"),
    ("S38_EOL", "Geração eólica", "geracao"),
    ("S38_SOL", "Geração solar fotovoltaica", "geracao"),
    ("S38_BIO", "Geração a biomassa e biogás", "geracao"),
    ("S38_CAR", "Geração a carvão mineral", "geracao"),
    ("S38_GN", "Geração a gás natural", "geracao"),
    ("S38_PET", "Geração a derivados de petróleo", "geracao"),
    ("S38_NUC", "Geração nuclear", "geracao"),
    ("S38_TRA", "Transmissão", "transmissao"),
    ("S38_DIS", "Distribuição e comercialização", "distribuicao"),
    ("S38_GAS", "Gás canalizado e utilidades", "gas_utilidades"),
]
GERACAO_11 = [c for c, _, t in SUBSETORES_11 if t == "geracao"]
# pesos da geração (fictícios); SOL e PET no RS = latentes; NUC no RS = zero
PESOS_GERACAO_FICT = {
    "RS": {"S38_HID": 0.60, "S38_EOL": 0.22, "S38_SOL": 0.0, "S38_BIO": 0.007, "S38_CAR": 0.16,
           "S38_GN": 0.013, "S38_PET": 0.0, "S38_NUC": 0.0},
    "RB": {"S38_HID": 0.65, "S38_EOL": 0.08, "S38_SOL": 0.01, "S38_BIO": 0.03, "S38_CAR": 0.06,
           "S38_GN": 0.12, "S38_PET": 0.01, "S38_NUC": 0.04},
}
NIVEIS_CO2E_FICT = {  # t CO2e (fictícios)
    "RS": {"S38_CAR": 3.0e6, "S38_GN": 7.0e4, "S38_BIO": 1.0e3, "S38_TRA": 1.0e4, "S38_DIS": 9.6e3},
    "RB": {"S38_CAR": 9.7e6, "S38_GN": 2.05e7, "S38_PET": 4.3e6, "S38_BIO": 1.0e4, "S38_TRA": 1.5e5, "S38_DIS": 1.5e5},
}


def espec_11_ficticia(modo_niveis: str = "residuo", gas_termicas: float = 0.0, niveis=None) -> Especificacao:
    subs = pd.DataFrame(SUBSETORES_11, columns=["codigo", "nome", "tipo"])
    part = []
    for r, pesos in PESOS_GERACAO_FICT.items():
        for c, _, tipo in SUBSETORES_11:
            part.append((r, c, pesos.get(c, np.nan) if tipo == "geracao" else np.nan, FONTE))
    part = pd.DataFrame(part, columns=["regiao", "subsetor", "participacao", "fonte"])
    comp = pd.DataFrame(
        [("RS", "vbp_transmissao", 1500.0, FONTE), ("RS", "vbp_gas", 1000.0, FONTE),
         ("RB", "vbp_transmissao", 24000.0, FONTE), ("RB", "vbp_gas", 20000.0, FONTE),
         ("*", "fracao_transmissao_distribuicao", 0.5, FONTE),
         ("RS", "gas_termicas", gas_termicas, FONTE), ("RB", "gas_termicas", gas_termicas, FONTE)],
        columns=["regiao", "componente", "valor", "fonte"],
    )
    col = [("*", "*", "*", "proporcional_vbp", "", np.nan, np.nan, "")]
    col += [("*", "S04", "*", "fixa_com_teto", "S38_CAR", 1.0, 0.40, "demais_vbp")]
    col += [("*", "S05", "*", "fixa_com_teto", "S38_GN", 0.6, 0.60, "demais_vbp"),
            ("*", "S05", "*", "fixa_com_teto", "S38_GAS", 0.4, np.nan, "demais_vbp")]
    col += [("*", "S19", "*", "fixa_com_teto", "S38_PET", 1.0, 0.60, "demais_vbp")]
    col += [("*", f, "*", "fixa_com_teto", "S38_BIO", 1.0, 0.40, "demais_vbp") for f in ("S03", "S09")]
    regras_coluna = pd.DataFrame(col, columns=["regiao", "fornecedor", "regiao_fornecedor", "regra", "subsetor",
                                               "valor", "teto_vbp", "destino_excedente"])
    regras_coluna["fonte"] = FONTE
    lin = [("*", "*", "*", "fixa_por_comprador", "S38_DIS", 1.0, False),
           ("*", "S08:S37|S43|FAM", "*", "somente_distribuicao_e_gas", "", np.nan, False),
           ("*", "INV", "*", "fixa_por_comprador", "S38_DIS", 1.0, False),
           ("*", "EXP", "*", "fixa_por_comprador", "S38_DIS", 1.0, False),
           ("*", "DISCREP", "*", "somente_distribuicao_e_gas", "", np.nan, False)]
    regras_linha = pd.DataFrame(lin, columns=["regiao", "comprador", "regiao_comprador", "regra", "subsetor", "valor",
                                              "fixar_no_ras"])
    regras_linha["fonte"] = FONTE
    pri = [("*", "*", "proporcional_vbp", "", np.nan),
           ("*", "importacoes", "fixa", "S38_DIS", 0.7), ("*", "importacoes", "fixa", "S38_GAS", 0.3)]
    pri += [("*", it, "proporcional_ci", "", np.nan) for it in ("ipi", "icms", "outros_impostos")]
    ind_rem = {"S38_TRA": 1.5, "S38_DIS": 1.2, "S38_GAS": 1.0} | {c: 1.0 for c in GERACAO_11}
    pri += [("*", "remuneracoes", "indicador", c, v) for c, v in ind_rem.items()]
    term = {"S38_CAR": 5.0, "S38_GN": 3.0, "S38_BIO": 2.0, "S38_PET": 4.0, "S38_NUC": 5.0}
    for it in ("energia", "agua"):
        pri += [("*", it, "indicador", c, term.get(c, 0.0)) for c, _, _ in SUBSETORES_11]
    ind_ocup = {"S38_TRA": 2.0, "S38_DIS": 3.0, "S38_GAS": 1.0} | {c: 1.0 for c in GERACAO_11}
    pri += [("*", "ocupacoes", "indicador", c, v) for c, v in ind_ocup.items()]
    for r, niv in (niveis or NIVEIS_CO2E_FICT).items():
        pri += [(r, "co2e", "niveis", c, v) for c, v in niv.items()]
    regras_primarios = pd.DataFrame(pri, columns=["regiao", "item", "regra", "subsetor", "valor"])
    regras_primarios["fonte"] = FONTE
    latentes = pd.DataFrame([("RS", "S38_SOL", "RB", FONTE), ("RS", "S38_PET", "RB", FONTE)],
                            columns=["regiao", "subsetor", "regiao_espelho", "fonte"])
    return Especificacao(
        nome="11 subsetores (fictícia)", setor_alvo="S38", regioes=["RS", "RB"], subsetores=subs,
        participacoes=part, bloco="roteamento_por_componentes", modo_vbp="ancora_componentes",
        regras_coluna=regras_coluna, regras_linha=regras_linha, regras_primarios=regras_primarios,
        latentes_espelho=latentes, componentes=comp,
        niveis={"co2e": {"modo": modo_niveis, "residuo_para": ["S38_DIS", "S38_GAS"]}},
        subsetor_termica_gas="S38_GN",
    )
