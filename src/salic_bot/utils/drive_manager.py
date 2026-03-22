"""Utilitários para navegação na estrutura de pastas de clientes"""

import logging
from pathlib import Path

from ..utils.formatters import formatar_data_arquivo

logger = logging.getLogger(__name__)


def localizar_pasta_execucao_financeira(
    clientes_dir: str | Path, cnpj: str, pronac: int | str
) -> Path:
    """
    Localiza a pasta de execução financeira navegando pela estrutura de pastas.

    Fluxo:
        clientes_dir → pasta com CNPJ → pasta com PRONAC → pasta '04*'

    Args:
        clientes_dir: Caminho para a pasta raiz de clientes.
        cnpj: CNPJ do proponente (somente dígitos).
        pronac: PRONAC do projeto.

    Returns:
        Path para a pasta de execução financeira.

    Raises:
        FileNotFoundError: Se alguma pasta do caminho não for encontrada.
    """
    # 1. Pasta do cliente (contém CNPJ no nome)
    clientes_path = Path(clientes_dir)
    pasta_cliente = None
    for pasta in clientes_path.iterdir():
        if pasta.is_dir() and cnpj in pasta.name:
            pasta_cliente = pasta
            break
    if pasta_cliente is None:
        raise FileNotFoundError(
            f"Nenhuma pasta de cliente com CNPJ '{cnpj}' encontrada em '{clientes_dir}'"
        )

    # 2. Pasta do projeto (contém PRONAC no nome)
    pronac_str = str(pronac)
    pasta_projeto = None
    for pasta in pasta_cliente.iterdir():
        if pasta.is_dir() and pronac_str in pasta.name:
            pasta_projeto = pasta
            break
    if pasta_projeto is None:
        raise FileNotFoundError(
            f"Nenhuma pasta de projeto com PRONAC '{pronac_str}' "
            f"encontrada em '{pasta_cliente}'"
        )

    # 3. Pasta de execução financeira (nome começa com '04')
    for pasta in pasta_projeto.iterdir():
        if pasta.is_dir() and pasta.name.startswith("04"):
            return pasta
    raise FileNotFoundError(
        f"Nenhuma pasta de execução financeira (início '04') "
        f"encontrada em '{pasta_projeto}'"
    )


def localizar_csv_execucao_financeira(
    clientes_dir: str | Path, cnpj: str, pronac: int | str
) -> Path:
    """
    Localiza o CSV de execução financeira navegando pela estrutura de pastas.

    Fluxo:
        clientes_dir → pasta com CNPJ → pasta com PRONAC → pasta '04*' → CSV único

    Args:
        clientes_dir: Caminho para a pasta raiz de clientes.
        cnpj: CNPJ do proponente (somente dígitos).
        pronac: PRONAC do projeto.

    Returns:
        Path para o CSV de execução financeira.

    Raises:
        FileNotFoundError: Se a pasta ou o CSV não for encontrado.
    """
    pasta_execucao = localizar_pasta_execucao_financeira(clientes_dir, cnpj, pronac)
    csvs = [
        f
        for f in pasta_execucao.iterdir()
        if f.is_file() and f.suffix.lower() == ".csv"
    ]
    if not csvs:
        raise FileNotFoundError(f"Nenhum CSV encontrado em '{pasta_execucao}'")
    return csvs[0]


def localizar_comprovante(execucao_dir: Path, data_pagamento: str, numero: str) -> Path:
    """
    Localiza o PDF de comprovante dentro da pasta de comprovantes.

    Busca em TODAS as subpastas (meses de pagamento) dentro da pasta de comprovantes
    por um arquivo cujo nome comece com '<YYYY.mm.DD>_<qualquer coisa>_<numero>_'.

    Args:
        execucao_dir: Caminho para a pasta de execução financeira.
        data_pagamento: Data de pagamento no formato 'D/M/YYYY' (ex: '10/1/2025').
        numero: Número do comprovante (ex: '35').

    Returns:
        Path para o arquivo PDF encontrado.

    Raises:
        FileNotFoundError: Se nenhum ou mais de um match for encontrado.
    """
    # Localizar pasta de comprovantes (contém 'nfs' no nome)
    pasta_comprovantes = None
    for pasta in Path(execucao_dir).iterdir():
        if pasta.is_dir() and "nfs" in pasta.name.lower():
            pasta_comprovantes = pasta
            break
    if pasta_comprovantes is None:
        raise FileNotFoundError(
            f"Nenhuma pasta com 'nfs' no nome encontrada em '{execucao_dir}'"
        )

    data_formatada = formatar_data_arquivo(data_pagamento)

    termo_data = f"{data_formatada}_"
    termo_numero = f"_{numero}_"
    logger.debug(
        "Buscando comprovante com data %s e número %s", termo_data, termo_numero
    )

    matches = []
    for pasta_mes in pasta_comprovantes.iterdir():
        if not pasta_mes.is_dir():
            continue
        for arquivo in pasta_mes.iterdir():
            if (
                arquivo.is_file()
                and arquivo.name.startswith(termo_data)
                and termo_numero in arquivo.name
            ):
                matches.append(arquivo)

    if len(matches) == 1:
        logger.info("Comprovante encontrado: %s", matches[0])
        return matches[0]
    elif len(matches) == 0:
        raise FileNotFoundError(
            f"Nenhum comprovante encontrado com data '{termo_data}' "
            f"e número '{termo_numero}' em '{pasta_comprovantes}'"
        )
    else:
        nomes = [m.name for m in matches]
        raise FileNotFoundError(
            f"Múltiplos comprovantes encontrados com data '{termo_data}' "
            f"e número '{termo_numero}': {nomes}"
        )
