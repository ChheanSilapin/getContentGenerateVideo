@echo off
setlocal enabledelayedexpansion
title Video Generator Build Tool
cls
echo ================================
echo       Video Generator Tool
echo ================================
echo.

:main_menu
echo What would you like to do?
echo 1. Update version and build
echo 2. Build executable only (clean build)
echo 3. Build installer only
echo 4. Build both executable and installer
echo 5. Update version only
echo 6. Exit
echo.
set /p main_choice="Enter your choice (1-6): "

if "%main_choice%"=="1" goto update_and_build
if "%main_choice%"=="2" goto build_exe_only
if "%main_choice%"=="3" goto build_installer_only
if "%main_choice%"=="4" goto build_both
if "%main_choice%"=="5" goto update_version_only
if "%main_choice%"=="6" goto end

echo Invalid choice. Try again.
echo.
goto main_menu

:update_and_build
call :update_version
echo.
call :choose_build_type
goto main_menu

:choose_build_type
echo What would you like to build with the new version?
echo 1. Build executable only
echo 2. Build installer only
echo 3. Build both
echo 4. Return to main menu
echo.
set /p build_choice="Enter your choice (1-4): "
if "%build_choice%"=="1" call :build_executable
if "%build_choice%"=="2" call :build_installer
if "%build_choice%"=="3" (
    call :build_executable
    call :build_installer
)
goto main_menu

:update_version_only
call :update_version
goto main_menu

:build_exe_only
call :build_executable
goto main_menu

:build_installer_only
call :build_installer
goto main_menu

:build_both
call :build_executable
call :build_installer
goto main_menu

:update_version
echo Version Update
echo ==============

set /p new_version="Enter new version (e.g., 1.2.3): "
echo Updating version to !new_version!...

REM Create version.py
> version.py (
    echo # Version information for Video Generator
    echo __version__ = "!new_version!"
)

REM Create file_version_info.txt
> file_version_info.txt (
    echo # UTF-8
    echo VSVersionInfo^(
    echo   ffi=FixedFileInfo^(
    echo     filevers=^(!new_version:.=, !, 0^),
    echo     prodvers=^(!new_version:.=, !, 0^),
    echo     mask=0x3f,
    echo     flags=0x0,
    echo     OS=0x40004,
    echo     fileType=0x1,
    echo     subtype=0x0,
    echo     date=^(0, 0^)
    echo   ^),
    echo   kids=[
    echo     StringFileInfo^(
    echo       [StringTable^(
    echo         u'040904B0',
    echo         [StringStruct^(u'CompanyName', u'Your Company'^),
    echo          StringStruct^(u'FileDescription', u'Video Generator'^),
    echo          StringStruct^(u'FileVersion', u'!new_version!'^),
    echo          StringStruct^(u'InternalName', u'video_generator'^),
    echo          StringStruct^(u'ProductName', u'Video Generator'^),
    echo          StringStruct^(u'ProductVersion', u'!new_version!'^),
    echo          StringStruct^(u'LegalCopyright', u'Copyright ^(c^) 2023'^),
    echo          StringStruct^(u'OriginalFilename', u'Video Generator.exe'^)]^)
    echo       ]^),
    echo     VarFileInfo^([VarStruct^(u'Translation', [1033, 1200]^)]^)
    echo   ]
    echo ^)
)
echo Version info updated to !new_version!
goto :eof

:build_executable
echo Building Executable
echo ===================

REM Ensure version.py exists
if not exist version.py (
    echo __version__ = "0.1.0" > version.py
)

REM Set paths
set PYTHON="C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe"
set VENV=video_generator_env

if not exist %VENV% (
    echo Creating virtual environment...
    %PYTHON% -m venv %VENV%
)

echo Installing dependencies...
%VENV%\Scripts\pip.exe install -r requirements.txt > nul
%VENV%\Scripts\pip.exe install pyinstaller > nul

echo Compiling with PyInstaller...
%VENV%\Scripts\pyinstaller.exe video_generator.spec --clean > nul

if exist "dist\Video Generator.exe" (
    echo ✓ Executable created: dist\Video Generator.exe
) else (
    echo ✗ Build failed.
)
goto :eof

:build_installer
echo Building Installer
echo ===================

REM Check if executable exists
if not exist "dist\Video Generator.exe" (
    echo Executable not found. Building now...
    call :build_executable
)

REM Extract version
powershell -Command "[System.IO.File]::WriteAllText('temp_version.txt', (Get-Content version.py | Select-String '__version__').ToString().Split('=')[1].Trim().Trim('\"'), [System.Text.Encoding]::ASCII)"
set /p APP_VERSION=<temp_version.txt
del temp_version.txt
echo Using version: !APP_VERSION!

REM Create NSIS script
> installer.nsi (
    echo ^^!include "MUI2.nsh"
    echo Name "Video Generator"
    echo OutFile "dist\Video Generator_Setup_!APP_VERSION!.exe"
    echo InstallDir "$PROGRAMFILES\Video Generator"
    echo ^^!define MUI_ABORTWARNING
    echo ^^!insertmacro MUI_PAGE_WELCOME
    echo ^^!insertmacro MUI_PAGE_DIRECTORY
    echo ^^!insertmacro MUI_PAGE_INSTFILES
    echo ^^!insertmacro MUI_PAGE_FINISH
    echo ^^!insertmacro MUI_LANGUAGE "English"
    echo Section "Install"
    echo     SetOutPath "$INSTDIR"
    echo     File /r "dist\Video Generator\*"
    echo     WriteUninstaller "$INSTDIR\Uninstall.exe"
    echo     CreateShortcut "$DESKTOP\Video Generator.lnk" "$INSTDIR\Video Generator.exe"
    echo SectionEnd
    echo Section "Uninstall"
    echo     Delete "$INSTDIR\Uninstall.exe"
    echo     RMDir /r "$INSTDIR"
    echo     Delete "$DESKTOP\Video Generator.lnk"
    echo SectionEnd
)

REM Build NSIS installer
set NSIS_PATH="C:\Program Files (x86)\NSIS\makensis.exe"
if not exist %NSIS_PATH% (
    echo ✗ NSIS not found. Install it from https://nsis.sourceforge.io/Download
    goto :eof
)

echo Compiling NSIS installer...
%NSIS_PATH% installer.nsi > nul
echo ✓ Installer created: dist\Video Generator_Setup_!APP_VERSION!.exe

REM Create portable version
mkdir "dist\Video_Generator_Portable" 2>nul
copy /y "dist\Video Generator\Video Generator.exe" "dist\Video_Generator_Portable\" >nul
copy /y "ffmpeg.exe" "dist\Video_Generator_Portable\" >nul
copy /y "ffplay.exe" "dist\Video_Generator_Portable\" >nul
copy /y "ffprobe.exe" "dist\Video_Generator_Portable\" >nul

> "dist\Video_Generator_Portable\README.txt" (
    echo Video Generator (Portable)
    echo ==========================
    echo 1. Extract all files
    echo 2. Run "Video Generator.exe"
)

> "dist\Video_Generator_Portable\Run_Video_Generator.bat" (
    echo @echo off
    echo "Video Generator.exe"
)

powershell -Command "Compress-Archive -Path 'dist\Video_Generator_Portable\*' -DestinationPath 'dist\Video_Generator_Portable.zip' -Force"

echo ✓ Portable ZIP created: dist\Video_Generator_Portable.zip
goto :eof

:end
echo.
echo Build process completed!
pause
