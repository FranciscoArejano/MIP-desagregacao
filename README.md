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

Decisões do Francisco em vigor: D1 = C (11 subsetores), D2 = D3 = D4 = D6 = A, D5 = E1 (E2 e E3 como
sensibilidades), D7 = A.

A **primeira desagregação real** é a v01 (Rodada 02b): `resultados/rodada02/MIP_RS_RB_2019_S38_11sub_v01.xlsx`
(principal, P1 + E1), as variantes `_P2`, `_E2` e `_E3`, o quadro `resultados/rodada02/quadro_subsetores_v01.xlsx`
e a prévia `previa_multiplicadores_v01.xlsx` (marcada PRÉVIA). A v01 tem EOB negativo em GN e GAS (ALERTA; ver o
relatório da 02b, Seção 10). Os arquivos em `resultados/rodada01/teste/` usam valores fictícios e não devem ser
usados em análises.

## Estrutura

```
MIP-desagregacao/
├── README.md
├── requirements.txt          pandas, numpy, openpyxl, pytest, pyyaml, pyarrow
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
│   └── externos/             um leitor por fonte: ons, siga, leiloes (+ IPCA), seeg, cempre
├── scripts/                  rodada01.py; rodada01_teste_fontes.py; rodada02_coleta.py (downloads, rede);
│                             rodada02.py (tratamento); rodada02_parametros.py (parâmetros v01);
│                             rodada02_mip.py (MIP v01, variantes, quadro e prévia)
├── tests/                    pytest (T1–T8, T2 com a especificação real e demais)
├── resultados/rodada01/      saídas da Rodada 01
├── resultados/rodada02/      saídas das Rodadas 02 e 02b (MIP v01 e variantes, checagens, quadro, prévia, referências)
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
```

Para desagregar com outra especificação:

```python
import sys; sys.path.insert(0, "src")
from mip.leitura import ler_mip_original
from mip.desagregacao import ler_especificacao, desagregar
from mip.modelo import ModeloLeontief

res = desagregar(ler_mip_original(), ler_especificacao("parametros/especificacao_v01.yaml"))
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
