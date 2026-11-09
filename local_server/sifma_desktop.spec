# -*- mode: python ; coding: utf-8 -*-
# SIFMA — Especificación de Empaquetado Nativo (PyInstaller + PyWebView)
# Empaqueta exclusivamente el código y activos estáticos de interfaz (HTML, CSS, JS, íconos),
# excluyendo estrictamente bases de datos (.db), credenciales (.env) o fotos de prueba.

import os

block_cipher = None
BASE_DIR = os.path.abspath(SPECPATH)
ICON_PATH = os.path.join(BASE_DIR, 'static', 'img', 'sifma_icon.ico')

# Incluir únicamente recursos estáticos de diseño, nunca datos operativos ni .db
datas = [
    (os.path.join(BASE_DIR, 'templates'), 'templates'),
    (os.path.join(BASE_DIR, 'static', 'css'), os.path.join('static', 'css')),
    (os.path.join(BASE_DIR, 'static', 'js'), os.path.join('static', 'js')),
    (os.path.join(BASE_DIR, 'static', 'img'), os.path.join('static', 'img')),
    (os.path.join(BASE_DIR, 'static', 'docs'), os.path.join('static', 'docs')),
]

hiddenimports = [
    'flask',
    'flask_sqlalchemy',
    'sqlalchemy',
    'sqlalchemy.sql.default_comparator',
    'sqlalchemy.dialects.sqlite',
    'werkzeug',
    'jinja2',
    'cv2',
    'numpy',
    'serial',
    'dotenv',
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'clr_loader',
    'pythonnet',
]

a = Analysis(
    ['desktop_launcher.py'],
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
        'skimage', 'scikit-image', 'statsmodels', 'altair', 'plantcv', 'tornado'
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
    name='SIFMA_Desktop',
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

