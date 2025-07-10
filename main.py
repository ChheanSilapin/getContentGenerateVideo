#!/usr/bin/env python3
"""
Video Generator - Optimized Main Entry Point
Creates videos with subtitles from a text and images
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
    try:
        # Set up paths for bundled FFmpeg
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            bundle_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)

            # Add bundle directory to PATH for FFmpeg
            current_path = os.environ.get('PATH', '')
            if bundle_dir not in current_path:
                os.environ['PATH'] = bundle_dir + os.pathsep + current_path
                print(f"Added bundle directory to PATH: {bundle_dir}")

        # Create output directory in user's documents if needed
        try:
            import tempfile
            output_dir = os.path.join(tempfile.gettempdir(), "Video Generator", "output")
            os.makedirs(output_dir, exist_ok=True)
            os.environ['VIDEO_GENERATOR_OUTPUT_DIR'] = output_dir
            print(f"Set up fallback output directory: {output_dir}")
        except OSError as e:
            print(f"Warning: Could not create output directory: {e}")
            # Will use the current directory as fallback
    except Exception as e:
        print(f"Warning: Error in environment setup: {e}")
        # Continue execution - the application should handle missing setup gracefully

def initialize_models():
    """Initialize models in background for performance optimization"""
    try:
        # For portable builds, check if models are available first
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable - check portable model status
            try:
                from utils.portable_model_manager import get_portable_model_manager
                model_manager = get_portable_model_manager()

                if not model_manager.is_setup_complete():
                    print("⚠️ Models not yet downloaded - will be available after first-run setup")
                    return

            except ImportError:
                print("Warning: Portable model manager not available")

        print("Initializing models for optimal performance...")

        # Start background model initialization (non-blocking)
        import threading
        background_thread = threading.Thread(target=_background_model_initialization, daemon=True)
        background_thread.start()
        print("✅ Background model initialization started")

    except Exception as e:
        print(f"Warning: Model initialization failed: {e}")
        # Continue execution - models will load on-demand if pre-loading fails

def _background_model_initialization():
    """Background thread function for model pre-loading"""
    try:
        # Pre-load Whisper model through service manager (only if available)
        try:
            from services.whisper_service_manager import preload_whisper_model_background
            if preload_whisper_model_background():
                print("✅ Whisper model pre-loaded successfully")
            else:
                print("⚠️ Whisper model not available (will use fallback)")
        except ImportError:
            print("⚠️ Whisper service not available (optional dependency)")
        except Exception as e:
            print(f"⚠️ Whisper model background loading failed: {e}")

        # Pre-load model cache (only if available)
        try:
            from utils.model_cache import get_model_cache
            cache = get_model_cache()
            # Initialize cache without forcing model loads
            cache._initialize_background()
            print("✅ Model cache initialized")
        except ImportError:
            print("⚠️ Model cache not available (optional dependency)")
        except Exception as e:
            print(f"⚠️ Model cache background initialization failed: {e}")

    except Exception as e:
        print(f"Warning: Background model initialization failed: {e}")
        # Models will load on-demand if background pre-loading fails

def check_ffmpeg_availability():
    """Check if FFmpeg is available (bundled or system-installed)"""
    try:
        # Use the centralized implementation from utils.helpers
        from utils.helpers import check_ffmpeg_availability as centralized_check
        is_available, _, _ = centralized_check()
        return is_available  # Return only boolean for backward compatibility
    except ImportError:
        # Minimal fallback if utils.helpers is completely unavailable
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
        # Fallback to a console message if tkinter not available
        print("WARNING: FFmpeg not found!")
        print("Video generation requires FFmpeg. Please install it from https://ffmpeg.org/download.html")

def create_gui():
    """Create and run the GUI application with lazy imports and first-run setup"""
    try:
        from config import GUI_WINDOW_SIZE, GUI_TITLE
        import tkinter as tk

        # Create root window first for first-run setup
        root = tk.Tk()
        root.title(GUI_TITLE)
        root.geometry(GUI_WINDOW_SIZE)

        # Check if first-run setup is needed (only for portable builds)
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable - check for first-run setup
            try:
                from utils.portable_model_manager import get_portable_model_manager
                model_manager = get_portable_model_manager()

                if not model_manager.is_setup_complete():
                    print("\n" + "="*60)
                    print("🚀 FIRST TIME SETUP - Video Generator")
                    print("="*60)
                    print("Downloading required AI models...")
                    print("This will take 2-3 minutes with good internet connection.")
                    print("Future startups will be instant!")
                    print("="*60 + "\n")

                    # Hide root window during setup
                    root.withdraw()

                    # Download models with console progress
                    success = model_manager.download_all_missing_models()

                    if not success:
                        print("\n❌ Setup failed. Please check your internet connection.")
                        print("The application will continue but some features may not work.")
                        input("Press Enter to continue...")
                    else:
                        print("\n✅ Setup complete! Video Generator is ready to use.")
                        print("Starting application...")

                    # Show root window after setup
                    root.deiconify()

            except ImportError as setup_error:
                print(f"Warning: Could not check model setup: {setup_error}")
                # Continue without setup check

        # Import and create main GUI
        from ui.gui import VideoGeneratorGUI
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
        except Exception as e:
            print(f"Warning: Could not show FFmpeg warning: {e}")
        
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
    # CRITICAL: Set up multiprocessing protection early to prevent duplicate processes
    import multiprocessing
    multiprocessing.freeze_support()

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

    # Initialize models for performance optimization
    initialize_models()

    # Check FFmpeg availability (non-blocking)
    if not check_ffmpeg_availability():
        print("Warning: FFmpeg not detected")
        # Show warning but don't block startup
        try:
            import threading
            warning_thread = threading.Thread(target=show_ffmpeg_warning, daemon=True)
            warning_thread.start()
        except Exception as e:
            print(f"Warning: Could not start FFmpeg warning thread: {e}")  # Continue without warning if threading fails
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if "--console" in sys.argv:
            run_console_mode()
            return
        elif "--verbose" in sys.argv:
            # Enable verbose logging
            try:
                import config
                config.LOGGING_CONFIG['verbose_mode'] = True
                print("Verbose logging enabled")
            except Exception as e:
                print(f"Warning: Could not enable verbose mode: {e}")

    # Start the GUI (with lazy imports)
    create_gui()

if __name__ == "__main__":
    # CRITICAL: Prevent multiprocessing issues with PyInstaller
    # This prevents Kokoro TTS and other libraries from spawning duplicate processes
    import multiprocessing
    multiprocessing.freeze_support()

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
