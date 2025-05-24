# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'sqlite3',
        'pyodbc', 
        'tkinter',
        'tkinter.ttk',
        'PIL.Image',
        'pystray',
        'pandas',
        'numpy',    # Pandas lo necesita
        'pytz',     # Pandas lo necesita para fechas
        'dateutil'  # Por si acaso
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Solo exclusiones seguras
        'gi', 'Xlib',
        'jupyter', 'jupyter_client', 'jupyter_core',
        'IPython', 'notebook',
        'matplotlib', 'scipy', 'seaborn',
        'pytest', 'unittest', 'setuptools', 'pip'
    ],
    noarchive=False,
    optimize=1,  # Optimización moderada
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='imputaciones_1.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Sin strip para mayor compatibilidad
    upx=True,
    upx_exclude=['vcruntime140.dll', 'python3.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icono.ico'
)