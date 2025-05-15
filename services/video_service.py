"""
Video service for creating videos
"""
import os
import sys
import subprocess

# Import config
from config import DEFAULT_FRAME_RATE, DEFAULT_ZOOM_FACTOR

def create_slideshow(images_folder, title, content, audio_file, output_file, use_gpu=False, use_effects=True, zoom_effect=True, fade_effect=True):
    """
    Create a slideshow video from images
    
    Args:
        images_folder: Folder containing images
        title: Title of the video
        content: Content text
        audio_file: Path to audio file
        output_file: Path to output video file
        use_gpu: Whether to use GPU for processing
        use_effects: Whether to use visual effects
        zoom_effect: Whether to use zoom effects
        fade_effect: Whether to use fade effects
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import the createSideShowWithFFmpeg function
        from create_video import createSideShowWithFFmpeg
        
        # Set environment variable for GPU/CPU selection
        if use_gpu:
            print("Using GPU for video processing")
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use the first GPU
            # Force CPU encoding for final video even when using GPU for processing
            # This ensures compatibility
            use_gpu_encoding = False
        else:
            print("Using CPU for video processing")
            os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Disable GPU
            use_gpu_encoding = False
        
        # Set environment variables for effects
        os.environ["USE_EFFECTS"] = "1" if use_effects else "0"
        os.environ["USE_ZOOM"] = "1" if zoom_effect else "0"
        os.environ["USE_FADE"] = "1" if fade_effect else "0"
        
        result = createSideShowWithFFmpeg(
            folderName=images_folder,
            title=title,
            content=content,
            audioFile=audio_file,
            outputVideo=output_file,
            zoomFactor=DEFAULT_ZOOM_FACTOR,
            frameRarte=DEFAULT_FRAME_RATE,
            use_gpu_encoding=use_gpu_encoding
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
        # Import the merge_video_subtitle function
        from Final_Video import merge_video_subtitle
        return merge_video_subtitle(video_path, subtitle_path, output_file)
    except Exception as e:
        print(f"Error merging video with subtitles: {e}")
        return None
