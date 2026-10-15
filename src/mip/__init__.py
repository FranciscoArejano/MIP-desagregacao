"""Pacote da desagregação do S38 na MIP inter-regional RS × Restante do Brasil (2019).

Módulos:
- estrutura:    classe MIP, layout da planilha e constantes (itens primários, contas satélite, colunas de DF)
- leitura:      leitura da planilha original (e de planilhas exportadas com o mesmo layout)
- validacao:    checagens das identidades contábeis
- modelo:       modelo de Leontief genérico (coeficientes, inversa, emissões, recortes, ranking)
- referencia:   cenários e valores de referência da Rodada 01
- diagnostico:  diagnóstico de um setor (insumos, vendas, bloco intrassetorial, contas satélite)
- desagregacao: motor genérico de desagregação + RAS + verificação
- exportacao:   exportação em .xlsx (mesmo layout da original) e em CSV formato longo
"""

__all__ = [
    "estrutura",
    "leitura",
    "validacao",
    "modelo",
    "referencia",
    "diagnostico",
    "desagregacao",
    "exportacao",
]
