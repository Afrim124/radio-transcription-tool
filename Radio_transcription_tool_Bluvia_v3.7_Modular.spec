# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('config.py', '.'), ('logging_config.py', '.'), ('phrase_filtering.py', '.'), ('transcription.py', '.'), ('utils.py', '.'), ('gui.py', '.'), ('audio_processing.py', '.'), ('app.py', '.'), ('Bluvia images', 'Bluvia images')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['bin', 'ffmpeg', 'ffplay'],
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
    name='Radio_transcription_tool_Bluvia_v3.7_Modular',
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
    icon=['Bluvia images\\Bluebird app icon 2a.ico'],
)
