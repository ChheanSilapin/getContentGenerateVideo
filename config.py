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
    "silence_threshold_db": 15,    # dB below average for silence detection (optimized for neural TTS)
    "min_silence_length_ms": 100,  # Minimum silence length in milliseconds (detect natural pauses)
    
    # Dynamic Background Effects
    "enable_dynamic_backgrounds": True,     # Enable voice-synchronized background effects
    "background_opacity": 0.7,              # Background transparency (0.0-1.0)
    "background_padding": 10,               # Padding around text in pixels
    "background_border_radius": 8,          # Rounded corners for background
    "voice_sync_precision": "high",         # Background sync precision: "low", "medium", "high"

    # Sentence-Level Processing Only (optimized for speed)
    "enable_word_level_highlighting": False, # Disabled for speed optimization
    "word_highlight_mode": "sentence",       # Force sentence-level only

    # Style Presets
    "available_styles": {
        "modern_glow": {
            "name": "Modern Glow",
            "description": "White text with blue glow effect and dynamic background",
            "font": "Rubik",
            "size": 12,
            "primary_color": "&H00FFFFFF",  # White
            "outline_color": "&H00FF8000",  # Blue glow
            "outline_width": 3,
            "shadow": 2,
            "bold": True,
            "alignment": 2,  # Bottom center
            "margin_v": 80,
            # Dynamic background settings
            "background_color": "&H80000000",  # Semi-transparent black
            "background_active_color": "&H80001040",  # Semi-transparent dark blue when voice active
            "enable_voice_sync": True
        },
        "gradient_gold": {
            "name": "Gradient Gold",
            "description": "Gold gradient with black shadow and dynamic background",
            "font": "Rubik",
            "size": 46,
            "primary_color": "&H0000D7FF",  # Gold
            "secondary_color": "&H000080FF",  # Orange
            "outline_color": "&H00000000",  # Black
            "outline_width": 2,
            "shadow": 2,
            "bold": True,
            "alignment": 2,
            "margin_v": 90,
            # Dynamic background settings
            "background_color": "&H80000000",  # Semi-transparent black
            "background_active_color": "&H80402000",  # Semi-transparent dark gold when voice active
            "enable_voice_sync": True
        },
        "fire_red": {
            "name": "Fire Red",
            "description": "Red to orange gradient with glow and dynamic background",
            "font": "Rubik",
            "size": 50,
            "primary_color": "&H000000FF",  # Red
            "secondary_color": "&H000080FF",  # Orange
            "outline_color": "&H00000080",  # Dark red
            "outline_width": 3,
            "shadow": 2,
            "bold": True,
            "alignment": 2,
            "margin_v": 85,
            # Dynamic background settings
            "background_color": "&H80000000",  # Semi-transparent black
            "background_active_color": "&H80000040",  # Semi-transparent dark red when voice active
            "enable_voice_sync": True
        },
        "ice_blue": {
            "name": "Ice Blue",
            "description": "Light blue with white glow and dynamic background",
            "font": "Rubik",
            "size": 45,
            "primary_color": "&H00FFFF80",  # Light blue
            "outline_color": "&H00FFFFFF",  # White glow
            "outline_width": 2,
            "shadow": 1,
            "bold": True,
            "alignment": 2,
            "margin_v": 75,
            # Dynamic background settings
            "background_color": "&H80000000",  # Semi-transparent black
            "background_active_color": "&H80804000",  # Semi-transparent dark blue when voice active
            "enable_voice_sync": True
        },

        "bold_outline": {
            "name": "Bold Outline",
            "description": "Gold text with thick black outline for maximum visibility",
            "font": "Rubik",
            "size": 12,
            "primary_color": "&H0000D7FF",  # Bright yellow/gold
            "secondary_color": "&H0000B8FF",  # Slightly darker gold for gradient
            "outline_color": "&H00000000",  # Black outline
            "outline_width": 6,  # Thick outline for bold effect
            "shadow": 0,
            "bold": True,
            "alignment": 2,  # Bottom center
            "margin_v": 85,
            # Dynamic background settings
            "enable_voice_sync": True,
            # Enhanced outline settings for bold effect
            "background_padding": 15,  # Extra padding for bold style
            "background_border_radius": 10  # Rounded corners
        }
    },
    
    # Default style to use
    "default_style": "bold_outline"
}

AUTO_CLEANUP_AFTER_COMPLETION = False
ENABLE_TTS_CACHE = True
TTS_CACHE_MAX_SIZE = 50
TTS_CACHE_TTL_HOURS = 48

# Professional TTS Configuration (Edge TTS + Kokoro TTS)
TTS_CONFIG = {
    # Edge TTS Voices (Microsoft Neural Voices)
    "edge_voices": {
        "Guy": "en-US-GuyNeural",           # US Male - Warm, friendly
        "Connor": "en-IE-ConnorNeural",     # Irish Male - Authentic accent
        "Aria": "en-US-AriaNeural"          # US Female - Natural, expressive
    },

    # Kokoro TTS Voices (82M Parameter Model)
    "kokoro_voices": {
        "Michael": "am_michael",            # Male - Friendly, warm
        "Adam": "am_adam",                  # Male - Professional, clear
        "Heart": "af_heart"                 # Female - Warm, expressive
    },

    # Provider Settings
    "default_provider": "edge_tts",         # Prefer Edge TTS
    "fallback_enabled": True,               # Enable provider fallback
    "priority_order": ["edge_tts", "kokoro_tts"],

    # Voice Quality Settings
    "emotion_processing": True,             # Maintain emotional text processing
    "speed_adjustment": True,               # Keep speed adjustment features
    "default_voice": "Guy",                 # Default voice selection

    # Audio Settings
    "edge_audio_format": "wav",             # Edge TTS output format
    "kokoro_sample_rate": 24000,            # Kokoro TTS sample rate
    "auto_install_dependencies": True       # Auto-install TTS packages
}

FFMPEG_OPTIMIZATION = {
    "preset": "ultrafast",      # Fastest encoding for speed
    "crf": 28,                  # Higher CRF = faster encoding
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
    },

    # NEW: Advanced FFmpeg Optimizations
    "hardware_acceleration": {
        "enable_hwaccel": True,         # Enable hardware acceleration detection
        "prefer_nvenc": True,           # Prefer NVIDIA NVENC if available
        "prefer_qsv": True,             # Prefer Intel Quick Sync if available
        "fallback_to_software": True,   # Fallback to software encoding if hardware fails
    },

    "operation_specific": {
        "slideshow_creation": {
            "preset": "ultrafast",
            "crf": 30,                  # Higher CRF for slideshow (static images)
            "tune": "stillimage",       # Optimize for still images
        },
        "video_merging": {
            "use_stream_copy": True,    # Use stream copy when possible (no re-encoding)
            "concat_demuxer": True,     # Use concat demuxer for fastest merging
        },
        "subtitle_embedding": {
            "preset": "veryfast",       # Slightly better quality for subtitle embedding
            "crf": 25,                  # Better quality for text readability
        }
    }
}

# Parallel Processing Settings
ENABLE_PARALLEL_PROCESSING = True  # Enable parallel video generation (experimental)
MAX_PARALLEL_VIDEOS = 4            # Maximum videos to process simultaneously
PARALLEL_PROCESSING_MEMORY_LIMIT = 8  # GB of RAM limit for parallel processing

# NEW: Advanced Memory Management
MEMORY_OPTIMIZATION = {
    "enable_memory_monitoring": True,    # Monitor memory usage during processing
    "memory_threshold_warning": 6.0,     # GB - warn when memory usage exceeds this
    "memory_threshold_limit": 7.5,       # GB - pause processing when memory exceeds this
    "force_gc_interval": 30,             # Seconds between forced garbage collection
    "moviepy_clip_disposal": True,       # Aggressively dispose MoviePy clips
    "temp_file_streaming": True,         # Stream temp files instead of loading to memory
    "parallel_memory_per_job": 1.5,      # GB - estimated memory per parallel job
}

# Smart Duplicate Detection
ENABLE_DUPLICATE_DETECTION = True
DUPLICATE_CHECK_METHODS = ["content_hash", "filename_similarity"]  # Methods to detect duplicates
DUPLICATE_SIMILARITY_THRESHOLD = 0.95  # Similarity threshold (0.0-1.0)

# Processing Optimizations
PROCESSING_OPTIMIZATIONS = {
    "skip_redundant_analysis": True,     # Skip analysis if content hasn't changed
    "reuse_similar_effects": False,      # Disable for speed - skip effect reuse logic
    "batch_audio_generation": False,     # Disable batching - process one at a time for speed
    "optimize_image_loading": True,      # Keep image optimization
    "smart_temp_cleanup": True,          # Keep cleanup
    "memory_efficient_mode": False,      # Disable for speed - use direct processing
    "fast_mode": True,                   # Enable fast mode - skip non-essential processing

    # NEW: Image-to-Video Performance Optimizations
    "parallel_image_processing": True,   # Process images in parallel batches
    "image_batch_size": 8,               # Number of images to process simultaneously
    "skip_intermediate_files": True,     # Stream directly to FFmpeg without temp files
    "use_ffmpeg_image_sequence": True,   # Use FFmpeg's image sequence input for better performance
    "optimize_image_pipeline": True,     # Use optimized PIL → FFmpeg pipeline

    # NEW: Video Merging Performance Optimizations
    "prefer_ffmpeg_concat": True,        # Use FFmpeg concat demuxer for fastest merging
    "video_merge_batch_size": 10,        # Maximum videos to merge in one FFmpeg command
    "enable_merge_streaming": True,      # Stream merge without loading all videos to memory
    "optimize_merge_pipeline": True,     # Use optimized merge pipeline with minimal re-encoding
}

# Logging Configuration - Cleaner, less verbose output
LOGGING_CONFIG = {
    "verbose_mode": False,               # Enable/disable verbose logging
    "show_emojis": False,                # Show emoji indicators in logs (helpful for status)
    "show_performance_status": False,    # Show performance optimization status
    "show_content_analysis": False,      # Show detailed content synchronization analysis
    "show_speech_recognition": True,    # Show speech recognition results (essential info)
    "show_cache_operations": True,      # Show model and speech recognition cache operations
    "show_model_loading": True,         # Show model loading details
    "show_debug_messages": False,        # Show debug messages from services
    "show_file_operations": False,       # Show file copy/move operations
    "show_cache_operations": False,      # Show cache hit/miss operations
    "show_ffmpeg_commands": False,       # Show FFmpeg command details
    "show_subtitle_details": False,      # Show detailed subtitle timing logs
    "show_media_duration": False,        # Show media duration detection logs
    "show_cleanup_details": False,       # Show detailed cleanup operations
}
# Simplified tab configuration - only active tabs
TAB_VISIBILITY = {
    'images': True,
    'video': True,
    'log': True,
}

def get_tab_visibility():
    """
    Get the active tab visibility configuration

    Returns:
        dict: Tab visibility settings for active tabs only
    """
    return TAB_VISIBILITY.copy()

PROGRESS_DISPLAY_MODE = "percentage"  
WHISPER_TIMESTAMPED_CONFIG = {
    # Model Configuration
    "model_name": "tiny",           # Whisper model size: "tiny", "base", "small", "medium", "large"
    "device": "auto",               # Device: "auto", "cpu", "cuda"
    "enable_service": True,         # Enable/disable whisper-timestamped service

    # Transcription Options
    "use_vad": True,               # Disable VAD to avoid dependency issues
    "vad_method": "silero",            # VAD method: "silero", "auditok", or False
    "compute_confidence": True,     # Compute word-level confidence scores
    "temperature": 0.0,             # Temperature for deterministic output

    # Language Settings
    "default_language": "en",       # Default language code
    "auto_detect_language": True,  # Auto-detect language (slower but more accurate)

    # Subtitle Integration
    "replace_speech_analysis": True,    # Replace current speech analysis with whisper-timestamped
    "min_confidence_threshold": 0.7,   # Minimum confidence for using whisper timestamps
    "subtitle_sync_offset": 0.0,       # Fine-tune subtitle timing offset (seconds)

    # Performance Settings
    "max_audio_duration": 300,      # Maximum audio duration for processing (seconds)
    "enable_caching": True,         # Cache whisper results for repeated content
    "cache_ttl_hours": 24,          # Cache time-to-live in hours
}
