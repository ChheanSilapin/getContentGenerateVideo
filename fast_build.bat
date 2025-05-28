@echo off
setlocal enabledelayedexpansion
title Video Generator - Fast Build Tool
cls
echo ========================================
echo    Video Generator - Fast Build Tool
echo ========================================
echo.

REM Initialize error tracking
set "BUILD_ERRORS=0"
set "START_TIME=%TIME%"

echo [INFO] Starting optimized build process...
echo [INFO] Build started at: %START_TIME%
echo.

REM Check for FFmpeg binaries first
echo [STEP 1/6] Checking FFmpeg binaries...
set "FFMPEG_FOUND=0"
if exist "ffmpeg.exe" (
    if exist "ffplay.exe" (
        if exist "ffprobe.exe" (
            set "FFMPEG_FOUND=1"
            echo ✓ FFmpeg binaries found - will be bundled for standalone operation
        )
    )
)

if !FFMPEG_FOUND! equ 0 (
    echo ⚠️  FFmpeg binaries not found in current directory
    echo    Users will need to install FFmpeg separately
    echo    Download from: https://ffmpeg.org/download.html
    echo.
    set /p continue="Continue build anyway? (y/n): "
    if /i not "!continue!"=="y" (
        echo Build cancelled.
        goto end
    )
)

REM Detect Python
echo [STEP 2/6] Detecting Python installation...
set "PYTHON_FOUND=0"
set "PYTHON="

for %%P in ("python" "py") do (
    %%P --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON=%%P"
        set "PYTHON_FOUND=1"
        echo ✓ Found Python: %%P
        goto python_found
    )
)

:python_found
if !PYTHON_FOUND! equ 0 (
    echo ✗ Python not found. Please install Python 3.8+ and add it to PATH.
    set /a BUILD_ERRORS+=1
    goto end
)

REM Set virtual environment path
set VENV=video_generator_env

REM Create or reuse virtual environment
echo [STEP 3/6] Setting up virtual environment...
if not exist %VENV% (
    echo Creating new virtual environment...
    !PYTHON! -m venv %VENV%
    if !errorlevel! neq 0 (
        echo ✗ Failed to create virtual environment
        set /a BUILD_ERRORS+=1
        goto end
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Using existing virtual environment
)

REM Smart dependency installation
echo [STEP 4/6] Installing dependencies...
set "REQUIREMENTS_HASH="
if exist "requirements.txt" (
    for /f %%i in ('powershell -command "Get-FileHash requirements.txt -Algorithm MD5 | Select-Object -ExpandProperty Hash"') do set "REQUIREMENTS_HASH=%%i"
)

set "INSTALLED_HASH="
if exist "%VENV%\.requirements_hash" (
    set /p INSTALLED_HASH=<"%VENV%\.requirements_hash"
)

if "!REQUIREMENTS_HASH!"=="!INSTALLED_HASH!" (
    echo ✓ Dependencies already up to date, skipping installation
) else (
    echo Installing/updating dependencies...
    %VENV%\Scripts\pip.exe install --upgrade pip --quiet
    %VENV%\Scripts\pip.exe install -r requirements.txt --quiet
    if !errorlevel! neq 0 (
        echo ✗ Failed to install requirements
        set /a BUILD_ERRORS+=1
        goto end
    )
    
    %VENV%\Scripts\pip.exe install pyinstaller --quiet
    if !errorlevel! neq 0 (
        echo ✗ Failed to install PyInstaller
        set /a BUILD_ERRORS+=1
        goto end
    )
    
    echo !REQUIREMENTS_HASH! > "%VENV%\.requirements_hash"
    echo ✓ Dependencies installed successfully
)

REM Ensure version file exists
echo [STEP 5/6] Preparing build files...
if not exist version.py (
    echo Creating default version.py...
    echo __version__ = "1.0.0" > version.py
)

REM Clean only dist folder, keep build cache for faster rebuilds
if exist dist (
    echo Cleaning previous build...
    rmdir /s /q dist
)

REM Build with optimized settings
echo [STEP 6/6] Building executable...
echo This may take a few minutes for the first build...
echo Building with optimizations for faster startup and smaller size...

%VENV%\Scripts\pyinstaller.exe video_generator.spec --noconfirm --log-level WARN
if !errorlevel! neq 0 (
    echo ✗ PyInstaller build failed
    set /a BUILD_ERRORS+=1
    goto end
)

REM Verify build success
if exist "dist\Video Generator\Video Generator.exe" (
    echo ✓ Executable created successfully!
    
    REM Get file size
    for %%A in ("dist\Video Generator\Video Generator.exe") do (
        set "FILE_SIZE=%%~zA"
        set /a "FILE_SIZE_MB=!FILE_SIZE!/1024/1024"
    )
    
    echo.
    echo ========================================
    echo           BUILD SUCCESSFUL!
    echo ========================================
    echo Executable: dist\Video Generator\Video Generator.exe
    echo Size: !FILE_SIZE_MB! MB
    
    if !FFMPEG_FOUND! equ 1 (
        echo ✓ FFmpeg bundled - fully standalone
    ) else (
        echo ⚠️  FFmpeg not bundled - users need FFmpeg installed
    )
    
    echo.
    echo The application is now ready for distribution!
    echo Users do NOT need Python installed to run it.
    
) else (
    echo ✗ Build failed - executable not found
    set /a BUILD_ERRORS+=1
)

:end
set "END_TIME=%TIME%"
echo.
echo Build started: %START_TIME%
echo Build ended:   %END_TIME%

if !BUILD_ERRORS! gtr 0 (
    echo.
    echo ⚠️  Build completed with !BUILD_ERRORS! error(s)
    echo Check the output above for details.
) else (
    echo.
    echo ✓ Build process completed successfully!
    echo.
    echo Next steps:
    echo 1. Test the executable: "dist\Video Generator\Video Generator.exe"
    echo 2. Create installer with: build.bat (option 3)
    echo 3. Distribute the entire "dist\Video Generator" folder
)

echo.
pause 