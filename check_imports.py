#!/usr/bin/env python3
"""
Check if all required modules are available
"""
import sys
import os

def check_import(module_name):
    try:
        __import__(module_name)
        print(f"✓ {module_name} imported successfully")
        return True
    except ImportError as e:
        print(f"✗ {module_name} import failed: {e}")
        return False

def check_file(file_path):
    if os.path.exists(file_path):
        print(f"✓ {file_path} exists")
        return True
    else:
        print(f"✗ {file_path} does not exist")
        return False

if __name__ == "__main__":
    print("Checking Python version...")
    print(f"Python {sys.version}")
    
    print("\nChecking required modules...")
    modules = [
        "PySide6", 
        "PySide6.QtWidgets", 
        "PySide6.QtCore", 
        "threading", 
        "datetime"
    ]
    
    for module in modules:
        check_import(module)
    
    print("\nChecking required files...")
    files = [
        "ui/__init__.py",
        "ui/ui_dialog.py",
        "models/__init__.py",
        "models/video_generator.py"
    ]
    
    for file in files:
        check_file(file)
    
    print("\nChecking UI module...")
    try:
        from ui import Ui_dialog
        print("✓ Ui_dialog imported successfully from ui module")
    except ImportError as e:
        print(f"✗ Ui_dialog import failed: {e}")
    
    print("\nChecking model module...")
    try:
        from models.video_generator import VideoGeneratorModel
        print("✓ VideoGeneratorModel imported successfully")
    except ImportError as e:
        print(f"✗ VideoGeneratorModel import failed: {e}")