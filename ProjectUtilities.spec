# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('multifile-zip-bomb/backward.pyd', 'multifile-zip-bomb')],
    datas=[('made_apk.py', '.'), ('made_exe.py', '.'), ('icons', 'icons'), ('frkb/tolk.py', 'frkb'), ('frkb/tolk2.py', 'frkb'), ('frkb/tolk3.py', 'frkb'), ('frkb/get_file.py', 'frkb'), ('multifile-zip-bomb/zip_bomb_multipe.py', 'multifile-zip-bomb'), ('multifile-zip-bomb/Readme.md', 'multifile-zip-bomb'), ('one_file_inside_zip_bomb', 'one_file_inside_zip_bomb'), ('png_bomb', 'png_bomb')],
    hiddenimports=['winreg', 'multiprocessing', 'isal', 'isal.isal_zlib'],
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
    name='ProjectUtilities',
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
)
