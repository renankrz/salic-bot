"""Utilitários para navegação na estrutura de pastas de clientes"""

from pathlib import Path


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
    pasta_cliente = encontrar_pasta_cliente(clientes_dir, cnpj)
    pasta_projeto = encontrar_pasta_projeto(pasta_cliente, pronac)
    pasta_execucao = encontrar_pasta_execucao_financeira(pasta_projeto)
    return encontrar_csv(pasta_execucao)
