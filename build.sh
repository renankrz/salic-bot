#!/usr/bin/env bash
# build.sh — Gera o executável do Salic Bot com PyInstaller
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Salic Bot — Build com PyInstaller ==="

# Ativa o venv do projeto (onde pyinstaller está instalado)
if [ ! -f ".venv/bin/activate" ]; then
    echo "ERRO: .venv não encontrado. Execute: python3 -m venv .venv && pip install -e '.[dev]'"
    exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# Verifica se os browsers estão instalados
if [ ! -d "browsers/chromium-1208" ]; then
    echo "Browsers não encontrados. Instalando Chromium via Playwright..."
    PLAYWRIGHT_BROWSERS_PATH=./browsers python -m playwright install chromium
fi

echo "Executando PyInstaller..."
pyinstaller --clean --noconfirm salic-bot.spec

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
