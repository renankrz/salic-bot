"""Entry point para execução via CLI"""

import os
import sys

from dotenv import load_dotenv

from .bot import SalicBot


def main():
    """Função principal"""
    load_dotenv()

    headless = os.getenv("HEADLESS", "False").lower() == "true"
    slow_mo = int(os.getenv("SLOW_MO", "100"))

    print("=" * 60)
    print("🎭 Salic Bot - Automação de Prestação de Contas")
    print("=" * 60)
    print()

    bot = SalicBot(headless=headless, slow_mo=slow_mo)
    sucesso = bot.executar()

    print()
    print("=" * 60)
    if sucesso:
        print("✅ Execução concluída com sucesso!")
    else:
        print("❌ Execução falhou. Verifique os logs.")
    print("=" * 60)

    return 0 if sucesso else 1


if __name__ == "__main__":
    sys.exit(main())
