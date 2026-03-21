"""Page Object para a tela de Comprovação Financeira do Salic"""

from playwright.sync_api import Page

from ..base_page import BasePage


class ComprovacaoFinanceiraPage(BasePage):
    """Page Object para a página de Comprovação Financeira no Salic.

    Gerencia a navegação pelo accordion multinível (Produto > Etapa > UF > Cidade)
    e o clique no botão 'Comprovar item' da tabela de itens de custo.
    """

    def __init__(self, page: Page):
        super().__init__(page)

    def _abrir_se_fechado(self, header) -> None:
        """Clica no header do accordion apenas se ainda não estiver aberto.

        O Materialize CSS adiciona a classe 'active' ao header quando a seção
        está aberta. Se a classe não estiver presente, o item está fechado.
        """
        classes = header.get_attribute("class") or ""
        if "active" not in classes:
            self.logger.debug("Abrindo seção: %r", header.inner_text().strip())
            header.click()
            header.locator(
                "xpath=following-sibling::div[contains(@class,'collapsible-body')]"
            ).wait_for(state="visible", timeout=5000)
        else:
            self.logger.debug("Seção já aberta: %r", header.inner_text().strip())

    def navegar_e_clicar_comprovar_item(
        self,
        produto: str,
        etapa: str,
        uf: str,
        cidade: str,
        item_de_custo: str,
    ) -> bool:
        """Navega pelo accordion e clica em 'Comprovar item' para o item de custo.

        Args:
            produto: Nome do produto (ex: "Exposição Cultural / de Artes")
            etapa: Nome da etapa (ex: "Pré-Produção / Preparação")
            uf: Sigla da UF (ex: "SP")
            cidade: Nome da cidade (ex: "São Paulo")
            item_de_custo: Nome do item de custo a localizar na tabela

        Returns:
            True se o clique foi realizado com sucesso.
        """
        try:
            self.logger.info(
                "Navegando: %r > %r > %r > %r > %r",
                produto,
                etapa,
                uf,
                cidade,
                item_de_custo,
            )

            # 1. Localizar e abrir o Produto
            produto_lis = self.page.locator("#produtos-collapsible > li")
            n = produto_lis.count()
            produto_li = None
            for i in range(n):
                li = produto_lis.nth(i)
                header = li.locator("> div.collapsible-header")
                if produto.strip() in header.inner_text().strip():
                    self._abrir_se_fechado(header)
                    produto_li = li
                    break

            if produto_li is None:
                raise ValueError(f"Produto não encontrado: {produto!r}")

            # 2. Localizar e abrir a Etapa dentro do Produto
            etapa_lis = produto_li.locator("> div.collapsible-body > ul > li")
            n = etapa_lis.count()
            etapa_li = None
            for i in range(n):
                li = etapa_lis.nth(i)
                header = li.locator("> div.collapsible-header")
                if etapa.strip() in header.inner_text().strip():
                    self._abrir_se_fechado(header)
                    etapa_li = li
                    break

            if etapa_li is None:
                raise ValueError(f"Etapa não encontrada: {etapa!r}")

            # 3. Localizar e abrir a UF dentro da Etapa
            uf_lis = etapa_li.locator("> div.collapsible-body > ul > li")
            n = uf_lis.count()
            uf_li = None
            for i in range(n):
                li = uf_lis.nth(i)
                header = li.locator("> div.collapsible-header")
                if uf.strip() in header.inner_text().strip():
                    self._abrir_se_fechado(header)
                    uf_li = li
                    break

            if uf_li is None:
                raise ValueError(f"UF não encontrada: {uf!r}")

            # 4. Localizar e abrir a Cidade dentro da UF
            cidade_lis = uf_li.locator("> div.collapsible-body > ul > li")
            n = cidade_lis.count()
            cidade_li = None
            for i in range(n):
                li = cidade_lis.nth(i)
                header = li.locator("> div.collapsible-header")
                if cidade.strip() in header.inner_text().strip():
                    self._abrir_se_fechado(header)
                    cidade_li = li
                    break

            if cidade_li is None:
                raise ValueError(f"Cidade não encontrada: {cidade!r}")

            # 5. Localizar o item de custo na tabela e clicar em "Comprovar item"
            rows = cidade_li.locator("> div.collapsible-body table.bordered tbody tr")
            n = rows.count()
            for i in range(n):
                row = rows.nth(i)
                cell_text = row.locator("td").first.inner_text().strip()
                if item_de_custo.strip() in cell_text:
                    self.logger.info("Item de custo encontrado: %r", cell_text)
                    btn = row.locator('a[title="Comprovar item"]')
                    btn.click()
                    self.page.wait_for_load_state("networkidle")
                    self.logger.info("Clicou em 'Comprovar item'!")
                    self.page.screenshot(
                        path="screenshots/comprovantes.png", full_page=True
                    )
                    return True

            raise ValueError(f"Item de custo não encontrado: {item_de_custo!r}")

        except Exception as e:
            self.logger.error("Erro ao navegar e clicar em 'Comprovar item': %s", e)
            self.page.screenshot(
                path="screenshots/erro_comprovar_item.png", full_page=True
            )
            return False
