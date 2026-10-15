"""Estrutura de dados da MIP e layout da planilha.

A classe `MIP` guarda a matriz em arrays numpy, com os rótulos dos setores-região num DataFrame.
Ela serve tanto para a matriz original (136 setores-região) quanto para a desagregada (n qualquer).

Layout da planilha (aba única), para n setores-região (n = 136 na original):
- linhas 1–2: títulos; linhas 3–6: cabeçalhos; colunas A–D: rótulos das linhas
- linhas 7 … 6+n, colunas E … 4+n: consumo intermediário Z
- colunas 5+n … 15+n: demanda final (10 colunas + discrepância estatística); coluna 16+n: total da linha
- linhas abaixo de Z: deslocadas de (n − 136) em relação à original (143 = total do CI, …, 163 = energia)
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------------------------
# Regiões e rótulos usados na planilha
# ---------------------------------------------------------------------------------------------
ROTULOS_REGIAO = {
    # sigla interna: (nome no cabeçalho/linha 3 e coluna A, sigla na linha 4/6, sigla na coluna B)
    "RS": {"nome": "R1: Rio Grande do Sul", "cab": "R1:RS", "linha": "R1: RS"},
    "RB": {"nome": "R2: Restante do Brasil", "cab": "R2:RBR", "linha": "R2: RBR"},
}
REGIAO_POR_ROTULO_LINHA = {v["linha"]: k for k, v in ROTULOS_REGIAO.items()}
REGIAO_POR_ROTULO_CAB = {v["cab"]: k for k, v in ROTULOS_REGIAO.items()}

TITULO_1 = "Tabela 3. Matriz interestadual de insumo-produto, 2019 (valores correntes, milhões R$)"
TITULO_2 = (
    "(Setor x Setor) - agregada em duas regiões: R1 Rio Grande do Sul e R2 Restante do Brasil"
)

# ---------------------------------------------------------------------------------------------
# Colunas de demanda final (EK:EU na original), na ordem da planilha
# ---------------------------------------------------------------------------------------------
COLUNAS_DF = pd.DataFrame(
    [
        # codigo,      nome,                        tipo,      regiao, cab4 (linha 4),            cab5
        ("INV_RS", "Investimento RS", "INV", "RS", "INVESTIMENT DEMAND", "INV"),
        ("INV_RB", "Investimento RB", "INV", "RB", None, "INV"),
        ("FAM_RS", "Famílias RS", "FAM", "RS", "HOUSEHOLD DEMAND", "HH"),
        ("FAM_RB", "Famílias RB", "FAM", "RB", None, "HH"),
        ("GOV_RS", "Governo RS", "GOV", "RS", "GOVERNMENT DEMAND", "GOV"),
        ("GOV_RB", "Governo RB", "GOV", "RB", None, "GOV"),
        ("ISFLSF_RS", "ISFLSF RS", "ISFLSF", "RS", "NPISH DEMAND", "NPISH"),
        ("ISFLSF_RB", "ISFLSF RB", "ISFLSF", "RB", None, "NPISH"),
        ("EXP_RS", "Exportações RS (origem RS)", "EXP", "RS", "FOREING EXPORTS", "EXP"),
        ("EXP_RB", "Exportações RB (origem RB)", "EXP", "RB", None, "EXP"),
        ("DISCREP", "Discrepância estatística", "DISCREP", "", "STATISTICAL DISCREPANCY", None),
    ],
    columns=["codigo", "nome", "tipo", "regiao", "cab4", "cab5"],
)
N_DF = len(COLUNAS_DF)
IDX_DISCREP = N_DF - 1

# ---------------------------------------------------------------------------------------------
# Insumos primários (linhas abaixo de Z) e contas satélite
# ---------------------------------------------------------------------------------------------
# Itens das colunas de setores (linhas 144, 147–149, 151–154 da original)
ITENS_PRIMARIOS = [
    "importacoes",
    "ipi",
    "icms",
    "outros_impostos",
    "va",
    "remuneracoes",
    "eob",
    "impostos_producao",
]
# Itens que também aparecem nas colunas de demanda final (linhas 144 e 147–149)
ITENS_PRIMARIOS_DF = ["importacoes", "ipi", "icms", "outros_impostos"]
ITENS_IMPOSTOS_PRODUTOS = ["ipi", "icms", "outros_impostos"]
ITENS_SATELITE = ["ocupacoes", "co2e", "agua", "energia"]

NOMES_ITENS = {
    "importacoes": "Importações internacionais",
    "ipi": "IPI",
    "icms": "ICMS",
    "outros_impostos": "Outros impostos líquidos sobre produtos",
    "va": "Valor adicionado bruto",
    "remuneracoes": "Remunerações",
    "eob": "Excedente operacional bruto (EOB)",
    "impostos_producao": "Impostos líquidos sobre a produção",
    "vbp": "Valor da produção (VBP)",
    "ocupacoes": "Ocupações",
    "co2e": "Emissões de CO2e",
    "agua": "Uso de água",
    "energia": "Consumo energético",
}
UNIDADES = {
    "ocupacoes": "ocupações",
    "co2e": "t CO2e",
    "agua": "hm3",
    "energia": "mil tep",
}
UNIDADE_MONETARIA = "R$ milhões (2019)"


# ---------------------------------------------------------------------------------------------
# Layout (coordenadas) da planilha
# ---------------------------------------------------------------------------------------------
N_ORIGINAL = 136
LINHA_PRIMEIRO_SETOR = 7
COL_PRIMEIRO_SETOR = 5  # coluna E

# Linhas abaixo de Z, como deslocamento a partir da primeira linha após os setores (143 na original)
DESLOC_LINHAS = {
    "ci_total": 0,  # 143 (fórmula)
    "importacoes": 1,  # 144
    "ci_importacoes": 2,  # 145 (fórmula)
    "titulo_impostos": 3,  # 146
    "ipi": 4,  # 147
    "icms": 5,  # 148
    "outros_impostos": 6,  # 149
    "total_impostos": 7,  # 150 (fórmula)
    "va": 8,  # 151
    "remuneracoes": 9,  # 152
    "eob": 10,  # 153
    "impostos_producao": 11,  # 154
    "vbp": 13,  # 156
    "total_vbp": 14,  # 157 (fórmula)
    "ocupacoes": 15,  # 158
    "check": 16,  # 159 (fórmula)
    "titulo_ambientais": 17,  # 160
    "co2e": 18,  # 161
    "agua": 19,  # 162
    "energia": 20,  # 163
}
ROTULOS_LINHAS_INFERIORES = {
    "importacoes": "Importações internacionais",
    "ci_importacoes": "CI+IMPORTAÇÕES",
    "titulo_impostos": "Impostos, líquidos de subsídios, sobre produto",
    "ipi": "    IPI",
    "icms": "    ICMS",
    "outros_impostos": "    Outros",
    "total_impostos": "TOTAL",
    "va": "Valor adicionado bruto",
    "remuneracoes": "Remunerações",
    "eob": "Excedente operacional bruto (EOB)",
    "impostos_producao": "Impostos, líquidos de subsídios sobre a produção",
    "vbp": "Valor da produção",
    "total_vbp": "TOTAL VBP",
    "ocupacoes": "Fator trabalho (ocupações)",
    "check": "CHECK",
    "titulo_ambientais": "Contas Ambientais",
    "co2e": "Emissões de CO2e (t)",
    "agua": "Uso de Água (hm3)",
    "energia": "Consumo Energético (1000 tep)",
}
# Itens cuja coluna "total" (EV na original) tem valor na planilha
ITENS_COM_TOTAL_EV = ITENS_PRIMARIOS + ["vbp"]


@dataclass(frozen=True)
class Layout:
    """Coordenadas (1-based, como no Excel) de uma planilha com n setores-região."""

    n: int

    @property
    def linha_ini(self) -> int:
        return LINHA_PRIMEIRO_SETOR

    @property
    def linha_fim(self) -> int:
        return LINHA_PRIMEIRO_SETOR + self.n - 1

    @property
    def col_ini(self) -> int:
        return COL_PRIMEIRO_SETOR

    @property
    def col_fim(self) -> int:
        return COL_PRIMEIRO_SETOR + self.n - 1

    @property
    def col_df_ini(self) -> int:
        return self.col_fim + 1

    @property
    def col_df_fim(self) -> int:
        return self.col_fim + N_DF

    @property
    def col_total(self) -> int:
        return self.col_df_fim + 1

    def linha(self, item: str) -> int:
        return self.linha_fim + 1 + DESLOC_LINHAS[item]


# ---------------------------------------------------------------------------------------------
# Classe MIP
# ---------------------------------------------------------------------------------------------
@dataclass
class MIP:
    """Matriz insumo-produto inter-regional setor × setor.

    Atributos (n = número de setores-região):
    - setores: DataFrame com colunas `regiao` (RS/RB), `codigo` (S01…), `nome`, `id` (ex.: RS_S38)
    - Z: consumo intermediário (n × n), linhas = vendedor, colunas = comprador
    - F: demanda final (n × 11), colunas na ordem de COLUNAS_DF (inclui a discrepância estatística)
    - total_linha: total de cada linha (coluna EV na original)
    - X: valor bruto da produção (linha 156 na original)
    - V: insumos primários (8 × n), linhas na ordem de ITENS_PRIMARIOS
    - V_df: importações e impostos nas colunas de demanda final (4 × 11), ordem ITENS_PRIMARIOS_DF
    - X_df: total de cada coluna de demanda final (linha 156 na original), 11 valores
    - S: contas satélite (4 × n), linhas na ordem de ITENS_SATELITE
    - totais_ev: valores da coluna "total" nas linhas de insumos primários e do VBP
    - coef_latentes: coeficientes de subsetores latentes (DataFrame longo) ou None
    - titulo: (linha 1, linha 2)
    """

    setores: pd.DataFrame
    Z: np.ndarray
    F: np.ndarray
    total_linha: np.ndarray
    X: np.ndarray
    V: np.ndarray
    V_df: np.ndarray
    X_df: np.ndarray
    S: np.ndarray
    totais_ev: dict = field(default_factory=dict)
    coef_latentes: pd.DataFrame | None = None
    titulo: tuple = (TITULO_1, TITULO_2)

    def __post_init__(self):
        n = len(self.setores)
        self.setores = self.setores.reset_index(drop=True)
        if "id" not in self.setores.columns:
            self.setores["id"] = self.setores["regiao"] + "_" + self.setores["codigo"]
        formas = {
            "Z": (n, n),
            "F": (n, N_DF),
            "total_linha": (n,),
            "X": (n,),
            "V": (len(ITENS_PRIMARIOS), n),
            "V_df": (len(ITENS_PRIMARIOS_DF), N_DF),
            "X_df": (N_DF,),
            "S": (len(ITENS_SATELITE), n),
        }
        for nome, forma in formas.items():
            arr = np.asarray(getattr(self, nome), dtype=float)
            if arr.shape != forma:
                raise ValueError(f"MIP.{nome}: forma {arr.shape}, esperada {forma}")
            setattr(self, nome, arr)

    # -- atalhos --------------------------------------------------------------------------------
    @property
    def n(self) -> int:
        return len(self.setores)

    @property
    def regioes(self) -> np.ndarray:
        return self.setores["regiao"].to_numpy()

    @property
    def lista_regioes(self) -> list:
        return list(dict.fromkeys(self.setores["regiao"]))

    @property
    def layout(self) -> Layout:
        return Layout(self.n)

    def indice(self, regiao: str, codigo: str) -> int:
        m = (self.setores["regiao"] == regiao) & (self.setores["codigo"] == codigo)
        idx = np.flatnonzero(m.to_numpy())
        if len(idx) != 1:
            raise KeyError(f"setor {regiao} {codigo} não encontrado (ou repetido)")
        return int(idx[0])

    def primario(self, item: str) -> np.ndarray:
        return self.V[ITENS_PRIMARIOS.index(item)]

    def primario_df(self, item: str) -> np.ndarray:
        return self.V_df[ITENS_PRIMARIOS_DF.index(item)]

    def satelite(self, item: str) -> np.ndarray:
        return self.S[ITENS_SATELITE.index(item)]

    def copia(self) -> "MIP":
        return copy.deepcopy(self)

    # -- tabelas rotuladas (para inspeção e exportação) -----------------------------------------
    def tabela_Z(self) -> pd.DataFrame:
        return pd.DataFrame(self.Z, index=self.setores["id"], columns=self.setores["id"])

    def tabela_F(self) -> pd.DataFrame:
        return pd.DataFrame(self.F, index=self.setores["id"], columns=COLUNAS_DF["codigo"])

    def tabela_V(self) -> pd.DataFrame:
        return pd.DataFrame(self.V, index=ITENS_PRIMARIOS, columns=self.setores["id"])

    def tabela_S(self) -> pd.DataFrame:
        return pd.DataFrame(self.S, index=ITENS_SATELITE, columns=self.setores["id"])
