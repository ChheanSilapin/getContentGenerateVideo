@echo off
echo Building Video Generator with Clean Environment...
echo.

REM Check if virtual environment exists
if not exist "video_generator_env" (
    echo Creating virtual environment...
    "C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe" -m venv video_generator_env
    echo.
    
    echo Installing dependencies...
    "video_generator_env\Scripts\pip.exe" install -r requirements.txt
    "video_generator_env\Scripts\pip.exe" install pyinstaller
    echo.
)

echo Building executable...
"video_generator_env\Scripts\pyinstaller.exe" video_generator.spec --clean

echo.
if exist "dist\Video Generator.exe" (
    echo ✓ Build completed successfully!
    echo Executable location: dist\Video Generator.exe
    echo File size: 
    dir "dist\Video Generator.exe" | findstr "Video Generator.exe"
) else (
    echo ✗ Build failed!
)

echo.
pause
