"""
Configuration settings for the Video Generator application
"""

# Output settings
DEFAULT_FRAME_RATE = 25
DEFAULT_ZOOM_FACTOR = 0.5
DEFAULT_MAX_CHARS_PER_LINE = 56

# Video dimensions - Default is 9:16 (vertical)
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280

# Aspect ratio presets
RATIO_9_16 = {
    "name": "9:16 (Vertical)",
    "width": 720,
    "height": 1280
}

RATIO_16_9 = {
    "name": "16:9 (Horizontal)",
    "width": 1280,
    "height": 720
}

RATIO_1_1 = {
    "name": "1:1 (Square)",
    "width": 1080,
    "height": 1080
}

# Default aspect ratio
DEFAULT_ASPECT_RATIO = "9:16"

# File paths and extensions
SUPPORTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')

# GUI settings
GUI_WINDOW_SIZE = "900x780"
GUI_TITLE = "Video Generator"
GUI_MIN_WIDTH = 800
GUI_MIN_HEIGHT = 600
GUI_RESIZABLE = True
GUI_CENTER_ON_SCREEN = True

# GUI Colors
GUI_COLORS = {
    "primary": "#2c3e50",      # Dark blue-gray
    "secondary": "#3498db",    # Blue
    "accent": "#e74c3c",       # Red
    "success": "#2ecc71",      # Green
    "background": "#ecf0f1",   # Light gray
    "text": "#34495e",         # Dark text
    "light_text": "#7f8c8d"    # Gray text
}

# GUI Fonts with intelligent fallbacks
def get_gui_fonts():
    """
    Get GUI fonts with intelligent fallbacks for all platforms
    
    Returns:
        dict: Font configuration with automatic fallbacks
    """
    try:
        # Import font manager if available
        from utils.font_manager import initialize_fonts
        return initialize_fonts()
    except ImportError:
        # Fallback font configuration (silent)
        return {
            "default": ("Consolas", 12),
            "button": ("Consolas", 12),  
            "label": ("Consolas", 12),
            "heading": ("Consolas", 12, "bold"),
            "console": ("Consolas", 12),
            "tab": ("Consolas", 12),
            "small": ("Consolas", 10),
            "large": ("Consolas", 14)
        }
    except Exception as e:
        # Only print actual errors
        print(f"⚠️ Font initialization error: {e}")
        # Safe fallback to system defaults
        return {
            "default": ("Arial", 12),
            "button": ("Arial", 12),
            "label": ("Arial", 12),
            "heading": ("Arial", 12, "bold"),
            "console": ("Courier New", 12),
            "tab": ("Arial", 12),
            "small": ("Arial", 10),
            "large": ("Arial", 14)
        }

# Initialize fonts at module load
try:
    GUI_FONTS = get_gui_fonts()
except:
    # Emergency fallback if everything fails
    GUI_FONTS = {
        "default": ("Arial", 12),
        "button": ("Arial", 12),
        "label": ("Arial", 12),
        "heading": ("Arial", 12, "bold"),
        "console": ("Courier New", 12),
        "tab": ("Arial", 12)
    }

# ENHANCED: Performance Optimization Settings
SUBTITLE_PERFORMANCE_MODE = "auto"  # "auto", "speed", "quality"
LONG_AUDIO_THRESHOLD = 10.0  # Seconds - switch to ultra-fast mode above this
ULTRA_FAST_MIN_OVERLAP = 0.05  # Minimal overlap for long audio (seconds)
STANDARD_OVERLAP = 0.1  # Standard overlap for shorter audio (seconds)
FAST_READING_SPEED_WPM = 200  # Words per minute for subtitle timing
ADAPTIVE_GROUP_SIZING = True  # Use adaptive word group sizing based on text length

# File Cleanup Settings  
AUTO_CLEANUP_INTERMEDIATE_FILES = False  # Ask user by default
KEEP_DEBUG_FILES_BY_DEFAULT = False  # Clean by default to save space
CLEANUP_TEMP_FILES_DURING_GENERATION = True  # Clean temp files during generation

# Audio Analysis Settings
ENABLE_SPEECH_ANALYSIS = True  # Use audio analysis for better sync
SPEECH_ANALYSIS_MAX_DURATION = 15.0  # Max duration for speech analysis (seconds)
SILENCE_DETECTION_THRESHOLD = 14  # dB below average for silence detection
MIN_SILENCE_LENGTH = 200  # Milliseconds

# Video Processing Options
VIDEO_RESOLUTIONS = ["1920x1080", "1280x720", "854x480", "640x360"]
DEFAULT_RESOLUTION = "1280x720"