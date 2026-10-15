# Registro de fontes externas

Regra do projeto: todo número externo precisa de fonte (instituição, tabela/arquivo, URL, data de acesso).
Se uma fonte não estiver acessível, isso é registrado aqui e ela **não** é substituída por estimativa própria.

## Dados usados em cálculos

| Rodada | Arquivo | Instituição | Tabela/arquivo | URL | Data de acesso | Uso |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | Nenhum dado externo foi usado em cálculos até a Rodada 01. |

A única base usada é a MIP original (`dados/original/`), recebida do Francisco: matriz inter-regional
setor × setor RS × Restante do Brasil, 2019, estimada pelo NEREUS/USP (método IIOAS), com contas
ambientais (CO₂e, água, energia) e ocupações. SHA-256 em `dados/original/CHECKSUM.txt`.

## Rodada 01 — teste de acesso (Etapa 6)

Teste feito em 15/10/2026 (UTC) por `scripts/rodada01_teste_fontes.py`, a partir do ambiente de nuvem
do Claude Code. Registro completo (URL exata, horário, erro): `dados/externos/rodada01_teste/acesso_fontes_rodada01.csv`.
**Nenhum dado destas fontes foi usado em cálculo.**

| Fonte | Endereço testado | Acessível? | Amostra baixada | Observação |
|---|---|---|---|---|
| ANEEL – Dados Abertos (SIGA) | https://dadosabertos.aneel.gov.br/api/3/action/package_search?q=siga&rows=1 | não | — | 403 no proxy do ambiente (política de rede) |
| ONS – Dados Abertos | https://dados.ons.org.br/api/3/action/package_list | não | — | 403 no proxy do ambiente (política de rede) |
| CCEE – Dados Abertos | https://dadosabertos.ccee.org.br/api/3/action/package_list | não | — | 403 no proxy do ambiente (política de rede) |
| EPE (Anuário; BEN) | https://www.epe.gov.br/ | não | — | 403 no proxy do ambiente (política de rede) |
| IBGE – API SIDRA | https://apisidra.ibge.gov.br/values/t/6579/n1/all/p/2019 | não | — | 403 no proxy do ambiente (política de rede) |
| SEEG | https://seeg.eco.br/ (e https://plataforma.seeg.eco.br) | não | — | 403 no proxy do ambiente (política de rede) |
| Base dos Dados (RAIS) | https://basedosdados.org/ | não | — | 403 no proxy do ambiente; nenhuma credencial criada |
| PyPI | https://pypi.org/simple/openpyxl/ | sim (200) | — (não é fonte de dados) | `pip install pytest` funcionou |

O bloqueio não é das instituições: é a política de rede do ambiente de nuvem, que só libera uma lista de
domínios. Para a Rodada 2, o Francisco precisa liberar esses domínios nas configurações do ambiente
(ver `respostas/RODADA_01_resposta.md`, "Pontos para o Francisco").
