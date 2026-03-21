"""Entry point para execução via CLI"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from .bot import SalicBot
from .logging_config import configurar_logging
from .models.projeto import Projeto

logger = logging.getLogger(__name__)


def main():
    """Função principal"""
    load_dotenv()
    configurar_logging(log_dir="logs")

    parser = argparse.ArgumentParser(
        description="Salic Bot - Automação de Prestação de Contas"
    )
    parser.add_argument("mecanismo", help="Mecanismo do projeto (ex: Mecenato)")
    parser.add_argument("proponente", help="CNPJ do proponente (somente dígitos)")
    parser.add_argument("pronac", type=int, help="PRONAC do projeto")
    args = parser.parse_args()

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
    sucesso = bot.executar()

    logger.info("=" * 60)
    if sucesso:
        logger.info("Execução concluída com sucesso!")
    else:
        logger.error("Execução falhou. Verifique os logs.")
    logger.info("=" * 60)

    return 0 if sucesso else 1


if __name__ == "__main__":
    sys.exit(main())
