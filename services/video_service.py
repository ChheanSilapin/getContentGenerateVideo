"""
Video service for creating videos
"""
import os
import sys
import shutil
import subprocess
import traceback
import tempfile
import numpy as np
from PIL import Image
from moviepy.editor import (
    ImageClip, ColorClip, AudioFileClip, VideoFileClip, 
    CompositeAudioClip, concatenate_videoclips, CompositeVideoClip, AudioClip
)
# Import from utils
from utils.helpers import ensure_directory_exists, get_ffmpeg_path


# Import config
try:
    from config import (
        DEFAULT_FRAME_RATE, DEFAULT_ZOOM_FACTOR, VIDEO_WIDTH, VIDEO_HEIGHT,
        DEFAULT_ASPECT_RATIO, RATIO_9_16, RATIO_16_9, RATIO_1_1
    )
except ImportError:
    # Default values if config.py is not available
    DEFAULT_FRAME_RATE = 25
    DEFAULT_ZOOM_FACTOR = 0.5
    VIDEO_WIDTH = 720
    VIDEO_HEIGHT = 1280
    DEFAULT_ASPECT_RATIO = "9:16"
    RATIO_9_16 = {"name": "9:16 (Vertical)", "width": 720, "height": 1280}
    RATIO_16_9 = {"name": "16:9 (Horizontal)", "width": 1280, "height": 720}
    RATIO_1_1 = {"name": "1:1 (Square)", "width": 1080, "height": 1080}

# Import from Final_Video.py
try:
    from Final_Video import merge_video_subtitle
except ImportError:
    print("Error importing merge_video_subtitle from Final_Video.py")

    # Fallback implementation
    def merge_video_subtitle(video_path, subtitle_path, output_file="final_output.mp4"):
        """Fallback implementation for merging video and subtitle"""
        print(f"WARNING: Using fallback merge_video_subtitle function")
        try:
            # Just copy the video file as a fallback
            shutil.copy2(video_path, output_file)
            return output_file
        except Exception as e:
            print(f"Error in fallback merge_video_subtitle: {e}")
            return None

def calculate_loops_needed(target_duration, single_item_duration, min_loops=1):
    """
    Calculate how many loops are needed to match or exceed target duration
    
    Args:
        target_duration: The desired total duration
        single_item_duration: Duration of one loop/iteration
        min_loops: Minimum number of loops (default 1)
    
    Returns:
        int: Number of loops needed
    """
    return max(min_loops, int(target_duration / single_item_duration) + 1)

def process_image_for_slideshow(img, target_width, target_height, fit_method="smart", zoom_effect=True):
    """
    Process an image for slideshow with different fitting methods

    Args:
        img: PIL Image or ImageClip object
        target_width: Target width
        target_height: Target height
        fit_method: How to fit the image - "smart", "contain", "cover", or "stretch"
                    "smart" aggressively fills the frame to eliminate black backgrounds
        zoom_effect: Whether to apply zoom effect

    Returns:
        Processed ImageClip
    """
    from moviepy.editor import ImageClip
    import numpy as np

    # Create a fallback image with a neutral gray background in case of errors
    fallback_img = Image.new('RGB', (target_width, target_height), (128, 128, 128))

    try:
        # Handle different input types
        if isinstance(img, Image.Image):  # It's already a PIL Image
            pil_img = img
        elif hasattr(img, 'img') and isinstance(img.img, Image.Image):  # It's an ImageClip with PIL image
            pil_img = img.img
        elif hasattr(img, 'img') and isinstance(img.img, np.ndarray):  # It's an ImageClip with numpy array
            # Convert numpy array back to PIL Image
            pil_img = Image.fromarray(img.img.astype('uint8'))
        elif isinstance(img, np.ndarray):  # It's a numpy array
            # Convert numpy array to PIL Image
            pil_img = Image.fromarray(img.astype('uint8'))
        elif hasattr(img, 'filename') and os.path.exists(img.filename):  # It has a filename attribute
            # Try to load from filename
            pil_img = Image.open(img.filename)
        else:
            # Unknown image type - use fallback
            return ImageClip(np.array(fallback_img))

        # Validate that pil_img is a valid PIL Image
        if not isinstance(pil_img, Image.Image):
            return ImageClip(np.array(fallback_img))

        # Get original image dimensions
        # Handle case where size might not be a tuple
        try:
            if hasattr(pil_img, 'size'):
                if isinstance(pil_img.size, tuple) and len(pil_img.size) == 2:
                    img_width, img_height = pil_img.size
                else:
                    return ImageClip(np.array(fallback_img))
            else:
                return ImageClip(np.array(fallback_img))
        except Exception as e:
            return ImageClip(np.array(fallback_img))

        # Ensure dimensions are valid
        if img_width <= 0 or img_height <= 0:
            return ImageClip(np.array(fallback_img))

        # Calculate aspect ratios
        img_aspect = img_width / img_height
        target_aspect = target_width / target_height

        # Process based on fit method
        if fit_method == "smart":
            # Automatically choose the best fit method based on aspect ratios
            aspect_ratio_difference = abs(img_aspect - target_aspect)

            # More aggressive approach to fill the frame and eliminate black background
            if aspect_ratio_difference < 0.1:  # Very similar aspect ratios
                # Use stretch with slight modifications to avoid distortion
                new_img = pil_img.resize((target_width, target_height), Image.LANCZOS)
            else:
                # Use cover method for most cases to eliminate black background
                # Calculate scaling factor to cover the entire frame (may crop)
                width_ratio = target_width / img_width
                height_ratio = target_height / img_height
                scale_factor = max(width_ratio, height_ratio) * 1.05  # 5% larger to ensure full coverage

                # Calculate new dimensions
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)

                # Resize the image
                resized_pil = pil_img.resize((new_width, new_height), Image.LANCZOS)

                # Calculate crop position to center the image
                left = (new_width - target_width) // 2
                top = (new_height - target_height) // 2
                right = left + target_width
                bottom = top + target_height

                # Ensure crop coordinates are valid
                left = max(0, left)
                top = max(0, top)
                right = min(new_width, right)
                bottom = min(new_height, bottom)

                # Crop the image
                new_img = resized_pil.crop((left, top, right, bottom))

                # Ensure the cropped image has the correct dimensions
                if new_img.size != (target_width, target_height):
                    # If dimensions are off, create a new image with correct dimensions
                    correct_img = Image.new('RGB', (target_width, target_height), (128, 128, 128))
                    correct_img.paste(new_img, (0, 0))
                    new_img = correct_img

        elif fit_method == "contain":
            # Calculate scaling factor to fit image within the frame without cropping
            width_ratio = target_width / img_width
            height_ratio = target_height / img_height
            scale_factor = min(width_ratio, height_ratio) * 0.95  # 95% of max size for a small margin

            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)

            # Resize the image
            resized_pil = pil_img.resize((new_width, new_height), Image.LANCZOS)

            # Create a blurred background instead of gray bars
            try:
                # Create a blurred and darkened version of the original image as background
                background = pil_img.resize((target_width, target_height), Image.LANCZOS)
                
                # Apply blur effect
                from PIL import ImageFilter
                background = background.filter(ImageFilter.GaussianBlur(radius=15))
                
                # Darken the background
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Brightness(background)
                background = enhancer.enhance(0.3)  # Make it 30% of original brightness
                
                new_img = background
            except Exception as e:
                # Fallback: create a gradient background based on image colors
                try:
                    # Get dominant color from the image
                    temp_img = pil_img.resize((1, 1), Image.LANCZOS)
                    dominant_color = temp_img.getpixel((0, 0))
                    
                    # Create a gradient background
                    new_img = Image.new('RGB', (target_width, target_height), dominant_color)
                except:
                    # Final fallback: use a dark background
                    new_img = Image.new('RGB', (target_width, target_height), (32, 32, 32))

            # Paste the resized image in the center
            paste_x = (target_width - new_width) // 2
            paste_y = (target_height - new_height) // 2
            new_img.paste(resized_pil, (paste_x, paste_y))

        elif fit_method == "cover":
            # Calculate scaling factor to cover the entire frame (may crop)
            width_ratio = target_width / img_width
            height_ratio = target_height / img_height
            scale_factor = max(width_ratio, height_ratio) * 1.05  # 5% larger to ensure full coverage

            # Calculate new dimensions
            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)

            # Resize the image
            resized_pil = pil_img.resize((new_width, new_height), Image.LANCZOS)

            # Calculate crop position to center the image
            left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
            right = left + target_width
            bottom = top + target_height

            # Ensure crop coordinates are valid
            left = max(0, left)
            top = max(0, top)
            right = min(new_width, right)
            bottom = min(new_height, bottom)

            # Crop the image
            new_img = resized_pil.crop((left, top, right, bottom))

            # Ensure the cropped image has the correct dimensions
            if new_img.size != (target_width, target_height):
                # If dimensions are off, create a new image with correct dimensions
                correct_img = Image.new('RGB', (target_width, target_height), (128, 128, 128))
                correct_img.paste(new_img, (0, 0))
                new_img = correct_img

        else:  # "stretch" or any other value
            # Stretch the image to fit the target dimensions
            new_img = pil_img.resize((target_width, target_height), Image.LANCZOS)

        # Convert back to ImageClip
        result_clip = ImageClip(np.array(new_img))

        # Apply zoom effect if requested (temporarily disabled to fix dimension issues)
        if False:  # zoom_effect:
            from moviepy.video.fx.resize import resize
            # Apply zoom effect but ensure dimensions remain even
            def zoom_resize_func(t):
                zoom_factor = 1 + 0.05 * t
                return zoom_factor
            
            # Apply resize with zoom factor
            result_clip = resize(result_clip, zoom_resize_func)
            
            # After zoom, ensure dimensions are even
            if hasattr(result_clip, 'size'):
                w, h = result_clip.size
                if w % 2 != 0 or h % 2 != 0:
                    # Adjust to even dimensions
                    new_w = w if w % 2 == 0 else w - 1  # Subtract 1 to keep within bounds
                    new_h = h if h % 2 == 0 else h - 1
                    result_clip = result_clip.resize((new_w, new_h))
        
        # Final check: ensure the clip dimensions are even
        if hasattr(result_clip, 'size'):
            w, h = result_clip.size
            if w % 2 != 0 or h % 2 != 0:
                # Adjust to even dimensions
                new_w = w if w % 2 == 0 else w - 1
                new_h = h if h % 2 == 0 else h - 1
                result_clip = result_clip.resize((new_w, new_h))

        return result_clip

    except Exception as e:
        # Return a fallback black clip
        return ImageClip(np.array(fallback_img))

def createSideShowWithFFmpeg(folderName, title, content, audioFile, outputVideo, zoomFactor=0.5, frameRarte=25, use_gpu_encoding=False, stop_event=None, aspect_ratio=DEFAULT_ASPECT_RATIO):
    """
    Create a slideshow video from images using MoviePy

    Args:
        folderName: Folder containing images
        title: Title of the video
        content: Content text
        audioFile: Path to audio file
        outputVideo: Path to output video file
        zoomFactor: Zoom factor for effects
        frameRarte: Frame rate for video
        use_gpu_encoding: Whether to use GPU for encoding
        stop_event: Threading event to stop the process
        aspect_ratio: Aspect ratio for the video (9:16, 16:9, or 1:1)

    Returns:
        str: Path to output video if successful, None otherwise
    """
    # Check if we should stop
    if stop_event and stop_event.is_set():
        return None

    # Configure MoviePy for bundled executable
    
    # Set up proper temporary directory for bundled executable
    if getattr(sys, 'frozen', False):
        # Running as bundled executable
        temp_dir = os.path.join(os.path.dirname(outputVideo), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        # Set MoviePy temporary directory
        os.environ['TMPDIR'] = temp_dir
        os.environ['TEMP'] = temp_dir
        os.environ['TMP'] = temp_dir
        
        # Configure FFmpeg paths for bundled executable
        try:
            ffmpeg_path = get_ffmpeg_path()
            if ffmpeg_path and os.path.exists(ffmpeg_path):
                # Set FFmpeg path for MoviePy
                try:
                    from moviepy.config import change_settings
                    change_settings({"FFMPEG_BINARY": ffmpeg_path})
                except ImportError:
                    # Fallback: set environment variable for FFmpeg
                    os.environ['FFMPEG_BINARY'] = ffmpeg_path
        except Exception as e:
            pass  # Continue without FFmpeg configuration

    image_clips = []

    # Set target dimensions based on aspect ratio
    if aspect_ratio == "16:9":
        target_width, target_height = RATIO_16_9["width"], RATIO_16_9["height"]
    elif aspect_ratio == "1:1":
        target_width, target_height = RATIO_1_1["width"], RATIO_1_1["height"]
    else:  # Default to 9:16
        target_width, target_height = RATIO_9_16["width"], RATIO_9_16["height"]

    # Check if GPU is enabled
    use_gpu = os.environ.get("CUDA_VISIBLE_DEVICES", "") != ""
    if use_gpu:
        try:
            # Try to import moviepy with GPU support
            from moviepy.video.io.VideoFileClip import VideoFileClip
        except ImportError:
            use_gpu = False

    # Load audio first to get duration
    try:
        audio = AudioFileClip(audioFile)
        audio_duration = audio.duration
    except Exception as e:
        audio_duration = 15  # Default duration if audio can't be loaded
        audio = None

    # Get all image files from the folder
    image_files = []
    for filename in sorted(os.listdir(folderName)):
        if filename.endswith((".jpg", ".jpeg", ".png")):
            image_files.append(os.path.join(folderName, filename))

    if not image_files:
        return None

    # Calculate how many times we need to loop through images to match audio duration
    # Each image will be shown for 3 seconds by default
    image_count = len(image_files)
    single_loop_duration = image_count * 3  # 3 seconds per image

    # If audio is longer than one loop of images, we'll need multiple loops
    loops_needed = calculate_loops_needed(audio_duration, single_loop_duration)

    # Process each image, applying effects
    for loop in range(loops_needed):
        for filename in sorted(os.listdir(folderName)):
            if filename.endswith((".jpg", ".jpeg", ".png")):
                img_path = os.path.join(folderName, filename)

                try:
                    # Create a neutral gray background with target dimensions
                    bg = ColorClip(size=(target_width, target_height), color=(128, 128, 128), duration=3)

                    # Load the image and convert to RGB
                    try:
                        # First try to open with PIL to check channels
                        pil_img = Image.open(img_path)

                        # Verify that the image was loaded correctly
                        if not hasattr(pil_img, 'size') or not isinstance(pil_img.size, tuple) or len(pil_img.size) != 2:
                            # Create a fallback image
                            pil_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))

                        # Convert to RGB mode to ensure 3 channels
                        if pil_img.mode != 'RGB':
                            try:
                                pil_img = pil_img.convert('RGB')
                            except Exception as convert_error:
                                # Create a fallback image
                                pil_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))

                        # Save the converted image
                        converted_path = os.path.join(folderName, f"converted_{filename}")
                        pil_img.save(converted_path)

                        # Verify the image was saved correctly
                        if os.path.exists(converted_path) and os.path.getsize(converted_path) > 0:
                            # Create ImageClip directly from the PIL image to avoid conversion issues
                            img = ImageClip(np.array(pil_img))
                        else:
                            # Create a fallback image
                            fallback_img = Image.new('RGB', (target_width, target_height), (128, 128, 128))
                            fallback_path = os.path.join(folderName, f"fallback_{filename}")
                            fallback_img.save(fallback_path)
                            img = ImageClip(np.array(fallback_img))

                    except Exception as pil_error:
                        try:
                            # Try to open the image directly with PIL and convert to ImageClip
                            try:
                                direct_pil_img = Image.open(img_path).convert('RGB')
                                img = ImageClip(np.array(direct_pil_img))
                            except Exception as direct_pil_error:
                                # Try direct ImageClip as a fallback
                                img = ImageClip(img_path)
                        except Exception as clip_error:
                            # Create a neutral gray image as a last resort
                            fallback_img = Image.new('RGB', (target_width, target_height), (128, 128, 128))
                            fallback_path = os.path.join(folderName, f"fallback_{filename}")
                            fallback_img.save(fallback_path)
                            img = ImageClip(np.array(fallback_img))

                    # Get the fit method from environment variables or use default
                    fit_method = os.environ.get("IMAGE_FIT_METHOD", "smart")

                    # Process the image using our new function
                    resized_img = process_image_for_slideshow(
                        img,
                        target_width,
                        target_height,
                        fit_method=fit_method,
                        zoom_effect=os.environ.get("USE_ZOOM", "1") == "1"
                    )

                    # Set duration and position the image in the center
                    final_img = resized_img.set_duration(3).set_position(("center", "center"))

                    # Apply fade in/out effect if enabled
                    if os.environ.get("USE_FADE", "1") == "1":
                        from moviepy.video.fx.fadein import fadein
                        from moviepy.video.fx.fadeout import fadeout
                        final_img = fadein(final_img, 0.5)
                        final_img = fadeout(final_img, 0.5)

                    # Composite the image on the background
                    final_clip = CompositeVideoClip([bg, final_img])
                    image_clips.append(final_clip)

                except Exception as e:
                    # Create a fallback clip with error message
                    try:
                        bg = ColorClip(size=(target_width, target_height), color=(128, 128, 128), duration=3)
                        image_clips.append(bg)
                    except Exception as bg_error:
                        pass  # Continue processing other images

                # Check if we have enough clips to match audio duration
                total_duration = sum(clip.duration for clip in image_clips)
                if total_duration >= audio_duration:
                    break

        # Check if we have enough clips to match audio duration
        total_duration = sum(clip.duration for clip in image_clips)
        if total_duration >= audio_duration:
            break

    # If no images were processed successfully, create a blank clip
    if not image_clips:
        blank = ColorClip(size=(target_width, target_height), color=(128, 128, 128), duration=3)
        image_clips = [blank]

    # Concatenate all image clips
    
    video = concatenate_videoclips(image_clips, method="compose")

    # Ensure video dimensions are even (divisible by 2) for H.264 compatibility
    if hasattr(video, 'size'):
        w, h = video.size
        if w % 2 != 0 or h % 2 != 0:
            # Adjust to even dimensions
            new_w = w if w % 2 == 0 else w - 1
            new_h = h if h % 2 == 0 else h - 1
            video = video.resize((new_w, new_h))

    # Trim video to match audio duration exactly
    if video.duration > audio_duration:
        video = video.subclip(0, audio_duration)

    # Load audio
    try:
        if audio is None:
            audio = AudioFileClip(audioFile)
        # If audio is longer than video, extend video duration
        if audio.duration > video.duration:
            # This shouldn't happen now with our looping, but just in case
            # Create a blank clip to extend the video
            blank = ColorClip(size=(target_width, target_height), color=(128, 128, 128), duration=audio.duration - video.duration)
            video = concatenate_videoclips([video, blank])
    except Exception as e:
        # Create silent audio
        audio = AudioClip(lambda t: 0, duration=video.duration)

    # Set audio to video
    video = video.set_audio(audio)

    # Write the final video file with appropriate encoding
    try:
        # Configure write parameters for bundled executable with maximum compatibility
        write_params = {
            'fps': frameRarte,
            'codec': 'libx264',
            'audio_codec': 'aac',
            'temp_audiofile': os.path.join(os.path.dirname(outputVideo), 'temp_audio.m4a'),
            'remove_temp': True,
            'verbose': False,
            'logger': None,
            # Add compatibility parameters
            'ffmpeg_params': [
                '-profile:v', 'baseline',  # Use baseline profile for maximum compatibility
                '-level', '3.0',           # Use level 3.0 for wide device support
                '-pix_fmt', 'yuv420p',     # Ensure compatible pixel format
                '-ar', '44100',            # Standard sample rate
                '-ac', '2',                # Stereo audio
                '-avoid_negative_ts', 'make_zero'
            ]
        }
        
        # For bundled executables, use more conservative settings
        if getattr(sys, 'frozen', False):
            write_params.update({
                'preset': 'ultrafast',
                'ffmpeg_params': ['-avoid_negative_ts', 'make_zero']
            })
        
        # Always use CPU encoding for final output to ensure compatibility
        video.write_videofile(outputVideo, **write_params)
        
    except Exception as write_error:
        # Fallback to basic write
        try:
            video.write_videofile(outputVideo, fps=frameRarte, codec='libx264', verbose=False, logger=None)
        except Exception as fallback_error:
            return None

    return outputVideo

def create_slideshow(images_folder, title, content, audio_file, output_file, use_gpu=False, use_effects=True, zoom_effect=True, fade_effect=True, stop_event=None, aspect_ratio=DEFAULT_ASPECT_RATIO):
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
        stop_event: Threading event to stop the process
        aspect_ratio: Aspect ratio for the video (9:16, 16:9, or 1:1)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if we should stop
        if stop_event and stop_event.is_set():
            return False

        # Set environment variable for GPU/CPU selection
        if use_gpu:
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use the first GPU
            use_gpu_encoding = False
        else:
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
            use_gpu_encoding=use_gpu_encoding,
            aspect_ratio=aspect_ratio
        )
        return result is not None
    except Exception as e:
        return False

def create_enhanced_slideshow(images_folder, title, content, audio_file, output_file, use_gpu=False,
                             use_effects=True, zoom_effect=True, fade_effect=True, enhance=True,
                             enhancement_options=None, stop_event=None, aspect_ratio=DEFAULT_ASPECT_RATIO,
                             ffmpeg_timeout=30):  # Change default timeout from 300 to 30
    """
    Create an enhanced slideshow video with optimizations

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
        enhance: Whether to apply video enhancements
        enhancement_options: Dictionary of enhancement options
        stop_event: Threading event to stop the process
        aspect_ratio: Aspect ratio for the video (9:16, 16:9, or 1:1)
        ffmpeg_timeout: Maximum time in seconds to wait for FFmpeg to complete (default: 30s)

    Returns:
        bool: True if successful, False otherwise
    """
    # Check if we should stop
    if stop_event and stop_event.is_set():
        return False

    # Default enhancement options if not provided
    if enhancement_options is None:
        enhancement_options = {
            "color_correction": True,
            "audio_enhancement": True,
            "framing": True,
            "motion_graphics": False,
            "preset": "ultrafast",  # Change from fast to ultrafast
            "crf": 28,  # Increase from 23 to 28 for faster processing
            "image_fit_method": "cover"  # Changed from "contain" to "cover" to eliminate margins
        }
    try:
        # First create the basic slideshow
        temp_output = output_file.replace('.mp4', '_temp.mp4')

        # Extract aspect ratio from enhancement options if available
        if enhancement_options and 'aspect_ratio' in enhancement_options:
            aspect_ratio = enhancement_options['aspect_ratio']

        # Create the basic slideshow
        result = create_slideshow(
            images_folder, title, content, audio_file, temp_output,
            use_gpu=use_gpu, use_effects=use_effects,
            zoom_effect=zoom_effect, fade_effect=fade_effect,
            stop_event=stop_event,  # Pass the stop_event
            aspect_ratio=aspect_ratio  # Pass the aspect ratio
        )

        # If the process was stopped by user, clean up and return True
        if stop_event and stop_event.is_set():
            # Clean up any temporary files (simple inline cleanup)
            try:
                if os.path.exists(temp_output):
                    os.remove(temp_output)
            except Exception as e:
                pass
            return True  # Return True instead of False for a clean stop

        if not result:
            return False

        # Check if the temp file was created and has content
        if not os.path.exists(temp_output) or os.path.getsize(temp_output) < 1000:
            print(f"Warning: Basic slideshow file is missing or too small: {temp_output}")
            # Create a fallback video file
            try:
                # Copy the first image as a fallback
                image_files = [f for f in os.listdir(images_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
                if image_files:
                    shutil.copy2(os.path.join(images_folder, image_files[0]), output_file)
                    print(f"Created fallback video file by copying first image: {image_files[0]}")
                    return True
                else:
                    print("No images found for fallback.")
                    return False
            except Exception as fallback_error:
                print(f"Error creating fallback video: {fallback_error}")
                return False

        # Apply enhancements if requested
        if enhance:
            print("Step 2: Applying video enhancements...")
            try:
                # Check if we should stop
                if stop_event and stop_event.is_set():
                    print("Process stopped by user before enhancement.")
                    return False

                # Apply our custom enhancements
                enhanced_temp = output_file.replace('.mp4', '_enhanced_temp.mp4')

                
                print("Applying initial video enhancements...")
                enhance_result = enhance_video(temp_output, enhanced_temp, enhancement_options, stop_event)

                
                if stop_event and stop_event.is_set():
                    print("Process stopped by user during enhancement.")
                    return False

                if enhance_result and os.path.exists(enhanced_temp) and os.path.getsize(enhanced_temp) > 1000:
                    # Check if FFmpeg enhancements are enabled
                    if enhancement_options.get("apply_ffmpeg", False):
                        # Apply final FFmpeg enhancements with timeout
                        print("Applying final FFmpeg enhancements...")
                        ffmpeg_result = apply_ffmpeg_enhancements(
                            enhanced_temp,
                            output_file,
                            enhancement_options,
                            stop_event,
                            max_timeout=ffmpeg_timeout
                        )
                    else:
                        print("Skipping FFmpeg enhancements (disabled in options)...")
                        # Just copy the enhanced temp file to the output
                        import shutil
                        shutil.copy2(enhanced_temp, output_file)
                        ffmpeg_result = True

                    # Clean up temporary files
                    try:
                        if os.path.exists(temp_output):
                            os.remove(temp_output)
                            print(f"Removed temporary file: {temp_output}")
                        if os.path.exists(enhanced_temp):
                            os.remove(enhanced_temp)
                            print(f"Removed temporary file: {enhanced_temp}")
                    except Exception as cleanup_error:
                        print(f"Warning: Could not clean up temporary files: {cleanup_error}")

                    if ffmpeg_result and os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                        print("Video enhancement completed successfully.")
                        return True
                    else:
                        print("FFmpeg enhancement failed, using fallback...")
                        # If FFmpeg enhancement failed, use the enhanced temp file
                        if os.path.exists(enhanced_temp) and os.path.getsize(enhanced_temp) > 1000:
                            print(f"Using enhanced temp file as fallback: {enhanced_temp}")
                            shutil.copy2(enhanced_temp, output_file)
                            return os.path.exists(output_file)
                        # If that doesn't exist, use the original temp file
                        elif os.path.exists(temp_output) and os.path.getsize(temp_output) > 1000:
                            print(f"Using original temp file as fallback: {temp_output}")
                            shutil.copy2(temp_output, output_file)
                            return os.path.exists(output_file)
                        else:
                            print("No valid fallback files available.")
                            return False
                else:
                    # If enhancement failed, use the original temp file
                    print("Initial video enhancement failed, using original video")
                    if os.path.exists(temp_output) and os.path.getsize(temp_output) > 1000:
                        shutil.copy2(temp_output, output_file)
                        print(f"Copied original video to output: {output_file}")
                        return os.path.exists(output_file)
                    else:
                        print(f"Original video file is invalid: {temp_output}")
                        return False
            except Exception as enhance_error:
                print(f"Error during enhancement: {enhance_error}")
                traceback.print_exc()
                # If any enhancement step fails, just use the original video
                if os.path.exists(temp_output) and os.path.getsize(temp_output) > 1000:
                    try:
                        shutil.copy2(temp_output, output_file)
                        print(f"Used original video as fallback after error: {output_file}")
                        return os.path.exists(output_file)
                    except Exception as copy_error:
                        print(f"Error copying original video: {copy_error}")
                        return False
                return False
        else:
            # If no enhancement requested, just rename the temp file
            print("No enhancement requested, using basic slideshow.")
            try:
                shutil.copy2(temp_output, output_file)
                print(f"Copied basic slideshow to output: {output_file}")
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                    print(f"Removed temporary file: {temp_output}")
                return os.path.exists(output_file)
            except Exception as rename_error:
                print(f"Error renaming video file: {rename_error}")
                return False
    except Exception as e:
        print(f"Error creating enhanced slideshow: {e}")
        traceback.print_exc()
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

from services.video_optimization import enhance_video, apply_ffmpeg_enhancements

def validate_video_file(video_file):
    """
    Validate video file compatibility with MoviePy and FFmpeg
    
    Args:
        video_file: Path to video file to validate
        
    Returns:
        tuple: (is_valid, error_message, suggested_fix)
    """
    import subprocess
    
    try:
        # Check if file exists and is readable
        if not os.path.exists(video_file):
            return False, f"File does not exist: {video_file}", "Check file path"
        
        if not os.access(video_file, os.R_OK):
            return False, f"File is not readable: {video_file}", "Check file permissions"
        
        # Get file size
        file_size = os.path.getsize(video_file)
        if file_size == 0:
            return False, f"File is empty: {video_file}", "File appears to be corrupted"
        
        print(f"Video file validation: {video_file} ({file_size} bytes)")
        
        # Test with FFmpeg directly to check codec compatibility
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path and (ffmpeg_path == 'ffmpeg' or os.path.exists(ffmpeg_path)):
            try:
                # Use FFmpeg to probe the video file
                cmd = [
                    ffmpeg_path, 
                    '-i', video_file,
                    '-t', '1',  # Only process 1 second
                    '-f', 'null',
                    '-'
                ]
                
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=10,
                    cwd=os.path.dirname(ffmpeg_path) if os.path.dirname(ffmpeg_path) else None
                )
                
                # Check if FFmpeg can read the file
                if result.returncode == 0:
                    print(f"FFmpeg can read video file successfully")
                    return True, "Video file is valid", None
                else:
                    error_output = result.stderr.lower()
                    if 'invalid data' in error_output or 'corrupt' in error_output:
                        return False, "Video file appears to be corrupted", "Try re-encoding the video"
                    elif 'codec' in error_output:
                        return False, "Unsupported video codec", "Convert to H.264/MP4 format"
                    else:
                        print(f"FFmpeg error output: {result.stderr}")
                        return False, f"FFmpeg cannot read video: {result.stderr[:200]}", "Check video file format"
                        
            except subprocess.TimeoutExpired:
                return False, "FFmpeg validation timed out", "Video file may be corrupted or very large"
            except FileNotFoundError:
                return False, "FFmpeg not found", "Install or configure FFmpeg properly"
            except Exception as e:
                print(f"FFmpeg validation error: {e}")
                return False, f"FFmpeg validation failed: {e}", "Check FFmpeg installation"
        else:
            return False, "FFmpeg not available for validation", "Install FFmpeg"
            
    except Exception as e:
        return False, f"Validation error: {e}", "Unknown validation issue"

def add_voiceover_to_video(video_file, audio_file, output_file, mix_with_original=True, original_volume=0.3):
    """
    Add voice-over audio to a video while preserving the original video duration

    Args:
        video_file: Path to the input video file
        audio_file: Path to the generated audio file
        output_file: Path to the output video file
        mix_with_original: Whether to mix with original audio or replace it (mute original if False)
        original_volume: Volume level for original audio when mixing (0.0 to 1.0)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # STEP 1: Validate video file compatibility BEFORE MoviePy processing
        print(f"Validating video file: {video_file}")
        is_valid, error_msg, suggested_fix = validate_video_file(video_file)
        
        if not is_valid:
            print(f"ERROR: Video validation failed: {error_msg}")
            if suggested_fix:
                print(f"Suggested fix: {suggested_fix}")
            return False
        
        print(f"Video file validation successful")
        
        # STEP 2: Reset MoviePy configuration to fix compatibility issues
        print("Resetting MoviePy configuration...")
        reset_moviepy_configuration()
        
        # CRITICAL FIX: Configure MoviePy for both bundled and development environments
        ffmpeg_configured = False
        
        # Always try to configure FFmpeg path first
        try:
            ffmpeg_path = get_ffmpeg_path()
            print(f"Detected FFmpeg path: {ffmpeg_path}")
            
            if ffmpeg_path and (ffmpeg_path == 'ffmpeg' or os.path.exists(ffmpeg_path)):
                # Set FFmpeg path for MoviePy using multiple methods
                try:
                    from moviepy.config import change_settings
                    change_settings({"FFMPEG_BINARY": ffmpeg_path})
                    print(f"Voice-over: Configured MoviePy to use FFmpeg from: {ffmpeg_path}")
                    ffmpeg_configured = True
                except ImportError:
                    print("MoviePy config import failed, using environment variable")
                
                # Also set environment variable as fallback
                os.environ['FFMPEG_BINARY'] = ffmpeg_path
                print(f"Voice-over: Set FFMPEG_BINARY environment variable: {ffmpeg_path}")
                ffmpeg_configured = True
            else:
                print(f"Warning: FFmpeg path not found or invalid: {ffmpeg_path}")
                
        except Exception as e:
            print(f"Warning: Could not configure FFmpeg path for voice-over: {e}")

        # Configure temp directory for bundled executables
        if getattr(sys, 'frozen', False):
            # Running as bundled executable - set up proper temp directory
            temp_dir = os.path.join(os.path.dirname(output_file), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            # Set MoviePy temporary directory
            os.environ['TMPDIR'] = temp_dir
            os.environ['TEMP'] = temp_dir
            os.environ['TMP'] = temp_dir
            print(f"Voice-over: Set temp directory for bundled executable: {temp_dir}")

        # STEP 2: Enhanced video loading with multiple fallback strategies
        print(f"Loading video: {video_file}")
        video = None
        loading_success = False
        
        # Strategy 1: Standard MoviePy loading
        try:
            print("Trying standard MoviePy loading...")
            video = VideoFileClip(video_file)
            loading_success = True
            print("Standard MoviePy loading successful")
        except Exception as e:
            print(f"Standard MoviePy loading failed: {e}")
        
        # Strategy 2: MoviePy with specific codec parameters
        if not loading_success:
            try:
                print("Trying MoviePy with specific codec parameters...")
                # Force specific codec handling
                video = VideoFileClip(video_file, audio=True, target_resolution=None)
                loading_success = True
                print("MoviePy with codec parameters successful")
            except Exception as e:
                print(f"MoviePy with codec parameters failed: {e}")
        
        # Strategy 3: MoviePy without audio first, then add audio separately
        if not loading_success:
            try:
                print("Trying MoviePy without audio processing...")
                video = VideoFileClip(video_file, audio=False)
                # Try to add audio back
                try:
                    audio_clip = AudioFileClip(video_file)
                    video = video.set_audio(audio_clip)
                    print("Audio re-attached successfully")
                except:
                    print("WARNING: Could not re-attach original audio, continuing without it")
                loading_success = True
                print("MoviePy without audio processing successful")
            except Exception as e:
                print(f"MoviePy without audio processing failed: {e}")
        
        # Strategy 4: Convert video to compatible format as last resort
        if not loading_success:
            print("Attempting video format conversion as last resort...")
            success, converted_video, error_msg = convert_video_to_compatible_format(video_file)
            
            if success and converted_video:
                try:
                    print(f"Loading converted video: {converted_video}")
                    video = VideoFileClip(converted_video)
                    loading_success = True
                    print("Converted video loading successful")
                    # Note: We'll use the converted video for processing
                    video_file = converted_video  # Update video_file path for the rest of the function
                except Exception as e:
                    print(f"Even converted video failed to load: {e}")
            else:
                print(f"Video conversion failed: {error_msg}")
        
        # Final check - if all strategies failed
        if not loading_success or video is None:
            print(f"ERROR: All video loading strategies failed for {video_file}")
            print("This indicates a serious compatibility issue with the video file.")
            print("Possible solutions:")
            print("   1. Try converting the video with a different tool (e.g., HandBrake)")
            print("   2. Check if the video file is corrupted")
            print("   3. Update FFmpeg to a newer version")
            print("   4. Try a different video file format")
            return False

        print(f"Loading generated audio: {audio_file}")
        new_audio = AudioFileClip(audio_file)

        print(f"Original video duration: {video.duration:.2f}s")
        print(f"Generated audio duration: {new_audio.duration:.2f}s")

        # SIMPLIFIED APPROACH: Try basic MoviePy first, then use FFmpeg fallback
        
        # For simple cases where audio fits in video, try MoviePy
        if new_audio.duration <= video.duration:
            print("Audio is shorter than video - trying simple MoviePy approach")
            try:
                if video.audio is not None and mix_with_original:
                    # Mix with original audio
                    print(f"Mixing new audio with existing video audio (original at {original_volume*100}% volume)")
                    original_audio = video.audio.volumex(original_volume)
                    mixed_audio = CompositeAudioClip([original_audio, new_audio])
                    final_video = video.set_audio(mixed_audio)
                else:
                    # Replace audio
                    print("Replacing original audio with new voice-over")
                    final_video = video.set_audio(new_audio)
            except Exception as simple_error:
                print(f"Simple MoviePy approach failed: {simple_error}")
                print("Switching to FFmpeg fallback for reliability...")
                
                # Clean up MoviePy objects
                video.close()
                new_audio.close()
                
                # Use FFmpeg fallback
                return add_voiceover_to_video_ffmpeg_fallback(video_file, audio_file, output_file)
        else:
            # Audio is longer than video - need looping, use FFmpeg directly
            print("Audio is longer than video - using FFmpeg fallback for looping")
            
            # Get audio duration before cleanup
            audio_duration = new_audio.duration
            
            # Clean up MoviePy objects
            video.close()
            new_audio.close()
            
            # Use FFmpeg fallback which handles looping reliably
            return add_voiceover_to_video_ffmpeg_fallback(video_file, audio_file, output_file, audio_duration)



        # SIMPLIFIED VIDEO WRITING: Try once with MoviePy, fallback to FFmpeg if it fails
        print(f"Writing video with voice-over to: {output_file}")
        
        try:
            # Simple MoviePy write approach
            final_video.write_videofile(
                output_file,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None,
                ffmpeg_params=['-avoid_negative_ts', 'make_zero']
            )
            
            # Clean up MoviePy objects
            video.close()
            new_audio.close()
            final_video.close()
            
            print("Video written successfully with MoviePy")
            return True
            
        except Exception as write_error:
            print(f"MoviePy video writing failed: {write_error}")
            print("Switching to FFmpeg fallback for reliability...")
            
            # Clean up MoviePy objects
            try:
                video.close()
                new_audio.close()
                final_video.close()
            except:
                pass
            
            # Use FFmpeg fallback
            return add_voiceover_to_video_ffmpeg_fallback(video_file, audio_file, output_file)

    except Exception as e:
        print(f"Error adding voice-over to video: {e}")
        import traceback
        traceback.print_exc()
        return False



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
    import os
    
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

def add_voiceover_to_video_ffmpeg_fallback(video_file, audio_file, output_file, target_duration=None):
    """
    FFmpeg-based fallback for adding voiceover when MoviePy fails
    Uses FFmpeg directly for video looping and audio mixing - much more reliable
    
    Args:
        video_file: Path to input video
        audio_file: Path to audio file  
        output_file: Path to output video
        target_duration: Target duration for looping (None = use audio duration)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path or not (ffmpeg_path == 'ffmpeg' or os.path.exists(ffmpeg_path)):
            print("FFmpeg not available for fallback processing")
            return False
        
        print(f"Using FFmpeg fallback for reliable video processing...")
        
        # Get video duration using FFmpeg
        probe_cmd = [
            ffmpeg_path, '-i', video_file, '-f', 'null', '-', '-v', 'quiet', '-show_entries', 
            'format=duration', '-of', 'csv=p=0'
        ]
        
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
            video_duration = float(result.stdout.strip()) if result.stdout.strip() else 0
        except:
            print("WARNING: Could not determine video duration, using direct processing")
            video_duration = 0
        
        # Get audio duration
        probe_cmd = [
            ffmpeg_path, '-i', audio_file, '-f', 'null', '-', '-v', 'quiet', '-show_entries', 
            'format=duration', '-of', 'csv=p=0'
        ]
        
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
            audio_duration = float(result.stdout.strip()) if result.stdout.strip() else 0
        except:
            print("WARNING: Could not determine audio duration, using direct processing")
            audio_duration = 0
        
        target_duration = target_duration or audio_duration
        
        # Determine if we need to loop the video
        if target_duration > 0 and video_duration > 0 and target_duration > video_duration:
            loops_needed = int(target_duration / video_duration) + 1
            print(f"Video duration: {video_duration:.2f}s, Audio duration: {target_duration:.2f}s")
            print(f"Creating {loops_needed} loops using FFmpeg...")
            
            # Create looped video first
            temp_looped = output_file.replace('.mp4', '_temp_looped.mp4')
            
            # FFmpeg command for smooth video looping
            loop_cmd = [
                ffmpeg_path,
                '-stream_loop', str(loops_needed - 1),  # Additional loops needed
                '-i', video_file,
                '-c', 'copy',  # Copy without re-encoding (fast and reliable)
                '-avoid_negative_ts', 'make_zero',
                '-t', str(target_duration),  # Trim to exact duration
                '-y',
                temp_looped
            ]
            
            print("Creating looped video with FFmpeg...")
            result = subprocess.run(loop_cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode != 0:
                print(f"FFmpeg video looping failed: {result.stderr}")
                return False
            
            video_for_mixing = temp_looped
        else:
            print("No looping needed - audio fits within video duration")
            video_for_mixing = video_file
        
        # Step 2: Add audio using FFmpeg (replace original audio)
        print(f"Adding voice-over audio using FFmpeg...")
        
        mix_cmd = [
            ffmpeg_path,
            '-i', video_for_mixing,  # Video input
            '-i', audio_file,        # Audio input
            '-c:v', 'copy',          # Copy video stream (fast, no quality loss)
            '-c:a', 'aac',           # AAC audio codec (compatible)
            '-map', '0:v:0',         # Use video from first input
            '-map', '1:a:0',         # Use audio from second input  
            '-shortest',             # Stop when shortest stream ends
            '-avoid_negative_ts', 'make_zero',
            '-y',
            output_file
        ]
        
        result = subprocess.run(mix_cmd, capture_output=True, text=True, timeout=180)
        
        # Clean up temporary looped video
        if video_for_mixing != video_file and os.path.exists(video_for_mixing):
            os.remove(video_for_mixing)
        
        if result.returncode == 0:
            print("FFmpeg fallback processing successful!")
            return True
        else:
            print(f"FFmpeg audio mixing failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"FFmpeg fallback error: {e}")
        return False
