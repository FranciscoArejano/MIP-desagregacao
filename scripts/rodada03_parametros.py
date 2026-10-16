"""Rodada 03 — parâmetros da MIP v02 (D8, D9 = (a) + (b) + (f) + (r), D10).

Uso (na raiz do repositório, depois de scripts/rodada02.py e scripts/rodada03.py):
    python scripts/rodada03_parametros.py

Entradas:
- MIP original (dados/original/)
- dados/intermediarios/geracao_2019_regiao_subsetor_v03.csv (D8: Brasil = BEN, RS = ONS, RB = Brasil − RS)
- dados/intermediarios/precos_2019_subsetor_v01.csv, cempre_2019_composicao_v01.csv, seeg_2019_emissoes_v01.csv,
  ben_2019_gas_natural_por_setor_v01.csv (Rodada 02b); ben_2019_consumo_especifico_v02.csv e
  ben_2019_gas_eletricidade_por_setor_v01.csv (scripts/rodada03.py)
- dados/externos/valores_documentais_v02.csv (RAP, θ, Sulgás, MME, Comex, Angra, TUST; preço médio do gás, se houver)
- dados/externos/gas/sulgas_segmentos_2019_v01.csv (Nota 18 das demonstrações da Sulgás 2019; D10)

Saídas (todas com coluna `fonte`), em parametros/:
- especificacao_v02.yaml (principal: P1 + E1 + D9, κ = 0.70, η = 0.10) e as variantes _P2, _E2, _E3, _k060, _k080,
  _eta005, _sem_viabilidade e _gas_sulgas (com componentes/regras_linha/regras_primarios_v02_gas_sulgas.csv);
- subsetores_v02.csv, participacoes_vbp_v02.csv (P1) e _v02_P2.csv, componentes_v02.csv, regras_coluna_v02.csv,
  regras_linha_v02.csv, regras_primarios_v02.csv, latentes_espelho_v02.csv, correspondencia_ben_mip_v02.csv;
- quadro_parametros_v02.xlsx: cada número, com unidade, fonte e cálculo.

Mudanças em relação à v01 (instruções da Rodada 03, Seção 2):
- D8: GWh por fonte = BEN 2020 (Brasil) − ONS (RS).
- D9-a: importações do S38-RS → 100% DIS (no RB continua a regra do Comex).
- D9-b: VBP do GAS-RB = preço médio do gás (R$/m³) × volume não térmico do RB (MME).
- D9-f: combustíveis integrais (S04 → CAR; S05 → GN por θ, sem teto, resto ao GAS; gás importado → GN por θ no RB;
  S19 → PET no RB e, no RS, aos demais na proporção do VBP; S03 + S09 → BIO) e piso VBP_k ≥ combustível_k ÷ κ
  (κ = 0.70, HIPÓTESE), aplicado pelo motor (`piso_vbp`). Extensão de viabilidade: o piso também garante que os
  custos fixos + η × VBP cabem no VBP (ver o relatório da Rodada 03).
- D9-r: reequilíbrio dos insumos não energéticos (RAS) com EOB mínimo η = 0.10 (`reequilibrio`, no motor).
- D10: gás por comprador no RS pela estrutura de receita da Sulgás (Nota 18); no RB, o BEN nacional (como na v01).
- Revisão da Rodada 03: teto do gás por comprador (W_MAX_GAS = 0.90 das compras ao S38, HIPÓTESE), com o excedente
  redistribuído no mesmo grupo (D10 no RS; indústria do BEN no RB) ou, se o grupo inteiro estiver no teto, entre os
  demais compradores da região; consumo específico do PET com 'outras não
  renováveis' (ben_2019_consumo_especifico_v02.csv); variante _gas_sulgas (VBP do GAS-RB pelo preço da Sulgás);
  variantes κ sem a extensão de viabilidade.
- Remunerações e ocupações: composição do CEMPRE com a geração repartida na proporção do VBP final (`fixa_por_tipo`).
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from mip.caminhos import PASTA_EXTERNOS, PASTA_INTERMEDIARIOS, PASTA_PARAMETROS  # noqa: E402
from mip.estrutura import COLUNAS_DF  # noqa: E402
from mip.exportacao import salvar_tabelas  # noqa: E402
from mip.leitura import ler_mip_original  # noqa: E402

INT = PASTA_INTERMEDIARIOS
PAR = PASTA_PARAMETROS
DOCS = PASTA_EXTERNOS / "valores_documentais_v02.csv"
SULGAS_SEG = PASTA_EXTERNOS / "gas" / "sulgas_segmentos_2019_v01.csv"
REGIOES = ["RS", "RB"]
V = "v02"

KAPPA = 0.70  # HIPÓTESE das instruções (D9-f): participação máxima do combustível na receita das térmicas
ETA = 0.10    # HIPÓTESE das instruções (D9-r): EOB mínimo ÷ VBP
ALERTA_MULTIPLICADOR = 2.2  # Seção 4 da Rodada 03
W_MAX_GAS = 0.90  # HIPÓTESE (revisão da Rodada 03): gás ≤ 90% das compras de cada comprador ao S38
M3_POR_TEP_GAS = 1e7 / 8800  # BEN: gás natural seco, 8800 kcal/m³ (1 tep = 10^7 kcal)
MWH_POR_TEP = 1 / 0.086      # BEN: 1 MWh = 0.086 tep

SUBSETORES = [
    ("S38_HID", "Geração hidrelétrica (UHE, PCH, CGH)", "geracao"),
    ("S38_EOL", "Geração eólica", "geracao"),
    ("S38_SOL", "Geração solar fotovoltaica (centralizada)", "geracao"),
    ("S38_BIO", "Geração a biomassa e biogás", "geracao"),
    ("S38_CAR", "Geração termelétrica a carvão mineral", "geracao"),
    ("S38_GN", "Geração termelétrica a gás natural", "geracao"),
    ("S38_PET", "Geração termelétrica a derivados de petróleo", "geracao"),
    ("S38_NUC", "Geração nuclear", "geracao"),
    ("S38_TRA", "Transmissão de energia elétrica", "transmissao"),
    ("S38_DIS", "Distribuição e comercialização de energia elétrica", "distribuicao"),
    ("S38_GAS", "Gás natural canalizado e outras utilidades (vapor, água quente)", "gas_utilidades"),
]
GERACAO = [c for c, _, t in SUBSETORES if t == "geracao"]
TERMICAS = ["S38_CAR", "S38_GN", "S38_PET", "S38_BIO", "S38_NUC"]
LATENTES_RS = ["S38_SOL", "S38_PET"]  # D6 = A
COMBUSTIVEIS = {"S38_CAR": ["S04"], "S38_GN": ["S05", "importacoes"], "S38_PET": ["S19"], "S38_BIO": ["S03", "S09"]}
LINHAS_COMBUSTIVEL = ["S04", "S05", "S19", "S03", "S09"]

FONTE_GER = {"RS": "ONS 2019 (dados abertos), sem autoprodução, Canoas → GN (D8: RS pelo ONS)",
             "RB": "EPE, BEN 2020, Tabela 5.4 (serviço público) − RS pelo ONS (D8); PET = diesel + óleo combustível "
                   "+ outras não renováveis; BIO = lenha + biodiesel + outras renováveis"}
FONTE_PRECOS = "Leilões de geração ANEEL até 31/12/2018 corrigidos pelo IPCA (SIDRA 1737), média ponderada pela energia"
FONTE_CEMPRE = "IBGE, CEMPRE 2019 (SIDRA 6450); sigilosos do RS por diferença e proporção nacional; RB = Brasil − RS"
FONTE_SEEG = "SEEG 13.0, Dados nacionais, CO2e (t) GWP-AR5, 2019, Geração de eletricidade (serviço público)"
FONTE_MIP = "MIP NEREUS/USP 2019 (dados/original)"
_F_CORR = "HIPÓTESE: correspondência BEN → 68 setores feita pelo projeto (nomes dos setores do BEN e da MIP)"
# correspondência BEN (consumo final de gás) → compradores da MIP (igual à v01)
CORRESPONDENCIA_BEN = [
    ("RESIDENCIAL", "FAM", _F_CORR + "; famílias = residencial (Seção 6.4 da Rodada 02)"),
    ("RODOVIÁRIO", "S43|FAM", _F_CORR + "; GNV: transporte terrestre e famílias, ∝ compras ao S38"),
    ("COMERCIAL", "S41|S42|S46|S47|S48|S49|S50|S51|S52|S53|S54|S55|S56|S57|S58|S59|S60|S63|S65|S66|S67", _F_CORR),
    ("PÚBLICO", "S39|S61|S62|S64", _F_CORR + "; água e esgoto no setor público do BEN"),
    ("CIMENTO", "S26", _F_CORR),
    ("CERÂMICA", "S26", _F_CORR),
    ("FERRO GUSA E AÇO", "S27", _F_CORR),
    ("FERRO LIGAS", "S27", _F_CORR),
    ("MINERAÇÃO E PELOTIZAÇÃO", "S04|S06|S07", _F_CORR),
    ("NÃO FERROSOS E OUT. METALURG.", "S28", _F_CORR),
    ("QUÍMICA", "S21|S22|S23|S24", _F_CORR),
    ("CONSUMO FINAL NÃO ENERGÉTICO", "S21|S22|S23|S24", _F_CORR + "; matéria-prima da química (fertilizantes, metanol)"),
    ("ALIMENTOS E BEBIDAS", "S08|S09|S10|S11", _F_CORR),
    ("TÊXTIL", "S13", _F_CORR),
    ("PAPEL E CELULOSE", "S17", _F_CORR),
    ("OUTRAS INDÚSTRIAS", "S12|S14|S15|S16|S18|S25|S29|S30|S31|S32|S33|S34|S35|S36|S37", _F_CORR),
    ("SETOR ENERGÉTICO", "", "HIPÓTESE: fora — E&P, refinarias e UPGN usam gás próprio ou comprado do S05, não das distribuidoras"),
    ("AGROPECUÁRIO", "", "consumo zero no BEN 2019"),
    ("FERROVIÁRIO", "", "consumo zero no BEN 2019"),
    ("AÉREO", "", "consumo zero no BEN 2019"),
    ("HIDROVIÁRIO", "", "consumo zero no BEN 2019"),
    ("CONSUMO NÃO IDENTIFICADO", "", "consumo zero no BEN 2019"),
]
BEN_INDUSTRIA = ["CIMENTO", "CERÂMICA", "FERRO GUSA E AÇO", "FERRO LIGAS", "MINERAÇÃO E PELOTIZAÇÃO",
                 "NÃO FERROSOS E OUT. METALURG.", "QUÍMICA", "CONSUMO FINAL NÃO ENERGÉTICO", "ALIMENTOS E BEBIDAS",
                 "TÊXTIL", "PAPEL E CELULOSE", "OUTRAS INDÚSTRIAS"]
# D10 (RS): "consumo industrial de gás do BEN" — sem o consumo final não energético, que no BEN não é do setor industrial
BEN_INDUSTRIA_RS = [x for x in BEN_INDUSTRIA if x != "CONSUMO FINAL NÃO ENERGÉTICO"]
SERVICOS_RS = "|".join(f"S{k}" for k in range(41, 69))  # D10: residencial + comercial → famílias e S41–S68

quadro = []


def anotar(grupo, regiao, item, valor, unidade, fonte, calculo=""):
    quadro.append({"grupo": grupo, "regiao": regiao, "item": item, "valor": valor, "unidade": unidade,
                   "fonte": fonte, "calculo": calculo})
    return valor


def docs() -> pd.DataFrame:
    return pd.read_csv(DOCS, dtype={"parametro": str})


def doc(d: pd.DataFrame, chave: str):
    m = d[d["parametro"] == chave]
    if not len(m) or pd.isna(m["valor"].iloc[0]):
        return None, "não encontrado"
    r = m.iloc[0]
    fonte = f"{r['fonte_instituicao']}, {r['documento']} ({r['localizacao']}); acesso {r['data_acesso_utc']}; {r['url']}"
    return float(r["valor"]), fonte


def exigir(d, chave):
    v, f = doc(d, chave)
    if v is None:
        raise SystemExit(f"{chave} ausente em {DOCS.relative_to(RAIZ)}")
    return v, f


def compras_ao_s38(mip, r: str, codigos: list[str]) -> dict[str, float]:
    """Vendas do S38-r a cada comprador da própria região (setor ou FAM)."""
    i = mip.indice(r, "S38")
    df = list(COLUNAS_DF["codigo"])
    return {k: float(mip.F[i, df.index(f"{k}_{r}")]) if k == "FAM" else float(mip.Z[i, mip.indice(r, k)]) for k in codigos}


def teto_gas(contrib: dict, compra: dict, w_max: float) -> tuple[dict, set]:
    """Teto do gás por comprador (HIPÓTESE W_MAX_GAS) com redistribuição do excedente dentro do grupo.

    contrib = {grupo: {comprador: alvo de gás}}. Quem passa de w_max × compras ao S38 fica no teto; o excedente vai
    aos demais compradores do mesmo grupo, na proporção do alvo; se o grupo inteiro estiver no teto, aos demais
    compradores da região, na proporção do alvo total (grupo '… → demais'). Repete até ninguém passar do teto.
    O total (VBP do GAS) não muda. Devolve (contrib final, compradores no teto).
    """
    c = {g: {k: float(v) for k, v in d.items() if v > 0 and compra.get(k, 0.0) > 0} for g, d in contrib.items()}

    def total(k):
        return sum(d.get(k, 0.0) for d in c.values())

    presos: set = set()
    for _ in range(10 * (len(compra) + 1)):
        todos = sorted({k for d in c.values() for k in d})
        novos = [k for k in todos if k not in presos and total(k) > w_max * compra[k] * (1 + 1e-12)]
        if not novos:
            return c, presos
        excesso = {}
        for k in novos:
            f = w_max * compra[k] / total(k)
            for g, d in c.items():
                if k in d:
                    excesso[g] = excesso.get(g, 0.0) + d[k] * (1 - f)
                    d[k] *= f
            presos.add(k)
        for g, e in excesso.items():
            livres = {k: v for k, v in c[g].items() if k not in presos}
            destino = g
            if not livres:
                livres = {k: total(k) for k in todos if k not in presos}
                destino = f"{g.split(' → ')[0]} → demais (grupo no teto)"
            if not livres:
                raise SystemExit("teto do gás: todos os compradores no teto; o VBP do GAS não cabe nas compras ao S38")
            soma = sum(livres.values())
            c.setdefault(destino, {})
            for k, v in livres.items():
                c[destino][k] = c[destino].get(k, 0.0) + e * v / soma
    raise SystemExit("teto do gás: a redistribuição não estabilizou")


def regras_gas(contrib: dict, compra: dict, r: str, fonte_base: str, lin: list, gas_comp: list, grupos: list):
    alvo0 = {k: sum(d.get(k, 0.0) for d in contrib.values()) for k in compra}
    c, presos = teto_gas(contrib, compra, W_MAX_GAS)
    alvo = {k: sum(d.get(k, 0.0) for d in c.values()) for k in compra}
    if abs(sum(alvo.values()) - sum(alvo0.values())) > 1e-9 * max(1.0, sum(alvo0.values())):
        raise SystemExit(f"teto do gás em {r}: o total mudou")
    for k in sorted(alvo):
        if alvo[k] <= 0 or compra.get(k, 0.0) <= 0:
            continue
        w = alvo[k] / compra[k]
        if k in presos:
            nota = (f"alvo {alvo0[k]:.4f} acima do teto: fica em {W_MAX_GAS} × compras ao S38 = {alvo[k]:.4f} "
                    f"(HIPÓTESE: ≥ {1 - W_MAX_GAS:.2f} das compras ao S38 ficam com a eletricidade; o excedente vai aos "
                    "demais compradores do grupo)")
        elif abs(alvo[k] - alvo0[k]) > 1e-9:
            transb = {g: d[k] for g, d in c.items() if " → demais" in g and d.get(k, 0.0) > 0}
            proprio = alvo[k] - alvo0[k] - sum(transb.values())
            partes = ([f"{proprio:.4f} do excedente do teto no próprio grupo"] if proprio > 1e-9 else []) + \
                [f"{v:.4f} do grupo '{g.split(' → ')[0]}' inteiro no teto (aos demais compradores da região)"
                 for g, v in transb.items()]
            nota = f"alvo {alvo0[k]:.4f} + " + " + ".join(partes) + f" = {alvo[k]:.4f}"
        else:
            nota = f"alvo {alvo[k]:.4f}"
        fonte = (f"{fonte_base}; {nota} ÷ compras ao S38 {compra[k]:.4f}; HIPÓTESE: mesmo preço por unidade de gás "
                 "entre compradores; o GAS só vende na própria região; o RAS fecha o VBP do GAS")
        lin += [(r, k, r, "fixa_por_comprador", "S38_GAS", w, "nao", fonte),
                (r, k, r, "fixa_por_comprador", "S38_DIS", 1 - w, "nao", fonte)]
        gas_comp.append({"regiao": r, "comprador": k, "compras_ao_S38": compra[k], "alvo_gas_original": alvo0[k],
                         "alvo_gas": alvo[k], "participacao_gas": w, "no_teto": k in presos, "fonte": fonte_base})
    tot = sum(alvo0.values())
    for g in dict.fromkeys(list(contrib) + list(c)):
        a0, a1 = sum(contrib.get(g, {}).values()), sum(c.get(g, {}).values())
        grupos.append({"regiao": r, "grupo": g, "alvo_original": a0, "alvo_depois_do_teto": a1,
                       "participacao_original": a0 / tot, "participacao_depois_do_teto": a1 / tot,
                       "compradores_no_teto": ", ".join(sorted(k for k in presos if k in contrib.get(g, {})))})


def main():
    PAR.mkdir(parents=True, exist_ok=True)
    mip = ler_mip_original()
    D = docs()
    X = {r: float(mip.X[mip.indice(r, "S38")]) for r in REGIOES}
    F = {r: float(sum(mip.Z[mip.indice(r, "S38"), mip.indice(q, "S38")] for q in REGIOES)) for r in REGIOES}
    share_X = {r: X[r] / sum(X.values()) for r in REGIOES}
    for r in REGIOES:
        anotar("MIP", r, "VBP do S38 (X_r)", X[r], "R$ mi", FONTE_MIP)
        anotar("MIP", r, "F_r: vendas do S38 ao S38 das duas regiões", F[r], "R$ mi", FONTE_MIP)

    # ---- D8: geração por fonte -------------------------------------------------------------------
    g = pd.read_csv(INT / "geracao_2019_regiao_subsetor_v03.csv").set_index("regiao")
    gwh = {r: {c: float(g.loc[r, c]) for c in GERACAO} for r in REGIOES}
    for r in REGIOES:
        for c in GERACAO:
            anotar("geração (D8)", r, f"GWh {c}", gwh[r][c], "GWh", FONTE_GER[r])
    precos = pd.read_csv(INT / "precos_2019_subsetor_v01.csv").set_index("subsetor")["preco_2019_rs_mwh"].to_dict()
    fonte_preco = {c: FONTE_PRECOS for c in GERACAO}
    nuc, fnuc = doc(D, "preco_nuclear_2019")
    if nuc is not None:
        precos["S38_NUC"], fonte_preco["S38_NUC"] = nuc, fnuc
    for c in GERACAO:
        anotar("preços P1", "*", f"preço 2019 {c}", precos[c], "R$/MWh", fonte_preco[c])

    def participacoes(p2: bool) -> pd.DataFrame:
        linhas = []
        for r in REGIOES:
            for c, _, tipo in SUBSETORES:
                if tipo != "geracao":
                    linhas.append((r, c, np.nan, "não usado (ancora_componentes: VBP por componente/resíduo)"))
                elif r == "RS" and c in LATENTES_RS + ["S38_NUC"]:
                    linhas.append((r, c, 0.0, "produção zero no RS em 2019 (D6 = A: latente; nuclear zerado)"))
                else:
                    peso = gwh[r][c] * (1.0 if p2 else precos[c])
                    linhas.append((r, c, peso, f"GWh ({FONTE_GER[r]})" + ("" if p2 else f" × preço ({fonte_preco[c]})")
                                   + "; o piso de VBP (D9-f) redistribui depois, no motor"))
        return pd.DataFrame(linhas, columns=["regiao", "subsetor", "participacao", "fonte"])

    part_p1, part_p2 = participacoes(False), participacoes(True)

    # ---- transmissão (sem mudança) -----------------------------------------------------------------
    rap_1920, f1920 = exigir(D, "rap_total_ciclo_2019_2020")
    rap_1819, f1819 = exigir(D, "rap_total_ciclo_2018_2019")
    rap = (rap_1819 + rap_1920) / 2
    fonte_rap = (f"média dos ciclos 2018-2019 ({f1819}) e 2019-2020 ({f1920} — FONTE SECUNDÁRIA, não confirmada "
                 "em documento da ANEEL) = ano civil 2019")
    anotar("transmissão", "Brasil", "RAP 2019", rap, "R$ mi", fonte_rap)
    T = {r: rap * share_X[r] for r in REGIOES}
    for r in REGIOES:
        anotar("transmissão", r, "VBP_TRA = T_r", T[r], "R$ mi", fonte_rap + "; × participação no VBP do S38",
               f"RAP × {share_X[r]:.6f}")
    alfa, falfa = exigir(D, "tust_fracao_consumo")
    anotar("transmissão", "*", "fração da RAP paga pela distribuição (α)", alfa, "fração", falfa)

    # ---- gás: θ, Comex, VBP do GAS -----------------------------------------------------------------
    theta = {}
    for r in REGIOES:
        theta[r], ft = exigir(D, f"theta_{r}")
        anotar("gás", r, "θ: gás para termelétricas ÷ gás comprado pelo setor", theta[r], "fração", ft)
    fob = {k: exigir(D, f"comex_fob_2019_{k}") for k in ("2716", "2711_21", "2711_11")}
    s_elet = fob["2716"][0] / sum(v[0] for v in fob.values())
    fonte_imp = "Comex Stat 2019, FOB por NCM: " + "; ".join(v[1] for v in fob.values())
    anotar("importações", "RB", "participação da energia elétrica nas importações de energia (Comex)", s_elet, "fração", fonte_imp)
    anotar("importações", "RS", "importações do S38-RS → 100% DIS (D9-a)", 1.0, "fração",
           "Rodada 03, D9-a: o custo de gás da Sulgás (≈ 679 R$ mi, Nota 22) já é coberto pela compra ao S05 (668.9); "
           "o 'gás importado' da regra nacional do Comex não existe no RS (Comex por UF: gás importado no RS ≈ 0.14 US$ mi)")

    sul, fsul = exigir(D, "sulgas_receita_liquida_2019")
    sul_vol, _ = exigir(D, "sulgas_volume_total_2019")
    sul_serv, _ = exigir(D, "sulgas_volume_servico_2019")
    preco_sul = sul / (sul_vol - sul_serv)
    anotar("gás", "RS", "VBP_GAS = receita operacional líquida da Sulgás 2019", sul, "R$ mi", fsul)
    anotar("gás", "RS", "preço médio da Sulgás 2019 (receita líquida ÷ volume sem 'Serviço')", preco_sul, "R$/m³",
           fsul, f"{sul:.4f} ÷ ({sul_vol} − {sul_serv})")
    dist_sem_term, fdist = exigir(D, "mme_gas_distribuidoras_sem_termeletrico_2019")
    sul_d, _ = exigir(D, "mme_gas_sulgas_2019")
    vol_rb = (dist_sem_term - sul_d) * 365  # milhões m³/ano
    anotar("gás", "RB", "volume não térmico do RB", vol_rb, "milhões m³", fdist,
           f"({dist_sem_term} − Sulgás {sul_d}) × 365")
    p4, fp4 = doc(D, "gas_preco_medio_4_distribuidoras_2019")
    vbp_gas_sul = preco_sul * vol_rb
    anotar("gás", "RB", "VBP_GAS-RB com o preço da Sulgás (1.39)", vbp_gas_sul, "R$ mi", fsul + "; " + fdist,
           f"{preco_sul:.6f} × {vol_rb:.4f}")
    if p4 is not None:
        anotar("gás", "RB", "preço médio ponderado das 4 distribuidoras (Sulgás, Comgás, CEG, Gasmig)", p4, "R$/m³", fp4)
        vbp_gas_rb, fonte_gas_rb = p4 * vol_rb, f"D9-b: preço médio das 4 distribuidoras ({fp4}) × volume não térmico ({fdist})"
        anotar("gás", "RB", "VBP_GAS-RB (D9-b, usado)", vbp_gas_rb, "R$ mi", fonte_gas_rb, f"{p4:.6f} × {vol_rb:.4f}")
    else:
        vbp_gas_rb = vbp_gas_sul
        fonte_gas_rb = (f"D9-b: preço da Sulgás 2019 ({preco_sul:.6f} R$/m³; {fsul}) × volume não térmico do RB "
                        f"({fdist}); preço das 4 distribuidoras não reconferido")
        anotar("gás", "RB", "VBP_GAS-RB (D9-b, usado)", vbp_gas_rb, "R$ mi", fonte_gas_rb)
    vbp_gas = {"RS": sul, "RB": vbp_gas_rb}

    # ---- regras de coluna (D9-f: combustíveis integrais, sem teto) ---------------------------------
    col = [("*", "*", "*", "proporcional_vbp", "", np.nan, np.nan, "", "", "padrão: na proporção do VBP")]
    col += [("*", "S04", "*", "fixa", "S38_CAR", 1.0, np.nan, "", "", "D9-f: S04 (carvão) → 100% CAR, sem teto")]
    for r in REGIOES:
        col += [(r, "S05", "*", "fixa", "S38_GN", theta[r], np.nan, "", "",
                 f"D9-f: S05 → GN por θ_{r} = {theta[r]:.6f}, sem teto; o restante ao GAS"),
                (r, "S05", "*", "fixa", "S38_GAS", 1 - theta[r], np.nan, "", "", f"D9-f: S05 → 1 − θ_{r} ao GAS")]
    col += [("RB", "S19", "*", "fixa", "S38_PET", 1.0, np.nan, "", "", "D9-f: S19 (refino) → 100% PET no RB"),
            ("RS", "S19", "*", "proporcional_vbp", "", np.nan, np.nan, "", "",
             "D9-f: no RS o PET é latente; o S19 vai aos demais subsetores na proporção do VBP")]
    col += [("*", f, "*", "fixa", "S38_BIO", 1.0, np.nan, "", "", "D9-f: S03 e S09 (lenha; bagaço) → 100% BIO, sem teto")
            for f in ("S03", "S09")]
    regras_coluna = pd.DataFrame(col, columns=["regiao", "fornecedor", "regiao_fornecedor", "regra", "subsetor", "valor",
                                               "teto_vbp", "destino_excedente", "grupo_teto", "fonte"])

    # ---- gás por comprador (RB: BEN nacional; RS: Sulgás, D10) com teto por comprador ------------------
    gb = pd.read_csv(INT / "ben_2019_gas_natural_por_setor_v01.csv").set_index("setor_ben")["gas_natural_mil_tep"]
    corr = pd.DataFrame(CORRESPONDENCIA_BEN, columns=["setor_ben", "compradores_mip", "fonte"])
    corr["gas_natural_mil_tep"] = [float(gb.get(x, 0.0)) for x in corr["setor_ben"]]
    corr["entra"] = corr["compradores_mip"] != ""
    tep_total = corr.loc[corr["entra"], "gas_natural_mil_tep"].sum()
    corr["participacao_no_gas_distribuido"] = np.where(corr["entra"], corr["gas_natural_mil_tep"] / tep_total, 0.0)
    todos = sorted({c for x in corr["compradores_mip"] for c in x.split("|") if c})
    compra_rb = compras_ao_s38(mip, "RB", todos)
    fonte_rb = ("BEN 2020 (gás por setor, sem o setor energético) × VBP_GAS_RB, ∝ compras ao S38 dentro de cada setor do "
                "BEN (correspondencia_ben_mip_v02.csv); grupos do teto: indústria (setores industriais do BEN) e cada "
                "um dos demais setores do BEN")

    def contrib_rb(vbp_rb):
        c = {}
        for x in corr[corr["entra"]].itertuples(index=False):
            g = "indústria (BEN)" if x.setor_ben in BEN_INDUSTRIA else x.setor_ben.lower()
            ks = x.compradores_mip.split("|")
            base = sum(compra_rb[k] for k in ks)
            for k in ks:
                c.setdefault(g, {})
                c[g][k] = c[g].get(k, 0.0) + vbp_rb * x.participacao_no_gas_distribuido * compra_rb[k] / base
        return c

    # RS: estrutura de receita da Sulgás (D10)
    seg = pd.read_csv(SULGAS_SEG).set_index("segmento")["receita_liquida_rs"] / 1e6
    fonte_seg = ("Sulgás 2019, Nota 18 (receita líquida por segmento; dados/externos/gas/sulgas_segmentos_2019_v01.csv)")
    grupos_d10 = {
        "indústria + cogeração": float(seg["Industrial"] + seg["Cogeração"]),
        "automotivo": float(seg["Automotivo"]),
        "residencial + comercial": float(seg["Residencial"] + seg["Comercial"]),
        "serviço": float(seg["Serviço"]),
    }
    for nome, v in grupos_d10.items():
        anotar("gás por comprador (RS, D10)", "RS", f"participação: {nome}", v / seg.sum(), "fração", fonte_seg)
    ind = corr[corr["setor_ben"].isin(BEN_INDUSTRIA_RS)]
    todos_rs = sorted({c for x in ind["compradores_mip"] for c in x.split("|")} | {"S43", "FAM", "S19"}
                      | set(SERVICOS_RS.split("|")))
    compra_rs = compras_ao_s38(mip, "RS", todos_rs)
    contrib_rs = {g: {} for g in grupos_d10}
    tep_ind = ind["gas_natural_mil_tep"].sum()
    for x in ind.itertuples(index=False):  # indústria + cogeração ∝ consumo industrial de gás do BEN, por ramo
        ks = x.compradores_mip.split("|")
        base = sum(compra_rs[k] for k in ks)
        for k in ks:
            d_ = contrib_rs["indústria + cogeração"]
            d_[k] = d_.get(k, 0.0) + (sul * grupos_d10["indústria + cogeração"] / seg.sum() * (x.gas_natural_mil_tep / tep_ind)
                                      * compra_rs[k] / base)
    for nome, ks in (("automotivo", ["S43", "FAM"]), ("residencial + comercial", ["FAM"] + SERVICOS_RS.split("|")),
                     ("serviço", ["S19"])):
        base = sum(compra_rs[k] for k in ks)
        for k in ks:
            contrib_rs[nome][k] = contrib_rs[nome].get(k, 0.0) + sul * grupos_d10[nome] / seg.sum() * compra_rs[k] / base
    fonte_rs = (f"D10: {fonte_seg}; indústria + cogeração → setores industriais ∝ consumo industrial de gás do BEN 2020 "
                "(sem o consumo final não energético) e, no ramo, ∝ compras ao S38; automotivo → S43 e famílias; "
                "residencial + comercial → famílias e S41–S68, ∝ compras ao S38; serviço (transporte do gás da REFAP, "
                "HIPÓTESE) → S19")
    anotar("gás por comprador", "*", "teto: gás ÷ compras ao S38 de cada comprador", W_MAX_GAS, "fração",
           "HIPÓTESE (revisão da Rodada 03): com o VBP do GAS-RB da D9-b, o alvo de gás de S17, S21–S24 e S27 no RB "
           "passava das compras ao S38 (eletricidade zero); o excedente vai aos demais compradores do mesmo grupo e, "
           "se o grupo inteiro estiver no teto, aos demais compradores da região, na proporção do alvo")

    def montar_gas(vbp_gas: dict, an, fonte_gas: str) -> tuple:
        """Componentes, regras de linha, gás por comprador e regras de primários, que dependem do VBP do GAS."""
        componentes = []
        for r in REGIOES:
            componentes += [
                (r, "vbp_transmissao", T[r], fonte_rap + "; × participação no VBP do S38"),
                (r, "vbp_gas", vbp_gas[r], fsul if r == "RS" else fonte_gas),
                (r, "gas_termicas", 0.0, "G = 0 (padrão das instruções; as térmicas compram gás direto do S05 ou importado)"),
            ]
        componentes.append(("*", "fracao_transmissao_distribuicao", alfa, falfa))
        componentes = pd.DataFrame(componentes, columns=["regiao", "componente", "valor", "fonte"])
        for r in REGIOES:
            E = F[r] - T[r]
            an("VBP", r, "VBP da geração = E_r = F_r − T_r − G_r", E, "R$ mi", "âncora por componentes (D3 = A)")
            an("VBP", r, "VBP da distribuição = X_r − E_r − T_r − VBP_GAS", X[r] - E - T[r] - vbp_gas[r], "R$ mi",
                   "resíduo (Seção 6.3 da Rodada 02)")

        lin = [("*", "*", "*", "fixa_por_comprador", "S38_DIS", 1.0, "nao",
                "padrão: energia elétrica vendida pela distribuição (geração e TRA não vendem fora do bloco)")]
        gas_comp, gas_grupos = [], []
        regras_gas(contrib_rb(vbp_gas["RB"]), compra_rb, "RB", fonte_rb, lin, gas_comp, gas_grupos)
        regras_gas(contrib_rs, compra_rs, "RS", fonte_rs, lin, gas_comp, gas_grupos)
        lin += [("*", "INV", "*", "fixa_por_comprador", "S38_DIS", 1.0, "nao", "investimento → DIS"),
                ("*", "EXP", "*", "fixa_por_comprador", "S38_DIS", 1.0, "nao", "exportações → DIS"),
                ("*", "DISCREP", "*", "somente_distribuicao_e_gas", "", np.nan, "nao",
                 "discrepância estatística → DIS e GAS na proporção do VBP")]
        regras_linha = pd.DataFrame(lin, columns=["regiao", "comprador", "regiao_comprador", "regra", "subsetor", "valor",
                                                  "fixar_no_ras", "fonte"])
        # ---- primários e satélites ---------------------------------------------------------------------
        pri = [("*", "*", "proporcional_vbp", "", np.nan, "padrão: na proporção do VBP"),
               ("*", "impostos_producao", "proporcional_vbp", "", np.nan, "impostos sobre a produção ∝ VBP")]
        pri += [("*", it, "proporcional_ci", "", np.nan, "impostos sobre produtos ∝ compras intermediárias domésticas + importadas")
                for it in ("ipi", "icms", "outros_impostos")]
        pri += [("RS", "importacoes", "fixa", "S38_DIS", 1.0, "D9-a: importações do S38-RS → 100% DIS (energia elétrica)")]
        pri += [("RB", "importacoes", "fixa", "S38_DIS", s_elet, fonte_imp + "; energia elétrica → DIS"),
                ("RB", "importacoes", "fixa", "S38_GN", (1 - s_elet) * theta["RB"], fonte_imp + "; gás × θ_RB → GN"),
                ("RB", "importacoes", "fixa", "S38_GAS", (1 - s_elet) * (1 - theta["RB"]), fonte_imp + "; gás × (1 − θ_RB) → GAS")]
        cem = pd.read_csv(INT / "cempre_2019_composicao_v01.csv")
        cem = cem[cem["nivel"] == "subsetor"]
        for r in REGIOES:
            for var, item in (("salarios_mil", "remuneracoes"), ("pessoal_ocupado", "ocupacoes")):
                c = cem[(cem["territorio"] == r) & (cem["variavel"] == var)].set_index("item")["participacao"]
                pri.append((r, item, "fixa_por_tipo", "geracao", float(c["geracao"]),
                            f"{FONTE_CEMPRE}: geração {c['geracao']:.4f}, repartida entre as fontes na proporção do VBP final"))
                for sub in ("S38_TRA", "S38_DIS", "S38_GAS"):
                    pri.append((r, item, "fixa_por_tipo", sub, float(c[sub]), f"{FONTE_CEMPRE}: {sub}"))
                an("CEMPRE", r, f"composição {item}", ", ".join(f"{k} {v:.4f}" for k, v in c.items()), "fração", FONTE_CEMPRE)
        ce_ben = pd.read_csv(INT / "ben_2019_consumo_especifico_v02.csv").set_index("subsetor")
        for c in TERMICAS:
            an("energia", "*", f"consumo específico {c}", float(ce_ben.loc[c, "tep_por_mwh"]), "tep/MWh", ce_ben.loc[c, "fonte"])
        for r in REGIOES:
            base_e = {c: gwh[r][c] * float(ce_ben.loc[c, "tep_por_mwh"]) for c in TERMICAS}
            base_a = {c: gwh[r][c] for c in TERMICAS}
            se, sa = sum(base_e.values()), sum(base_a.values())
            for c in TERMICAS:
                if base_e[c] > 0:
                    pri.append((r, "energia", "fixa", c, base_e[c] / se,
                                f"GWh (D8) × consumo específico (BEN 2020, Tabela 5.4); {FONTE_GER[r]}"))
                if base_a[c] > 0:
                    pri.append((r, "agua", "fixa", c, base_a[c] / sa, f"HIPÓTESE: água ∝ GWh das térmicas; {FONTE_GER[r]}"))
        em = pd.read_csv(INT / "seeg_2019_emissoes_v01.csv")
        por_sub = em[em["tabela"].str.startswith("por_subsetor")].set_index("regiao")
        sf6 = float(em.loc[em["tabela"] == "sf6_nacional_mil_t", "valor"].iloc[0]) * 1000
        for r in REGIOES:
            for c in ("S38_CAR", "S38_GN", "S38_PET", "S38_BIO"):
                v = float(por_sub.loc[r, c]) * 1000
                if v > 0:
                    obs = ("; PET do RS (diesel + óleo, 17.8 mil t) realocado a CAR e GN ∝ GWh" if r == "RS"
                           else "; 'Não alocado' somado ao RB")
                    pri.append((r, "co2e", "niveis", c, v, FONTE_SEEG + obs))
                    an("emissões", r, f"CO2e SEEG {c}", v, "t CO2e", FONTE_SEEG + obs,
                           f"fator E1 = {v / (gwh[r][c] * 1000):.4f} t/MWh" if gwh[r][c] > 0 else "")
            vbp_tra, vbp_dis = T[r], X[r] - (F[r] - T[r]) - T[r] - vbp_gas[r]
            sf6_r = sf6 * share_X[r]
            for sub, v in (("S38_TRA", sf6_r * vbp_tra / (vbp_tra + vbp_dis)), ("S38_DIS", sf6_r * vbp_dis / (vbp_tra + vbp_dis))):
                pri.append((r, "co2e", "niveis", sub, v, f"SF6 nacional ({FONTE_SEEG}) × participação de {r} no VBP do S38 "
                            f"({share_X[r]:.4f}) × participação do {sub} no VBP de TRA + DIS"))
        regras_primarios = pd.DataFrame(pri, columns=["regiao", "item", "regra", "subsetor", "valor", "fonte"])
        return componentes, regras_linha, pd.DataFrame(gas_comp), pd.DataFrame(gas_grupos), regras_primarios

    componentes, regras_linha, gas_comp, gas_grupos, regras_primarios = montar_gas(vbp_gas, anotar, fonte_gas_rb)
    # variante: VBP do GAS-RB com o preço da Sulgás (a outra opção da D9-b)
    fonte_gas_sul = (f"D9-b (variante): preço da Sulgás 2019 ({preco_sul:.6f} R$/m³; {fsul}) × volume não térmico do RB "
                     f"({fdist})")
    comp_sul, lin_sul, gas_comp_sul, gas_grupos_sul, pri_sul = montar_gas({"RS": sul, "RB": vbp_gas_sul},
                                                                          lambda *a, **k: a[3], fonte_gas_sul)
    for nome_, gc_ in (("principal", gas_comp), ("preço da Sulgás", gas_comp_sul)):
        for r in REGIOES:
            n_teto = int(gc_.loc[gc_["regiao"] == r, "no_teto"].sum())
            anotar("gás por comprador", r, f"compradores no teto ({nome_})", n_teto, "nº",
                   ", ".join(gc_.loc[(gc_["regiao"] == r) & gc_["no_teto"], "comprador"]) or "nenhum")

    # evidência física: participação do gás no gasto com gás + eletricidade de cada setor do BEN (não entra na MIP)
    ge = pd.read_csv(INT / "ben_2019_gas_eletricidade_por_setor_v01.csv")
    tarifa, ftar = exigir(D, "tarifa_media_industrial_2019")
    p_gas = p4 if p4 is not None else preco_sul
    ge = ge[ge["setor_ben"].isin(BEN_INDUSTRIA)].copy()
    ge["gasto_gas_R$mi"] = ge["gas_natural_mil_tep"] * 1e3 * M3_POR_TEP_GAS * p_gas / 1e6
    ge["gasto_eletricidade_R$mi"] = ge["eletricidade_mil_tep"] * 1e3 * MWH_POR_TEP * tarifa / 1e6
    ge["gas_sobre_gas_mais_eletricidade"] = ge["gasto_gas_R$mi"] / (ge["gasto_gas_R$mi"] + ge["gasto_eletricidade_R$mi"])
    ge["compradores_mip"] = ge["setor_ben"].map(dict(zip(corr["setor_ben"], corr["compradores_mip"])))
    ge["nota"] = (f"INDICATIVO, não entra na MIP: gás a {p_gas:.4f} R$/m³ (preço médio usado na D9-b; 8800 kcal/m³) e "
                  f"eletricidade a {tarifa} R$/MWh (tarifa média industrial 2019; {ftar}); 1 MWh = 0.086 tep")
    latentes = pd.DataFrame([("RS", s, "RB", f"D6 = A: {s}-RS latente; coluna do mesmo subsetor no RB") for s in LATENTES_RS],
                            columns=["regiao", "subsetor", "regiao_espelho", "fonte"])
    subsetores = pd.DataFrame(SUBSETORES, columns=["codigo", "nome", "tipo"])

    # ---- gravação --------------------------------------------------------------------------------
    arquivos = {"subsetores": f"subsetores_{V}.csv", "participacoes_vbp": f"participacoes_vbp_{V}.csv",
                "componentes": f"componentes_{V}.csv", "regras_coluna": f"regras_coluna_{V}.csv",
                "regras_linha": f"regras_linha_{V}.csv", "regras_primarios": f"regras_primarios_{V}.csv",
                "latentes_espelho": f"latentes_espelho_{V}.csv"}
    subsetores.to_csv(PAR / arquivos["subsetores"], index=False)
    part_p1.to_csv(PAR / arquivos["participacoes_vbp"], index=False)
    part_p2.to_csv(PAR / f"participacoes_vbp_{V}_P2.csv", index=False)
    componentes.to_csv(PAR / arquivos["componentes"], index=False)
    regras_coluna.to_csv(PAR / arquivos["regras_coluna"], index=False)
    regras_linha.to_csv(PAR / arquivos["regras_linha"], index=False)
    regras_primarios.to_csv(PAR / arquivos["regras_primarios"], index=False)
    latentes.to_csv(PAR / arquivos["latentes_espelho"], index=False)
    corr.to_csv(PAR / f"correspondencia_ben_mip_{V}.csv", index=False)
    arq_sul = arquivos | {"componentes": f"componentes_{V}_gas_sulgas.csv", "regras_linha": f"regras_linha_{V}_gas_sulgas.csv",
                          "regras_primarios": f"regras_primarios_{V}_gas_sulgas.csv"}
    comp_sul.to_csv(PAR / arq_sul["componentes"], index=False)
    lin_sul.to_csv(PAR / arq_sul["regras_linha"], index=False)
    pri_sul.to_csv(PAR / arq_sul["regras_primarios"], index=False)

    def piso(kappa, eta_v):
        d = {"kappa": kappa, "combustiveis": COMBUSTIVEIS, "max_iter": 50}
        if eta_v is not None:
            d["viabilidade_eta"] = eta_v
        return d

    def reeq(eta, se_inviavel="erro"):
        return {"eta": eta, "linhas_fixas": LINHAS_COMBUSTIVEL, "primarios_ajustaveis": ["ipi", "icms", "outros_impostos"],
                "importacoes": "fixas", "se_inviavel": se_inviavel}

    variantes = {
        "": ("MIP RS×RB 2019 — S38 em 11 subsetores — v02 (P1 + E1 + D9, κ = 0.70, η = 0.10; principal)", "residuo",
             arquivos, piso(KAPPA, ETA), reeq(ETA)),
        "_P2": ("v02 — sensibilidade P2 (preços iguais) + E1", "residuo",
                arquivos | {"participacoes_vbp": f"participacoes_vbp_{V}_P2.csv"}, piso(KAPPA, ETA), reeq(ETA)),
        "_E2": ("v02 — sensibilidade P1 + E2 (emissões na proporção do SEEG)", "proporcional", arquivos,
                piso(KAPPA, ETA), reeq(ETA)),
        "_E3": ("v02 — sensibilidade P1 + E3 (só níveis do SEEG; NÃO preserva o total da base)", "sem_residuo", arquivos,
                piso(KAPPA, ETA), reeq(ETA)),
        "_k060": ("v02 — sensibilidade κ = 0.60 (só o piso κ, sem a extensão de viabilidade; compare com "
                  "_sem_viabilidade, κ = 0.70: com a viabilidade ligada, κ ≥ ≈ 0.62 não atua)", "residuo", arquivos,
                  piso(0.60, None), reeq(ETA, "limitar")),
        "_k080": ("v02 — sensibilidade κ = 0.80 (só o piso κ, sem a extensão de viabilidade; compare com "
                  "_sem_viabilidade, κ = 0.70)", "residuo", arquivos, piso(0.80, None), reeq(ETA, "limitar")),
        "_eta005": ("v02 — sensibilidade η = 0.05", "residuo", arquivos, piso(KAPPA, 0.05), reeq(0.05)),
        "_sem_viabilidade": ("v02 — sensibilidade: só o piso κ = 0.70 das instruções, sem a extensão de viabilidade "
                             "(o EOB fica abaixo de η onde não cabe)", "residuo", arquivos, piso(KAPPA, None),
                             reeq(ETA, "limitar")),
        "_gas_sulgas": ("v02 — sensibilidade D9-b: VBP do GAS-RB com o preço da Sulgás (1.39 R$/m³) em vez do preço "
                        "médio das 4 distribuidoras", "residuo", arq_sul, piso(KAPPA, ETA), reeq(ETA)),
    }
    for suf, (nome, modo, arqs, pv, rq) in variantes.items():
        cfg = {"nome": nome,
               "descricao": "Parâmetros da Rodada 03 (D1=C, D2=D3=D4=D6=D7=A, D5=E1, D8=A, D9=a+b+f+r, D10=Sulgás); "
                            "gerado por scripts/rodada03_parametros.py; fontes em cada linha dos CSVs e em "
                            "quadro_parametros_v02.xlsx",
               "setor_alvo": "S38", "regioes": REGIOES, "bloco_intrassetorial": "roteamento_por_componentes",
               "modo_vbp": "ancora_componentes", "subsetor_termica_gas": "S38_GN",
               "ras": {"tolerancia": 1.0e-8, "max_iter": 20000},
               "niveis": {"co2e": {"modo": modo, "residuo_para": ["S38_DIS", "S38_GAS"]}},
               "piso_vbp": pv, "reequilibrio": rq, "alerta_multiplicador_producao": ALERTA_MULTIPLICADOR,
               "arquivos": arqs}
        with open(PAR / f"especificacao_{V}{suf}.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
    anotar("D9", "*", "κ (participação máxima do combustível na receita das térmicas)", KAPPA, "fração",
           "HIPÓTESE das instruções da Rodada 03 (D9-f); variantes 0.60 e 0.80")
    anotar("D9", "*", "η (EOB mínimo ÷ VBP)", ETA, "fração", "HIPÓTESE das instruções da Rodada 03 (D9-r); variante 0.05")
    q = pd.DataFrame(quadro)
    salvar_tabelas(
        PAR / f"quadro_parametros_{V}.xlsx",
        {"quadro": q, "participacoes_P1": part_p1, "participacoes_P2": part_p2, "componentes": componentes,
         "regras_coluna": regras_coluna, "regras_linha": regras_linha, "regras_primarios": regras_primarios,
         "latentes_espelho": latentes, "correspondencia_ben_mip": corr, "gas_por_comprador": gas_comp,
         "gas_grupos_teto": gas_grupos, "gas_por_comprador_sulgas": gas_comp_sul, "gas_grupos_teto_sulgas": gas_grupos_sul,
         "gas_x_eletricidade_BEN": ge, "valores_documentais": D},
        leiame=["Rodada 03 — quadro de parâmetros da MIP v02 (S38 em 11 subsetores), para revisão.",
                "Aba quadro: cada número usado, com unidade, fonte e cálculo. As demais abas são os CSVs de parametros/*_v02.",
                "Os pisos de VBP (D9-f) e o reequilíbrio (D9-r) são aplicados pelo motor; os resultados ficam nas abas "
                "pisos_vbp e reequilibrio_RAS da MIP v02 e do quadro de subsetores.",
                "Gerado por scripts/rodada03_parametros.py. Hipóteses marcadas como HIPÓTESE."],
    )
    print(f"[parâmetros v02] {len(q)} números no quadro; VBP_GAS RS {sul:.2f}, RB {vbp_gas_rb:.2f}; "
          f"{len(variantes)} especificações")


if __name__ == "__main__":
    main()
