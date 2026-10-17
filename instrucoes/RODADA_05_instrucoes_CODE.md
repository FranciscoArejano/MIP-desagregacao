# Instruções para o Claude Code — Rodada 05 (MIP final e material para o artigo)

> **ESTE ARQUIVO É PARA O CLAUDE CODE.**
> Projeto: desagregação do S38 na MIP inter-regional RS × Restante do Brasil, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
> Data: 17/10/2026 · Base: a MIP v03 da Rodada 04 (`respostas/RODADA_04_resposta.md`)
>
> **Git:** trabalhe a partir da `main` (último commit conhecido: `607d68c`) e termine com push para a `main`. Copie este arquivo para `instrucoes/RODADA_05_instrucoes_CODE.md`, como na rodada anterior.
>
> **Convenção numérica:** no repositório (CSV, YAML, relatório), ponto decimal e sem separador de milhar. **No material do artigo (pasta `artigo/`), padrão brasileiro:** milhar com ponto e decimal com vírgula (1.925,0).

---

## 0. O que esta rodada entrega

Esta é a última rodada de construção da MIP. Depois dela, o Francisco leva o material para o artigo.

1. **MIP final (v04)** = v03 + D17 + D18 (Seção 2).
2. **Variantes da versão final**, incluindo duas novas:
   - `_E4`: parte do resíduo de emissões sai do S38 (Seção 3.2);
   - `_rap_media`: a transmissão da v03.
3. **Diagnóstico da conta-satélite de emissões do S38** (NEREUS × SEEG; Seção 3.1).
4. **Simulações finais**: A0, A1, A2 e sensibilidades, B por R$ 1 bi e por TWh, robustez (Seção 4).
5. **Material do artigo** na pasta nova `artigo/` (Seção 5):
   - tabelas e figuras no formato do artigo;
   - texto da metodologia, em duas versões: para o corpo do artigo e para o apêndice;
   - limitações, referências e uma ficha de números-chave.
6. **Relatório** `respostas/RODADA_05_resposta.md`.

Continuam valendo todas as regras fixas:
- original intocável (T1);
- nada sobrescrito: saídas novas em `resultados/rodada05/` e `artigo/`, parâmetros com sufixo `_v04`;
- nenhum dado inventado; toda hipótese marcada como HIPÓTESE;
- brutos grandes fora do git;
- fontes em `FONTES.md`.

**Ordem de prioridade**, se faltar tempo ou limite de uso: Seções 2 → 3 → 4 → 5.1 e 5.2 → 5.3. Faça commits intermediários e diga no relatório o que ficou faltando.

---

## 1. Decisões do Francisco

Valem as anteriores: D1 = C; D2, D3, D4, D6, D7 e D8 = A; D5 = E1; D9 = (a) + (b) + (f) + (r); D10 = Sulgás; D11 = R4a; D12 a D16, V1 e V2 como na Rodada 04. A V3 é substituída pela D17. Somam-se:

| Decisão | Escolha | Seção |
|---|---|---|
| **D17** — VBP da transmissão | **A:** encargos de uso faturados pelo ONS no ano civil de 2019 (**22935.6 R$ mi**) na principal. O valor da v03 (24883.4) vira a variante `_rap_media` | 2.1 |
| **D18** — TUST das colunas latentes | **A:** SOL-RS e PET-RS pagam a TUST por MWh das fontes do RS (regra da V1), e não a TUST por real do espelho do RB | 2.2 |
| **D19** — κ e o ALERTA do T12 | **A:** κ = 0.70 continua. O ALERTA do T12 (GN-RS e GN-RB abaixo de 0.05) fica aceito e documentado; `_k060` continua como sensibilidade | 2.3 |
| **D20** — Cesta fóssil nas tabelas principais | **A:** D13 (CAR e GN do RS ∝ VBP). 100% CAR e 100% GN vão para a tabela de sensibilidade | 5.1 |
| **D21** — Emissões do S38 | **A:** E1 continua a principal. E3 e a nova E4 viram sensibilidades | 3 |

Se a mensagem de abertura do Francisco indicar outra opção, **a mensagem prevalece**. Se ela disser **D17 = B e D18 = B**, não existe v04: a versão final é a v03, e as variantes novas são criadas sobre ela (`_v03_E4`). O resto da rodada não muda.

---

## 2. MIP final (v04)

### 2.1 D17 — Transmissão pelos encargos do ONS

- **VBP total da transmissão (Brasil)** = 22935.6 R$ mi. É o ano civil de 2019 pelos "Total Encargos de Uso" do SEAMSE: jun/2019 acumulado − dez/2018 acumulado + dez/2019 acumulado. Os três PDFs já estão em `dados/externos/aneel_rap/`.
- **Repartição RS × RB:** a mesma regra da v03, ou seja, é a variante `_rap_ons` da Rodada 04 promovida a principal.
- **Fonte nos CSVs:** "D17: encargos de uso do sistema de transmissão faturados pelo ONS no ano civil de 2019 (SEAMSE dez/2018, jun/2019 e dez/2019); sem PIS/Pasep e Cofins; inclui o orçamento do ONS".
- **Por quê** (para o texto da metodologia):
  - a fonte é oficial e cobre o ano civil de 2019;
  - o valor está sem PIS/Pasep e Cofins, que são impostos sobre produtos. Isso é coerente com o VBP a preços básicos.
- **A transmissão da v03 (24883.4)** vira a variante `_rap_media`.

### 2.2 D18 — TUST das colunas latentes (SOL-RS e PET-RS)

Para cada coluna latente k:
- coeficiente total de TUST = τ_RS ÷ p_k, onde:
  - **τ_RS** = TUST por MWh que as fontes do RS no SIN pagam na versão final (R$/MWh; regra da V1);
  - **p_k** = R$/MWh do espelho (k-RB) na versão final;
- mantenha a repartição atual entre as linhas TRA-RS e TRA-RB da coluna;
- os demais coeficientes de insumo não mudam. A diferença sai do valor adicionado da coluna latente (ela não tem VBP; para o modelo, só os coeficientes importam).

Marque **HIPÓTESE (D18)** na fonte do `coef_latentes`. Reporte:
- τ_RS e p_k;
- o coeficiente de TUST antes e depois;
- o efeito nos multiplicadores do SOL-RS e do PET-RS e no B por TWh do SOL.

Referência da Rodada 04 (com a RAP da v03): SOL por TWh de 4589.8 para 4939.4 t CO₂e.

### 2.3 Sem mudança

- **D19:** κ = 0.70.
- η = 0.10, E1, D8, D9, D10, V1, V2, α = 0.5, latentes por espelho e preços P1.

### 2.4 Variantes da versão final

| Variante | O que muda |
|---|---|
| `_P2`, `_E2`, `_E3`, `_gas4dist`, `_k060`, `_eta005` | Como na Rodada 04, refeitas sobre a v04 |
| `_rap_media` | Transmissão da v03 (24883.4) |
| `_E4` | Nova (Seção 3.2) |

Para cada uma: CSV longo, `coef_latentes` e uma linha no quadro de variantes. A v04 principal também sai em `.xlsx`, no mesmo layout das anteriores.

---

## 3. Emissões do S38: diagnóstico e variante E4

**Contexto.** Na E1, o resíduo (emissões do S38 na base NEREUS − emissões das usinas no SEEG − SF6) vai para DIS e GAS, na proporção do VBP. Ele é grande:
- **34% do CO₂e do S38 no RS;**
- **59% no RB.**

O texto do artigo precisa explicar de onde ele vem. O revisor do Francisco fez uma conferência preliminar com o arquivo do SEEG 13.0 que você já baixou (`dados/externos/brutos/seeg/Dados-nacionais-13.0.xlsx`, SHA-256 `21fc4965…`).

Critérios da conferência:
- ano 2019;
- `Gás` = 'CO2e (t) GWP-AR5';
- linhas 'Emissão' e 'Emissão NCI';
- região: `Estado` = RS → RS; demais estados → RB; 'Não alocado' separado.

**Resultado preliminar** (mil t CO₂e):

| Componente (SEEG: `Atividade geral` › `Categoria emissora` › `Sub-categoria emissora`) | RS | RB (estados) | Não alocado |
|---|---|---|---|
| Geração de eletricidade › Geração de eletricidade (serviço público) | 3842.6 | 34181.1 | 344.0 |
| Geração de eletricidade › demais categorias (autoprodução: indústria, comércio, público, agropecuária) | 96.5 | 2094.4 | 4833.4 |
| Geração de eletricidade › Produção de combustíveis › Refino de petróleo | 76.1 | 759.7 | 496.3 |
| Geração de eletricidade › Produção de combustíveis › Exploração de petróleo e gás natural | 0 | 5778.2 | 0 |
| Geração de eletricidade › Produção de combustíveis › Produção de álcool | 0 | 0 | 412.4 |
| Produção de combustíveis › Refino de petróleo | 1736.0 | 17329.1 | 7053.5 |
| Produção de combustíveis › Exploração de petróleo e gás natural | 0 | 17721.0 | 53.4 |
| Produção de combustíveis › Produção de carvão mineral e outros | 88.1 | 1155.4 | 355.6 |
| Produção de combustíveis › demais (carvão vegetal, álcool, transporte de petróleo e gás) | 0 | 0 | 5151.2 |
| **Soma das duas atividades** | **5839.2** | **79018.9** | **18700.0** |
| **S38 na base NEREUS** | **5838.0** | **84518.3** | — |

**Leitura:**
- **No RS**, o S38 da NEREUS coincide com a soma "Geração de eletricidade" + "Produção de combustíveis" do SEEG (diferença de 0.02%). Isso sugere que a conta-satélite inclui no S38 as emissões do refino (a REFAP) e da mineração de carvão.
- **No RB** a correspondência não é exata. O total nacional da NEREUS (1836.7 Mt) também não bate com nenhum total do SEEG 13.0.
- **É um indício, não uma prova.**

### 3.1 Diagnóstico (obrigatório; não muda a versão principal)

1. **Reproduza a tabela acima** a partir do arquivo bruto, com o script versionado e o recorte salvo em `dados/externos/seeg/`. Confira os números; se algum divergir, mostre o seu e explique.
2. **Teste outras métricas.** Repita só os totais (S38-RS, S38-RB, total RS e total Brasil, emissão bruta e líquida) para GWP-AR2, AR4 e AR6 e para as GTP. Diga se alguma bate melhor com a NEREUS.
3. **Teste o casamento de outros setores do RS:**
   - compare os setores da NEREUS com maiores emissões no RS (S01, S02, S03, S19, S26, S39 e S43) com somas de atividades do SEEG do RS;
   - o objetivo é ver se o padrão "atividade do SEEG → setor da MIP" se repete;
   - registre só casamentos com diferença menor que 0.1% **e** com sentido econômico. Diga quantas combinações testou: com muitas combinações, coincidências aparecem.
4. **Escreva a conclusão com cautela.** Use "indício", "compatível com". Nunca escreva que a NEREUS fez X: não temos a documentação da conta-satélite.
5. **Saídas:**
   - `resultados/rodada05/diagnostico_seeg_nereus.xlsx`;
   - a Seção 19 do relatório;
   - a Tabela A7 do apêndice (Seção 5.1).

### 3.2 Variante E4 (sensibilidade)

**Base:** a E1 da versão final. **Só o vetor de CO₂e muda**; a MIP monetária é a da versão final.

**Regra.** Em cada região, retire de DIS e GAS (na proporção do resíduo E1 de cada um, sem mexer no SF6) os valores abaixo, do SEEG 13.0, e some-os ao setor indicado da mesma região:

| Região | Componentes do SEEG (tabela acima) | Vai para | Referência (mil t) |
|---|---|---|---|
| RS | Refino de petróleo (as duas linhas: "Produção de combustíveis" e "Geração de eletricidade › Produção de combustíveis") | S19 | 1736.0 + 76.1 = 1812.1 |
| RS | Produção de carvão mineral e outros | S04 | 88.1 |
| RB | Refino de petróleo (as duas linhas) | S19 | 17329.1 + 759.7 = 18088.8 |
| RB | Exploração de petróleo e gás natural (as duas linhas) | S05 | 17721.0 + 5778.2 = 23499.2 |
| RB | Produção de carvão mineral e outros | S04 | 1155.4 |

- O "Não alocado" não entra.
- O que sobrar do resíduo continua em DIS e GAS. Referência: sobram cerca de 93 mil t no RS e 7220 mil t no RB.
- **A0_E4:** na MIP original, retire os mesmos valores do S38 de cada região e some-os a S19, S05 e S04. Serve para mostrar quanto dos resultados do artigo vem dessas emissões.

**Checagens (T14):**
- valores movidos exatos;
- total de CO₂e da economia inalterado;
- S38 reduzido exatamente no valor movido;
- nenhuma emissão negativa.

O T2 da E4 só vale para o total (como na E3), e isso deve estar documentado.

**Referência preliminar** (feita sobre a v03; os seus números serão os da v04), variação da E4 em relação à E1:

| Cenário | Variação |
|---|---|
| A2 E1 | −31.2% |
| A2 R1 | +1.8% |
| A2 F1 | +2.1% |
| A2 R2, R3, R4a, F2, F3 | de +1.2% a +2.9% |
| A2 F1 com 100% GN | +8.5% |
| B por TWh: EOL, HID, GN | +4.2% |
| B por TWh: CAR | 0.0% |

---

## 4. Simulações finais

- **Cenários:** os mesmos da Rodada 04 (`parametros/cenarios_v04.csv`), rodados na versão final. Recalcule as proporções do A2 fóssil (CAR × GN) pelo VBP da versão final.
- **Robustez:** todas as variantes da Seção 2.4 e o A0_E4.
- **B por TWh:**
  - SOL-RS já com a D18; a linha "SOL com a TUST do espelho" sai e vira só um registro no relatório;
  - colunas novas: **g CO₂e/kWh** (= t por TWh ÷ 1000) e **emissões evitadas por TWh em relação ao gás natural** (além de em relação ao carvão).
- **Saída:** `resultados/rodada05/simulacoes_v04.xlsx`, com as mesmas abas da Rodada 04 e mais `A0_E4`, `E4` e `rap_media`.

---

## 5. Material do artigo (pasta `artigo/`)

**Regras gerais:**
- **Idioma:** português do Brasil.
- **Números:** padrão brasileiro em `.docx` e `.md`. No `.xlsx`, células numéricas, com formato de exibição de uma casa decimal.
- **Um único script.** Tudo sai de `scripts/rodada05_artigo.py`, a partir dos arquivos de resultado. Nenhum número digitado à mão.
- **Formatação dos `.docx`** (é a do artigo):
  - A4, margens de 2.5 cm;
  - texto em Times New Roman 12;
  - tabelas em Times New Roman 8, cabeçalho em negrito, todas as bordas simples de 0.5 pt, tabela centralizada;
  - título **acima** da tabela ("**Tabela N:** título");
  - fonte e notas **abaixo**, em itálico 10: "*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*";
  - equações nativas do Word: escreva o texto em Markdown com LaTeX e converta com pandoc (`pip install pypandoc_binary`).
- **Para o revisor ler no GitHub:** cada tabela e cada texto também sai em `.md`.
- **Você não tem o artigo e não vai editá-lo.** Também não escreva a discussão dos resultados: a interpretação fica com o Francisco e o revisor. Os textos desta seção são técnicos e descritivos.

**Rótulos:**

| Item | Rótulos |
|---|---|
| Cenários principais | "Energia elétrica agregada RS", "Cesta renovável RS", "Cesta fóssil RS" |
| Cestas da sensibilidade | "Renovável base", "Renovável balanceada", "Renovável infraestrutura-intensiva", "Renovável energia/transporte-intensiva", "Fóssil base", "Fóssil balanceada", "Fóssil energia-intensiva" |
| Regiões | "RS", "RB" |

**Nomes curtos dos setores:**
- **Do artigo** (use exatamente estes):

  | Código | Nome |
  |---|---|
  | S01 | Agricultura e apoio à agricultura |
  | S03 | Produção florestal, pesca e aquicultura |
  | S19 | Refino de petróleo e coquerias |
  | S26 | Fabricação de produtos de minerais não metálicos |
  | S27 | Siderurgia e tubos de aço sem costura |
  | S28 | Metalurgia de metais não ferrosos e fundição |
  | S29 | Fabricação de produtos de metal, exceto máquinas e equipamentos |
  | S31 | Fabricação de máquinas e equipamentos elétricos |
  | S38 | Energia elétrica, gás natural e outras utilidades |
  | S39 | Água, esgoto e gestão de resíduos |
  | S40 | Construção |
  | S43 | Transporte terrestre |
  | S56 | Serviços de arquitetura, engenharia, testes/análises técnicas e P&D |

- **Demais setores:** forma curta do nome da MIP (S02 = "Pecuária").
- **Subsetores:**

  | Código | Nome |
  |---|---|
  | S38_HID | Geração hidrelétrica |
  | S38_EOL | Geração eólica |
  | S38_SOL | Geração solar fotovoltaica |
  | S38_BIO | Geração a biomassa |
  | S38_CAR | Geração a carvão mineral |
  | S38_GN | Geração a gás natural |
  | S38_PET | Geração a derivados de petróleo |
  | S38_NUC | Geração nuclear |
  | S38_TRA | Transmissão de energia elétrica |
  | S38_DIS | Distribuição e comercialização de energia elétrica |
  | S38_GAS | Gás canalizado e outras utilidades |

### 5.1 Tabelas

**Arquivos:** `artigo/tabelas/tabelas_artigo.xlsx` (uma aba por tabela), `tabelas_artigo.docx` e `tabelas_artigo.md`.

**Painéis.**
- **Painel A:** MIP com o S38 desagregado (A2, versão final).
- **Painel B:** MIP original (A0).
- **O Painel B tem de reproduzir os valores publicados no artigo** (teste T13, valores abaixo).

**Quadro 1 (revisado).** As colunas do quadro original e mais uma, "Setor na MIP desagregada".

| Cenário | Código | Part. (%) | Função no cenário | Setor na MIP desagregada |
|---|---|---|---|---|
| Energia elétrica agregada | S38 | 100 | Expansão agregada do setor energético | S38_DIS e S38_GAS, pela composição da demanda final (dar os %) |
| Cesta renovável | S38 | 30 | Componente energético agregado associado à implantação | S38_EOL |
| Cesta renovável | S31 | 25 | Equipamentos elétricos e componentes de conexão | igual |
| Cesta renovável | S29 | 15 | Estruturas metálicas e componentes físicos | igual |
| Cesta renovável | S40 | 20 | Obras civis, fundações e instalação | igual |
| Cesta renovável | S43 | 5 | Transporte de equipamentos e insumos | igual |
| Cesta renovável | S56 | 5 | Engenharia, projetos, testes e P&D | igual |
| Cesta fóssil | S19 | 40 | Processamento e oferta de combustíveis fósseis | igual |
| Cesta fóssil | S38 | 35 | Energia/gás e utilidades associadas | S38_CAR e S38_GN, pelo VBP de 2019 (dar os %) |
| Cesta fóssil | S43 | 25 | Logística e transporte associados | igual |

Colunas do original: Cenário | Região | Código | Setor | Participação no choque (%) | Valor do choque (R$ milhões) | Função no cenário.

**Tabela 1 — "Impactos econômicos e ambientais dos cenários energéticos"** (Painéis A e B)
- **Colunas:** Cenário | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Produção bruta por mil t CO₂e (R$ milhões).
- **Linhas:**
  - os 3 cenários;
  - "Diferença de emissões incorporadas (fóssil − renovável)", com o valor na coluna de emissões;
  - "Redução da intensidade carbônica", com o % na coluna de intensidade.
- **Painel B, valores exatos:**

  | Cenário | Produção | Emissões | Intensidade | Produção por mil t |
  |---|---|---|---|---|
  | Energia elétrica agregada RS | 1.925,0 | 428.113,5 | 222,4 | 4,5 |
  | Cesta renovável RS | 1.959,4 | 216.407,0 | 110,4 | 9,1 |
  | Cesta fóssil RS | 2.120,6 | 356.045,7 | 167,9 | 6,0 |

  Diferença 139.638,8; redução 34,2%.

**Tabela 2 — "Principais setores responsáveis pelas emissões induzidas pela cesta renovável"** (A2)
- **Colunas:** Ranking | Região | Código | Setor | Produção induzida (R$ milhões) | Emissões induzidas (t CO₂e) | Participação (%).
- **Linhas:**
  - as 10 primeiras;
  - "Demais setores";
  - "Total", com "Cesta renovável RS" na coluna Setor;
  - uma linha de memória: "Memória: subsetores do S38 (RS e RB)", com a soma.
- **Tabela A2 (apêndice):** a mesma tabela para o A0. Tem de reproduzir o artigo:
  - 1º: RS, S38, 357,1 | 99.554,6 | 46,0;
  - 2º: RS, S43, 84,1 | 35.489,9 | 16,4;
  - …
  - 10º: RB, S01, 3,5 | 2.649,5 | 1,2;
  - Demais setores: 16.285,6 | 7,5.

**Tabela 3 — "Spillovers ambientais entre o Rio Grande do Sul e o Restante do Brasil"** (Painéis A e B)
- **Colunas:** Cenário | Região impactada | Produção induzida (R$ milhões) | Emissões induzidas (t CO₂e) | Participação nas emissões (%).
- **Painel B, valores exatos:**

  | Cenário | Região | Produção | Emissões | Participação |
  |---|---|---|---|---|
  | Energia elétrica agregada RS | RS | 1.357,0 | 339.326,4 | 79,3 |
  | Energia elétrica agregada RS | RB | 568,0 | 88.787,1 | 20,7 |
  | Cesta renovável RS | RS | 1.391,3 | 142.390,0 | 65,8 |
  | Cesta renovável RS | RB | 568,0 | 74.016,9 | 34,2 |
  | Cesta fóssil RS | RS | 1.373,2 | 277.141,4 | 77,8 |
  | Cesta fóssil RS | RB | 747,3 | 78.904,3 | 22,2 |

**Tabela 4 — "Sensibilidade dos resultados à composição dos vetores de choque"** (Painéis A e B, as 7 cestas)
- **Colunas:** Cenário | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Emissões indiretas (%) | Emissões no RB (%).
- **Painel B, valores exatos:**

  | Cesta | Produção | Emissões | Intensidade | Indiretas (%) | No RB (%) |
  |---|---|---|---|---|---|
  | Renovável base | 1.959,4 | 216.407,0 | 110,4 | 51,5 | 34,2 |
  | Renovável balanceada | 1.920,4 | 216.987,2 | 113,0 | 46,1 | 29,1 |
  | Renovável infraestrutura-intensiva | 1.969,2 | 169.090,0 | 85,9 | 62,7 | 43,5 |
  | Renovável energia/transporte-intensiva (R4a) | 1.959,5 | 309.794,9 | 158,1 | 39,0 | 23,8 |
  | Fóssil base | 2.120,6 | 356.045,7 | 167,9 | 35,3 | 22,2 |
  | Fóssil balanceada | 2.110,5 | 381.702,9 | 180,9 | 32,9 | 19,7 |
  | Fóssil energia-intensiva | 2.073,9 | 375.427,3 | 181,0 | 35,0 | 21,5 |

- Nota na linha R4a do Painel B: "Vetor da Tabela A1 (45/15/10/10/15/5)."

**Tabela 5 (nova) — "Sensibilidade à tecnologia atribuída ao S38"** (A2, as 7 cestas)
- **Renováveis:** EOL 100% (principal) | EOL 50% + SOL 50% | EOL 2/3 + TRA 1/3.
- **Fósseis:** CAR e GN ∝ VBP (principal) | 100% CAR | 100% GN.
- **Colunas:** as da Tabela 4.

**Tabela 6 (nova) — "Emissões por tecnologia de geração do RS"** (bloco B)
- **Linhas:** Hidrelétrica, Eólica, Solar fotovoltaica, Biomassa, Gás natural, Carvão mineral. Mais uma linha "Distribuição (eletricidade da rede, mix de 2019)", só com as colunas por R$ 1 bilhão.
- **Colunas:**
  - Preço médio (R$/MWh);
  - Produção induzida por TWh (R$ milhões);
  - Emissões por TWh (t CO₂e): diretas, indiretas e total;
  - g CO₂e/kWh;
  - Emissões no RB (%);
  - Emissões por R$ 1 bilhão (t CO₂e);
  - Emissões evitadas por TWh em relação ao carvão (t CO₂e).
- **Nota:** "Choque de 1 TWh (ao preço médio de 2019) e de R$ 1 bilhão na demanda final de cada subsetor de geração do RS. Emissões da operação (produção de energia elétrica); não incluem bens de capital (implantação das usinas). Solar: subsetor sem produção no RS em 2019 (latente), com os coeficientes técnicos do RB e a TUST do RS."

**Tabela 7 (nova) — "Efeito da desagregação: MIP original, S38 desagregado sem e com atribuição de tecnologia"** (A0 → A1 → A2, as 8 cestas)
- **Colunas:**
  - Emissões totais em A0, A1 e A2;
  - variação de A1 e de A2 em relação a A0 (%);
  - intensidade carbônica em A0 e A2;
  - emissões indiretas (%) em A0 e A2;
  - emissões no RB (%) em A0 e A2.
- Se ficar larga demais para A4 retrato, divida em duas.

**Apêndice:**

| Tabela | Conteúdo |
|---|---|
| A1 | Vetores de choque: as 7 cestas (% por setor), como na Tabela A1 do artigo, com uma nota sobre a atribuição do S38 no A2 |
| A2 | Top-10 do A0 (acima) |
| A3 | Os 11 subsetores, RS e RB: VBP (R$ mi), GWh, R$/MWh, t CO₂e/MWh (E1), EOB/VBP, multiplicador de produção, multiplicador de emissões (t CO₂e por R$ mi). Inclua as linhas "S38 agregado (MIP original)" de cada região, como referência |
| A4 | Fontes de dados: dado, fonte, ano ou versão, uso na desagregação |
| A5 | Parâmetros e hipóteses: parâmetro, valor, fonte ou justificativa, sensibilidade testada |
| A6 | Robustez: principal e as 8 variantes (P2, E2, E3, E4, gas4dist, rap_media, k060, eta005). CO₂e e intensidade do A2 (E1, R1 e F1) e do B por TWh (cada tecnologia), com o desvio em relação à principal (%). Inclua o A0_E4 |
| A7 | Diagnóstico NEREUS × SEEG (Seção 3.1) |
| A8 | Testes de consistência, em linguagem de artigo (ex.: "a soma dos 11 subsetores reproduz exatamente a matriz original") |

### 5.2 Figuras

**Arquivos:** `artigo/figuras/`, PNG a 300 dpi **e** PDF.

**Estilo (o das figuras do artigo):**
- matplotlib, fonte DejaVu Sans, 7 × 4.4 polegadas, fundo branco;
- **cores:** RS e emissões diretas = `#2c6e9e`; RB e emissões indiretas = `#da7e2e`;
- grade cinza-clara (`#e0e0e0`) só no eixo de valores; sem bordas superior e direita;
- **sem título dentro da figura** (o título vai na legenda do artigo);
- porcentagens e decimais com vírgula ("46,0%");
- rótulos de setor por extenso com a região ("Transporte terrestre (RS)"), quebrados em cerca de 30 caracteres.

| Figura | Conteúdo |
|---|---|
| **1** | Top-10 da cesta renovável (A2). Barras horizontais, participação (%). Eixo: "Participação nas emissões induzidas pela cesta renovável (%)". Legenda: "Rio Grande do Sul (RS)" e "Restante do Brasil (RB)" |
| **A1** (apêndice) | A mesma figura para o A0 |
| **2** | Emissões diretas × indiretas (%), barras empilhadas a 100%. Os 3 cenários principais, cada um com duas barras ("MIP original" e "MIP desagregada"). Rótulos de % dentro das barras (branco, negrito). Legenda: "Emissões diretas" e "Emissões indiretas" |
| **3** | Bloco B, mil t CO₂e por TWh, empilhado em diretas e indiretas. Dois painéis com escalas próprias: fósseis (carvão, gás natural) e demais (biomassa, eólica, solar, hidrelétrica). Valor no fim da barra, com uma casa decimal |
| **4** | Emissões totais por cesta, A0 × A2. Dois painéis: as 4 renováveis e as 3 fósseis, mais o cenário de energia agregada no painel que fizer sentido |

### 5.3 Textos (pasta `artigo/texto/`; cada um em `.md` e `.docx`)

**Estilo:**
- impessoal ("adotou-se", "foi realizada"), técnico e preciso;
- sem adjetivos de valor ("robusto", "significativo") que não venham com o número;
- hipóteses escritas como hipóteses ("supôs-se que…");
- no texto, nomes por extenso ("geração eólica"); códigos (S38_EOL) só nas tabelas;
- equações em LaTeX, numeradas provisoriamente a partir de **(15)** (o artigo vai até a (14)). Notação do artigo:
  - Z_ij = fluxos; X_j = VBP; A = Z·diag(X)⁻¹; Y e ΔY = demanda final; e_i = CO2_i/X_i;
  - aqui, acrescente r ∈ {RS, RB} para região e k ∈ K = {HID, …, GAS} para subsetor.

**(a) `secao_3x_desagregacao`** — subseção para o corpo do artigo. Título provisório "3.x Desagregação do setor de energia elétrica, gás natural e outras utilidades (S38)". **Entre 1.200 e 1.800 palavras.** Conteúdo, nesta ordem:
1. **Motivação:** o S38 agregado mistura tecnologias com intensidades de emissão muito diferentes, e o objetivo é separá-las. Sem afirmações sobre as conclusões do artigo.
2. **Os 11 subsetores** e o critério do VBP de cada um (Quadro 2: código, subsetor, critério, fonte).
3. **Princípio:** a desagregação preserva a matriz original. Escreva as restrições de agregação em equações:
   - soma dos subsetores nas linhas;
   - soma nas colunas;
   - soma no bloco S38 × S38;
   - soma no VBP;
   - soma no CO₂e (na E1).
4. **Produção:**
   - âncora da geração;
   - GWh × preço;
   - transmissão (D17);
   - gás canalizado (Sulgás);
   - distribuição como resíduo.
5. **Vendas (linhas) e compras (colunas):**
   - roteamento dentro do bloco;
   - combustíveis;
   - TUST por MWh;
   - remunerações;
   - insumos não energéticos com o ajuste RAS e o EOB mínimo.
6. **Emissões:**
   - E1;
   - o resíduo e o que o diagnóstico sugere sobre ele, com cautela;
   - E3 e E4 como sensibilidades.
7. **Subsetores sem produção no RS em 2019** (latentes) e como foram tratados.
8. **Verificação:** re-agregação exata; reprodução dos resultados do artigo na MIP original.
9. **Como os choques foram atribuídos:**
   - A1 e A2;
   - o bloco B, por R$ 1 bilhão e por TWh, explicando que se trata da operação e não da implantação.

Cite a literatura de método ao descrever o procedimento:
- Wolsky (1984);
- Lenzen (2011);
- Lindner, Legault e Guan (2012; 2013);
- Peters (2016), GTAP-Power;
- Lahr e de Mesnard (2004), RAS;
- Miller e Blair (2022).

**(b) `apendice_B_nota_tecnica`** — a versão completa, para o apêndice. Todos os passos, parâmetros, fontes, testes e variantes, remetendo às Tabelas A3 a A8. Sem limite de tamanho, mas sem repetir tabelas inteiras no texto.

**(c) `limitacoes`** — parágrafos curtos, um por limitação:
1. Hidrelétrica, eólica e solar compartilham a mesma estrutura de insumos não energéticos (não há dado de custo por tecnologia).
2. A solar e os derivados de petróleo não produziam no RS em 2019: são latentes, com coeficientes do RB.
3. O resíduo de emissões do S38 (E1) e o que o diagnóstico sugere. Mostre a faixa E3/E4.
4. O bloco B mede a operação, sem bens de capital. Os valores por TWh não são comparáveis diretamente a estudos de ciclo de vida.
5. Os preços por fonte vêm de leilões, ajustados à produção da MIP. Mostre o efeito dos preços iguais (P2).
6. As térmicas a gás ficam com poucos insumos não energéticos (ALERTA do T12). Mostre o efeito do κ = 0.60.
7. A transmissão vem dos encargos faturados pelo ONS. Mostre o efeito da `_rap_media`.
8. Os pesos das cestas continuam hipóteses dos autores. A desagregação muda o S38, não a composição das cestas.
9. O modelo continua linear, sem substituição entre fontes, sem mudança de preços e sem as emissões dos importados.

**(d) `numeros_chave.md`** — todos os números que provavelmente serão citados no texto: resultados principais, participações, diferenças, por TWh e faixas da robustez. Cada um com:
- o valor bruto;
- o valor no padrão brasileiro;
- o arquivo, a aba e a linha de onde veio.

**(e) `referencias.md`** — em ABNT, no estilo do artigo (exemplo: "LENZEN, Mark. Environmentally important paths, linkages and key sectors in the Australian economy. Structural Change and Economic Dynamics, v. 14, n. 1, p. 1–34, 2003.").
- Inclua tudo o que os textos (a)–(c) citam: método e fontes de dados (ONS, ANEEL, EPE, SEEG, IBGE, Sulgás, MME, Comex Stat, CVM).
- **Confira os dados de cada referência** (título, periódico, volume, páginas, DOI) no Crossref (`api.crossref.org`) ou na própria fonte. Marque **[CONFERIR]** o que não conseguir confirmar.

---

## 6. Testes e checagens

- **Todas as anteriores**, na versão final e nas variantes:
  - T1;
  - T2 (E3 e E4 só pelo total);
  - T9 a T11;
  - T12, com o ALERTA aceito pela D19.
- **T13 (novo):** os Painéis B das Tabelas 1, 3 e 4 e a Tabela A2 reproduzem os valores listados na Seção 5.1. São os valores publicados no artigo, exceto a linha R4a da Tabela 4 (D11). Arredondados a uma casa, os valores têm de ser idênticos.
- **T14 (novo):** E4 e A0_E4 (Seção 3.2).
- **T15 (novo):** rodar `scripts/rodada05_artigo.py` duas vezes dá os mesmos números em todas as tabelas.
- **T16 (novo):** D18 — a TUST por MWh das colunas latentes, ao p_k, é igual a τ_RS.
- **Revisão adversarial**, como nas rodadas anteriores. Se os agentes atingirem o limite de uso, faça as conferências você mesmo e registre.

---

## 7. Relatório

Salve em `respostas/RODADA_05_resposta.md`, com as seções 1 a 16 do modelo das rodadas anteriores e mais:
- **17. v03 × v04:** o efeito de D17 e de D18 em VBP, multiplicadores e resultados.
- **18. Resultados finais:** as Tabelas 1 a 7 em Markdown.
- **19. Diagnóstico NEREUS × SEEG e variante E4.**
- **20. Material do artigo:** a lista completa de arquivos de `artigo/`, com caminho, o que é e para que serve.

Também:
- atualize `respostas/HISTORICO.md` e o `README.md`;
- crie a tag **`mip-v04-final`** no commit final e faça push da tag;
- não mude a visibilidade do repositório.

Na última mensagem, diga:
- onde está o relatório;
- se tudo foi para a `main`;
- o que o Francisco precisa fazer ou decidir.

---

## 8. Checklist final

- [ ] Trabalho a partir da `main`; push para a `main`; tag `mip-v04-final`
- [ ] D17 e D18 aplicadas (v04); D19 a D21 respeitadas
- [ ] Variantes, incluindo `_E4` e `_rap_media`; A0_E4
- [ ] Diagnóstico NEREUS × SEEG reproduzido e testado (3.1)
- [ ] Simulações finais e robustez (`simulacoes_v04.xlsx`)
- [ ] Tabelas (Quadro 1, Tabelas 1 a 7, A1 a A8) em `.xlsx`, `.docx` e `.md`; T13 passando
- [ ] Figuras 1 a 4 e A1 em PNG (300 dpi) e PDF
- [ ] Textos (a) a (e) em `.md` e `.docx`
- [ ] Testes T1 a T16
- [ ] Relatório, `HISTORICO.md` e `README.md`
