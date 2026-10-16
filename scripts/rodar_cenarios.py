"""Executor de cenários: roda choques de demanda final em uma ou mais versões da MIP.

Uso (na raiz do repositório):
    python scripts/rodar_cenarios.py                                   # 9 cenários da Rodada 01 na original, v01 e v02
    python scripts/rodar_cenarios.py --cenarios meus_cenarios.csv \\
        --mip original --mip v02=resultados/rodada03/MIP_RS_RB_2019_S38_11sub_v02.xlsx \\
        --saida resultados/rodada03/cenarios_meus.xlsx

--cenarios: CSV com cenario, regiao, setor, valor_R$mi (R$ milhões na demanda final; ver parametros/cenarios_exemplo.csv).
--mip: 'original', um .xlsx exportado, um _longo.csv ou uma especificação .yaml; 'nome=caminho' dá o nome da versão.
       Repetível: com mais de uma versão sai também a aba 'sensibilidade' (diferença para a primeira versão).
--reparticao: como repartir um choque em setor agregado (ex.: S38) numa MIP desagregada: 'vendas_df' (padrão,
       ∝ vendas de cada subsetor à demanda final) ou pesos 'S38_DIS=0.9,S38_GAS=0.1'.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from mip.cenarios import executar_versoes, ler_cenarios  # noqa: E402
from mip.exportacao import salvar_tabelas  # noqa: E402

PADRAO_MIP = ["original", f"v01={RAIZ / 'resultados/rodada02/MIP_RS_RB_2019_S38_11sub_v01.xlsx'}",
              f"v02={RAIZ / 'resultados/rodada03/MIP_RS_RB_2019_S38_11sub_v02.xlsx'}"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cenarios", default=str(RAIZ / "parametros" / "cenarios_exemplo.csv"))
    ap.add_argument("--mip", action="append", help="versão da MIP (repetível)")
    ap.add_argument("--reparticao", default="vendas_df")
    ap.add_argument("--saida", default=str(RAIZ / "resultados" / "rodada03" / "cenarios_exemplo.xlsx"))
    a = ap.parse_args(argv)
    fontes = {}
    for m in a.mip or PADRAO_MIP:
        nome, _, cam = m.partition("=") if "=" in m else (Path(m).stem if m != "original" else "original", "", m)
        nome, cam = nome.strip(), cam.strip()
        if nome in fontes:
            ap.error(f"--mip: versão '{nome}' repetida (dê nomes diferentes: --mip nome=caminho)")
        fontes[nome] = cam
    rep = a.reparticao.strip()
    if "=" in rep:
        itens = [x.strip() for x in rep.split(",")]
        if any(not x or x.count("=") != 1 for x in itens):
            ap.error(f"--reparticao: use 'SUB=peso,SUB=peso' (recebido: {a.reparticao!r})")
        rep = {}
        for k, v in (x.split("=") for x in itens):
            k = k.strip()
            if k in rep:
                ap.error(f"--reparticao: subsetor {k} repetido")
            try:
                rep[k] = float(v)
            except ValueError:
                ap.error(f"--reparticao: peso inválido {v!r} para {k}")
    cen = ler_cenarios(a.cenarios)
    tab = executar_versoes(fontes, cen, rep)
    salvar_tabelas(Path(a.saida), tab, leiame=[
        "Executor de cenários (src/mip/cenarios.py): impactos de choques de demanda final.",
        f"Cenários: {a.cenarios}. Versões: " + "; ".join(f"{k} = {v}" for k, v in fontes.items()),
        "impactos: produção induzida (R$ mi), CO2e (t), IC (t CO2e por R$ mi de produção), produção por mil t de CO2e; "
        "top10: setores que mais emitem; regioes: RS × RB; diretas_indiretas; reparticao: como os choques em setores "
        "agregados foram repartidos entre os subsetores; sensibilidade: diferença de cada versão para a primeira.",
        "Choques em S38 numa MIP desagregada: repartidos " + ("∝ vendas de cada subsetor à demanda final" if rep == "vendas_df"
                                                             else f"pelos pesos {rep}") + "."])
    print(f"[cenários] {cen['cenario'].nunique()} cenários × {len(fontes)} versões → {a.saida}")


if __name__ == "__main__":
    main()
