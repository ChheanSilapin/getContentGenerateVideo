#!/usr/bin/env python3
"""
Setup script for Video Generator
"""
import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required")
        sys.exit(1)
    print(f"Python version: {sys.version}")

def install_dependencies():
    """Install required dependencies"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print("Please install the dependencies manually:")
        print("pip install -r requirements.txt")

def create_directories():
    """Create required directories"""
    directories = [
        "models",
        "services",
        "output"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"Created directory: {directory}")
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("FFmpeg is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("FFmpeg is not installed or not in PATH")
    if platform.system() == "Windows":
        print("Please download FFmpeg from: https://github.com/BtbN/FFmpeg-Builds/releases")
        print("Extract the files and place ffmpeg.exe, ffplay.exe, and ffprobe.exe in the root directory of the project")
    elif platform.system() == "Darwin":  # macOS
        print("Install FFmpeg using Homebrew: brew install ffmpeg")
    else:  # Linux
        print("Install FFmpeg using your package manager, e.g.: sudo apt-get install ffmpeg")
    
    return False

def main():
    """Main function"""
    print("=== Video Generator Setup ===")
    
    # Check Python version
    check_python_version()
    
    # Create directories
    create_directories()
    
    # Install dependencies
    install_dependencies()
    
    # Check FFmpeg
    check_ffmpeg()
    
    print("\nSetup complete. Run 'python main.py' to start the application")

if __name__ == "__main__":
    print("\nSetup complete. You can now run the application with 'python main.py'")
