"""Rodada 02 — tratamento dos dados coletados e saídas da rodada (sem rede).

Uso (na raiz do repositório):
    python scripts/rodada02_coleta.py   # 1) baixa as fontes (precisa de rede; registra o acesso)
    python scripts/rodada02.py          # 2) trata o que foi baixado e gera as saídas

Saídas (só das fontes disponíveis; as demais são registradas como pendentes):
- dados/intermediarios/geracao_2019_usina_v01.csv               (ONS, Seção 5.1)
- dados/intermediarios/geracao_2019_regiao_subsetor_v01.csv     (ONS, Seção 5.1)
- resultados/rodada02/comparacao_referencias_v01.csv            (esperado × obtido × diferença)
- resultados/rodada02/situacao_fontes_v01.csv                   (o que foi tratado e o que falta)
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import pandas as pd  # noqa: E402

from mip.caminhos import PASTA_EXTERNOS, PASTA_INTERMEDIARIOS, PASTA_RESULTADOS  # noqa: E402
from mip.externos import ons  # noqa: E402

PASTA_SAIDA = PASTA_RESULTADOS / "rodada02"
BRUTOS = PASTA_EXTERNOS / "brutos"

# fonte → nome do arquivo gravado por scripts/rodada02_coleta.py. O arquivo fica em
# dados/externos/brutos/<fonte>/ (> 20 MB, fora do git) ou em dados/externos/<fonte>/ (≤ 20 MB).
NOMES = {
    "ons": "GERACAO_USINA-2_2019.parquet",
    "siga": "siga-empreendimentos-geracao.csv",
    "leiloes": "resultado-leiloes-geracao.csv",
    "ipca": "ipca_1737.json",
    "seeg": "Dados-nacionais-13.0.xlsx",
    "cempre": "cempre_6450.json",
}


def localizar(fonte: str) -> Path:
    """Caminho do bruto da fonte: na pasta versionada ou em brutos/ (o que existir; senão, o versionado)."""
    for pasta in (PASTA_EXTERNOS / fonte, BRUTOS / fonte):
        if (pasta / NOMES[fonte]).exists():
            return pasta / NOMES[fonte]
    return PASTA_EXTERNOS / fonte / NOMES[fonte]


ARQUIVOS = {f: localizar(f) for f in NOMES}
OBRIGATORIAS = {"ons": "5.1", "leiloes": "5.4", "ipca": "5.4", "seeg": "5.7", "cempre": "5.8"}


def tratar_ons():
    """Seção 5.1: geração por usina e por região × subsetor; comparação com as referências."""
    df = ons.ler_ons(ARQUIVOS["ons"])
    reclass = ons.ler_reclassificacao(PASTA_EXTERNOS / "ons" / "reclassificacao_usinas_v01.csv")
    siga = None
    if ARQUIVOS["siga"].exists():
        from mip.externos import siga as siga_mod

        siga = siga_mod.classificar_siga(siga_mod.ler_siga(ARQUIVOS["siga"]))
    usinas = ons.geracao_por_usina(df, reclass, siga)
    PASTA_INTERMEDIARIOS.mkdir(parents=True, exist_ok=True)
    usinas.to_csv(PASTA_INTERMEDIARIOS / "geracao_2019_usina_v01.csv", index=False)
    tab = ons.geracao_por_regiao_subsetor(usinas)
    tab.to_csv(PASTA_INTERMEDIARIOS / "geracao_2019_regiao_subsetor_v01.csv", index=False)
    comp = ons.comparar_com_referencia(usinas)
    comp.insert(0, "fonte", "ONS (Seção 5.1)")
    print(f"[ONS] {len(usinas)} usinas; horas com valor nulo: {usinas.attrs['horas_com_valor_nulo']}; "
          f"{int(comp['confere'].sum())}/{len(comp)} referências conferem; "
          f"pendentes: {usinas.loc[usinas['subsetor'] == ons.PENDENTE, 'nom_usina'].tolist()}")
    return usinas, tab, comp


def situacao_fontes() -> pd.DataFrame:
    linhas = []
    for fonte, caminho in ARQUIVOS.items():
        linhas.append({
            "fonte": fonte,
            "secao": OBRIGATORIAS.get(fonte, "5.2" if fonte == "siga" else ""),
            "obrigatoria": fonte in OBRIGATORIAS,
            "arquivo_esperado": caminho.relative_to(RAIZ).as_posix(),
            "disponivel": caminho.exists(),
        })
    return pd.DataFrame(linhas)


def main():
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    sit = situacao_fontes()
    sit.to_csv(PASTA_SAIDA / "situacao_fontes_v01.csv", index=False)
    comparacoes = []
    if ARQUIVOS["ons"].exists():
        _, _, comp = tratar_ons()
        comparacoes.append(comp.rename(columns={"esperado_gwh": "esperado", "obtido_gwh": "obtido"}))
    faltam = sit[sit["obrigatoria"] & ~sit["disponivel"]]
    if len(faltam):
        print("[Rodada 02] fontes obrigatórias indisponíveis: " + ", ".join(faltam["fonte"])
              + " — parâmetros reais e MIP v01 não podem ser gerados (Etapa 1 das instruções).")
    if comparacoes:
        pd.concat(comparacoes, ignore_index=True).to_csv(PASTA_SAIDA / "comparacao_referencias_v01.csv", index=False)


if __name__ == "__main__":
    main()
