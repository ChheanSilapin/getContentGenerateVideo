"""
Helper functions for the Video Generator application
"""
import os
import sys
import platform
import re
import emoji
import shutil
import traceback
import subprocess
import tempfile
import requests
from bs4 import BeautifulSoup
import urllib.parse
from config import SUPPORTED_IMAGE_EXTENSIONS

# Import text processing functions from centralized module
from utils.text_processing import get_title_content, process_text_for_tts

# ===== NEW CENTRALIZED UTILITY FUNCTIONS =====

def configure_ffmpeg_for_moviepy():
    """
    Centralized FFmpeg configuration for MoviePy
    Eliminates duplicate FFmpeg setup code across services

    Returns:
        bool: True if FFmpeg was configured successfully
    """
    try:
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path and (ffmpeg_path == 'ffmpeg' or os.path.exists(ffmpeg_path)):
            # Set environment variable first (always works)
            os.environ['FFMPEG_BINARY'] = ffmpeg_path
            os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_path

            # Try to configure MoviePy directly
            try:
                from moviepy.config import change_settings
                change_settings({"FFMPEG_BINARY": ffmpeg_path})
                print(f"FFmpeg configured for MoviePy: {ffmpeg_path}")
                return True
            except ImportError:
                print(f"FFmpeg configured via environment variables: {ffmpeg_path}")
                return True
        else:
            print(f"Warning: FFmpeg path not found or invalid: {ffmpeg_path}")
            return False
    except Exception as e:
        print(f"Warning: Could not configure FFmpeg: {e}")
        return False

def setup_temp_directory_for_bundled_exe(output_file_path):
    """
    Centralized temp directory setup for bundled executables
    Eliminates duplicate temp directory code across services

    Args:
        output_file_path: Path to output file (used to determine temp location)

    Returns:
        str: Path to temp directory
    """
    if getattr(sys, 'frozen', False):
        # Running as bundled executable
        temp_dir = os.path.join(os.path.dirname(output_file_path), 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Set environment variables for various temp directory uses
        os.environ['TMPDIR'] = temp_dir
        os.environ['TEMP'] = temp_dir
        os.environ['TMP'] = temp_dir

        print(f"Temp directory configured for bundled executable: {temp_dir}")
        return temp_dir
    else:
        return tempfile.gettempdir()

def validate_output_file(file_path, min_size_bytes=1024, file_type="output"):
    """
    Centralized file validation
    Eliminates duplicate file validation code across services

    Args:
        file_path: Path to file to validate
        min_size_bytes: Minimum file size in bytes (default: 1KB)
        file_type: Type of file for logging (e.g., "video", "audio")

    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not os.path.exists(file_path):
        return False, f"{file_type} file not found: {file_path}"

    file_size = os.path.getsize(file_path)
    if file_size < min_size_bytes:
        return False, f"{file_type} file too small ({file_size} bytes), likely corrupted"

    return True, f"{file_type} file valid ({file_size} bytes)"

def safe_file_operation(operation_func, *args, operation_name="file operation", **kwargs):
    """
    Centralized safe file operation wrapper
    Eliminates duplicate try-catch patterns across services

    Args:
        operation_func: Function to execute safely
        *args: Arguments for the function
        operation_name: Name of operation for logging
        **kwargs: Keyword arguments for the function

    Returns:
        tuple: (success: bool, result: any, error_message: str)
    """
    try:
        result = operation_func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        error_msg = f"Error in {operation_name}: {str(e)}"
        print(error_msg)
        return False, None, error_msg

def cleanup_temp_files(*file_paths):
    """
    Centralized temp file cleanup
    Eliminates duplicate cleanup code across services

    Args:
        *file_paths: Variable number of file paths to clean up
    """
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Cleaned up temp file: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Warning: Could not remove temp file {file_path}: {e}")

def get_media_duration_safe(media_file):
    """
    Centralized media duration detection with fallbacks
    Eliminates duplicate duration detection code across services

    Args:
        media_file: Path to media file

    Returns:
        float: Duration in seconds, or 0.0 if failed
    """
    try:
        # Try using moviepy first
        from moviepy.editor import VideoFileClip, AudioFileClip

        # Determine if it's video or audio
        ext = os.path.splitext(media_file)[1].lower()
        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            with VideoFileClip(media_file) as clip:
                duration = clip.duration
        else:
            with AudioFileClip(media_file) as clip:
                duration = clip.duration

        print(f"Media duration: {duration:.2f} seconds")
        return duration
    except Exception as e:
        print(f"Failed to get media duration with moviepy: {e}")

        # Fallback: try FFprobe
        try:
            ffprobe_path = get_ffprobe_path()
            cmd = [
                ffprobe_path,
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                media_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                print(f"Media duration (ffprobe): {duration:.2f} seconds")
                return duration
        except Exception as e2:
            print(f"Failed to get media duration with ffprobe: {e2}")

        # Final fallback
        print("Using default media duration: 10.0 seconds")
        return 10.0

def get_app_data_dir():
    """
    Get the application data directory where we can safely write files

    Returns:
        str: Path to writable application data directory
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        if platform.system() == "Windows":
            # Try AppData\Local first (more appropriate for app data)
            try:
                appdata_local = os.environ.get('LOCALAPPDATA')
                if appdata_local:
                    app_data_dir = os.path.join(appdata_local, "Video Generator")
                    os.makedirs(app_data_dir, exist_ok=True)
                    # Test write permissions
                    test_file = os.path.join(app_data_dir, "test_write.tmp")
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    return app_data_dir
            except Exception as e:
                print(f"Could not use AppData\\Local: {e}")

            # Fallback to Documents folder
            try:
                documents_path = os.path.join(os.path.expanduser("~"), "Documents")
                app_data_dir = os.path.join(documents_path, "Video Generator")
                os.makedirs(app_data_dir, exist_ok=True)
                # Test write permissions
                test_file = os.path.join(app_data_dir, "test_write.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                return app_data_dir
            except Exception as e:
                print(f"Could not use Documents folder: {e}")
        else:
            # Use home directory on other systems
            app_data_dir = os.path.join(os.path.expanduser("~"), ".video_generator")
    else:
        # Running as script - use current directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_data_dir = os.path.dirname(script_dir)  # Go up one level from utils/

    # Ensure the directory exists
    try:
        os.makedirs(app_data_dir, exist_ok=True)
        # Test write permissions
        test_file = os.path.join(app_data_dir, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        print(f"Warning: Could not create app data directory {app_data_dir}: {e}")
        # Fallback to temp directory
        app_data_dir = os.path.join(tempfile.gettempdir(), "Video Generator")
        try:
            os.makedirs(app_data_dir, exist_ok=True)
        except Exception as e2:
            print(f"Error: Could not create temp directory {app_data_dir}: {e2}")
            # Last resort - use current directory
            app_data_dir = os.getcwd()

    return app_data_dir

def get_output_directory():
    """
    Get the safe output directory for video files

    Returns:
        str: Path to output directory
    """
    # Check if the output directory was set by main.py
    output_dir = os.environ.get('VIDEO_GENERATOR_OUTPUT_DIR')
    if output_dir and os.path.exists(output_dir):
        return output_dir

    # Fallback to app data directory
    app_data_dir = get_app_data_dir()
    output_dir = os.path.join(app_data_dir, "output")

    # Ensure it exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create output directory {output_dir}: {e}")
        # Last resort - use temp directory
        output_dir = os.path.join(tempfile.gettempdir(), "Video Generator", "output")
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            output_dir = tempfile.gettempdir()

    return output_dir

def check_ffmpeg_availability():
    """
    Check if FFmpeg is available and working

    Returns:
        tuple: (is_available: bool, ffmpeg_path: str, error_message: str)
    """
    ffmpeg_path = get_ffmpeg_path()

    try:
        # Try to run ffmpeg -version to check if it's working
        result = subprocess.run([ffmpeg_path, '-version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, ffmpeg_path, None
        else:
            return False, ffmpeg_path, f"FFmpeg returned error code {result.returncode}"
    except FileNotFoundError:
        return False, ffmpeg_path, "FFmpeg executable not found"
    except subprocess.TimeoutExpired:
        return False, ffmpeg_path, "FFmpeg check timed out"
    except Exception as e:
        return False, ffmpeg_path, f"Error checking FFmpeg: {str(e)}"

def get_ffmpeg_path():
    """
    Get the path to FFmpeg executable, prioritizing bundled version

    Returns:
        str: Path to FFmpeg executable
    """
    # Check if running as PyInstaller executable
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller extracts files to sys._MEIPASS
            bundled_ffmpeg = os.path.join(sys._MEIPASS, 'ffmpeg.exe')
            if os.path.exists(bundled_ffmpeg):
                return bundled_ffmpeg

        # Fallback: check in executable directory
        exe_dir = os.path.dirname(sys.executable)
        exe_dir_ffmpeg = os.path.join(exe_dir, 'ffmpeg.exe')
        if os.path.exists(exe_dir_ffmpeg):
            return exe_dir_ffmpeg

    # Check in current script directory (for development)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level from utils/
    local_ffmpeg = os.path.join(project_root, 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg

    # Fallback to system PATH
    return 'ffmpeg'

def get_ffprobe_path():
    """
    Get the path to FFprobe executable, prioritizing bundled version

    Returns:
        str: Path to FFprobe executable
    """
    # Check if running as PyInstaller executable
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller extracts files to sys._MEIPASS
            bundled_ffprobe = os.path.join(sys._MEIPASS, 'ffprobe.exe')
            if os.path.exists(bundled_ffprobe):
                return bundled_ffprobe

        # Fallback: check in executable directory
        exe_dir = os.path.dirname(sys.executable)
        exe_dir_ffprobe = os.path.join(exe_dir, 'ffprobe.exe')
        if os.path.exists(exe_dir_ffprobe):
            return exe_dir_ffprobe

    # Check in current script directory (for development)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level from utils/
    local_ffprobe = os.path.join(project_root, 'ffprobe.exe')
    if os.path.exists(local_ffprobe):
        return local_ffprobe

    # Fallback to system PATH
    return 'ffprobe'

def get_file_extension(file_path):
    """
    Get the extension of a file

    Args:
        file_path: Path to file

    Returns:
        str: File extension (with dot)
    """
    return os.path.splitext(file_path)[1].lower()

def is_image_file(file_path):
    """
    Check if a file is an image based on its extension

    Args:
        file_path: Path to file

    Returns:
        bool: True if a file is an image, False otherwise
    """
    return get_file_extension(file_path) in SUPPORTED_IMAGE_EXTENSIONS

def copy_file(source, destination):
    """
    Copy a file from source to destination

    Args:
        source: Source file path
        destination: Destination file path

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create destination directory if it doesn't exist
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)

        # Copy the file
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(f"Error copying file from {source} to {destination}: {e}")
        return False

def get_platform_info():
    """
    Get information about the current platform

    Returns:
        dict: Platform information
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }

def print_exception(e, message="An error occurred"):
    """
    Print exception details with a custom message

    Args:
        e: Exception object
        message: Custom message to print before the exception
    """
    print(f"{message}: {str(e)}")
    traceback.print_exc()

def test_subtitle_functionality():
    """
    Test the subtitle functionality to ensure it's working correctly

    Returns:
        bool: True if subtitles are working, False otherwise
    """
    try:
        print("Testing subtitle functionality...")

        # Check if FFmpeg is available
        ffmpeg_available, ffmpeg_path, error_msg = check_ffmpeg_availability()
        if not ffmpeg_available:
            print(f"FFmpeg not available: {error_msg}")
            return False

        print(f"FFmpeg available at: {ffmpeg_path}")

        # Test subtitle file creation
        with tempfile.NamedTemporaryFile(suffix='.ass', delete=False) as temp_sub:
            temp_subtitle_path = temp_sub.name

        # Create a simple test subtitle
        try:
            with open(temp_subtitle_path, 'w', encoding='utf-8') as f:
                f.write("[Script Info]\nTitle: Test Subtitle\nScriptType: v4.00+\n\n")
                f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                f.write("Style: Default,Arial,32,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,80,1\n\n")
                f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                f.write("Dialogue: 0,0:00:00.00,0:00:03.00,Default,,0,0,0,,Test subtitle working!\n")

            print(f"Created test subtitle file: {temp_subtitle_path}")

            # Clean up
            os.remove(temp_subtitle_path)
            print("Subtitle functionality test passed!")
            return True

        except Exception as e:
            print(f"Error creating test subtitle: {e}")
            return False

    except Exception as e:
        print(f"Error testing subtitle functionality: {e}")
        return False

def ensure_directory_exists(directory_path):
    """
    Create a directory if it doesn't exist

    Args:
        directory_path: Path to directory

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            print(f"Created directory: {directory_path}")
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False
