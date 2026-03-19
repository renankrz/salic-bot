"""Lógica principal do bot"""

import os

from dotenv import load_dotenv
from playwright.sync_api import Page

from .automation.base_page import BasePage
from .automation.browser import BrowserManager
from .automation.pages.inicio_page import InicioPage
from .automation.pages.login_page import LoginPage
from .automation.pages.project_page import ProjectPage
from .automation.pages.projects_page import ProjectsPage
from .models.projeto import Projeto
from .utils.csv_tools import ler_csv
from .utils.drive_manager import localizar_csv_execucao_financeira


class SalicBot:
    """Bot principal para automação do Salic"""

    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 0,
        projeto: Projeto = None,
        clientes_dir: str = None,
    ):
        """
        Inicializa o bot

        Args:
            headless: Se deve rodar sem interface gráfica
            slow_mo: Delay entre ações em ms (para debug)
            projeto: Dados do projeto a ser selecionado
            clientes_dir: Caminho para a pasta raiz de clientes
        """
        self.browser_manager = BrowserManager(headless=headless, slow_mo=slow_mo)
        self.page: Page = None
        self.projeto_page: Page = None
        self.pagina_atual: Page = None
        self.projeto = projeto
        self.clientes_dir = clientes_dir

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
        self.pagina_atual = self.page
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

    def selecionar_projeto(self) -> bool:
        """
        Executa a seleção do projeto na página de projetos.
        Armazena a nova aba aberta em self.projeto_page.

        Returns:
            True se o projeto foi selecionado com sucesso.
        """
        if not self.page:
            raise RuntimeError("Navegador não foi iniciado. Chame iniciar() primeiro.")

        projeto = self.projeto
        print(
            f"Projeto carregado: PRONAC {projeto.pronac} | {projeto.mecanismo} | {projeto.proponente}"
        )

        projects_page = ProjectsPage(self.page)
        nova_pagina = projects_page.selecionar_projeto(projeto)

        if nova_pagina:
            self.projeto_page = nova_pagina
            self.pagina_atual = nova_pagina
            print("🎉 Projeto selecionado com sucesso!")
            return True
        else:
            print("❌ Falha ao selecionar projeto")
            return False

    def navegar_para_comprovacao_financeira(self) -> bool:
        """
        Na página do projeto (nova aba), clica em 'Comprovação Financeira'
        no menu da esquerda.

        Returns:
            True se a navegação foi bem-sucedida.
        """
        if not self.projeto_page:
            raise RuntimeError(
                "Página do projeto não está disponível. "
                "Chame selecionar_projeto() primeiro."
            )

        project_page = ProjectPage(self.projeto_page)
        sucesso = project_page.clicar_comprovacao_financeira()

        if sucesso:
            print("🎉 Navegação para 'Comprovação Financeira' realizada com sucesso!")
        else:
            print("❌ Falha ao navegar para 'Comprovação Financeira'")

        return sucesso

    def carregar_dados_financeiros(self) -> bool:
        """
        Localiza e lê o CSV de execução financeira a partir da pasta de clientes.

        Returns:
            True se o CSV foi lido com sucesso.
        """
        try:
            csv_path = localizar_csv_execucao_financeira(
                self.clientes_dir,
                self.projeto.proponente,
                self.projeto.pronac,
            )
            print(f"📄 CSV de execução financeira encontrado: {csv_path}")

            df = ler_csv(csv_path)

            print(f"📊 Dados de execução financeira ({len(df)} linha(s)):")
            print(df.to_string(index=True))

            return True
        except FileNotFoundError as e:
            print(f"❌ Arquivo não encontrado: {e}")
            return False
        except Exception as e:
            print(f"❌ Erro ao carregar dados financeiros: {e}")
            return False

    def fazer_logout(self) -> bool:
        """
        Realiza o logout através do menu de Perfil da página atual.

        Returns:
            True se o logout foi realizado com sucesso.
        """
        if not self.pagina_atual:
            raise RuntimeError("Nenhuma página ativa. Chame iniciar() primeiro.")

        sucesso = BasePage(self.pagina_atual).fazer_logout()

        if sucesso:
            print("🎉 Logout realizado com sucesso!")
        else:
            print("❌ Falha ao realizar logout")

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

            if not self.selecionar_projeto():
                print("❌ Falha ao selecionar projeto")
                return False

            if not self.navegar_para_comprovacao_financeira():
                print("❌ Falha ao navegar para Comprovação Financeira")
                return False

            # Aguarda 5 segundos na página de Comprovação Financeira
            print("Aguardando 5 segundos na página de Comprovação Financeira...")
            self.projeto_page.wait_for_timeout(5000)

            if not self.carregar_dados_financeiros():
                print("❌ Falha ao carregar dados de execução financeira")
                return False

            if not self.fazer_logout():
                print("❌ Falha ao realizar logout")
                return False

            # Aguarda 5 segundos após o logout antes de fechar o navegador
            print("Aguardando 5 segundos antes de fechar o navegador...")
            self.projeto_page.wait_for_timeout(5000)

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
