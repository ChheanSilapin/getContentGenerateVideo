# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('ffmpeg.exe', '.'), ('ffplay.exe', '.'), ('ffprobe.exe', '.')],
    datas=[('config.py', '.'), ('version.py', '.'), ('utils', 'utils'), ('models', 'models'), ('services', 'services'), ('ui', 'ui')],
    hiddenimports=['ui.video_tab', 'ui.gui', 'models.video_generator_refactored', 'models.video_processor', 'models.batch_processor', 'models.cleanup_manager', 'services.video_service', 'services.audio_service', 'services.subtitle_service', 'services.merge_service', 'services.video_optimization', 'utils.settings_manager', 'utils.folder_processor', 'Final_Video', 'moviepy.editor', 'pyttsx3', 'PIL'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['cv2', 'scipy', 'matplotlib'],
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
    name='VideoGenerator_1.0.4',
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
