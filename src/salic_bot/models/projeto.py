"""Modelo de dados para um Projeto do Salic"""

from dataclasses import dataclass


@dataclass
class Projeto:
    mecanismo: str
    proponente: str  # CNPJ apenas dígitos, ex: "11222333000181"
    pronac: int
