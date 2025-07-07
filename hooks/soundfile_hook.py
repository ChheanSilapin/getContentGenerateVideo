
"""
Runtime hook to ensure SoundFile can find its DLL
"""
import os
import sys
import ctypes

# When running as a frozen application
if getattr(sys, 'frozen', False):
    # Get the directory where the executable is located
    base_dir = os.path.dirname(sys.executable)
    
    # Add the base directory to PATH
    os.environ['PATH'] = base_dir + os.pathsep + os.environ['PATH']
    
    # Try to preload the DLL
    try:
        dll_path = os.path.join(base_dir, 'libsndfile.dll')
        if os.path.exists(dll_path):
            ctypes.CDLL(dll_path)
            print(f"Successfully loaded {dll_path}")
    except Exception as e:
        print(f"Failed to load libsndfile.dll: {e}")
    
    try:
        dll_path = os.path.join(base_dir, 'libsndfile_x64.dll')
        if os.path.exists(dll_path):
            ctypes.CDLL(dll_path)
            print(f"Successfully loaded {dll_path}")
    except Exception as e:
        print(f"Failed to load libsndfile_x64.dll: {e}")
