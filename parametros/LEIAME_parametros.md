# Parâmetros da desagregação — formato

Uma desagregação é descrita por **um YAML** (opções) + **CSVs** (subsetores, participações e regras).
Todos os arquivos `TESTE_*` desta pasta têm **valores fictícios** e servem só para testar o motor
(Rodada 01).

Os parâmetros **reais** são os arquivos `*_v01*` (Rodada 02b; `scripts/rodada02_parametros.py`) e `*_v02*` (Rodada 03,
MIP v02: D8 = A, D9 = (a) + (b) + (f) + (r), D10 = Sulgás; `scripts/rodada03_parametros.py`; especificações
`especificacao_v02.yaml` e variantes `_P2`, `_E2`, `_E3`, `_k060`, `_k080`, `_eta005`, `_sem_viabilidade` e
`_gas_sulgas`; as variantes κ e `_sem_viabilidade` usam só o piso κ, sem a extensão de viabilidade; `_gas_sulgas` usa
`componentes_v02_gas_sulgas.csv`, `regras_linha_v02_gas_sulgas.csv` e `regras_primarios_v02_gas_sulgas.csv`, com o
VBP do GAS-RB pelo preço da Sulgás). Na v02, o gás por comprador (`regras_linha_v02.csv`) tem um teto: o gás de cada
comprador não passa de 0.90 das compras dele ao S38 (HIPÓTESE da revisão da Rodada 03); o excedente vai aos demais
compradores do mesmo grupo (D10 no RS; indústria do BEN no RB) ou, se o grupo inteiro estiver no teto (caso do
"serviço" do RS, só o S19), aos demais compradores da região, na proporção do alvo. Abas `gas_por_comprador`, `gas_grupos_teto` e
`gas_x_eletricidade_BEN` do `quadro_parametros_v02.xlsx`. A energia do satélite usa
`dados/intermediarios/ben_2019_consumo_especifico_v02.csv` (PET com as "outras não renováveis", como na D8).
Os parâmetros **v03** (Rodada 04, a versão final: `scripts/rodada04_parametros.py`) partem dos v02 e mudam V1 (TUST da
geração por MWh no SIN, `pesos_tust_geracao_v03.csv`; remunerações e ocupações da geração ∝ VBP − combustível), V2
(VBP do GAS-RB pelo preço da Sulgás) e V3 (variante `_rap_ons`); especificações `especificacao_v03.yaml` e variantes
`_P2`, `_E2`, `_E3`, `_gas4dist`, `_rap_ons`, `_k060` e `_eta005`, todas sem a extensão de viabilidade (o script roda o
T9 sem ela e só a ligaria se ele falhasse); `quadro_parametros_v03.xlsx`. `cenarios_v03.csv` traz os cenários das
simulações da Rodada 04 (blocos A0, A1, A2 e B).
Não edite à mão: rode o script de novo. `cenarios_exemplo.csv` traz os 9 cenários da Rodada 01 no formato do
executor de cenários (`scripts/rodar_cenarios.py`). Na v01:
- `especificacao_v01.yaml` — principal (P1 + E1); `_P2`, `_E2` e `_E3` — sensibilidades;
- `subsetores_v01.csv`, `participacoes_vbp_v01.csv` (P1 = GWh × preço) e `_P2` (GWh), `componentes_v01.csv`
  (VBP do TRA e do GAS, G, fração da TUST), `regras_coluna_v01.csv`, `regras_linha_v01.csv`,
  `regras_primarios_v01.csv`, `latentes_espelho_v01.csv`, `correspondencia_ben_mip_v01.csv` (BEN → compradores);
- `quadro_parametros_v01.xlsx` — cada número usado, com unidade, fonte e cálculo (para revisão).
Cada linha dos CSVs tem a coluna `fonte`; os números de documentos estão em `dados/externos/valores_documentais_v01.csv`.

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
| `bloco_intrassetorial` | `proporcional` \| `geracao_vende_para_rede` \| `roteamento_por_componentes` | regra do bloco S38→S38 (D4) |
| `modo_vbp` | `participacoes` \| `ancora_bloco` \| `ancora_componentes` | `participacoes`: VBP de cada subsetor = participação × VBP do S38. `ancora_bloco` (só com `geracao_vende_para_rede`): o VBP total da geração de cada região é igual às vendas do S38 da região ao S38 das duas regiões; as participações informadas só repartem a geração entre fontes e o restante entre rede e gás. `ancora_componentes` (só com `roteamento_por_componentes`, Rodada 02): geração = E_r = F_r − T_r − G_r, repartida pelos pesos da geração (MWh × preço); transmissão = T_r; gás = `vbp_gas`; distribuição = resíduo X_r − E_r − T_r − VBP_gas (tem de ser > 0) |
| `subsetor_termica_gas` | ex.: `S38_GN` | comprador do gás G_r no roteamento (obrigatório se algum G_r > 0) |
| `niveis` | `{co2e: {modo: residuo \| proporcional \| sem_residuo, residuo_para: [S38_DIS, S38_GAS]}}` | tratamento dos níveis absolutos (regra `niveis`, ex.: emissões do SEEG): `residuo` (E1) = níveis + resíduo (total da base − Σ níveis) aos subsetores de `residuo_para`, na proporção do VBP; resíduo negativo reduz os níveis proporcionalmente (ALERTA). `proporcional` (E2) = total da base na proporção dos níveis. `sem_residuo` (E3) = só os níveis; **não preserva o total da base** (ALERTA) |
| `piso_vbp` | `{kappa: 0.70, combustiveis: {S38_CAR: [S04], S38_GN: [S05, importacoes], ...}, viabilidade_eta: 0.10, max_iter: 50}` | Rodada 03, D9-f (só com `ancora_componentes`): VBP de cada subsetor listado ≥ combustível ÷ κ (combustível = compras às linhas listadas, de todas as origens, e as importações, se `importacoes` estiver na lista). Com `viabilidade_eta`, o piso também é ≥ combustível ÷ (1 − η − φ), em que φ é a parte do VBP que o reequilíbrio não pode mexer além do combustível (TUST, remunerações, impostos sobre a produção, células negativas e o resíduo contábil da coluna original). Quem fica abaixo sobe ao piso; os demais subsetores de geração da mesma região caem na proporção do VBP inicial (E_r não muda). O motor repete a desagregação até estabilizar, redistribuindo sempre a partir do VBP inicial (o piso de viabilidade pode baixar quando o VBP sobe, e o VBP desce até ele); resultado na aba `pisos_vbp` |
| `reequilibrio` | `{eta: 0.10, linhas_fixas: [S04, S05, S19, S03, S09], primarios_ajustaveis: [ipi, icms, outros_impostos], importacoes: fixas, se_inviavel: erro \| limitar}` | Rodada 03, D9-r: RAS dos insumos não energéticos das colunas dos subsetores (compras a setores fora do bloco, exceto `linhas_fixas`; impostos sobre produtos). Fixos: bloco, combustíveis, importações (só `fixas`: as importações do setor-alvo são de energia pela regra do Comex), remunerações e impostos sobre a produção; a checagem `reequilibrio_insumos_fixos` confere que não mudam. Totais de linha preservados; alvo de coluna tal que EOB ≥ η × VBP; quem está acima cede a folga (EOB − η × VBP) na proporção; a soma dos EOB da região não muda. Se nem com os ajustáveis a zero couber, `erro` (padrão) ou `limitar` (EOB fica no máximo possível, ALERTA). Abas `reequilibrio_RAS` e `reequilibrio_insumos`; na aba `parametros`, a etapa `apos_reequilibrio` traz os pesos realizados. Com `piso_vbp.viabilidade_eta`, o bloco `reequilibrio` é obrigatório e `viabilidade_eta ≥ eta` |
| `alerta_multiplicador_producao` | número (ex.: 2.2) | ALERTA se o multiplicador de produção (Σ da coluna de L) de algum subsetor passar desse valor |
| `alerta_insumos_nao_energeticos` | número (ex.: 0.05) | Rodada 04, T12: ALERTA se as compras de algum subsetor com produção a setores fora do bloco, exceto as linhas de combustível (`reequilibrio.linhas_fixas` e `piso_vbp.combustiveis`), ficarem abaixo dessa fração do VBP (checagem `insumos_nao_energeticos_minimo`) |
| `arquivos.pesos_tust_geracao` | CSV `regiao, subsetor, valor, fonte` | Rodada 04, V1 (só no `roteamento_por_componentes`): a parte (1 − α) da transmissão paga pela geração de cada região compradora é repartida entre os subsetores de geração por esses pesos (na v03, o MWh gerado no SIN), e não pelo VBP. Só subsetores de geração, com uma linha para cada região e subsetor de geração (0 explícito para quem não paga; linha faltando é erro); peso > 0 para subsetor sem produção é erro |
| `arquivos` | nomes dos CSVs | relativos à pasta do YAML |
| `ras.tolerancia`, `ras.max_iter` | número | conciliação biproporcional das linhas |

## CSVs

Em todas as regras, `*` (ou vazio) é curinga. Quando mais de uma regra se aplica, vale a **mais
específica**; empate entre regras diferentes é erro. Sem regra aplicável, vale `proporcional_vbp`.
A coluna `fonte` é obrigatória na prática: tudo o que não for fictício precisa de fonte (regra 4).

**`subsetores`**: `codigo, nome, tipo` — tipo ∈ `geracao | transmissao | distribuicao | gas_utilidades`
(`rede`, da Rodada 01, equivale a `distribuicao`). A mesma lista vale para todas as regiões desagregadas.
`geracao_vende_para_rede` exige exatamente um subsetor `distribuicao`; `roteamento_por_componentes` exige
exatamente um `transmissao`, exatamente um `distribuicao` e ao menos um `geracao`.

**`componentes`** (Rodada 02): `regiao, componente, valor, fonte` — valores em R$ milhões por região (ou `*`):
`vbp_transmissao` (T_r), `vbp_gas`, `gas_termicas` (G_r, padrão 0) e `fracao_transmissao_distribuicao`
(parte de T_r paga pela distribuição; padrão 0.5 — metodologia da TUST). Roteamento por componentes: para a
região vendedora r, F_r = vendas do S38-r ao S38 de todas as regiões; E_r = F_r − T_r − G_r (≥ 0). Cada
componente vai à região compradora q na proporção F_rq / F_r: energia (geração de r, ∝ VBP) → distribuição de q;
transmissão (TRA de r) → fração α à distribuição de q e 1 − α à geração de q (∝ VBP, sem latentes e zerados);
gás (GAS de r) → `subsetor_termica_gas` de q.

**`latentes_espelho`** (Rodada 02): `regiao, subsetor, regiao_espelho, fonte` — subsetor latente (produção zero)
cuja coluna de coeficientes copia a do mesmo subsetor em outra região: para cada fornecedor, soma as duas
origens na coluna do espelho e reparte entre as origens pela participação de cada origem nas compras desse
insumo na coluna original do S38 da região do latente (para subsetores do próprio S38, pela participação das
origens no bloco S38→S38 da região). Intensidades satélite: as do espelho.

**`participacoes_vbp`**: `regiao, subsetor, participacao, fonte` — uma linha por região e subsetor;
somam 1 em cada região. Participação zero = subsetor com produção zero (permitido).

**`regras_coluna`** (repartição dos insumos de cada fornecedor):
`regiao, fornecedor, regiao_fornecedor, regra, subsetor, valor, fonte`
- `regiao`: região do S38 que compra; `fornecedor`: código do setor fornecedor (ex.: `S04`);
  `regiao_fornecedor`: região do fornecedor.
- `regra`: `proporcional_vbp` (uma linha, sem subsetor) | `fixa` (uma linha por subsetor, `valor` =
  participação, somando 1) | `indicador` (uma linha por subsetor, `valor` = indicador; peso ∝ VBP × indicador) |
  `fixa_com_teto` (como `fixa`, com coluna `teto_vbp` = teto como fração do VBP do subsetor; o excedente vai,
  conforme `destino_excedente`, aos `demais_vbp` — subsetores sem teto na regra, na proporção do VBP — ou aos
  subsetores da regra `sem_teto`, na proporção das participações). Todo teto atingido é registrado (aba
  `tetos_atingidos`).

**`regras_linha`** (repartição das vendas a cada comprador fora do bloco S38 e a cada coluna da demanda final):
`regiao, comprador, regiao_comprador, regra, subsetor, valor, fixar_no_ras, fonte`
- `regiao`: região do S38 que vende; `comprador`: código do setor (`S01`…), código da coluna de demanda
  final (`INV_RS`, `FAM_RB`, `EXP_RS`, `DISCREP`…), tipo da coluna (`INV`, `FAM`, `GOV`, `ISFLSF`, `EXP`,
  `DISCREP`), faixa de setores (`S08:S37`), lista separada por `|` (`S08:S37|S43|FAM`), `CI` (todos os setores)
  ou `DF` (todas as colunas de demanda final). Especificidade: código exato 3; faixa, lista ou tipo 2; `CI`/`DF` 1.
- `regra`: `proporcional_vbp` | `somente_rede_e_gas` = `somente_distribuicao_e_gas` (geração e transmissão não
  vendem fora do bloco; distribuição e gás ∝ VBP) | `fixa_por_comprador` (uma linha por subsetor, `valor` = participação).
- `fixar_no_ras` (`sim`/`nao`): mantém fixas as células dessa regra na conciliação RAS. As células do
  bloco S38→S38 e as de valor negativo (discrepância estatística) são sempre fixas.
- Se as regras de linha não fecharem o VBP de cada subsetor, o motor aplica RAS (reporta convergência e
  iterações). Se for impossível fechar (ex.: geração sem compradores com VBP maior que as vendas ao
  bloco), o motor para com uma mensagem explicando o motivo.

**`regras_primarios`** (insumos primários e contas satélite): `regiao, item, regra, subsetor, valor, fonte`
- `item` ∈ `importacoes, ipi, icms, outros_impostos, remuneracoes, impostos_producao, ocupacoes, co2e, agua, energia` (ou `*`).
- `regra`: `proporcional_vbp` | `fixa` | `indicador`, como nas colunas; `proporcional_ci` (impostos sobre produtos:
  na proporção das compras intermediárias totais — domésticas + importadas — de cada subsetor); `niveis` (uma linha
  por subsetor com o nível absoluto, ex.: t CO₂e do SEEG; o resíduo segue o `modo` do YAML); `fixa_por_tipo`
  (Rodada 03: `subsetor` = código ou tipo — `geracao`, `transmissao`, `distribuicao`, `gas_utilidades` — e `valor` =
  participação; a parte de um tipo é repartida entre os seus subsetores na proporção do VBP final; usada nas
  remunerações e ocupações do CEMPRE, para acompanhar o piso de VBP); `fixa_por_tipo_sem_combustivel` (Rodada 04,
  V1: igual, mas dentro do tipo na proporção de VBP − combustível, com o combustível de `piso_vbp.combustiveis`;
  exige `piso_vbp.combustiveis`).
- **EOB é o resíduo** que fecha a coluna de cada subsetor (o pequeno resíduo contábil da original é repartido
  pelo VBP); VA = remunerações + EOB + impostos sobre a produção. EOB negativo é **sinalizado** (ALERTA), nunca corrigido
  pelo motor por conta própria; a correção só acontece se a especificação pedir `reequilibrio` (Rodada 03, D9-r).

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
