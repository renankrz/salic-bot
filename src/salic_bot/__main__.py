"""Entry point para execução via CLI ou GUI"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from .bot import SalicBot
from .config import LOGS_DIR, SCREENSHOTS_DIR
from .logging_config import configurar_logging
from .models.projeto import Projeto

logger = logging.getLogger(__name__)


def _run_cli(args: argparse.Namespace) -> int:
    """Executa o bot via linha de comando"""
    projeto = Projeto(
        mecanismo=args.mecanismo,
        proponente=args.proponente,
        pronac=args.pronac,
    )

    headless = os.getenv("HEADLESS", "False").lower() == "true"
    slow_mo = int(os.getenv("SLOW_MO", "100"))
    clientes_dir = os.getenv("CLIENTES_DIR")

    if not clientes_dir:
        logger.error("CLIENTES_DIR não definido no .env")
        return 1

    logger.info("=" * 60)
    logger.info("Salic Bot - Automação de Prestação de Contas")
    logger.info("=" * 60)
    logger.info(
        "Iniciando execução | mecanismo=%s | proponente=%s | pronac=%s",
        args.mecanismo,
        args.proponente,
        args.pronac,
    )

    bot = SalicBot(
        headless=headless, slow_mo=slow_mo, projeto=projeto, clientes_dir=clientes_dir
    )
    itens_ok, total = bot.executar()

    logger.info("=" * 60)
    if itens_ok == total and total > 0:
        logger.info(
            "Execução concluída com sucesso! (%d/%d itens incluídos)", itens_ok, total
        )
    elif itens_ok > 0:
        logger.warning(
            "Execução concluída com erros! (%d/%d itens incluídos)", itens_ok, total
        )
    else:
        logger.error("Execução falhou! (%d/%d itens incluídos)", itens_ok, total)
    logger.info("=" * 60)

    return 0 if itens_ok == total and total > 0 else 1


def main():
    """Função principal — sem argumentos abre a GUI, com argumentos usa CLI"""
    load_dotenv()

    # Se não houver argumentos posicionais, abre a GUI
    if len(sys.argv) == 1:
        from .gui.main_window import iniciar_gui

        return iniciar_gui()

    # CLI
    configurar_logging(logs_dir=LOGS_DIR)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Salic Bot - Automação de Prestação de Contas"
    )
    parser.add_argument("mecanismo", help="Mecanismo do projeto (ex: Mecenato)")
    parser.add_argument("proponente", help="CNPJ do proponente (somente dígitos)")
    parser.add_argument("pronac", type=int, help="PRONAC do projeto")
    args = parser.parse_args()

    return _run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
