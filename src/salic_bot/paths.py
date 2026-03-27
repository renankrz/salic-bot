"""Configurações globais do Salic Bot"""

import sys
from pathlib import Path


def is_frozen() -> bool:
    """Retorna True se estiver rodando a partir de um executável PyInstaller."""
    return getattr(sys, "frozen", False)


def _get_bundle_dir() -> Path:
    """Diretório onde o PyInstaller extrai os dados embutidos.

    - Executável PyInstaller: sys._MEIPASS (pasta temporária de extração)
    - Desenvolvimento: raiz do projeto (3 níveis acima de src/salic_bot/paths.py)
    """
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent.parent


def _get_app_dir() -> Path:
    """Diretório gravável para dados gerados pelo app (logs, screenshots).

    - Executável PyInstaller: pasta onde o executável está
    - Desenvolvimento: raiz do projeto
    """
    if is_frozen():
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


BUNDLE_DIR = _get_bundle_dir()
APP_DIR = _get_app_dir()

BROWSERS_DIR = str(BUNDLE_DIR / "browsers")
LOGS_DIR = str(APP_DIR / "logs")
SCREENSHOTS_DIR = str(APP_DIR / "screenshots")
