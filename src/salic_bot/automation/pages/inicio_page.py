"""Page Object para a tela inicial do Salic (comunicados-proponente)"""

import os

from playwright.sync_api import Page

from ...config import SCREENSHOTS_DIR
from ..base_page import BasePage


class InicioPage(BasePage):
    """Page Object para a tela inicial do Salic após o login"""

    # Seletores
    MENU_PROJETO = 'a.dropdown-button[data-activates="projeto"]'
    LINK_LISTAR_PROJETOS = 'a[title="Ir para Listar Projetos"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def navegar_para_listar_projetos(self):
        """
        Abre o menu 'Projeto' no topo e clica em 'Listar Projetos'

        Returns:
            True se a navegação foi bem-sucedida
        """
        self.logger.info("Abrindo menu 'Projeto'...")
        try:
            # Aguarda o menu estar disponível
            self.page.wait_for_selector(self.MENU_PROJETO)

            # Clica no menu "Projeto" para abrir o dropdown
            self.page.click(self.MENU_PROJETO)

            # Aguarda o item "Listar Projetos" ficar visível e clica
            self.page.wait_for_selector(self.LINK_LISTAR_PROJETOS, state="visible")
            self.page.click(self.LINK_LISTAR_PROJETOS)

            # Aguarda navegação para a página de projetos
            self.page.wait_for_url(
                lambda url: "listar-projetos" in url or "projeto" in url,
                timeout=15000,
            )

            self.logger.info("Navegação para 'Listar Projetos' realizada com sucesso!")
            return True

        except Exception as e:
            self.logger.error("Erro ao navegar para 'Listar Projetos': %s", e)
            self.page.screenshot(
                path=os.path.join(SCREENSHOTS_DIR, "erro_listar_projetos.png"),
                full_page=True,
            )
            return False
