# Instruções para o Claude Code — Rodada 01

> **ESTE ARQUIVO É PARA O CLAUDE CODE.**
> Projeto: desagregação do setor S38 (energia elétrica, gás natural e outras utilidades) na MIP inter-regional RS × Restante do Brasil, 2019.
> Repositório: `FranciscoArejano/MIP-desagregacao` · Responsável: Francisco · Data: 15/10/2026
>
> **Antes de começar:** leia este arquivo inteiro. Execute as etapas na ordem. O relatório da rodada (Etapa 7) é obrigatório: é por ele que o Francisco acompanha o que você fez.
>
> Convenção numérica deste arquivo: ponto decimal, sem separador de milhar (ex.: `20942.66`).

---

## 0. O que esta rodada entrega

1. Repositório organizado, com a planilha original protegida (somente leitura + hash).
2. Leitor da MIP em Python e validação das identidades contábeis.
3. Reprodução exata dos resultados de referência já obtidos com esta MIP (prova de que a matriz está sendo lida e o modelo calculado corretamente).
4. Diagnóstico do setor S38 nas duas regiões.
5. Motor de desagregação genérico + testes automáticos, **com parâmetros fictícios de teste**. Nenhuma desagregação real nesta rodada.
6. Teste de acesso a fontes de dados externas (prepara a Rodada 2).
7. Relatório da rodada em `respostas/RODADA_01_resposta.md`.

---

## 1. Contexto do projeto

- A base é uma matriz insumo-produto inter-regional setor × setor de 2019, estimada pelo NEREUS/USP (método IIOAS), com duas regiões: **R1 Rio Grande do Sul (RS)** e **R2 Restante do Brasil (RB)**, 68 setores em cada (136 setores-região). Valores em R$ milhões correntes; emissões em t CO₂e.
- A matriz é usada num modelo de Leontief com coeficientes de emissão para simular choques de R$ 1 bilhão na demanda final de setores do RS (cenários na Etapa 3).
- Problema: o setor **S38 — Energia elétrica, gás natural e outras utilidades** agrega todas as fontes de geração (hidrelétrica, eólica, solar, biomassa, térmicas fósseis, nuclear), a transmissão/distribuição e o gás canalizado. O coeficiente de emissão dele é uma média, o que impede separar fontes renováveis de fósseis.
- Objetivo do projeto: desagregar o S38 em subsetores **preservando exatamente todos os totais da matriz original**. A lista final de subsetores e os métodos de repartição serão decididos pelo Francisco (Seção 10). Por isso o motor desta rodada precisa ser genérico.
- Você não vai receber o artigo de pesquisa. Tudo o que precisa está neste arquivo.

---

## 2. Regras fixas (valem para todas as rodadas)

1. **O arquivo original é intocável.** Nunca edite, renomeie, reformate nem salve por cima da planilha original. Ela fica em `dados/original/` com o nome exatamente como recebido. Todo produto vai para arquivos novos.
2. **Nada é sobrescrito entre rodadas.** As saídas de cada rodada ficam em `resultados/rodadaXX/`. Arquivos de dados derivados levam a versão no nome (`_v01`, `_v02`…).
3. **Decisões metodológicas são do Francisco.** As da Seção 10 você não toma. Decisões de implementação (estrutura do código, formatos, nomes de arquivo) você pode tomar, desde que registre cada uma no relatório com a justificativa.
4. **Não invente dados.** Todo número externo precisa de fonte (instituição, tabela/arquivo, URL, data de acesso) registrada em `dados/externos/FONTES.md`. Se uma fonte não estiver acessível, registre e siga em frente. Não a substitua por estimativa própria sem autorização.
5. **Tudo reprodutível por script.** Nada de edição manual em Excel. Um único comando regenera as saídas da rodada (informe qual no relatório).
6. **Idioma e unidades.** Código em Python; comentários, nomes de colunas e relatórios em português. Unidades: R$ milhões (2019), t CO₂e, hm³, mil tep, ocupações.
7. **Relatório obrigatório ao fim de cada rodada** em `respostas/RODADA_XX_resposta.md` (modelo na Etapa 7), mais uma linha nova em `respostas/HISTORICO.md`.
8. **Git.** Faça commits por etapa com mensagens claras (ex.: `R01-E2: leitor da MIP e validações`). No fim, tudo precisa estar na branch `main`: se você trabalhou em outra branch, faça o merge se tiver permissão; se não tiver, abra um Pull Request e explique no relatório exatamente o que o Francisco precisa clicar.
9. **Se algo não bater, não improvise.** Documente no relatório o que esperava e o que encontrou, siga com as etapas que não dependem do problema e registre a dúvida em "Pontos para o Francisco".

---

## 3. Estrutura do repositório (criar)

```
MIP-desagregacao/
├── README.md                 ← o que é o projeto, estrutura, como rodar, status
├── requirements.txt
├── dados/
│   ├── original/             ← planilha original (somente leitura) + CHECKSUM.txt
│   ├── externos/             ← dados de fontes externas + FONTES.md
│   └── intermediarios/       ← CSVs derivados (formato longo etc.)
├── parametros/               ← hipóteses e pesos da desagregação (CSV/YAML)
├── src/mip/                  ← código: leitura, modelo, desagregação, exportação
├── scripts/                  ← um script por rodada (ex.: rodada01.py)
├── tests/                    ← testes automáticos (pytest)
├── resultados/rodada01/      ← saídas desta rodada
├── instrucoes/               ← cópia dos arquivos de instrução de cada rodada
└── respostas/                ← relatórios das rodadas + HISTORICO.md
```

---

## 4. Etapa 1 — Organizar o repositório e proteger o original

1. Localize a planilha da MIP. O Francisco a subiu na raiz do repositório ou a anexou na conversa. Nome esperado: `Matrtiz_Insumo-Produto_RS_RB_com_emissões.xlsx`. O "Matrtiz" faz parte do nome original: mantenha.
2. Mova-a para `dados/original/` com `git mv` (ou salve lá, se veio anexada), sem alterar conteúdo nem nome.
3. Calcule o SHA-256 e grave em `dados/original/CHECKSUM.txt`. Hash da versão que o Francisco usou:
   `15e734a43aba6cc582117a742e4279e0535ccad331c86b880eab38ece420a3ea`
   Se o seu for diferente, **não pare**: registre no relatório (pode ser outra versão do arquivo).
4. Deixe o arquivo como somente leitura (`chmod 444`) e crie um teste que falha se o hash mudar. Ele roda em todo `pytest`.
5. Mova este arquivo de instruções para `instrucoes/RODADA_01_instrucoes_CODE.md` (com `git mv`, se estiver na raiz).
6. Crie `README.md`, `requirements.txt` (pandas, numpy, openpyxl, pytest, pyyaml) e `.gitignore` (caches, `__pycache__`, `.venv`). **Não** ignore os `.xlsx` de `dados/` e `resultados/`.

---

## 5. Etapa 2 — Ler a MIP e validar as identidades contábeis

A planilha tem uma aba só: `MIP SS RS_RBR` (intervalo A1:EV163). Mapa exato:

| Bloco | Linhas | Colunas | Conteúdo |
|---|---|---|---|
| Títulos | 1–2 | A:EV (mescladas) | título da tabela |
| Cabeçalhos | 3–6 | E:EV | região (3–4), nome do setor (5), código S01…S68 e região da demanda final (6) |
| Rótulos das linhas | 7–142 | A:D | região (A/B), código (C), nome (D) |
| Consumo intermediário Z | 7–142 | E:EJ | 136×136. Linhas 7–74 = RS S01–S68; linhas 75–142 = RB S01–S68. Colunas E:BT = RS; BU:EJ = RB |
| Demanda final | 7–142 | EK:ET | EK Investimento RS · EL Investimento RB · EM Famílias RS · EN Famílias RB · EO Governo RS · EP Governo RB · EQ ISFLSF RS · ER ISFLSF RB · ES Exportações RS · ET Exportações RB |
| Discrepância estatística | 7–142 | EU | |
| Total da linha | 7–142 | EV | soma da linha (= VBP) |
| Total do CI doméstico | 143 | | fórmula `=SUM()` |
| Importações internacionais | 144 | E:EV | |
| CI + importações | 145 | | fórmula |
| Impostos líquidos sobre produtos | 147, 148, 149 | | IPI, ICMS, Outros (146 = título; 150 = total, fórmula) |
| Valor adicionado bruto | 151 | E:EJ | = Remunerações (152) + EOB (153) + Impostos líquidos sobre a produção (154) |
| Valor da produção (VBP) | 156 | E:EV | |
| TOTAL VBP / CHECK | 157 / 159 | | fórmulas |
| Ocupações | 158 | E:EJ | fator trabalho |
| Emissões de CO₂e (t) | 161 | E:EJ | conta ambiental |
| Uso de água (hm³) | 162 | E:EJ | conta ambiental |
| Consumo energético (mil tep) | 163 | E:EJ | conta ambiental |

Observações:
- O S38 está na **linha 44 / coluna AP** (RS) e na **linha 112 / coluna DF** (RB).
- Investimento, Famílias, Governo e ISFLSF estão por região **compradora** (ex.: "Famílias RS" compra de linhas RS e RB). Exportações estão por região de **origem** (ES = produtos do RS; ET = produtos do RB).
- Nas colunas de demanda final, as linhas 144 a 149 trazem importações e impostos da demanda final, e a linha 156 traz o total de cada coluna.
- As linhas 143, 145, 150, 157 e 159 são fórmulas. Recalcule em Python (o openpyxl não avalia fórmulas).
- No RS, os setores S05, S06, S07 e S20 têm produção zero (linha e coluna zeradas). Nos coeficientes, use zero onde a produção for zero (sem divisão por zero).

Tarefas:
1. `src/mip/leitura.py`: função que devolve uma estrutura com Z (136×136), demanda final (136×11, incluindo a discrepância), VBP, linhas de insumos primários (importações, IPI, ICMS, outros, VA, remunerações, EOB, impostos sobre a produção), contas satélite (ocupações, CO₂e, água, energia) e rótulos (região, código, nome). Use as coordenadas acima, não posições "adivinhadas".
2. Exporte em formato longo para `dados/intermediarios/mip_original_longo.csv` (região de origem, setor de origem, região de destino, setor ou coluna de destino, valor).
3. Rode e registre as checagens abaixo (os valores esperados são os que eu encontrei; servem de referência):

| Checagem | Esperado |
|---|---|
| Linha: Σ Z + Σ demanda final (EK:EU) − total (EV) | diferença máxima ≈ 7e-10 |
| Coluna: Σ Z + importações + impostos (147–149) + VA (151) − VBP (156) | diferença máxima ≈ 0.0095 (RB S40 Construção); demais ≈ 0 |
| VA − (remunerações + EOB + impostos sobre a produção) | ≈ 1e-10 |
| VBP (linha 156) − total da linha (EV), por setor | 0 |
| Setores com VBP = 0 | RS S05, RS S06, RS S07, RS S20 |
| Valores negativos | coluna EU (65 células; mínimo −5987.45); linha 153 EOB (RS S09, RB S09); linha 154 (RS S01, RB S01) |

---

## 6. Etapa 3 — Reproduzir os resultados de referência (validação do modelo)

Modelo:
- A = Z · diag(X)⁻¹ (coluna zero onde X_j = 0); L = (I − A)⁻¹.
- e_j = CO₂e_j / X_j (zero onde X_j = 0).
- ΔX = L · ΔY; emissões induzidas por setor = e ∘ ΔX; total = soma.
- Intensidade carbônica (IC) = CO₂e total / Σ ΔX (t CO₂e por R$ milhão).
- Emissões diretas = e · ΔY; indiretas = total − diretas.
- Recorte regional: somar ΔX e emissões pela região de origem do setor.

Choques em R$ milhões, todos na demanda final de setores do **RS**:

| Cenário | S38 | S31 | S29 | S40 | S43 | S56 | S19 |
|---|---|---|---|---|---|---|---|
| E1 Energia elétrica agregada | 1000 | | | | | | |
| R1 Cesta renovável (base) | 300 | 250 | 150 | 200 | 50 | 50 | |
| F1 Cesta fóssil (base) | 350 | | | | 250 | | 400 |
| R2 Renovável balanceada | 1000/6 | 1000/6 | 1000/6 | 1000/6 | 1000/6 | 1000/6 | |
| R3 Renovável infraestrutura-intensiva | 150 | 250 | 250 | 250 | 50 | 50 | |
| R4a Renovável energia/transporte, vetor A | 450 | 150 | 100 | 100 | 150 | 50 | |
| R4b Renovável energia/transporte, vetor B | 500 | 150 | 100 | 100 | 100 | 50 | |
| F2 Fóssil balanceada | 1000/3 | | | | 1000/3 | | 1000/3 |
| F3 Fóssil energia-intensiva | 500 | | | | 200 | | 300 |

Resultados esperados. Devem bater com tolerância de 0.01 (R$ mi) e 1 t (CO₂e):

| Cenário | ΔX total | ΔX RS | ΔX RB | CO₂e total | CO₂e RS | CO₂e RB | IC | % CO₂e no RB | % indiretas |
|---|---|---|---|---|---|---|---|---|---|
| E1 | 1925.04 | 1357.01 | 568.03 | 428113.53 | 339326.41 | 88787.12 | 222.39 | 20.74 | 34.89 |
| R1 | 1959.35 | 1391.32 | 568.04 | 216406.97 | 142390.03 | 74016.95 | 110.45 | 34.20 | 51.55 |
| F1 | 2120.56 | 1373.23 | 747.32 | 356045.72 | 277141.45 | 78904.28 | 167.90 | 22.16 | 35.34 |
| R2 | 1920.37 | 1399.36 | 521.01 | 216987.16 | 153932.23 | 63054.92 | 112.99 | 29.06 | 46.11 |
| R3 | 1969.21 | 1396.49 | 572.72 | 169090.02 | 95597.22 | 73492.80 | 85.87 | 43.46 | 62.70 |
| R4a | 1959.49 | 1395.81 | 563.67 | 309794.88 | 236133.84 | 73661.05 | 158.10 | 23.78 | 39.04 |
| R4b | 1950.48 | 1387.14 | 563.34 | 304336.55 | 228514.51 | 75822.04 | 156.03 | 24.91 | 40.31 |
| F2 | 2110.49 | 1392.22 | 718.27 | 381702.86 | 306553.93 | 75148.94 | 180.86 | 19.69 | 32.87 |
| F3 | 2073.93 | 1371.35 | 702.58 | 375427.26 | 294592.52 | 80834.74 | 181.02 | 21.53 | 34.97 |

Dez setores que mais emitem no cenário R1 (conferência):

| # | Região | Setor | ΔX (R$ mi) | CO₂e (t) | % do total |
|---|---|---|---|---|---|
| 1 | RS | S38 | 357.1 | 99554.6 | 46.0 |
| 2 | RS | S43 | 84.1 | 35489.9 | 16.4 |
| 3 | RB | S38 | 92.0 | 23960.2 | 11.1 |
| 4 | RB | S27 | 46.8 | 11392.4 | 5.3 |
| 5 | RB | S43 | 16.4 | 7311.5 | 3.4 |
| 6 | RB | S26 | 15.3 | 6949.7 | 3.2 |
| 7 | RB | S28 | 34.1 | 5082.2 | 2.3 |
| 8 | RB | S39 | 4.7 | 4646.4 | 2.1 |
| 9 | RB | S03 | 1.0 | 3085.0 | 1.4 |
| 10 | RB | S01 | 3.5 | 2649.5 | 1.2 |

Tarefas:
1. `src/mip/modelo.py`: funções genéricas, que sirvam para **qualquer** MIP (inclusive a desagregada): coeficientes, inversa de Leontief, emissões, decomposição direta/indireta, recorte regional e ranking setorial.
2. `scripts/rodada01.py` roda os 9 cenários e salva `resultados/rodada01/replicacao_v01.xlsx`, com uma aba por cenário (ΔX e emissões por setor-região) e uma aba-resumo "esperado × obtido × diferença".
3. Teste automático que compara os resultados com as tabelas acima.
4. Para o relatório: R4a e R4b são duas versões do mesmo cenário. Reporte as duas. O Francisco decide qual corresponde ao texto final; não tente escolher.

---

## 7. Etapa 4 — Diagnóstico do S38 (RS e RB)

Gere `resultados/rodada01/diagnostico_S38_v01.xlsx` com:
1. **Estrutura de insumos (coluna)** do S38-RS e do S38-RB: valor, coeficiente técnico e região de origem de cada insumo. Destaque os insumos energéticos: S01, S03, S04 (inclui carvão mineral), S05 (petróleo e gás natural), S09, S16, S19 (derivados de petróleo) e S20.
2. **Estrutura de vendas (linha)**: para quais setores e componentes da demanda final o S38 de cada região vende.
3. **Bloco intrassetorial S38→S38**: RS→RS, RS→RB, RB→RS e RB→RB, e a soma "vendas do S38 de cada região para o S38 das duas regiões" como % do VBP. Essa soma é candidata a âncora do valor da geração elétrica (decisão D3, Seção 10).
4. **Insumos primários e contas satélite**: importações, impostos, VA e componentes, ocupações, CO₂e, água e energia, com intensidades por R$ milhão de VBP.
5. **Peso do S38 em cada cenário da Etapa 3**: emissões induzidas no S38-RS e no S38-RB como % do total.

Valores de referência:

| Item | S38-RS | S38-RB |
|---|---|---|
| VBP | 20942.66 | 324387.34 |
| Consumo intermediário (soma da coluna em Z) | 10462.3 | 159881.3 |
| Importações | 894.4 | 13667.96 |
| VA | 8081.27 | 127843.73 |
| CO₂e (t) | 5838005.55 | 84518349.06 |
| t CO₂e por R$ mi | 278.76 | 260.55 |
| Ocupações | 15012 | 151807 |
| Energia (mil tep) | 503.96 | 7805.92 |
| Água (hm³) | 6.79 | 67.61 |
| Vendas ao S38 das duas regiões | 5659.7 (27.0% do VBP) | 96538.4 (29.8% do VBP) |

Bloco S38→S38: RS→RS 3057.1 · RS→RB 2602.5 · RB→RS 3220.2 · RB→RB 93318.2.

Peso do S38 (RS + RB) nas emissões de cada cenário (%): E1 92.2 · R1 57.1 · F1 39.4 · R2 32.8 · R3 38.8 · R4a 58.5 · R4b 66.0 · F2 35.1 · F3 53.0.

---

## 8. Etapa 5 — Motor de desagregação genérico e testes

Objetivo: deixar pronta a ferramenta que, na Rodada 3, vai gerar a MIP desagregada com os parâmetros reais.

### 8.1 Requisitos do motor (`src/mip/desagregacao.py`)

Uma função principal recebe a MIP original + uma especificação (arquivos em `parametros/`) e devolve a MIP desagregada. A especificação deve ser legível (CSV ou YAML) e conter:

a) **Lista de subsetores**: código, nome e tipo (`geracao` | `rede` | `gas_utilidades`), a mesma lista nas duas regiões. Subsetores com produção zero são permitidos.

b) **Participação de cada subsetor no VBP** do S38 de cada região.

c) **Repartição da coluna (insumos)**, definida por setor fornecedor, com três tipos de regra:
   - `proporcional_vbp` (padrão);
   - `fixa`: participações dadas (ex.: S04 → 100% num subsetor);
   - `indicador`: proporcional a VBP × indicador dado.

d) **Bloco intrassetorial S38→S38**, com duas opções implementadas:
   - `proporcional`;
   - `geracao_vende_para_rede`: os subsetores de geração vendem apenas ao subsetor de rede das duas regiões, respeitando os quatro fluxos originais RS↔RB; o subsetor de rede compra toda essa energia.

e) **Repartição da linha (vendas)** por comprador e por coluna da demanda final:
   - `proporcional_vbp` (padrão);
   - `somente_rede_e_gas`: subsetores de geração não vendem fora do bloco S38;
   - `fixa_por_comprador`: participações por comprador.

f) **Insumos primários e contas satélite**, com os mesmos tipos de regra. O **EOB é o item de ajuste** (resíduo) de cada subsetor, para fechar o balanço da coluna.

g) **Subsetor latente**: produção-base zero, mas com uma coluna de coeficientes técnicos fornecida externamente. Ela é guardada à parte, porque não aparece como fluxo, e permite simular choques nesse subsetor.

Outros requisitos:
- **Utilitário RAS (biproporcional)** para conciliar linhas e colunas quando as regras gerarem totais incompatíveis, mantendo fixas as células indicadas. Deve reportar convergência e número de iterações.
- **Exportação** (`src/mip/exportacao.py`): gera um `.xlsx` **com o mesmo layout da original** (títulos, cabeçalhos, rótulos, linhas de totais com fórmulas, contas satélite), com os subsetores no lugar do S38 de cada região. Formatação visual é opcional. Abas extras: `LEIAME`, `mapa_setores` (original → novo), `parametros` (todos os pesos usados, com fonte), `checagens` e `coef_latentes` (se houver). Gere também o CSV em formato longo.
- **Verificação**, chamada sempre ao final da desagregação:
  - re-agregação: somando os subsetores, reproduz a MIP original em todas as células (tolerância 1e-6);
  - balanço de linha e de coluna de cada subsetor;
  - não negatividade, exceto onde a original já tem negativos (coluna EU e linhas 153/154);
  - totais das contas satélite preservados;
  - EOB ≥ 0 em todos os subsetores (se negativo, **sinalize**; não corrija em silêncio);
  - L ≥ 0 e diagonal de L ≥ 1.

### 8.2 Testes obrigatórios (pytest)

- **T1:** hash da planilha original inalterado.
- **T2:** re-agregação exata, para qualquer especificação válida.
- **T3 (desagregação neutra):** divida o S38 de cada região em K subsetores com participações positivas arbitrárias, colunas proporcionais (mesmos coeficientes técnicos), linhas proporcionais e contas satélite proporcionais. Para os 9 cenários da Etapa 3, com o choque do S38 repartido de **qualquer** forma entre os subsetores, os resultados (ΔX total e regional, CO₂e total e regional, diretas e indiretas) devem ser idênticos aos da MIP original (tolerância 1e-6). Isso tem de acontecer porque, com colunas idênticas, a agregação é exata.
- **T4 (subsetor latente):** num exemplo pequeno (3 setores), acrescentar um subsetor de produção zero com coluna de coeficientes dada não altera os fluxos-base e gera o multiplicador esperado, calculado à mão no teste.
- **T5 (geração vende para rede):** num exemplo de teste, a soma das vendas dos subsetores de geração é igual ao bloco S38→S38 original, e esses subsetores não vendem a nenhum outro setor nem à demanda final.

### 8.3 Parâmetros de teste

Crie `parametros/TESTE_*.csv` com valores **fictícios** para os 8 subsetores provisórios abaixo e gere `resultados/rodada01/teste/MIP_TESTE_valores_ficticios_NAO_USAR.xlsx`. Esse arquivo serve apenas para provar que o motor funciona: marque "TESTE — VALORES FICTÍCIOS" no nome, na aba `LEIAME` e no topo da aba principal.

Lista provisória de subsetores (pode mudar depois da decisão D1):

| Código | Subsetor |
|---|---|
| S38_HID | Geração hidrelétrica (UHE, PCH, CGH) |
| S38_EOL | Geração eólica |
| S38_SOL | Geração solar fotovoltaica |
| S38_BIO | Geração a biomassa e biogás |
| S38_FOS | Geração termelétrica fóssil (carvão, gás natural, derivados de petróleo) |
| S38_NUC | Geração nuclear (inexistente no RS) |
| S38_TD | Transmissão, distribuição e comercialização de energia elétrica |
| S38_GAS | Gás natural canalizado e outras utilidades (vapor, água quente) |

---

## 9. Etapa 6 — Teste de acesso a fontes externas

Para cada fonte, teste se o ambiente consegue acessá-la com uma requisição leve. Se conseguir, baixe apenas um arquivo pequeno de amostra ou catálogo para `dados/externos/rodada01_teste/` e registre em `dados/externos/FONTES.md`. **Não use esses dados em nenhum cálculo nesta rodada.**

| Fonte | Endereço | Uso previsto (Rodada 2) |
|---|---|---|
| ANEEL – Dados Abertos (SIGA) | https://dadosabertos.aneel.gov.br | usinas: potência, fonte, UF |
| ONS – Dados Abertos | https://dados.ons.org.br | geração por usina/fonte e UF |
| CCEE – Dados Abertos | https://dadosabertos.ccee.org.br | geração, consumo por ramo, preços |
| EPE (Anuário Estatístico de Energia Elétrica; BEN) | https://www.epe.gov.br | geração e consumo por fonte e UF, 2019 |
| IBGE – API SIDRA | https://apisidra.ibge.gov.br | pessoal ocupado e salários por CNAE e UF |
| SEEG | https://seeg.eco.br | emissões por UF e fonte |
| Base dos Dados (RAIS) | https://basedosdados.org | emprego por CNAE subclasse e UF (só verificar se responde; não crie credenciais) |
| PyPI | https://pypi.org | instalação de pacotes |

---

## 10. Decisões pendentes do Francisco (não decida por ele)

O Francisco decide estes pontos antes da Rodada 2. O motor desta rodada precisa suportar todas as opções:

- **D1** — lista de subsetores (provisória: os 8 da Seção 8.3; alternativas: versão enxuta com 5 e versão detalhada com cerca de 11).
- **D2** — desagregar o S38 também no RB (provável: sim).
- **D3** — como medir o VBP de cada subsetor (âncora nas vendas S38→S38 + geração por fonte × preço, ou alternativas).
- **D4** — estrutura de vendas (`geracao_vende_para_rede` ou `proporcional`).
- **D5** — repartição de emissões e demais contas satélite (preservando os totais da base).
- **D6** — subsetores com produção zero em 2019 (ex.: solar no RS): latente, fundir ou excluir.

---

## 11. Etapa 7 — Relatório da rodada (obrigatório)

Salve em `respostas/RODADA_01_resposta.md`, com exatamente estas seções:

1. **Resumo** (até 8 linhas).
2. **Status por etapa**: tabela Etapa | Status (concluída / parcial / não feita) | Observação.
3. **Arquivos criados, movidos ou alterados**: tabela Caminho | Tipo | O que é | Etapa. Liste **todos**.
4. **Validação da MIP original**: tabela com cada checagem e o valor obtido.
5. **Reprodução dos resultados**: tabela esperado × obtido × diferença para os 9 cenários, mais o top-10 do R1.
6. **Diagnóstico do S38**: números-chave e caminho do arquivo.
7. **Motor de desagregação**: como está organizado, como usar (exemplo de comando) e resultado de cada teste (T1 a T5).
8. **Acesso a fontes externas**: tabela Fonte | Acessível? | O que foi baixado | Observação.
9. **Decisões tomadas por você nesta rodada**: tabela Decisão | Alternativas consideradas | Por quê. Só decisões de implementação.
10. **Pontos para o Francisco**: dúvidas objetivas, problemas encontrados e o que você precisa dele.
11. **Como reproduzir**: comandos exatos.
12. **Git**: branch usada, lista de commits e status do merge ou do PR.

Além disso:
- Acrescente uma linha em `respostas/HISTORICO.md`: data | rodada | resumo em uma linha | link para o relatório.
- Atualize o `README.md` com o status do projeto.
- Na sua última mensagem da conversa, diga: (a) onde está o relatório; (b) se tudo foi para a `main`; (c) se o Francisco precisa fazer alguma coisa.

---

## 12. Checklist final

- [ ] Planilha original intacta (hash conferido; T1 passando)
- [ ] Todos os testes passando (`pytest`)
- [ ] Resultados da Etapa 3 batendo com as tabelas esperadas
- [ ] Nenhum dado inventado; fontes registradas
- [ ] Relatório salvo em `respostas/RODADA_01_resposta.md` e `HISTORICO.md` atualizado
- [ ] Commit + push; tudo na `main` (ou PR aberto e explicado no relatório)
