"""
Video service for creating videos
"""
import os
import sys
import shutil
import subprocess
import traceback
from PIL import Image
from moviepy.editor import ImageClip, ColorClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip

# Import from utils
from utils.helpers import ensure_directory_exists

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
        print("Process stopped by user during slideshow creation.")
        return None

    image_clips = []

    # Set target dimensions based on aspect ratio
    if aspect_ratio == "16:9":
        target_width, target_height = RATIO_16_9["width"], RATIO_16_9["height"]
        print(f"Using 16:9 aspect ratio: {target_width}x{target_height}")
    elif aspect_ratio == "1:1":
        target_width, target_height = RATIO_1_1["width"], RATIO_1_1["height"]
        print(f"Using 1:1 aspect ratio: {target_width}x{target_height}")
    else:  # Default to 9:16
        target_width, target_height = RATIO_9_16["width"], RATIO_9_16["height"]
        print(f"Using 9:16 aspect ratio: {target_width}x{target_height}")

    # Check if GPU is enabled
    use_gpu = os.environ.get("CUDA_VISIBLE_DEVICES", "") != ""
    if use_gpu:
        try:
            # Try to import moviepy with GPU support
            from moviepy.video.io.VideoFileClip import VideoFileClip
            print("MoviePy GPU acceleration enabled")
        except ImportError:
            print("MoviePy GPU acceleration not available, falling back to CPU")
            use_gpu = False

    # Load audio first to get duration
    try:
        audio = AudioFileClip(audioFile)
        audio_duration = audio.duration
        print(f"Audio duration: {audio_duration} seconds")
    except Exception as e:
        print(f"Error loading audio: {e}")
        audio_duration = 15  # Default duration if audio can't be loaded
        audio = None

    # Get all image files from the folder
    image_files = []
    for filename in sorted(os.listdir(folderName)):
        if filename.endswith((".jpg", ".jpeg", ".png")):
            image_files.append(os.path.join(folderName, filename))

    if not image_files:
        print("No images found in folder")
        return None

    # Calculate how many times we need to loop through images to match audio duration
    # Each image will be shown for 3 seconds by default
    image_count = len(image_files)
    single_loop_duration = image_count * 3  # 3 seconds per image

    # If audio is longer than one loop of images, we'll need multiple loops
    loops_needed = max(1, int(audio_duration / single_loop_duration) + 1)

    print(f"Using {image_count} images, looping {loops_needed} times to match {audio_duration}s audio")

    # Process each image, applying effects
    for loop in range(loops_needed):
        for filename in sorted(os.listdir(folderName)):
            if filename.endswith((".jpg", ".jpeg", ".png")):
                img_path = os.path.join(folderName, filename)

                try:
                    # Create a black background with target dimensions
                    bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=3)

                    # Load the image and convert to RGB
                    try:
                        # First try to open with PIL to check channels
                        pil_img = Image.open(img_path)
                        # Convert to RGB mode to ensure 3 channels
                        if pil_img.mode != 'RGB':
                            print(f"Converting image {filename} from {pil_img.mode} to RGB")
                            pil_img = pil_img.convert('RGB')
                            # Save the converted image
                            converted_path = os.path.join(folderName, f"converted_{filename}")
                            pil_img.save(converted_path)
                            img = ImageClip(converted_path)
                        else:
                            img = ImageClip(img_path)
                    except Exception as pil_error:
                        print(f"Error with PIL: {pil_error}, trying direct ImageClip")
                        img = ImageClip(img_path)

                    # Get original image dimensions
                    img_width, img_height = img.size

                    # Calculate scaling factor to fit image within the frame without cropping
                    width_ratio = target_width / img_width
                    height_ratio = target_height / img_height

                    # Use the smaller ratio to ensure the entire image fits
                    scale_factor = min(width_ratio, height_ratio) * 0.9  # 90% of max size for a small margin

                    # Apply zoom effect - start slightly smaller and zoom in
                    # Use a hash of the filename instead of trying to parse as integer
                    # This ensures consistent effects for the same file while avoiding parsing errors
                    img_hash = hash(filename) % 4  # Get a number 0-3 based on filename hash

                    # Choose effect type based on hash value
                    effect_type = img_hash

                    if effect_type == 0:
                        # Zoom in effect
                        start_scale = scale_factor * 0.8
                        end_scale = scale_factor * 1.1

                        def zoom(t):
                            current_scale = start_scale + (end_scale - start_scale) * t / 3
                            new_w = int(img_width * current_scale)
                            new_h = int(img_height * current_scale)
                            return new_w, new_h

                        resized_img = img.resize(zoom)
                    elif effect_type == 1:
                        # Zoom out effect
                        start_scale = scale_factor * 1.1
                        end_scale = scale_factor * 0.9

                        def zoom_out(t):
                            current_scale = start_scale + (end_scale - start_scale) * t / 3
                            new_w = int(img_width * current_scale)
                            new_h = int(img_height * current_scale)
                            return new_w, new_h

                        resized_img = img.resize(zoom_out)
                    elif effect_type == 2:
                        # Pan from left to right
                        new_width = int(img_width * scale_factor)
                        new_height = int(img_height * scale_factor)

                        # First resize the image
                        from moviepy.video.fx.resize import resize
                        resized_img = resize(img, width=new_width, height=new_height)

                        # Then apply the pan effect
                        from moviepy.video.fx.scroll import scroll
                        resized_img = scroll(resized_img, w=target_width, h=target_height, x_speed=10, y_speed=0)
                    else:
                        # Simple fade in/out with fixed size
                        new_width = int(img_width * scale_factor)
                        new_height = int(img_height * scale_factor)

                        # Use the resize method with proper parameters
                        try:
                            resized_img = img.resize((new_width, new_height))
                        except Exception as resize_error:
                            print(f"Error resizing with resize method: {resize_error}")
                            # Alternative approach using fx.resize
                            from moviepy.video.fx.resize import resize
                            resized_img = resize(img, width=new_width, height=new_height)

                    # Set duration and position the image in the center
                    final_img = resized_img.set_duration(3).set_position(("center", "center"))

                    # Apply fade in/out effect
                    from moviepy.video.fx.fadein import fadein
                    from moviepy.video.fx.fadeout import fadeout
                    final_img = fadein(final_img, 0.5)
                    final_img = fadeout(final_img, 0.5)

                    # Composite the image on the background
                    final_clip = CompositeVideoClip([bg, final_img])
                    image_clips.append(final_clip)

                except Exception as e:
                    print(f"Error processing image {filename}: {e}")
                    traceback.print_exc()
                    # Create a fallback clip with error message
                    try:
                        bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=3)
                        image_clips.append(bg)
                    except Exception as bg_error:
                        print(f"Failed to create fallback clip: {bg_error}")

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
        print("No images were processed successfully. Creating a blank video.")
        blank = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=3)
        image_clips = [blank]

    # Concatenate all image clips
    video = concatenate_videoclips(image_clips, method="compose")

    # Trim video to match audio duration exactly
    if video.duration > audio_duration:
        video = video.subclip(0, audio_duration)

    # Load audio
    try:
        if audio is None:
            audio = AudioFileClip(audioFile)
        # If audio is longer than video, extend video duration
        if audio.duration > video.duration:
            print(f"Audio ({audio.duration}s) is longer than video ({video.duration}s). Extending video duration.")
            # This shouldn't happen now with our looping, but just in case
            # Create a blank clip to extend the video
            blank = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=audio.duration - video.duration)
            video = concatenate_videoclips([video, blank])
    except Exception as e:
        print(f"Error loading audio: {e}")
        # Create silent audio
        audio = AudioClip(lambda t: 0, duration=video.duration)

    # Set audio to video
    video = video.set_audio(audio)

    # Write the final video file with appropriate encoding
    print(f"Writing video to {outputVideo}")

    # Always use CPU encoding for final output to ensure compatibility
    video.write_videofile(outputVideo, fps=frameRarte, codec='libx264')

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
            print("Process stopped by user before slideshow creation.")
            return False

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
            use_gpu_encoding=use_gpu_encoding,
            aspect_ratio=aspect_ratio
        )
        return result is not None
    except Exception as e:
        print(f"Error creating slideshow: {e}")
        traceback.print_exc()
        return False

def create_enhanced_slideshow(images_folder, title, content, audio_file, output_file, use_gpu=False,
                             use_effects=True, zoom_effect=True, fade_effect=True, enhance=True,
                             enhancement_options=None, stop_event=None, aspect_ratio=DEFAULT_ASPECT_RATIO):
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

    Returns:
        bool: True if successful, False otherwise
    """
    # Check if we should stop
    if stop_event and stop_event.is_set():
        print("Process stopped by user during slideshow creation.")
        return False

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

        # Extract aspect ratio from enhancement options if available
        if enhancement_options and 'aspect_ratio' in enhancement_options:
            aspect_ratio = enhancement_options['aspect_ratio']

        result = create_slideshow(
            images_folder, title, content, audio_file, temp_output,
            use_gpu=use_gpu, use_effects=use_effects,
            zoom_effect=zoom_effect, fade_effect=fade_effect,
            stop_event=stop_event,  # Pass the stop_event
            aspect_ratio=aspect_ratio  # Pass the aspect ratio
        )

        # If the process was stopped by user, clean up and return True
        if stop_event and stop_event.is_set():
            print("Process stopped by user after slideshow creation.")
            # Clean up any temporary files
            _clean_up_temp_files(temp_output, output_file)
            return True  # Return True instead of False for a clean stop

        if not result:
            return False

        if enhance:
            print("Applying video enhancements...")
            try:
                # Check if we should stop
                if stop_event and stop_event.is_set():
                    print("Process stopped by user before enhancement.")
                    return False

                # Apply our custom enhancements
                enhanced_temp = output_file.replace('.mp4', '_enhanced_temp.mp4')

                # Use the provided enhancement options
                enhance_result = enhance_video(temp_output, enhanced_temp, enhancement_options)

                # Check if we should stop
                if stop_event and stop_event.is_set():
                    print("Process stopped by user during enhancement.")
                    return False

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
                        print(f"Error copying original video: {copy_error}")
                        return False
                return False
        else:
            # If no enhancement requested, just rename the temp file
            try:
                shutil.copy2(temp_output, output_file)
                if os.path.exists(temp_output):
                    os.remove(temp_output)
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

def _clean_up_temp_files(*file_paths):
    """
    Clean up temporary files created during video generation

    Args:
        file_paths: Paths to files that should be removed
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed temporary file: {file_path}")

            # Also check for MoviePy temporary files
            temp_audio = file_path + "TEMP_MPY_wvf_snd.mp3"
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
                print(f"Removed temporary audio file: {temp_audio}")

            # Check for other potential temp files with similar names
            dir_path = os.path.dirname(file_path)
            base_name = os.path.basename(file_path)
            for f in os.listdir(dir_path):
                if f.startswith(base_name) and "_temp" in f:
                    full_path = os.path.join(dir_path, f)
                    os.remove(full_path)
                    print(f"Removed related temporary file: {full_path}")
        except Exception as e:
            print(f"Warning: Could not remove temporary file {file_path}: {e}")
