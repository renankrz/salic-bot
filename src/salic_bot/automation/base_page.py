"""Classe base para todos os Page Objects do Salic"""

from playwright.sync_api import Page


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

    def fazer_logout(self) -> bool:
        """Realiza o logout através do menu de Perfil no cabeçalho.

        Abre o dropdown de Perfil, clica em 'Sair' e confirma
        clicando em 'Sim' no modal de confirmação.

        Returns:
            True se o logout foi realizado com sucesso.
        """
        print("Realizando logout via menu 'Perfil'...")
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

            self.page.screenshot(path="screenshots/logout.png", full_page=True)
            print("✅ Logout realizado com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro ao realizar logout: {str(e)}")
            self.page.screenshot(path="screenshots/erro_logout.png", full_page=True)
            return False
