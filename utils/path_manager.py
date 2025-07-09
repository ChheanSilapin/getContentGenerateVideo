"""
Path management utilities for the Video Generator application
Centralizes all path setup and management functionality
"""
import os
import sys

def setup_project_paths():
    """
    Setup all necessary paths for the project
    
    Returns:
        str: Project root directory path
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Add paths if not already present
    paths_to_add = [current_dir, project_root]
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    return project_root

def get_base_path():
    """
    Get the base path for the application, handling PyInstaller executable

    Returns:
        str: Base path for the application
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        else:
            return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_application_paths():
    """
    Get all application paths dynamically for portable installation

    Returns:
        dict: Dictionary containing all application paths
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        if hasattr(sys, '_MEIPASS'):
            # During execution, use temp directory for internal files
            base_dir = sys._MEIPASS
            exe_dir = os.path.dirname(sys.executable)
        else:
            # Fallback
            exe_dir = os.path.dirname(sys.executable)
            base_dir = exe_dir
    else:
        # Running as script (development)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        exe_dir = base_dir

    # All user data goes next to the executable for portability
    return {
        'base_dir': base_dir,                                    # Internal app files
        'exe_dir': exe_dir,                                      # Where .exe is located
        'models_dir': os.path.join(exe_dir, 'models'),           # AI models
        'cache_dir': os.path.join(exe_dir, 'cache'),             # Cache files
        'config_dir': os.path.join(exe_dir, 'config'),           # Configuration
        'logs_dir': os.path.join(exe_dir, 'logs'),               # Log files
        'temp_dir': os.path.join(exe_dir, 'temp'),               # Temporary files
        'settings_file': os.path.join(exe_dir, 'config', 'settings.json'),  # Settings
    }

def ensure_portable_directories():
    """
    Create all necessary directories for portable operation
    """
    paths = get_application_paths()

    directories_to_create = [
        paths['models_dir'],
        paths['cache_dir'],
        paths['config_dir'],
        paths['logs_dir'],
        paths['temp_dir'],
        os.path.join(paths['models_dir'], 'whisper'),
        os.path.join(paths['models_dir'], 'kokoro'),
    ]

    for directory in directories_to_create:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create directory {directory}: {e}")

    return paths

def add_utils_to_path():
    """
    Add utils directory to Python path for imports
    Used by services that need to import from utils
    
    Returns:
        str: Utils directory path
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    utils_dir = os.path.join(project_root, 'utils')
    
    if utils_dir not in sys.path:
        sys.path.insert(0, utils_dir)
    
    return utils_dir

def get_project_root():
    """
    Get the project root directory
    
    Returns:
        str: Project root directory path
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir) 