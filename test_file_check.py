#!/usr/bin/env python3
"""
Test script to verify the file checking fix works correctly
"""
import os
import sys

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def get_base_path():
    """Get the base path for the application, handling PyInstaller executable"""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        # PyInstaller extracts files to sys._MEIPASS
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        else:
            # Fallback to executable directory
            return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

def check_required_files():
    """Check if all required files exist"""
    base_path = get_base_path()
    
    required_files = [
        "models/video_generator.py",
        "services/audio_service.py",
        "services/image_service.py",
        "services/video_service.py",
        "services/subtitle_service.py",
        "ui/gui.py",
        "ui/image_selector.py",
        "ui/text_redirector.py",
        "utils/helpers.py",
        "config.py"
    ]

    missing_files = []
    found_files = []
    
    print(f"Base path: {base_path}")
    print(f"Running as frozen executable: {getattr(sys, 'frozen', False)}")
    print(f"Has _MEIPASS: {hasattr(sys, '_MEIPASS')}")
    if hasattr(sys, '_MEIPASS'):
        print(f"_MEIPASS: {sys._MEIPASS}")
    
    print("\nChecking files:")
    for file in required_files:
        full_path = os.path.join(base_path, file)
        exists = os.path.exists(full_path)
        print(f"  {file}: {'✓' if exists else '✗'} ({full_path})")
        
        if exists:
            found_files.append(file)
        else:
            missing_files.append(file)

    print(f"\nSummary:")
    print(f"  Found: {len(found_files)} files")
    print(f"  Missing: {len(missing_files)} files")
    
    if missing_files:
        print(f"\nMissing files:")
        for file in missing_files:
            print(f"  - {file}")
    
    return missing_files

if __name__ == "__main__":
    print("Testing file checking functionality...")
    missing = check_required_files()
    
    if not missing:
        print("\n✓ All required files found!")
    else:
        print(f"\n✗ {len(missing)} files are missing")
    
    print("\nTest completed.")
