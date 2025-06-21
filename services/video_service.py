"""
Video service for creating videos
Refactored main orchestrator that delegates to specialized modules
"""
import os
import sys
import shutil

# Import modular video components
from .video_slideshow import create_slideshow, createSideShowWithFFmpeg
from .video_voiceover import add_voiceover_to_video
from .video_utils import (
    calculate_loops_needed, get_media_duration, validate_video_file,
    convert_video_to_compatible_format, reset_moviepy_configuration
)
from .video_looping import loop_video

# Import centralized utility functions
from utils.helpers import (
    configure_ffmpeg_for_moviepy,
    setup_temp_directory_for_bundled_exe,
    validate_output_file,
    safe_file_operation,
    cleanup_temp_files,
    get_media_duration_safe,
    get_ffmpeg_path,
    get_ffprobe_path
)

# Import config
try:
    from config import (
        DEFAULT_FRAME_RATE, DEFAULT_ZOOM_FACTOR, VIDEO_WIDTH, VIDEO_HEIGHT,
        DEFAULT_ASPECT_RATIO, RATIO_9_16, RATIO_16_9, RATIO_1_1
    )
except ImportError:
    # Default values if config.py is not available
    DEFAULT_FRAME_RATE = 25
    DEFAULT_ZOOM_FACTOR = 0.5
    VIDEO_WIDTH = 720
    VIDEO_HEIGHT = 1280
    DEFAULT_ASPECT_RATIO = "9:16"
    RATIO_9_16 = {"name": "9:16 (Vertical)", "width": 720, "height": 1280}
    RATIO_16_9 = {"name": "16:9 (Horizontal)", "width": 1280, "height": 720}
    RATIO_1_1 = {"name": "1:1 (Square)", "width": 1080, "height": 1080}

# Import from centralized video finalization service
from services.video_finalization import merge_video_subtitle

# =============================================================================
# PUBLIC API - Main video service functions that delegate to specialized modules
# =============================================================================

def create_video_with_voiceover(video_file, audio_file, output_file, mix_with_original=True, original_volume=0.3):
    """
    Main orchestrator function for adding voice-over to videos

    Args:
        video_file: Path to input video file
        audio_file: Path to voice-over audio file
        output_file: Path to output video file
        mix_with_original: Whether to mix with original audio
        original_volume: Volume level for original audio (0.0 to 1.0)

    Returns:
        bool: True if successful, False otherwise
    """
    return add_voiceover_to_video(video_file, audio_file, output_file, mix_with_original, original_volume)

def create_video_slideshow(images_folder, title, content, audio_file, output_file,
                          use_gpu=False, use_effects=True, zoom_effect=True, fade_effect=True,
                          enhance=False, enhancement_options=None, stop_event=None,
                          aspect_ratio=DEFAULT_ASPECT_RATIO, ffmpeg_timeout=30):
    """
    Main orchestrator function for creating slideshow videos

    Args:
        images_folder: Folder containing images
        title: Title text
        content: Content text
        audio_file: Path to audio file
        output_file: Path to output video file
        use_gpu: Whether to use GPU acceleration
        use_effects: Whether to apply visual effects
        zoom_effect: Whether to apply zoom effect
        fade_effect: Whether to apply fade transitions
        enhance: Whether to apply video enhancement
        enhancement_options: Enhancement options
        stop_event: Threading event to stop process
        aspect_ratio: Video aspect ratio
        ffmpeg_timeout: Timeout for FFmpeg operations

    Returns:
        bool: True if successful, False otherwise
    """
    return create_slideshow(images_folder, title, content, audio_file, output_file,
                          use_gpu, use_effects, zoom_effect, fade_effect,
                          enhance, enhancement_options, stop_event,
                          aspect_ratio, ffmpeg_timeout)

def create_looped_video(video_file, target_duration, output_file, method="seamless"):
    """
    Main orchestrator function for creating looped videos

    Args:
        video_file: Path to input video
        target_duration: Target duration for looped video
        output_file: Path to output video file
        method: Looping method ("direct", "crossfade", "seamless", "pingpong")

    Returns:
        str: Path to created looped video file, or None if failed
    """
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        print("FFmpeg not available for video looping")
        return None

    return loop_video(video_file, target_duration, ffmpeg_path, output_file, method)

def merge_video_and_subtitles(video_path, subtitle_path, output_file):
    """
    Main orchestrator function for merging video with subtitles

    Args:
        video_path: Path to video file
        subtitle_path: Path to subtitle file
        output_file: Path to output file

    Returns:
        str: Path to output file if successful, None otherwise
    """
    return merge_video_subtitle(video_path, subtitle_path, output_file)

# =============================================================================
# REFACTORING COMPLETE
# =============================================================================
# All duplicate functions have been moved to their respective specialized modules:
# - video_looping.py: Video looping and loop creation functions
# - video_utils.py: Utility functions (duration, validation, conversion, etc.)
# - video_voiceover.py: Voice-over and audio mixing functions
# - video_slideshow.py: Slideshow creation and image processing functions
#
# This module now serves as a clean entry point and orchestrator that delegates
# to the appropriate specialized modules while maintaining backward compatibility.
