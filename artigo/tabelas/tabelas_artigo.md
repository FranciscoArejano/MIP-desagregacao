# Tabelas do artigo

Gerado por `scripts/rodada05_artigo.py`; números no padrão brasileiro.

**Quadro 1:** Composição dos vetores de choque dos cenários principais e atribuição do S38 na MIP desagregada

| Cenário | Região | Código | Setor | Participação no choque (%) | Valor do choque (R$ milhões) | Função no cenário | Setor na MIP desagregada |
|---|---|---|---|---:|---:|---|---|
| Energia elétrica agregada | RS | S38 | Energia elétrica, gás natural e outras utilidades | 100,0 | 1.000,0 | Expansão agregada do setor energético | Distribuição e comercialização de energia elétrica (97,5%) e Gás canalizado e outras utilidades (2,5%), pela composição da demanda final |
| Cesta renovável | RS | S38 | Energia elétrica, gás natural e outras utilidades | 30,0 | 300,0 | Componente energético agregado associado à implantação | Geração eólica (S38_EOL) |
| Cesta renovável | RS | S31 | Fabricação de máquinas e equipamentos elétricos | 25,0 | 250,0 | Equipamentos elétricos e componentes de conexão | igual |
| Cesta renovável | RS | S29 | Fabricação de produtos de metal, exceto máquinas e equipamentos | 15,0 | 150,0 | Estruturas metálicas e componentes físicos | igual |
| Cesta renovável | RS | S40 | Construção | 20,0 | 200,0 | Obras civis, fundações e instalação | igual |
| Cesta renovável | RS | S43 | Transporte terrestre | 5,0 | 50,0 | Transporte de equipamentos e insumos | igual |
| Cesta renovável | RS | S56 | Serviços de arquitetura, engenharia, testes/análises técnicas e P&D | 5,0 | 50,0 | Engenharia, projetos, testes e P&D | igual |
| Cesta fóssil | RS | S38 | Energia elétrica, gás natural e outras utilidades | 35,0 | 350,0 | Energia/gás e utilidades associadas | Geração a carvão mineral (93,4%) e Geração a gás natural (6,6%), pelo VBP de 2019 |
| Cesta fóssil | RS | S43 | Transporte terrestre | 25,0 | 250,0 | Logística e transporte associados | igual |
| Cesta fóssil | RS | S19 | Refino de petróleo e coquerias | 40,0 | 400,0 | Processamento e oferta de combustíveis fósseis | igual |

*Nota: choques de R$ 1.000 milhões na demanda final de setores do RS. Na MIP desagregada, o S38 da energia elétrica agregada é repartido entre distribuição e gás canalizado na proporção das vendas de cada subsetor à demanda final do RS; o das cestas renováveis vai para a geração eólica; o das cestas fósseis, para a geração a carvão mineral e a gás natural do RS na proporção do VBP de 2019 de cada uma.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 1:** Impactos econômicos e ambientais dos cenários energéticos

*Painel A — MIP com o S38 desagregado (versão final)*

| Cenário | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Produção bruta por mil t CO₂e (R$ milhões) |
|---|---:|---:|---:|---:|
| Energia elétrica agregada RS | 1.908,1 | 383.253,7 | 200,9 | 5,0 |
| Cesta renovável RS | 1.845,2 | 95.371,0 | 51,7 | 19,3 |
| Cesta fóssil RS | 1.997,1 | 2.026.202,2 | 1.014,6 | 1,0 |
| Diferença de emissões incorporadas (fóssil − renovável) |  | 1.930.831,2 |  |  |
| Redução da intensidade carbônica (%) |  |  | 94,9 |  |

*Painel B — MIP original*

| Cenário | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Produção bruta por mil t CO₂e (R$ milhões) |
|---|---:|---:|---:|---:|
| Energia elétrica agregada RS | 1.925,0 | 428.113,5 | 222,4 | 4,5 |
| Cesta renovável RS | 1.959,4 | 216.407,0 | 110,4 | 9,1 |
| Cesta fóssil RS | 2.120,6 | 356.045,7 | 167,9 | 6,0 |
| Diferença de emissões incorporadas (fóssil − renovável) |  | 139.638,8 |  |  |
| Redução da intensidade carbônica (%) |  |  | 34,2 |  |

*Nota: choques de R$ 1.000 milhões na demanda final do RS. A redução da intensidade carbônica é a da cesta renovável em relação à cesta fóssil, em % da intensidade da cesta fóssil.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 2:** Principais setores responsáveis pelas emissões induzidas pela cesta renovável

*Painel A — MIP com o S38 desagregado (versão final)*

| Ranking | Região | Código | Setor | Produção induzida (R$ milhões) | Emissões induzidas (t CO₂e) | Participação (%) |
|---|---|---|---|---:|---:|---:|
| 1 | RS | S43 | Transporte terrestre | 83,9 | 35.418,9 | 37,1 |
| 2 | RB | S27 | Siderurgia e tubos de aço sem costura | 45,9 | 11.166,8 | 11,7 |
| 3 | RB | S26 | Fabricação de produtos de minerais não metálicos | 15,0 | 6.799,0 | 7,1 |
| 4 | RB | S43 | Transporte terrestre | 14,7 | 6.567,0 | 6,9 |
| 5 | RB | S28 | Metalurgia de metais não ferrosos e fundição | 33,9 | 5.049,7 | 5,3 |
| 6 | RB | S39 | Água, esgoto e gestão de resíduos | 4,6 | 4.524,1 | 4,7 |
| 7 | RB | S03 | Produção florestal, pesca e aquicultura | 1,0 | 3.030,2 | 3,2 |
| 8 | RB | S01 | Agricultura e apoio à agricultura | 3,4 | 2.537,3 | 2,7 |
| 9 | RB | S02 | Pecuária | 0,4 | 2.514,7 | 2,6 |
| 10 | RB | S19 | Refino de petróleo e coquerias | 35,4 | 2.038,0 | 2,1 |
|  |  |  | Demais setores | 1.606,9 | 15.725,3 | 16,5 |
| Total |  |  | Cesta renovável RS | 1.845,2 | 95.371,0 | 100,0 |
|  |  |  | Memória: subsetores do S38 (RS e RB) | 373,1 | 4.997,8 | 5,2 |

*Nota: choque de R$ 1.000 milhões na demanda final do RS (cesta renovável base); o S38 da cesta foi atribuído à geração eólica do RS. A linha de memória soma os 22 subsetores do S38 (11 em cada região) e não entra no total.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 3:** Spillovers ambientais entre o Rio Grande do Sul e o Restante do Brasil

*Painel A — MIP com o S38 desagregado (versão final)*

| Cenário | Região impactada | Produção induzida (R$ milhões) | Emissões induzidas (t CO₂e) | Participação nas emissões (%) |
|---|---|---:|---:|---:|
| Energia elétrica agregada RS | RS | 1.384,2 | 283.644,1 | 74,0 |
| Energia elétrica agregada RS | RB | 524,0 | 99.609,6 | 26,0 |
| Cesta renovável RS | RS | 1.364,6 | 43.833,7 | 46,0 |
| Cesta renovável RS | RB | 480,5 | 51.537,3 | 54,0 |
| Cesta fóssil RS | RS | 1.333,2 | 1.971.586,1 | 97,3 |
| Cesta fóssil RS | RB | 663,8 | 54.616,1 | 2,7 |

*Painel B — MIP original*

| Cenário | Região impactada | Produção induzida (R$ milhões) | Emissões induzidas (t CO₂e) | Participação nas emissões (%) |
|---|---|---:|---:|---:|
| Energia elétrica agregada RS | RS | 1.357,0 | 339.326,4 | 79,3 |
| Energia elétrica agregada RS | RB | 568,0 | 88.787,1 | 20,7 |
| Cesta renovável RS | RS | 1.391,3 | 142.390,0 | 65,8 |
| Cesta renovável RS | RB | 568,0 | 74.016,9 | 34,2 |
| Cesta fóssil RS | RS | 1.373,2 | 277.141,4 | 77,8 |
| Cesta fóssil RS | RB | 747,3 | 78.904,3 | 22,2 |

*Nota: choques de R$ 1.000 milhões na demanda final do RS; RB = Restante do Brasil.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 4:** Sensibilidade dos resultados à composição dos vetores de choque

*Painel A — MIP com o S38 desagregado (versão final)*

| Cenário | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Emissões indiretas (%) | Emissões no RB (%) |
|---|---:|---:|---:|---:|---:|
| Renovável base | 1.845,2 | 95.371,0 | 51,7 | 77,7 | 54,0 |
| Renovável balanceada | 1.857,0 | 149.558,1 | 80,5 | 52,9 | 33,8 |
| Renovável infraestrutura-intensiva | 1.912,2 | 108.198,6 | 56,6 | 80,4 | 57,4 |
| Renovável energia/transporte-intensiva | 1.788,1 | 128.646,3 | 71,9 | 50,7 | 31,2 |
| Fóssil base | 1.997,1 | 2.026.202,2 | 1.014,6 | 4,2 | 2,7 |
| Fóssil balanceada | 1.992,9 | 1.972.315,4 | 989,7 | 4,4 | 2,6 |
| Fóssil energia-intensiva | 1.897,5 | 2.761.423,7 | 1.455,3 | 2,6 | 1,7 |

*Painel B — MIP original*

| Cenário | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Emissões indiretas (%) | Emissões no RB (%) |
|---|---:|---:|---:|---:|---:|
| Renovável base | 1.959,4 | 216.407,0 | 110,4 | 51,5 | 34,2 |
| Renovável balanceada | 1.920,4 | 216.987,2 | 113,0 | 46,1 | 29,1 |
| Renovável infraestrutura-intensiva | 1.969,2 | 169.090,0 | 85,9 | 62,7 | 43,5 |
| Renovável energia/transporte-intensiva (a) | 1.959,5 | 309.794,9 | 158,1 | 39,0 | 23,8 |
| Fóssil base | 2.120,6 | 356.045,7 | 167,9 | 35,3 | 22,2 |
| Fóssil balanceada | 2.110,5 | 381.702,9 | 180,9 | 32,9 | 19,7 |
| Fóssil energia-intensiva | 2.073,9 | 375.427,3 | 181,0 | 35,0 | 21,5 |

*Nota: choques de R$ 1.000 milhões na demanda final do RS; vetores na Tabela A1.*
*(a) Vetor da Tabela A1 (45/15/10/10/15/5).*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 5:** Sensibilidade à tecnologia atribuída ao S38

*Painel A — MIP com o S38 desagregado (versão final)*

| Cenário | Atribuição do S38 | Produção bruta induzida (R$ milhões) | Emissões totais (t CO₂e) | Intensidade carbônica (t CO₂e/R$ milhão) | Emissões indiretas (%) | Emissões no RB (%) |
|---|---|---:|---:|---:|---:|---:|
| Renovável base | Geração eólica 100% (principal) | 1.845,2 | 95.371,0 | 51,7 | 77,7 | 54,0 |
| Renovável base | Geração eólica 50% + solar 50% | 1.839,8 | 95.171,6 | 51,7 | 77,7 | 54,0 |
| Renovável base | Geração eólica 2/3 + transmissão 1/3 | 1.822,9 | 95.139,9 | 52,2 | 77,6 | 53,9 |
| Renovável balanceada | Geração eólica 100% (principal) | 1.857,0 | 149.558,1 | 80,5 | 52,9 | 33,8 |
| Renovável balanceada | Geração eólica 50% + solar 50% | 1.854,0 | 149.447,3 | 80,6 | 52,8 | 33,7 |
| Renovável balanceada | Geração eólica 2/3 + transmissão 1/3 | 1.844,6 | 149.429,7 | 81,0 | 52,8 | 33,7 |
| Renovável infraestrutura-intensiva | Geração eólica 100% (principal) | 1.912,2 | 108.198,6 | 56,6 | 80,4 | 57,4 |
| Renovável infraestrutura-intensiva | Geração eólica 50% + solar 50% | 1.909,6 | 108.098,9 | 56,6 | 80,3 | 57,4 |
| Renovável infraestrutura-intensiva | Geração eólica 2/3 + transmissão 1/3 | 1.901,1 | 108.083,1 | 56,9 | 80,3 | 57,4 |
| Renovável energia/transporte-intensiva | Geração eólica 100% (principal) | 1.788,1 | 128.646,3 | 71,9 | 50,7 | 31,2 |
| Renovável energia/transporte-intensiva | Geração eólica 50% + solar 50% | 1.780,0 | 128.347,2 | 72,1 | 50,6 | 31,0 |
| Renovável energia/transporte-intensiva | Geração eólica 2/3 + transmissão 1/3 | 1.754,7 | 128.299,7 | 73,1 | 50,4 | 30,9 |
| Fóssil base | Carvão mineral e gás natural ∝ VBP (principal) | 1.997,1 | 2.026.202,2 | 1.014,6 | 4,2 | 2,7 |
| Fóssil base | Geração a carvão mineral 100% | 1.976,7 | 2.114.151,8 | 1.069,5 | 3,9 | 2,5 |
| Fóssil base | Geração a gás natural 100% | 2.285,7 | 778.840,7 | 340,7 | 13,0 | 9,6 |
| Fóssil balanceada | Carvão mineral e gás natural ∝ VBP (principal) | 1.992,9 | 1.972.315,4 | 989,7 | 4,4 | 2,6 |
| Fóssil balanceada | Geração a carvão mineral 100% | 1.973,5 | 2.056.076,9 | 1.041,8 | 4,1 | 2,5 |
| Fóssil balanceada | Geração a gás natural 100% | 2.267,8 | 784.352,0 | 345,9 | 13,1 | 9,1 |
| Fóssil energia-intensiva | Carvão mineral e gás natural ∝ VBP (principal) | 1.897,5 | 2.761.423,7 | 1.455,3 | 2,6 | 1,7 |
| Fóssil energia-intensiva | Geração a carvão mineral 100% | 1.868,4 | 2.887.066,0 | 1.545,2 | 2,4 | 1,5 |
| Fóssil energia-intensiva | Geração a gás natural 100% | 2.309,9 | 979.478,6 | 424,0 | 9,9 | 7,6 |

*Nota: choques de R$ 1.000 milhões na demanda final do RS. A atribuição muda só a parcela do S38 de cada cesta; os demais setores do vetor não mudam. Solar: subsetor sem produção no RS em 2019 (latente), com os coeficientes técnicos do RB e a TUST do RS.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 6:** Emissões por tecnologia de geração do RS

*Painel A — MIP com o S38 desagregado (versão final)*

| Tecnologia | Preço médio (R$/MWh) | Produção induzida por TWh (R$ milhões) | Emissões diretas por TWh (t CO₂e) | Emissões indiretas por TWh (t CO₂e) | Emissões totais por TWh (t CO₂e) | g CO₂e/kWh | Emissões no RB (%) | Emissões por R$ 1 bilhão (t CO₂e) | Emissões evitadas por TWh em relação ao carvão (t CO₂e) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Hidrelétrica | 175,3 | 272,3 | 0,0 | 4.627,1 | 4.627,1 | 4,6 | 54,8 | 26.391,5 | 1.437.533,4 |
| Eólica | 182,4 | 281,6 | 0,0 | 4.787,8 | 4.787,8 | 4,8 | 54,7 | 26.246,9 | 1.437.372,7 |
| Solar fotovoltaica | 200,8 | 302,8 | 0,0 | 5.003,3 | 5.003,3 | 5,0 | 53,0 | 24.917,7 | 1.437.157,3 |
| Biomassa | 217,1 | 340,3 | 49,5 | 8.759,6 | 8.809,0 | 8,8 | 68,9 | 40.583,5 | 1.433.351,5 |
| Gás natural | 280,5 | 672,4 | 436.436,9 | 22.581,7 | 459.018,6 | 459,0 | 4,7 | 1.636.355,7 | 983.141,9 |
| Carvão mineral | 264,5 | 400,5 | 1.434.683,4 | 7.477,1 | 1.442.160,5 | 1.442,2 | 0,3 | 5.451.530,5 | 0,0 |
| Distribuição (eletricidade da rede, mix de 2019) |  |  |  |  |  |  |  | 387.680,1 |  |

*Nota: Choque de 1 TWh (ao preço médio de 2019) e de R$ 1 bilhão na demanda final de cada subsetor de geração do RS. Emissões da operação (produção de energia elétrica); não incluem bens de capital (implantação das usinas). Solar: subsetor sem produção no RS em 2019 (latente), com os coeficientes técnicos do RB e a TUST do RS.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela 7:** Efeito da desagregação: MIP original, S38 desagregado sem e com atribuição de tecnologia

*Parte 1 — Emissões totais*

| Cenário | Emissões A0 (t CO₂e) | Emissões A1 (t CO₂e) | Emissões A2 (t CO₂e) | Variação A1/A0 (%) | Variação A2/A0 (%) |
|---|---:|---:|---:|---:|---:|
| Energia elétrica agregada | 428.113,5 | 383.253,7 | 383.253,7 | −10,5 | −10,5 |
| Renovável base | 216.407,0 | 202.473,0 | 95.371,0 | −6,4 | −55,9 |
| Renovável balanceada | 216.987,2 | 209.059,2 | 149.558,1 | −3,7 | −31,1 |
| Renovável infraestrutura-intensiva | 169.090,0 | 161.749,6 | 108.198,6 | −4,3 | −36,0 |
| Renovável energia/transporte-intensiva | 309.794,9 | 289.299,3 | 128.646,3 | −6,6 | −58,5 |
| Fóssil base | 356.045,7 | 340.254,9 | 2.026.202,2 | −4,4 | 469,1 |
| Fóssil balanceada | 381.702,9 | 366.651,4 | 1.972.315,4 | −3,9 | 416,7 |
| Fóssil energia-intensiva | 375.427,3 | 352.927,6 | 2.761.423,7 | −6,0 | 635,5 |

*Parte 2 — Intensidade carbônica, emissões indiretas e emissões no RB*

| Cenário | Intensidade A0 (t CO₂e/R$ milhão) | Intensidade A2 (t CO₂e/R$ milhão) | Emissões indiretas A0 (%) | Emissões indiretas A2 (%) | Emissões no RB A0 (%) | Emissões no RB A2 (%) |
|---|---:|---:|---:|---:|---:|---:|
| Energia elétrica agregada | 222,4 | 200,9 | 34,9 | 66,0 | 20,7 | 26,0 |
| Renovável base | 110,4 | 51,7 | 51,5 | 77,7 | 34,2 | 54,0 |
| Renovável balanceada | 113,0 | 80,5 | 46,1 | 52,9 | 29,1 | 33,8 |
| Renovável infraestrutura-intensiva | 85,9 | 56,6 | 62,7 | 80,4 | 43,5 | 57,4 |
| Renovável energia/transporte-intensiva | 158,1 | 71,9 | 39,0 | 50,7 | 23,8 | 31,2 |
| Fóssil base | 167,9 | 1.014,6 | 35,3 | 4,2 | 22,2 | 2,7 |
| Fóssil balanceada | 180,9 | 989,7 | 32,9 | 4,4 | 19,7 | 2,6 |
| Fóssil energia-intensiva | 181,0 | 1.455,3 | 35,0 | 2,6 | 21,5 | 1,7 |

*Nota: A0 = MIP original; A1 = MIP desagregada, com o S38 do vetor repartido entre distribuição e gás canalizado pela composição da demanda final; A2 = MIP desagregada, com o S38 atribuído a tecnologias (Quadro 1). Na energia elétrica agregada, A1 e A2 coincidem.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela A1:** Vetores de choque das cestas (participação de cada setor no choque, %)

| Código | Setor | Renovável base | Renovável balanceada | Renovável infraestrutura-intensiva | Renovável energia/transporte-intensiva | Fóssil base | Fóssil balanceada | Fóssil energia-intensiva |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| S38 | Energia elétrica, gás natural e outras utilidades | 30,0 | 16,7 | 15,0 | 45,0 | 35,0 | 33,3 | 50,0 |
| S31 | Fabricação de máquinas e equipamentos elétricos | 25,0 | 16,7 | 25,0 | 15,0 | 0,0 | 0,0 | 0,0 |
| S29 | Fabricação de produtos de metal, exceto máquinas e equipamentos | 15,0 | 16,7 | 25,0 | 10,0 | 0,0 | 0,0 | 0,0 |
| S40 | Construção | 20,0 | 16,7 | 25,0 | 10,0 | 0,0 | 0,0 | 0,0 |
| S43 | Transporte terrestre | 5,0 | 16,7 | 5,0 | 15,0 | 25,0 | 33,3 | 20,0 |
| S56 | Serviços de arquitetura, engenharia, testes/análises técnicas e P&D | 5,0 | 16,7 | 5,0 | 5,0 | 0,0 | 0,0 | 0,0 |
| S19 | Refino de petróleo e coquerias | 0,0 | 0,0 | 0,0 | 0,0 | 40,0 | 33,3 | 30,0 |
|  | Total | 100,0 | 100,0 | 100,0 | 100,0 | 100,0 | 100,0 | 100,0 |

*Nota: choques de R$ 1.000 milhões na demanda final do RS. Renovável energia/transporte-intensiva: vetor 45/15/10/10/15/5. No A2 (MIP desagregada), a parcela do S38 das cestas renováveis vai para a geração eólica do RS, e a das cestas fósseis para a geração a carvão mineral (93,4%) e a gás natural (6,6%) do RS, na proporção do VBP de 2019.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela A2:** Principais setores responsáveis pelas emissões induzidas pela cesta renovável na MIP original

*Painel B — MIP original*

| Ranking | Região | Código | Setor | Produção induzida (R$ milhões) | Emissões induzidas (t CO₂e) | Participação (%) |
|---|---|---|---|---:|---:|---:|
| 1 | RS | S38 | Energia elétrica, gás natural e outras utilidades | 357,1 | 99.554,6 | 46,0 |
| 2 | RS | S43 | Transporte terrestre | 84,1 | 35.489,9 | 16,4 |
| 3 | RB | S38 | Energia elétrica, gás natural e outras utilidades | 92,0 | 23.960,2 | 11,1 |
| 4 | RB | S27 | Siderurgia e tubos de aço sem costura | 46,8 | 11.392,4 | 5,3 |
| 5 | RB | S43 | Transporte terrestre | 16,4 | 7.311,5 | 3,4 |
| 6 | RB | S26 | Fabricação de produtos de minerais não metálicos | 15,3 | 6.949,7 | 3,2 |
| 7 | RB | S28 | Metalurgia de metais não ferrosos e fundição | 34,1 | 5.082,2 | 2,3 |
| 8 | RB | S39 | Água, esgoto e gestão de resíduos | 4,7 | 4.646,4 | 2,1 |
| 9 | RB | S03 | Produção florestal, pesca e aquicultura | 1,0 | 3.085,0 | 1,4 |
| 10 | RB | S01 | Agricultura e apoio à agricultura | 3,5 | 2.649,5 | 1,2 |
|  |  |  | Demais setores | 1.304,3 | 16.285,6 | 7,5 |
| Total |  |  | Cesta renovável RS | 1.959,4 | 216.407,0 | 100,0 |
|  |  |  | Memória: S38 (RS e RB) | 449,1 | 123.514,8 | 57,1 |

*Nota: choque de R$ 1.000 milhões na demanda final do RS (cesta renovável base). A linha de memória soma o S38 das duas regiões e não entra no total.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP).*

**Tabela A3:** Os 11 subsetores do S38 no RS e no RB: produção, preços, emissões e multiplicadores

| Região | Subsetor | VBP (R$ milhões) | GWh | R$/MWh | t CO₂e/MWh (E1) | EOB/VBP | Multiplicador de produção | Multiplicador de emissões (t CO₂e/R$ milhão) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| RS | Geração hidrelétrica | 2.549,7 | 14.542,6 | 175,3 | 0,000 | 0,515 | 1,553 | 26,4 |
| RS | Geração eólica | 960,8 | 5.266,9 | 182,4 | 0,000 | 0,523 | 1,544 | 26,2 |
| RS | Geração solar fotovoltaica (latente) | 0,0 |  |  |  |  | 1,508 | 24,9 |
| RS | Geração a biomassa | 14,8 | 68,2 | 217,1 | 0,000 | 0,529 | 1,568 | 40,6 |
| RS | Geração a carvão mineral | 694,5 | 2.625,2 | 264,5 | 1,435 | 0,562 | 1,514 | 5.451,5 |
| RS | Geração a gás natural | 49,0 | 174,6 | 280,5 | 0,436 | 0,100 | 2,397 | 1.636,4 |
| RS | Geração a derivados de petróleo (latente) | 0,0 |  |  |  |  | 2,801 | 1.187,6 |
| RS | Geração nuclear (sem produção) | 0,0 |  |  |  |  |  |  |
| RS | Transmissão de energia elétrica | 1.390,9 |  |  |  | 0,695 | 1,321 | 23,9 |
| RS | Distribuição e comercialização de energia elétrica | 14.384,3 |  |  |  | 0,241 | 1,897 | 387,7 |
| RS | Gás canalizado e outras utilidades | 898,7 |  |  |  | 0,100 | 2,344 | 213,9 |
| RS | S38 agregado (MIP original) | 20.942,7 |  |  |  | 0,322 | 1,925 | 428,1 |
| RB | Geração hidrelétrica | 46.661,0 | 363.907,4 | 128,2 | 0,000 | 0,471 | 1,510 | 26,1 |
| RB | Geração eólica | 6.761,9 | 50.687,1 | 133,4 | 0,000 | 0,487 | 1,492 | 25,8 |
| RB | Geração solar fotovoltaica | 999,5 | 4.978,0 | 200,8 | 0,000 | 0,552 | 1,419 | 24,7 |
| RB | Geração a biomassa | 281,3 | 1.771,8 | 158,7 | 0,007 | 0,488 | 1,517 | 81,6 |
| RB | Geração a carvão mineral | 2.166,4 | 11.197,8 | 193,5 | 0,867 | 0,433 | 1,631 | 4.520,9 |
| RB | Geração a gás natural | 10.981,9 | 47.422,4 | 231,6 | 0,433 | 0,100 | 1,851 | 1.916,1 |
| RB | Geração a derivados de petróleo | 4.066,6 | 5.174,0 | 786,0 | 0,829 | 0,100 | 2,760 | 1.184,2 |
| RB | Geração nuclear | 3.075,1 | 16.129,0 | 190,7 | 0,000 | 0,532 | 1,442 | 25,0 |
| RB | Transmissão de energia elétrica | 21.544,7 |  |  |  | 0,663 | 1,305 | 24,4 |
| RB | Distribuição e comercialização de energia elétrica | 208.427,9 |  |  |  | 0,269 | 1,922 | 422,6 |
| RB | Gás canalizado e outras utilidades | 19.421,0 |  |  |  | 0,171 | 1,775 | 269,8 |
| RB | S38 agregado (MIP original) | 324.387,3 |  |  |  | 0,320 | 1,909 | 406,3 |

*Nota: GWh de 2019 (BEN 2020 e ONS); R$/MWh = VBP ÷ GWh; t CO₂e/MWh pela variante E1. Multiplicador de produção = soma da coluna da inversa de Leontief; multiplicador de emissões = emissões totais (diretas e indiretas) por R$ milhão de demanda final do subsetor. Subsetores latentes: coeficientes técnicos do mesmo subsetor no RB, com a TUST por MWh do RS.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela A4:** Fontes de dados da desagregação

| Dado | Fonte | Ano ou versão | Uso na desagregação |
|---|---|---|---|
| Matriz inter-regional de insumo-produto RS-RB e conta-satélite de emissões (CO₂e) | NEREUS/USP | 2019 | Base da desagregação; todas as restrições de agregação |
| Geração de energia elétrica por fonte (serviço público), Brasil | EPE, Balanço Energético Nacional 2020, Tabela 5.4 | 2019 (BEN 2020) | GWh por fonte do Brasil; RB = Brasil − RS |
| Geração por usina | ONS, dados abertos (geração por usina) | 2019 | GWh por fonte do RS; MWh no SIN (pesos da TUST da geração) |
| Encargos de uso do sistema de transmissão | ONS, Síntese da Apuração Mensal dos Serviços e Encargos (SEAMSE) | dez/2018, jun/2019 e dez/2019 | VBP da transmissão (ano civil de 2019) |
| Receita anual permitida da transmissão | ANEEL, REH nº 2.408/2018 e decisão de 25/06/2019 (REH nº 2.565/2019; total por fonte secundária) | ciclos 2018-2019 e 2019-2020 | Variante _rap_media |
| Rateio dos encargos de uso entre geração e consumo | ANEEL, Resolução Normativa nº 559/2013 | 2013 | Parcela da transmissão paga pela geração (50%) |
| Preços de energia por fonte | ANEEL, resultado dos leilões de geração | leilões até 2019, corrigidos pelo IPCA (IBGE, SIDRA, Tabela 1737) | Participação de cada fonte no VBP da geração (preços P1) |
| Remunerações e pessoal ocupado por atividade | IBGE, Cadastro Central de Empresas (CEMPRE), SIDRA, Tabela 6450 | 2019 | Repartição de remunerações e ocupações entre geração, transmissão, distribuição e gás |
| Demonstrações contábeis da Sulgás | Sulgás (publicadas pela CAGE/Sefaz-RS) | 2019 | VBP do gás canalizado no RS; preço do gás usado no RB; vendas por segmento |
| Demanda de gás natural por distribuidora | MME, Boletim Mensal de Acompanhamento da Indústria de Gás Natural nº 154 (fonte: Abegás) | dez/2019 (média de 2019) | Volume não térmico do RB |
| Demonstrações financeiras de distribuidoras de gás | CVM, DFP de Comgás, CEG e Gasmig | 2019 | Variante _gas4dist |
| Importações de energia elétrica e gás natural | MDIC, Comex Stat | 2019 | Importações do S38 (energia) |
| Emissões de gases de efeito estufa | SEEG 13.0 (Observatório do Clima), GWP-AR5 | 2019 | Níveis por fonte de geração (E1), SF₆, variantes E2 a E4, diagnóstico (Tabela A7) |

*Nota: URLs, datas de acesso, páginas e SHA-256 dos arquivos no registro de fontes do repositório (dados/externos/FONTES.md).*
*Fonte: Elaboração própria.*

**Tabela A5:** Parâmetros e hipóteses da desagregação

| Parâmetro | Valor | Fonte ou justificativa | Sensibilidade testada |
|---|---|---|---|
| VBP da transmissão (Brasil) | R$ 22.935,6 milhões | Encargos de uso faturados pelo ONS no ano civil de 2019 (SEAMSE), sem PIS/Pasep e Cofins; repartido entre RS e RB pela participação no VBP do S38 | RAP 2019: R$ 24.883,4 milhões (_rap_media) |
| Parcela da transmissão paga pelo consumo, via distribuição (α); a geração paga 1 − α | 0,5 | Rateio inicial dos encargos de uso: 50% geração e 50% consumo (ANEEL, REN nº 559/2013) | — |
| TUST da geração entre as fontes | ∝ MWh gerado no SIN | Regra do encargo por uso da rede; sistemas isolados não pagam | — |
| TUST das colunas latentes (solar e derivados de petróleo no RS) | 32,41 R$/MWh | HIPÓTESE: a mesma TUST por MWh das fontes do RS no SIN, ao preço do espelho do RB | TUST por real do espelho (registro no relatório) |
| VBP do gás canalizado no RS | R$ 898,7 milhões | Receita líquida da Sulgás em 2019 | — |
| VBP do gás canalizado no RB | R$ 19.421,0 milhões | HIPÓTESE: preço da Sulgás × volume não térmico do RB (MME/Abegás) | Preço médio de 4 distribuidoras: R$ 26.990,1 milhões (_gas4dist) |
| Participação máxima do gás canalizado na compra de S38 de cada comprador | 0,90 | HIPÓTESE (teto) | — |
| Piso do VBP das térmicas (κ) | 0,70 | HIPÓTESE: combustível ≤ κ × VBP | κ = 0,60 (_k060) |
| Excedente operacional bruto mínimo (η) | 0,10 | HIPÓTESE: EOB ≥ η × VBP em cada subsetor (ajuste RAS dos insumos não energéticos) | η = 0,05 (_eta005) |
| Remunerações e ocupações entre as fontes de geração | ∝ VBP − combustível | HIPÓTESE: o combustível é repasse e não exige mão de obra proporcional | — |
| Preços da energia por fonte (P1) | leilões | HIPÓTESE: preços relativos dos leilões ajustados à produção da MIP | Preços iguais (P2) |
| Emissões das usinas (E1) | níveis do SEEG + resíduo | Níveis por fonte do SEEG; o resíduo (base − níveis) vai para distribuição e gás canalizado ∝ VBP | E2 (proporcional ao SEEG), E3 (só níveis), E4 (realocação) |
| Subsetores sem produção no RS (solar e derivados de petróleo) | espelho do RB | HIPÓTESE: coeficientes técnicos do mesmo subsetor no RB | — |

*Fonte: Elaboração própria.*

**Tabela A6:** Robustez: resultados da versão principal e das variantes da desagregação

*Painel A — MIP com o S38 desagregado: versão principal e 8 variantes*

| Cenário | Versão | Emissões (t CO₂e) | Desvio das emissões (%) | Intensidade (t CO₂e/R$ milhão) | Desvio da intensidade (%) |
|---|---|---:|---:|---:|---:|
| Energia elétrica agregada | Principal (versão final) | 383.253,7 | 0,0 | 200,9 | 0,0 |
| Energia elétrica agregada | P2 — preços iguais entre as fontes | 383.253,8 | 0,0 | 200,9 | 0,0 |
| Energia elétrica agregada | E2 — emissões na proporção do SEEG | 437.947,0 | 14,3 | 229,5 | 14,3 |
| Energia elétrica agregada | E3 — só os níveis do SEEG | 253.058,0 | −34,0 | 132,6 | −34,0 |
| Energia elétrica agregada | E4 — refino, petróleo e gás e carvão fora do S38 | 263.584,2 | −31,2 | 138,1 | −31,2 |
| Energia elétrica agregada | gas4dist — gás do RB pelo preço de 4 distribuidoras | 383.234,7 | 0,0 | 200,9 | 0,0 |
| Energia elétrica agregada | rap_media — transmissão pela RAP 2019 | 383.250,4 | 0,0 | 200,8 | 0,0 |
| Energia elétrica agregada | k060 — piso do combustível κ = 0,60 | 383.304,7 | 0,0 | 200,8 | 0,0 |
| Energia elétrica agregada | eta005 — EOB mínimo η = 0,05 | 383.232,9 | 0,0 | 200,9 | 0,0 |
| Renovável base | Principal (versão final) | 95.371,0 | 0,0 | 51,7 | 0,0 |
| Renovável base | P2 — preços iguais entre as fontes | 95.341,9 | 0,0 | 51,7 | 0,1 |
| Renovável base | E2 — emissões na proporção do SEEG | 95.175,6 | −0,2 | 51,6 | −0,2 |
| Renovável base | E3 — só os níveis do SEEG | 92.569,0 | −2,9 | 50,2 | −2,9 |
| Renovável base | E4 — refino, petróleo e gás e carvão fora do S38 | 97.102,7 | 1,8 | 52,6 | 1,8 |
| Renovável base | gas4dist — gás do RB pelo preço de 4 distribuidoras | 95.279,8 | −0,1 | 51,6 | −0,1 |
| Renovável base | rap_media — transmissão pela RAP 2019 | 95.500,7 | 0,1 | 51,5 | −0,3 |
| Renovável base | k060 — piso do combustível κ = 0,60 | 95.327,7 | 0,0 | 51,7 | 0,0 |
| Renovável base | eta005 — EOB mínimo η = 0,05 | 95.202,5 | −0,2 | 51,7 | 0,0 |
| Fóssil base | Principal (versão final) | 2.026.202,2 | 0,0 | 1.014,6 | 0,0 |
| Fóssil base | P2 — preços iguais entre as fontes | 2.755.249,2 | 36,0 | 1.362,0 | 34,2 |
| Fóssil base | E2 — emissões na proporção do SEEG | 2.951.716,5 | 45,7 | 1.478,0 | 45,7 |
| Fóssil base | E3 — só os níveis do SEEG | 2.024.744,2 | −0,1 | 1.013,9 | −0,1 |
| Fóssil base | E4 — refino, petróleo e gás e carvão fora do S38 | 2.070.526,6 | 2,2 | 1.036,8 | 2,2 |
| Fóssil base | gas4dist — gás do RB pelo preço de 4 distribuidoras | 2.026.188,1 | 0,0 | 1.014,6 | 0,0 |
| Fóssil base | rap_media — transmissão pela RAP 2019 | 2.077.383,8 | 2,5 | 1.036,9 | 2,2 |
| Fóssil base | k060 — piso do combustível κ = 0,60 | 2.024.409,0 | −0,1 | 1.014,8 | 0,0 |
| Fóssil base | eta005 — EOB mínimo η = 0,05 | 2.026.084,0 | 0,0 | 1.015,4 | 0,1 |
| 1 TWh — Hidrelétrica | Principal (versão final) | 4.627,1 | 0,0 | 17,0 | 0,0 |
| 1 TWh — Hidrelétrica | P2 — preços iguais entre as fontes | 4.903,6 | 6,0 | 17,0 | 0,1 |
| 1 TWh — Hidrelétrica | E2 — emissões na proporção do SEEG | 4.663,6 | 0,8 | 17,1 | 0,8 |
| 1 TWh — Hidrelétrica | E3 — só os níveis do SEEG | 4.497,6 | −2,8 | 16,5 | −2,8 |
| 1 TWh — Hidrelétrica | E4 — refino, petróleo e gás e carvão fora do S38 | 4.820,9 | 4,2 | 17,7 | 4,2 |
| 1 TWh — Hidrelétrica | gas4dist — gás do RB pelo preço de 4 distribuidoras | 4.624,9 | 0,0 | 17,0 | 0,0 |
| 1 TWh — Hidrelétrica | rap_media — transmissão pela RAP 2019 | 4.574,4 | −1,1 | 17,0 | 0,0 |
| 1 TWh — Hidrelétrica | k060 — piso do combustível κ = 0,60 | 4.592,3 | −0,8 | 16,9 | −0,5 |
| 1 TWh — Hidrelétrica | eta005 — EOB mínimo η = 0,05 | 4.528,0 | −2,1 | 16,7 | −1,6 |
| 1 TWh — Eólica | Principal (versão final) | 4.787,8 | 0,0 | 17,0 | 0,0 |
| 1 TWh — Eólica | P2 — preços iguais entre as fontes | 4.903,6 | 2,4 | 17,0 | 0,0 |
| 1 TWh — Eólica | E2 — emissões na proporção do SEEG | 4.824,1 | 0,8 | 17,1 | 0,8 |
| 1 TWh — Eólica | E3 — só os níveis do SEEG | 4.653,8 | −2,8 | 16,5 | −2,8 |
| 1 TWh — Eólica | E4 — refino, petróleo e gás e carvão fora do S38 | 4.988,7 | 4,2 | 17,7 | 4,2 |
| 1 TWh — Eólica | gas4dist — gás do RB pelo preço de 4 distribuidoras | 4.785,5 | 0,0 | 17,0 | 0,0 |
| 1 TWh — Eólica | rap_media — transmissão pela RAP 2019 | 4.730,4 | −1,2 | 17,0 | 0,0 |
| 1 TWh — Eólica | k060 — piso do combustível κ = 0,60 | 4.752,2 | −0,7 | 16,9 | −0,4 |
| 1 TWh — Eólica | eta005 — EOB mínimo η = 0,05 | 4.683,4 | −2,2 | 16,7 | −1,7 |
| 1 TWh — Solar fotovoltaica | Principal (versão final) | 5.003,3 | 0,0 | 16,5 | 0,0 |
| 1 TWh — Solar fotovoltaica | P2 — preços iguais entre as fontes | 3.552,1 | −29,0 | 16,5 | −0,1 |
| 1 TWh — Solar fotovoltaica | E2 — emissões na proporção do SEEG | 5.040,3 | 0,7 | 16,6 | 0,7 |
| 1 TWh — Solar fotovoltaica | E3 — só os níveis do SEEG | 4.857,8 | −2,9 | 16,0 | −2,9 |
| 1 TWh — Solar fotovoltaica | E4 — refino, petróleo e gás e carvão fora do S38 | 5.063,0 | 1,2 | 16,7 | 1,2 |
| 1 TWh — Solar fotovoltaica | gas4dist — gás do RB pelo preço de 4 distribuidoras | 5.000,6 | −0,1 | 16,5 | 0,0 |
| 1 TWh — Solar fotovoltaica | rap_media — transmissão pela RAP 2019 | 4.939,4 | −1,3 | 16,5 | 0,2 |
| 1 TWh — Solar fotovoltaica | k060 — piso do combustível κ = 0,60 | 4.641,8 | −7,2 | 16,0 | −2,9 |
| 1 TWh — Solar fotovoltaica | eta005 — EOB mínimo η = 0,05 | 4.863,2 | −2,8 | 16,2 | −2,2 |
| 1 TWh — Biomassa | Principal (versão final) | 8.809,0 | 0,0 | 25,9 | 0,0 |
| 1 TWh — Biomassa | P2 — preços iguais entre as fontes | 8.139,5 | −7,6 | 27,0 | 4,4 |
| 1 TWh — Biomassa | E2 — emissões na proporção do SEEG | 8.868,7 | 0,7 | 26,1 | 0,7 |
| 1 TWh — Biomassa | E3 — só os níveis do SEEG | 8.627,4 | −2,1 | 25,4 | −2,1 |
| 1 TWh — Biomassa | E4 — refino, petróleo e gás e carvão fora do S38 | 9.059,7 | 2,8 | 26,6 | 2,8 |
| 1 TWh — Biomassa | gas4dist — gás do RB pelo preço de 4 distribuidoras | 8.806,0 | 0,0 | 25,9 | 0,0 |
| 1 TWh — Biomassa | rap_media — transmissão pela RAP 2019 | 8.729,6 | −0,9 | 26,0 | 0,4 |
| 1 TWh — Biomassa | k060 — piso do combustível κ = 0,60 | 8.770,4 | −0,4 | 25,8 | −0,2 |
| 1 TWh — Biomassa | eta005 — EOB mínimo η = 0,05 | 8.688,0 | −1,4 | 25,7 | −0,9 |
| 1 TWh — Gás natural | Principal (versão final) | 459.018,6 | 0,0 | 682,7 | 0,0 |
| 1 TWh — Gás natural | P2 — preços iguais entre as fontes | 459.018,6 | 0,0 | 682,7 | 0,0 |
| 1 TWh — Gás natural | E2 — emissões na proporção do SEEG | 682.288,9 | 48,6 | 1.014,8 | 48,6 |
| 1 TWh — Gás natural | E3 — só os níveis do SEEG | 458.629,1 | −0,1 | 682,1 | −0,1 |
| 1 TWh — Gás natural | E4 — refino, petróleo e gás e carvão fora do S38 | 478.208,6 | 4,2 | 711,2 | 4,2 |
| 1 TWh — Gás natural | gas4dist — gás do RB pelo preço de 4 distribuidoras | 459.009,5 | 0,0 | 682,7 | 0,0 |
| 1 TWh — Gás natural | rap_media — transmissão pela RAP 2019 | 458.891,9 | 0,0 | 681,6 | −0,2 |
| 1 TWh — Gás natural | k060 — piso do combustível κ = 0,60 | 461.800,5 | 0,6 | 608,7 | −10,8 |
| 1 TWh — Gás natural | eta005 — EOB mínimo η = 0,05 | 459.929,3 | 0,2 | 671,1 | −1,7 |
| 1 TWh — Carvão mineral | Principal (versão final) | 1.442.160,5 | 0,0 | 3.600,5 | 0,0 |
| 1 TWh — Carvão mineral | P2 — preços iguais entre as fontes | 1.440.413,6 | −0,1 | 4.820,6 | 33,9 |
| 1 TWh — Carvão mineral | E2 — emissões na proporção do SEEG | 2.176.164,8 | 50,9 | 5.433,0 | 50,9 |
| 1 TWh — Carvão mineral | E3 — só os níveis do SEEG | 1.441.929,4 | 0,0 | 3.599,9 | 0,0 |
| 1 TWh — Carvão mineral | E4 — refino, petróleo e gás e carvão fora do S38 | 1.442.833,9 | 0,0 | 3.602,2 | 0,0 |
| 1 TWh — Carvão mineral | gas4dist — gás do RB pelo preço de 4 distribuidoras | 1.442.155,1 | 0,0 | 3.600,7 | 0,0 |
| 1 TWh — Carvão mineral | rap_media — transmissão pela RAP 2019 | 1.442.050,4 | 0,0 | 3.657,7 | 1,6 |
| 1 TWh — Carvão mineral | k060 — piso do combustível κ = 0,60 | 1.442.116,8 | 0,0 | 3.610,4 | 0,3 |
| 1 TWh — Carvão mineral | eta005 — EOB mínimo η = 0,05 | 1.442.004,2 | 0,0 | 3.620,1 | 0,5 |

*Painel B — MIP original sem e com a realocação de emissões da E4 (A0_E4)*

| Cenário | Versão | Emissões (t CO₂e) | Desvio das emissões (%) | Intensidade (t CO₂e/R$ milhão) | Desvio da intensidade (%) |
|---|---|---:|---:|---:|---:|
| Energia elétrica agregada | MIP original | 428.113,5 | 0,0 | 222,4 | 0,0 |
| Energia elétrica agregada | MIP original com a E4 | 294.095,6 | −31,3 | 152,8 | −31,3 |
| Renovável base | MIP original | 216.407,0 | 0,0 | 110,4 | 0,0 |
| Renovável base | MIP original com a E4 | 177.469,2 | −18,0 | 90,6 | −18,0 |
| Fóssil base | MIP original | 356.045,7 | 0,0 | 167,9 | 0,0 |
| Fóssil base | MIP original com a E4 | 351.029,4 | −1,4 | 165,5 | −1,4 |

*Nota: desvio em relação à versão principal (Painel A) ou à MIP original (Painel B). Choques de R$ 1.000 milhões (cenários) e de 1 TWh ao preço médio de cada versão (tecnologias). Na E4, emissões do refino, da exploração de petróleo e gás e da mineração de carvão do SEEG saem do S38 e vão para os setores S19, S05 e S04 da mesma região.*
*Fonte: Elaboração própria a partir da matriz inter-regional de insumo-produto RS-RB (NEREUS/USP), com o setor S38 desagregado.*

**Tabela A7:** Emissões do S38 na base NEREUS e componentes do SEEG 13.0 (2019, GWP-AR5)

| Componente (SEEG: atividade › categoria › subcategoria) | RS (mil t CO₂e) | RB (estados) (mil t CO₂e) | Não alocado (mil t CO₂e) |
|---|---:|---:|---:|
| Geração de eletricidade › Geração de eletricidade (serviço público) | 3.842,6 | 34.181,1 | 344,0 |
| Geração de eletricidade › demais categorias (autoprodução: indústria, comércio, público, agropecuária) | 96,5 | 2.094,4 | 4.833,4 |
| Geração de eletricidade › Produção de combustíveis › Refino de petróleo | 76,1 | 759,7 | 496,3 |
| Geração de eletricidade › Produção de combustíveis › Exploração de petróleo e gás natural | 0,0 | 5.778,2 | 0,0 |
| Geração de eletricidade › Produção de combustíveis › Produção de álcool | 0,0 | 0,0 | 412,4 |
| Produção de combustíveis › Refino de petróleo | 1.736,0 | 17.329,1 | 7.053,5 |
| Produção de combustíveis › Exploração de petróleo e gás natural | 0,0 | 17.721,0 | 53,4 |
| Produção de combustíveis › Produção de carvão mineral e outros | 88,1 | 1.155,4 | 355,6 |
| Produção de combustíveis › demais (carvão vegetal, álcool, transporte de petróleo e gás) | 0,0 | 0,0 | 5.151,2 |
| Soma das duas atividades | 5.839,2 | 79.018,9 | 18.700,0 |
| S38 na base NEREUS | 5.838,0 | 84.518,3 |  |

*Nota: emissões de 'Emissão' e 'Emissão NCI' (não há NCI nessas duas atividades). RB = estados exceto o RS; 'Não alocado' = sem estado. No RS, a soma das duas atividades é compatível com o S38 da base NEREUS, o que é um indício fraco de que a conta-satélite inclua no S38 o refino e a produção de carvão mineral: o RB não fecha pelo mesmo critério, coincidências são esperadas com o número de combinações testadas (Apêndice B) e há uma combinação concorrente que atribui o refino ao S19. Não há documentação da conta-satélite que permita confirmar.*
*Fonte: Elaboração própria a partir da base NEREUS/USP e do SEEG 13.0 (Observatório do Clima).*

**Tabela A8:** Testes de consistência da desagregação

| Teste | Resultado | Valor | Unidade |
|---|---|---:|---|
| Re-agregação | A soma dos 11 subsetores de cada região reproduz a matriz original (fluxos intermediários, demanda final, produção, valor adicionado e importações) | 0,000000 | R$ milhões |
| Contas-satélite | A soma dos subsetores reproduz as emissões, as ocupações, a água e a energia do S38 original | 0,000000 | unidades da conta |
| Balanço | Em cada subsetor, vendas = VBP e compras + valor adicionado = VBP (salvo o resíduo da matriz original, repartido pelo VBP) | 0,000000 | R$ milhões |
| Não negatividade | Nenhum fluxo, valor adicionado ou emissão negativo novo | 0,000000 | número de células |
| Excedente operacional | EOB ≥ 10% do VBP em todos os subsetores com produção | 0,100000 | fração do VBP |
| Modelo | A inversa de Leontief é não negativa, com diagonal ≥ 1, também com as colunas latentes | 0,000000 | menor elemento de L |
| Reprodução do artigo | Os nove cenários do artigo, rodados na MIP original, reproduzem os valores publicados | 0,004859 | t CO₂e (maior diferença) |
| Variantes | As 9 especificações (principal e 8 variantes) passam nas mesmas checagens; nas variantes E3 e E4 as emissões preservam só o total | 9,000000 | especificações |

*Nota: 'Valor' é a maior diferença absoluta encontrada (ou a contagem indicada); tolerância de 10⁻⁶ nas igualdades.*
*Fonte: Elaboração própria.*
