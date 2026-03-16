"""Utilitários de formatação"""


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
