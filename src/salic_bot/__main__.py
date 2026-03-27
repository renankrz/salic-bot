"""Entry point para execução via CLI ou GUI"""

import argparse
import logging
import os
import sys

from .bot import SalicBot
from .logging_setup import configurar_logging
from .models.projeto import Projeto
from .paths import LOGS_DIR, SCREENSHOTS_DIR
from .settings import ConfigManager

logger = logging.getLogger(__name__)


def _run_cli(args: argparse.Namespace) -> int:
    """Executa o bot via linha de comando"""
    config = ConfigManager()

    mecanismo = config.get_for_cli("mecanismo", args.mecanismo)
    proponente = config.get_for_cli("proponente", args.proponente)
    pronac = config.get_for_cli("pronac", args.pronac)
    clientes_dir = config.get_for_cli("clientes_dir", args.clientes_dir)
    cpf = config.get_for_cli("cpf", args.cpf)
    senha = config.get_for_cli("senha", args.senha)

    erros = []
    if not proponente:
        erros.append("Proponente é obrigatório (--proponente ou .env ou QSettings)")
    if not pronac:
        erros.append("PRONAC é obrigatório (--pronac ou .env ou QSettings)")
    if not clientes_dir:
        erros.append(
            "Pasta de clientes é obrigatória (--clientes-dir ou .env ou QSettings)"
        )
    if not cpf:
        erros.append("CPF é obrigatório (--cpf ou .env ou keyring)")
    if not senha:
        erros.append("Senha é obrigatória (--senha ou .env ou keyring)")

    if erros:
        for erro in erros:
            logger.error(erro)
        return 1

    projeto = Projeto(
        mecanismo=mecanismo,
        proponente=proponente,
        pronac=int(pronac),
    )

    headless = os.getenv("HEADLESS", "False").lower() == "true"
    slow_mo = int(os.getenv("SLOW_MO", "100"))

    logger.info("=" * 60)
    logger.info("Salic Bot - Automação de Prestação de Contas")
    logger.info("=" * 60)
    logger.info(
        "Iniciando execução | mecanismo=%s | proponente=%s | pronac=%s",
        mecanismo,
        proponente,
        pronac,
    )

    bot = SalicBot(
        headless=headless,
        slow_mo=slow_mo,
        projeto=projeto,
        clientes_dir=clientes_dir,
        cpf=cpf,
        senha=senha,
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

    # Se não houver argumentos nomeados, abre a GUI
    if len(sys.argv) == 1:
        from .gui.main_window import iniciar_gui

        return iniciar_gui()

    # CLI
    configurar_logging(logs_dir=LOGS_DIR)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Salic Bot - Automação de Prestação de Contas"
    )
    parser.add_argument(
        "--mecanismo", default=None, help="Mecanismo do projeto (ex: Mecenato)"
    )
    parser.add_argument(
        "--proponente", default=None, help="CNPJ do proponente (somente dígitos)"
    )
    parser.add_argument("--pronac", default=None, help="PRONAC do projeto")
    parser.add_argument("--clientes-dir", default=None, help="Pasta raiz de clientes")
    parser.add_argument("--cpf", default=None, help="CPF do usuário (somente dígitos)")
    parser.add_argument("--senha", default=None, help="Senha do usuário")
    args = parser.parse_args()

    return _run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
