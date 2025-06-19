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

# Centralized file extension definitions for consistent usage across components
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
TEXT_EXTENSIONS = {'.txt', '.md'}

# Text file priority for automatic selection
TEXT_FILE_PRIORITY = ['main.txt', 'prompt.txt', 'script.txt', 'text.txt', 'content.txt']

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
    
    # Word Grouping (words per subtitle) - IMPROVED for better readability
    "words_per_group_short": 8,    # For text < 100 words (increased from 5)
    "words_per_group_medium": 7,   # For text 100-200 words (increased from 4)
    "words_per_group_long": 6,     # For text > 200 words (increased from 3)

    # Timing Settings - SLOWER for much more comfortable reading
    "reading_speed_wpm": 80,       # Words per minute (slower for comfortable reading)
    "min_display_time": 4.0,       # Minimum seconds to display each subtitle (much longer)
    "early_start_offset": 0.2,     # Start subtitles X seconds before speech
    "overlap_time": 0.0,           # No overlap between subtitles (prevents overlapping text)
    "gap_time": 0.1,               # Minimum gap between subtitles to prevent overlap
    
    #Text Formart Settings
    "uppercase": True,
    # Speech Analysis - DISABLED to use manual timing
    "use_speech_analysis": False,   # Disabled to force manual timing control
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
    "default_style": "gradient_gold"
}
# File cleanup settings
AUTO_CLEANUP_AFTER_COMPLETION = True  # Set to True to automatically clean up intermediate files after video generation

# =============================================================================
# PERFORMANCE OPTIMIZATION SETTINGS
# =============================================================================

# Content Analysis Caching - Prevents duplicate analysis for same content
ENABLE_CONTENT_ANALYSIS_CACHE = True
CONTENT_CACHE_MAX_SIZE = 100  # Maximum number of cached analyses
CONTENT_CACHE_TTL_HOURS = 24  # Cache time-to-live in hours

# TTS Audio Caching - Reuse audio for identical text/settings
ENABLE_TTS_CACHE = True
TTS_CACHE_MAX_SIZE = 50  # Maximum number of cached audio files
TTS_CACHE_TTL_HOURS = 48  # Cache time-to-live in hours

# FFmpeg Optimization Settings - Optimized for speed while maintaining quality
FFMPEG_OPTIMIZATION = {
    "preset": "fast",           # Balance of speed/quality (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
    "crf": 22,                  # Quality setting (18-28, lower = better quality)
    "threads": 0,               # Use all available CPU cores (0 = auto)
    "tune": "film",             # Optimize for content type (film, animation, grain, stillimage, fastdecode, zerolatency)
    "profile": "high",          # H.264 profile (baseline, main, high)
    "level": "4.0",             # H.264 level
    "pixel_format": "yuv420p",  # Pixel format for compatibility
    "audio_codec": "aac",       # Audio codec
    "audio_bitrate": "128k",    # Audio bitrate
    "movflags": "+faststart",   # Enable fast start for web playback

    # Additional speed optimizations
    "x264_params": {
        "me": "hex",            # Motion estimation (hex is faster than umh)
        "subme": "6",           # Subpixel motion estimation (6 is good speed/quality balance)
        "ref": "3",             # Reference frames (3 is good for speed)
        "mixed_refs": "1",      # Mixed references
        "trellis": "1",         # Trellis quantization (1 for speed)
        "weightb": "1",         # Weighted biprediction
        "8x8dct": "1",          # 8x8 DCT transform
        "fast_pskip": "1",      # Fast P-frame skip detection
        "aq_mode": "1",         # Adaptive quantization mode
        "aq_strength": "1.0"    # Adaptive quantization strength
    }
}

# Parallel Processing Settings
ENABLE_PARALLEL_PROCESSING = True  # Enable parallel video generation (experimental)
MAX_PARALLEL_VIDEOS = 4            # Maximum videos to process simultaneously
PARALLEL_PROCESSING_MEMORY_LIMIT = 8  # GB of RAM limit for parallel processing

# Smart Duplicate Detection
ENABLE_DUPLICATE_DETECTION = True
DUPLICATE_CHECK_METHODS = ["content_hash", "filename_similarity"]  # Methods to detect duplicates
DUPLICATE_SIMILARITY_THRESHOLD = 0.95  # Similarity threshold (0.0-1.0)

# Processing Optimizations
PROCESSING_OPTIMIZATIONS = {
    "skip_redundant_analysis": True,     # Skip analysis if content hasn't changed
    "reuse_similar_effects": True,       # Reuse effects for similar content types
    "batch_audio_generation": True,      # Generate all audio files before video processing
    "optimize_image_loading": True,      # Optimize image loading and caching
    "smart_temp_cleanup": True,          # Clean temporary files during processing
    "memory_efficient_mode": True       # Use memory-efficient processing for large batches
}
TAB_VISIBILITY = {
    'input': False,
    'images': True,
    'video': True,
    'merge': False,
    'options': False,
    'batch': False,
    'speech_recognition': False,  # Speech recognition tab disabled
    'log': True,
}

UI_MODE = "custom" 
UI_MODE_PRESETS = {
    "standard": {
        'input': True,
        'images': True,
        'video': True,
        'merge': False,
        'options': True,
        'batch': False,
        'log': True,
    },
    "custom": {
        'input': False,
        'images': True,
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

PROGRESS_DISPLAY_MODE = "percentage"  # Options: "percentage", "descriptive", "both"
