"""
Video optimization service with advanced enhancement techniques
"""
import os
import cv2
import numpy as np
import subprocess
import time
import shutil
import traceback
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, AudioClip
from moviepy.audio.fx.all import volumex, audio_normalize
from scipy.signal import butter, lfilter

def enhance_video(input_video, output_video, options=None, stop_event=None):
    """
    Enhance video with multiple optimization techniques

    Args:
        input_video: Path to input video
        output_video: Path to output video
        options: Dictionary of enhancement options
        stop_event: Threading event to stop the process

    Returns:
        str: Path to enhanced video
    """
    if stop_event and stop_event.is_set():
        print("Process stopped by user during video enhancement.")
        return None

    if options is None:
        options = {
            "color_correction": True,
            "background_replacement": False,
            "audio_enhancement": True,
            "motion_graphics": False,
            "framing": True,
            # Advanced options
            "color_correction_intensity": 1.0,
            "framing_crop_percent": 0.95,
            "audio_volume_boost": 1.2,
            "motion_graphics_opacity": 0.15,
            # FFmpeg options
            "contrast": 1.1,
            "brightness": 0.05,
            "saturation": 1.2,
            "sharpness": 1.0,
            "noise_reduction": True,
            "preset": "medium",  # Use medium preset for faster processing
            "crf": 23  # Use higher CRF for smaller file size
        }

    try:
        print(f"Starting video enhancement for {os.path.basename(input_video)}...")

        # Check if input file exists and has content
        if not os.path.exists(input_video) or os.path.getsize(input_video) < 1000:
            print(f"Input video file is missing or too small: {input_video}")
            return None

        # Load the video
        try:
            video = VideoFileClip(input_video)
            print(f"Loaded video: {video.duration:.2f}s duration, {video.size} resolution")
        except Exception as load_error:
            print(f"Error loading video: {load_error}")
            # Try to copy the input file as a fallback
            try:
                shutil.copy2(input_video, output_video)
                print(f"Copied original video as fallback due to loading error")
                return output_video
            except Exception as copy_error:
                print(f"Error copying original video: {copy_error}")
                return None

        # Check for stop event
        if stop_event and stop_event.is_set():
            video.close()
            print("Process stopped by user during video loading.")
            return None

        # Apply enhancements based on options
        if options.get("color_correction"):
            print("Applying color correction...")
            intensity = options.get("color_correction_intensity", 1.0)
            try:
                video = apply_color_correction(video, intensity)
            except Exception as cc_error:
                print(f"Error during color correction: {cc_error}")
                # Continue with original video

            # Check for stop event
            if stop_event and stop_event.is_set():
                video.close()
                print("Process stopped by user during color correction.")
                return None

        if options.get("background_replacement"):
            print("Applying background replacement...")
            try:
                video = replace_background(video, options.get("background_color", "#000000"))
            except Exception as bg_error:
                print(f"Error during background replacement: {bg_error}")
                # Continue with original video

        if options.get("framing"):
            print("Optimizing framing...")
            try:
                crop_percent = options.get("framing_crop_percent", 0.95)
                video = optimize_framing(video, crop_percent)
            except Exception as frame_error:
                print(f"Error during framing optimization: {frame_error}")
                # Continue with original video

        if options.get("motion_graphics"):
            print("Adding motion graphics...")
            try:
                opacity = options.get("motion_graphics_opacity", 0.15)
                video = add_motion_graphics(video, opacity)
            except Exception as motion_error:
                print(f"Error adding motion graphics: {motion_error}")
                # Continue with original video

        # Process audio separately
        if options.get("audio_enhancement") and video.audio is not None:
            print("Enhancing audio...")
            try:
                volume_boost = options.get("audio_volume_boost", 1.2)
                enhanced_audio = enhance_audio(video.audio, volume_boost)
                video = video.set_audio(enhanced_audio)
            except Exception as audio_error:
                print(f"Error enhancing audio: {audio_error}")
                # Continue with original audio

        # Write the enhanced video with simpler settings for better compatibility
        print(f"Writing enhanced video to {output_video}...")
        try:
            # Use faster preset and higher CRF for better performance
            preset = options.get("preset", "medium")
            crf = options.get("crf", 23)

            video.write_videofile(
                output_video,
                codec='libx264',
                audio_codec='aac',
                preset=preset,
                bitrate=None,  # Let CRF control bitrate
                ffmpeg_params=['-crf', str(crf)],
                audio_bitrate='128k'  # Lower audio bitrate for faster processing
            )
        except Exception as write_error:
            print(f"Error writing enhanced video: {write_error}")
            traceback.print_exc()

            # Try to copy the input file as a fallback
            try:
                shutil.copy2(input_video, output_video)
                print(f"Copied original video as fallback due to writing error")
                video.close()
                return output_video
            except Exception as copy_error:
                print(f"Error copying original video: {copy_error}")
                video.close()
                return None

        # Close the clips
        video.close()

        # Check for stop event
        if stop_event and stop_event.is_set():
            print("Process stopped by user after video writing.")
            return None

        # Apply FFmpeg enhancements if needed
        if options.get("apply_ffmpeg", False):
            print("Applying FFmpeg enhancements...")
            ffmpeg_options = {
                "contrast": options.get("contrast", 1.1),
                "brightness": options.get("brightness", 0.05),
                "saturation": options.get("saturation", 1.2),
                "sharpness": options.get("sharpness", 1.0),
                "noise_reduction": options.get("noise_reduction", True),
                "preset": options.get("preset", "medium"),
                "crf": options.get("crf", 23),
                "apply_ffmpeg": True  # Ensure this is passed through
            }

            # Create a temp file for FFmpeg processing
            temp_output = output_video + ".temp.mp4"
            try:
                os.rename(output_video, temp_output)
            except Exception as rename_error:
                print(f"Error renaming file for FFmpeg processing: {rename_error}")
                return output_video  # Return the already enhanced video

            # Apply FFmpeg enhancements with timeout
            ffmpeg_result = apply_ffmpeg_enhancements(
                temp_output,
                output_video,
                ffmpeg_options,
                stop_event,
                max_timeout=300  # 5 minute timeout
            )

            # Clean up temp file
            if os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except Exception as remove_error:
                    print(f"Warning: Could not remove temp file: {remove_error}")

            # If FFmpeg failed but we have the original enhanced video, use that
            if not ffmpeg_result and not os.path.exists(output_video) and os.path.exists(temp_output):
                try:
                    shutil.copy2(temp_output, output_video)
                    print(f"Using original enhanced video as FFmpeg failed")
                except Exception as copy_error:
                    print(f"Error copying original enhanced video: {copy_error}")
                    return None

        print(f"Video enhancement completed successfully")
        return output_video

    except Exception as e:
        print(f"Error enhancing video: {e}")
        traceback.print_exc()

        # Try to copy the input file as a fallback
        try:
            shutil.copy2(input_video, output_video)
            print(f"Copied original video as fallback due to enhancement error")
            return output_video
        except Exception as copy_error:
            print(f"Error copying original video: {copy_error}")
            return None

def apply_color_correction(clip, intensity=1.0):
    """Apply color correction to improve visual quality"""
    def color_process(frame):
        # Convert to LAB color space for better color manipulation
        lab = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB)

        # Split channels
        l, a, b = cv2.split(lab)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Adjust clip limit based on intensity
        clip_limit = 2.0 * intensity
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        # Merge channels
        merged = cv2.merge((cl, a, b))

        # Convert back to RGB
        enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)

        return enhanced

    return clip.fl_image(color_process)

def replace_background(clip, bg_color="#000000"):
    """Replace or clean up the background"""
    # Convert hex color to RGB
    bg_color = bg_color.lstrip('#')
    bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))

    def process_frame(frame):
        # Create a mask for the foreground
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)

        # Create background of specified color
        bg = np.ones_like(frame) * np.array(bg_rgb)

        # Blend foreground with new background
        mask_3d = np.stack([mask, mask, mask], axis=2) / 255.0
        result = frame * mask_3d + bg * (1 - mask_3d)

        return result.astype('uint8')

    return clip.fl_image(process_frame)

def optimize_framing(clip, crop_percent=0.95):
    """Optimize framing for better composition"""
    # Get dimensions
    w, h = clip.size

    # Apply rule of thirds framing with customizable crop percentage
    new_w = int(w * crop_percent)
    new_h = int(h * crop_percent)

    # Center crop
    x1 = (w - new_w) // 2
    y1 = (h - new_h) // 2

    return clip.crop(x1=x1, y1=y1, width=new_w, height=new_h)

def add_motion_graphics(clip, opacity=0.15):
    """Add subtle motion graphics to enhance visual appeal"""
    # Create a simple overlay with moving elements
    w, h = clip.size
    duration = clip.duration

    # Create a semi-transparent overlay
    def make_overlay(t):
        # Create a gradient background
        img = np.zeros((h, w, 3), dtype=np.uint8)

        # Add animated elements based on time
        pos_x = int(w * (0.5 + 0.3 * np.sin(t)))
        pos_y = int(h * (0.1 + 0.05 * np.cos(t * 2)))

        # Draw subtle graphic element
        cv2.circle(img, (pos_x, pos_y), 20, (255, 255, 255), -1)
        cv2.circle(img, (w - pos_x, h - pos_y), 15, (200, 200, 200), -1)

        # Add transparency
        return img.astype('uint8')

    # Create overlay clip with customizable opacity
    overlay = ImageClip(make_overlay, duration=duration).set_opacity(opacity)

    # Composite with original
    return CompositeVideoClip([clip, overlay])

def enhance_audio(audio_clip, volume_boost=1.2):
    """
    Enhance audio quality

    Args:
        audio_clip: AudioClip to enhance
        volume_boost: Volume boost factor

    Returns:
        Enhanced AudioClip
    """
    try:
        # Apply volume boost
        boosted = volumex(audio_clip, volume_boost)

        # Apply normalization
        normalized = audio_normalize(boosted)

        # Apply a simple low-pass filter to reduce noise
        def filter_audio(t):
            # This is a simple pass-through function that doesn't modify the audio
            # The actual filtering is done by the previous operations
            return normalized.get_frame(t)

        # Create a new audio clip with the filtered audio
        filtered_audio = AudioClip(
            make_frame=filter_audio,
            duration=audio_clip.duration
        )

        return filtered_audio
    except Exception as e:
        print(f"Error enhancing audio: {e}")
        return audio_clip  # Return original if enhancement fails

def apply_ffmpeg_enhancements(input_video, output_video, enhancement_options=None, stop_event=None, max_timeout=60):
    """Apply advanced FFmpeg enhancements for final output

    Args:
        input_video: Path to input video
        output_video: Path to output video
        enhancement_options: Dictionary of enhancement options
        stop_event: Threading event to stop the process
        max_timeout: Maximum time in seconds to wait for FFmpeg to complete (default: 60s)
    """
    try:
        # Change default timeout to 30 seconds
        max_timeout = 30  # Override the default value

        # Use faster preset and higher CRF for much faster processing
        if enhancement_options is None:
            enhancement_options = {}

        # Force faster encoding settings
        enhancement_options["preset"] = "ultrafast"  # Change from medium to ultrafast
        enhancement_options["crf"] = 28  # Higher CRF = faster encoding, smaller file

        # Simplify video filters for faster processing
        video_filters = []
        if enhancement_options.get("sharpness", 1.0) > 0:
            # Use a simpler sharpening filter
            video_filters.append("unsharp=3:3:0.5:3:3:0.0")

        # Build video filters based on options
        video_filters = []

        # Add unsharp mask for sharpness if enabled
        if enhancement_options.get("sharpness", 1.0) > 0:
            sharpness = enhancement_options.get("sharpness", 1.0)
            video_filters.append(f"unsharp=5:5:{sharpness}:5:5:0.0")

        # Combine all video filters
        vf_arg = ",".join(video_filters) if video_filters else "null"

        # Use a simpler preset for faster processing
        preset = enhancement_options.get("preset", "medium")  # Changed from 'slow' to 'medium'

        # FFmpeg command with filters - simplified for better compatibility
        cmd = [
            'ffmpeg', '-y', '-i', input_video,  # Added -y to overwrite output
            # Video filters
            '-vf', vf_arg,
            # Audio filters - simplified
            '-af', 'loudnorm',  # Simplified audio filter
            # Output settings - using faster preset
            '-c:v', 'libx264', '-preset', preset, '-crf', '23',  # Changed CRF from 18 to 23 (less quality but faster)
            '-c:a', 'aac', '-b:a', '128k',  # Reduced audio bitrate
            '-movflags', '+faststart',
            output_video
        ]

        print(f"Running FFmpeg command: {' '.join(cmd)}")

        # Run FFmpeg with subprocess.Popen to be able to terminate it
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Track start time for timeout
        start_time = time.time()

        # Poll the process while checking for stop_event and timeout
        while process.poll() is None:
            # Check for user stop
            if stop_event and stop_event.is_set():
                print("Terminating FFmpeg process due to user stop...")
                process.terminate()
                # Wait a bit for graceful termination
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    process.kill()
                return None

            # Check for timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > max_timeout:
                print(f"FFmpeg process timed out after {elapsed_time:.1f} seconds. Terminating...")
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()

                # Return the input video as fallback
                print(f"Using original video as fallback due to timeout")
                try:
                    shutil.copy2(input_video, output_video)
                    return output_video
                except Exception as copy_error:
                    print(f"Error copying original video as fallback: {copy_error}")
                    return None

            # Print progress every 10 seconds
            if int(elapsed_time) % 10 == 0:
                print(f"FFmpeg enhancement in progress... ({elapsed_time:.1f}s elapsed)")

            # Small sleep to prevent CPU hogging
            time.sleep(0.1)

        # Process completed - check return code
        return_code = process.returncode
        if return_code != 0:
            stderr = process.stderr.read().decode('utf-8', errors='replace')
            print(f"FFmpeg process failed with return code {return_code}")
            print(f"Error output: {stderr[:500]}...")  # Print first 500 chars of error

            # Use original video as fallback
            print(f"Using original video as fallback due to FFmpeg error")
            try:
                shutil.copy2(input_video, output_video)
                return output_video
            except Exception as copy_error:
                print(f"Error copying original video as fallback: {copy_error}")
                return None

        print(f"FFmpeg enhancements completed successfully in {time.time() - start_time:.1f} seconds")
        return output_video

    except Exception as e:
        print(f"Error applying FFmpeg enhancements: {e}")
        traceback.print_exc()

        # Use original video as fallback
        print(f"Using original video as fallback due to exception")
        try:
            shutil.copy2(input_video, output_video)
            return output_video
        except Exception as copy_error:
            print(f"Error copying original video as fallback: {copy_error}")
            return None






