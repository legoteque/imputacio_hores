# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['sqlite3', 'sqlalchemy.dialects.sqlite.pysqlite', 'pyarrow'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['gi', 'Xlib'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
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
    icon=[r'C:\Users\NET4\OneDrive - ETL GLOBAL\ETL GLOBAL\SQL Server\App Imputacion Horas\icono.ico']
)
