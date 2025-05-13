"""
Video Service - Handles video creation and processing functionality
"""
import os
import sys

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from create_video import createSideShowWithFFmpeg
from Final_Video import merge_video_subtitle
from config import DEFAULT_FRAME_RATE, DEFAULT_ZOOM_FACTOR

def create_slideshow(folderName, title, content, audioFile, outputVideo):
    """
    Create a slideshow video from images and audio
    
    Args:
        folderName: Folder containing images
        title: Title of the slideshow
        content: Content description
        audioFile: Path to the audio file
        outputVideo: Path to save the output video
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        createSideShowWithFFmpeg(
            folderName=folderName,
            title=title,
            content=content,
            audioFile=audioFile,
            outputVideo=outputVideo,
            zoomFactor=DEFAULT_ZOOM_FACTOR,
            frameRarte=DEFAULT_FRAME_RATE
        )
        return True
    except Exception as e:
        print(f"Error creating slideshow: {e}")
        return False

def merge_video_with_subtitles(video_path, subtitle_path, output_file):
    """
    Merge video and subtitles into a final output video
    
    Args:
        video_path: Path to the video file
        subtitle_path: Path to the subtitle file
        output_file: Path to save the output video
        
    Returns:
        str: Path to the merged video or None on failure
    """
    return merge_video_subtitle(video_path, subtitle_path, output_file=output_file)
