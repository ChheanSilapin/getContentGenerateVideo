"""
Video slideshow creation functionality
Extracted from video_service.py for better organization
Optimized with FFmpeg-based approach for better performance
"""
import os
import sys
import shutil
import traceback
import tempfile
import subprocess
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from moviepy.editor import (
    ImageClip, ColorClip, AudioFileClip, VideoFileClip,
    CompositeAudioClip, concatenate_videoclips, CompositeVideoClip
)

# Import centralized utility functions
from utils.helpers import (
    configure_ffmpeg_for_moviepy, setup_temp_directory_for_bundled_exe,
    cleanup_temp_files, get_ffmpeg_path
)
# video_utils removed for performance optimization
from config import DEFAULT_ASPECT_RATIO


def _analyze_content_timing_for_images(audio_timing_result, image_count, actual_audio_duration=None):
    """
    Analyze Whisper segments to create content-aware timing for images

    Args:
        audio_timing_result: AudioTimingResult with Whisper segments
        image_count: Number of images to distribute timing across
        actual_audio_duration: Actual audio file duration (to prevent cutoff issues)

    Returns:
        List of timing data for each image: [{'start': float, 'duration': float, 'content': str}, ...]
    """
    if not audio_timing_result or not audio_timing_result.whisper_segments:
        print("⚠️ No Whisper timing data available, falling back to equal distribution")
        return None

    segments = audio_timing_result.whisper_segments
    if len(segments) == 0:
        print("⚠️ No Whisper segments found, falling back to equal distribution")
        return None

    # Calculate total audio duration - use actual audio duration to prevent cutoff
    # Whisper segments might not extend to the very end of audio (silence at end)
    whisper_end_time = segments[-1]['end'] if segments else 0
    total_duration = actual_audio_duration if actual_audio_duration else whisper_end_time

    # Debug logging to identify timing mismatches
    if actual_audio_duration and abs(whisper_end_time - actual_audio_duration) > 0.1:
        print(f"⚠️ Timing mismatch detected: Whisper ends at {whisper_end_time:.2f}s, actual audio is {actual_audio_duration:.2f}s")
        print(f"   Using actual audio duration to prevent black screen at end")

    # Method 1: Distribute segments evenly among images with CONTINUOUS COVERAGE
    if len(segments) >= image_count:
        # Use full audio duration for continuous coverage (no gaps!)
        audio_start = segments[0]['start']
        audio_end = total_duration
        full_duration = audio_end - audio_start
        duration_per_image = full_duration / image_count

        segments_per_image = len(segments) // image_count
        remainder_segments = len(segments) % image_count

        image_timings = []
        segment_idx = 0

        for i in range(image_count):
            # Calculate continuous timing (no gaps)
            start_time = audio_start + (i * duration_per_image)
            end_time = start_time + duration_per_image

            # Ensure last image goes exactly to audio end
            if i == image_count - 1:
                end_time = audio_end
                duration_per_image = end_time - start_time

            # Calculate how many segments this image gets for content mapping
            segments_for_this_image = segments_per_image
            if i < remainder_segments:
                segments_for_this_image += 1

            # Get the segments for content mapping
            start_segment = segment_idx
            end_segment = segment_idx + segments_for_this_image

            # Collect content text for this image
            content_parts = []
            for seg_idx in range(start_segment, min(end_segment, len(segments))):
                content_parts.append(segments[seg_idx]['text'].strip())

            # If no content mapped, find content by time overlap
            if not content_parts:
                mid_time = (start_time + end_time) / 2
                for segment in segments:
                    if segment['start'] <= mid_time <= segment['end']:
                        content_parts.append(segment['text'].strip())
                        break

                if not content_parts:
                    content_parts.append(f"Content section {i+1}")

            image_timings.append({
                'start': start_time,
                'duration': end_time - start_time,
                'content': ' '.join(content_parts)
            })

            segment_idx = end_segment

        # Final verification: ensure perfect coverage
        calculated_end = image_timings[-1]['start'] + image_timings[-1]['duration']

        if abs(calculated_end - total_duration) > 0.01:
            image_timings[-1]['duration'] = total_duration - image_timings[-1]['start']

        return image_timings

    else:
        # Method 2: When we have fewer segments than images, distribute images across full audio duration
        # Use full audio duration to ensure no content is cut off
        audio_start = segments[0]['start'] if segments else 0
        audio_end = total_duration  # Use actual audio duration, not just last segment end
        full_duration = audio_end - audio_start

        # Calculate equal distribution across full duration
        duration_per_image = full_duration / image_count

        image_timings = []

        # Create segment content mapping for reference
        segment_content = {}
        for segment in segments:
            for t in range(int(segment['start']), int(segment['end']) + 1):
                segment_content[t] = segment['text'].strip()

        for i in range(image_count):
            start_time = audio_start + (i * duration_per_image)
            end_time = start_time + duration_per_image

            # Ensure last image goes to the very end of audio
            if i == image_count - 1:
                end_time = audio_end
                duration_per_image = end_time - start_time

            # Find the most relevant content for this time range
            mid_time = int((start_time + end_time) / 2)
            content = segment_content.get(mid_time, f"Content section {i+1}")

            # If no content found, try to find nearest segment
            if content == f"Content section {i+1}":
                for segment in segments:
                    if segment['start'] <= mid_time <= segment['end']:
                        content = segment['text'].strip()
                        break

            image_timings.append({
                'start': start_time,
                'duration': end_time - start_time,
                'content': content
            })

        # Verify total duration matches audio
        calculated_total = image_timings[-1]['start'] + image_timings[-1]['duration']

        if abs(calculated_total - audio_end) > 0.1:
            image_timings[-1]['duration'] = audio_end - image_timings[-1]['start']

        return image_timings


def _create_content_aware_slideshow_ffmpeg(processed_images, content_timings, audio_file, output_file,
                                          target_width, target_height, use_effects, zoom_effect, fade_effect, temp_dir):
    """
    Create slideshow with content-aware timing using FFmpeg

    Args:
        processed_images: List of processed image file paths
        content_timings: List of timing data for each image
        audio_file: Path to audio file
        output_file: Path to output video file
        target_width, target_height: Video dimensions
        use_effects, zoom_effect, fade_effect: Effect settings
        temp_dir: Temporary directory for processing

    Returns:
        bool: Success status
    """
    try:
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path:
            print("❌ FFmpeg not found for content-aware slideshow")
            return False



        # Create individual video clips for each image with custom duration
        temp_clips = []
        for i, (img_path, timing) in enumerate(zip(processed_images, content_timings)):
            clip_output = os.path.join(temp_dir, f"clip_{i:03d}.mp4")
            temp_clips.append(clip_output)

            # Build video filters
            filters = []

            # Scale and fit
            filters.append(f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease')
            filters.append(f'pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black')

            # Add zoom effect if requested
            if use_effects and zoom_effect:
                filters.append('scale=iw*1.05:ih*1.05,crop=iw/1.05:ih/1.05')

            # Add fade effect if requested and duration is long enough
            if use_effects and fade_effect and timing['duration'] > 1.5:
                fade_duration = min(0.3, timing['duration'] * 0.15)
                filters.append(f'fade=in:0:{int(fade_duration*24)}')
                filters.append(f'fade=out:{int((timing["duration"]-fade_duration)*24)}:{int(fade_duration*24)}')

            # Create individual clip with specific duration
            clip_cmd = [
                ffmpeg_path,
                '-loop', '1',
                '-i', img_path,
                '-t', str(timing['duration']),  # Custom duration for this image
                '-vf', ','.join(filters),
                '-r', '24',  # Standard frame rate
                '-pix_fmt', 'yuv420p',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-y',  # Overwrite output
                clip_output
            ]

            print(f"📸 Creating clip {i+1}: {timing['duration']:.2f}s - {timing['content'][:50]}...")

            result = subprocess.run(clip_cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                print(f"❌ Failed to create clip {i+1}: {result.stderr}")
                return False

        # Create concat file for FFmpeg
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for clip in temp_clips:
                # Use forward slashes for FFmpeg compatibility
                clip_path = clip.replace('\\', '/')
                f.write(f"file '{clip_path}'\n")



        # Concatenate all clips and add audio
        final_cmd = [
            ffmpeg_path,
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-i', audio_file,
            '-c:v', 'copy',  # Copy video (already encoded)
            '-c:a', 'aac',
            '-shortest',  # Match shortest stream (video or audio)
            '-avoid_negative_ts', 'make_zero',
            '-y',  # Overwrite output
            output_file
        ]

        result = subprocess.run(final_cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"❌ Failed to concatenate clips: {result.stderr}")
            return False


        return True

    except Exception as e:
        print(f"❌ Error in content-aware slideshow creation: {e}")
        traceback.print_exc()
        return False


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

def create_slideshow_ffmpeg(images_folder, audio_file, output_file,
                           use_effects=True, zoom_effect=True, fade_effect=True,
                           aspect_ratio=DEFAULT_ASPECT_RATIO, fit_method="cover",
                           stop_event=None, audio_timing_result=None):
    """
    Create slideshow using FFmpeg for optimal performance

    Args:
        images_folder: Folder containing images OR list of image file paths
        audio_file: Path to audio file
        output_file: Path to output video file
        use_effects: Whether to apply visual effects
        zoom_effect: Whether to apply zoom effect to images
        fade_effect: Whether to apply fade transitions
        aspect_ratio: Video aspect ratio (width, height)
        fit_method: How to fit images ("cover", "contain", "stretch")
        stop_event: Threading event to stop the process

    Returns:
        bool: True if successful, False otherwise
    """
    try:


        # Get FFmpeg path
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path:
            print("FFmpeg not found, falling back to MoviePy")
            return False

        # Get image files
        if isinstance(images_folder, list):
            image_files = images_folder
        else:
            image_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.webp']:
                import glob
                image_files.extend(glob.glob(os.path.join(images_folder, ext)))
                image_files.extend(glob.glob(os.path.join(images_folder, ext.upper())))
            image_files.sort()

        if not image_files:
            print("No image files found")
            return False

        # Get audio duration
        try:
            audio_clip = AudioFileClip(audio_file)
            audio_duration = audio_clip.duration
            audio_clip.close()
        except Exception as e:
            print(f"Error reading audio file: {e}")
            return False

        # Calculate timing - use content-aware timing if available
        content_timings = None
        if audio_timing_result:

            content_timings = _analyze_content_timing_for_images(audio_timing_result, len(image_files), audio_duration)

        if content_timings:
            pass
        else:
            duration_per_image = audio_duration / len(image_files) if len(image_files) > 0 else 0

        # Check if we should stop
        if stop_event and stop_event.is_set():
            return False

        # Create temporary directory for processed images
        temp_dir = tempfile.mkdtemp(prefix="slideshow_")
        processed_images = []

        try:
            target_width, target_height = aspect_ratio

            # Process images with PIL (faster than MoviePy for static processing)
            for i, img_path in enumerate(image_files):
                if stop_event and stop_event.is_set():
                    return False

                try:
                    # Load and process image
                    pil_img = Image.open(img_path)
                    processed_img = _process_image_for_ffmpeg(
                        pil_img, target_width, target_height, fit_method
                    )

                    # Save processed image
                    processed_path = os.path.join(temp_dir, f"img_{i:06d}.jpg")
                    processed_img.save(processed_path, "JPEG", quality=95)
                    processed_images.append(processed_path)

                except Exception as e:
                    print(f"Error processing image {img_path}: {e}")
                    # Create black placeholder
                    black_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                    processed_path = os.path.join(temp_dir, f"img_{i:06d}.jpg")
                    black_img.save(processed_path, "JPEG", quality=95)
                    processed_images.append(processed_path)

            if not processed_images:
                return False

            # Build FFmpeg command for slideshow creation
            if content_timings:
                # Content-aware timing: Create slideshow with custom timing per image

                return _create_content_aware_slideshow_ffmpeg(
                    processed_images, content_timings, audio_file, output_file,
                    target_width, target_height, use_effects, zoom_effect, fade_effect, temp_dir
                )

            else:
                # Traditional equal timing: use standard approach
                cmd = [ffmpeg_path]
                cmd.extend([
                    '-framerate', f'{1/duration_per_image}',  # Frame rate based on duration
                    '-i', os.path.join(temp_dir, 'img_%06d.jpg'),
                    '-i', audio_file  # Audio input
                ])

            # Video filters for effects
            filters = []

            # Scale and fit
            if fit_method == "cover":
                filters.append(f'scale={target_width}:{target_height}:force_original_aspect_ratio=increase')
                filters.append(f'crop={target_width}:{target_height}')
            elif fit_method == "contain":
                filters.append(f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease')
                filters.append(f'pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black')
            else:  # stretch
                filters.append(f'scale={target_width}:{target_height}')

            # Add zoom effect if requested
            if use_effects and zoom_effect:
                # Subtle zoom effect using scale filter
                filters.append('scale=iw*1.1:ih*1.1,crop=iw/1.1:ih/1.1')

            # Add fade effect if requested
            if use_effects and fade_effect and duration_per_image > 1.5:
                fade_duration = min(0.3, duration_per_image * 0.15)
                filters.append(f'fade=in:0:{int(fade_duration*25)}:alpha=1')
                filters.append(f'fade=out:{int((duration_per_image-fade_duration)*25)}:{int(fade_duration*25)}:alpha=1')

            # Apply filters
            if filters:
                cmd.extend(['-vf', ','.join(filters)])

            # Output settings
            cmd.extend([
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-pix_fmt', 'yuv420p',
                '-crf', '23',
                '-preset', 'medium',
                '-shortest',  # Stop when shortest input ends
                '-avoid_negative_ts', 'make_zero',
                '-y',  # Overwrite output
                output_file
            ])

            # For bundled executables, use faster settings
            if getattr(sys, 'frozen', False):
                # Replace preset and crf for faster encoding
                cmd[cmd.index('-preset')+1] = 'ultrafast'
                cmd[cmd.index('-crf')+1] = '28'


            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                return False


            return True

        finally:
            # Clean up temporary files
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not clean up temp directory: {e}")

    except Exception as e:
        print(f"Error in FFmpeg slideshow creation: {e}")
        return False

def _process_image_for_ffmpeg(pil_img, target_width, target_height, fit_method="cover"):
    """
    Process image for FFmpeg slideshow (simplified version without MoviePy)
    """
    try:
        orig_width, orig_height = pil_img.size
        orig_ratio = orig_width / orig_height
        target_ratio = target_width / target_height

        if fit_method == "cover":
            # Cover: crop to fill frame
            if orig_ratio > target_ratio:
                # Image is wider - crop sides
                new_height = target_height
                new_width = int(new_height * orig_ratio)
                resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                x_offset = (new_width - target_width) // 2
                final_img = resized_img.crop((x_offset, 0, x_offset + target_width, target_height))
            else:
                # Image is taller - crop top/bottom
                new_width = target_width
                new_height = int(new_width / orig_ratio)
                resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                y_offset = (new_height - target_height) // 2
                final_img = resized_img.crop((0, y_offset, target_width, y_offset + target_height))

        elif fit_method == "contain":
            # Contain: fit with blurred background
            if orig_ratio > target_ratio:
                new_width = target_width
                new_height = int(new_width / orig_ratio)
                resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)

                # Create blurred background
                bg_img = pil_img.resize((target_width, target_height), Image.LANCZOS)
                bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=20))
                enhancer = ImageEnhance.Brightness(bg_img)
                bg_img = enhancer.enhance(0.3)

                y_offset = (target_height - new_height) // 2
                bg_img.paste(resized_img, (0, y_offset))
                final_img = bg_img
            else:
                new_height = target_height
                new_width = int(new_height * orig_ratio)
                resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)

                # Create blurred background
                bg_img = pil_img.resize((target_width, target_height), Image.LANCZOS)
                bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=20))
                enhancer = ImageEnhance.Brightness(bg_img)
                bg_img = enhancer.enhance(0.3)

                x_offset = (target_width - new_width) // 2
                bg_img.paste(resized_img, (x_offset, 0))
                final_img = bg_img

        else:  # stretch
            final_img = pil_img.resize((target_width, target_height), Image.LANCZOS)

        return final_img

    except Exception as e:
        print(f"Error processing image: {e}")
        # Return black image as fallback
        return Image.new('RGB', (target_width, target_height), (0, 0, 0))

def create_slideshow(images_folder, title, content, audio_file, output_file,
                  use_gpu=False, use_effects=True, zoom_effect=True, fade_effect=True,
                  enhance=False, enhancement_options=None, stop_event=None,
                  aspect_ratio=DEFAULT_ASPECT_RATIO, ffmpeg_timeout=30, fit_method="cover",
                  audio_timing_result=None):
    """
    Create a slideshow video from images with performance optimization

    First attempts FFmpeg-based creation for optimal performance,
    falls back to MoviePy if FFmpeg is not available or fails.

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
        fit_method: How to fit images ("cover", "contain", "stretch")

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Try FFmpeg-based slideshow creation first for optimal performance

        ffmpeg_success = create_slideshow_ffmpeg(
            images_folder, audio_file, output_file,
            use_effects=use_effects, zoom_effect=zoom_effect, fade_effect=fade_effect,
            aspect_ratio=aspect_ratio, fit_method=fit_method, stop_event=stop_event,
            audio_timing_result=audio_timing_result
        )

        if ffmpeg_success:


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

            return True

        # Fall back to MoviePy if FFmpeg failed

        return _create_slideshow_moviepy(images_folder, title, content, audio_file, output_file,
                                       use_gpu, use_effects, zoom_effect, fade_effect,
                                       enhance, enhancement_options, stop_event,
                                       aspect_ratio, ffmpeg_timeout, fit_method)

    except Exception as e:
        print(f"Error in slideshow creation: {e}")
        traceback.print_exc()
        return False

def _create_slideshow_moviepy(images_folder, title, content, audio_file, output_file,
                            use_gpu=False, use_effects=True, zoom_effect=True, fade_effect=True,
                            enhance=False, enhancement_options=None, stop_event=None,
                            aspect_ratio=DEFAULT_ASPECT_RATIO, ffmpeg_timeout=30, fit_method="cover"):
    """
    Original MoviePy-based slideshow creation (fallback method)
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
        if not image_files:
            print("No supported image files found")
            return False

        # Sort images by filename for consistent order
        image_files.sort()
        
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

    return create_slideshow(
        folderName, title, content, audioFile, outputVideo,
        use_gpu=use_gpu_encoding, use_effects=True, zoom_effect=True, fade_effect=True,
        enhance=False, enhancement_options=None, stop_event=stop_event,
        aspect_ratio=aspect_ratio
    )
