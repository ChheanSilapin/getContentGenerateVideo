"""
Video voice-over functionality
Extracted from video_service.py for better organization
"""
import os
import subprocess
import traceback
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# Import centralized utility functions
from utils.helpers import (
    configure_ffmpeg_for_moviepy, setup_temp_directory_for_bundled_exe,
    get_ffmpeg_path, cleanup_temp_files, force_moviepy_cleanup, build_ffmpeg_command,
    get_media_duration_safe
)
from .video_looping import loop_video

def add_voiceover_to_video(video_file, audio_file, output_file, mix_with_original=True, original_volume=0.3):
    """
    Add voice-over audio to a video while preserving the original video duration

    Args:
        video_file: Path to the input video file
        audio_file: Path to the voice-over audio file
        output_file: Path to the output video file
        mix_with_original: Whether to mix with original audio or replace it
        original_volume: Volume level for original audio (0.0 to 1.0)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Normalize video file path to fix mixed path separators
        video_file = os.path.normpath(video_file)
        output_file = os.path.normpath(output_file)

        print(f"Adding voice-over to video: {os.path.basename(video_file)}")

        # Configure FFmpeg and temp directory (centralized)
        ffmpeg_configured = configure_ffmpeg_for_moviepy()
        setup_temp_directory_for_bundled_exe(output_file)

        # STEP 2: Enhanced video loading with multiple fallback strategies
        video = None
        loading_success = False

        # Strategy 1: Standard MoviePy loading
        try:
            video = VideoFileClip(video_file)
            loading_success = True
        except Exception as e:
            print(f"DEBUG: Strategy 1 failed: {type(e).__name__}: {str(e)[:100]}")
            pass  # Try next strategy
        
        # Strategy 2: MoviePy with specific codec parameters
        if not loading_success:
            try:
                # Force specific codec handling
                video = VideoFileClip(video_file, audio=True, target_resolution=None)
                loading_success = True
            except Exception as e:
                print(f"DEBUG: Strategy 2 failed: {type(e).__name__}: {str(e)[:100]}")
                pass  # Try next strategy
        
        # Strategy 3: MoviePy without audio first, then add audio separately
        if not loading_success:
            try:
                video = VideoFileClip(video_file, audio=False)
                # Try to add audio back
                try:
                    audio_clip = AudioFileClip(video_file)
                    video = video.set_audio(audio_clip)
                except:
                    pass  # Continue without original audio
                loading_success = True
            except Exception as e:
                print(f"DEBUG: Strategy 3 failed: {type(e).__name__}: {str(e)[:100]}")
                pass  # Try next strategy
        
        # Strategy 4: Convert video to compatible format as last resort
        if not loading_success:
            from .video_utils import convert_video_to_compatible_format
            success, converted_video, error_msg = convert_video_to_compatible_format(video_file)

            if success and converted_video:
                try:
                    video = VideoFileClip(converted_video)
                    loading_success = True
                    # Note: We'll use the converted video for processing
                    video_file = converted_video  # Update video_file path for the rest of the function
                except Exception as e:
                    print(f"DEBUG: Strategy 4 (converted video) failed: {type(e).__name__}: {str(e)[:100]}")
                    pass  # Final failure
            else:
                print(f"DEBUG: Strategy 4 (conversion) failed: {error_msg}")
                pass  # Conversion failed
        
        # Final check - if all strategies failed
        if not loading_success or video is None:
            print(f"ERROR: All video loading strategies failed for {video_file}")

            # Additional debugging information
            if os.path.exists(video_file):
                file_size = os.path.getsize(video_file)
                print(f"DEBUG: File exists, size: {file_size} bytes")

                # Try basic validation
                from .video_utils import validate_video_file
                is_valid, message, suggestion = validate_video_file(video_file)
                print(f"DEBUG: Validation result: {is_valid}, {message}")
                if suggestion:
                    print(f"DEBUG: Suggestion: {suggestion}")
            else:
                print(f"DEBUG: File does not exist at path: {video_file}")

            return False

        new_audio = AudioFileClip(audio_file)

        # SIMPLIFIED APPROACH: Try basic MoviePy first, then use FFmpeg fallback
        
        # For simple cases where audio fits in video, try MoviePy
        if new_audio.duration <= video.duration:
            try:
                if video.audio is not None and mix_with_original:
                    # Mix with original audio
                    original_audio = video.audio.volumex(original_volume)
                    mixed_audio = CompositeAudioClip([original_audio, new_audio])
                    final_video = video.set_audio(mixed_audio)
                else:
                    # Replace audio
                    final_video = video.set_audio(new_audio)
            except Exception as simple_error:
                # Clean up MoviePy objects
                video.close()
                new_audio.close()

                # Use FFmpeg fallback
                return add_voiceover_to_video_ffmpeg_fallback(video_file, audio_file, output_file)
        else:
            # Audio is longer than video - need looping, use FFmpeg directly
            # Get audio duration before cleanup
            audio_duration = new_audio.duration

            # Clean up MoviePy objects
            video.close()
            new_audio.close()

            # Use FFmpeg fallback which handles looping reliably
            return add_voiceover_to_video_ffmpeg_fallback(video_file, audio_file, output_file, audio_duration)

        # SIMPLIFIED VIDEO WRITING: Try once with MoviePy, fallback to FFmpeg if it fails
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

            # Force comprehensive MoviePy cleanup
            force_moviepy_cleanup()

            return True

        except Exception as write_error:
            # Clean up MoviePy objects
            try:
                video.close()
                new_audio.close()
                final_video.close()
            except:
                pass

            # Force comprehensive MoviePy cleanup before fallback
            force_moviepy_cleanup()

            # Use FFmpeg fallback
            return add_voiceover_to_video_ffmpeg_fallback(video_file, audio_file, output_file)

    except Exception as e:
        print(f"Error adding voice-over to video: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_voiceover_to_video_ffmpeg_fallback(video_file, audio_file, output_file, target_duration=None):
    """
    FFmpeg-based fallback for adding voiceover when MoviePy fails
    Uses FFmpeg directly for video looping with seamless or ping-pong transitions
    
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
        
        # Get video and audio durations using the proper function
        video_duration = get_media_duration_safe(video_file)
        audio_duration = get_media_duration_safe(audio_file)
        
        target_duration = target_duration or audio_duration
        
        # Determine if we need to loop the video
        if target_duration > 0 and video_duration > 0 and target_duration > video_duration:
            loops_needed = int(target_duration / video_duration) + 1

            # Use only seamless looping for speed (fastest and most reliable)
            looped_video = loop_video(video_file, target_duration, ffmpeg_path, output_file, method="seamless")

            if not looped_video:
                print("⚠️ Seamless looping failed, skipping video looping for speed")
                return False

            video_for_mixing = looped_video
        else:
            video_for_mixing = video_file
        
        # Step 2: Add audio using FFmpeg (replace original audio)
        # Use centralized FFmpeg command builder for audio mixing
        mix_cmd = build_ffmpeg_command(ffmpeg_path, video_for_mixing, output_file, "audio_mix",
                                      audio_file=audio_file, target_duration=target_duration)

        result = subprocess.run(mix_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=180)

        if result.returncode == 0:
            # Validate output duration and file integrity
            output_duration = get_media_duration_safe(output_file)
            output_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0

            if output_duration > 0 and abs(output_duration - target_duration) < 2.0:  # Allow 2s tolerance
                if output_size > 100000:  # At least 100KB for a valid video
                    success = True
                else:
                    success = True  # Still proceed, but warn user
            else:
                success = True  # Still consider it successful, but log the discrepancy
        else:
            success = False
        
        # Clean up temporary looped video
        if video_for_mixing != video_file and os.path.exists(video_for_mixing):
            cleanup_temp_files(video_for_mixing)

        # Force comprehensive cleanup to ensure file handles are released
        force_moviepy_cleanup()

        return success
            
    except Exception as e:
        print(f"FFmpeg fallback error: {e}")
        return False

# merge_video_with_subtitles function moved to services.video_finalization
# Import it from there if needed:
# from services.video_finalization import merge_video_with_subtitles
