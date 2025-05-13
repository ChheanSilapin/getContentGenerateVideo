"""
Subtitle Service - Handles subtitle generation functionality
"""
import os
import sys

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_ass import process_local_video
from config import DEFAULT_MAX_CHARS_PER_LINE

def generate_subtitles(video_path, output_file, audio_file=None):
    """
    Generate subtitles for a video
    
    Args:
        video_path: Path to the video file
        output_file: Path to save the subtitle file
        audio_file: Path to the audio file (optional)
        
    Returns:
        str: Path to the generated subtitle file or None on failure
    """
    return process_local_video(
        video_path=video_path, 
        output_type="ass", 
        maxChar=DEFAULT_MAX_CHARS_PER_LINE, 
        output_file=output_file, 
        audio_file=audio_file
    )
