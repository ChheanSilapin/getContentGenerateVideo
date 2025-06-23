@echo off
echo Building VideoGenerator with PyInstaller...
echo.

pyinstaller --onefile ^
--hidden-import=ui.video_tab ^
--hidden-import=ui.gui ^
--hidden-import=ui.components.settings_popup ^
--hidden-import=models.video_generator ^
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
--hidden-import=services.emotion_aware_effects ^
--hidden-import=services.video_slideshow ^
--hidden-import=services.speech_recognition_postprocessor ^
--hidden-import=utils.settings_manager ^
--hidden-import=utils.folder_processor ^
--hidden-import=utils.helpers ^
--hidden-import=utils.path_manager ^
--hidden-import=utils.media_helpers ^
--hidden-import=utils.gui_helpers ^
--hidden-import=utils.logging_utils ^
--hidden-import=moviepy.editor ^
--hidden-import=moviepy.config ^
--hidden-import=PIL ^
--hidden-import=PIL.Image ^
--hidden-import=vosk ^
--hidden-import=vosk_cffi ^
--hidden-import=_cffi_backend ^
--hidden-import=gtts ^
--hidden-import=gtts.lang ^
--hidden-import=json ^
--hidden-import=requests ^
--hidden-import=requests.adapters ^
--hidden-import=urllib3 ^
--hidden-import=certifi ^
--hidden-import=charset_normalizer ^
--hidden-import=idna ^
--hidden-import=numpy ^
--hidden-import=scipy ^
--hidden-import=cv2 ^
--hidden-import=pydub ^
--hidden-import=difflib ^
--hidden-import=re ^
--hidden-import=threading ^
--hidden-import=queue ^
--hidden-import=tkinter ^
--hidden-import=tkinter.ttk ^
--hidden-import=tkinter.filedialog ^
--hidden-import=tkinter.messagebox ^
--collect-data moviepy ^
--collect-data vosk ^
--collect-data gtts ^
--collect-data certifi ^
--add-data="config.py;." ^
--add-data="version.py;." ^
--add-data="utils;utils" ^
--add-data="models;models" ^
--add-data="models/vosk-model-small-en-us-0.15;models/vosk-model-small-en-us-0.15" ^
--add-data="services;services" ^
--add-data="ui;ui" ^
--add-binary="ffmpeg.exe;." ^
--add-binary="ffplay.exe;." ^
--add-binary="ffprobe.exe;." ^
--exclude-module=matplotlib ^
--exclude-module=pytest ^
--exclude-module=setuptools ^
--exclude-module=pip ^
--paths="hooks" ^
--name="VideoGenerator_1.0.5" ^
--icon="app_icon.ico" ^
--clean ^
--noconfirm ^
main.py

echo.
echo Build completed! Check the dist folder for VideoGenerator_1.0.5.exe
echo.
pause
