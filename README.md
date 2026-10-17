# MIP-desagregacao

Desagregação do setor **S38 — Energia elétrica, gás natural e outras utilidades** na matriz
insumo-produto inter-regional **Rio Grande do Sul (RS) × Restante do Brasil (RB), 2019**
(NEREUS/USP, método IIOAS; 68 setores × 2 regiões; R$ milhões correntes; emissões em t CO₂e).

O S38 junta todas as fontes de geração, a transmissão/distribuição e o gás canalizado. Por isso o seu
coeficiente de emissão é uma média. O projeto desagrega o S38 em subsetores (renováveis × fósseis,
rede, gás) **preservando exatamente todos os totais da matriz original**, para simular choques de
demanda final no RS com um modelo de Leontief com coeficientes de emissão.

## Status

| Rodada | Situação | Relatório |
|---|---|---|
| 01 — organização, leitor, validação, replicação, diagnóstico do S38, motor de desagregação (com parâmetros **fictícios**), teste de fontes externas | concluída em 15/10/2026 | [respostas/RODADA_01_resposta.md](respostas/RODADA_01_resposta.md) |
| 02 — dados de 2019, motor com 11 subsetores, parâmetros reais e MIP v01 | **parcial** em 15/10/2026: ONS coletado e conferido; motor com 11 subsetores pronto (T6–T8); leitores das demais fontes prontos. Parâmetros e MIP v01 **parados**: a rede liberada não chegou ao ambiente (`*.gov.br` e `seeg.eco.br` com 403) | [respostas/RODADA_02_resposta.md](respostas/RODADA_02_resposta.md) |
| 02b — continuação da 02 com rede: fontes, parâmetros reais, MIP v01 e variantes, quadro por subsetor | concluída em 15/10/2026, com pontos em aberto (EOB negativo em GN e GAS; RAP 2019-2020 com fonte secundária) | [respostas/RODADA_02b_resposta.md](respostas/RODADA_02b_resposta.md) |
| 03 — MIP v02 consolidada (D8, D9, D10), variantes, comparativo v01 × v02 e executor de cenários | concluída em 16/10/2026 | [respostas/RODADA_03_resposta.md](respostas/RODADA_03_resposta.md) |
| 04 — MIP v03 final (V1, V2, V3) e simulações do artigo (blocos A0, A1, A2 e B), tabelas e figuras de rascunho | concluída em 17/10/2026 | [respostas/RODADA_04_resposta.md](respostas/RODADA_04_resposta.md) |
| 05 — MIP v04 final (D17, D18), variante E4, diagnóstico NEREUS × SEEG, simulações finais e material do artigo (`artigo/`) | concluída em 17/10/2026 (tag `mip-v04-final`) | [respostas/RODADA_05_resposta.md](respostas/RODADA_05_resposta.md) |

Decisões do Francisco em vigor: D1 = C (11 subsetores), D2 = D3 = D4 = D6 = A, D5 = E1 (E2 e E3 como
sensibilidades), D7 = A, D8 = A (geração por fonte: Brasil pelo BEN 2020, RS pelo ONS), D9 = (a) + (b) + (f) + (r)
(correção do EOB negativo), D10 = gás por comprador no RS pela Sulgás, V1 (TUST da geração por MWh no SIN;
remunerações da geração ∝ VBP − combustível), V2 (GAS-RB pelo preço da Sulgás), V3 (RAP 24883.4; variante com os
encargos do ONS), D11 = R4a, D12 = renováveis → EOL-RS, D13 = fósseis → CAR-RS e GN-RS ∝ VBP, D14 = E1 pela regra do
executor, D15 = bloco B por R$ 1 bi e por TWh, D16 = investimento fora, D17 = transmissão pelos encargos de uso faturados
pelo ONS em 2019 (substitui a V3), D18 = TUST das colunas latentes pela TUST por MWh do RS, D19 = κ 0.70 (ALERTA do T12
aceito), D20 = fósseis por D13 nas tabelas principais, D21 = E1 na principal (E3 e E4 como sensibilidades).

A versão **final** é a **v04** (Rodada 05; tag `mip-v04-final`): `resultados/rodada05/MIP_RS_RB_2019_S38_11sub_v04.xlsx`
(+ `_longo.csv` e `_coef_latentes.csv`; v03 + D17 + D18), com as variantes `_P2`, `_E2`, `_E3`, `_E4`, `_gas4dist`,
`_rap_media`, `_k060` e `_eta005` (CSV longo), o quadro `resultados/rodada05/quadro_subsetores_v04.xlsx` (com o
comparativo v03 × v04), as simulações finais em `resultados/rodada05/simulacoes_v04.xlsx`, o diagnóstico
`resultados/rodada05/diagnostico_seeg_nereus.xlsx` e o **material do artigo** em `artigo/` (tabelas em .xlsx, .docx e
.md; figuras em PNG e PDF; textos da metodologia, limitações, referências e números-chave em .md e .docx), todo gerado
por `scripts/rodada05_artigo.py`.

A versão anterior, v03 (Rodada 04): `resultados/rodada04/MIP_RS_RB_2019_S38_11sub_v03.xlsx` (+ `_longo.csv`
e `_coef_latentes.csv`; principal: P1 + E1 + D9 + V1 + V2, κ = 0.70, η = 0.10, sem a extensão de viabilidade), com as
variantes `_P2`, `_E2`, `_E3`, `_gas4dist`, `_rap_ons`, `_k060` e `_eta005` (CSV longo), o quadro
`resultados/rodada04/quadro_subsetores_v03.xlsx` (com o comparativo v02 × v03) e as simulações do artigo em
`resultados/rodada04/simulacoes_v03.xlsx` (figuras de rascunho em `resultados/rodada04/figuras/`).

A versão anterior, v02 (Rodada 03): `resultados/rodada03/MIP_RS_RB_2019_S38_11sub_v02.xlsx` (principal:
P1 + E1 + D9, κ = 0.70, η = 0.10, teto do gás por comprador 0.90), com as variantes P2, E2, E3 (.xlsx) e
κ = 0.60/0.80 e κ = 0.70 sem a extensão de viabilidade (as três só com o piso κ), η = 0.05 e GAS-RB pelo preço da
Sulgás (CSV longo + `_coef_latentes.csv`), o quadro `resultados/rodada03/quadro_subsetores_v02.xlsx` (com o comparativo v01 × v02) e a
prévia `previa_multiplicadores_v02.xlsx` (PRÉVIA). Para simular choques, use o executor de cenários (abaixo).

A **primeira desagregação real** foi a v01 (Rodada 02b): `resultados/rodada02/MIP_RS_RB_2019_S38_11sub_v01.xlsx`
(principal, P1 + E1), as variantes `_P2`, `_E2` e `_E3`, o quadro `resultados/rodada02/quadro_subsetores_v01.xlsx`
e a prévia `previa_multiplicadores_v01.xlsx` (marcada PRÉVIA). A v01 tem EOB negativo em GN e GAS (ALERTA; ver o
relatório da 02b, Seção 10). Os arquivos em `resultados/rodada01/teste/` usam valores fictícios e não devem ser
usados em análises.

## Estrutura

```
MIP-desagregacao/
├── README.md
├── requirements.txt          pandas, numpy, openpyxl, pytest, pyyaml, pyarrow, matplotlib, python-docx, pypandoc_binary
├── dados/
│   ├── original/             planilha original (somente leitura) + CHECKSUM.txt (SHA-256)
│   ├── externos/             dados de fontes externas + FONTES.md (registro de fontes) + valores_documentais_v01.csv;
│   │                         brutos/ fica fora do git
│   └── intermediarios/       CSVs derivados (MIP em formato longo; geração, preços, CEMPRE, SEEG, BEN)
├── parametros/               especificações da desagregação (YAML + CSV): TESTE_* (fictícios) e *_v01 (reais);
│                             LEIAME_parametros.md
├── src/mip/                  código (pacote Python)
│   ├── estrutura.py          classe MIP e layout da planilha
│   ├── leitura.py            leitor da planilha (coordenadas fixas) e formato longo
│   ├── validacao.py          identidades contábeis
│   ├── modelo.py             Leontief genérico: A, L, emissões, diretas/indiretas, recortes, ranking
│   ├── referencia.py         cenários e valores de referência da Rodada 01
│   ├── diagnostico.py        diagnóstico de um setor nas duas regiões
│   ├── desagregacao.py       motor de desagregação, RAS e verificação
│   ├── exportacao.py         .xlsx com o layout da original e CSV formato longo
│   ├── dados_externos.py     funções de tratamento das fontes externas (reúne mip.externos)
│   ├── cenarios.py           executor de cenários (choques de demanda final em qualquer versão da MIP)
│   └── externos/             um leitor por fonte: ons, siga, leiloes (+ IPCA), seeg, cempre, ben (BEN 2020, D8)
├── scripts/                  rodada01.py; rodada01_teste_fontes.py; rodada02_coleta.py (downloads, rede);
│                             rodada02.py (tratamento); rodada02_parametros.py (parâmetros v01);
│                             rodada02_mip.py (MIP v01, variantes, quadro e prévia);
│                             rodada03.py, rodada03_parametros.py, rodada03_mip.py (MIP v02),
│                             rodada03_decomposicao.py (v01 → v02 passo a passo), rodar_cenarios.py (executor);
│                             rodada04_parametros.py, rodada04_mip.py (MIP v03), rodada04_simulacoes.py;
│                             rodada05_diagnostico_seeg.py, rodada05_parametros.py, rodada05_mip.py (MIP v04),
│                             rodada05_simulacoes.py, rodada05_artigo.py (material do artigo)
├── tests/                    pytest (T1–T16, T2 com as especificações reais v01 a v04, e demais)
├── resultados/rodada01/      saídas da Rodada 01
├── resultados/rodada02/      saídas das Rodadas 02 e 02b (MIP v01 e variantes, checagens, quadro, prévia, referências)
├── resultados/rodada03/      saídas da Rodada 03 (MIP v02 e variantes, quadro v02, prévia, decomposição, cenários)
├── resultados/rodada04/      saídas da Rodada 04 (MIP v03 e variantes, quadro v03, simulações, figuras)
├── resultados/rodada05/      saídas da Rodada 05 (MIP v04 final e variantes, quadro v04, simulações, diagnóstico SEEG)
├── artigo/                   material do artigo: tabelas/ (.xlsx, .docx, .md), figuras/ (PNG e PDF), texto/ (.md e .docx)
├── instrucoes/               instruções de cada rodada
└── respostas/                relatórios das rodadas + HISTORICO.md
```

## Como rodar

```bash
pip install -r requirements.txt
python scripts/rodada01.py              # regenera todas as saídas da Rodada 01
python -m pytest                        # testes (inclui T1: hash da planilha original)
python scripts/rodada01_teste_fontes.py # opcional: teste de acesso às fontes externas (precisa de rede)
python scripts/rodada02_coleta.py       # Rodada 02: baixa as fontes (precisa de rede; brutos > 20 MB ficam fora do git)
python scripts/rodada02.py              # Rodada 02: trata o que foi baixado e gera as saídas
python scripts/rodada02_parametros.py   # Rodada 02b: parâmetros reais (parametros/*_v01)
python scripts/rodada02_mip.py          # Rodada 02b: MIP v01 + variantes, checagens, quadro e prévia
python scripts/rodada03.py              # Rodada 03: geração por fonte (D8) e reconciliação
python scripts/rodada03_parametros.py   # Rodada 03: parâmetros v02
python scripts/rodada03_mip.py          # Rodada 03: MIP v02 + variantes, quadro v02 e prévia
python scripts/rodada03_decomposicao.py # Rodada 03: efeito de cada mudança v01 → v02
python scripts/rodar_cenarios.py        # executor de cenários (padrão: 9 cenários da Rodada 01 na original, v01 e v02)
python scripts/rodada04_parametros.py   # Rodada 04: parâmetros v03 (V1, V2, V3)
python scripts/rodada04_mip.py          # Rodada 04: MIP v03 + variantes e quadro v03
python scripts/rodada04_simulacoes.py   # Rodada 04: simulações do artigo (A0, A1, A2, B), robustez, tabelas e figuras
python scripts/rodada05_diagnostico_seeg.py  # Rodada 05: diagnóstico NEREUS × SEEG e valores da E4 (bruto do SEEG)
python scripts/rodada05_parametros.py   # Rodada 05: parâmetros v04 (D17, D18, E4)
python scripts/rodada05_mip.py          # Rodada 05: MIP v04 + variantes e quadro v04
python scripts/rodada05_simulacoes.py   # Rodada 05: simulações finais, A0_E4 e robustez
python scripts/rodada05_artigo.py       # Rodada 05: material do artigo (pasta artigo/)
```

Executor de cenários: escreva os choques num CSV `cenario,regiao,setor,valor_R$mi` (modelo em
`parametros/cenarios_exemplo.csv`) e rode, por exemplo,
`python scripts/rodar_cenarios.py --cenarios meus.csv --mip original --mip v02=resultados/rodada03/MIP_RS_RB_2019_S38_11sub_v02.xlsx`.
Sai um .xlsx com impactos (produção, CO₂e, IC, produção por mil t), top-10, RS × RB, diretas × indiretas e a
sensibilidade entre versões. Choque em `S38` numa MIP desagregada é repartido entre os subsetores na proporção das
vendas à demanda final (ou por pesos: `--reparticao S38_DIS=0.9,S38_GAS=0.1`).

Para desagregar com outra especificação:

```python
import sys; sys.path.insert(0, "src")
from mip.leitura import ler_mip_original
from mip.desagregacao import ler_especificacao, desagregar
from mip.modelo import ModeloLeontief

res = desagregar(ler_mip_original(), ler_especificacao("parametros/especificacao_v04.yaml"))
print(res.checagens)                       # verificação (OK / ALERTA / FALHA)
res.exportar("saida.xlsx", "saida_longo.csv")
modelo = ModeloLeontief(res.mip)           # o mesmo modelo serve para a MIP desagregada
```

O formato das especificações está em [parametros/LEIAME_parametros.md](parametros/LEIAME_parametros.md).

## Regras do projeto

A planilha original é intocável (hash conferido em todo `pytest`). Nada é sobrescrito entre rodadas:
as saídas ficam em `resultados/rodadaXX/` e os arquivos derivados levam versão (`_v01`…). As decisões
metodológicas são do Francisco. Nenhum dado é inventado (fontes em `dados/externos/FONTES.md`). Tudo é
reproduzível por script.
