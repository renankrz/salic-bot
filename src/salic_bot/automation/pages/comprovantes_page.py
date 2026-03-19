"""Page Object para a tela de Comprovantes do Salic"""

from playwright.sync_api import Page

from ..base_page import BasePage


class ComprovantesPage(BasePage):
    """Page Object para a página de Comprovantes no Salic.

    Gerencia as interações na tela de Prestação de Contas: Comprovantes,
    incluindo abertura do modal de novo comprovante, cancelamento e volta.
    """

    BOTAO_ADICIONAR = ".fixed-action-btn a.btn-floating"
    MODAL_NOVO_COMPROVANTE = "#modal1"
    BOTAO_CANCELAR = "#test1 button.btn.white.black-text"
    BOTAO_VOLTAR = "#app-comprovante .page-title a"

    def __init__(self, page: Page):
        super().__init__(page)

    def clicar_botao_adicionar(self) -> bool:
        """Clica no botão '+' para abrir o modal de novo comprovante.

        Returns:
            True se o modal foi aberto com sucesso.
        """
        try:
            print("Clicando no botão '+'...")
            self.page.click(self.BOTAO_ADICIONAR)
            self.page.wait_for_selector(
                self.MODAL_NOVO_COMPROVANTE, state="visible", timeout=10000
            )
            print("✅ Modal 'Cadastrar novo comprovante' aberto!")
            self.page.screenshot(
                path="screenshots/modal_novo_comprovante.png", full_page=True
            )
            return True
        except Exception as e:
            print(f"❌ Erro ao clicar no botão '+': {e}")
            self.page.screenshot(
                path="screenshots/erro_botao_adicionar.png", full_page=True
            )
            return False

    def clicar_cancelar_modal(self) -> bool:
        """Clica no botão 'CANCELAR' no modal de novo comprovante.

        Returns:
            True se o modal foi fechado com sucesso.
        """
        try:
            print("Clicando em 'CANCELAR'...")
            self.page.locator(self.BOTAO_CANCELAR).click()
            self.page.wait_for_selector(
                self.MODAL_NOVO_COMPROVANTE, state="hidden", timeout=10000
            )
            print("✅ Modal fechado!")
            self.page.screenshot(path="screenshots/apos_cancelar.png", full_page=True)
            return True
        except Exception as e:
            print(f"❌ Erro ao clicar em 'CANCELAR': {e}")
            self.page.screenshot(path="screenshots/erro_cancelar.png", full_page=True)
            return False

    def clicar_voltar(self) -> bool:
        """Clica na seta 'Voltar' no topo da página de Comprovantes.

        Returns:
            True se a navegação de volta foi realizada com sucesso.
        """
        try:
            print("Clicando na seta 'Voltar'...")
            self.page.locator(self.BOTAO_VOLTAR).click()
            self.page.wait_for_load_state("networkidle")
            print("✅ Voltou para a página anterior!")
            self.page.screenshot(path="screenshots/apos_voltar.png", full_page=True)
            return True
        except Exception as e:
            print(f"❌ Erro ao clicar em 'Voltar': {e}")
            self.page.screenshot(path="screenshots/erro_voltar.png", full_page=True)
            return False
