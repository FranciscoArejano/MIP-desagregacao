# Apêndice B — Nota técnica da desagregação do S38

Este apêndice descreve, na ordem em que foram executados, todos os passos da desagregação do setor S38 (energia elétrica, gás natural e outras utilidades) da matriz inter-regional de insumo-produto Rio Grande do Sul (RS) × Restante do Brasil (RB) de 2019 (NEREUS, [2025?]; Haddad et al., 2025), com os parâmetros, as fontes de dados, as hipóteses, as checagens e as variantes. Os valores por subsetor estão na Tabela A3; as fontes, na Tabela A4; os parâmetros e as hipóteses, na Tabela A5; a robustez, na Tabela A6; o diagnóstico da conta-satélite de emissões, na Tabela A7; e os testes de consistência, na Tabela A8. O procedimento foi implementado em Python, com os parâmetros em arquivos separados do código e a fonte registrada em cada parâmetro.

## B.1 Notação e restrições de agregação

Mantém-se a notação do artigo: $Z_{ij}$ são os fluxos intermediários, $X_j$ o valor bruto da produção (VBP), $A = Z\,\mathrm{diag}(X)^{-1}$ a matriz de coeficientes técnicos, $L = (I - A)^{-1}$ a inversa de Leontief, $Y$ e $\Delta Y$ a demanda final e o choque, e $e_i = CO2_i / X_i$ a intensidade de emissão. Acrescentam-se a região, $r, q \in \{\mathrm{RS}, \mathrm{RB}\}$, e o subsetor, $k, l \in K = G \cup \{\mathrm{TRA}, \mathrm{DIS}, \mathrm{GAS}\}$, com $G = \{\mathrm{HID}, \mathrm{EOL}, \mathrm{SOL}, \mathrm{BIO}, \mathrm{CAR}, \mathrm{GN}, \mathrm{PET}, \mathrm{NUC}\}$ o conjunto dos subsetores de geração. Os 11 subsetores são os do Quadro 2 (subseção 3.x): geração hidrelétrica, eólica, solar fotovoltaica, a biomassa, a carvão mineral, a gás natural, a derivados de petróleo e nuclear; transmissão de energia elétrica; distribuição e comercialização de energia elétrica; e gás canalizado e outras utilidades. A mesma lista vale para as duas regiões. Os índices $i, j$ designam os setores fora do S38, $d$ as colunas da demanda final e $h$ as linhas dos insumos primários (importações, impostos sobre produtos, remunerações, impostos sobre a produção e excedente operacional bruto, EOB).

A desagregação seguiu o princípio de preservar a matriz original (Wolsky, 1984; Lindner, Legault e Guan, 2012): a soma dos subsetores de cada região reproduz cada célula da matriz e das contas-satélite. As restrições de agregação, que repetem as Equações (15) a (19) do corpo do artigo, são, para $r, q \in \{\mathrm{RS}, \mathrm{RB}\}$ e $i, j \neq \mathrm{S38}$:

$$\sum_{k \in K} Z_{(r,k),(q,j)} = Z_{(r,\mathrm{S38}),(q,j)}, \qquad \sum_{k \in K} Y_{(r,k),d} = Y_{(r,\mathrm{S38}),d} \qquad \text{(B.1)}$$

$$\sum_{k \in K} Z_{(q,i),(r,k)} = Z_{(q,i),(r,\mathrm{S38})}, \qquad \sum_{k \in K} V_{h,(r,k)} = V_{h,(r,\mathrm{S38})} \qquad \text{(B.2)}$$

$$\sum_{k \in K} \sum_{l \in K} Z_{(r,k),(q,l)} = Z_{(r,\mathrm{S38}),(q,\mathrm{S38})} \qquad \text{(B.3)}$$

$$\sum_{k \in K} X_{r,k} = X_{r,\mathrm{S38}} \qquad \text{(B.4)}$$

$$\sum_{k \in K} CO2_{r,k} = CO2_{r,\mathrm{S38}} \qquad \text{(B.5)}$$

As Equações (B.1) a (B.4) valem em todas as versões; a (B.5) vale nas versões de emissões E1 (principal) e E2. Na variante E3, as emissões do S38 deixam de reproduzir a base (diferem pelo resíduo); na E4, só o total da economia é preservado (Seção B.9). As mesmas restrições valem para as demais contas-satélite (ocupações, água e energia). Lenzen (2011) mostra que, em análises ambientais, desagregar a tabela econômica é preferível a agregar a conta ambiental; por isso, desagregaram-se as linhas, as colunas e os insumos primários, e não só as intensidades de emissão.

## B.2 Ordem dos passos

O procedimento executou os passos abaixo, nesta ordem, para as duas regiões:

1. validação dos parâmetros (subsetores, regras e coerência entre elas);
2. VBP de cada subsetor pelos componentes do bloco S38 × S38 (Seção B.3), com as participações da geração pelos GWh e pelos preços (Seção B.4);
3. compras de fornecedores fora do bloco, coluna a coluna (Seção B.6);
4. bloco S38 × S38, roteado por componentes (Seção B.5);
5. vendas a compradores fora do bloco e à demanda final, linha a linha, com conciliação RAS (Seção B.6);
6. insumos primários e contas-satélite, com o EOB como resíduo de cada coluna (Seções B.7 e B.9);
7. piso do VBP das térmicas (Seção B.4): os passos 2 a 6 são repetidos, sem o reequilíbrio, até que os VBP se estabilizem;
8. reequilíbrio dos insumos não energéticos por RAS, com EOB mínimo (Seção B.8);
9. colunas dos subsetores latentes, com o ajuste da tarifa de uso da transmissão (Seção B.10);
10. na variante E4, realocação de parte das emissões do resíduo (Seção B.9);
11. verificação (Seção B.12).

## B.3 Produção: componentes do bloco S38 × S38

O VBP da geração foi ancorado nas vendas do S38 ao próprio S38. Para cada região vendedora $r$, as vendas do S38 de $r$ ao S38 das duas regiões são

$$F_r = \sum_{q} Z_{(r,\mathrm{S38}),(q,\mathrm{S38})}, \qquad F_{rq} = Z_{(r,\mathrm{S38}),(q,\mathrm{S38})} \qquad \text{(B.6)}$$

Supôs-se que $F_r$ se compõe de três componentes: a energia vendida pela geração à distribuição, $E_r$; os serviços de transmissão, $T_r$; e o gás vendido pelas distribuidoras de gás às térmicas, $G_r$. Adotou-se $G_r = 0$ nas duas regiões (HIPÓTESE: as térmicas compram o gás diretamente da extração de petróleo e gás ou do exterior, e não das distribuidoras). O VBP da geração da região é, então, o resíduo do bloco:

$$E_r = F_r - T_r - G_r = \sum_{q} Z_{(r,\mathrm{S38}),(q,\mathrm{S38})} - T_r - G_r \qquad \text{(B.7)}$$

que é a mesma Equação (20) do corpo do artigo com $G_r = 0$. Os VBP da transmissão ($T_r$) e do gás canalizado ($X_{r,\mathrm{GAS}}$) vêm de fontes externas, e a distribuição fica com o resíduo do VBP do S38:

$$X_{r,\mathrm{DIS}} = X_{r,\mathrm{S38}} - E_r - T_r - X_{r,\mathrm{GAS}} \qquad \text{(B.8)}$$

(Equação (23) do corpo do artigo). O procedimento exige $E_r \geq 0$ e $X_{r,\mathrm{DIS}} > 0$; as duas condições foram satisfeitas na versão final e em todas as variantes.

**Transmissão.** O VBP da transmissão do Brasil, $T^{\mathrm{BR}}$, é o total dos "Encargos de Uso" faturados pelo Operador Nacional do Sistema Elétrico no ano civil de 2019, R\$ 22.935,6 milhões, obtido dos relatórios de síntese da apuração mensal dos serviços e encargos da transmissão: o acumulado do ciclo 2018-2019 até junho de 2019, menos o acumulado do mesmo ciclo até dezembro de 2018, mais o acumulado do ciclo 2019-2020 até dezembro de 2019 (ONS, 2019a; ONS, 2019b; ONS, 2020). O valor está sem PIS/Pasep e Cofins, que são impostos sobre produtos, o que é coerente com o VBP a preços básicos, e inclui o orçamento do ONS. A repartição entre as regiões seguiu a participação de cada uma no VBP do S38 (HIPÓTESE):

$$T_r = T^{\mathrm{BR}} \, \frac{X_{r,\mathrm{S38}}}{X_{\mathrm{RS},\mathrm{S38}} + X_{\mathrm{RB},\mathrm{S38}}} \qquad \text{(B.9)}$$

o que dá R\$ 1.390,9 milhões no RS e R\$ 21.544,7 milhões no RB. Na variante rap_media, $T^{\mathrm{BR}}$ é a receita anual permitida (RAP) de 2019, média dos ciclos 2018-2019 (ANEEL, 2018a) e 2019-2020 (ANEEL, 2019), este último pelo total divulgado em fonte secundária (CanalEnergia, 2019): R\$ 24.883,4 milhões, repartidos pela mesma Equação (B.9).

**Gás canalizado.** No RS, o VBP é a receita líquida de venda de gás e serviços da Sulgás em 2019, R\$ 898,7 milhões (Sulgás, 2020). No RB, adotou-se o preço médio da Sulgás, $\pi^{\mathrm{S}}$ (receita líquida dividida pelo volume vendido sem o segmento "serviço"), aplicado ao volume não térmico das distribuidoras do RB, $W^{\mathrm{nt}}_{\mathrm{RB}}$, isto é, o total das distribuidoras sem o segmento termelétrico menos a Sulgás (Brasil, 2020):

$$X_{\mathrm{RB},\mathrm{GAS}} = \pi^{\mathrm{S}} \, W^{\mathrm{nt}}_{\mathrm{RB}} \qquad \text{(B.10)}$$

o que dá R\$ 19.421,0 milhões (HIPÓTESE: o preço da Sulgás representa o das demais distribuidoras). Na variante gas4dist, $\pi^{\mathrm{S}}$ foi substituído pelo preço médio ponderado pelo volume de quatro distribuidoras (Sulgás, Comgás, CEG e Gasmig), com a receita líquida de venda de gás não térmica e o volume correspondente das demonstrações financeiras de 2019 (Sulgás, 2020; Comgás, [2020]; CEG, [2020]; Gasmig, [2020]); o VBP resultante está na Tabela A5. Como o VBP do S38 é fixo, a diferença vai para a distribuição pela Equação (B.8).

## B.4 Produção: participação das fontes na geração

O VBP da geração de cada região, $E_r$, foi repartido entre as fontes pelo produto da energia gerada em 2019, $Q_{r,g}$ (GWh), pelo preço médio de cada fonte, $p_g$, como em Peters (2016) e Lindner, Legault e Guan (2013):

$$X^{0}_{r,g} = E_r \, \frac{Q_{r,g} \, p_g}{\sum_{h \in G} Q_{r,h} \, p_h}, \qquad g \in G \qquad \text{(B.11)}$$

(Equação (21) do corpo do artigo). A energia gerada é a do serviço público. No RS, veio da geração por usina do ONS em 2019, sem a autoprodução e com a usina térmica de Canoas classificada como gás natural (ONS, [2026]), num total de 22.677,5 GWh. No RB, é a diferença entre a geração do Brasil por fonte no Balanço Energético Nacional (EPE, 2020, Tabela 5.4) e a do RS, num total de 501.267,5 GWh; por construção, RS + RB reproduz o total do Brasil em cada fonte. Na correspondência com o balanço, os derivados de petróleo reúnem o óleo diesel, o óleo combustível e as outras não renováveis, e a biomassa reúne a lenha, o biodiesel e as outras renováveis. A geração solar fotovoltaica e a geração a derivados de petróleo não tinham produção no RS em 2019, e a nuclear só existe no RB; esses subsetores do RS ficaram com VBP zero (Seção B.10).

Os preços $p_g$ (preços P1) são os preços médios dos leilões de geração por fonte, ponderados pela energia negociada (ANEEL, [2026]), corrigidos pelo IPCA para a média de 2019 (IBGE, 2026). Para a geração nuclear, adotou-se a tarifa de Angra 1 e 2 homologada para 2019 (ANEEL, 2018b). Supôs-se que os preços relativos dos leilões representam os preços relativos da produção da matriz (HIPÓTESE); como $E_r$ é fixo, só os preços relativos importam. Os preços implícitos resultantes, $X_{r,g} / Q_{r,g}$, estão na Tabela A3. Na variante P2 (preços iguais), os pesos da Equação (B.11) são só os GWh.

**Piso do VBP das térmicas.** Nas térmicas, a Equação (B.11) pode dar um VBP menor que o combustível comprado. Definiu-se o combustível de cada térmica, $C_{r,g}$, como as suas compras, de todas as origens, aos setores fornecedores do combustível correspondente: extração de carvão mineral e de minerais não metálicos, na geração a carvão; extração de petróleo e gás, mais as importações de gás, na geração a gás natural; refino de petróleo e coquerias, na geração a derivados de petróleo; e produção florestal, pesca e aquicultura (lenha) e fabricação e refino de açúcar (bagaço), na biomassa. Impôs-se o piso

$$X_{r,g} \geq \frac{C_{r,g}}{\kappa}, \qquad \kappa = 0,70 \qquad \text{(B.12)}$$

(HIPÓTESE: o combustível não passa de $\kappa$ do VBP; Equação (22) do corpo do artigo). Quando o piso de uma fonte é atingido, ela sobe ao piso e as demais fontes da mesma região, $g \notin P_r$, caem na proporção do VBP inicial, de modo que $E_r$ não mude:

$$X_{r,g} = \frac{C_{r,g}}{\kappa}, \quad g \in P_r; \qquad X_{r,g} = X^{0}_{r,g} \, \frac{E_r - \sum_{h \in P_r} C_{r,h}/\kappa}{\sum_{h \notin P_r} X^{0}_{r,h}}, \quad g \notin P_r \qquad \text{(B.13)}$$

em que $P_r$ é o conjunto das fontes no piso. Como o combustível de cada coluna depende das regras de coluna (Seção B.6), a desagregação foi repetida, sem o reequilíbrio da Seção B.8, até que os VBP se estabilizassem, sempre a partir dos VBP iniciais da Equação (B.11). Na versão final, o piso foi atingido pela geração a gás natural das duas regiões e pela geração a derivados de petróleo do RB; nessas três, o combustível é exatamente $\kappa$ do VBP. O motor prevê uma extensão do piso para garantir a viabilidade do reequilíbrio, que não foi necessária nem usada na versão final e nas variantes. Na variante k060, $\kappa$ = 0,60.

## B.5 Bloco S38 × S38: roteamento por componentes

Dentro do bloco, cada componente de $r$ foi enviado à região compradora $q$ na proporção $F_{rq}/F_r$ das vendas originais, o que preserva os quatro fluxos regionais do bloco (RS→RS, RS→RB, RB→RS e RB→RB) e a Equação (B.3). A energia de cada fonte de $r$ vai à distribuição de $q$:

$$Z_{(r,g),(q,\mathrm{DIS})} = E_r \, \frac{F_{rq}}{F_r} \, \frac{X_{r,g}}{\sum_{h \in G} X_{r,h}}, \qquad g \in G \qquad \text{(B.14)}$$

A transmissão de $r$ é paga em uma fração $\alpha$ = 0,5 pela distribuição e em $1 - \alpha$ pela geração, de acordo com o rateio inicial dos encargos de uso entre consumo e geração (ANEEL, 2013). Entre as fontes de $q$, a parcela da geração foi repartida pela energia gerada no Sistema Interligado Nacional (SIN), $M_{q,g}$:

$$Z_{(r,\mathrm{TRA}),(q,\mathrm{DIS})} = \alpha \, T_r \, \frac{F_{rq}}{F_r}, \qquad Z_{(r,\mathrm{TRA}),(q,g)} = (1 - \alpha) \, T_r \, \frac{F_{rq}}{F_r} \, \frac{M_{q,g}}{\sum_{h \in G} M_{q,h}} \qquad \text{(B.15)}$$

(Equação (24) do corpo do artigo). O peso $M_{q,g}$ é o menor valor entre os GWh da Seção B.4 e os GWh da geração por usina do ONS no SIN, sem a autoprodução e sem Itaipu (ONS, [2026]); a geração dos sistemas isolados e os subsetores sem produção não pagam a tarifa de uso da transmissão (TUST). Com essa regra, a TUST por MWh é a mesma para todas as fontes de uma região:

$$\tau_q = \frac{\sum_{r} Z_{(r,\mathrm{TRA}),(q,g)}}{M_{q,g}}, \qquad \text{igual para todo } g \text{ com } M_{q,g} > 0 \qquad \text{(B.16)}$$

No RS, $\tau_{\mathrm{RS}}$ = 32,41 R\$/MWh. Com $G_r = 0$, o gás canalizado não vende dentro do bloco. Fora dessas células, o bloco é zero: a geração não vende à transmissão nem a outras fontes, e a distribuição e o gás canalizado não vendem ao S38.

## B.6 Vendas (linhas) e compras (colunas) fora do bloco

**Linhas.** A geração e a transmissão não vendem fora do bloco nem à demanda final: toda a energia elétrica comprada pelos demais setores e pela demanda final sai da distribuição. A distribuição e o gás canalizado dividem cada célula de vendas do S38 a um comprador fora do bloco. O gás canalizado só vende na própria região. No RS, a repartição do gás entre os compradores seguiu as vendas da Sulgás por segmento em 2019 (Sulgás, 2020): indústria e cogeração aos setores industriais, na proporção do consumo industrial de gás de cada ramo no Balanço Energético Nacional (EPE, 2020, sem o consumo final não energético) e, dentro do ramo, na proporção das compras ao S38; o segmento automotivo ao transporte terrestre e às famílias; o residencial e o comercial às famílias e aos setores de comércio e serviços, na proporção das compras ao S38; e o segmento "serviço" ao refino de petróleo e coquerias (HIPÓTESE: transporte do gás da refinaria do RS). No RB, a repartição seguiu o consumo de gás por setor do Balanço Energético Nacional, sem o setor energético (EPE, 2020), aplicado ao VBP do gás canalizado do RB e, dentro de cada setor do balanço, na proporção das compras ao S38 de cada setor da matriz. Supôs-se o mesmo preço por unidade de gás para todos os compradores (HIPÓTESE). Sendo $\gamma_{r,j}$ a participação do comprador $j$ nas vendas de gás de $r$, as vendas iniciais do gás canalizado e da distribuição são

$$Z^{0}_{(r,\mathrm{GAS}),(r,j)} = \min\!\left(\gamma_{r,j} \, X_{r,\mathrm{GAS}},\; \bar{s} \, Z_{(r,\mathrm{S38}),(r,j)}\right), \qquad Z^{0}_{(r,\mathrm{DIS}),(q,j)} = Z_{(r,\mathrm{S38}),(q,j)} - Z^{0}_{(r,\mathrm{GAS}),(q,j)} \qquad \text{(B.17)}$$

com $Z^{0}_{(r,\mathrm{GAS}),(q,j)} = 0$ para $q \neq r$ e com o teto $\bar{s}$ = 0,90 (HIPÓTESE): o gás de cada comprador não passa dessa fração das suas compras ao S38, para que nenhum comprador fique sem eletricidade. O excedente de quem atinge o teto vai aos demais compradores do mesmo grupo (os segmentos da Sulgás no RS; a indústria e cada um dos demais setores do balanço no RB) e, se o grupo inteiro estiver no teto, aos demais compradores da região, na proporção do alvo. A discrepância estatística foi repartida entre a distribuição e o gás canalizado na proporção do VBP; as exportações e o investimento ficaram com a distribuição.

Como essas regras não fecham, em geral, o VBP de cada subsetor, as linhas de cada região foram conciliadas por ajuste biproporcional (RAS; Lahr e de Mesnard, 2004; Miller e Blair, 2022):

$$Z_{(r,k),c} = \rho_k \, Z^{0}_{(r,k),c} \, \sigma_c, \qquad \sum_{c} Z_{(r,k),c} = X_{r,k} - \sum_{q} \sum_{l \in K} Z_{(r,k),(q,l)}, \qquad \sum_{k \in K} Z_{(r,k),c} = Z_{(r,\mathrm{S38}),c} \qquad \text{(B.18)}$$

em que $c$ percorre os compradores fora do bloco e as colunas da demanda final, $\rho_k$ e $\sigma_c$ são os fatores de linha e de coluna, as vendas no bloco (Seção B.5) ficam fixas e as células de valor negativo (discrepância estatística) também. Os zeros, como as vendas da geração fora do bloco, continuam zero.

**Colunas.** A regra-padrão para as compras de cada fornecedor fora do bloco foi a proporção do VBP (Wolsky, 1984). Os combustíveis foram atribuídos integralmente à fonte correspondente: as compras à extração de carvão mineral e de minerais não metálicos, à geração a carvão; as compras à produção florestal, pesca e aquicultura e à fabricação e refino de açúcar, à biomassa; as compras ao refino de petróleo e coquerias, no RB, à geração a derivados de petróleo e, no RS, onde essa geração é latente, aos demais subsetores na proporção do VBP. As compras à extração de petróleo e gás (S05, na equação) foram repartidas entre a geração a gás natural e o gás canalizado:

$$Z_{(q,\mathrm{S05}),(r,\mathrm{GN})} = \theta_r \, Z_{(q,\mathrm{S05}),(r,\mathrm{S38})}, \qquad Z_{(q,\mathrm{S05}),(r,\mathrm{GAS})} = (1 - \theta_r) \, Z_{(q,\mathrm{S05}),(r,\mathrm{S38})} \qquad \text{(B.19)}$$

em que $\theta_r$ é a participação das térmicas no gás comprado pelo S38 da região. No RB, $\theta_{\mathrm{RB}}$ é o consumo de gás na geração elétrica do Brasil, menos o das térmicas do RS, dividido pela soma das distribuidoras e dos outros agentes, menos a Sulgás e as térmicas do RS (Brasil, 2020). No RS, onde não se encontrou o volume da térmica de Canoas, $\theta_{\mathrm{RS}}$ é o volume térmico, estimado pela geração a gás do RS vezes um consumo específico de 0,20 m³/kWh (HIPÓTESE), dividido pela soma desse volume com o volume da Sulgás sem o segmento "serviço".

As importações do S38 são de energia (energia elétrica e gás natural) e foram atribuídas como compras de energia. No RS, foram todas para a distribuição, porque o custo do gás da Sulgás já é coberto pelas compras à extração de petróleo e gás. No RB, foram repartidas pela participação de cada produto no valor FOB das importações brasileiras de 2019 (Brasil, [2026]): a energia elétrica (NCM 2716.00.00) à distribuição; o gás natural (NCM 2711.11.00 e 2711.21.00) à geração a gás natural e ao gás canalizado, na proporção $\theta_{\mathrm{RB}}$ e $1 - \theta_{\mathrm{RB}}$:

$$V_{\mathrm{imp},(\mathrm{RB},\mathrm{DIS})} = s^{\mathrm{el}} \, V_{\mathrm{imp},(\mathrm{RB},\mathrm{S38})}, \quad V_{\mathrm{imp},(\mathrm{RB},\mathrm{GN})} = (1 - s^{\mathrm{el}}) \, \theta_{\mathrm{RB}} \, V_{\mathrm{imp},(\mathrm{RB},\mathrm{S38})}, \quad V_{\mathrm{imp},(\mathrm{RB},\mathrm{GAS})} = (1 - s^{\mathrm{el}}) (1 - \theta_{\mathrm{RB}}) \, V_{\mathrm{imp},(\mathrm{RB},\mathrm{S38})} \qquad \text{(B.20)}$$

em que $s^{\mathrm{el}}$ é a participação da energia elétrica no valor FOB das importações desses três produtos.

## B.7 Insumos primários e contas-satélite

Os impostos sobre produtos (IPI, ICMS e outros) foram repartidos na proporção das compras intermediárias de cada subsetor, domésticas e importadas:

$$V_{h,(r,k)} = V_{h,(r,\mathrm{S38})} \, \frac{\sum_{i} Z_{i,(r,k)} + V_{\mathrm{imp},(r,k)}}{\sum_{l \in K} \left( \sum_{i} Z_{i,(r,l)} + V_{\mathrm{imp},(r,l)} \right)} \qquad \text{(B.21)}$$

em que a soma em $i$ inclui todas as linhas da matriz, inclusive as do bloco. Os impostos sobre a produção foram repartidos na proporção do VBP.

As remunerações e as ocupações seguiram a repartição entre geração, transmissão, distribuição e gás do Cadastro Central de Empresas de 2019 (IBGE, 2021), com os dados sigilosos do RS estimados por diferença e pela proporção nacional, e o RB como Brasil menos RS. Dentro da geração, a parcela foi repartida na proporção do VBP líquido do combustível (HIPÓTESE: o combustível é um repasse e não exige mão de obra proporcional):

$$W_{r,g} = W_{r,\mathrm{S38}} \, \omega_{r}^{\mathrm{ger}} \, \frac{X_{r,g} - C_{r,g}}{\sum_{h \in G} \left( X_{r,h} - C_{r,h} \right)}, \qquad g \in G \qquad \text{(B.22)}$$

em que $W$ são as remunerações (ou as ocupações) e $\omega_{r}^{\mathrm{ger}}$ a participação da geração no Cadastro Central de Empresas; a transmissão, a distribuição e o gás canalizado recebem as suas participações diretamente. A conta-satélite de energia do S38 foi atribuída inteiramente às térmicas (inclusive a nuclear, no RB), na proporção do produto dos GWh pelo consumo específico de cada fonte (EPE, 2020, Tabela 5.4); a de água, também às térmicas, na proporção dos GWh (HIPÓTESE).

O EOB de cada subsetor é o resíduo que fecha a coluna:

$$EOB_{r,k} = X_{r,k} - \sum_{i} Z_{i,(r,k)} - V_{\mathrm{imp},(r,k)} - \sum_{h \in H^{p}} V_{h,(r,k)} - W_{r,k} - V_{\mathrm{ip},(r,k)} + \frac{X_{r,k}}{X_{r,\mathrm{S38}}} \, \varepsilon_r \qquad \text{(B.23)}$$

em que $H^{p}$ são os impostos sobre produtos, $V_{\mathrm{ip}}$ os impostos sobre a produção e $\varepsilon_r$ o resíduo contábil da coluna original do S38 (a diferença entre o EOB publicado e o EOB que fecha a coluna), repartido pelo VBP. O valor adicionado é a soma de remunerações, EOB e impostos sobre a produção.

## B.8 Reequilíbrio dos insumos não energéticos (EOB mínimo)

As regras anteriores podem deixar EOB negativo nas térmicas e no gás canalizado, cujos custos de combustível são altos. Para evitá-lo, os insumos não energéticos de cada região foram ajustados por RAS (Lahr e de Mesnard, 2004), com a restrição

$$EOB_{r,k} \geq \eta \, X_{r,k}, \qquad \eta = 0,10 \qquad \text{(B.24)}$$

(HIPÓTESE; Equação (25) do corpo do artigo). São ajustáveis as compras a setores fora do bloco, exceto as dos setores fornecedores de combustível (Seção B.4), e os impostos sobre produtos. Ficam fixos o bloco, os combustíveis, as importações (todas de energia), as remunerações e os impostos sobre a produção. O EOB-alvo de quem está abaixo do mínimo é $\eta X_{r,k}$; o déficit total, $D_r$, é coberto pelos demais subsetores com produção, na proporção da folga $f_{r,k} = EOB_{r,k} - \eta X_{r,k}$:

$$EOB^{*}_{r,k} = EOB_{r,k} - D_r \, \frac{f_{r,k}}{\sum_{l} f_{r,l}} \qquad \text{(B.25)}$$

O RAS foi aplicado à matriz $N_r$ (insumos ajustáveis × subsetores da região), com os totais de linha preservados (o total de cada insumo comprado pelo S38 da região) e os totais de coluna iguais aos originais menos a variação do EOB:

$$\sum_{k \in K} N_{r,ik} = \sum_{k \in K} N^{0}_{r,ik}, \qquad \sum_{i} N_{r,ik} = \sum_{i} N^{0}_{r,ik} - \left( EOB^{*}_{r,k} - EOB_{r,k} \right) \qquad \text{(B.26)}$$

Assim, a soma dos EOB de cada região é a do S38 original. Na versão final, foram elevadas ao mínimo a geração a gás natural e o gás canalizado do RS e a geração a gás natural e a derivados de petróleo do RB; os demais subsetores cederam folga. Na geração a gás natural, as compras de insumos não energéticos ficaram em 0,026 do VBP no RS e em 0,032 no RB, abaixo do limiar de alerta de 0,05 do VBP fixado para essa checagem: com o combustível em $\kappa$ do VBP, a TUST, as remunerações, os impostos e o EOB mínimo deixam pouco para os demais insumos. Esse alerta foi mantido e registrado; com $\kappa$ = 0,60 (variante k060), a menor razão passa a 0,077. Na variante eta005, $\eta$ = 0,05.

## B.9 Emissões

**E1 (versão principal).** Os subsetores de geração receberam as emissões das usinas de serviço público do SEEG 13.0 em 2019, em CO₂e pela métrica GWP-AR5, por combustível (SEEG, 2025), $N_{r,g}$. No RS, onde a geração a derivados de petróleo não tem produção na base, as emissões do SEEG com óleo diesel e óleo combustível foram atribuídas às gerações a carvão e a gás natural na proporção dos GWh (HIPÓTESE). No RB, as emissões dessa subcategoria sem estado ("Não alocado") foram somadas ao RB. As gerações hidrelétrica, eólica, solar e nuclear não receberam níveis do SEEG (fator de emissão direto nulo). As emissões de SF₆ do sistema elétrico (SEEG, 2025) foram repartidas entre as regiões pela participação no VBP do S38 e, dentro de cada região, entre a transmissão e a distribuição pela participação no VBP das duas:

$$N_{r,k} = S^{\mathrm{SF6}} \, \frac{X_{r,\mathrm{S38}}}{\sum_{q} X_{q,\mathrm{S38}}} \, \frac{X_{r,k}}{X_{r,\mathrm{TRA}} + X_{r,\mathrm{DIS}}}, \qquad k \in \{\mathrm{TRA}, \mathrm{DIS}\} \qquad \text{(B.27)}$$

O resíduo da conta-satélite, $R_r = CO2_{r,\mathrm{S38}} - \sum_{l \in K} N_{r,l}$, foi atribuído à distribuição e ao gás canalizado na proporção do VBP (HIPÓTESE):

$$CO2_{r,k} = N_{r,k} + R_r \, \frac{X_{r,k}}{X_{r,\mathrm{DIS}} + X_{r,\mathrm{GAS}}}, \quad k \in \{\mathrm{DIS}, \mathrm{GAS}\}; \qquad CO2_{r,k} = N_{r,k}, \quad k \notin \{\mathrm{DIS}, \mathrm{GAS}\} \qquad \text{(B.28)}$$

(Equação (26) do corpo do artigo). Se o resíduo fosse negativo, os níveis seriam reduzidos proporcionalmente até o total da base; isso não ocorreu. O resíduo é de 1.975.857,7 t CO₂e no RS (33,8% das emissões do S38 da região, 5.838.005,6 t CO₂e) e de 49.689.733,9 t CO₂e no RB (58,8% de 84.518.349,1 t CO₂e). Os fatores de emissão implícitos, em t CO₂e/MWh, estão na Tabela A3.

**E2 e E3 (sensibilidades).** Na E2, o total da base foi repartido na proporção dos níveis do SEEG, sem resíduo; na E3, cada subsetor ficou só com o seu nível, e o total do S38 da base deixa de ser preservado (difere exatamente pelo resíduo):

$$CO2^{\mathrm{E2}}_{r,k} = CO2_{r,\mathrm{S38}} \, \frac{N_{r,k}}{\sum_{l \in K} N_{r,l}}, \qquad CO2^{\mathrm{E3}}_{r,k} = N_{r,k} \qquad \text{(B.29)}$$

**E4 (sensibilidade).** Partindo da E1, retiraram-se de cada região, da parte de resíduo da distribuição e do gás canalizado (na proporção do resíduo de cada um, que é a do VBP, sem mexer no SF₆), as emissões que o SEEG 13.0 atribui, na mesma região, ao refino de petróleo, à exploração de petróleo e gás natural e à produção de carvão mineral, nas atividades "Produção de combustíveis" e "Geração de eletricidade › Produção de combustíveis". Esses valores, $m_{r,j}$, foram somados aos setores correspondentes da mesma região: refino de petróleo e coquerias, extração de petróleo e gás e extração de carvão mineral e de minerais não metálicos (S19, S05 e S04, na equação). O "Não alocado" do SEEG não entra. Sendo $m_r = \sum_j m_{r,j} \leq R_r$:

$$CO2^{\mathrm{E4}}_{r,k} = CO2^{\mathrm{E1}}_{r,k} - m_r \, \frac{X_{r,k}}{X_{r,\mathrm{DIS}} + X_{r,\mathrm{GAS}}}, \quad k \in \{\mathrm{DIS}, \mathrm{GAS}\}; \qquad CO2^{\mathrm{E4}}_{r,j} = CO2_{r,j} + m_{r,j}, \quad j \in \{\mathrm{S19}, \mathrm{S05}, \mathrm{S04}\} \qquad \text{(B.30)}$$

Os valores por componente estão na Tabela A7. O total movido é de 1.900.182,0 t CO₂e no RS e de 42.743.466,0 t CO₂e no RB; da parte de resíduo, ficam na distribuição e no gás canalizado 75.675,7 t CO₂e no RS e 6.946.267,9 t CO₂e no RB, além do SF₆ da distribuição. Só o vetor de emissões muda; a matriz monetária é a da versão final. O total de emissões da economia não muda, mas o S38 de cada região deixa de reproduzir a base: a Equação (B.5) vale só para o total. Com a mesma realocação aplicada à matriz original (retirando os valores do S38 de cada região e somando-os aos mesmos setores), obteve-se a versão A0_E4, usada para medir quanto dos resultados do artigo na matriz original depende dessas emissões (Tabela A6, Painel B).

## B.10 Subsetores sem produção no RS: colunas latentes e TUST (D18)

A geração solar fotovoltaica e a geração a derivados de petróleo não tinham produção no RS em 2019. Esses subsetores foram tratados como latentes: produção-base zero, nenhuma célula na matriz e uma coluna de coeficientes técnicos e de intensidades que entra em $A$ e em $e$ só no modelo, para permitir choques neles. A coluna foi copiada do mesmo subsetor no RB (espelho). Para cada insumo $i$, somou-se o coeficiente das duas origens no espelho e repartiu-se a soma entre as origens pela participação de cada origem nas compras desse insumo na coluna original do S38 do RS:

$$a_{(q,i),(\mathrm{RS},k)} = \Big( \sum_{q'} a_{(q',i),(\mathrm{RB},k)} \Big) \, \frac{Z_{(q,i),(\mathrm{RS},\mathrm{S38})}}{\sum_{q'} Z_{(q',i),(\mathrm{RS},\mathrm{S38})}}, \qquad e_{\mathrm{RS},k} = e_{\mathrm{RB},k}, \qquad k \in \{\mathrm{SOL}, \mathrm{PET}\} \qquad \text{(B.31)}$$

Para os insumos que são subsetores do próprio S38 (transmissão), usou-se a participação das origens no bloco S38 × S38 que chega ao RS; para os insumos que o S38 do RS não compra, a participação das origens no total das suas compras fora do bloco. A geração nuclear do RS não tem produção nem coluna latente.

Copiar a coluna inteira faria os subsetores latentes pagarem a TUST por real do espelho do RB. Supôs-se, em vez disso, que eles pagam a mesma TUST por MWh das fontes do RS no SIN, $\tau_{\mathrm{RS}}$ (Equação (B.16)), ao preço do espelho (HIPÓTESE, D18). O coeficiente total de TUST da coluna latente passa a

$$a_{\mathrm{TRA},(\mathrm{RS},k)} = \frac{\tau_{\mathrm{RS}}}{p_{\mathrm{RB},k}}, \qquad p_{\mathrm{RB},k} = \frac{X_{\mathrm{RB},k}}{Q_{\mathrm{RB},k}}, \qquad k \in \{\mathrm{SOL}, \mathrm{PET}\} \qquad \text{(B.32)}$$

(Equação (27) do corpo do artigo), com a repartição entre as linhas de transmissão do RS e do RB mantida como na Equação (B.31). Os demais coeficientes não mudam; como a coluna latente não tem VBP, a diferença corresponde a uma variação implícita do seu valor adicionado, que não entra no modelo. Com $\tau_{\mathrm{RS}}$ = 32,41 R\$/MWh, $p_{\mathrm{RB},\mathrm{SOL}}$ = 200,8 R\$/MWh e $p_{\mathrm{RB},\mathrm{PET}}$ = 786,0 R\$/MWh, o coeficiente de TUST passou de 0,0953 para 0,1614 na geração solar e de 0,0105 para 0,0412 na geração a derivados de petróleo. Na geração solar do RS, o multiplicador de produção passou de 1,421 para 1,508, o multiplicador de emissões de 23,3 para 24,9 t CO₂e por R\$ milhão e as emissões por TWh de 4.682,1 para 5.003,3 t CO₂e.

## B.11 Diagnóstico da conta-satélite de emissões do S38 (NEREUS × SEEG)

Como o resíduo da E1 é grande, comparou-se o S38 da conta-satélite com o SEEG 13.0 (SEEG, 2025), sem alterar a versão principal. Critérios: ano de 2019; métrica GWP-AR5; linhas de emissão (inclusive as não contabilizadas no inventário, que não existem nessas atividades); o RS pelo estado, o RB pelos demais estados e o "Não alocado" à parte. O resultado está na Tabela A7.

No RS, a soma das atividades "Geração de eletricidade" e "Produção de combustíveis" do SEEG, 5.839,2 mil t CO₂e, difere em 0,02% do S38 da base (5.838,0 mil t CO₂e). Esse resultado é compatível com a inclusão, no S38 da conta-satélite, das emissões do refino de petróleo e da produção de carvão mineral, que o SEEG classifica em "Produção de combustíveis". No RB, pelo mesmo critério, a diferença é de −6,51% (79.018,9 contra 84.518,3 mil t CO₂e), e o "Não alocado" das duas atividades soma 18.700,0 mil t CO₂e. Repetidas as somas com as métricas GWP-AR2, AR4 e AR6 e GTP-AR2, AR4, AR5 e AR6, a GWP-AR5 é a mais próxima no S38 do RS, e nenhuma métrica aproxima o S38 do RB. No total do Brasil (estados e "Não alocado", contra o total da base), a diferença é de 36,5% nas emissões brutas e de 1,0% nas líquidas, ambas pela GWP-AR5; com o número de métricas, bases e escopos testados, aproximações de totais como a das emissões líquidas podem ocorrer por acaso e não indicam qual base ou versão do SEEG a conta-satélite usou.

Para verificar se o padrão "atividade do SEEG → setor da matriz" se repete, compararam-se os setores do RS com as maiores emissões na base (agricultura, pecuária, produção florestal, refino de petróleo, minerais não metálicos, água, esgoto e gestão de resíduos e transporte terrestre, além do próprio S38 como controle) com somas de uma, duas ou três unidades do SEEG do RS, dentro de cada nível de classificação. Foram testadas 679.856 combinações; 224 ficaram com diferença abaixo de 0,1% (126 núcleos distintos), para cerca de 211 esperadas por acaso. Pelo critério da classificação das contas nacionais, aplicado igualmente a todos os setores, dessas combinações, 0 têm sentido econômico e 9 têm sentido discutível; o padrão não se repete nos outros setores do RS. A busca encontrou também um casamento concorrente: o refino de petróleo e coquerias do RS aproxima-se da soma do refino de petróleo com a indústria química do SEEG (0,071%), com as mesmas emissões do refino. As duas leituras se excluem; e, se o refino estiver no S38, as emissões do refino de petróleo e coquerias do RS na base (2.693,9 mil t CO₂e) não têm contrapartida no SEEG do RS. Nesse caso, a E4 contaria o refino duas vezes no S19 do RS.

O diagnóstico fornece, portanto, um indício, compatível com a inclusão do refino e da mineração de carvão no S38 da conta-satélite, e não uma prova: não há documentação da conta-satélite, o RB não fecha pelo mesmo critério, coincidências abaixo de 0,1% são esperadas com o número de combinações testadas e há um casamento concorrente. Por isso, a E1 foi mantida como versão principal, e a E3 e a E4 foram tratadas como sensibilidades.

## B.12 Verificação

Ao final de cada desagregação (versão principal e variantes), foram executadas as checagens abaixo (Tabela A8):

- re-agregação célula a célula de $Z$, $Y$, $X$, dos insumos primários, do valor adicionado e das contas-satélite, Equações (B.1) a (B.5), com tolerância absoluta indicada na Tabela A8; na versão final, a maior diferença foi de 0,000000001 R\$ milhões;
- balanço de cada subsetor: vendas iguais ao VBP e compras mais valor adicionado iguais ao VBP, salvo o resíduo contábil da matriz original, repartido pelo VBP; identidade do valor adicionado;
- não negatividade: nenhum fluxo, insumo primário ou item satélite negativo onde a original não o tem;
- subsetores sem produção com linha e coluna zeradas;
- roteamento do bloco: as vendas da geração de cada região dentro do bloco somam $E_r$, as da transmissão somam $T_r$, a geração e a transmissão não vendem fora do bloco, a transmissão é paga nas frações $\alpha$ e $1 - \alpha$, e os quatro fluxos regionais do bloco são os da original;
- convergência dos ajustes RAS (linhas e reequilíbrio);
- piso das térmicas, Equação (B.12); EOB mínimo, Equação (B.24); soma dos EOB de cada região igual à original; insumos fixos iguais antes e depois do reequilíbrio;
- modelo: $L \geq 0$ e diagonal de $L$ maior ou igual a 1, inclusive com as colunas latentes; alerta se a soma de uma coluna de $A$ chegar a 1, se o multiplicador de produção de um subsetor passar de 2,2 e se os insumos não energéticos ficarem abaixo do limiar da Seção B.8;
- na E4: valores movidos exatos, total da economia inalterado, S38 de cada região reduzido exatamente no valor movido e nenhuma emissão negativa;
- na D18: a TUST por MWh das colunas latentes, ao preço do espelho, é igual a $\tau_{\mathrm{RS}}$.

As nove especificações (principal e oito variantes) passaram nas mesmas checagens, sem falhas; na E3, as emissões do S38 deixam de reproduzir a base, e na E4 só o total da economia é preservado (Seção B.9), o que fica registrado como alerta. Ficaram registrados também dois outros alertas: o multiplicador de produção acima de 2,2, nas nove especificações (na versão principal, na geração a gás natural e no gás canalizado do RS e na geração a derivados de petróleo do RS, latente, e do RB); e os insumos não energéticos da geração a gás natural abaixo do limiar da Seção B.8, em todas as especificações exceto as variantes k060 e eta005. Além disso, conferiu-se que o arquivo da matriz original não foi alterado, que os cenários do artigo rodados na matriz original reproduzem os valores publicados (arredondados a uma casa decimal, são idênticos nos Painéis B das Tabelas 1, 3 e 4 e na Tabela A2, exceto a linha da cesta renovável energia/transporte-intensiva da Tabela 4 calculada com o vetor da Tabela A1), e que a geração das tabelas, repetida, dá os mesmos números.

## B.13 Modelo e atribuição dos choques

Com a matriz desagregada, $A$ inclui as colunas latentes da Seção B.10, e as intensidades são $e_k = CO2_k / X_k$ (as do espelho nas colunas latentes). Os multiplicadores da Tabela A3 são

$$m^{X}_{j} = \sum_{i} L_{ij}, \qquad m^{CO2}_{j} = \sum_{i} e_i \, L_{ij} \qquad \text{(B.33)}$$

o de produção e o de emissões (t CO₂e por R\$ milhão de demanda final do subsetor $j$), como em Miller e Blair (2022). Mantiveram-se os vetores de choque do artigo, de R\$ 1 bilhão (R\$ 1.000 milhões) na demanda final de setores do RS (Quadro 1 e Tabela A1). As emissões totais, diretas e indiretas de um choque são

$$CO2^{\mathrm{tot}} = e' L \, \Delta Y, \qquad CO2^{\mathrm{dir}} = e' \Delta Y, \qquad CO2^{\mathrm{ind}} = CO2^{\mathrm{tot}} - CO2^{\mathrm{dir}} \qquad \text{(B.34)}$$

(Equação (29) do corpo do artigo); a intensidade carbônica é $CO2^{\mathrm{tot}} / \sum_i \Delta X_i$, com $\Delta X = L \, \Delta Y$.

**A0.** Os cenários do artigo, inclusive a cesta renovável energia/transporte-intensiva nas duas versões de vetor, foram rodados na matriz original, para reproduzir os resultados publicados (Seção B.12).

**A1.** Na matriz desagregada, o choque no S38 foi repartido entre os subsetores do RS na proporção das vendas líquidas de cada um à demanda final, $y_{\mathrm{RS},k} = \sum_d Y_{(\mathrm{RS},k),d}$, com valores negativos contados como zero:

$$\Delta Y_{\mathrm{RS},k} = \Delta Y_{\mathrm{RS},\mathrm{S38}} \, \frac{\max(y_{\mathrm{RS},k}, 0)}{\sum_{l \in K} \max(y_{\mathrm{RS},l}, 0)} \qquad \text{(B.35)}$$

(Equação (28) do corpo do artigo). Como só a distribuição e o gás canalizado vendem à demanda final, o choque vai a esses dois subsetores (participações no Quadro 1).

**A2.** A parcela do S38 das cestas renováveis foi atribuída à geração eólica do RS (D12). A das cestas fósseis foi atribuída à geração a carvão mineral e à geração a gás natural do RS, na proporção do VBP de 2019 na versão final (D13):

$$\Delta Y_{\mathrm{RS},g} = \Delta Y_{\mathrm{RS},\mathrm{S38}} \, \frac{X_{\mathrm{RS},g}}{X_{\mathrm{RS},\mathrm{CAR}} + X_{\mathrm{RS},\mathrm{GN}}}, \qquad g \in \{\mathrm{CAR}, \mathrm{GN}\} \qquad \text{(B.36)}$$

com as participações do Quadro 1. No cenário de energia elétrica agregada, o A2 coincide com o A1 (D14). Os demais setores das cestas não mudam. As sensibilidades da Tabela 5 trocam a atribuição do S38: nas cestas renováveis, metade à geração eólica e metade à solar fotovoltaica (latente), ou dois terços à geração eólica e um terço à transmissão; nas cestas fósseis, todo o S38 à geração a carvão mineral ou todo à geração a gás natural.

**B.** Cada subsetor de geração do RS (hidrelétrica, eólica, solar fotovoltaica, biomassa, carvão mineral e gás natural) e a distribuição receberam um choque de R\$ 1 bilhão. Os subsetores de geração receberam também um choque de 1 TWh, valorado ao preço médio implícito de 2019 na matriz, $p_{\mathrm{RS},g} = X_{\mathrm{RS},g} / Q_{\mathrm{RS},g}$ (para a solar latente, o preço do espelho, $p_{\mathrm{RB},\mathrm{SOL}}$):

$$\Delta Y_{\mathrm{RS},g} = 1\ \mathrm{TWh} \times p_{\mathrm{RS},g} \qquad \text{(B.37)}$$

que, com o preço em R\$/MWh, dá o choque em R\$ milhões igual ao preço. As emissões por kWh são as emissões por TWh divididas por 1.000 (g CO₂e/kWh), e as emissões evitadas por TWh em relação ao carvão (ou ao gás natural) são a diferença entre as emissões por TWh da geração a carvão (ou a gás natural) e as da tecnologia (Tabela 6). O choque movimenta a coluna de insumos de 2019 de cada subsetor (combustível, transmissão, manutenção e serviços): mede a operação das usinas, e não a implantação, cujos bens de capital estão na demanda final de investimento e não entram em $A$. A Tabela 7 compara as emissões dos blocos A0, A1 e A2.

## B.14 Variantes e robustez

As variantes mudam um parâmetro ou uma hipótese de cada vez sobre a versão final e passam pelas mesmas checagens (Seção B.12):

- **P2:** preços iguais entre as fontes (pesos da Equação (B.11) iguais aos GWh);
- **E2:** emissões do S38 na proporção dos níveis do SEEG, Equação (B.29);
- **E3:** só os níveis do SEEG, sem o resíduo, Equação (B.29);
- **E4:** refino, exploração de petróleo e gás e produção de carvão mineral do SEEG realocados do resíduo para os setores correspondentes, Equação (B.30);
- **gas4dist:** VBP do gás canalizado do RB pelo preço médio de quatro distribuidoras (Seção B.3);
- **rap_media:** transmissão pela RAP de 2019, R\$ 24.883,4 milhões (Seção B.3);
- **k060:** $\kappa$ = 0,60 no piso das térmicas, Equação (B.12);
- **eta005:** $\eta$ = 0,05 no EOB mínimo, Equação (B.24).

Nas variantes que mudam o SF₆ por mudarem o VBP da transmissão ou da distribuição (rap_media e gas4dist), a Equação (B.27) foi recalculada com os VBP da variante. Na robustez, o vetor do A2 fóssil é o da versão final em todas as variantes, de modo que só a matriz muda; o choque de 1 TWh é valorado ao preço implícito de cada variante. A Tabela A6 traz as emissões e a intensidade carbônica do A2 (energia elétrica agregada, cesta renovável base e cesta fóssil base) e das emissões por TWh de cada tecnologia nas nove versões, com o desvio em relação à principal, e, no Painel B, a matriz original com e sem a E4. Entre as nove versões, as emissões do A2 vão de 92.569,0 a 97.102,7 t CO₂e na cesta renovável base, de 2.024.409,0 a 2.951.716,5 t CO₂e na cesta fóssil base e de 253.058,0 a 437.947,0 t CO₂e na energia elétrica agregada.
