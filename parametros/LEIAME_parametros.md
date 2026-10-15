# Parâmetros da desagregação — formato

Uma desagregação é descrita por **um YAML** (opções) + **CSVs** (subsetores, participações e regras).
Todos os arquivos `TESTE_*` desta pasta têm **valores fictícios** e servem só para testar o motor
(Rodada 01). Os parâmetros reais (decisões D1–D6 do Francisco) entram na Rodada 3, em arquivos novos.

Uso:

```python
from mip.leitura import ler_mip_original
from mip.desagregacao import ler_especificacao, desagregar

res = desagregar(ler_mip_original(), ler_especificacao("parametros/TESTE_especificacao.yaml"))
res.checagens            # verificação (OK / ALERTA / FALHA)
res.exportar("saida.xlsx", "saida_longo.csv")
```

## YAML (`*_especificacao.yaml`)

| Chave | Valores | Significado |
|---|---|---|
| `nome`, `descricao`, `aviso` | texto | identificação; `aviso` vai no topo da aba principal e no LEIAME |
| `setor_alvo` | ex.: `S38` | setor a desagregar |
| `regioes` | ex.: `[RS, RB]` ou `[RS]` | regiões onde o setor é desagregado (D2) |
| `bloco_intrassetorial` | `proporcional` \| `geracao_vende_para_rede` | regra do bloco S38→S38 (D4) |
| `modo_vbp` | `participacoes` \| `ancora_bloco` | `participacoes`: VBP de cada subsetor = participação × VBP do S38. `ancora_bloco` (só com `geracao_vende_para_rede`): o VBP total da geração de cada região é igual às vendas do S38 da região ao S38 das duas regiões; as participações informadas só repartem a geração entre fontes e o restante entre rede e gás (D3) |
| `arquivos` | nomes dos CSVs | relativos à pasta do YAML |
| `ras.tolerancia`, `ras.max_iter` | número | conciliação biproporcional das linhas |

## CSVs

Em todas as regras, `*` (ou vazio) é curinga. Quando mais de uma regra se aplica, vale a **mais
específica**; empate entre regras diferentes é erro. Sem regra aplicável, vale `proporcional_vbp`.
A coluna `fonte` é obrigatória na prática: tudo o que não for fictício precisa de fonte (regra 4).

**`subsetores`**: `codigo, nome, tipo` — tipo ∈ `geracao | rede | gas_utilidades`. A mesma lista vale
para todas as regiões desagregadas. `geracao_vende_para_rede` exige exatamente um subsetor `rede`.

**`participacoes_vbp`**: `regiao, subsetor, participacao, fonte` — uma linha por região e subsetor;
somam 1 em cada região. Participação zero = subsetor com produção zero (permitido).

**`regras_coluna`** (repartição dos insumos de cada fornecedor):
`regiao, fornecedor, regiao_fornecedor, regra, subsetor, valor, fonte`
- `regiao`: região do S38 que compra; `fornecedor`: código do setor fornecedor (ex.: `S04`);
  `regiao_fornecedor`: região do fornecedor.
- `regra`: `proporcional_vbp` (uma linha, sem subsetor) | `fixa` (uma linha por subsetor, `valor` =
  participação, somando 1) | `indicador` (uma linha por subsetor, `valor` = indicador; peso ∝ VBP × indicador).

**`regras_linha`** (repartição das vendas a cada comprador fora do bloco S38 e a cada coluna da demanda final):
`regiao, comprador, regiao_comprador, regra, subsetor, valor, fixar_no_ras, fonte`
- `regiao`: região do S38 que vende; `comprador`: código do setor (`S01`…), código da coluna de demanda
  final (`INV_RS`, `FAM_RB`, `EXP_RS`, `DISCREP`…), tipo da coluna (`INV`, `FAM`, `GOV`, `ISFLSF`, `EXP`,
  `DISCREP`), `CI` (todos os setores) ou `DF` (todas as colunas de demanda final).
- `regra`: `proporcional_vbp` | `somente_rede_e_gas` (geração não vende fora do bloco; rede e gás ∝ VBP) |
  `fixa_por_comprador` (uma linha por subsetor, `valor` = participação).
- `fixar_no_ras` (`sim`/`nao`): mantém fixas as células dessa regra na conciliação RAS. As células do
  bloco S38→S38 e as de valor negativo (discrepância estatística) são sempre fixas.
- Se as regras de linha não fecharem o VBP de cada subsetor, o motor aplica RAS (reporta convergência e
  iterações). Se for impossível fechar (ex.: geração sem compradores com VBP maior que as vendas ao
  bloco), o motor para com uma mensagem explicando o motivo.

**`regras_primarios`** (insumos primários e contas satélite): `regiao, item, regra, subsetor, valor, fonte`
- `item` ∈ `importacoes, ipi, icms, outros_impostos, remuneracoes, impostos_producao, ocupacoes, co2e, agua, energia` (ou `*`).
- `regra`: `proporcional_vbp` | `fixa` | `indicador`, como nas colunas.
- **EOB é o resíduo** que fecha a coluna de cada subsetor (o pequeno resíduo contábil da original é repartido
  pelo VBP); VA = remunerações + EOB + impostos sobre a produção. EOB negativo é **sinalizado** (ALERTA), nunca corrigido.

**`coef_latentes`** (opcional): `regiao, subsetor, tipo_linha, regiao_linha, codigo_linha, coeficiente, fonte`
- Para subsetores com produção-base zero. `tipo_linha = setor`: coeficiente técnico (R$ por R$ de produção)
  comprado do setor `regiao_linha/codigo_linha` da MIP desagregada (pode ser um subsetor, ex.: `S38_TD`).
  `tipo_linha = satelite`: intensidade (`codigo_linha` ∈ `ocupacoes, co2e, agua, energia`, por R$ milhão).
- Esses coeficientes ficam na aba `coef_latentes` (não aparecem como fluxo) e entram em A e nas intensidades
  só no modelo (`ModeloLeontief`), permitindo simular choques no subsetor latente.

## Verificação (sempre executada ao final)

Re-agregação célula a célula (tolerância 1e-6) · balanço de linha e de coluna de cada subsetor ·
identidade do VA · não negatividade (exceto onde a original já tem negativos) · totais satélite ·
EOB ≥ 0 (ALERTA) · subsetores com produção zero zerados · L ≥ 0 e diag(L) ≥ 1 · convergência do RAS.
