"""
Fallback management utilities for the Video Generator application
Provides centralized fallback functionality for imports and operations
"""
import functools
import traceback
import tempfile
import os
import shutil

# Removed unused decorator and import functions (42 lines saved):
# - with_fallback(): Complex decorator not used in practice
# - safe_import(): Over-engineered import system not utilized

# Standard fallback functions
def fallback_get_app_data_dir():
    """Fallback implementation of get_app_data_dir"""
    try:
        # Try to use the primary implementation first
        from utils.helpers import get_app_data_dir as primary_get_app_data_dir
        return primary_get_app_data_dir()
    except Exception as e:
        print(f"Primary get_app_data_dir failed: {e}")
        # Fallback implementation
        app_data_dir = os.path.join(tempfile.gettempdir(), "Video Generator")
        try:
            os.makedirs(app_data_dir, exist_ok=True)
        except Exception:
            app_data_dir = os.getcwd()
        return app_data_dir

def fallback_ensure_directory_exists(directory_path):
    """Fallback implementation of ensure_directory_exists"""
    try:
        # Try to use the primary implementation first
        from utils.helpers import ensure_directory_exists as primary_ensure_directory_exists
        return primary_ensure_directory_exists(directory_path)
    except Exception as e:
        print(f"Primary ensure_directory_exists failed: {e}")
        # Fallback implementation
        try:
            if not os.path.exists(directory_path):
                os.makedirs(directory_path, exist_ok=True)
                print(f"Created directory: {directory_path}")
            return True
        except OSError as os_error:
            print(f"OS Error creating directory {directory_path}: {os_error}")
            return False
        except Exception as fallback_error:
            print(f"Unexpected error creating directory {directory_path}: {fallback_error}")
            return False

def fallback_get_ffmpeg_path():
    """Fallback implementation of get_ffmpeg_path"""
    try:
        # Try to use the primary implementation first
        from utils.helpers import get_ffmpeg_path as primary_get_ffmpeg_path
        return primary_get_ffmpeg_path()
    except Exception as e:
        print(f"Primary get_ffmpeg_path failed: {e}")
        return 'ffmpeg'

def fallback_check_ffmpeg_availability():
    """Fallback implementation of check_ffmpeg_availability"""
    return False, 'ffmpeg', 'Import failed'

# Removed unused fallback functions and dictionaries (16 lines saved):
# - fallback_copy_file(): Not used anywhere
# - HELPER_FALLBACKS: Unused dictionary

def get_helpers_with_fallback():
    """
    Get helpers module with fallback functions
    
    Returns:
        Module or fallback object with helper functions
    """
    try:
        from utils.helpers import (
            get_app_data_dir, ensure_directory_exists, 
            get_ffmpeg_path, check_ffmpeg_availability
        )
        # Create a simple namespace object instead of a class instance
        class HelpersModule:
            pass
        
        helpers = HelpersModule()
        helpers.get_app_data_dir = get_app_data_dir
        helpers.ensure_directory_exists = ensure_directory_exists
        helpers.get_ffmpeg_path = get_ffmpeg_path
        helpers.check_ffmpeg_availability = check_ffmpeg_availability
        
        return helpers
    except ImportError as e:
        print(f"Could not import helpers: {e}")
        
        # Create a simple namespace object for fallbacks
        class FallbackHelpersModule:
            pass
        
        helpers = FallbackHelpersModule()
        helpers.get_app_data_dir = fallback_get_app_data_dir
        helpers.ensure_directory_exists = fallback_ensure_directory_exists
        helpers.get_ffmpeg_path = fallback_get_ffmpeg_path
        helpers.check_ffmpeg_availability = fallback_check_ffmpeg_availability
        
        return helpers 