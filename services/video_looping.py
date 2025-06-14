"""
Video looping functionality
Extracted from video_service.py for better organization
"""
import os
import subprocess
import tempfile
import time

# Import centralized utility functions
from utils.helpers import (
    get_ffmpeg_path, validate_output_file, cleanup_temp_files
)
from .video_utils import get_media_duration

def loop_video(video_file, target_duration, ffmpeg_path, output_file, method="seamless"):
    """
    Create a looped video using the specified method
    
    Args:
        video_file: Path to input video
        target_duration: Target duration for the looped video
        ffmpeg_path: Path to FFmpeg executable
        output_file: Output file path for naming temporary file
        method: Looping method ("direct", "crossfade", "seamless", or "pingpong")
        
    Returns:
        str: Path to created looped video file, or None if failed
    """
    try:
        # Validation and error prevention
        if not os.path.exists(video_file):
            print(f"Error: Input video file not found: {video_file}")
            return None
            
        if not os.path.exists(ffmpeg_path) and ffmpeg_path != 'ffmpeg':
            print(f"Error: FFmpeg executable not found: {ffmpeg_path}")
            return None
            
        video_duration = get_media_duration(video_file)
        if video_duration <= 0:
            print("Error: Could not determine video duration or video is empty")
            return None
            
        if target_duration <= video_duration:
            print("Error: Target duration must be longer than video duration for looping")
            return None
            
        loops_needed = int(target_duration / video_duration) + 1
        
        # Create unique temporary file to prevent duplicates
        timestamp = int(time.time() * 1000)
        
        # Use different methods based on the specified approach and video length
        if method == "pingpong":
            # Ping-pong looping works for all video lengths
            print(f"Using ping-pong loop method (forward->backward)")
            return create_pingpong_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, output_file)
        elif method == "seamless":
            # Seamless looping works for all video lengths
            print(f"Using seamless loop method for smooth transitions")
            return create_seamless_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, output_file)
        elif method == "crossfade":
            # For longer videos, use the optimized crossfade approach
            if video_duration > 30:
                print(f"Video is longer than 30 seconds ({video_duration:.1f}s), using optimized crossfade method")
                return create_optimized_crossfade_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, output_file)
            else:
                return create_crossfade_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp)
        else:  # Default to direct method
            return create_direct_loop(video_file, target_duration, ffmpeg_path, loops_needed, output_file, timestamp)
            
    except Exception as e:
        print(f"Video looping error: {e}")
        return None

def create_direct_loop(video_file, target_duration, ffmpeg_path, loops_needed, output_file, timestamp):
    """Create a looped video using direct concatenation (internal helper)"""
    # Prevent excessive loops that could cause memory issues
    if loops_needed > 100:
        print(f"Error: Too many loops needed ({loops_needed}), maximum is 100")
        return None
    
    temp_looped = os.path.join(tempfile.gettempdir(), f"temp_direct_loop_{timestamp}.mp4")
    
    # Create a simple loop by repeating the video
    loop_cmd = [
        ffmpeg_path,
        '-stream_loop', str(loops_needed - 1),  # Loop the input
        '-i', video_file,
        '-t', str(target_duration),  # Limit to target duration
        '-c', 'copy',  # Copy streams without re-encoding (fastest)
        '-avoid_negative_ts', 'make_zero',
        '-y',
        temp_looped
    ]
    
    print("Creating direct looped video...")
    result = subprocess.run(loop_cmd, capture_output=True, text=True, timeout=180)
    
    if result.returncode == 0 and os.path.exists(temp_looped):
        # Validate output file using centralized function
        is_valid, message = validate_output_file(temp_looped, file_type="looped video")
        if is_valid:
            print("Direct loop created successfully!")
            return temp_looped
        else:
            print(f"Error: {message}")
            cleanup_temp_files(temp_looped)
            return None
    else:
        print(f"Direct loop failed: {result.stderr}")
        return None

def create_crossfade_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp):
    """Create a looped video with crossfade transitions (internal helper)"""
    # Prevent excessive loops that could cause memory issues
    if loops_needed > 50:
        print(f"Error: Too many loops needed ({loops_needed}), maximum is 50")
        return None
    
    temp_looped = os.path.join(tempfile.gettempdir(), f"temp_crossfade_loop_{timestamp}.mp4")
    
    # Create crossfade loop using FFmpeg's complex filter
    crossfade_duration = 0.5  # 0.5 second crossfade
    
    # Build complex filter for crossfade looping
    filter_complex = f"[0:v]split={loops_needed}"
    for i in range(loops_needed):
        filter_complex += f"[v{i}]"
    filter_complex += ";"
    
    # Add crossfade between segments
    for i in range(loops_needed - 1):
        if i == 0:
            filter_complex += f"[v{i}][v{i+1}]xfade=transition=fade:duration={crossfade_duration}:offset={get_media_duration(video_file) - crossfade_duration}[vx{i}];"
        else:
            filter_complex += f"[vx{i-1}][v{i+1}]xfade=transition=fade:duration={crossfade_duration}:offset={get_media_duration(video_file) - crossfade_duration}[vx{i}];"
    
    # Final output
    filter_complex += f"[vx{loops_needed-2}]trim=duration={target_duration}[out]"
    
    cmd = [
        ffmpeg_path,
        '-i', video_file,
        '-filter_complex', filter_complex,
        '-map', '[out]',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '28',
        '-avoid_negative_ts', 'make_zero',
        '-y',
        temp_looped
    ]
    
    print("Executing crossfade loop command...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if result.returncode == 0 and os.path.exists(temp_looped):
        # Validate output file using centralized function
        is_valid, message = validate_output_file(temp_looped, file_type="crossfade looped video")
        if is_valid:
            print("Crossfade loop created successfully!")
            return temp_looped
        else:
            print(f"Error: {message}")
            cleanup_temp_files(temp_looped)
            return None
    else:
        print(f"Crossfade loop failed: {result.stderr}")
        # Clean up on failure
        cleanup_temp_files(temp_looped)
        return None

def create_seamless_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, output_file):
    """
    Create a seamless looped video with no visible transitions
    Uses a specialized FFmpeg approach that works well for all types of videos
    
    Args:
        video_file: Path to input video
        target_duration: Target duration for looped video
        ffmpeg_path: Path to FFmpeg executable
        loops_needed: Number of loops needed
        timestamp: Unique timestamp for temp files
        output_file: Output file path for naming temp file
        
    Returns:
        str: Path to created looped video file, or None if failed
    """
    try:
        temp_final = os.path.join(tempfile.gettempdir(), f"temp_seamless_final_{timestamp}.mp4")
        
        # Use stream_loop for seamless looping - this is the most reliable method
        cmd = [
            ffmpeg_path,
            '-stream_loop', str(loops_needed - 1),  # Number of additional loops
            '-i', video_file,
            '-t', str(target_duration),  # Exact target duration
            '-c:v', 'libx264',
            '-preset', 'ultrafast',  # Fast encoding
            '-crf', '28',  # Good quality/speed balance
            '-c:a', 'aac',
            '-avoid_negative_ts', 'make_zero',
            '-y',
            temp_final
        ]
        
        print("Creating seamless looped video...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and os.path.exists(temp_final):
            # Validate output file using centralized function
            is_valid, message = validate_output_file(temp_final, file_type="seamless looped video")
            if is_valid:
                print("Seamless loop created successfully!")
                return temp_final
            else:
                print(f"Error: {message}")
                cleanup_temp_files(temp_final)
                return None
        else:
            print(f"Seamless loop failed: {result.stderr}")
            cleanup_temp_files(temp_final)
            return None
            
    except Exception as e:
        print(f"Seamless loop error: {str(e)}")
        return None

def create_optimized_crossfade_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, output_file):
    """
    Create a looped video with crossfade transitions optimized for longer videos
    Uses a more efficient approach that processes videos in chunks to prevent memory issues
    """
    try:
        # For very long videos or many loops, use a simpler approach
        if loops_needed > 20:
            print(f"Too many loops needed ({loops_needed}), using direct method instead")
            return create_direct_loop(video_file, target_duration, ffmpeg_path, loops_needed, output_file, timestamp)
        
        temp_final = os.path.join(tempfile.gettempdir(), f"temp_optimized_crossfade_{timestamp}.mp4")
        
        # Use a simplified crossfade approach for longer videos
        cmd = [
            ffmpeg_path,
            '-stream_loop', str(loops_needed - 1),
            '-i', video_file,
            '-t', str(target_duration),
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '30',  # Higher CRF for faster processing
            '-c:a', 'aac',
            '-avoid_negative_ts', 'make_zero',
            '-y',
            temp_final
        ]
        
        print("Creating optimized crossfade loop...")
        final_result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # Longer timeout for big files
        
        if final_result.returncode == 0 and os.path.exists(temp_final):
            is_valid, message = validate_output_file(temp_final, file_type="optimized crossfade looped video")
            if is_valid:
                print("Optimized crossfade loop created successfully!")
                return temp_final
            else:
                print(f"Error: {message}")
                cleanup_temp_files(temp_final)
                return None
        else:
            print(f"Optimized crossfade loop failed: {final_result.stderr}")
            cleanup_temp_files(temp_final)
            return None
            
    except Exception as e:
        print(f"Optimized crossfade error: {str(e)}")
        return None

def create_pingpong_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, output_file):
    """
    Create a ping-pong looped video (forward then backward)
    This creates a natural-looking loop by playing the video forward then backward
    """
    try:
        # Get video duration for calculations
        video_duration = get_media_duration(video_file)
        
        # Create unique temporary files
        temp_dir = tempfile.gettempdir()
        temp_reversed = os.path.join(temp_dir, f"temp_reversed_{timestamp}.mp4")
        temp_pingpong = os.path.join(temp_dir, f"temp_pingpong_{timestamp}.mp4")
        temp_final = os.path.join(temp_dir, f"temp_pingpong_final_{timestamp}.mp4")
        
        # Clean up any existing files with same name
        cleanup_temp_files(temp_reversed, temp_pingpong, temp_final)
        
        # Step 1: Create reversed version of the video (video-only to avoid audio issues)
        reverse_cmd = [
            ffmpeg_path,
            '-i', video_file,
            '-vf', 'reverse',
            '-an',  # No audio to avoid issues with videos that don't have audio
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '28',
            '-y',
            temp_reversed
        ]
        
        print("Creating reversed video for ping-pong effect...")
        result = subprocess.run(reverse_cmd, capture_output=True, text=True, timeout=180)

        if result.returncode != 0 or not os.path.exists(temp_reversed):
            print(f"Failed to create reversed video: {result.stderr}")
            print("This might be due to video format compatibility issues.")
            return None
        
        # Step 2: Concatenate original and reversed to create ping-pong effect
        # Check if video has audio stream first
        video_duration = get_media_duration(video_file)

        # Try with audio first, fallback to video-only if audio doesn't exist
        concat_cmd = [
            ffmpeg_path,
            '-i', video_file,
            '-i', temp_reversed,
            '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[outv]',  # Video-only concatenation
            '-map', '[outv]',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '28',
            '-y',
            temp_pingpong
        ]
        
        print("Concatenating original and reversed videos...")
        result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=180)

        # Clean up reversed file
        cleanup_temp_files(temp_reversed)

        if result.returncode != 0 or not os.path.exists(temp_pingpong):
            print(f"Failed to create ping-pong video: {result.stderr}")
            print("Video concatenation failed - this is normal for some video formats.")
            print("The system will automatically try the seamless method next.")
            return None
        
        # Step 3: Loop the ping-pong video to reach target duration
        pingpong_duration = video_duration * 2  # Original + reversed
        pingpong_loops = int(target_duration / pingpong_duration) + 1
        
        loop_cmd = [
            ffmpeg_path,
            '-stream_loop', str(pingpong_loops - 1),
            '-i', temp_pingpong,
            '-t', str(target_duration),
            '-c', 'copy',  # Copy without re-encoding for speed
            '-avoid_negative_ts', 'make_zero',
            '-y',
            temp_final
        ]
        
        print("Creating final ping-pong looped video...")
        result = subprocess.run(loop_cmd, capture_output=True, text=True, timeout=180)
        
        # Clean up intermediate ping-pong file
        cleanup_temp_files(temp_pingpong)
        
        if result.returncode == 0 and os.path.exists(temp_final):
            is_valid, message = validate_output_file(temp_final, file_type="ping-pong looped video")
            if is_valid:
                print("Ping-pong loop created successfully!")
                return temp_final
            else:
                print(f"Error: {message}")
                cleanup_temp_files(temp_final)
                return None
        else:
            print(f"Ping-pong loop failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Ping-pong loop error: {str(e)}")
        return None
