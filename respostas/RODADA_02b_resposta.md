# Rodada 02b — Relatório do Claude Code

Projeto: desagregação do S38 na MIP inter-regional RS × RB, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
Data: 15/10/2026 · Instruções: `instrucoes/RODADA_02b_instrucoes_CODE.md` (sobre `instrucoes/RODADA_02_instrucoes_CODE.md`) · Rodada anterior: `respostas/RODADA_02_resposta.md`
Convenção numérica: ponto decimal, sem separador de milhar.

Decisões aplicadas: D1 = C (11 subsetores); D2, D3, D4 e D6 = A; D5 = E1 (E2 e E3 como sensibilidades); D7 = A.
Respostas da Seção 1 aplicadas: excedente do teto do S05 → GAS (`sem_teto`); S03 + S09 com teto comum (`grupo_teto`); SF6 entre TRA e DIS na proporção do VBP; usina "Sol" fora do S38; D3-A mantida (a âncora define o total e o GWh × preço só reparte).

## 1. Resumo

- **Rede:** o teste da Seção 0 deu 200 em ANEEL, SIDRA, SEEG, EPE, gov.br e Comex Stat (19:27 UTC). A rodada foi até o fim: Etapas 2, 4, 5, 6a, 6b e 7.
- **Usinas de autoprodução fora do S38 (Seção 2):** as 7 usinas "Resíduos Industriais" saem da geração. São 9440.4 GWh no RB e 72.7 GWh no RS. As novas referências do ONS conferem: **20/20**.
- **Sistemas isolados (Seção 3):** o Anuário 2020 não traz a geração dos isolados por fonte. Usei a opção 2, o BEN 2020 (Tabela 5.4): PET-RB = 3506 (diesel) + 1263 (óleo combustível) = **4769 GWh**, isto é, ONS 1974.3 + isolados 2794.7. Com isso, o fator do PET-RB cai de 2.17 para **0.90 t CO₂e/MWh**.
- **Referências:** **101/102 conferem.** A única divergência é o preço da BIO (206.05 contra 203.0 R$/MWh), que já estava no relatório da 2b-E2 (Seção 14).
- **Parâmetros** (`parametros/*_v01`, com fonte em cada linha):
  - RAP 2019 = 24883.4 R$ mi. É a média do ciclo 2018-2019 (24066.9, ANEEL, primária) com o 2019-2020 (25700, **fonte secundária, não confirmada**).
  - θ_RS = 0.051 (fallback de 0.20 m³/kWh) e θ_RB = 0.431 (MME).
  - VBP do GAS: RS = 898.7 R$ mi (receita líquida da Sulgás); RB = 13539.8 R$ mi (fallback ÷ 0.75).
  - Importações: 44.3% são energia elétrica (Comex Stat).
  - Angra: 247.47 R$/MWh, confirmado na REH 2.509/2018. TUST 50/50: confirmada na REN 559/2013.
  - Consumo específico das térmicas e gás por comprador: do BEN 2020.
- **MIP v01** (P1 + E1) e variantes P2, E2 e E3:
  - A re-agregação é exata, e o **T2 com a especificação real passa nas 4**.
  - Em cada uma: 30 checagens OK e 1 ALERTA. O ALERTA é **EOB negativo**, sinalizado e não corrigido, em GN-RB (−4115), GAS-RB (−1519), GAS-RS (−580), PET-RB (−161) e GN-RS (−36).
  - Os fatores de emissão ficam dentro das faixas: CAR-RS 1.43, CAR-RB 0.86, GN 0.44, PET-RB 0.90 e BIO ≈ 0.
- **Quadro por subsetor** (`resultados/rodada02/quadro_subsetores_v01.xlsx`) e **prévia** (marcada "PRÉVIA") gerados.
- **327 testes passam**: os 322 da Rodada 02, mais 4 casos do T2 com a especificação real e 1 teste da especificação real.
- **Decisões que ficam com você** (Seção 10):
  - os EOB negativos. Há duas sensibilidades que mostram de onde vêm: as importações de gás no RS e o fallback do VBP do GAS-RB;
  - a RAP 2019-2020, que segue com fonte secundária.

## 2. Status por etapa

| Etapa | Status | Observação |
|---|---|---|
| 0 — Teste rápido de rede (02b) | concluída | 6/6 domínios com 200 (`dados/externos/rodada02b_teste_rede.csv`) |
| E2 — Coletar e tratar as fontes 5.2–5.10 | concluída | Leitores validados com os arquivos reais; 101/102 referências; Seções 2 e 3 da 02b aplicadas; fontes documentais (RAP, gás, Angra, TUST) lidas e conferidas no documento |
| E3 — Motor | concluída (Rodada 02) | Sem mudança no motor nesta rodada |
| E4 — Parâmetros reais | concluída | `scripts/rodada02_parametros.py` → `parametros/especificacao_v01*.yaml`, `parametros/*_v01.csv`, `parametros/quadro_parametros_v01.xlsx` |
| E5 — MIP v01 + variantes | concluída, com ALERTA | 4 MIPs; todas re-agregam exatamente; EOB negativo em 5 subsetores (Seção 10, ponto 1) |
| E6a — Quadro por subsetor | concluída | `resultados/rodada02/quadro_subsetores_v01.xlsx` |
| E6b — Prévia (opcional) | concluída | `resultados/rodada02/previa_multiplicadores_v01.xlsx`, marcada "PRÉVIA — NÃO É RESULTADO DO ARTIGO" |
| E7 — Relatório | concluída | Este arquivo; `HISTORICO.md` e `README.md` atualizados |

## 3. Arquivos criados, movidos ou alterados

| Caminho | Tipo | O que é | Etapa |
|---|---|---|---|
| `instrucoes/RODADA_02b_instrucoes_CODE.md` | texto | Cópia das instruções da 02b | 0 |
| `dados/externos/rodada02b_teste_rede.csv` | registro | Teste da Seção 0 (URL, status, tempo, horário) | 0 |
| `dados/externos/{siga,leiloes,ipca,cempre,seeg}/…` | dados + `DOWNLOAD.txt` | Fontes 5.2, 5.4, 5.7 e 5.8 baixadas (commit `4e8568a`); SEEG bruto (185 MB) fora do git, recorte versionado | E2 |
| `dados/externos/ons/reclassificacao_usinas_v01.csv` | dado (método, alterado) | Coluna nova `tratamento`; 7 usinas `excluir_autoproducao` com GWh e motivo; Canoas → GN | E2 |
| `src/mip/externos/ons.py`, `src/mip/externos/seeg.py` | código (alterado, commit `4e8568a`) | Usinas fora do S38 (`FORA_S38`), referências da 02b; rótulo "Carvão mineral sem especificação" do SEEG 13.0 | E2 |
| `dados/externos/epe/` | dados | Anuário 2020 (xlsx), BEN 2020 (matriz xlsx e PDF), `ben2020_tabela_5_4_v01.csv` (transcrição da Tabela 5.4), `sistemas_isolados_2019_v01.csv`, `DOWNLOAD.txt` | E2 |
| `dados/externos/aneel_rap/` | dados | REH 2.565/2019 (DOU), recorte das atas da Diretoria (RAP 2018-2019), voto CEEE-GT, REN 559/2013, REH 2.509/2018 (Angra), ONS SEAMSE dez/2019, CAGE (CEEE-GT); `DOWNLOAD.txt` | E2 |
| `dados/externos/gas/` | dados | Boletins do gás do MME (dez/2019 e dez/2020); `DOWNLOAD.txt` (DF da Sulgás, ANP e CVM ficam em `brutos/`, fora do git) | E2 |
| `dados/externos/comex/` | dados | Respostas da API do Comex Stat (por NCM e por NCM × UF) + requisições | E2 |
| `dados/externos/valores_documentais_v01.csv` | dado | 22 números lidos de documentos: valor, unidade, documento, página, URL, arquivo, SHA-256, data, primária ou não | E2/E4 |
| `dados/externos/FONTES.md` | documentação (alterado) | Fontes da 02b e o que não foi acessado | E2 |
| `scripts/rodada02.py` | script (alterado) | + sistemas isolados (método "nacional − ONS"), BEN (gás por setor, consumo específico, consistência), reconciliação EPE | E2 |
| `dados/intermediarios/geracao_2019_usina_v02.csv`, `geracao_2019_regiao_subsetor_v02.csv` | dado derivado | Geração sem autoprodução + linha dos isolados | E2 |
| `dados/intermediarios/precos_2019_*_v01.csv`, `cempre_2019_composicao_v01.csv`, `seeg_2019_emissoes_v01.csv`, `siga_divergencias_ons_v01.csv` | dado derivado | Preços, CEMPRE, SEEG, divergências ONS × SIGA (commit `4e8568a`) | E2 |
| `dados/intermediarios/ben_2019_gas_natural_por_setor_v01.csv`, `ben_2019_consumo_especifico_v01.csv` | dado derivado | BEN 2020: gás por setor (mil tep); consumo específico das centrais de serviço público | E2 |
| `resultados/rodada02/comparacao_referencias_v02.csv`, `situacao_fontes_v02.csv`, `reconciliacao_epe_v01.csv` | resultado | Referências (102 itens); situação das fontes; Seção 4 da 02b | E2 |
| `scripts/rodada02_parametros.py` | script | Etapa 4 | E4 |
| `parametros/especificacao_v01.yaml` (+ `_P2`, `_E2`, `_E3`) e `parametros/*_v01.csv`, `correspondencia_ben_mip_v01.csv`, `quadro_parametros_v01.xlsx` | parâmetros | Especificação real (todas as linhas com `fonte`) | E4 |
| `parametros/LEIAME_parametros.md` | documentação (alterado) | Lista dos parâmetros reais | E4 |
| `scripts/rodada02_mip.py` | script | Etapas 5 e 6 | E5/E6 |
| `resultados/rodada02/MIP_RS_RB_2019_S38_11sub_v01*.xlsx` e `_longo.csv` | resultado | MIP v01 e variantes (layout da original + formato longo) | E5 |
| `resultados/rodada02/checagens_v01.csv` | resultado | Todas as checagens das 4 versões | E5 |
| `resultados/rodada02/quadro_subsetores_v01.xlsx` | resultado | Quadro por subsetor (Etapa 6a) | E6a |
| `resultados/rodada02/previa_multiplicadores_v01.xlsx` | resultado (PRÉVIA) | Multiplicadores do RS e 9 cenários na v01 | E6b |
| `tests/test_especificacao_real_v01.py` | teste | T2 com a especificação real (4 variantes) + geração e TRA só no bloco | E5 |
| `tests/test_desagregacao_r02.py` | teste (alterado) | Só o comentário que apontava o T2 real como pendente | E5 |
| `respostas/RODADA_02b_resposta.md`, `respostas/HISTORICO.md`, `README.md` | documentação | Este relatório; histórico; status | E7 |

Movidos para `dados/externos/brutos/` (fora do git): o CSV completo das atas da ANEEL (19 MB), as DFP da CVM (Comgás, CEG, Gasmig) e uma cópia da matriz do BEN, idêntica à de `epe/`, que foi removida. O `RODADA_02_resposta.md` e as saídas `_v01` da Rodada 02 não foram alterados.

## 4. Validação da MIP original

Sem mudança: o T1 (SHA-256 `15e734a4…a3ea`) e as identidades da Rodada 01 continuam passando.

## 5. Reprodução dos resultados

- Os 9 cenários da Rodada 01 continuam reproduzidos na MIP original (`tests/test_replicacao.py`).
- **Prévia na v01 (PRÉVIA, não é resultado do artigo).** O choque que ia ao S38 foi repartido entre DIS (96.8%) e GAS (3.2%), na proporção das vendas do S38-RS à demanda final. Isso mede só o efeito da desagregação, sem remapear as cestas para tecnologias:

| Cenário | ΔX total (original → v01) | CO₂e total (t) | Diferença CO₂e |
|---|---|---|---|
| E1 | 1925.0 → 1903.9 | 428113.5 → 381676.9 | −10.8% |
| R1 | 1959.4 → 1953.5 | 216407.0 → 202090.3 | −6.6% |
| F1 | 2120.6 → 2113.2 | 356045.7 → 339717.7 | −4.6% |
| R2 | 1920.4 → 1917.2 | 216987.2 → 208874.0 | −3.7% |
| R3 | 1969.2 → 1966.7 | 169090.0 → 161630.1 | −4.4% |
| R4a | 1959.5 → 1950.2 | 309794.9 → 288643.7 | −6.8% |
| R4b | 1950.5 → 1940.2 | 304336.6 → 280872.7 | −7.7% |
| F2 | 2110.5 → 2103.4 | 381702.9 → 366138.5 | −4.1% |
| F3 | 2073.9 → 2063.4 | 375427.3 → 352150.2 | −6.2% |

As emissões caem porque o choque, que antes ia ao S38 médio, agora vai à DIS. As emissões diretas da DIS são só o resíduo E1 e o SF6; as térmicas entram pelo efeito indireto. Os multiplicadores de emissão do RS (t CO₂e por R$ mi de demanda final) são: CAR 5601, PET (latente) 4510, GN 1814, DIS 387, GAS 225, BIO 41, HID e EOL 25, TRA 22. O S38 agregado original é 428.

## 6. Diagnóstico do S38

Quadro por subsetor da v01 (P1 + E1). O quadro completo, com ocupações, remunerações, CI/VBP e os 5 maiores insumos, está em `quadro_subsetores_v01.xlsx`.

| Região | Subsetor | VBP (R$ mi) | % do S38 | GWh | R$/MWh | CO₂e E1 (t) | t/MWh | EOB/VBP |
|---|---|---|---|---|---|---|---|---|
| RS | HID | 2481.2 | 11.85 | 14542.6 | 170.6 | 0 | 0 | 0.52 |
| RS | EOL | 935.0 | 4.46 | 5266.9 | 177.5 | 0 | 0 | 0.52 |
| RS | BIO | 14.4 | 0.07 | 68.2 | 211.2 | 3.4 | 0.0000 | 0.49 |
| RS | CAR | 675.8 | 3.23 | 2625.2 | 257.4 | 3766365 | 1.435 | 0.49 |
| RS | GN | 44.1 | 0.21 | 174.6 | 252.9 | 76185 | 0.436 | **−0.82** |
| RS | SOL, PET (latentes); NUC (zerado) | 0 | 0 | 0 | — | 0 | — | — |
| RS | TRA | 1509.1 | 7.21 | — | — | 1860 (SF6) | — | 0.72 |
| RS | DIS | 14384.3 | 68.68 | — | — | 1877402 | — | 0.29 |
| RS | GAS | 898.7 | 4.29 | — | — | 116189 | — | **−0.65** |
| RB | HID | 48737.6 | 15.02 | 370796.7 | 131.4 | 0 | 0 | 0.51 |
| RB | EOL | 6581.0 | 2.03 | 48122.9 | 136.8 | 0 | 0 | 0.51 |
| RB | SOL | 902.5 | 0.28 | 4384.6 | 205.8 | 0 | 0 | 0.51 |
| RB | BIO | 1508.8 | 0.47 | 9271.9 | 162.7 | 12196 | 0.001 | 0.50 |
| RB | CAR | 2248.7 | 0.69 | 11338.7 | 198.3 | 9708245 | 0.856 | 0.39 |
| RB | GN | 9054.1 | 2.79 | 46474.0 | 194.8 | 20513050 | 0.441 | **−0.45** |
| RB | PET | 979.2 | 0.30 | 4769.0 | 205.3 | 4291626 | 0.900 | **−0.16** |
| RB | NUC | 3152.2 | 0.97 | 16128.8 | 195.4 | 0 | 0 | 0.51 |
| RB | TRA | 23374.4 | 7.21 | — | — | 29847 (SF6) | — | 0.69 |
| RB | DIS | 214309.1 | 66.07 | — | — | 47010600 | — | 0.29 |
| RB | GAS | 13539.8 | 4.17 | — | — | 2952789 | — | **−0.11** |

Na E1, a DIS e o GAS levam o resíduo da base NEREUS (resíduo − SF6, ∝ VBP): 1975.9 mil t no RS e 49689.7 mil t no RB, ou seja, 34% e 59% da base. A DIS concentra a maior parte disso.

## 7. Motor de desagregação

O motor não mudou nesta rodada: é o da Rodada 02, com as correções da revisão adversarial. Tudo o que é novo está nos scripts e nos parâmetros. A especificação real usa:
- `roteamento_por_componentes` e `ancora_componentes`, com `subsetor_termica_gas: S38_GN`;
- RAS com tolerância 1e-8;
- `niveis.co2e` com resíduo para DIS e GAS.

**Testes** (`python -m pytest`: **327 passaram, 0 falharam**):

| Teste | Resultado | O que verifica |
|---|---|---|
| T1 | passou | Hash da original |
| T2 | passou: Rodada 01, 11 subsetores fictícios e **especificação real** (v01, P2, E2, E3) | Re-agregação exata de Z, F, X, V e da conta satélite. Na E3, todas as satélites menos CO₂e |
| T3–T8 | passaram | Como na Rodada 02 |
| Especificação real | passou | VBP ≥ 0; TRA, DIS e GAS > 0; geração e TRA não vendem fora do bloco |
| Leitores | passaram | Agora validados também com os arquivos reais (Seção 14) |

## 8. Acesso a fontes externas

| Fonte | Acessível? | O que foi baixado | Observação |
|---|---|---|---|
| Teste da Seção 0 (ANEEL, SIDRA, SEEG, EPE, gov.br, Comex) | sim, 200 | — | 19:27:24–19:27:33 UTC |
| ANEEL SIGA, leilões; IBGE SIDRA (IPCA, CEMPRE); SEEG | sim | ver `dados/externos/rodada02_acesso_fontes.csv` | SEEG bruto fora do git (185 MB) |
| EPE — Anuário 2020 e BEN 2020 | sim | xlsx e PDF | — |
| ANEEL — atas da Diretoria (dados abertos), DOU (in.gov.br) | sim | recorte das atas; páginas do DOU | — |
| ANEEL — biblioteca (`www2.aneel.gov.br/cedoc`) | **não** | — | Desafio anti-robô (Cloudflare, 403); também pelo Chromium. Não tentei contornar |
| CanalEnergia | **não** | — | Mesmo desafio anti-robô |
| Sulgás (`sulgas.rs.gov.br`) | **não** | — | Certificado TLS vencido. A DF da Sulgás veio da CAGE/Sefaz-RS |
| MME (boletim do gás), ANP (anuário), CVM (DFP), CAGE/Sefaz-RS, ONS (SEAMSE) | sim | ver `DOWNLOAD.txt` de cada pasta | — |
| Comex Stat (API) | sim (após 429) | JSON por NCM e por NCM × UF | 429 nas primeiras tentativas; deu certo ao repetir |

## 9. Decisões tomadas por você nesta rodada

| Decisão | Alternativas consideradas | Por quê |
|---|---|---|
| Sistemas isolados pela opção 2 (BEN): PET-RB = diesel + óleo combustível = 4769 GWh | Somar também o biodiesel (404 GWh, mistura do diesel) e "outras não renováveis" (405 GWh) | A instrução fala em "derivados de petróleo"; na Tabela 5.4, biodiesel é renovável e "outras não renováveis" não é só petróleo. Com os dois, o PET-RB iria a 5578 GWh e o fator a 0.77 |
| Registrar os isolados como "nacional − ONS (RS + RB)" no arquivo de dados | Gravar 2794.7 GWh fixos | Se o ONS mudar, o número acompanha; a regra fica explícita |
| RAP 2019 = média dos ciclos: 2018-2019 da ata oficial da ANEEL (24066.85) e 2019-2020 de 25700 (fonte secundária das instruções) | Só o 2019-2020 | A instrução manda a média quando o 2018-2019 aparece. O 2019-2020 oficial não foi achado (Seção 10, ponto 2) |
| θ_RS pelo fallback (GWh × 0.20 m³/kWh) sobre o volume da Sulgás sem o "Serviço" (transporte da REFAP) | Usar as vendas dos produtores no RS (ANP, 649 milhões m³) como denominador | O volume térmico do RS não existe por UF. A Sulgás sem serviço é o volume que ela compra; θ ficaria quase igual (0.054) |
| θ_RB = (geração elétrica − térmico RS) ÷ (distribuidoras − Sulgás + outros agentes − térmico RS), sem refinarias e Fafens | Incluir refinarias e Fafens | Refinarias e Fafens são consumo próprio da Petrobras, não compra do S38 |
| VBP do GAS-RB pelo fallback das instruções (÷ 0.75) | Estimar por volume × R$/m³ | Não há soma oficial; a alternativa vai como sensibilidade (Seção 10, ponto 1) |
| Gás por comprador pelo BEN, com a tabela `correspondencia_ben_mip_v01.csv` (HIPÓTESES marcadas). O setor energético fica fora; GNV → S43 e famílias (∝ compras ao S38); mesmo preço por tep; o GAS só vende na própria região | Fallback (S08–S37, S43 e famílias) | A instrução prefere o BEN. A estrutura da Sulgás confirma o perfil: indústria + cogeração 76.5%, automotivo 16.0% e residencial + comercial 6.5% da receita. No BEN sem o setor energético: indústria 77%, rodoviário 18% e residencial + comercial + público 5% |
| Consumo específico pelo BEN (Tabela 5.4); BIO = (lenha + biodiesel + outras renováveis) ÷ geração | Fallback (eficiências típicas) | A instrução prefere o BEN. A BIO do BEN de serviço público é pequena (1840 GWh), mas é a única fonte de serviço público por combustível |
| Importações: participação nacional do Comex (elétrica 44.3%) nas duas regiões | Usar a UF do importador | Por UF, quase toda a energia elétrica está como "Não Declarada"; o gás entra em MS, BA e CE e é revendido. A consequência no RS vai à Seção 10, ponto 1 |
| Preço da nuclear pela REH 2.509/2018 | Manter a fonte jornalística | Documento oficial achado; mesmo valor |
| Pesquisa documental com agentes e verificação cética; quando os verificadores pararam por limite de sessão, conferi cada número usado direto no documento | Usar sem conferência | Regra "nenhum dado inventado". Os 3 valores da CVM (Comgás, CEG, Gasmig) não foram reconferidos e não entram em parâmetro |
| Não contornar desafios anti-robô (ANEEL biblioteca, CanalEnergia) | Automatizar o navegador para passar | São barreiras de acesso dos sites |
| Brutos grandes ou não usados em `brutos/` (fora do git), com URL e SHA-256 no `DOWNLOAD.txt` | Versionar tudo que tem menos de 20 MB | O git só leva o que é usado e os recortes |
| EOB negativo **não corrigido** (só ALERTA) | Forçar o fechamento | Regra da Rodada 02 e resposta 6 da Seção 1 da 02b |

## 10. Pontos para o Francisco

1. **EOB negativo em 5 subsetores (decisão de método).** As causas são duas, e ambas vêm dos parâmetros, não do motor.

   **GAS.** As compras de gás do GAS passam do VBP.
   - No RS, a regra do Comex nacional manda 473.0 R$ mi de "gás importado" ao GAS-RS. Somados aos 642.4 do S05, o custo de gás passa a receita da Sulgás (898.7). O custo real de gás da Sulgás em 2019 foi ≈ 679 (Nota 22).
   - No RB, o VBP do fallback (13539.8) é baixo. Só Comgás + CEG + Gasmig (DFP 2019 na CVM, sem construção e sem o segmento térmico da CEG) somam ≈ 14200 R$ mi, para cerca de 60% do volume não térmico do RB. Esses três valores são do agente de pesquisa e não foram reconferidos; servem só de indício.

   **GN-RB.** A âncora (D3-A) dá 194.8 R$/MWh ao GN. As compras de gás atribuídas ao GN são 7687 R$ mi: θ × S05 = 4405 e θ × importações de gás = 3282. A isso somam-se TRA, impostos e salários.

   Sensibilidades, feitas fora dos resultados oficiais e não versionadas:

   | Variante de teste | GN-RS | GAS-RS | GN-RB | GAS-RB | PET-RB |
   |---|---|---|---|---|---|
   | v01 (oficial) | −36.1 | −580.2 | −4115.0 | −1518.9 | −161.1 |
   | importações do S38-RS só para DIS | −7.1 | −44.6 | −4115.0 | −1518.9 | −161.1 |
   | VBP do GAS-RB = R$/m³ da Sulgás (1.39) × volume não térmico do RB = 19421.0 | −36.1 | −580.2 | −4115.0 | **+3217.7** | −161.1 |

   Opções:
   - (a) importações do RS só para a DIS. Por UF, o RS quase não importa gás pelo Comex;
   - (b) VBP do GAS-RB por volume × preço documentado, no lugar do fallback de 0.25;
   - (c) teto comum para S05 + gás importado no GN (`grupo_teto`), com o excedente ao GAS;
   - (d) aceitar como está, com o ALERTA.

   Sem (c) ou uma revisão da âncora, o GN-RB continua negativo. Diga quais aplicar na próxima versão (v02).
2. **RAP do ciclo 2019-2020: só fonte secundária.**
   - A ata oficial da ANEEL de 25/06/2019 registra a REH 2.565/2019 sem o total.
   - O anexo e as notas técnicas estão na biblioteca da ANEEL, que bloqueia acesso automatizado.
   - Se você conseguir o total do anexo da REH 2.565/2019, ou da nota técnica da SGT do reajuste 2019, eu troco: é uma linha em `valores_documentais_v01.csv`.
   - Com 25700, a média dá 24883.4. Cada R$ 1 bi a mais no ciclo 2019-2020 muda a RAP 2019 em 0.5 bi e o T_RS em 30 R$ mi.
3. **Preço da BIO:** dá 206.05, contra 203.0 da referência. Nenhuma variante de método reproduz o 203.0: a média simples dá 204.31; ponderar por garantia física dá 201.01; usar o IPCA do mês anterior dá 206.79. O arquivo da ANEEL foi gerado em 01/10/2026 e pode ter revisões. Mantive 206.05.
4. **Rótulos ONS × SIGA divergentes:** mantive o rótulo do ONS, como mandam as instruções. São 7 usinas:
   - Veracel (BA, 953.0 GWh): ONS Gás × SIGA BIO;
   - Cristiano Rocha e Tambaqui (AM, 589.0 e 503.1 GWh): ONS Gás × SIGA PET;
   - Berneck (PR, 58.5 GWh): ONS Gás × SIGA BIO;
   - Termocabo (PE, 24.7 GWh): ONS Óleo × SIGA GN;
   - Piratininga e Termo Norte II: 0 GWh.

   Se quiser seguir o SIGA, é uma linha por usina em `reclassificacao_usinas_v01.csv`. A lista está em `dados/intermediarios/siga_divergencias_ons_v01.csv`.
5. **Gás natural dos sistemas isolados.** O BEN tem 47597 GWh de GN de serviço público, contra 46648.6 do ONS (RS + RB), ou +948 GWh. Provavelmente são térmicas a gás fora do SIN. O Anuário (Tabela 2.6) mostra 1.25 Mt CO₂ de gás nos isolados em 2019. A Seção 3 só pede o PET, então não somei. Diga se o GN-RB deve receber esses 948 GWh.
6. **Gás por comprador:** usei a estrutura nacional do BEN também no RS. A da Sulgás é parecida (Seção 9). Se preferir a da Sulgás no RS, é uma troca simples.
7. **Branch padrão do GitHub:** continua `claude/new-session-vyrfjo`. Não alterei, pela regra fixa. Para tornar a `main` a padrão: Settings → General → Default branch.
8. **Repositório público:** continua público. Não alterei.

## 11. Como reproduzir

```bash
pip install -r requirements.txt
python scripts/rodada02_coleta.py      # baixa as fontes com download direto (precisa de rede)
python scripts/rodada02.py             # trata: geração (ONS + SIGA + isolados), preços, CEMPRE, SEEG, BEN, referências
python scripts/rodada02_parametros.py  # Etapa 4: parametros/*_v01 (lê dados/externos/valores_documentais_v01.csv)
python scripts/rodada02_mip.py         # Etapas 5 e 6: MIP v01 + variantes, checagens, quadro e prévia
python -m pytest                       # 327 testes
```

Os documentos lidos à mão (RAP, Sulgás, MME, Angra, TUST, Comex) estão em `dados/externos/valores_documentais_v01.csv`, com página e SHA-256. Os brutos grandes (SEEG, ONS, CAGE, ANP) não estão no git: o `DOWNLOAD.txt` de cada pasta tem URL e SHA-256 para baixá-los de novo.

## 12. Git

- Branch de trabalho: `claude/new-session-vyrfjo`.
- Commits da rodada:
  - `4e8568a` R02b-E2: fontes baixadas e leitores validados com os arquivos reais (SIGA, leilões+IPCA, SEEG, CEMPRE); usinas de autoprodução fora do S38; referências 94/95
  - R02b-E2/E4/E5/E6: isolados (BEN), documentos (RAP, gás, Angra, TUST, Comex), parâmetros v01, MIP v01 e variantes, quadro e prévia
  - R02b-E7: relatório da rodada (o commit que traz este arquivo)
- `main`: push direto (fast-forward) da branch, como na Rodada 02. O resultado está na mensagem final da conversa.

## 13. Fontes de dados

| Fonte | URL | Data de acesso (UTC) | Arquivo | Usada para |
|---|---|---|---|---|
| ONS — geração por usina, 2019 | https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/GERACAO_USINA-2_2019.parquet | 15/10/2026 19:27 | `brutos/ons/` (fora do git) | GWh por usina e subsetor |
| ANEEL — SIGA | dadosabertos.aneel.gov.br (…/siga-empreendimentos-geracao.csv) | 15/10/2026 19:27 | `dados/externos/siga/` | Casamento ONS × SIGA |
| ANEEL — leilões de geração | dadosabertos.aneel.gov.br (…/resultado-leiloes-geracao.csv) | 15/10/2026 19:27 | `dados/externos/leiloes/` | Preços P1 |
| IBGE — SIDRA 1737 (IPCA) | https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all | 15/10/2026 19:27 | `dados/externos/ipca/` | Correção dos preços |
| SEEG 13.0 | https://seeg.eco.br/wp-content/uploads/2025/12/Dados-nacionais-13.0.xlsx | 15/10/2026 19:27 | `brutos/seeg/` + recorte | Emissões E1/E2/E3, SF6 |
| IBGE — SIDRA 6450 (CEMPRE) | apisidra.ibge.gov.br/values/t/6450/… | 15/10/2026 19:28 | `dados/externos/cempre/` | Ocupações e remunerações |
| EPE — BEN 2020 | epe.gov.br, publicação 479 (matriz e PDF) | 15/10/2026 19:38 | `dados/externos/epe/ben_2020/` | Isolados, consumo específico, gás por setor, reconciliação |
| EPE — Anuário 2020 | epe.gov.br, publicação 160 | 15/10/2026 19:37 | `dados/externos/epe/anuario_2020/` | Procura dos isolados por fonte (não há) |
| ANEEL — atas da Diretoria | dadosabertos.aneel.gov.br (…/pautas-atas-reunioes-publicas-diretoria.csv) | 15/10/2026 19:40 | recorte em `aneel_rap/atas_reunioes_diretoria/` | RAP 2018-2019 (REH 2.408/2018) |
| CanalEnergia (secundária, via instruções) | canalenergia.com.br/noticias/53103542 | não acessada (403) | — | RAP 2019-2020 = 25.7 bi |
| ANEEL — voto 22/04/2021 (CEEE-GT) | static.poder360.com.br/2021/04/voto-transmissoras-Aneel-22abr2021.pdf | 15/10/2026 19:30 | `aneel_rap/voto_2021_04_22_ceee_gt/` | Checagem T_RS ≥ RAP CEEE-GT |
| ANEEL — REN 559/2013 (DOU) | pesquisa.in.gov.br (DOU S1, 28/06/2013, p. 87) | 15/10/2026 19:48 | `aneel_rap/dou_2013_06_28_ren_559_2013/` | TUST 50/50 |
| ANEEL — REH 2.509/2018 (DOU) | in.gov.br (DOU S1, 26/12/2018, p. 56) | 15/10/2026 19:48 | `aneel_rap/dou_reh_2509_2018_angra/` | Preço da nuclear |
| Sulgás — DF 2019 (CAGE/Sefaz-RS) | cage.fazenda.rs.gov.br/…/02143858-prestacao-de-contas-do-governador-2019-v-5-2.pdf | 15/10/2026 19:34 | `brutos/gas/cage_rs_2019/` (38 MB) | VBP do GAS-RS; volume para θ_RS |
| MME — Boletim do gás nº 154 | gov.br/mme (boletim dez/2019) | 15/10/2026 19:36 | `dados/externos/gas/mme_boletim_dez2019/` | θ_RB |
| Comex Stat (MDIC) | https://api-comexstat.mdic.gov.br/general | 15/10/2026 19:50 | `dados/externos/comex/api_2019_ncm/` | Repartição das importações |

Detalhes por número em `dados/externos/valores_documentais_v01.csv`; por fonte, em `dados/externos/FONTES.md` e nos `DOWNLOAD.txt`.

## 14. Comparação com os valores de referência

**Total: 101/102 conferem** (`resultados/rodada02/comparacao_referencias_v02.csv`).

| Fonte | Conferem | Maior diferença |
|---|---|---|
| ONS (Rodada 02, Seção 5.1; 26 itens) | 26/26 | 0.15 GWh (total do RB) |
| ONS (02b, Seção 2; 20 itens) | 20/20 | 0.13 GWh (total RB SIN: 508491.77 × 508491.9) |
| Preços (leilões + IPCA; 8) | 7/8 | **BIO: 206.05 × 203.0 (+3.05)**. Os demais ficam dentro de ±0.04: HID 166.43, EOL 173.16, SOL 260.63, CAR 251.12, GN 246.69, PET 259.99, NUC 247.47 |
| IPCA (média do índice em 2019) | 1/1 | 5213.61 × 5213.61 |
| SEEG (mil t CO₂e; 20) | 20/20 | 0.13 (total do RB: 34181.13 × 34181.0). Não alocado 343.99; SF6 323.10 |
| CEMPRE (20) | 20/20 | 0 |
| BEN (consistência da matriz × Tabela 5.4; 7) | 7/7 | 0.43 mil tep (lenha) |

Os GWh das usinas excluídas também conferem (fazem parte dos 20 itens da 02b): RS 72.72 (CMPC) e RB 9440.38 (Do Atlântico 2758.36, Klabin 1777.13, CSP 1611.78, Suzano 1255.39, CST 1198.49, Sol 839.23).

**RAP (Seção 5.5):**
- O ciclo 2019-2020 da referência (25.7 bi) não pôde ser conferido em documento da ANEEL.
- O ciclo 2018-2019 oficial é 24066.85 R$ mi.
- Conferência indireta (ONS, SEAMSE dez/2019): os encargos de uso faturados de julho a dezembro de 2019 somam 12145.09 R$ mi, ≈ 24290 R$ mi/ano, já com PA, PV e orçamento do ONS. É compatível com 25.7 bi de RAP.
- A RAP da CEEE-GT no ciclo 2019-2020 confere: 749.75 R$ mi (voto de 22/04/2021, p. 10; 751.29 pela REH 2.565/2019 original). T_RS = 1509.1 ≥ 749.75 ✓.

**Reconciliação com o EPE (Seção 4 da 02b; `resultados/rodada02/reconciliacao_epe_v01.csv`; GWh):**

| Fonte | BEN 2020, serviço público | RS + RB montado | Diferença | % |
|---|---|---|---|---|
| HID | 378450 | 385339.2 | +6889.2 | +1.8 |
| EOL | 55954 | 53389.8 | −2564.2 | −4.6 |
| SOL | 4978 | 4384.6 | −593.4 | −11.9 |
| BIO (lenha + biodiesel + outras renováveis) | 1840 | 9340.2 | +7500.2 | +407.6 |
| CAR | 13823 | 13963.9 | +140.9 | +1.0 |
| GN | 47597 | 46648.6 | −948.4 | −2.0 |
| PET (diesel + óleo combustível) | 4769 | 4769.0 | 0 (por construção) | 0 |
| NUC | 16129 | 16128.8 | −0.2 | 0.0 |
| Outras não renováveis | 405 | 0 | −405 | −100 |
| **Total** (soma das fontes; o BEN publica 523943, diferença de arredondamento) | **523945** | **533964.0** | **+10019.0** | **+1.9** |

Leitura, sem trocar a fonte principal:
- **BIO:** o ONS inclui usinas de bagaço e cavaco que o BEN conta como autoprodução.
- **HID:** o ONS tem usinas em consórcio com autoprodutores e conta o 60 Hz de Itaipu de forma diferente.
- **EOL e SOL:** o BEN inclui usinas não despachadas pelo ONS.
- **GN:** a diferença é provavelmente a geração a gás fora do SIN (Seção 10, ponto 5).
- **Carga dos isolados (Anuário, Tabela 2.13):** 461 MWmed ≈ 4038 GWh. É compatível com 2794.7 GWh de derivados + ≈ 948 GWh de gás.

## 15. Parâmetros

Todos estão em `parametros/quadro_parametros_v01.xlsx` (71 números, com unidade, fonte e cálculo) e nos CSVs `parametros/*_v01.csv` (coluna `fonte`).

| Parâmetro | RS | RB | Fonte / regra |
|---|---|---|---|
| VBP do S38 (X_r) | 20942.66 | 324387.34 | MIP original |
| F_r (vendas ao bloco S38) | 5659.65 | 96538.40 | MIP original |
| RAP 2019 (Brasil) | 24883.43 | | Média de 24066.85 (ANEEL, REH 2.408/2018) e 25700 (secundária) |
| T_r = VBP do TRA | 1509.06 | 23374.36 | RAP × participação no VBP do S38 (6.06% e 93.94%) |
| α (parcela da RAP paga pela distribuição) | 0.5 | 0.5 | REN 559/2013, art. 3º, IV |
| G_r (gás às térmicas pelo GAS) | 0 | 0 | Padrão das instruções |
| E_r = VBP da geração | 4150.59 | 73164.04 | F_r − T_r − G_r (D3-A) |
| VBP do GAS | 898.71 | 13539.81 | Sulgás (receita líquida 2019); RB: ((1 − θ) × 10224.20 + 4335.78) ÷ 0.75 (fallback; 0.25 = HIPÓTESE) |
| VBP da DIS (resíduo) | 14384.30 | 214309.12 | X_r − E_r − T_r − VBP_GAS |
| θ | 0.0512 | 0.4309 | Fallback (0.20 m³/kWh) sobre a Sulgás sem serviço; MME, Boletim nº 154 |
| Preço implícito da âncora | 183.0 R$/MWh | 143.1 R$/MWh | E_r ÷ GWh (ONS + isolados) |
| Σ GWh × preço de leilão ÷ âncora | 0.975 | 1.266 | Conferência (D3-A mantida) |
| Importações: energia elétrica / gás | 44.26% / 55.74% | igual | Comex Stat 2019, FOB: 2716 = 1533.67; 2711.21 = 1293.13; 2711.11 = 638.05 US$ mi |
| Consumo específico (tep/MWh) | CAR 0.2415 · GN 0.1972 · PET 0.2655 · BIO 0.2359 · NUC 0.2533 | | BEN 2020, Tabela 5.4 |
| Tetos de coluna | S04 → CAR (0.40), S05 → GN (θ; 0.60; excedente → GAS), S19 → PET (0.60), S03 + S09 → BIO (0.40 comum) | | Seção 6.8 + respostas 2 e 3 da 02b |
| Tetos atingidos | S05 → GN-RS (excedente 7.8 → GAS); S19 → PET-RS (latente: 186.4 aos demais) | S19 → PET-RB (excedente 2259.1 aos demais ∝ VBP) | `quadro_subsetores_v01.xlsx`, aba `tetos_atingidos` |
| SF6 (t CO₂e) | TRA 1860.5 · DIS 17733.9 | TRA 29847.2 · DIS 273655.4 | SEEG 323.1 mil t × participação no VBP do S38 × VBP de TRA/DIS (resposta 4) |
| Emprego e salários | composição do CEMPRE (RS por diferença) | RB = Brasil − RS | Seção 5.8 |
| Água | ∝ GWh das térmicas | | HIPÓTESE (Seção 5.10) |

## 16. Variantes

**P1 × P2 (VBP da geração, R$ mi).** P2 usa preço igual. O total E_r, o TRA, o GAS e a DIS não mudam. Só muda a repartição entre as fontes:

| Região | HID | EOL | SOL | BIO | CAR | GN | PET | NUC |
|---|---|---|---|---|---|---|---|---|
| RS P1 | 2481.2 | 935.0 | 0 | 14.4 | 675.8 | 44.1 | 0 | 0 |
| RS P2 | 2661.7 | 964.0 | 0 | 12.5 | 480.5 | 31.9 | 0 | 0 |
| RB P1 | 48737.6 | 6581.0 | 902.5 | 1508.8 | 2248.7 | 9054.1 | 979.2 | 3152.2 |
| RB P2 | 53060.2 | 6886.3 | 627.4 | 1326.8 | 1622.5 | 6650.3 | 682.4 | 2308.0 |

Com P2, as fósseis perdem de 26% a 30% do VBP, e o EOB do GN-RB piora de −4115 para −5152.

**E1 × E2 × E3 (fatores, t CO₂e/MWh):**

| Subsetor | E1 (principal) | E2 (base inteira ∝ SEEG) | E3 (só SEEG; não preserva o total) |
|---|---|---|---|
| CAR-RS | 1.435 | 2.169 | 1.435 |
| GN-RS | 0.436 | 0.660 | 0.436 |
| CAR-RB | 0.856 | 2.078 | 0.856 |
| GN-RB | 0.441 | 1.071 | 0.441 |
| PET-RB | 0.900 | 2.184 | 0.900 |
| BIO-RB | 0.001 | 0.003 | 0.001 |
| DIS-RS / DIS-RB (t) | 1877402 / 47010600 | 26806 / 664078 | 17734 / 273655 (só SF6) |

- **E1:** a geração fica com o SEEG; o resíduo vai a DIS e GAS ∝ VBP. Preserva o total.
- **E2:** a base é repartida ∝ SEEG. Os fatores das fósseis ficam acima das faixas da Seção 9a (CAR > 1.6 no RS e no RB; GN > 0.65; PET > 1.1).
- **E3:** descarta o resíduo: 1975.9 mil t no RS e 49689.7 mil t no RB.

**Faixas de plausibilidade (Seção 9a, com o CAR em 0.8–1.6):** na E1, todos os subsetores ficam dentro.

**Âncora × GWh·preço (D3-A mantida, resposta 6):**
- No RB, o preço implícito da âncora é 143.1 R$/MWh; Σ GWh × preço de leilão é 1.266 vezes a âncora.
- No RS, o preço implícito é 183.0 (razão 0.975).
- Por fonte (R$/MWh implícito na v01): HID 131.4, EOL 136.8, SOL 205.8, BIO 162.7, CAR 198.3, GN 194.8, PET 205.3, NUC 195.4 no RB; HID 170.6, EOL 177.5, BIO 211.2, CAR 257.4, GN 252.9 no RS.

As hipóteses da Seção 16 da Rodada 02 seguem válidas: cotas e parque antigo no RB, vendas no mercado livre e autoprodução fora do bloco, Itaipu como compra das distribuidoras. Não forcei o fechamento.

## 17. Mudanças da 02b

Efeito das duas mudanças de escopo, uma por vez. O VBP usa a âncora e os preços desta rodada nos três casos, para isolar o efeito dos GWh.

| Região | Subsetor | GWh R02 | GWh 02b sem isolados | GWh 02b final | VBP R02 | VBP 02b final | t/MWh R02 | t/MWh 02b |
|---|---|---|---|---|---|---|---|---|
| RB | CAR | 16907.3 | 11338.7 | 11338.7 | 3306.9 | 2248.7 | **0.574** | **0.856** |
| RB | BIO | 12304.5 | 9271.9 | 9271.9 | 1974.6 | 1508.8 | 0.001 | 0.001 |
| RB | PET | 1974.3 | 1974.3 | 4769.0 | 399.8 | 979.2 | **2.174** | **0.900** |
| RB | pendente (Sol) | 839.2 | — | — | — | — | — | — |
| RS | BIO | 141.0 | 68.2 | 68.2 | 29.7 | 14.4 | 0.000 | 0.000 |
| RB | HID / EOL / SOL / GN / NUC | sem mudança de GWh | | | 48064.9 / 6490.1 / 890.0 / 8929.1 / 3108.7 | 48737.6 / 6581.0 / 902.5 / 9054.1 / 3152.2 | GN 0.441 | GN 0.441 |
| RS | HID / EOL / CAR / GN | sem mudança de GWh | | | 2472.1 / 931.5 / 673.3 / 44.0 | 2481.2 / 935.0 / 675.8 / 44.1 | CAR 1.435 | CAR 1.435 |

- **Usinas de autoprodução fora:** saem 9513.1 GWh.
  - RB: 9440.4 GWh, dos quais CAR −5568.6 (Do Atlântico, CSP, CST), BIO −3032.5 (Klabin, Suzano) e Sol 839.2 (pendente na Rodada 02).
  - RS: 72.7 GWh (CMPC).
  - O VBP do CAR-RB cai 32% e o fator do CAR-RB sobe de 0.57 para 0.86, dentro da faixa. Os demais subsetores ganham VBP (cerca de 1.4% no RB e 0.4% no RS), porque o total E_r é o mesmo.
- **Sistemas isolados:** +2794.7 GWh no PET-RB. O VBP do PET-RB vai de 399.8 para 979.2 e o fator cai de 2.17 para 0.90.
- **Sem efeito nos totais:** a âncora (E_r), o TRA, o GAS, a DIS e os totais de CO₂e por região não mudam; só a repartição entre as fontes.
