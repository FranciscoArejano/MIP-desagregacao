# Registro de fontes externas

Regra do projeto: todo número externo precisa de fonte (instituição, tabela/arquivo, URL, data de acesso).
Se uma fonte não estiver acessível, isso é registrado aqui e ela **não** é substituída por estimativa própria.

## Dados usados em cálculos

| Rodada | Arquivo | Instituição | Tabela/arquivo | URL | Data de acesso | Uso |
|---|---|---|---|---|---|---|
| 02 | `dados/externos/brutos/ons/GERACAO_USINA-2_2019.parquet` (fora do git; 25049331 bytes; SHA-256 `4fee764a541f11c47abaa3add1a7797ddb79683d383475b7c5834acb9709bf2b`) | ONS — Operador Nacional do Sistema Elétrico | Dados abertos, "Geração por usina em base horária" (geracao_usina_2_ho), 2019 | https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/GERACAO_USINA-2_2019.parquet | 15/10/2026 | Geração 2019 por usina, região e subsetor (`dados/intermediarios/geracao_2019_*_v01.csv` e `_v02.csv`); pesos da geração (P1, P2), energia, água e CEMPRE da geração (R02b) |
| 02 | `dados/externos/ons/reclassificacao_usinas_v01.csv` | Instruções da Rodada 02 (Francisco) + CEG do próprio ONS | Seção 5.1 | — | 15/10/2026 | R02: reclassificação de 7 usinas. **R02b (Seção 2):** Canoas → GN; as 7 usinas de resíduos industriais (Do Atlântico, CSP, CST, Sol, Klabin Celulose, Suzano Maranhão, CMPC) ficam **fora do S38** (`tratamento = excluir_autoproducao`; 9513.1 GWh) |
| 02b | `dados/externos/siga/siga-empreendimentos-geracao.csv` (SHA-256 `60de2b32…5a0540`) | ANEEL — Dados Abertos | SIGA, empreendimentos de geração | https://dadosabertos.aneel.gov.br/dataset/6d90b77c-c5f5-4d81-bdec-7bc619494bb9/resource/11ec447d-698d-4ab8-977f-b424d5deee6a/download/siga-empreendimentos-geracao.csv | 15/10/2026 19:27 UTC | Casamento ONS × SIGA (CEG); divergências de rótulo só reportadas (`siga_divergencias_ons_v01.csv`) |
| 02b | `dados/externos/leiloes/resultado-leiloes-geracao.csv` (SHA-256 `547345ef…ef6c747`) | ANEEL — Dados Abertos | Resultado dos leilões de geração | https://dadosabertos.aneel.gov.br/dataset/593537c6-9e0e-4ed9-817a-2c5d5de05147/resource/a1328fc1-f06b-437d-8893-57ac2c8103df/download/resultado-leiloes-geracao.csv | 15/10/2026 19:27 UTC | Preços P1 por fonte (corrigidos pelo IPCA) |
| 02b | `dados/externos/ipca/ipca_1737.json` (SHA-256 `f3b75095…c26b97`) | IBGE — SIDRA | Tabela 1737, número-índice do IPCA | https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all | 15/10/2026 19:27 UTC | Correção dos preços para a média de 2019 |
| 02b | `dados/externos/brutos/seeg/Dados-nacionais-13.0.xlsx` (fora do git, 185 MB; SHA-256 `21fc4965…aff350`); recorte versionado `seeg/seeg13_2019_recorte_geracao_sf6_v01.csv` | SEEG (Observatório do Clima) | Dados nacionais 13.0 | https://seeg.eco.br/wp-content/uploads/2025/12/Dados-nacionais-13.0.xlsx | 15/10/2026 19:27 UTC | Emissões 2019 da geração (serviço público) e SF6 → níveis E1/E2/E3 |
| 02b | `dados/externos/cempre/cempre_6450.json` (SHA-256 `21765f03…a98d0e`) | IBGE — SIDRA | Tabela 6450, CEMPRE 2019 | https://apisidra.ibge.gov.br/values/t/6450/n1/all/n3/43/v/707,662/p/2019/c12762/117297,117298,117299,117300,117301,117302,117303,117304,117305,117306 | 15/10/2026 19:28 UTC | Composição de ocupações e remunerações por subsetor |
| 02b | `dados/externos/epe/ben_2020/BEN2020_Matriz_ab2019.xlsx` e `BEN2020_sp.pdf`; transcrição `epe/ben2020_tabela_5_4_v01.csv` | EPE | Balanço Energético Nacional 2020 (ano-base 2019): matriz consolidada; Tabela 5.4 (p. 112) | ver `dados/externos/epe/DOWNLOAD.txt` | 15/10/2026 19:38 UTC | Sistemas isolados (PET-RB = 4769 GWh, Seção 3, opção 2); consumo específico das térmicas; gás por setor comprador; reconciliação (Seção 4) |
| 02b | `dados/externos/epe/anuario_2020/…Workbook.xlsx` | EPE | Anuário Estatístico de Energia Elétrica 2020 | ver `epe/DOWNLOAD.txt` | 15/10/2026 19:37 UTC | Procura da geração dos isolados por fonte (não há: só carga, consumo e emissões, Tabelas 2.6 e 2.13) |
| 02b | `dados/externos/aneel_rap/…` (ver `aneel_rap/DOWNLOAD.txt`) | ANEEL (atas da Diretoria em dados abertos; DOU; voto de 22/04/2021); ONS | RAP 2018-2019 (REH 2.408/2018, primária); RAP 2019-2020 (R$ 25.7 bi, **secundária**); RAP da CEEE-GT; REN 559/2013 (TUST 50/50); REH 2.509/2018 (Angra, R$ 247.47/MWh) | ver `aneel_rap/DOWNLOAD.txt` | 15/10/2026 19:30–19:50 UTC | VBP do TRA, fração da TUST, preço da nuclear |
| 02b | `dados/externos/gas/mme_boletim_dez2019/boletim_gn_dez2019.pdf`; `brutos/gas/cage_rs_2019/…v-5-2.pdf` (fora do git, 38 MB) | MME; Sulgás (DF publicadas pela CAGE/Sefaz-RS) | Boletim do gás nº 154; DF da Sulgás 2019 | ver `gas/DOWNLOAD.txt` | 15/10/2026 19:34–19:36 UTC | θ_RS, θ_RB; VBP do GAS-RS (R$ 898.71 mi) |
| 02b | `dados/externos/comex/api_2019_ncm/*.json` | MDIC — Comex Stat (API) | Importações 2019, NCM 2716.00.00, 2711.21.00, 2711.11.00, valor FOB | https://api-comexstat.mdic.gov.br/general | 15/10/2026 19:50 UTC | Repartição das importações do S38 (Seção 5.9) |
| 02b | `dados/externos/valores_documentais_v01.csv` | (várias) | Um número por linha, com documento, página, URL, arquivo local, SHA-256 e data | — | 15/10/2026 | Entrada de `scripts/rodada02_parametros.py` |

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

## Rodada 02b — teste de acesso (Seção 0) e fontes

Teste rápido feito em 15/10/2026, das 19:27:24 às 19:27:33 UTC, depois de o Francisco mudar a rede do ambiente para
**Full**: `dadosabertos.aneel.gov.br`, `apisidra.ibge.gov.br`, `seeg.eco.br`, `www.epe.gov.br`, `www.gov.br` e
`comexstat.mdic.gov.br` responderam **200** (registro: `dados/externos/rodada02b_teste_rede.csv`). Todas as fontes
obrigatórias foram baixadas (`dados/externos/rodada02_acesso_fontes.csv`).

Não acessados nesta rodada (sem contornar):
- `www2.aneel.gov.br/cedoc` (biblioteca da ANEEL: anexo da REH 2.565/2019 e notas técnicas) e `www.canalenergia.com.br`:
  desafio anti-robô (Cloudflare, 403). Por isso a RAP total do ciclo 2019-2020 (R$ 25.7 bilhões) segue com a fonte
  **secundária** indicada nas instruções.
- `www.sulgas.rs.gov.br`: certificado TLS vencido. As demonstrações da Sulgás vieram da cópia oficial publicada pela
  CAGE/Sefaz-RS (Prestação de Contas do Governador 2019).
- Receita agregada das demais distribuidoras de gás: não existe fonte oficial (ANP, MME e ABEGÁS não publicam). Na v01
  valeu o fallback das instruções (margem de 0.25 como hipótese); na v02 a D9-b o substitui (preço médio × volume).

## Rodada 03 — fontes novas ou com uso novo

Nenhum download novo de rede; todos os números abaixo vêm de arquivos já baixados na 02b (URL, data e SHA-256 em
`dados/externos/valores_documentais_v02.csv` e nos `DOWNLOAD.txt` de cada pasta). Conferidos no documento nesta rodada.

| Uso (Rodada 03) | Fonte | Localização | Arquivo |
|---|---|---|---|
| D8: geração por fonte do Brasil (serviço público) | EPE, BEN 2020, Tabela 5.4 | PDF p. 112 (transcrição em `epe/ben2020_tabela_5_4_v01.csv`) | `epe/ben_2020/BEN2020_sp.pdf` |
| D9-b: volume não térmico do RB = (40.482 − 2.214) × 365 milhões m³ | MME, Boletim do gás nº 154 (dez/2019) | p. 16, "TOTAL DISTRIBUIDORAS SEM O SEGMENTO TERMELÉTRICO" e "Sulgás (RS)", média 2019 | `gas/mme_boletim_dez2019/boletim_gn_dez2019.pdf` |
| D9-b: preço médio do gás (4 distribuidoras) | DFP 2019 na CVM: Comgás (seq. 90958; Relatório da Administração p. 14 e nota 5 p. 27), CEG (seq. 91986; nota 22 p. 99), Gasmig (seq. 92390; nota 19 p. 93); Sulgás (Nota 18, p. 86 da cópia da CAGE) | receita líquida de venda de gás e volume, sem térmico, construção e serviços | `brutos/gas/cvm_rad_*` e `brutos/gas/cage_rs_2019/` (fora do git; SHA-256 na tabela de valores) |
| D10: gás por comprador no RS | Sulgás, Demonstrações Contábeis 2019, Nota 18 (receita líquida por segmento) | PDF p. 86 | `gas/sulgas_segmentos_2019_v01.csv` (transcrição, com fonte por linha) |
| Energia do satélite: consumo específico com o mapeamento da D8 (PET com "outras não renováveis") | EPE, BEN 2020, Tabela 5.4 | PDF p. 112 | `epe/ben2020_tabela_5_4_v01.csv` → `dados/intermediarios/ben_2019_consumo_especifico_v02.csv` |
| Evidência para o teto do gás por comprador (não entra na MIP): gás natural e eletricidade por setor | EPE, BEN 2020, Matriz ab2019.xlsx | aba Consolidada, colunas GÁS NATURAL e ELETRICIDADE | `epe/ben_2020/BEN2020_Matriz_ab2019.xlsx` → `dados/intermediarios/ben_2019_gas_eletricidade_por_setor_v01.csv` |
| Idem: tarifa média industrial 2019 (479.16 R$/MWh) | EPE, Anuário Estatístico de Energia Elétrica 2020, Tabela 2.15 (fonte: ANEEL, SAD; mercado cativo) | aba Tabela 2.15, linha Industrial, coluna 2019 | `epe/anuario_2020/…Workbook.xlsx` (linha `tarifa_media_industrial_2019` em `valores_documentais_v02.csv`) |

Observações: o preço da Gasmig sem o térmico é **aproximação** (a companhia não divulga deduções por segmento; foram
rateadas na proporção da receita bruta). Os volumes por segmento da CEG e da Gasmig são marcados "não auditados" nas DFP.
A extração foi feita e conferida por agentes verificadores independentes (dois por empresa; um dos verificadores da
Gasmig não terminou por limite de sessão), e os valores usados foram reconferidos nas tabelas citadas.

## Rodada 04 — fontes novas

| Uso (Rodada 04) | Fonte | Localização | Arquivo |
|---|---|---|---|
| V3 (`_rap_ons`): encargos de uso da transmissão faturados em jul–dez/2018 (10576544162.01) | ONS, Síntese da Apuração Mensal dos Serviços e Encargos (SEAMSE), dez/2018 | p. 8, seção 4, "Total Encargos de Uso", coluna "Total Ciclo 18/19" | `aneel_rap/ons_seamse_201812/SEAMSE_201812.pdf` |
| V3: ciclo 2018-2019 inteiro (21367058292.17) | ONS, SEAMSE jun/2019 | p. 8, seção 4, idem | `aneel_rap/ons_seamse_201906/SEAMSE_201906.pdf` |
| V3: jul–dez/2019 (12145090044.99) | ONS, SEAMSE dez/2019 (o mesmo arquivo da 02b) | p. 7, seção 4 | `aneel_rap/ons_seamse_201912/SEAMSE_201912.pdf` |
| Confirmação da REH 2.565/2019 (sem o total da RAP) | ANEEL, REH 2.565/2019, texto integral (enviado pelo Francisco) | 3 p. | `aneel_rap/reh_2565_2019_texto/reh20192565ti.pdf` |
| V1: MWh no SIN = mín(GWh da D8; GWh do ONS sem autoprodução e sem Itaipu) | ONS 2019 por usina (02b) e D8 (Rodada 03) | — | `dados/intermediarios/geracao_2019_usina_v02.csv`, `geracao_2019_regiao_subsetor_v03.csv` |

Ano civil 2019 = (21367.06 − 10576.54) + 12145.09 = 22935.6 R$ mi (`valores_documentais_v03.csv`). Os encargos do
SEAMSE não incluem PIS/Pasep e Cofins e incluem a parcela do orçamento do ONS. O total da RAP 2019-2020 continua o da
fonte secundária (25700): o texto da REH não o traz, e o Anexo na biblioteca da ANEEL respondeu 403 (desafio
anti-robô, não contornado) em 16/10/2026.
