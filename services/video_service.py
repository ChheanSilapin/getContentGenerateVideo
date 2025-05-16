"""
Video service for creating videos
"""
import os
import sys
import shutil
import subprocess

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from create_video.py
try:
    from create_video import createSideShowWithFFmpeg
except ImportError:
    print("Error importing createSideShowWithFFmpeg from create_video.py")

# Import config
try:
    from config import DEFAULT_FRAME_RATE, DEFAULT_ZOOM_FACTOR
except ImportError:
    # Default values if config.py is not available
    DEFAULT_FRAME_RATE = 25
    DEFAULT_ZOOM_FACTOR = 0.5

from services.video_optimization import enhance_video, apply_ffmpeg_enhancements

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

def create_enhanced_slideshow(images_folder, title, content, audio_file, output_file, use_gpu=False, 
                             use_effects=True, zoom_effect=True, fade_effect=True, enhance=True,
                             enhancement_options=None):
    """
    Create an enhanced slideshow video with optimizations
    """
    # Default enhancement options if not provided
    if enhancement_options is None:
        enhancement_options = {
            "color_correction": True,
            "audio_enhancement": True,
            "framing": True,
            "motion_graphics": False
        }
    try:
        # First create the basic slideshow
        temp_output = output_file.replace('.mp4', '_temp.mp4')
        
        result = create_slideshow(
            images_folder, title, content, audio_file, temp_output,
            use_gpu=use_gpu, use_effects=use_effects,
            zoom_effect=zoom_effect, fade_effect=fade_effect
        )
        
        if not result:
            return False
            
        if enhance:
            print("Applying video enhancements...")
            try:
                # Apply our custom enhancements
                enhanced_temp = output_file.replace('.mp4', '_enhanced_temp.mp4')
                
                # Use the provided enhancement options
                enhance_result = enhance_video(temp_output, enhanced_temp, enhancement_options)
                
                if enhance_result and os.path.exists(enhanced_temp):
                    # Apply final FFmpeg enhancements
                    ffmpeg_result = apply_ffmpeg_enhancements(enhanced_temp, output_file, enhancement_options)
                    
                    # Clean up temporary files
                    try:
                        if os.path.exists(temp_output):
                            os.remove(temp_output)
                        if os.path.exists(enhanced_temp):
                            os.remove(enhanced_temp)
                    except Exception as cleanup_error:
                        print(f"Warning: Could not clean up temporary files: {cleanup_error}")
                    
                    if ffmpeg_result:
                        return os.path.exists(output_file)
                    else:
                        # If FFmpeg enhancement failed, use the enhanced temp file
                        if os.path.exists(enhanced_temp):
                            shutil.copy2(enhanced_temp, output_file)
                            return os.path.exists(output_file)
                        # If that doesn't exist, use the original temp file
                        elif os.path.exists(temp_output):
                            shutil.copy2(temp_output, output_file)
                            return os.path.exists(output_file)
                else:
                    # If enhancement failed, use the original temp file
                    print("Video enhancement failed, using original video")
                    shutil.copy2(temp_output, output_file)
                    return os.path.exists(output_file)
            except Exception as enhance_error:
                print(f"Error during enhancement: {enhance_error}")
                # If any enhancement step fails, just use the original video
                if os.path.exists(temp_output):
                    try:
                        shutil.copy2(temp_output, output_file)
                        return os.path.exists(output_file)
                    except Exception as copy_error:
                        print(f"Error copying temp file: {copy_error}")
                        return False
                return False
        else:
            # Just rename the temp file to the final output
            try:
                shutil.copy2(temp_output, output_file)
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                return os.path.exists(output_file)
            except Exception as rename_error:
                print(f"Error renaming temp file: {rename_error}")
                return False
            
    except Exception as e:
        print(f"Error creating enhanced slideshow: {e}")
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





