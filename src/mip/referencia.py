"""Cenários e valores de referência da Rodada 01 (Seções 6 e 7 das instruções).

Todos os choques são em R$ milhões na demanda final de setores do RS.
"""
from __future__ import annotations

import pandas as pd

_RENOV = ["S38", "S31", "S29", "S40", "S43", "S56"]
_FOSS = ["S38", "S43", "S19"]

# cenário → {código do setor no RS: valor do choque}
CENARIOS_RS: dict[str, dict[str, float]] = {
    "E1": {"S38": 1000.0},
    "R1": {"S38": 300.0, "S31": 250.0, "S29": 150.0, "S40": 200.0, "S43": 50.0, "S56": 50.0},
    "F1": {"S38": 350.0, "S43": 250.0, "S19": 400.0},
    "R2": {s: 1000.0 / 6 for s in _RENOV},
    "R3": {"S38": 150.0, "S31": 250.0, "S29": 250.0, "S40": 250.0, "S43": 50.0, "S56": 50.0},
    "R4a": {"S38": 450.0, "S31": 150.0, "S29": 100.0, "S40": 100.0, "S43": 150.0, "S56": 50.0},
    "R4b": {"S38": 500.0, "S31": 150.0, "S29": 100.0, "S40": 100.0, "S43": 100.0, "S56": 50.0},
    "F2": {s: 1000.0 / 3 for s in _FOSS},
    "F3": {"S38": 500.0, "S43": 200.0, "S19": 300.0},
}

NOMES_CENARIOS = {
    "E1": "Energia elétrica agregada",
    "R1": "Cesta renovável (base)",
    "F1": "Cesta fóssil (base)",
    "R2": "Renovável balanceada",
    "R3": "Renovável infraestrutura-intensiva",
    "R4a": "Renovável energia/transporte, vetor A",
    "R4b": "Renovável energia/transporte, vetor B",
    "F2": "Fóssil balanceada",
    "F3": "Fóssil energia-intensiva",
}


def choques(cenario: str, regiao: str = "RS") -> dict[tuple[str, str], float]:
    """Choques do cenário no formato {(regiao, codigo): valor}."""
    return {(regiao, cod): v for cod, v in CENARIOS_RS[cenario].items()}


# Resultados esperados (tolerância 0.01 R$ mi e 1 t CO2e; IC e % com 2 casas)
_COLS = [
    "cenario", "dX_total", "dX_RS", "dX_RB", "co2e_total", "co2e_RS", "co2e_RB",
    "IC", "pct_co2e_RB", "pct_indiretas",
]
ESPERADO = pd.DataFrame(
    [
        ("E1", 1925.04, 1357.01, 568.03, 428113.53, 339326.41, 88787.12, 222.39, 20.74, 34.89),
        ("R1", 1959.35, 1391.32, 568.04, 216406.97, 142390.03, 74016.95, 110.45, 34.20, 51.55),
        ("F1", 2120.56, 1373.23, 747.32, 356045.72, 277141.45, 78904.28, 167.90, 22.16, 35.34),
        ("R2", 1920.37, 1399.36, 521.01, 216987.16, 153932.23, 63054.92, 112.99, 29.06, 46.11),
        ("R3", 1969.21, 1396.49, 572.72, 169090.02, 95597.22, 73492.80, 85.87, 43.46, 62.70),
        ("R4a", 1959.49, 1395.81, 563.67, 309794.88, 236133.84, 73661.05, 158.10, 23.78, 39.04),
        ("R4b", 1950.48, 1387.14, 563.34, 304336.55, 228514.51, 75822.04, 156.03, 24.91, 40.31),
        ("F2", 2110.49, 1392.22, 718.27, 381702.86, 306553.93, 75148.94, 180.86, 19.69, 32.87),
        ("F3", 2073.93, 1371.35, 702.58, 375427.26, 294592.52, 80834.74, 181.02, 21.53, 34.97),
    ],
    columns=_COLS,
)

# Tolerâncias de comparação por coluna
TOLERANCIAS = {
    "dX_total": 0.01, "dX_RS": 0.01, "dX_RB": 0.01,
    "co2e_total": 1.0, "co2e_RS": 1.0, "co2e_RB": 1.0,
    "IC": 0.005, "pct_co2e_RB": 0.005, "pct_indiretas": 0.005,
}

# Dez setores que mais emitem no R1
TOP10_R1 = pd.DataFrame(
    [
        (1, "RS", "S38", 357.1, 99554.6, 46.0),
        (2, "RS", "S43", 84.1, 35489.9, 16.4),
        (3, "RB", "S38", 92.0, 23960.2, 11.1),
        (4, "RB", "S27", 46.8, 11392.4, 5.3),
        (5, "RB", "S43", 16.4, 7311.5, 3.4),
        (6, "RB", "S26", 15.3, 6949.7, 3.2),
        (7, "RB", "S28", 34.1, 5082.2, 2.3),
        (8, "RB", "S39", 4.7, 4646.4, 2.1),
        (9, "RB", "S03", 1.0, 3085.0, 1.4),
        (10, "RB", "S01", 3.5, 2649.5, 1.2),
    ],
    columns=["#", "regiao", "codigo", "dX", "co2e", "pct_total"],
)

# Diagnóstico do S38 (Etapa 4): valores de referência e tolerância (pela casa decimal informada)
DIAGNOSTICO_S38 = pd.DataFrame(
    [
        ("VBP", 20942.66, 324387.34, 0.005),
        ("Consumo intermediário (soma da coluna em Z)", 10462.3, 159881.3, 0.05),
        ("Importações", 894.4, 13667.96, 0.05),
        ("VA", 8081.27, 127843.73, 0.005),
        ("CO2e (t)", 5838005.55, 84518349.06, 0.005),
        ("t CO2e por R$ mi", 278.76, 260.55, 0.005),
        ("Ocupações", 15012, 151807, 0.5),
        ("Energia (mil tep)", 503.96, 7805.92, 0.005),
        ("Água (hm3)", 6.79, 67.61, 0.005),
        ("Vendas ao S38 das duas regiões", 5659.7, 96538.4, 0.05),
        ("Vendas ao S38 das duas regiões (% do VBP)", 27.0, 29.8, 0.05),
    ],
    columns=["item", "S38-RS", "S38-RB", "tolerancia"],
)

BLOCO_S38 = {("RS", "RS"): 3057.1, ("RS", "RB"): 2602.5, ("RB", "RS"): 3220.2, ("RB", "RB"): 93318.2}

PESO_S38_CENARIOS = {
    "E1": 92.2, "R1": 57.1, "F1": 39.4, "R2": 32.8, "R3": 38.8,
    "R4a": 58.5, "R4b": 66.0, "F2": 35.1, "F3": 53.0,
}

# Insumos energéticos a destacar na estrutura de insumos do S38
INSUMOS_ENERGETICOS = ["S01", "S03", "S04", "S05", "S09", "S16", "S19", "S20"]
