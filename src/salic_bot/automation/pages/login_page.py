"""Page Object para tela de login do Salic"""

import time

from playwright.sync_api import Page


class LoginPage:
    """Page Object para login no Salic"""

    # URL
    URL = "https://salic.cultura.gov.br/autenticacao/index/index/"

    # Seletores
    INPUT_CPF = 'input[name="Login"]'
    INPUT_SENHA = 'input[name="Senha"]'
    BTN_ENTRAR = 'button[type="submit"]#btConfirmar'

    def __init__(self, page: Page):
        self.page = page

    def acessar(self):
        """Acessa página de login"""
        print("Acessando página de login do Salic")
        self.page.goto(self.URL)

        # Aguarda formulário carregar
        self.page.wait_for_selector(self.INPUT_CPF)
        print("Página de login carregada")

    def fazer_login(self, cpf: str, senha: str):
        """
        Realiza login no SALIC

        Args:
            cpf: CPF do usuário (pode ser com ou sem formatação)
            senha: Senha do usuário
        """
        print(f"Realizando login com CPF {cpf[:3]}.***.**-**")

        # Remove formatação do CPF se houver
        cpf_limpo = cpf.replace(".", "").replace("-", "")

        # Preenche campos
        self.page.fill(self.INPUT_CPF, cpf_limpo)
        time.sleep(0.5)

        self.page.fill(self.INPUT_SENHA, senha)
        time.sleep(0.5)

        # Screenshot antes de clicar
        self.page.screenshot(path="screenshots/antes_login.png", full_page=True)

        # Clica em entrar
        self.page.click(self.BTN_ENTRAR)

        # Aguarda navegação para fora da tela de autenticação
        print("Aguardando login...")
        try:
            self.page.wait_for_url(
                lambda url: "autenticacao" not in url,
                timeout=15000,
            )
            print("✅ Login realizado com sucesso!")
            self.page.screenshot(path="screenshots/login_sucesso.png", full_page=True)
            return True

        except Exception as e:
            print(f"❌ Erro no login: {str(e)}")
            self.page.screenshot(path="screenshots/login_erro.png", full_page=True)
            return False
