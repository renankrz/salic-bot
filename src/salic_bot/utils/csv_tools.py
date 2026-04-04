"""Utilitários para manipulação de CSVs"""

from pathlib import Path

import pandas as pd

from ..models.despesa import COLUNAS_ESPERADAS, DespesaCSV


def ler_csv(csv_path: str | Path) -> list[DespesaCSV]:
    """
    Lê um CSV de despesas e retorna uma lista de DespesaCSV.

    Os nomes das colunas são normalizados (strip + lowercase) antes
    da conversão, tornando a leitura robusta a variações de case e
    espaços extras.

    Args:
        csv_path: Caminho para o arquivo CSV.

    Returns:
        Lista de DespesaCSV com os dados do CSV.

    Raises:
        ValueError: Se colunas esperadas estiverem ausentes no CSV.
    """
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip().str.lower()

    colunas_presentes = set(df.columns)
    faltantes = COLUNAS_ESPERADAS - colunas_presentes
    if faltantes:
        raise ValueError(f"Colunas ausentes no CSV: {', '.join(sorted(faltantes))}")

    return [DespesaCSV.from_series(row) for _, row in df.iterrows()]
