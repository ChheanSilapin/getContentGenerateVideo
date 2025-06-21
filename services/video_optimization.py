"""
Video Optimization Service - Unified video enhancement and performance optimization
Consolidates video quality enhancement and performance optimization features
"""
import os
import numpy as np
import subprocess
import time
import shutil
import traceback
import sys
import hashlib
from typing import Dict, List, Optional

# Make cv2 import optional for smaller bundles and better compatibility
try:
    import cv2
    CV2_AVAILABLE = True
    print("OpenCV available - enhanced video optimization enabled")
except ImportError:
    print("OpenCV not available - using basic video optimization")
    CV2_AVAILABLE = False
    cv2 = None
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip, AudioClip
from moviepy.audio.fx.all import volumex, audio_normalize

# Use centralized path management
try:
    from utils.path_manager import setup_project_paths
    # Set up all project paths at once
    setup_project_paths()
except ImportError:
    # Fallback path setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    utils_dir = os.path.join(project_root, 'utils')
    if utils_dir not in sys.path:
        sys.path.insert(0, utils_dir)

# Import FFmpeg utilities from centralized location
try:
    from utils.helpers import (
        check_ffmpeg_availability,
        configure_ffmpeg_for_moviepy, setup_temp_directory_for_bundled_exe,
        build_ffmpeg_command
    )
except ImportError:
    # Use fallback manager if available
    try:
        from utils.fallback_manager import get_helpers_with_fallback
        helpers = get_helpers_with_fallback()
        check_ffmpeg_availability = helpers.check_ffmpeg_availability
        # Import centralized functions - no need for fallback implementations
        from utils.helpers import (
            configure_ffmpeg_for_moviepy, setup_temp_directory_for_bundled_exe,
            build_ffmpeg_command
        )
    except ImportError:
        # Critical error - should not happen in production
        print("CRITICAL: Cannot import FFmpeg utilities from utils.helpers or fallback_manager")
        raise ImportError("FFmpeg utilities are required but unavailable")

def enhance_video(input_video, output_video, options=None, stop_event=None):
    """
    Enhance video quality with various improvements

    Args:
        input_video: Path to input video file
        output_video: Path to output enhanced video file
        options: Dictionary of enhancement options
        stop_event: Threading event to stop the process

    Returns:
        str: Path to enhanced video if successful, None otherwise
    """
    # Configure MoviePy for bundled executable (centralized)
    configure_ffmpeg_for_moviepy()
    setup_temp_directory_for_bundled_exe(output_video)

    # Default enhancement options
    if options is None:
        options = {
            "color_correction": True,
            "audio_enhancement": True,
            "framing": True,
            "motion_graphics": False,
            "preset": "ultrafast",
            "crf": 28
        }

    try:
        print(f"Starting video enhancement for {os.path.basename(input_video)}...")

        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user before enhancement.")
            return None

        # Load the video
        video = VideoFileClip(input_video)
        print(f"Loaded video: {video.duration:.2f}s duration, {video.size} resolution")

        # Apply color correction if enabled
        if options.get("color_correction", True):
            print("Applying color correction...")
            try:
                video = apply_color_correction(video, intensity=1.2)
            except Exception as color_error:
                print(f"Error applying color correction: {color_error}")
                # Continue without color correction

        # Check for stop event
        if stop_event and stop_event.is_set():
            print("Process stopped by user during color correction.")
            video.close()
            return None

        # Apply framing optimization if enabled
        if options.get("framing", True):
            print("Optimizing framing...")
            try:
                video = optimize_framing(video, crop_percent=0.98)
            except Exception as framing_error:
                print(f"Error optimizing framing: {framing_error}")
                # Continue without framing optimization

        # Check for stop event
        if stop_event and stop_event.is_set():
            print("Process stopped by user during framing optimization.")
            video.close()
            return None

        # Apply motion graphics if enabled
        if options.get("motion_graphics", False):
            print("Adding motion graphics...")
            try:
                video = add_motion_graphics(video, opacity=0.1)
            except Exception as motion_error:
                print(f"Error adding motion graphics: {motion_error}")
                # Continue without motion graphics

        # Check for stop event
        if stop_event and stop_event.is_set():
            print("Process stopped by user during motion graphics.")
            video.close()
            return None

        # Ensure video dimensions are even (divisible by 2) for H.264 compatibility
        if hasattr(video, 'size'):
            w, h = video.size
            if w % 2 != 0 or h % 2 != 0:
                # Adjust to even dimensions
                new_w = w if w % 2 == 0 else w - 1
                new_h = h if h % 2 == 0 else h - 1
                print(f"Enhancement: Adjusting video dimensions from {w}x{h} to {new_w}x{new_h} for H.264 compatibility")
                video = video.resize((new_w, new_h))

        # Apply audio enhancement if enabled and audio exists
        if options.get("audio_enhancement", True) and video.audio is not None:
            print("Enhancing audio...")
            try:
                volume_boost = options.get("volume_boost", 1.2)
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

            # Configure write parameters for bundled executable (same as video_service.py)
            write_params = {
                'codec': 'libx264',
                'audio_codec': 'aac',
                'preset': preset,
                'bitrate': None,  # Let CRF control bitrate
                'ffmpeg_params': [
                    '-crf', str(crf),
                    '-profile:v', 'baseline',  # Use baseline profile for maximum compatibility
                    '-level', '3.0',           # Use level 3.0 for wide device support
                    '-pix_fmt', 'yuv420p',     # Ensure compatible pixel format
                    '-ar', '44100',            # Standard sample rate
                    '-ac', '2',                # Stereo audio
                    '-avoid_negative_ts', 'make_zero'
                ],
                'audio_bitrate': '128k',  # Lower audio bitrate for faster processing
                'temp_audiofile': os.path.join(os.path.dirname(output_video), 'temp_audio_enhance.m4a'),
                'remove_temp': True,
                'verbose': False,
                'logger': None
            }
            
            # For bundled executables, use more conservative settings
            if getattr(sys, 'frozen', False):
                write_params.update({
                    'preset': 'ultrafast',
                    'ffmpeg_params': [
                        '-crf', str(crf),
                        '-profile:v', 'baseline',  # Maintain compatibility
                        '-level', '3.0',           # Maintain compatibility
                        '-pix_fmt', 'yuv420p',     # Maintain compatibility
                        '-ar', '44100',            # Maintain compatibility
                        '-ac', '2',                # Maintain compatibility
                        '-avoid_negative_ts', 'make_zero'
                    ]
                })
            
            video.write_videofile(output_video, **write_params)
            
        except Exception as write_error:
            print(f"Error writing enhanced video: {write_error}")
            traceback.print_exc()

            # Fallback to basic write
            try:
                video.write_videofile(output_video, codec='libx264', audio_codec='aac', verbose=False, logger=None)
            except Exception as fallback_error:
                print(f"Error with fallback enhanced video write: {fallback_error}")
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
    if not CV2_AVAILABLE:
        print("Color correction requires OpenCV - skipping enhancement")
        return clip
        
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
    if not CV2_AVAILABLE:
        print("Background replacement requires OpenCV - skipping enhancement")
        return clip
        
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
    if not CV2_AVAILABLE:
        print("Motion graphics require OpenCV - skipping enhancement")
        return clip
        
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

        # Check FFmpeg availability first
        ffmpeg_available, ffmpeg_path, error_msg = check_ffmpeg_availability()
        if not ffmpeg_available:
            print(f"FFmpeg not available: {error_msg}")
            print("Skipping FFmpeg enhancements, using original video")
            try:
                shutil.copy2(input_video, output_video)
                return output_video
            except Exception as e:
                print(f"Error copying original video: {e}")
                return None

        # Use centralized FFmpeg command builder for optimization
        cmd = build_ffmpeg_command(ffmpeg_path, input_video, output_video, "optimization",
                                  preset=preset, vf_arg=vf_arg)

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


# Performance Optimization Manager (consolidated from optimization_service.py)
class PerformanceOptimizer:
    """Manages performance optimizations across the video generation pipeline"""

    def __init__(self):
        self._load_config()
        self._duplicate_tracker = {}

    def _load_config(self):
        """Load optimization configuration"""
        try:
            import config
            self.enable_duplicate_detection = getattr(config, 'ENABLE_DUPLICATE_DETECTION', True)
            self.duplicate_threshold = getattr(config, 'DUPLICATE_SIMILARITY_THRESHOLD', 0.95)
            self.processing_opts = getattr(config, 'PROCESSING_OPTIMIZATIONS', {})
            self.ffmpeg_opts = getattr(config, 'FFMPEG_OPTIMIZATION', {})
        except ImportError:
            # Fallback settings
            self.enable_duplicate_detection = True
            self.duplicate_threshold = 0.95
            self.processing_opts = {}
            self.ffmpeg_opts = {}

    def get_content_hash(self, text: str, additional_data: str = "") -> str:
        """Generate hash for content to detect duplicates"""
        content = f"{text}|{additional_data}".strip()
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def check_duplicate_content(self, text: str, folder_path: str = "") -> Optional[str]:
        """Check if content is duplicate and return previous result if found"""
        if not self.enable_duplicate_detection:
            return None

        content_hash = self.get_content_hash(text, folder_path)

        if content_hash in self._duplicate_tracker:
            previous_result = self._duplicate_tracker[content_hash]
            print(f"🔄 Duplicate content detected (hash: {content_hash[:8]}...)")
            print(f"   Previous result: {previous_result}")
            return previous_result

        return None

    def register_content_result(self, text: str, folder_path: str, result_path: str):
        """Register successful generation result for duplicate detection"""
        if not self.enable_duplicate_detection:
            return

        content_hash = self.get_content_hash(text, folder_path)
        self._duplicate_tracker[content_hash] = result_path
        print(f"📝 Registered content result (hash: {content_hash[:8]}...)")

    def get_optimized_ffmpeg_params(self) -> Dict:
        """Get optimized FFmpeg parameters for faster encoding"""
        base_params = {
            "preset": "fast",
            "crf": "22",
            "threads": "0",
            "tune": "film",
            "profile:v": "high",
            "level": "4.0",
            "pix_fmt": "yuv420p",
            "c:a": "aac",
            "b:a": "128k",
            "movflags": "+faststart"
        }

        # Override with user-configured options
        base_params.update(self.ffmpeg_opts)
        return base_params

    def should_skip_analysis(self, content_hash: str) -> bool:
        """Check if content analysis should be skipped for performance"""
        return self.processing_opts.get("skip_redundant_analysis", True) and \
               content_hash in self._duplicate_tracker

    def should_reuse_effects(self, content_type: str, emotional_tone: str) -> bool:
        """Check if effects can be reused for similar content"""
        return self.processing_opts.get("reuse_similar_effects", True)

    def should_batch_audio(self) -> bool:
        """Check if audio generation should be batched"""
        return self.processing_opts.get("batch_audio_generation", True)

    def should_optimize_images(self) -> bool:
        """Check if image loading should be optimized"""
        return self.processing_opts.get("optimize_image_loading", True)

    def should_cleanup_during_processing(self) -> bool:
        """Check if temporary files should be cleaned during processing"""
        return self.processing_opts.get("smart_temp_cleanup", True)

    def is_memory_efficient_mode(self) -> bool:
        """Check if memory-efficient mode is enabled"""
        return self.processing_opts.get("memory_efficient_mode", True)

    def get_optimization_summary(self) -> Dict:
        """Get summary of current optimization settings"""
        return {
            "duplicate_detection": self.enable_duplicate_detection,
            "duplicate_threshold": self.duplicate_threshold,
            "ffmpeg_preset": self.ffmpeg_opts.get("preset", "fast"),
            "ffmpeg_crf": self.ffmpeg_opts.get("crf", 22),
            "processing_optimizations": self.processing_opts,
            "tracked_content": len(self._duplicate_tracker)
        }

    def print_optimization_status(self):
        """Print current optimization status"""
        from utils.logging_utils import log_performance_status

        summary = self.get_optimization_summary()
        log_performance_status("\n🚀 Performance Optimization Status:")
        log_performance_status(f"   Duplicate Detection: {'✅' if summary['duplicate_detection'] else '❌'}")
        log_performance_status(f"   FFmpeg Preset: {summary['ffmpeg_preset']} (CRF: {summary['ffmpeg_crf']})")
        log_performance_status(f"   Tracked Content: {summary['tracked_content']} items")

        enabled_opts = [k for k, v in summary['processing_optimizations'].items() if v]
        if enabled_opts:
            log_performance_status(f"   Enabled Optimizations: {', '.join(enabled_opts)}")


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer instance"""
    return performance_optimizer


def apply_ffmpeg_optimizations(cmd_args: List[str]) -> List[str]:
    """Apply FFmpeg optimizations to command arguments"""
    optimized_params = performance_optimizer.get_optimized_ffmpeg_params()

    # Insert optimization parameters before output file
    if len(cmd_args) >= 2:
        # Find the output file (usually the last argument)
        output_file = cmd_args[-1]
        base_cmd = cmd_args[:-1]

        # Add optimization parameters
        for key, value in optimized_params.items():
            if key not in [arg.lstrip('-') for arg in base_cmd]:  # Avoid duplicates
                base_cmd.extend([f"-{key}", value])

        return base_cmd + [output_file]

    return cmd_args


def log_performance_improvement(operation: str, original_time: float, optimized_time: float):
    """Log performance improvement for an operation"""
    if optimized_time < original_time:
        improvement = ((original_time - optimized_time) / original_time) * 100
        print(f"⚡ {operation}: {improvement:.1f}% faster ({original_time:.1f}s → {optimized_time:.1f}s)")
    else:
        print(f"📊 {operation}: {optimized_time:.1f}s")


# Backward compatibility aliases for optimization_service.py
def get_optimization_manager() -> PerformanceOptimizer:
    """Backward compatibility alias for get_performance_optimizer"""
    return get_performance_optimizer()


optimization_manager = performance_optimizer  # Backward compatibility alias






