"""
Helper functions for the Video Generator application
"""
import os
import sys
import platform
import shutil
import subprocess
import tempfile
from config import SUPPORTED_IMAGE_EXTENSIONS

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

def force_moviepy_cleanup():
    """
    Force cleanup of MoviePy resources and file handles
    This helps prevent file locking issues during cleanup
    """
    try:
        import gc
        import time

        # Force garbage collection multiple times to ensure all references are released
        for _ in range(3):
            gc.collect()
            time.sleep(0.1)

        # Try to clear MoviePy's internal caches if available
        try:
            import moviepy.config as mp_config
            # Clear any cached settings that might hold file references
            if hasattr(mp_config, '_FFMPEG_BINARY'):
                mp_config._FFMPEG_BINARY = None
        except (ImportError, AttributeError):
            pass

        # Additional delay to ensure all file handles are released
        time.sleep(0.5)

    except Exception as e:
        # Silent failure - this is a best-effort cleanup
        pass

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

def get_output_directory(user_settings=None):
    """
    Get the safe output directory for video files with proper user settings priority

    Args:
        user_settings: Optional user settings dict to check for custom output folder

    Returns:
        str: Path to output directory
    """
    # Priority 1: Check user settings for custom output folder
    if user_settings:
        custom_folder = user_settings.get('output_folder')
        if custom_folder and custom_folder.strip() and custom_folder != "Default (Auto)":
            if os.path.exists(custom_folder) and os.path.isdir(custom_folder):
                print(f"Using user-specified output folder: {custom_folder}")
                return custom_folder
            else:
                print(f"Warning: User-specified output folder doesn't exist: {custom_folder}")

    # Priority 2: Try to load settings from settings manager if not provided
    if not user_settings:
        try:
            from utils.settings_manager import SettingsManager
            settings_manager = SettingsManager()
            loaded_settings = settings_manager.load_settings()
            custom_folder = loaded_settings.get('output_folder')
            if custom_folder and custom_folder.strip() and custom_folder != "Default (Auto)":
                if os.path.exists(custom_folder) and os.path.isdir(custom_folder):
                    # Reduced logging: print(f"Using settings file output folder: {custom_folder}")
                    return custom_folder
                else:
                    print(f"Warning: Settings file output folder doesn't exist: {custom_folder}")
        except Exception as e:
            print(f"Could not load user settings: {e}")

    # Priority 3: Check if the output directory was set by main.py (environment variable)
    output_dir = os.environ.get('VIDEO_GENERATOR_OUTPUT_DIR')
    if output_dir and os.path.exists(output_dir):
        print(f"Using environment-specified output folder: {output_dir}")
        return output_dir

    # Priority 4: Fallback to app data directory
    app_data_dir = get_app_data_dir()
    output_dir = os.path.join(app_data_dir, "output")
    print(f"Using default app data output folder: {output_dir}")

    # Ensure it exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create output directory {output_dir}: {e}")
        # Last resort - use temp directory
        output_dir = os.path.join(tempfile.gettempdir(), "Video Generator", "output")
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"Using temporary output folder: {output_dir}")
        except Exception:
            output_dir = tempfile.gettempdir()
            print(f"Using system temp folder: {output_dir}")

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

# Removed unused utility functions (72 lines saved):
# - get_platform_info(): Not used anywhere in the project
# - print_exception(): Redundant with error_helpers.py functionality
# - test_subtitle_functionality(): Development function not used in production

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

def build_ffmpeg_command(ffmpeg_path, input_file, output_file, command_type="basic", **kwargs):
    """
    Centralized FFmpeg command builder to eliminate duplicate command construction

    Args:
        ffmpeg_path: Path to FFmpeg executable
        input_file: Input file path
        output_file: Output file path
        command_type: Type of command ("basic", "subtitle", "optimization", "compatibility", "audio_mix", "loop")
        **kwargs: Additional parameters specific to command type

    Returns:
        list: FFmpeg command as list of arguments
    """
    base_cmd = [ffmpeg_path, '-y', '-i', input_file]

    if command_type == "subtitle":
        subtitle_file = kwargs.get('subtitle_file', '')
        subtitle_filename = os.path.basename(subtitle_file)
        return base_cmd + [
            '-vf', f'subtitles={subtitle_filename}',
            '-c:v', 'libx264', '-profile:v', 'baseline', '-level', '3.0',
            '-crf', '23', '-preset', 'medium', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-ac', '2',
            '-movflags', '+faststart', '-f', 'mp4',
            output_file
        ]

    elif command_type == "optimization":
        preset = kwargs.get('preset', 'medium')
        vf_arg = kwargs.get('vf_arg', 'scale=1280:720')
        return base_cmd + [
            '-vf', vf_arg,
            '-af', 'loudnorm',
            '-c:v', 'libx264', '-preset', preset, '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            output_file
        ]

    elif command_type == "compatibility":
        return base_cmd + [
            '-c:v', 'libx264', '-profile:v', 'baseline', '-level', '3.0',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '44100', '-ac', '2',
            '-movflags', '+faststart', '-avoid_negative_ts', 'make_zero',
            output_file
        ]

    elif command_type == "audio_mix":
        audio_file = kwargs.get('audio_file', '')
        target_duration = kwargs.get('target_duration', None)
        cmd = base_cmd + ['-i', audio_file, '-c:v', 'copy', '-c:a', 'aac',
                         '-map', '0:v:0', '-map', '1:a:0', '-avoid_negative_ts', 'make_zero']
        if target_duration:
            cmd.extend(['-t', str(target_duration)])
        cmd.append(output_file)
        return cmd

    elif command_type == "loop":
        loops = kwargs.get('loops', 1)
        target_duration = kwargs.get('target_duration', None)
        cmd = base_cmd[:-2] + [  # Remove -i input_file, add stream_loop
            '-stream_loop', str(loops - 1), '-i', input_file,
            '-c', 'copy', '-avoid_negative_ts', 'make_zero'
        ]
        if target_duration:
            cmd.extend(['-t', str(target_duration)])
        cmd.append(output_file)
        return cmd

    else:  # basic
        return base_cmd + ['-c', 'copy', output_file]

def create_temp_file_with_cleanup(suffix='', prefix='temp_', directory=None):
    """
    Create a temporary file with automatic cleanup tracking

    Args:
        suffix: File suffix/extension
        prefix: File prefix
        directory: Directory to create file in (None for system temp)

    Returns:
        str: Path to temporary file
    """
    import time
    timestamp = str(int(time.time() * 1000))

    if directory is None:
        directory = tempfile.gettempdir()

    temp_filename = f"{prefix}{timestamp}{suffix}"
    temp_path = os.path.join(directory, temp_filename)

    return temp_path

def execute_ffmpeg_command(cmd, operation_name="FFmpeg operation", timeout=None, video_duration=None):
    """
    Execute FFmpeg command with standardized error handling and dynamic timeout

    Args:
        cmd: FFmpeg command list
        operation_name: Name of operation for logging
        timeout: Timeout in seconds (None for dynamic calculation)
        video_duration: Video duration for dynamic timeout calculation

    Returns:
        tuple: (success: bool, result: subprocess.CompletedProcess, error_message: str)
    """
    try:
        # Calculate dynamic timeout if not provided
        if timeout is None and video_duration:
            # Base timeout of 60s + 30s per minute of video + 120s buffer
            timeout = max(180, int(60 + (video_duration / 60) * 30 + 120))
        elif timeout is None:
            timeout = 300  # Default 5 minutes

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        if result.returncode == 0:
            return True, result, None
        else:
            error_msg = f"{operation_name} failed: {result.stderr}"
            return False, result, error_msg

    except subprocess.TimeoutExpired:
        error_msg = f"{operation_name} timed out after {timeout} seconds"
        return False, None, error_msg
    except Exception as e:
        error_msg = f"{operation_name} error: {str(e)}"
        return False, None, error_msg

def validate_loop_count(loops_needed, max_loops, operation_name="operation"):
    """
    Validate loop count to prevent excessive resource usage

    Args:
        loops_needed: Number of loops requested
        max_loops: Maximum allowed loops
        operation_name: Name of operation for error messages

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if loops_needed > max_loops:
        error_msg = f"Error: Too many loops needed ({loops_needed}) for {operation_name}, maximum is {max_loops}"
        return False, error_msg
    return True, None

def validate_ffmpeg_path(ffmpeg_path):
    """
    Validate FFmpeg path using cross-platform detection

    Args:
        ffmpeg_path: Path to FFmpeg executable

    Returns:
        tuple: (is_valid: bool, resolved_path: str, error_message: str or None)
    """
    try:
        # Use shutil.which for better cross-platform detection
        if ffmpeg_path == 'ffmpeg':
            resolved_path = shutil.which('ffmpeg')
            if resolved_path:
                return True, resolved_path, None
            else:
                return False, ffmpeg_path, "FFmpeg not found in system PATH"
        elif os.path.exists(ffmpeg_path):
            return True, ffmpeg_path, None
        else:
            # Try to find it using shutil.which as fallback
            resolved_path = shutil.which(ffmpeg_path)
            if resolved_path:
                return True, resolved_path, None
            else:
                return False, ffmpeg_path, f"FFmpeg executable not found: {ffmpeg_path}"
    except Exception as e:
        return False, ffmpeg_path, f"Error validating FFmpeg path: {str(e)}"

class TempVideoFile:
    """
    Context manager for temporary video files with automatic cleanup
    Ensures files are cleaned up even if exceptions occur
    """
    def __init__(self, suffix='.mp4', prefix='temp_video_', directory=None):
        self.suffix = suffix
        self.prefix = prefix
        self.directory = directory
        self.temp_path = None

    def __enter__(self):
        self.temp_path = create_temp_file_with_cleanup(
            suffix=self.suffix,
            prefix=self.prefix,
            directory=self.directory
        )
        return self.temp_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_path:
            cleanup_temp_files(self.temp_path)

def log_message(message, level="INFO", logger_func=None):
    """
    Centralized logging function that works with project's logging system

    Args:
        message: Message to log
        level: Log level (INFO, WARNING, ERROR)
        logger_func: Optional logger function (e.g., main_gui.log)
    """
    formatted_message = f"{level}: {message}" if level != "INFO" else message

    if logger_func and callable(logger_func):
        logger_func(formatted_message)
    else:
        print(formatted_message)
