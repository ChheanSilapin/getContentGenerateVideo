@echo off
setlocal enabledelayedexpansion
title Video Generator Build Tool
cls
echo ================================
echo       Video Generator Tool
echo ================================
echo.

REM Initialize error tracking
set "BUILD_ERRORS=0"

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
if !BUILD_ERRORS! gtr 0 goto main_menu
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
    if !BUILD_ERRORS! equ 0 call :build_installer
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
if !BUILD_ERRORS! equ 0 call :build_installer
goto main_menu

:detect_python
echo Detecting Python installation...
set "PYTHON_FOUND=0"
set "PYTHON="

REM Try common Python installation paths
for %%P in (
    "python"
    "py"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%PROGRAMFILES%\Python312\python.exe"
    "%PROGRAMFILES%\Python311\python.exe"
    "%PROGRAMFILES%\Python310\python.exe"
    "%PROGRAMFILES(x86)%\Python312\python.exe"
    "%PROGRAMFILES(x86)%\Python311\python.exe"
    "%PROGRAMFILES(x86)%\Python310\python.exe"
) do (
    %%P --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON=%%P"
        set "PYTHON_FOUND=1"
        echo Found Python: %%P
        goto python_found
    )
)

:python_found
if !PYTHON_FOUND! equ 0 (
    echo ✗ Python not found. Please install Python 3.10+ and add it to PATH.
    set /a BUILD_ERRORS+=1
    goto :eof
)
goto :eof

:update_version
echo Version Update
echo ==============

set /p new_version="Enter new version (e.g., 1.2.3): "
echo Updating version to !new_version!...

REM Validate version format (basic check)
echo !new_version! | findstr /R "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul
if !errorlevel! neq 0 (
    echo ✗ Invalid version format. Please use format like 1.2.3
    set /a BUILD_ERRORS+=1
    goto :eof
)

REM Create version.py
> version.py (
    echo # Version information for Video Generator
    echo __version__ = "!new_version!"
)

REM Parse version components for Windows version info
for /f "tokens=1,2,3 delims=." %%a in ("!new_version!") do (
    set "VER_MAJOR=%%a"
    set "VER_MINOR=%%b"
    set "VER_PATCH=%%c"
)

REM Create file_version_info.txt with proper formatting
> file_version_info.txt (
    echo # UTF-8
    echo VSVersionInfo^(
    echo   ffi=FixedFileInfo^(
    echo     filevers=^(!VER_MAJOR!,!VER_MINOR!,!VER_PATCH!,0^),
    echo     prodvers=^(!VER_MAJOR!,!VER_MINOR!,!VER_PATCH!,0^),
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
    echo          StringStruct^(u'LegalCopyright', u'Copyright ^(c^) 2024'^),
    echo          StringStruct^(u'OriginalFilename', u'Video Generator.exe'^)]^)
    echo       ]^),
    echo     VarFileInfo^([VarStruct^(u'Translation', [1033, 1200]^)]^)
    echo   ]
    echo ^)
)
echo ✓ Version info updated to !new_version!
goto :eof

:build_executable
echo Building Executable
echo ===================

REM Detect Python
call :detect_python
if !BUILD_ERRORS! gtr 0 goto :eof

REM Ensure version.py exists
if not exist version.py (
    echo Creating default version.py...
    echo __version__ = "0.1.0" > version.py
)

REM Set virtual environment path
set VENV=video_generator_env

REM Create virtual environment if it doesn't exist
if not exist %VENV% (
    echo Creating virtual environment...
    !PYTHON! -m venv %VENV%
    if !errorlevel! neq 0 (
        echo ✗ Failed to create virtual environment
        set /a BUILD_ERRORS+=1
        goto :eof
    )
)

REM Check if virtual environment was created successfully
if not exist "%VENV%\Scripts\pip.exe" (
    echo ✗ Virtual environment creation failed
    set /a BUILD_ERRORS+=1
    goto :eof
)

echo Installing dependencies...
%VENV%\Scripts\pip.exe install -r requirements.txt
if !errorlevel! neq 0 (
    echo ✗ Failed to install requirements
    set /a BUILD_ERRORS+=1
    goto :eof
)

%VENV%\Scripts\pip.exe install pyinstaller
if !errorlevel! neq 0 (
    echo ✗ Failed to install PyInstaller
    set /a BUILD_ERRORS+=1
    goto :eof
)

echo Compiling with PyInstaller...
%VENV%\Scripts\pyinstaller.exe video_generator.spec --clean
if !errorlevel! neq 0 (
    echo ✗ PyInstaller build failed
    set /a BUILD_ERRORS+=1
    goto :eof
)

REM Check if build was successful
if exist "dist\Video Generator\Video Generator.exe" (
    echo ✓ Executable created: dist\Video Generator\Video Generator.exe
) else (
    echo ✗ Build failed - executable not found
    set /a BUILD_ERRORS+=1
)
goto :eof

:build_installer
echo Building Installer
echo ===================

REM Check if executable exists
if not exist "dist\Video Generator\Video Generator.exe" (
    echo Executable not found. Building now...
    call :build_executable
    if !BUILD_ERRORS! gtr 0 goto :eof
)

REM Extract version with better error handling
if not exist version.py (
    echo ✗ version.py not found
    set /a BUILD_ERRORS+=1
    goto :eof
)

powershell -Command "try { $content = Get-Content version.py | Select-String '__version__'; $version = $content.ToString().Split('=')[1].Trim().Trim('\"'); [System.IO.File]::WriteAllText('temp_version.txt', $version, [System.Text.Encoding]::ASCII) } catch { exit 1 }"
if !errorlevel! neq 0 (
    echo ✗ Failed to extract version
    set /a BUILD_ERRORS+=1
    goto :eof
)

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
    set /a BUILD_ERRORS+=1
    goto :eof
)

echo Compiling NSIS installer...
%NSIS_PATH% installer.nsi
if !errorlevel! neq 0 (
    echo ✗ NSIS installer build failed
    set /a BUILD_ERRORS+=1
    goto :eof
)
echo ✓ Installer created: dist\Video Generator_Setup_!APP_VERSION!.exe

REM Create portable version
echo Creating portable version...
mkdir "dist\Video_Generator_Portable" 2>nul
copy /y "dist\Video Generator\Video Generator.exe" "dist\Video_Generator_Portable\" >nul
if !errorlevel! neq 0 (
    echo ✗ Failed to copy executable for portable version
    set /a BUILD_ERRORS+=1
    goto :eof
)

copy /y "ffmpeg.exe" "dist\Video_Generator_Portable\" >nul
copy /y "ffplay.exe" "dist\Video_Generator_Portable\" >nul
copy /y "ffprobe.exe" "dist\Video_Generator_Portable\" >nul

> "dist\Video_Generator_Portable\README.txt" (
    echo Video Generator ^(Portable^)
    echo ==========================
    echo 1. Extract all files
    echo 2. Run "Video Generator.exe"
)

> "dist\Video_Generator_Portable\Run_Video_Generator.bat" (
    echo @echo off
    echo "Video Generator.exe"
)

powershell -Command "try { Compress-Archive -Path 'dist\Video_Generator_Portable\*' -DestinationPath 'dist\Video_Generator_Portable.zip' -Force } catch { exit 1 }"
if !errorlevel! neq 0 (
    echo ✗ Failed to create portable ZIP
    set /a BUILD_ERRORS+=1
    goto :eof
)

echo ✓ Portable ZIP created: dist\Video_Generator_Portable.zip
goto :eof

:end
if !BUILD_ERRORS! gtr 0 (
    echo.
    echo ⚠️  Build completed with !BUILD_ERRORS! error^(s^)
) else (
    echo.
    echo ✓ Build process completed successfully!
)
pause
