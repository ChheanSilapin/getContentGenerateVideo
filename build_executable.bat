@echo off
echo Building Video Generator executable with Vosk support...
echo.

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "VideoGenerator_1.0.5.spec" del "VideoGenerator_1.0.5.spec"

echo Cleaned previous builds
echo.

REM Build with PyInstaller using the spec file
pyinstaller VideoGenerator_1.0.5.spec

echo.
if exist "dist\VideoGenerator_1.0.5.exe" (
    echo ✅ Build completed successfully!
    echo Executable location: dist\VideoGenerator_1.0.5.exe
    echo.
    echo Testing the executable...
    echo.
    REM Test the executable briefly
    timeout /t 2 /nobreak >nul
    echo You can now run: dist\VideoGenerator_1.0.5.exe
) else (
    echo ❌ Build failed! Check the output above for errors.
    echo.
    echo Common issues:
    echo - Missing dependencies
    echo - Vosk DLL files not found
    echo - FFmpeg binaries not found
)

echo.
pause
