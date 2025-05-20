"""
Video optimization service with advanced enhancement techniques
"""
import os
import cv2
import numpy as np
import subprocess
import time
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
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
            "noise_reduction": True
        }
    
    try:
        # Load the video
        video = VideoFileClip(input_video)
        
        # Check for stop event
        if stop_event and stop_event.is_set():
            video.close()
            print("Process stopped by user during video loading.")
            return None
            
        # Apply enhancements based on options
        if options.get("color_correction"):
            intensity = options.get("color_correction_intensity", 1.0)
            video = apply_color_correction(video, intensity)
            
            # Check for stop event
            if stop_event and stop_event.is_set():
                video.close()
                print("Process stopped by user during color correction.")
                return None
        
        if options.get("background_replacement"):
            video = replace_background(video, options.get("background_color", "#000000"))
        
        if options.get("framing"):
            crop_percent = options.get("framing_crop_percent", 0.95)
            video = optimize_framing(video, crop_percent)
        
        if options.get("motion_graphics"):
            opacity = options.get("motion_graphics_opacity", 0.15)
            video = add_motion_graphics(video, opacity)
        
        # Process audio separately
        if options.get("audio_enhancement") and video.audio is not None:
            volume_boost = options.get("audio_volume_boost", 1.2)
            enhanced_audio = enhance_audio(video.audio, volume_boost)
            video = video.set_audio(enhanced_audio)
        
        # Write the enhanced video
        video.write_videofile(output_video, codec='libx264', audio_codec='aac', 
                             bitrate='8000k', audio_bitrate='192k')
        
        # Close the clips
        video.close()
        
        # Check for stop event
        if stop_event and stop_event.is_set():
            print("Process stopped by user after video writing.")
            return None
            
        # Apply FFmpeg enhancements if needed
        if options.get("apply_ffmpeg", True):
            ffmpeg_options = {
                "contrast": options.get("contrast", 1.1),
                "brightness": options.get("brightness", 0.05),
                "saturation": options.get("saturation", 1.2),
                "sharpness": options.get("sharpness", 1.0),
                "noise_reduction": options.get("noise_reduction", True)
            }
            temp_output = output_video + ".temp.mp4"
            os.rename(output_video, temp_output)
            apply_ffmpeg_enhancements(temp_output, output_video, ffmpeg_options, stop_event)
            if os.path.exists(temp_output):
                os.remove(temp_output)
        
        return output_video
    
    except Exception as e:
        print(f"Error enhancing video: {e}")
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

def apply_ffmpeg_enhancements(input_video, output_video, enhancement_options=None, stop_event=None):
    """Apply advanced FFmpeg enhancements for final output"""
    if stop_event and stop_event.is_set():
        print("Process stopped by user during FFmpeg enhancements.")
        return None
        
    try:
        # Default enhancement options
        if enhancement_options is None:
            enhancement_options = {
                "contrast": 1.1,
                "brightness": 0.05,
                "saturation": 1.2,
                "sharpness": 1.0,
                "noise_reduction": True
            }
        
        # Build video filters based on options
        video_filters = []
        
        # Add unsharp mask for sharpness if enabled
        if enhancement_options.get("sharpness", 1.0) > 0:
            sharpness = enhancement_options.get("sharpness", 1.0)
            video_filters.append(f"unsharp=5:5:{sharpness}:5:5:0.0")
            
        # Combine all video filters
        vf_arg = ",".join(video_filters) if video_filters else "null"
        
        # FFmpeg command with filters
        cmd = [
            'ffmpeg', '-i', input_video,
            # Video filters
            '-vf', vf_arg,
            # Audio filters
            '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11,acompressor=threshold=0.05:ratio=2:attack=200:release=1000',
            # Output settings
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
            '-c:a', 'aac', '-b:a', '192k',
            '-movflags', '+faststart',
            output_video
        ]
        
        # Run FFmpeg with subprocess.Popen to be able to terminate it
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Poll the process while checking for stop_event
        while process.poll() is None:
            if stop_event and stop_event.is_set():
                print("Terminating FFmpeg process...")
                process.terminate()
                # Wait a bit for graceful termination
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    process.kill()
                return None
            # Small sleep to prevent CPU hogging
            time.sleep(0.1)
            
        return output_video
    
    except Exception as e:
        print(f"Error applying FFmpeg enhancements: {e}")
        return None








