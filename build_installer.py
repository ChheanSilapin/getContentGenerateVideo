#!/usr/bin/env python3
"""
Build installer for Video Generator
Creates a Windows installer that includes FFmpeg
"""
import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
import tempfile

# Configuration
APP_NAME = "Video Generator"
APP_VERSION = "1.0.0"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
MAIN_SCRIPT = "main.py"
ICON_FILE = "app_icon.ico"  # Updated to match your icon file name

def download_ffmpeg(target_dir):
    """Download and extract FFmpeg binaries"""
    print(f"Downloading FFmpeg from {FFMPEG_URL}...")
    
    # Create a temporary directory for the download
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "ffmpeg.zip")
        
        # Download the file
        urllib.request.urlretrieve(FFMPEG_URL, zip_path)
        
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the bin directory in the extracted files
        ffmpeg_dir = None
        for root, dirs, files in os.walk(temp_dir):
            if "bin" in dirs:
                ffmpeg_dir = os.path.join(root, "bin")
                break
        
        if not ffmpeg_dir:
            raise Exception("Could not find FFmpeg binaries in the downloaded package")
        
        # Copy the FFmpeg binaries to the target directory
        for file in ["ffmpeg.exe", "ffplay.exe", "ffprobe.exe"]:
            src = os.path.join(ffmpeg_dir, file)
            dst = os.path.join(target_dir, file)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"Copied {file} to {target_dir}")
            else:
                print(f"Warning: {file} not found in FFmpeg package")

def build_installer():
    """Build the installer using PyInstaller and NSIS"""
    # Ensure output directories exist
    os.makedirs("build", exist_ok=True)
    os.makedirs("dist", exist_ok=True)
    
    # Download FFmpeg to the current directory
    download_ffmpeg(".")
    
    # Create spec file for PyInstaller
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=['.'],
    binaries=[
        ('ffmpeg.exe', '.'),
        ('ffplay.exe', '.'),
        ('ffprobe.exe', '.')
    ],
    datas=[
        ('config.py', '.'),
        ('README.md', '.'),
        ('requirements.txt', '.'),
        ('models', 'models'),
        ('services', 'services'),
        ('ui', 'ui'),
        ('utils', 'utils')
    ],
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
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
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True to show console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{ICON_FILE}' if os.path.exists('{ICON_FILE}') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{APP_NAME}',
)
    """
    
    with open("video_generator.spec", "w") as f:
        f.write(spec_content)
    
    # Run PyInstaller
    print("Building executable with PyInstaller...")
    subprocess.run([sys.executable, "-m", "PyInstaller", "video_generator.spec"], check=True)
    
    # Create NSIS installer script without icon references
    nsis_script = f"""
; Video Generator Installer Script
!include "MUI2.nsh"

; General
Name "{APP_NAME}"
OutFile "dist/{APP_NAME}_Setup_{APP_VERSION}.exe"
InstallDir "$PROGRAMFILES\\{APP_NAME}"
InstallDirRegKey HKCU "Software\\{APP_NAME}" ""

; Interface Settings
!define MUI_ABORTWARNING

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer Sections
Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Add files
    File /r "dist\\{APP_NAME}\\*.*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\\{APP_NAME}"
    CreateShortcut "$SMPROGRAMS\\{APP_NAME}\\{APP_NAME}.lnk" "$INSTDIR\\{APP_NAME}.exe"
    CreateShortcut "$SMPROGRAMS\\{APP_NAME}\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
    CreateShortcut "$DESKTOP\\{APP_NAME}.lnk" "$INSTDIR\\{APP_NAME}.exe"
    
    ; Write registry keys
    WriteRegStr HKCU "Software\\{APP_NAME}" "" $INSTDIR
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "DisplayName" "{APP_NAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "UninstallString" "$\\"$INSTDIR\\Uninstall.exe$\\""
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "DisplayIcon" "$\\"$INSTDIR\\{APP_NAME}.exe$\\""
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "DisplayVersion" "{APP_VERSION}"
SectionEnd

; Uninstaller Section
Section "Uninstall"
    ; Remove files and directories
    Delete "$INSTDIR\\Uninstall.exe"
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\\{APP_NAME}\\{APP_NAME}.lnk"
    Delete "$SMPROGRAMS\\{APP_NAME}\\Uninstall.lnk"
    RMDir "$SMPROGRAMS\\{APP_NAME}"
    Delete "$DESKTOP\\{APP_NAME}.lnk"
    
    ; Remove registry keys
    DeleteRegKey HKCU "Software\\{APP_NAME}"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}"
SectionEnd
    """
    
    with open("installer.nsi", "w") as f:
        f.write(nsis_script)
    
    # Check if NSIS is installed
    nsis_path = "C:\\Program Files (x86)\\NSIS\\makensis.exe"
    if not os.path.exists(nsis_path):
        print("NSIS not found. Please install NSIS from https://nsis.sourceforge.io/Download")
        print("After installing NSIS, run: makensis installer.nsi")
        return
    
    # Build the installer
    print("Building installer with NSIS...")
    subprocess.run([nsis_path, "installer.nsi"], check=True)
    
    print(f"Installer created: dist/{APP_NAME}_Setup_{APP_VERSION}.exe")

def create_portable_package():
    """Create a portable ZIP package that users can extract and run directly"""
    print("Creating portable package...")
    
    # Create a directory for the portable version
    portable_dir = "dist/Video_Generator_Portable"
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    os.makedirs(portable_dir)
    
    # Copy the executable and FFmpeg files
    shutil.copy2("dist/Video Generator.exe", os.path.join(portable_dir, "Video Generator.exe"))
    for file in ["ffmpeg.exe", "ffplay.exe", "ffprobe.exe"]:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(portable_dir, file))
    
    # Create a README file
    readme_content = """# Video Generator (Portable Version)

## How to Use
1. Extract all files to a folder of your choice
2. Run "Video Generator.exe" to start the application
3. Make sure you don't move the FFmpeg files away from the executable

## Troubleshooting
- If you see an error about missing DLLs, you may need to install the Visual C++ Redistributable
- Make sure all files remain in the same folder
"""
    with open(os.path.join(portable_dir, "README.txt"), "w") as f:
        f.write(readme_content)
    
    # Create a batch file to run the application
    batch_content = """@echo off
echo Starting Video Generator...
"Video Generator.exe"
if errorlevel 1 (
    echo An error occurred. Press any key to exit.
    pause > nul
)
"""
    with open(os.path.join(portable_dir, "Run_Video_Generator.bat"), "w") as f:
        f.write(batch_content)
    
    # Create the ZIP file
    zip_path = "dist/Video_Generator_Portable.zip"
    print(f"Creating ZIP file: {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(portable_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, portable_dir))
    
    print(f"Portable package created: {zip_path}")
    return zip_path

if __name__ == "__main__":
    build_installer()
    create_portable_package()


