# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_ui_v2.py'],
    pathex=[],
    binaries=[],
    datas=[('core_v2', 'core_v2'), ('ui_v2', 'ui_v2')],
    hiddenimports=['matplotlib', 'networkx'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Sd0p-V3.5',
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
    icon=['ManS2.ico'],
)
