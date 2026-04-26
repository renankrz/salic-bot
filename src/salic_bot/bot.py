"""Lógica principal do bot"""

import logging
import os

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
from .paths import SCREENSHOTS_DIR
from .utils.csv_tools import PlanilhaDespesas
from .utils.drive_manager import localizar_comprovante


class SalicBot:
    """Bot para automação do Salic"""

    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 0,
        projeto: Projeto = None,
        despesas_csv: str = None,
        comprovantes_dir: str = None,
        cpf: str = None,
        senha: str = None,
        dry_run: bool = False,
    ):
        """
        Inicializa o bot

        Args:
            headless: Se deve rodar sem interface gráfica
            slow_mo: Delay entre ações em ms (para debug)
            projeto: Dados do projeto a ser selecionado
            despesas_csv: Caminho para o CSV de despesas
            comprovantes_dir: Caminho para a pasta de comprovantes
            cpf: CPF do usuário para login
            senha: Senha do usuário para login
            dry_run: Se True, cancela em vez de salvar cada comprovante
        """
        self.browser_manager = BrowserManager(headless=headless, slow_mo=slow_mo)
        self.page: Page = None
        self.projeto_page: Page = None
        self.pagina_atual: Page = None
        self.projeto = projeto
        self.despesas_csv = despesas_csv
        self.comprovantes_dir = comprovantes_dir

        self.cpf = cpf
        self.senha = senha
        self.dry_run = dry_run

        self.planilha: PlanilhaDespesas | None = None

        if not self.cpf or not self.senha:
            raise ValueError("cpf e senha são obrigatórios")

    def iniciar(self):
        """Inicia o navegador"""
        logger.info("Iniciando Salic Bot...")
        self.page = self.browser_manager.start()
        self.pagina_atual = self.page
        logger.info("Navegador iniciado")

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

    def processar_todas_despesas(self) -> tuple[int, int]:
        """
        Processa as despesas previamente carregadas em ``self.planilha``.
        Para cada despesa não incluída:

          1. Verifica se já foi incluída ou tem valor inválido na coluna
             ``incluída``.
          2. Navega até a rubrica correta e abre a página de Comprovantes.
          3. Abre o modal de Novo Comprovante.
          4. Preenche os campos com os dados do CSV.
          5. Tira um screenshot nomeado sequencialmente.
          6. Salva ou cancela (dry run) o comprovante.
          7. Volta para a página de Comprovação Financeira.

        Ao final, salva o CSV atualizado com os resultados (``incluída``
        e ``erro``).

        Returns:
            Tupla (despesas_ok, total) com a contagem de despesas incluídas
            com sucesso (incluindo as previamente incluídas) e o total.
        """
        if not self.projeto_page:
            raise RuntimeError(
                "Página do projeto não está disponível. "
                "Chame selecionar_projeto() primeiro."
            )

        cf_page = ComprovacaoFinanceiraPage(self.projeto_page)
        comp_page = ComprovantesPage(self.projeto_page)

        planilha = self.planilha
        total = len(planilha)
        despesas_ok = 0

        for idx, despesa in enumerate(planilha.despesas):
            numero_despesa = idx + 1
            produto = despesa.produto
            etapa = despesa.etapa
            uf = despesa.uf
            cidade = despesa.cidade
            item_de_custo = despesa.item_de_custo

            logger.info(
                "─── Despesa %d/%d: %s ───", numero_despesa, total, item_de_custo
            )

            # Verificar coluna "incluída"
            try:
                if planilha.ja_incluida(idx):
                    logger.info(
                        "Despesa %d/%d já incluída, pulando", numero_despesa, total
                    )
                    despesas_ok += 1
                    continue
            except ValueError as e:
                logger.error(str(e))
                planilha.marcar_erro(idx, str(e))
                continue

            # 1. Navegar até a rubrica e abrir a página de Comprovantes
            if not cf_page.encontrar_rubrica_e_clicar_comprovar_item(
                produto=produto,
                etapa=etapa,
                uf=uf,
                cidade=cidade,
                item_de_custo=item_de_custo,
            ):
                msg = (
                    f"Rubrica não encontrada: {produto} / {etapa} / {uf} / "
                    f"{cidade} / {item_de_custo}"
                )
                logger.error("Falha ao navegar para a despesa %d", numero_despesa)
                self.projeto_page.screenshot(
                    path=os.path.join(
                        SCREENSHOTS_DIR, f"erro_despesa_{numero_despesa}_navegacao.png"
                    ),
                    full_page=True,
                )
                planilha.marcar_erro(idx, msg)
                continue

            # 2. Abrir modal de Novo Comprovante
            if not comp_page.clicar_botao_adicionar():
                msg = "Falha ao abrir modal de novo comprovante"
                logger.error("Falha ao abrir modal na despesa %d", numero_despesa)
                self.projeto_page.screenshot(
                    path=os.path.join(
                        SCREENSHOTS_DIR,
                        f"erro_despesa_{numero_despesa}_abrir_modal.png",
                    ),
                    full_page=True,
                )
                comp_page.clicar_voltar()
                planilha.marcar_erro(idx, msg)
                continue

            # 3. Preencher campos do modal
            data_emissao = despesa.data_de_emissao
            numero_nf = despesa.numero
            arquivo_comprovante = None
            if data_emissao and numero_nf:
                try:
                    pdf_path = localizar_comprovante(
                        self.comprovantes_dir, data_emissao, numero_nf
                    )
                    arquivo_comprovante = str(pdf_path)
                    logger.info("PDF do comprovante: %s", arquivo_comprovante)
                except FileNotFoundError as e:
                    msg = str(e)
                    logger.error(
                        "Comprovante não encontrado para despesa %d: %s",
                        numero_despesa,
                        e,
                    )
                    comp_page.clicar_cancelar_modal()
                    comp_page.clicar_voltar()
                    planilha.marcar_erro(idx, msg)
                    continue

            if not comp_page.preencher_modal(
                despesa, arquivo_comprovante=arquivo_comprovante
            ):
                msg = "Falha ao preencher formulário do comprovante"
                logger.error("Falha ao preencher modal na despesa %d", numero_despesa)
                self.projeto_page.screenshot(
                    path=os.path.join(
                        SCREENSHOTS_DIR, f"erro_despesa_{numero_despesa}_preencher.png"
                    ),
                    full_page=True,
                )
                comp_page.clicar_cancelar_modal()
                comp_page.clicar_voltar()
                planilha.marcar_erro(idx, msg)
                continue

            # 4. Tirar screenshot
            screenshot_path = os.path.join(
                SCREENSHOTS_DIR, f"despesa_{numero_despesa}.png"
            )
            self.projeto_page.screenshot(path=screenshot_path, full_page=True)
            logger.info("Screenshot salvo: %s", screenshot_path)

            # 5. Salvar ou cancelar comprovante (dry run)
            if self.dry_run:
                logger.info(
                    "DRY RUN: cancelando despesa %d/%d (%s) em vez de salvar",
                    numero_despesa,
                    total,
                    item_de_custo,
                )
                comp_page.clicar_cancelar_modal()
            else:
                salvo = comp_page.clicar_salvar_modal()
                if not salvo:
                    if (
                        comp_page.ultimo_alert
                        and ComprovantesPage.ALERT_JUSTIFICATIVA
                        in comp_page.ultimo_alert
                    ):
                        msg = (
                            "Justificativa obrigatória ausente: o valor ultrapassa "
                            "o permitido e o campo Justificativa não foi preenchido"
                        )
                        logger.error(
                            "Despesa %d/%d (%s): %s",
                            numero_despesa,
                            total,
                            item_de_custo,
                            msg,
                        )
                    else:
                        msg = (
                            f"Erro ao salvar comprovante: "
                            f"{comp_page.ultimo_alert or 'erro desconhecido'}"
                        )
                        logger.error(
                            "Despesa %d/%d (%s): %s",
                            numero_despesa,
                            total,
                            item_de_custo,
                            msg,
                        )
                    self.projeto_page.screenshot(
                        path=os.path.join(
                            SCREENSHOTS_DIR,
                            f"erro_despesa_{numero_despesa}_salvar.png",
                        ),
                        full_page=True,
                    )
                    comp_page.clicar_cancelar_modal()
                    comp_page.clicar_voltar()
                    planilha.marcar_erro(idx, msg)
                    continue

            # 6. Voltar para Comprovação Financeira
            if not comp_page.clicar_voltar():
                msg = "Falha ao voltar para página de comprovação financeira"
                logger.error("Falha ao voltar na despesa %d", numero_despesa)
                self.projeto_page.screenshot(
                    path=os.path.join(
                        SCREENSHOTS_DIR, f"erro_despesa_{numero_despesa}_voltar.png"
                    ),
                    full_page=True,
                )
                planilha.marcar_erro(idx, msg)
                continue

            # Sucesso
            if not self.dry_run:
                planilha.marcar_incluida(idx)
            despesas_ok += 1

        # Salvar CSV com resultados
        planilha.salvar()

        return (despesas_ok, total)

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

    def _marcar_todas_despesas_erro(self, mensagem: str) -> None:
        """Marca todas as despesas do CSV como não incluídas e registra o erro.

        Salva o CSV atualizado em disco.

        Args:
            mensagem: Mensagem de erro a ser registrada em todas as linhas.
        """
        self.planilha.marcar_todas_erro(mensagem)
        self.planilha.salvar()

    def executar(self) -> tuple[int, int]:
        """Executa fluxo completo do bot.

        Lê o CSV de despesas antes de iniciar a navegação, de modo que
        erros gerais (login, navegação, etc.) possam ser registrados em
        todas as linhas do CSV.

        Returns:
            Tupla (despesas_ok, total) com a contagem de despesas incluídas
            com sucesso e o total de despesas. Retorna (0, 0) quando o CSV
            não pôde ser lido.
        """
        try:
            # Ler CSV antes de tudo para poder registrar erros gerais
            try:
                logger.info("CSV de despesas: %s", self.despesas_csv)
                self.planilha = PlanilhaDespesas(self.despesas_csv)
                logger.info("Total de despesas: %d", len(self.planilha))
                logger.info("Pasta de comprovantes: %s", self.comprovantes_dir)
            except FileNotFoundError as e:
                logger.error("Arquivo não encontrado: %s", e)
                return (0, 0)
            except Exception as e:
                logger.error("Erro ao carregar dados financeiros: %s", e)
                return (0, 0)

            self.iniciar()

            if not self.fazer_login():
                msg = "Falha no login"
                logger.error("Falha na execução do bot")
                self._marcar_todas_despesas_erro(msg)
                return (0, len(self.planilha))

            if not self.navegar_para_projetos():
                msg = "Falha ao navegar para projetos"
                logger.error(msg)
                self._marcar_todas_despesas_erro(msg)
                return (0, len(self.planilha))

            if not self.selecionar_projeto():
                msg = "Falha ao selecionar projeto"
                logger.error(msg)
                self._marcar_todas_despesas_erro(msg)
                return (0, len(self.planilha))

            if not self.navegar_para_comprovacao_financeira():
                msg = "Falha ao navegar para Comprovação Financeira"
                logger.error(msg)
                self._marcar_todas_despesas_erro(msg)
                return (0, len(self.planilha))

            despesas_ok, total = self.processar_todas_despesas()

            if not self.fazer_logout():
                logger.error("Falha ao realizar logout")

            return (despesas_ok, total)

        except Exception as e:
            logger.error("Erro na execução: %s", e, exc_info=True)
            if self.planilha is not None:
                self._marcar_todas_despesas_erro(str(e))
            if self.projeto_page:
                self.projeto_page.screenshot(
                    path=os.path.join(SCREENSHOTS_DIR, "erro_execucao_projeto.png"),
                    full_page=True,
                )
            if self.page:
                self.page.screenshot(
                    path=os.path.join(SCREENSHOTS_DIR, "erro_execucao.png")
                )
            total = len(self.planilha) if self.planilha else 0
            return (0, total)

        finally:
            self.fechar()

    def __enter__(self):
        """Context manager"""
        self.iniciar()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.fechar()
