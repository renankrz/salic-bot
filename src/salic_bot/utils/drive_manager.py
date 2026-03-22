"""Utilitários para navegação na estrutura de pastas de clientes"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def encontrar_pasta_cliente(clientes_dir: str | Path, cnpj: str) -> Path:
    """
    Dentro de clientes_dir, encontra a pasta cujo nome contém o CNPJ fornecido.

    Args:
        clientes_dir: Caminho para a pasta raiz de clientes.
        cnpj: CNPJ do proponente (somente dígitos).

    Returns:
        Path para a pasta do cliente.

    Raises:
        FileNotFoundError: Se nenhuma pasta contendo o CNPJ for encontrada.
    """
    clientes_path = Path(clientes_dir)
    for pasta in clientes_path.iterdir():
        if pasta.is_dir() and cnpj in pasta.name:
            return pasta
    raise FileNotFoundError(
        f"Nenhuma pasta de cliente com CNPJ '{cnpj}' encontrada em '{clientes_dir}'"
    )


def encontrar_pasta_projeto(cliente_dir: Path, pronac: int | str) -> Path:
    """
    Dentro de cliente_dir, encontra a pasta cujo nome contém o PRONAC fornecido.

    Args:
        cliente_dir: Caminho para a pasta do cliente.
        pronac: PRONAC do projeto.

    Returns:
        Path para a pasta do projeto.

    Raises:
        FileNotFoundError: Se nenhuma pasta contendo o PRONAC for encontrada.
    """
    pronac_str = str(pronac)
    for pasta in cliente_dir.iterdir():
        if pasta.is_dir() and pronac_str in pasta.name:
            return pasta
    raise FileNotFoundError(
        f"Nenhuma pasta de projeto com PRONAC '{pronac_str}' encontrada em '{cliente_dir}'"
    )


def encontrar_pasta_execucao_financeira(projeto_dir: Path) -> Path:
    """
    Dentro de projeto_dir, encontra a pasta cujo nome começa com '04'.

    Args:
        projeto_dir: Caminho para a pasta do projeto.

    Returns:
        Path para a pasta de execução financeira.

    Raises:
        FileNotFoundError: Se nenhuma pasta iniciando em '04' for encontrada.
    """
    for pasta in projeto_dir.iterdir():
        if pasta.is_dir() and pasta.name.startswith("04"):
            return pasta
    raise FileNotFoundError(
        f"Nenhuma pasta de execução financeira (início '04') encontrada em '{projeto_dir}'"
    )


def encontrar_csv(execucao_dir: Path) -> Path:
    """
    Dentro de execucao_dir, encontra o único arquivo CSV presente.

    Args:
        execucao_dir: Caminho para a pasta de execução financeira.

    Returns:
        Path para o arquivo CSV.

    Raises:
        FileNotFoundError: Se nenhum CSV for encontrado.
    """
    csvs = [
        f for f in execucao_dir.iterdir() if f.is_file() and f.suffix.lower() == ".csv"
    ]
    if not csvs:
        raise FileNotFoundError(f"Nenhum CSV encontrado em '{execucao_dir}'")
    return csvs[0]


def encontrar_pasta_comprovantes(execucao_dir: Path) -> Path:
    """
    Dentro de execucao_dir, encontra a pasta cujo nome contém o termo 'nfs'
    (case-insensitive).

    Args:
        execucao_dir: Caminho para a pasta de execução financeira.

    Returns:
        Path para a pasta de comprovantes.

    Raises:
        FileNotFoundError: Se nenhuma pasta com 'nfs' no nome for encontrada.
    """
    for pasta in execucao_dir.iterdir():
        if pasta.is_dir() and "nfs" in pasta.name.lower():
            return pasta
    raise FileNotFoundError(
        f"Nenhuma pasta com 'nfs' no nome encontrada em '{execucao_dir}'"
    )


def encontrar_comprovante(execucao_dir: Path, data_pagamento: str, numero: str) -> Path:
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
    pasta_comprovantes = encontrar_pasta_comprovantes(execucao_dir)

    # Converter data D/M/YYYY para YYYY.mm.DD
    partes = data_pagamento.strip().split("/")
    dia, mes, ano = partes
    data_formatada = f"{ano}.{int(mes):02d}.{int(dia):02d}"

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
    """
    pasta_execucao = localizar_pasta_execucao(clientes_dir, cnpj, pronac)
    return encontrar_csv(pasta_execucao)


def localizar_pasta_execucao(
    clientes_dir: str | Path, cnpj: str, pronac: int | str
) -> Path:
    """
    Retorna o Path da pasta de execução financeira (pasta '04*').

    Args:
        clientes_dir: Caminho para a pasta raiz de clientes.
        cnpj: CNPJ do proponente (somente dígitos).
        pronac: PRONAC do projeto.

    Returns:
        Path para a pasta de execução financeira.
    """
    pasta_cliente = encontrar_pasta_cliente(clientes_dir, cnpj)
    pasta_projeto = encontrar_pasta_projeto(pasta_cliente, pronac)
    return encontrar_pasta_execucao_financeira(pasta_projeto)
