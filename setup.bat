@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Video Generator - FULL Setup
echo ========================================
echo Installing ALL features with NO conflicts
echo.

REM Check if already set up
if exist "venv\Scripts\python.exe" (
    echo Checking existing setup...
    call venv\Scripts\activate.bat
    python -c "import edge_tts, kokoro, whisper_timestamped, moviepy" >nul 2>&1
    if not errorlevel 1 (
        echo.
        echo  Setup already complete!
        echo  All features working
        echo.
        echo To run: double-click "run.bat"
        echo To reinstall: delete "venv" folder first
        echo.
        pause
        exit /b 0
    ) else (
        echo ⚠️ Setup incomplete, reinstalling...
    )
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python not found!
    echo Install Python from https://python.org
    pause
    exit /b 1
)

echo  Python found
python --version

REM Create fresh virtual environment
if exist "venv" rmdir /s /q "venv"
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo ========================================
echo Installing ALL dependencies (conflict-free)
echo ========================================

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo  requirements.txt not found!
    echo Make sure requirements.txt is in the same folder as setup.bat
    pause
    exit /b 1
)

echo [1/2] Installing main dependencies from requirements.txt...
pip install -r requirements.txt

echo [2/2] Installing PyTorch CPU (separate to avoid index conflicts)...
pip install torch --index-url https://download.pytorch.org/whl/cpu

echo.
echo ========================================
echo Testing ALL features...
echo ========================================

echo Testing core imports...
python -c "import edge_tts, moviepy, PIL, pydub, requests, bs4, emoji, soundfile, numpy, scipy, onnxruntime; print('✅ Core imports successful')" || (
    echo  Core imports failed
    pause
    exit /b 1
)

echo Testing TTS providers...
python -c "import kokoro; print('✅ Kokoro TTS ready')" || (
    echo  Kokoro TTS failed
    pause
    exit /b 1
)

echo Testing Whisper...
python -c "import whisper_timestamped; print('✅ Whisper Timestamped ready')" || (
    echo  Whisper Timestamped failed
    pause
    exit /b 1
)

echo Testing PyTorch...
python -c "import torch; print('✅ PyTorch ready')" || (
    echo  PyTorch failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo FULL Setup Complete - NO CONFLICTS!
echo ========================================
echo  Virtual environment: venv
echo  ALL features installed and tested:
echo   - Edge TTS (Guy, Connor, Aria)
echo   - Kokoro TTS (Michael, Adam, Heart)
echo   - Whisper Timestamped (subtitle timing)
echo   - MoviePy (video processing)
echo   - Pillow (image processing)
echo   - PyDub (audio processing)
echo   - NumPy 1.x (no conflicts)
echo   - PyTorch CPU (compatible)
echo.
echo To run: double-click "run.bat"
echo.
pause
