"""Utilitários de formatação"""

import re


def formatar_cnpj(cnpj: str) -> str:
    """
    Formata um CNPJ string de dígitos para o padrão XX.XXX.XXX/XXXX-XX.

    Completa com zeros à esquerda se necessário para chegar a 14 dígitos.

    Exemplos:
        "11222333000181" -> "11.222.333/0001-81"
        "191"            -> "00.000.000/0001-91"
    """
    digits = cnpj.strip().zfill(14)
    return f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"


def limpar_documento(valor) -> str:
    """Remove formatação de CPF/CNPJ, retorna apenas dígitos."""
    import pandas as pd

    if _eh_vazio(valor):
        return ""
    return re.sub(r"\D", "", str(valor))


def formatar_data_br(valor) -> str:
    """
    Converte data no formato D/M/YYYY para DD/MM/YYYY.

    Exemplos:
        "9/1/2025"  -> "09/01/2025"
        "19/9/2025" -> "19/09/2025"
    """
    if _eh_vazio(valor):
        return ""
    partes = str(valor).strip().split("/")
    if len(partes) == 3:
        dia, mes, ano = partes
        return f"{int(dia):02d}/{int(mes):02d}/{ano}"
    return str(valor).strip()


def limpar_valor_monetario(valor) -> str:
    """
    Remove formatação de moeda e retorna apenas dígitos (valor em centavos).

    Exemplos:
        "R$ 2.200,00" -> "220000"
        "R$ 1,99"     -> "199"
        "20000,00"    -> "2000000"
    """
    if _eh_vazio(valor):
        return ""
    return re.sub(r"\D", "", str(valor))


def safe_str(valor) -> str:
    """Retorna string limpa de um valor pandas, ou '' se vazio/NaN."""
    if _eh_vazio(valor):
        return ""
    s = str(valor).strip()
    # Remove sufixo '.0' que pandas adiciona ao ler inteiros como float
    if s.endswith(".0") and s[:-2].lstrip("-").isdigit():
        s = s[:-2]
    return s


def _eh_vazio(valor) -> bool:
    """Retorna True se o valor é NaN, None ou string vazia."""
    import pandas as pd

    try:
        return pd.isna(valor)
    except (TypeError, ValueError):
        return valor is None or str(valor).strip() == ""
