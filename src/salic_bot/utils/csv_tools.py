"""Utilitários para manipulação de CSVs"""

import re
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
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df.columns = [re.sub(r"\s*\*$", "", col) for col in df.columns]
    return df
