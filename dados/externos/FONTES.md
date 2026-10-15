# Registro de fontes externas

Regra do projeto: todo número externo precisa de fonte (instituição, tabela/arquivo, URL, data de acesso).
Se uma fonte não estiver acessível, isso é registrado aqui e ela **não** é substituída por estimativa própria.

## Dados usados em cálculos

| Rodada | Arquivo | Instituição | Tabela/arquivo | URL | Data de acesso | Uso |
|---|---|---|---|---|---|---|
| 02 | `dados/externos/brutos/ons/GERACAO_USINA-2_2019.parquet` (fora do git; 25049331 bytes; SHA-256 `4fee764a541f11c47abaa3add1a7797ddb79683d383475b7c5834acb9709bf2b`) | ONS — Operador Nacional do Sistema Elétrico | Dados abertos, "Geração por usina em base horária" (geracao_usina_2_ho), 2019 | https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/GERACAO_USINA-2_2019.parquet | 15/10/2026 | Geração 2019 por usina, região e subsetor (`dados/intermediarios/geracao_2019_*_v01.csv`). Ainda não entrou em parâmetro (Etapa 4 bloqueada) |
| 02 | `dados/externos/ons/reclassificacao_usinas_v01.csv` | Instruções da Rodada 02 (Francisco) + CEG do próprio ONS | Seção 5.1 | — | 15/10/2026 | Reclassificação de 7 usinas (Canoas → GN; CMPC, Klabin, Suzano → BIO; Do Atlântico, CSP, CST → CAR). As 5 do RB seguem a sugestão das instruções e ficam a confirmar no SIGA |

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

## Rodada 02 — teste de acesso (Etapa 1)

Teste feito em 15/10/2026 (UTC), a partir do mesmo ambiente de nuvem, depois do aviso do Francisco de que a rede
tinha sido liberada para `*.gov.br`, `*.ons.org.br` e `seeg.eco.br`. Registro por URL:
`dados/externos/rodada02_acesso_fontes.csv` (gerado por `scripts/rodada02_coleta.py`).

| Fonte (seção) | Domínio | Acessível? | Observação |
|---|---|---|---|
| ONS — geração por usina (5.1, obrigatória) | `ons-aws-prod-opendata.s3.amazonaws.com` | **sim** | baixado (25 MB, fora do git) |
| ANEEL SIGA (5.2) | `dadosabertos.aneel.gov.br` | não | 403 no proxy do ambiente |
| ANEEL leilões (5.4, obrigatória) | `dadosabertos.aneel.gov.br` | não | 403 |
| IBGE SIDRA — IPCA e CEMPRE (5.4 e 5.8, obrigatórias) | `apisidra.ibge.gov.br` (e `servicodados.ibge.gov.br`) | não | 403 |
| ANEEL — RAP (5.5, obrigatória) | `www.gov.br`, `www2.aneel.gov.br` | não | 403 |
| Sulgás, ANP, MME, EPE (5.3, 5.6) | `www.sulgas.rs.gov.br`, `sulgas.rs.gov.br`, `www.gov.br`, `www.epe.gov.br` | não | 403 |
| SEEG (5.7, obrigatória) | `seeg.eco.br` | não | 403 (com User-Agent de navegador) |
| Comex Stat (5.9) | `comexstat.mdic.gov.br`, `api-comexstat.mdic.gov.br` | não | 403 |
| ONS (portal) | `dados.ons.org.br`, `www.ons.org.br` | não | 403 |
| ABEGÁS | `www.abegas.org.br` | não | 403 |
| PyPI | `pypi.org` | sim | `pip install pyarrow` funcionou |

A liberação informada pelo Francisco não chegou ao container desta sessão: os mesmos domínios continuaram
recebendo 403 do proxy em todos os testes (início e fim da sessão). Nenhum número dessas fontes foi usado,
estimado ou substituído.
