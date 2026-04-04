"""Modelo de dados para uma linha do CSV de despesas."""

from __future__ import annotations

from dataclasses import dataclass

from ..utils.formatters import safe_str

# Mapeamento: nome normalizado da coluna CSV → nome do atributo Python
_COLUNA_PARA_CAMPO: dict[str, str] = {
    "produto": "produto",
    "etapa": "etapa",
    "uf": "uf",
    "cidade": "cidade",
    "item de custo": "item_de_custo",
    "cpf": "cpf",
    "cnpj": "cnpj",
    "tipo comprovante": "tipo_comprovante",
    "data de emissão": "data_de_emissao",
    "número": "numero",
    "série": "serie",
    "forma de pagamento": "forma_de_pagamento",
    "data do pagamento": "data_do_pagamento",
    "nº documento pagamento": "nr_documento_pagamento",
    "valor": "valor",
    "justificativa": "justificativa",
}

COLUNAS_ESPERADAS: set[str] = set(_COLUNA_PARA_CAMPO.keys())


@dataclass
class DespesaCSV:
    """Representa uma linha do CSV de despesas, com campos já limpos."""

    produto: str
    etapa: str
    uf: str
    cidade: str
    item_de_custo: str
    cpf: str
    cnpj: str
    tipo_comprovante: str
    data_de_emissao: str
    numero: str
    serie: str
    forma_de_pagamento: str
    data_do_pagamento: str
    nr_documento_pagamento: str
    valor: str
    justificativa: str

    @classmethod
    def from_series(cls, series) -> DespesaCSV:
        """Cria uma DespesaCSV a partir de uma pandas Series com colunas normalizadas.

        Cada valor é convertido para string limpa (NaN → "").
        """
        kwargs = {}
        for coluna, campo in _COLUNA_PARA_CAMPO.items():
            kwargs[campo] = safe_str(series[coluna])
        return cls(**kwargs)
