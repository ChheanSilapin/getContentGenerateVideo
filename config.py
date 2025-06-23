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
    
    # Word Grouping (words per subtitle) - Larger groups for better speech analysis compatibility
    "words_per_group_short": 6,    # Larger groups for better speech timing compatibility
    "words_per_group_medium": 5,   # Larger groups for better speech timing compatibility
    "words_per_group_long": 4,     # Larger groups for longer text

    # Timing Settings - SLOWER for much more comfortable reading
    "reading_speed_wpm": 80,       # Words per minute (slower for comfortable reading)
    "min_display_time": 4.0,       # Minimum seconds to display each subtitle (much longer)
    "early_start_offset": 0.2,     # Start subtitles X seconds before speech
    "overlap_time": 0.0,           # No overlap between subtitles (prevents overlapping text)
    "gap_time": 0.1,               # Minimum gap between subtitles to prevent overlap
    
    #Text Formart Settings
    "uppercase": True,
    # Speech Analysis - ENABLED for precise subtitle-voice synchronization
    "use_speech_analysis": True,    # Enabled for accurate timing based on actual speech patterns
    "speech_analysis_max_duration": 60.0,  # Max audio length for speech analysis
    "silence_threshold_db": 15,    # dB below average for silence detection (more sensitive for gTTS)
    "min_silence_length_ms": 100,  # Minimum silence length in milliseconds (detect natural pauses)
    
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

AUTO_CLEANUP_AFTER_COMPLETION = True  
ENABLE_CONTENT_ANALYSIS_CACHE = True
CONTENT_CACHE_MAX_SIZE = 100  
CONTENT_CACHE_TTL_HOURS = 24  
ENABLE_TTS_CACHE = True
TTS_CACHE_MAX_SIZE = 50  
TTS_CACHE_TTL_HOURS = 48  

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

# Logging Configuration - Cleaner, less verbose output
LOGGING_CONFIG = {
    "verbose_mode": False,               # Enable/disable verbose logging
    "show_emojis": True,                # Show emoji indicators in logs (helpful for status)
    "show_performance_status": False,    # Show performance optimization status
    "show_content_analysis": False,      # Show detailed content synchronization analysis
    "show_speech_recognition": True,     # Show speech recognition results (essential info)
    "show_file_operations": False,       # Show file copy/move operations
    "show_cache_operations": False,      # Show cache hit/miss operations
    "show_ffmpeg_commands": False,       # Show FFmpeg command details
    "show_subtitle_details": False,      # Show detailed subtitle timing logs
    "show_media_duration": False,        # Show media duration detection logs
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

PROGRESS_DISPLAY_MODE = "percentage"  
WHISPER_TIMESTAMPED_CONFIG = {
    # Model Configuration
    "model_name": "tiny",           # Whisper model size: "tiny", "base", "small", "medium", "large"
    "device": "auto",               # Device: "auto", "cpu", "cuda"
    "enable_service": True,         # Enable/disable whisper-timestamped service

    # Transcription Options
    "use_vad": True,                # Enable Voice Activity Detection for better accuracy
    "vad_method": "silero",         # VAD method: "silero", "auditok", or False
    "compute_confidence": True,     # Compute word-level confidence scores
    "temperature": 0.0,             # Temperature for deterministic output

    # Language and Content Settings
    "default_language": "en",       # Default language code
    "auto_detect_language": False,  # Auto-detect language (slower but more accurate)
    "content_aware_prompts": True,  # Use content-type specific prompts

    # Subtitle Integration
    "replace_speech_analysis": True,    # Replace current speech analysis with whisper-timestamped
    "fallback_to_vosk": True,          # Fallback to Vosk if whisper-timestamped fails
    "min_confidence_threshold": 0.7,   # Minimum confidence for using whisper timestamps
    "subtitle_sync_offset": 0.0,       # Fine-tune subtitle timing offset (seconds)

    # Performance Settings
    "max_audio_duration": 300,      # Maximum audio duration for processing (seconds)
    "enable_caching": True,         # Cache whisper results for repeated content
    "cache_ttl_hours": 24,          # Cache time-to-live in hours

    # Content Type Optimizations
    "content_type_prompts": {
        "historical": "This is historical content with names, dates, and places.",
        "story_review": "This is a story review with descriptive and emotional language.",
        "documentary": "This is documentary content with factual information.",
        "educational": "This is educational content with clear explanations.",
        "quote_reflection": "This is a quote with reflective commentary."
    }
}
