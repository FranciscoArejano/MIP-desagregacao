## 3.x Desagregação do setor de energia elétrica, gás natural e outras utilidades (S38)

Na matriz inter-regional de insumo-produto de 2019, Rio Grande do Sul (RS) e Restante do Brasil (RB), com conta-satélite de emissões de CO₂e (NEREUS, [2025?]; Haddad et al., 2025), o setor S38 reúne em uma coluna a geração de energia elétrica de todas as fontes, a transmissão, a distribuição e o gás canalizado. No modelo de Leontief, essas atividades compartilham os coeficientes técnicos e a intensidade $e_i = CO2_i/X_i$, mas as intensidades por fonte diferem: no RS, os fatores de emissão adotados (Tabela A3) são de {{fator_e1_rs_car}} t CO₂e/MWh na geração a carvão mineral, {{fator_e1_rs_gn}} na geração a gás natural e {{fator_e1_rs_hid}} nas gerações hidrelétrica e eólica. Lenzen (2011) mostra que agregar setores com intensidades distintas altera os multiplicadores ambientais. O objetivo foi separar as fontes, nas duas regiões, para atribuir os choques a cada tecnologia.

O procedimento segue a desagregação a partir de participações e de informação parcial (Wolsky, 1984; Lindner, Legault e Guan, 2012) e, em particular, a do setor elétrico em geração por tecnologia, transmissão e distribuição (Lindner, Legault e Guan, 2013; Peters, 2016, na base GTAP-Power). O S38 foi dividido em 11 subsetores em cada região (Quadro 2): oito de geração (conjunto $G$) e três de rede e utilidades, com $K = G \cup \{\mathrm{TRA}, \mathrm{DIS}, \mathrm{GAS}\}$.

**Quadro 2:** Subsetores do S38 e critério do valor bruto da produção (VBP)

| Código | Subsetor | Critério do VBP | Fonte |
|---|---|---|---|
| S38_HID | Geração hidrelétrica | Parcela de $E_r$ (Eq. 20) por GWh × preço (Eq. 21) | ONS ([2026]); EPE (2020); ANEEL ([2026]); IBGE (2026) |
| S38_EOL | Geração eólica | Idem | Idem |
| S38_SOL | Geração solar fotovoltaica | Idem no RB; latente no RS | Idem |
| S38_BIO | Geração a biomassa | Idem, com piso (Eq. 22) | Idem |
| S38_CAR | Geração a carvão mineral | Idem, com piso (Eq. 22) | Idem |
| S38_GN | Geração a gás natural | Idem, com piso (Eq. 22) | Idem |
| S38_PET | Geração a derivados de petróleo | Idem, com piso (Eq. 22), no RB; latente no RS | Idem |
| S38_NUC | Geração nuclear | Parcela de $E_r$ (Eq. 20) por GWh × tarifa de Angra 1 e 2 (Eq. 21) no RB; zero no RS | EPE (2020); ANEEL (2018b) |
| S38_TRA | Transmissão de energia elétrica | Encargos de uso faturados pelo ONS em 2019 | ONS (2019a; 2019b; 2020) |
| S38_DIS | Distribuição de energia elétrica | Resíduo (Eq. 23) | NEREUS ([2025?]) |
| S38_GAS | Gás canalizado e outras utilidades | RS: receita da Sulgás; RB: preço da Sulgás × volume não térmico | Sulgás (2020); Brasil (2020) |

*Fonte: Elaboração própria.*

O princípio é preservar a matriz original: a soma dos subsetores reproduz cada célula da matriz e da conta-satélite. Sendo $Z_{(r,k),(q,j)}$ o fluxo do subsetor $k$ de $r$ ao setor $j$ de $q$, $Y_{(r,k),(q,d)}$ a venda à coluna $d$ da demanda final e $V_{h,(r,k)}$ o insumo primário $h$ (inclusive o excedente operacional bruto, EOB), as restrições são, para $r, q \in \{\mathrm{RS}, \mathrm{RB}\}$ e $i, j \neq \mathrm{S38}$:

$$\sum_{k \in K} Z_{(r,k),(q,j)} = Z_{(r,\mathrm{S38}),(q,j)}, \qquad \sum_{k \in K} Y_{(r,k),(q,d)} = Y_{(r,\mathrm{S38}),(q,d)} \qquad (15)$$

$$\sum_{k \in K} Z_{(q,i),(r,k)} = Z_{(q,i),(r,\mathrm{S38})}, \qquad \sum_{k \in K} V_{h,(r,k)} = V_{h,(r,\mathrm{S38})} \qquad (16)$$

$$\sum_{k \in K} \sum_{l \in K} Z_{(r,k),(q,l)} = Z_{(r,\mathrm{S38}),(q,\mathrm{S38})} \qquad (17)$$

$$\sum_{k \in K} X_{r,k} = X_{r,\mathrm{S38}} \qquad (18)$$

$$\sum_{k \in K} CO2_{r,k} = CO2_{r,\mathrm{S38}} \quad \text{(na E1)} \qquad (19)$$

**Produção.** O VBP da geração foi ancorado no bloco S38 × S38. Supôs-se que as vendas do S38 de $r$ ao S38 das duas regiões são a energia da geração vendida à distribuição mais a transmissão, $T_r$ (HIPÓTESE: as térmicas não compram gás das distribuidoras). O VBP da geração,

$$E_r = \sum_{q} Z_{(r,\mathrm{S38}),(q,\mathrm{S38})} - T_r \qquad (20)$$

é repartido entre as fontes pela energia gerada em 2019, $Q_{r,g}$ (GWh), vezes o preço de cada fonte, $p_g$ (Peters, 2016):

$$X_{r,g} = E_r \, \frac{Q_{r,g} \, p_g}{\sum_{h \in G} Q_{r,h} \, p_h}, \qquad g \in G \qquad (21)$$

A geração do RS veio do ONS ([2026]); a do RB, do Brasil (EPE, 2020) menos o RS. Os preços são os dos leilões (ANEEL, [2026]), corrigidos pelo IPCA para 2019 (IBGE, 2026), e, na nuclear, a tarifa de Angra 1 e 2 (ANEEL, 2018b) (HIPÓTESE: os preços relativos dos leilões representam os da matriz; preços iguais na Tabela A6). Nas térmicas, o VBP tem um piso dado pelo combustível comprado, $C_{r,g}$ (HIPÓTESE):

$$X_{r,g} \geq \frac{C_{r,g}}{\kappa}, \qquad \kappa = {{param_kappa}} \qquad (22)$$

Atingido o piso, as demais fontes caem na proporção do VBP, sem alterar $E_r$. O VBP da transmissão são os encargos de uso faturados pelo ONS em 2019, sem PIS/Pasep e Cofins, R\$ {{vbp_tra_total}} milhões (ONS, 2019a; 2019b; 2020), repartidos entre as regiões pelo VBP do S38 (HIPÓTESE). O do gás canalizado no RS é a receita líquida da Sulgás em 2019, R\$ {{vbp_rs_gas}} milhões (Sulgás, 2020); no RB, o preço da Sulgás vezes o volume não térmico das distribuidoras (Brasil, 2020), R\$ {{vbp_rb_gas}} milhões (HIPÓTESE). A distribuição é o resíduo:

$$X_{r,\mathrm{DIS}} = X_{r,\mathrm{S38}} - E_r - T_r - X_{r,\mathrm{GAS}} \qquad (23)$$

**Vendas e compras.** No bloco S38 × S38, cada componente vai de $r$ a $q$ na proporção $F_{rq}/F_r$ das vendas originais do S38: a energia vai à distribuição de $q$; a transmissão é paga em uma fração $\alpha = {{param_alfa}}$ pela distribuição e em $1 - \alpha$ pela geração (ANEEL, 2013), repartida entre as fontes de $q$ pela energia gerada no Sistema Interligado Nacional, $M_{q,g}$ (ONS, [2026]), o que iguala a tarifa de uso da transmissão (TUST) por MWh das fontes de uma região:

$$Z_{(r,\mathrm{TRA}),(q,g)} = (1 - \alpha) \, T_r \, \frac{F_{rq}}{F_r} \, \frac{M_{q,g}}{\sum_{h \in G} M_{q,h}} \qquad (24)$$

Fora do bloco, a geração e a transmissão não vendem: a energia elétrica sai da distribuição, e o gás canalizado vende na própria região, pelas vendas por segmento da Sulgás (Sulgás, 2020) no RS e pelo consumo por setor (EPE, 2020) no RB, até {{param_teto_gas}} das compras de S38 de cada comprador (HIPÓTESE); as linhas foram conciliadas por RAS (Lahr e de Mesnard, 2004). Nas colunas, os combustíveis vão à fonte correspondente: carvão mineral à geração a carvão; petróleo e gás natural à geração a gás natural e ao gás canalizado (Brasil, 2020); refino, no RB, aos derivados de petróleo; lenha e bagaço à biomassa. As importações do S38 vão à distribuição e, no RB, também à geração a gás e ao gás canalizado (Brasil, [2026]). As remunerações seguem o CEMPRE (IBGE, 2021) entre geração, transmissão, distribuição e gás e, na geração, o VBP líquido do combustível (HIPÓTESE). Os demais insumos seguem o VBP, e o EOB fecha cada coluna. Para evitar EOB negativo, esses insumos e os impostos sobre produtos foram ajustados por RAS (Lahr e de Mesnard, 2004), preservando os totais de linha e a soma dos EOB de cada região, com (HIPÓTESE)

$$EOB_{r,k} \geq \eta \, X_{r,k}, \qquad \eta = {{param_eta}} \qquad (25)$$

**Emissões.** Na versão principal (E1), a geração recebe as emissões das usinas do SEEG (2025), $N_{r,k}$, e a transmissão e a distribuição, as de SF₆; o resíduo da conta-satélite vai à distribuição e ao gás canalizado, na proporção do VBP (HIPÓTESE):

$$CO2_{r,k} = N_{r,k} + \Big( CO2_{r,\mathrm{S38}} - \sum_{l \in K} N_{r,l} \Big) \frac{X_{r,k}}{X_{r,\mathrm{DIS}} + X_{r,\mathrm{GAS}}}, \qquad k \in \{\mathrm{DIS}, \mathrm{GAS}\} \qquad (26)$$

O resíduo é {{residuo_rs_pct}}% do CO₂e do S38 no RS e {{residuo_rb_pct}}% no RB. No diagnóstico (Tabela A7), a soma das atividades "Geração de eletricidade" e "Produção de combustíveis" no RS difere em {{diag_s38_rs_dif}}% do S38 da base, compatível com um S38 da conta-satélite que inclua o refino e a produção de carvão mineral. É um indício, não uma confirmação: não há documentação da conta-satélite; no RB, a diferença é de {{diag_s38_rb_dif}}%; das {{diag_testes}} combinações testadas no RS, {{diag_casamentos}} ficaram abaixo de 0,1%, contra cerca de {{diag_acaso}} esperadas por acaso; e uma combinação concorrente põe o refino no setor de refino da base. Mantida a E1, calcularam-se sensibilidades (Tabela A6): a E2, que reparte o total da base na proporção dos níveis do SEEG; a E3, só com os níveis do SEEG, sem preservar o total da base; e a E4, em que as emissões do refino, da exploração de petróleo e gás e da produção de carvão mineral saem do resíduo para esses setores da mesma região.

**Subsetores sem produção no RS.** A geração solar fotovoltaica e a geração a derivados de petróleo não produziam no RS em 2019 (a nuclear foi zerada). Foram tratadas como latentes: produção-base zero e, só no modelo, coluna de coeficientes técnicos e de intensidades do mesmo subsetor no RB, com as origens repartidas como na coluna do S38 do RS. Supôs-se que essas colunas pagam a mesma TUST por MWh das fontes do RS, $\tau_{\mathrm{RS}} = {{tau_rs}}$ R\$/MWh, sobre o VBP por MWh do espelho, $p_{\mathrm{RB},k}$ (HIPÓTESE):

$$a_{\mathrm{TRA},(\mathrm{RS},k)} = \frac{\tau_{\mathrm{RS}}}{p_{\mathrm{RB},k}}, \qquad k \in \{\mathrm{SOL}, \mathrm{PET}\} \qquad (27)$$

**Verificação.** A soma dos subsetores reproduz a matriz original e as contas-satélite, com diferença máxima de {{reag_max}} R\$ milhões; verificaram-se o balanço, a não negatividade, o EOB mínimo e a inversa de Leontief, $L = (I - A)^{-1}$, não negativa e com diagonal maior ou igual a 1 (Tabela A8). Os cenários do artigo, rodados na matriz original, reproduzem os valores publicados: arredondados a uma casa decimal, são idênticos nos Painéis B das Tabelas 1, 3 e 4 (exceto a linha R4a da Tabela 4) e na Tabela A2.

**Atribuição dos choques.** Mantiveram-se os vetores de R\$ 1 bilhão (R\$ 1.000 milhões) na demanda final do RS (Quadro 1; Tabela A1) e o modelo (Miller e Blair, 2022). No bloco A1, o choque no S38 foi repartido entre os subsetores do RS na proporção das vendas de cada um à demanda final, $y_{\mathrm{RS},k}$, o que o leva à distribuição e ao gás canalizado:

$$\Delta Y_{\mathrm{RS},k} = \Delta Y_{\mathrm{RS},\mathrm{S38}} \, \frac{\max(y_{\mathrm{RS},k}, 0)}{\sum_{l \in K} \max(y_{\mathrm{RS},l}, 0)} \qquad (28)$$

No bloco A2, o S38 das cestas renováveis foi atribuído à geração eólica, e o das fósseis às gerações a carvão mineral e a gás natural, na proporção do VBP de 2019; na energia elétrica agregada, A2 coincide com A1 (sensibilidades na Tabela 5). No bloco B, seis subsetores de geração do RS e a distribuição receberam R\$ 1 bilhão, e os seis de geração, 1 TWh valorado pelo VBP por MWh, $\Delta Y_{\mathrm{RS},g} = p_{\mathrm{RS},g}$ R\$ milhões (na solar, o do espelho). As emissões totais e diretas são

$$CO2^{tot} = e' L \, \Delta Y, \qquad CO2^{dir} = e' \Delta Y \qquad (29)$$

e as indiretas, a diferença (Tabela 6). O choque mede a operação, que movimenta a coluna de insumos de 2019 (combustível, transmissão e serviços), e não a implantação das usinas, cujos bens de capital não entram em $A$. Os detalhes estão nas Tabelas A3 a A8 e no Apêndice B.
