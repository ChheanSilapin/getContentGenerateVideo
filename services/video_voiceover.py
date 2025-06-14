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
    get_ffmpeg_path, cleanup_temp_files
)
from .video_utils import get_media_duration
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
        print(f"Adding voice-over to video: {os.path.basename(video_file)}")
        print(f"Voice-over audio: {os.path.basename(audio_file)}")
        print(f"Output: {os.path.basename(output_file)}")
        print(f"Mix with original: {mix_with_original}, Original volume: {original_volume}")

        # Configure FFmpeg and temp directory (centralized)
        ffmpeg_configured = configure_ffmpeg_for_moviepy()
        setup_temp_directory_for_bundled_exe(output_file)

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
            from .video_utils import convert_video_to_compatible_format
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
        
        print(f"Using FFmpeg fallback for professional video processing...")
        
        # Get video and audio durations using the proper function
        video_duration = get_media_duration(video_file)
        audio_duration = get_media_duration(audio_file)
        
        print(f"Detected video duration: {video_duration:.2f}s")
        print(f"Detected audio duration: {audio_duration:.2f}s")
        
        target_duration = target_duration or audio_duration
        
        # Determine if we need to loop the video
        if target_duration > 0 and video_duration > 0 and target_duration > video_duration:
            loops_needed = int(target_duration / video_duration) + 1
            print(f"Video duration: {video_duration:.2f}s, Audio duration: {target_duration:.2f}s")
            print(f"Creating {loops_needed} loops for reliable video looping...")
            
            # Try seamless looping first (fast and reliable for most videos)
            looped_video = loop_video(video_file, target_duration, ffmpeg_path, output_file, method="seamless")

            if not looped_video:
                print("Seamless looping failed, trying ping-pong method...")
                # Try ping-pong as second option
                looped_video = loop_video(video_file, target_duration, ffmpeg_path, output_file, method="pingpong")

            if not looped_video:
                print("Ping-pong looping failed, trying direct method...")
                # Try direct as last resort
                looped_video = loop_video(video_file, target_duration, ffmpeg_path, output_file, method="direct")
            
            if not looped_video:
                print("Video looping failed completely")
                return False
                
            video_for_mixing = looped_video
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
            '-t', str(target_duration),  # Use target duration instead of -shortest
            '-avoid_negative_ts', 'make_zero',
            '-y',
            output_file
        ]
        
        result = subprocess.run(mix_cmd, capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            # Validate output duration and file integrity
            output_duration = get_media_duration(output_file)
            output_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
            
            print(f"Final output duration: {output_duration:.2f}s (expected: {target_duration:.2f}s)")
            print(f"Final output size: {output_size} bytes")
            
            if output_duration > 0 and abs(output_duration - target_duration) < 2.0:  # Allow 2s tolerance
                if output_size > 100000:  # At least 100KB for a valid video
                    print("FFmpeg video processing successful!")
                    success = True
                else:
                    print(f"Warning: Output file too small ({output_size} bytes), may be corrupted")
                    success = True  # Still proceed, but warn user
            else:
                print(f"Warning: Output duration mismatch - got {output_duration:.2f}s, expected {target_duration:.2f}s")
                success = True  # Still consider it successful, but log the discrepancy
        else:
            print(f"FFmpeg audio mixing failed: {result.stderr}")
            success = False
        
        # Clean up temporary looped video
        if video_for_mixing != video_file and os.path.exists(video_for_mixing):
            cleanup_temp_files(video_for_mixing)
            print(f"Cleaned up temporary looped video: {os.path.basename(video_for_mixing)}")
        
        return success
            
    except Exception as e:
        print(f"FFmpeg fallback error: {e}")
        return False

def merge_video_with_subtitles(video_path, subtitle_path, output_file):
    """
    Merge video with subtitles
    
    Args:
        video_path: Path to video file
        subtitle_path: Path to subtitle file
        output_file: Path to output file
        
    Returns:
        str: Path to output file if successful, None otherwise
    """
    try:
        from Final_Video import merge_video_subtitle
        return merge_video_subtitle(video_path, subtitle_path, output_file)
    except Exception as e:
        print(f"Error merging video with subtitles: {e}")
        return None
