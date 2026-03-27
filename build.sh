#!/usr/bin/env bash
# build.sh — Gera o executável do Salic Bot com PyInstaller
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Salic Bot — Build com PyInstaller ==="

# Sincroniza o ambiente com uv (instala deps + dev deps)
if ! command -v uv &> /dev/null; then
    echo "ERRO: uv não encontrado. Instale com: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
uv sync --dev

# Verifica se os browsers estão instalados
if [ ! -d "browsers/chromium-1208" ]; then
    echo "Browsers não encontrados. Instalando Chromium via Playwright..."
    PLAYWRIGHT_BROWSERS_PATH=./browsers uv run python -m playwright install chromium
fi

echo "Executando PyInstaller..."
uv run pyinstaller --clean --noconfirm salic-bot.spec

echo ""
echo "=== Build concluído ==="
echo "Executável gerado em: dist/salic-bot"
echo ""

# Verificação básica
if [ -f "dist/salic-bot" ]; then
    echo "Tamanho: $(du -h dist/salic-bot | cut -f1)"
    echo "Testando execução (--help)..."
    dist/salic-bot --help 2>&1 || echo "AVISO: Falha ao executar o binário."
else
    echo "ERRO: Executável não foi gerado!"
    exit 1
fi
