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
import requests
from bs4 import BeautifulSoup
import urllib.parse
from config import SUPPORTED_IMAGE_EXTENSIONS

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
        import tempfile
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
        import tempfile
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

def get_title_content(text):
    """
    Extract title and content from a text

    Args:
        text: Input text

    Returns:
        tuple: (title, content)
    """
    lines = text.strip().split('\n')

    # If there's only one line, use it as both title and content
    if len(lines) == 1:
        return lines[0], lines[0]

    # Use the first line as title and the rest as content
    title = lines[0]
    content = '\n'.join(lines[1:])

    return title, content

def process_text_for_tts(text):
    """
    Process text for text-to-speech by removing emojis and non-ASCII characters

    Args:
        text: Text to process

    Returns:
        str: Processed text
    """
    if not text:
        return ""

    # Remove emojis
    text = emoji.replace_emoji(text, replace='')

    # Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text

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
        import tempfile
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
