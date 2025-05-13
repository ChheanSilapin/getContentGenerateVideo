"""
Setup script to check and install required packages
"""
import subprocess
import sys

def check_and_install_packages():
    """Check for required packages and install them if missing"""
    required_packages = [
        'pyttsx3',
        'requests',
        'beautifulsoup4',
        'moviepy',
        'pillow',
        'emoji',
        'tk'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is already installed")
        except ImportError:
            print(f"✗ {package} is missing. Installing...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"  ✓ {package} installed successfully")
            except subprocess.CalledProcessError:
                print(f"  ✗ Failed to install {package}")

if __name__ == "__main__":
    print("Checking for required packages...")
    check_and_install_packages()
    print("\nSetup complete. You can now run the application with 'python main.py'")