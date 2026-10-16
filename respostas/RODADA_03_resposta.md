# Rodada 03 — Relatório do Claude Code

Projeto: desagregação do S38 na MIP inter-regional RS × RB, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
Data: 16/10/2026 · Instruções: `instrucoes/RODADA_03_instrucoes_CODE.md` · Rodada anterior: `respostas/RODADA_02b_resposta.md`
Convenção numérica: ponto decimal, sem separador de milhar.

Decisões aplicadas (mensagem de abertura + Seção 1):
- as anteriores: D1 = C; D2, D3, D4 e D6 = A; D5 = E1; D7 = A;
- **D8 = A:** geração por fonte com o Brasil pelo BEN 2020, o RS pelo ONS e RB = Brasil − RS;
- **D9 = (a) + (b) + (f) + (r):** pacote contra o EOB negativo;
- **D10:** gás por comprador no RS pela estrutura de receita da Sulgás.

## 1. Resumo

- **MIP v02 pronta**, com variantes, comparativo v01 × v02 e executor de cenários. Tudo em `resultados/rodada03/` e `parametros/*_v02*`, sem sobrescrever a v01.
- **Nenhum EOB negativo na principal.** Todos os subsetores com produção têm EOB ≥ 10% do VBP: T9 passa e o RAS converge.
  - Para isso, precisei de uma **extensão de viabilidade** no piso das térmicas. Com κ = 0.70 e η = 0.10, como nas instruções, o pacote é **inviável** para GN-RB, PET-RB e GN-RS: os custos fixos (combustível + TUST + remunerações + impostos) passam de 90% do VBP.
  - O piso passa a ser o maior entre combustível ÷ κ e combustível ÷ (1 − η − φ).
  - O preço disso: nessas três térmicas os insumos não energéticos vão a ≈ 0.
  - A variante `_sem_viabilidade` mostra o piso puro das instruções. **É o principal ponto para você decidir** (Seção 10, ponto 1).
- **D8:** RS + RB = BEN em cada fonte (T10). As 24 referências da Seção 2.1 conferem.
  - Os fatores E1 ficam todos dentro das faixas: CAR-RS 1.435, CAR-RB 0.867, GN-RB 0.433, GN-RS 0.436, PET-RB 0.829 e BIO-RB 0.007 t CO₂e/MWh.
- **(b) VBP do GAS-RB = 26990.1 R$ mi.** É o preço médio ponderado das 4 distribuidoras (1.932 R$/m³) × o volume não térmico do RB (13967.8 milhões m³).
  - As DFP 2019 de Comgás, CEG e Gasmig foram reconferidas no documento.
  - Só com a Sulgás (1.390 R$/m³), o VBP seria 19421.0 (variante `_gas_sulgas`).
- **(f) Pisos atingidos:**

  | Subsetor | VBP (R$ mi) | R$/MWh | Combustível no VBP |
  |---|---|---|---|
  | GN-RB | 12542.4 | 264.5 | 61% |
  | PET-RB | 4644.4 | 897.7 | 61% |
  | GN-RS | 54.9 | 314.6 | 62% |

  As demais fontes da mesma região caem na proporção do VBP; E_r não muda.
- **(r)** moveu 141.5 R$ mi de insumos não energéticos no RS e 4797.7 no RB. A soma dos EOB de cada região é a mesma da v01 e da original.
- **Revisão adversarial: 19 achados (17 distintos), todos corrigidos** (Seção 7). O mais grave estava no gás por comprador:
  - com o VBP do GAS-RB da D9-b, o alvo de gás de 6 ramos industriais do RB (S17, S21–S24, S27) passava das compras deles ao S38, e eles ficavam **sem eletricidade**;
  - pus um **teto: o gás de cada comprador ≤ 0.90 das compras dele ao S38** (HIPÓTESE), com o excedente aos demais compradores do mesmo grupo;
  - é o **segundo ponto para você decidir** (Seção 10, ponto 2). Com o preço da Sulgás (variante nova `_gas_sulgas`), nenhum comprador do RB bate no teto.
- **Multiplicador de produção acima de 2.2** (novo alerta): GN-RS 2.327, GAS-RS 2.344, PET-RB 2.620 e PET-RS (latente) 2.620. Na v01, o GN-RS estava em 2.555.
- **Executor de cenários:** reproduz os 9 cenários da Rodada 01 na original (T11). Já rodou os 9 cenários na original, na v01 e na v02 (`resultados/rodada03/cenarios_exemplo.xlsx`).
- **367 testes passam** (eram 327): os novos são T9, T10, T11, o T2 com as 9 especificações v02, os das peças novas do motor e os das correções da revisão.

## 2. Status por etapa

| Item | Status | Observação |
|---|---|---|
| Git: trabalhar a partir da `main` | concluído | `main` local = `origin/main` (c4817e9); commits da rodada na `main` |
| D8 — geração por fonte | concluído | `scripts/rodada03.py` → `dados/intermediarios/geracao_2019_regiao_subsetor_v03.csv`; 24/24 referências; T10 |
| D9-a — importações do RS → DIS | concluído | Regra de primários `RS importacoes fixa S38_DIS 1.0` |
| D9-b — VBP do GAS-RB por volume | concluído | Preço das 4 distribuidoras (DFP reconferidas); o da Sulgás vira a variante `_gas_sulgas` |
| D9-f — combustíveis integrais + piso | concluído, com extensão | Piso de viabilidade além do κ (Seção 9); variante sem a extensão |
| D9-r — reequilíbrio (RAS) | concluído | T9 passa; RAS convergiu (7 e 8 iterações) |
| D10 — gás por comprador no RS | concluído | Nota 18 da Sulgás; serviço → S19 (documentado); com o teto do gás por comprador (revisão) |
| Produto 1 — MIP v02 principal | concluído | `MIP_RS_RB_2019_S38_11sub_v02.xlsx` + `_longo.csv` |
| Produto 2 — variantes | concluído | P2, E2, E3 (.xlsx + CSV); κ 0.60, κ 0.80 e sem viabilidade (as três só com o piso κ), η 0.05 e preço da Sulgás (CSV + linha no quadro) |
| Produto 3 — quadro v02 | concluído | Abas `v01_x_v02`, `reequilibrio_RAS`, `pisos_atingidos` e outras |
| Produto 4 — prévia | concluído | `previa_multiplicadores_v02.xlsx`, marcada "PRÉVIA" |
| Produto 5 — executor de cenários | concluído | `src/mip/cenarios.py`, `scripts/rodar_cenarios.py`, `parametros/cenarios_exemplo.csv`; T11 |
| Checagens e testes | concluído | T1–T11; 367 testes passam |
| Revisão adversarial | concluída | 19 achados (17 distintos), todos corrigidos; Seção 7 |
| Relatório, HISTORICO, README | concluído | Este arquivo |

## 3. Arquivos criados, movidos ou alterados

| Caminho | Tipo | O que é |
|---|---|---|
| `instrucoes/RODADA_03_instrucoes_CODE.md` | texto | Cópia das instruções |
| `src/mip/desagregacao.py` | código (alterado) | Opções `piso_vbp` (D9-f) e `reequilibrio` (D9-r) na especificação; regra `fixa_por_tipo`; `_desagregar_passo`, `_resolver_pisos`, `_redistribuir_com_piso`, `_custos_fixos_e_combustivel`, `_eob_maximo`, `_reequilibrar_eob`; checagens `piso_vbp_combustivel`, `EOB_minimo_eta`, `reequilibrio_soma_EOB_regiao`, `reequilibrio_insumos_fixos`, `multiplicador_producao_subsetores`; pesos realizados depois do reequilíbrio (etapa `apos_reequilibrio`); LEIAME da planilha com o piso e o reequilíbrio; `_coef_latentes.csv` gravado ao lado de todo `_longo.csv` |
| `src/mip/externos/ben.py` | código | D8: BEN 2020 (Tabela 5.4) por subsetor, RS pelo ONS, RB = Brasil − RS, referências; consumo específico com o mapeamento da D8; leitor da matriz consolidada |
| `src/mip/cenarios.py` | código | Executor de cenários (valida o CSV, os pesos e os choques em setores sem produção) |
| `src/mip/leitura.py` | código (alterado) | `ler_mip_longo` (MIP a partir do CSV longo; lê `_coef_latentes.csv` ao lado; erro se o arquivo indicado não existe) |
| `scripts/rodada03.py` | script | D8 + referências + reconciliação EPE + consumo específico v02 + gás e eletricidade por setor (BEN) |
| `scripts/rodada03_parametros.py` | script | Parâmetros v02 (9 especificações), com o teto do gás por comprador |
| `scripts/rodada03_mip.py` | script | MIP v02, variantes, checagens, quadro e prévia |
| `scripts/rodada03_decomposicao.py` | script | v01 → v02 passo a passo (Seção 17) |
| `scripts/rodar_cenarios.py` | script | Executor de cenários (linha de comando) |
| `dados/externos/valores_documentais_v02.csv` | dado | As linhas da v01 + MME p. 16 + receitas e volumes de Comgás, CEG, Gasmig e Sulgás + preço médio + tarifa média industrial 2019 (só evidência) |
| `dados/externos/gas/sulgas_segmentos_2019_v01.csv` | dado | Nota 18 da Sulgás (volume e receitas por segmento) |
| `dados/externos/FONTES.md` | documentação (alterado) | Seção "Rodada 03" |
| `dados/intermediarios/geracao_2019_regiao_subsetor_v03.csv` | dado derivado | GWh por região × subsetor (D8) |
| `dados/intermediarios/ben_2019_consumo_especifico_v02.csv` | dado derivado | Consumo específico das térmicas com o mapeamento da D8 (PET com as outras não renováveis) |
| `dados/intermediarios/ben_2019_gas_eletricidade_por_setor_v01.csv` | dado derivado | BEN 2020: gás natural e eletricidade por setor (evidência para o teto do gás) |
| `parametros/*_v02*` | parâmetros | `especificacao_v02.yaml` e as variantes `_P2`, `_E2`, `_E3`, `_k060`, `_k080`, `_eta005`, `_sem_viabilidade`, `_gas_sulgas` (com `componentes`, `regras_linha` e `regras_primarios_v02_gas_sulgas.csv`); CSVs com a coluna `fonte`; `quadro_parametros_v02.xlsx` (abas novas `gas_grupos_teto`, `gas_x_eletricidade_BEN` e as do preço da Sulgás) |
| `parametros/cenarios_exemplo.csv` | parâmetros | Os 9 cenários da Rodada 01 no formato do executor |
| `parametros/LEIAME_parametros.md` | documentação (alterado) | Opções novas e arquivos v02 |
| `resultados/rodada03/` | resultados | MIP v02 e variantes, `checagens_v02.csv`, `quadro_subsetores_v02.xlsx`, `previa_multiplicadores_v02.xlsx`, `decomposicao_v01_v02.csv`, `cenarios_exemplo.xlsx`, `comparacao_referencias_v03.csv`, `reconciliacao_epe_v02.csv` |
| `tests/test_rodada03.py` | teste | T2 v02, T9, T10, T11, peças novas e correções da revisão |
| `respostas/RODADA_03_resposta.md`, `respostas/HISTORICO.md`, `README.md` | documentação | Este relatório, histórico e status |

Nada foi sobrescrito: v01, `resultados/rodada02/` e os parâmetros v01 ficaram como estavam. A v01 continua idêntica (os testes da Rodada 02 passam com o motor novo).

## 4. Validação da MIP original

Sem mudança: o T1 (SHA-256 `15e734a4…a3ea`) e as identidades da Rodada 01 passam.

## 5. Reprodução dos resultados

- **Os 9 cenários da Rodada 01** são reproduzidos pela Rodada 01 (`tests/test_replicacao.py`) e, agora, também pelo executor de cenários (T11): mesmos valores, mesmas tolerâncias e mesmo top-10 do R1.
- **Prévia (PRÉVIA, não é resultado do artigo).** O choque do S38 foi repartido na proporção das vendas à demanda final: DIS 97.5% e GAS 2.5% na v02 (96.8% e 3.2% na v01). Resultados (`cenarios_exemplo.xlsx` e prévia):

| Cenário | CO₂e original (t) | v01 | v02 | v02 − v01 |
|---|---|---|---|---|
| E1 | 428113.5 | 381676.9 | 383167.6 | +1490.7 |
| R1 | 216407.0 | 202090.3 | 202360.3 | +270.0 |
| F1 | 356045.7 | 339717.7 | 340218.1 | +500.5 |
| R2 | 216987.2 | 208874.0 | 208975.7 | +101.8 |
| R3 | 169090.0 | 161630.1 | 161630.2 | +0.1 |
| R4a | 309794.9 | 288643.7 | 289210.5 | +566.8 |
| R4b | 304336.5 | 280872.7 | 281514.3 | +641.7 |
| F2 | 381702.9 | 366138.5 | 366616.8 | +478.2 |
| F3 | 375427.3 | 352150.2 | 352879.5 | +729.3 |

A v02 muda pouco os cenários porque o choque do S38 cai quase todo na DIS, que é parecida nas duas versões. A diferença grande está nos multiplicadores das térmicas (Seção 17).

## 6. Diagnóstico do S38

Quadro por subsetor da v02 (P1 + E1 + D9). As colunas completas, incluindo E2, E3, ocupações, remunerações e os 5 maiores insumos, estão em `quadro_subsetores_v02.xlsx`.

| Região | Subsetor | VBP (R$ mi) | % do S38 | GWh | R$/MWh | t CO₂e/MWh E1 | t CO₂e/R$ mi E1 | EOB/VBP | CI/VBP | Mult. produção | Mult. emissões (t/R$ mi) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RS | HID | 2474.7 | 11.82 | 14542.6 | 170.2 | 0 | 0 | 0.506 | 0.368 | 1.564 | 26.7 |
| RS | EOL | 932.5 | 4.45 | 5266.9 | 177.1 | 0 | 0 | 0.506 | 0.368 | 1.564 | 26.7 |
| RS | SOL (latente) | 0 | 0 | 0 | — | — | — | — | — | 1.514 | 25.5 |
| RS | BIO | 14.4 | 0.07 | 68.2 | 210.7 | 0.000 | 0.2 | 0.478 | 0.393 | 1.626 | 42.1 |
| RS | CAR | 674.1 | 3.22 | 2625.2 | 256.8 | 1.435 | 5587.6 | 0.482 | 0.389 | 1.605 | 5617.5 |
| RS | GN | 54.9 | 0.26 | 174.6 | 314.6 | 0.436 | 1387.2 | 0.100 | 0.825 | **2.327** | 1458.6 |
| RS | PET (latente) | 0 | 0 | 0 | — | — | — | — | — | **2.620** | 1034.4 |
| RS | NUC (zerado) | 0 | 0 | 0 | — | — | — | — | — | — | — |
| RS | TRA | 1509.1 | 7.21 | — | — | — | 1.2 | 0.701 | 0.183 | 1.322 | 24.0 |
| RS | DIS | 14384.3 | 68.68 | — | — | — | 130.5 | 0.245 | 0.550 | 1.896 | 387.6 |
| RS | GAS | 898.7 | 4.29 | — | — | — | 129.3 | 0.100 | 0.792 | **2.344** | 213.8 |
| RB | HID | 43572.3 | 13.43 | 363907.4 | 119.7 | 0 | 0 | 0.489 | 0.334 | 1.513 | 27.0 |
| RB | EOL | 6314.3 | 1.95 | 50687.1 | 124.6 | 0 | 0 | 0.489 | 0.334 | 1.513 | 27.0 |
| RB | SOL | 933.4 | 0.29 | 4978.0 | 187.5 | 0 | 0 | 0.489 | 0.334 | 1.513 | 27.0 |
| RB | BIO | 262.6 | 0.08 | 1771.8 | 148.2 | 0.007 | 46.4 | 0.466 | 0.353 | 1.562 | 87.0 |
| RB | CAR | 2023.0 | 0.62 | 11197.8 | 180.7 | 0.867 | 4798.9 | 0.370 | 0.438 | 1.712 | 4841.1 |
| RB | GN | 12542.4 | 3.87 | 47422.4 | 264.5 | 0.433 | 1635.5 | 0.100 | 0.510 | 1.803 | 1676.2 |
| RB | PET | 4644.4 | 1.43 | 5174.0 | 897.7 | 0.829 | 924.0 | 0.100 | 0.772 | **2.620** | 1031.7 |
| RB | NUC | 2871.5 | 0.89 | 16129.0 | 178.0 | 0 | 0 | 0.489 | 0.334 | 1.513 | 27.0 |
| RB | TRA | 23374.4 | 7.21 | — | — | — | 1.4 | 0.659 | 0.188 | 1.325 | 26.0 |
| RB | DIS | 200858.8 | 61.92 | — | — | — | 219.4 | 0.250 | 0.579 | 1.945 | 429.4 |
| RB | GAS | 26990.1 | 8.32 | — | — | — | 218.1 | 0.337 | 0.380 | 1.647 | 262.1 |
| RS | S38 agregado (original) | 20942.7 | — | — | — | — | 278.8 | 0.322 | 0.500 | 1.925 | 428.1 |
| RB | S38 agregado (original) | 324387.3 | — | — | — | — | 260.5 | 0.320 | 0.493 | 1.909 | 406.3 |

Faixas de E1 (Seção 4): todas dentro (CAR 0.8–1.6; GN 0.35–0.65; PET 0.65–1.1; BIO ≤ 0.1; demais 0).

Por que o multiplicador passa de 2.2:
- **PET-RB e GN-RS:** o combustível (S19 e S05) é ≈ 61–62% do VBP e é comprado internamente, de setores com cadeia longa.
- **GAS-RS:** compra 634.6 R$ mi do S05 do RB (70.6% do VBP).
- **PET-RS:** é latente e herda a coluna do PET-RB.

Não é erro de conta; é a estrutura de custo que as regras D9-f impõem.

**Gás por comprador (D10), resultado depois do RAS** (abas `gas_por_comprador` e `gas_por_grupo` do quadro): do total vendido pelo GAS-RS (898.7 R$ mi), vão
- 77.2% à indústria (S04–S37, com o S19; alvo da Sulgás: indústria + cogeração 76.5% e serviço 1.0%);
- 20.0% às famílias;
- 2.4% aos serviços S41–S68 (exceto S43);
- 0.4% ao S43 (transporte terrestre);
- nada ao RB.

Sem o teto (e já sem o consumo não energético na D10), a indústria ficava com 72.8% e as famílias com 23.8%, e seis compradores do RS ficavam sem eletricidade (S04, S17, S19, S26, S27 e S28): o alvo dos compradores que passavam das compras se perdia, e o RAS o levava às famílias. Na v01 eram 73.2% e 24.8%, e S04, S17, S27 e S28 do RS ficavam sem eletricidade. Na v02 nenhum comprador fica sem eletricidade (teste novo), por causa do teto do gás por comprador (Seção 10, ponto 2):
- no RS ficam no teto S04, S17, S19, S26, S27 e S28;
- o excedente vai aos demais compradores da indústria;
- o do S19, único do grupo "serviço", vai aos demais compradores da região.

## 7. Motor de desagregação

**O que mudou** (`src/mip/desagregacao.py`; formato em `parametros/LEIAME_parametros.md`):

| Item | Implementação |
|---|---|
| D9-f, piso de VBP | YAML `piso_vbp` (`kappa`, `combustiveis`, `viabilidade_eta`). O motor desagrega com os pesos P1 e calcula o combustível de cada térmica a partir das células reais (linhas S04/S05/S19/S03/S09 de todas as origens; as importações no GN). Quem fica abaixo do piso sobe; as demais fontes da região caem na proporção do VBP (E_r fixo). Repete até estabilizar: 2 iterações na v02. Tabela na aba `pisos_vbp` |
| D9-r, reequilíbrio | YAML `reequilibrio` (`eta`, `linhas_fixas`, `primarios_ajustaveis`, `importacoes: fixas`, `se_inviavel`). É um RAS por região sobre a matriz [insumos ajustáveis × subsetores]. Linhas: total de cada insumo na região (preservado). Colunas: ajustável − (EOB* − EOB). Células negativas e colunas sem produção ficam fixas; zeros continuam zero. EOB e VA são recalculados. Abas `reequilibrio_RAS` e `reequilibrio_insumos`; na aba `parametros`, a etapa `apos_reequilibrio` traz os pesos realizados |
| Regra `fixa_por_tipo` | Participação por tipo de subsetor (ex.: geração), repartida na proporção do VBP final. Usada no CEMPRE, para que remunerações e ocupações acompanhem os pisos |
| Checagens novas | `piso_vbp_combustivel` (FALHA se VBP < combustível ÷ κ); `EOB_minimo_eta` (T9; FALHA, ou ALERTA com `se_inviavel: limitar`); `reequilibrio_soma_EOB_regiao`; `reequilibrio_insumos_fixos` (bloco, combustíveis, importações, remunerações e impostos sobre a produção iguais antes e depois); `multiplicador_producao_subsetores` (ALERTA acima de 2.2) |
| Leitor longo | `ler_mip_longo`: as variantes só em CSV podem ser lidas pelo executor. A exportação grava o `_coef_latentes.csv` ao lado de todo `_longo.csv` (principal e variantes) |

**Revisão adversarial.** Foi um workflow com 4 revisores (motor, parâmetros, executor e resultados) e 2 céticos por achado, que tentam refutá-lo.
- Os céticos só rodaram para os achados dos parâmetros: os 4 foram confirmados, 2 de 2.
- Nos demais, os verificadores pararam por limite de sessão. Reproduzi cada achado eu mesmo, no código e nos dados, antes de corrigir.
- Cada correção tem teste.
- Foram 19 achados, 17 distintos: o 5 e o 14 vieram de dois revisores.

| # | Revisor | Gravidade | Achado | Verificação | Correção |
|---|---|---|---|---|---|
| 1 | parâmetros | alta | Com o VBP do GAS-RB da D9-b, o alvo de gás de S17, S21, S22, S23, S24 e S27 no RB passava das compras deles ao S38. A participação do gás era limitada a 1 e a eletricidade ia a zero: as vendas da DIS-RB a esses ramos caíam de 4495.8 (v01) para 0. No RS, o mesmo com S04, S17, S19, S27 e S28 (e também o S26, depois da correção 3). O alvo perdido ia às famílias pelo RAS e desviava a D10 | confirmado (2 de 2) | Teto: gás ≤ 0.90 das compras ao S38 de cada comprador (HIPÓTESE); o excedente vai aos demais compradores do mesmo grupo. Abas `gas_grupos_teto`, `gas_por_comprador` e `gas_por_grupo`. Teste: nenhum comprador sem eletricidade. Seção 10, ponto 2 |
| 2 | parâmetros | baixa | Consumo específico do PET sem as "outras não renováveis": 0.2655 em vez de 0.2712 tep/MWh | confirmado (2 de 2) | `ben_2019_consumo_especifico_v02.csv` com o mapeamento da D8; teste |
| 3 | parâmetros | baixa | A D10 incluía o consumo final não energético do BEN no "consumo industrial de gás" do RS | confirmado (2 de 2) | Retirado no RS; no RB fica como na v01. Teste |
| 4 | parâmetros | baixa | Notas de `valores_documentais_v02.csv` ainda citavam o fallback da margem de 0.25 | confirmado (2 de 2) | Notas atualizadas |
| 5 | executor e resultados | alta | `_longo.csv` da principal, P2, E2 e E3 sem o `_coef_latentes.csv`. Lidos pelo executor, o PET-RS e o SOL-RS latentes viravam colunas vazias (multiplicador 1, CO₂e 0) | reproduzido | A exportação grava o arquivo ao lado; o leitor dá erro se o arquivo indicado não existe. Teste com o arquivo publicado |
| 6 | executor | média | Choque em setor com produção zero e sem coluna latente saía com multiplicador 1 e CO₂e 0, sem aviso | reproduzido | Erro explicativo (`CenarioInvalido`); teste |
| 7 | executor | média | Pesos de repartição com espaço ou erro de digitação eram ignorados em silêncio | reproduzido | `strip` na linha de comando; subsetor desconhecido dá erro. Teste |
| 8 | executor | média | Peso negativo inflava o choque | reproduzido | Peso negativo dá erro. Na regra das vendas à demanda final, venda líquida negativa conta como zero. O executor confere que a soma repartida é igual ao choque |
| 9 | executor | baixa | CSV de cenários com célula vazia passava (NaN) | reproduzido | Erro com o número da linha; teste |
| 10 | executor | baixa | Duas versões com o mesmo nome na linha de comando: uma sumia | reproduzido | Erro; teste |
| 11 | motor | média | Com `importacoes: ajustaveis`, o piso e o reequilíbrio tratavam as importações de forma diferente, e o RAS movia gás importado do GN. A principal usa `fixas` e não era afetada | reproduzido | Opção retirada: pela regra do Comex, as importações do S38 são de energia, fixas pelo D9-r. Checagem nova `reequilibrio_insumos_fixos`. Teste |
| 12 | motor | baixa | A aba `parametros` só trazia os pesos de antes do reequilíbrio | reproduzido | Etapa `apos_reequilibrio` com os pesos realizados; teste |
| 13 | motor | baixa | O LEIAME da planilha v02 dizia que o EOB negativo "não é corrigido" | reproduzido | O LEIAME descreve o piso e o reequilíbrio quando estão ligados |
| 14 | motor e resultados | baixa | A variante κ = 0.80 era idêntica à principal: com a viabilidade ligada, κ ≥ ≈ 0.62 não atua | reproduzido | Variantes κ = 0.60 e 0.80 só com o piso κ, para comparar com `_sem_viabilidade` (κ = 0.70). Teste |
| 15 | motor | baixa | A tolerância do reequilíbrio era relativa (1e-6 × VBP) e a da checagem, absoluta. `viabilidade_eta` < η não era recusado | reproduzido | Mesma tolerância absoluta. `viabilidade_eta` exige `reequilibrio` e ≥ η. A checagem mostra o déficit em R$ mi. Teste |
| 16 | resultados | média | A aba `variantes_subsetores` rotulava as emissões E2 e E3 como "E1" e acusava "E1 fora da faixa" | reproduzido | Rótulo certo por variante; a faixa só se aplica ao E1 |
| 17 | resultados | baixa | Números do rascunho deste relatório: S05 do GAS-RS, repartição do choque, D10 e nº de testes | reproduzido | Corrigidos aqui |

**Verificação das correções.** Rodei um segundo workflow, com 3 revisores (números do relatório, teto do gás e bugs introduzidos pelas correções) e 1 cético por achado. Os 5 achados foram confirmados e corrigidos:
- dois números deste relatório: a D10 "sem o teto" e o gás importado tirado pelo passo (a);
- a nota da coluna `fonte`, que não separava o gás vindo do próprio grupo do vindo do transbordo do grupo "serviço";
- duas regressões das minhas correções:
  - os pesos explícitos de repartição (`--reparticao S38_DIS=…`) passaram a abortar qualquer execução que incluísse a MIP original. Agora só as chaves com o prefixo do setor chocado são conferidas;
  - o nome do `_coef_latentes.csv` divergia entre quem grava e quem lê quando o CSV não termina em `_longo.csv`. Agora uma função só define o nome.

  Ambas têm teste.
- O revisor do teto confirmou o resto:
  - o total por região é igual ao VBP do GAS;
  - nenhum comprador passa de 0.90;
  - os grupos são preservados;
  - depois do RAS, ninguém fica sem eletricidade, e o maior desvio das participações da D10 é 9e-5.

**Testes** (`python -m pytest`: **367 passaram, 0 falharam**):

| Teste | Resultado | O que verifica |
|---|---|---|
| T1 | passou | Hash da original |
| T2 | passou: Rodadas 01 e 02 + **9 especificações v02** | Re-agregação exata de Z, F, X, V e satélites, inclusive CO₂e na E1 e na E2 (na E3 o CO₂e difere só pelo resíduo) |
| T3–T8 | passaram | Como nas rodadas anteriores |
| **T9** | passou | v02: EOB ≥ η × VBP em todo subsetor com produção; Σ EOB de cada região = v01 = original; os 2 RAS do reequilíbrio convergiram. Com `_sem_viabilidade`: ALERTA; com `se_inviavel: erro`: erro explicativo |
| **T10** | passou | RS + RB = BEN por fonte (0.5 GWh) e as referências da Seção 2.1 |
| **T11** | passou | O executor (CSV `parametros/cenarios_exemplo.csv`) reproduz os 9 cenários e o top-10 do R1 da Rodada 01 |
| Novos do motor | passaram | Piso (VBP ≥ combustível ÷ κ, E_r preservado, cascata), combustíveis integrais, importações do RS na DIS, `fixa_por_tipo`, VBP do GAS por volume, alerta de multiplicador, leitor longo (ida e volta), repartição do choque do S38 |
| Correções da revisão | passaram | Nenhum comprador do S38 sem eletricidade (principal e `_gas_sulgas`); teto do gás (total e grupo preservados; grupo inteiro no teto); D10 sem o não energético; consumo específico do PET; validações novas; insumos fixos e pesos depois do reequilíbrio; variantes κ atuam; `_longo.csv` publicado com latentes; executor e linha de comando recusam entradas inválidas |

## 8. Acesso a fontes externas

Nenhum download novo. Os números novos vêm de arquivos baixados na Rodada 02b e foram conferidos no documento nesta rodada:
- MME, Boletim do gás nº 154, p. 16: distribuidoras sem o segmento termelétrico = 40.482 milhões m³/d (média 2019);
- DFP 2019 na CVM de Comgás, CEG e Gasmig: receita líquida de venda de gás e volume, sem térmico, construção e serviços;
- Sulgás, Nota 18.

A extração das DFP foi feita por um agente por empresa e conferida por dois verificadores céticos independentes; um dos verificadores da Gasmig parou por limite de sessão. Depois disso, conferi eu mesmo os números usados nas páginas citadas.

Também sem download novo, usei como evidência para o teto do gás (Seção 10, ponto 2), sem entrar na MIP:
- a coluna ELETRICIDADE da matriz do BEN 2020;
- a Tabela 2.15 do Anuário Estatístico de Energia Elétrica 2020 da EPE: tarifa média industrial de 2019 = 479.16 R$/MWh (ANEEL/SAD, mercado cativo).

## 9. Decisões tomadas por você nesta rodada

| Decisão | Alternativas consideradas | Por quê |
|---|---|---|
| **Piso de viabilidade:** piso_k = max(combustível ÷ κ, combustível ÷ (1 − η − φ_k)), em que φ_k é a parte do VBP que o RAS não pode mexer além do combustível (TUST, remunerações, impostos sobre a produção, células negativas e resíduo contábil) | (i) só o piso κ das instruções, com o EOB limitado ao possível (variante `_sem_viabilidade`); (ii) errar e parar | Com κ = 0.70 e η = 0.10, GN-RB, PET-RB e GN-RS não cabem: φ = 0.287 no RB e 0.276 no RS, e 0.70 + 0.287 > 0.90. A extensão é a menor mudança que cumpre (f), (r) e o T9, e mantém VBP ≥ combustível ÷ κ. O custo: os insumos não energéticos dessas três térmicas vão a ≈ 0 (Seção 10, ponto 1) |
| Preço do gás (b): média ponderada pelo volume, só venda de gás não térmica (sem construção nem serviços), nas 4 distribuidoras | Usar a receita total da Sulgás (com serviço) na média | Mesmo conceito nas 4. Com a receita total da Sulgás, o preço seria 1.933 em vez de 1.932 |
| Gasmig sem o térmico: deduções rateadas pela receita bruta | Pior caso (térmico sem deduções): 1.894 R$/m³ | A Gasmig não divulga deduções por segmento. Registrado como aproximação |
| D10, segmento "Serviço" da Sulgás (1.0%) → S19 (refino; transporte do gás da REFAP, HIPÓTESE) | Juntar à indústria | O volume de serviço (160.6 milhões m³) bate com o consumo próprio da Petrobras no RS (ANP). O S38-RS só vende 1.71 R$ mi ao S19-RS; o RAS fecha o resto |
| D10, residencial + comercial (6.5%) → famílias e S41–S68 juntos, na proporção das compras ao S38 | Residencial só às famílias e comercial só aos serviços | Leitura literal da instrução |
| (f): no RS, o S19 vai aos demais na proporção do VBP (regra explícita) | — | Instrução (o PET-RS é latente) |
| Remunerações e ocupações: a parte da geração (CEMPRE) acompanha o VBP final (`fixa_por_tipo`) | Manter as parcelas fixas da v01 (pesos P1) | Com os pisos, o VBP das térmicas muda; a regra do CEMPRE é "na proporção do VBP dentro da geração" |
| Combustível do GN = S05 × θ + importações de gás × θ (RB) | — | Instrução (f) |
| Todo `_longo.csv` (principal e variantes) ganha `_coef_latentes.csv` ao lado | Perder as colunas latentes | Para o executor ler qualquer versão com os latentes (revisão, achado 5) |
| **Teto do gás por comprador:** gás ≤ 0.90 das compras ao S38 (HIPÓTESE). O excedente vai aos demais compradores do mesmo grupo (D10 no RS; indústria do BEN no RB); se o grupo inteiro estiver no teto, aos demais compradores da região | (i) deixar a participação chegar a 1, com eletricidade zero (era o defeito); (ii) teto pela participação física do gás no gasto com gás + eletricidade (BEN × preços), que é de 0.07 a 0.30 na maioria dos ramos | 0.90 é a menor mudança que evita eletricidade zero e mantém a participação de cada grupo da D10 e do BEN. Com (ii), o excedente não caberia na indústria: o alvo de gás da indústria do RB é 20794.4, 64% das compras dela ao S38 (32738.0), e iria às famílias e aos serviços. Seção 10, ponto 2 |
| Importações do S38 sempre fixas no reequilíbrio (opção `ajustaveis` retirada) | Manter a opção | Pela regra do Comex, as importações do S38 são todas de energia (eletricidade e gás), que o D9-r manda manter fixas (revisão, achado 11) |
| Variantes κ só com o piso κ | Com a extensão de viabilidade | Com a viabilidade ligada, κ ≥ ≈ 0.62 não muda nada (revisão, achado 14) |
| Variante `_gas_sulgas` (VBP do GAS-RB pelo preço da Sulgás) | Só citar o valor | A instrução pede os dois preços; a variante mostra o efeito na MIP |
| Executor: choque num setor agregado (S38) repartido na proporção das vendas à demanda final, ou por pesos informados | Exigir sempre os subsetores no CSV | Mesma regra da prévia; aceita cenários escritos para a original |
| Decomposição v01 → v02 por passos cumulativos; no passo (f) só o piso κ, e a extensão de viabilidade entra com (r) | Tirar um item por vez da v02 | Sem (f), o (r) é inviável; a ordem das instruções é cumulativa. A extensão só existe junto com o reequilíbrio (o motor agora exige os dois juntos) |

## 10. Pontos para o Francisco

1. **Piso de viabilidade (decisão de método).**
   - **O problema.** Com κ = 0.70, o combustível já é 70% do VBP das térmicas a gás e a óleo. Somados TUST (≈ 16–18% do VBP, porque a TUST da geração é repartida na proporção do VBP), remunerações (≈ 7–12%) e impostos sobre a produção (≈ 1%), não sobram 10% para o EOB. Isso vale para GN-RB, PET-RB e GN-RS.
   - **O que fiz.** Elevei o piso até caber: o combustível fica em 61–62% do VBP.
   - **O preço.**
     - GN-RB fica em 264.5 R$/MWh, e não nos ≈ 230 da instrução.
     - PET-RB fica em 897.7 R$/MWh, e não nos ≈ 790.
     - Os insumos não energéticos dessas três térmicas (serviços, manutenção, impostos sobre produtos) vão a ≈ 0.
   - **A alternativa** com o piso κ puro (`_sem_viabilidade`) dá GN-RB 10981.9 e PET-RB 4066.6, mas com EOB de 1.3% (RB) e 2.4% (GN-RS), abaixo de η.
   - **Opções:**
     - (a) manter a extensão;
     - (b) aceitar EOB < η nessas três térmicas (piso puro);
     - (c) repartir a TUST da geração por capacidade ou energia (MW ou MWh), e não pelo VBP: as térmicas pagariam menos e caberiam com κ = 0.70;
     - (d) baixar κ: com κ = 0.60 só o piso κ já basta (variante `_k060`, EOB ≥ η em todos).

   Para comparar: só com o piso κ, κ = 0.70 dá EOB de 1.3% e κ = 0.80 dá EOB negativo (−8.7%) em GN-RB e PET-RB. Diga qual opção vale para a v03.
2. **Teto do gás por comprador (decisão nova, da revisão).**
   - **O problema.** Com o VBP do GAS-RB pelas 4 distribuidoras (26990.1, o dobro da v01), o gás que o BEN atribui a papel e celulose, química e siderurgia passa do que esses ramos compram do S38 na MIP. Exemplo: química RB, alvo de gás 4223.1 contra compras de 3953.6. Sem correção, esses ramos ficavam sem eletricidade.
   - **O que fiz.** O gás de cada comprador vai no máximo a 0.90 das compras dele ao S38 (HIPÓTESE), e o excedente vai aos demais do grupo.
     - No teto: 7 compradores no RB (S17, S21–S24, S26, S27) e 6 no RS (S04, S17, S19, S26, S27, S28).
     - Os demais ramos industriais do RB passam a ter de 0.38 a 0.52 das compras ao S38 em gás.
     - A participação de cada grupo da D10 e do BEN fica igual à do alvo.
   - **Evidência** (aba `gas_x_eletricidade_BEN`, indicativa, não entra na MIP). Pelo BEN 2020, com o preço médio do gás e a tarifa industrial média de 2019, o gás é de 0.07 a 0.30 do gasto com gás + eletricidade na maioria dos ramos: química 0.30, siderurgia 0.24, papel 0.15, alimentos 0.13. A cerâmica é a exceção (0.60). Ou seja, o VBP do GAS-RB pelas 4 distribuidoras não cabe nas compras industriais ao S38 da MIP com a estrutura do BEN: a indústria do RB compra 32738.0 do S38 e o alvo de gás dela é 20794.4 (64%).
   - **Com o preço da Sulgás** (variante `_gas_sulgas`: VBP do GAS-RB 19421.0; DIS-RB sobe na mesma medida), nenhum comprador do RB bate no teto. As térmicas e os multiplicadores do RS não mudam.
   - **Opções:**
     - (a) manter as 4 distribuidoras + teto 0.90 (a principal);
     - (b) preço da Sulgás (`_gas_sulgas`);
     - (c) no RB, repartir o gás pela estrutura de receita por segmento das distribuidoras, como a D10 faz no RS. Deve dar menos peso à indústria, porque o m³ industrial costuma ser mais barato que o residencial (não conferi). Os dados estão nas DFP já baixadas de Comgás, CEG e Gasmig;
     - (d) outro valor de teto.
3. **Multiplicador de produção acima de 2.2** em GN-RS (2.327), GAS-RS (2.344), PET-RB (2.620) e PET-RS latente (2.620). É estrutural: combustível comprado a setores com cadeia longa. Os da v01 eram maiores (2.555, 2.501, 2.854 e 2.857). Fica como ALERTA; diga se quer algum tratamento.
4. **D10:** com o teto, as participações ficam perto da Nota 18. Indústria + S19: 77.2%, contra 77.5% de indústria + cogeração + serviço. Famílias: 20.0%.
5. **Pendências que continuam:**
   - RAP 2019-2020 com fonte secundária (24883.4 R$ mi);
   - preço da BIO (206.05);
   - rótulos ONS × SIGA: agora só afetam o RS, porque o RB vem do BEN.
6. **Repositório público:** continua público. Não alterei.

## 11. Como reproduzir

```bash
pip install -r requirements.txt
python scripts/rodada02.py              # tratamento das fontes (Rodada 02b)
python scripts/rodada03.py              # D8: geração por fonte, reconciliação, consumo específico v02, BEN por setor
python scripts/rodada03_parametros.py   # parâmetros v02 (9 especificações)
python scripts/rodada03_mip.py          # MIP v02 + variantes, checagens, quadro e prévia (≈ 15 s)
python scripts/rodada03_decomposicao.py # v01 → v02 passo a passo
python scripts/rodar_cenarios.py        # executor: 9 cenários na original, v01 e v02
python -m pytest                        # 367 testes
```

## 12. Git

- Trabalho feito na `main` (a branch padrão), a partir de `c4817e9`. A branch antiga já não existe no GitHub; a cópia local foi deixada de lado.
- Commits da rodada: três de trabalho em andamento (o terceiro com o rascunho deste relatório) e o final, com as correções da revisão e este relatório. Push direto para a `main`; o resultado está na mensagem final da conversa.

## 13. Fontes de dados

Sem fontes novas de rede (ver Seção 8). Fontes usadas em números novos da v02:

| Fonte | Localização | Arquivo | Usada para |
|---|---|---|---|
| EPE, BEN 2020, Tabela 5.4 | PDF p. 112 | `dados/externos/epe/ben2020_tabela_5_4_v01.csv` (transcrição) | D8 |
| MME, Boletim do gás nº 154 (dez/2019) | p. 15–16 | `dados/externos/gas/mme_boletim_dez2019/boletim_gn_dez2019.pdf` | Volume não térmico do RB (D9-b) |
| Comgás, DFP 2019 (CVM, seq. 90958) | RA p. 14; nota 5 p. 27 | `dados/externos/brutos/gas/cvm_rad_comgas_dfp2019/` (fora do git) | Preço médio (D9-b) |
| CEG, DFP 2019 (CVM, seq. 91986) | Nota 22 p. 99 | `…/cvm_rad_ceg_dfp2019/` | Preço médio (D9-b) |
| Gasmig, DFP 2019 (CVM, seq. 92390) | Nota 19 p. 93 | `…/cvm_rad_gasmig_dfp2019/` | Preço médio (D9-b), aproximação |
| Sulgás, Demonstrações 2019 (CAGE/Sefaz-RS) | Nota 18, p. 86 | `dados/externos/gas/sulgas_segmentos_2019_v01.csv` | D10 e preço médio |
| EPE, BEN 2020, matriz consolidada | aba Consolidada, colunas GÁS NATURAL e ELETRICIDADE | `dados/externos/epe/ben_2020/BEN2020_Matriz_ab2019.xlsx` | Evidência para o teto do gás (não entra na MIP) |
| EPE, Anuário Estatístico de Energia Elétrica 2020 | Tabela 2.15, Industrial, 2019 | `dados/externos/epe/anuario_2020/…Workbook.xlsx` | Idem (tarifa média industrial) |

URLs, datas e SHA-256 em `dados/externos/valores_documentais_v02.csv` e nos `DOWNLOAD.txt`.

## 14. Comparação com os valores de referência

| Referência | Esperado | Obtido | Confere |
|---|---|---|---|
| D8, Brasil (BEN), 8 fontes | Seção 2.1 | idem | 8/8 |
| D8, RS (ONS), 8 fontes | HID 14542.6 · EOL 5266.9 · CAR 2625.2 · GN 174.6 · BIO 68.2 · demais 0 | 14542.55 · 5266.92 · 2625.22 · 174.56 · 68.23 · 0 | 8/8 |
| D8, RB = BEN − RS, 8 fontes | HID 363907.4 · EOL 50687.1 · SOL 4978 · BIO 1771.8 · CAR 11197.8 · GN 47422.4 · PET 5174 · NUC 16129 | 363907.45 · 50687.08 · 4978 · 1771.77 · 11197.78 · 47422.44 · 5174 · 16129 | 8/8 |
| (b) VBP do GAS-RB com 1.39 R$/m³ | ≈ 19421 | 19421.0 (preço da Sulgás; não usado) | sim |
| (f) GN-RB | ≈ 11000 R$ mi (≈ 230 R$/MWh) | κ puro: 10981.9 (231.6); principal: 12542.4 (264.5) | ordem de grandeza sim; a diferença é a viabilidade |
| (f) PET-RB | ≈ 4070 R$ mi (≈ 790 R$/MWh) | κ puro: 4066.6 (786.0); principal: 4644.4 (897.7) | idem |
| 9 cenários da Rodada 01 (executor, T11) | Rodada 01 | Idênticos, dentro das tolerâncias | 9/9 + top-10 do R1 |

**Reconciliação com o EPE** (`resultados/rodada03/reconciliacao_epe_v02.csv`): pela D8, RS + RB = BEN em todas as fontes (diferença 0). A montagem da 02b (ONS + isolados) ficava 10019.0 GWh acima do BEN: BIO +7500.2, HID +6889.2, EOL −2564.2, GN −948.4, SOL −593.4, PET −405.0.

## 15. Parâmetros

Em `parametros/quadro_parametros_v02.xlsx` (cada número com fonte e cálculo) e nos CSVs `parametros/*_v02.csv`. O que mudou em relação à v01:

| Parâmetro | v01 | v02 | Fonte / regra |
|---|---|---|---|
| GWh por fonte (RB) | ONS + isolados | BEN − RS | D8 |
| Importações do S38-RS | Comex nacional (44.3% DIS, 55.7% gás) | 100% DIS | D9-a |
| VBP do GAS-RB | 13539.8 (fallback ÷ 0.75) | 26990.1 = 1.9323 R$/m³ × 13967.8 milhões m³ | D9-b; DFP de 4 distribuidoras; MME p. 16 |
| S04 → CAR | teto 0.40 × VBP | 100%, sem teto | D9-f |
| S05 → GN/GAS | θ ao GN com teto 0.60 (excedente ao GAS) | θ ao GN sem teto; 1 − θ ao GAS | D9-f |
| S19 → PET | teto 0.60 | 100% no RB; no RS, aos demais na proporção do VBP | D9-f |
| S03 + S09 → BIO | teto comum 0.40 | 100% | D9-f |
| Piso de VBP | — | κ = 0.70 (HIPÓTESE) + viabilidade | D9-f |
| Reequilíbrio | — | η = 0.10 (HIPÓTESE) | D9-r |
| Gás por comprador no RS | BEN nacional | Nota 18 da Sulgás; indústria ∝ BEN sem o consumo não energético | D10 |
| Gás por comprador (RS e RB) | Participação limitada a 1 (eletricidade podia ir a zero) | Teto de 0.90 das compras ao S38; excedente no grupo | HIPÓTESE (revisão) |
| Consumo específico do PET (satélite energia) | 0.2655 tep/MWh (diesel + óleo) | 0.2712 (com as outras não renováveis) | BEN 2020, Tabela 5.4, mapeamento da D8 |
| Remunerações e ocupações da geração | Parcelas fixas pelos pesos P1 | Na proporção do VBP final (`fixa_por_tipo`) | CEMPRE |
| Sem mudança | RAP 24883.4; preços P1 (BIO 206.05); E1; latentes; α = 0.5; G = 0; θ_RS = 0.0512; θ_RB = 0.4309 | | |

**Pisos (aba `pisos_atingidos`):**

| Região | Subsetor | Combustível (R$ mi) | VBP pelos pesos P1 | Piso κ | φ | Piso de viabilidade | VBP final | Combustível ÷ VBP |
|---|---|---|---|---|---|---|---|---|
| RS | GN | 34.28 | 44.1 | 49.0 | 0.276 | 54.9 | **54.9** | 0.624 |
| RS | CAR | 14.75 | 675.8 | 21.1 | 0.276 | 23.6 | 674.1 | 0.022 |
| RS | BIO | 0.37 | 14.4 | 0.5 | 0.276 | 0.6 | 14.4 | 0.026 |
| RB | GN | 7687.35 | 9420.8 | 10981.9 | 0.287 | 12542.4 | **12542.4** | 0.613 |
| RB | PET | 2846.62 | 1083.3 | 4066.6 | 0.287 | 4644.4 | **4644.4** | 0.613 |
| RB | CAR | 226.23 | 2264.5 | 323.2 | 0.287 | 369.1 | 2023.0 | 0.112 |
| RB | BIO | 5.56 | 294.0 | 7.9 | 0.287 | 9.1 | 262.6 | 0.021 |

Só GN-RS, GN-RB e PET-RB ficam no piso. As demais fontes da região caem na proporção do VBP:
- **RB:** HID 48774.1 → 43572.3, EOL 7068.2 → 6314.3, SOL 1044.8 → 933.4, NUC 3214.3 → 2871.5, CAR 2264.5 → 2023.0, BIO 294.0 → 262.6.
- **RS:** HID 2481.2 → 2474.7, EOL 935.0 → 932.5, CAR 675.8 → 674.1.

O carvão compra pouco do S04 (D7 = A: a coluna do S38-RS copia a estrutura do RB), por isso o piso não o alcança.

**Reequilíbrio (aba `reequilibrio_RAS`):**

| Região | Subsetor | EOB/VBP antes → depois | Situação |
|---|---|---|---|
| RS | GN | −0.189 → 0.100 | elevado a η (ajustáveis a zero) |
| RS | GAS | −0.040 → 0.100 | elevado a η |
| RB | GN | −0.179 → 0.100 | elevado a η (ajustáveis a zero) |
| RB | PET | −0.179 → 0.100 | elevado a η (ajustáveis a zero) |
| RS | demais | HID/EOL 0.518 → 0.506; CAR 0.493 → 0.482; TRA 0.719 → 0.701; DIS 0.250 → 0.245 | cedem folga |
| RB | demais | HID/EOL/SOL/NUC 0.515 → 0.489; CAR 0.388 → 0.370; TRA 0.697 → 0.659; DIS 0.261 → 0.250; GAS 0.353 → 0.337 | cedem folga |

Valor movido (Σ|Δ| ÷ 2):
- **RS:** 141.5 R$ mi. Os maiores: ICMS 43.6, outros impostos 15.4, RS S53 9.5, RS S43 7.4.
- **RB:** 4797.7 R$ mi. Os maiores: ICMS 1546.7, outros impostos 546.6, RB S53 427.8, RB S31 293.9.

Convergência: RS em 7 iterações e RB em 8 (erro ≤ 2.1e-09).

## 16. Variantes

| Variante | O que muda | EOB/VBP mínimo | VBP GN-RB | VBP PET-RB | VBP GN-RS | Mult. máx. | Arquivos |
|---|---|---|---|---|---|---|---|
| **v02** (principal) | P1 + E1, κ 0.70, η 0.10 | 0.100 | 12542.4 | 4644.4 | 54.9 | 2.620 | .xlsx + CSV |
| v02_P2 | Preços iguais | 0.100 | 12542.4 | 4644.4 | 54.9 | 2.620 | .xlsx + CSV |
| v02_E2 | Emissões ∝ SEEG | 0.100 | idem | idem | idem | 2.620 | .xlsx + CSV |
| v02_E3 | Só níveis do SEEG (não preserva o total) | 0.100 | idem | idem | idem | 2.620 | .xlsx + CSV |
| v02_k060 | κ = 0.60, só o piso κ | 0.100 | 12812.3 | 4744.4 | 57.1 | 2.603 | CSV |
| v02_sem_viabilidade | κ = 0.70, só o piso κ (a regra das instruções) | **0.013** | 10981.9 | 4066.6 | 49.0 | 2.820 | CSV |
| v02_k080 | κ = 0.80, só o piso κ | **−0.087** | 9609.2 | 3558.3 | 44.1 | 3.050 | CSV |
| v02_eta005 | η = 0.05 | 0.050 | 11596.4 | 4294.1 | 50.8 | 2.734 | CSV |
| v02_gas_sulgas | VBP do GAS-RB pelo preço da Sulgás (19421.0) | 0.100 | 12542.4 | 4644.4 | 54.9 | 2.621 | CSV |

Leitura:
- **κ, só com o piso κ:**
  - 0.60: GN-RB 12812.3 e EOB ≥ η em todos (o piso κ basta);
  - 0.70: GN-RB 10981.9, com EOB de 1.3%;
  - 0.80: GN-RB 9609.2, com EOB negativo (−8.7%) em GN-RB e PET-RB e de −5.2% no GN-RS.
  - Com a extensão de viabilidade ligada, qualquer κ ≥ ≈ 0.62 dá a principal.
- **Preço da Sulgás:** o GAS-RB cai para 19421.0 (EOB/VBP 0.169) e a DIS-RB sobe na mesma medida. As térmicas não mudam, e nenhum comprador do RB fica no teto do gás.
- **P2:** com os pisos, GN e PET ficam iguais à principal. Só a repartição entre as renováveis e o carvão muda.
- **E2:** os fatores E2 saem fora das faixas (CAR > 1.6; GN > 0.65), como na v01. A aba `variantes_subsetores` agora rotula E2 e E3 corretamente.
- **Por subsetor:** os valores de todas as variantes estão na aba `variantes_subsetores` do quadro.

## 17. v01 × v02

**Efeito de cada item, aplicado em sequência** (`scripts/rodada03_decomposicao.py` → `resultados/rodada03/decomposicao_v01_v02.csv`; o último passo reproduz a v02 com diferença 0). No passo (f) entra só o piso κ das instruções; a extensão de viabilidade entra com (r), porque só existe junto com o reequilíbrio:

| Indicador | v01 | + D8 | + (a) | + (b) | + (f) | + (r) | + D10 = v02 |
|---|---|---|---|---|---|---|---|
| VBP GN-RB | 9054.1 | 9420.8 | 9420.8 | 9420.8 | 10981.9 | 12542.4 | 12542.4 |
| VBP PET-RB | 979.2 | 1083.3 | 1083.3 | 1083.3 | 4066.6 | 4644.4 | 4644.4 |
| VBP BIO-RB | 1508.8 | 294.0 | 294.0 | 294.0 | 272.7 | 262.6 | 262.6 |
| VBP HID-RB | 48737.6 | 48774.1 | 48774.1 | 48774.1 | 45236.8 | 43572.3 | 43572.3 |
| VBP GAS-RB | 13539.8 | 13539.8 | 13539.8 | 26990.1 | 26990.1 | 26990.1 | 26990.1 |
| VBP DIS-RB | 214309.1 | 214309.1 | 214309.1 | 200858.8 | 200858.8 | 200858.8 | 200858.8 |
| VBP GN-RS | 44.1 | 44.1 | 44.1 | 44.1 | 49.0 | 54.9 | 54.9 |
| t CO₂e/MWh CAR-RB | 0.856 | 0.867 | 0.867 | 0.867 | 0.867 | 0.867 | 0.867 |
| t CO₂e/MWh GN-RB | 0.441 | 0.433 | 0.433 | 0.433 | 0.433 | 0.433 | 0.433 |
| t CO₂e/MWh PET-RB | 0.900 | 0.829 | 0.829 | 0.829 | 0.829 | 0.829 | 0.829 |
| t CO₂e/MWh BIO-RB | 0.001 | 0.007 | 0.007 | 0.007 | 0.007 | 0.007 | 0.007 |
| EOB/VBP GN-RS | −0.817 | −0.817 | −0.161 | −0.161 | −0.275 | 0.100 | 0.100 |
| EOB/VBP GAS-RS | −0.646 | −0.646 | −0.050 | −0.050 | −0.040 | 0.100 | 0.100 |
| EOB/VBP GN-RB | −0.454 | −0.412 | −0.412 | −0.412 | −0.278 | 0.100 | 0.100 |
| EOB/VBP PET-RB | −0.165 | −0.153 | −0.153 | −0.153 | −0.278 | 0.100 | 0.100 |
| EOB/VBP GAS-RB | −0.112 | −0.112 | −0.112 | 0.345 | 0.353 | 0.337 | 0.337 |
| EOB/VBP BIO-RB | 0.503 | −0.002 | −0.002 | −0.002 | 0.492 | 0.466 | 0.466 |
| Nº de subsetores com EOB < 0 | 5 | 6 | 6 | 5 | 4 | 0 | 0 |
| Mult. produção RS GN | 2.555 | 2.555 | 2.555 | 2.555 | 2.722 | 2.327 | 2.327 |
| Mult. produção RS GAS | 2.501 | 2.501 | 2.501 | 2.500 | 2.486 | 2.344 | 2.344 |
| Mult. produção RS DIS | 1.884 | 1.885 | 1.885 | 1.884 | 1.893 | 1.896 | 1.896 |
| Mult. produção RS HID | 1.543 | 1.543 | 1.543 | 1.543 | 1.542 | 1.564 | 1.564 |
| Mult. produção RS PET (latente) | 2.857 | 2.857 | 2.857 | 2.856 | 3.085 | 2.620 | 2.620 |
| Mult. emissões RS GN (t/R$ mi) | 1813.6 | 1813.6 | 1813.6 | 1813.5 | 1653.9 | 1458.6 | 1458.6 |
| Mult. emissões RS DIS | 386.8 | 386.8 | 386.8 | 386.8 | 387.4 | 387.6 | 387.6 |
| Mult. emissões RS GAS | 224.8 | 224.8 | 224.8 | 224.7 | 223.8 | 213.8 | 213.8 |
| Mult. emissões RS PET (latente) | 4509.8 | 4088.7 | 4088.7 | 4088.7 | 1199.6 | 1034.4 | 1034.4 |
| Mult. emissões RS CAR | 5601.4 | 5601.4 | 5601.4 | 5601.4 | 5607.8 | 5617.5 | 5617.5 |

**Leitura, item a item:**
- **D8 (BEN − ONS)** muda os GWh do RB.
  - A BIO-RB cai de 9271.9 para 1771.8 GWh: o ONS incluía usinas de bagaço que o BEN conta como autoprodução. O VBP da BIO-RB cai de 1508.8 para 294.0, e o EOB dela fica negativo até (f) chegar.
  - PET-RB sobe para 5174 GWh (com as outras não renováveis); GN-RB sobe para 47422.4 (com os isolados a gás); SOL-RB sobe para 4978.
  - Fatores: PET-RB 0.900 → 0.829, GN-RB 0.441 → 0.433, CAR-RB 0.856 → 0.867 e BIO-RB 0.001 → 0.007, todos dentro das faixas. GWh e SEEG passam a cobrir o mesmo conjunto de usinas.
- **(a)** tira os 498.5 R$ mi de "gás importado" do GAS-RS (473.0) e do GN-RS (25.5); as importações da DIS-RS passam de 395.9 para 894.4. O EOB/VBP do GAS-RS vai de −0.646 para −0.050 e o do GN-RS de −0.817 para −0.161. A DIS-RS recebe as importações (EOB/VBP 0.289 → 0.250).
- **(b)** dobra o VBP do GAS-RB, cujo EOB/VBP vai de −0.112 para 0.345. A DIS-RB (resíduo) cai de 214309.1 para 200858.8. O gás por comprador do RB, já com o teto, entra aqui.
- **(f)** leva as compras de combustível inteiras às térmicas e aplica o piso κ:
  - GN-RB vai a 10981.9 (231.6 R$/MWh), PET-RB a 4066.6 (786.0 R$/MWh; diesel e óleo dos sistemas isolados) e GN-RS a 49.0;
  - as renováveis do RB perdem ≈ 7.3% do VBP: o R$/MWh da HID-RB cai de 134.0 para 124.3;
  - o EOB das três térmicas no piso fica em ≈ −28% do VBP;
  - o multiplicador de emissões do PET cai de 4088.7 para 1199.6 t/R$ mi, porque o VBP do PET quase quadruplica com as mesmas emissões; o do GN-RS cai de 1813.6 para 1653.9.
- **(r)** aplica a extensão de viabilidade do piso e o reequilíbrio:
  - GN-RB vai a 12542.4 (264.5 R$/MWh), PET-RB a 4644.4 (897.7) e GN-RS a 54.9; a HID-RB fica em 43572.3 (119.7 R$/MWh);
  - os EOB negativos somem: os insumos não energéticos saem das térmicas e do GAS-RS e vão aos demais, e as renováveis e a DIS ganham 1–2% de insumos;
  - caem os multiplicadores do GN-RS (2.722 → 2.327), do GAS-RS (2.486 → 2.344) e do PET (3.085 → 2.620); os das renováveis sobem um pouco (HID 1.542 → 1.564).
- **D10** só muda os compradores do GAS-RS, já com o teto. O efeito nos multiplicadores do RS fica abaixo de 0.001.

**Resumo por subsetor (v01 → v02):**

| Região | Subsetor | VBP | R$/MWh | t CO₂e/MWh E1 | EOB/VBP | Mult. produção | Mult. emissões (t/R$ mi) |
|---|---|---|---|---|---|---|---|
| RS | HID | 2481.2 → 2474.7 | 170.6 → 170.2 | 0 → 0 | 0.518 → 0.506 | 1.543 → 1.564 | 25.2 → 26.7 |
| RS | EOL | 935.0 → 932.5 | 177.5 → 177.1 | 0 → 0 | 0.518 → 0.506 | 1.543 → 1.564 | 25.2 → 26.7 |
| RS | SOL (latente) | 0 → 0 | — | — | — | 1.493 → 1.514 | 24.0 → 25.5 |
| RS | BIO | 14.4 → 14.4 | 211.2 → 210.7 | 0.000 → 0.000 | 0.489 → 0.478 | 1.606 → 1.626 | 40.6 → 42.1 |
| RS | CAR | 675.8 → 674.1 | 257.4 → 256.8 | 1.435 → 1.435 | 0.494 → 0.482 | 1.585 → 1.605 | 5601.4 → 5617.5 |
| RS | GN | 44.1 → 54.9 | 252.9 → 314.6 | 0.436 → 0.436 | −0.817 → 0.100 | 2.555 → 2.327 | 1813.6 → 1458.6 |
| RS | PET (latente) | 0 → 0 | — | — | — | 2.857 → 2.620 | 4509.8 → 1034.4 |
| RS | TRA | 1509.1 → 1509.1 | — | — | 0.719 → 0.701 | 1.295 → 1.322 | 22.1 → 24.0 |
| RS | DIS | 14384.3 → 14384.3 | — | — | 0.289 → 0.245 | 1.884 → 1.896 | 386.8 → 387.6 |
| RS | GAS | 898.7 → 898.7 | — | — | −0.646 → 0.100 | 2.501 → 2.344 | 224.8 → 213.8 |
| RB | HID | 48737.6 → 43572.3 | 131.4 → 119.7 | 0 → 0 | 0.507 → 0.489 | 1.491 → 1.513 | 25.3 → 27.0 |
| RB | EOL | 6581.0 → 6314.3 | 136.8 → 124.6 | 0 → 0 | 0.507 → 0.489 | 1.491 → 1.513 | 25.3 → 27.0 |
| RB | SOL | 902.5 → 933.4 | 205.8 → 187.5 | 0 → 0 | 0.507 → 0.489 | 1.491 → 1.513 | 25.3 → 27.0 |
| RB | BIO | 1508.8 → 262.6 | 162.7 → 148.2 | 0.001 → 0.007 | 0.503 → 0.466 | 1.500 → 1.562 | 35.8 → 87.0 |
| RB | CAR | 2248.7 → 2023.0 | 198.3 → 180.7 | 0.856 → 0.867 | 0.393 → 0.370 | 1.682 → 1.712 | 4357.2 → 4841.1 |
| RB | GN | 9054.1 → 12542.4 | 194.8 → 264.5 | 0.441 → 0.433 | −0.454 → 0.100 | 2.311 → 1.803 | 2341.7 → 1676.2 |
| RB | PET | 979.2 → 4644.4 | 205.3 → 897.7 | 0.900 → 0.829 | −0.165 → 0.100 | 2.854 → 2.620 | 4508.3 → 1031.7 |
| RB | NUC | 3152.2 → 2871.5 | 195.4 → 178.0 | 0 → 0 | 0.507 → 0.489 | 1.491 → 1.513 | 25.3 → 27.0 |
| RB | TRA | 23374.4 → 23374.4 | — | — | 0.689 → 0.659 | 1.286 → 1.325 | 22.9 → 26.0 |
| RB | DIS | 214309.1 → 200858.8 | — | — | 0.287 → 0.250 | 1.903 → 1.945 | 417.5 → 429.4 |
| RB | GAS | 13539.8 → 26990.1 | — | — | −0.112 → 0.337 | 2.011 → 1.647 | 284.6 → 262.1 |
