# Instruções para o Claude Code — Rodada 03 (MIP v02 consolidada)

> **ESTE ARQUIVO É PARA O CLAUDE CODE.**
> Projeto: desagregação do S38 na MIP inter-regional RS × Restante do Brasil, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
> Data: 16/10/2026 · Base: a MIP v01 da Rodada 02b (`respostas/RODADA_02b_resposta.md`)
>
> **Git:** a branch padrão agora é a `main`. O Francisco apagou a `claude/new-session-vyrfjo`; nada se perdeu, porque a `main` tem todos os commits até `R02b-E7`. Trabalhe a partir da `main` e termine com push para a `main`.
> Convenção numérica: ponto decimal, sem separador de milhar.

---

## 0. O que esta rodada entrega

1. **MIP v02**: a v01 corrigida, sem EOB negativo e com a geração por fonte consistente com o SEEG.
2. Variantes de sensibilidade da v02 e o comparativo v01 × v02.
3. Um executor de cenários genérico, para a Rodada 4 só precisar definir os choques.
4. Relatório `respostas/RODADA_03_resposta.md`.

Todas as regras fixas das rodadas anteriores continuam valendo:
- original intocável (T1);
- nada sobrescrito: as saídas novas ficam em `resultados/rodada03/` e os parâmetros com sufixo `_v02`;
- nenhum dado inventado; toda hipótese marcada como hipótese;
- brutos grandes fora do git;
- fontes em `FONTES.md`.

---

## 1. Decisões do Francisco para a v02

Valem as decisões anteriores: D1 = C; D2, D3, D4 e D6 = A; D5 = E1; D7 = A. Somam-se a elas:

| Decisão | Escolha |
|---|---|
| **D8** — geração por fonte | Total do Brasil pelo **BEN 2020** (geração de serviço público por fonte, Tabela 5.4), a mesma base do SEEG; o RS pelo ONS; RB = Brasil − RS (Seção 2.1) |
| **D9** — EOB negativo | Pacote **(a) + (b) + (f) + (r)** (Seção 2.2) |
| **D10** — gás por comprador no RS | Estrutura de receita da **Sulgás** por segmento (Seção 2.3); o RB continua com o BEN nacional |

Se a mensagem de abertura do Francisco indicar outra opção, a mensagem prevalece.

---

## 2. Mudanças da v01 para a v02

### 2.1 Geração por fonte (D8)

- **Brasil** = BEN 2020, Tabela 5.4, centrais de serviço público (GWh), que você já transcreveu em `ben2020_tabela_5_4_v01.csv`:
  - HID 378450 · EOL 55954 · SOL 4978 · NUC 16129;
  - BIO 1840 (lenha + biodiesel + outras renováveis);
  - CAR 13823 · GN 47597;
  - PET 4769 (diesel + óleo combustível) + 405 (outras não renováveis) = **5174**. As outras não renováveis vão para o PET, com nota.
- **RS** = ONS, como na 02b (sem CMPC; Canoas → GN): HID 14542.6 · EOL 5266.9 · CAR 2625.2 · GN 174.6 · BIO 68.2 · SOL, PET e NUC = 0.
- **RB = Brasil − RS.** Referência (GWh): HID 363907.4 · EOL 50687.1 · SOL 4978 · BIO 1771.8 · CAR 11197.8 · GN 47422.4 · PET 5174 · NUC 16129.
- **Itaipu 50 Hz** continua como importação.
- **Por quê:** o SEEG (emissões E1) é construído sobre o BEN de serviço público. Com o mesmo total, GWh e emissões passam a cobrir exatamente o mesmo conjunto de usinas: inclui os sistemas isolados (diesel e também gás) e exclui a autoprodução industrial (bagaço, licor negro, gases siderúrgicos). Isso resolve os seus pontos 4 e 5 da 02b.
- O trabalho por usina do ONS continua valendo para o RS e como conferência. Mantenha `reconciliacao_epe` atualizado.

### 2.2 Pacote para o EOB negativo (D9)

Aplique **na ordem**:

**(a) Importações do S38-RS → 100% DIS.** O custo de gás da Sulgás em 2019 (≈ 679 R$ mi, Nota 22) já é coberto pela compra ao S05 (668.9). O "gás importado" pela regra nacional do Comex não existe no RS. No RB, a regra do Comex continua (energia elétrica → DIS; gás → GAS e GN por θ).

**(b) VBP do GAS-RB = preço médio × volume não térmico do RB.**
- Preço: o R$/m³ da Sulgás em 2019 (898.71 ÷ 646.362 = 1.390 R$/m³, já documentado).
- Se conseguir **reconferir no documento** as DFP 2019 de Comgás, CEG e Gasmig na CVM (receita líquida de venda de gás e volume), calcule o preço médio ponderado das quatro distribuidoras e use esse; reporte os dois.
- Substitui o fallback da margem de 0.25. Referência (com 1.39): ≈ 19421 R$ mi.

**(f) Combustíveis integrais e piso de VBP nas térmicas.**
- **Compras de combustível:**
  - S04 → 100% CAR;
  - S05 → GN por θ, sem teto (o restante vai ao GAS);
  - gás importado → GN por θ (só RB);
  - S19 → 100% PET onde o PET existe (no RS ele é latente, então o S19-RS vai aos demais, na proporção do VBP);
  - S03 + S09 → 100% BIO.
- **Piso:** VBP_k ≥ combustível_k ÷ κ, com **κ = 0.70** (participação máxima do combustível na receita; HIPÓTESE), para k ∈ {CAR, GN, PET, BIO}. Quando o piso for atingido, aumente o VBP_k até o piso e reduza os **demais subsetores de geração da mesma região** na proporção do VBP, de forma que E_r (âncora) não mude. Itere até estabilizar.
- Reporte os pisos atingidos e o R$/MWh resultante.
- Ordem de grandeza esperada: GN-RB ≈ 11000 R$ mi (≈ 230 R$/MWh) e PET-RB ≈ 4070 R$ mi (≈ 790 R$/MWh, compatível com o diesel dos sistemas isolados).

**(r) Reequilíbrio dos insumos não energéticos (RAS), com EOB mínimo.**
- **Insumos ajustados:** só os não energéticos — insumos intermediários de setores fora do bloco, exceto os combustíveis de (f); importações não energéticas; IPI, ICMS e outros impostos sobre produtos.
- **Ficam fixos:**
  - combustíveis;
  - bloco S38→S38 (energia e TUST);
  - importações de energia;
  - remunerações (CEMPRE);
  - impostos sobre a produção.
- **Totais de linha:** em cada região, o total de cada insumo ajustado na coluna original do S38 (preservado).
- **Alvos de coluna:** total ajustável_k = VBP_k − fixos_k − EOB_k*. O EOB-alvo é:
  - EOB_k* = η × VBP_k para quem estiver abaixo do mínimo, com **η = 0.10**;
  - para os demais, EOB_k* = EOB_k menos uma parte do déficit total, repartida na proporção da folga (EOB_k − η × VBP_k).

  Assim, a soma dos EOB da região não muda.
- **Execução:** RAS com o utilitário que você já tem; células zero continuam zero; latentes fora do ajuste.
- **Reporte:** EOB/VBP antes e depois, o valor movido por insumo e a convergência.

### 2.3 Gás por comprador no RS (D10)

Use a estrutura de receita da Sulgás em 2019 (Nota 18):
- indústria + cogeração (76.5%) → setores industriais na proporção do consumo industrial de gás do BEN;
- automotivo (16.0%) → S43 e famílias (GNV), como na v01;
- residencial + comercial (6.5%) → famílias e serviços (S41–S68), na proporção das compras ao S38.

Se a Nota 18 tiver outros segmentos, documente o tratamento. O RB continua com o BEN nacional.

### 2.4 Sem mudança

- RAP (24883.4, com a mesma ressalva de fonte secundária);
- preços P1 (BIO 206.05);
- E1;
- latentes por espelho;
- α = 0.5;
- G = 0;
- tetos de S04 e S03 + S09 substituídos por (f).

---

## 3. Produtos

1. **MIP v02 principal** (P1 + E1 + pacote D9) → `resultados/rodada03/MIP_RS_RB_2019_S38_11sub_v02.xlsx` + `_longo.csv`, no mesmo layout e com as mesmas abas extras.
2. **Variantes:**
   - P2 + E1, P1 + E2 e P1 + E3 (`.xlsx` + CSV longo);
   - **κ = 0.60** e **κ = 0.80** (só CSV longo + linha no quadro);
   - **η = 0.05** (só CSV longo + linha no quadro).
3. **`resultados/rodada03/quadro_subsetores_v02.xlsx`**, as mesmas colunas da v01 e mais:
   - aba `v01_x_v02` (VBP, R$/MWh, t/MWh, t/R$ mi, EOB/VBP e multiplicadores, por subsetor);
   - aba `reequilibrio_RAS` (o que foi movido);
   - aba `pisos_atingidos`.
4. **`resultados/rodada03/previa_multiplicadores_v02.xlsx`** ("PRÉVIA — NÃO É RESULTADO DO ARTIGO"):
   - multiplicadores do RS (produção e emissões, diretas e indiretas, incluindo latentes);
   - os 9 cenários com o choque do S38 repartido entre DIS e GAS (como na v01);
   - comparação com a v01.
5. **Executor de cenários** (`src/mip/cenarios.py` + `scripts/rodar_cenarios.py`):
   - lê um CSV de cenários (`cenario, regiao, setor, valor_R$mi`) e qualquer versão da MIP (original, v01, v02, variantes);
   - devolve as tabelas no formato do artigo:
     - impactos totais: produção induzida, CO₂e, IC e produção por mil t;
     - top-10 setores por emissão;
     - repartição RS × RB;
     - diretas × indiretas;
     - sensibilidade.
   - Teste: com o CSV dos 9 cenários de referência na MIP original, reproduz os valores da Rodada 01. Deixe um `parametros/cenarios_exemplo.csv` com esses 9 cenários.

---

## 4. Checagens e testes

- Todas as checagens anteriores, nas versões principais e em todas as variantes.
- **T2** com a especificação v02 (re-agregação exata, incluindo CO₂e na E1 e na E2).
- **T9 (novo):** na v02 principal, EOB ≥ η × VBP em todos os subsetores que produzem (tolerância 1e-6); soma dos EOB de cada região igual à da v01; RAS convergido.
- **T10 (novo):** geração por fonte: RS + RB = BEN, para cada fonte (tolerância 0.5 GWh).
- **T11 (novo):** o executor de cenários reproduz os 9 cenários da Rodada 01 na MIP original.
- Faixas de plausibilidade (E1, t CO₂e/MWh): CAR 0.8–1.6 · GN 0.35–0.65 · PET 0.65–1.1 · BIO ≤ 0.1 · demais = 0.
- **Novo alerta:** multiplicador de produção de um subsetor maior que 2.2, para pegar distorções como a do GN-RS na v01 (2.55).

---

## 5. Relatório

Salve em `respostas/RODADA_03_resposta.md`, com as 16 seções do modelo da Rodada 02 e mais uma: **"17. v01 × v02"**. Ela deve conter:
- o que mudou e o efeito de cada item (D8, (a), (b), (f), (r), D10) nos VBP, nos fatores de emissão, no EOB e nos multiplicadores do RS;
- uma tabela-resumo por subsetor.

Atualize também `respostas/HISTORICO.md` e o `README.md`. Push para a `main`. Na última mensagem, diga onde está o relatório, se tudo foi para a `main` e o que o Francisco precisa fazer.

---

## 6. Checklist final

- [ ] Trabalho a partir da `main`; push para a `main`
- [ ] D8: GWh por fonte = BEN (Brasil) − ONS (RS); T10 passando
- [ ] D9: (a), (b), (f) e (r) aplicados na ordem; T9 passando; nenhum EOB negativo na principal
- [ ] D10: gás por comprador no RS pela Sulgás
- [ ] Variantes (P2, E2, E3, κ, η) e quadro v01 × v02
- [ ] Executor de cenários com T11
- [ ] Prévia v02 marcada como PRÉVIA
- [ ] Relatório, `HISTORICO.md` e `README.md`
