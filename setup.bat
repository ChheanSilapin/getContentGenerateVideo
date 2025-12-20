@echo off
echo ========================================
echo    Video Generator - Setup
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found! Please install Git from git-scm.com
    pause
    exit /b 1
)

:: Clone if not already in project folder
if not exist "main.py" (
    echo [INFO] Cloning project from GitHub...
    git clone https://github.com/MyWork22-creator/VideoGenerate_Tools.git
    cd VideoGenerate_Tools
)

:: Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing uv package manager...
    pip install uv
)

:: Install dependencies
echo [INFO] Installing dependencies...
uv sync

echo.
echo ========================================
echo    Setup Complete!
echo    Run 'run.bat' to start the app
echo ========================================
pause
