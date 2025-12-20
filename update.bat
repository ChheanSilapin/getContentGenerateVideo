@echo off
echo ========================================
echo    Video Generator - Update
echo ========================================
echo.

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
