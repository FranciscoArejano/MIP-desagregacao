# Instruções para o Claude Code — Rodada 02b (continuação da Rodada 02)

> **ESTE ARQUIVO É PARA O CLAUDE CODE.**
> Projeto: desagregação do S38 na MIP inter-regional RS × Restante do Brasil, 2019 · Repositório `FranciscoArejano/MIP-desagregacao`
> Data: 15/10/2026 · Base: `instrucoes/RODADA_02_instrucoes_CODE.md` + seu relatório `respostas/RODADA_02_resposta.md`
>
> A Rodada 02 parou na Etapa 1 porque a rede estava bloqueada. O Francisco mudou o acesso à rede do ambiente para **Full** (completo). Esta rodada **retoma a Rodada 02 de onde parou**, com as mudanças abaixo. Tudo o que não for alterado aqui segue valendo como está nas instruções da Rodada 02.
> Convenção numérica: ponto decimal, sem separador de milhar.

---

## 0. Primeiro passo (obrigatório): teste rápido de rede

Antes de qualquer outra coisa, teste o acesso a:
- `dadosabertos.aneel.gov.br`
- `apisidra.ibge.gov.br`
- `seeg.eco.br` (com User-Agent de navegador)
- `www.epe.gov.br`
- `www.gov.br`
- `comexstat.mdic.gov.br`

**Se ANEEL, SIDRA ou SEEG ainda derem 403 do proxy:** pare imediatamente. Salve `respostas/RODADA_02b_resposta.md` só com a tabela do teste (URL, status, horário), faça commit e push, e diga ao Francisco que o ambiente da sessão continua sem rede. Mencione o nome do ambiente da sessão, se conseguir vê-lo. Não gaste a sessão com outras tarefas.

Se só fontes **não obrigatórias** falharem (Comex Stat, Sulgás, ABEGÁS, EPE), siga e use os fallbacks da Rodada 02.

---

## 1. Respostas às suas perguntas (Seção 10 do relatório da Rodada 02)

| # | Pergunta | Resposta |
|---|---|---|
| 2 | Excedente do teto do S05 (gás → GN) | `sem_teto`: o excedente vai para o **GAS**. O gás que as térmicas não queimam é gás de revenda da distribuidora |
| 3 | Teto de S03 + S09 | **Um teto comum** (`grupo_teto`): 0.40 × VBP_BIO sobre a soma dos dois |
| 4 | SF6 entre TRA e DIS | Na proporção do VBP de TRA e DIS, em cada região |
| 5 | Usina "Sol" (ES) | Conferido no SIGA: `UTE.OF.ES.029273-7`, Fóssil / Outros Fósseis / "Calor de Processo – OF", 147.3 MW, 100% ArcelorMittal Brasil (PIE). É calor de processo siderúrgico. Ela entra na regra da Seção 2 (fora do S38) |
| 6 | Âncora × GWh·preço no RB | **Mantém D3-A:** a âncora define o total e o GWh × preço só reparte. Reporte o preço implícito por fonte e as hipóteses da sua Seção 16; não force o fechamento |

---

## 2. Mudança de escopo: usinas de resíduos industriais ficam fora do S38

**Motivo.** O SEEG que usamos para as emissões (categoria "Geração de eletricidade (serviço público)") não inclui as usinas que queimam subprodutos industriais: gases siderúrgicos, calor de processo e licor negro. O BEN e o SEEG contam essas usinas como **autoprodução** das indústrias. Se elas entrarem no VBP da geração e as emissões delas não entrarem, os coeficientes ficam incoerentes. Exemplo: o fator do CAR-RB cairia para cerca de 0.55 t/MWh, implausível para carvão.

**Regra.** Exclua da geração do S38 as 7 usinas que o ONS rotula "Resíduos Industriais":
- RB: Do Atlântico, CSP, CST, Sol, Klabin Celulose e Suzano Maranhão;
- RS: CMPC.

A geração delas é tratada como produção das indústrias (S27/S17) e só sai dos pesos da geração. Não mexa nos fluxos dessas indústrias na MIP. Registre os GWh excluídos e o motivo em `reclassificacao_usinas_v01.csv` (nova coluna `tratamento`).

**Novas referências (GWh; tolerância 0.5):**

| | HID | EOL | CAR | GN | BIO | PET | SOL | NUC | Total |
|---|---|---|---|---|---|---|---|---|---|
| RS | 14542.6 | 5266.9 | 2625.2 | 174.6 | 68.2 | 0 | 0 | 0 | 22677.5 |
| RB (SIN) | 370796.7 | 48122.9 | 11338.7 | 46474.0 | 9271.9 | 1974.3 | 4384.6 | 16128.8 | 508491.9 |

No RS, a BIO fica com São Sepé (43.7) e São Borja (24.5). No RB, a PET ainda recebe os sistemas isolados (Seção 3).

**Faixa de plausibilidade do CAR** (Seção 9a da Rodada 02): ajuste para **0.8–1.6 t CO₂e/MWh**. O carvão do SIN fica perto de 0.86 pelo SEEG.

---

## 3. Sistemas isolados: agora obrigatório

As emissões de diesel e óleo combustível do SEEG no RB (3958.6 mil t, mais 333.0 de gás de refinaria "não alocado") incluem os sistemas isolados. Sem a geração deles, o fator do PET-RB fica em cerca de 2 t/MWh, o que é implausível.

Ordem de busca:
1. **EPE**, Anuário Estatístico de Energia Elétrica 2020 (ano-base 2019): geração dos sistemas isolados por fonte. Some ao RB.
2. Se não houver: **EPE**, BEN 2020, geração de serviço público a partir de derivados de petróleo (Brasil). PET-RB = nacional − PET-RS (0).
3. Se nenhum dos dois: registre, siga com o ONS e marque o fator do PET-RB como superestimado.

---

## 4. Reconciliação com o EPE (desejável)

Compare a geração de serviço público por fonte no Brasil (EPE: Anuário 2020 ou BEN 2020) com a soma RS + RB que você montou (ONS + isolados − autoprodução). Reporte a diferença por fonte. É só conferência; não troque a fonte principal.

---

## 5. Continuação: o que fazer depois do teste de rede

Siga a Rodada 02 a partir de onde parou:

1. **Etapa 2:** colete e trate as fontes 5.2 a 5.10, já com as mudanças das Seções 2 e 3. Valide os leitores com os arquivos reais e compare com os valores de referência da Rodada 02:
   - preços e IPCA;
   - SEEG;
   - CEMPRE;
   - RAP.
2. **Etapa 4:** escreva `scripts/rodada02_parametros.py` → `parametros/especificacao_v01.yaml`, `parametros/*_v01.csv` (com coluna `fonte`) e `parametros/quadro_parametros_v01.xlsx`. Incorpore as respostas da Seção 1.
3. **Etapa 5:** gere a MIP v01 principal (P1 + E1) e as variantes P2 + E1, P1 + E2 e P1 + E3, com todas as checagens. O T2 com a especificação real precisa passar.
4. **Etapa 6:**
   - **a) obrigatória:** `resultados/rodada02/quadro_subsetores_v01.xlsx`;
   - **b) opcional:** prévia de multiplicadores e os 9 cenários na v01 (marcar "PRÉVIA").
5. **Etapa 7:** relatório (Seção 6 abaixo).

As regras fixas da Rodada 02 continuam:
- original intocável;
- nada sobrescrito;
- nenhum dado inventado;
- brutos grandes fora do git;
- fontes em `FONTES.md`;
- não alterar a branch padrão nem a visibilidade do repositório.

---

## 6. Relatório desta rodada

Salve em **`respostas/RODADA_02b_resposta.md`**. Não sobrescreva o `RODADA_02_resposta.md`.

Use as mesmas 16 seções do relatório da Rodada 02 e acrescente uma 17ª: **"Mudanças da 02b"**, com o efeito da exclusão das usinas de autoprodução e dos sistemas isolados nos GWh, nos VBP e nos fatores de emissão.

Atualize também `respostas/HISTORICO.md` e o `README.md`. No fim, faça push para a `main`, como na Rodada 02, e diga na última mensagem:
- onde está o relatório;
- se tudo foi para a `main`;
- o que o Francisco precisa fazer.

---

## 7. Checklist final

- [ ] Teste de rede feito primeiro (e parada imediata se ANEEL, SIDRA ou SEEG falharem)
- [ ] Respostas da Seção 1 aplicadas
- [ ] Usinas de autoprodução fora da geração (Seção 2) e sistemas isolados somados (Seção 3)
- [ ] Leitores validados com os arquivos reais; valores de referência reproduzidos ou divergências explicadas
- [ ] Parâmetros com fonte; MIP v01 e variantes com checagens; T1–T8 passando
- [ ] `quadro_subsetores_v01.xlsx` gerado
- [ ] `respostas/RODADA_02b_resposta.md` salvo; `HISTORICO.md` e `README.md` atualizados; push para a `main`
