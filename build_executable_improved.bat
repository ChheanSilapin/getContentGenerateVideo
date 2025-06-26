@echo off
echo ========================================
echo Building VideoGenerator with PyInstaller
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo FAILED to install PyInstaller. Please install manually.
        pause
        exit /b 1
    )
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist\VideoGenerator_1.0.6.exe" del "dist\VideoGenerator_1.0.6.exe"

echo.
echo Starting PyInstaller build...
echo.

pyinstaller --onefile ^
--hidden-import=ui.video_tab ^
--hidden-import=ui.gui ^
--hidden-import=ui.input_tab ^
--hidden-import=ui.image_tab ^
--hidden-import=ui.batch_tab ^
--hidden-import=ui.merge_video_tab ^
--hidden-import=ui.option_tab ^
--hidden-import=ui.image_selector ^
--hidden-import=ui.text_redirector ^
--hidden-import=ui.components ^
--hidden-import=ui.components.settings_popup ^
--hidden-import=ui.components.button_factory ^
--hidden-import=ui.components.audio_settings ^
--hidden-import=ui.components.video_entry ^
--hidden-import=ui.components.layout_factory ^
--hidden-import=ui.components.video_loader ^
--hidden-import=ui.components.progress_manager ^
--hidden-import=ui.components.video_grid ^
--hidden-import=ui.components.dropdown_menu ^
--hidden-import=ui.components.group_entry ^
--hidden-import=ui.components.image_entry ^
--hidden-import=models ^
--hidden-import=models.video_generator ^
--hidden-import=models.video_generator_refactored ^
--hidden-import=models.video_processor ^
--hidden-import=models.batch_processor ^
--hidden-import=models.cleanup_manager ^
--hidden-import=services ^
--hidden-import=services.video_service ^
--hidden-import=services.audio_service ^
--hidden-import=services.subtitle_service ^
--hidden-import=services.merge_service ^
--hidden-import=services.video_optimization ^
--hidden-import=services.video_finalization ^
--hidden-import=services.speech_recognition_core ^
--hidden-import=services.speech_recognition_models ^
--hidden-import=services.content_analysis ^

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
--hidden-import=utils ^
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
--hidden-import=utils.migration_helper ^
--hidden-import=utils.output_manager ^
--hidden-import=utils.text_processing ^
--hidden-import=moviepy.editor ^
--hidden-import=moviepy.config ^
--hidden-import=moviepy.video.io.VideoFileClip ^
--hidden-import=moviepy.audio.io.AudioFileClip ^
--hidden-import=moviepy.video.fx.resize ^
--hidden-import=moviepy.video.fx.fadein ^
--hidden-import=moviepy.video.fx.fadeout ^
--hidden-import=moviepy.video.fx.loop ^
--hidden-import=moviepy.video.compositing.CompositeVideoClip ^
--hidden-import=moviepy.video.compositing.concatenate_videoclips ^
--hidden-import=moviepy.audio.fx.volumex ^
--hidden-import=PIL ^
--hidden-import=PIL.Image ^
--hidden-import=PIL.ImageDraw ^
--hidden-import=PIL.ImageFont ^
--hidden-import=PIL.ImageEnhance ^
--hidden-import=PIL.ImageFilter ^
--hidden-import=vosk ^
--hidden-import=vosk_cffi ^
--hidden-import=_cffi_backend ^
--hidden-import=gtts ^
--hidden-import=gtts.lang ^
--hidden-import=gtts.tts ^
--hidden-import=json ^
--hidden-import=requests ^
--hidden-import=requests.adapters ^
--hidden-import=requests.sessions ^
--hidden-import=urllib3 ^
--hidden-import=urllib3.poolmanager ^
--hidden-import=certifi ^
--hidden-import=charset_normalizer ^
--hidden-import=idna ^
--hidden-import=numpy ^
--hidden-import=numpy.core ^
--hidden-import=scipy ^
--hidden-import=scipy.io ^
--hidden-import=cv2 ^
--hidden-import=pydub ^
--hidden-import=pydub.AudioSegment ^
--hidden-import=pydub.effects ^
--hidden-import=difflib ^
--hidden-import=re ^
--hidden-import=threading ^
--hidden-import=queue ^
--hidden-import=tkinter ^
--hidden-import=tkinter.ttk ^
--hidden-import=tkinter.filedialog ^
--hidden-import=tkinter.messagebox ^
--hidden-import=tkinter.font ^
--hidden-import=tkinter.simpledialog ^
--hidden-import=tkinter.scrolledtext ^
--hidden-import=pyaudio ^
--hidden-import=emoji ^
--hidden-import=bs4 ^
--hidden-import=beautifulsoup4 ^
--hidden-import=hashlib ^
--hidden-import=tempfile ^
--hidden-import=shutil ^
--hidden-import=glob ^
--hidden-import=platform ^
--hidden-import=datetime ^
--hidden-import=time ^
--hidden-import=subprocess ^
--hidden-import=sys ^
--hidden-import=os ^
--hidden-import=pathlib ^
--hidden-import=typing ^
--hidden-import=dataclasses ^
--hidden-import=abc ^
--hidden-import=functools ^
--hidden-import=itertools ^
--hidden-import=collections ^
--hidden-import=warnings ^
--hidden-import=traceback ^
--hidden-import=logging ^
--hidden-import=configparser ^
--hidden-import=io ^
--hidden-import=base64 ^
--hidden-import=uuid ^
--hidden-import=random ^
--hidden-import=math ^
--hidden-import=copy ^
--hidden-import=pickle ^
--hidden-import=gzip ^
--hidden-import=zipfile ^
--hidden-import=tarfile ^
--hidden-import=wave ^
--hidden-import=audioop ^
--collect-data moviepy ^
--collect-data vosk ^
--collect-data gtts ^
--collect-data certifi ^
--collect-data PIL ^
--collect-data cv2 ^
--collect-data pydub ^
--collect-data emoji ^
--collect-data numpy ^
--collect-data scipy ^
--add-data="config.py;." ^
--add-data="version.py;." ^
--add-data="utils;utils" ^
--add-data="models;models" ^
--add-data="models/vosk-model-small-en-us-0.15;models/vosk-model-small-en-us-0.15" ^
--add-data="services;services" ^
--add-data="ui;ui" ^
--add-data="fonts;fonts" ^
--add-data="user_settings.json;." ^
--add-binary="ffmpeg.exe;." ^
--add-binary="ffplay.exe;." ^
--add-binary="ffprobe.exe;." ^
--exclude-module=matplotlib ^
--exclude-module=pytest ^
--exclude-module=setuptools ^
--exclude-module=pip ^
--exclude-module=PySide6 ^
--exclude-module=PyQt5 ^
--exclude-module=PyQt6 ^
--exclude-module=IPython ^
--exclude-module=jupyter ^
--exclude-module=notebook ^
--exclude-module=sphinx ^
--exclude-module=docutils ^
--exclude-module=wheel ^
--exclude-module=distutils ^
--paths="hooks" ^
--runtime-tmpdir="." ^
--name="VideoGenerator_1.0.6" ^
--icon="app_icon.ico" ^
--clean ^
--noconfirm ^
--log-level=INFO ^
main.py

echo.
if exist "dist\VideoGenerator_1.0.6.exe" (
    echo ========================================
    echo BUILD SUCCESSFUL!
    echo ========================================
    echo Executable created: dist\VideoGenerator_1.0.6.exe
    echo File size:
    dir "dist\VideoGenerator_1.0.6.exe" | find "VideoGenerator_1.0.6.exe"
    echo.
    echo Testing executable...
    "dist\VideoGenerator_1.0.6.exe" --console
    echo.
    echo Build completed successfully!
) else (
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    echo Check the output above for errors.
    echo Common issues:
    echo - Missing dependencies
    echo - Import errors
    echo - File permission issues
)

echo.
pause
