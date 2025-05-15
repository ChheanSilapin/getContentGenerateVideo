"""
Subtitle service for generating subtitles
"""
import os
import sys

# Import config
from config import DEFAULT_MAX_CHARS_PER_LINE

def generate_subtitles(text, video_file, audio_file, output_file):
    """
    Generate subtitles for a video
    
    Args:
        text: Text for subtitles
        video_file: Path to video file
        audio_file: Path to audio file
        output_file: Path to output subtitle file
        
    Returns:
        str: Path to subtitle file or None on failure
    """
    try:
        # Import the process_local_video function
        from generate_ass import process_local_video
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Create a text file with the original text
        text_file = f"{audio_file}.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(text)
        
        # Generate subtitles
        print(f"Generating subtitles for video: {os.path.basename(video_file)}")
        subtitle_file = process_local_video(video_file, audio_file, output_file, max_chars_per_line=DEFAULT_MAX_CHARS_PER_LINE)
        
        # Check if the subtitle file was created
        if subtitle_file and os.path.exists(subtitle_file):
            print(f"Subtitles generated successfully: {os.path.basename(subtitle_file)}")
            return subtitle_file
        else:
            print("Failed to generate subtitles")
            return None
    except Exception as e:
        print(f"Error generating subtitles: {e}")
        return None
