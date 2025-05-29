# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Exclude unnecessary modules to reduce size and build time
excludes = [
    'matplotlib', 'scipy', 'pandas', 'jupyter', 'IPython',
    'tornado', 'zmq', 'sqlite3', 'xmlrpc',
    'unittest', 'test', 'tests',
    'pip', 'numpy.tests',
    'PIL.tests', 'cv2.tests', 'requests.tests'
]

# Hidden imports to ensure all required modules are included
hiddenimports = [
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.simpledialog',
    'moviepy.editor',
    'moviepy.video.io.VideoFileClip',
    'moviepy.audio.io.AudioFileClip',
    'cv2',
    'requests',
    'bs4',
    'emoji',
    'pyttsx3',
    'threading',
    'tempfile',
    'urllib.parse',
    'datetime',
    'json',
    'subprocess',
    'xml',
    'xml.etree',
    'xml.etree.ElementTree',
    'xml.parsers',
    'xml.parsers.expat',
    'plistlib',
    'jaraco',
    'jaraco.text',
    'jaraco.functools',
    'more_itertools',
    'importlib_metadata',
    'zipp',
    'packaging',
    'packaging.version',
    'packaging.specifiers',
    'packaging.requirements',
    # Add UI module imports to prevent import errors
    'ui.input_tab',
    'ui.image_tab',
    'ui.video_tab',
    'ui.option_tab',
    'ui.batch_tab',
    'ui.image_selector',
    'ui.text_redirector',
    'models.video_generator',
    'services.image_service',
    'utils.gui_helpers',
    'utils.font_manager',  # ✅ Include font management utility
]

# Ensure FFmpeg binaries are included for standalone operation
binaries = []
ffmpeg_files = ['ffmpeg.exe', 'ffplay.exe', 'ffprobe.exe']
for ff in ffmpeg_files:
    if os.path.exists(ff):
        binaries.append((ff, '.'))
    else:
        print(f"Warning: {ff} not found - users will need FFmpeg installed")

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=[
        ('config.py', '.'),
        ('app_icon.ico', '.'),
        ('models', 'models'),
        ('services', 'services'),
        ('ui', 'ui'),
        ('utils', 'utils'),
        ('README.md', '.'),  # Include documentation
        ('fonts', 'fonts'),  # ✅ Include fonts directory for bundled fonts
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate files to reduce size
seen = set()
unique_datas = []
for item in a.datas:
    if item not in seen:
        seen.add(item)
        unique_datas.append(item)
a.datas = unique_datas

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],  # Don't bundle everything in one file for faster startup
    exclude_binaries=True,  # Separate binaries for faster loading
    name='Video Generator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Disable strip to prevent Windows warnings
    upx=False,  # Disable UPX - causes slow startup and compatibility issues
    console=True,  # Hide console for clean user experience
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico' if os.path.exists('app_icon.ico') else None,
    version='file_version_info.txt' if os.path.exists('file_version_info.txt') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,  # Disable strip to prevent Windows warnings
    upx=False,  # Disable UPX compression for faster startup
    name='Video Generator',
)
    