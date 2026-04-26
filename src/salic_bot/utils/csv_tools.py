"""Utilitários para manipulação de CSVs"""

import logging
from pathlib import Path

import pandas as pd

from ..models.despesa import COLUNAS_ESPERADAS, Despesa

logger = logging.getLogger(__name__)

# Mapeamento de valores comuns para booleanos na coluna "incluída".
# Cobre formatos gerados por Google Sheets, Calc e Excel em locales
# inglês e português.
_BOOL_MAP: dict[str, bool] = {
    "true": True,
    "false": False,
    "verdadeiro": True,
    "falso": False,
    "sim": True,
    "não": False,
    "nao": False,
    "yes": True,
    "no": False,
    "1": True,
    "0": False,
}


def _parsear_incluida(valor) -> bool | None:
    """Converte um valor da coluna 'incluída' para booleano.

    Aceita variações comuns de formatos gerados por Google Sheets, Calc e
    Excel. Valores vazios ou NaN são tratados como False. Valores não
    reconhecidos retornam ``pd.NA`` (serão tratados como erro individual
    na despesa correspondente).
    """
    if pd.isna(valor) or str(valor).strip() == "":
        return False
    texto = str(valor).strip().lower()
    if texto in _BOOL_MAP:
        return _BOOL_MAP[texto]
    return pd.NA


def _ler_csv(csv_path: str | Path) -> tuple[pd.DataFrame, list[Despesa]]:
    """
    Lê um CSV de despesas e retorna o DataFrame completo e uma lista de
    Despesa.

    Os nomes das colunas são normalizados (strip + lowercase) antes
    da conversão, tornando a leitura robusta a variações de case e
    espaços extras.

    A coluna ``incluída`` é parseada como booleano nullable
    (``pd.BooleanDtype``), tolerando formatos comuns de Google Sheets,
    Calc e Excel (TRUE/FALSE, VERDADEIRO/FALSO, etc.). Se ausente no
    CSV de entrada, é gerada com todos os valores False.

    A coluna ``erro`` é lida como string. Se ausente no CSV de entrada,
    é gerada vazia.

    Args:
        csv_path: Caminho para o arquivo CSV.

    Returns:
        Tupla (DataFrame, lista de Despesa).

    Raises:
        ValueError: Se colunas esperadas estiverem ausentes no CSV.
    """
    df = pd.read_csv(csv_path, encoding="utf-8-sig", index_col=False)
    df.columns = df.columns.str.strip().str.lower()

    # Gerar colunas de controle se ausentes
    if "incluída" not in df.columns:
        logger.info("Coluna 'incluída' ausente no CSV — gerada com valores False")
        df["incluída"] = False
    if "erro" not in df.columns:
        logger.info("Coluna 'erro' ausente no CSV — gerada vazia")
        df["erro"] = ""

    colunas_presentes = set(df.columns)
    faltantes = COLUNAS_ESPERADAS - colunas_presentes
    if faltantes:
        raise ValueError(f"Colunas ausentes no CSV: {', '.join(sorted(faltantes))}")

    # Parsear coluna "incluída" como booleano nullable
    df["incluída"] = df["incluída"].apply(_parsear_incluida).astype("boolean")

    # Garantir coluna "erro" como string
    df["erro"] = df["erro"].fillna("").astype(str)

    despesas = [Despesa.from_series(row) for _, row in df.iterrows()]
    return df, despesas


def _salvar_csv(df: pd.DataFrame, csv_path: str | Path) -> None:
    """
    Salva o DataFrame de despesas de volta para o CSV.

    A coluna ``incluída`` é escrita como TRUE/FALSE (maiúsculo) para
    máxima compatibilidade com Google Sheets, Calc e Excel.

    Args:
        df: DataFrame com os dados de despesas.
        csv_path: Caminho para o arquivo CSV de saída.
    """
    df = df.copy()
    df["incluída"] = df["incluída"].apply(
        lambda v: "TRUE" if (not pd.isna(v) and v) else "FALSE"
    )
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info("CSV atualizado")


class PlanilhaDespesas:
    """Encapsula o DataFrame de despesas e suas operações de rastreamento.

    Fornece uma interface de alto nível para consultar e atualizar o
    estado de inclusão de cada despesa, sem expor detalhes de pandas ao
    código chamador.
    """

    def __init__(self, csv_path: str | Path):
        self._csv_path = csv_path
        self._df, self._despesas = _ler_csv(csv_path)

    @property
    def despesas(self) -> list[Despesa]:
        """Lista de despesas lidas do CSV."""
        return self._despesas

    def __len__(self) -> int:
        return len(self._despesas)

    def ja_incluida(self, idx: int) -> bool:
        """Retorna True se a despesa no índice ``idx`` já foi incluída.

        Raises:
            ValueError: Se o valor da coluna 'incluída' for inválido
                (por exemplo, texto não reconhecido como booleano).
        """
        valor = self._df.at[idx, "incluída"]
        if pd.isna(valor):
            raise ValueError(
                f"Valor inválido na coluna 'incluída' para a despesa {idx + 1}"
            )
        return bool(valor)

    def marcar_incluida(self, idx: int) -> None:
        """Marca a despesa no índice ``idx`` como incluída com sucesso."""
        self._df.at[idx, "incluída"] = True
        self._df.at[idx, "erro"] = ""

    def marcar_erro(self, idx: int, mensagem: str) -> None:
        """Registra um erro para a despesa no índice ``idx``."""
        self._df.at[idx, "incluída"] = False
        self._df.at[idx, "erro"] = mensagem

    def marcar_todas_erro(self, mensagem: str) -> None:
        """Marca todas as despesas como não incluídas com a mesma mensagem de erro."""
        self._df["incluída"] = False
        self._df["erro"] = mensagem

    def salvar(self) -> None:
        """Salva o estado atual de volta para o CSV de origem."""
        _salvar_csv(self._df, self._csv_path)
