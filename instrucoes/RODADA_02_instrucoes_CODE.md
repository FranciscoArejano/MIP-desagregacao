# Instruções para o Claude Code — Rodada 02

> **ESTE ARQUIVO É PARA O CLAUDE CODE.**
> Projeto: desagregação do S38 na MIP inter-regional RS × Restante do Brasil, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
> Data: 15/10/2026 · Rodada anterior: `respostas/RODADA_01_resposta.md` (tudo validado; 56 testes passando)
>
> **Antes de começar:** leia este arquivo inteiro. Execute as etapas na ordem. O relatório (Etapa 7) é obrigatório.
> Convenção numérica: ponto decimal, sem separador de milhar.

---

## 0. O que esta rodada entrega

1. Teste de acesso às fontes de dados (o Francisco liberou a rede do ambiente).
2. Coleta e tratamento dos dados de 2019, com scripts e fontes registradas.
3. Ajustes no motor para os 11 subsetores: dois subsetores de rede e roteamento do bloco S38→S38 por componentes.
4. Parâmetros reais em `parametros/*_v01.*`, cada número com fonte.
5. **MIP desagregada v01** (versão principal) + três variantes de sensibilidade, com todas as checagens.
6. Quadro-diagnóstico dos subsetores e, se der tempo, uma prévia de multiplicadores (não é resultado do artigo).
7. Relatório em `respostas/RODADA_02_resposta.md`.

Se faltar tempo ou dado, a prioridade é 1 → 2 → 3 → 4 → 5 → 7. O item 6 vem por último.

---

## 1. Decisões do Francisco (valem para esta rodada)

| Decisão | Escolha |
|---|---|
| D1 — subsetores | **C: 11 subsetores** (Seção 3) |
| D2 — regiões | **A:** desagregar no RS e no RB |
| D3 — VBP | **A:** o valor total da geração de cada região vem do bloco S38→S38, descontada a transmissão; a repartição entre fontes é MWh × preço médio por fonte. A opção B (preços iguais) entra como sensibilidade |
| D4 — vendas | **A:** geração → rede → usuários, agora com dois subsetores de rede (transmissão e distribuição) |
| D5 — emissões (revisada) | **E1** como versão principal (Seção 6.6); E2 e E3 como sensibilidades |
| D6 — produção zero | **A:** Solar-RS e Petróleo-RS como subsetores latentes; Nuclear-RS fica zerado, sem latente |
| D7 — coluna de insumos do S38-RS | **A:** manter como está na base, sem ajuste híbrido (o ponto 2 do seu relatório anterior vira limitação documentada) |

Se a mensagem de abertura do Francisco indicar outra opção para D5 ou D7, a mensagem prevalece.

---

## 2. Regras fixas

Todas as regras da Rodada 01 continuam valendo: original intocável (T1), nada sobrescrito, nenhum dado inventado, tudo por script, português, relatório e git. Novidades desta rodada:

1. **Arquivos brutos grandes não vão para o git.** O GitHub recusa arquivos acima de 100 MB, e o do SEEG tem 185 MB. Brutos acima de 20 MB ficam em `dados/externos/brutos/` (incluída no `.gitignore`). No git ficam o script de download, o SHA-256, a URL, a data de acesso e o recorte usado (CSV pequeno) em `dados/externos/<fonte>/`.
2. **Todo número externo** usado em parâmetro tem uma linha em `dados/externos/FONTES.md` e aparece na coluna `fonte` dos CSVs de parâmetros.
3. **Encoding:** os CSVs da ANEEL variam (o SIGA vem em UTF-8; o de leilões, em Latin-1, com decimal vírgula). Detecte.
4. **SEEG:** o servidor (CloudFront) devolve 403 sem User-Agent de navegador. Envie um User-Agent de navegador.
5. **Valores de referência:** nas Seções 5 e 6 há números que eu (Cowork) obtive dessas mesmas fontes. Reproduza-os. Se a diferença passar da tolerância indicada, investigue e reporte; não force o resultado.
6. **Não altere** a branch padrão nem a visibilidade do repositório: isso é com o Francisco.

---

## 3. Os 11 subsetores

Substituem o S38 de cada região, nesta ordem: 78 setores por região, 156 setores-região.

| Código | Subsetor | Tipo no motor | RS em 2019 | RB em 2019 |
|---|---|---|---|---|
| S38_HID | Geração hidrelétrica (UHE, PCH, CGH) | geracao | produz | produz |
| S38_EOL | Geração eólica | geracao | produz | produz |
| S38_SOL | Geração solar fotovoltaica (centralizada) | geracao | **latente** | produz |
| S38_BIO | Geração a biomassa e biogás (inclui licor negro e resíduos sólidos urbanos) | geracao | produz | produz |
| S38_CAR | Geração termelétrica a carvão mineral (inclui gases siderúrgicos) | geracao | produz | produz |
| S38_GN | Geração termelétrica a gás natural | geracao | produz (UTE Canoas) | produz |
| S38_PET | Geração termelétrica a derivados de petróleo | geracao | **latente** | produz |
| S38_NUC | Geração nuclear | geracao | **zero** | produz |
| S38_TRA | Transmissão de energia elétrica | transmissao | produz | produz |
| S38_DIS | Distribuição e comercialização de energia elétrica | distribuicao | produz | produz |
| S38_GAS | Gás natural canalizado e outras utilidades (vapor, água quente) | gas_utilidades | produz | produz |

---

## 4. Etapa 1 — Testar o acesso às fontes

Antes de qualquer coisa, teste as URLs da Seção 5. Se uma fonte **obrigatória** (5.1, 5.4, 5.5, 5.7 e 5.8) estiver bloqueada:
- registre o domínio exato que falhou;
- faça a Etapa 3 (motor) mesmo assim;
- pare antes da Etapa 4 e explique no relatório o que o Francisco precisa liberar.

---

## 5. Etapa 2 — Coletar e tratar os dados de 2019

Scripts: `scripts/rodada02_coleta.py` (downloads) e `src/mip/dados_externos.py` (tratamento). Saídas tratadas em `dados/intermediarios/*_v01.csv`.

### 5.1 Geração por usina — ONS (obrigatória)

- **URL:** `https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/GERACAO_USINA-2_2019.parquet` (25 MB).
- **Colunas usadas:** `id_estado`, `cod_modalidadeoperacao`, `nom_tipocombustivel`, `nom_usina`, `ceg`, `val_geracao`. O `val_geracao` é MWmed em cada hora; a soma no ano dá MWh.
- **Região:**
  - `id_estado == "RS"` → RS;
  - `id_estado == "I"` (Itaipu 50 Hz, parcela paraguaia) → **importação**, não é geração do RB;
  - demais → RB.
- **Subsetor:** use o rótulo `nom_tipocombustivel` do ONS: Hidráulica→HID, Eólica→EOL, Fotovoltaica→SOL, Biomassa→BIO, Carvão→CAR, Gás→GN, Óleo Diesel e Óleo Combustível→PET, Nuclear→NUC. Duas exceções:
  1. "Resíduos Industriais" → classificar pelo SIGA (5.2);
  2. UTE Canoas (RS) → GN. O ONS a rotula como diesel, mas o SIGA a registra como gás natural, e o SEEG mostra emissões de gás no RS em 2019 compatíveis com a geração dela.
- **Saídas:** `geracao_2019_usina_v01.csv` (usina, CEG, região, subsetor, GWh) e `geracao_2019_regiao_subsetor_v01.csv`.
- **Referência (GWh; tolerância 0.5):**

| | HID | EOL | CAR | GN | BIO | PET | SOL | NUC | Resíduos Ind. | Total |
|---|---|---|---|---|---|---|---|---|---|---|
| RS (já com as exceções) | 14542.6 | 5266.9 | 2625.2 | 174.6 | 140.9 | 0 | 0 | 0 | — | 22750.2 |
| RB (rótulo ONS, antes de reclassificar) | 370796.7 | 48122.9 | 11338.7 | 46474.0 | 9271.9 | 1974.3 | 4384.6 | 16128.8 | 9440.4 | 517932.3 |

  Itaipu 50 Hz (importação): 24402.2. No RS, a BIO soma São Sepé, São Borja e CMPC (licor negro, rotulada "Resíduos Industriais" pelo ONS).
- **"Resíduos Industriais" no RB** (6 usinas, GWh): Do Atlântico 2758.4 · Klabin Celulose 1777.1 · CSP 1611.8 · Suzano Maranhão 1255.4 · CST 1198.5 · Sol 839.2. Sugestão: gases siderúrgicos (Do Atlântico, CSP, CST) → CAR; licor negro (Klabin, Suzano) → BIO; as demais pelo SIGA. Registre a tabela final no relatório.

### 5.2 Cadastro de usinas — ANEEL SIGA

- **URL:** `https://dadosabertos.aneel.gov.br/dataset/6d90b77c-c5f5-4d81-bdec-7bc619494bb9/resource/11ec447d-698d-4ab8-977f-b424d5deee6a/download/siga-empreendimentos-geracao.csv` (UTF-8, separador `;`).
- **Uso:** classificar as usinas pelo `DscFonteCombustivel` (e `NomFonteCombustivel`, se precisar):
  - Carvão mineral → CAR;
  - Gás natural → GN;
  - Petróleo → PET;
  - Outros Fósseis → pelo nome: gás de alto-forno ou de coqueria → CAR; gás de refinaria ou derivados → PET;
  - Agroindustriais, Floresta, Resíduos sólidos urbanos, Resíduos animais, Biocombustíveis líquidos → BIO.
- **Casamento com o ONS:** pelo núcleo numérico do CEG (6 dígitos). No SIGA é o `IdeNucleoCEG`; no ONS, extraia de `ceg` (ex.: `UTE.GN.RS.028038-0.01` → `028038`).

### 5.3 Sistemas isolados (desejável)

O arquivo do ONS cobre só o SIN; as emissões do SEEG (5.7) incluem os sistemas isolados (sobretudo diesel no Norte). Some ao RB a geração dos sistemas isolados em 2019, por fonte, se encontrar a informação (EPE, Anuário Estatístico de Energia Elétrica 2020, ou relatórios de sistemas isolados da EPE/ONS). Se não encontrar, registre: o fator de emissão por MWh do PET-RB ficará superestimado.

### 5.4 Preços médios por fonte — leilões da ANEEL + IPCA (obrigatória)

- **Leilões:** `https://dadosabertos.aneel.gov.br/dataset/593537c6-9e0e-4ed9-817a-2c5d5de05147/resource/a1328fc1-f06b-437d-8893-57ac2c8103df/download/resultado-leiloes-geracao.csv` (Latin-1, `;`, decimal vírgula). Campos: `DatLeilao`, `DscFonteEnergia`, `VlrPrecoLeilao` (R$/MWh na data do leilão), `VlrEnergiaVendida` (MWmed).
- **IPCA:** SIDRA, tabela 1737, variável 2266 (número-índice): `https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all`.
- **Método:**
  - leilões até 31/12/2018;
  - preço corrigido = `VlrPrecoLeilao` × (média do índice em 2019 ÷ índice do mês do leilão);
  - média ponderada por `VlrEnergiaVendida`, por fonte: Hidro→HID, Eólica→EOL, Solar→SOL, Biomassa e Resíduos Sólidos Urbanos→BIO, Carvão→CAR, Gás→GN, Óleo→PET;
  - um preço nacional por fonte, o mesmo nas duas regiões.
- **NUC:** tarifa de Angra 1 e 2 em 2019 = R$ 247.47/MWh (ANEEL, dezembro de 2018). Procure a resolução da ANEEL; se não achar, use o valor citando a fonte jornalística (IstoÉ Dinheiro/Estadão Conteúdo, 18/12/2018).
- **Referência (R$/MWh de 2019; tolerância 1):** HID 166.4 · EOL 173.2 · SOL 260.6 · BIO 203.0 · CAR 251.1 · GN 246.7 · PET 260.0 · NUC 247.47. Média do índice IPCA em 2019: 5213.61.
- **Sensibilidade P2:** preço igual para todas as fontes.

### 5.5 Transmissão — RAP (obrigatória)

- **RAP total do ciclo jul/2019–jun/2020:** R$ 25.7 bilhões (ANEEL, reunião de 25/06/2019; fonte secundária: CanalEnergia). Procure o documento da ANEEL que fixou as RAPs do ciclo para confirmar. Se achar também o total do ciclo 2018-2019, use a média dos dois (ano civil 2019) e reporte os dois valores.
- **Repartição RS × RB (padrão):** pela participação do RS no VBP do S38 das duas regiões, 20942.66 / 345330.00 = 6.06%. Checagem: a RAP do RS precisa ser ≥ RAP da CEEE-GT no ciclo 2019-2020, R$ 749.75 milhões (ANEEL, voto de 22/04/2021).
- **Vendas da transmissão:** só dentro do bloco S38→S38; 50% para a distribuição e 50% para a geração (metodologia da TUST: metade da receita paga pela geração, metade pelo consumo). Confirme a regra 50/50 em documento da ANEEL e registre.

### 5.6 Gás natural canalizado

- **VBP do GAS-RS:** receita operacional líquida da Sulgás em 2019 (demonstrações financeiras, site `sulgas.rs.gov.br`).
- **VBP do GAS-RB:** receita líquida das demais distribuidoras de gás canalizado em 2019 (ABEGÁS, relatórios das companhias ou ANP). Se não houver: (compras de gás alocadas ao GAS-RB) ÷ (1 − 0.25). O 0.25 é a margem de distribuição; registre-o como **hipótese**.
- **Participação térmica no gás comprado (θ), por região:** volume de gás para geração termelétrica em 2019 ÷ volume total comprado pelo S38 (MME, Boletim Mensal de Acompanhamento da Indústria de Gás Natural, dez/2019; ou ANP, Anuário Estatístico 2020). Fallback: gás das térmicas = GWh(GN) × 0.20 m³/kWh (registrar).
- **Gás por setor comprador** (para repartir as vendas entre DIS e GAS): EPE, BEN 2020 (ano-base 2019), consumo final de gás natural por setor, com tabela de correspondência BEN → 68 setores. Fallback: o GAS vende só à indústria de transformação (S08–S37), ao S43 e às famílias, na proporção das compras de cada um ao S38 (com RAS).
- **G** (gás vendido pelas distribuidoras às térmicas dentro do bloco) = 0 no padrão: as térmicas compram gás direto do S05 ou importado. Implemente como parâmetro, para sensibilidade futura.

### 5.7 Emissões — SEEG 13.0 (obrigatória)

- **URL:** `https://seeg.eco.br/wp-content/uploads/2025/12/Dados-nacionais-13.0.xlsx` (185 MB; User-Agent de navegador; não versionar o bruto).
- **Aba `Dados`:** colunas Emissão/Remoção/Bunker, Gás, Setor de emissão, Categoria emissora, Sub-categoria emissora, Produto ou sistema, Detalhamento, Recorte, Atividade geral, Estado, Bioma e anos 1970–2024. Leia em modo streaming (`openpyxl` read-only leva cerca de 2,5 minutos).
- **Filtro:** Gás = `CO2e (t) GWP-AR5`; ano 2019; Categoria emissora = `Geração de eletricidade (serviço público)`. Separadamente, `Uso de SF6 em equipamentos elétricos` (setor Processos Industriais).
- **Mapeamento:**
  - Carvão mineral e Alcatrão → CAR;
  - Gás natural seco e úmido → GN;
  - Diesel de petróleo, Óleo combustível, Gás de refinaria e Outros energéticos de petróleo → PET;
  - Biodiesel, Biogás, Lenha e Outras biomassas → BIO;
  - Estado "Não Alocado" → RB;
  - SF6 (valor nacional) → TRA e DIS de cada região, repartido entre RS e RB pela participação no VBP do S38.
- **Petróleo no RS:** como o PET-RS é latente, as emissões de diesel e óleo combustível do RS (17.8 mil t: partida e reserva das térmicas) vão para CAR-RS e GN-RS, na proporção do GWh.
- **Referência (mil t CO₂e, 2019; tolerância 0.5):**

| | Carvão | Gás natural | Diesel | Óleo combustível | Outros | Total |
|---|---|---|---|---|---|---|
| RS | 3749.6 | 75.1 | 8.6 | 9.2 | 0 | 3842.5 |
| RB | 9708.2 | 20513.0 | 3102.8 | 855.8 | biodiesel 1.2 | 34181.0 |
| Não alocado | — | — | — | — | gás de refinaria 333.0 · lenha 6.5 · outras biomassas 4.0 · biogás 0.5 | 344.0 |

  SF6 no setor elétrico (nacional): 323.1.

### 5.8 Emprego e salários — IBGE CEMPRE 2019 (obrigatória)

- **URL:** `https://apisidra.ibge.gov.br/values/t/6450/n1/all/n3/43/v/707,662/p/2019/c12762/117297,117298,117299,117300,117301,117302,117303,117304,117305,117306` (testada em 15/10/2026). A variável 707 é pessoal ocupado total; a 662, salários e outras remunerações (R$ mil).
- **Mapeamento:**
  - 35.11-5 geração → subsetores de geração, na proporção do VBP dentro da geração;
  - 35.12-3 transmissão → TRA;
  - 35.13-1 comércio atacadista de energia + 35.14-0 distribuição → DIS;
  - 35.20-4 gás + 35.30-1 vapor → GAS.
- **Valores sigilosos ("X") no RS:** obtenha por diferença. 35.1 − geração − distribuição = transmissão + comércio; 35 − 35.1 = gás + vapor. Reparta cada soma pela proporção nacional.
- **Uso:** só a composição (não o nível), para repartir as ocupações da base NEREUS e as remunerações da MIP entre os subsetores.
- **Referência — Brasil (PO / salários em R$ mil):** geração 39913 / 5171106 · transmissão 16084 / 1657692 · comércio 3146 / 346415 · distribuição 74946 / 5204004 · gás 4575 / 524127 · vapor 756 / 34747.
- **Referência — RS:** divisão 35 = 12509 / 862439 · 35.1 = 12146 / 834364 · geração 2217 / 203958 · distribuição 9087 / 518275 · demais classes sigilosas.

### 5.9 Importações de energia — Comex Stat 2019 (desejável)

- **Fonte:** `comexstat.mdic.gov.br` (API ou consulta), ano 2019, valor FOB.
- **NCM:** 2716.00.00 energia elétrica; 2711.21.00 gás natural no estado gasoso; 2711.11.00 gás natural liquefeito. Só as participações relativas importam.
- **Uso:** repartir a linha de importações do S38: eletricidade → DIS; gás → GAS e GN (por θ). O restante, se houver, vai na proporção do VBP. O carvão importado não é separável do da siderurgia: fica no proporcional (limitação).
- **Fallback:** importações na proporção do VBP, com registro.

### 5.10 Combustível e água das térmicas

- **Energia (mil tep):** composição na proporção de GWh × consumo específico.
  - Preferível: o implícito no BEN 2020 (consumo das centrais de serviço público por fonte ÷ geração por fonte).
  - Fallback (tep/MWh): CAR 0.261 · GN 0.191 · PET 0.246 · BIO 0.344 · NUC 0.261 (eficiências de 33%, 45%, 35%, 25% e 33%).
- **Água (hm³):** composição na proporção do GWh das térmicas (CAR, GN, PET, NUC, BIO); demais subsetores zero. Registre como hipótese.

---

## 6. Etapa 3 — Ajustes no motor

### 6.1 Tipos de subsetor
Aceitar `geracao | transmissao | distribuicao | gas_utilidades`, mantendo compatibilidade com `rede`, que equivale a `distribuicao`.

### 6.2 Bloco S38→S38: nova regra `roteamento_por_componentes`

Para cada região vendedora r, seja F_r = soma das vendas do S38-r ao S38 das duas regiões. Os componentes são:
- **T_r** = VBP do TRA-r: toda a transmissão é vendida dentro do bloco;
- **G_r** = gás vendido às térmicas (padrão 0);
- **E_r** = F_r − T_r − G_r: energia, igual ao VBP total da geração de r. Exigir E_r ≥ 0.

Regras de roteamento:
- Cada componente se reparte entre as regiões compradoras q na proporção F_rq / F_r.
- **Energia** E_r → compradora DIS-q. Entre os vendedores, reparte-se pelos subsetores de geração de r na proporção do VBP.
- **Transmissão** T_r → 50% para DIS-q e 50% para os subsetores de geração de q, na proporção do VBP (excluídos latentes e zerados).
- **Gás** G_r → GN-q.
- As participações (50/50) e o G ficam no YAML.

### 6.3 VBP: novo `modo_vbp: ancora_componentes`
- VBP total da geração de r = E_r, repartido entre fontes pelas participações de MWh × preço (5.1 + 5.4).
- VBP do TRA e do GAS: dados (5.5, 5.6), em R$ milhões.
- VBP do DIS = X_r − E_r − VBP_TRA − VBP_GAS. Tem de ser > 0.

### 6.4 Vendas fora do bloco
- Geração e TRA não vendem fora do bloco.
- DIS e GAS vendem aos demais setores e à demanda final:
  - a participação do gás por comprador vem de 5.6, e o RAS fecha o VBP do GAS;
  - famílias pela mesma tabela do BEN (residencial);
  - exportações e investimento → DIS;
  - discrepância estatística → DIS e GAS, na proporção do VBP.

### 6.5 Subsetores latentes (Solar-RS e Petróleo-RS)
- **Coluna de coeficientes:** a do mesmo subsetor no RB, somando as duas origens para cada setor fornecedor.
- **Origem de cada insumo:** reparta entre RS e RB pela participação de cada origem nas compras desse insumo na coluna original do S38-RS. Para as compras de transmissão, use a mesma participação das origens no bloco S38→S38-RS.
- **Intensidades satélite:** as do subsetor correspondente no RB.
- **Nuclear-RS:** fica zerado, sem latente.

### 6.6 Emissões de CO₂e: três variantes

| Variante | Regra | Total da base |
|---|---|---|
| **E1 (principal)** | Os subsetores de geração recebem os níveis do SEEG 2019 (5.7); o SF6 vai para TRA e DIS. O resíduo R_r = emissões NEREUS do S38-r − emissões identificadas vai para **DIS e GAS**, na proporção do VBP. Se R_r < 0, reduza as identificadas proporcionalmente e reporte | preserva |
| E2 | Todas as emissões do S38-r na proporção da composição do SEEG (combustíveis da geração + SF6). É a D5-A original: as renováveis ficam com zero e as fósseis absorvem o excedente | preserva |
| E3 | Só os níveis do SEEG; o resíduo é descartado. Marque "não preserva o total da base" | não preserva |

- **Referência (E1, mil t):**
  - RS: identificadas = 3842.5 + SF6 19.6 = 3862.1; resíduo ≈ 5838.0 − 3862.1 = 1975.9;
  - RB: identificadas = 34181.0 + 344.0 + SF6 303.5 = 34828.5; resíduo ≈ 84518.3 − 34828.5 = 49689.8.
- Reporte, para cada variante e subsetor: t CO₂e/MWh e t CO₂e por R$ milhão.

### 6.7 Demais contas satélite (totais da base preservados)
- **Energia e água:** pela composição de 5.10.
- **Ocupações:** pela composição do CEMPRE (5.8).

### 6.8 Regras de coluna (insumos)

| Insumo | Regra |
|---|---|
| S04 (carvão e minerais não metálicos) | 100% CAR, com teto de 0.40 × VBP_CAR; o excedente vai aos demais, na proporção do VBP |
| S05 (petróleo e gás natural) | θ_r → GN (teto de 0.60 × VBP_GN); 1 − θ_r → GAS |
| S19 (refino) | PET onde existe (teto de 0.60 × VBP_PET); o restante vai aos demais, na proporção do VBP |
| S03 e S09 (lenha; bagaço) | 100% BIO (teto de 0.40 × VBP_BIO) |
| Bloco S38→S38 | `roteamento_por_componentes` (6.2) |
| Importações | conforme 5.9 |
| IPI, ICMS e outros impostos sobre produtos | na proporção das compras intermediárias totais (domésticas + importadas) de cada subsetor |
| Remunerações | composição do CEMPRE (5.8) |
| Impostos sobre a produção | na proporção do VBP |
| EOB | resíduo: ALERTA se negativo, sem correção automática |
| Demais insumos | na proporção do VBP |

Os tetos servem para evitar EOB negativo. Registre todo teto que for atingido. Se ainda assim algum EOB ficar negativo, **não corrija**: reporte o subsetor, quais insumos pesam e alternativas.

### 6.9 Testes novos (somam-se aos 56)
- **T2** com a especificação real: re-agregação exata.
- **T3** (desagregação neutra) continua passando.
- **T6 — roteamento por componentes:**
  - as vendas da geração de r somam E_r;
  - as vendas do TRA-r somam T_r;
  - a repartição 50/50 é respeitada;
  - os quatro fluxos RS↔RB originais são respeitados.
- **T7 — latentes:** fluxos-base zero, coeficientes somando conforme a origem e multiplicador calculável.
- **T8 — emissões:** E1 e E2 preservam o total de cada região; E3 difere da base exatamente pelo resíduo.

---

## 7. Etapa 4 — Parâmetros reais

- Script `scripts/rodada02_parametros.py`, que gera `parametros/especificacao_v01.yaml` e os CSVs `parametros/*_v01.csv`, sempre com a coluna `fonte`.
- Para o Francisco revisar: `parametros/quadro_parametros_v01.xlsx`, com todos os números usados, a fonte e o cálculo de cada um.
- Os arquivos `TESTE_*` ficam como estão.

---

## 8. Etapa 5 — MIP desagregada v01

- **Principal:** preços P1 + emissões E1 → `resultados/rodada02/MIP_RS_RB_2019_S38_11sub_v01.xlsx` (+ `_longo.csv`), no layout da original e com as abas extras da Rodada 01.
- **Sensibilidades:** P2 + E1, P1 + E2 e P1 + E3, com sufixos `_v01_P2`, `_v01_E2` e `_v01_E3`. Gere `.xlsx` se o tamanho permitir; senão, só o CSV longo.
- **Checagens:** todas as da Rodada 01 + T6–T8, em todas as versões.
- **Ordem de grandeza esperada** (estimativas minhas, para conferência; **não** são alvos):
  - RS: geração ≈ R$ 4.10 bi; TRA ≈ R$ 1.56 bi; DIS + GAS ≈ R$ 15.28 bi;
  - dentro da geração do RS (P1): HID ≈ 60%, EOL ≈ 22%, CAR ≈ 16%, GN ≈ 1%, BIO ≈ 0.7%;
  - RB: geração ≈ R$ 72.4 bi pela âncora, contra ≈ R$ 94 bi por GWh × preço com dados externos. Explique essa diferença no relatório; não force o fechamento.

---

## 9. Etapa 6 — Quadro-diagnóstico e prévia

**a) Obrigatório:** `resultados/rodada02/quadro_subsetores_v01.xlsx`, por região × subsetor, com:
- VBP e % do S38;
- GWh e R$/MWh implícito;
- CO₂e em E1, E2 e E3; t/MWh e t/R$ mi;
- ocupações e remunerações;
- CI/VBP e EOB/VBP;
- os 5 maiores insumos;
- alertas.

Faixas de plausibilidade da emissão direta em E1 (t CO₂e/MWh): CAR 0.9–1.6 · GN 0.35–0.65 · PET 0.65–1.1 · BIO ≤ 0.1 · HID, EOL, SOL e NUC = 0. Sinalize o que ficar fora.

**b) Opcional ("PRÉVIA — não é resultado do artigo"):**
- multiplicadores tipo I de produção e de emissões (por R$ 1 milhão de demanda final) de cada subsetor do RS, incluindo latentes, comparados com o S38 agregado;
- os 9 cenários da Rodada 01 recalculados na v01, com o choque do S38 repartido entre DIS e GAS na proporção das vendas do S38-RS à demanda final. Isso mede o efeito da desagregação sozinha, sem remapear as cestas para tecnologias.

---

## 10. Etapa 7 — Relatório

`respostas/RODADA_02_resposta.md`, com as 12 seções da Rodada 01 e mais quatro:

13. **Fontes de dados:** tabela Fonte | URL | Data de acesso | Arquivo | Usada para | Acessível?
14. **Comparação com os valores de referência** (Seções 5 e 6): esperado × obtido × diferença.
15. **Parâmetros:** resumo dos principais números e onde está o quadro completo.
16. **Variantes:** P1/P2 e E1/E2/E3, com os números-chave por subsetor e o que muda entre elas.

Atualize também `respostas/HISTORICO.md` e o `README.md`. Na última mensagem da conversa, diga onde está o relatório, se tudo foi para a `main` e o que o Francisco precisa fazer.

---

## 11. Checklist final

- [ ] Original intacta (T1)
- [ ] Todos os testes passando, antigos e novos (T6–T8)
- [ ] Valores de referência reproduzidos ou divergências explicadas
- [ ] Nenhum dado inventado; toda hipótese marcada como hipótese; fontes em `FONTES.md`
- [ ] Brutos grandes fora do git
- [ ] MIP v01 e variantes geradas, com checagens
- [ ] Relatório salvo e `HISTORICO.md` atualizado
- [ ] Commit + push; tudo na `main` (ou PR aberto e explicado)
