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