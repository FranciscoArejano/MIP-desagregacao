"""Tratamento das fontes de dados externas (Rodada 02): reúne os leitores de `mip.externos`.

| Seção | Fonte | Módulo | Validado com o arquivo real? |
|---|---|---|---|
| 5.1 | ONS — geração por usina, 2019 | `mip.externos.ons` | sim (26/26 referências) |
| 5.2 | ANEEL SIGA — cadastro de usinas | `mip.externos.siga` | não (domínio bloqueado) |
| 5.4 | ANEEL leilões + IPCA (SIDRA 1737) | `mip.externos.leiloes` | não (domínios bloqueados) |
| 5.7 | SEEG 13.0 | `mip.externos.seeg` | não (domínio bloqueado) |
| 5.8 | IBGE CEMPRE (SIDRA 6450) | `mip.externos.cempre` | não (domínio bloqueado) |

Os leitores ainda não validados foram escritos contra o formato documentado nas instruções e testados
com dados sintéticos; ao rodar com os arquivos reais, confira as comparações com as referências.
"""
from __future__ import annotations

from .externos import cempre, leiloes, ons, seeg, siga  # noqa: F401

__all__ = ["ons", "siga", "leiloes", "seeg", "cempre"]
