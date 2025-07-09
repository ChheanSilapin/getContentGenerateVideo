@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Video Generator - Application Launcher
echo ========================================

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check for virtual environment (try multiple names)
set "VENV_PATH="
if exist "video_generator_env\Scripts\python.exe" (
    set "VENV_PATH=video_generator_env"
    echo  Found virtual environment: video_generator_env
) else if exist "venv\Scripts\python.exe" (
    set "VENV_PATH=venv"
    echo  Found virtual environment: venv
) else (
    echo  No virtual environment found!
    echo.
    echo Please run setup first:
    echo   - For minimal setup: double-click setup_minimal.bat
    echo   - For full setup: double-click setup.bat
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call "%VENV_PATH%\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment
    echo Try running setup again.
    pause
    exit /b 1
)

REM Quick dependency check
echo Checking core dependencies...
python -c "import edge_tts, moviepy, PIL, pydub" >nul 2>&1
if errorlevel 1 (
    echo Core dependencies missing or broken
    echo Please run setup again to fix dependencies.
    echo.
    pause
    exit /b 1
)

echo  Core dependencies OK

REM Check if main.py exists
if not exist "main.py" (
    echo  main.py not found!
    echo Make sure you're running this from the correct directory.
    echo.
    pause
    exit /b 1
)

echo  Application files found

REM Launch the application
echo.
echo ========================================
echo Starting Video Generator...
echo ========================================
echo.

python main.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ========================================
    echo Application exited with error
    echo ========================================
    echo.
    echo If you see import errors, try running setup again.
    echo If you see other errors, check the error messages above.
    echo.
) else (
    echo.
    echo ========================================
    echo Application closed normally
    echo ========================================
    echo.
)

echo Press any key to close this window...
pause >nul
