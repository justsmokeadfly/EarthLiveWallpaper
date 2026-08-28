# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for EarthLive.

Build with:
    pyinstaller EarthLive.spec

Produces a one-folder distribution at dist/EarthLive/ containing
EarthLive.exe plus all dependencies, which is faster to start and easier
to debug than a one-file build.
"""

import sys
from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH)

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / "assets" / "icon.png"), "assets"),
        (str(project_root / "assets" / "icon.ico"), "assets"),
    ],
    hiddenimports=[
        "customtkinter",
        "pystray._win32",
        "PIL._tkinter_finder",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EarthLive",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "assets" / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="EarthLive",
)
