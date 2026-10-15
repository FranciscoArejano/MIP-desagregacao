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
| 02 — coleta de dados externos (ANEEL, ONS, CCEE, EPE, IBGE, SEEG, RAIS) | aguardando decisões D1–D6 e liberação de rede | — |
| 03 — MIP desagregada com parâmetros reais | — | — |

Até aqui **nenhuma desagregação real** foi feita. O arquivo em `resultados/rodada01/teste/` usa
valores fictícios e não deve ser usado em análises.

## Estrutura

```
MIP-desagregacao/
├── README.md
├── requirements.txt          pandas, numpy, openpyxl, pytest, pyyaml
├── dados/
│   ├── original/             planilha original (somente leitura) + CHECKSUM.txt (SHA-256)
│   ├── externos/             dados de fontes externas + FONTES.md (registro de fontes)
│   └── intermediarios/       CSVs derivados (MIP em formato longo)
├── parametros/               especificações da desagregação (YAML + CSV); LEIAME_parametros.md
├── src/mip/                  código (pacote Python)
│   ├── estrutura.py          classe MIP e layout da planilha
│   ├── leitura.py            leitor da planilha (coordenadas fixas) e formato longo
│   ├── validacao.py          identidades contábeis
│   ├── modelo.py             Leontief genérico: A, L, emissões, diretas/indiretas, recortes, ranking
│   ├── referencia.py         cenários e valores de referência da Rodada 01
│   ├── diagnostico.py        diagnóstico de um setor nas duas regiões
│   ├── desagregacao.py       motor de desagregação, RAS e verificação
│   └── exportacao.py         .xlsx com o layout da original e CSV formato longo
├── scripts/                  rodada01.py (todas as saídas) e rodada01_teste_fontes.py (rede)
├── tests/                    pytest (T1–T5 e demais)
├── resultados/rodada01/      saídas da Rodada 01
├── instrucoes/               instruções de cada rodada
└── respostas/                relatórios das rodadas + HISTORICO.md
```

## Como rodar

```bash
pip install -r requirements.txt
python scripts/rodada01.py              # regenera todas as saídas da Rodada 01
python -m pytest                        # testes (inclui T1: hash da planilha original)
python scripts/rodada01_teste_fontes.py # opcional: teste de acesso às fontes externas (precisa de rede)
```

Para desagregar com outra especificação:

```python
import sys; sys.path.insert(0, "src")
from mip.leitura import ler_mip_original
from mip.desagregacao import ler_especificacao, desagregar
from mip.modelo import ModeloLeontief

res = desagregar(ler_mip_original(), ler_especificacao("parametros/TESTE_especificacao.yaml"))
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
