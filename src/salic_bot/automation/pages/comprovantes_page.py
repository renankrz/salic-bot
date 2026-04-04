"""Page Object para a tela de Comprovantes do Salic"""

import os

from playwright.sync_api import Page

from ...models.despesa import DespesaCSV
from ...paths import SCREENSHOTS_DIR
from ...utils.formatters import formatar_data_br, limpar_ni, limpar_valor_monetario
from ..base_page import BasePage


class ComprovantesPage(BasePage):
    """Page Object para a página de Comprovantes no Salic.

    Gerencia as interações na tela de Prestação de Contas: Comprovantes,
    incluindo abertura do modal de novo comprovante, cancelamento e volta.
    """

    BOTAO_ADICIONAR = ".fixed-action-btn a.btn-floating"
    MODAL_NOVO_COMPROVANTE = "#modal1"
    BOTAO_SALVAR = "#test1 button[type='button'].btn:not(.white)"
    BOTAO_CANCELAR = "#test1 button.btn.white.black-text"
    BOTAO_VOLTAR = "#app-comprovante .page-title a"

    ALERT_JUSTIFICATIVA = "Valor acima do permitido, justificar acrescimo."

    def __init__(self, page: Page):
        super().__init__(page)
        self.ultimo_alert: str | None = None

    def clicar_botao_adicionar(self) -> bool:
        """Clica no botão '+' para abrir o modal de novo comprovante.

        Returns:
            True se o modal foi aberto com sucesso.
        """
        try:
            self.logger.info("Clicando no botão '+'...")
            self.page.click(self.BOTAO_ADICIONAR)
            self.page.wait_for_selector(
                self.MODAL_NOVO_COMPROVANTE, state="visible", timeout=10000
            )
            self.logger.info("Modal 'Cadastrar novo comprovante' aberto!")
            return True
        except Exception as e:
            self.logger.error("Erro ao clicar no botão '+': %s", e)
            self.page.screenshot(
                path=os.path.join(SCREENSHOTS_DIR, "erro_botao_adicionar.png"),
                full_page=True,
            )
            return False

    def clicar_salvar_modal(self) -> bool:
        """Clica no botão 'SALVAR' no modal de novo comprovante.

        Trata o alert do navegador caso o Salic exija justificativa
        ("Valor acima do permitido, justificar acrescimo."). Nesse caso,
        aceita o alert, loga o erro e retorna False.

        O conteúdo do alert fica disponível em ``self.ultimo_alert``
        para que o chamador possa classificar o tipo de erro.

        Returns:
            True se o comprovante foi salvo com sucesso.
        """
        self.ultimo_alert = None

        def _on_dialog(dialog):
            self.ultimo_alert = dialog.message
            dialog.accept()

        try:
            self.logger.info("Clicando em 'SALVAR'...")
            self.page.on("dialog", _on_dialog)
            self.page.locator(self.BOTAO_SALVAR).click()

            # O dialog do navegador é tratado de forma síncrona pelo
            # Playwright: quando click() retorna, o handler _on_dialog
            # já foi executado (se houve alert).
            if self.ultimo_alert:
                self.logger.error("Alert do Salic ao salvar: %s", self.ultimo_alert)
                return False

            # Sem alert → salvo com sucesso; aguarda modal fechar
            self.page.wait_for_selector(
                self.MODAL_NOVO_COMPROVANTE, state="hidden", timeout=15000
            )
            self.logger.info("Comprovante salvo com sucesso!")
            return True

        except Exception as e:
            self.logger.error("Erro ao clicar em 'SALVAR': %s", e)
            self.page.screenshot(
                path=os.path.join(SCREENSHOTS_DIR, "erro_salvar.png"),
                full_page=True,
            )
            return False
        finally:
            self.page.remove_listener("dialog", _on_dialog)

    def clicar_cancelar_modal(self) -> bool:
        """Clica no botão 'CANCELAR' no modal de novo comprovante.

        Returns:
            True se o modal foi fechado com sucesso.
        """
        try:
            self.logger.info("Clicando em 'CANCELAR'...")
            self.page.locator(self.BOTAO_CANCELAR).click()
            self.page.wait_for_selector(
                self.MODAL_NOVO_COMPROVANTE, state="hidden", timeout=10000
            )
            self.logger.info("Modal fechado!")
            return True
        except Exception as e:
            self.logger.error("Erro ao clicar em 'CANCELAR': %s", e)
            self.page.screenshot(
                path=os.path.join(SCREENSHOTS_DIR, "erro_cancelar.png"),
                full_page=True,
            )
            return False

    def clicar_voltar(self) -> bool:
        """Clica no botão 'Voltar' no topo da página de Comprovantes.

        Returns:
            True se a navegação de volta foi realizada com sucesso.
        """
        try:
            self.logger.info("Clicando em 'Voltar'...")
            self.page.locator(self.BOTAO_VOLTAR).click()
            self.page.wait_for_load_state("networkidle")
            self.logger.info("Voltou para a página anterior!")
            return True
        except Exception as e:
            self.logger.error("Erro ao clicar em 'Voltar': %s", e)
            self.page.screenshot(
                path=os.path.join(SCREENSHOTS_DIR, "erro_voltar.png"),
                full_page=True,
            )
            return False

    def preencher_modal(
        self, despesa: DespesaCSV, arquivo_comprovante: str = None
    ) -> bool:
        """Preenche os campos do modal de Novo Comprovante com dados de uma despesa.

        Args:
            despesa: Dados da despesa já limpos e normalizados.
            arquivo_comprovante: Caminho absoluto para o arquivo PDF a ser enviado como comprovante.

        Returns:
            True se o modal foi preenchido com sucesso.
        """
        try:
            # --- Identificação do Contratado ---
            if despesa.cpf:
                tipo_pessoa = "1"
                ni = limpar_ni(despesa.cpf)
                tipo_label = "CPF"
            else:
                tipo_pessoa = "2"
                ni = limpar_ni(despesa.cnpj)
                tipo_label = "CNPJ"

            self.logger.info("  %s: %s", tipo_label, ni)

            # Selecionar radio CPF ou CNPJ (label intercepta o clique; usar force=True)
            radio = self.page.locator(
                f"#test1 input[name='tipoPessoa'][value='{tipo_pessoa}']"
            )
            radio.click(force=True)

            # Preencher campo CPF/CNPJ (usa v-mask; 'type' aciona a máscara corretamente)
            cnpjcpf_input = (
                self.page.locator("#test1 form fieldset")
                .first.locator(".row")
                .nth(1)
                .locator("input[type='text']")
                .first
            )
            cnpjcpf_input.click()
            cnpjcpf_input.fill("")
            cnpjcpf_input.type(ni, delay=30)
            # TAB dispara o blur que aciona pesquisarFornecedor()
            try:
                with self.page.expect_response(
                    lambda r: "buscar-pessoa" in r.url or "agentecadastrado" in r.url,
                    timeout=10000,
                ):
                    cnpjcpf_input.press("Tab")
            except Exception:
                self.logger.debug("pesquisarFornecedor: AJAX response not detected")

            # --- Dados do Comprovante de Despesa ---
            tipo_comp = despesa.tipo_comprovante
            if tipo_comp:
                self.page.select_option("#tpDocumento", label=tipo_comp)
                self.logger.info("  Tipo Comprovante: %s", tipo_comp)

            data_emissao = formatar_data_br(despesa.data_de_emissao)
            if data_emissao:
                self.page.fill("#dataEmissao", data_emissao)
                self.logger.info("  Data de Emissão: %s", data_emissao)

            numero = despesa.numero
            if numero:
                self.page.fill("#nrComprovante", numero)
                self.logger.info("  Número: %s", numero)

            serie = despesa.serie
            if serie:
                self.page.fill("#nrSerie", serie)
                self.logger.info("  Série: %s", serie)

            # --- Upload do Comprovante ---
            if arquivo_comprovante:
                file_input = self.page.locator("#test1 input[type='file']#arquivo")
                file_input.set_input_files(arquivo_comprovante)
                self.logger.info("  Comprovante enviado: %s", arquivo_comprovante)

            # --- Dados do Comprovante Bancário ---
            forma_pag = despesa.forma_de_pagamento
            if forma_pag:
                self.page.select_option("#tpFormaDePagamento", label=forma_pag)
                self.logger.info("  Forma de Pagamento: %s", forma_pag)

            data_pag = formatar_data_br(despesa.data_do_pagamento)
            if data_pag:
                self.page.fill("#dtPagamento", data_pag)
                self.logger.info("  Data do pagamento: %s", data_pag)

            nr_doc = despesa.nr_documento_pagamento
            if nr_doc:
                self.page.fill("#nrDocumentoDePagamento", nr_doc)
                self.logger.info("  Nº Documento Pagamento: %s", nr_doc)

            # Valor: remove formatação → dígitos em centavos; 'type' aciona a máscara
            valor_centavos = limpar_valor_monetario(despesa.valor)
            if valor_centavos:
                valor_field = self.page.locator("#vlComprovado")
                valor_field.click(click_count=3)
                valor_field.type(valor_centavos, delay=30)
                self.logger.info("  Valor (centavos): %s", valor_centavos)

            # --- Justificativa ---
            justif = despesa.justificativa
            if justif:
                self.page.fill("#dsJustificativa", justif)
                self.logger.info("  Justificativa: %s...", justif[:40])

            self.logger.info("Modal preenchido com sucesso!")
            return True

        except Exception as e:
            self.logger.error("Erro ao preencher modal: %s", e)
            self.page.screenshot(
                path=os.path.join(SCREENSHOTS_DIR, "erro_preencher_modal.png"),
                full_page=True,
            )
            return False
