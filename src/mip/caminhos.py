"""Caminhos padrão do repositório."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

PASTA_ORIGINAL = RAIZ / "dados" / "original"
NOME_ORIGINAL = "Matrtiz_Insumo-Produto_RS_RB_com_emissões.xlsx"
CAMINHO_ORIGINAL = PASTA_ORIGINAL / NOME_ORIGINAL
HASH_ORIGINAL = "15e734a43aba6cc582117a742e4279e0535ccad331c86b880eab38ece420a3ea"

PASTA_INTERMEDIARIOS = RAIZ / "dados" / "intermediarios"
PASTA_EXTERNOS = RAIZ / "dados" / "externos"
PASTA_PARAMETROS = RAIZ / "parametros"
PASTA_RESULTADOS = RAIZ / "resultados"
