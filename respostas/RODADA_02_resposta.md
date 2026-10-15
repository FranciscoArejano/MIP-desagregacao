# Rodada 02 — Relatório do Claude Code

Projeto: desagregação do S38 na MIP inter-regional RS × RB, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
Data: 15/10/2026 · Instruções: `instrucoes/RODADA_02_instrucoes_CODE.md` · Rodada anterior: `respostas/RODADA_01_resposta.md`
Convenção numérica: ponto decimal, sem separador de milhar.

Decisões aplicadas (mensagem de abertura + Seção 1): D1 = C (11 subsetores); D2, D3, D4 e D6 = A; D5 revisada = E1
principal, com E2 e E3 como sensibilidades; D7 = A (coluna do S38-RS mantida como na base).

## 1. Resumo

- **A liberação da rede não chegou a este container.** `*.gov.br`, `*.ons.org.br` e `seeg.eco.br` continuaram recebendo 403 do proxy em todos os testes, do início ao fim da sessão. Só o bucket S3 do ONS (`ons-aws-prod-opendata.s3.amazonaws.com`) e o PyPI responderam.
- Por isso, conforme a Etapa 1 das instruções, fiz a coleta possível (ONS), a Etapa 3 (motor) e **parei antes da Etapa 4**. As 4 fontes obrigatórias restantes (leilões+IPCA, RAP, SEEG e CEMPRE) estão bloqueadas.
- **ONS:** geração 2019 por usina e por região × subsetor; **26/26 valores de referência reproduzidos** (diferença máxima 0.15 GWh no total do RB). Só a usina "Sol" (ES, 839.2 GWh, "Resíduos Industriais") fica pendente, porque o SIGA não abre.
- **Motor:** 11 subsetores (156 setores-região), `roteamento_por_componentes`, `modo_vbp: ancora_componentes`, regras de coluna com teto, compradores por faixa/lista, impostos ∝ compras intermediárias, latentes por espelho e emissões E1/E2/E3. Os testes T6–T8 e os complementares passam; os 56 testes da Rodada 01 continuam passando.
- **Leitores das fontes bloqueadas** (SIGA, leilões+IPCA, SEEG, CEMPRE) e script de coleta estão prontos e testados com dados sintéticos, mas **não validados com os arquivos reais**. Ao todo, 322 testes passam.
- **Revisão adversarial do motor:** 6 defeitos confirmados (o mais grave: teto aplicado por célula de origem e não pelo total do insumo), todos corrigidos e com teste de regressão.
- Conferência de ordem de grandeza, com os preços e a RAP de referência das instruções: RS fecha (âncora 4.10 bi × GWh·preço 4.06 bi); RB não fecha (72.4 × 93.9 bi). Explicação na Seção 16.
- **O que falta para concluir a rodada:** que a rede liberada chegue ao ambiente (provavelmente exige uma sessão nova). Daí em diante: coleta → parâmetros → MIP v01 + variantes → quadro.

## 2. Status por etapa

| Etapa | Status | Observação |
|---|---|---|
| E1 — Testar o acesso às fontes | concluída | Bloqueadas (403): `dadosabertos.aneel.gov.br`, `apisidra.ibge.gov.br`, `servicodados.ibge.gov.br`, `seeg.eco.br`, `www.gov.br`, `www2.aneel.gov.br`, `www.epe.gov.br`, `www.sulgas.rs.gov.br`, `sulgas.rs.gov.br`, `comexstat.mdic.gov.br`, `api-comexstat.mdic.gov.br`, `dados.ons.org.br`, `www.ons.org.br`, `www.abegas.org.br`. Acessíveis: S3 do ONS e PyPI |
| E2 — Coletar e tratar os dados de 2019 | parcial | 5.1 (ONS) concluída e conferida. 5.2–5.10 bloqueadas; leitores prontos (sem validação com o arquivo real) |
| E3 — Ajustes no motor | concluída | 6.1–6.9 implementados; T6, T7 e T8 passam. T2 "com a especificação real" depende da Etapa 4 |
| E4 — Parâmetros reais | não feita | Parada exigida pela Etapa 1 (fontes obrigatórias bloqueadas) |
| E5 — MIP desagregada v01 + variantes | não feita | Depende da E4 |
| E6 — Quadro-diagnóstico e prévia | não feita | Depende da E5 |
| E7 — Relatório | concluída | Este arquivo, `HISTORICO.md` e `README.md` |

## 3. Arquivos criados, movidos ou alterados

| Caminho | Tipo | O que é | Etapa |
|---|---|---|---|
| `instrucoes/RODADA_02_instrucoes_CODE.md` | texto | Cópia das instruções (veio como anexo; não estava na raiz do repositório no GitHub) | E1 |
| `.gitignore` | config (alterado) | `dados/externos/brutos/` fora do git (brutos > 20 MB) | E1 |
| `requirements.txt` | config (alterado) | + `pyarrow` (leitura do parquet do ONS) | E2 |
| `scripts/rodada02_coleta.py` | script | Downloads com User-Agent de navegador, SHA-256, `DOWNLOAD.txt` por fonte e CSV de acesso; brutos > 20 MB em `brutos/` | E1/E2 |
| `dados/externos/rodada02_acesso_fontes.csv` | registro | Resultado do acesso por URL (data, status, erro, arquivo, bytes, SHA-256) | E1 |
| `dados/externos/ons/DOWNLOAD.txt` | registro | URL, data, tamanho e SHA-256 do bruto do ONS (o bruto, 25 MB, fica fora do git) | E2 |
| `dados/externos/ons/reclassificacao_usinas_v01.csv` | dado (tabela de método) | 7 usinas reclassificadas, com justificativa e fonte | E2 |
| `dados/externos/FONTES.md` | documentação (alterado) | ONS registrado; resultado do teste de acesso da Rodada 02 | E1/E2 |
| `src/mip/externos/__init__.py` | código | Pacote dos leitores de fontes | E2 |
| `src/mip/externos/ons.py` | código | ONS: geração por usina, região, subsetor; reclassificação; casamento com o SIGA; comparação com referências | E2 |
| `src/mip/externos/siga.py` | código | ANEEL SIGA: leitura (encoding/separador), núcleo do CEG, classificação pela Seção 5.2, casamento com o ONS | E2 |
| `src/mip/externos/leiloes.py` | código | Leilões da ANEEL + IPCA (SIDRA): leitura, mapeamento de fontes, correção pelo IPCA, média ponderada, nuclear | E2 |
| `src/mip/externos/seeg.py` | código | SEEG 13.0: leitura em streaming, filtros, mapeamento de combustíveis, PET do RS realocado, SF6 | E2 |
| `src/mip/externos/cempre.py` | código | CEMPRE (SIDRA 6450): leitura, sigilosos por diferença, composição por subsetor | E2 |
| `src/mip/dados_externos.py` | código | Reúne os leitores (e diz quais já foram validados com o arquivo real) | E2 |
| `scripts/rodada02.py` | script | Trata o que foi baixado e gera as saídas da rodada; lista o que falta | E2 |
| `dados/intermediarios/geracao_2019_usina_v01.csv` | dado derivado | Geração 2019 por usina (526 usinas): CEG, região, rótulo ONS, subsetor, regra, GWh | E2 |
| `dados/intermediarios/geracao_2019_regiao_subsetor_v01.csv` | dado derivado | GWh por região × subsetor (com importação de Itaipu e pendentes) | E2 |
| `resultados/rodada02/comparacao_referencias_v01.csv` | resultado | Esperado × obtido × diferença (ONS, 26 itens) | E2 |
| `resultados/rodada02/situacao_fontes_v01.csv` | resultado | Fontes disponíveis × pendentes | E2 |
| `src/mip/desagregacao.py` | código (alterado) | Motor: tipos novos, roteamento por componentes, âncora por componentes, teto sobre o total do insumo, compradores por faixa/lista, `proporcional_ci`, `niveis` (E1/E2/E3), latentes por espelho, checagens novas | E3 |
| `parametros/LEIAME_parametros.md` | documentação (alterado) | Formato das novas opções da especificação | E3 |
| `tests/auxiliares.py` | teste (alterado) | Especificação de 11 subsetores com valores **fictícios** (só para testar o motor) | E3 |
| `tests/test_desagregacao_r02.py` | teste | T2/T3 com 11 subsetores, T6, T7, T8, tetos, regressões da revisão | E3 |
| `tests/test_externos_ons.py`, `test_externos_siga.py`, `test_externos_leiloes.py`, `test_externos_seeg.py`, `test_externos_cempre.py` | teste | Testes dos leitores (dados sintéticos; o do ONS também com o arquivo real, se presente) | E2 |
| `respostas/RODADA_02_resposta.md` | relatório | Este relatório | E7 |
| `respostas/HISTORICO.md`, `README.md` | documentação (alterado) | Linha da Rodada 02; status do projeto | E7 |

Nada foi movido. As saídas da Rodada 01 (`resultados/rodada01/`) não foram alteradas: re-rodei `scripts/rodada01.py` com o motor novo para conferir (valores idênticos, diferença máxima 0) e restaurei os arquivos, para não sobrescrever a rodada anterior.

## 4. Validação da MIP original

Sem mudança nesta rodada: a original segue intacta (T1: SHA-256 `15e734a4…a3ea` confere) e as checagens de identidades da Rodada 01 continuam passando (`tests/test_leitura_validacao.py`, 9 testes).

## 5. Reprodução dos resultados

- Os 9 cenários da Rodada 01 continuam reproduzidos com o motor novo (`tests/test_replicacao.py`, 14 testes).
- A MIP de teste da Rodada 01 (8 subsetores fictícios) sai com valores **idênticos** (diferença máxima 0) com o motor da Rodada 02; só ganhou uma checagem nova (`bloco_fluxos_regionais_preservados`).
- A prévia de multiplicadores e os 9 cenários na v01 (Etapa 6b) **não foram feitos**: dependem da MIP v01.

## 6. Diagnóstico do S38

O quadro-diagnóstico por subsetor (Etapa 6a, `resultados/rodada02/quadro_subsetores_v01.xlsx`) **não foi gerado**, porque depende da MIP v01. O que já dá para dizer com os dados disponíveis:

- **Geração 2019 (ONS, GWh):** RS 22750.2 = HID 14542.6 · EOL 5266.9 · CAR 2625.2 · GN 174.6 (UTE Canoas) · BIO 141.0 (São Sepé, São Borja e CMPC). RB 517932.1 = HID 370796.7 · EOL 48122.9 · SOL 4384.6 · BIO 12304.5 · CAR 16907.3 · GN 46474.0 · PET 1974.3 · NUC 16128.8 · pendente 839.2 (usina Sol). Itaipu 50 Hz (importação): 24402.2.
- **D7 = A (limitação documentada):** a coluna de insumos do S38-RS repete a estrutura do RB (Rodada 01, ponto 2). Por isso as regras de coluna com teto movem valores pequenos no RS (ex.: carvão S04 → CAR-RS: 14.7 R$ mi no total).

## 7. Motor de desagregação

**O que mudou** (`src/mip/desagregacao.py`, documentado em `parametros/LEIAME_parametros.md`):

| Seção | Implementação |
|---|---|
| 6.1 | Tipos `geracao`, `transmissao`, `distribuicao`, `gas_utilidades`; `rede` continua aceito e equivale a `distribuicao` |
| 6.2 | `bloco_intrassetorial: roteamento_por_componentes`. Para cada região vendedora r: F_r (vendas ao S38 das duas regiões), T_r = VBP do TRA, G_r (gás às térmicas, padrão 0) e E_r = F_r − T_r − G_r ≥ 0 (senão, erro explicativo). Cada componente vai à região q na proporção F_rq/F_r. Energia: geração de r (∝ VBP) → DIS-q. Transmissão: α → DIS-q e 1 − α → geração de q (∝ VBP, sem latentes e zerados). Gás: GAS-r → `subsetor_termica_gas` de q. α e G vêm do CSV `componentes` (padrão 0.5 e 0) |
| 6.3 | `modo_vbp: ancora_componentes`: geração = E_r repartida pelos pesos (MWh × preço); TRA = T_r; GAS = `vbp_gas`; DIS = X_r − E_r − T_r − VBP_GAS > 0 (senão, erro) |
| 6.4 | Regras de linha com comprador por faixa e lista (`S08:S37\|S43\|FAM`), `somente_distribuicao_e_gas` (geração e TRA não vendem fora do bloco), RAS fechando o VBP de DIS e GAS |
| 6.5 | `latentes_espelho`: coluna do mesmo subsetor no RB, somando as origens; origem de cada insumo pela coluna original do S38-RS; subsetores do S38 (ex.: TRA) pela participação das origens no bloco S38→S38-RS; intensidades satélite do espelho. Nuclear-RS fica zerado, sem latente |
| 6.6 | Regra `niveis` + YAML `niveis.co2e.modo`: `residuo` (E1), `proporcional` (E2) e `sem_residuo` (E3, marcada "NÃO PRESERVA O TOTAL DA BASE"). Resíduo negativo reduz os níveis proporcionalmente e gera ALERTA |
| 6.7 | Energia, água e ocupações: regras `fixa`/`indicador` já existentes (os pesos virão da Etapa 4) |
| 6.8 | Regra de coluna `fixa_com_teto`: teto × VBP sobre o **total** do insumo (todas as origens; `grupo_teto` opcional para insumos que dividem o mesmo teto, ex.: S03 + S09); excedente aos demais ∝ VBP (`demais_vbp`) ou aos subsetores sem teto da regra (`sem_teto`); todo teto atingido vai para a aba `tetos_atingidos`. Impostos sobre produtos: `proporcional_ci` (compras intermediárias domésticas + importadas) |
| 6.9 | Testes T6, T7, T8 (abaixo) |

Novas checagens: `roteamento_vendas_geracao_igual_E`, `roteamento_vendas_transmissao_igual_T`, `roteamento_geracao_e_transmissao_nao_vendem_fora` (valores absolutos), `roteamento_fracao_transmissao`, `bloco_fluxos_regionais_preservados`, `tetos_atingidos`, `niveis_residuo_nao_negativo`. A re-agregação na E3 exige que só o S38 difira da base, e exatamente pelo resíduo. `A_soma_colunas_menor_1` agora nomeia as colunas (inclusive as latentes) com Σa ≥ 1. Abas extras na exportação: `componentes_bloco`, `tetos_atingidos`, `niveis`.

**Revisão adversarial** (workflow com 3 revisores e um cético por achado): 6 achados confirmados e corrigidos, 2 refutados.

| Achado confirmado | Correção |
|---|---|
| Teto aplicado por célula de origem, e não pelo total do insumo (o subsetor podia chegar a 2 × teto); o latente PET-RS herdava Σa > 1 | Teto sobre o total (todas as origens; grupo opcional); redução proporcional por origem; teste do total |
| Checagem da fração da transmissão dava FALHA falsa com região não desagregada | O esperado considera só as regiões desagregadas; teste com `regioes=['RS']` |
| Checagens do roteamento usavam soma líquida (geração vendendo fora do bloco passava) — dois achados | Vendas dentro do bloco comparadas com E_r/T_r + checagem em valor absoluto fora do bloco; teste de regressão |
| E3 desligava toda a verificação de CO₂e | Esperado ajustado só no S38 da região (base − resíduo); o resto continua estrito; teste de regressão |

**Como usar:** igual à Rodada 01 (`desagregar(ler_mip_original(), ler_especificacao("parametros/<espec>.yaml"))`). A especificação real (`parametros/especificacao_v01.yaml`) é a Etapa 4, que não foi feita.

**Testes** (`python -m pytest`: **322 passaram, 0 falharam**):

| Teste | Resultado | O que verifica |
|---|---|---|
| T1 | passou | Hash da original |
| T2 | passou (12 casos da Rodada 01 + 11 subsetores fictícios) | Re-agregação exata. **Com a especificação real: pendente (Etapa 4)** |
| T3 | passou (K = 2, 5, 8 e 11) | Desagregação neutra reproduz os cenários |
| T4, T5 | passaram | Latente explícito; geração vende para a rede (compatibilidade) |
| T6 — roteamento | passou (3 testes) | Geração de r vende E_r (tudo à distribuição); TRA vende T_r dentro do bloco; 50/50 por região compradora (e ∝ VBP entre as fontes); energia por F_rq/F_r; os 4 fluxos RS↔RB; latentes e zerados não pagam transmissão; G_r > 0 vai às térmicas a gás; E_r < 0 dá erro |
| T7 — latentes | passou (3 testes) | Solar-RS e Petróleo-RS: fluxos-base zero; Σ das origens = coluna do espelho; origens pela coluna original e pelo bloco; intensidades do espelho; multiplicador = coluna de (I − A)⁻¹; Nuclear-RS zerado sem latente |
| T8 — emissões | passou (3 testes) | E1 e E2 preservam o total de cada região; E3 difere exatamente pelo resíduo; resíduo negativo reduz os identificados; E3 continua verificando o resto |
| Complementares do motor | passaram | Tetos (total por insumo, grupo S03+S09, PET latente), faixas/listas de comprador, vendas fora do bloco, erros explicativos, exportação com 156 setores |
| Leitores | 245 passaram | ONS (5, incluindo as referências com o arquivo real), SIGA (60), leilões+IPCA (76), SEEG (45), CEMPRE (59) — sintéticos |

## 8. Acesso a fontes externas

| Fonte | Acessível? | O que foi baixado | Observação |
|---|---|---|---|
| ONS — geração por usina (S3) | sim | `GERACAO_USINA-2_2019.parquet` (25049331 bytes; fora do git) | SHA-256 em `dados/externos/ons/DOWNLOAD.txt` |
| ANEEL SIGA | não | nada | 403 em `dadosabertos.aneel.gov.br` |
| ANEEL leilões | não | nada | 403 em `dadosabertos.aneel.gov.br` |
| IBGE SIDRA (IPCA, CEMPRE) | não | nada | 403 em `apisidra.ibge.gov.br` e `servicodados.ibge.gov.br` |
| ANEEL RAP (documentos) | não | nada | 403 em `www.gov.br` e `www2.aneel.gov.br` |
| SEEG 13.0 | não | nada | 403 em `seeg.eco.br` (também com User-Agent de navegador) |
| Sulgás / ANP / MME / EPE | não | nada | 403 em `www.sulgas.rs.gov.br`, `sulgas.rs.gov.br`, `www.gov.br`, `www.epe.gov.br` |
| Comex Stat | não | nada | 403 em `comexstat.mdic.gov.br` e `api-comexstat.mdic.gov.br` |
| ONS (portal), ABEGÁS | não | nada | 403 em `dados.ons.org.br`, `www.ons.org.br`, `www.abegas.org.br` |
| PyPI | sim | `pyarrow` | — |

Testei no início (10:29 UTC), no meio e no fim da sessão (17:20 UTC): o mesmo resultado em todos os testes.

## 9. Decisões tomadas por você nesta rodada

Só decisões de implementação. Os pontos de método em aberto estão na Seção 10.

| Decisão | Alternativas consideradas | Por quê |
|---|---|---|
| Parar antes da Etapa 4 | Montar parâmetros com valores de referência das instruções | A Etapa 1 manda parar; usar os números de referência como dado seria inventar fonte |
| Classificar as 7 exceções do ONS por uma tabela explícita (`reclassificacao_usinas_v01.csv`) | Regras no código | Fica auditável, com justificativa e fonte em cada linha; a "Sol" (ES, 839.2 GWh) fica **pendente** até o SIGA |
| Leitores das fontes bloqueadas escritos agora, contra o formato documentado, com testes sintéticos | Esperar a rede | Adianta a Rodada 2b; todos marcados como "não validados com o arquivo real" |
| Teto sobre o total do insumo (todas as origens), com `grupo_teto` opcional | Teto por célula de origem | A instrução fala do insumo (ex.: "S04 … teto de 0.40 × VBP_CAR"); por célula o teto podia ser ultrapassado (achado da revisão) |
| Excedente de teto: padrão `demais_vbp`, opção `sem_teto` | Só uma das duas | A instrução diz "demais, na proporção do VBP" para S04/S19, mas não diz nada para o S05 (ver Seção 10) |
| Roteamento com vendedor não desagregado: fluxo ao grupo comprador ∝ VBP | Tratar como energia | Não há componentes para o S38 agregado; caso só aparece se D2 ≠ A |
| Latente por espelho: se o S38-RS original não compra um insumo, as origens seguem o total das compras fora do bloco (registrado na fonte de cada coeficiente) | 50/50; origens do espelho | Mantém a regra "pela coluna original do S38-RS" o mais próxima possível |
| E3 marcada como ALERTA "NÃO PRESERVA", mas verificada estritamente (só o S38 pode diferir, e exatamente pelo resíduo) | Desligar a checagem de CO₂e | Pedido da instrução + achado da revisão |
| CEMPRE: RB = Brasil − RS | Usar a composição nacional no RB | A instrução pede a composição por região; o RB é o complemento |
| Brutos > 20 MB em `dados/externos/brutos/`; menores em `dados/externos/<fonte>/`; `scripts/rodada02.py` procura nos dois | Tudo em `brutos/` | Regra 1 da Seção 2 |
| Restaurar `resultados/rodada01/` depois de re-rodar a Rodada 01 com o motor novo | Commitar as saídas regeneradas | "Nada é sobrescrito entre rodadas"; os valores são idênticos |
| Leitores escritos e revisados por subagentes (workflow), integrados e conferidos por mim; as revisões de SEEG, leilões e coleta falharam por limite de sessão e foram feitas por mim | Escrever tudo sozinho | Paralelismo; eu conferi o método de cada um contra as Seções 5.4 e 5.7 |

## 10. Pontos para o Francisco

1. **Rede (bloqueante).** A liberação de `*.gov.br`, `*.ons.org.br` e `seeg.eco.br` não chegou a este container: 403 do proxy em todos os testes (10:29–17:20 UTC). É provável que a mudança só valha para **sessões novas**. Abra uma sessão nova (ou reinicie o ambiente) e confira em Settings do ambiente → Network access que estes domínios estão na lista:
   - `dadosabertos.aneel.gov.br`, `www.gov.br`, `www2.aneel.gov.br`
   - `apisidra.ibge.gov.br`, `servicodados.ibge.gov.br`
   - `seeg.eco.br`
   - `www.epe.gov.br`, `www.sulgas.rs.gov.br`, `sulgas.rs.gov.br`
   - `comexstat.mdic.gov.br`, `api-comexstat.mdic.gov.br`

   Passo a passo: https://code.claude.com/docs/en/cloud-environments#network-access. Na sessão nova, `python scripts/rodada02_coleta.py` baixa tudo e `python scripts/rodada02.py` trata.
2. **S05 (petróleo e gás): para onde vai o excedente do teto do GN?** A Seção 6.8 diz "θ_r → GN (teto 0.60 × VBP_GN); 1 − θ_r → GAS", mas não diz o destino do excedente. O motor aceita `demais_vbp` (como S04/S19) ou `sem_teto` (só para o GAS). Com dados fictícios o teto do GN-RB é atingido, então a escolha deve importar.
3. **S03 + S09: um teto comum ou um teto para cada?** A instrução diz "100% BIO (teto de 0.40 × VBP_BIO)" para os dois juntos. O motor aceita as duas leituras (`grupo_teto`).
4. **SF6 entre TRA e DIS.** A instrução diz "SF6 → TRA e DIS de cada região", sem a proporção. Sugiro na proporção do VBP de TRA e DIS; confirme.
5. **Usina "Sol" (ES, 839.2 GWh).** O CEG tem código OF (outros fósseis). Fica pendente até o SIGA; se for gás de processo siderúrgico (ArcelorMittal Tubarão), vai para CAR.
6. **RB: âncora × GWh·preço (Seção 16).** A diferença é estrutural, não de dado: decida se a âncora continua (D3-A) com repartição por GWh × preço, como está.
7. **Branch padrão do GitHub.** Ela continua `claude/new-session-vyrfjo`. Pela regra 6 eu não alterei; para que a `main` seja a padrão: Settings → General → Default branch → `main`.
8. **Repositório público** (ponto 5 da Rodada 01): continua público.

## 11. Como reproduzir

```bash
pip install -r requirements.txt
python scripts/rodada02_coleta.py   # precisa de rede; hoje só o ONS baixa
python scripts/rodada02.py          # trata o ONS e lista o que falta
python -m pytest                    # 322 testes
```

## 12. Git

- Branch de trabalho: `claude/new-session-vyrfjo`, recriada a partir da `main` (merge do PR #1).
- Commits da rodada:
  - `d2dcf0a` R02-E1/E2: teste de acesso às fontes e geração 2019 por usina e subsetor (ONS)
  - `5ca712e` R02-E3: motor com 11 subsetores — roteamento por componentes, âncora por componentes, tetos, latentes por espelho, emissões E1/E2/E3 e testes T6–T8
  - `0550d77` R02-E2 (em andamento): leitores SIGA, leilões+IPCA e SEEG; rascunho do relatório; README e HISTORICO
  - R02-E2/E3: leitores CEMPRE e SEEG, script de coleta, casamento ONS×SIGA, dados_externos; correções da revisão adversarial do motor e testes de regressão
  - R02-E7: relatório da rodada (o commit que traz este arquivo)
- `main`: push direto (fast-forward) da branch para a `main`, como você pediu na mensagem de abertura. O resultado está na mensagem final da conversa.

## 13. Fontes de dados

| Fonte | URL | Data de acesso | Arquivo | Usada para | Acessível? |
|---|---|---|---|---|---|
| ONS — geração por usina, 2019 | https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/GERACAO_USINA-2_2019.parquet | 15/10/2026 | `dados/externos/brutos/ons/GERACAO_USINA-2_2019.parquet` (fora do git) | GWh por usina, região e subsetor | sim |
| ANEEL SIGA | https://dadosabertos.aneel.gov.br/…/siga-empreendimentos-geracao.csv | 15/10/2026 | — | classificar "Resíduos Industriais" | não |
| ANEEL leilões | https://dadosabertos.aneel.gov.br/…/resultado-leiloes-geracao.csv | 15/10/2026 | — | preços por fonte | não |
| IBGE SIDRA 1737 (IPCA) | https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all | 15/10/2026 | — | correção dos preços | não |
| ANEEL — RAP 2019-2020 | www.gov.br/aneel (documento a localizar) | 15/10/2026 | — | VBP da transmissão | não |
| Sulgás / ABEGÁS / ANP / MME | sulgas.rs.gov.br, abegas.org.br, gov.br/anp, gov.br/mme | 15/10/2026 | — | VBP e θ do gás | não |
| SEEG 13.0 | https://seeg.eco.br/wp-content/uploads/2025/12/Dados-nacionais-13.0.xlsx | 15/10/2026 | — | emissões E1/E2/E3 | não |
| IBGE SIDRA 6450 (CEMPRE) | https://apisidra.ibge.gov.br/values/t/6450/… | 15/10/2026 | — | ocupações e remunerações | não |
| EPE (Anuário, BEN) | www.epe.gov.br | 15/10/2026 | — | sistemas isolados, consumo específico, gás por setor | não |
| Comex Stat | api-comexstat.mdic.gov.br | 15/10/2026 | — | importações de energia | não |

## 14. Comparação com os valores de referência

**ONS (Seção 5.1; tolerância 0.5 GWh): 26/26 conferem.**

| Grupo | Item | Esperado | Obtido | Diferença | Confere |
|---|---|---|---|---|---|
| RS (com exceções) | HID | 14542.6 | 14542.55 | −0.05 | sim |
| RS | EOL | 5266.9 | 5266.92 | +0.02 | sim |
| RS | CAR | 2625.2 | 2625.22 | +0.02 | sim |
| RS | GN | 174.6 | 174.56 | −0.04 | sim |
| RS | BIO | 140.9 | 140.96 | +0.06 | sim |
| RS | PET / SOL / NUC | 0 / 0 / 0 | 0 / 0 / 0 | 0 | sim |
| RS | Total | 22750.2 | 22750.21 | +0.01 | sim |
| RB (rótulo ONS) | Hidráulica | 370796.7 | 370796.68 | −0.02 | sim |
| RB | Eólica | 48122.9 | 48122.86 | −0.04 | sim |
| RB | Carvão | 11338.7 | 11338.69 | −0.01 | sim |
| RB | Gás | 46474.0 | 46473.99 | −0.01 | sim |
| RB | Biomassa | 9271.9 | 9271.94 | +0.04 | sim |
| RB | Óleo (diesel + combustível) | 1974.3 | 1974.28 | −0.02 | sim |
| RB | Fotovoltaica | 4384.6 | 4384.56 | −0.04 | sim |
| RB | Nuclear | 16128.8 | 16128.76 | −0.04 | sim |
| RB | Resíduos Industriais | 9440.4 | 9440.38 | −0.02 | sim |
| RB | Total | 517932.3 | 517932.15 | −0.15 | sim |
| Importação | Itaipu 50 Hz | 24402.2 | 24402.23 | +0.03 | sim |
| RB Resíduos Ind. | Do Atlântico / Klabin / CSP / Suzano / CST / Sol | 2758.4 / 1777.1 / 1611.8 / 1255.4 / 1198.5 / 839.2 | 2758.36 / 1777.13 / 1611.78 / 1255.39 / 1198.49 / 839.23 | ≤ 0.04 | sim |

Tabela final dos "Resíduos Industriais" do RB: Do Atlântico, CSP e CST → CAR (gases siderúrgicos); Klabin e Suzano → BIO (licor negro); Sol → pendente (SIGA). No RS: CMPC → BIO; UTE Canoas → GN.

**Demais referências (5.4 preços e IPCA, 5.7 SEEG, 5.8 CEMPRE, 6.6 resíduos E1):** não comparáveis, porque as fontes estão bloqueadas. As funções de comparação já existem nos leitores (`comparar_com_referencia`).

**Ordem de grandeza da Seção 8.** Usei o GWh do ONS mais os preços e a RAP **de referência das instruções**, que não são dados coletados por mim e serviram só para conferência:
- **RS:** T = 25.7 bi × 6.06% = 1558.6; E = 5659.7 − 1558.6 = 4101.1 (≈ 4.10 bi ✓); DIS + GAS = 15283.0 ✓. GWh × preço = 4063.0 (razão 0.99), com HID 59.6%, EOL 22.5%, CAR 16.2%, GN 1.06% e BIO 0.70% ✓. A RAP do RS (1558.6) passa da RAP da CEEE-GT (749.75) ✓.
- **RB:** E = 96538.4 − 24141.4 = 72397.0 (≈ 72.4 bi) contra GWh × preço = 93891.1 (≈ 94 bi; razão 1.30). Explicação na Seção 16.

## 15. Parâmetros

Não gerados (Etapa 4 parada). Fica pronto para a rodada que tiver rede:
- **Dados:** GWh por região × subsetor (ONS) em `dados/intermediarios/geracao_2019_regiao_subsetor_v01.csv`.
- **Leitores:** prontos para preços (leilões + IPCA + nuclear), emissões (SEEG, com o PET do RS realocado), composição de emprego e salários (CEMPRE) e classificação de usinas (SIGA).
- **Motor:** aceita todas as regras da Seção 6.

Falta escrever `scripts/rodada02_parametros.py`, que vai gerar `parametros/especificacao_v01.yaml`, os `*_v01.csv` e `parametros/quadro_parametros_v01.xlsx`. As fontes dos valores de RAP, Sulgás, θ e gás por setor (5.5 e 5.6) são documentos, a ler quando a rede abrir.

## 16. Variantes

Não há números por subsetor: as variantes dependem dos parâmetros reais. O motor está pronto para todas.

**Preços.**
- **P1:** pesos da geração = MWh × preço de leilão de cada fonte.
- **P2:** preço igual para todas as fontes, ou seja, pesos = MWh. Só muda a repartição de E_r entre as fontes. O VBP total da geração (E_r), o TRA, o GAS e o DIS não mudam.

**Emissões** (regra `niveis`; o modo vai no YAML).
- **E1:** a geração fica com os níveis do SEEG; o SF6 vai a TRA/DIS; o resíduo da base NEREUS vai a DIS e GAS ∝ VBP. Preserva o total.
- **E2:** a base NEREUS inteira é repartida na proporção dos níveis do SEEG. As renováveis ficam com zero e as fósseis absorvem o excedente. Preserva o total.
- **E3:** só os níveis; o resíduo é descartado. Não preserva o total e é marcada assim.

Com os níveis de referência das instruções, o resíduo da E1 seria ≈ 1975.9 mil t no RS e ≈ 49689.8 mil t no RB, ou seja, 34% e 59% da base do S38. É isso que a E1 deixa em DIS e GAS.

**Âncora × GWh·preço no RB.** A âncora (E_r = vendas do S38 ao S38 − transmissão) dá preço implícito de 140.0 R$/MWh no RB, contra 180.3 no RS e cerca de 181 pela média dos leilões. Hipóteses para a diferença, sem conclusão:
1. Os preços de leilão (energia nova, corrigida pelo IPCA) superestimam a remuneração média do parque existente do RB, sobretudo das hidrelétricas antigas em regime de cotas, com tarifa que cobre basicamente O&M.
2. Parte da geração é vendida direto a consumidores livres (ACL) e por autoprodutores. Na MIP, isso aparece como venda do S38 a outros setores, e não S38→S38, e por isso fica fora da âncora.
3. Itaipu e as importações entram como energia comprada pelas distribuidoras.

No RS as duas medidas coincidem (razão 0.99), o que sugere que o efeito se concentra no RB. Não forcei o fechamento: com D3-A, a âncora define o total e o GWh × preço só reparte.

