@echo off
echo ========================================
echo    Video Generator - Update
echo ========================================
echo.

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

:: Ensure pip is available (required by Kokoro TTS)
uv pip install pip >nul 2>&1

echo.
echo ========================================
echo    Update Complete!
echo    Run 'run.bat' to start the app
echo ========================================
pause
