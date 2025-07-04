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
from PIL import Image, ImageFilter, ImageEnhance
from moviepy.editor import (
    ImageClip, ColorClip, AudioFileClip, VideoFileClip, 
    CompositeAudioClip, concatenate_videoclips, CompositeVideoClip
)

# Import centralized utility functions
from utils.helpers import (
    configure_ffmpeg_for_moviepy, setup_temp_directory_for_bundled_exe,
    cleanup_temp_files
)
# video_utils removed for performance optimization
from config import DEFAULT_ASPECT_RATIO

def process_image_for_slideshow(img, target_width, target_height, fit_method="cover", zoom_effect=True):
    """
    Process an image for slideshow with different fitting methods

    Args:
        img: PIL Image or ImageClip object
        target_width: Target width for the image
        target_height: Target height for the image
        fit_method: How to fit the image ("cover", "contain", "stretch", "smart")
                   - "cover": Crop to fill frame (like CSS object-fit: cover)
                   - "contain": Fit with padding (like CSS object-fit: contain)
                   - "stretch": Stretch to fit exactly (may distort)
                   - "smart": Legacy smart fitting (same as cover)
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

        if fit_method == "cover" or fit_method == "smart":
            # Cover: crop to fill the frame while maintaining aspect ratio (like CSS object-fit: cover)
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

        elif fit_method == "contain":
            # Contain: fit with blurred background to maintain aspect ratio
            if orig_ratio > target_ratio:
                # Image is wider - add top/bottom padding with blurred background
                new_width = target_width
                new_height = int(new_width / orig_ratio)
                resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)

                # Create blurred background from the original image
                bg_img = pil_img.resize((target_width, target_height), Image.LANCZOS)
                bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=20))

                # Darken the background slightly
                enhancer = ImageEnhance.Brightness(bg_img)
                bg_img = enhancer.enhance(0.3)

                y_offset = (target_height - new_height) // 2
                bg_img.paste(resized_img, (0, y_offset))
                final_img = bg_img
            else:
                # Image is taller - add left/right padding with blurred background
                new_height = target_height
                new_width = int(new_height * orig_ratio)
                resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)

                # Create blurred background from the original image
                bg_img = pil_img.resize((target_width, target_height), Image.LANCZOS)
                bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=20))

                # Darken the background slightly
                enhancer = ImageEnhance.Brightness(bg_img)
                bg_img = enhancer.enhance(0.3)

                x_offset = (target_width - new_width) // 2
                bg_img.paste(resized_img, (x_offset, 0))
                final_img = bg_img

        elif fit_method == "stretch":
            # Stretch: stretch to fit exactly (may distort aspect ratio)
            final_img = pil_img.resize((target_width, target_height), Image.LANCZOS)

        else:  # Default to cover
            # Default: use cover method
            final_img = pil_img.resize((target_width, target_height), Image.LANCZOS)

        # Convert to numpy array for MoviePy
        img_array = np.array(final_img)
        
        # Create ImageClip
        clip = ImageClip(img_array)
        
        # Note: Zoom effect will be applied later when duration is set
        
        return clip

    except Exception as e:
        print(f"Error processing image: {e}")
        # Create a fallback black image
        fallback_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
        return ImageClip(np.array(fallback_img))

def create_slideshow(images_folder, title, content, audio_file, output_file,
                  use_gpu=False, use_effects=True, zoom_effect=True, fade_effect=True,
                  enhance=False, enhancement_options=None, stop_event=None,
                  aspect_ratio=DEFAULT_ASPECT_RATIO, ffmpeg_timeout=30, fit_method="cover"):
    """
    Create a slideshow video from images with memory-optimized processing

    Args:
        images_folder: Folder containing images OR list of image file paths (optimized mode)
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
        from utils.memory_manager import get_memory_manager

        # Get memory manager for clip tracking
        memory_manager = get_memory_manager()

        # Reduced logging: print(f"Creating slideshow from {images_folder}")

        # Configure FFmpeg and temp directory
        configure_ffmpeg_for_moviepy()
        setup_temp_directory_for_bundled_exe(output_file)
        
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user before slideshow creation.")
            return False
        
        # Get list of image files (support both folder path and list of image paths)
        image_files = []
        supported_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')

        if isinstance(images_folder, list):
            # images_folder is actually a list of image paths (optimized mode)
            for image_path in images_folder:
                if os.path.exists(image_path) and image_path.lower().endswith(supported_extensions):
                    image_files.append(image_path)
            print(f"Using {len(image_files)} image paths directly (no folder scanning)")
        else:
            # images_folder is a directory path (traditional mode)
            for file in os.listdir(images_folder):
                if file.lower().endswith(supported_extensions):
                    image_files.append(os.path.join(images_folder, file))
            print(f"Found {len(image_files)} images in folder")

        if not image_files:
            print("No supported image files found")
            return False

        # Sort images by filename for consistent order
        image_files.sort()
        print(f"Processing {len(image_files)} images")
        
        # Load audio to get duration
        try:
            audio_clip = AudioFileClip(audio_file)
            audio_duration = audio_clip.duration
            print(f"Audio duration: {audio_duration:.2f} seconds")
        except Exception as e:
            print(f"Error loading audio: {e}")
            return False

        # Calculate simple timing based on audio duration
        duration_per_image = audio_duration / len(image_files) if len(image_files) > 0 else 0
        image_sequence = list(range(len(image_files)))
        effects_recommended = []

        print(f"Duration per image: {duration_per_image:.2f} seconds")
        print(f"Using {len(image_sequence)} images")
        
        # Process images into clips using optimized sequence
        clips = []
        target_width, target_height = aspect_ratio

        # Determine effects based on recommendations
        use_slow_zoom = 'slow_zoom' in effects_recommended
        use_pan_effect = 'pan_effect' in effects_recommended
        use_subtle_zoom = 'subtle_zoom' in effects_recommended

        for slot_index, image_index in enumerate(image_sequence):
            if stop_event and stop_event.is_set():
                print("Process stopped by user during image processing.")
                return False

            # Handle case where image_index might exceed available images
            actual_image_index = image_index % len(image_files)
            img_path = image_files[actual_image_index]

            try:
                # Reduced logging: print(f"Processing slot {slot_index+1}/{len(image_sequence)}: {os.path.basename(img_path)} (image #{actual_image_index+1})")

                # Load and process image
                pil_img = Image.open(img_path)
                processed_clip = process_image_for_slideshow(
                    pil_img, target_width, target_height,
                    fit_method=fit_method, zoom_effect=(zoom_effect and use_effects) or use_subtle_zoom
                )

                # Set duration and FPS
                processed_clip = processed_clip.set_duration(duration_per_image)
                processed_clip = processed_clip.set_fps(24)  # Set standard FPS

                # Apply enhanced effects
                if use_effects and duration_per_image > 0:
                    # Apply standard zoom effects (emotion-aware effects removed for simplicity)
                    if use_slow_zoom or (zoom_effect and duration_per_image > 3.0):
                        # Slower, more subtle zoom for longer durations
                        zoom_factor = 0.05 if use_slow_zoom else 0.1
                        processed_clip = processed_clip.resize(lambda t: 1 + zoom_factor * t / duration_per_image)
                    elif use_subtle_zoom or zoom_effect:
                        # Standard zoom effect
                        processed_clip = processed_clip.resize(lambda t: 1 + 0.1 * t / duration_per_image)

                # Apply fade effect with conservative duration to prevent black frames
                if fade_effect and use_effects and duration_per_image > 1.5:
                    # Conservative fade duration to prevent black gaps
                    max_fade = min(0.3, duration_per_image * 0.15)  # Max 15% of clip duration
                    if duration_per_image > 4.0:
                        fade_duration = min(0.4, max_fade)  # Slightly longer for very long clips
                    else:
                        fade_duration = min(0.2, max_fade)  # Conservative for normal clips
                    processed_clip = processed_clip.fadein(fade_duration).fadeout(fade_duration)

                clips.append(processed_clip)
                
            except Exception as e:
                print(f"Error processing image {img_path}: {e}")
                # Create a black placeholder clip
                black_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                placeholder_clip = ImageClip(np.array(black_img)).set_duration(duration_per_image).set_fps(24)
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
            # Ensure all clips have the same FPS before concatenating
            for clip in clips:
                if not hasattr(clip, 'fps') or clip.fps is None:
                    clip.fps = 24

            # Apply standard transitions (emotion-aware transitions removed for simplicity)
            final_video = concatenate_videoclips(clips, method="compose")

            final_video = final_video.set_audio(audio_clip)

            # Explicitly set FPS on the final video
            final_video.fps = 24

        except Exception as e:
            print(f"Error concatenating clips: {e}")
            return False
        
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user before video writing.")
            final_video.close()
            return False
        
        # Write the final video
        # Reduced logging: print(f"Writing slideshow video to {output_file}")
        try:
            # Use optimized settings for slideshow videos
            write_params = {
                'fps': 24,
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
                    fps=24,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
            except Exception as fallback_error:
                print(f"Fallback write also failed: {fallback_error}")
                final_video.close()
                return False
        
        # Clean up with memory management
        try:
            final_video.close()
            audio_clip.close()
            for clip in clips:
                clip.close()

            # Force garbage collection
            memory_manager.force_garbage_collection()
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup error: {cleanup_error}")
        
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
