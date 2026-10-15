"""Rodada 01 — regenera todas as saídas da rodada.

Uso (na raiz do repositório):
    python scripts/rodada01.py

Saídas:
- dados/intermediarios/mip_original_longo.csv              (Etapa 2)
- resultados/rodada01/validacao_mip_original_v01.csv        (Etapa 2)
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from mip.caminhos import PASTA_INTERMEDIARIOS, PASTA_RESULTADOS  # noqa: E402
from mip.leitura import formato_longo, ler_mip_original  # noqa: E402
from mip.validacao import validar_identidades  # noqa: E402

PASTA_SAIDA = PASTA_RESULTADOS / "rodada01"


def etapa2():
    """Leitura da MIP, formato longo e validação das identidades."""
    mip = ler_mip_original()
    PASTA_INTERMEDIARIOS.mkdir(parents=True, exist_ok=True)
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    formato_longo(mip).to_csv(PASTA_INTERMEDIARIOS / "mip_original_longo.csv", index=False)
    val = validar_identidades(mip)
    val.to_csv(PASTA_SAIDA / "validacao_mip_original_v01.csv", index=False)
    print("[Etapa 2] validação da MIP original:")
    for r in val.itertuples(index=False):
        print(f"  - {r.checagem}: obtido {r.obtido} (esperado {r.esperado})")
    return mip


def main():
    etapa2()


if __name__ == "__main__":
    main()
