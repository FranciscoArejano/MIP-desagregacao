"""Rodada 02 / 02b — Etapa 4: parâmetros reais da desagregação do S38 (11 subsetores).

Uso (na raiz do repositório, depois de scripts/rodada02.py):
    python scripts/rodada02_parametros.py

Entradas:
- MIP original (dados/original/)
- dados/intermediarios/*_v01 / *_v02 gerados por scripts/rodada02.py (ONS, preços, CEMPRE, SEEG)
- dados/externos/valores_documentais_v01.csv: números lidos de documentos (RAP, gás, EPE, Comex, nuclear),
  um por linha, com fonte, documento, localização, URL e data de acesso
- dados/externos/epe/sistemas_isolados_2019_v01.csv (se houver), já somado em geracao_2019_regiao_subsetor_v02.csv

Saídas (todas com coluna `fonte`):
- parametros/especificacao_v01.yaml            principal: preços P1 + emissões E1
- parametros/especificacao_v01_P2.yaml         preços iguais (P2) + E1
- parametros/especificacao_v01_E2.yaml         P1 + E2;  parametros/especificacao_v01_E3.yaml  P1 + E3
- parametros/subsetores_v01.csv, participacoes_vbp_v01.csv (P1), participacoes_vbp_v01_P2.csv, componentes_v01.csv,
  regras_coluna_v01.csv, regras_linha_v01.csv, regras_primarios_v01.csv, latentes_espelho_v01.csv,
  correspondencia_ben_mip_v01.csv
- parametros/quadro_parametros_v01.xlsx       todos os números, fonte e cálculo (para revisão do Francisco)

Decisões aplicadas: D1 = C (11 subsetores); D2 = A (RS e RB); D3 = A (âncora por componentes; P1 = MWh × preço);
D4 = A (roteamento por componentes, 50/50 da TUST); D5 = E1 (E2 e E3 como sensibilidades); D6 = A (Solar-RS e
Petróleo-RS latentes por espelho do RB; Nuclear-RS zerado); D7 = A (coluna do S38-RS como na base).
Respostas da Rodada 02b (Seção 1): excedente do teto do S05 → GAS (sem_teto); S03 + S09 com teto comum;
SF6 entre TRA e DIS na proporção do VBP; usinas de autoprodução fora do S38.
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
DOCS = PASTA_EXTERNOS / "valores_documentais_v01.csv"
REGIOES = ["RS", "RB"]

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
# consumo específico de fallback (tep/MWh; Seção 5.10 da Rodada 02): eficiências de 33%, 45%, 35%, 25% e 33%
CONSUMO_ESPECIFICO_FALLBACK = {"S38_CAR": 0.261, "S38_GN": 0.191, "S38_PET": 0.246, "S38_BIO": 0.344, "S38_NUC": 0.261}
# correspondência BEN 2020 (consumo final de gás natural) → compradores da MIP (HIPÓTESE do projeto; Seção 5.6)
_F_CORR = "HIPÓTESE: correspondência BEN → 68 setores feita pelo projeto (nomes dos setores do BEN e da MIP)"
CORRESPONDENCIA_BEN = [
    ("RESIDENCIAL", "FAM", _F_CORR + "; famílias = residencial (Seção 6.4)"),
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
MARGEM_DISTRIBUICAO_GAS = 0.25  # HIPÓTESE das instruções (Seção 5.6), usada só no fallback do VBP do GAS-RB

FONTE_ONS = "ONS, geração por usina 2019 (dados abertos, GERACAO_USINA-2_2019.parquet); sem autoprodução (R02b, Seção 2)"
FONTE_PRECOS = "Leilões de geração ANEEL até 31/12/2018 corrigidos pelo IPCA (SIDRA 1737), média ponderada pela energia"
FONTE_CEMPRE = "IBGE, CEMPRE 2019 (SIDRA 6450); sigilosos do RS por diferença e proporção nacional; RB = Brasil − RS"
FONTE_SEEG = "SEEG 13.0, Dados nacionais, CO2e (t) GWP-AR5, 2019, Geração de eletricidade (serviço público)"
FONTE_MIP = "MIP NEREUS/USP 2019 (dados/original)"

quadro = []  # todos os números: (grupo, regiao, item, valor, unidade, fonte, calculo)


def anotar(grupo, regiao, item, valor, unidade, fonte, calculo=""):
    quadro.append({"grupo": grupo, "regiao": regiao, "item": item, "valor": valor, "unidade": unidade,
                   "fonte": fonte, "calculo": calculo})
    return valor


def docs() -> pd.DataFrame:
    if not DOCS.exists():
        return pd.DataFrame(columns=["parametro", "valor", "unidade", "fonte"])
    return pd.read_csv(DOCS, dtype={"parametro": str})


def doc(d: pd.DataFrame, chave: str):
    """(valor, fonte) de um número documental, ou (None, motivo)."""
    m = d[d["parametro"] == chave]
    if not len(m) or pd.isna(m["valor"].iloc[0]):
        return None, "não encontrado"
    r = m.iloc[0]
    fonte = f"{r['fonte_instituicao']}, {r['documento']} ({r['localizacao']}); acesso {r['data_acesso_utc']}; {r['url']}"
    return float(r["valor"]), fonte


# ---------------------------------------------------------------------------------------------
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
        anotar("MIP", r, "participação no VBP do S38 das duas regiões", share_X[r], "fração", FONTE_MIP, "X_r / (X_RS + X_RB)")

    # ---- geração (GWh) e preços ----------------------------------------------------------------
    g = pd.read_csv(INT / "geracao_2019_regiao_subsetor_v02.csv")
    gwh = {r: g[g["regiao"] == r][GERACAO].sum().to_dict() for r in REGIOES}
    for r in REGIOES:
        for c in GERACAO:
            fonte = FONTE_ONS
            if r == "RB" and (g[(g["regiao"] == "RB") & (g["origem"] != "ONS (SIN)")][c].sum() > 0):
                fonte += " + EPE, sistemas isolados (R02b, Seção 3)"
            anotar("geração", r, f"GWh {c}", gwh[r][c], "GWh", fonte)
    precos = pd.read_csv(INT / "precos_2019_subsetor_v01.csv").set_index("subsetor")["preco_2019_rs_mwh"].to_dict()
    nuc, fonte_nuc = doc(D, "preco_nuclear_2019")
    fonte_preco = {c: FONTE_PRECOS for c in GERACAO}
    if nuc is not None:
        precos["S38_NUC"], fonte_preco["S38_NUC"] = nuc, fonte_nuc
    else:
        fonte_preco["S38_NUC"] = "tarifa de Angra 1 e 2 para 2019 (R$ 247.47/MWh; fonte secundária: IstoÉ Dinheiro/Estadão Conteúdo, 18/12/2018)"
    for c in GERACAO:
        anotar("preços P1", "*", f"preço 2019 {c}", precos[c], "R$/MWh", fonte_preco[c])

    # participações (pesos da geração) P1 = GWh × preço; P2 = GWh (preço igual)
    def participacoes(p2: bool) -> pd.DataFrame:
        linhas = []
        for r in REGIOES:
            for c, _, tipo in SUBSETORES:
                if tipo != "geracao":
                    linhas.append((r, c, np.nan, "não usado (ancora_componentes: VBP por componente/resíduo)"))
                    continue
                if r == "RS" and c in LATENTES_RS + ["S38_NUC"]:
                    linhas.append((r, c, 0.0, "produção zero no RS em 2019 (D6 = A: latente; nuclear zerado)"))
                    continue
                peso = gwh[r][c] * (1.0 if p2 else precos[c])
                linhas.append((r, c, peso, f"GWh ({FONTE_ONS})" + ("" if p2 else f" × preço ({fonte_preco[c]})")))
        return pd.DataFrame(linhas, columns=["regiao", "subsetor", "participacao", "fonte"])

    part_p1, part_p2 = participacoes(False), participacoes(True)

    # ---- componentes: transmissão (RAP), gás, TUST ----------------------------------------------
    rap_1920, f1920 = doc(D, "rap_total_ciclo_2019_2020")
    rap_1819, f1819 = doc(D, "rap_total_ciclo_2018_2019")
    if rap_1920 is None:
        raise SystemExit("RAP do ciclo 2019-2020 não encontrada em valores_documentais_v01.csv")
    if rap_1819 is not None:
        rap = (rap_1819 + rap_1920) / 2
        fonte_rap = f"média dos ciclos 2018-2019 ({f1819}) e 2019-2020 ({f1920}) = ano civil 2019"
    else:
        rap, fonte_rap = rap_1920, f"ciclo 2019-2020 ({f1920}); ciclo 2018-2019 não encontrado"
    anotar("transmissão", "Brasil", "RAP 2019 (R$ mi)", rap, "R$ mi", fonte_rap)
    T = {r: rap * share_X[r] for r in REGIOES}
    for r in REGIOES:
        anotar("transmissão", r, "VBP_TRA = T_r", T[r], "R$ mi", fonte_rap + "; repartição pela participação no VBP do S38",
               f"RAP × {share_X[r]:.6f}")
    ceee, fceee = doc(D, "rap_ceee_gt_ciclo_2019_2020")
    if ceee is not None:
        anotar("transmissão", "RS", "checagem: RAP da CEEE-GT 2019-2020", ceee, "R$ mi", fceee,
               f"T_RS = {T['RS']:.2f} {'≥' if T['RS'] >= ceee else '<'} RAP CEEE-GT")
    alfa, falfa = doc(D, "tust_fracao_consumo")
    if alfa is None:
        alfa, falfa = 0.5, "metodologia da TUST (50% geração, 50% consumo), conforme instruções da Rodada 02 (documento da ANEEL não localizado)"
    anotar("transmissão", "*", "fração da RAP paga pela distribuição (consumo)", alfa, "fração", falfa)

    # θ: participação térmica no gás comprado pelo S38
    theta = {}
    for r in REGIOES:
        v, fv = doc(D, f"theta_{r}")
        theta[r] = v
        anotar("gás", r, "θ: gás para termelétricas ÷ gás comprado pelo setor", v, "fração", fv)
    if any(v is None for v in theta.values()):
        raise SystemExit("θ ausente em valores_documentais_v01.csv (Seção 5.6)")

    # importações: participações (Comex Stat); eletricidade → DIS; gás → GN (θ) e GAS (1 − θ)
    fob = {k: doc(D, f"comex_fob_2019_{k}") for k in ("2716", "2711_21", "2711_11")}
    if all(v[0] is not None for v in fob.values()):
        tot = sum(v[0] for v in fob.values())
        s_elet = fob["2716"][0] / tot
        fonte_imp = "Comex Stat 2019, FOB por NCM (2716.00.00 energia elétrica; 2711.21.00 e 2711.11.00 gás natural): " + \
                    "; ".join(v[1] for v in fob.values())
        anotar("importações", "Brasil", "participação da energia elétrica nas importações de energia", s_elet, "fração", fonte_imp)
    else:
        s_elet, fonte_imp = None, "Comex Stat indisponível: importações na proporção do VBP (fallback da Seção 5.9)"
        anotar("importações", "Brasil", "importações por subsetor", np.nan, "", fonte_imp)

    # VBP do GAS: RS = receita líquida da Sulgás; RB = receita das demais distribuidoras ou fallback
    vbp_gas = {}
    v, fv = doc(D, "sulgas_receita_liquida_2019")
    if v is None:
        raise SystemExit("receita líquida da Sulgás 2019 ausente em valores_documentais_v01.csv")
    vbp_gas["RS"] = anotar("gás", "RS", "VBP_GAS = receita operacional líquida da Sulgás 2019", v, "R$ mi", fv)
    v, fv = doc(D, "gas_receita_liquida_demais_distribuidoras_2019")
    if v is not None:
        vbp_gas["RB"] = anotar("gás", "RB", "VBP_GAS = receita líquida das demais distribuidoras 2019", v, "R$ mi", fv)
    else:
        jRB = mip.indice("RB", "S38")
        s05 = sum(mip.Z[mip.indice(q, "S05"), jRB] for q in REGIOES)
        compras = (1 - theta["RB"]) * s05
        imp_gas = 0.0
        if s_elet is not None:
            imp_gas = (1 - s_elet) * (1 - theta["RB"]) * float(mip.primario("importacoes")[jRB])
        vbp_gas["RB"] = (compras + imp_gas) / (1 - MARGEM_DISTRIBUICAO_GAS)
        anotar("gás", "RB", "VBP_GAS (fallback)", vbp_gas["RB"], "R$ mi",
               f"{FONTE_MIP} (compras de S05 e importações de gás alocadas ao GAS-RB) ÷ (1 − 0.25); "
               "margem de distribuição 0.25 = HIPÓTESE das instruções (Seção 5.6)",
               f"((1 − θ_RB) × {s05:.2f} + {imp_gas:.2f}) / 0.75")

    componentes = []
    for r in REGIOES:
        componentes += [
            (r, "vbp_transmissao", T[r], fonte_rap + "; × participação no VBP do S38"),
            (r, "vbp_gas", vbp_gas[r], [q for q in quadro if q["item"].startswith("VBP_GAS") and q["regiao"] == r][0]["fonte"]),
            (r, "gas_termicas", 0.0, "G = 0 (padrão das instruções, Seção 5.6: as térmicas compram gás direto do S05 ou importado)"),
        ]
    componentes.append(("*", "fracao_transmissao_distribuicao", alfa, falfa))
    componentes = pd.DataFrame(componentes, columns=["regiao", "componente", "valor", "fonte"])
    for r in REGIOES:  # VBPs implícitos (conferência)
        E = F[r] - T[r]
        anotar("VBP", r, "VBP da geração = E_r = F_r − T_r − G_r", E, "R$ mi", "âncora por componentes (D3 = A)")
        anotar("VBP", r, "VBP da distribuição = X_r − E_r − T_r − VBP_GAS", X[r] - E - T[r] - vbp_gas[r], "R$ mi",
               "resíduo (Seção 6.3)")
        mwh = sum(gwh[r][c] for c in GERACAO) * 1000
        anotar("VBP", r, "preço implícito da âncora (E_r / MWh)", E * 1e6 / mwh, "R$/MWh", "E_r ÷ geração (ONS + isolados)")
        tot_p1 = sum(gwh[r][c] * precos[c] for c in GERACAO if not (r == "RS" and c in LATENTES_RS + ["S38_NUC"])) / 1000
        anotar("VBP", r, "Σ GWh × preço de leilão (conferência)", tot_p1, "R$ mi", "GWh (ONS + isolados) × preços P1",
               f"razão GWh·preço / âncora = {tot_p1 / E:.3f}")

    # ---- regras de coluna (Seção 6.8 + respostas da 02b) ----------------------------------------
    col = [("*", "*", "*", "proporcional_vbp", "", np.nan, np.nan, "", "", "padrão: na proporção do VBP (Seção 6.8)")]
    col += [("*", "S04", "*", "fixa_com_teto", "S38_CAR", 1.0, 0.40, "demais_vbp", "",
             "S04 (carvão e minerais não metálicos) 100% CAR, teto 0.40 × VBP_CAR, excedente aos demais ∝ VBP (Seção 6.8)")]
    for r in REGIOES:
        col += [(r, "S05", "*", "fixa_com_teto", "S38_GN", theta[r], 0.60, "sem_teto", "",
                 f"S05: θ_{r} → GN (teto 0.60 × VBP_GN); excedente → GAS (resposta 2 da R02b); θ: {[q for q in quadro if q['item'].startswith('θ') and q['regiao'] == r][0]['fonte']}"),
                (r, "S05", "*", "fixa_com_teto", "S38_GAS", 1 - theta[r], np.nan, "sem_teto", "",
                 f"S05: 1 − θ_{r} → GAS (Seção 6.8)")]
    col += [("*", "S19", "*", "fixa_com_teto", "S38_PET", 1.0, 0.60, "demais_vbp", "",
             "S19 (refino) → PET onde existe, teto 0.60 × VBP_PET; restante aos demais ∝ VBP (Seção 6.8)")]
    col += [("*", f, "*", "fixa_com_teto", "S38_BIO", 1.0, 0.40, "demais_vbp", "lenha_bagaco",
             "S03 e S09 (lenha; bagaço) 100% BIO, teto comum 0.40 × VBP_BIO sobre a soma (resposta 3 da R02b)") for f in ("S03", "S09")]
    regras_coluna = pd.DataFrame(col, columns=["regiao", "fornecedor", "regiao_fornecedor", "regra", "subsetor", "valor",
                                               "teto_vbp", "destino_excedente", "grupo_teto", "fonte"])

    # ---- regras de linha (Seção 6.4) -----------------------------------------------------------
    lin = [("*", "*", "*", "fixa_por_comprador", "S38_DIS", 1.0, "nao",
            "padrão: energia elétrica vendida pela distribuição (geração e TRA não vendem fora do bloco; Seção 6.4)")]
    gas_ben = INT / "ben_2019_gas_natural_por_setor_v01.csv"
    if gas_ben.exists():  # Seção 5.6: BEN 2020, consumo final de gás por setor, com correspondência BEN → 68 setores
        gb = pd.read_csv(gas_ben).set_index("setor_ben")["gas_natural_mil_tep"]
        corr = pd.DataFrame(CORRESPONDENCIA_BEN, columns=["setor_ben", "compradores_mip", "fonte"])
        corr["gas_natural_mil_tep"] = [float(gb.get(x, 0.0)) for x in corr["setor_ben"]]
        corr["entra"] = corr["compradores_mip"] != ""
        tep_total = corr.loc[corr["entra"], "gas_natural_mil_tep"].sum()
        corr["participacao_no_gas_distribuido"] = np.where(corr["entra"], corr["gas_natural_mil_tep"] / tep_total, 0.0)
        anotar("gás", "Brasil", "gás natural distribuído (consumo final sem o setor energético)", tep_total, "mil tep",
               "EPE, BEN 2020, aba Consolidada; HIPÓTESE: o setor energético (E&P, refinarias, UPGN) consome gás próprio "
               "ou comprado do S05, não das distribuidoras")
        gas_comp = []
        for r in REGIOES:
            i = mip.indice(r, "S38")
            compra = {}  # vendas do S38-r a cada comprador da própria região (R$ mi)
            for k in sorted({c for x in corr["compradores_mip"] for c in x.split("|") if c}):
                compra[k] = float(mip.F[i, list(COLUNAS_DF["codigo"]).index(f"{k}_{r}")]) if k == "FAM" \
                    else float(mip.Z[i, mip.indice(r, k)])
            alvo = dict.fromkeys(compra, 0.0)
            for x in corr[corr["entra"]].itertuples(index=False):
                ks = x.compradores_mip.split("|")
                base = sum(compra[k] for k in ks)
                for k in ks:
                    alvo[k] += vbp_gas[r] * x.participacao_no_gas_distribuido * compra[k] / base
            for k in compra:
                if alvo[k] <= 0 or compra[k] <= 0:
                    continue
                w = min(alvo[k] / compra[k], 1.0)
                fonte = (f"BEN 2020 (gás por setor, sem o setor energético) × VBP_GAS_{r}, repartido ∝ compras ao S38 "
                         f"dentro de cada setor do BEN (correspondencia_ben_mip_v01.csv); alvo {alvo[k]:.2f} ÷ compras "
                         f"{compra[k]:.2f}{' (limitado a 1)' if alvo[k] > compra[k] else ''}; HIPÓTESE: mesmo preço por tep "
                         "em todos os setores; o GAS só vende na própria região; o RAS fecha o VBP do GAS")
                comp_k = "FAM" if k == "FAM" else k
                lin += [(r, comp_k, r, "fixa_por_comprador", "S38_GAS", w, "nao", fonte),
                        (r, comp_k, r, "fixa_por_comprador", "S38_DIS", 1 - w, "nao", fonte)]
                gas_comp.append({"regiao": r, "comprador": k, "compras_ao_S38": compra[k], "alvo_gas": alvo[k],
                                 "participacao_gas": w})
        gas_comp = pd.DataFrame(gas_comp)
        fonte_gas_lin = "BEN 2020 (gás por setor) — ver parametros/correspondencia_ben_mip_v01.csv e a aba gas_por_comprador"
    else:
        corr, gas_comp = pd.DataFrame(), pd.DataFrame()
        lin += [("*", "S08:S37|S43|FAM", "*", "somente_distribuicao_e_gas", "", np.nan, "nao",
                 "fallback da Seção 5.6: o GAS vende à indústria de transformação (S08–S37), ao S43 e às famílias, "
                 "na proporção das compras de cada um ao S38 (RAS fecha o VBP do GAS)")]
        fonte_gas_lin = "fallback (BEN não usado)"
    lin += [("*", "INV", "*", "fixa_por_comprador", "S38_DIS", 1.0, "nao", "investimento → DIS (Seção 6.4)"),
            ("*", "EXP", "*", "fixa_por_comprador", "S38_DIS", 1.0, "nao", "exportações → DIS (Seção 6.4)"),
            ("*", "DISCREP", "*", "somente_distribuicao_e_gas", "", np.nan, "nao",
             "discrepância estatística → DIS e GAS na proporção do VBP (Seção 6.4)")]
    regras_linha = pd.DataFrame(lin, columns=["regiao", "comprador", "regiao_comprador", "regra", "subsetor", "valor",
                                              "fixar_no_ras", "fonte"])
    anotar("vendas", "*", "participação do gás por comprador", np.nan, "", fonte_gas_lin)

    # ---- insumos primários e contas satélite (Seções 5.7–5.10, 6.6–6.8) -------------------------
    pri = [("*", "*", "proporcional_vbp", "", np.nan, "padrão: na proporção do VBP"),
           ("*", "impostos_producao", "proporcional_vbp", "", np.nan, "impostos sobre a produção ∝ VBP (Seção 6.8)")]
    pri += [("*", it, "proporcional_ci", "", np.nan, "impostos sobre produtos ∝ compras intermediárias domésticas + importadas (Seção 6.8)")
            for it in ("ipi", "icms", "outros_impostos")]
    if s_elet is not None:
        for r in REGIOES:
            pri += [(r, "importacoes", "fixa", "S38_DIS", s_elet, fonte_imp + "; energia elétrica → DIS (Seção 5.9)"),
                    (r, "importacoes", "fixa", "S38_GN", (1 - s_elet) * theta[r], fonte_imp + f"; gás × θ_{r} → GN"),
                    (r, "importacoes", "fixa", "S38_GAS", (1 - s_elet) * (1 - theta[r]), fonte_imp + f"; gás × (1 − θ_{r}) → GAS")]
    # composição do CEMPRE (remunerações e ocupações); geração repartida pelo peso P1 (VBP) dentro da geração
    cem = pd.read_csv(INT / "cempre_2019_composicao_v01.csv")
    cem = cem[cem["nivel"] == "subsetor"]
    for r in REGIOES:
        pesos = part_p1[(part_p1["regiao"] == r) & part_p1["subsetor"].isin(GERACAO)].set_index("subsetor")["participacao"]
        pesos = pesos / pesos.sum()
        for var, item in (("salarios_mil", "remuneracoes"), ("pessoal_ocupado", "ocupacoes")):
            c = cem[(cem["territorio"] == r) & (cem["variavel"] == var)].set_index("item")["participacao"]
            for sub in GERACAO:
                pri.append((r, item, "fixa", sub, float(c["geracao"] * pesos.get(sub, 0.0)),
                            f"{FONTE_CEMPRE}: geração {c['geracao']:.4f} × peso da fonte na geração (VBP)"))
            for sub in ("S38_TRA", "S38_DIS", "S38_GAS"):
                pri.append((r, item, "fixa", sub, float(c[sub]), f"{FONTE_CEMPRE}: {sub}"))
            anotar("CEMPRE", r, f"composição {item}", ", ".join(f"{k} {v:.4f}" for k, v in c.items()), "fração", FONTE_CEMPRE)
    # energia e água: térmicas, GWh × consumo específico / GWh
    ce = {}
    ce_ben = INT / "ben_2019_consumo_especifico_v01.csv"
    ce_ben = pd.read_csv(ce_ben).set_index("subsetor") if ce_ben.exists() else pd.DataFrame()
    for c in TERMICAS:
        if c in ce_ben.index:  # preferível (Seção 5.10): implícito no BEN 2020, Tabela 5.4
            x = ce_ben.loc[c]
            ce[c] = (float(x["tep_por_mwh"]), f"{x['fonte']} ({x['consumo_mil_tep_2019']:.0f} mil tep ÷ "
                                              f"{x['geracao_gwh_2019']:.0f} GWh)")
        else:
            ce[c] = (CONSUMO_ESPECIFICO_FALLBACK[c], "fallback das instruções (Seção 5.10): eficiência típica")
        anotar("energia", "*", f"consumo específico {c}", ce[c][0], "tep/MWh", ce[c][1])
    for r in REGIOES:
        base_e = {c: gwh[r][c] * ce[c][0] for c in TERMICAS}
        base_a = {c: gwh[r][c] for c in TERMICAS}
        se, sa = sum(base_e.values()), sum(base_a.values())
        for c in TERMICAS:
            if base_e[c] > 0:
                pri.append((r, "energia", "fixa", c, base_e[c] / se, f"GWh × consumo específico ({ce[c][1]}); {FONTE_ONS}"))
            if base_a[c] > 0:
                pri.append((r, "agua", "fixa", c, base_a[c] / sa,
                            f"HIPÓTESE (Seção 5.10): água ∝ GWh das térmicas; {FONTE_ONS}"))
    # emissões: níveis do SEEG (E1/E2/E3) + SF6
    em = pd.read_csv(INT / "seeg_2019_emissoes_v01.csv")
    por_sub = em[em["tabela"].str.startswith("por_subsetor")].set_index("regiao")
    sf6 = float(em.loc[em["tabela"] == "sf6_nacional_mil_t", "valor"].iloc[0]) * 1000
    anotar("emissões", "Brasil", "SF6 em equipamentos elétricos (t CO2e)", sf6, "t CO2e", FONTE_SEEG.replace("Geração de eletricidade (serviço público)", "Uso de SF6 em equipamentos elétricos"))
    for r in REGIOES:
        for c in ("S38_CAR", "S38_GN", "S38_PET", "S38_BIO"):
            v = float(por_sub.loc[r, c]) * 1000
            if v > 0:
                obs = "; PET do RS (diesel + óleo, 17.8 mil t) realocado a CAR e GN ∝ GWh (Seção 5.7)" if r == "RS" else \
                      "; 'Não alocado' somado ao RB (Seção 5.7)"
                pri.append((r, "co2e", "niveis", c, v, FONTE_SEEG + obs))
                anotar("emissões", r, f"CO2e SEEG {c}", v, "t CO2e", FONTE_SEEG + obs)
        vbp_tra, vbp_dis = T[r], X[r] - (F[r] - T[r]) - T[r] - vbp_gas[r]
        sf6_r = sf6 * share_X[r]
        for sub, v in (("S38_TRA", sf6_r * vbp_tra / (vbp_tra + vbp_dis)), ("S38_DIS", sf6_r * vbp_dis / (vbp_tra + vbp_dis))):
            pri.append((r, "co2e", "niveis", sub, v, f"SF6 nacional ({FONTE_SEEG}) × participação de {r} no VBP do S38 "
                        f"({share_X[r]:.4f}) × participação do {sub} no VBP de TRA + DIS (resposta 4 da R02b)"))
            anotar("emissões", r, f"SF6 {sub}", v, "t CO2e", "ver regras_primarios_v01.csv")
    regras_primarios = pd.DataFrame(pri, columns=["regiao", "item", "regra", "subsetor", "valor", "fonte"])

    latentes = pd.DataFrame([("RS", s, "RB", f"D6 = A: {s}-RS latente; coluna do mesmo subsetor no RB (Seção 6.5)") for s in LATENTES_RS],
                            columns=["regiao", "subsetor", "regiao_espelho", "fonte"])
    subsetores = pd.DataFrame(SUBSETORES, columns=["codigo", "nome", "tipo"])

    # ---- gravação --------------------------------------------------------------------------------
    subsetores.to_csv(PAR / "subsetores_v01.csv", index=False)
    part_p1.to_csv(PAR / "participacoes_vbp_v01.csv", index=False)
    part_p2.to_csv(PAR / "participacoes_vbp_v01_P2.csv", index=False)
    componentes.to_csv(PAR / "componentes_v01.csv", index=False)
    regras_coluna.to_csv(PAR / "regras_coluna_v01.csv", index=False)
    regras_linha.to_csv(PAR / "regras_linha_v01.csv", index=False)
    regras_primarios.to_csv(PAR / "regras_primarios_v01.csv", index=False)
    if len(corr):
        corr.to_csv(PAR / "correspondencia_ben_mip_v01.csv", index=False)
    latentes.to_csv(PAR / "latentes_espelho_v01.csv", index=False)
    base = {
        "setor_alvo": "S38",
        "regioes": REGIOES,
        "bloco_intrassetorial": "roteamento_por_componentes",
        "modo_vbp": "ancora_componentes",
        "subsetor_termica_gas": "S38_GN",
        "ras": {"tolerancia": 1.0e-8, "max_iter": 20000},
    }
    arquivos = {"subsetores": "subsetores_v01.csv", "participacoes_vbp": "participacoes_vbp_v01.csv",
                "componentes": "componentes_v01.csv", "regras_coluna": "regras_coluna_v01.csv",
                "regras_linha": "regras_linha_v01.csv", "regras_primarios": "regras_primarios_v01.csv",
                "latentes_espelho": "latentes_espelho_v01.csv"}
    variantes = {
        "": ("MIP RS×RB 2019 — S38 em 11 subsetores — v01 (P1 + E1, principal)", "residuo", arquivos),
        "_P2": ("v01 — sensibilidade P2 (preços iguais) + E1", "residuo",
                arquivos | {"participacoes_vbp": "participacoes_vbp_v01_P2.csv"}),
        "_E2": ("v01 — sensibilidade P1 + E2 (emissões na proporção do SEEG)", "proporcional", arquivos),
        "_E3": ("v01 — sensibilidade P1 + E3 (só níveis do SEEG; NÃO preserva o total da base)", "sem_residuo", arquivos),
    }
    for suf, (nome, modo, arqs) in variantes.items():
        cfg = {"nome": nome,
               "descricao": "Parâmetros reais da Rodada 02/02b (decisões D1=C, D2=A, D3=A, D4=A, D5=E1, D6=A, D7=A); "
                            "gerado por scripts/rodada02_parametros.py; fontes em cada linha dos CSVs e em quadro_parametros_v01.xlsx",
               **base,
               "niveis": {"co2e": {"modo": modo, "residuo_para": ["S38_DIS", "S38_GAS"]}},
               "arquivos": arqs}
        with open(PAR / f"especificacao_v01{suf}.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    q = pd.DataFrame(quadro)
    salvar_tabelas(
        PAR / "quadro_parametros_v01.xlsx",
        {"quadro": q, "participacoes_P1": part_p1, "participacoes_P2": part_p2, "componentes": componentes,
         "regras_coluna": regras_coluna, "regras_linha": regras_linha, "regras_primarios": regras_primarios,
         "latentes_espelho": latentes, "correspondencia_ben_mip": corr, "gas_por_comprador": gas_comp,
         "valores_documentais": D},
        leiame=["Rodada 02/02b — quadro de parâmetros da desagregação do S38 (11 subsetores), para revisão.",
                "Aba quadro: cada número usado, com unidade, fonte e cálculo. As demais abas são os CSVs de parametros/*_v01.",
                "Gerado por scripts/rodada02_parametros.py. Hipóteses marcadas como HIPÓTESE; fallbacks marcados como fallback."],
    )
    print(f"[parâmetros] {len(q)} números no quadro; arquivos em {PAR.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
