"""
Utils package for Video Generator
Provides centralized utilities and helper functions
"""

# Import commonly used functions for easy access
try:
    from .helpers import (
        get_app_data_dir, ensure_directory_exists, get_ffmpeg_path, 
        check_ffmpeg_availability, get_title_content, process_text_for_tts
    )
    from .path_manager import setup_project_paths, get_base_path, add_utils_to_path
    from .fallback_manager import get_helpers_with_fallback, with_fallback
except ImportError as e:
    print(f"Warning: Could not import some utils modules: {e}")

__all__ = [
    'get_app_data_dir', 'ensure_directory_exists', 'get_ffmpeg_path',
    'check_ffmpeg_availability', 'get_title_content', 'process_text_for_tts',
    'setup_project_paths', 'get_base_path', 'add_utils_to_path',
    'get_helpers_with_fallback', 'with_fallback'
]