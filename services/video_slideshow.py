"""
Video slideshow creation functionality
Extracted from video_service.py for better organization
"""
import os
import sys
import shutil
import traceback
import tempfile
import numpy as np
from PIL import Image
from moviepy.editor import (
    ImageClip, ColorClip, AudioFileClip, VideoFileClip, 
    CompositeAudioClip, concatenate_videoclips, CompositeVideoClip
)

# Import centralized utility functions
from utils.helpers import (
    configure_ffmpeg_for_moviepy, setup_temp_directory_for_bundled_exe,
    cleanup_temp_files
)
from .video_utils import create_fallback_video, use_best_available_output
from config import DEFAULT_ASPECT_RATIO

def process_image_for_slideshow(img, target_width, target_height, fit_method="smart", zoom_effect=True):
    """
    Process an image for slideshow with different fitting methods

    Args:
        img: PIL Image or ImageClip object
        target_width: Target width for the image
        target_height: Target height for the image
        fit_method: How to fit the image ("smart", "crop", "pad", "stretch")
        zoom_effect: Whether to apply zoom effect

    Returns:
        ImageClip: Processed image clip
    """
    try:
        # Convert to PIL Image if it's an ImageClip
        if hasattr(img, 'img'):
            pil_img = img.img
        else:
            pil_img = img

        # Get original dimensions
        orig_width, orig_height = pil_img.size
        target_ratio = target_width / target_height
        orig_ratio = orig_width / orig_height

        if fit_method == "smart":
            # Smart fitting: crop to fill the frame while maintaining aspect ratio
            if orig_ratio > target_ratio:
                # Image is wider than target - crop width
                new_height = target_height
                new_width = int(new_height * orig_ratio)
                resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                
                # Center crop
                left = (new_width - target_width) // 2
                cropped_img = resized_img.crop((left, 0, left + target_width, target_height))
            else:
                # Image is taller than target - crop height
                new_width = target_width
                new_height = int(new_width / orig_ratio)
                resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                
                # Center crop
                top = (new_height - target_height) // 2
                cropped_img = resized_img.crop((0, top, target_width, top + target_height))
            
            final_img = cropped_img

        elif fit_method == "pad":
            # Pad with black bars to maintain aspect ratio
            if orig_ratio > target_ratio:
                # Image is wider - add top/bottom padding
                new_width = target_width
                new_height = int(new_width / orig_ratio)
                resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                
                # Create black background
                final_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                y_offset = (target_height - new_height) // 2
                final_img.paste(resized_img, (0, y_offset))
            else:
                # Image is taller - add left/right padding
                new_height = target_height
                new_width = int(new_height * orig_ratio)
                resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                
                # Create black background
                final_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                x_offset = (target_width - new_width) // 2
                final_img.paste(resized_img, (x_offset, 0))

        elif fit_method == "stretch":
            # Stretch to fit exactly (may distort aspect ratio)
            final_img = pil_img.resize((target_width, target_height), Image.LANCZOS)

        else:  # Default to crop
            # Simple center crop
            final_img = pil_img.resize((target_width, target_height), Image.LANCZOS)

        # Convert to numpy array for MoviePy
        img_array = np.array(final_img)
        
        # Create ImageClip
        clip = ImageClip(img_array)
        
        # Apply zoom effect if requested
        if zoom_effect:
            # Subtle zoom effect: start at 100% and zoom to 110%
            clip = clip.resize(lambda t: 1 + 0.1 * t / clip.duration if hasattr(clip, 'duration') and clip.duration > 0 else 1)
        
        return clip

    except Exception as e:
        print(f"Error processing image: {e}")
        # Create a fallback black image
        fallback_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
        return ImageClip(np.array(fallback_img))

def create_slideshow(images_folder, title, content, audio_file, output_file, 
                  use_gpu=False, use_effects=True, zoom_effect=True, fade_effect=True, 
                  enhance=False, enhancement_options=None, stop_event=None, 
                  aspect_ratio=DEFAULT_ASPECT_RATIO, ffmpeg_timeout=30):
    """
    Create a slideshow video from images with optional enhancements
    
    Args:
        images_folder: Folder containing images
        title: Title text (not used in current implementation)
        content: Content text (not used in current implementation)
        audio_file: Path to audio file
        output_file: Path to output video file
        use_gpu: Whether to use GPU acceleration
        use_effects: Whether to apply visual effects
        zoom_effect: Whether to apply zoom effect to images
        fade_effect: Whether to apply fade transitions
        enhance: Whether to apply video enhancement
        enhancement_options: Options for enhancement
        stop_event: Threading event to stop the process
        aspect_ratio: Video aspect ratio (width, height)
        ffmpeg_timeout: Timeout for FFmpeg operations
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Creating slideshow from {images_folder}")
        
        # Configure FFmpeg and temp directory
        configure_ffmpeg_for_moviepy()
        setup_temp_directory_for_bundled_exe(output_file)
        
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user before slideshow creation.")
            return False
        
        # Get list of image files
        image_files = []
        supported_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
        
        for file in os.listdir(images_folder):
            if file.lower().endswith(supported_extensions):
                image_files.append(os.path.join(images_folder, file))
        
        if not image_files:
            print("No supported image files found in folder")
            return False
        
        # Sort images by filename for consistent order
        image_files.sort()
        print(f"Found {len(image_files)} images")
        
        # Load audio to get duration
        try:
            audio_clip = AudioFileClip(audio_file)
            audio_duration = audio_clip.duration
            print(f"Audio duration: {audio_duration:.2f} seconds")
        except Exception as e:
            print(f"Error loading audio: {e}")
            return False
        
        # Calculate duration per image
        duration_per_image = audio_duration / len(image_files)
        print(f"Duration per image: {duration_per_image:.2f} seconds")
        
        # Process images into clips
        clips = []
        target_width, target_height = aspect_ratio
        
        for i, img_path in enumerate(image_files):
            if stop_event and stop_event.is_set():
                print("Process stopped by user during image processing.")
                return False
            
            try:
                print(f"Processing image {i+1}/{len(image_files)}: {os.path.basename(img_path)}")
                
                # Load and process image
                pil_img = Image.open(img_path)
                processed_clip = process_image_for_slideshow(
                    pil_img, target_width, target_height, 
                    fit_method="smart", zoom_effect=zoom_effect and use_effects
                )
                
                # Set duration
                processed_clip = processed_clip.set_duration(duration_per_image)
                
                # Apply fade effect if requested
                if fade_effect and use_effects and duration_per_image > 1.0:
                    fade_duration = min(0.5, duration_per_image / 4)  # Max 0.5s or 1/4 of image duration
                    processed_clip = processed_clip.fadein(fade_duration).fadeout(fade_duration)
                
                clips.append(processed_clip)
                
            except Exception as e:
                print(f"Error processing image {img_path}: {e}")
                # Create a black placeholder clip
                black_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                placeholder_clip = ImageClip(np.array(black_img)).set_duration(duration_per_image)
                clips.append(placeholder_clip)
        
        if not clips:
            print("No valid image clips created")
            return False
        
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user before video composition.")
            return False
        
        # Concatenate all clips
        print("Concatenating image clips...")
        try:
            final_video = concatenate_videoclips(clips, method="compose")
            final_video = final_video.set_audio(audio_clip)
        except Exception as e:
            print(f"Error concatenating clips: {e}")
            return False
        
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user before video writing.")
            final_video.close()
            return False
        
        # Write the final video
        print(f"Writing slideshow video to {output_file}")
        try:
            # Use optimized settings for slideshow videos
            write_params = {
                'codec': 'libx264',
                'audio_codec': 'aac',
                'preset': 'medium',
                'ffmpeg_params': [
                    '-crf', '23',
                    '-pix_fmt', 'yuv420p',
                    '-avoid_negative_ts', 'make_zero'
                ],
                'verbose': False,
                'logger': None
            }
            
            # For bundled executables, use faster settings
            if getattr(sys, 'frozen', False):
                write_params['preset'] = 'ultrafast'
                write_params['ffmpeg_params'] = [
                    '-crf', '28',
                    '-pix_fmt', 'yuv420p',
                    '-avoid_negative_ts', 'make_zero'
                ]
            
            final_video.write_videofile(output_file, **write_params)
            
        except Exception as write_error:
            print(f"Error writing slideshow video: {write_error}")
            traceback.print_exc()
            
            # Try fallback approach
            try:
                print("Trying fallback video write...")
                final_video.write_videofile(
                    output_file,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
            except Exception as fallback_error:
                print(f"Fallback write also failed: {fallback_error}")
                final_video.close()
                return False
        
        # Clean up
        final_video.close()
        audio_clip.close()
        for clip in clips:
            clip.close()
        
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user after slideshow creation.")
            return False
        
        # Apply enhancement if requested
        if enhance and enhancement_options:
            print("Applying video enhancement...")
            try:
                from .video_optimization import enhance_video
                enhanced_output = enhance_video(output_file, output_file, enhancement_options, stop_event)
                if not enhanced_output:
                    print("Enhancement failed, using original slideshow")
            except ImportError:
                print("Video optimization module not available, skipping enhancement")
            except Exception as e:
                print(f"Enhancement error: {e}")
        
        print("Slideshow creation completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error creating slideshow: {e}")
        traceback.print_exc()
        return False

def createSideShowWithFFmpeg(folderName, title, content, audioFile, outputVideo, 
                           zoomFactor=0.5, frameRarte=25, use_gpu_encoding=False, 
                           stop_event=None, aspect_ratio=DEFAULT_ASPECT_RATIO):
    """
    Legacy slideshow creation function - redirects to new implementation
    Maintained for backward compatibility
    """
    print("Using legacy slideshow function - redirecting to new implementation")
    return create_slideshow(
        folderName, title, content, audioFile, outputVideo,
        use_gpu=use_gpu_encoding, use_effects=True, zoom_effect=True, fade_effect=True,
        enhance=False, enhancement_options=None, stop_event=stop_event,
        aspect_ratio=aspect_ratio
    )
