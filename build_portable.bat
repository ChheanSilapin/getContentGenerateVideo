@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Video Generator - Portable Build Script
echo ========================================
echo Building minimal executable with model downloads
echo.

REM Check if we're in the right directory
if not exist "main.py" (
    echo ERROR: main.py not found!
    echo Make sure you're running this from the project root directory.
    pause
    exit /b 1
)

REM Check for spec file
if not exist "video_generator.spec" (
    echo ERROR: video_generator.spec not found!
    echo Make sure the spec file is in the project root directory.
    pause
    exit /b 1
)

set SPEC_FILE=video_generator.spec
echo  Using: video_generator.spec

REM Check if PyInstaller is available
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller not found!
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo  PyInstaller found

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"

REM Find and clean Python cache files
for /r %%i in (*.pyc) do del "%%i" >nul 2>&1
for /r %%i in (__pycache__) do rmdir /s /q "%%i" >nul 2>&1

echo  Previous builds cleaned

REM Check for optional files
echo.
echo Checking for optional files...

if exist "app_icon.ico" (
    echo  Found app_icon.ico
) else (
    echo  app_icon.ico not found (will use default icon)
)

if exist "LICENSE.txt" (
    echo  Found LICENSE.txt
) else (
    echo  LICENSE.txt not found (creating default)
    echo MIT License > LICENSE.txt
    echo. >> LICENSE.txt
    echo Copyright (c) 2024 Video Generator >> LICENSE.txt
    echo. >> LICENSE.txt
    echo Permission is hereby granted, free of charge, to any person obtaining a copy >> LICENSE.txt
    echo of this software and associated documentation files (the "Software"), to deal >> LICENSE.txt
    echo in the Software without restriction. >> LICENSE.txt
)

REM Check for libsndfile DLLs (required for Kokoro TTS)
echo.
echo Checking for libsndfile DLLs...
set DLL_MISSING=0

if not exist "libsndfile.dll" (
    echo  libsndfile.dll not found in project root
    set DLL_MISSING=1
)

if not exist "libsndfile_x64.dll" (
    echo  libsndfile_x64.dll not found in project root
    set DLL_MISSING=1
)

if !DLL_MISSING!==1 (
    echo  Attempting to copy DLLs from Python installation...
    python -c "import soundfile; import os; import shutil; import glob; site_packages = os.path.dirname(soundfile.__file__); soundfile_data_dir = os.path.join(site_packages, '_soundfile_data'); [shutil.copy2(dll, '.') for dll in glob.glob(os.path.join(soundfile_data_dir, 'libsndfile*.dll')) if os.path.exists(dll)]; print('DLLs copied successfully')" 2>nul

    REM Check again after copying
    if not exist "libsndfile.dll" if not exist "libsndfile_x64.dll" (
        echo  WARNING: Could not find or copy libsndfile DLLs
        echo  Kokoro TTS may not work properly in the built executable
        echo  Please ensure soundfile package is installed: pip install soundfile
    ) else (
        echo  libsndfile DLLs found/copied successfully
    )
) else (
    echo  libsndfile DLLs found
)

REM Build with PyInstaller
echo.
echo ========================================
echo Building executable...
echo ========================================
echo Using spec file: %SPEC_FILE%
echo.

python -m PyInstaller %SPEC_FILE% --clean --noconfirm

if errorlevel 1 (
    echo.
    echo  BUILD FAILED!
    echo Check the error messages above.
    pause
    exit /b 1
)

REM Check if build was successful
if not exist "dist\VideoGenerator_1.0.9\VideoGenerator_1.0.9.exe" (
    echo.
    echo  BUILD FAILED!
    echo VideoGenerator.exe not found in dist folder.
    pause
    exit /b 1
)

echo.
echo  BUILD SUCCESSFUL!

REM Verify DLLs are in the build output
echo.
echo Verifying DLLs in build output...
set BUILD_DIR=dist\VideoGenerator_1.0.9

if not exist "%BUILD_DIR%\libsndfile.dll" if not exist "%BUILD_DIR%\libsndfile_x64.dll" (
    echo  WARNING: DLLs not found in build output
    echo  This may cause Kokoro TTS to fail at runtime
) else (
    echo  DLLs successfully included in build
)

echo  DLL files in build output:
dir "%BUILD_DIR%\libsndfile*.dll" /b 2>nul

REM Get file size
for %%A in ("dist\VideoGenerator_1.0.9\VideoGenerator_1.0.9.exe") do set size=%%~zA
set /a size_mb=!size!/1024/1024

echo.
echo ========================================
echo Build Summary
echo ========================================
echo Executable: dist\VideoGenerator_1.0.9\VideoGenerator_1.0.9.exe
echo Size: !size_mb! MB
echo Type: Portable (models downloaded on first run)
echo DLL Support: libsndfile included for Kokoro TTS
echo.

echo.
echo ========================================
echo Next Steps
echo ========================================
echo 1. Test the executable: dist\VideoGenerator_1.0.9\VideoGenerator_1.0.9.exe
echo 2. Build installer: run build_installer.bat
echo 3. Test complete workflow: install and run first-time setup
echo.
echo The executable is now ready for distribution!
echo.

pause
