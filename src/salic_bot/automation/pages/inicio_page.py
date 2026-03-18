"""Page Object para a tela inicial do Salic (comunicados-proponente)"""

from playwright.sync_api import Page

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
        print("Abrindo menu 'Projeto'...")
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

            print("✅ Navegação para 'Listar Projetos' realizada com sucesso!")
            self.page.screenshot(path="screenshots/listar_projetos.png", full_page=True)
            return True

        except Exception as e:
            print(f"❌ Erro ao navegar para 'Listar Projetos': {str(e)}")
            self.page.screenshot(
                path="screenshots/erro_listar_projetos.png", full_page=True
            )
            return False
