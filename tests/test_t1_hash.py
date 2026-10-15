"""T1 — a planilha original não pode mudar (hash SHA-256 conferido em todo pytest)."""
import hashlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTA_ORIGINAL = RAIZ / "dados" / "original"
NOME_ORIGINAL = "Matrtiz_Insumo-Produto_RS_RB_com_emissões.xlsx"
HASH_REFERENCIA = "15e734a43aba6cc582117a742e4279e0535ccad331c86b880eab38ece420a3ea"


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def test_t1_hash_da_planilha_original():
    caminho = PASTA_ORIGINAL / NOME_ORIGINAL
    assert caminho.exists(), f"planilha original não encontrada em {caminho}"
    assert _sha256(caminho) == HASH_REFERENCIA


def test_t1_checksum_txt_confere():
    linhas = (PASTA_ORIGINAL / "CHECKSUM.txt").read_text(encoding="utf-8").splitlines()
    registros = [l.split(maxsplit=1) for l in linhas if l.strip() and not l.startswith("#")]
    assert registros == [[HASH_REFERENCIA, NOME_ORIGINAL]]
