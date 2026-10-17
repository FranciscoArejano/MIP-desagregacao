# Rodada 04 — Relatório do Claude Code

Projeto: desagregação do S38 na MIP inter-regional RS × RB, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
Data: 16–17/10/2026 · Instruções: `instrucoes/RODADA_04_instrucoes_CODE.md` · Rodada anterior: `respostas/RODADA_03_resposta.md`
Convenção numérica: ponto decimal, sem separador de milhar.

Decisões aplicadas: as anteriores (D1 = C; D2, D3, D4 e D6 = A; D5 = E1; D7 = A; D8 = A; D9 = (a) + (b) + (f) + (r); D10 = Sulgás) e as da Seção 1 das instruções:
- **V1:** TUST da geração pelo MWh gerado no SIN; remunerações e ocupações da geração por (VBP − combustível);
- **V2:** VBP do GAS-RB pelo preço da Sulgás;
- **V3:** RAP de 24883.4 na principal e variante `_rap_ons`;
- **D11 a D16:** R4a oficial; renováveis → EOL; fósseis → CAR e GN pelo VBP; E1 pela regra do executor; bloco B por R$ 1 bi e por TWh; investimento fora.

## 1. Resumo

- **MIP v03 pronta, sem a extensão de viabilidade.** Com a V1, o piso κ = 0.70 e o reequilíbrio η = 0.10 fecham sozinhos: o T9 passa nas 8 especificações (principal e 7 variantes). A extensão da v02 ficou desligada em todas.
- **Insumos não energéticos das térmicas no piso (T12):**

  | Subsetor | v02 | v03 |
  |---|---|---|
  | GN-RB | 0 | 0.027 do VBP |
  | PET-RB | 0 | 0.078 |
  | GN-RS | 0 | 0.020 |

  GN-RB e GN-RS ficam abaixo de 0.05: é um **ALERTA explicado** (Seção 10, ponto 1). Com κ = 0.60 (variante `_k060`), o mínimo vai a 0.077 e o ALERTA some.
- **Térmicas mais baratas:**

  | Subsetor | v02 (R$/MWh) | v03 (R$/MWh) |
  |---|---|---|
  | GN-RB | 264.5 | 231.6 |
  | PET-RB | 897.7 | 786.0 |
  | GN-RS | 314.6 | 280.5 |

  O combustível é 70% do VBP nas três, que é o piso κ exato das instruções. As renováveis do RB ganham VBP: HID-RB 119.7 → 124.3 R$/MWh.
- **V2:** VBP do GAS-RB = 19421.0 (era 26990.1). Nenhum comprador do RB encosta no teto de 0.90 do gás; no RS continuam os 6 da v02, porque o VBP do GAS-RS não muda.
- **V3:** o texto da REH 2.565/2019 que você enviou tem só 3 páginas e **não traz o total da RAP**, que fica nos Anexos. A principal continua com o valor secundário. A variante `_rap_ons` usa os encargos de uso faturados pelo ONS em 2019, **22935.6 R$ mi**: os três números conferem nos PDFs do SEAMSE. São 1947.8 R$ mi a menos que a principal (−7.8%). As bases podem diferir: o SEAMSE diz que não inclui PIS/Pasep e Cofins, e não sei se o total secundário de 25700 os inclui (Seção 13).
- **Simulações:** A0 reproduz o artigo (9/9 cenários e o top-10 do R1). Os resultados de A1, A2 e B estão em `resultados/rodada04/simulacoes_v03.xlsx`, as figuras de rascunho em `resultados/rodada04/figuras/`, e os 5 achados principais na Seção 18.
- **Testes:** 389 passaram, 0 falharam (`python -m pytest`), incluindo 2 novos da revisão.

## 2. Status por etapa

| Item | Status | Observação |
|---|---|---|
| Git: trabalhar a partir da `main` | concluído | Partiu de `cf8e3b0` (Rodada 03); commits na `main` |
| V1 — TUST e remunerações das térmicas | concluído | Extensão de viabilidade desligada (T9 passa sem ela); T12 com ALERTA em GN-RB e GN-RS |
| V2 — GAS-RB pela Sulgás | concluído | 19421.0; 4 distribuidoras na variante `_gas4dist` |
| V3 — RAP | concluído, com limitação | REH sem o total → principal com 24883.4; `_rap_ons` = 22935.6 (SEAMSE conferido) |
| Variantes da v03 | concluído | `_P2`, `_E2`, `_E3`, `_gas4dist`, `_rap_ons`, `_k060`, `_eta005` (CSV longo + latentes) |
| Quadro v03 | concluído | `quadro_subsetores_v03.xlsx`, com `v02_x_v03`, `passos_v02_v03`, `insumos_nao_energeticos`, `tust_geracao` e checagens |
| Bloco A0 | concluído | Reproduz o artigo |
| Blocos A1 e A2 (com sensibilidades) | concluído | D11–D14 |
| Bloco B (R$ 1 bi e 1 TWh) | concluído | Tabela por TWh com "evitadas" |
| Robustez | concluído | 8 versões (principal + 7 variantes) |
| Tabelas do artigo e figuras | concluído, com ressalva | Ordem e rótulos das Tabelas 1–4 inferidos (Seção 10, ponto 2) |
| Revisão adversarial | concluído, com limitação | 9 achados, todos conferidos por mim (os verificadores pararam no limite de uso); 8 corrigidos e 1 mantido com ressalva (Seção 7) |
| Relatório, HISTORICO, README | concluído | Este arquivo |

## 3. Arquivos criados, movidos ou alterados

| Caminho | Tipo | O que é |
|---|---|---|
| `instrucoes/RODADA_04_instrucoes_CODE.md` | texto | Cópia das instruções |
| `src/mip/desagregacao.py` | código (alterado) | `pesos_tust_geracao` (TUST da geração por pesos próprios no roteamento); regra `fixa_por_tipo_sem_combustivel` (dentro do tipo, ∝ VBP − combustível); `_combustivel_nas_colunas`; `insumos_nao_energeticos` e a checagem `insumos_nao_energeticos_minimo` (T12; opção `alerta_insumos_nao_energeticos` no YAML); validações; correção do piso de viabilidade (revisão) |
| `src/mip/cenarios.py` | código (alterado) | Tabela `participacao_setor`: participação do S38 (ou dos subsetores `S38_*`) nas emissões de cada cenário |
| `scripts/rodada04_parametros.py` | script | Parâmetros v03 a partir dos v02 (V1, V2, V3); decide a extensão de viabilidade rodando o T9 sem ela |
| `scripts/rodada04_mip.py` | script | MIP v03, variantes, checagens e quadro com o comparativo v02 × v03 e os passos V1, V2, V3; marca a hipótese da TUST nas colunas latentes |
| `scripts/rodada04_simulacoes.py` | script | Cenários (A0, A1, A2, sensibilidades, B), robustez, tabelas do artigo, figuras e a hipótese alternativa do SOL-RS latente |
| `parametros/*_v03*` | parâmetros | `especificacao_v03.yaml` e 7 variantes; `pesos_tust_geracao_v03.csv` (novo); `componentes`, `regras_linha` e `regras_primarios` (com `_gas4dist` e `_rap_ons`); `quadro_parametros_v03.xlsx` |
| `parametros/cenarios_v03.csv` | parâmetros | Os 52 cenários desta rodada no formato do executor |
| `dados/externos/valores_documentais_v03.csv` | dado | As linhas da v02 + os três totais do SEAMSE e o ano civil de 2019 |
| `dados/externos/aneel_rap/ons_seamse_201812/`, `ons_seamse_201906/` | dado | PDFs do ONS (SEAMSE dez/2018 e jun/2019) |
| `dados/externos/aneel_rap/reh_2565_2019_texto/reh20192565ti.pdf` | dado | O texto da REH 2.565/2019 enviado por você |
| `dados/externos/aneel_rap/DOWNLOAD.txt`, `dados/externos/FONTES.md` | documentação (alterado) | Registro das fontes da Rodada 04 |
| `resultados/rodada04/` | resultados | MIP v03 (.xlsx + longo + latentes), 7 variantes (longo + latentes), `checagens_v03.csv`, `quadro_subsetores_v03.xlsx`, `simulacoes_v03.xlsx`, `figuras/` (3 PNG) |
| `tests/test_rodada04.py` | teste | T2 v03, T9 sem extensão, T12, V1, V2, V3, validações, simulações |
| `requirements.txt` | alterado | + matplotlib (figuras) |
| `parametros/LEIAME_parametros.md`, `README.md`, `respostas/HISTORICO.md` | documentação | Formato novo, status e histórico |

Nada foi sobrescrito: v01, v02 e as saídas das rodadas anteriores ficaram como estavam.

## 4. Validação da MIP original

Sem mudança: T1 (SHA-256 da planilha original) e as identidades da Rodada 01 passam.

## 5. Reprodução dos resultados

O bloco A0 roda os 9 cenários do artigo (com R4a e R4b) na MIP original pelo executor e reproduz a Rodada 01 dentro das tolerâncias: 0.01 R$ mi, 1 t e 0.005 nos índices (teste `test_a0_reproduz_o_artigo`, além do T11). A participação do S38 nas emissões também confere com a da Rodada 01 (E1 92.2%, R1 57.1%, F1 39.4%).

## 6. Diagnóstico do S38 (v03)

Quadro por subsetor da v03 (P1 + E1 + D9 + V1 + V2). As colunas completas estão em `quadro_subsetores_v03.xlsx`.

| Região | Subsetor | VBP (R$ mi) | GWh | R$/MWh | t CO₂e/MWh E1 | EOB/VBP | CI/VBP | Mult. produção | Mult. emissões (t/R$ mi) |
|---|---|---|---|---|---|---|---|---|---|
| RS | HID | 2478.3 | 14542.6 | 170.4 | 0 | 0.490 | 0.381 | 1.580 | 26.8 |
| RS | EOL | 933.9 | 5266.9 | 177.3 | 0 | 0.499 | 0.374 | 1.570 | 26.7 |
| RS | SOL (latente) | 0 | 0 | — | — | — | — | 1.436 | 23.6 |
| RS | BIO | 14.4 | 68.2 | 211.0 | 0.000 | 0.507 | 0.368 | 1.592 | 41.4 |
| RS | CAR | 675.0 | 2625.2 | 257.1 | 1.435 | 0.544 | 0.335 | 1.533 | 5608.1 |
| RS | GN | 49.0 | 174.6 | 280.5 | 0.436 | 0.100 | 0.854 | **2.400** | 1635.9 |
| RS | PET (latente) | 0 | 0 | — | — | — | — | **2.760** | 1186.7 |
| RS | NUC (zerado) | 0 | 0 | — | — | — | — | — | — |
| RS | TRA | 1509.1 | — | — | — | 0.701 | 0.182 | 1.322 | 24.0 |
| RS | DIS | 14384.3 | — | — | — | 0.245 | 0.550 | 1.897 | 387.7 |
| RS | GAS | 898.7 | — | — | — | 0.100 | 0.792 | **2.344** | 213.9 |
| RB | HID | 45236.8 | 363907.4 | 124.3 | 0 | 0.445 | 0.356 | 1.535 | 26.5 |
| RB | EOL | 6555.5 | 50687.1 | 129.3 | 0 | 0.463 | 0.340 | 1.515 | 26.2 |
| RB | SOL | 969.0 | 4978.0 | 194.7 | 0 | 0.535 | 0.277 | 1.434 | 25.0 |
| RB | BIO | 272.7 | 1771.8 | 153.9 | 0.007 | 0.465 | 0.341 | 1.539 | 83.7 |
| RB | CAR | 2100.3 | 11197.8 | 187.6 | 0.867 | 0.412 | 0.398 | 1.654 | 4662.7 |
| RB | GN | 10981.9 | 47422.4 | 231.6 | 0.433 | 0.100 | 0.527 | 1.853 | 1915.7 |
| RB | PET | 4066.6 | 5174.0 | 786.0 | 0.829 | 0.100 | 0.789 | **2.759** | 1184.0 |
| RB | NUC | 2981.2 | 16129.0 | 184.8 | 0 | 0.512 | 0.297 | 1.460 | 25.4 |
| RB | TRA | 23374.4 | — | — | — | 0.672 | 0.177 | 1.307 | 24.6 |
| RB | DIS | 208427.9 | — | — | — | 0.273 | 0.564 | 1.922 | 422.6 |
| RB | GAS | 19421.0 | — | — | — | 0.171 | 0.456 | 1.775 | 269.8 |

Fatores E1 dentro das faixas da Rodada 03 (CAR 0.8–1.6; GN 0.35–0.65; PET 0.65–1.1; BIO ≤ 0.1). Nenhum comprador do S38 fica sem eletricidade. A D10 continua perto da Nota 18: no RS, a indústria fica com 77.2% das vendas do GAS e as famílias com 20.0%.

## 7. Motor de desagregação

**O que mudou** (`src/mip/desagregacao.py`; formato em `parametros/LEIAME_parametros.md`):

| Item | Implementação |
|---|---|
| V1, TUST da geração | Arquivo opcional `pesos_tust_geracao` (regiao, subsetor, valor, fonte). No roteamento por componentes, a parte (1 − α) da transmissão que vai à geração de cada região compradora é repartida por esses pesos (MWh no SIN), e não pelo VBP. Peso para subsetor sem produção dá erro |
| V1, remunerações e ocupações | Regra `fixa_por_tipo_sem_combustivel`: igual à `fixa_por_tipo`, mas dentro do tipo a parcela é repartida ∝ (VBP − combustível), com o combustível de `piso_vbp.combustiveis` (linhas de todas as origens e as importações do GN) |
| T12 | `insumos_nao_energeticos(res)`: compras de cada subsetor com produção a setores fora do bloco, exceto as linhas de combustível, em valor e ÷ VBP. A checagem `insumos_nao_energeticos_minimo` dá ALERTA abaixo de `alerta_insumos_nao_energeticos` (0.05 na v03) |
| Executor | Tabela `participacao_setor`: emissões induzidas no S38 (original) ou em cada `S38_*` (v03), por região e no total |
| Piso de VBP (revisão, #2) | `_resolver_pisos` redistribui a partir do VBP inicial em cada iteração, para que o VBP possa descer quando o piso de viabilidade baixa |
| Validação (revisão, #3) | `pesos_tust_geracao` exige uma linha para cada região e subsetor de geração (0 explícito) e o bloco `roteamento_por_componentes` |

**Revisão adversarial.** Rodei 4 revisores independentes (motor, parâmetros v03, simulações e resultados), com um verificador cético por achado. Os verificadores e o revisor de resultados pararam no limite semanal de uso dos agentes. Por isso **reproduzi e conferi cada achado eu mesmo**, com scripts próprios, antes de corrigir. Os números dos resultados (Seções 6, 16, 17 e 18) conferi contra as planilhas geradas.

| # | Achado | Gravidade | Conferência | Correção |
|---|---|---|---|---|
| 1 | O SOL-RS latente paga a TUST por real do SOL-RB (20.8 R$/MWh), e não os 35.2 R$/MWh das fontes do RS; isso põe o SOL abaixo da EOL por TWh | média | reproduzido (coeficiente 0.1067; 4939.4 t/TWh com a TUST do RS) | Marcado como **HIPÓTESE** (Seções 9, 10 e 18.2 e fonte do `coef_latentes`); alternativa calculada na aba `B_TWh` |
| 2 | Piso de viabilidade com "catraca": como φ cai quando o VBP sobe (V1), o piso baixa na iteração seguinte, mas o VBP não desce até ele. Com η = 0.20, GN-RS e GN-RB paravam acima do piso | média (não afeta a v03, com a extensão desligada) | reproduzido (`piso_atingido` = False nos dois) | `_resolver_pisos` redistribui sempre a partir do VBP inicial. Teste novo com η = 0.20. v02 e v03 iguais às publicadas (diferença ≤ 5e-11 R$ mi, arredondamento) |
| 3 | Sem a linha de um subsetor em `pesos_tust_geracao`, ele ficava sem TUST, sem erro nem alerta | média | reproduzido (NUC-RB com TUST 0) | Validação: uma linha por região e subsetor de geração (0 explícito) e bloco `roteamento_por_componentes`. Teste novo |
| 4 | "Os encargos do SEAMSE não incluem PIS/Pasep e Cofins" | baixa | refutado em parte: a nota está na tabela do SEAMSE | Mantido, com a ressalva de que a base da RAP secundária não foi verificada (Seção 13 e `FONTES.md`) |
| 5 | "Variantes de método mudam menos de 3%" valia para o CO₂e, não para a IC (GN por TWh na `_k060`: −10.8%) | baixa | reproduzido | Texto da Seção 18.3 corrigido |
| 6 | A fonte do GAS-RB em `componentes_v03.csv` dizia "D9-b (variante)", e a da `_gas4dist` terminava em "nan" | baixa | reproduzido | Fontes reescritas ("V2: principal" e "V2: sensibilidade") |
| 7 | Na Fig. 2, a borda branca das barras escondia as diretas pequenas (A2 R1) | baixa | reproduzido | Borda de 0.5 nas 3 figuras; figuras refeitas |
| 8 | Achado 4 da Seção 18.4 dava a faixa errada ("de 10.5% a 4.4%") | baixa | reproduzido (R2: −3.7%) | Corrigido: de 3.7% (R2) a 10.5% (E1) |
| 9 | O LEIAME de `simulacoes_v03.xlsx` dizia que todo o B por TWh usa o R$/MWh da v03 | baixa | reproduzido | Texto corrigido (cada variante usa o próprio R$/MWh) |

**Testes** (389 passaram, 0 falharam):

| Teste | Resultado | O que verifica |
|---|---|---|
| T1–T11 e os da Rodada 03 | passaram | Como antes |
| T2 v03 | passou (8 especificações) | Re-agregação exata, inclusive CO₂e na E1 e na E2; extensão desligada em todas |
| T9 v03 | passou | EOB ≥ 0.10 × VBP sem a extensão; Σ EOB por região = original; pisos pelo κ (combustível = 0.70 do VBP) |
| **T12** | passou (com ALERTA explicado) | Insumos não energéticos ÷ VBP ≥ 0.05, exceto GN-RS (0.020) e GN-RB (0.027), com ALERTA; κ = 0.60 dá OK |
| V1 | passou | TUST da geração exatamente ∝ MWh no SIN em cada região; remunerações e ocupações ∝ VBP − combustível |
| V2 e V3 | passaram | GAS-RB = 19421.05, sem comprador do RB no teto; SEAMSE e ano civil; transmissão da `_rap_ons` |
| Simulações | passaram | A0 = artigo; choques de R$ 1000 mi; D11–D14; B por TWh = R$/MWh; A1_E1 = A2_E1; fator direto do carvão por TWh = fator E1 |
| Revisão | passaram (2 novos) | Piso de viabilidade atingido com η = 0.20; erro sem a linha de um subsetor em `pesos_tust_geracao` |

## 8. Acesso a fontes externas

| Fonte | Acessível? | O que foi baixado | Observação |
|---|---|---|---|
| ONS, SEAMSE dez/2018 e jun/2019 | sim | 2 PDFs (`ons_seamse_201812/`, `ons_seamse_201906/`) | "Total Encargos de Uso", seção 4, p. 8 |
| ONS, SEAMSE dez/2019 | sim | já estava (02b); baixado de novo, SHA-256 igual | p. 7 |
| ANEEL, Anexo da REH 2.565/2019 (biblioteca) | não | — | 403 (desafio anti-robô); não contornado |
| ANEEL, dados abertos (busca "receita anual permitida") | sim | — | Não há conjunto com a RAP por ciclo |
| REH 2.565/2019, texto integral | enviado por você | `reh_2565_2019_texto/reh20192565ti.pdf` | 3 p.; sem o total da RAP |

## 9. Decisões tomadas por mim nesta rodada

| Decisão | Alternativas consideradas | Por quê |
|---|---|---|
| A v03 parte dos parâmetros v02 publicados (regras de linha e coluna, participações, componentes) e muda só V1, V2 e V3 | Refazer tudo a partir das fontes | É a definição de "v02 com três ajustes"; cada CSV v03 diz de onde veio |
| Extensão de viabilidade decidida pelo próprio script: roda o T9 sem ela em cada especificação | Decidir à mão | Seção 2.1, item 3. Resultado: desligada nas 8 |
| MWh no SIN = mín(D8; ONS sem autoprodução e sem Itaipu); RS pelo ONS; latentes e zerados com peso 0 | — | Seção 2.1; os 8 valores do RB conferem com a referência |
| Combustível na regra das remunerações = as linhas de `piso_vbp.combustiveis` (S04, S05 + gás importado, S19, S03 + S09) | Só o S38 interno | É o mesmo "combustível" do piso κ |
| T12: insumos não energéticos = compras a setores fora do bloco, exceto as linhas de combustível (sem impostos) | Incluir IPI/ICMS | São insumos; impostos não |
| SF6 entre TRA e DIS refeito em cada variante (depende do VBP da DIS, que muda com o GAS-RB e a transmissão) | Copiar o da v02 | Mesma regra da v02 com o VBP de cada variante |
| A2 fóssil: proporção CAR × GN pelo VBP da v03 principal (CAR 93.2%, GN 6.8%), a mesma em todas as variantes | Recalcular em cada variante | O vetor do choque fica igual na robustez; só a MIP muda |
| A2 e A1 do E1: S38 agregado no CSV; a repartição DIS × GAS é feita pelo executor em cada MIP | Fixar os valores | D14 ("a regra do executor") |
| B por TWh nas variantes: 1 TWh ao R$/MWh de cada variante | R$/MWh da principal | O choque físico (1 TWh) é o mesmo; o valor segue a MIP |
| B por TWh sem a DIS | Usar um R$/MWh médio da rede | A instrução lista as tecnologias; a DIS não tem GWh próprio na v03 |
| Tabelas 1–4 do artigo: 1 = impactos totais; 2 = top-10 da cesta R1; 3 = RS × RB; 4 = diretas × indiretas; rótulos da Rodada 01 | — | Não recebi o artigo; é a ordem das tabelas do executor (Rodada 03). **Confira** (Seção 10, ponto 2) |
| Fig. 3 em dois painéis com escalas lineares próprias | Escala log | Barras em escala log distorcem o comprimento; fósseis e renováveis diferem em duas ordens de grandeza |
| **HIPÓTESE:** SOL-RS e PET-RS latentes com a TUST por real do espelho do RB | Reescalar as linhas S38_TRA da coluna latente para a TUST por MWh do RS | O espelho (D6 = A) copia a coluna inteira. A alternativa está calculada para o SOL (aba `B_TWh`) e escrita na fonte do `coef_latentes` (Seção 10, ponto 7) |

## 10. Pontos para o Francisco

1. **T12 em GN-RB (0.027) e GN-RS (0.020).**
   - Com κ = 0.70, o combustível já leva 70% do VBP do GN; a TUST (10.0% e 12.5% do VBP), as remunerações (4.2% e 2.0%), os impostos sobre a produção e o EOB de 10% deixam de 2% a 3% para os outros insumos.
   - Opções: (a) aceitar o ALERTA; (b) κ = 0.60, que dá mínimo de 0.077 (variante `_k060`: GN-RB 12812.3, 270.2 R$/MWh).
2. **Formato das Tabelas 1–4 do artigo.** Montei pela ordem das tabelas do executor (impactos, top-10, RS × RB, diretas × indiretas) e com os rótulos da Rodada 01. Se o artigo tiver outra ordem ou outros rótulos, mande a lista e eu ajusto (é só a montagem; os números já estão nas abas A2).
3. **A2 fóssil.** Com D13 (CAR e GN do RS ∝ VBP), o carvão leva 93.2% do S38 das cestas fósseis, e as emissões da F1 sobem 5.8 vezes em relação ao artigo (Seção 18). As sensibilidades 100% CAR e 100% GN estão na aba `A2_sens`; diga qual entra no texto.
4. **RAP 2019-2020.** Para trocar o valor secundário, é preciso o **Anexo** da REH 2.565/2019 (Anexos I, IV, V e VIII, com as receitas por concessionária), e não o texto. A biblioteca da ANEEL bloqueia o download automático. Se você baixar o Anexo pelo navegador e subir, eu somo e troco. O efeito esperado é pequeno: a variante `_rap_ons` (−7.8% na transmissão) muda o CO₂e e a IC de todos os cenários da robustez em menos de 3% (Seção 18.3).
5. **Multiplicador de produção acima de 2.2:** GN-RS 2.400, GAS-RS 2.344, PET-RB 2.759 e PET-RS latente 2.760. Ficou um pouco maior que na v02, porque as térmicas voltaram a comprar insumos. Segue como ALERTA.
6. **Limitação do bloco B:** HID, EOL e SOL têm a mesma estrutura de insumos não energéticos (não há dado de custo por tecnologia). As diferenças entre elas vêm do VBP e, no SOL-RS, da coluna latente.
7. **HIPÓTESE: TUST do SOL-RS latente.** A coluna latente copia o SOL-RB e, com ela, a TUST por real do RB. Ao R$/MWh do SOL-RB, isso dá 20.8 R$/MWh, contra 35.2 R$/MWh que todas as fontes do RS no SIN pagam pela V1.
   - Com a TUST do RS, o SOL por TWh vai de 4589.8 a 4939.4 t CO₂e (+7.6%) e passa a eólica (4730.4). Essa conta está na aba `B_TWh`, versão "v03 (SOL-RS com a TUST/MWh do RS)".
   - O PET-RS latente tem o mesmo problema (cerca de 9 R$/MWh de TUST, porque 62% do MWh do PET-RB é de sistemas isolados), mas não entra em nenhuma simulação.
   - Diga qual das duas fica na principal.
8. **Repositório público:** continua público; não alterei.

## 11. Como reproduzir

```bash
pip install -r requirements.txt
python scripts/rodada03.py && python scripts/rodada03_parametros.py   # base v02 (Rodada 03)
python scripts/rodada04_parametros.py   # parâmetros v03 (8 especificações; testa a viabilidade)
python scripts/rodada04_mip.py          # MIP v03 + variantes, checagens e quadro
python scripts/rodada04_simulacoes.py   # cenários, simulações, tabelas e figuras
python -m pytest                        # 389 testes
```

## 12. Git

Trabalho na `main`, a partir de `cf8e3b0`: dois commits de trabalho em andamento (`3e5f826` e `0f5279d`) e o final, com as correções da revisão e este relatório. Push direto para a `main`.

## 13. Fontes de dados

| Fonte | Localização | Arquivo | Usada para |
|---|---|---|---|
| ONS, SEAMSE dez/2018 | p. 8, seção 4, "Total Encargos de Uso", Total Ciclo 18/19 = 10576544162.01 | `dados/externos/aneel_rap/ons_seamse_201812/SEAMSE_201812.pdf` | V3 |
| ONS, SEAMSE jun/2019 | p. 8, idem = 21367058292.17 | `…/ons_seamse_201906/SEAMSE_201906.pdf` | V3 |
| ONS, SEAMSE dez/2019 | p. 7, idem (ciclo 19/20) = 12145090044.99 | `…/ons_seamse_201912/SEAMSE_201912.pdf` | V3 |
| ANEEL, REH 2.565/2019 (texto) | 3 p. | `…/reh_2565_2019_texto/reh20192565ti.pdf` | Confirma a REH; sem o total |
| ONS 2019 por usina (02b) | — | `dados/intermediarios/geracao_2019_usina_v02.csv` | MWh no SIN (V1) |

URLs, datas e SHA-256 em `dados/externos/valores_documentais_v03.csv` e em `dados/externos/aneel_rap/DOWNLOAD.txt`.

- A tabela da seção 4 do SEAMSE traz a nota "Não inclui PIS/PASEP e COFINS". Os encargos de uso incluem a parcela do orçamento do ONS (R$ 677.4 mi em 2019).
- Não verifiquei se o total secundário da RAP (25700) inclui PIS/Pasep e Cofins. Por isso a diferença de −7.8% entre a `_rap_ons` e a principal não é, necessariamente, uma comparação homologado × faturado na mesma base.

## 14. Comparação com os valores de referência

| Referência | Esperado | Obtido | Confere |
|---|---|---|---|
| MWh no SIN do RB (Seção 2.1) | HID 363907.4 · EOL 48122.9 · SOL 4384.6 · BIO 1771.8 · CAR 11197.8 · GN 46474.0 · PET 1974.3 · NUC 16128.8 | os mesmos | 8/8 |
| SEAMSE (Seção 2.3) | 10576544162.01 · 21367058292.17 · 12145090044.99 | os mesmos | 3/3 |
| Ano civil 2019 | 22935.6 | 22935.60 | sim |
| VBP do GAS-RB (V2) | 19421.0 | 19421.05 | sim |
| A0 = artigo (9 cenários e top-10 do R1) | Rodada 01 | dentro das tolerâncias | 9/9 |

## 15. Parâmetros

| Parâmetro | v02 | v03 | Fonte / regra |
|---|---|---|---|
| TUST paga pela geração, entre as fontes | ∝ VBP | ∝ MWh no SIN | V1 (`pesos_tust_geracao_v03.csv`) |
| Remunerações e ocupações da geração, entre as fontes | ∝ VBP final | ∝ VBP − combustível | V1 (`fixa_por_tipo_sem_combustivel`) |
| Extensão de viabilidade do piso | ligada | desligada | V1: o T9 passa sem ela |
| VBP do GAS-RB | 26990.1 (4 distribuidoras) | 19421.0 (Sulgás) | V2 |
| Transmissão (RAP 2019) | 24883.4 | 24883.4; `_rap_ons`: 22935.6 | V3 |
| Sem mudança | D8, κ = 0.70, η = 0.10, teto do gás 0.90, D10, E1, latentes, α = 0.5 | | |

**Pisos (aba `pisos_vbp`):** só GN-RS (48.97), GN-RB (10981.9) e PET-RB (4066.6) ficam no piso κ, com combustível = 0.70 do VBP. As demais fontes da região caem na proporção do VBP:
- RB: HID 48774.1 → 45236.8; EOL 7068.2 → 6555.5; SOL 1044.8 → 969.0; NUC 3214.3 → 2981.2; CAR 2264.5 → 2100.3; BIO 294.0 → 272.7;
- RS: quase nada (HID 2481.2 → 2478.3).

**Reequilíbrio (aba `reequilibrio_RAS`):** levou GN-RS (−0.153), GAS-RS (−0.040), GN-RB (−0.134) e PET-RB (−0.034) a EOB = 0.10 × VBP, com as demais fontes cedendo folga. Moveu 138.0 R$ mi no RS e 3117.7 no RB (v02: 141.5 e 4797.7). Os RAS convergiram em 7 e 8 iterações.

## 16. Variantes

| Variante | O que muda | EOB/VBP mín. | Insumos não energ./VBP mín. | VBP GN-RB | VBP GAS-RB | VBP TRA-RS | Mult. máx. |
|---|---|---|---|---|---|---|---|
| **v03** (principal) | P1 + E1 + D9 + V1 + V2 | 0.100 | 0.020 | 10981.9 | 19421.0 | 1509.1 | 2.760 |
| v03_P2 | Preços iguais | 0.100 | 0.020 | 10981.9 | 19421.0 | 1509.1 | 2.760 |
| v03_E2 | Emissões ∝ SEEG | 0.100 | 0.020 | idem | idem | idem | 2.760 |
| v03_E3 | Só níveis do SEEG (não preserva o total) | 0.100 | 0.020 | idem | idem | idem | 2.760 |
| v03_gas4dist | GAS-RB pelas 4 distribuidoras | 0.100 | 0.020 | 10981.9 | 26990.1 | 1509.1 | 2.760 |
| v03_rap_ons | Transmissão = encargos do ONS | 0.100 | 0.026 | 10981.9 | 19421.0 | 1390.9 | 2.761 |
| v03_k060 | κ = 0.60 | 0.100 | **0.077** | 12812.3 | 19421.0 | 1509.1 | 2.628 |
| v03_eta005 | η = 0.05 | 0.050 | 0.047 | 10981.9 | 19421.0 | 1509.1 | 2.810 |

Nenhuma variante precisa da extensão de viabilidade. O ALERTA do T12 some só com κ = 0.60.

## 17. v02 × v03

**Efeito de V1, V2 e V3** (aba `passos_v02_v03`; "v02 + V1" é a v03 com o GAS-RB das 4 distribuidoras, ou seja, a `_gas4dist`):

| Indicador | v02 | v02 + V2 | v02 + V1 | v03 (V1 + V2) | v03 + V3 |
|---|---|---|---|---|---|
| VBP GN-RB | 12542.4 | 12542.4 | 10981.9 | 10981.9 | 10981.9 |
| R$/MWh GN-RB | 264.5 | 264.5 | 231.6 | 231.6 | 231.6 |
| TUST ÷ VBP GN-RB | 0.159 | 0.159 | 0.100 | 0.100 | 0.092 |
| Remunerações ÷ VBP GN-RB | 0.118 | 0.118 | 0.042 | 0.042 | 0.040 |
| Insumos não energ. ÷ VBP GN-RB | 0 | 0 | 0.027 | 0.027 | 0.032 |
| VBP PET-RB | 4644.4 | 4644.4 | 4066.6 | 4066.6 | 4066.6 |
| TUST ÷ VBP PET-RB | 0.159 | 0.159 | 0.011 | 0.011 | 0.011 |
| Insumos não energ. ÷ VBP PET-RB | 0 | 0 | 0.078 | 0.078 | 0.079 |
| VBP GN-RS | 54.9 | 54.9 | 49.0 | 49.0 | 49.0 |
| Insumos não energ. ÷ VBP GN-RS | 0 | 0 | 0.020 | 0.020 | 0.026 |
| VBP HID-RB | 43572.3 | 43572.3 | 45236.8 | 45236.8 | 46661.0 |
| TUST ÷ VBP HID-RB | 0.159 | 0.159 | 0.190 | 0.190 | 0.169 |
| VBP GAS-RB | 26990.1 | 19421.0 | 26990.1 | 19421.0 | 19421.0 |
| EOB/VBP GAS-RB | 0.337 | 0.169 | 0.342 | 0.171 | 0.171 |
| VBP DIS-RB | 200858.8 | 208427.9 | 200858.8 | 208427.9 | 208427.9 |
| Mult. produção RS GN | 2.327 | 2.327 | 2.400 | 2.400 | 2.397 |
| Mult. emissões RS GN (t/R$ mi) | 1458.6 | 1458.6 | 1635.9 | 1635.9 | 1636.4 |
| Mult. produção RS PET | 2.620 | 2.621 | 2.760 | 2.760 | 2.761 |
| Mult. produção RS CAR | 1.605 | 1.605 | 1.533 | 1.533 | 1.514 |
| Mult. emissões RS CAR (t/R$ mi) | 5617.5 | 5617.5 | 5608.1 | 5608.1 | 5451.5 |
| Mult. produção RS HID | 1.564 | 1.564 | 1.580 | 1.580 | 1.553 |
| Mult. emissões RS DIS (t/R$ mi) | 387.6 | 387.6 | 387.7 | 387.7 | 387.7 |

Leitura:
- **V1** é o que muda as térmicas: a TUST e as remunerações delas caem (o PET-RB quase não paga TUST, porque 62% do seu MWh é de sistemas isolados). O piso de viabilidade deixa de mandar, e o VBP volta ao piso κ das instruções (GN-RB 10981.9 ≈ 11000; PET-RB 4066.6 ≈ 4070, os valores esperados na Rodada 03). As renováveis ficam com mais VBP e passam a pagar mais TUST por real (HID-RB 0.159 → 0.190).
- **V2** só mexe no GAS-RB e na DIS-RB (resíduo); os multiplicadores do RS quase não mudam.
- **V3** reduz a transmissão em 7.8%; o efeito nos multiplicadores do RS fica abaixo de 3% (o maior é no multiplicador de emissões do CAR-RS, −2.8%).

**Resumo por subsetor (v02 → v03):**

| Região | Subsetor | VBP | R$/MWh | EOB/VBP | Mult. produção | Mult. emissões (t/R$ mi) |
|---|---|---|---|---|---|---|
| RS | HID | 2474.7 → 2478.3 | 170.2 → 170.4 | 0.506 → 0.490 | 1.564 → 1.580 | 26.7 → 26.8 |
| RS | EOL | 932.5 → 933.9 | 177.1 → 177.3 | 0.506 → 0.499 | 1.564 → 1.570 | 26.7 → 26.7 |
| RS | SOL (latente) | 0 → 0 | — | — | 1.514 → 1.436 | 25.5 → 23.6 |
| RS | BIO | 14.4 → 14.4 | 210.7 → 211.0 | 0.478 → 0.507 | 1.626 → 1.592 | 42.1 → 41.4 |
| RS | CAR | 674.1 → 675.0 | 256.8 → 257.1 | 0.482 → 0.544 | 1.605 → 1.533 | 5617.5 → 5608.1 |
| RS | GN | 54.9 → 49.0 | 314.6 → 280.5 | 0.100 → 0.100 | 2.327 → 2.400 | 1458.6 → 1635.9 |
| RS | PET (latente) | 0 → 0 | — | — | 2.620 → 2.760 | 1034.4 → 1186.7 |
| RS | TRA | 1509.1 → 1509.1 | — | 0.701 → 0.701 | 1.322 → 1.322 | 24.0 → 24.0 |
| RS | DIS | 14384.3 → 14384.3 | — | 0.245 → 0.245 | 1.896 → 1.897 | 387.6 → 387.7 |
| RS | GAS | 898.7 → 898.7 | — | 0.100 → 0.100 | 2.344 → 2.344 | 213.8 → 213.9 |
| RB | HID | 43572.3 → 45236.8 | 119.7 → 124.3 | 0.489 → 0.445 | 1.513 → 1.535 | 27.0 → 26.5 |
| RB | EOL | 6314.3 → 6555.5 | 124.6 → 129.3 | 0.489 → 0.463 | 1.513 → 1.515 | 27.0 → 26.2 |
| RB | SOL | 933.4 → 969.0 | 187.5 → 194.7 | 0.489 → 0.535 | 1.513 → 1.434 | 27.0 → 25.0 |
| RB | BIO | 262.6 → 272.7 | 148.2 → 153.9 | 0.466 → 0.465 | 1.562 → 1.539 | 87.0 → 83.7 |
| RB | CAR | 2023.0 → 2100.3 | 180.7 → 187.6 | 0.370 → 0.412 | 1.712 → 1.654 | 4841.1 → 4662.7 |
| RB | GN | 12542.4 → 10981.9 | 264.5 → 231.6 | 0.100 → 0.100 | 1.803 → 1.853 | 1676.2 → 1915.7 |
| RB | PET | 4644.4 → 4066.6 | 897.7 → 786.0 | 0.100 → 0.100 | 2.620 → 2.759 | 1031.7 → 1184.0 |
| RB | NUC | 2871.5 → 2981.2 | 178.0 → 184.8 | 0.489 → 0.512 | 1.513 → 1.460 | 27.0 → 25.4 |
| RB | TRA | 23374.4 → 23374.4 | — | 0.659 → 0.672 | 1.325 → 1.307 | 26.0 → 24.6 |
| RB | DIS | 200858.8 → 208427.9 | — | 0.250 → 0.273 | 1.945 → 1.922 | 429.4 → 422.6 |
| RB | GAS | 26990.1 → 19421.0 | — | 0.337 → 0.171 | 1.647 → 1.775 | 262.1 → 269.8 |

## 18. Resultados das simulações

Todos os choques são de R$ 1000 mi na demanda final de setores do RS, exceto o bloco B por TWh. Arquivo: `resultados/rodada04/simulacoes_v03.xlsx`.

### 18.1 A0 × A1 × A2 (E1, R1 e F1)

| Cenário | Bloco | ΔX total | CO₂e total (t) | IC | % CO₂e no RB | % indiretas | % das emissões no S38 |
|---|---|---|---|---|---|---|---|
| E1 | A0 (artigo) | 1925.04 | 428113.5 | 222.39 | 20.74 | 34.89 | 92.2 |
| E1 | A1 = A2 (S38 → DIS 97.5% e GAS 2.5%) | 1908.18 | 383250.4 | 200.85 | 25.99 | 65.95 | 91.6 |
| R1 | A0 (artigo) | 1959.35 | 216407.0 | 110.45 | 34.20 | 51.55 | 57.1 |
| R1 | A1 (S38 → DIS/GAS) | 1954.45 | 202472.1 | 103.60 | 38.09 | 70.18 | 54.2 |
| R1 | A2 (S38 → EOL) | 1853.01 | 95500.7 | 51.54 | 54.07 | 77.77 | 5.3 |
| F1 | A0 (artigo) | 2120.56 | 356045.7 | 167.90 | 22.16 | 35.34 | 39.4 |
| F1 | A1 (S38 → DIS/GAS) | 2114.64 | 340253.8 | 160.90 | 24.30 | 47.59 | 36.7 |
| F1 | A2 (S38 → CAR 93.2% + GN 6.8%) | 2003.93 | 2074925.0 | 1035.43 | 2.64 | 4.08 | 89.7 |

Demais cestas do A2, em t CO₂e (artigo → A2):
- R2: 216987.2 → 149630.2;
- R3: 169090.0 → 108263.4;
- R4a: 309794.9 → 128840.8;
- F2: 381702.9 → 2018718.0;
- F3: 375427.3 → 2831027.7.

Sensibilidades do A2 na R1: 50% EOL + 50% SOL dá 95035.5; 2/3 EOL + 1/3 TRA dá 95228.5. Na F1: 100% CAR dá 2168953.3; 100% GN dá 778682.6.

### 18.2 Bloco B — por R$ 1 bi e por TWh

| Tecnologia (RS) | R$/MWh (= choque de 1 TWh, R$ mi) | t CO₂e por R$ 1 bi | t CO₂e por TWh | diretas | indiretas | % no RB | Evitadas por TWh se substituir o carvão |
|---|---|---|---|---|---|---|---|
| Eólica | 177.3 | 26679.3 | 4730.4 | 0 | 4730.4 | 55.1 | 1437320.0 |
| Solar (latente) | 194.7 | 23578.1 | 4589.8 | 0 | 4589.8 | 51.8 | 1437460.7 |
| Hidráulica | 170.4 | 26842.2 | 4574.4 | 0 | 4574.4 | 55.2 | 1437476.0 |
| Biomassa | 211.0 | 41376.0 | 8729.6 | 49.5 | 8680.2 | 69.2 | 1433320.8 |
| Carvão | 257.1 | 5608106.1 | 1442050.4 | 1434683.4 | 7367.0 | 0.3 | 0 |
| Gás natural | 280.5 | 1635904.2 | 458891.9 | 436436.9 | 22455.0 | 4.7 | 983158.5 |
| Distribuição (mix de 2019) | — | 387676.7 | — | — | — | 25.8 | — |

**Limitação:** HID, EOL e SOL têm a mesma estrutura de insumos não energéticos (não há dado de custo por tecnologia). As diferenças entre elas vêm do VBP (R$/MWh) e, no SOL-RS, da coluna latente (espelho do SOL-RB), não de tecnologia.

**HIPÓTESE no SOL (latente):** a coluna latente paga a TUST por real do SOL-RB, que dá 20.8 R$/MWh. Se pagar a TUST por MWh das fontes do RS (35.2 R$/MWh), o SOL por TWh vai a **4939.4 t CO₂e** (diretas 0; 53.4% no RB), acima da eólica (Seção 10, ponto 7).

### 18.3 Robustez (8 versões: principal + 7 variantes)

| Cenário | CO₂e total v03 | mín.–máx. (versão) | IC mín.–máx. | % no RB mín.–máx. |
|---|---|---|---|---|
| A2 R1 | 95500.7 | 92695.1 (E3) – 95500.7 (v03) | 50.02–51.69 | 53.27–54.25 |
| A2 F1 | 2074925.0 | 2023840.6 (rap_ons) – 3025295.1 (E2) | 1013.13–1509.68 | 1.81–2.70 |
| A2 E1 | 383250.4 | 253054.8 (E3) – 437949.9 (E2) | 132.62–229.51 | 25.99–48.20 |
| B TWh EOL | 4730.4 | 4598.0 (E3) – 4842.9 (P2) | 16.52–17.13 | 54.28–55.42 |
| B TWh SOL | 4589.8 | 3179.2 (P2) – 4682.1 (rap_ons) | 15.94–16.50 | 50.92–53.06 |
| B TWh HID | 4574.4 | 4446.4 (E3) – 4842.9 (P2) | 16.51–17.13 | 54.42–55.56 |
| B TWh BIO | 8729.6 | 8079.4 (P2) – 8809.0 (rap_ons) | 25.46–27.12 | 68.86–70.66 |
| B TWh CAR | 1442050.4 | 1440353.5 (P2) – 2176057.8 (E2) | 3600.49–5519.40 | 0.19–0.28 |
| B TWh GN | 458891.9 | 458506.3 (E3) – 682165.3 (E2) | 608.17–1013.26 | 3.15–4.95 |

De onde vem a variação (desvio de cada variante em relação à v03, aba `robustez_detalhe`):
- **Variantes de emissão (E2, E3):** E2 sobe o CO₂e das fósseis em 46% a 51% e o do E1 em 14%; E3 baixa o E1 em 34%. Na E2, os fatores saem das faixas de plausibilidade (CAR 2.17 t/MWh).
- **Preços iguais (P2):** muda o valor em R$ de cada tecnologia. F1 +36.1%, porque o mesmo choque em R$ compra mais MWh de carvão. Por TWh: SOL −30.7%, BIO −7.5% e HID +5.9%.
- **Variantes de método (`_gas4dist`, `_rap_ons`, `_k060`, `_eta005`):**
  - no CO₂e total, a variação fica abaixo de 3% em todos os cenários, exceto o SOL por TWh na `_k060` (−7.4%). Lá o piso κ muda o VBP do SOL-RB e, com ele, o R$/MWh usado no choque;
  - na IC (t por R$ mi), a variação também fica abaixo de 3%, exceto o GN por TWh na `_k060` (−10.8%). Com κ = 0.60, o R$/MWh do GN-RS sobe, e o mesmo TWh vira mais reais com quase o mesmo CO₂e (+0.6%).

### 18.4 Os 5 achados principais (só fatos dos números)

1. **Cesta renovável com o S38 como eólica (A2):** as emissões da R1 caem de 216.4 mil t (artigo) para 95.5 mil t por R$ 1 bi, e a IC de 110.45 para 51.54 t por R$ mi. A participação do S38 nas emissões cai de 57.1% para 5.3%, e o maior emissor passa a ser o transporte terrestre do RS (37.1%). Nas outras cestas renováveis a queda vai de 31% (R2) a 58% (R4a).
2. **Cesta fóssil com o S38 como térmicas do RS (A2):** as emissões da F1 sobem de 356.0 mil t para 2074.9 mil t por R$ 1 bi (5.8 vezes). O carvão do RS responde sozinho por 87.8% delas, e 95.9% são diretas. Com 100% gás natural no lugar do carvão, a F1 fica em 778.7 mil t.
3. **Por TWh demandado no RS:** carvão 1442 mil t CO₂e; gás natural 459 mil t; biomassa 8.7 mil t; eólica 4.7 mil t; hidráulica 4.6 mil t; solar 4.6 mil t (4.9 mil t com a TUST do RS, hipótese da Seção 10, ponto 7). Cada TWh de eólica no lugar do carvão evita 1437 mil t.
4. **Só desagregar, sem mudar o vetor (A1), muda pouco:** nas 8 cestas, as emissões caem de 3.7% (R2) a 10.5% (E1). Mas as indiretas passam a ser maioria no E1 (de 34.9% para 66.0%), porque o choque cai na distribuição, que compra a energia das usinas.
5. **Onde as emissões acontecem:** nas cestas renováveis do A2, entre 31% e 57% das emissões induzidas ocorrem no RB (R1: 54.1%, contra 34.2% no artigo); nas cestas fósseis do A2, menos de 3%. Por TWh, 55% das emissões da eólica ocorrem no RB.
