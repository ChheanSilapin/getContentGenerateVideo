@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Video Generator - Installer Build Script
echo ========================================
echo Creating professional NSIS installer
echo.

REM Check if executable exists
if not exist "dist\VideoGenerator\VideoGenerator.exe" (
    echo ERROR: VideoGenerator.exe not found!
    echo Please run build_portable.bat first to create the executable.
    pause
    exit /b 1
)

echo  Executable found

REM Check if NSIS is installed
where makensis >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: NSIS (Nullsoft Scriptable Install System) not found!
    echo.
    echo Please install NSIS from: https://nsis.sourceforge.io/Download
    echo.
    echo After installation, make sure makensis.exe is in your PATH.
    echo Typical location: C:\Program Files (x86)\NSIS\makensis.exe
    echo.
    pause
    exit /b 1
)

echo  NSIS found

REM Check installer script
if not exist "installer.nsi" (
    echo ERROR: installer.nsi not found!
    echo Make sure the installer script is in the project root directory.
    pause
    exit /b 1
)

echo  Installer script found

REM Get executable size for installer
for %%A in ("dist\VideoGenerator\VideoGenerator.exe") do set exe_size=%%~zA
set /a exe_size_mb=!exe_size!/1024/1024

REM Get total distribution size
echo.
echo Calculating distribution size...
set total_size=0
for /r "dist\VideoGenerator" %%A in (*) do (
    set /a total_size+=%%~zA
)
set /a total_size_mb=!total_size!/1024/1024

echo  Distribution size: !total_size_mb! MB

REM Clean previous installer
if exist "VideoGeneratorSetup.exe" (
    echo.
    echo Removing previous installer...
    del "VideoGeneratorSetup.exe"
)

REM Build installer
echo.
echo ========================================
echo Building installer with NSIS...
echo ========================================
echo.

makensis installer.nsi

if errorlevel 1 (
    echo.
    echo  INSTALLER BUILD FAILED!
    echo Check the error messages above.
    echo.
    echo Common issues:
    echo - Missing files referenced in installer.nsi
    echo - NSIS syntax errors
    echo - Insufficient permissions
    echo.
    pause
    exit /b 1
)

REM Check if installer was created
if not exist "VideoGeneratorSetup.exe" (
    echo.
    echo  INSTALLER BUILD FAILED!
    echo VideoGeneratorSetup.exe not found.
    pause
    exit /b 1
)

echo.
echo  INSTALLER BUILD SUCCESSFUL!

REM Get installer size
for %%A in ("VideoGeneratorSetup.exe") do set installer_size=%%~zA
set /a installer_size_mb=!installer_size!/1024/1024

echo.
echo ========================================
echo Installer Summary
echo ========================================
echo Installer: VideoGeneratorSetup.exe
echo Installer Size: !installer_size_mb! MB
echo Distribution Size: !total_size_mb! MB
echo Compression Ratio: !installer_size_mb!/!total_size_mb! MB
echo.
echo Features:
echo - Professional installer interface
echo - User choice: Standard or Portable installation
echo - Desktop and Start Menu shortcuts (optional)
echo - Proper uninstaller
echo - Add/Remove Programs integration
echo - First-run model download
echo.

REM Test installer (optional)
echo ========================================
echo Testing Options
echo ========================================
echo 1. Test installer now (will install to temp location)
echo 2. Skip testing and finish
echo.
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo Testing installer...
    echo This will run the installer - you can cancel it after seeing it works.
    echo.
    pause
    start "" VideoGeneratorSetup.exe
    echo.
    echo Installer launched. Test the installation process.
) else (
    echo.
    echo Skipping installer test.
)

echo.
echo ========================================
echo Distribution Ready!
echo ========================================
echo.
echo Files created:
echo - VideoGeneratorSetup.exe (!installer_size_mb! MB) - Main installer
echo - dist\VideoGenerator\ - Portable application folder
echo.
echo Distribution strategy:
echo 1. Share VideoGeneratorSetup.exe for easy installation
echo 2. Or share dist\VideoGenerator\ folder for portable use
echo.
echo The installer provides:
echo - Small download size (!installer_size_mb! MB vs !total_size_mb! MB)
echo - Professional installation experience
echo - Works from any location (portable)
echo - Automatic model download on first run
echo.

pause
