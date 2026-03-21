"""Page Object para tela de login do Salic"""

import os
import time

from playwright.sync_api import Page

from ...config import SCREENSHOTS_DIR
from ..base_page import BasePage


class LoginPage(BasePage):
    """Page Object para login no Salic"""

    # URL
    URL = "https://salic.cultura.gov.br/autenticacao/index/index/"

    # Seletores
    INPUT_CPF = 'input[name="Login"]'
    INPUT_SENHA = 'input[name="Senha"]'
    BTN_ENTRAR = 'button[type="submit"]#btConfirmar'

    def __init__(self, page: Page):
        super().__init__(page)

    def acessar(self):
        """Acessa página de login"""
        self.logger.info("Acessando página de login do Salic")
        self.page.goto(self.URL)

        # Aguarda formulário carregar
        self.page.wait_for_selector(self.INPUT_CPF)
        self.logger.info("Página de login carregada")

    def fazer_login(self, cpf: str, senha: str):
        """
        Realiza login no SALIC

        Args:
            cpf: CPF do usuário (pode ser com ou sem formatação)
            senha: Senha do usuário
        """
        self.logger.info("Realizando login com CPF %s.***.**-**", cpf[:3])

        # Remove formatação do CPF se houver
        cpf_limpo = cpf.replace(".", "").replace("-", "")

        # Preenche campos
        self.page.fill(self.INPUT_CPF, cpf_limpo)
        time.sleep(0.5)

        self.page.fill(self.INPUT_SENHA, senha)
        time.sleep(0.5)

        # Clica em entrar
        self.page.click(self.BTN_ENTRAR)

        # Aguarda navegação para fora da tela de autenticação
        self.logger.info("Aguardando login...")
        try:
            self.page.wait_for_url(
                lambda url: "autenticacao" not in url,
                timeout=15000,
            )
            self.logger.info("Login realizado com sucesso!")
            return True

        except Exception as e:
            self.logger.error("Erro no login: %s", e)
            self.page.screenshot(
                path=os.path.join(SCREENSHOTS_DIR, "login_erro.png"),
                full_page=True,
            )
            return False
