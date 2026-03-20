"""Page Object para a tela de Comprovantes do Salic"""

from playwright.sync_api import Page

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

    def preencher_modal(self, linha) -> bool:
        """Preenche os campos do modal de Novo Comprovante com os dados de uma linha do CSV.

        Args:
            linha: Linha do DataFrame (pandas Series) com os dados do comprovante.

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

            print(f"  {tipo_label}: {documento}")

            # Selecionar radio CPF ou CNPJ (label intercepta o clique; usar force=True)
            radio = self.page.locator(
                f"#test1 input[name='tipoPessoa'][value='{tipo_pessoa}']"
            )
            radio.click(force=True)
            self.page.wait_for_timeout(300)

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
            cnpjcpf_input.press("Tab")
            self.page.wait_for_timeout(1500)

            # --- Dados do Comprovante de Despesa ---
            tipo_comp = safe_str(linha["Tipo Comprovante"])
            if tipo_comp:
                self.page.select_option("#tpDocumento", label=tipo_comp)
                print(f"  Tipo Comprovante: {tipo_comp}")

            data_emissao = formatar_data_br(linha["Data de Emissão"])
            if data_emissao:
                self.page.fill("#dataEmissao", data_emissao)
                print(f"  Data de Emissão: {data_emissao}")

            numero = safe_str(linha["Número"])
            if numero:
                self.page.fill("#nrComprovante", numero)
                print(f"  Número: {numero}")

            serie = safe_str(linha["Série"])
            if serie:
                self.page.fill("#nrSerie", serie)
                print(f"  Série: {serie}")

            # --- Dados do Comprovante Bancário ---
            forma_pag = safe_str(linha["Forma de Pagamento"])
            if forma_pag:
                self.page.select_option("#tpFormaDePagamento", label=forma_pag)
                print(f"  Forma de Pagamento: {forma_pag}")

            data_pag = formatar_data_br(linha["Data do pagamento"])
            if data_pag:
                self.page.fill("#dtPagamento", data_pag)
                print(f"  Data do pagamento: {data_pag}")

            nr_doc = safe_str(linha["Nº Documento Pagamento"])
            if nr_doc:
                self.page.fill("#nrDocumentoDePagamento", nr_doc)
                print(f"  Nº Documento Pagamento: {nr_doc}")

            # Valor: remove formatação → dígitos em centavos; 'type' aciona a máscara
            valor_centavos = limpar_valor_monetario(linha["Valor"])
            if valor_centavos:
                valor_field = self.page.locator("#vlComprovado")
                valor_field.click(click_count=3)
                valor_field.type(valor_centavos, delay=30)
                print(f"  Valor (centavos): {valor_centavos}")

            # --- Justificativa ---
            justif = safe_str(linha["Justificativa"])
            if justif:
                self.page.fill("#dsJustificativa", justif)
                print(f"  Justificativa: {justif[:40]}...")

            print("✅ Modal preenchido com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro ao preencher modal: {e}")
            self.page.screenshot(
                path="screenshots/erro_preencher_modal.png", full_page=True
            )
            return False
