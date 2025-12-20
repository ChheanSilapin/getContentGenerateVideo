@echo off
echo ========================================
echo    Video Generator - Update
echo ========================================
echo.

:: Enter project folder if we're outside
if exist "getContentGenerateVideo" cd getContentGenerateVideo

:: Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing uv package manager...
    pip install uv
)

echo [INFO] Pulling latest changes from GitHub...
git pull

echo [INFO] Updating dependencies...
uv sync

echo.
echo ========================================
echo    Update Complete!
echo    Run 'run.bat' to start the app
echo ========================================
pause
