# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
import os

block_cipher = None

def collect_data_folder_recursively(folder_name):
    data_files = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            src_path = os.path.join(root, file)
            dst_path = os.path.relpath(root, start='.')
            data_files.append((src_path, dst_path))
    return data_files

datas = []
datas += collect_data_folder_recursively("assets")
datas += collect_data_folder_recursively("mapas")
datas += collect_data_folder_recursively("sons")
datas += collect_data_folder_recursively("BloodVein SCORE")

hiddenimports = collect_submodules("inimigos")
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    name='BloodVein',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='icon.ico'
)
