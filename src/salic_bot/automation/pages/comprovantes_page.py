"""Page Object para a tela de Comprovantes do Salic"""

import os

from playwright.sync_api import Page

from ...config import SCREENSHOTS_DIR
from ...utils.formatters import (
    formatar_data_br,
    limpar_documento,
    limpar_valor_monetario,
    safe_str,
)
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

    def preencher_modal(self, linha, arquivo_comprovante: str = None) -> bool:
        """Preenche os campos do modal de Novo Comprovante com os dados de uma linha do CSV.

        Args:
            linha: Linha do DataFrame (pandas Series) com os dados do comprovante.
            arquivo_comprovante: Caminho absoluto para o arquivo PDF a ser enviado como comprovante.

        Returns:
            True se o modal foi preenchido com sucesso.
        """
        import pandas as pd

        try:
            # --- Identificação do Contratado ---
            cpf_raw = linha["CPF"]
            cnpj_raw = linha["CNPJ"]
            tem_cpf = not pd.isna(cpf_raw) and str(cpf_raw).strip() != ""

            if tem_cpf:
                tipo_pessoa = "1"
                documento = limpar_documento(cpf_raw)
                tipo_label = "CPF"
            else:
                tipo_pessoa = "2"
                documento = limpar_documento(cnpj_raw)
                tipo_label = "CNPJ"

            self.logger.info("  %s: %s", tipo_label, documento)

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
            cnpjcpf_input.type(documento, delay=30)
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
            tipo_comp = safe_str(linha["Tipo Comprovante"])
            if tipo_comp:
                self.page.select_option("#tpDocumento", label=tipo_comp)
                self.logger.info("  Tipo Comprovante: %s", tipo_comp)

            data_emissao = formatar_data_br(linha["Data de Emissão"])
            if data_emissao:
                self.page.fill("#dataEmissao", data_emissao)
                self.logger.info("  Data de Emissão: %s", data_emissao)

            numero = safe_str(linha["Número"])
            if numero:
                self.page.fill("#nrComprovante", numero)
                self.logger.info("  Número: %s", numero)

            serie = safe_str(linha["Série"])
            if serie:
                self.page.fill("#nrSerie", serie)
                self.logger.info("  Série: %s", serie)

            # --- Upload do Comprovante ---
            if arquivo_comprovante:
                file_input = self.page.locator("#test1 input[type='file']#arquivo")
                file_input.set_input_files(arquivo_comprovante)
                self.logger.info("  Comprovante enviado: %s", arquivo_comprovante)

            # --- Dados do Comprovante Bancário ---
            forma_pag = safe_str(linha["Forma de Pagamento"])
            if forma_pag:
                self.page.select_option("#tpFormaDePagamento", label=forma_pag)
                self.logger.info("  Forma de Pagamento: %s", forma_pag)

            data_pag = formatar_data_br(linha["Data do pagamento"])
            if data_pag:
                self.page.fill("#dtPagamento", data_pag)
                self.logger.info("  Data do pagamento: %s", data_pag)

            nr_doc = safe_str(linha["Nº Documento Pagamento"])
            if nr_doc:
                self.page.fill("#nrDocumentoDePagamento", nr_doc)
                self.logger.info("  Nº Documento Pagamento: %s", nr_doc)

            # Valor: remove formatação → dígitos em centavos; 'type' aciona a máscara
            valor_centavos = limpar_valor_monetario(linha["Valor"])
            if valor_centavos:
                valor_field = self.page.locator("#vlComprovado")
                valor_field.click(click_count=3)
                valor_field.type(valor_centavos, delay=30)
                self.logger.info("  Valor (centavos): %s", valor_centavos)

            # --- Justificativa ---
            justif = safe_str(linha["Justificativa"])
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
