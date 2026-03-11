"""Configuração e gerenciamento do navegador Playwright"""

import os
from pathlib import Path
from typing import Optional

from dotenv import find_dotenv, load_dotenv
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

# Garante que PLAYWRIGHT_BROWSERS_PATH esteja em os.environ antes do sync_playwright,
# resolvendo o caminho relativo em relação à raiz do projeto (onde fica o .env).
_dotenv_path = find_dotenv()
load_dotenv(_dotenv_path)

_browsers_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH")
if _browsers_path and not os.path.isabs(_browsers_path):
    _project_root = Path(_dotenv_path).parent
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(
        (_project_root / _browsers_path).resolve()
    )


class BrowserManager:
    """Gerencia ciclo de vida do navegador"""

    def __init__(self, headless: bool = True, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self) -> Page:
        """Inicia navegador e retorna página"""
        self.playwright = sync_playwright().start()

        # Configurações do navegador
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
            slow_mo=self.slow_mo,
        )

        # Configurações do contexto
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )

        # Configurações da página
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)  # 30s timeout

        return self.page

    def close(self):
        """Fecha navegador"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def screenshot(self, name: str) -> str:
        """Tira screenshot para debug"""
        if self.page:
            screenshots_dir = "screenshots"
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)

            path = f"{screenshots_dir}/{name}.png"
            self.page.screenshot(path=path, full_page=True)
            return path
        return ""

    def __enter__(self):
        """Context manager"""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()
