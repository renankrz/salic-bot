"""Configurações globais do Salic Bot"""

from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

LOGS_DIR = str(_PROJECT_ROOT / "logs")
SCREENSHOTS_DIR = str(_PROJECT_ROOT / "screenshots")
