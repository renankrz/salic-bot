"""Lógica principal do bot"""

import os

from dotenv import load_dotenv
from playwright.sync_api import Page

from .automation.browser import BrowserManager
from .automation.pages.inicio_page import InicioPage
from .automation.pages.login_page import LoginPage


class SalicBot:
    """Bot principal para automação do Salic"""

    def __init__(self, headless: bool = True, slow_mo: int = 0):
        """
        Inicializa o bot

        Args:
            headless: Se deve rodar sem interface gráfica
            slow_mo: Delay entre ações em ms (para debug)
        """
        self.browser_manager = BrowserManager(headless=headless, slow_mo=slow_mo)
        self.page: Page = None

        # Carrega variáveis de ambiente
        load_dotenv()
        self.cpf = os.getenv("cpf") or os.getenv("USER_CPF")
        self.senha = os.getenv("senha") or os.getenv("USER_SENHA")

        if not self.cpf or not self.senha:
            raise ValueError("cpf e senha devem estar definidos no .env")

    def iniciar(self):
        """Inicia o navegador"""
        print("🚀 Iniciando Salic Bot...")
        self.page = self.browser_manager.start()
        print("✅ Navegador iniciado")

        # Cria pasta de screenshots
        os.makedirs("screenshots", exist_ok=True)

    def fazer_login(self) -> bool:
        """
        Realiza login no Salic

        Returns:
            True se login foi bem-sucedido
        """
        if not self.page:
            raise RuntimeError("Navegador não foi iniciado. Chame iniciar() primeiro.")

        login_page = LoginPage(self.page)
        login_page.acessar()

        sucesso = login_page.fazer_login(self.cpf, self.senha)

        if sucesso:
            print("🎉 Login realizado com sucesso!")
        else:
            print("❌ Falha no login")

        return sucesso

    def navegar_para_projetos(self) -> bool:
        """
        Na tela inicial, abre o menu 'Projeto' e clica em 'Listar Projetos'

        Returns:
            True se a navegação foi bem-sucedida
        """
        if not self.page:
            raise RuntimeError("Navegador não foi iniciado. Chame iniciar() primeiro.")

        inicio_page = InicioPage(self.page)
        sucesso = inicio_page.navegar_para_listar_projetos()

        if sucesso:
            print("🎉 Navegação para projetos realizada com sucesso!")
        else:
            print("❌ Falha ao navegar para projetos")

        return sucesso

    def fechar(self):
        """Fecha o navegador"""
        print("Fechando navegador...")
        self.browser_manager.close()
        print("✅ Navegador fechado")

    def executar(self):
        """Executa fluxo completo do bot"""
        try:
            self.iniciar()

            if not self.fazer_login():
                print("❌ Falha na execução do bot")
                return False

            if not self.navegar_para_projetos():
                print("❌ Falha ao navegar para projetos")
                return False

            print("✅ Bot executado com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro na execução: {str(e)}")
            if self.page:
                self.page.screenshot(path="screenshots/erro_execucao.png")
            return False

        finally:
            self.fechar()

    def __enter__(self):
        """Context manager"""
        self.iniciar()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.fechar()
