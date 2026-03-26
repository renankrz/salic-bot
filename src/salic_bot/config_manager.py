"""Gerenciador de configuração com múltiplas fontes (QSettings, keyring, .env, defaults)"""

import logging
import os

import keyring
from dotenv import load_dotenv
from PySide6.QtCore import QSettings

logger = logging.getLogger(__name__)

APP_NAME = "SalicBot"
KEYRING_SERVICE = "SalicBot"


class ConfigManager:
    """Busca valores de configuração em múltiplas fontes com cadeia de precedência.

    Fontes disponíveis:
    - .env: variáveis de ambiente (desenvolvimento)
    - QSettings: preferências persistentes do usuário
    - keyring: cofre de credenciais do sistema operacional
    - default: valores padrão
    """

    # Mapeamento de variável → chave no .env
    ENV_KEYS = {
        "mecanismo": "MECANISMO",
        "proponente": "PROPONENTE",
        "pronac": "PRONAC",
        "clientes_dir": "CLIENTES_DIR",
        "cpf": "USER_CPF",
        "senha": "USER_SENHA",
    }

    DEFAULTS = {
        "mecanismo": "Mecenato",
        "proponente": "",
        "pronac": "",
        "clientes_dir": "",
        "cpf": "",
        "senha": "",
    }

    def __init__(self):
        load_dotenv()
        self._settings = QSettings(APP_NAME, APP_NAME)

    # --- Leitura com precedência ---

    def get_for_gui(self, key: str) -> str:
        """Retorna valor para pré-preencher a GUI.

        Precedência:
        - mecanismo, proponente, pronac, clientes_dir: .env → QSettings → default
        - cpf, senha: .env → keyring → default
        """
        value = self._from_env(key)
        if value:
            logger.debug("GUI: %s obtido do .env", key)
            return value

        if key in ("cpf", "senha"):
            value = self._from_keyring(key)
            if value:
                logger.debug("GUI: %s obtido do keyring", key)
                return value
        else:
            value = self._from_qsettings(key)
            if value:
                logger.debug("GUI: %s obtido do QSettings", key)
                return value

        logger.debug("GUI: %s usando default", key)
        return self.DEFAULTS.get(key, "")

    def get_for_cli(self, key: str, cli_value: str | None = None) -> str:
        """Retorna valor para a CLI.

        Precedência:
        - mecanismo, proponente, pronac, clientes_dir: CLI → .env → QSettings → default/erro
        - cpf, senha: CLI → .env → keyring → default/erro
        """
        if cli_value:
            logger.debug("CLI: %s obtido da linha de comando", key)
            return cli_value

        value = self._from_env(key)
        if value:
            logger.debug("CLI: %s obtido do .env", key)
            return value

        if key in ("cpf", "senha"):
            value = self._from_keyring(key)
            if value:
                logger.debug("CLI: %s obtido do keyring", key)
                return value
        else:
            value = self._from_qsettings(key)
            if value:
                logger.debug("CLI: %s obtido do QSettings", key)
                return value

        logger.debug("CLI: %s usando default", key)
        return self.DEFAULTS.get(key, "")

    # --- Persistência ---

    def save_preferences(
        self, mecanismo: str, proponente: str, pronac: str, clientes_dir: str
    ):
        """Salva preferências de sessão no QSettings."""
        self._settings.setValue("mecanismo", mecanismo)
        self._settings.setValue("proponente", proponente)
        self._settings.setValue("pronac", pronac)
        self._settings.setValue("clientes_dir", clientes_dir)
        self._settings.sync()
        logger.info("Preferências salvas no QSettings")

    def save_credentials(self, cpf: str, senha: str):
        """Salva credenciais no keyring do sistema operacional."""
        keyring.set_password(KEYRING_SERVICE, "cpf", cpf)
        keyring.set_password(KEYRING_SERVICE, "senha", senha)
        logger.info("Credenciais salvas no keyring")

    def has_saved_credentials(self) -> bool:
        """Verifica se existem credenciais salvas no keyring."""
        cpf = self._from_keyring("cpf")
        return bool(cpf)

    # --- Fontes individuais ---

    def _from_env(self, key: str) -> str:
        env_key = self.ENV_KEYS.get(key, "")
        if not env_key:
            return ""
        value = os.getenv(env_key, "")
        return value if value else ""

    def _from_qsettings(self, key: str) -> str:
        value = self._settings.value(key, "")
        return value if value else ""

    def _from_keyring(self, key: str) -> str:
        try:
            value = keyring.get_password(KEYRING_SERVICE, key)
            return value if value else ""
        except Exception as e:
            logger.warning("Erro ao acessar keyring para '%s': %s", key, e)
            return ""
