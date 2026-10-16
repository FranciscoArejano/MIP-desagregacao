"""Executor de cenários (Rodada 03): choques de demanda final em qualquer versão da MIP.

Entrada: um CSV com as colunas `cenario, regiao, setor, valor_R$mi` (um choque por linha; R$ milhões na demanda
final do setor-região) e uma ou mais versões da MIP: a original, uma MIP exportada (.xlsx), uma especificação de
desagregação (.yaml, desagregada na hora) ou o CSV em formato longo (`_longo.csv`).

Choque num setor agregado que foi desagregado (ex.: `S38` numa MIP com `S38_DIS`, `S38_GAS`…): é repartido entre os
subsetores da região na proporção das vendas de cada subsetor à demanda final (`reparticao="vendas_df"`, padrão; a
mesma regra da prévia da Rodada 02b) ou por pesos explícitos ({subsetor: peso}).

Saídas (formato do artigo), por versão:
- impactos: produção induzida, CO2e, IC (t CO2e por R$ mi de produção) e produção por mil t de CO2e;
- top10: os 10 setores-região que mais emitem em cada cenário;
- regioes: repartição RS × RB (produção e CO2e);
- diretas_indiretas: emissões diretas (dos setores chocados) e indiretas;
- reparticao: como os choques em setores agregados foram repartidos;
e, com mais de uma versão, `sensibilidade`: os indicadores de cada cenário em cada versão.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .estrutura import MIP
from .leitura import ler_mip, ler_mip_longo, ler_mip_original
from .modelo import ModeloLeontief, ranking_setorial

COLUNAS = ["cenario", "regiao", "setor", "valor_R$mi"]
INDICADORES = ["dY_total", "dX_total", "dX_RS", "dX_RB", "co2e_total", "co2e_RS", "co2e_RB", "IC",
               "producao_por_mil_t", "pct_co2e_RS", "pct_co2e_RB", "co2e_diretas", "co2e_indiretas", "pct_indiretas",
               "ocupacoes", "agua", "energia"]


class CenarioInvalido(ValueError):
    pass


def ler_cenarios(caminho: str | Path) -> pd.DataFrame:
    df = pd.read_csv(caminho, comment="#", dtype={"cenario": str, "regiao": str, "setor": str})
    faltam = set(COLUNAS) - set(df.columns)
    if faltam:
        raise CenarioInvalido(f"{caminho}: colunas ausentes {sorted(faltam)} (esperadas: {COLUNAS})")
    df = df[COLUNAS].copy()
    df["valor_R$mi"] = pd.to_numeric(df["valor_R$mi"], errors="raise")
    for c in ("cenario", "regiao", "setor"):
        df[c] = df[c].str.strip()
    vazias = df[df[["cenario", "regiao", "setor"]].isna().any(axis=1) | (df[["cenario", "regiao", "setor"]] == "").any(axis=1)
                | df["valor_R$mi"].isna()]
    if len(vazias):
        raise CenarioInvalido(f"{caminho}: célula vazia em cenario, regiao, setor ou valor_R$mi nas linhas de dados "
                              f"{[int(i) + 1 for i in vazias.index]} (contadas sem o cabeçalho e os comentários)")
    return df


def cenarios_da_rodada01() -> pd.DataFrame:
    """Os 9 cenários de referência da Rodada 01 (choques no RS), no formato do executor."""
    from . import referencia as ref

    return pd.DataFrame([(c, "RS", s, v) for c, d in ref.CENARIOS_RS.items() for s, v in d.items()], columns=COLUNAS)


def carregar_mip(fonte: str | Path | MIP) -> MIP:
    """'original' | caminho .xlsx | caminho .yaml (especificação) | caminho _longo.csv | objeto MIP."""
    if isinstance(fonte, MIP):
        return fonte
    if str(fonte) == "original":
        return ler_mip_original()
    p = Path(fonte)
    if p.suffix.lower() in (".yaml", ".yml"):
        from .desagregacao import desagregar, ler_especificacao

        return desagregar(ler_mip_original(), ler_especificacao(p)).mip
    if p.suffix.lower() == ".xlsx":
        return ler_mip(p)
    if p.suffix.lower() == ".csv":
        return ler_mip_longo(p)
    raise CenarioInvalido(f"fonte de MIP não reconhecida: {fonte}")


def resolver_choques(mip: MIP, df: pd.DataFrame, reparticao: str | dict = "vendas_df") -> tuple[dict, pd.DataFrame]:
    """Converte as linhas de um cenário em {(regiao, codigo): valor}, repartindo setores agregados."""
    existentes = set(zip(mip.setores["regiao"], mip.setores["codigo"]))
    if isinstance(reparticao, dict):
        neg = {c: w for c, w in reparticao.items() if not float(w) >= 0}
        if neg:
            raise CenarioInvalido(f"repartição: pesos negativos ou inválidos {neg}")
    lat = set()
    if mip.coef_latentes is not None and len(mip.coef_latentes):
        lat = set(zip(mip.coef_latentes["regiao"], mip.coef_latentes["subsetor"]))

    def sem_base(r, c):  # produção zero e sem coluna latente: A e intensidade nulas, choque sem insumos nem emissões
        return mip.X[mip.indice(r, c)] <= 0 and (r, c) not in lat

    choques, reg = {}, []
    for cen, r, s, v in zip(df["cenario"], df["regiao"], df["setor"], df["valor_R$mi"].astype(float)):
        if (r, s) in existentes:
            if sem_base(r, s):
                raise CenarioInvalido(f"cenário {cen}: {r} {s} tem produção zero e não tem coluna latente "
                                      "(o choque sairia sem insumos e sem emissões)")
            choques[(r, s)] = choques.get((r, s), 0.0) + v
            continue
        subs = [c for (rr, c) in existentes if rr == r and c.startswith(f"{s}_")]
        if not subs:
            raise CenarioInvalido(f"cenário {cen}: setor {r} {s} não existe na MIP (nem como agregado)")
        subs = sorted(subs)
        if isinstance(reparticao, dict):
            # a mesma repartição serve a várias versões (na original o S38 nem é repartido); aqui, toda chave com o
            # prefixo do setor chocado tem de ser subsetor desta MIP (pega erro de digitação)
            desconhecidos = sorted(c for c in reparticao if c.startswith(f"{s}_") and c not in subs)
            if desconhecidos:
                raise CenarioInvalido(f"cenário {cen}: repartição de {r} {s} com subsetores inexistentes na MIP "
                                      f"{desconhecidos} (existentes: {subs})")
            pesos = np.array([float(reparticao.get(c, 0.0)) for c in subs])
            regra = "pesos informados"
        elif reparticao == "vendas_df":
            # vendas líquidas à demanda final (a discrepância pode ser negativa); negativo conta como zero
            pesos = np.array([max(float(mip.F[mip.indice(r, c)].sum()), 0.0) for c in subs])
            regra = "∝ vendas de cada subsetor à demanda final"
        else:
            raise CenarioInvalido(f"repartição desconhecida: {reparticao}")
        if pesos.sum() <= 0:
            raise CenarioInvalido(f"cenário {cen}: pesos nulos para repartir {r} {s}")
        pesos = pesos / pesos.sum()
        for c, w in zip(subs, pesos):
            if w > 0:
                if sem_base(r, c):
                    raise CenarioInvalido(f"cenário {cen}: a repartição de {r} {s} manda {w:.4f} para {r} {c}, que tem "
                                          "produção zero e não tem coluna latente")
                choques[(r, c)] = choques.get((r, c), 0.0) + v * w
                reg.append({"cenario": cen, "regiao": r, "setor_agregado": s, "subsetor": c, "peso": w,
                            "valor_R$mi": v * w, "regra": regra})
    total = float(df["valor_R$mi"].astype(float).sum())
    if abs(sum(choques.values()) - total) > 1e-9 * max(1.0, abs(total)):
        raise CenarioInvalido(f"repartição não preservou o choque: {sum(choques.values())} ≠ {total}")
    return choques, pd.DataFrame(reg)


def _resumo(res, modelo: ModeloLeontief) -> dict:
    r = res.resumo()
    co2, dx = r["co2e_total"], r["dX_total"]
    d = {"dY_total": float(res.dY.sum()), **{k: r.get(k, np.nan) for k in ("dX_total", "dX_RS", "dX_RB", "co2e_total",
                                                                              "co2e_RS", "co2e_RB", "IC")}}
    d["producao_por_mil_t"] = dx / (co2 / 1000) if co2 else np.nan
    d.update({k: r.get(k, np.nan) for k in ("pct_co2e_RS", "pct_co2e_RB", "co2e_diretas", "co2e_indiretas", "pct_indiretas")})
    for it in ("ocupacoes", "agua", "energia"):
        d[it] = float(res.outros[it].sum()) if it in res.outros else np.nan
    return d


def executar(mip: MIP, cenarios: pd.DataFrame, versao: str = "", reparticao: str | dict = "vendas_df",
             n_top: int = 10) -> dict[str, pd.DataFrame]:
    """Roda todos os cenários numa MIP e devolve as tabelas no formato do artigo."""
    modelo = ModeloLeontief(mip)
    imp, top, regs, di, rep = [], [], [], [], []
    for nome, g in cenarios.groupby("cenario", sort=False):
        choques, r_ = resolver_choques(mip, g, reparticao)
        if len(r_):
            rep.append(r_.assign(versao=versao))
        res = modelo.simular_choques(choques, nome)
        d = _resumo(res, modelo)
        imp.append({"versao": versao, "cenario": nome, **d})
        t = ranking_setorial(res, n_top)
        t.insert(0, "cenario", nome)
        t.insert(0, "versao", versao)
        top.append(t)
        reg_arr = mip.setores["regiao"].to_numpy()
        em = res.emissoes
        for r in sorted(set(reg_arr), key=lambda x: (x != "RS", x)):
            m = reg_arr == r
            regs.append({"versao": versao, "cenario": nome, "regiao": r, "dX": float(res.dX[m].sum()),
                         "pct_dX": 100 * float(res.dX[m].sum()) / d["dX_total"] if d["dX_total"] else np.nan,
                         "co2e": float(em[m].sum()),
                         "pct_co2e": 100 * float(em[m].sum()) / d["co2e_total"] if d["co2e_total"] else np.nan,
                         "IC": float(em[m].sum()) / float(res.dX[m].sum()) if res.dX[m].sum() else np.nan,
                         "co2e_diretas": float((res.e * res.dY)[m].sum())})
        di.append({"versao": versao, "cenario": nome, "co2e_total": d["co2e_total"], "co2e_diretas": d["co2e_diretas"],
                   "co2e_indiretas": d["co2e_indiretas"], "pct_diretas": 100 - d["pct_indiretas"],
                   "pct_indiretas": d["pct_indiretas"]})
    return {"impactos": pd.DataFrame(imp), "top10": pd.concat(top, ignore_index=True), "regioes": pd.DataFrame(regs),
            "diretas_indiretas": pd.DataFrame(di),
            "reparticao": pd.concat(rep, ignore_index=True) if rep else pd.DataFrame(
                columns=["cenario", "regiao", "setor_agregado", "subsetor", "peso", "valor_R$mi", "regra", "versao"])}


def sensibilidade(tabelas: dict[str, dict[str, pd.DataFrame]], base: str | None = None) -> pd.DataFrame:
    """Indicadores de cada cenário em cada versão (formato longo), com a diferença para a versão-base."""
    imp = pd.concat([t["impactos"] for t in tabelas.values()], ignore_index=True)
    longo = imp.melt(id_vars=["versao", "cenario"], value_vars=[c for c in INDICADORES if c in imp.columns],
                     var_name="indicador", value_name="valor")
    base = base or next(iter(tabelas))
    ref = longo[longo["versao"] == base].set_index(["cenario", "indicador"])["valor"]
    longo["valor_base"] = [ref.get((c, i), np.nan) for c, i in zip(longo["cenario"], longo["indicador"])]
    longo["diferenca"] = longo["valor"] - longo["valor_base"]
    longo["dif_%"] = np.where(longo["valor_base"].abs() > 0, 100 * longo["diferenca"] / longo["valor_base"].abs(), np.nan)
    longo.insert(0, "versao_base", base)
    return longo


def executar_versoes(fontes: dict[str, str | Path | MIP], cenarios: pd.DataFrame, reparticao: str | dict = "vendas_df",
                     base: str | None = None) -> dict[str, pd.DataFrame]:
    """Roda os cenários em várias versões e junta as tabelas (+ sensibilidade, se houver mais de uma versão)."""
    por_versao = {v: executar(carregar_mip(f), cenarios, v, reparticao) for v, f in fontes.items()}
    junto = {k: pd.concat([t[k] for t in por_versao.values()], ignore_index=True) for k in next(iter(por_versao.values()))}
    if len(por_versao) > 1:
        junto["sensibilidade"] = sensibilidade(por_versao, base)
    return junto
