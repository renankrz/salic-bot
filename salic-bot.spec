# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec para o Salic Bot (com Chromium embutido)."""

import os
import playwright

block_cipher = None

project_root = os.path.dirname(os.path.abspath(SPEC))

# --- Localização do driver do Playwright ---
playwright_driver = os.path.join(os.path.dirname(playwright.__file__), "driver")

# --- Localização dos browsers ---
browsers_dir = os.path.join(project_root, "browsers")

# --- Dados a embutir ---
# No macOS, o Chromium é um .app bundle com frameworks internos que o PyInstaller
# não consegue re-assinar (codesign). Por isso, no macOS os browsers são
# distribuídos ao lado do executável em vez de embutidos.
import sys

datas = [
    (playwright_driver, os.path.join("playwright", "driver")),
]
if sys.platform != "darwin":
    datas.append((browsers_dir, "browsers"))

a = Analysis(
    [os.path.join(project_root, "run.py")],
    pathex=[os.path.join(project_root, "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "playwright",
        "playwright.sync_api",
        "playwright._impl",
        "playwright._impl._driver",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="salic-bot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
