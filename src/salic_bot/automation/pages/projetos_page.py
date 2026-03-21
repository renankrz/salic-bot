"""Page Object para a tela de Projetos do Salic"""

import os

from playwright.sync_api import Page

from ...config import SCREENSHOTS_DIR
from ...models.projeto import Projeto
from ...utils.formatters import formatar_cnpj
from ..base_page import BasePage


class ProjetosPage(BasePage):
    """Page Object para listar e selecionar projetos no Salic"""

    # Seletores — dropdowns Vuetify (v-select / combobox)
    # O elemento clicável é o .v-input__slot (pai do input), pois o
    # .v-select__selections intercepta eventos diretos no <input>.
    SLOT_MECANISMO = (
        'div[role="combobox"]:has(input[aria-label="Mecanismo"]) .v-input__slot'
    )
    SLOT_PROPONENTES = (
        'div[role="combobox"]:has(input[aria-label="Proponentes"]) .v-input__slot'
    )

    # Itens de lista dentro dos dropdowns Vuetify
    DROPDOWN_ITEM = ".v-select-list .v-list__tile"

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _normalizar(self, texto: str) -> str:
        return texto.strip().lower()

    def _selecionar_vuetify_dropdown(self, slot_selector: str, valor_alvo: str):
        """
        Abre um dropdown Vuetify clicando no .v-input__slot e escolhe a opção
        cujo texto contém `valor_alvo` (comparação case-insensitive e com trim).
        """
        alvo = self._normalizar(valor_alvo)

        # Clica no slot do campo para abrir o dropdown
        self.page.click(slot_selector)

        # Aguarda a lista ficar visível
        self.page.wait_for_selector(f"{self.DROPDOWN_ITEM}:visible", timeout=10000)

        # Itera pelos itens visíveis e clica no que bater
        items = self.page.locator(self.DROPDOWN_ITEM)
        count = items.count()

        for i in range(count):
            item = items.nth(i)
            texto = self._normalizar(item.inner_text())
            if alvo in texto:
                item.click()
                self.page.wait_for_selector(
                    self.DROPDOWN_ITEM, state="hidden", timeout=5000
                )
                return

        raise ValueError(
            f"Opção contendo '{valor_alvo}' não encontrada no dropdown "
            f"(seletor: {slot_selector})"
        )

    # ------------------------------------------------------------------
    # Ações públicas
    # ------------------------------------------------------------------

    def selecionar_mecanismo(self, mecanismo: str):
        """Seleciona o mecanismo no primeiro dropdown (ex: 'Mecenato')"""
        self.logger.info("Selecionando mecanismo: %s", mecanismo)
        self._selecionar_vuetify_dropdown(self.SLOT_MECANISMO, mecanismo)

    def selecionar_proponente(self, cnpj: str):
        """
        Seleciona o proponente pelo CNPJ (apenas dígitos).
        Formata o CNPJ antes de procurar no dropdown.
        """
        cnpj_formatado = formatar_cnpj(cnpj)
        self.logger.info("Selecionando proponente com CNPJ: %s", cnpj_formatado)
        self._selecionar_vuetify_dropdown(self.SLOT_PROPONENTES, cnpj_formatado)

    def clicar_pronac(self, pronac: int):
        """
        Na tabela de resultados, clica no link do PRONAC correspondente.
        A página do projeto é aberta em nova aba; retorna o objeto Page dela.
        """
        pronac_str = str(pronac).strip()
        self.logger.info("Clicando no PRONAC: %s", pronac_str)

        # Links de PRONAC na tabela — filtra pelo texto exato
        links_pronac = self.page.locator('td a[title="Visualizar Projeto"]')

        self.page.wait_for_selector('td a[title="Visualizar Projeto"]', timeout=15000)

        count = links_pronac.count()
        for i in range(count):
            link = links_pronac.nth(i)
            texto = self._normalizar(link.inner_text())
            if texto == self._normalizar(pronac_str):
                # Captura a nova aba aberta pelo clique
                with self.page.context.expect_page() as nova_pagina_info:
                    link.click()
                nova_pagina = nova_pagina_info.value
                nova_pagina.wait_for_load_state("networkidle")
                return nova_pagina

        raise ValueError(f"PRONAC '{pronac_str}' não encontrado na tabela de projetos")

    def selecionar_projeto(self, projeto: Projeto):
        """
        Executa a sequência completa: seleciona mecanismo, proponente e
        clica no PRONAC para entrar na página do projeto.

        Returns:
            O objeto Page da nova aba aberta, ou None em caso de falha.
        """
        try:
            self.selecionar_mecanismo(projeto.mecanismo)
            self.selecionar_proponente(projeto.proponente)

            nova_pagina = self.clicar_pronac(projeto.pronac)

            self.logger.info(
                "Projeto PRONAC %s selecionado com sucesso!", projeto.pronac
            )
            return nova_pagina

        except Exception as e:
            self.logger.error("Erro ao selecionar projeto: %s", e)
            self.page.screenshot(
                path=os.path.join(SCREENSHOTS_DIR, "erro_selecionar_projeto.png"),
                full_page=True,
            )
            return None
