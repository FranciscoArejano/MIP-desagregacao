# Rodada 01 — Relatório do Claude Code

Projeto: desagregação do S38 na MIP inter-regional RS × RB, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
Data: 15/10/2026 · Instruções: `instrucoes/RODADA_01_instrucoes_CODE.md`
Convenção numérica: ponto decimal, sem separador de milhar.

## 1. Resumo

- A planilha original está protegida em `dados/original/`: somente leitura, SHA-256 **igual** ao de referência (`15e734a4…a3ea`), e o teste T1 confere o hash.
- O leitor (`src/mip/`) usa as coordenadas da Seção 5. Todas as identidades contábeis batem com a referência.
- Os 9 cenários foram reproduzidos: 81/81 comparações dentro da tolerância (maior diferença 0.0049, só arredondamento da tabela), e o top-10 do R1 confere. R4a e R4b estão reportados.
- Diagnóstico do S38: os 26 valores de referência conferem, e o peso do S38 nas emissões confere nos 9 cenários.
- O motor de desagregação genérico (regras de coluna, linha, bloco, primários/satélite, latentes, RAS, verificação, exportação no layout da original) passou em 56 testes, entre eles T1–T5. A MIP de teste usa **valores fictícios**.
- Fontes externas: ANEEL, ONS, CCEE, EPE, IBGE, SEEG e Base dos Dados foram **bloqueadas pela política de rede do ambiente** (403). Só o PyPI respondeu. É preciso liberar esses domínios antes da Rodada 2 (Seção 10).
- Pontos que precisam do Francisco (Seção 10): a coluna de insumos do S38-RS reproduz a estrutura do RB (quase não há compra de carvão); o repositório é **público**; e é preciso trocar a branch padrão do GitHub para `main`.

## 2. Status por etapa

| Etapa | Status | Observação |
|---|---|---|
| E1 — Organizar o repositório e proteger o original | concluída | Hash igual ao de referência. O anexo chegou com o nome alterado pelo sistema de upload; foi salvo com o nome original esperado (Seção 9). O `chmod 444` vale no disco local; o git não guarda essa permissão, por isso a proteção efetiva é o teste T1. |
| E2 — Ler a MIP e validar identidades | concluída | Todas as checagens batem. Detalhe na Seção 4: os resíduos de coluna dos "demais" setores chegam a 0.0087 (não exatamente ≈ 0), sempre abaixo de 6e-8 do VBP. |
| E3 — Reproduzir os resultados de referência | concluída | 81/81 comparações dentro da tolerância; top-10 do R1 confere; R4a e R4b reportados. |
| E4 — Diagnóstico do S38 | concluída | 26/26 valores de referência conferem; peso do S38 confere nos 9 cenários (diferença ≤ 0.04 p.p.). |
| E5 — Motor de desagregação e testes | concluída | 56 testes passando: 19 casos de T1–T5 e 37 complementares. A MIP de teste (fictícia) passa em todas as 24 checagens. |
| E6 — Teste de acesso a fontes externas | concluída (com bloqueio) | 7 das 8 fontes bloqueadas pela rede do ambiente (403 no proxy). Nada foi baixado e nada foi estimado no lugar. |
| E7 — Relatório | concluída | Este arquivo, `respostas/HISTORICO.md` e `README.md`. |

## 3. Arquivos criados, movidos ou alterados

| Caminho | Tipo | O que é | Etapa |
|---|---|---|---|
| `dados/original/Matrtiz_Insumo-Produto_RS_RB_com_emissões.xlsx` | dado (somente leitura) | Planilha original, salva a partir do anexo sem alteração de conteúdo | E1 |
| `dados/original/CHECKSUM.txt` | texto | SHA-256 da original | E1 |
| `instrucoes/RODADA_01_instrucoes_CODE.md` | texto | Cópia das instruções da rodada (veio como anexo) | E1 |
| `README.md` | texto (alterado) | Descrição do projeto, estrutura, como rodar e status | E1, E7 |
| `requirements.txt` | config | pandas, numpy, openpyxl, pytest, pyyaml | E1 |
| `.gitignore` | config | Caches e `__pycache__`, `.venv`; não ignora `.xlsx` | E1 |
| `pytest.ini` | config | Pasta de testes | E1 |
| `tests/conftest.py` | teste | Coloca `src/` no caminho de importação | E1 |
| `tests/test_t1_hash.py` | teste | T1: hash da original e conferência do CHECKSUM.txt | E1 |
| `src/mip/__init__.py` | código | Pacote `mip` | E2 |
| `src/mip/caminhos.py` | código | Caminhos padrão do repositório | E2 |
| `src/mip/estrutura.py` | código | Classe `MIP`, layout (coordenadas) e constantes | E2 |
| `src/mip/leitura.py` | código | Leitor da planilha e formato longo | E2 |
| `src/mip/validacao.py` | código | Checagens das identidades contábeis | E2 |
| `tests/test_leitura_validacao.py` | teste | Dimensões, rótulos, identidades, negativos, formato longo | E2 |
| `scripts/rodada01.py` | script | Gera todas as saídas da rodada (E2–E5) | E2–E5 |
| `dados/intermediarios/mip_original_longo.csv` | dado derivado | MIP original em formato longo (21815 linhas) | E2 |
| `resultados/rodada01/validacao_mip_original_v01.csv` | resultado | Checagens da Etapa 2 | E2 |
| `src/mip/modelo.py` | código | Modelo de Leontief genérico (A, L, emissões, diretas/indiretas, recortes, ranking, latentes) | E3 |
| `src/mip/referencia.py` | código | Cenários e valores de referência da rodada | E3 |
| `src/mip/exportacao.py` | código | Tabelas `.xlsx`, MIP `.xlsx` no layout da original, CSV longo | E3, E5 |
| `tests/test_replicacao.py` | teste | 9 cenários, top-10 R1, propriedades de L, peso do S38 | E3 |
| `resultados/rodada01/replicacao_v01.xlsx` | resultado | Uma aba por cenário + resumo esperado × obtido × diferença + top-10 | E3 |
| `src/mip/diagnostico.py` | código | Insumos, vendas, bloco intrassetorial, primários/satélite, peso nas emissões | E4 |
| `tests/test_diagnostico.py` | teste | Valores de referência do diagnóstico | E4 |
| `resultados/rodada01/diagnostico_S38_v01.xlsx` | resultado | Diagnóstico do S38-RS e do S38-RB | E4 |
| `src/mip/desagregacao.py` | código | Motor de desagregação, especificação, RAS, re-agregação e verificação | E5 |
| `parametros/LEIAME_parametros.md` | documentação | Formato das especificações (YAML + CSVs) | E5 |
| `parametros/TESTE_especificacao.yaml` | parâmetro fictício | Especificação de teste (8 subsetores provisórios) | E5 |
| `parametros/TESTE_subsetores.csv` | parâmetro fictício | Lista provisória de subsetores | E5 |
| `parametros/TESTE_participacoes_vbp.csv` | parâmetro fictício | Participações no VBP (fictícias) | E5 |
| `parametros/TESTE_regras_coluna.csv` | parâmetro fictício | Regras de repartição dos insumos | E5 |
| `parametros/TESTE_regras_linha.csv` | parâmetro fictício | Regras de repartição das vendas | E5 |
| `parametros/TESTE_regras_primarios.csv` | parâmetro fictício | Regras dos insumos primários e contas satélite | E5 |
| `parametros/TESTE_coef_latentes.csv` | parâmetro fictício | Coluna de coeficientes do subsetor latente (S38_SOL no RS) | E5 |
| `tests/auxiliares.py` | teste | Geradores de especificações (neutra e aleatória) e MIP de 3 setores | E5 |
| `tests/test_desagregacao.py` | teste | T2–T5, RAS, EOB negativo, especificações inválidas, latentes | E5 |
| `tests/test_exportacao.py` | teste | Exportação reproduz a original célula a célula; releitura sem perda | E5 |
| `resultados/rodada01/teste/MIP_TESTE_valores_ficticios_NAO_USAR.xlsx` | resultado fictício | MIP de teste (150 setores-região) no layout da original + abas extras | E5 |
| `resultados/rodada01/teste/MIP_TESTE_valores_ficticios_NAO_USAR_longo.csv` | resultado fictício | A mesma MIP de teste em formato longo | E5 |
| `resultados/rodada01/teste/checagens_TESTE_v01.csv` | resultado fictício | Checagens da MIP de teste | E5 |
| `scripts/rodada01_teste_fontes.py` | script | Teste de acesso às fontes externas (depende de rede) | E6 |
| `dados/externos/FONTES.md` | documentação | Registro de fontes e resultado do teste de acesso | E6 |
| `dados/externos/rodada01_teste/acesso_fontes_rodada01.csv` | registro | URL, horário, status e erro de cada fonte | E6 |
| `respostas/RODADA_01_resposta.md` | relatório | Este relatório | E7 |
| `respostas/HISTORICO.md` | relatório | Histórico das rodadas | E7 |

Nenhum arquivo foi movido com `git mv`: a planilha e as instruções vieram como anexos da conversa, e o repositório só tinha `README.md`.

## 4. Validação da MIP original

Arquivo: `resultados/rodada01/validacao_mip_original_v01.csv`.

| Checagem | Esperado | Obtido |
|---|---|---|
| Linha: Σ Z + Σ demanda final (EK:EU) − total (EV) | máx ≈ 7e-10 | 6.985e-10 (RB S42) |
| Coluna: Σ Z + importações + impostos (147–149) + VA (151) − VBP (156) | máx ≈ 0.0095 (RB S40); demais ≈ 0 | 0.009486 (RB S40 Construção). Demais: maior 0.0087 (RB S19); mediana 3.1e-4; 32 setores com \|dif\| > 1e-3; maior \|dif\|/VBP = 5.3e-8 |
| VA − (remunerações + EOB + impostos sobre a produção) | ≈ 1e-10 | 1.164e-10 |
| VBP (linha 156) − total da linha (EV) | 0 | 0 (exatamente) |
| Setores com VBP = 0 | RS S05, RS S06, RS S07, RS S20 | RS S05, RS S06, RS S07, RS S20 (linhas e colunas zeradas) |
| Valores negativos | EU: 65 células, mín −5987.45; 153: RS S09, RB S09; 154: RS S01, RB S01 | EU: 65 células, mín −5987.45; EOB: RS S09 (−3.50), RB S09 (−1231.50); 154: RS S01 (−646.30), RB S01 (−4883.70). Nenhum outro negativo |
| [extra] Colunas de DF: Σ linhas + importações + impostos − total (linha 156) | — | máx 0.0139 (GOV_RB) |
| [extra] Coluna EV das linhas 144–156 | — | Bate com a soma de cada linha (≤ 5e-9). Na linha 156, EV = Σ VBP + importações + impostos de todas as colunas = oferta total (dif 0.0014) |
| [extra] Totais satélite | — | ocupações 105995759; CO₂e 1836705849.28 t; água 298198.73 hm³; energia 216869.54 mil tep |

Observação: a referência dizia "demais ≈ 0" para os resíduos de coluna. Eles não são exatamente zero (até 0.0087), mas são resíduos de arredondamento: remunerações e EOB parecem gravados em precisão simples (ex.: 3838.328125). Não atrapalham nada. O motor de desagregação reparte o resíduo original de cada coluna do S38 pelo VBP, o que mantém a re-agregação exata.

## 5. Reprodução dos resultados

Arquivo: `resultados/rodada01/replicacao_v01.xlsx` (aba `resumo_esperado_obtido` com as 81 comparações; uma aba por cenário).
Tolerâncias: 0.01 R$ mi, 1 t CO₂e e 0.005 em IC e percentuais (metade da última casa informada). **Todas as 81 comparações estão dentro da tolerância.**

Cada célula: esperado → obtido (diferença).

| Cenário | ΔX total | ΔX RS | ΔX RB | CO₂e total | CO₂e RS | CO₂e RB |
|---|---|---|---|---|---|---|
| E1 | 1925.04 → 1925.0372 (−0.0028) | 1357.01 → 1357.0119 (+0.0019) | 568.03 → 568.0253 (−0.0047) | 428113.53 → 428113.5341 (+0.0041) | 339326.41 → 339326.4139 (+0.0039) | 88787.12 → 88787.1202 (+0.0002) |
| R1 | 1959.35 → 1959.3530 (+0.0030) | 1391.32 → 1391.3153 (−0.0047) | 568.04 → 568.0377 (−0.0023) | 216406.97 → 216406.9711 (+0.0011) | 142390.03 → 142390.0253 (−0.0047) | 74016.95 → 74016.9458 (−0.0042) |
| F1 | 2120.56 → 2120.5583 (−0.0017) | 1373.23 → 1373.2338 (+0.0038) | 747.32 → 747.3244 (+0.0044) | 356045.72 → 356045.7240 (+0.0040) | 277141.45 → 277141.4460 (−0.0040) | 78904.28 → 78904.2780 (−0.0020) |
| R2 | 1920.37 → 1920.3710 (+0.0010) | 1399.36 → 1399.3628 (+0.0028) | 521.01 → 521.0083 (−0.0017) | 216987.16 → 216987.1566 (−0.0034) | 153932.23 → 153932.2325 (+0.0025) | 63054.92 → 63054.9241 (+0.0041) |
| R3 | 1969.21 → 1969.2062 (−0.0038) | 1396.49 → 1396.4902 (+0.0002) | 572.72 → 572.7160 (−0.0040) | 169090.02 → 169090.0151 (−0.0049) | 95597.22 → 95597.2189 (−0.0011) | 73492.80 → 73492.7962 (−0.0038) |
| R4a | 1959.49 → 1959.4883 (−0.0017) | 1395.81 → 1395.8137 (+0.0037) | 563.67 → 563.6746 (+0.0046) | 309794.88 → 309794.8843 (+0.0043) | 236133.84 → 236133.8368 (−0.0032) | 73661.05 → 73661.0475 (−0.0025) |
| R4b | 1950.48 → 1950.4824 (+0.0024) | 1387.14 → 1387.1379 (−0.0021) | 563.34 → 563.3445 (+0.0045) | 304336.55 → 304336.5492 (−0.0008) | 228514.51 → 228514.5086 (−0.0014) | 75822.04 → 75822.0406 (+0.0006) |
| F2 | 2110.49 → 2110.4861 (−0.0039) | 1392.22 → 1392.2197 (−0.0003) | 718.27 → 718.2665 (−0.0035) | 381702.86 → 381702.8635 (+0.0035) | 306553.93 → 306553.9279 (−0.0021) | 75148.94 → 75148.9356 (−0.0044) |
| F3 | 2073.93 → 2073.9295 (−0.0005) | 1371.35 → 1371.3473 (−0.0027) | 702.58 → 702.5822 (+0.0022) | 375427.26 → 375427.2603 (+0.0003) | 294592.52 → 294592.5201 (+0.0001) | 80834.74 → 80834.7403 (+0.0003) |

| Cenário | IC (t/R$ mi) | % CO₂e no RB | % indiretas | CO₂e diretas (t) | CO₂e indiretas (t) |
|---|---|---|---|---|---|
| E1 | 222.39 → 222.3923 (+0.0023) | 20.74 → 20.7392 (−0.0008) | 34.89 → 34.8861 (−0.0039) | 278761.44 | 149352.10 |
| R1 | 110.45 → 110.4482 (−0.0018) | 34.20 → 34.2027 (+0.0027) | 51.55 → 51.5467 (−0.0033) | 104856.30 | 111550.67 |
| F1 | 167.90 → 167.9019 (+0.0019) | 22.16 → 22.1613 (+0.0013) | 35.34 → 35.3371 (−0.0029) | 230229.47 | 125816.26 |
| R2 | 112.99 → 112.9923 (+0.0023) | 29.06 → 29.0593 (−0.0007) | 46.11 → 46.1065 (−0.0035) | 116941.95 | 100045.21 |
| R3 | 85.87 → 85.8671 (−0.0029) | 43.46 → 43.4637 (+0.0037) | 62.70 → 62.7012 (+0.0012) | 63068.57 | 106021.45 |
| R4a | 158.10 → 158.0999 (−0.0001) | 23.78 → 23.7774 (−0.0026) | 39.04 → 39.0423 (+0.0023) | 188843.81 | 120951.07 |
| R4b | 156.03 → 156.0314 (+0.0014) | 24.91 → 24.9139 (+0.0039) | 40.31 → 40.3054 (−0.0046) | 181672.63 | 122663.92 |
| F2 | 180.86 → 180.8602 (+0.0002) | 19.69 → 19.6878 (−0.0022) | 32.87 → 32.8677 (−0.0023) | 256246.09 | 125456.78 |
| F3 | 181.02 → 181.0222 (+0.0022) | 21.53 → 21.5314 (+0.0014) | 34.97 → 34.9660 (−0.0040) | 244155.26 | 131272.01 |

R4a e R4b são duas versões do mesmo cenário. As duas estão reportadas acima, e não escolhi entre elas.

Top-10 do R1 (esperado | obtido). Todas as 10 linhas conferem: mesma ordem, mesmo setor e mesmos valores na precisão informada.

| # | Região | Setor | ΔX esp. | ΔX obt. | CO₂e esp. | CO₂e obt. | % esp. | % obt. |
|---|---|---|---|---|---|---|---|---|
| 1 | RS | S38 | 357.1 | 357.1 | 99554.6 | 99554.6 | 46.0 | 46.0 |
| 2 | RS | S43 | 84.1 | 84.1 | 35489.9 | 35489.9 | 16.4 | 16.4 |
| 3 | RB | S38 | 92.0 | 92.0 | 23960.2 | 23960.2 | 11.1 | 11.1 |
| 4 | RB | S27 | 46.8 | 46.8 | 11392.4 | 11392.4 | 5.3 | 5.3 |
| 5 | RB | S43 | 16.4 | 16.4 | 7311.5 | 7311.5 | 3.4 | 3.4 |
| 6 | RB | S26 | 15.3 | 15.3 | 6949.7 | 6949.7 | 3.2 | 3.2 |
| 7 | RB | S28 | 34.1 | 34.1 | 5082.2 | 5082.2 | 2.3 | 2.3 |
| 8 | RB | S39 | 4.7 | 4.7 | 4646.4 | 4646.4 | 2.1 | 2.1 |
| 9 | RB | S03 | 1.0 | 1.0 | 3085.0 | 3085.0 | 1.4 | 1.4 |
| 10 | RB | S01 | 3.5 | 3.5 | 2649.5 | 2649.5 | 1.2 | 1.2 |

## 6. Diagnóstico do S38

Arquivo: `resultados/rodada01/diagnostico_S38_v01.xlsx`. Abas: `resumo_referencia`, `insumos_S38_RS/RB` (insumos energéticos destacados), `vendas_S38_RS/RB`, `bloco_S38_S38`, `bloco_S38_resumo`, `primarios_satelite` e `peso_nas_emissoes`.

| Item | S38-RS (ref. → obtido) | S38-RB (ref. → obtido) |
|---|---|---|
| VBP | 20942.66 → 20942.66 | 324387.34 → 324387.34 |
| Consumo intermediário (Σ coluna de Z) | 10462.3 → 10462.29 | 159881.3 → 159881.29 |
| Importações | 894.4 → 894.40 | 13667.96 → 13667.96 |
| VA | 8081.27 → 8081.27 | 127843.73 → 127843.73 |
| CO₂e (t) | 5838005.55 → 5838005.55 | 84518349.06 → 84518349.06 |
| t CO₂e por R$ mi | 278.76 → 278.76 | 260.55 → 260.55 |
| Ocupações | 15012 → 15012 | 151807 → 151807 |
| Energia (mil tep) | 503.96 → 503.96 | 7805.92 → 7805.92 |
| Água (hm³) | 6.79 → 6.79 | 67.61 → 67.61 |
| Vendas ao S38 das duas regiões | 5659.7 (27.0%) → 5659.65 (27.02%) | 96538.4 (29.8%) → 96538.40 (29.76%) |

Bloco S38→S38 (R$ mi; linha = vendedor): RS→RS 3057.11 · RS→RB 2602.55 · RB→RS 3220.23 · RB→RB 93318.17 (todos conferem).
Compras do S38 às duas regiões: RS 6277.34 (29.97% do VBP); RB 95920.72 (29.57%).

Peso do S38 (RS + RB) nas emissões induzidas, em %, esperado → obtido: E1 92.2 → 92.22 · R1 57.1 → 57.08 · F1 39.4 → 39.43 · R2 32.8 → 32.77 · R3 38.8 → 38.77 · R4a 58.5 → 58.52 · R4b 66.0 → 65.99 · F2 35.1 → 35.10 · F3 53.0 → 53.04.

Outros números-chave:
- **Insumos (coluna).** Nas duas regiões o maior insumo é o próprio S38: RS 6277.3 (60.0% do CI); RB 95920.7 (60.0%). Depois vem petróleo e gás (S05) do RB: RS 668.9 (6.4% do CI); RB 10224.2 (6.4%).
- **Insumos energéticos** (S01, S03, S04, S05, S09, S16, S19, S20, das duas origens) somam 8.58% do CI nas **duas** regiões: RS 897.7; RB 13720.9. O carvão e os minerais não metálicos (S04) comprados pelo S38-RS somam só 14.7 R$ mi (RS 7.6 + RB 7.1), e os derivados de petróleo (S19), 186.4.
- **Vendas (linha).** RS: 66.3% vão ao consumo intermediário e 33.7% à demanda final. Os maiores destinos são Famílias RS (17.9%), Famílias RB (15.8%), S38-RS (14.6%) e S38-RB (12.4%). RB: 66.9% / 33.1%; Famílias RB 31.8% e S38-RB 28.8%.
- **Primários e satélite por R$ mi de VBP.** RS: VA 0.386; remunerações 0.055; EOB 0.322; importações 0.043; impostos sobre produtos 0.072; 0.717 ocupações; 278.76 t CO₂e; 0.024 mil tep. RB: VA 0.394; remunerações 0.065; EOB 0.320; importações 0.042; impostos 0.071; 0.468 ocupações; 260.55 t CO₂e; 0.024 mil tep.

## 7. Motor de desagregação

**Organização** (`src/mip/desagregacao.py`):
- `Especificacao` / `ler_especificacao(yaml)`: lê o YAML com as opções e os CSVs (subsetores, participações no VBP, regras de coluna, de linha, de primários/satélite e coeficientes latentes). O formato está em `parametros/LEIAME_parametros.md`. Curingas `*`; a regra mais específica vence; empate é erro; sem regra, vale `proporcional_vbp`.
- `desagregar(mip, espec, estrito=True)` → `ResultadoDesagregacao`, com a MIP nova, o mapa de setores, os pesos usados (com fonte), o relatório do RAS e as checagens. A função monta os blocos assim:
  - fora × fora: cópia;
  - colunas: `proporcional_vbp`, `fixa` ou `indicador`;
  - bloco S38→S38: `proporcional` ou `geracao_vende_para_rede` (os 4 fluxos RS↔RB são respeitados; a rede compra toda a energia);
  - linhas: `proporcional_vbp`, `somente_rede_e_gas` ou `fixa_por_comprador`, mais **RAS** para fechar o VBP de cada subsetor;
  - primários e satélite: `proporcional_vbp`, `fixa` ou `indicador`; **EOB é o resíduo**; VA = rem. + EOB + imp. produção;
  - subsetores **latentes**: produção zero e coluna de coeficientes guardada à parte, que entra em `ModeloLeontief`.
- Regiões não desagregadas ficam com o S38 agregado (D2 coberta: RS e RB, só RS ou só RB).
- `modo_vbp`: `participacoes` (VBP = participação × VBP do S38) ou `ancora_bloco`. Na âncora, o VBP total da geração de cada região é igual às vendas do S38 dessa região ao S38 das duas regiões (RS 27.02%, RB 29.76%). Isso só **suporta** a D3, não a decide.
- `ras(M0, alvo_linhas, alvo_colunas, fixas, tol, max_iter)`: utilitário biproporcional genérico que reporta necessidade, convergência, iterações e erro.
- Especificações incoerentes param com uma mensagem explicativa: valores fixos em subsetor de produção zero, participações que não somam 1, regras ambíguas, linha impossível de fechar.
- `verificar(res)` roda sempre ao final da desagregação:
  - re-agregação célula a célula (1e-6);
  - balanço de linha e de coluna de cada subsetor;
  - identidade do VA;
  - não negatividade (exceto onde a original já tem negativos);
  - totais satélite;
  - EOB ≥ 0 (**ALERTA**, nunca corrigido);
  - subsetores de produção zero zerados;
  - L ≥ 0 e diag(L) ≥ 1 (com as colunas latentes);
  - convergência do RAS.
- `src/mip/exportacao.py` gera o `.xlsx` no **mesmo layout** da original: títulos, cabeçalhos, rótulos, linhas de totais com fórmulas e contas satélite, com os subsetores no lugar do S38. Abas extras: `LEIAME`, `mapa_setores`, `parametros`, `checagens`, `ras` e `coef_latentes`. Também gera o CSV longo. Prova do layout: exportar a MIP original reproduz a planilha original **célula a célula** (valores, fórmulas e mesclagens; teste `test_exportar_original_reproduz_a_planilha_celula_a_celula`).

**Como usar:**

```bash
python scripts/rodada01.py   # roda tudo, inclusive a desagregação de teste
```
```python
import sys; sys.path.insert(0, "src")
from mip.leitura import ler_mip_original
from mip.desagregacao import ler_especificacao, desagregar
res = desagregar(ler_mip_original(), ler_especificacao("parametros/TESTE_especificacao.yaml"))
res.checagens; res.exportar("saida.xlsx", "saida_longo.csv")
```

**MIP de teste (valores fictícios):** `resultados/rodada01/teste/MIP_TESTE_valores_ficticios_NAO_USAR.xlsx`, com 150 setores-região (8 subsetores × 2 regiões).
- Opções usadas: `geracao_vende_para_rede` + `ancora_bloco`, linha `somente_rede_e_gas`, Famílias com `fixa_por_comprador` (fixas no RAS), regras `fixa` e `indicador` em colunas e satélite, S38_SOL-RS latente e S38_NUC-RS com produção zero.
- Resultado: 24/24 checagens OK; RAS necessário nas duas regiões e convergido; a releitura do `.xlsx` bate com a matriz em memória (máx \|dif\| 5.8e-11, precisão de gravação).
- Marcação "TESTE — VALORES FICTÍCIOS" no nome do arquivo, na aba `LEIAME`, na célula A3 e no título (A1) da aba principal.

**Testes** (`python -m pytest`: **56 passaram, 0 falharam**):

| Teste | Resultado | O que verifica |
|---|---|---|
| T1 — hash | passou (2 testes) | SHA-256 da original = referência; CHECKSUM.txt confere |
| T2 — re-agregação exata | passou (12 casos) | Especificação TESTE + 8 especificações aleatórias (todas as regras) + desagregação só no RS, só no RB e nas duas. Todas as células re-agregam com tolerância 1e-6 (obtido ~1e-11). Fora dos testes, rodei também 600 especificações aleatórias: todas re-agregaram e o RAS convergiu (máx 18 iterações) |
| T3 — desagregação neutra | passou (K = 2, 5, 8) | 9 cenários com choque do S38 repartido arbitrariamente (até zerando subsetores): ΔX total/RS/RB, CO₂e total/RS/RB, diretas, indiretas, IC e % indiretas iguais aos da original (1e-6; obtido ~1e-10) |
| T4 — subsetor latente | passou | MIP de 3 setores: fluxos-base inalterados; choque unitário no latente dá ΔX = [0.09, 0.09, 0.1, 1] (multiplicador 1.28) e 2.087 t, calculados à mão no teste; L dos setores existentes inalterada |
| T5 — geração vende para a rede | passou | Na MIP de teste, a soma das vendas da geração é igual às vendas originais ao S38 das duas regiões. A geração não vende a nenhum outro setor nem à demanda final, vende só à rede, os 4 fluxos RS↔RB são respeitados e a rede compra todo o bloco |
| Complementares | passaram (37) | Leitura/identidades (9), replicação (14), diagnóstico (3), exportação (3), RAS (3: converge com células fixas, inviável reporta não convergência, não necessário), EOB negativo vira ALERTA e não é corrigido, especificações inválidas, inconsistência com `geracao_vende_para_rede` dá erro claro e fecha com `ancora_bloco`, latente na MIP real, modo estrito |

## 8. Acesso a fontes externas

Script: `scripts/rodada01_teste_fontes.py`. Registro: `dados/externos/rodada01_teste/acesso_fontes_rodada01.csv` e `dados/externos/FONTES.md`. Data: 15/10/2026 (UTC).

| Fonte | Acessível? | O que foi baixado | Observação |
|---|---|---|---|
| ANEEL – Dados Abertos (SIGA) | não | nada | 403 no proxy do ambiente (`dadosabertos.aneel.gov.br`) |
| ONS – Dados Abertos | não | nada | 403 (`dados.ons.org.br`) |
| CCEE – Dados Abertos | não | nada | 403 (`dadosabertos.ccee.org.br`) |
| EPE (Anuário; BEN) | não | nada | 403 (`www.epe.gov.br`) |
| IBGE – API SIDRA | não | nada | 403 (`apisidra.ibge.gov.br`) |
| SEEG | não | nada | 403 (`seeg.eco.br` e `plataforma.seeg.eco.br`) |
| Base dos Dados (RAIS) | não | nada | 403 (`basedosdados.org`); nenhuma credencial criada |
| PyPI | sim (200) | nada (não é fonte de dados) | `pip install pytest` funcionou |

O bloqueio vem da política de rede do ambiente de nuvem do Claude Code, não das instituições.

## 9. Decisões tomadas por você nesta rodada

Só decisões de implementação.

| Decisão | Alternativas consideradas | Por quê |
|---|---|---|
| Salvar a planilha como `Matrtiz_Insumo-Produto_RS_RB_com_emissões.xlsx` | Manter o nome do anexo (`f1a2bc66-Matrtiz_Insumo-Produto_RS_RB_com_emiss_es.xlsx`) | O sistema de upload acrescentou o prefixo e trocou o "õ" por "_". O conteúdo é idêntico (hash confere), e as instruções dão o nome esperado (forma Unicode NFC). |
| Proteção da original por `chmod 444` + teste T1 | Só o chmod | O git não versiona a permissão de leitura; o T1 garante a proteção em qualquer clone. |
| Pacote `src/mip/` com 9 módulos e a classe `MIP` (arrays numpy + rótulos) | DataFrames rotulados em tudo | O mesmo objeto serve à original e à desagregada; álgebra direta e rápida (desagregação em ~0.05 s). |
| Leitor detecta n pela linha "Importações internacionais" e confere rótulos e cabeçalhos | Só coordenadas fixas | Na original, as coordenadas são exatamente as da Seção 5 (conferidas). Detectar n permite reler as MIPs exportadas, que têm outro tamanho. |
| Formato longo com 7 colunas (`bloco`, …, `valor`, `unidade`), incluindo zeros, primários, VBP e satélite | Só Z e DF, com 5 colunas | Um único arquivo com a MIP inteira, fácil de filtrar e pivotar. |
| `mip_original_longo.csv` sem sufixo `_v01` | Pôr `_v01` | É o nome pedido na Etapa 2, e o arquivo é uma transformação determinística da original intocável. As saídas de resultado levam `_v01`. |
| Tolerância de 0.005 para IC e percentuais na replicação; 0.05 no top-10; no diagnóstico, metade da última casa informada | Exigir igualdade nas casas informadas | Os valores de referência vêm arredondados; a meia unidade da última casa é o critério natural. Para ΔX e CO₂e usei as tolerâncias dadas (0.01 e 1 t). |
| Especificação em YAML + CSVs, com curingas e regra mais específica vencendo | Um único Excel; Python | Legível, versionável e com campo de fonte em cada linha. Os CSVs são editáveis em Excel. |
| Resíduos contábeis originais repartidos pelo VBP (coluna e identidade do VA) ao calcular o EOB residual | Ignorar os resíduos | Mantém a re-agregação **exata** do EOB e do VA (sem isso sobrariam diferenças de até 0.0017 no S38-RB). |
| RAS só nas linhas dos subsetores; bloco S38→S38 e células negativas (discrepância, ex.: RB S38 EU = −16.15) sempre fixos; tolerância 1e-8 | RAS na matriz inteira | As colunas já fecham pelo EOB residual; o RAS só precisa reconciliar as vendas com o VBP de cada subsetor. RAS não lida com negativos. |
| Especificação incoerente para com erro explicativo; checagem com FALHA levanta erro (modo estrito); EOB negativo é só ALERTA | Ajustar automaticamente | As instruções pedem que nada seja corrigido em silêncio e que as decisões fiquem com o Francisco. |
| Opção `modo_vbp = ancora_bloco` | Só participações | Torna utilizável a alternativa "âncora no bloco S38→S38" da D3 sem decidi-la. |
| Comprador nas regras de linha pode ser setor, coluna de DF, tipo de DF (`FAM`…), `CI` ou `DF` | Só códigos exatos | Evita listar 136 + 11 linhas por regra. |
| Aviso "TESTE — VALORES FICTÍCIOS" em A3 (vazia na original) e prefixado ao título em A1 | Inserir uma linha no topo | Mantém o layout idêntico ao da original, e o leitor continua conseguindo reler o arquivo. |
| Exportação sem copiar a formatação visual da original (só negrito, painel congelado e destaque dos subsetores) | Copiar estilos | As instruções dizem que a formatação é opcional. Valores, fórmulas, rótulos e mesclagens são reproduzidos exatamente. |
| Teste de fontes em script separado (`rodada01_teste_fontes.py`) | Dentro de `rodada01.py` | O teste depende de rede e grava em `dados/externos/`, enquanto `rodada01.py` precisa ser reproduzível offline. |
| Branch `main` criada no GitHub a partir do commit inicial, para receber o PR | Não criar `main` | O repositório no GitHub não tinha `main` (só a branch desta sessão). As instruções pedem que tudo termine na `main`. |

## 10. Pontos para o Francisco

1. **Liberar a rede para a Rodada 2 (bloqueante).** No ambiente de nuvem do Claude Code: menu do ambiente no título da sessão → **Edit** → **Network access**. Escolha um nível mais amplo ou acrescente em *Allowed domains* (deixando marcado *Allow package managers*):
   - `dadosabertos.aneel.gov.br`
   - `dados.ons.org.br`
   - `dadosabertos.ccee.org.br`
   - `www.epe.gov.br`
   - `apisidra.ibge.gov.br` (e `servicodados.ibge.gov.br`)
   - `seeg.eco.br` e `plataforma.seeg.eco.br`
   - `basedosdados.org`

   Os dados da ONS e da CCEE costumam ser servidos por buckets/CDNs em outros domínios. Se der 403 de novo, eu informo o domínio exato. Passo a passo: https://code.claude.com/docs/en/cloud-environments#network-access
2. **A coluna de insumos do S38-RS repete a estrutura do RB.** Somando as duas origens, os coeficientes técnicos por produto do S38-RS e do S38-RB têm correlação 0.999998 (diferença máxima de 0.004 por coeficiente), e os insumos energéticos são 8.58% do CI nas duas regiões. Isso é compatível com uma regionalização que parte da tecnologia nacional. Consequência: o S38-RS quase não compra carvão (S04: 14.7 R$ mi), apesar de emitir 5.84 Mt CO₂e. Regras de coluna como "S04 → 100% térmica fóssil" vão mover valores pequenos. Isso pesa nas decisões D3 e D5 e na eventual necessidade de ajustar a coluna do S38-RS com dados externos (o motor aceita isso via regras `fixa`/`indicador`, mas a decisão é sua).
3. **D4 e o gás.** Com `geracao_vende_para_rede`, todo o bloco S38→S38 vira "geração → rede". Compras de gás canalizado pelas térmicas (S38_GAS → S38_FOS), que na realidade também estão dentro do S38, não ficam representadas. Se quiser essa variante (parte do bloco como gás → térmica), eu implemento como terceira opção.
4. **D3 e as participações.** Com `geracao_vende_para_rede` e geração vendendo só à rede, o VBP da geração fica obrigatoriamente igual à âncora (RS 27.02%, RB 29.76% do VBP do S38). Participações diferentes geram erro explicativo. Para usar participações vindas de geração × preço, a geração precisa poder vender a outros compradores (o RAS então fecha as linhas) ou é preciso usar `modo_vbp: ancora_bloco`.
5. **Repositório público.** O repositório `FranciscoArejano/MIP-desagregacao` está **público**, então a planilha original da NEREUS/USP e todos os resultados ficam visíveis para qualquer pessoa. Confirme que a licença dos dados permite; se não permitir, torne o repositório privado (Settings → General → Danger Zone → Change visibility).
6. **Branch padrão do GitHub.** O repositório não tinha branch `main` no GitHub, e a branch desta sessão (`claude/new-session-vyrfjo`) virou a padrão por ter sido a primeira enviada. Criei a `main` a partir do commit inicial e fiz o merge do PR #1 nela. Falta você, em Settings → General → Default branch, trocar para **`main`**. Depois, se quiser, apague a branch `claude/new-session-vyrfjo`.
7. **R4a × R4b.** As duas versões foram reportadas (Seção 5). Diga qual corresponde ao texto final.
8. **Resíduos de coluna.** Os "demais" setores não têm resíduo ≈ 0 exato (até 0.0087; Seção 4), por arredondamento de VA/remunerações/EOB. É só para registro; nada a fazer, a menos que você queira investigar com a NEREUS.
9. **Decisões D1–D6.** Continuam pendentes. O motor suporta:
   - D1: qualquer lista de subsetores;
   - D2: desagregar em uma ou nas duas regiões;
   - D3: participações ou âncora;
   - D4: bloco `proporcional` ou `geracao_vende_para_rede`;
   - D5: regras `fixa` ou `indicador` por conta satélite;
   - D6: subsetores latentes ou com produção zero. Para fundir ou excluir, basta mudar a lista de subsetores.

   Para os latentes, vou precisar da fonte das colunas de coeficientes e das intensidades satélite.

## 11. Como reproduzir

```bash
git clone https://github.com/FranciscoArejano/MIP-desagregacao.git
cd MIP-desagregacao
pip install -r requirements.txt
python scripts/rodada01.py               # regenera todas as saídas da rodada (E2–E5), ~5 s
python -m pytest                         # 56 testes, inclui T1 (hash da original)
python scripts/rodada01_teste_fontes.py  # opcional (E6): precisa de acesso à rede
```

Ambiente usado: Python 3.13, pandas 3.0.5, numpy 2.5.3, openpyxl 3.1.5, PyYAML 6.0.1, pytest 9.1.1.
Os `.xlsx` regenerados mudam só nos metadados de data de gravação; os valores são idênticos.

## 12. Git

- Branch de trabalho: `claude/new-session-vyrfjo`.
- Commits da rodada (em ordem):
  - `eeefa3e` R01-E1: estrutura do repositório e planilha original protegida (hash + T1)
  - `539231c` R01-E2: leitor da MIP, formato longo e validação das identidades contábeis
  - `fffd707` R01-E3: modelo de Leontief genérico e reprodução dos 9 cenários de referência
  - `3406cf4` R01-E4: diagnóstico do S38 no RS e no RB
  - `080dcd4` R01-E5: motor genérico de desagregação, RAS, exportação e testes T2–T5 (parâmetros fictícios)
  - `8b26f73` R01-E6: teste de acesso a fontes externas e registro em FONTES.md
  - `47deb5d` R01-E5: ajuste do piso de tolerância do RAS e da leitura de valores vazios nos CSVs; saídas regeneradas
  - R01-E7: relatório da rodada, HISTORICO e README (o commit que traz este arquivo)
- `main`: não existia no GitHub. Criei a `main` a partir do commit inicial do repositório (`6d15181`).
- Pull Request: **#1** (`claude/new-session-vyrfjo` → `main`): https://github.com/FranciscoArejano/MIP-desagregacao/pull/1. O merge do PR na `main` (merge commit) é o último passo desta rodada, feito por mim via GitHub. O resultado está na mensagem final da conversa. Se este relatório estiver na `main`, o merge foi feito.
- O que o Francisco precisa clicar: só trocar a branch padrão para `main` (item 6 da Seção 10).
