"""
Video utility functions
Extracted from video_service.py for better organization
"""
import os
import sys
import shutil
import subprocess
import traceback
import tempfile
import time
import numpy as np
from PIL import Image

# Import centralized utility functions
from utils.helpers import (
    get_ffmpeg_path, get_ffprobe_path, 
    validate_output_file, cleanup_temp_files
)

def calculate_loops_needed(target_duration, single_item_duration, min_loops=1):
    """
    Calculate how many loops are needed to match or exceed target duration
    
    Args:
        target_duration: The desired total duration
        single_item_duration: Duration of a single item (video/audio)
        min_loops: Minimum number of loops (default: 1)
        
    Returns:
        int: Number of loops needed
    """
    return max(min_loops, int(target_duration / single_item_duration) + 1)

def get_media_duration(media_file):
    """
    Get the duration of a media file (video or audio) using FFprobe
    
    Args:
        media_file: Path to media file
        
    Returns:
        float: Duration in seconds, or 0 if failed
    """
    try:
        ffprobe_path = get_ffprobe_path()
        if not ffprobe_path:
            print("FFprobe not available for duration detection")
            return 0
            
        cmd = [
            ffprobe_path,
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            media_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return duration
        else:
            print(f"FFprobe failed to get duration: {result.stderr}")
            return 0
            
    except subprocess.TimeoutExpired:
        print("FFprobe timeout while getting media duration")
        return 0
    except ValueError:
        print("Invalid duration value from FFprobe")
        return 0
    except Exception as e:
        print(f"Error getting media duration: {e}")
        return 0

def validate_video_file(video_file):
    """
    Validate video file compatibility with MoviePy and FFmpeg
    
    Args:
        video_file: Path to video file to validate
        
    Returns:
        tuple: (is_valid: bool, message: str, suggestion: str)
    """
    try:
        if not os.path.exists(video_file):
            return False, "Video file not found", "Check the file path"
        
        if os.path.getsize(video_file) == 0:
            return False, "Video file is empty", "Use a different video file"
        
        # Try to get basic info with FFprobe
        ffprobe_path = get_ffprobe_path()
        if ffprobe_path:
            cmd = [
                ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"Video file validation successful")
                return True, "Video file is valid", None
            else:
                error_output = result.stderr.lower()
                if 'invalid data' in error_output or 'corrupt' in error_output:
                    return False, "Video file appears to be corrupted", "Try re-encoding the video"
                elif 'codec' in error_output:
                    return False, "Unsupported video codec", "Convert to H.264/MP4 format"
                else:
                    print(f"FFprobe error output: {result.stderr}")
                    return False, f"FFprobe cannot read video: {result.stderr[:200]}", "Check video file format"
        else:
            return False, "FFprobe not available for validation", "Install FFmpeg"
            
    except subprocess.TimeoutExpired:
        return False, "Video validation timed out", "File may be too large or corrupted"
    except Exception as e:
        return False, f"Validation error: {e}", "Unknown validation issue"

def convert_video_to_compatible_format(input_video, output_video=None):
    """
    Convert video to a MoviePy-compatible format using FFmpeg
    
    Args:
        input_video: Path to input video file
        output_video: Path to output converted video (optional)
        
    Returns:
        tuple: (success, converted_video_path, error_message)
    """
    try:
        if output_video is None:
            # Create output path with "_converted" suffix
            base, ext = os.path.splitext(input_video)
            output_video = f"{base}_converted.mp4"
        
        print(f"Converting video to compatible format...")
        print(f"Input: {input_video}")
        print(f"Output: {output_video}")
        
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path or not (ffmpeg_path == 'ffmpeg' or os.path.exists(ffmpeg_path)):
            return False, None, "FFmpeg not available for conversion"
        
        # FFmpeg command for maximum compatibility conversion
        cmd = [
            ffmpeg_path,
            '-i', input_video,
            '-c:v', 'libx264',           # H.264 video codec
            '-profile:v', 'baseline',    # Baseline profile for maximum compatibility
            '-level', '3.0',             # Level 3.0 for broad device support
            '-pix_fmt', 'yuv420p',       # YUV420P pixel format (most compatible)
            '-c:a', 'aac',               # AAC audio codec
            '-ar', '44100',              # 44.1kHz audio sample rate
            '-ac', '2',                  # Stereo audio
            '-movflags', '+faststart',   # Enable fast start for web compatibility
            '-avoid_negative_ts', 'make_zero',  # Fix timestamp issues
            '-y',                        # Overwrite output file
            output_video
        ]
        
        print(f"Running FFmpeg conversion command...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd=os.path.dirname(ffmpeg_path) if os.path.dirname(ffmpeg_path) else None
        )
        
        if result.returncode == 0:
            if os.path.exists(output_video) and os.path.getsize(output_video) > 0:
                print(f"Video conversion successful: {output_video}")
                return True, output_video, None
            else:
                return False, None, "Conversion completed but output file is invalid"
        else:
            error_msg = result.stderr if result.stderr else "Unknown FFmpeg error"
            return False, None, f"FFmpeg conversion failed: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return False, None, "Video conversion timed out (file too large or complex)"
    except Exception as e:
        return False, None, f"Conversion error: {e}"

def reset_moviepy_configuration():
    """
    Reset and reconfigure MoviePy's FFmpeg settings completely
    This fixes compatibility issues where MoviePy's cached settings conflict with FFmpeg
    """
    try:
        # Clear any existing MoviePy configuration
        print("Resetting MoviePy configuration...")
        
        # Remove any cached MoviePy config files
        try:
            import moviepy.config as mp_config
            
            # Reset internal MoviePy settings
            if hasattr(mp_config, 'FFMPEG_BINARY'):
                delattr(mp_config, 'FFMPEG_BINARY')
            if hasattr(mp_config, 'IMAGEIO_FFMPEG_EXE'):
                delattr(mp_config, 'IMAGEIO_FFMPEG_EXE')
                
        except (ImportError, AttributeError):
            pass
        
        # Clear environment variables that might conflict
        env_vars_to_clear = [
            'FFMPEG_BINARY', 
            'IMAGEIO_FFMPEG_EXE',
            'FFMPEG_QUIET',
            'MOVIEPY_TEMP_DIR'
        ]
        
        for var in env_vars_to_clear:
            if var in os.environ:
                print(f"Clearing environment variable: {var}")
                del os.environ[var]
        
        # Configure FFmpeg path freshly
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path and (ffmpeg_path == 'ffmpeg' or os.path.exists(ffmpeg_path)):
            print(f"Setting fresh FFmpeg path: {ffmpeg_path}")
            
            # Set environment variable
            os.environ['FFMPEG_BINARY'] = ffmpeg_path
            os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_path
            
            # Try to configure MoviePy directly
            try:
                from moviepy.config import change_settings
                change_settings({"FFMPEG_BINARY": ffmpeg_path})
                print("MoviePy configuration reset and reconfigured successfully")
                return True
            except ImportError:
                print("WARNING: MoviePy config change_settings not available, using environment variables only")
                return True
        else:
            print(f"Could not reset MoviePy - FFmpeg path invalid: {ffmpeg_path}")
            return False
            
    except Exception as e:
        print(f"WARNING: Error resetting MoviePy configuration: {e}")
        return False

def create_fallback_video(images_folder, output_file):
    """Create a fallback video from the first image in the folder"""
    try:
        image_files = [f for f in os.listdir(images_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
        if image_files:
            shutil.copy2(os.path.join(images_folder, image_files[0]), output_file)
            print(f"Created fallback video from first image: {image_files[0]}")
            return True
        else:
            print("No images found for fallback video")
            return False
    except Exception as fallback_error:
        print(f"Error creating fallback video: {fallback_error}")
        return False

def use_best_available_output(enhanced_temp, original_temp, output_file):
    """Use the best available temporary file as the final output"""
    # Try enhanced temp first
    if enhanced_temp and os.path.exists(enhanced_temp) and os.path.getsize(enhanced_temp) > 1000:
        try:
            shutil.copy2(enhanced_temp, output_file)
            print(f"Using enhanced output: {enhanced_temp}")
            return True
        except Exception as e:
            print(f"Error copying enhanced temp file: {e}")
    
    # Try original temp as fallback
    if original_temp and os.path.exists(original_temp) and os.path.getsize(original_temp) > 1000:
        try:
            shutil.copy2(original_temp, output_file)
            print(f"Using original output: {original_temp}")
            return True
        except Exception as e:
            print(f"Error copying original temp file: {e}")
    
    # Clean up temp files
    try:
        cleanup_temp_files(enhanced_temp, original_temp)
    except:
        pass
        
    print("No valid fallback files available.")
    return False
