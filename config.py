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
GUI_FONTS = get_gui_fonts()

# =============================================================================
# SUBTITLE CONFIGURATION - Single source of truth for all subtitle settings
# =============================================================================

SUBTITLE_CONFIG = {
    # Font and Styling
    "default_font": "Times New Roman",
    "font_size": 48,
    "font_bold": False,
    
    # Word Grouping (words per subtitle)
    "words_per_group_short": 5,    # For text < 100 words
    "words_per_group_medium": 4,   # For text 100-200 words  
    "words_per_group_long": 3,     # For text > 200 words
    
    # Timing Settings
    "reading_speed_wpm": 120,      # Words per minute for timing calculations
    "min_display_time": 1.2,       # Minimum seconds to display each subtitle
    "early_start_offset": 0.6,     # Start subtitles X seconds before speech
    "overlap_time": 0.3,           # Overlap between consecutive subtitles
    
    #Text Formart Settings
    "uppercase": True,
    "preserve_specail_formartting": True,


    
    # Speech Analysis
    "use_speech_analysis": True,
    "speech_analysis_max_duration": 60.0,  # Max audio length for speech analysis
    "silence_threshold_db": 16,    # dB below average for silence detection
    "min_silence_length_ms": 150,  # Minimum silence length in milliseconds
    
    # Style Presets
    "available_styles": {
        "modern_glow": {
            "name": "Modern Glow",
            "description": "White text with blue glow effect",
            "font": "Times New Roman",
            "size": 48,
            "primary_color": "&H00FFFFFF",  # White
            "outline_color": "&H00FF8000",  # Blue glow
            "outline_width": 3,
            "shadow": 2,
            "bold": True,
            "alignment": 2,  # Bottom center
            "margin_v": 80
        },
        "gradient_gold": {
            "name": "Gradient Gold", 
            "description": "Gold gradient with black shadow",
            "font": "Times New Roman",
            "size": 46,
            "primary_color": "&H0000D7FF",  # Gold
            "secondary_color": "&H000080FF",  # Orange
            "outline_color": "&H00000000",  # Black
            "outline_width": 2,
            "shadow": 2,
            "bold": True,
            "alignment": 2,
            "margin_v": 90
        },
        "fire_red": {
            "name": "Fire Red",
            "description": "Red to orange gradient with glow", 
            "font": "Times New Roman",
            "size": 50,
            "primary_color": "&H000000FF",  # Red
            "secondary_color": "&H000080FF",  # Orange
            "outline_color": "&H00000080",  # Dark red
            "outline_width": 3,
            "shadow": 2,
            "bold": True,
            "alignment": 2,
            "margin_v": 85
        },
        "ice_blue": {
            "name": "Ice Blue",
            "description": "Light blue with white glow",
            "font": "Times New Roman", 
            "size": 45,
            "primary_color": "&H00FFFF80",  # Light blue
            "outline_color": "&H00FFFFFF",  # White glow
            "outline_width": 2,
            "shadow": 1,
            "bold": True,
            "alignment": 2,
            "margin_v": 75
        }
    },
    
    # Default style to use
    "default_style": "modern_glow"
}

# File Cleanup Settings - CONSOLIDATED SYSTEM
# All cleanup now handled by models/video_generator.py cleanup_after_video_complete()
AUTO_CLEANUP_INTERMEDIATE_FILES = True   # Enable auto-cleanup by default to save space
KEEP_DEBUG_FILES_BY_DEFAULT = False      # Clean all files by default, keep only final_output.mp4
CLEANUP_TEMP_FILES_DURING_GENERATION = True  # Clean temp files during generation
AUTO_CLEANUP_AFTER_COMPLETION = True     # NEW: Enable auto-cleanup after video completion (single or batch)

# Cleanup Policy: Keep ONLY final_output.mp4, remove all intermediate files:
# - voice.mp3, voice.mp3.txt (voice generation files)
# - subtitles.ass (subtitle files) 
# - slideshow.mp4 (intermediate video)
# - temp_subtitle_*.ass (temporary subtitle files)
# - temp_audio_*.m4a (temporary audio files)
# - *TEMP_MPY_wvf_snd.mp3 (MoviePy temporary files)
# - images/ directory (unless from URL download)

# =============================================================================
# TAB VISIBILITY CONFIGURATION - Control which tabs are shown in the UI
# =============================================================================

# Individual Tab Visibility Controls
TAB_VISIBILITY = {
    'input': True,      # Core functionality - always recommended
    'images': True,     # Core functionality - always recommended
    'video': True,      # Advanced video processing features
    'merge': False,     # Advanced video merging - hide by default
    'options': True,    # Settings and configuration
    'batch': False,     # Batch processing - hide by default
    'log': True,        # Always visible for debugging and progress tracking
}

# UI Mode Presets - Override individual settings when selected
UI_MODE = "custom"  # Options: "simple", "standard", "advanced", "custom"

# UI Mode Definitions
UI_MODE_PRESETS = {
    "simple": {
        # Minimal interface for basic users
        'input': True,
        'images': True,
        'video': False,
        'merge': False,
        'options': False,
        'batch': False,
        'log': True,
    },
    "standard": {
        # Default interface with core features
        'input': True,
        'images': True,
        'video': True,
        'merge': False,
        'options': True,
        'batch': False,
        'log': True,
    },
    "advanced": {
        # Full interface with all features
        'input': True,
        'images': True,
        'video': True,
        'merge': True,
        'options': True,
        'batch': True,
        'log': True,
    },
    "custom": {
        'input': False,
        'images': False,
        'video': True,
        'merge': False,
        'options': False,
        'batch': False,
        'log': True,
    }
}

def get_tab_visibility():
    """
    Get the current tab visibility configuration based on UI_MODE
    
    Returns:
        dict: Tab visibility settings for current UI mode
    """
    if UI_MODE in UI_MODE_PRESETS:
        return UI_MODE_PRESETS[UI_MODE].copy()
    else:
        # Fallback to standard mode if invalid mode specified
        print(f"⚠️ Invalid UI_MODE '{UI_MODE}', using 'standard' mode")
        return UI_MODE_PRESETS["standard"].copy()

# Progress Display Settings
PROGRESS_DISPLAY_MODE = "percentage"  # Options: "percentage", "descriptive", "both"
# - "percentage": Always show just percentage (e.g., "45%")
# - "descriptive": Show descriptive messages when available (e.g., "Processing video 2 of 5")  
# - "both": Show both percentage and message (e.g., "45% - Processing video 2 of 5")