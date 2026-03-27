"""Classe base para todos os Page Objects do Salic"""

import logging
import os

from playwright.sync_api import Page

from ..paths import SCREENSHOTS_DIR


class BasePage:
    """Classe base que fornece comportamentos compartilhados por todas as páginas.

    Centraliza operações presentes no cabeçalho/rodapé global do site,
    como o menu de Perfil e o logout.
    """

    # Seletores do menu de Perfil no cabeçalho (presente em todas as páginas)
    DROPDOWN_PERFIL = 'a.dropdown-button[data-activates="dropdown1"]'
    LINK_SAIR = "#sairSistema"

    # Modal de confirmação de logout (jQuery UI dialog)
    MODAL_CONFIRMAR_LOGOUT = "#dialog-confirm"
    BOTAO_SIM = '.ui-dialog-buttonpane button:has-text("Sim")'

    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(type(self).__name__)

    def fazer_logout(self) -> bool:
        """Realiza o logout através do menu de Perfil no cabeçalho.

        Abre o dropdown de Perfil, clica em 'Sair' e confirma
        clicando em 'Sim' no modal de confirmação.

        Returns:
            True se o logout foi realizado com sucesso.
        """
        self.logger.info("Realizando logout via menu 'Perfil'...")
        try:
            # Abre o dropdown do Perfil
            self.page.click(self.DROPDOWN_PERFIL)

            # Aguarda o link "Sair" ficar visível e clica
            self.page.wait_for_selector(self.LINK_SAIR, state="visible", timeout=5000)
            self.page.locator(self.LINK_SAIR).click()

            # Aguarda o modal de confirmação aparecer e clica em "Sim"
            self.page.wait_for_selector(
                self.MODAL_CONFIRMAR_LOGOUT, state="visible", timeout=5000
            )
            self.page.locator(self.BOTAO_SIM).click()

            # Aguarda o redirecionamento pós-logout
            self.page.wait_for_load_state("networkidle")

            self.logger.info("Logout realizado com sucesso!")
            return True

        except Exception as e:
            self.logger.error("Erro ao realizar logout: %s", e)
            self.page.screenshot(
                path=os.path.join(SCREENSHOTS_DIR, "erro_logout.png"),
                full_page=True,
            )
            return False
