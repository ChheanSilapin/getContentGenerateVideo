@echo off
setlocal enabledelayedexpansion
title Video Generator - Inno Setup Installer Builder
cls

echo =====================================
echo    Video Generator Inno Installer
echo =====================================
echo.

REM Set Inno Setup path
set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_PATH%" (
    set "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
)
if not exist "%INNO_PATH%" (
    echo ✗ Inno Setup not found. Please install from: https://jrsoftware.org/isdl.php
    echo Expected location: C:\Program Files (x86)\Inno Setup 6\ISCC.exe
    pause
    exit /b 1
)

REM Check if executable exists
if not exist "dist\Video Generator\Video Generator.exe" (
    echo ✗ Executable not found at: dist\Video Generator\Video Generator.exe
    echo Please build the executable first using build.bat
    pause
    exit /b 1
)

REM Extract version from version.py
if not exist version.py (
    echo ✗ version.py not found
    pause
    exit /b 1
)

REM Extract version using PowerShell
powershell -Command "try { $content = Get-Content version.py | Select-String '__version__'; $version = $content.ToString().Split('=')[1].Trim().Trim('\"'); [System.IO.File]::WriteAllText('temp_version.txt', $version, [System.Text.Encoding]::ASCII) } catch { exit 1 }"
if !errorlevel! neq 0 (
    echo ✗ Failed to extract version from version.py
    pause
    exit /b 1
)

set /p APP_VERSION=<temp_version.txt
del temp_version.txt >nul 2>&1
echo Using version: %APP_VERSION%

REM Update version in Inno Setup script
powershell -Command "try { (Get-Content 'video_generator_setup.iss') -replace '#define MyAppVersion \".*\"', '#define MyAppVersion \"%APP_VERSION%\"' | Set-Content 'video_generator_setup.iss' } catch { exit 1 }"
if !errorlevel! neq 0 (
    echo ✗ Failed to update version in Inno Setup script
    pause
    exit /b 1
)

echo Building Inno Setup installer...
"%INNO_PATH%" "video_generator_setup.iss"
if !errorlevel! neq 0 (
    echo ✗ Inno Setup installer build failed
    pause
    exit /b 1
)

echo ✓ Installer created successfully!
echo Location: dist\Video Generator_Setup_%APP_VERSION%.exe

REM Check if installer was actually created
if exist "dist\Video Generator_Setup_%APP_VERSION%.exe" (
    echo ✓ Installer verified: dist\Video Generator_Setup_%APP_VERSION%.exe
    
    REM Get file size
    for %%A in ("dist\Video Generator_Setup_%APP_VERSION%.exe") do (
        set "size=%%~zA"
        set /a "sizeMB=!size!/1024/1024"
        echo Size: !sizeMB! MB
    )
    
    echo.
    echo Would you like to test the installer? (y/n)
    set /p test_choice="> "
    if /i "!test_choice!"=="y" (
        echo Starting installer...
        start "" "dist\Video Generator_Setup_%APP_VERSION%.exe"
    )
) else (
    echo ✗ Installer was not created
    exit /b 1
)

echo.
echo Build complete!
pause
