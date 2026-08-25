# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules

SPEC_DIR = Path(SPECPATH)
ROOT = SPEC_DIR.parent

datas = [
    (str(ROOT / "dist"), "dist"),
    (str(ROOT / "data" / "dictionary.db"), "data"),
]

binaries = []
hiddenimports = collect_submodules("backend") + collect_submodules("uvicorn")
hiddenimports = [name for name in hiddenimports if not name.startswith("backend.test")]

for pkg in ("webview", "uvicorn", "fastapi", "starlette", "pydantic"):
    try:
        collected = collect_all(pkg)
        datas += collected[0]
        binaries += collected[1]
        hiddenimports += collected[2]
    except Exception:
        pass

block_cipher = None

a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="EnWord",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="EnWord",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="EnWord.app",
        icon=None,
        bundle_identifier="com.enword.offline",
        version="0.1.0",
        info_plist={
            "CFBundleName": "离线背单词",
            "CFBundleDisplayName": "离线背单词",
            "NSHighResolutionCapable": True,
        },
    )
