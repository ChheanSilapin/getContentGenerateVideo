"""
Subtitle service for generating subtitles
"""
import os
import sys

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from generate_ass.py
try:
    from generate_ass import process_local_video
except ImportError:
    print("Error importing process_local_video from generate_ass.py")

# Import config
try:
    from config import DEFAULT_MAX_CHARS_PER_LINE
except ImportError:
    # Default value if config.py is not available
    DEFAULT_MAX_CHARS_PER_LINE = 56

def generate_subtitles(text, video_file, audio_file, output_file):
    """
    Generate subtitles for a video
    
    Args:
        text: Text for subtitles
        video_file: Path to video file
        audio_file: Path to audio file
        output_file: Path to output subtitle file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # First, save the text to a file that process_local_video will read
        text_file = f"{audio_file}.txt"
        try:
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Created text file for subtitles: {text_file}")
        except Exception as e:
            print(f"Error creating text file: {e}")
            return False
        
        # Generate subtitles
        print(f"Generating subtitles for video: {video_file}")
        result = process_local_video(
            video_path=video_file,
            output_type="ass",
            maxChar=DEFAULT_MAX_CHARS_PER_LINE,
            output_file=output_file,
            audio_file=audio_file
        )
        
        # Check if the file was created
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"Subtitles generated successfully: {output_file}")
            return True
        else:
            print(f"Subtitle file not created or empty: {output_file}")
            return False
    except Exception as e:
        print(f"Error generating subtitles: {e}")
        return False


