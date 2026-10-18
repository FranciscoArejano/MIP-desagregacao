# Rodada 05 — Relatório do Claude Code

Projeto: desagregação do S38 na MIP inter-regional RS × RB, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
Data: 18/10/2026 · Instruções: `instrucoes/RODADA_05_instrucoes_CODE.md` · Rodada anterior: `respostas/RODADA_04_resposta.md`
Convenção numérica: neste relatório, ponto decimal, sem separador de milhar. No material do artigo (`artigo/`), padrão brasileiro.

Decisões aplicadas: as anteriores (D1 = C; D2, D3, D4, D6, D7 e D8 = A; D5 = E1; D9 = (a) + (b) + (f) + (r); D10 = Sulgás; D11 = R4a; D12 a D16, V1 e V2 como na Rodada 04) e as da Seção 1 das instruções. A sua mensagem de abertura não indicou outra opção, então:
- **D17 = A:** transmissão pelos encargos de uso faturados pelo ONS em 2019 (22935.6 R$ mi); a transmissão da v03 virou a variante `_rap_media`;
- **D18 = A:** SOL-RS e PET-RS latentes pagam a TUST por MWh das fontes do RS;
- **D19 = A:** κ = 0.70; o ALERTA do T12 fica aceito;
- **D20 = A:** fósseis por D13 nas tabelas principais; 100% CAR e 100% GN na sensibilidade (Tabela 5);
- **D21 = A:** E1 na principal; E3 e E4 como sensibilidades.

## 1. Resumo

- **MIP final (v04) pronta**, com as 8 variantes (`_P2`, `_E2`, `_E3`, `_E4`, `_gas4dist`, `_rap_media`, `_k060`, `_eta005`). As 9 especificações passam no T2 e no T9 sem a extensão de viabilidade.
- **D17:** a transmissão cai de 24883.4 para 22935.6 R$ mi: RS 1390.9 e RB 21544.7. Com o bloco S38 × S38 fixo, a diferença vai para a geração: HID-RB passa de 124.3 para 128.2 R$/MWh.
- **D18:** a TUST por MWh das fontes do RS (τ_RS) é 32.41 R$/MWh na v04.
  - SOL-RS: o coeficiente de TUST vai de 0.0953 para 0.1614.
  - PET-RS: vai de 0.0105 para 0.0412.
  - SOL por TWh: 4682.1 t CO₂e sem a D18; 5003.3 com ela (+6.9%).
- **T12 com ALERTA aceito (D19):** insumos não energéticos ÷ VBP de 0.026 no GN-RS e 0.032 no GN-RB. Subiram em relação à v03 (0.020 e 0.027), porque a D17 reduziu a TUST.
- **Diagnóstico NEREUS × SEEG** (Seção 19): o S38-RS da base (5838.0 mil t) é compatível com a soma "Geração de eletricidade" + "Produção de combustíveis" do SEEG 13.0 em GWP-AR5 (+0.021%), mas o RB não fecha pelo mesmo critério (−6.51%). Com 679856 combinações testadas, 224 abaixo de 0.1% e um casamento concorrente para o S19, é um indício fraco, não prova. A E1 continua na principal.
- **E4:** saem do S38 1900.2 mil t no RS e 42743.5 mil t no RB. O E1 do A2 cai 31.2%; as cestas mudam de +1.3% a +2.9%, e o B por TWh de EOL, HID e GN sobe 4.2%. Os números conferem com a referência das instruções.
- **Resultados finais (A2, por R$ 1 bi):**
  - energia elétrica agregada: 383253.7 t CO₂e;
  - cesta renovável: 95371.0 t;
  - cesta fóssil: 2026202.2 t.

  O Painel B (MIP original) reproduz o artigo nas Tabelas 1, 3, 4 e A2 (T13).
- **Material do artigo** em `artigo/`: 16 tabelas (Quadro 1, Tabelas 1–7, A1–A8) em `.xlsx`, `.docx` e `.md`; 5 figuras em PNG (300 dpi) e PDF; e os textos em `.md` e `.docx`: subseção 3.x (1331 palavras sem as equações e o Quadro 2), Apêndice B, limitações, 379 números-chave e referências. Os textos saem de modelos com `{{chave}}`, preenchidos pelo script.
- **Testes:** 417 passaram, 0 falharam, inclusive T13 a T16.

## 2. Status por etapa

| Item | Status | Observação |
|---|---|---|
| Git: trabalhar a partir da `main` | concluído | Partiu de `607d68c`; commits na `main`; tag `mip-v04-final` |
| D17 — transmissão pelo ONS | concluído | 22935.6 R$ mi; `_rap_media` com 24883.4 |
| D18 — TUST das latentes | concluído | τ_RS = 32.41 R$/MWh; HIPÓTESE marcada no `coef_latentes` |
| D19 a D21 | respeitadas | κ = 0.70; D13 nas tabelas principais; E1 na principal |
| Variantes (8), incluindo `_E4` e `_rap_media` | concluído | CSV longo, `coef_latentes` e uma linha no quadro de variantes |
| Diagnóstico NEREUS × SEEG (3.1) | concluído (indício, não prova) | Seção 19 e Tabela A7 |
| E4 e A0_E4 (3.2) e T14 | concluído | Valores movidos exatos; total da economia preservado |
| Simulações finais e robustez | concluído | `simulacoes_v04.xlsx` (28 abas) |
| Tabelas (Quadro 1, 1–7, A1–A8) | concluído | `.xlsx`, `.docx` e `.md`; T13 passa |
| Figuras 1–4 e A1 | concluído | PNG 300 dpi e PDF |
| Textos (a)–(e) | concluído; 3 referências [CONFERIR] | Seção 20 |
| Testes T1–T16 | concluído (417 passaram, 0 falharam) | Seção 7 |
| Revisão adversarial | concluído, com limitação: 9 achados no código, 2 verificados por agente e 7 por mim (os verificadores pararam no limite de uso); 8 corrigidos e 1 registrado como limitação; os textos foram conferidos por mim e por um revisor | Seção 7 |
| Relatório, HISTORICO, README | concluído | Este arquivo |

## 3. Arquivos criados, movidos ou alterados

| Caminho | Tipo | O que é |
|---|---|---|
| `instrucoes/RODADA_05_instrucoes_CODE.md` | texto | Cópia das instruções |
| `src/mip/desagregacao.py` | código (alterado) | Opção `tust_latentes` (D18), arquivo `realocacao_emissoes` (E4), `realocar_emissoes_original` (A0_E4), validações e checagens da E4 (T14) |
| `scripts/rodada05_parametros.py` | script | Parâmetros v04 a partir dos v03 (D17, D18, E4) e as 9 especificações |
| `scripts/rodada05_mip.py` | script | MIP v04, variantes, checagens e `quadro_subsetores_v04.xlsx` (com v03 × v04, D18 e E4) |
| `scripts/rodada05_simulacoes.py` | script | Cenários na v04, A0_E4, robustez nas 8 variantes, B por TWh com g/kWh e evitadas em relação ao gás |
| `scripts/rodada05_diagnostico_seeg.py` | script | Diagnóstico NEREUS × SEEG (Seção 3.1) e valores da E4 |
| `scripts/rodada05_artigo.py` | script | Todo o material de `artigo/` (tabelas, figuras, números-chave e textos) |
| `parametros/*_v04*`, `parametros/cenarios_v04.csv`, `parametros/realocacao_emissoes_v04_E4.csv` | parâmetros | 9 especificações e os CSVs; `quadro_parametros_v04.xlsx` |
| `dados/externos/seeg/seeg13_2019_recorte_energia_v04.csv`, `seeg13_2019_componentes_e4_v04.csv` | dado | Recorte do SEEG 13.0 (2019; "Geração de eletricidade" e "Produção de combustíveis") e as 5 linhas da E4 |
| `resultados/rodada05/` | resultados | MIP v04 (.xlsx + longo + latentes), 8 variantes, `checagens_v04.csv`, `quadro_subsetores_v04.xlsx`, `simulacoes_v04.xlsx`, `diagnostico_seeg_nereus.xlsx`, `tabelas_artigo_ponto_decimal.md` |
| `artigo/` | material do artigo | Seção 20 |
| `tests/test_rodada05.py` | teste | T2 v04, D17, T13, T14, T15, T16 e validações |
| `requirements.txt` | alterado | + python-docx e pypandoc_binary |
| `README.md`, `respostas/HISTORICO.md`, `parametros/LEIAME_parametros.md`, `dados/externos/FONTES.md` | documentação | Status, histórico, formato novo e fontes |

Nada foi sobrescrito: v01 a v03 e as saídas das rodadas anteriores ficaram como estavam.

## 4. Validação da MIP original

Sem mudança: o T1 (SHA-256 da planilha original) e as identidades da Rodada 01 passam.

## 5. Reprodução dos resultados

O A0 roda os 9 cenários do artigo na MIP original e reproduz a Rodada 01. O T13 confere, arredondados a uma casa, os valores publicados nos Painéis B das Tabelas 1, 3 e 4 e na Tabela A2: são idênticos. A maior diferença de CO₂e entre o A0 e os valores de referência é 0.0049 t.

## 6. Diagnóstico do S38 (v04)

É a Tabela A3 do apêndice, aqui em ponto decimal. As colunas completas estão em `resultados/rodada05/quadro_subsetores_v04.xlsx`.

**Tabela A3:** Os 11 subsetores do S38 no RS e no RB: produção, preços, emissões e multiplicadores

| Região | Subsetor | VBP (R$ milhões) | GWh | R$/MWh | t CO₂e/MWh (E1) | EOB/VBP | Multiplicador de produção | Multiplicador de emissões (t CO₂e/R$ milhão) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| RS | Geração hidrelétrica | 2549.7 | 14542.6 | 175.3 | 0.000 | 0.515 | 1.553 | 26.4 |
| RS | Geração eólica | 960.8 | 5266.9 | 182.4 | 0.000 | 0.523 | 1.544 | 26.2 |
| RS | Geração solar fotovoltaica (latente) | 0.0 |  |  |  |  | 1.508 | 24.9 |
| RS | Geração a biomassa | 14.8 | 68.2 | 217.1 | 0.000 | 0.529 | 1.568 | 40.6 |
| RS | Geração a carvão mineral | 694.5 | 2625.2 | 264.5 | 1.435 | 0.562 | 1.514 | 5451.5 |
| RS | Geração a gás natural | 49.0 | 174.6 | 280.5 | 0.436 | 0.100 | 2.397 | 1636.4 |
| RS | Geração a derivados de petróleo (latente) | 0.0 |  |  |  |  | 2.801 | 1187.6 |
| RS | Geração nuclear (sem produção) | 0.0 |  |  |  |  |  |  |
| RS | Transmissão de energia elétrica | 1390.9 |  |  |  | 0.695 | 1.321 | 23.9 |
| RS | Distribuição e comercialização de energia elétrica | 14384.3 |  |  |  | 0.241 | 1.897 | 387.7 |
| RS | Gás canalizado e outras utilidades | 898.7 |  |  |  | 0.100 | 2.344 | 213.9 |
| RS | S38 agregado (MIP original) | 20942.7 |  |  |  | 0.322 | 1.925 | 428.1 |
| RB | Geração hidrelétrica | 46661.0 | 363907.4 | 128.2 | 0.000 | 0.471 | 1.510 | 26.1 |
| RB | Geração eólica | 6761.9 | 50687.1 | 133.4 | 0.000 | 0.487 | 1.492 | 25.8 |
| RB | Geração solar fotovoltaica | 999.5 | 4978.0 | 200.8 | 0.000 | 0.552 | 1.419 | 24.7 |
| RB | Geração a biomassa | 281.3 | 1771.8 | 158.7 | 0.007 | 0.488 | 1.517 | 81.6 |
| RB | Geração a carvão mineral | 2166.4 | 11197.8 | 193.5 | 0.867 | 0.433 | 1.631 | 4520.9 |
| RB | Geração a gás natural | 10981.9 | 47422.4 | 231.6 | 0.433 | 0.100 | 1.851 | 1916.1 |
| RB | Geração a derivados de petróleo | 4066.6 | 5174.0 | 786.0 | 0.829 | 0.100 | 2.760 | 1184.2 |
| RB | Geração nuclear | 3075.1 | 16129.0 | 190.7 | 0.000 | 0.532 | 1.442 | 25.0 |
| RB | Transmissão de energia elétrica | 21544.7 |  |  |  | 0.663 | 1.305 | 24.4 |
| RB | Distribuição e comercialização de energia elétrica | 208427.9 |  |  |  | 0.269 | 1.922 | 422.6 |
| RB | Gás canalizado e outras utilidades | 19421.0 |  |  |  | 0.171 | 1.775 | 269.8 |
| RB | S38 agregado (MIP original) | 324387.3 |  |  |  | 0.320 | 1.909 | 406.3 |

*Nota: GWh de 2019 (BEN 2020 e ONS); R$/MWh = VBP ÷ GWh; t CO₂e/MWh pela variante E1. Multiplicador de produção = soma da coluna da inversa de Leontief; multiplicador de emissões = emissões totais (diretas e indiretas) por R$ milhão de demanda final do subsetor. Subsetores latentes: coeficientes técnicos do mesmo subsetor no RB, com a TUST por MWh do RS.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

Ficam com ALERTA de multiplicador de produção acima de 2.2: GN-RS (2.397), GAS-RS (2.344), PET-RB (2.760) e PET-RS latente (2.801). Os fatores E1 ficam dentro das faixas da Rodada 03.

## 7. Motor de desagregação

**O que mudou** (`src/mip/desagregacao.py`; formato em `parametros/LEIAME_parametros.md`):

| Item | Implementação |
|---|---|
| D18 | Opção `tust_latentes: {gwh_espelho: {subsetor: GWh}, fonte}` no YAML. Para cada coluna latente k da região r: τ_r = TUST paga pelas fontes de r ÷ MWh no SIN dessas fontes (`pesos_tust_geracao`); p_k = VBP do espelho ÷ GWh do espelho; coeficiente total de TUST = τ_r ÷ p_k. A repartição entre TRA-RS e TRA-RB fica como estava, e os demais coeficientes não mudam. A fonte de cada linha recebe "HIPÓTESE (D18)", e a aba `tust_latentes` registra τ, p e os coeficientes antes e depois. É erro faltar o GWh de algum latente |
| E4 | Arquivo `realocacao_emissoes` (regiao, item, setor_destino, valor, fonte). Depois da E1, retira os valores dos subsetores do resíduo (DIS e GAS), na proporção do resíduo de cada um, e os soma ao setor de destino da mesma região. É erro o destino ser o setor-alvo e o valor passar do resíduo |
| T14 | Checagens `realocacao_co2e_valores_movidos`, `_setor_alvo`, `_total_economia`, `_sem_negativos` e `_proporcao_residuo` (a retirada de DIS e GAS segue o resíduo de cada um). A `satelite_co2e_preservado` vira ALERTA, porque na E4 só o total da economia é preservado, como na E3 |
| A0_E4 | `realocar_emissoes_original(mip, tabela, "S38")`: cópia da MIP original com os mesmos valores tirados do S38 de cada região |

**Revisão adversarial.** Rodei revisores independentes para o motor (D18 e E4) e para os scripts e resultados da v04, com um verificador cético por achado. Os agentes pararam várias vezes no limite de uso. Dois achados foram verificados por agente; os outros, **conferi eu mesmo**, reproduzindo cada um com scripts próprios antes de corrigir. O diagnóstico NEREUS × SEEG e as referências tiveram construtor e verificador independentes (Seções 19 e 20). O revisor do material do artigo e os verificadores dos textos também pararam no limite. Por isso, conferi eu mesmo a seção 3.x e o Apêndice B contra o código e as saídas, e escrevi as limitações. Depois, um revisor independente conferiu os três textos contra o código, os parâmetros e as planilhas. Ele achou 7 problemas, todos de redação, nenhum de método ou de número. Conferi e corrigi os 7:
- **Quadro 2:** faltava o piso na geração a derivados de petróleo; o critério da nuclear parecia "GWh × tarifa", quando é a parcela de E_r ponderada por GWh × tarifa.
- **Reprodução do artigo** (seção 3.x, B.12 e Tabela A8): "diferença máxima de 0.005 t em relação aos valores publicados" misturava duas coisas. A comparação é com a referência de duas casas; contra os valores publicados, os números são idênticos após o arredondamento a uma casa, exceto a linha R4a da Tabela 4.
- **Limitação 1:** a diferença da solar por TWh vem também da coluna latente do RB, que não compra derivados de petróleo.
- **B.12 e Tabela A8:** faltava declarar o alerta de multiplicador acima de 2.2. Ele aparece nas 9 especificações; o do T12, em 7, porque a `_k060` e a `_eta005` passam. A Tabela A8 ganhou a linha "Alertas".
- **Seção 3.x:** dizia "duas sensibilidades" de emissões, mas a E2 também foi calculada.
- **Limitação 6:** "a maior variação" com κ = 0.60 vale só entre as emissões da Tabela A6.

Dois ajustes menores: a Eq. (28) ganhou o max(·, 0) da (B.35); as citações cujo ano está entre colchetes na referência passaram a usar o colchete ("ONS, [2026]").

| # | Achado | Gravidade | Conferência | Correção |
|---|---|---|---|---|
| 1 | O teste do A0_E4 não conferia os setores e as regiões de destino | baixa | confirmado pelo verificador: dois mutantes (tudo no S19-RS; S04 ↔ S05) passavam | O teste confere cada destino, por região, e o resto do vetor |
| 2 | O `verificar` não detectava uma retirada da E4 fora da proporção do resíduo | baixa | o verificador classificou como lacuna de cobertura, não defeito (o teste já cobria a proporção) | Checagem nova `realocacao_co2e_proporcao_residuo` na `_E4` |
| 3 | A E4 não estava marcada como HIPÓTESE na fonte dos parâmetros | baixa | reproduzido | A fonte de `realocacao_emissoes_v04_E4.csv` começa com "HIPÓTESE (E4, sensibilidade…)", com o risco de dupla contagem |
| 4 | O T16 só testava a D18 na versão principal | baixa | reproduzido | T16 parametrizado nas 9 especificações |
| 5 | Com a D18, o EOB/VBP implícito do PET-RS latente (6.9%) fica abaixo de η (10%), e nenhuma saída registrava isso | média | reproduzido: espelho 10.0% − Δ TUST 3.07 p.p.; o SOL-RS fica em 48.6% | Registrado nas abas `d18_latentes` e `d18_eob_implicito_versoes` (9 versões) e na limitação 2. A coluna não entra nos cenários do artigo. Mantido, porque a D18 é decisão sua (Seção 10) |
| 6 | A aba `robustez` de `simulacoes_v04.xlsx` não trazia o A0_E4 | baixa | reproduzido | Bloco A0 × A0_E4 acrescentado à aba |
| 7 | A sobra do resíduo depois da E4 (75.7 e 6946.3 mil t) diferia da referência das instruções (cerca de 93 e 7220), sem explicação nas saídas | baixa | reproduzido: a diferença é o SF₆ do DIS, que na E1 é nível identificado | Explicado no LEIAME do quadro, no Apêndice B e nas Seções 14 e 19 |
| 8 | A fonte da D17 nos CSVs terminava em "nan" e remetia a "SEAMSE acima", que não existe no arquivo | baixa | reproduzido | A fonte cita os três SEAMSE (documento, localização, endereço e SHA-256) |
| 9 | Apêndice B entregue pelo agente com 8 números marcados "FALTA" (consumo específico do θ_RS, limiares de alerta e 5 números do diagnóstico) | baixa | conferido por mim | Números-chave novos no script, lidos dos arquivos; nenhum digitado à mão |

O revisor do motor conferiu, com mutações, τ_RS, p_k, a repartição entre TRA-RS e TRA-RB, a E4 na proporção do resíduo, o A0_E4 e as validações novas. O dos scripts recalculou a v04, a `_E4`, a `_rap_media` e a `_P2` em memória (diferença ≤ 1.5e-11) e refez o A2 e o B por TWh com um Leontief independente: tudo bate com as planilhas.

**Testes** (417 passaram, 0 falharam):

| Teste | Resultado | O que verifica |
|---|---|---|
| T1–T12 e os das rodadas anteriores | passaram | Como antes (T12 com o ALERTA aceito pela D19) |
| T2 v04 | passou (9 especificações) | Re-agregação exata; na E3 e na E4, o CO₂e só pelo total |
| D17 | passou | Transmissão RS + RB = 22935.6, ∝ VBP do S38; `_rap_media` = 24883.4; fonte "D17: …" |
| **T13** | passou | Painéis B das Tabelas 1, 3 e 4 e Tabela A2 = valores publicados |
| **T14** | passou | E4 e A0_E4: valores movidos exatos, total inalterado, S38 reduzido no valor movido, nada negativo |
| **T15** | passou | Gerar o material duas vezes dá os mesmos números em todas as tabelas e nos números-chave |
| **T16** | passou | TUST por MWh das latentes, ao p_k, = τ_RS; repartição entre as origens mantida; demais coeficientes iguais |
| Validações | passaram | D18 sem o GWh de um latente; E4 com destino no S38 ou valor acima do resíduo |

## 8. Acesso a fontes externas

| Fonte | Acessível? | O que foi usado | Observação |
|---|---|---|---|
| SEEG 13.0, dados nacionais | já estava (02b) | Bruto local (185 MB, fora do git), SHA-256 conferido | Recortes novos versionados em `dados/externos/seeg/` |
| Crossref (`api.crossref.org`) | sim | Conferência das referências de método | Seção 20 |
| ONS (SEAMSE) | já estava (Rodada 04) | Os três PDFs da D17 | — |

## 9. Decisões tomadas por mim nesta rodada

| Decisão | Alternativas consideradas | Por quê |
|---|---|---|
| D18 implementada no motor (opção `tust_latentes`), com τ e p calculados na própria versão | Reescalar o `coef_latentes` num script | Fica no YAML e vale em todas as variantes: com P2, por exemplo, p_k muda e o coeficiente acompanha |
| p_k = VBP do espelho ÷ GWh da D8 (inclui os sistemas isolados do RB) | GWh no SIN | É o R$/MWh usado no choque do B por TWh (o mesmo da Rodada 04) |
| E4 implementada no motor (arquivo `realocacao_emissoes`) | Só no script das simulações | Gera a variante como as outras (CSV longo, latentes, checagens) |
| Vetor do A2 fóssil fixo nas variantes, o da v04 (CAR 93.4%, GN 6.6%) | Recalcular em cada variante | Como na Rodada 04: o choque fica igual na robustez; só a MIP muda |
| Painel A = A2 da v04; Painel B = A0 | — | Seção 5.1 |
| Tabela 7 em duas partes | Uma tabela de 12 colunas | Não cabe em A4 retrato |
| Tabela 6: linha da distribuição só com "Emissões por R$ 1 bilhão" | Preencher também "% no RB" | A instrução pede só as colunas por R$ 1 bilhão |
| xlsx com uma casa decimal, salvo razões, fatores e multiplicadores (três casas) e a Tabela A8 (seis) | Uma casa em tudo | Com uma casa, EOB/VBP, t CO₂e/MWh e multiplicadores perdem a informação |
| Números dos textos como `{{chave}}`, trocados pelo script | Digitar os números | "Nenhum número digitado à mão": cada número vem de `numeros_chave.json`, com origem |
| Nomes curtos dos setores fora da lista do artigo: forma curta do nome da MIP, escrita no script | — | Seção 5 |

## 10. Pontos para o Francisco

**Para revisar ou decidir:**

1. **Textos do artigo** (`artigo/texto/`). A seção 3.x foi escrita por um agente e conferida por mim. O Apêndice B foi escrito por um agente que parou no limite; completei e conferi. As limitações são minhas. Os números são trocados pelo script, mas a redação precisa da sua leitura. Para mudar o texto, edite os modelos em `artigo/texto/modelos/` (Seção 20).
2. **Três referências [CONFERIR]** (`artigo/texto/referencias.md`):
   - CanalEnergia (2019): o site bloqueou o acesso (desafio anti-robô), então o título exato não foi confirmado. É a fonte secundária da RAP 2019-2020, usada só na `_rap_media`.
   - Sulgás (2020): o conteúdo foi conferido no PDF, mas não o título formal do volume da CAGE nem a designação "v. 5, pt. 2".
   - NEREUS ([2025?]): o título foi conferido na planilha, mas não o ano nem a forma de publicação. Vale perguntar à equipe da NEREUS como citar.
3. **Diagnóstico NEREUS × SEEG:** o resultado é um indício fraco, não prova (Seção 19). Só a documentação da conta-satélite resolve a questão. Se puder pedi-la à NEREUS, a E3/E4 deixa de ser uma faixa.
4. **E4 e dupla contagem:** na E4, o S19-RS passa de 2693.9 para 4506.0 mil t. Se a base já tiver o refino no S19, a E4 o conta duas vezes. Mantive a E4 só como sensibilidade (D21).
5. **PET-RS latente sob a D18:** o EOB/VBP implícito fica em 6.9%, abaixo de η = 10% (achado 5 da Seção 7). A coluna não entra em nenhum cenário do artigo e está na limitação 2. Se preferir, posso limitar o ajuste da TUST para manter o EOB implícito ≥ η.
6. **P2 na cesta fóssil:** com preços iguais, as emissões do A2 fóssil sobem 36.0%. É a maior sensibilidade da robustez (Tabela A6). Ela vem do preço do carvão nos leilões (251 R$/MWh contra cerca de 170 da hidrelétrica e da eólica no RS). Está na limitação 5; avalie se merece menção no corpo do texto.
7. **Alertas mantidos:**
   - T12 (D19): insumos não energéticos ÷ VBP = 0.026 no GN-RS e 0.032 no GN-RB.
   - Multiplicador de produção acima de 2.2: GN-RS (2.397), GAS-RS (2.344), PET-RB (2.760) e PET-RS latente (2.801).
8. **Formato das tabelas:** confira se o `.docx` das Tabelas 1–7 atende às normas da revista. Confira também os nomes curtos dos setores fora da lista do artigo (Tabelas 2 e A2 e Figuras 1 e A1), que escrevi no script.
9. **Repositório:** não mexi na visibilidade. Ele continua público, com os dados da MIP original.

## 11. Como reproduzir

```bash
pip install -r requirements.txt
python scripts/rodada05_diagnostico_seeg.py   # diagnóstico NEREUS × SEEG e valores da E4 (precisa do bruto do SEEG)
python scripts/rodada05_parametros.py         # parâmetros v04 (9 especificações)
python scripts/rodada05_mip.py                # MIP v04 + variantes, checagens e quadro
python scripts/rodada05_simulacoes.py         # cenários, A0_E4, robustez
python scripts/rodada05_artigo.py             # tabelas, figuras, números-chave e textos do artigo
python -m pytest                              # 417 passaram, 0 falharam
```

O bruto do SEEG (185 MB) não está no git. O endereço e o SHA-256 estão em `dados/externos/seeg/DOWNLOAD.txt`. Sem o bruto, os passos seguintes usam o recorte versionado.

## 12. Git

Trabalho na `main`, a partir de `607d68c`: commits intermediários (`b8d0aef`, `8a2cd11`, `477b794`, `3e584a4`, `ab71e51`, `532e747`, `8276084`, `8ff74b3`, `d7bdb22`, `b3d0cda` e os da revisão dos textos) e o final. A tag `mip-v04-final` aponta para o commit final. Push direto para a `main`, com a tag.

## 13. Fontes de dados

| Fonte | Localização | Arquivo | Usada para |
|---|---|---|---|
| SEEG 13.0, dados nacionais | aba Dados; 2019; GWP-AR5; Emissão e Emissão NCI; "Geração de eletricidade" e "Produção de combustíveis" | `dados/externos/seeg/seeg13_2019_recorte_energia_v04.csv` (recorte); bruto fora do git | Diagnóstico (3.1), E4 e Tabela A7 |
| ONS, SEAMSE dez/2018, jun/2019 e dez/2019 | seção 4, "Total Encargos de Uso" | `dados/externos/aneel_rap/ons_seamse_*` | D17 |
| EPE, BEN 2020, Tabela 5.4 (D8) | p. 112 | `dados/externos/epe/ben2020_tabela_5_4_v01.csv` | GWh do espelho (p_k) |

As demais fontes são as das rodadas anteriores (`dados/externos/FONTES.md`; Tabela A4 do apêndice).

## 14. Comparação com os valores de referência

| Referência (instruções) | Esperado | Obtido | Confere |
|---|---|---|---|
| Tabela da Seção 3 (SEEG, mil t) | 9 componentes × 3 regiões | todas as células a menos de 0.05 mil t | sim |
| S38 NEREUS: RS e RB | 5838.0 e 84518.3 | 5838.0 e 84518.3 | sim |
| E4: valores movidos (mil t) | 1812.1; 88.1; 18088.8; 23499.2; 1155.4 | 1812.1; 88.1; 18088.9; 23499.2; 1155.4 | sim; 18088.8 é a soma de parcelas já arredondadas (17329.1 + 759.7) |
| E4: o que sobra do resíduo | cerca de 93 (RS) e 7220 (RB) | 75.7 e 6946.3 | a diferença é o SF₆ (19.6 no RS e 303.5 no RB): na E1 ele é nível identificado, não resíduo |
| E4 × E1 (A2) | E1 −31.2%; R1 +1.8%; F1 +2.1%; outras de +1.2% a +2.9%; F1 100% GN +8.5%; TWh EOL, HID, GN +4.2%; CAR 0.0% | E1 −31.2%; R1 +1.8%; F1 +2.2%; outras de +1.3% a +2.9%; F1 100% GN +8.5%; TWh EOL, HID, GN +4.2%; CAR 0.0% | sim (a referência foi feita sobre a v03) |
| SOL por TWh com a TUST do RS | 4939.4 (sobre a v03) | 5003.3 (v04) | sobre a v03, a conta da Rodada 04 dava 4939.4; na v04, τ_RS e p_SOL mudam com a D17 |
| Painel B das Tabelas 1, 3, 4 e A2 | valores publicados | idênticos a uma casa | sim (T13) |
| Transmissão (D17) | 22935.6 | 22935.60 | sim |

## 15. Parâmetros

| Parâmetro | v03 | v04 | Fonte / regra |
|---|---|---|---|
| Transmissão (Brasil) | 24883.4 (RAP) | 22935.6 (ONS) | D17 (`componentes_v04.csv`) |
| Transmissão RS / RB | 1509.1 / 23374.4 | 1390.9 / 21544.7 | ∝ VBP do S38 |
| TUST das latentes | por real do espelho do RB | τ_RS ÷ p_k (32.41 R$/MWh) | D18 (`tust_latentes` no YAML) |
| E4 | — | `realocacao_emissoes_v04_E4.csv` | Seção 3.2 |
| Sem mudança | κ = 0.70 (D19), η = 0.10, teto do gás 0.90, α = 0.5, D8, D9, D10, V1, V2, E1, latentes por espelho, P1 | | |

**Pisos (aba `pisos_vbp`):** GN-RS (49.0), GN-RB (10981.9) e PET-RB (4066.6) ficam no piso κ, com o combustível em 0.70 do VBP. As demais fontes da região caem na proporção do VBP inicial.

## 16. Variantes

| Variante | O que muda | EOB/VBP mín. | Insumos não energ./VBP mín. | VBP TRA-RS | VBP GAS-RB | τ_RS (R$/MWh) | Mult. máx. |
|---|---|---|---|---|---|---|---|
| **v04** (principal) | P1 + E1 + D9 + V1 + V2 + D17 + D18 | 0.100 | 0.026 | 1390.9 | 19421.0 | 32.41 | 2.801 |
| v04_P2 | Preços iguais | 0.100 | 0.026 | 1390.9 | 19421.0 | 32.41 | 2.801 |
| v04_E2 | Emissões ∝ SEEG | 0.100 | 0.026 | idem | idem | idem | 2.801 |
| v04_E3 | Só níveis do SEEG (não preserva o total) | 0.100 | 0.026 | idem | idem | idem | 2.801 |
| v04_E4 | Refino, exploração de petróleo e gás e carvão do SEEG saem de DIS e GAS para S19, S05 e S04 (preserva só o total da economia) | 0.100 | 0.026 | idem | idem | idem | 2.801 |
| v04_gas4dist | GAS-RB pelas 4 distribuidoras | 0.100 | 0.026 | 1390.9 | 26990.1 | 32.41 | 2.801 |
| v04_rap_media | Transmissão da v03 (24883.4) | 0.100 | 0.020 | 1509.1 | 19421.0 | 35.16 | 2.804 |
| v04_k060 | κ = 0.60 | 0.100 | **0.077** | 1390.9 | 19421.0 | 32.41 | 2.664 |
| v04_eta005 | η = 0.05 | 0.050 | 0.053 | 1390.9 | 19421.0 | 32.41 | 2.851 |

Nenhuma variante precisa da extensão de viabilidade. Com a D17, a `_eta005` passa a ter o T12 OK (0.053). A robustez completa está na Tabela A6 e na aba `robustez_detalhe`.

## 17. v03 × v04

**Efeito de D17 e de D18** (aba `passos_v03_v04`):

| Indicador | v03 | v03 + D17 (= v03_rap_ons) | v03 + D18 (= v04_rap_media) | v04 = v03 + D17 + D18 |
|---|---|---|---|---|
| VBP HID-RB | 45236.8 | 46661.0 | 45236.8 | 46661.0 |
| R$/MWh HID-RB | 124.3 | 128.2 | 124.3 | 128.2 |
| TUST ÷ VBP HID-RB | 0.190 | 0.169 | 0.190 | 0.169 |
| VBP CAR-RS | 675.0 | 694.5 | 675.0 | 694.5 |
| R$/MWh CAR-RS | 257.1 | 264.5 | 257.1 | 264.5 |
| VBP GN-RB / PET-RB / GN-RS (no piso κ) | 10981.9 / 4066.6 / 49.0 | iguais | iguais | iguais |
| Insumos não energ. ÷ VBP GN-RS | 0.020 | 0.026 | 0.020 | 0.026 |
| Insumos não energ. ÷ VBP GN-RB | 0.027 | 0.032 | 0.027 | 0.032 |
| Mult. emissões CAR-RS (t/R$ mi) | 5608.1 | 5451.5 | 5608.1 | 5451.5 |
| Mult. produção HID-RS | 1.580 | 1.553 | 1.580 | 1.553 |
| Mult. produção SOL-RS (latente) | 1.436 | 1.421 | 1.533 | 1.508 |
| Mult. emissões SOL-RS (latente; t/R$ mi) | 23.6 | 23.3 | 25.4 | 24.9 |
| Mult. produção PET-RS (latente) | 2.760 | 2.761 | 2.804 | 2.801 |

Leitura:
- **D17** reduz a transmissão em 1947.8 R$ mi (−7.8%). Como o bloco S38 × S38 da original é fixo, E_r = bloco − T_r sobe, e a geração ganha VBP e R$/MWh: HID-RB passa de 124.3 para 128.2 R$/MWh e CAR-RS de 257.1 para 264.5. As térmicas no piso κ não mudam. A TUST por MWh das fontes do RS cai de 35.16 para 32.41 R$/MWh.
- **D18** só mexe nas colunas latentes. SOL-RS: TUST de 19.14 para 32.41 R$/MWh, ao p_SOL = 200.79 R$/MWh; coeficiente de 0.0953 para 0.1614. PET-RS: TUST de 8.29 para 32.41 R$/MWh, ao p_PET = 785.97; coeficiente de 0.0105 para 0.0412. Os multiplicadores sobem: SOL-RS de 1.421 para 1.508 (produção) e de 23.3 para 24.9 t/R$ mi (emissões); PET-RS de 2.761 para 2.801 e de 1186.9 para 1187.6.

**Resultados, v03 → v04** (A2 por R$ 1 bi; B por TWh ao R$/MWh de cada versão):

| Cenário | v03 | v04 | Variação |
|---|---|---|---|
| A2 E1 (t CO₂e) | 383250.4 | 383253.7 | 0.0% |
| A2 R1 | 95500.7 | 95371.0 | −0.1% |
| A2 F1 | 2074925.0 | 2026202.2 | −2.3% |
| A2 F2 / F3 | 2018718.0 / 2831027.6 | 1972315.4 / 2761423.7 | −2.3% / −2.5% |
| TWh EOL / HID / BIO | 4730.4 / 4574.4 / 8729.6 | 4787.8 / 4627.1 / 8809.0 | +1.2% / +1.2% / +0.9% |
| TWh SOL | 4589.8 | 5003.3 | +9.0% (D17: +2.0%; D18: +6.9%) |
| TWh CAR / GN | 1442050.4 / 458891.9 | 1442160.5 / 459018.6 | 0.0% / 0.0% |

A F1 cai porque o CAR-RS fica mais caro (264.5 R$/MWh): o mesmo choque em reais compra menos MWh de carvão. A fração de CAR no A2 fóssil passa de 93.2% para 93.4%.

## 18. Resultados finais

As Tabelas do artigo, em ponto decimal. As versões no padrão brasileiro estão em `artigo/tabelas/`.

**Quadro 1:** Composição dos vetores de choque dos cenários principais e atribuição do S38 na MIP desagregada

| Cenário | Região | Código | Setor | Participação no choque (%) | Valor do choque (R$ milhões) | Função no cenário | Setor na MIP desagregada |
|---|---|---|---|---:|---:|---|---|
| Energia elétrica agregada | RS | S38 | Energia elétrica, gás natural e outras utilidades | 100.0 | 1000.0 | Expansão agregada do setor energético | Distribuição e comercialização de energia elétrica (97,5%) e Gás canalizado e outras utilidades (2,5%), pela composição da demanda final |
| Cesta renovável | RS | S38 | Energia elétrica, gás natural e outras utilidades | 30.0 | 300.0 | Componente energético agregado associado à implantação | Geração eólica (S38_EOL) |
| Cesta renovável | RS | S31 | Fabricação de máquinas e equipamentos elétricos | 25.0 | 250.0 | Equipamentos elétricos e componentes de conexão | igual |
| Cesta renovável | RS | S29 | Fabricação de produtos de metal, exceto máquinas e equipamentos | 15.0 | 150.0 | Estruturas metálicas e componentes físicos | igual |
| Cesta renovável | RS | S40 | Construção | 20.0 | 200.0 | Obras civis, fundações e instalação | igual |
| Cesta renovável | RS | S43 | Transporte terrestre | 5.0 | 50.0 | Transporte de equipamentos e insumos | igual |
| Cesta renovável | RS | S56 | Serviços de arquitetura, engenharia, testes/análises técnicas e P&D | 5.0 | 50.0 | Engenharia, projetos, testes e P&D | igual |
| Cesta fóssil | RS | S38 | Energia elétrica, gás natural e outras utilidades | 35.0 | 350.0 | Energia/gás e utilidades associadas | Geração a carvão mineral (93,4%) e Geração a gás natural (6,6%), pelo VBP de 2019 |
| Cesta fóssil | RS | S43 | Transporte terrestre | 25.0 | 250.0 | Logística e transporte associados | igual |
| Cesta fóssil | RS | S19 | Refino de petróleo e coquerias | 40.0 | 400.0 | Processamento e oferta de combustíveis fósseis | igual |

*Nota: choques de R$ 1.000 milhões na demanda final de setores do RS. Na MIP desagregada, o S38 da energia elétrica agregada é repartido entre distribuição e gás canalizado na proporção das vendas de cada subsetor à demanda final do RS; o das cestas renováveis vai para a geração eólica; o das cestas fósseis, para a geração a carvão mineral e a gás natural do RS na proporção do VBP de 2019 de cada uma.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 1:** Impactos econômicos e ambientais dos cenários energéticos

*Painel A — MIP com o S38 desagregado (versão final)*

| Cenário | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Produção bruta por mil t CO₂e (R$ milhões) |
|---|---:|---:|---:|---:|
| Energia elétrica agregada RS | 1908.1 | 383253.7 | 200.9 | 5.0 |
| Cesta renovável RS | 1845.2 | 95371.0 | 51.7 | 19.3 |
| Cesta fóssil RS | 1997.1 | 2026202.2 | 1014.6 | 1.0 |
| Diferença de emissões incorporadas (fóssil − renovável) |  | 1930831.2 |  |  |
| Redução da intensidade carbônica (%) |  |  | 94.9 |  |

*Painel B — MIP original*

| Cenário | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Produção bruta por mil t CO₂e (R$ milhões) |
|---|---:|---:|---:|---:|
| Energia elétrica agregada RS | 1925.0 | 428113.5 | 222.4 | 4.5 |
| Cesta renovável RS | 1959.4 | 216407.0 | 110.4 | 9.1 |
| Cesta fóssil RS | 2120.6 | 356045.7 | 167.9 | 6.0 |
| Diferença de emissões incorporadas (fóssil − renovável) |  | 139638.8 |  |  |
| Redução da intensidade carbônica (%) |  |  | 34.2 |  |

*Nota: choques de R$ 1.000 milhões na demanda final do RS. A redução da intensidade carbônica é a da cesta renovável em relação à cesta fóssil, em % da intensidade da cesta fóssil.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 2:** Principais setores responsáveis pelas emissões induzidas pela cesta renovável

*Painel A — MIP com o S38 desagregado (versão final)*

| Ranking | Região | Código | Setor | Produção induzida (R$ milhões) | Emissões induzidas (t CO₂e) | Participação (%) |
|---|---|---|---|---:|---:|---:|
| 1 | RS | S43 | Transporte terrestre | 83.9 | 35418.9 | 37.1 |
| 2 | RB | S27 | Siderurgia e tubos de aço sem costura | 45.9 | 11166.8 | 11.7 |
| 3 | RB | S26 | Fabricação de produtos de minerais não metálicos | 15.0 | 6799.0 | 7.1 |
| 4 | RB | S43 | Transporte terrestre | 14.7 | 6567.0 | 6.9 |
| 5 | RB | S28 | Metalurgia de metais não ferrosos e fundição | 33.9 | 5049.7 | 5.3 |
| 6 | RB | S39 | Água, esgoto e gestão de resíduos | 4.6 | 4524.1 | 4.7 |
| 7 | RB | S03 | Produção florestal, pesca e aquicultura | 1.0 | 3030.2 | 3.2 |
| 8 | RB | S01 | Agricultura e apoio à agricultura | 3.4 | 2537.3 | 2.7 |
| 9 | RB | S02 | Pecuária | 0.4 | 2514.7 | 2.6 |
| 10 | RB | S19 | Refino de petróleo e coquerias | 35.4 | 2038.0 | 2.1 |
|  |  |  | Demais setores | 1606.9 | 15725.3 | 16.5 |
| Total |  |  | Cesta renovável RS | 1845.2 | 95371.0 | 100.0 |
|  |  |  | Memória: subsetores do S38 (RS e RB) | 373.1 | 4997.8 | 5.2 |

*Nota: choque de R$ 1.000 milhões na demanda final do RS (cesta renovável base); o S38 da cesta foi atribuído à geração eólica do RS. A linha de memória soma os 22 subsetores do S38 (11 em cada região) e não entra no total.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 3:** Spillovers ambientais entre o Rio Grande do Sul e o Restante do Brasil

*Painel A — MIP com o S38 desagregado (versão final)*

| Cenário | Região impactada | Produção induzida (R$ milhões) | Emissões induzidas (t CO₂e) | Participação nas emissões (%) |
|---|---|---:|---:|---:|
| Energia elétrica agregada RS | RS | 1384.2 | 283644.1 | 74.0 |
| Energia elétrica agregada RS | RB | 524.0 | 99609.6 | 26.0 |
| Cesta renovável RS | RS | 1364.6 | 43833.7 | 46.0 |
| Cesta renovável RS | RB | 480.5 | 51537.3 | 54.0 |
| Cesta fóssil RS | RS | 1333.2 | 1971586.1 | 97.3 |
| Cesta fóssil RS | RB | 663.8 | 54616.1 | 2.7 |

*Painel B — MIP original*

| Cenário | Região impactada | Produção induzida (R$ milhões) | Emissões induzidas (t CO₂e) | Participação nas emissões (%) |
|---|---|---:|---:|---:|
| Energia elétrica agregada RS | RS | 1357.0 | 339326.4 | 79.3 |
| Energia elétrica agregada RS | RB | 568.0 | 88787.1 | 20.7 |
| Cesta renovável RS | RS | 1391.3 | 142390.0 | 65.8 |
| Cesta renovável RS | RB | 568.0 | 74016.9 | 34.2 |
| Cesta fóssil RS | RS | 1373.2 | 277141.4 | 77.8 |
| Cesta fóssil RS | RB | 747.3 | 78904.3 | 22.2 |

*Nota: choques de R$ 1.000 milhões na demanda final do RS; RB = Restante do Brasil.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 4:** Sensibilidade dos resultados à composição dos vetores de choque

*Painel A — MIP com o S38 desagregado (versão final)*

| Cenário | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Emissões indiretas (%) | Emissões no RB (%) |
|---|---:|---:|---:|---:|---:|
| Renovável base | 1845.2 | 95371.0 | 51.7 | 77.7 | 54.0 |
| Renovável balanceada | 1857.0 | 149558.1 | 80.5 | 52.9 | 33.8 |
| Renovável infraestrutura-intensiva | 1912.2 | 108198.6 | 56.6 | 80.4 | 57.4 |
| Renovável energia/transporte-intensiva | 1788.1 | 128646.3 | 71.9 | 50.7 | 31.2 |
| Fóssil base | 1997.1 | 2026202.2 | 1014.6 | 4.2 | 2.7 |
| Fóssil balanceada | 1992.9 | 1972315.4 | 989.7 | 4.4 | 2.6 |
| Fóssil energia-intensiva | 1897.5 | 2761423.7 | 1455.3 | 2.6 | 1.7 |

*Painel B — MIP original*

| Cenário | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Emissões indiretas (%) | Emissões no RB (%) |
|---|---:|---:|---:|---:|---:|
| Renovável base | 1959.4 | 216407.0 | 110.4 | 51.5 | 34.2 |
| Renovável balanceada | 1920.4 | 216987.2 | 113.0 | 46.1 | 29.1 |
| Renovável infraestrutura-intensiva | 1969.2 | 169090.0 | 85.9 | 62.7 | 43.5 |
| Renovável energia/transporte-intensiva (a) | 1959.5 | 309794.9 | 158.1 | 39.0 | 23.8 |
| Fóssil base | 2120.6 | 356045.7 | 167.9 | 35.3 | 22.2 |
| Fóssil balanceada | 2110.5 | 381702.9 | 180.9 | 32.9 | 19.7 |
| Fóssil energia-intensiva | 2073.9 | 375427.3 | 181.0 | 35.0 | 21.5 |

*Nota: choques de R$ 1.000 milhões na demanda final do RS; vetores na Tabela A1.*
*(a) Vetor da Tabela A1 (45/15/10/10/15/5).*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 5:** Sensibilidade à tecnologia atribuída ao S38

*Painel A — MIP com o S38 desagregado (versão final)*

| Cenário | Atribuição do S38 | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Emissões indiretas (%) | Emissões no RB (%) |
|---|---|---:|---:|---:|---:|---:|
| Renovável base | Geração eólica 100% (principal) | 1845.2 | 95371.0 | 51.7 | 77.7 | 54.0 |
| Renovável base | Geração eólica 50% + solar 50% | 1839.8 | 95171.6 | 51.7 | 77.7 | 54.0 |
| Renovável base | Geração eólica 2/3 + transmissão 1/3 | 1822.9 | 95139.9 | 52.2 | 77.6 | 53.9 |
| Renovável balanceada | Geração eólica 100% (principal) | 1857.0 | 149558.1 | 80.5 | 52.9 | 33.8 |
| Renovável balanceada | Geração eólica 50% + solar 50% | 1854.0 | 149447.3 | 80.6 | 52.8 | 33.7 |
| Renovável balanceada | Geração eólica 2/3 + transmissão 1/3 | 1844.6 | 149429.7 | 81.0 | 52.8 | 33.7 |
| Renovável infraestrutura-intensiva | Geração eólica 100% (principal) | 1912.2 | 108198.6 | 56.6 | 80.4 | 57.4 |
| Renovável infraestrutura-intensiva | Geração eólica 50% + solar 50% | 1909.6 | 108098.9 | 56.6 | 80.3 | 57.4 |
| Renovável infraestrutura-intensiva | Geração eólica 2/3 + transmissão 1/3 | 1901.1 | 108083.1 | 56.9 | 80.3 | 57.4 |
| Renovável energia/transporte-intensiva | Geração eólica 100% (principal) | 1788.1 | 128646.3 | 71.9 | 50.7 | 31.2 |
| Renovável energia/transporte-intensiva | Geração eólica 50% + solar 50% | 1780.0 | 128347.2 | 72.1 | 50.6 | 31.0 |
| Renovável energia/transporte-intensiva | Geração eólica 2/3 + transmissão 1/3 | 1754.7 | 128299.7 | 73.1 | 50.4 | 30.9 |
| Fóssil base | Carvão mineral e gás natural ∝ VBP (principal) | 1997.1 | 2026202.2 | 1014.6 | 4.2 | 2.7 |
| Fóssil base | Geração a carvão mineral 100% | 1976.7 | 2114151.8 | 1069.5 | 3.9 | 2.5 |
| Fóssil base | Geração a gás natural 100% | 2285.7 | 778840.7 | 340.7 | 13.0 | 9.6 |
| Fóssil balanceada | Carvão mineral e gás natural ∝ VBP (principal) | 1992.9 | 1972315.4 | 989.7 | 4.4 | 2.6 |
| Fóssil balanceada | Geração a carvão mineral 100% | 1973.5 | 2056076.9 | 1041.8 | 4.1 | 2.5 |
| Fóssil balanceada | Geração a gás natural 100% | 2267.8 | 784352.0 | 345.9 | 13.1 | 9.1 |
| Fóssil energia-intensiva | Carvão mineral e gás natural ∝ VBP (principal) | 1897.5 | 2761423.7 | 1455.3 | 2.6 | 1.7 |
| Fóssil energia-intensiva | Geração a carvão mineral 100% | 1868.4 | 2887066.0 | 1545.2 | 2.4 | 1.5 |
| Fóssil energia-intensiva | Geração a gás natural 100% | 2309.9 | 979478.6 | 424.0 | 9.9 | 7.6 |

*Nota: choques de R$ 1.000 milhões na demanda final do RS. A atribuição muda só a parcela do S38 de cada cesta; os demais setores do vetor não mudam. Solar: subsetor sem produção no RS em 2019 (latente), com os coeficientes técnicos do RB e a TUST do RS.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 6:** Emissões por tecnologia de geração do RS

*Painel A — MIP com o S38 desagregado (versão final)*

| Tecnologia | Preço médio (R$/MWh) | Produção induzida por TWh (R$ milhões) | Emissões diretas por TWh (t CO₂e) | Emissões indiretas por TWh (t CO₂e) | Emissões totais por TWh (t CO₂e) | g CO₂e/kWh | Emissões no RB (%) | Emissões por R$ 1 bilhão (t CO₂e) | Emissões evitadas por TWh em relação ao carvão (t CO₂e) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Hidrelétrica | 175.3 | 272.3 | 0.0 | 4627.1 | 4627.1 | 4.6 | 54.8 | 26391.5 | 1437533.4 |
| Eólica | 182.4 | 281.6 | 0.0 | 4787.8 | 4787.8 | 4.8 | 54.7 | 26246.9 | 1437372.7 |
| Solar fotovoltaica | 200.8 | 302.8 | 0.0 | 5003.3 | 5003.3 | 5.0 | 53.0 | 24917.7 | 1437157.3 |
| Biomassa | 217.1 | 340.3 | 49.5 | 8759.6 | 8809.0 | 8.8 | 68.9 | 40583.5 | 1433351.5 |
| Gás natural | 280.5 | 672.4 | 436436.9 | 22581.7 | 459018.6 | 459.0 | 4.7 | 1636355.7 | 983141.9 |
| Carvão mineral | 264.5 | 400.5 | 1434683.4 | 7477.1 | 1442160.5 | 1442.2 | 0.3 | 5451530.5 | 0.0 |
| Distribuição (eletricidade da rede, mix de 2019) |  |  |  |  |  |  |  | 387680.1 |  |

*Nota: Choque de 1 TWh (ao preço médio de 2019) e de R$ 1 bilhão na demanda final de cada subsetor de geração do RS. Emissões da operação (produção de energia elétrica); não incluem bens de capital (implantação das usinas). Solar: subsetor sem produção no RS em 2019 (latente), com os coeficientes técnicos do RB e a TUST do RS.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 7:** Efeito da desagregação: MIP original, S38 desagregado sem e com atribuição de tecnologia

*Parte 1 — Emissões totais*

| Cenário | Emissões A0 (t CO₂e) | Emissões A1 (t CO₂e) | Emissões A2 (t CO₂e) | Variação A1/A0 (%) | Variação A2/A0 (%) |
|---|---:|---:|---:|---:|---:|
| Energia elétrica agregada | 428113.5 | 383253.7 | 383253.7 | -10.5 | -10.5 |
| Renovável base | 216407.0 | 202473.0 | 95371.0 | -6.4 | -55.9 |
| Renovável balanceada | 216987.2 | 209059.2 | 149558.1 | -3.7 | -31.1 |
| Renovável infraestrutura-intensiva | 169090.0 | 161749.6 | 108198.6 | -4.3 | -36.0 |
| Renovável energia/transporte-intensiva | 309794.9 | 289299.3 | 128646.3 | -6.6 | -58.5 |
| Fóssil base | 356045.7 | 340254.9 | 2026202.2 | -4.4 | 469.1 |
| Fóssil balanceada | 381702.9 | 366651.4 | 1972315.4 | -3.9 | 416.7 |
| Fóssil energia-intensiva | 375427.3 | 352927.6 | 2761423.7 | -6.0 | 635.5 |

*Parte 2 — Intensidade carbônica, emissões indiretas e emissões no RB*

| Cenário | Intensidade A0 (t CO₂e/R$ milhão) | Intensidade A2 (t CO₂e/R$ milhão) | Emissões indiretas A0 (%) | Emissões indiretas A2 (%) | Emissões no RB A0 (%) | Emissões no RB A2 (%) |
|---|---:|---:|---:|---:|---:|---:|
| Energia elétrica agregada | 222.4 | 200.9 | 34.9 | 66.0 | 20.7 | 26.0 |
| Renovável base | 110.4 | 51.7 | 51.5 | 77.7 | 34.2 | 54.0 |
| Renovável balanceada | 113.0 | 80.5 | 46.1 | 52.9 | 29.1 | 33.8 |
| Renovável infraestrutura-intensiva | 85.9 | 56.6 | 62.7 | 80.4 | 43.5 | 57.4 |
| Renovável energia/transporte-intensiva | 158.1 | 71.9 | 39.0 | 50.7 | 23.8 | 31.2 |
| Fóssil base | 167.9 | 1014.6 | 35.3 | 4.2 | 22.2 | 2.7 |
| Fóssil balanceada | 180.9 | 989.7 | 32.9 | 4.4 | 19.7 | 2.6 |
| Fóssil energia-intensiva | 181.0 | 1455.3 | 35.0 | 2.6 | 21.5 | 1.7 |

*Nota: A0 = MIP original; A1 = MIP desagregada, com o S38 do vetor repartido entre distribuição e gás canalizado pela composição da demanda final; A2 = MIP desagregada, com o S38 atribuído a tecnologias (Quadro 1). Na energia elétrica agregada, A1 e A2 coincidem.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

## 19. Diagnóstico NEREUS × SEEG e variante E4

Script: `scripts/rodada05_diagnostico_seeg.py`. Saídas:
- `resultados/rodada05/diagnostico_seeg_nereus.xlsx`, com as abas LEIAME, componentes_S38, metricas, casamentos_RS, unidades_RS e resumo;
- o recorte `dados/externos/seeg/seeg13_2019_recorte_energia_v04.csv`;
- os valores da E4 em `dados/externos/seeg/seeg13_2019_componentes_e4_v04.csv`.

O diagnóstico não muda a versão principal.

### 19.1 Reprodução da tabela da Seção 3 (SEEG 13.0, 2019, GWP-AR5, mil t CO₂e)

| Componente (Atividade geral › Categoria › Sub-categoria) | RS | RB (estados) | Não alocado |
|---|---|---|---|
| Geração de eletricidade › serviço público | 3842.55 | 34181.13 | 343.99 |
| Geração de eletricidade › demais categorias (autoprodução) | 96.48 | 2094.36 | 4833.44 |
| Geração de eletricidade › Produção de combustíveis › Refino de petróleo | 76.11 | 759.73 | 496.34 |
| Geração de eletricidade › Produção de combustíveis › Exploração de petróleo e gás natural | 0 | 5778.19 | 0 |
| Geração de eletricidade › Produção de combustíveis › Produção de álcool | 0 | 0 | 412.44 |
| Produção de combustíveis › Refino de petróleo | 1735.95 | 17329.14 | 7053.49 |
| Produção de combustíveis › Exploração de petróleo e gás natural | 0 | 17721.00 | 53.42 |
| Produção de combustíveis › Produção de carvão mineral e outros | 88.13 | 1155.40 | 355.60 |
| Produção de combustíveis › demais | 0 | 0 | 5151.24 |
| **Soma das duas atividades** | **5839.22** | **79018.95** | **18699.96** |
| **S38 na base NEREUS** | **5838.01** | **84518.35** | — |

- Todas as células conferem com as das instruções; a maior diferença é de 0.05 mil t, de arredondamento.
- A soma contra a NEREUS dá +0.021% no RS e −6.51% no RB (estados).
- Não há linhas "Emissão NCI" nessas duas atividades, e todas são do setor "Energia" do SEEG.
- O refino do RB na E4 é 18088.87 mil t. A instrução dá 18088.8 porque soma as parcelas já arredondadas (17329.1 + 759.7).

### 19.2 Outras métricas

As bases seguem a convenção do próprio SEEG: bruta = "Emissão"; líquida = "Emissão" + "Remoção". As versões com NCI ficam como variantes. "Total Brasil" = 27 UF + "Não alocado"; o Bunker fica fora, salvo numa sensibilidade.

- **S38-RS:** a GWP-AR5 é a que mais se aproxima, com +0.02%. As outras: GWP-AR2 −0.47%, AR4 −0.18%, AR6 +0.16%, GTP de −1.5% a −1.8%.
- **S38-RB (estados):** nenhuma métrica fecha. A mais perto é a GWP-AR6, com −6.15% (AR5: −6.51%).
- **Total RS** (GWP-AR5): bruta +18.3%, líquida −0.7%. Com NCI: +22.8% e −14.7%.
- **Total Brasil** (GWP-AR5): bruta +36.5%, líquida +1.0%. Com NCI: +46.6% e −1.9%. Só com as UF, a líquida dá −2.6%.
- A mais perto nos totais é a GWP-AR6 líquida: RS −0.57% e Brasil +0.50%.
- Com cerca de 8 métricas × 5 bases × 2 escopos, coincidências abaixo de 1% são fáceis. A "métrica mais perto" vale só dentro das bases testadas.

### 19.3 Casamento de outros setores do RS

**Espaço de busca:** somas de 1, 2 ou 3 unidades do SEEG do RS, do mesmo tipo:
- "Atividade geral";
- "Setor › Categoria";
- "Atividade › Categoria › Sub-categoria".

São 84982 combinações por setor × 8 setores (S01, S02, S03, S19, S26, S39, S43 e o S38 como controle): **679856 testes**.

**Resultado:**
- **224 combinações** ficam abaixo de 0.1% (126 núcleos distintos, sem as unidades desprezíveis). Por acaso, seriam esperadas cerca de 211; é só ordem de grandeza.
- Pelo critério do SCN, aplicado a todos os setores do mesmo jeito: 0 com sentido econômico, 9 "discutíveis" (todas com mudança de uso da terra, no S01) e 215 sem sentido.
- O "sentido econômico" é uma classificação do diagnóstico (HIPÓTESE), registrada na aba unidades_RS.
- A combinação do S38 que é a hipótese em teste (geração de eletricidade + produção de combustíveis) fica marcada à parte como "formulada antes da busca". Pelo critério do SCN, ela não tem sentido econômico: o refino é do S19 e o carvão mineral do S04.
- No controle S38, a combinação mais exata não tem sentido econômico: energia na agropecuária + serviço público + residencial, com +0.001%.
- O teste direto "atividade do SEEG → setor da MIP" não repete o padrão do S38. A diferença contra a NEREUS é de +115% no S01, −11.2% no S02, −32.3% no S19, −37.4% no S26, −18.3% no S39 e −11.6% no S43.
- **Casamento concorrente:** S19-RS ≈ Refino + Química, com +0.071%. Ele usa as mesmas emissões do refino, e as duas leituras se excluem.
- Se o refino estiver no S38, as 2693.9 mil t do S19-RS na NEREUS ficam sem contrapartida no SEEG do RS. As únicas unidades de refino no RS são as duas da hipótese (1812.1 mil t).

### 19.4 Conclusão (cautelosa)

O S38-RS da base NEREUS (5838.0 mil t) é **compatível com** a soma "Geração de eletricidade" + "Produção de combustíveis" do SEEG 13.0 em GWP-AR5 (5839.2 mil t, +0.021%). É um **indício**, e fraco, pelos motivos abaixo:
- não temos a documentação da conta-satélite;
- o RB não fecha pelo mesmo critério (−6.51%);
- os totais do RS e do Brasil só se aproximam conforme a base e o escopo escolhidos;
- com 679856 combinações, coincidências abaixo de 0.1% são esperadas, e os outros setores do RS não repetem o padrão;
- há um casamento concorrente para o S19 que usa as mesmas emissões.

A combinação do S38 ganha peso só por ter sido formulada antes da busca. Nada aqui permite dizer o que a NEREUS fez.

### 19.5 Variante E4

**Valores movidos** (mil t CO₂e; `parametros/realocacao_emissoes_v04_E4.csv`):

| Região | Para S19 (refino) | Para S04 (carvão mineral) | Para S05 (petróleo e gás) | Total | Resíduo E1 | Sobra em DIS e GAS |
|---|---|---|---|---|---|---|
| RS | 1812.1 | 88.1 | — | 1900.2 | 1975.9 | 75.7 |
| RB | 18088.9 | 1155.4 | 23499.2 | 42743.5 | 49689.7 | 6946.3 |

Os valores saem de DIS e GAS na proporção do resíduo de cada um, sem mexer no SF₆. As instruções falavam em "cerca de 93 e 7220" de sobra; a diferença é o SF₆, que na E1 é nível identificado (19.6 mil t no RS e 303.5 no RB).

O T14 passa: valores movidos exatos, total da economia inalterado, S38 reduzido no valor movido e nenhuma emissão negativa. O T2 da E4 vale só pelo total, como o da E3.

**Efeito da E4 em relação à E1 (A2, v04):**
- Energia elétrica agregada: −31.2%.
- Cesta renovável: +1.8%; cesta fóssil: +2.2%; demais cestas: de +1.3% a +2.9%.
- Cesta fóssil com 100% gás natural: +8.5%.
- Por TWh: EOL, HID e GN +4.2%; BIO +2.8%; SOL +1.2%; CAR 0.0%.

**A0_E4** (a mesma realocação na MIP original, contra o A0):

| Cenário | E1 | R1 | F1 | R2 | R3 | R4a | R4b | F2 | F3 |
|---|---|---|---|---|---|---|---|---|---|
| Variação das emissões | −31.3% | −18.0% | −1.4% | −8.7% | −11.1% | −18.5% | −21.3% | −1.9% | −9.4% |

**Risco de dupla contagem:** na E4, o S19-RS passa de 2693.9 para 4506.0 mil t (2693.9 + 1812.1). Se as 2693.9 mil t da NEREUS já incluírem o refino, a E4 conta o refino duas vezes. Por isso a E4 só deve ser lida como sensibilidade (D21).

## 20. Material do artigo

Tudo foi gerado por `scripts/rodada05_artigo.py`, sem número digitado à mão. Os números dos textos vêm de `artigo/texto/numeros_chave.json`, cada um com a origem (arquivo › aba › linha). No material do artigo, os números estão no padrão brasileiro.

| Arquivo | O que é |
|---|---|
| `artigo/tabelas/tabelas_artigo.xlsx` | As 16 tabelas (Quadro 1, Tabelas 1–7 e A1–A8), uma por aba |
| `artigo/tabelas/tabelas_artigo.docx` | As mesmas no formato pedido: A4, margens de 2.5 cm, Times New Roman 8 nas tabelas, cabeçalho em negrito, bordas de 0.5 pt, título acima, fonte e notas abaixo em itálico 10 |
| `artigo/tabelas/tabelas_artigo.md` | As mesmas em Markdown |
| `artigo/figuras/figura_1_top10_cesta_renovavel` | Figura 1: os 10 maiores emissores da cesta renovável (A2) |
| `artigo/figuras/figura_2_diretas_indiretas` | Figura 2: participação das emissões diretas e indiretas, MIP original (A0) × desagregada (A2) |
| `artigo/figuras/figura_3_emissoes_por_TWh` | Figura 3: emissões por TWh de cada tecnologia do RS, diretas e indiretas |
| `artigo/figuras/figura_4_emissoes_por_cesta` | Figura 4: emissões totais por cesta, MIP original (A0) × desagregada (A2) |
| `artigo/figuras/figura_A1_top10_cesta_renovavel_original` | Figura A1: os 10 maiores emissores da cesta renovável na MIP original |
| `artigo/texto/secao_3x_desagregacao.md` e `.docx` | (a) Subseção 3.x: 1331 palavras sem as equações e sem o Quadro 2; Equações (15) a (29); cita Wolsky (1984), Lenzen (2011), Lindner, Legault e Guan (2012; 2013), Peters (2016), Lahr e de Mesnard (2004) e Miller e Blair (2022) |
| `artigo/texto/apendice_B_nota_tecnica.md` e `.docx` | (b) Apêndice B: B.1 a B.14, Equações (B.1) a (B.37), remetendo às Tabelas A3 a A8 |
| `artigo/texto/limitacoes.md` e `.docx` | (c) 9 parágrafos curtos, na ordem da Seção 5.3 |
| `artigo/texto/numeros_chave.md`, `.docx` e `.json` | (d) 379 números, cada um com o valor bruto, o padrão brasileiro, a unidade e a origem |
| `artigo/texto/referencias.md` e `.docx` | (e) Referências em ABNT, conferidas no Crossref ou na própria fonte; 3 marcadas [CONFERIR] |
| `artigo/texto/modelos/*.md` | Os modelos dos quatro textos, com `{{chave}}` no lugar dos números |
| `resultados/rodada05/tabelas_artigo_ponto_decimal.md` | As tabelas em ponto decimal, para este relatório (Seção 18) |

PNG em 300 dpi e PDF, 7 × 4.4 polegadas, cores #2c6e9e e #da7e2e, sem título interno e com vírgula decimal.

**Para editar um texto:** mude o modelo em `artigo/texto/modelos/` e rode `python scripts/rodada05_artigo.py`. O script troca os números e refaz o `.md` e o `.docx`. Uma edição feita direto no `.docx` se perde na próxima execução.

**Equações:** no `.docx`, são equações nativas do Word, geradas pelo pandoc. Convertido de volta para Markdown, o `.docx` devolve todas as equações. A prévia em PDF do LibreOffice deste ambiente não desenha equações, nem num `.docx` saído direto do pandoc. Vale abrir no Word para conferir.
