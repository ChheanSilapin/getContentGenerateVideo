"""
Fallback management utilities for the Video Generator application
Provides centralized fallback functionality for imports and operations
"""
import functools
import traceback
import tempfile
import os
import shutil

def with_fallback(fallback_func):
    """
    Decorator to provide fallback functionality for any function
    
    Args:
        fallback_func: Function to call if the primary function fails
        
    Returns:
        Decorated function with fallback capability
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Primary function {func.__name__} failed: {e}")
                try:
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    print(f"Fallback function also failed: {fallback_error}")
                    return None
        return wrapper
    return decorator

def safe_import(module_name, fallback_dict=None):
    """
    Safely import modules with fallback functions
    
    Args:
        module_name: Name of the module to import
        fallback_dict: Dictionary of fallback functions
        
    Returns:
        Imported module or fallback object
    """
    try:
        return __import__(module_name)
    except ImportError as e:
        print(f"Could not import {module_name}: {e}")
        if fallback_dict:
            return type('FallbackModule', (), fallback_dict)()
        return None

# Standard fallback functions
def fallback_get_app_data_dir():
    """Fallback implementation of get_app_data_dir"""
    app_data_dir = os.path.join(tempfile.gettempdir(), "Video Generator")
    try:
        os.makedirs(app_data_dir, exist_ok=True)
    except Exception:
        app_data_dir = os.getcwd()
    return app_data_dir

def fallback_ensure_directory_exists(directory_path):
    """Fallback implementation of ensure_directory_exists"""
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            print(f"Created directory: {directory_path}")
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False

def fallback_get_ffmpeg_path():
    """Fallback implementation of get_ffmpeg_path"""
    return 'ffmpeg'

def fallback_check_ffmpeg_availability():
    """Fallback implementation of check_ffmpeg_availability"""
    return False, 'ffmpeg', 'Import failed'

def fallback_copy_file(source, destination):
    """Fallback implementation for file copying"""
    try:
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(f"Error copying file from {source} to {destination}: {e}")
        return False

# Centralized fallback dictionaries for common imports
HELPER_FALLBACKS = {
    'get_app_data_dir': fallback_get_app_data_dir,
    'ensure_directory_exists': fallback_ensure_directory_exists,
    'get_ffmpeg_path': fallback_get_ffmpeg_path,
    'check_ffmpeg_availability': fallback_check_ffmpeg_availability,
}

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