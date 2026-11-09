"""Deja `soporte` importable cuando las pruebas se lanzan desde la raíz."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
