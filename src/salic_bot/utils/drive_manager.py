"""Utilitários para localização de comprovantes no diretório de comprovantes"""

import logging
from pathlib import Path

from ..utils.formatters import formatar_data_arquivo

logger = logging.getLogger(__name__)


def localizar_comprovante(
    comprovantes_dir: str | Path, data_emissao: str, numero: str
) -> Path:
    """
    Localiza o PDF de comprovante dentro do diretório de comprovantes.

    Busca em TODAS as subpastas (e no próprio diretório) por um arquivo cujo
    nome comece com '<YYYY.mm.DD>_' e contenha '_<numero>_'.

    Args:
        comprovantes_dir: Caminho para a pasta de comprovantes.
        data_emissao: Data de emissão no formato 'D/M/YYYY' (ex: '10/1/2025').
        numero: Número do comprovante (ex: '35').

    Returns:
        Path para o arquivo PDF encontrado.

    Raises:
        FileNotFoundError: Se nenhum ou mais de um match for encontrado.
    """
    comprovantes_path = Path(comprovantes_dir)
    if not comprovantes_path.is_dir():
        raise FileNotFoundError(
            f"Diretório de comprovantes não encontrado: '{comprovantes_dir}'"
        )

    data_formatada = formatar_data_arquivo(data_emissao)

    termo_data = f"{data_formatada}_"
    termo_numero = f"_{numero}_"
    logger.debug(
        "Buscando comprovante com data %s e número %s", termo_data, termo_numero
    )

    matches = []
    for arquivo in comprovantes_path.rglob("*"):
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
            f"e número '{termo_numero}' em '{comprovantes_path}'"
        )
    else:
        nomes = [m.name for m in matches]
        raise FileNotFoundError(
            f"Múltiplos comprovantes encontrados com data '{termo_data}' "
            f"e número '{termo_numero}': {nomes}"
        )
