"""Ponto de entrada para o PyInstaller.

Quando o PyInstaller executa __main__.py diretamente, as importações relativas
falham, pois não há pacote pai. Este wrapper importa e executa a função main()
a partir do pacote salic_bot.
"""

import sys

from salic_bot.__main__ import main

sys.exit(main())
