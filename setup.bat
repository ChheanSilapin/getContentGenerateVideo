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

:: Check if FFmpeg is installed
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found!
    echo FFmpeg is REQUIRED for video processing.
    echo Please install from: https://ffmpeg.org/download.html
    echo Or use: winget install FFmpeg
    echo.
    pause
)

:: Clone if not already exists
if not exist "getContentGenerateVideo" (
    echo [INFO] Cloning project from GitHub...
    git clone https://github.com/ChheanSilapin/getContentGenerateVideo.git
)

:: Enter project folder
cd getContentGenerateVideo

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
