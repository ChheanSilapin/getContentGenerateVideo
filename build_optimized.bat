@echo off
echo ========================================
echo VideoGenerator Optimized Build Script
echo ========================================
echo.

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo ERROR: Virtual environment not activated!
    echo Please run: video_generator_env\Scripts\activate
    echo.
    pause
    exit /b 1
)

echo ✅ Virtual environment detected: %VIRTUAL_ENV%
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Check if required packages are installed
echo Checking required packages...
python -c "import moviepy, vosk, gtts, PIL, cv2, numpy, whisper_timestamped; print('✅ All required packages found')" 2>nul
if errorlevel 1 (
    echo ❌ Missing required packages. Installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install requirements
        pause
        exit /b 1
    )
)

REM Check FFmpeg
echo Checking FFmpeg...
if exist "ffmpeg.exe" (
    echo ✅ FFmpeg found: ffmpeg.exe
) else (
    echo ❌ FFmpeg not found! Please ensure ffmpeg.exe is in the project directory
    pause
    exit /b 1
)

REM Check GPU capabilities
echo.
echo Checking GPU capabilities...
python -c "from services.gpu_acceleration import print_gpu_info; print_gpu_info()" 2>nul
if errorlevel 1 (
    echo ⚠️ GPU detection failed, will use CPU encoding
)

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"
echo ✅ Cleaned previous builds

REM Run tests before building
echo.
echo Running quick tests...
python -c "
import sys
import os
sys.path.insert(0, '.')

# Test imports
try:
    from ui.gui import VideoGeneratorGUI
    from models.video_generator_refactored import VideoGeneratorModel
    from services.gpu_acceleration import get_gpu_service
    from config import FFMPEG_OPTIMIZATION, PROCESSING_OPTIMIZATIONS
    print('✅ All core imports successful')
except Exception as e:
    print(f'❌ Import test failed: {e}')
    sys.exit(1)

# Test GPU service
try:
    gpu_service = get_gpu_service()
    print(f'✅ GPU service initialized: {gpu_service.gpu_info[\"type\"]}')
except Exception as e:
    print(f'⚠️ GPU service warning: {e}')

print('✅ All tests passed')
"

if errorlevel 1 (
    echo ❌ Tests failed! Please fix errors before building.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Starting PyInstaller Build...
echo ========================================
echo.

REM Build with PyInstaller
pyinstaller --onefile ^
--hidden-import=ui.video_tab ^
--hidden-import=ui.gui ^
--hidden-import=ui.image_tab ^
--hidden-import=ui.text_redirector ^
--hidden-import=ui.components.video_entry ^
--hidden-import=ui.components.progress_manager ^
--hidden-import=ui.components.dropdown_menu ^
--hidden-import=ui.components.group_entry ^
--hidden-import=ui.components.image_entry ^
--hidden-import=ui.components.settings_popup ^
--hidden-import=models.video_generator_refactored ^
--hidden-import=models.video_processor ^
--hidden-import=models.batch_processor ^
--hidden-import=models.cleanup_manager ^
--hidden-import=services.video_service ^
--hidden-import=services.audio_service ^
--hidden-import=services.subtitle_service ^
--hidden-import=services.merge_service ^
--hidden-import=services.video_optimization ^
--hidden-import=services.video_finalization ^
--hidden-import=services.speech_recognition_core ^
--hidden-import=services.speech_recognition_models ^
--hidden-import=services.content_analysis ^
--hidden-import=services.gpu_acceleration ^
--hidden-import=services.video_slideshow ^
--hidden-import=services.speech_recognition_postprocessor ^
--hidden-import=services.enhanced_speech_recognition ^
--hidden-import=services.image_service ^
--hidden-import=services.video_looping ^
--hidden-import=services.video_utils ^
--hidden-import=services.video_voiceover ^
--hidden-import=services.whisper_service_manager ^
--hidden-import=services.whisper_timestamped_service ^
--hidden-import=services.tts_providers ^
--hidden-import=utils.settings_manager ^
--hidden-import=utils.folder_processor ^
--hidden-import=utils.helpers ^
--hidden-import=utils.path_manager ^
--hidden-import=utils.media_helpers ^
--hidden-import=utils.gui_helpers ^
--hidden-import=utils.logging_utils ^
--hidden-import=utils.common_imports ^
--hidden-import=utils.content_sync ^
--hidden-import=utils.dialog_helpers ^
--hidden-import=utils.error_helpers ^
--hidden-import=utils.fallback_manager ^
--hidden-import=utils.filename_validator ^
--hidden-import=utils.font_manager ^
--hidden-import=utils.output_manager ^
--hidden-import=utils.text_processing ^
--hidden-import=moviepy.editor ^
--hidden-import=moviepy.config ^
--hidden-import=moviepy.video.io.VideoFileClip ^
--hidden-import=moviepy.audio.io.AudioFileClip ^
--hidden-import=moviepy.video.fx.resize ^
--hidden-import=moviepy.video.fx.fadein ^
--hidden-import=moviepy.video.fx.fadeout ^
--hidden-import=PIL.Image ^
--hidden-import=PIL.ImageDraw ^
--hidden-import=PIL.ImageFont ^
--hidden-import=vosk ^
--hidden-import=vosk_cffi ^
--hidden-import=_cffi_backend ^
--hidden-import=gtts ^
--hidden-import=gtts.lang ^
--hidden-import=requests ^
--hidden-import=urllib3 ^
--hidden-import=certifi ^
--hidden-import=numpy ^
--hidden-import=scipy ^
--hidden-import=cv2 ^
--hidden-import=pydub ^
--hidden-import=threading ^
--hidden-import=queue ^
--hidden-import=tkinter ^
--hidden-import=tkinter.ttk ^
--hidden-import=tkinter.filedialog ^
--hidden-import=tkinter.messagebox ^
--hidden-import=tkinter.font ^
--hidden-import=pyaudio ^
--hidden-import=subprocess ^
--collect-data moviepy ^
--collect-data vosk ^
--collect-data gtts ^
--collect-data certifi ^
--collect-data PIL ^
--collect-data cv2 ^
--collect-data pydub ^
--collect-data numpy ^
--collect-data scipy ^
--add-data="config.py;." ^
--add-data="version.py;." ^
--add-data="user_settings.json;." ^
--add-data="utils;utils" ^
--add-data="models;models" ^
--add-data="models/vosk-model-small-en-us-0.15;models/vosk-model-small-en-us-0.15" ^
--add-data="services;services" ^
--add-data="ui;ui" ^
--add-data="fonts;fonts" ^
--add-binary="ffmpeg.exe;." ^
--add-binary="ffplay.exe;." ^
--add-binary="ffprobe.exe;." ^
--exclude-module=matplotlib ^
--exclude-module=pytest ^
--exclude-module=setuptools ^
--exclude-module=pip ^
--exclude-module=wheel ^
--exclude-module=test ^
--exclude-module=tests ^
--exclude-module=unittest ^
--exclude-module=ui.input_tab ^
--exclude-module=ui.batch_tab ^
--exclude-module=ui.merge_video_tab ^
--exclude-module=ui.option_tab ^
--exclude-module=ui.image_selector ^
--exclude-module=ui.components.button_factory ^
--exclude-module=ui.components.audio_settings ^
--exclude-module=ui.components.layout_factory ^
--paths="hooks" ^
--name="VideoGenerator_Optimized_1.0.8" ^
--icon="app_icon.ico" ^
--clean ^
--noconfirm ^
main.py

if errorlevel 1 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.

REM Test the executable
if exist "dist\VideoGenerator_Optimized_1.0.8.exe" (
    echo ✅ Executable created: dist\VideoGenerator_Optimized_1.0.8.exe
    
    REM Get file size
    for %%A in ("dist\VideoGenerator_Optimized_1.0.8.exe") do (
        set size=%%~zA
        set /a sizeMB=!size!/1024/1024
    )
    echo 📊 File size: !sizeMB! MB
    
    echo.
    echo Testing executable startup...
    timeout /t 2 /nobreak >nul
    
    REM Quick startup test (5 second timeout)
    start /wait /b "" "dist\VideoGenerator_Optimized_1.0.8.exe" --test-startup 2>nul
    
    echo.
    echo ========================================
    echo 🎉 BUILD SUCCESSFUL! 🎉
    echo ========================================
    echo.
    echo Executable location: dist\VideoGenerator_Optimized_1.0.8.exe
    echo.
    echo Features included:
    echo ✅ GPU Acceleration (NVIDIA/Intel/AMD)
    echo ✅ Optimized FFmpeg settings
    echo ✅ Parallel processing support
    echo ✅ Enhanced speech recognition
    echo ✅ Hybrid TTS system
    echo ✅ Streamlined UI (Image + Video + Log tabs)
    echo ✅ Automatic cleanup system
    echo.
    echo Ready for distribution!
    echo.
) else (
    echo ❌ Executable not found! Build may have failed.
    echo Check the output above for errors.
)

pause
