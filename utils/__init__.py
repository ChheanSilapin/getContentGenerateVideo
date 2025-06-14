"""
Utils package for Video Generator
Provides centralized utilities and helper functions
"""

# Import commonly used functions for easy access
import os


try:
    from .helpers import (
        get_app_data_dir, ensure_directory_exists, get_ffmpeg_path, get_ffprobe_path,
        check_ffmpeg_availability, get_title_content, process_text_for_tts,
        configure_ffmpeg_for_moviepy, setup_temp_directory_for_bundled_exe,
        validate_output_file, safe_file_operation, cleanup_temp_files, get_media_duration_safe
    )
    from .path_manager import setup_project_paths, get_base_path, add_utils_to_path
    from .fallback_manager import get_helpers_with_fallback, with_fallback
    from .dialog_helpers import (
        select_image_files, select_video_files, select_folder,
        save_video_file, save_file_generic
    )
    from .error_helpers import (
        show_error_with_log, show_warning_with_log, show_info_with_log,
        handle_operation_error, safe_operation, confirm_action
    )
except ImportError as e:
    print(f"Warning: Could not import some utils modules: {e}")

def initialize_service():
    """
    Initialize service module with proper path setup and imports
    This function should be called at the beginning of each service module
    
    Returns:
        dict: Dictionary with common utility functions
    """
    # Set up project paths
    try:
        setup_project_paths()
    except Exception as e:
        print(f"Warning: Could not set up project paths: {e}")
    
    # Return common utility functions
    try:
        return {
            'get_ffmpeg_path': get_ffmpeg_path,
            'get_ffprobe_path': get_ffprobe_path,
            'check_ffmpeg_availability': check_ffmpeg_availability,
            'ensure_directory_exists': ensure_directory_exists,
            'get_app_data_dir': get_app_data_dir
        }
    except Exception as e:
        print(f"Warning: Could not initialize service utilities: {e}")
        # Use fallback manager
        try:
            helpers = get_helpers_with_fallback()
            return {
                'get_ffmpeg_path': helpers.get_ffmpeg_path,
                'get_ffprobe_path': lambda: 'ffprobe',  # Simple fallback
                'check_ffmpeg_availability': helpers.check_ffmpeg_availability,
                'ensure_directory_exists': helpers.ensure_directory_exists,
                'get_app_data_dir': helpers.get_app_data_dir
            }
        except Exception:
            # Last resort fallbacks
            return {
                'get_ffmpeg_path': lambda: 'ffmpeg',
                'get_ffprobe_path': lambda: 'ffprobe',
                'check_ffmpeg_availability': lambda: (False, 'ffmpeg', 'Initialization failed'),
                'ensure_directory_exists': lambda path: False,
                'get_app_data_dir': lambda: os.getcwd()
            }

__all__ = [
    # Core helpers
    'get_app_data_dir', 'ensure_directory_exists', 'get_ffmpeg_path', 'get_ffprobe_path',
    'check_ffmpeg_availability', 'get_title_content', 'process_text_for_tts',
    'setup_project_paths', 'get_base_path', 'add_utils_to_path',
    'get_helpers_with_fallback', 'with_fallback', 'initialize_service',
    'configure_ffmpeg_for_moviepy', 'setup_temp_directory_for_bundled_exe',
    'validate_output_file', 'safe_file_operation', 'cleanup_temp_files', 'get_media_duration_safe',
    # Dialog helpers
    'select_image_files', 'select_video_files', 'select_folder',
    'save_video_file', 'save_file_generic',
    # Error helpers
    'show_error_with_log', 'show_warning_with_log', 'show_info_with_log',
    'handle_operation_error', 'safe_operation', 'confirm_action'
]