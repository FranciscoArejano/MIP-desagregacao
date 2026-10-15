# Rodada 02 — Relatório do Claude Code

Projeto: desagregação do S38 na MIP inter-regional RS × RB, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
Data: 15/10/2026 · Instruções: `instrucoes/RODADA_02_instrucoes_CODE.md` · Rodada anterior: `respostas/RODADA_01_resposta.md`
Convenção numérica: ponto decimal, sem separador de milhar.

Decisões aplicadas (mensagem de abertura + Seção 1): D1 = C (11 subsetores); D2, D3, D4 e D6 = A; D5 revisada = E1
principal, com E2 e E3 como sensibilidades; D7 = A (coluna do S38-RS mantida como na base).

## 1. Resumo

- **A liberação da rede não chegou a este container.** `*.gov.br`, `*.ons.org.br` e `seeg.eco.br` continuaram recebendo 403 do proxy em todos os testes, do início ao fim da sessão. Só o bucket S3 do ONS (`ons-aws-prod-opendata.s3.amazonaws.com`) e o PyPI responderam.
- Por isso, conforme a Etapa 1 das instruções, fiz a coleta possível (ONS), a Etapa 3 (motor) e **parei antes da Etapa 4**. As 4 fontes obrigatórias restantes (leilões+IPCA, RAP, SEEG e CEMPRE) estão bloqueadas.
- **ONS:** geração 2019 por usina e por região × subsetor; **26/26 valores de referência reproduzidos** (diferença máxima 0.15 GWh no total do RB). Só a usina "Sol" (ES, 839.2 GWh, "Resíduos Industriais") fica pendente, porque o SIGA não abre.
- **Motor:** 11 subsetores (156 setores-região), `roteamento_por_componentes`, `modo_vbp: ancora_componentes`, regras de coluna com teto, compradores por faixa/lista, impostos ∝ compras intermediárias, latentes por espelho e emissões E1/E2/E3. Os testes T6–T8 e os complementares passam; os 56 testes da Rodada 01 continuam passando.
- **Leitores das fontes bloqueadas** (SIGA, leilões+IPCA, SEEG, CEMPRE) e script de coleta estão prontos e testados com dados sintéticos, mas **não validados com os arquivos reais**.
- Conferência de ordem de grandeza, com os preços e a RAP de referência das instruções: RS fecha (âncora 4.10 bi × GWh·preço 4.06 bi); RB não fecha (72.4 × 93.9 bi). Explicação na Seção 16.
- **O que falta para concluir a rodada:** que a rede liberada chegue ao ambiente (provavelmente exige uma sessão nova). Daí em diante: coleta → parâmetros → MIP v01 + variantes → quadro.

## 2. Status por etapa

| Etapa | Status | Observação |
|---|---|---|
| E1 — Testar o acesso às fontes | concluída | Bloqueadas (403): `dadosabertos.aneel.gov.br`, `apisidra.ibge.gov.br`, `servicodados.ibge.gov.br`, `seeg.eco.br`, `www.gov.br`, `www2.aneel.gov.br`, `www.epe.gov.br`, `www.sulgas.rs.gov.br`, `sulgas.rs.gov.br`, `comexstat.mdic.gov.br`, `api-comexstat.mdic.gov.br`, `dados.ons.org.br`, `www.ons.org.br`, `www.abegas.org.br`. Acessíveis: S3 do ONS e PyPI |
| E2 — Coletar e tratar os dados de 2019 | parcial | 5.1 (ONS) concluída e conferida. 5.2–5.10 bloqueadas; leitores prontos (sem validação com o arquivo real) |
| E3 — Ajustes no motor | concluída | 6.1–6.9 implementados; T6, T7 e T8 passam. T2 "com a especificação real" depende da Etapa 4 |
| E4 — Parâmetros reais | não feita | Parada exigida pela Etapa 1 (fontes obrigatórias bloqueadas) |
| E5 — MIP desagregada v01 + variantes | não feita | Depende da E4 |
| E6 — Quadro-diagnóstico e prévia | não feita | Depende da E5 |
| E7 — Relatório | concluída | Este arquivo, `HISTORICO.md` e `README.md` |

<!-- SECOES_3_A_16 -->
