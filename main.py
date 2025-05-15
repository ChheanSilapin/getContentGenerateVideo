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
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import the moviepy patch
try:
    from utils.moviepy_patch import apply_patch
    apply_patch()
except ImportError:
    print("Note: moviepy_patch module not found, continuing without it.")

def check_required_directories():
    """Check and create required directories"""
    required_dirs = [
        "output",
        "models",
        "services",
        "ui",
        "utils"
    ]

    for directory in required_dirs:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"Created directory: {directory}")
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        "models/video_generator.py",
        "services/audio_service.py",
        "services/image_service.py",
        "services/video_service.py",
        "services/subtitle_service.py",
        "ui/main_window.py",
        "ui/image_selector.py",
        "ui/text_redirector.py",
        "utils/helpers.py",
        "utils/web_utils.py",
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
        # Import tkinter
        import tkinter as tk
        from ui.main_window import MainWindow

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
        app = MainWindow(root)
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

if __name__ == "__main__":
    print("Starting Video Generator...")

    # Check and create required directories
    check_required_directories()

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

    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--console":
        run_console_mode()
    else:
        # Start the GUI
        create_gui()
