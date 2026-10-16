"""Motor genérico de desagregação de um setor da MIP em subsetores (Etapa 5).

Entrada: a MIP original + uma `Especificacao` (lida de `parametros/*.yaml` + CSVs). Saída: a MIP
desagregada, que preserva exatamente todos os totais da original (a soma dos subsetores reproduz
cada célula da original), mais o mapa de setores, os pesos usados e as checagens.

Blocos da nova matriz (t = setor-alvo; "fora do bloco" = setores ≠ t e colunas de demanda final):
- fora × fora ......................... cópia da original
- fornecedor fora → subsetores (coluna) .... regras de coluna: proporcional_vbp | fixa | indicador | fixa_com_teto
- subsetores → comprador fora (linha) ...... regras de linha: proporcional_vbp | somente_rede_e_gas
                                             (= somente_distribuicao_e_gas) | fixa_por_comprador (+ RAS)
- subsetores → subsetores (bloco t→t) ...... proporcional | geracao_vende_para_rede | roteamento_por_componentes
- insumos primários e contas satélite ...... proporcional_vbp | fixa | indicador | proporcional_ci | niveis;
                                             EOB = resíduo
- subsetores latentes ...................... produção-base zero + coluna de coeficientes dada à parte
                                             (explícita ou "espelho" do mesmo subsetor em outra região)

VBP dos subsetores (modo_vbp): participacoes | ancora_bloco | ancora_componentes.

Regiões não desagregadas ficam com o setor agregado (tratado como um grupo de um único "subsetor").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .estrutura import (
    COLUNAS_DF,
    ITENS_IMPOSTOS_PRODUTOS,
    ITENS_PRIMARIOS,
    ITENS_SATELITE,
    MIP,
)
from .modelo import ModeloLeontief

# 'rede' (Rodada 01) equivale a 'distribuicao'
TIPOS_SUBSETOR = ("geracao", "transmissao", "distribuicao", "gas_utilidades", "rede")
REGRAS_COLUNA = ("proporcional_vbp", "fixa", "indicador", "fixa_com_teto")
REGRAS_LINHA = ("proporcional_vbp", "somente_rede_e_gas", "somente_distribuicao_e_gas", "fixa_por_comprador")
REGRAS_PRIMARIOS = ("proporcional_vbp", "fixa", "indicador", "proporcional_ci", "niveis", "fixa_por_tipo",
                    "fixa_por_tipo_sem_combustivel")
REGRAS_POR_TIPO = ("fixa_por_tipo", "fixa_por_tipo_sem_combustivel")
OPCOES_BLOCO = ("proporcional", "geracao_vende_para_rede", "roteamento_por_componentes")
MODOS_VBP = ("participacoes", "ancora_bloco", "ancora_componentes")
MODOS_NIVEIS = ("residuo", "proporcional", "sem_residuo")
DESTINOS_EXCEDENTE = ("demais_vbp", "sem_teto")
# componentes do bloco (roteamento_por_componentes / ancora_componentes), em R$ milhões, por região
COMPONENTES = {
    "vbp_transmissao": None,  # T_r: VBP do subsetor de transmissão (obrigatório no roteamento)
    "vbp_gas": None,  # VBP do subsetor de gás canalizado (obrigatório em ancora_componentes)
    "gas_termicas": 0.0,  # G_r: gás vendido pelas distribuidoras às térmicas dentro do bloco
    "fracao_transmissao_distribuicao": 0.5,  # parte de T_r paga pela distribuição (resto: geração)
}
# Itens repartidos por regra; EOB é o resíduo e VA = remunerações + EOB + impostos sobre a produção
ITENS_PRIMARIOS_REPARTIVEIS = ["importacoes", "ipi", "icms", "outros_impostos", "remuneracoes", "impostos_producao"]
ITENS_REPARTIVEIS = ITENS_PRIMARIOS_REPARTIVEIS + ITENS_SATELITE
CURINGA = "*"
TOL_SOMA = 1e-9
TOL_REAGREGACAO = 1e-6

COLS_SUBSETORES = ["codigo", "nome", "tipo"]
COLS_PARTICIPACOES = ["regiao", "subsetor", "participacao", "fonte"]
COLS_REGRAS_COLUNA = ["regiao", "fornecedor", "regiao_fornecedor", "regra", "subsetor", "valor", "teto_vbp",
                      "destino_excedente", "grupo_teto", "fonte"]
COLS_REGRAS_LINHA = ["regiao", "comprador", "regiao_comprador", "regra", "subsetor", "valor", "fixar_no_ras", "fonte"]
COLS_REGRAS_PRIMARIOS = ["regiao", "item", "regra", "subsetor", "valor", "fonte"]
COLS_COEF_LATENTES = ["regiao", "subsetor", "tipo_linha", "regiao_linha", "codigo_linha", "coeficiente", "fonte"]
COLS_LATENTES_ESPELHO = ["regiao", "subsetor", "regiao_espelho", "fonte"]
COLS_COMPONENTES = ["regiao", "componente", "valor", "fonte"]
COLS_PESOS_TUST = ["regiao", "subsetor", "valor", "fonte"]


def tipo_canonico(tipo: str) -> str:
    """'rede' (nome da Rodada 01) equivale a 'distribuicao'."""
    return "distribuicao" if tipo == "rede" else tipo


class EspecificacaoInvalida(ValueError):
    """A especificação é incoerente (erro de parâmetros, não de código)."""


class DesagregacaoInvalida(RuntimeError):
    """A verificação final encontrou FALHA (só levantada com estrito=True)."""


# =============================================================================================
# Especificação
# =============================================================================================
def _tabela(df: pd.DataFrame | None, colunas: list[str]) -> pd.DataFrame:
    """Normaliza uma tabela de parâmetros: garante as colunas, textos sem NaN e espaços."""
    if df is None:
        df = pd.DataFrame(columns=colunas)
    df = df.copy()
    for c in colunas:
        if c not in df.columns:
            df[c] = np.nan
    numericas = {"participacao", "valor", "coeficiente", "teto_vbp"}
    for c in colunas:
        if c in numericas:
            df[c] = pd.to_numeric(df[c].replace("", np.nan), errors="raise")
        elif c == "fixar_no_ras":
            df[c] = df[c].map(
                lambda v: str(v).strip().lower() in {"1", "true", "sim", "s", "verdadeiro", "yes"}
                if pd.notna(v) else False
            )
        else:
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else str(v).strip())
    return df[colunas].reset_index(drop=True)


@dataclass
class Especificacao:
    """Parâmetros de uma desagregação (ver parametros/LEIAME_parametros.md)."""

    nome: str
    setor_alvo: str
    regioes: list
    subsetores: pd.DataFrame
    participacoes: pd.DataFrame
    bloco: str = "proporcional"
    modo_vbp: str = "participacoes"
    regras_coluna: pd.DataFrame | None = None
    regras_linha: pd.DataFrame | None = None
    regras_primarios: pd.DataFrame | None = None
    coef_latentes: pd.DataFrame | None = None
    latentes_espelho: pd.DataFrame | None = None
    componentes: pd.DataFrame | None = None
    niveis: dict = field(default_factory=dict)  # {item: {"modo": ..., "residuo_para": [...]}}
    subsetor_termica_gas: str | None = None  # comprador do gás G_r no roteamento (ex.: S38_GN)
    # Rodada 03 — piso de VBP das térmicas (pacote D9-f) e reequilíbrio dos insumos não energéticos (D9-r)
    piso_vbp: dict = field(default_factory=dict)  # {kappa, combustiveis: {subsetor: [fornecedores | 'importacoes']}, viabilidade_eta, max_iter}
    reequilibrio: dict = field(default_factory=dict)  # {eta, linhas_fixas, primarios_ajustaveis, importacoes, se_inviavel}
    alerta_multiplicador: float | None = None  # ALERTA se o multiplicador de produção de um subsetor passar deste valor
    # Rodada 04 — V1: TUST paga pela geração repartida por pesos próprios (ex.: MWh no SIN), e não pelo VBP
    pesos_tust_geracao: pd.DataFrame | None = None  # colunas regiao, subsetor, valor, fonte
    alerta_insumos_nao_energeticos: float | None = None  # T12: ALERTA se insumos não energéticos ÷ VBP < este valor
    ras_tolerancia: float = 1e-8
    ras_max_iter: int = 10000
    aviso: str | None = None
    descricao: str = ""
    arquivos: dict = field(default_factory=dict)

    def __post_init__(self):
        self.regioes = list(self.regioes)
        self.subsetores = _tabela(self.subsetores, COLS_SUBSETORES)
        self.participacoes = _tabela(self.participacoes, COLS_PARTICIPACOES)
        self.regras_coluna = _tabela(self.regras_coluna, COLS_REGRAS_COLUNA)
        self.regras_linha = _tabela(self.regras_linha, COLS_REGRAS_LINHA)
        self.regras_primarios = _tabela(self.regras_primarios, COLS_REGRAS_PRIMARIOS)
        if self.coef_latentes is not None:
            self.coef_latentes = _tabela(self.coef_latentes, COLS_COEF_LATENTES)
        self.latentes_espelho = _tabela(self.latentes_espelho, COLS_LATENTES_ESPELHO)
        self.componentes = _tabela(self.componentes, COLS_COMPONENTES)
        self.niveis = dict(self.niveis or {})
        self.piso_vbp = dict(self.piso_vbp or {})
        self.reequilibrio = dict(self.reequilibrio or {})
        if self.pesos_tust_geracao is not None:
            self.pesos_tust_geracao = _tabela(self.pesos_tust_geracao, COLS_PESOS_TUST)

    def componente(self, regiao: str, nome: str) -> float | None:
        """Valor de um componente do bloco para a região (linha da região vence a linha '*')."""
        c = self.componentes
        m = c[(c["componente"] == nome) & (c["regiao"] == regiao)]
        if not len(m):
            m = c[(c["componente"] == nome) & c["regiao"].isin([CURINGA, ""])]
        if len(m) > 1:
            raise EspecificacaoInvalida(f"componentes: '{nome}' repetido para a região {regiao}")
        if len(m):
            return float(m["valor"].iloc[0])
        return COMPONENTES.get(nome)

    def fonte_componente(self, regiao: str, nome: str) -> str:
        c = self.componentes
        m = c[(c["componente"] == nome) & c["regiao"].isin([regiao, CURINGA, ""])]
        return "; ".join(dict.fromkeys(f for f in m["fonte"] if f)) or "padrão do motor"


def _relativo(caminho: Path) -> str:
    """Caminho relativo à raiz do repositório (para registro), se possível."""
    from .caminhos import RAIZ

    try:
        return Path(caminho).resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        return str(caminho)


def ler_especificacao(caminho_yaml: str | Path) -> Especificacao:
    """Lê a especificação: um YAML com as opções e os nomes dos CSVs (relativos à pasta do YAML)."""
    caminho_yaml = Path(caminho_yaml)
    with open(caminho_yaml, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    pasta = caminho_yaml.parent
    arqs = cfg.get("arquivos", {})

    def ler(chave):
        if not arqs.get(chave):
            return None
        return pd.read_csv(pasta / arqs[chave], dtype=str, keep_default_na=False, comment="#")

    ras = cfg.get("ras", {}) or {}
    return Especificacao(
        nome=cfg["nome"],
        setor_alvo=cfg["setor_alvo"],
        regioes=cfg["regioes"],
        subsetores=ler("subsetores"),
        participacoes=ler("participacoes_vbp"),
        bloco=cfg.get("bloco_intrassetorial", "proporcional"),
        modo_vbp=cfg.get("modo_vbp", "participacoes"),
        regras_coluna=ler("regras_coluna"),
        regras_linha=ler("regras_linha"),
        regras_primarios=ler("regras_primarios"),
        coef_latentes=ler("coef_latentes"),
        latentes_espelho=ler("latentes_espelho"),
        componentes=ler("componentes"),
        niveis=cfg.get("niveis") or {},
        subsetor_termica_gas=cfg.get("subsetor_termica_gas"),
        piso_vbp=cfg.get("piso_vbp") or {},
        reequilibrio=cfg.get("reequilibrio") or {},
        alerta_multiplicador=(float(cfg["alerta_multiplicador_producao"])
                              if cfg.get("alerta_multiplicador_producao") is not None else None),
        pesos_tust_geracao=ler("pesos_tust_geracao"),
        alerta_insumos_nao_energeticos=(float(cfg["alerta_insumos_nao_energeticos"])
                                        if cfg.get("alerta_insumos_nao_energeticos") is not None else None),
        ras_tolerancia=float(ras.get("tolerancia", 1e-8)),
        ras_max_iter=int(ras.get("max_iter", 10000)),
        aviso=cfg.get("aviso"),
        descricao=cfg.get("descricao", ""),
        arquivos={k: _relativo(pasta / v) for k, v in arqs.items() if v} | {"especificacao": _relativo(caminho_yaml)},
    )


def validar_especificacao(espec: Especificacao, mip: MIP) -> None:
    """Confere a coerência interna da especificação (levanta EspecificacaoInvalida)."""
    erros = []
    t = espec.setor_alvo
    regs_mip = mip.lista_regioes
    if t not in set(mip.setores["codigo"]):
        erros.append(f"setor-alvo {t} não existe na MIP")
    for r in espec.regioes:
        if r not in regs_mip:
            erros.append(f"região {r} não existe na MIP")
    subs = espec.subsetores
    if len(subs) == 0:
        erros.append("lista de subsetores vazia")
    if subs["codigo"].duplicated().any():
        erros.append("códigos de subsetor repetidos")
    if set(subs["codigo"]) & set(mip.setores["codigo"]):
        erros.append("código de subsetor coincide com código de setor existente")
    tipos_inv = set(subs["tipo"]) - set(TIPOS_SUBSETOR)
    if tipos_inv:
        erros.append(f"tipos de subsetor inválidos: {sorted(tipos_inv)} (válidos: {TIPOS_SUBSETOR})")
    if espec.bloco not in OPCOES_BLOCO:
        erros.append(f"bloco_intrassetorial inválido: {espec.bloco} (válidos: {OPCOES_BLOCO})")
    if espec.modo_vbp not in MODOS_VBP:
        erros.append(f"modo_vbp inválido: {espec.modo_vbp} (válidos: {MODOS_VBP})")
    if espec.modo_vbp == "ancora_bloco" and espec.bloco != "geracao_vende_para_rede":
        erros.append("modo_vbp = ancora_bloco exige bloco_intrassetorial = geracao_vende_para_rede")
    if espec.modo_vbp == "ancora_componentes" and espec.bloco != "roteamento_por_componentes":
        erros.append("modo_vbp = ancora_componentes exige bloco_intrassetorial = roteamento_por_componentes")
    tipos = subs["tipo"].map(tipo_canonico)
    n_ger, n_tra, n_dis, n_gas = (int((tipos == x).sum()) for x in ("geracao", "transmissao", "distribuicao", "gas_utilidades"))
    if espec.bloco == "geracao_vende_para_rede":
        if n_dis != 1:
            erros.append("geracao_vende_para_rede exige exatamente um subsetor do tipo 'distribuicao' (ou 'rede')")
        if n_ger < 1:
            erros.append("geracao_vende_para_rede exige ao menos um subsetor do tipo 'geracao'")
    if espec.bloco == "roteamento_por_componentes":
        if n_tra != 1 or n_dis != 1 or n_ger < 1:
            erros.append("roteamento_por_componentes exige exatamente um subsetor 'transmissao', exatamente um "
                         "'distribuicao' e ao menos um 'geracao'")
    codigos = set(subs["codigo"])
    # componentes do bloco
    comp = espec.componentes
    inv = set(comp["componente"]) - set(COMPONENTES)
    if inv:
        erros.append(f"componentes inválidos: {sorted(inv)} (válidos: {sorted(COMPONENTES)})")
    if comp["valor"].isna().any():
        erros.append("componentes: há valores vazios")
    if espec.bloco == "roteamento_por_componentes" and not inv:
        for r in espec.regioes:
            T = espec.componente(r, "vbp_transmissao")
            if T is None or T < 0:
                erros.append(f"componentes: vbp_transmissao da região {r} ausente ou negativo")
            G = espec.componente(r, "gas_termicas")
            if G is None or G < 0:
                erros.append(f"componentes: gas_termicas da região {r} negativo")
            elif G > 0:
                if n_gas != 1:
                    erros.append("gas_termicas > 0 exige exatamente um subsetor 'gas_utilidades'")
                st = espec.subsetor_termica_gas
                if not st or st not in codigos or tipo_canonico(subs.set_index("codigo").loc[st, "tipo"]) != "geracao":
                    erros.append("gas_termicas > 0 exige subsetor_termica_gas = código de um subsetor de geração")
            a = espec.componente(r, "fracao_transmissao_distribuicao")
            if a is None or not 0 <= a <= 1:
                erros.append(f"componentes: fracao_transmissao_distribuicao da região {r} fora de [0, 1]")
            if espec.modo_vbp == "ancora_componentes":
                vg = espec.componente(r, "vbp_gas")
                if vg is None or vg < 0:
                    erros.append(f"componentes: vbp_gas da região {r} ausente ou negativo")
                if vg and n_gas != 1:
                    erros.append("vbp_gas > 0 exige exatamente um subsetor 'gas_utilidades'")
    # participações: uma por (região, subsetor), não negativas
    p = espec.participacoes
    for r in espec.regioes:
        pr = p[p["regiao"] == r]
        if set(pr["subsetor"]) != codigos or pr["subsetor"].duplicated().any():
            erros.append(f"participações da região {r}: é preciso exatamente uma linha por subsetor")
            continue
        if espec.modo_vbp == "ancora_componentes":
            # só os pesos da geração importam (MWh × preço); os demais VBPs vêm dos componentes
            pg = pr[pr["subsetor"].map(subs.set_index("codigo")["tipo"]).map(tipo_canonico) == "geracao"]["participacao"]
            if pg.isna().any() or (pg < 0).any() or pg.sum() <= 0:
                erros.append(f"participações da geração na região {r}: precisam ser ≥ 0, sem vazios, com soma > 0")
            continue
        if pr["participacao"].isna().any() or (pr["participacao"] < 0).any():
            erros.append(f"participações vazias ou negativas na região {r}")
        if abs(pr["participacao"].sum() - 1) > TOL_SOMA:
            erros.append(f"participações da região {r} somam {pr['participacao'].sum():.12f} (≠ 1)")
    if set(p["regiao"]) - set(espec.regioes):
        erros.append(f"participações para regiões não desagregadas: {sorted(set(p['regiao']) - set(espec.regioes))}")
    # regras: nomes válidos e subsetores existentes
    for nome, tab, validas in (
        ("regras_coluna", espec.regras_coluna, REGRAS_COLUNA),
        ("regras_linha", espec.regras_linha, REGRAS_LINHA),
        ("regras_primarios", espec.regras_primarios, REGRAS_PRIMARIOS),
    ):
        inv = set(tab["regra"]) - set(validas)
        if inv:
            erros.append(f"{nome}: regras inválidas {sorted(inv)} (válidas: {validas})")
        tipos_validos = {tipo_canonico(x) for x in TIPOS_SUBSETOR}
        por_tipo = tab["regra"].isin(REGRAS_POR_TIPO)
        subs_inv = (set(tab.loc[~por_tipo, "subsetor"]) - codigos - {""}) | \
                   (set(tab.loc[por_tipo, "subsetor"]) - codigos - tipos_validos)
        if subs_inv:
            erros.append(f"{nome}: subsetores inexistentes {sorted(subs_inv)}")
    dest_inv = set(espec.regras_coluna["destino_excedente"]) - set(DESTINOS_EXCEDENTE) - {""}
    if dest_inv:
        erros.append(f"regras_coluna: destino_excedente inválido {sorted(dest_inv)} (válidos: {DESTINOS_EXCEDENTE})")
    if (espec.regras_coluna["teto_vbp"] < 0).any():
        erros.append("regras_coluna: teto_vbp negativo")
    # níveis absolutos (ex.: emissões do SEEG): modo e destinatários do resíduo
    itens_niveis = set(espec.regras_primarios.loc[espec.regras_primarios["regra"] == "niveis", "item"])
    if CURINGA in itens_niveis or "" in itens_niveis:
        erros.append("regras_primarios: a regra 'niveis' exige item explícito (não '*')")
    for item in itens_niveis - {CURINGA, ""}:
        cfg = espec.niveis.get(item)
        if not cfg or cfg.get("modo") not in MODOS_NIVEIS:
            erros.append(f"niveis: configure o modo de '{item}' no YAML (niveis.{item}.modo ∈ {MODOS_NIVEIS})")
        elif cfg["modo"] == "residuo":
            rp = cfg.get("residuo_para") or []
            if not rp or set(rp) - codigos:
                erros.append(f"niveis.{item}.residuo_para precisa listar subsetores existentes (tem {rp})")
    # latentes por espelho
    for le in espec.latentes_espelho.itertuples(index=False):
        if le.regiao not in espec.regioes or le.regiao_espelho not in espec.regioes or le.regiao == le.regiao_espelho:
            erros.append(f"latentes_espelho: {le.regiao} {le.subsetor} ← {le.regiao_espelho}: regiões inválidas")
        if le.subsetor not in codigos:
            erros.append(f"latentes_espelho: subsetor {le.subsetor} inexistente")
    itens_inv = set(espec.regras_primarios["item"]) - set(ITENS_REPARTIVEIS) - {CURINGA}
    if itens_inv:
        erros.append(
            f"regras_primarios: itens inválidos {sorted(itens_inv)} (válidos: {ITENS_REPARTIVEIS}; "
            "EOB é o resíduo e VA é calculado, não recebem regra)"
        )
    if espec.coef_latentes is not None and len(espec.coef_latentes):
        cl = espec.coef_latentes
        for (r, s) in cl[["regiao", "subsetor"]].drop_duplicates().itertuples(index=False):
            linha = p[(p["regiao"] == r) & (p["subsetor"] == s)]
            if r not in espec.regioes or s not in codigos:
                erros.append(f"coef_latentes: subsetor {r} {s} não faz parte da desagregação")
            elif espec.modo_vbp == "participacoes" and len(linha) and linha["participacao"].iloc[0] != 0:
                erros.append(f"coef_latentes: subsetor {r} {s} tem participação não nula (latente exige produção zero)")
        tl_inv = set(cl["tipo_linha"]) - {"setor", "satelite"}
        if tl_inv:
            erros.append(f"coef_latentes: tipo_linha inválido {sorted(tl_inv)}")
    # piso de VBP (D9-f) e reequilíbrio (D9-r)
    pv = espec.piso_vbp
    if pv:
        k = pv.get("kappa")
        if k is None or not 0 < float(k) <= 1:
            erros.append("piso_vbp.kappa precisa estar em (0, 1]")
        comb = pv.get("combustiveis") or {}
        if not comb:
            erros.append("piso_vbp.combustiveis vazio")
        for sub, forn in comb.items():
            if sub not in codigos:
                erros.append(f"piso_vbp.combustiveis: subsetor {sub} inexistente")
            elif tipo_canonico(subs.set_index("codigo").loc[sub, "tipo"]) != "geracao":
                erros.append(f"piso_vbp.combustiveis: {sub} não é de geração")
            cods = set(forn or []) - {"importacoes"}
            inv = cods - set(mip.setores["codigo"])
            if inv or not forn:
                erros.append(f"piso_vbp.combustiveis.{sub}: fornecedores inválidos {sorted(inv) or forn}")
        ev = pv.get("viabilidade_eta")
        if ev is not None and not 0 <= float(ev) < 1:
            erros.append("piso_vbp.viabilidade_eta precisa estar em [0, 1)")
        if espec.modo_vbp != "ancora_componentes":
            erros.append("piso_vbp exige modo_vbp = ancora_componentes (o piso redistribui E_r entre as fontes)")
    rq = espec.reequilibrio
    if rq:
        eta = rq.get("eta")
        if eta is None or not 0 <= float(eta) < 1:
            erros.append("reequilibrio.eta precisa estar em [0, 1)")
        inv = set(rq.get("linhas_fixas") or []) - set(mip.setores["codigo"])
        if inv:
            erros.append(f"reequilibrio.linhas_fixas: setores inexistentes {sorted(inv)}")
        inv = set(rq.get("primarios_ajustaveis", ["ipi", "icms", "outros_impostos"])) - {"ipi", "icms", "outros_impostos"}
        if inv:
            erros.append(f"reequilibrio.primarios_ajustaveis: só ipi, icms e outros_impostos (inválidos: {sorted(inv)})")
        if rq.get("importacoes", "fixas") != "fixas":
            erros.append("reequilibrio.importacoes: só 'fixas' — as importações do setor-alvo são de energia "
                         "(eletricidade e gás, regra do Comex), fixas pelo D9-r; não há importação não energética a mover")
        if rq.get("se_inviavel", "erro") not in ("erro", "limitar"):
            erros.append("reequilibrio.se_inviavel ∈ {erro, limitar}")
    if (espec.regras_primarios["regra"] == "fixa_por_tipo_sem_combustivel").any() and not (pv or {}).get("combustiveis"):
        erros.append("regra fixa_por_tipo_sem_combustivel exige piso_vbp.combustiveis (o combustível de cada subsetor)")
    pt = espec.pesos_tust_geracao
    if pt is not None and len(pt):
        tipos_sub = dict(zip(subs["codigo"], subs["tipo"].map(tipo_canonico)))
        inv = sorted(set(pt["subsetor"]) - codigos)
        if inv:
            erros.append(f"pesos_tust_geracao: subsetores inexistentes {inv}")
        nao_ger = sorted(c for c in set(pt["subsetor"]) & codigos if tipos_sub[c] != "geracao")
        if nao_ger:
            erros.append(f"pesos_tust_geracao: só subsetores de geração (inválidos: {nao_ger})")
        if pt["valor"].isna().any() or (pt["valor"] < 0).any():
            erros.append("pesos_tust_geracao: pesos vazios ou negativos")
        if set(pt["regiao"]) - set(espec.regioes):
            erros.append(f"pesos_tust_geracao: regiões não desagregadas {sorted(set(pt['regiao']) - set(espec.regioes))}")
        if pt.duplicated(["regiao", "subsetor"]).any():
            erros.append("pesos_tust_geracao: (regiao, subsetor) repetido")
        for r in espec.regioes:
            if pt.loc[pt["regiao"] == r, "valor"].sum() <= 0:
                erros.append(f"pesos_tust_geracao: região {r} sem peso positivo")
    if pv and pv.get("viabilidade_eta") is not None:
        if not rq:
            erros.append("piso_vbp.viabilidade_eta exige o bloco reequilibrio (o piso de viabilidade só existe para ele)")
        elif rq.get("eta") is not None and float(pv["viabilidade_eta"]) < float(rq["eta"]):
            erros.append(f"piso_vbp.viabilidade_eta ({pv['viabilidade_eta']}) < reequilibrio.eta ({rq['eta']}): "
                         "o piso não garantiria o EOB mínimo")
    if erros:
        raise EspecificacaoInvalida("especificação inválida:\n  - " + "\n  - ".join(erros))


# =============================================================================================
# Resolução das regras
# =============================================================================================
@dataclass
class _Grupo:
    """Um grupo de regras com a mesma chave (ex.: região RS, fornecedor S04, qualquer região)."""

    chave: dict
    regra: str
    valores: dict
    fonte: str
    fixar: bool = False
    tetos: dict = field(default_factory=dict)  # subsetor → teto como fração do VBP (fixa_com_teto)
    destino: str = "demais_vbp"  # destino do excedente dos tetos
    grupo_teto: str = ""  # insumos que dividem o mesmo teto (vazio = o código do fornecedor, todas as origens)


def _agrupar(tab: pd.DataFrame, chave_cols: list[str], nome: str) -> list[_Grupo]:
    grupos = []
    if len(tab) == 0:
        return grupos
    for chave, g in tab.groupby(chave_cols, sort=False):
        chave = dict(zip(chave_cols, chave if isinstance(chave, tuple) else (chave,)))
        regras = g["regra"].unique()
        if len(regras) != 1:
            raise EspecificacaoInvalida(f"{nome}: chave {chave} com mais de uma regra: {list(regras)}")
        valores, tetos = {}, {}
        for k, (s, v) in enumerate(zip(g["subsetor"], g["valor"])):
            if s:
                if s in valores:
                    raise EspecificacaoInvalida(f"{nome}: chave {chave}: subsetor {s} repetido")
                valores[s] = float(v)
                if "teto_vbp" in g and pd.notna(g["teto_vbp"].iloc[k]):
                    tetos[s] = float(g["teto_vbp"].iloc[k])
        fontes = "; ".join(dict.fromkeys(f for f in g["fonte"] if f))
        fixar = bool(g["fixar_no_ras"].any()) if "fixar_no_ras" in g else False
        destinos = {d for d in g["destino_excedente"] if d} if "destino_excedente" in g else set()
        if len(destinos) > 1:
            raise EspecificacaoInvalida(f"{nome}: chave {chave} com mais de um destino_excedente: {sorted(destinos)}")
        gts = {x for x in g["grupo_teto"] if x} if "grupo_teto" in g else set()
        if len(gts) > 1:
            raise EspecificacaoInvalida(f"{nome}: chave {chave} com mais de um grupo_teto: {sorted(gts)}")
        grupos.append(_Grupo(chave, regras[0], valores, fontes, fixar, tetos,
                             destinos.pop() if destinos else "demais_vbp", gts.pop() if gts else ""))
    return grupos


def _escolher(grupos: list[_Grupo], pontuar, descricao: str) -> _Grupo | None:
    """Regra aplicável mais específica (maior pontuação); empate entre regras diferentes = erro."""
    melhores, melhor = [], -1
    for g in grupos:
        p = pontuar(g.chave)
        if p is None:
            continue
        if p > melhor:
            melhores, melhor = [g], p
        elif p == melhor:
            melhores.append(g)
    if not melhores:
        return None
    if len(melhores) > 1:
        raise EspecificacaoInvalida(
            f"{descricao}: regras ambíguas (mesma especificidade): {[g.chave for g in melhores]}"
        )
    return melhores[0]


def _casa(valor_regra: str, *aceitos) -> bool:
    return valor_regra in (CURINGA, "") or valor_regra in aceitos


def _num_codigo(cod: str) -> int | None:
    digitos = "".join(ch for ch in str(cod) if ch.isdigit())
    return int(digitos) if digitos and str(cod).upper().startswith("S") else None


def _pontua_comprador(regra: str, codigo: str, tipo_df: str | None = None) -> int | None:
    """Pontuação de especificidade do campo `comprador` de uma regra de linha (None = não casa).

    Aceita: '*' (0); 'CI' — todos os setores (1); 'DF' — todas as colunas de demanda final (1);
    tipo de coluna de DF, ex. 'FAM' (2); faixa de setores 'S08:S37' (2); lista 'S08:S37|S43|FAM' (2);
    código exato do setor ou da coluna de DF (3).
    """
    eh_df = tipo_df is not None
    if regra in (CURINGA, ""):
        return 0
    if regra == codigo:
        return 3
    if "|" in regra:
        partes = [_pontua_comprador(x.strip(), codigo, tipo_df) for x in regra.split("|") if x.strip()]
        return 2 if any(p is not None and p > 0 for p in partes) else None
    if regra == "CI":
        return None if eh_df else 1
    if regra == "DF":
        return 1 if eh_df else None
    if eh_df and regra == tipo_df:
        return 2
    if ":" in regra and not eh_df:
        a, b = (_num_codigo(x) for x in regra.split(":", 1))
        n = _num_codigo(codigo)
        if a is not None and b is not None and n is not None and a <= n <= b:
            return 2
    return None


@dataclass
class _GrupoAlvo:
    """Subsetores do setor-alvo numa região (ou o setor agregado, se a região não é desagregada)."""

    regiao: str
    idx_orig: int
    idx_novo: list
    codigos: list
    tipos: list
    s: np.ndarray  # participações efetivas no VBP
    desagregado: bool


def _pesos(grupo: _Grupo | None, ga: _GrupoAlvo, descricao: str, base_tipo: np.ndarray | None = None
           ) -> tuple[np.ndarray, str, str]:
    """Pesos de repartição entre os subsetores (somam 1). Devolve (pesos, regra, fonte).

    `base_tipo`: base da repartição dentro do tipo nas regras por tipo (padrão: o VBP; na
    fixa_por_tipo_sem_combustivel, VBP − combustível)."""
    s = ga.s
    if not ga.desagregado:
        return np.ones(1), "agregado", ""
    regra = grupo.regra if grupo else "proporcional_vbp"
    fonte = grupo.fonte if grupo else "padrão (proporcional ao VBP)"
    if regra == "proporcional_vbp":
        w = s / s.sum()
    elif regra in ("fixa", "fixa_por_comprador"):
        w = np.array([grupo.valores.get(c, 0.0) for c in ga.codigos])
        if (w < 0).any() or abs(w.sum() - 1) > TOL_SOMA:
            raise EspecificacaoInvalida(f"{descricao}: participações fixas devem ser ≥ 0 e somar 1 (soma = {w.sum()})")
    elif regra in REGRAS_POR_TIPO:
        # valor por subsetor (código) ou por tipo (geracao, transmissao, ...): dentro do tipo, na proporção do VBP
        # (fixa_por_tipo) ou de VBP − combustível (fixa_por_tipo_sem_combustivel; base_tipo)
        b = s if base_tipo is None else np.maximum(np.asarray(base_tipo, dtype=float), 0.0) * (s > 0)
        w = np.zeros(len(ga.codigos))
        tipos = [tipo_canonico(x) for x in ga.tipos]
        for chave, v in grupo.valores.items():
            if chave in ga.codigos:
                w[ga.codigos.index(chave)] += v
                continue
            membros = [k for k, tk in enumerate(tipos) if tk == tipo_canonico(chave) and s[k] > 0 and b[k] > 0]
            if v > 0 and not membros:
                raise EspecificacaoInvalida(f"{descricao}: {regra} dá {v} ao tipo '{chave}', sem subsetor com base > 0")
            if membros:
                w[membros] += v * b[membros] / b[membros].sum()
        if (w < 0).any() or abs(w.sum() - 1) > TOL_SOMA:
            raise EspecificacaoInvalida(f"{descricao}: {regra} deve somar 1 (soma = {w.sum()})")
    elif regra == "indicador":
        faltam = [c for c, sk in zip(ga.codigos, s) if sk > 0 and c not in grupo.valores]
        if faltam:
            raise EspecificacaoInvalida(f"{descricao}: indicador sem valor para {faltam}")
        ind = np.array([grupo.valores.get(c, 0.0) for c in ga.codigos])
        if (ind < 0).any():
            raise EspecificacaoInvalida(f"{descricao}: indicador negativo")
        base = s * ind
        if base.sum() <= 0:
            raise EspecificacaoInvalida(f"{descricao}: Σ VBP × indicador = 0")
        w = base / base.sum()
    elif regra in ("somente_rede_e_gas", "somente_distribuicao_e_gas"):
        m = np.isin([tipo_canonico(t) for t in ga.tipos], ["distribuicao", "gas_utilidades"])
        base = np.where(m, s, 0.0)
        if base.sum() <= 0:
            raise EspecificacaoInvalida(f"{descricao}: {regra}, mas distribuição e gás têm VBP zero")
        w = base / base.sum()
    elif regra == "fixa_com_teto":  # participações-base; os tetos são aplicados em _alocar_com_teto
        w = np.array([grupo.valores.get(c, 0.0) for c in ga.codigos])
        if (w < 0).any() or abs(w.sum() - 1) > TOL_SOMA:
            raise EspecificacaoInvalida(f"{descricao}: participações fixas devem ser ≥ 0 e somar 1 (soma = {w.sum()})")
        semteto = [c for c, wk, sk in zip(ga.codigos, w, s) if wk > 0 and sk == 0 and c not in grupo.tetos]
        if semteto:
            raise EspecificacaoInvalida(f"{descricao}: fixa_com_teto dá valor sem teto a subsetor com produção zero: {semteto}")
        return w, regra, fonte
    else:  # pragma: no cover - validado antes
        raise EspecificacaoInvalida(f"{descricao}: regra desconhecida {regra}")
    if ((w > 0) & (s == 0)).any():
        zerados = [c for c, wk, sk in zip(ga.codigos, w, s) if wk > 0 and sk == 0]
        raise EspecificacaoInvalida(
            f"{descricao}: regra '{regra}' atribui valor a subsetor com produção zero: {zerados}"
        )
    return w, regra, fonte


def _alocar_grupo_com_teto(celulas: list[tuple[float, _Grupo]], ga: _GrupoAlvo, X_sub: np.ndarray,
                           descricao: str) -> tuple[list[np.ndarray], list[dict]]:
    """Reparte um insumo (todas as origens, e os insumos que dividem o mesmo grupo_teto) com tetos sobre o TOTAL.

    Cada célula (valor, regra) é repartida primeiro pelas participações fixas da sua regra. Para cada subsetor
    com teto, o total do grupo (soma das células) fica limitado a teto × VBP; quando o teto é atingido, a parte
    de cada célula nesse subsetor é reduzida na mesma proporção. O excedente de cada célula vai, conforme o
    `destino_excedente` da regra, aos "demais" subsetores (sem teto no grupo), na proporção do VBP
    ('demais_vbp'), ou aos subsetores da regra sem teto, na proporção das participações ('sem_teto').
    Cada célula continua somando o seu valor original (re-agregação exata). Valores ≤ 0 não são limitados.
    Devolve a alocação de cada célula e a lista dos tetos atingidos (no total do grupo).
    """
    tetos: dict[str, float] = {}
    for _, g in celulas:
        for c, tt in g.tetos.items():
            if c in tetos and abs(tetos[c] - tt) > 1e-12:
                raise EspecificacaoInvalida(f"{descricao}: tetos diferentes para {c} no mesmo grupo ({tetos[c]} e {tt})")
            tetos[c] = tt
    bases = []
    for z, g in celulas:
        w, _, _ = _pesos(g, ga, descricao)
        bases.append(w * z)
    pos = [z > 0 for z, _ in celulas]
    base_tot = sum((b for b, p in zip(bases, pos) if p), np.zeros(len(ga.codigos)))
    fator = np.ones(len(ga.codigos))
    atingidos = []
    for k, c in enumerate(ga.codigos):
        if c in tetos:
            lim = tetos[c] * X_sub[k]
            if base_tot[k] > lim + 1e-12:
                fator[k] = lim / base_tot[k]
                atingidos.append({"subsetor": c, "valor_pela_regra": base_tot[k], "teto": lim,
                                  "teto_fracao_vbp": tetos[c], "excedente": base_tot[k] - lim})
    com_teto = np.array([c in tetos for c in ga.codigos])
    alocs = []
    for (z, g), b, p in zip(celulas, bases, pos):
        if not p:
            alocs.append(b)
            continue
        aloc = b * fator
        exced = z - aloc.sum()
        if exced > 1e-12 * max(1.0, abs(z)):
            if g.destino == "sem_teto":
                w, _, _ = _pesos(g, ga, descricao)
                base = np.where(com_teto, 0.0, w)
            else:
                base = np.where(com_teto, 0.0, X_sub)
            if base.sum() <= 0:
                raise EspecificacaoInvalida(f"{descricao}: excedente de teto ({exced:.4f}) sem destinatário ({g.destino})")
            aloc = aloc + exced * base / base.sum()
        alocs.append(aloc)
    return alocs, atingidos


def _alocar_com_teto(grupo: _Grupo, ga: _GrupoAlvo, valor: float, X_sub: np.ndarray,
                     descricao: str) -> tuple[np.ndarray, list[dict]]:
    """Caso de uma única célula de `_alocar_grupo_com_teto`."""
    alocs, atingidos = _alocar_grupo_com_teto([(valor, grupo)], ga, X_sub, descricao)
    return alocs[0], atingidos


# =============================================================================================
# RAS (biproporcional)
# =============================================================================================
@dataclass
class InfoRAS:
    contexto: str
    necessario: bool
    convergiu: bool
    iteracoes: int
    erro_max: float
    erro_inicial: float


def ras(
    M0: np.ndarray,
    alvo_linhas: np.ndarray,
    alvo_colunas: np.ndarray,
    fixas: np.ndarray | None = None,
    tol: float = 1e-8,
    max_iter: int = 10000,
    contexto: str = "",
) -> tuple[np.ndarray, InfoRAS]:
    """Ajuste biproporcional: escala linhas e colunas de M0 até bater com os totais-alvo.

    Células marcadas em `fixas` não mudam (seus valores são descontados dos alvos). Células livres
    devem ser ≥ 0; zeros continuam zero. Devolve a matriz ajustada e o relatório de convergência.
    """
    M0 = np.asarray(M0, dtype=float)
    fixas = np.zeros_like(M0, dtype=bool) if fixas is None else np.asarray(fixas, dtype=bool)
    livre = np.where(fixas, 0.0, M0)
    if (livre < 0).any():
        raise ValueError("RAS: células livres negativas (marque-as como fixas)")
    F = np.where(fixas, M0, 0.0)
    u = np.asarray(alvo_linhas, dtype=float) - F.sum(axis=1)
    v = np.asarray(alvo_colunas, dtype=float) - F.sum(axis=0)

    def erro(M):
        return max(np.abs(M.sum(axis=1) - u).max(initial=0.0), np.abs(M.sum(axis=0) - v).max(initial=0.0))

    M = livre.copy()
    e0 = erro(M)
    if e0 <= tol:
        return M + F, InfoRAS(contexto, False, True, 0, e0, e0)
    it = 0
    for it in range(1, max_iter + 1):
        rs = M.sum(axis=1)
        M *= np.where(rs > 0, u / np.where(rs > 0, rs, 1.0), 1.0)[:, None]
        cs = M.sum(axis=0)
        M *= np.where(cs > 0, v / np.where(cs > 0, cs, 1.0), 1.0)[None, :]
        e = erro(M)
        if e <= tol:
            return M + F, InfoRAS(contexto, True, True, it, e, e0)
    return M + F, InfoRAS(contexto, True, False, it, erro(M), e0)


# =============================================================================================
# Resultado
# =============================================================================================
@dataclass
class ResultadoDesagregacao:
    mip: MIP
    original: MIP
    especificacao: Especificacao
    mapa: pd.DataFrame
    pesos: pd.DataFrame
    info_ras: pd.DataFrame
    checagens: pd.DataFrame = field(default_factory=pd.DataFrame)
    extras: dict = field(default_factory=dict)  # tabelas auxiliares (componentes do bloco, tetos, níveis)

    @property
    def ok(self) -> bool:
        return not (self.checagens["status"] == "FALHA").any()

    @property
    def alertas(self) -> pd.DataFrame:
        return self.checagens[self.checagens["status"] == "ALERTA"]

    def leiame(self) -> list[str]:
        e = self.especificacao
        linhas = []
        if e.aviso:
            linhas += [e.aviso, ""]
        linhas += [
            f"MIP desagregada — especificação: {e.nome}",
            e.descricao,
            f"Setor desagregado: {e.setor_alvo}, nas regiões {', '.join(e.regioes)}; "
            f"subsetores: {', '.join(e.subsetores['codigo'])}.",
            f"Bloco intrassetorial: {e.bloco}; modo do VBP: {e.modo_vbp}.",
            "A soma dos subsetores reproduz cada célula da MIP original (ver aba checagens).",
        ]
        if e.piso_vbp:
            pv = e.piso_vbp
            linhas.append(
                f"Piso de VBP (D9-f): VBP de cada térmica ≥ combustível ÷ κ (κ = {pv['kappa']})"
                + (f" e ≥ combustível ÷ (1 − η − φ) (viabilidade, η = {pv['viabilidade_eta']}; φ = custos que o "
                   "reequilíbrio não pode mexer, fora o combustível, ÷ VBP)" if pv.get("viabilidade_eta") is not None else "")
                + "; quem fica abaixo sobe e as demais fontes da região caem na proporção do VBP (VBP da geração fixo). "
                "Aba pisos_vbp.")
        if e.reequilibrio:
            rq = e.reequilibrio
            linhas.append(
                f"EOB: resíduo que fecha a coluna, depois do reequilíbrio (D9-r): RAS dos insumos não energéticos "
                f"(compras fora do bloco, exceto combustíveis; {', '.join(rq.get('primarios_ajustaveis', ['ipi', 'icms', 'outros_impostos']))}) "
                f"para que EOB ≥ η × VBP (η = {rq['eta']}) em todo subsetor com produção; total de cada insumo na "
                "região e Σ EOB da região preservados. Abas reequilibrio_RAS e reequilibrio_insumos; na aba parametros, "
                "etapa 'regra' = pesos antes do reequilíbrio e 'apos_reequilibrio' = pesos realizados.")
        else:
            linhas.append("EOB de cada subsetor = resíduo que fecha a coluna (EOB negativo é sinalizado em checagens, não corrigido).")
        linhas += [
            "Aba principal: mesmo layout da planilha original, com os subsetores no lugar do setor-alvo.",
            "Abas: mapa_setores (original → novo), parametros (todos os pesos usados, com fonte), "
            "checagens, ras (conciliação das linhas), coef_latentes (se houver subsetores latentes).",
            "Subsetores latentes: produção-base zero; a coluna de coeficientes técnicos fica na aba coef_latentes "
            "(não aparece como fluxo) e é usada pelo modelo para simular choques nesses subsetores.",
            f"Arquivos de parâmetros: {'; '.join(f'{k}={v}' for k, v in e.arquivos.items())}",
        ]
        if e.aviso:
            linhas += ["", e.aviso]
        return linhas

    def exportar(self, caminho_xlsx: str | Path, caminho_csv: str | Path | None = None) -> None:
        from .exportacao import exportar_longo, exportar_xlsx

        abas = {
            "mapa_setores": self.mapa,
            "parametros": self.pesos,
            "checagens": self.checagens,
            "ras": self.info_ras,
        }
        for nome, tab in self.extras.items():
            abas[nome] = tab
        if self.mip.coef_latentes is not None and len(self.mip.coef_latentes):
            abas["coef_latentes"] = self.mip.coef_latentes
        sub_ids = list(self.mapa.loc[self.mapa["desagregado"], "id_novo"])
        exportar_xlsx(
            self.mip,
            caminho_xlsx,
            aviso_topo=self.especificacao.aviso,
            leiame=self.leiame(),
            abas_extras=abas,
            destacar_setores=sub_ids,
        )
        if caminho_csv is not None:
            exportar_longo(self.mip, caminho_csv)
            if self.mip.coef_latentes is not None and len(self.mip.coef_latentes):
                # ler_mip_longo procura este arquivo ao lado do longo; sem ele, os latentes ficariam sem coluna
                from .leitura import caminho_coef_latentes_ao_lado

                self.mip.coef_latentes.to_csv(caminho_coef_latentes_ao_lado(caminho_csv), index=False)


# =============================================================================================
# Desagregação
# =============================================================================================
def _participacoes_efetivas(espec: Especificacao, mip: MIP, idx_alvo: dict) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    """Participações no VBP de cada região desagregada e, no roteamento, os componentes do bloco.

    - participacoes: as informadas;
    - ancora_bloco: VBP da geração = vendas do setor-alvo da região ao setor-alvo de todas as regiões;
    - ancora_componentes: geração = E_r = F_r − T_r − G_r (repartida pelos pesos da geração); transmissão = T_r;
      gás = vbp_gas; distribuição = X_r − E_r − T_r − vbp_gas (tem de ser > 0).
    """
    subs = espec.subsetores
    tipos = subs["tipo"].map(tipo_canonico).to_numpy()
    ger = tipos == "geracao"
    saida, comps = {}, []
    for r in espec.regioes:
        p = espec.participacoes[espec.participacoes["regiao"] == r].set_index("subsetor")["participacao"]
        s = p.reindex(subs["codigo"]).to_numpy(dtype=float)
        i = idx_alvo[r]
        Xr = mip.X[i]
        F = float(sum(mip.Z[i, idx_alvo[r2]] for r2 in idx_alvo))  # vendas ao setor-alvo de todas as regiões
        if espec.modo_vbp == "ancora_bloco":
            sg, sn = s[ger].sum(), s[~ger].sum()
            if (F > 0 and sg <= 0) or (Xr - F > 0 and sn <= 0):
                raise EspecificacaoInvalida(f"ancora_bloco na região {r}: grupo sem participação positiva")
            novo = np.zeros_like(s)
            novo[ger] = (F / Xr) * s[ger] / sg if sg > 0 else 0.0
            novo[~ger] = ((Xr - F) / Xr) * s[~ger] / sn if sn > 0 else 0.0
            s = novo
        if espec.bloco == "roteamento_por_componentes":
            T = espec.componente(r, "vbp_transmissao")
            G = espec.componente(r, "gas_termicas") or 0.0
            E = F - T - G
            tol = 1e-9 * max(1.0, F)
            if E < -tol:
                raise EspecificacaoInvalida(
                    f"roteamento na região {r}: E_r = F_r − T_r − G_r = {F:.4f} − {T:.4f} − {G:.4f} = {E:.4f} < 0 "
                    "(a transmissão e o gás às térmicas não cabem nas vendas do bloco)"
                )
            E = max(E, 0.0)
            linha = {"regiao": r, "VBP_setor (X_r)": Xr, "F_r (vendas ao bloco)": F, "T_r (transmissão)": T,
                     "G_r (gás às térmicas)": G, "E_r (energia = VBP da geração)": E,
                     "fracao_transmissao_distribuicao": espec.componente(r, "fracao_transmissao_distribuicao")}
            if espec.modo_vbp == "ancora_componentes":
                Vg = espec.componente(r, "vbp_gas") or 0.0
                D = Xr - E - T - Vg
                linha.update({"VBP_gas": Vg, "VBP_distribuicao (resíduo)": D})
                if D <= 0:
                    raise EspecificacaoInvalida(
                        f"ancora_componentes na região {r}: VBP da distribuição = X_r − E_r − T_r − VBP_gas = "
                        f"{Xr:.4f} − {E:.4f} − {T:.4f} − {Vg:.4f} = {D:.4f} ≤ 0"
                    )
                sg = np.where(ger, np.nan_to_num(s), 0.0)
                novo = np.zeros_like(s)
                novo[ger] = (E / Xr) * sg[ger] / sg.sum()
                novo[tipos == "transmissao"] = T / Xr
                novo[tipos == "gas_utilidades"] = Vg / Xr
                novo[tipos == "distribuicao"] = D / Xr
                s = novo
            comps.append(linha)
        saida[r] = s
    return saida, pd.DataFrame(comps)


def _matriz_agregacao(mapa: pd.DataFrame, n_orig: int, n_novo: int) -> np.ndarray:
    P = np.zeros((n_orig, n_novo))
    P[mapa["indice_original"].to_numpy(), mapa["indice_novo"].to_numpy()] = 1.0
    return P


def agregar(mip_novo: MIP, mapa: pd.DataFrame, setores_originais: pd.DataFrame) -> MIP:
    """Re-agrega a MIP desagregada (soma os subsetores) para a classificação original."""
    P = _matriz_agregacao(mapa, len(setores_originais), mip_novo.n)
    return MIP(
        setores=setores_originais[["regiao", "codigo", "nome"]].copy(),
        Z=P @ mip_novo.Z @ P.T,
        F=P @ mip_novo.F,
        total_linha=P @ mip_novo.total_linha,
        X=P @ mip_novo.X,
        V=mip_novo.V @ P.T,
        V_df=mip_novo.V_df.copy(),
        X_df=mip_novo.X_df.copy(),
        S=mip_novo.S @ P.T,
        totais_ev=dict(mip_novo.totais_ev),
        titulo=mip_novo.titulo,
    )


def _celulas_roteamento(espec: Especificacao, gv: _GrupoAlvo, gc: _GrupoAlvo, B: float, Fr: float) -> np.ndarray:
    """Bloco vendedor gv → comprador gc no roteamento por componentes (Seção 6.2 da Rodada 02).

    Para a região vendedora r: F_r = vendas ao setor-alvo de todas as regiões; T_r = VBP da transmissão;
    G_r = gás às térmicas; E_r = F_r − T_r − G_r (energia). Cada componente vai à região compradora q na
    proporção F_rq / F_r. Energia: geração de r (∝ VBP) → distribuição de q. Transmissão: TRA de r →
    fração α à distribuição de q e (1 − α) à geração de q (∝ VBP). Gás: GAS de r → térmica a gás de q.
    Vendedor não desagregado: o fluxo vai ao grupo comprador na proporção do VBP.
    """
    if not gv.desagregado:
        return np.outer(np.ones(1), gc.s / gc.s.sum()) * B
    frac = B / Fr if Fr else 0.0
    r = gv.regiao
    T = espec.componente(r, "vbp_transmissao")
    G = espec.componente(r, "gas_termicas") or 0.0
    E = max(Fr - T - G, 0.0)
    alfa = espec.componente(r, "fracao_transmissao_distribuicao")
    tv = np.array(gv.tipos)
    ger_v = tv == "geracao"
    sg = gv.s[ger_v].sum()
    if E * frac > 0 and sg <= 0:
        raise EspecificacaoInvalida(f"roteamento: {r} vende energia ({E * frac:.4f}), mas a geração de {r} tem VBP zero")
    w_ger_v = np.where(ger_v, gv.s / sg, 0.0) if sg > 0 else np.zeros(len(tv))
    w_tra_v = (tv == "transmissao").astype(float)
    w_gas_v = (tv == "gas_utilidades").astype(float)
    if gc.desagregado:
        tc = np.array(gc.tipos)
        w_dis_c = (tc == "distribuicao").astype(float)
        ger_c = tc == "geracao"
        sgc = gc.s[ger_c].sum()
        if (1 - alfa) * T * frac > 0 and sgc <= 0:
            raise EspecificacaoInvalida(f"roteamento: a geração de {gc.regiao} tem VBP zero e não pode pagar transmissão")
        w_ger_c = np.where(ger_c, gc.s / sgc, 0.0) if sgc > 0 else np.zeros(len(tc))
        pt = espec.pesos_tust_geracao
        if pt is not None and len(pt):  # V1 (Rodada 04): TUST da geração por pesos próprios (MWh no SIN)
            pr = pt[pt["regiao"] == gc.regiao].set_index("subsetor")["valor"]
            p = np.array([float(pr.get(c, 0.0)) if g else 0.0 for c, g in zip(gc.codigos, ger_c)])
            sem_base = [c for c, pk, sk in zip(gc.codigos, p, gc.s) if pk > 0 and sk <= 0]
            if sem_base:
                raise EspecificacaoInvalida(f"pesos_tust_geracao em {gc.regiao}: peso para subsetor sem produção {sem_base}")
            if (1 - alfa) * T * frac > 0 and p.sum() <= 0:
                raise EspecificacaoInvalida(f"pesos_tust_geracao em {gc.regiao}: soma zero")
            w_ger_c = p / p.sum() if p.sum() > 0 else w_ger_c
        w_gn_c = (np.array(gc.codigos) == espec.subsetor_termica_gas).astype(float)
    else:
        w_dis_c = w_ger_c = w_gn_c = np.ones(1)
    cel = np.outer(w_ger_v, w_dis_c) * E * frac
    cel += np.outer(w_tra_v, w_dis_c) * alfa * T * frac
    cel += np.outer(w_tra_v, w_ger_c) * (1 - alfa) * T * frac
    if G > 0:
        cel += np.outer(w_gas_v, w_gn_c) * G * frac
    return cel


def _repartir_niveis(espec: Especificacao, item: str, grupo: _Grupo, ga: _GrupoAlvo, total: float,
                     X_sub: np.ndarray, descricao: str) -> tuple[np.ndarray, dict]:
    """Níveis absolutos por subsetor (ex.: emissões do SEEG) e tratamento do resíduo em relação ao total da base.

    Modos (YAML niveis.<item>.modo): 'residuo' (E1) — níveis + resíduo (total − Σ níveis) aos subsetores de
    `residuo_para`, na proporção do VBP; resíduo negativo reduz os níveis proporcionalmente (sinalizado);
    'proporcional' (E2) — total da base repartido na proporção dos níveis; 'sem_residuo' (E3) — só os níveis
    (NÃO preserva o total da base).
    """
    L = np.array([grupo.valores.get(c, 0.0) for c in ga.codigos], dtype=float)
    if (L < 0).any() or np.isnan(L).any():
        raise EspecificacaoInvalida(f"{descricao}: níveis negativos ou vazios")
    zerados = [c for c, lk, xk in zip(ga.codigos, L, X_sub) if lk > 0 and xk == 0]
    if zerados:
        raise EspecificacaoInvalida(f"{descricao}: nível positivo em subsetor com produção zero: {zerados}")
    cfg = espec.niveis[item]
    modo = cfg["modo"]
    soma = L.sum()
    info = {"regiao": ga.regiao, "item": item, "modo": modo, "total_base": total, "identificado": soma,
            "residuo": total - soma, "fator_reducao_identificados": 1.0, "preserva_total": modo != "sem_residuo",
            "observacao": ""}
    if modo == "residuo":
        R = total - soma
        if R >= 0:
            m = np.isin(ga.codigos, cfg["residuo_para"])
            base = np.where(m, X_sub, 0.0)
            if R > 0 and base.sum() <= 0:
                raise EspecificacaoInvalida(f"{descricao}: resíduo {R:.4f} sem destinatário com VBP > 0")
            vals = L + (R * base / base.sum() if R > 0 else 0.0)
        else:
            f = total / soma
            vals = L * f
            info["fator_reducao_identificados"] = f
            info["observacao"] = f"resíduo negativo ({R:.4f}): níveis identificados reduzidos pelo fator {f:.6f}"
    elif modo == "proporcional":
        if soma <= 0:
            raise EspecificacaoInvalida(f"{descricao}: modo proporcional com Σ níveis = 0")
        vals = total * L / soma
    else:  # sem_residuo
        vals = L.copy()
        info["observacao"] = f"NÃO PRESERVA o total da base: diferença = {soma - total:.4f}"
    return vals, info


def _latentes_por_espelho(espec: Especificacao, mip: MIP, grupos: dict, setores2: pd.DataFrame,
                          Z2: np.ndarray, X2: np.ndarray, S2: np.ndarray) -> pd.DataFrame:
    """Coluna de coeficientes de um subsetor latente copiada do mesmo subsetor em outra região (Seção 6.5).

    Para cada fornecedor (código), soma o coeficiente das duas origens na coluna do espelho; reparte entre
    as origens pela participação de cada origem nas compras desse insumo na coluna ORIGINAL do setor-alvo da
    região do latente. Para fornecedores que são subsetores do próprio setor-alvo (ex.: transmissão), usa a
    participação das origens no bloco alvo→alvo dessa região. Se o setor-alvo original não compra o insumo,
    usa a participação das origens no total das compras fora do bloco (fallback, registrado na fonte).
    Intensidades satélite: as do espelho.
    """
    linhas = []
    t = espec.setor_alvo
    regs = list(grupos)
    pares = set(zip(setores2["regiao"], setores2["codigo"]))
    for le in espec.latentes_espelho.itertuples(index=False):
        gl, ge = grupos[le.regiao], grupos[le.regiao_espelho]
        k = gl.codigos.index(le.subsetor)
        if gl.s[k] != 0:
            raise EspecificacaoInvalida(f"latente {le.regiao} {le.subsetor}: a produção-base precisa ser zero")
        m = ge.idx_novo[ge.codigos.index(le.subsetor)]
        Xm = X2[m]
        if Xm <= 0:
            raise EspecificacaoInvalida(f"latente {le.regiao} {le.subsetor}: o espelho {le.regiao_espelho} tem VBP zero")
        a = Z2[:, m] / Xm
        a_cod = pd.Series(a, index=setores2["codigo"].to_numpy()).groupby(level=0, sort=False).sum()
        j0 = gl.idx_orig
        bloco_in = np.array([mip.Z[grupos[q].idx_orig, j0] for q in regs])
        fora_reg = {q: mip.Z[(mip.setores["regiao"] == q).to_numpy() & (mip.setores["codigo"] != t).to_numpy(), j0].sum()
                    for q in regs}
        tot_fora = sum(fora_reg.values())
        fonte_base = le.fonte or f"espelho de {le.regiao_espelho} {le.subsetor}"
        for cod, val in a_cod.items():
            if val == 0:
                continue
            if cod in gl.codigos or cod == t:
                w = bloco_in / bloco_in.sum() if bloco_in.sum() > 0 else np.full(len(regs), 1 / len(regs))
                nota = "origens pelo bloco alvo→alvo da região"
            else:
                compras = np.array([mip.Z[mip.indice(q, cod), j0] for q in regs])
                if compras.sum() > 0:
                    w = compras / compras.sum()
                    nota = "origens pela coluna original do setor-alvo"
                else:
                    w = np.array([fora_reg[q] / tot_fora for q in regs])
                    nota = "insumo não comprado na coluna original: origens pelo total das compras fora do bloco (fallback)"
            for q, wq in zip(regs, w):
                if wq <= 0:
                    continue
                cod_q = cod if (q, cod) in pares else t  # região não desagregada: setor agregado
                linhas.append((le.regiao, le.subsetor, "setor", q, cod_q, float(val * wq), f"{fonte_base}; {nota}"))
        for kk, item in enumerate(ITENS_SATELITE):
            linhas.append((le.regiao, le.subsetor, "satelite", "", item, float(S2[kk, m] / Xm),
                           f"{fonte_base}; intensidade do espelho"))
    return pd.DataFrame(linhas, columns=COLS_COEF_LATENTES)


def desagregar(mip: MIP, espec: Especificacao, estrito: bool = True) -> ResultadoDesagregacao:
    """Desagrega `espec.setor_alvo` em subsetores e verifica o resultado.

    Com estrito=True, levanta DesagregacaoInvalida se alguma checagem der FALHA
    (ALERTA, como EOB negativo, não interrompe: fica registrado nas checagens).

    Opções da Rodada 03 (YAML): `piso_vbp` (D9-f: VBP das térmicas ≥ combustível ÷ κ, redistribuindo E_r entre as
    fontes da mesma região; repete a desagregação até estabilizar) e `reequilibrio` (D9-r: RAS dos insumos não
    energéticos para que EOB ≥ η × VBP, preservando o total de cada insumo e a soma dos EOB da região).
    """
    validar_especificacao(espec, mip)
    espec_final, pisos = espec, None
    if espec.piso_vbp:
        espec_final, pisos = _resolver_pisos(mip, espec)
    res = _desagregar_passo(mip, espec_final, reequilibrar=bool(espec.reequilibrio))
    if pisos is not None:
        res.extras["pisos_vbp"] = pisos
    res.checagens = verificar(res)
    if estrito and not res.ok:
        falhas = res.checagens[res.checagens["status"] == "FALHA"]
        raise DesagregacaoInvalida("verificação falhou:\n" + falhas.to_string(index=False))
    return res


def _custos_fixos_e_combustivel(espec: Especificacao, m2: MIP, mapa: pd.DataFrame, idx: list[int]) -> tuple[np.ndarray, np.ndarray]:
    """(custos fixos, combustível) de cada coluna em `idx` — D9-f/r.

    Fixos: compras ao bloco (setor-alvo de todas as regiões), compras às linhas de combustível (`linhas_fixas`),
    importações (todas de energia), remunerações e impostos sobre a produção. Combustível: as linhas de
    `piso_vbp.combustiveis` de cada subsetor (e as importações, se listadas).
    """
    ip = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}
    cod_orig = mapa["codigo_original"].to_numpy()
    cod_novo = list(mapa["codigo_novo"])
    comb_cfg = espec.piso_vbp.get("combustiveis") or {}
    fixas = set(espec.reequilibrio.get("linhas_fixas") or []) | {c for v in comb_cfg.values() for c in v if c != "importacoes"}
    bloco = cod_orig == espec.setor_alvo
    linhas_fixas = np.isin(cod_orig, sorted(fixas)) & ~bloco
    fixos = (m2.Z[bloco][:, idx].sum(axis=0) + m2.Z[linhas_fixas][:, idx].sum(axis=0)
             + m2.V[ip["remuneracoes"], idx] + m2.V[ip["impostos_producao"], idx] + m2.V[ip["importacoes"], idx])
    comb = np.zeros(len(idx))
    for n, k in enumerate(idx):
        forn = comb_cfg.get(cod_novo[k]) or []
        linhas = np.isin(cod_orig, [c for c in forn if c != "importacoes"]) & ~bloco
        comb[n] = m2.Z[linhas, k].sum() + (m2.V[ip["importacoes"], k] if "importacoes" in forn else 0.0)
    return fixos, comb


def _combustivel_nas_colunas(espec: Especificacao, Z2: np.ndarray, V2: np.ndarray, mapa: pd.DataFrame,
                            idx: list[int], ip: dict) -> np.ndarray:
    """Combustível de cada coluna em `idx` (linhas de piso_vbp.combustiveis, de todas as origens, e as importações
    se listadas), com as matrizes em construção — usado pela regra fixa_por_tipo_sem_combustivel (V1, Rodada 04)."""
    cod_orig = mapa["codigo_original"].to_numpy()
    cod_novo = list(mapa["codigo_novo"])
    bloco = cod_orig == espec.setor_alvo
    comb_cfg = espec.piso_vbp.get("combustiveis") or {}
    out = np.zeros(len(idx))
    for n, k in enumerate(idx):
        forn = comb_cfg.get(cod_novo[k]) or []
        linhas = np.isin(cod_orig, [c for c in forn if c != "importacoes"]) & ~bloco
        out[n] = Z2[linhas, k].sum() + (V2[ip["importacoes"], k] if "importacoes" in forn else 0.0)
    return out


def _eob_maximo(espec: Especificacao, m2: MIP, mapa: pd.DataFrame, idx: list[int]) -> np.ndarray:
    """EOB que cada coluna teria com todos os insumos ajustáveis (D9-r) positivos a zero: EOB + Σ ajustáveis > 0."""
    ip = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}
    cod_orig = mapa["codigo_original"].to_numpy()
    fixas = set(espec.reequilibrio.get("linhas_fixas") or []) | {
        c for v in (espec.piso_vbp.get("combustiveis") or {}).values() for c in v if c != "importacoes"}
    aj = ~np.isin(cod_orig, sorted(fixas)) & (cod_orig != espec.setor_alvo)
    itens = list(espec.reequilibrio.get("primarios_ajustaveis", ["ipi", "icms", "outros_impostos"]))
    M = np.vstack([m2.Z[aj][:, idx], m2.V[[ip[x] for x in itens]][:, idx]])
    return m2.V[ip["eob"], idx] + np.where(M > 0, M, 0.0).sum(axis=0)


def _redistribuir_com_piso(g: np.ndarray, piso: np.ndarray, E: float, contexto: str) -> np.ndarray:
    """Eleva ao piso quem estiver abaixo e reduz os demais na proporção do VBP, mantendo Σ = E (itera)."""
    preso = np.zeros(len(g), dtype=bool)
    novo = g.copy()
    for _ in range(len(g) + 1):
        livres = ~preso
        resto = E - piso[preso].sum()
        if resto < -1e-9 * max(1.0, E) or (livres.any() and g[livres].sum() <= 0 and resto > 1e-9 * max(1.0, E)):
            raise EspecificacaoInvalida(
                f"piso_vbp em {contexto}: os pisos ({piso[preso].sum():.4f}) não cabem no VBP da geração E_r = {E:.4f}")
        novo = np.where(preso, piso, 0.0)
        if not livres.any() and abs(resto) > 1e-9 * max(1.0, E):
            raise EspecificacaoInvalida(
                f"piso_vbp em {contexto}: todas as fontes ficaram no piso e sobram {resto:.4f} de E_r sem destino")
        if livres.any() and g[livres].sum() > 0:
            novo[livres] = g[livres] * resto / g[livres].sum()
        abaixo = (novo < piso * (1 - 1e-12) - 1e-12) & livres
        if not abaixo.any():
            return novo
        preso |= abaixo
    raise EspecificacaoInvalida(f"piso_vbp em {contexto}: a redistribuição não estabilizou")


def _resolver_pisos(mip: MIP, espec: Especificacao) -> tuple[Especificacao, pd.DataFrame]:
    """D9-f: VBP_k ≥ combustível_k ÷ κ (e, com viabilidade_eta, ≥ combustível_k ÷ (1 − η − φ_k), em que φ_k é a
    parte dos custos fixos não combustíveis no VBP_k), elevando k e reduzindo os demais subsetores de geração da
    mesma região na proporção do VBP, de forma que E_r não mude. Repete a desagregação (sem reequilíbrio) até
    os VBPs estabilizarem. Devolve a especificação com as participações finais e a tabela dos pisos."""
    from dataclasses import replace

    cfg = espec.piso_vbp
    kappa = float(cfg["kappa"])
    eta_v = cfg.get("viabilidade_eta")
    eta_v = None if eta_v is None else float(eta_v)
    max_iter = int(cfg.get("max_iter", 50))
    tol = float(cfg.get("tolerancia", 1e-12))
    comb_cfg = cfg["combustiveis"]
    p = espec.participacoes.copy()
    tipos = dict(zip(espec.subsetores["codigo"], espec.subsetores["tipo"].map(tipo_canonico)))
    inicial, linhas = {}, []
    for it in range(1, max_iter + 1):
        res = _desagregar_passo(mip, replace(espec, participacoes=p), reequilibrar=False)
        m2, mapa = res.mip, res.mapa
        mudou, linhas = False, []
        for r in espec.regioes:
            sel = mapa[(mapa["regiao"] == r) & mapa["desagregado"]]
            idx = [int(k) for k, c in zip(sel["indice_novo"], sel["codigo_novo"]) if tipos[c] == "geracao" and m2.X[k] > 0]
            cods = [mapa["codigo_novo"][k] for k in idx]
            g = m2.X[idx].astype(float)
            E = float(g.sum())
            if r not in inicial:
                inicial[r] = dict(zip(cods, g))
            fixos, comb = _custos_fixos_e_combustivel(espec, m2, mapa, idx)
            # φ: tudo o que o reequilíbrio não pode mexer, exceto o combustível (custos fixos, células ajustáveis
            # negativas e o resíduo contábil da coluna original), como fração do VBP — proporcional ao VBP nas regras
            phi = (g - _eob_maximo(espec, m2, mapa, idx) - comb) / g
            piso_k = np.where([c in comb_cfg for c in cods], comb / kappa, 0.0)
            piso_v = np.zeros(len(idx))
            if eta_v is not None:
                den = 1.0 - eta_v - phi
                for n, c in enumerate(cods):
                    if c in comb_cfg and comb[n] > 0:
                        if den[n] <= 0:
                            raise EspecificacaoInvalida(
                                f"piso_vbp em {r} {c}: custos fixos não combustíveis já passam 1 − η do VBP (φ = {phi[n]:.4f})")
                        piso_v[n] = comb[n] / den[n] * (1 + 1e-10)  # margem de arredondamento
            piso = np.maximum(piso_k, piso_v)
            novo = _redistribuir_com_piso(g, piso, E, f"região {r}")
            if np.abs(novo - g).max() > tol * max(1.0, E):
                mudou = True
            for n, c in enumerate(cods):
                lin = (p["regiao"] == r) & (p["subsetor"] == c)
                p.loc[lin, "participacao"] = novo[n]
                p.loc[lin, "fonte"] = (f"piso de VBP (D9-f, κ = {kappa}"
                                       + (f", viabilidade η = {eta_v}" if eta_v is not None else "")
                                       + f"): VBP final; peso inicial: {espec.participacoes.loc[lin, 'fonte'].iloc[0]}")
                linhas.append({"regiao": r, "subsetor": c, "combustivel": comb[n],
                               "VBP_inicial (pesos da especificação)": inicial[r][c], "VBP_antes_desta_iteracao": g[n],
                               "piso_kappa (combustível ÷ κ)": piso_k[n], "fixos_nao_combustivel / VBP (φ)": phi[n],
                               "piso_viabilidade (combustível ÷ (1 − η − φ))": piso_v[n], "piso": piso[n],
                               "VBP_final": novo[n], "piso_atingido": bool(piso[n] > 0 and novo[n] <= piso[n] * (1 + 1e-9)),
                               "piso_que_manda": ("viabilidade" if piso_v[n] > piso_k[n] else "kappa") if piso[n] > 0 else "",
                               "combustivel / VBP_final": comb[n] / novo[n] if novo[n] else np.nan,
                               "kappa": kappa, "viabilidade_eta": eta_v, "iteracoes": it})
        if not mudou:
            tab = pd.DataFrame(linhas)
            return replace(espec, participacoes=p), tab
    raise EspecificacaoInvalida(f"piso_vbp: não estabilizou em {max_iter} iterações")


def _reequilibrar_eob(espec: Especificacao, ga: _GrupoAlvo, Z2: np.ndarray, V2: np.ndarray, X2: np.ndarray,
                      linhas_aj: list[int], rotulos: list[str], ip: dict) -> tuple[InfoRAS, pd.DataFrame, pd.DataFrame]:
    """D9-r: RAS dos insumos não energéticos das colunas dos subsetores de uma região (altera Z2 e V2).

    Ajustáveis: compras a setores fora do bloco, exceto as linhas fixas (combustíveis); impostos sobre produtos.
    Fixos: bloco, combustíveis, importações (de energia), remunerações e impostos sobre a produção. Totais de
    linha = total de cada insumo na região (preservado). Alvo de coluna = ajustável_k − (EOB*_k − EOB_k), com
    EOB*_k = η × VBP_k para quem está abaixo e, para os demais, EOB_k menos uma parte do déficit, na proporção da
    folga (EOB_k − η × VBP_k). A soma dos EOB da região não muda.
    """
    cfg = espec.reequilibrio
    eta = float(cfg["eta"])
    itens = list(cfg.get("primarios_ajustaveis", ["ipi", "icms", "outros_impostos"]))
    limitar = cfg.get("se_inviavel", "erro") == "limitar"
    idx = ga.idx_novo
    X = X2[idx]
    prod = X > 0
    M = np.vstack([Z2[np.ix_(linhas_aj, idx)], V2[[ip[x] for x in itens]][:, idx]])
    rot = list(rotulos) + itens
    fix = (M < 0) | ~prod[None, :]
    livre_pos = np.where(fix, 0.0, M)
    eob = V2[ip["eob"], idx].copy()
    adj = M.sum(axis=0)
    minimo = eta * X
    escala = max(1.0, float(X.sum()))
    tol_eob = 1e-9 * escala
    alvo = eob.copy()
    situacao = np.array(["sem produção" if not p_ else "" for p_ in prod], dtype=object)
    abaixo = prod & (eob < minimo - tol_eob)
    max_eob = eob + livre_pos.sum(axis=0)  # EOB máximo: todos os ajustáveis livres a zero
    tol_viab = TOL_REAGREGACAO  # a mesma tolerância (absoluta) da checagem EOB_minimo_eta
    for k in np.flatnonzero(abaixo):
        if minimo[k] > max_eob[k] + tol_viab:
            msg = (f"reequilíbrio em {ga.regiao} {ga.codigos[k]}: mesmo com os insumos ajustáveis a zero, EOB = "
                   f"{max_eob[k]:.4f} < η × VBP = {minimo[k]:.4f} (custos fixos > (1 − η) × VBP)")
            if not limitar:
                raise EspecificacaoInvalida(msg)
            alvo[k] = max_eob[k]
            situacao[k] = "abaixo do mínimo: inviável, limitado (ajustáveis a zero)"
        else:
            alvo[k] = min(minimo[k], max_eob[k])
            situacao[k] = "abaixo do mínimo: elevado a η × VBP" + (
                " (ajustáveis a zero: o piso de viabilidade foi o que bastou)" if minimo[k] >= max_eob[k] - tol_viab else "")
    deficit = float((alvo - eob)[abaixo].sum())
    folga = np.where(prod & ~abaixo & (livre_pos.sum(axis=0) > 0), np.maximum(eob - minimo, 0.0), 0.0)
    if deficit > tol_eob:
        if folga.sum() < deficit - tol_eob:
            raise EspecificacaoInvalida(f"reequilíbrio em {ga.regiao}: déficit de EOB ({deficit:.4f}) maior que a folga "
                                        f"dos demais subsetores ({folga.sum():.4f})")
        cede = folga > 0
        alvo[cede] = eob[cede] - deficit * folga[cede] / folga.sum()
        for k in np.flatnonzero(cede):
            situacao[k] = "cede folga"
    for k in np.flatnonzero(prod & (situacao == "")):
        situacao[k] = "sem mudança"
    alvo_col = adj - (alvo - eob)
    alvo_lin = M.sum(axis=1)
    tol = max(espec.ras_tolerancia, 1e-14 * escala)
    M2, info = ras(M, alvo_lin, alvo_col, fix, tol=tol, max_iter=espec.ras_max_iter,
                   contexto=f"reequilibrio_EOB {ga.regiao} (η = {eta})")
    nz = len(linhas_aj)
    Z2[np.ix_(linhas_aj, idx)] = M2[:nz]
    for n, x in enumerate(itens):
        V2[ip[x], idx] = M2[nz + n]
    novo_adj = M2.sum(axis=0)
    eob_novo = eob + (adj - novo_adj)
    V2[ip["eob"], idx] = eob_novo
    V2[ip["va"], idx] += eob_novo - eob
    tab_sub = pd.DataFrame({
        "regiao": ga.regiao, "subsetor": ga.codigos, "VBP": X, "fixos": X - eob - adj,
        "ajustaveis_antes": adj, "ajustaveis_depois": novo_adj, "EOB_antes": eob, "EOB_depois": eob_novo,
        "EOB/VBP_antes": np.where(prod, eob / np.where(prod, X, 1.0), np.nan),
        "EOB/VBP_depois": np.where(prod, eob_novo / np.where(prod, X, 1.0), np.nan),
        "EOB_alvo": alvo, "situacao": situacao, "eta": eta,
        "RAS": f"{'convergiu' if info.convergiu else 'NÃO convergiu'} em {info.iteracoes} iterações (erro {info.erro_max:.2e})",
    })
    linhas = []
    for n, r_ in enumerate(rot):
        if not (np.abs(M[n]).sum() > 0 or np.abs(M2[n]).sum() > 0):
            continue
        d = {"regiao": ga.regiao, "insumo": r_, "total_preservado": float(M[n].sum()),
             "valor_movido (Σ|Δ| ÷ 2)": float(np.abs(M2[n] - M[n]).sum() / 2)}
        d.update({f"Δ {c}": float(v) for c, v in zip(ga.codigos, M2[n] - M[n])})
        linhas.append(d)
    return info, tab_sub, pd.DataFrame(linhas)


def _desagregar_passo(mip: MIP, espec: Especificacao, reequilibrar: bool = True) -> ResultadoDesagregacao:
    """Uma passada da desagregação (sem a verificação final)."""
    t = espec.setor_alvo
    regs = mip.lista_regioes
    subs = espec.subsetores
    K = len(subs)
    tipos_can = [tipo_canonico(x) for x in subs["tipo"]]
    idx_alvo = {r: mip.indice(r, t) for r in regs}
    s_ef, componentes_bloco = _participacoes_efetivas(espec, mip, idx_alvo)
    extras = {}
    if len(componentes_bloco):
        extras["componentes_bloco"] = componentes_bloco

    # ---- nova lista de setores e mapa ----------------------------------------------------------
    novos, grupos = [], {}
    for i, s in enumerate(mip.setores.itertuples(index=False)):
        if s.codigo == t and s.regiao in espec.regioes:
            ini = len(novos)
            for k, sub in enumerate(subs.itertuples(index=False)):
                novos.append((s.regiao, sub.codigo, sub.nome, i, s.codigo, s.nome, sub.tipo, s_ef[s.regiao][k], True))
            grupos[s.regiao] = _GrupoAlvo(
                s.regiao, i, list(range(ini, ini + K)), list(subs["codigo"]), tipos_can, s_ef[s.regiao], True
            )
        else:
            novos.append((s.regiao, s.codigo, s.nome, i, s.codigo, s.nome, "", 1.0, False))
            if s.codigo == t:
                grupos[s.regiao] = _GrupoAlvo(s.regiao, i, [len(novos) - 1], [s.codigo], ["agregado"], np.ones(1), False)
    mapa = pd.DataFrame(
        novos,
        columns=["regiao", "codigo_novo", "nome_novo", "indice_original", "codigo_original", "nome_original",
                 "tipo_subsetor", "participacao_vbp", "desagregado"],
    )
    mapa.insert(0, "indice_novo", np.arange(len(mapa)))
    mapa["id_original"] = mapa["regiao"] + "_" + mapa["codigo_original"]
    mapa["id_novo"] = mapa["regiao"] + "_" + mapa["codigo_novo"]
    n2 = len(mapa)
    setores2 = mapa[["regiao", "codigo_novo", "nome_novo"]].rename(columns={"codigo_novo": "codigo", "nome_novo": "nome"})

    fora = np.array([i for i in range(mip.n) if mip.setores["codigo"][i] != t])  # índices originais fora do bloco
    fora2 = mapa.set_index("indice_original").loc[fora, "indice_novo"].to_numpy()  # (únicos: não são alvo)

    reg_orig = mip.setores["regiao"].to_numpy()
    cod_orig = mip.setores["codigo"].to_numpy()
    pesos_reg = []  # registro de todos os pesos usados

    def registrar(dimensao, ga, chave, regra, fonte, w, etapa="regra"):
        if not ga.desagregado:
            return
        linha = {"dimensao": dimensao, "regiao": ga.regiao, "chave": chave, "regra": regra, "etapa": etapa, "fonte": fonte}
        linha.update({c: float(x) for c, x in zip(ga.codigos, w)})
        pesos_reg.append(linha)

    for r, ga in grupos.items():
        registrar("vbp", ga, "participacao_vbp", espec.modo_vbp,
                  "; ".join(dict.fromkeys(espec.participacoes.loc[espec.participacoes["regiao"] == r, "fonte"])), ga.s)

    # ---- Z, F, X -------------------------------------------------------------------------------
    Z2 = np.zeros((n2, n2))
    F2 = np.zeros((n2, len(COLUNAS_DF)))
    X2 = np.zeros(n2)
    T2 = np.zeros(n2)
    Z2[np.ix_(fora2, fora2)] = mip.Z[np.ix_(fora, fora)]
    F2[fora2] = mip.F[fora]
    X2[fora2] = mip.X[fora]
    T2[fora2] = mip.total_linha[fora]
    for ga in grupos.values():
        X2[ga.idx_novo] = ga.s * mip.X[ga.idx_orig]
        T2[ga.idx_novo] = ga.s * mip.total_linha[ga.idx_orig]

    # colunas (insumos de fornecedores fora do bloco)
    g_col = _agrupar(espec.regras_coluna, ["regiao", "fornecedor", "regiao_fornecedor"], "regras_coluna")
    tetos_reg = []
    for r, ga in grupos.items():
        j = ga.idx_orig
        X_sub = X2[ga.idx_novo]
        com_teto = {}  # (grupo do teto) → células [(i, i2, z, regra)]
        for i, i2 in zip(fora, fora2):
            def pont(ch, r=r, i=i):
                if not (_casa(ch["regiao"], r) and _casa(ch["fornecedor"], cod_orig[i]) and _casa(ch["regiao_fornecedor"], reg_orig[i])):
                    return None
                return (ch["regiao"] not in ("", CURINGA)) + 2 * (ch["fornecedor"] not in ("", CURINGA)) + (ch["regiao_fornecedor"] not in ("", CURINGA))
            desc = f"coluna {r} {t} ← {reg_orig[i]} {cod_orig[i]}"
            g = _escolher(g_col, pont, desc) if ga.desagregado else None
            z = mip.Z[i, j]
            if g is not None and g.regra == "fixa_com_teto":
                com_teto.setdefault(g.grupo_teto or cod_orig[i], []).append((i, i2, z, g))
                continue
            w, regra, fonte = _pesos(g, ga, desc)
            Z2[i2, ga.idx_novo] = w * z
            registrar("coluna", ga, f"{reg_orig[i]} {cod_orig[i]}", regra, fonte, w)
        # tetos sobre o total do insumo (todas as origens) ou do grupo de insumos
        for chave_teto, cels in com_teto.items():
            desc = f"coluna {r} {t} ← {chave_teto} (teto sobre o total)"
            alocs, atingidos = _alocar_grupo_com_teto([(z, g) for _, _, z, g in cels], ga, X_sub, desc)
            for (i, i2, z, g), aloc in zip(cels, alocs):
                Z2[i2, ga.idx_novo] = aloc
                registrar("coluna", ga, f"{reg_orig[i]} {cod_orig[i]}", g.regra, g.fonte, aloc / z if z else aloc * 0.0)
            for a in atingidos:
                tetos_reg.append({"regiao": r, "insumo_ou_grupo": chave_teto,
                                  "origens": ", ".join(f"{reg_orig[i]} {cod_orig[i]}" for i, _, _, _ in cels),
                                  "valor_total": sum(z for _, _, z, _ in cels), **a,
                                  "destino_excedente": "; ".join(sorted({g.destino for _, _, _, g in cels})),
                                  "fonte": "; ".join(sorted({g.fonte for _, _, _, g in cels if g.fonte}))})
    if tetos_reg:
        extras["tetos_atingidos"] = pd.DataFrame(tetos_reg)

    # bloco intrassetorial
    bloco_linhas = {r: np.zeros(len(ga.idx_novo)) for r, ga in grupos.items()}
    F_bloco = {r: float(sum(mip.Z[gv.idx_orig, gc.idx_orig] for gc in grupos.values())) for r, gv in grupos.items()}
    for r, gv in grupos.items():
        for r2, gc in grupos.items():
            B = mip.Z[gv.idx_orig, gc.idx_orig]
            if espec.bloco == "proporcional":
                wv, wc = gv.s, gc.s
                cel = np.outer(wv, wc) * B
            elif espec.bloco == "geracao_vende_para_rede":
                if gv.desagregado:
                    ger = np.array(gv.tipos) == "geracao"
                    sg = gv.s[ger].sum()
                    if sg <= 0 and B != 0:
                        raise EspecificacaoInvalida(f"geracao_vende_para_rede: {r} sem geração com VBP > 0, mas fluxo {r}→{r2} = {B}")
                    wv = np.where(ger, gv.s / sg, 0.0) if sg > 0 else np.zeros(len(gv.s))
                else:
                    wv = np.ones(1)
                if gc.desagregado:
                    wc = (np.array(gc.tipos) == "distribuicao").astype(float)
                    if gc.s[wc == 1].sum() <= 0 and B != 0:
                        raise EspecificacaoInvalida(f"geracao_vende_para_rede: distribuição de {r2} com VBP zero não pode comprar {B}")
                else:
                    wc = np.ones(1)
                cel = np.outer(wv, wc) * B
            else:  # roteamento_por_componentes
                cel = _celulas_roteamento(espec, gv, gc, B, F_bloco[r])
            # nenhuma célula do bloco em subsetor com produção zero
            if gv.desagregado and ((np.abs(cel).sum(axis=1) > 0) & (gv.s == 0)).any():
                raise EspecificacaoInvalida(f"bloco {r}→{r2}: venda de subsetor com produção zero")
            if gc.desagregado and ((np.abs(cel).sum(axis=0) > 0) & (gc.s == 0)).any():
                raise EspecificacaoInvalida(f"bloco {r}→{r2}: compra de subsetor com produção zero")
            Z2[np.ix_(gv.idx_novo, gc.idx_novo)] = cel
            bloco_linhas[r] += cel.sum(axis=1)
            if gv.desagregado:
                for k, cod in enumerate(gv.codigos):
                    if gv.s[k] > 0 or cel[k].any():
                        linha = {"dimensao": "bloco", "regiao": r, "chave": f"{r}→{r2}: vendedor {cod}",
                                 "regra": espec.bloco, "etapa": "regra", "fonte": "fração do fluxo original"}
                        linha.update({c: float(x) for c, x in zip(gc.codigos, cel[k] / B if B else cel[k] * 0)})
                        pesos_reg.append(linha)

    # linhas (vendas a compradores fora do bloco e à demanda final) + RAS
    g_lin = _agrupar(espec.regras_linha, ["regiao", "comprador", "regiao_comprador"], "regras_linha")
    infos = []
    reequilibrio_sub, reequilibrio_ins = [], []
    ndf = len(COLUNAS_DF)
    for r, ga in grupos.items():
        i = ga.idx_orig
        m = len(fora) + ndf
        alvo_col = np.concatenate([mip.Z[i, fora], mip.F[i]])
        M0 = np.zeros((len(ga.idx_novo), m))
        fix = np.zeros_like(M0, dtype=bool)
        chaves = []
        for jj in range(m):
            if jj < len(fora):
                j = fora[jj]
                cj, rj, tipo_df = cod_orig[j], reg_orig[j], None
                chave = f"{rj} {cj}"
            else:
                d = COLUNAS_DF.iloc[jj - len(fora)]
                cj, rj, tipo_df = d.codigo, d.regiao, d.tipo
                chave = d.codigo
            desc = f"linha {r} {t} → {chave}"

            def pont(ch, r=r, cj=cj, rj=rj, tipo_df=tipo_df):
                if not (_casa(ch["regiao"], r) and _casa(ch["regiao_comprador"], rj)):
                    return None
                pc = _pontua_comprador(ch["comprador"], cj, tipo_df)
                if pc is None:
                    return None
                return (ch["regiao"] not in ("", CURINGA)) + pc + (ch["regiao_comprador"] not in ("", CURINGA))
            g = _escolher(g_lin, pont, desc) if ga.desagregado else None
            w, regra, fonte = _pesos(g, ga, desc)
            M0[:, jj] = w * alvo_col[jj]
            fix[:, jj] = (alvo_col[jj] < 0) or (g is not None and g.fixar)
            chaves.append(chave)
            registrar("linha", ga, chave, regra, fonte, w)
        alvo_lin = X2[ga.idx_novo] - bloco_linhas[r]
        if ga.desagregado:
            # inviabilidade estrutural: linha sem células livres com total ≠ 0
            livres = np.where(fix, 0.0, M0).sum(axis=1)
            resid = alvo_lin - np.where(fix, M0, 0.0).sum(axis=1)
            tol_inv = max(espec.ras_tolerancia, 1e-9 * mip.X[i])
            for k in np.flatnonzero(resid < -tol_inv):
                raise EspecificacaoInvalida(
                    f"linha de {r} {ga.codigos[k]}: o VBP ({X2[ga.idx_novo[k]]:.4f}) é menor que as vendas já "
                    f"fixadas (bloco {bloco_linhas[r][k]:.4f} + células fixas); resta {resid[k]:.4f} < 0. "
                    "Ajuste as participações no VBP (ou use modo_vbp = ancora_bloco / ancora_componentes)."
                )
            for k in np.flatnonzero((livres <= 0) & (np.abs(resid) > tol_inv)):
                raise EspecificacaoInvalida(
                    f"linha de {r} {ga.codigos[k]}: o VBP ({X2[ga.idx_novo[k]]:.4f}) menos as vendas no bloco "
                    f"({bloco_linhas[r][k]:.4f}) deixa {resid[k]:.4f} a vender, mas as regras de linha não lhe permitem "
                    "vender a nenhum comprador fora do bloco. Ajuste as participações (ou use modo_vbp = ancora_bloco / ancora_componentes)."
                )
            tol = max(espec.ras_tolerancia, 1e-14 * mip.X[i])  # piso: precisão numérica das somas
            M, info = ras(M0, alvo_lin, alvo_col, fix, tol=tol, max_iter=espec.ras_max_iter, contexto=f"linhas {r} {t}")
            infos.append(info)
            if info.necessario:
                for jj, chave in enumerate(chaves):
                    if alvo_col[jj] != 0:
                        w_real = M[:, jj] / alvo_col[jj]
                        registrar("linha", ga, chave, "realizado_apos_RAS", "RAS", w_real, etapa="apos_RAS")
        else:
            M = M0
        Z2[np.ix_(ga.idx_novo, fora2)] = M[:, : len(fora)]
        F2[ga.idx_novo] = M[:, len(fora):]

    # ---- insumos primários e contas satélite -------------------------------------------------
    V2 = np.zeros((len(ITENS_PRIMARIOS), n2))
    S2 = np.zeros((len(ITENS_SATELITE), n2))
    V2[:, fora2] = mip.V[:, fora]
    S2[:, fora2] = mip.S[:, fora]
    g_pri = _agrupar(espec.regras_primarios, ["regiao", "item"], "regras_primarios")
    ip = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}
    isat = {it: k for k, it in enumerate(ITENS_SATELITE)}
    niveis_reg = []
    for r, ga in grupos.items():
        j = ga.idx_orig
        if not ga.desagregado:
            V2[:, ga.idx_novo[0]] = mip.V[:, j]
            S2[:, ga.idx_novo[0]] = mip.S[:, j]
            continue
        idx = ga.idx_novo
        X_sub = X2[idx]
        for item in ITENS_REPARTIVEIS:  # importações vêm antes dos impostos (proporcional_ci usa as importações)
            def pont(ch, r=r, item=item):
                if not (_casa(ch["regiao"], r) and _casa(ch["item"], item)):
                    return None
                return (ch["regiao"] not in ("", CURINGA)) + 2 * (ch["item"] not in ("", CURINGA))
            desc = f"{item} {r} {t}"
            g = _escolher(g_pri, pont, desc)
            total = mip.V[ip[item], j] if item in ip else mip.S[isat[item], j]
            if g is not None and g.regra == "niveis":
                vals, info_n = _repartir_niveis(espec, item, g, ga, total, X_sub, desc)
                niveis_reg.append(info_n)
                regra, fonte = f"niveis ({info_n['modo']})", g.fonte
                w = vals / total if total else vals * 0.0
            elif g is not None and g.regra == "proporcional_ci":
                base = Z2[:, idx].sum(axis=0) + V2[ip["importacoes"], idx]
                if base.sum() <= 0:
                    raise EspecificacaoInvalida(f"{desc}: proporcional_ci com compras intermediárias nulas")
                w = base / base.sum()
                vals = w * total
                regra, fonte = g.regra, g.fonte
            elif g is not None and g.regra == "fixa_por_tipo_sem_combustivel":
                comb = _combustivel_nas_colunas(espec, Z2, V2, mapa, idx, ip)
                w, regra, fonte = _pesos(g, ga, desc, base_tipo=X_sub - comb)
                vals = w * total
            else:
                w, regra, fonte = _pesos(g, ga, desc)
                vals = w * total
            if item in ip:
                V2[ip[item], idx] = vals
            else:
                S2[isat[item], idx] = vals
            registrar("primarios_satelite", ga, item, regra, fonte, w)
        # EOB = resíduo da coluna; o resíduo contábil original do setor é repartido pelo VBP

        def custos(Zc, Vc, cols):
            return (Zc[:, cols].sum(axis=0) + Vc[ip["importacoes"], cols]
                    + sum(Vc[ip[x], cols] for x in ITENS_IMPOSTOS_PRODUTOS)
                    + Vc[ip["remuneracoes"], cols] + Vc[ip["impostos_producao"], cols])

        rho = mip.V[ip["eob"], j] - (mip.X[j] - custos(mip.Z, mip.V, [j])[0])
        V2[ip["eob"], idx] = X2[idx] - custos(Z2, V2, idx) + ga.s * rho
        eps = mip.V[ip["va"], j] - (mip.V[ip["remuneracoes"], j] + mip.V[ip["eob"], j] + mip.V[ip["impostos_producao"], j])
        V2[ip["va"], idx] = V2[ip["remuneracoes"], idx] + V2[ip["eob"], idx] + V2[ip["impostos_producao"], idx] + ga.s * eps
        registrar("primarios_satelite", ga, "eob", "residuo", "fecha a coluna", V2[ip["eob"], idx] / mip.V[ip["eob"], j] if mip.V[ip["eob"], j] else V2[ip["eob"], idx] * 0)
        if reequilibrar and espec.reequilibrio:
            fixas_rq = set(espec.reequilibrio.get("linhas_fixas") or []) | {
                c for v in (espec.piso_vbp.get("combustiveis") or {}).values() for c in v if c != "importacoes"}
            aj = [(i2, f"{reg_orig[i]} {cod_orig[i]}") for i, i2 in zip(fora, fora2) if cod_orig[i] not in fixas_rq]
            antes_Z, antes_V = Z2[:, idx].copy(), V2[:, idx].copy()
            info_rq, tab_sub, tab_ins = _reequilibrar_eob(espec, ga, Z2, V2, X2, [a for a, _ in aj], [b for _, b in aj], ip)
            # o que o reequilíbrio não pode mexer (bloco, combustíveis, importações, remunerações, impostos sobre a
            # produção) tem de sair igual; a diferença máxima vai para a checagem reequilibrio_insumos_fixos
            itens_rq = list(espec.reequilibrio.get("primarios_ajustaveis", ["ipi", "icms", "outros_impostos"]))
            outras_lin = np.setdiff1d(np.arange(n2), [a for a, _ in aj])
            outros_it = [ip[x] for x in ITENS_PRIMARIOS if x not in itens_rq + ["eob", "va"]]
            tab_sub["delta_max_insumos_fixos"] = max(float(np.abs(Z2[outras_lin][:, idx] - antes_Z[outras_lin]).max()),
                                                     float(np.abs(V2[outros_it][:, idx] - antes_V[outros_it]).max()))
            # pesos realizados depois do reequilíbrio (os da etapa 'regra' são os de antes do RAS do D9-r)
            fonte_rq = f"RAS do reequilíbrio do EOB (D9-r, η = {espec.reequilibrio['eta']})"
            for i2, rot_ in aj:
                if antes_Z[i2].any() or Z2[i2, idx].any():
                    tot = Z2[i2, idx].sum()
                    registrar("coluna", ga, rot_, "realizado_apos_reequilibrio", fonte_rq,
                              Z2[i2, idx] / tot if tot else Z2[i2, idx] * 0.0, etapa="apos_reequilibrio")
            for x in itens_rq:
                tot = V2[ip[x], idx].sum()
                registrar("primarios_satelite", ga, x, "realizado_apos_reequilibrio", fonte_rq,
                          V2[ip[x], idx] / tot if tot else V2[ip[x], idx] * 0.0, etapa="apos_reequilibrio")
            registrar("primarios_satelite", ga, "eob", "realizado_apos_reequilibrio", fonte_rq,
                      V2[ip["eob"], idx] / mip.V[ip["eob"], j] if mip.V[ip["eob"], j] else V2[ip["eob"], idx] * 0,
                      etapa="apos_reequilibrio")
            infos.append(info_rq)
            reequilibrio_sub.append(tab_sub)
            reequilibrio_ins.append(tab_ins)
    if niveis_reg:
        extras["niveis"] = pd.DataFrame(niveis_reg)
    if reequilibrio_sub:
        extras["reequilibrio_RAS"] = pd.concat(reequilibrio_sub, ignore_index=True)
        extras["reequilibrio_insumos"] = pd.concat(reequilibrio_ins, ignore_index=True)

    # ---- coeficientes latentes ---------------------------------------------------------------
    partes = []
    if espec.coef_latentes is not None and len(espec.coef_latentes):
        partes.append(espec.coef_latentes.copy())
    if len(espec.latentes_espelho):
        partes.append(_latentes_por_espelho(espec, mip, grupos, setores2, Z2, X2, S2))
    coef_lat = pd.concat(partes, ignore_index=True) if partes else None
    if coef_lat is not None:
        ids2 = set(zip(setores2["regiao"], setores2["codigo"]))
        for rr in coef_lat.itertuples(index=False):
            if rr.tipo_linha == "setor" and (rr.regiao_linha, rr.codigo_linha) not in ids2:
                raise EspecificacaoInvalida(f"coef_latentes: linha {rr.regiao_linha} {rr.codigo_linha} não existe na MIP desagregada")
            if rr.tipo_linha == "satelite" and rr.codigo_linha not in ITENS_SATELITE:
                raise EspecificacaoInvalida(f"coef_latentes: item satélite {rr.codigo_linha} inválido")
        dup = coef_lat.duplicated(["regiao", "subsetor", "tipo_linha", "regiao_linha", "codigo_linha"])
        if dup.any():
            raise EspecificacaoInvalida(f"coef_latentes: linhas repetidas: {coef_lat[dup].to_dict('records')[:5]}")
        for (r, s) in coef_lat[["regiao", "subsetor"]].drop_duplicates().itertuples(index=False):
            k = list(grupos[r].codigos).index(s)
            if grupos[r].s[k] != 0:
                raise EspecificacaoInvalida(f"coef_latentes: {r} {s} tem produção-base não nula")

    mip2 = MIP(
        setores=setores2,
        Z=Z2,
        F=F2,
        total_linha=T2,
        X=X2,
        V=V2,
        V_df=mip.V_df.copy(),
        X_df=mip.X_df.copy(),
        S=S2,
        totais_ev=dict(mip.totais_ev),
        coef_latentes=coef_lat,
        titulo=mip.titulo,
    )
    pesos = pd.DataFrame(pesos_reg)
    info_ras = pd.DataFrame([vars(x) for x in infos])
    res = ResultadoDesagregacao(mip2, mip, espec, mapa, pesos, info_ras, extras=extras)
    return res


# =============================================================================================
# Verificação
# =============================================================================================
def insumos_nao_energeticos(res: ResultadoDesagregacao) -> pd.DataFrame:
    """T12 (Rodada 04): compras de cada subsetor com produção a setores fora do bloco, exceto as linhas de
    combustível (reequilibrio.linhas_fixas e piso_vbp.combustiveis), em valor e ÷ VBP."""
    e, m2, mapa = res.especificacao, res.mip, res.mapa
    cod = mapa["codigo_original"].to_numpy()
    comb = set(e.reequilibrio.get("linhas_fixas") or []) | {
        c for v in (e.piso_vbp.get("combustiveis") or {}).values() for c in v if c != "importacoes"}
    linhas = ~np.isin(cod, sorted(comb)) & (cod != e.setor_alvo)
    out = []
    for row in mapa[mapa["desagregado"]].itertuples(index=False):
        k = int(row.indice_novo)
        if m2.X[k] > 0:
            v = float(m2.Z[linhas, k].sum())
            out.append({"regiao": row.regiao, "subsetor": row.codigo_novo, "insumos_nao_energeticos": v,
                        "insumos_nao_energeticos / VBP": v / m2.X[k], "VBP": float(m2.X[k])})
    return pd.DataFrame(out, columns=["regiao", "subsetor", "insumos_nao_energeticos", "insumos_nao_energeticos / VBP", "VBP"])


def verificar(res: ResultadoDesagregacao) -> pd.DataFrame:
    """Checagens obrigatórias ao final da desagregação. Status: OK | ALERTA | FALHA."""
    m2, m1, mapa = res.mip, res.original, res.mapa
    linhas = []

    def add(nome, ok, valor, tol, detalhe="", alerta=False):
        status = "OK" if ok else ("ALERTA" if alerta else "FALHA")
        linhas.append((nome, status, valor, tol, detalhe))

    # itens satélite que, por especificação, não preservam o total da base (níveis sem resíduo, variante E3):
    # nesses casos o valor esperado do setor-alvo da região é a soma dos níveis (base − resíduo), e todo o
    # resto continua tendo de bater com a original
    niv = res.extras.get("niveis")
    nao_preserva = set(niv.loc[~niv["preserva_total"].astype(bool), "item"]) if niv is not None and len(niv) else set()
    S_esperado = m1.S.copy()
    if nao_preserva:
        for x in niv[~niv["preserva_total"].astype(bool)].itertuples():
            S_esperado[ITENS_SATELITE.index(x.item), m1.indice(x.regiao, res.especificacao.setor_alvo)] = x.identificado

    # 1) re-agregação
    ag = agregar(m2, mapa, m1.setores)
    for nome in ["Z", "F", "X", "total_linha", "V", "S", "V_df", "X_df"]:
        A, B = getattr(ag, nome), (S_esperado if nome == "S" else getattr(m1, nome))
        detalhe = "máx |Σ subsetores − original|"
        if nome == "S" and nao_preserva:
            detalhe += (f"; para {sorted(nao_preserva)} sem resíduo (E3), o esperado no setor-alvo é a soma dos níveis "
                        "(original − resíduo)")
        d = float(np.abs(A - B).max()) if np.size(A) else 0.0
        add(f"reagregacao_{nome}", d <= TOL_REAGREGACAO, d, TOL_REAGREGACAO, detalhe)
    d = max((abs(m2.totais_ev[k] - m1.totais_ev[k]) for k in m1.totais_ev), default=0.0)
    add("reagregacao_totais_EV", d <= TOL_REAGREGACAO, d, TOL_REAGREGACAO)

    sub = mapa.loc[mapa["desagregado"], "indice_novo"].to_numpy()
    orig_de = mapa["indice_original"].to_numpy()
    if len(sub) == 0:
        return pd.DataFrame(linhas, columns=["checagem", "status", "valor", "tolerancia", "detalhe"])
    s = mapa["participacao_vbp"].to_numpy()

    # 2) balanço de linha e de coluna de cada subsetor
    rl = m2.Z.sum(axis=1) + m2.F.sum(axis=1) - m2.X
    rl1 = m1.Z.sum(axis=1) + m1.F.sum(axis=1) - m1.X
    lim = TOL_REAGREGACAO + np.abs(s * rl1[orig_de])
    d = np.abs(rl[sub]) - lim[sub]
    add("balanco_linha_subsetores", (d <= 0).all(), float(np.abs(rl[sub]).max()), TOL_REAGREGACAO,
        "máx |Σ vendas − VBP| nos subsetores (tolerância + resíduo original × participação)")
    ip = {it: k for k, it in enumerate(ITENS_PRIMARIOS)}

    def res_col(m):
        return (m.Z.sum(axis=0) + m.V[ip["importacoes"]] + sum(m.V[ip[x]] for x in ITENS_IMPOSTOS_PRODUTOS)
                + m.V[ip["va"]] - m.X)

    rc, rc1 = res_col(m2), res_col(m1)
    d = np.abs(rc[sub] - s[sub] * rc1[orig_de[sub]])
    add("balanco_coluna_subsetores", (d <= TOL_REAGREGACAO).all(), float(d.max()), TOL_REAGREGACAO,
        "máx |resíduo da coluna − participação × resíduo original| (o resíduo original é repartido pelo VBP)")
    dva = np.abs(m2.V[ip["va"]] - m2.V[ip["remuneracoes"]] - m2.V[ip["eob"]] - m2.V[ip["impostos_producao"]])
    dva1 = np.abs(m1.V[ip["va"]] - m1.V[ip["remuneracoes"]] - m1.V[ip["eob"]] - m1.V[ip["impostos_producao"]])
    add("identidade_VA_subsetores", (dva[sub] <= TOL_REAGREGACAO + dva1[orig_de[sub]]).all(), float(dva[sub].max()),
        TOL_REAGREGACAO, "VA − (remunerações + EOB + impostos sobre a produção)")

    # 3) não negatividade (exceto onde a original já tem negativos)
    neg = []
    Zo = m1.Z[np.ix_(orig_de, orig_de)]
    for (a, b) in zip(*np.nonzero((m2.Z < -1e-12) & (Zo >= 0))):
        neg.append(f"Z[{m2.setores['id'][a]},{m2.setores['id'][b]}]")
    Fo = m1.F[orig_de]
    for (a, b) in zip(*np.nonzero((m2.F < -1e-12) & (Fo >= 0))):
        neg.append(f"F[{m2.setores['id'][a]},{COLUNAS_DF['codigo'][b]}]")
    for it in ITENS_PRIMARIOS:
        if it in ("eob", "va"):
            continue
        k = ip[it]
        for b in np.flatnonzero((m2.V[k] < -1e-12) & (m1.V[k, orig_de] >= 0)):
            neg.append(f"{it}[{m2.setores['id'][b]}]")
    for k, it in enumerate(ITENS_SATELITE):
        for b in np.flatnonzero((m2.S[k] < -1e-12) & (m1.S[k, orig_de] >= 0)):
            neg.append(f"{it}[{m2.setores['id'][b]}]")
    for b in np.flatnonzero(m2.X < 0):
        neg.append(f"VBP[{m2.setores['id'][b]}]")
    add("nao_negatividade", not neg, len(neg), 0,
        "negativos só onde a original já tem (coluna de discrepância, EOB, impostos sobre a produção); "
        + (", ".join(neg[:20]) if neg else "nenhum negativo novo"))

    # 4) totais das contas satélite preservados (por região e setor original)
    for k, it in enumerate(ITENS_SATELITE):
        dif = m2.S[k] @ _matriz_agregacao(mapa, m1.n, m2.n).T - m1.S[k]
        d = float(np.abs(dif).max())
        if it in nao_preserva:
            ok_niv = float(np.abs(m2.S[k] @ _matriz_agregacao(mapa, m1.n, m2.n).T - S_esperado[k]).max()) <= TOL_REAGREGACAO
            add(f"satelite_{it}_preservado", False, d, TOL_REAGREGACAO,
                f"NÃO PRESERVA O TOTAL DA BASE (níveis sem resíduo, E3): diferença total = {dif.sum():.4f}; "
                + ("a diferença é exatamente o resíduo" if ok_niv else "A DIFERENÇA NÃO É O RESÍDUO"), alerta=ok_niv)
        else:
            add(f"satelite_{it}_preservado", d <= TOL_REAGREGACAO, d, TOL_REAGREGACAO)
    if niv is not None and len(niv):
        neg_res = niv[niv["fator_reducao_identificados"] < 1]
        add("niveis_residuo_nao_negativo", not len(neg_res), len(neg_res), 0,
            "; ".join(f"{a.regiao} {a.item}: {a.observacao}" for a in neg_res.itertuples()) or
            "; ".join(f"{a.regiao} {a.item} ({a.modo}): identificado {a.identificado:.4f}, resíduo {a.residuo:.4f}"
                      for a in niv.itertuples()), alerta=True)

    # 5) EOB ≥ 0 em todos os subsetores com produção (sinalizado, não corrigido)
    eob = m2.V[ip["eob"]]
    neg_eob = [f"{m2.setores['id'][b]} ({eob[b]:.4f})" for b in sub if eob[b] < -1e-9]
    add("EOB_nao_negativo_subsetores", not neg_eob, float(eob[sub].min()), 0,
        "EOB negativo (sinalizado, NÃO corrigido): " + ", ".join(neg_eob) if neg_eob else "todos ≥ 0", alerta=True)

    # 6) subsetores com produção zero: linha e coluna zeradas
    zeros = [b for b in sub if m2.X[b] == 0]
    ruins = [m2.setores["id"][b] for b in zeros
             if m2.Z[b].any() or m2.Z[:, b].any() or m2.F[b].any() or m2.V[:, b].any() or m2.S[:, b].any()]
    add("subsetores_producao_zero_zerados", not ruins, len(zeros), 0,
        ("com valores: " + ", ".join(ruins)) if ruins else
        f"{len(zeros)} subsetor(es) com produção zero: " + ", ".join(m2.setores["id"][b] for b in zeros))

    # 7) L ≥ 0 e diagonal ≥ 1 (inclui colunas latentes)
    mod = ModeloLeontief(m2)
    add("L_nao_negativa", mod.L.min() >= -1e-10, float(mod.L.min()), -1e-10)
    add("L_diagonal_maior_igual_1", np.diag(mod.L).min() >= 1 - 1e-10, float(np.diag(mod.L).min()), 1.0)
    cs = mod.A.sum(axis=0)
    acima = [f"{m2.setores['id'][k]} ({cs[k]:.4f})" for k in np.flatnonzero(cs >= 1)]
    add("A_soma_colunas_menor_1", (cs < 1).all(), float(cs.max()), 1.0,
        "Σ coeficientes técnicos de cada coluna (inclui latentes)" + ("; ≥ 1 em: " + ", ".join(acima) if acima else ""),
        alerta=True)

    # 8) RAS
    if len(res.info_ras):
        ok = bool(res.info_ras["convergiu"].all())
        add("RAS_convergencia", ok, int(res.info_ras["iteracoes"].max()), res.especificacao.ras_max_iter,
            "; ".join(f"{r.contexto}: {'necessário' if r.necessario else 'não necessário'}, "
                      f"{'convergiu' if r.convergiu else 'NÃO convergiu'} em {r.iteracoes} iterações, "
                      f"erro {r.erro_max:.2e} (inicial {r.erro_inicial:.2e})" for r in res.info_ras.itertuples()))

    # 9) roteamento por componentes: energia, transmissão, fração da transmissão e vendas fora do bloco
    comp = res.extras.get("componentes_bloco")
    if comp is not None and len(comp) and res.especificacao.bloco == "roteamento_por_componentes":
        e = res.especificacao
        tipo = dict(zip(mapa["id_novo"], mapa["tipo_subsetor"].map(tipo_canonico)))
        ids = list(m2.setores["id"])
        alvo_todos = mapa.loc[mapa["codigo_original"] == e.setor_alvo, "indice_novo"].to_numpy()  # inclui agregados
        fora_bloco = np.setdiff1d(np.arange(m2.n), alvo_todos)
        regs_des = set(mapa.loc[mapa["desagregado"], "regiao"])
        erros_e, erros_t, erros_a, fora_abs = [], [], [], []
        for c in comp.to_dict("records"):
            r = c["regiao"]
            linhas_r = [k for k in sub if m2.setores["regiao"][k] == r]
            ger = [k for k in linhas_r if tipo[ids[k]] == "geracao"]
            tra = [k for k in linhas_r if tipo[ids[k]] == "transmissao"]
            dis_todas = [k for k in sub if tipo[ids[k]] == "distribuicao"]
            ger_todas = [k for k in sub if tipo[ids[k]] == "geracao"]
            E, T = c["E_r (energia = VBP da geração)"], c["T_r (transmissão)"]
            erros_e.append(abs(m2.Z[np.ix_(ger, alvo_todos)].sum() - E))
            erros_t.append(abs(m2.Z[np.ix_(tra, alvo_todos)].sum() - T))
            fora_abs.append(float(np.abs(m2.Z[np.ix_(ger + tra, fora_bloco)]).sum() + np.abs(m2.F[ger + tra]).sum()))
            if T > 0:
                i0 = m1.indice(r, e.setor_alvo)
                Fr = sum(m1.Z[i0, m1.indice(q, e.setor_alvo)] for q in m1.lista_regioes)
                frac_des = sum(m1.Z[i0, m1.indice(q, e.setor_alvo)] for q in regs_des) / Fr
                alfa = e.componente(r, "fracao_transmissao_distribuicao")
                erros_a.append(abs(m2.Z[np.ix_(tra, dis_todas)].sum() - alfa * T * frac_des) / T)
                erros_a.append(abs(m2.Z[np.ix_(tra, ger_todas)].sum() - (1 - alfa) * T * frac_des) / T)
        add("roteamento_vendas_geracao_igual_E", max(erros_e) <= TOL_REAGREGACAO, max(erros_e), TOL_REAGREGACAO,
            "Σ vendas da geração de r dentro do bloco = E_r = F_r − T_r − G_r")
        add("roteamento_vendas_transmissao_igual_T", max(erros_t) <= TOL_REAGREGACAO, max(erros_t), TOL_REAGREGACAO,
            "Σ vendas da transmissão de r dentro do bloco = T_r")
        add("roteamento_geracao_e_transmissao_nao_vendem_fora", max(fora_abs) <= TOL_REAGREGACAO, max(fora_abs),
            TOL_REAGREGACAO, "Σ |vendas| da geração e da transmissão fora do bloco e à demanda final (Seção 6.4)")
        add("roteamento_fracao_transmissao", max(erros_a, default=0.0) <= 1e-9, max(erros_a, default=0.0), 1e-9,
            "fração da transmissão paga pela distribuição e pela geração das regiões desagregadas "
            "(o S38 agregado de região não desagregada recebe a sua parte inteira)")
    if res.especificacao.bloco != "proporcional":
        grupos_idx = {}
        for k, row in mapa.iterrows():
            if row["codigo_original"] == res.especificacao.setor_alvo:
                grupos_idx.setdefault(row["regiao"], []).append(row["indice_novo"])
        dmax = 0.0
        for a, la in grupos_idx.items():
            for b, lb in grupos_idx.items():
                dmax = max(dmax, abs(m2.Z[np.ix_(la, lb)].sum() - m1.Z[m1.indice(a, res.especificacao.setor_alvo),
                                                                          m1.indice(b, res.especificacao.setor_alvo)]))
        add("bloco_fluxos_regionais_preservados", dmax <= TOL_REAGREGACAO, dmax, TOL_REAGREGACAO,
            "os fluxos alvo→alvo entre as regiões (ex.: RS→RS, RS→RB, RB→RS, RB→RB) são os da original")
    tet = res.extras.get("tetos_atingidos")
    if tet is not None:
        add("tetos_atingidos", True, len(tet), 0, "; ".join(
            f"{x.regiao} {x.insumo_ou_grupo}→{x.subsetor}: excedente {x.excedente:.4f}" for x in tet.itertuples()))

    # 10) latentes
    if m2.coef_latentes is not None and len(m2.coef_latentes):
        lat = m2.coef_latentes[["regiao", "subsetor"]].drop_duplicates()
        add("subsetores_latentes", True, len(lat), 0,
            "colunas de coeficientes guardadas à parte: " + ", ".join(f"{a}_{b}" for a, b in lat.itertuples(index=False)))

    # 11) Rodada 03: piso de VBP das térmicas (D9-f), EOB mínimo (D9-r, T9) e multiplicador de produção
    e = res.especificacao
    ids = list(m2.setores["id"])
    if e.piso_vbp:
        kappa = float(e.piso_vbp["kappa"])
        comb_cfg = e.piso_vbp.get("combustiveis") or {}
        idx_c = [int(k) for k in sub if mapa["codigo_novo"][k] in comb_cfg and m2.X[k] > 0]
        viol, det = [], []
        if idx_c:
            _, comb = _custos_fixos_e_combustivel(e, m2, mapa, idx_c)
            for k, c in zip(idx_c, comb):
                det.append(f"{ids[k]}: combustível/VBP = {c / m2.X[k]:.4f}")
                if m2.X[k] < c / kappa - TOL_REAGREGACAO:
                    viol.append(f"{ids[k]} (VBP {m2.X[k]:.4f} < {c / kappa:.4f})")
        add("piso_vbp_combustivel", not viol, len(viol), 0,
            f"VBP ≥ combustível ÷ κ (κ = {kappa}); " + ("; ".join(viol) if viol else "; ".join(det)))
    if e.reequilibrio and res.extras.get("reequilibrio_RAS") is not None:
        eta = float(e.reequilibrio["eta"])
        limitar = e.reequilibrio.get("se_inviavel", "erro") == "limitar"
        abaixo = [f"{ids[k]} (EOB/VBP {eob[k] / m2.X[k]:.6f}; falta {eta * m2.X[k] - eob[k]:.6g} R$ mi)"
                  for k in sub if m2.X[k] > 0 and eob[k] < eta * m2.X[k] - TOL_REAGREGACAO]
        add("EOB_minimo_eta", not abaixo, float(min((eob[k] / m2.X[k] for k in sub if m2.X[k] > 0), default=0.0)), eta,
            f"EOB ≥ η × VBP (η = {eta}; tolerância absoluta {TOL_REAGREGACAO} R$ mi) em todo subsetor com produção"
            + (": abaixo em " + ", ".join(abaixo) if abaixo else ""), alerta=limitar)
        dfix = float(res.extras["reequilibrio_RAS"]["delta_max_insumos_fixos"].max())
        add("reequilibrio_insumos_fixos", dfix <= TOL_REAGREGACAO, dfix, TOL_REAGREGACAO,
            "bloco, combustíveis, importações, remunerações e impostos sobre a produção iguais antes e depois do reequilíbrio")
        dmax, det = 0.0, []
        for r in sorted(set(mapa.loc[mapa["desagregado"], "regiao"])):
            ks = [k for k in sub if m2.setores["regiao"][k] == r]
            d = abs(eob[ks].sum() - m1.V[ip["eob"], m1.indice(r, e.setor_alvo)])
            dmax = max(dmax, d)
            det.append(f"{r}: Σ EOB = {eob[ks].sum():.4f}")
        add("reequilibrio_soma_EOB_regiao", dmax <= TOL_REAGREGACAO, dmax, TOL_REAGREGACAO,
            "Σ EOB dos subsetores de cada região = EOB original do setor-alvo; " + "; ".join(det))
    if e.alerta_insumos_nao_energeticos is not None:
        lim = float(e.alerta_insumos_nao_energeticos)
        tab_ne = insumos_nao_energeticos(res)
        baixo = tab_ne[tab_ne["insumos_nao_energeticos / VBP"] < lim - 1e-12]
        add("insumos_nao_energeticos_minimo", not len(baixo), float(tab_ne["insumos_nao_energeticos / VBP"].min()), lim,
            f"compras a setores fora do bloco, exceto combustíveis, ÷ VBP ≥ {lim} em todo subsetor com produção"
            + (": abaixo em " + ", ".join(f"{a}_{b} ({c:.4f})" for a, b, c in
                                          zip(baixo["regiao"], baixo["subsetor"], baixo["insumos_nao_energeticos / VBP"]))
               if len(baixo) else ""),
            alerta=True)
    if e.alerta_multiplicador is not None:
        mult = mod.L.sum(axis=0)
        cols = [int(k) for k in sub]
        altos = [f"{ids[k]} ({mult[k]:.3f})" for k in cols if mult[k] > e.alerta_multiplicador]
        add("multiplicador_producao_subsetores", not altos, float(max(mult[cols], default=0.0)), e.alerta_multiplicador,
            f"multiplicador de produção (Σ coluna de L, inclui latentes) ≤ {e.alerta_multiplicador}"
            + (": acima em " + ", ".join(altos) if altos else ""), alerta=True)
    return pd.DataFrame(linhas, columns=["checagem", "status", "valor", "tolerancia", "detalhe"])
