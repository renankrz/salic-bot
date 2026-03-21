"""Configuração global de logging para o Salic Bot"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configurar_logging(log_dir: Path | str = "logs") -> None:
    """Configura o logging global com saída para arquivo (rotativo) e stdout.

    Args:
        log_dir: Diretório onde o arquivo de log será criado.
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "salic_bot.log"

    formato = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(formato)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1 * 1024 * 1024,  # 1 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[stream_handler, file_handler],
    )
