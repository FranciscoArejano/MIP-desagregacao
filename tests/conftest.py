"""Configuração comum dos testes: coloca src/ no caminho de importação."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
