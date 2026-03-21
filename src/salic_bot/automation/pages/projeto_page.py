"""Page Object para a tela de um Projeto específico do Salic"""

import os

from playwright.sync_api import Page

from ...config import SCREENSHOTS_DIR
from ..base_page import BasePage


class ProjetoPage(BasePage):
    """Page Object para a página de visualização de um projeto no Salic.

    Esta página é aberta em uma nova aba ao clicar no PRONAC na lista de
    projetos. Contém o menu lateral de navegação do projeto.
    """

    # Seletor para o item "Comprovação Financeira" no menu lateral
    LINK_COMPROVACAO_FINANCEIRA = "#sidenav li.bold a"

    def __init__(self, page: Page):
        super().__init__(page)

    def clicar_comprovacao_financeira(self) -> bool:
        """Clica em 'Comprovação Financeira' no menu da esquerda.

        Returns:
            True se o clique foi realizado com sucesso.
        """
        self.logger.info("Clicando em 'Comprovação Financeira'...")
        try:
            # Aguarda o menu lateral estar carregado
            self.page.wait_for_selector(self.LINK_COMPROVACAO_FINANCEIRA, timeout=15000)

            # Localiza o link pelo texto dentro do menu lateral
            link = self.page.locator(
                self.LINK_COMPROVACAO_FINANCEIRA,
                has_text="Comprovação Financeira",
            )
            link.click()

            self.page.wait_for_load_state("networkidle")
            self.logger.info("'Comprovação Financeira' clicado com sucesso!")
            return True

        except Exception as e:
            self.logger.error("Erro ao clicar em 'Comprovação Financeira': %s", e)
            self.page.screenshot(
                path=os.path.join(SCREENSHOTS_DIR, "erro_comprovacao_financeira.png"),
                full_page=True,
            )
            return False
