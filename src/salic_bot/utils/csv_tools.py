"""Utilitários para manipulação de CSVs"""

from pathlib import Path

import pandas as pd


def ler_csv(csv_path: str | Path) -> pd.DataFrame:
    """
    Lê um CSV com pandas.

    Args:
        csv_path: Caminho para o arquivo CSV.

    Returns:
        DataFrame com os dados do CSV.
    """
    return pd.read_csv(csv_path)
