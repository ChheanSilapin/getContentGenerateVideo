"""
Video Service - Handles video creation and processing
"""
import os
import sys

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from create_video import createSideShowWithFFmpeg
from Final_Video import merge_video_subtitle
from config import DEFAULT_FRAME_RATE, DEFAULT_ZOOM_FACTOR

def create_slideshow(images_folder, title, content, audio_file, output_file, use_gpu=False):
    """
    Create a slideshow video from images
    
    Args:
        images_folder: Folder containing images
        title: Video title
        content: Video content
        audio_file: Path to audio file
        output_file: Path to save the video
        use_gpu: Whether to use GPU for processing
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Set environment variable for GPU/CPU selection
        if use_gpu:
            print("Using GPU for video processing")
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use the first GPU
        else:
            print("Using CPU for video processing")
            os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Disable GPU
        
        result = createSideShowWithFFmpeg(
            folderName=images_folder,
            title=title,
            content=content,
            audioFile=audio_file,
            outputVideo=output_file,
            zoomFactor=DEFAULT_ZOOM_FACTOR,
            frameRarte=DEFAULT_FRAME_RATE
        )
        return result is not None
    except Exception as e:
        print(f"Error creating slideshow: {e}")
        return False

def merge_video_with_subtitles(video_path, subtitle_path, output_file):
    """
    Merge video with subtitles
    
    Args:
        video_path: Path to video file
        subtitle_path: Path to subtitle file
        output_file: Path to save the merged video
        
    Returns:
        str: Path to merged video or None on failure
    """
    try:
        return merge_video_subtitle(video_path, subtitle_path, output_file)
    except Exception as e:
        print(f"Error merging video with subtitles: {e}")
        return None


