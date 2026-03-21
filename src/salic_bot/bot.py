"""Lógica principal do bot"""

import logging
import os

from dotenv import load_dotenv
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

from .automation.base_page import BasePage
from .automation.browser import BrowserManager
from .automation.pages.comprovacao_financeira_page import ComprovacaoFinanceiraPage
from .automation.pages.comprovantes_page import ComprovantesPage
from .automation.pages.inicio_page import InicioPage
from .automation.pages.login_page import LoginPage
from .automation.pages.projeto_page import ProjetoPage
from .automation.pages.projetos_page import ProjetosPage
from .models.projeto import Projeto
from .utils.csv_tools import ler_csv
from .utils.drive_manager import (
    encontrar_pdf_comprovante,
    localizar_csv_execucao_financeira,
    localizar_pasta_execucao,
)
from .utils.formatters import safe_str


class SalicBot:
    """Bot para automação do Salic"""

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
        logger.info("Iniciando Salic Bot...")
        self.page = self.browser_manager.start()
        self.pagina_atual = self.page
        logger.info("Navegador iniciado")

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
            logger.info("Login realizado com sucesso!")
        else:
            logger.error("Falha no login")

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
            logger.info("Navegação para projetos realizada com sucesso!")
        else:
            logger.error("Falha ao navegar para projetos")

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
        logger.info(
            "Projeto carregado: PRONAC %s | %s | %s",
            projeto.pronac,
            projeto.mecanismo,
            projeto.proponente,
        )

        projetos_page = ProjetosPage(self.page)
        nova_pagina = projetos_page.selecionar_projeto(projeto)

        if nova_pagina:
            self.projeto_page = nova_pagina
            self.pagina_atual = nova_pagina
            logger.info("Projeto selecionado com sucesso!")
            return True
        else:
            logger.error("Falha ao selecionar projeto")
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

        projeto_page = ProjetoPage(self.projeto_page)
        sucesso = projeto_page.clicar_comprovacao_financeira()

        if sucesso:
            logger.info(
                "Navegação para 'Comprovação Financeira' realizada com sucesso!"
            )
        else:
            logger.error("Falha ao navegar para 'Comprovação Financeira'")

        return sucesso

    def navegar_para_comprovantes(self) -> bool:
        """
        Lê a primeira linha do CSV de execução financeira, navega pelo accordion
        de Comprovação Financeira e clica em 'Comprovar item' para o item de custo.

        Returns:
            True se o clique foi realizado com sucesso.
        """
        if not self.projeto_page:
            raise RuntimeError(
                "Página do projeto não está disponível. "
                "Chame selecionar_projeto() primeiro."
            )

        try:
            csv_path = localizar_csv_execucao_financeira(
                self.clientes_dir,
                self.projeto.proponente,
                self.projeto.pronac,
            )
            logger.info("CSV de execução financeira: %s", csv_path)

            df = ler_csv(csv_path)
            linha = df.iloc[0]

            produto = str(linha["Produto"]).strip()
            etapa = str(linha["Etapa"]).strip()
            uf = str(linha["UF"]).strip()
            cidade = str(linha["Cidade"]).strip()
            item_de_custo = str(linha["Item de Custo"]).strip()

        except FileNotFoundError as e:
            logger.error("Arquivo não encontrado: %s", e)
            return False
        except Exception as e:
            logger.error("Erro ao carregar dados financeiros: %s", e)
            return False

        page = ComprovacaoFinanceiraPage(self.projeto_page)
        sucesso = page.navegar_e_clicar_comprovar_item(
            produto=produto,
            etapa=etapa,
            uf=uf,
            cidade=cidade,
            item_de_custo=item_de_custo,
        )

        if sucesso:
            logger.info("Página de Comprovantes acessada com sucesso!")
        else:
            logger.error("Falha ao acessar página de Comprovantes")

        return sucesso

    def processar_todos_itens(self) -> tuple[int, int]:
        """
        Lê todos os itens de custo do CSV de execução financeira e, para cada um:
          1. Navega até a rubrica correta e abre a página de Comprovantes.
          2. Abre o modal de Novo Comprovante.
          3. Preenche os campos com os dados do CSV.
          4. Aguarda 5 segundos e tira um screenshot nomeado sequencialmente.
          5. Cancela o modal.
          6. Volta para a página de Comprovação Financeira.

        Returns:
            Tupla (itens_ok, total) com a contagem de itens processados com
            sucesso e o total de itens.
        """
        if not self.projeto_page:
            raise RuntimeError(
                "Página do projeto não está disponível. "
                "Chame selecionar_projeto() primeiro."
            )

        try:
            csv_path = localizar_csv_execucao_financeira(
                self.clientes_dir,
                self.projeto.proponente,
                self.projeto.pronac,
            )
            logger.info("CSV de execução financeira: %s", csv_path)
            df = ler_csv(csv_path)
            logger.info("Total de itens de custo: %d", len(df))

            execucao_dir = localizar_pasta_execucao(
                self.clientes_dir,
                self.projeto.proponente,
                self.projeto.pronac,
            )
            logger.info("Pasta de execução financeira: %s", execucao_dir)
        except FileNotFoundError as e:
            logger.error("Arquivo não encontrado: %s", e)
            return (0, 0)
        except Exception as e:
            logger.error("Erro ao carregar dados financeiros: %s", e)
            return (0, 0)

        cf_page = ComprovacaoFinanceiraPage(self.projeto_page)
        comp_page = ComprovantesPage(self.projeto_page)

        total = len(df)
        itens_ok = 0
        itens_erro = 0

        for idx, linha in df.iterrows():
            numero_item = idx + 1
            produto = str(linha["Produto"]).strip()
            etapa = str(linha["Etapa"]).strip()
            uf = str(linha["UF"]).strip()
            cidade = str(linha["Cidade"]).strip()
            item_de_custo = str(linha["Item de Custo"]).strip()

            logger.info("─── Item %d/%d: %s ───", numero_item, len(df), item_de_custo)

            # 1. Navegar até a rubrica e abrir a página de Comprovantes
            if not cf_page.navegar_e_clicar_comprovar_item(
                produto=produto,
                etapa=etapa,
                uf=uf,
                cidade=cidade,
                item_de_custo=item_de_custo,
            ):
                logger.error("Falha ao navegar para o item %d", numero_item)
                itens_erro += 1
                continue

            # 2. Abrir modal de Novo Comprovante
            if not comp_page.clicar_botao_adicionar():
                logger.error("Falha ao abrir modal no item %d", numero_item)
                comp_page.clicar_voltar()
                itens_erro += 1
                continue

            # 3. Preencher campos do modal
            nr_doc_pagamento = safe_str(linha["Nº Documento Pagamento"])
            arquivo_comprovante = None
            if nr_doc_pagamento:
                try:
                    pdf_path = encontrar_pdf_comprovante(execucao_dir, nr_doc_pagamento)
                    arquivo_comprovante = str(pdf_path)
                    logger.info("PDF do comprovante: %s", arquivo_comprovante)
                except FileNotFoundError as e:
                    logger.error("PDF não encontrado para item %d: %s", numero_item, e)
                    comp_page.clicar_cancelar_modal()
                    comp_page.clicar_voltar()
                    itens_erro += 1
                    continue

            if not comp_page.preencher_modal(
                linha, arquivo_comprovante=arquivo_comprovante
            ):
                logger.error("Falha ao preencher modal no item %d", numero_item)
                comp_page.clicar_cancelar_modal()
                comp_page.clicar_voltar()
                itens_erro += 1
                continue

            # 4. Aguardar 5 segundos e tirar screenshot
            logger.info("Aguardando 5 segundos (item %d)...", numero_item)
            self.projeto_page.wait_for_timeout(5000)
            screenshot_path = f"screenshots/item_{numero_item}.png"
            self.projeto_page.screenshot(path=screenshot_path, full_page=True)
            logger.info("Screenshot salvo: %s", screenshot_path)

            # 5. Cancelar modal
            if not comp_page.clicar_cancelar_modal():
                logger.error("Falha ao cancelar modal no item %d", numero_item)
                comp_page.clicar_voltar()
                itens_erro += 1
                continue

            # 6. Voltar para Comprovação Financeira
            if not comp_page.clicar_voltar():
                logger.error("Falha ao voltar no item %d", numero_item)
                itens_erro += 1
                continue

            itens_ok += 1

        return (itens_ok, total)

    def abrir_novo_comprovante(self) -> bool:
        """
        Na página de Comprovantes, clica no botão '+' para abrir o modal
        de cadastro de novo comprovante.

        Returns:
            True se o modal foi aberto com sucesso.
        """
        if not self.projeto_page:
            raise RuntimeError(
                "Página do projeto não está disponível. "
                "Chame selecionar_projeto() primeiro."
            )

        sucesso = ComprovantesPage(self.projeto_page).clicar_botao_adicionar()

        if sucesso:
            logger.info("Modal 'Cadastrar novo comprovante' aberto com sucesso!")
        else:
            logger.error("Falha ao abrir modal de novo comprovante")

        return sucesso

    def cancelar_novo_comprovante(self) -> bool:
        """
        No modal de novo comprovante, clica em 'CANCELAR' para fechá-lo.

        Returns:
            True se o modal foi fechado com sucesso.
        """
        if not self.projeto_page:
            raise RuntimeError(
                "Página do projeto não está disponível. "
                "Chame selecionar_projeto() primeiro."
            )

        sucesso = ComprovantesPage(self.projeto_page).clicar_cancelar_modal()

        if sucesso:
            logger.info("Modal cancelado com sucesso!")
        else:
            logger.error("Falha ao cancelar modal")

        return sucesso

    def voltar_de_comprovantes(self) -> bool:
        """
        Na página de Comprovantes, clica na seta 'Voltar' para retornar
        à página de Comprovação Financeira.

        Returns:
            True se a navegação de volta foi realizada com sucesso.
        """
        if not self.projeto_page:
            raise RuntimeError(
                "Página do projeto não está disponível. "
                "Chame selecionar_projeto() primeiro."
            )

        sucesso = ComprovantesPage(self.projeto_page).clicar_voltar()

        if sucesso:
            logger.info("Voltou da página de Comprovantes com sucesso!")
        else:
            logger.error("Falha ao voltar da página de Comprovantes")

        return sucesso

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
            logger.info("Logout realizado com sucesso!")
        else:
            logger.error("Falha ao realizar logout")

        return sucesso

    def fechar(self):
        """Fecha o navegador"""
        logger.info("Fechando navegador...")
        self.browser_manager.close()
        logger.info("Navegador fechado")

    def executar(self) -> tuple[int, int]:
        """Executa fluxo completo do bot.

        Returns:
            Tupla (itens_ok, total) com a contagem de itens processados
            com sucesso e o total de itens. Retorna (0, 0) em caso de
            falha antes do processamento de itens.
        """
        try:
            self.iniciar()

            if not self.fazer_login():
                logger.error("Falha na execução do bot")
                return (0, 0)

            if not self.navegar_para_projetos():
                logger.error("Falha ao navegar para projetos")
                return (0, 0)

            if not self.selecionar_projeto():
                logger.error("Falha ao selecionar projeto")
                return (0, 0)

            if not self.navegar_para_comprovacao_financeira():
                logger.error("Falha ao navegar para Comprovação Financeira")
                return (0, 0)

            itens_ok, total = self.processar_todos_itens()

            # Aguarda 5 segundos na página de Comprovação Financeira
            logger.info("Aguardando 5 segundos na página de Comprovação Financeira...")
            self.projeto_page.wait_for_timeout(5000)

            if not self.fazer_logout():
                logger.error("Falha ao realizar logout")

            # Aguarda 5 segundos após o logout antes de fechar o navegador
            logger.info("Aguardando 5 segundos antes de fechar o navegador...")
            self.projeto_page.wait_for_timeout(5000)
            return (itens_ok, total)

        except Exception as e:
            logger.error("Erro na execução: %s", e, exc_info=True)
            if self.page:
                self.page.screenshot(path="screenshots/erro_execucao.png")
            return (0, 0)

        finally:
            self.fechar()

    def __enter__(self):
        """Context manager"""
        self.iniciar()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.fechar()
