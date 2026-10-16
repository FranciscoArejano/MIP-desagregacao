"""Rodada 03 — decomposição v01 → v02: efeito de cada mudança (D8, D9-a, D9-b, D9-f, D9-r, D10), aplicada em sequência.

Uso (na raiz do repositório, depois de scripts/rodada03_parametros.py):
    python scripts/rodada03_decomposicao.py

Monta especificações intermediárias (em uma pasta temporária) combinando os parâmetros v01 e v02:
  passo 0  v01 (Rodada 02b)
  passo 1  + D8   GWh por fonte = BEN − ONS (pesos P1, energia e água das térmicas)
  passo 2  + (a)  importações do S38-RS → 100% DIS
  passo 3  + (b)  VBP do GAS-RB = preço médio × volume (e o que depende dele: SF6 de TRA/DIS e gás por comprador no
                  RB, já com o teto do gás por comprador da revisão)
  passo 4  + (f)  combustíveis integrais, piso de VBP só pelo κ (a regra das instruções) e remunerações/ocupações
                  seguindo o VBP final
  passo 5  + (r)  reequilíbrio dos insumos não energéticos (EOB ≥ η × VBP), com a extensão de viabilidade do piso
                  (que só existe junto com o reequilíbrio)
  passo 6  + D10  gás por comprador no RS pela Sulgás, com o teto  (= v02)
Saída: resultados/rodada03/decomposicao_v01_v02.csv (um indicador por linha, um passo por coluna).
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from mip.caminhos import PASTA_INTERMEDIARIOS, PASTA_PARAMETROS, PASTA_RESULTADOS  # noqa: E402
from mip.desagregacao import desagregar, ler_especificacao  # noqa: E402
from mip.estrutura import ITENS_PRIMARIOS, ITENS_SATELITE  # noqa: E402
from mip.leitura import ler_mip_original  # noqa: E402
from mip.modelo import ModeloLeontief  # noqa: E402

PAR = PASTA_PARAMETROS
PASSOS = ["v01", "+D8", "+(a)", "+(b)", "+(f)", "+(r)", "+D10 (= v02)"]
GER = ["S38_HID", "S38_EOL", "S38_SOL", "S38_BIO", "S38_CAR", "S38_GN", "S38_PET", "S38_NUC"]
SUBS = GER + ["S38_TRA", "S38_DIS", "S38_GAS"]


def ler(nome):
    return pd.read_csv(PAR / nome, dtype=str, keep_default_na=False)


def montar(pasta: Path, passo: int) -> Path:
    """Especificação do passo (0–6) na pasta temporária."""
    with open(PAR / "especificacao_v02.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    p1, p2 = {k: ler(f"{k}_v01.csv") for k in ("participacoes_vbp", "componentes", "regras_coluna", "regras_linha",
                                                "regras_primarios")}, \
        {k: ler(f"{k}_v02.csv") for k in ("participacoes_vbp", "componentes", "regras_coluna", "regras_linha", "regras_primarios")}
    part = p2["participacoes_vbp"] if passo >= 1 else p1["participacoes_vbp"]
    comp = p1["componentes"].copy()
    col = p2["regras_coluna"] if passo >= 4 else p1["regras_coluna"]
    # linhas: RB pelo v02 a partir de (b) (o alvo de gás depende do VBP do GAS-RB); RS pelo v02 só no D10
    l1, l2 = p1["regras_linha"], p2["regras_linha"]
    if passo < 3:
        lin = l1
    else:
        rs_v01 = l1[l1["regiao"] == "RS"] if passo < 6 else l2[l2["regiao"] == "RS"]
        lin = pd.concat([l2[l2["regiao"] != "RS"], rs_v01], ignore_index=True)
    pri1, pri2 = p1["regras_primarios"], p2["regras_primarios"]
    pri = pri1.copy()
    if passo >= 1:  # energia e água das térmicas com os GWh da D8
        pri = pd.concat([pri[~pri["item"].isin(["energia", "agua"])], pri2[pri2["item"].isin(["energia", "agua"])]], ignore_index=True)
    if passo >= 2:  # (a)
        pri = pd.concat([pri[~((pri["regiao"] == "RS") & (pri["item"] == "importacoes"))],
                         pri2[(pri2["regiao"] == "RS") & (pri2["item"] == "importacoes")]], ignore_index=True)
    if passo >= 3:  # (b): VBP do GAS-RB e o SF6 (repartido pelo VBP da DIS)
        comp = p2["componentes"]
        sf6 = lambda t: (t["item"] == "co2e") & t["subsetor"].isin(["S38_TRA", "S38_DIS"])  # noqa: E731
        pri = pd.concat([pri[~sf6(pri)], pri2[sf6(pri2)]], ignore_index=True)
    if passo >= 4:  # (f): remunerações e ocupações seguindo o VBP final (fixa_por_tipo)
        it = pri["item"].isin(["remuneracoes", "ocupacoes"])
        pri = pd.concat([pri[~it], pri2[pri2["item"].isin(["remuneracoes", "ocupacoes"])]], ignore_index=True)
    arqs = {}
    for k, df in (("participacoes_vbp", part), ("componentes", comp), ("regras_coluna", col), ("regras_linha", lin),
                  ("regras_primarios", pri)):
        df.to_csv(pasta / f"{k}_p{passo}.csv", index=False)
        arqs[k] = f"{k}_p{passo}.csv"
    for k in ("subsetores", "latentes_espelho"):
        shutil.copy(PAR / f"{k}_v02.csv", pasta / f"{k}_v02.csv")
        arqs[k] = f"{k}_v02.csv"
    cfg["arquivos"] = arqs
    cfg["nome"] = f"decomposição v01 → v02, passo {passo} ({PASSOS[passo]})"
    if passo < 4:
        cfg.pop("piso_vbp", None)
    if passo < 5:
        cfg.pop("reequilibrio", None)
        if "piso_vbp" in cfg:
            cfg["piso_vbp"].pop("viabilidade_eta", None)
    destino = pasta / f"especificacao_p{passo}.yaml"
    with open(destino, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
    return destino


def indicadores(res, gwh_v01, gwh_v02, passo) -> dict:
    m = res.mip
    ip = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}
    co2 = m.S[ITENS_SATELITE.index("co2e")]
    gwh = gwh_v01 if passo == 0 else gwh_v02
    mod = ModeloLeontief(m)
    mult, emult = mod.L.sum(axis=0), mod.e @ mod.L
    d = {}
    for r in ("RS", "RB"):
        for s in SUBS:
            k = m.indice(r, s)
            x = m.X[k]
            d[f"VBP {r} {s}"] = x
            if x > 0:
                d[f"EOB/VBP {r} {s}"] = m.V[ip["eob"], k] / x
            if s in GER and gwh[r].get(s, 0) > 0:
                d[f"GWh {r} {s}"] = gwh[r][s]
                d[f"R$/MWh {r} {s}"] = x * 1e6 / (gwh[r][s] * 1000)
                if s in ("S38_CAR", "S38_GN", "S38_PET", "S38_BIO"):
                    d[f"t CO2e/MWh E1 {r} {s}"] = co2[k] / (gwh[r][s] * 1000)
            if r == "RS" and (x > 0 or (m.coef_latentes is not None and
                                         ((m.coef_latentes["regiao"] == "RS") & (m.coef_latentes["subsetor"] == s)).any())):
                d[f"multiplicador de produção RS {s}"] = mult[k]
                d[f"multiplicador de emissões (t/R$ mi) RS {s}"] = emult[k]
    sub = res.mapa.loc[res.mapa["desagregado"], "indice_novo"].to_numpy()
    prod = [k for k in sub if m.X[k] > 0]
    d["EOB/VBP mínimo (subsetores com produção)"] = min(m.V[ip["eob"], k] / m.X[k] for k in prod)
    d["nº de subsetores com EOB < 0"] = sum(m.V[ip["eob"], k] < -1e-9 for k in prod)
    d["checagens (OK/ALERTA/FALHA)"] = "/".join(str((res.checagens["status"] == s).sum()) for s in ("OK", "ALERTA", "FALHA"))
    return d


def main():
    mip = ler_mip_original()
    g1 = pd.read_csv(PASTA_INTERMEDIARIOS / "geracao_2019_regiao_subsetor_v02.csv")
    gwh_v01 = {r: g1[g1["regiao"] == r][GER].sum().to_dict() for r in ("RS", "RB")}
    g2 = pd.read_csv(PASTA_INTERMEDIARIOS / "geracao_2019_regiao_subsetor_v03.csv").set_index("regiao")
    gwh_v02 = {r: g2.loc[r, GER].astype(float).to_dict() for r in ("RS", "RB")}
    cols = {}
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        for passo in range(len(PASSOS)):
            espec = ler_especificacao(PAR / "especificacao_v01.yaml") if passo == 0 else ler_especificacao(montar(pasta, passo))
            res = desagregar(mip, espec, estrito=False)
            cols[PASSOS[passo]] = indicadores(res, gwh_v01, gwh_v02, passo)
            print(f"[{PASSOS[passo]}] checagens {cols[PASSOS[passo]]['checagens (OK/ALERTA/FALHA)']}; "
                  f"EOB/VBP mín {cols[PASSOS[passo]]['EOB/VBP mínimo (subsetores com produção)']:.4f}")
    tab = pd.DataFrame(cols)
    tab.index.name = "indicador"
    # conferência: o passo 6 tem de ser igual à v02 publicada
    v02 = desagregar(mip, ler_especificacao(PAR / "especificacao_v02.yaml"), estrito=False)
    ref = indicadores(v02, gwh_v01, gwh_v02, 6)
    dif = max(abs(float(ref[k]) - float(tab.loc[k, PASSOS[-1]])) for k in ref if isinstance(ref[k], (int, float, np.floating)))
    print(f"[decomposição] passo final × v02: diferença máxima {dif:.2e}")
    if dif > 1e-6:
        raise SystemExit("o último passo da decomposição não reproduz a v02")
    tab.to_csv(PASTA_RESULTADOS / "rodada03" / "decomposicao_v01_v02.csv")


if __name__ == "__main__":
    main()
