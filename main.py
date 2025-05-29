#!/usr/bin/env python3
"""
Video Generator - Optimized Main Entry Point
Creates videos with subtitles from text and images
Optimized for fast startup and standalone operation
"""
import os
import sys

# Add the current directory to the path for standalone operation
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_critical_files():
    """Quick check for critical files before heavy imports"""
    critical_files = ['config.py']
    missing = []
    
    for file in critical_files:
        if not os.path.exists(os.path.join(current_dir, file)):
            missing.append(file)
    
    return missing

def setup_environment():
    """Setup environment for standalone operation"""
    # Set up paths for bundled FFmpeg
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        bundle_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        
        # Add bundle directory to PATH for FFmpeg
        current_path = os.environ.get('PATH', '')
        if bundle_dir not in current_path:
            os.environ['PATH'] = bundle_dir + os.pathsep + current_path
    
    # Create output directory in user's documents if needed
    try:
        import tempfile
        output_dir = os.path.join(tempfile.gettempdir(), "Video Generator", "output")
        os.makedirs(output_dir, exist_ok=True)
        os.environ['VIDEO_GENERATOR_OUTPUT_DIR'] = output_dir
    except Exception:
        pass  # Will use current directory as fallback

def check_ffmpeg_availability():
    """Check if FFmpeg is available (bundled or system-installed)"""
    try:
        # Use the centralized implementation from utils.helpers
        from utils.helpers import check_ffmpeg_availability as centralized_check
        is_available, ffmpeg_path, error_message = centralized_check()
        return is_available  # Return only boolean for backward compatibility
    except ImportError:
        # Fallback implementation if utils.helpers is not available
        import subprocess
        try:
            subprocess.run(['ffmpeg', '-version'], 
                          capture_output=True, 
                          timeout=5, 
                          check=True)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

def show_ffmpeg_warning():
    """Show warning if FFmpeg is not available"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        
        message = (
            "FFmpeg not found!\n\n"
            "Video generation requires FFmpeg to be installed.\n\n"
            "Options:\n"
            "1. Download FFmpeg from: https://ffmpeg.org/download.html\n"
            "2. Add FFmpeg to your system PATH\n"
            "3. Place ffmpeg.exe in the same folder as this application\n\n"
            "The application will continue, but video generation may fail."
        )
        
        messagebox.showwarning("FFmpeg Not Found", message)
        root.destroy()
        
    except ImportError:
        # Fallback to console message if tkinter not available
        print("WARNING: FFmpeg not found!")
        print("Video generation requires FFmpeg. Please install it from https://ffmpeg.org/download.html")

def create_gui():
    """Create and run the GUI application with lazy imports"""
    try:
        from config import GUI_WINDOW_SIZE, GUI_TITLE
        import tkinter as tk
        from ui.gui import VideoGeneratorGUI
        
        root = tk.Tk()
        root.title(GUI_TITLE)
        root.geometry(GUI_WINDOW_SIZE)
        
        VideoGeneratorGUI(root)
        root.mainloop()
        
    except ImportError as e:
        error_msg = f"Import error: {e}\n\nSome required modules are missing."
        print(error_msg)
        
        # Try to show GUI error if tkinter is available
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Import Error", error_msg)
            root.destroy()
        except ImportError:
            pass
        
        # Fall back to console mode
        print("Falling back to console mode...")
        run_console_mode()
        
    except Exception as e:
        error_msg = f"Error starting GUI: {e}"
        print(error_msg)
        
        # Try to show GUI error
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", error_msg)
            root.destroy()
        except:
            pass
        
        print("Falling back to console mode...")
        run_console_mode()

def run_console_mode():
    """Run the application in console mode as fallback"""
    print("\n" + "="*50)
    print("VIDEO GENERATOR (CONSOLE MODE)")
    print("="*50)
    print("This program creates videos with subtitles from text and images.")
    print("\nNote: Console mode is limited. GUI mode is recommended.")
    print("\nRequired components:")
    print("- Python 3.8+ (you have this)")
    print("- FFmpeg (for video processing)")
    print("- Required Python packages (see requirements.txt)")
    print("\nTo use GUI mode, ensure all dependencies are installed.")
    print("\nPress Enter to exit...")
    
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass

def main():
    """Main entry point with optimized startup"""
    print("Starting Video Generator...")
    
    # Quick file check before any heavy imports
    missing_files = check_critical_files()
    if missing_files:
        print(f"Error: Missing critical files: {', '.join(missing_files)}")
        print("Please ensure all application files are present.")
        input("Press Enter to exit...")
        return
    
    # Setup environment for standalone operation
    setup_environment()
    
    # Check FFmpeg availability (non-blocking)
    if not check_ffmpeg_availability():
        print("Warning: FFmpeg not detected")
        # Show warning but don't block startup
        try:
            import threading
            warning_thread = threading.Thread(target=show_ffmpeg_warning, daemon=True)
            warning_thread.start()
        except:
            pass  # Continue without warning if threading fails
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--console":
        run_console_mode()
    else:
        # Start the GUI (with lazy imports)
        create_gui()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        print("Please check that all required files are present and try again.")
        input("Press Enter to exit...")
        sys.exit(1)
