# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hiddenimports = (
    collect_submodules("tkinter")
    + collect_submodules("playwright")
    + ["greenlet", "pyee", "pyee.base"]
)

_HERE = globals().get("SPECPATH") or os.getcwd()

import importlib
_pw_pkg = os.path.dirname(importlib.import_module("playwright").__file__)
_pw_driver = os.path.join(_pw_pkg, "driver")

a = Analysis(
    ["main.py"],
    pathex=[_HERE],
    binaries=[
        (os.path.join(_HERE, "ffmpeg.exe"), "."),
        (os.path.join(_HERE, "yt-dlp.exe"), "."),
        (os.path.join(_HERE, "deno.exe"), "."),
    ],
    datas=[
        (_pw_driver, os.path.join("playwright", "driver")),
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ytd",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=["node.exe"],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
