"""Page Object para a tela de um Projeto específico do Salic"""

from playwright.sync_api import Page

from ..base_page import BasePage


class ProjectPage(BasePage):
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
        print("Clicando em 'Comprovação Financeira'...")
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
            self.page.screenshot(
                path="screenshots/comprovacao_financeira.png", full_page=True
            )
            print("✅ 'Comprovação Financeira' clicado com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro ao clicar em 'Comprovação Financeira': {str(e)}")
            self.page.screenshot(
                path="screenshots/erro_comprovacao_financeira.png", full_page=True
            )
            return False
