# -*- mode: python ; coding: utf-8 -*-
# SIFMA — Especificación de Empaquetado del Asistente de Instalación (SIFMA_Instalador_Setup.exe)

import os

block_cipher = None
BASE_DIR = os.path.abspath(SPECPATH)
ICON_PATH = os.path.join(BASE_DIR, 'static', 'img', 'sifma_icon.ico')
BUILT_APP_EXE = os.path.join(BASE_DIR, 'dist', 'SIFMA_Desktop.exe')

datas = [
    (BUILT_APP_EXE, 'payload'),
    (os.path.join(BASE_DIR, 'static', 'img'), os.path.join('static', 'img')),
]

hiddenimports = [
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'clr_loader',
    'pythonnet',
]

a = Analysis(
    ['installer_wizard.py'],
    pathex=[BASE_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'pytest', 'notebook',
        'pandas', 'dask', 'distributed', 'xarray', 'sklearn', 'scikit-learn',
        'skimage', 'scikit-image', 'statsmodels', 'altair', 'plantcv', 'tornado',
        'cv2', 'numpy', 'sqlalchemy', 'flask'
    ],
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
    name='SIFMA_Instalador_Setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH if os.path.exists(ICON_PATH) else None,
)

