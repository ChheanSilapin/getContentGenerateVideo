# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('ffmpeg.exe', '.'), ('ffplay.exe', '.'), ('ffprobe.exe', '.')],
    datas=[('config.py', '.'), ('version.py', '.'), ('app_icon.ico', '.')],
    hiddenimports=['ui.video_tab', 'ui.gui', 'models.video_generator', 'services.audio_service', 'services.video_service', 'services.subtitle_service', 'utils.folder_processor', 'Final_Video'],
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
    name='VideoGenerator_1.0.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app_icon.ico'],
)
