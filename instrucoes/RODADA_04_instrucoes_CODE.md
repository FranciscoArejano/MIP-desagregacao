# Instruções para o Claude Code — Rodada 04 (MIP v03 final + simulações)

> **ESTE ARQUIVO É PARA O CLAUDE CODE.**
> Projeto: desagregação do S38 na MIP inter-regional RS × Restante do Brasil, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
> Data: 16/10/2026 · Base: MIP v02 (`respostas/RODADA_03_resposta.md`)
>
> Trabalhe a partir da `main` e termine com push para a `main`. O repositório continua público por decisão do Francisco (não altere).
> Convenção numérica: ponto decimal, sem separador de milhar.

---

## 0. O que esta rodada entrega

1. **MIP v03 (versão final)**: a v02 com três ajustes de método (Seção 2).
2. **Simulações do artigo** na v03, em dois blocos (Seção 3), com tabelas no formato do artigo e figuras de rascunho.
3. Relatório `respostas/RODADA_04_resposta.md`.

As regras fixas de sempre continuam valendo:
- original intocável;
- nada sobrescrito (saídas em `resultados/rodada04/`, parâmetros `_v03`);
- nenhum dado inventado; toda hipótese marcada como hipótese;
- brutos grandes fora do git;
- fontes em `FONTES.md`;
- revisão adversarial antes de fechar, como você fez na Rodada 03.

---

## 1. Decisões do Francisco

Valem as anteriores: D1 = C; D2, D3, D4 e D6 = A; D5 = E1; D7 = A; D8 = A; D9 = (a) + (b) + (f) + (r); D10 = Sulgás. Somam-se as abaixo. Se a mensagem de abertura indicar outra opção, ela prevalece.

| Decisão | Escolha |
|---|---|
| **V1** — viabilidade das térmicas | TUST da geração **na proporção do MWh gerado no SIN** e remunerações da geração **na proporção de (VBP − combustível)**; extensão de viabilidade só como reserva (Seção 2.1) |
| **V2** — VBP do GAS-RB | **Preço da Sulgás** (19421.0) na principal; as 4 distribuidoras (26990.1) viram sensibilidade (Seção 2.2) |
| **V3** — RAP | Mantém 24883.4 na principal; sensibilidade com os encargos de uso faturados pelo ONS no ano civil de 2019 (Seção 2.3) |
| **D11** — cenário R4 | **R4a** (vetor da Tabela A1: 45/15/10/10/15/5) é o oficial; R4b só aparece no bloco A0, para registro |
| **D12** — o S38 da cesta renovável | **100% S38_EOL-RS**; sensibilidades 50% EOL + 50% SOL-RS (latente) e 2/3 EOL + 1/3 TRA-RS |
| **D13** — o S38 da cesta fóssil | **Térmicas do RS na proporção do VBP de 2019** (CAR-RS e GN-RS); sensibilidades 100% CAR-RS e 100% GN-RS |
| **D14** — cenário "energia elétrica agregada" (E1) | S38 → DIS-RS e GAS-RS **na proporção das vendas à demanda final** (a regra do executor) |
| **D15** — comparação de tecnologias | Bloco B com choques **por R$ 1 bi e por 1 TWh** (Seção 3.2) |
| **D16** — implantação por vetores de investimento | **Fora desta rodada** (agenda futura) |

---

## 2. MIP v03: três ajustes na v02

### 2.1 V1 — TUST e remunerações das térmicas

O problema da v02: com a TUST da geração repartida pelo VBP, e as remunerações também, as térmicas caras (GN e PET) pagavam TUST e salários demais. Por isso foi preciso a extensão de viabilidade, que zerou os insumos não energéticos delas.

1. **TUST da geração** (a parte de 1 − α que vai à geração de cada região compradora): reparta entre os subsetores de geração na proporção do **MWh gerado no SIN**.
   - MWh no SIN de cada fonte = mínimo entre o GWh da D8 e o GWh do ONS (rótulo do ONS, sem autoprodução).
   - Os sistemas isolados não estão no SIN e não pagam TUST. Exemplo: PET-RB = min(5174, 1974.3) = 1974.3.
   - Latentes e zerados não pagam.
   - Referência do RB (GWh): HID 363907.4 · EOL 48122.9 · SOL 4384.6 · BIO 1771.8 · CAR 11197.8 · GN 46474.0 · PET 1974.3 · NUC 16128.8.
   - RS: o ONS direto.
2. **Remunerações da geração (CEMPRE):** reparta entre as fontes na proporção de **(VBP − combustível)**, em vez do VBP. O combustível é repasse e não exige mão de obra proporcional. Use a mesma regra nas ocupações.
3. Rode o piso κ = 0.70 e o reequilíbrio η = 0.10.
   - Se o T9 passar **sem** a extensão de viabilidade, desligue a extensão na principal.
   - Se não passar, mantenha a extensão só onde for necessária e reporte em quais subsetores e por quanto.
4. Reporte os insumos não energéticos/VBP de GN-RB, PET-RB e GN-RS antes (v02) e depois (v03).

### 2.2 V2 — VBP do GAS-RB pelo preço da Sulgás

A principal passa a usar o preço da Sulgás (1.390 R$/m³), com VBP do GAS-RB = 19421.0, a mesma regra da variante `_gas_sulgas` da v02. Motivo: com o preço médio das 4 distribuidoras, o gás não cabe nas compras industriais ao S38 da própria MIP, e o teto de 0.90 vira regra ativa para 13 compradores.

O teto de 0.90 continua como salvaguarda (com o preço da Sulgás, nenhum comprador deve encostar nele; confira). A versão com as 4 distribuidoras vira sensibilidade.

### 2.3 V3 — Sensibilidade da RAP com dado oficial do ONS

A principal fica como está (RAP 2019 = 24883.4). Acrescente a variante `_rap_ons`, com o valor da transmissão de 2019 igual aos **encargos de uso da transmissão faturados pelo ONS no ano civil de 2019**:

| Relatório do ONS (SEAMSE) | URL | "Total Encargos de Uso", acumulado no ciclo |
|---|---|---|
| dez/2018 | `https://www.ons.org.br/AcervoDigitalDocumentosEPublicacoes/SEAMSE_201812.pdf` | 10576544162.01 (jul–dez/2018) |
| jun/2019 | `https://www.ons.org.br/AcervoDigitalDocumentosEPublicacoes/SEAMSE_201906.pdf` | 21367058292.17 (jul/2018–jun/2019) |
| dez/2019 | `https://www.ons.org.br/AcervoDigitalDocumentosEPublicacoes/SEAMSE_201912.pdf` | 12145090044.99 (jul–dez/2019) |

Ano civil 2019 = (21367.06 − 10576.54) + 12145.09 = **22935.6 R$ mi**. Confira os números nos PDFs e registre em `valores_documentais_v03.csv`.

Se o Francisco anexar ou subir no repositório o texto integral da REH 2.565/2019 com o total da RAP 2019-2020, troque o valor secundário (25700) pelo oficial na principal e reporte a diferença.

### 2.4 Produtos da v03

- **Principal:** `resultados/rodada04/MIP_RS_RB_2019_S38_11sub_v03.xlsx` + `_longo.csv` + `_coef_latentes.csv`.
- **Variantes (CSV longo):** `_P2`, `_E2`, `_E3`, `_gas4dist`, `_rap_ons`, `_k060`, `_eta005`.
- **Quadro** `quadro_subsetores_v03.xlsx`, com a aba `v02_x_v03` e as checagens.
- Todos os testes: T1–T11 e os da Rodada 03, mais um **T12**: na principal, nenhum subsetor com produção tem insumos não energéticos/VBP abaixo de 0.05 (ou ALERTA explicado).

---

## 3. Simulações do artigo na v03

Use o executor de cenários. Todos os choques são de R$ 1000 milhões na demanda final de setores do RS, salvo indicação. Para cada cenário, produza os indicadores do artigo:
- produção induzida total, no RS e no RB;
- CO₂e total, no RS e no RB;
- intensidade carbônica (IC);
- produção por mil t;
- % das emissões no RB;
- emissões diretas e indiretas (eq. 12–14 do modelo);
- top-10 setores por emissão;
- participação do S38, ou dos subsetores do S38, nas emissões.

### 3.1 Bloco A — ponte com o artigo (as mesmas cestas)

| Sub-bloco | MIP | Como o S38 da cesta entra |
|---|---|---|
| A0 | original | Como no artigo (replicação; inclui R4a e R4b) |
| A1 | v03 | S38 → DIS e GAS do RS, na proporção das vendas à demanda final: efeito "puro" da desagregação |
| A2 | v03 | **S38 remapeado para tecnologias** (abaixo) |

Remapeamento no A2:
- **Cestas renováveis (R1, R2, R3, R4a):** a parcela do S38 → 100% EOL-RS (D12). Sensibilidades: 50% EOL + 50% SOL-RS, e 2/3 EOL + 1/3 TRA-RS.
- **Cestas fósseis (F1, F2, F3):** a parcela do S38 → CAR-RS e GN-RS na proporção do VBP de 2019 na v03 (D13). Sensibilidades: 100% CAR-RS e 100% GN-RS.
- **Energia agregada (E1):** como em A1 (D14).

Os demais setores das cestas (S31, S29, S40, S43, S56, S19) ficam como no artigo.

### 3.2 Bloco B — operação por tecnologia (contribuição nova)

| Cenário | Choque |
|---|---|
| B-EOL, B-SOL (latente), B-HID, B-BIO, B-CAR, B-GN | R$ 1000 mi na demanda final do subsetor do RS |
| B-DIS | R$ 1000 mi em DIS-RS (eletricidade da rede, com o mix de 2019) |
| **B-TWh-***(mesmas tecnologias)* | **1 TWh** de cada tecnologia do RS, valorado ao R$/MWh da v03 (choque = R$/MWh × 1000 GWh ÷ 1000, em R$ mi). Para o SOL-RS (latente), use o R$/MWh do SOL-RB |

Inclua uma tabela "**emissões por TWh**" (t CO₂e por TWh demandado, total, direto e indireto, e % no RB) e a diferença entre cada fonte e o carvão: "emissões evitadas por TWh se a eólica substituir o carvão".

Deixe explícita, no relatório e nas tabelas, a **limitação**: HID, EOL e SOL têm a mesma estrutura de insumos não energéticos, porque não há dado de custo por tecnologia. As diferenças entre elas vêm do VBP e do latente, e não de tecnologia.

### 3.3 Sensibilidade das simulações

Rode os cenários principais (A2: R1, F1, E1; B: todos por TWh) nas variantes da v03: `_P2`, `_E2`, `_E3`, `_gas4dist`, `_rap_ons`, `_k060`, `_eta005`. Monte uma tabela de robustez com a faixa (mín–máx) de CO₂e total, IC e % RB por cenário.

### 3.4 Saídas

- `resultados/rodada04/simulacoes_v03.xlsx`, com abas:
  - `A0`, `A1`, `A2`, `A2_sens`, `B_RS1bi`, `B_TWh`, `robustez`, `top10_*`;
  - `tabela1_artigo`, `tabela2_artigo`, `tabela3_artigo` e `tabela4_artigo`: as tabelas do artigo refeitas com A2, no mesmo formato e com os mesmos rótulos;
  - `comparacao_artigo` (artigo original × A1 × A2, para E1, R1 e F1).
- **Figuras de rascunho** (PNG, `resultados/rodada04/figuras/`), com "RASCUNHO" no título:
  - Fig. 1: top-10 emissores na cesta renovável (A2);
  - Fig. 2: emissões diretas × indiretas por cenário (A0 × A2);
  - Fig. 3: t CO₂e por TWh por tecnologia (B).
- `parametros/cenarios_v03.csv`: todos os cenários desta rodada no formato do executor.

---

## 4. Relatório

Salve em `respostas/RODADA_04_resposta.md`, com as seções de sempre e mais:

17. **v02 × v03:** efeito de V1, V2 e V3.
18. **Resultados das simulações:**
    - A0 × A1 × A2 para E1, R1 e F1;
    - a tabela por TWh do bloco B;
    - a robustez;
    - os 5 achados principais, em linguagem simples, para o Francisco usar no texto. Só fatos dos números; nenhuma interpretação de política.

Atualize também `respostas/HISTORICO.md` e o `README.md`. Push para a `main`. Na última mensagem: onde está o relatório, se tudo foi para a `main` e o que o Francisco precisa decidir.

---

## 5. Checklist final

- [ ] V1, V2 e V3 aplicados; T9 e T12 passando (ou ALERTA explicado); extensão de viabilidade desligada se não for necessária
- [ ] Variantes da v03 geradas
- [ ] Blocos A0, A1, A2 (com sensibilidades) e B (por R$ 1 bi e por TWh)
- [ ] Robustez nas variantes
- [ ] Tabelas no formato do artigo e figuras de rascunho
- [ ] Revisão adversarial feita e registrada
- [ ] Relatório, `HISTORICO.md` e `README.md`; push para a `main`
