"""ONS — geração por usina, 2019 (Seção 5.1 das instruções da Rodada 02).

Arquivo: GERACAO_USINA-2_2019.parquet (dados abertos do ONS, bucket S3). `val_geracao` é a geração
média (MWmed) em cada hora; a soma das horas do ano dá MWh.

Região: `id_estado == "RS"` → RS; `id_estado == "I"` (Itaipu 50 Hz, parcela paraguaia) → importação
(não é geração do RB); demais estados → RB.

Subsetor: pelo rótulo `nom_tipocombustivel` do ONS, com duas exceções tratadas por uma tabela de
reclassificação explícita (arquivo `dados/externos/ons/reclassificacao_usinas_v01.csv`, com justificativa):
"Resíduos Industriais" (classificado pelo SIGA ou pela tabela) e a UTE Canoas (diesel no ONS → gás natural).
Usinas sem classificação ficam como PENDENTE — nada é atribuído por suposição.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

COLUNAS = ["din_instante", "id_estado", "cod_modalidadeoperacao", "nom_tipocombustivel", "nom_usina", "ceg", "val_geracao"]

# Rótulo do ONS → subsetor (Seção 5.1). "Resíduos Industriais" não tem mapeamento direto.
MAPA_COMBUSTIVEL = {
    "hidraulica": "S38_HID",
    "eolica": "S38_EOL",
    "fotovoltaica": "S38_SOL",
    "biomassa": "S38_BIO",
    "carvao": "S38_CAR",
    "gas": "S38_GN",
    "oleo diesel": "S38_PET",
    "oleo combustivel": "S38_PET",
    "nuclear": "S38_NUC",
}
PENDENTE = "PENDENTE"
ORDEM_SUBSETORES_GERACAO = ["S38_HID", "S38_EOL", "S38_SOL", "S38_BIO", "S38_CAR", "S38_GN", "S38_PET", "S38_NUC"]

# Valores de referência das instruções da Rodada 02, Seção 5.1 (GWh; tolerância 0.5) — só para comparação.
REFERENCIA_RS = {"S38_HID": 14542.6, "S38_EOL": 5266.9, "S38_CAR": 2625.2, "S38_GN": 174.6, "S38_BIO": 140.9,
                 "S38_PET": 0.0, "S38_SOL": 0.0, "S38_NUC": 0.0, "Total": 22750.2}
REFERENCIA_RB_ROTULO_ONS = {"Hidráulica": 370796.7, "Eólica": 48122.9, "Carvão": 11338.7, "Gás": 46474.0,
                            "Biomassa": 9271.9, "Óleo (diesel + combustível)": 1974.3, "Fotovoltaica": 4384.6,
                            "Nuclear": 16128.8, "Resíduos Industriais": 9440.4, "Total": 517932.3}
REFERENCIA_ITAIPU_IMPORTACAO = 24402.2
REFERENCIA_RESIDUOS_RB = {"Do Atlântico": 2758.4, "Klabin Celulose": 1777.1, "CSP": 1611.8,
                          "Suzano Maranhão": 1255.4, "CST": 1198.5, "Sol": 839.2}


def _norm(txt) -> str:
    s = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def nucleo_ceg(ceg) -> str | None:
    """Núcleo numérico (6 dígitos) do CEG: 'UTE.GN.RS.028038-0.01' → '028038'; '-' ou vazio → None."""
    if ceg is None or (isinstance(ceg, float) and np.isnan(ceg)):
        return None
    m = re.search(r"(\d{6})-\d", str(ceg))
    return m.group(1) if m else None


def ler_ons(caminho: str | Path) -> pd.DataFrame:
    """Lê o parquet do ONS (só as colunas usadas) e converte `val_geracao` em número."""
    df = pd.read_parquet(caminho, columns=COLUNAS)
    df["val_geracao"] = pd.to_numeric(df["val_geracao"], errors="coerce")
    return df


def ler_reclassificacao(caminho: str | Path) -> pd.DataFrame:
    """Tabela de reclassificação: nom_usina, id_estado, ceg, subsetor, justificativa, fonte."""
    tab = pd.read_csv(caminho, dtype=str, keep_default_na=False, comment="#")
    obrig = {"nom_usina", "id_estado", "subsetor", "justificativa", "fonte"}
    if obrig - set(tab.columns):
        raise ValueError(f"reclassificação sem colunas {sorted(obrig - set(tab.columns))}; tem {list(tab.columns)}")
    return tab


def geracao_por_usina(df: pd.DataFrame, reclassificacao: pd.DataFrame | None = None,
                      siga: pd.DataFrame | None = None) -> pd.DataFrame:
    """Geração anual (GWh) por usina, com região, rótulo do ONS, subsetor e a regra usada.

    Ordem de precedência do subsetor: (1) tabela de reclassificação (casada por nome da usina e UF);
    (2) SIGA, só para "Resíduos Industriais" (DataFrame com colunas nucleo_ceg e subsetor);
    (3) rótulo do ONS. O que sobrar sem subsetor fica PENDENTE.
    """
    horas_nulas = int(df["val_geracao"].isna().sum())
    g = (
        df.assign(val_geracao=df["val_geracao"].fillna(0.0))
        .groupby(["nom_usina", "ceg", "id_estado", "cod_modalidadeoperacao", "nom_tipocombustivel"], dropna=False)
        .agg(mwh=("val_geracao", "sum"), horas=("val_geracao", "size"))
        .reset_index()
    )
    g["gwh"] = g["mwh"] / 1000.0
    g["regiao"] = np.where(g["id_estado"] == "RS", "RS", np.where(g["id_estado"] == "I", "IMPORTACAO", "RB"))
    g["nucleo_ceg"] = g["ceg"].map(nucleo_ceg)
    g["subsetor"] = g["nom_tipocombustivel"].map(lambda x: MAPA_COMBUSTIVEL.get(_norm(x)))
    g["regra"] = np.where(g["subsetor"].notna(), "rótulo nom_tipocombustivel do ONS", "")

    if siga is not None and len(siga):
        mapa_siga = siga.dropna(subset=["subsetor"]).drop_duplicates("nucleo_ceg").set_index("nucleo_ceg")["subsetor"]
        m = (_norm_serie(g["nom_tipocombustivel"]) == "residuos industriais") & g["nucleo_ceg"].isin(mapa_siga.index)
        g.loc[m, "subsetor"] = g.loc[m, "nucleo_ceg"].map(mapa_siga)
        g.loc[m, "regra"] = "SIGA (núcleo do CEG)"

    if reclassificacao is not None and len(reclassificacao):
        chave = reclassificacao.assign(_k=_norm_serie(reclassificacao["nom_usina"]) + "|" + reclassificacao["id_estado"])
        mapa = chave.set_index("_k")
        k = _norm_serie(g["nom_usina"]) + "|" + g["id_estado"]
        m = k.isin(mapa.index)
        g.loc[m, "subsetor"] = k[m].map(mapa["subsetor"])
        g.loc[m, "regra"] = "reclassificação: " + k[m].map(mapa["justificativa"])
        faltam = set(mapa.index) - set(k)
        if faltam:
            raise ValueError(f"usinas da tabela de reclassificação não encontradas no ONS: {sorted(faltam)}")

    g["subsetor"] = g["subsetor"].fillna(PENDENTE).replace("", PENDENTE)
    g.loc[g["subsetor"] == PENDENTE, "regra"] = "sem classificação (pendente: SIGA indisponível ou usina não casada)"
    g.attrs["horas_com_valor_nulo"] = horas_nulas
    cols = ["nom_usina", "ceg", "nucleo_ceg", "id_estado", "regiao", "cod_modalidadeoperacao",
            "nom_tipocombustivel", "subsetor", "regra", "horas", "gwh"]
    return g[cols].sort_values(["regiao", "subsetor", "gwh"], ascending=[True, True, False]).reset_index(drop=True)


def _norm_serie(s: pd.Series) -> pd.Series:
    return s.map(_norm)


def geracao_por_regiao_subsetor(usinas: pd.DataFrame) -> pd.DataFrame:
    """Tabela regiao × subsetor (GWh), incluindo a importação de Itaipu 50 Hz e os pendentes."""
    t = usinas.pivot_table(index="regiao", columns="subsetor", values="gwh", aggfunc="sum", fill_value=0.0)
    cols = [c for c in ORDEM_SUBSETORES_GERACAO + [PENDENTE] if c in t.columns]
    t = t.reindex(columns=cols, fill_value=0.0)
    t["Total"] = t.sum(axis=1)
    return t.reindex([r for r in ["RS", "RB", "IMPORTACAO"] if r in t.index]).reset_index()


def comparar_com_referencia(usinas: pd.DataFrame) -> pd.DataFrame:
    """Esperado × obtido × diferença para as referências da Seção 5.1 (tolerância 0.5 GWh)."""
    linhas = []
    rs = usinas[usinas["regiao"] == "RS"].groupby("subsetor")["gwh"].sum()
    for sub, esp in REFERENCIA_RS.items():
        obt = float(rs.sum()) if sub == "Total" else float(rs.get(sub, 0.0))
        linhas.append(("RS (com exceções)", sub, esp, obt))
    rb = usinas[usinas["regiao"] == "RB"]
    por_rotulo = rb.groupby("nom_tipocombustivel")["gwh"].sum()
    for rot, esp in REFERENCIA_RB_ROTULO_ONS.items():
        if rot == "Total":
            obt = float(por_rotulo.sum())
        elif rot.startswith("Óleo"):
            obt = float(por_rotulo.get("Óleo Diesel", 0.0) + por_rotulo.get("Óleo Combustível", 0.0))
        else:
            obt = float(por_rotulo.get(rot, 0.0))
        linhas.append(("RB (rótulo ONS)", rot, esp, obt))
    imp = float(usinas.loc[usinas["regiao"] == "IMPORTACAO", "gwh"].sum())
    linhas.append(("Importação", "Itaipu 50 Hz", REFERENCIA_ITAIPU_IMPORTACAO, imp))
    ri = rb[_norm_serie(rb["nom_tipocombustivel"]) == "residuos industriais"].groupby("nom_usina")["gwh"].sum()
    for usina, esp in REFERENCIA_RESIDUOS_RB.items():
        linhas.append(("RB Resíduos Industriais", usina, esp, float(ri.get(usina, 0.0))))
    out = pd.DataFrame(linhas, columns=["grupo", "item", "esperado_gwh", "obtido_gwh"])
    out["diferenca"] = out["obtido_gwh"] - out["esperado_gwh"]
    out["tolerancia"] = 0.5
    out["confere"] = out["diferenca"].abs() <= out["tolerancia"]
    return out
