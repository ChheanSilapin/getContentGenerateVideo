#!/usr/bin/env python3
"""
Video Generator - Main Entry Point
Creates videos with subtitles from text and images
"""
import sys
import os
import platform
import traceback

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# Also add the parent directory to the path
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
print(f"Added to Python path: {current_dir}")
print(f"Added to Python path: {parent_dir}")

# Try to import the local moviepy_patch module
try:
    import moviepy_patch
except ImportError:
    print("Note: moviepy_patch module not found, continuing without it.")

# Import from utils
try:
    from utils.helpers import ensure_directory_exists
except ImportError:
    # Try a direct import
    sys.path.insert(0, os.path.join(current_dir, 'utils'))
    try:
        from helpers import ensure_directory_exists
        print("Imported helpers module directly")
    except ImportError as e:
        print(f"Error importing helpers module: {e}")

        # Define a fallback function
        def ensure_directory_exists(directory_path):
            """Fallback implementation of ensure_directory_exists"""
            try:
                if not os.path.exists(directory_path):
                    os.makedirs(directory_path, exist_ok=True)
                    print(f"Created directory: {directory_path}")
                return True
            except Exception as e:
                print(f"Error creating directory {directory_path}: {e}")
                return False

def check_required_files():
    """Check if all required files exist"""
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
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    return missing_files

def create_gui():
    """Create and run the GUI application"""
    try:
        # Import the GUI module
        import tkinter as tk
        from ui.gui import VideoGeneratorGUI

        root = tk.Tk()
        root.title("Video Generator")

        # Set window size and position it in the center of the screen
        window_width = 900
        window_height = 700
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        # Set a minimum size
        root.minsize(800, 600)

        # Create the application
        app = VideoGeneratorGUI(root)
        root.mainloop()
    except ImportError as e:
        print(f"Tkinter import error: {e}")
        # Fall back to console mode
        print("GUI framework not available. Falling back to console mode.")
        run_console_mode()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        traceback.print_exc()
        print("Falling back to console mode.")
        run_console_mode()

def run_console_mode():
    """Run the application in console mode"""
    print("\n=== VIDEO GENERATION SYSTEM (CONSOLE MODE) ===")
    print("This program will create a video with subtitles from text and images.")

    # Check if required modules are installed
    try:
        import tkinter
        print("Tkinter is installed but not being used in console mode.")
    except ImportError:
        print("Tkinter is not installed. You can install it with:")
        print("  - Windows: Install Python with the 'tcl/tk and IDLE' option")
        print("  - Linux: sudo apt-get install python3-tk")
        print("  - macOS: brew install python-tk")

    print("\nConsole mode is not fully implemented yet.")
    print("Please install the required packages and try again.")
    print("\nRequired packages:")
    print("  - tkinter (for GUI)")
    print("  - moviepy")
    print("  - pillow")
    print("  - requests")
    print("  - beautifulsoup4")
    print("  - emoji")

    print("\nYou can install these packages with:")
    print("pip install moviepy pillow requests beautifulsoup4 emoji")

def check_and_create_directories():
    """Check and create required directories"""
    required_dirs = [
        "output",
        "models",
        "services",
        "ui",
        "utils"
    ]

    for directory in required_dirs:
        ensure_directory_exists(directory)

if __name__ == "__main__":
    print("Starting Video Generator...")

    # Check and create required directories
    check_and_create_directories()

    # Check for required files
    missing_files = check_required_files()
    if missing_files:
        print("WARNING: The following required files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nThe application may not function correctly.")

        # Ask user if they want to continue
        response = input("Do you want to continue anyway? (y/n): ")
        if not response.lower().startswith('y'):
            print("Exiting.")
            sys.exit(1)

    try:
        # Check command line arguments
        if len(sys.argv) > 1 and sys.argv[1] == "--console":
            run_console_mode()
        else:
            # Start the GUI
            create_gui()
    except KeyboardInterrupt:
        print("\nProgram terminated by user (Ctrl+C)")
        sys.exit(0)
