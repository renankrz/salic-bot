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
    itens_csv = config.get_for_cli("itens_csv", args.itens_csv)
    comprovantes_dir = config.get_for_cli("comprovantes_dir", args.comprovantes_dir)
    cpf = config.get_for_cli("cpf", args.cpf)
    senha = config.get_for_cli("senha", args.senha)

    erros = []
    if not proponente:
        erros.append("Proponente é obrigatório (--proponente ou .env ou QSettings)")
    if not pronac:
        erros.append("PRONAC é obrigatório (--pronac ou .env ou QSettings)")
    if not itens_csv:
        erros.append(
            "CSV com itens de custo é obrigatório (--itens-csv ou .env ou QSettings)"
        )
    if not comprovantes_dir:
        erros.append(
            "Pasta de comprovantes é obrigatória (--comprovantes-dir ou .env ou QSettings)"
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
    if args.dry:
        logger.info("Modo DRY RUN ativado — comprovantes NÃO serão salvos")
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
        itens_csv=itens_csv,
        comprovantes_dir=comprovantes_dir,
        cpf=cpf,
        senha=senha,
        dry_run=args.dry,
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
    parser.add_argument(
        "--itens-csv", default=None, help="Caminho para o CSV com itens de custo"
    )
    parser.add_argument(
        "--comprovantes-dir", default=None, help="Pasta de comprovantes (PDFs)"
    )
    parser.add_argument("--cpf", default=None, help="CPF do usuário (somente dígitos)")
    parser.add_argument("--senha", default=None, help="Senha do usuário")
    parser.add_argument(
        "--dry",
        action="store_true",
        default=False,
        help="Dry run: cancela em vez de salvar cada comprovante",
    )
    args = parser.parse_args()

    return _run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
