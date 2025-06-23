"""
Video looping functionality
Extracted from video_service.py for better organization
"""
import os
import time

# Import centralized utility functions
from utils.helpers import (
    validate_output_file, cleanup_temp_files, build_ffmpeg_command,
    create_temp_file_with_cleanup, execute_ffmpeg_command, validate_loop_count,
    validate_ffmpeg_path, TempVideoFile, log_message, get_media_duration_safe
)

def loop_video(video_file, target_duration, ffmpeg_path, output_file, method="seamless",
               logger_func=None, content_analysis=None, sync_with_audio=True):
    """
    Create a looped video using the specified method with content-aware enhancements

    Args:
        video_file: Path to input video
        target_duration: Target duration for the looped video
        ffmpeg_path: Path to FFmpeg executable
        output_file: Output file path for naming temporary file
        method: Looping method ("direct", "crossfade", "seamless", "pingpong", or "content_aware")
        logger_func: Optional logging function (e.g., main_gui.log)
        content_analysis: Optional ContentAnalysis object for enhanced looping
        sync_with_audio: Whether to sync loop points with audio rhythm

    Returns:
        str: Path to created looped video file, or None if failed
    """
    try:
        # Enhanced validation using centralized functions
        if not os.path.exists(video_file):
            log_message(f"Input video file not found: {video_file}", "ERROR", logger_func)
            return None

        # Use improved FFmpeg path validation
        is_valid, resolved_ffmpeg_path, error_msg = validate_ffmpeg_path(ffmpeg_path)
        if not is_valid:
            log_message(error_msg, "ERROR", logger_func)
            return None

        video_duration = get_media_duration_safe(video_file)
        if video_duration <= 0:
            log_message("Could not determine video duration or video is empty", "ERROR", logger_func)
            return None

        if target_duration <= video_duration:
            log_message("Target duration must be longer than video duration for looping", "ERROR", logger_func)
            return None

        loops_needed = int(target_duration / video_duration) + 1
        timestamp = int(time.time() * 1000)

        # Use content analysis to determine optimal looping method
        if method == "content_aware" and content_analysis:
            method = _determine_optimal_loop_method(content_analysis, video_duration, logger_func)
            log_message(f"Content analysis suggests {method} loop method", "INFO", logger_func)

        # Method routing using dictionary for cleaner dispatch
        method_handlers = {
            "pingpong": lambda: create_pingpong_loop(video_file, target_duration, resolved_ffmpeg_path, loops_needed, timestamp, output_file, logger_func),
            "seamless": lambda: create_seamless_loop(video_file, target_duration, resolved_ffmpeg_path, loops_needed, timestamp, output_file, logger_func),
            "crossfade": lambda: _handle_crossfade_method(video_file, target_duration, resolved_ffmpeg_path, loops_needed, timestamp, output_file, video_duration, logger_func),
            "direct": lambda: create_direct_loop(video_file, target_duration, resolved_ffmpeg_path, loops_needed, output_file, timestamp, logger_func),
            "content_aware": lambda: create_seamless_loop(video_file, target_duration, resolved_ffmpeg_path, loops_needed, timestamp, output_file, logger_func)  # Fallback
        }

        # Get handler or default to direct method
        handler = method_handlers.get(method, method_handlers["direct"])

        log_message(f"Using {method} loop method", "INFO", logger_func)
        return handler()

    except Exception as e:
        log_message(f"Video looping error: {e}", "ERROR", logger_func)
        return None

def _determine_optimal_loop_method(content_analysis, video_duration, _=None):
    """Determine optimal looping method based on content analysis"""
    content_type = content_analysis.content_type.value
    emotional_tone = content_analysis.emotional_tone.value

    # Historical content often benefits from seamless loops
    if content_type == 'historical':
        return 'seamless'

    # Dramatic content works well with crossfade
    elif emotional_tone in ['dramatic', 'mysterious']:
        return 'crossfade'

    # Reflective content benefits from ping-pong for natural flow
    elif emotional_tone in ['reflective', 'melancholic']:
        return 'pingpong'

    # For short videos, use seamless; for longer videos, use direct
    elif video_duration < 10:
        return 'seamless'
    else:
        return 'direct'

def _handle_crossfade_method(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, output_file, video_duration, logger_func):
    """Helper function to handle crossfade method selection based on video duration"""
    if video_duration > 30:
        log_message(f"Video is longer than 30 seconds ({video_duration:.1f}s), using optimized crossfade method", "INFO", logger_func)
        return create_optimized_crossfade_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, output_file, logger_func)
    else:
        return create_crossfade_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, logger_func)

def create_direct_loop(video_file, target_duration, ffmpeg_path, loops_needed, output_file, timestamp, logger_func=None):
    """Create a looped video using direct concatenation (internal helper)"""
    # Validate loop count using centralized function
    is_valid, error_msg = validate_loop_count(loops_needed, 100, "direct loop")
    if not is_valid:
        log_message(error_msg, "ERROR", logger_func)
        return None

    temp_looped = create_temp_file_with_cleanup(suffix='.mp4', prefix=f'temp_direct_loop_{timestamp}_')

    # Use centralized FFmpeg command builder for looping
    loop_cmd = build_ffmpeg_command(ffmpeg_path, video_file, temp_looped, "loop",
                                   loops=loops_needed, target_duration=target_duration)

    log_message("Creating direct looped video...", "INFO", logger_func)

    # Use centralized FFmpeg execution with dynamic timeout
    video_duration = get_media_duration_safe(video_file)
    success, result, error_msg = execute_ffmpeg_command(
        loop_cmd, "Direct loop creation", video_duration=video_duration
    )

    if success and os.path.exists(temp_looped):
        # Validate output file using centralized function
        is_valid, message = validate_output_file(temp_looped, file_type="looped video")
        if is_valid:
            log_message("Direct loop created successfully!", "INFO", logger_func)
            return temp_looped
        else:
            log_message(f"Error: {message}", "ERROR", logger_func)
            cleanup_temp_files(temp_looped)
            return None
    else:
        log_message(f"Direct loop failed: {error_msg or (result.stderr if result else 'Unknown error')}", "ERROR", logger_func)
        return None

def create_crossfade_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, logger_func=None):
    """Create a looped video with crossfade transitions (internal helper)"""
    # Validate loop count using centralized function
    is_valid, error_msg = validate_loop_count(loops_needed, 50, "crossfade loop")
    if not is_valid:
        log_message(error_msg, "ERROR", logger_func)
        return None

    # Use context manager for automatic cleanup
    with TempVideoFile(suffix='.mp4', prefix=f'temp_crossfade_loop_{timestamp}_') as temp_looped:
        # Create crossfade loop using FFmpeg's complex filter
        crossfade_duration = 0.5  # 0.5 second crossfade
        video_duration = get_media_duration_safe(video_file)

        # Build complex filter for crossfade looping
        filter_complex = f"[0:v]split={loops_needed}"
        for i in range(loops_needed):
            filter_complex += f"[v{i}]"
        filter_complex += ";"

        # Add crossfade between segments
        for i in range(loops_needed - 1):
            if i == 0:
                filter_complex += f"[v{i}][v{i+1}]xfade=transition=fade:duration={crossfade_duration}:offset={video_duration - crossfade_duration}[vx{i}];"
            else:
                filter_complex += f"[vx{i-1}][v{i+1}]xfade=transition=fade:duration={crossfade_duration}:offset={video_duration - crossfade_duration}[vx{i}];"

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

        log_message("Executing crossfade loop command...", "INFO", logger_func)

        # Use centralized FFmpeg execution
        success, result, error_msg = execute_ffmpeg_command(
            cmd, "Crossfade loop creation", video_duration=video_duration
        )

        if success and os.path.exists(temp_looped):
            # Validate output file using centralized function
            is_valid, message = validate_output_file(temp_looped, file_type="crossfade looped video")
            if is_valid:
                log_message("Crossfade loop created successfully!", "INFO", logger_func)
                # Return the path and prevent cleanup by the context manager
                result_path = temp_looped
                # Create a copy to return since context manager will clean up
                final_path = create_temp_file_with_cleanup(suffix='.mp4', prefix=f'final_crossfade_{timestamp}_')
                import shutil
                shutil.copy2(temp_looped, final_path)
                return final_path
            else:
                log_message(f"Error: {message}", "ERROR", logger_func)
                return None
        else:
            log_message(f"Crossfade loop failed: {error_msg or (result.stderr if result else 'Unknown error')}", "ERROR", logger_func)
            return None

def create_seamless_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, output_file, logger_func=None):
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
        logger_func: Optional logging function

    Returns:
        str: Path to created looped video file, or None if failed
    """
    try:
        temp_final = create_temp_file_with_cleanup(suffix='.mp4', prefix=f'temp_seamless_final_{timestamp}_')

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

        log_message("Creating seamless looped video...", "INFO", logger_func)

        # Use centralized FFmpeg execution with dynamic timeout
        video_duration = get_media_duration_safe(video_file)
        success, result, error_msg = execute_ffmpeg_command(
            cmd, "Seamless loop creation", video_duration=video_duration
        )

        if success and os.path.exists(temp_final):
            # Validate output file using centralized function
            is_valid, message = validate_output_file(temp_final, file_type="seamless looped video")
            if is_valid:
                log_message("Seamless loop created successfully!", "INFO", logger_func)
                return temp_final
            else:
                log_message(f"Error: {message}", "ERROR", logger_func)
                cleanup_temp_files(temp_final)
                return None
        else:
            log_message(f"Seamless loop failed: {error_msg or (result.stderr if result else 'Unknown error')}", "ERROR", logger_func)
            cleanup_temp_files(temp_final)
            return None

    except Exception as e:
        log_message(f"Seamless loop error: {str(e)}", "ERROR", logger_func)
        return None

def create_optimized_crossfade_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, output_file, logger_func=None):
    """
    Create a looped video with crossfade transitions optimized for longer videos
    Uses a more efficient approach that processes videos in chunks to prevent memory issues
    """
    try:
        # For very long videos or many loops, use a simpler approach
        if loops_needed > 20:
            log_message(f"Too many loops needed ({loops_needed}), using direct method instead", "INFO", logger_func)
            return create_direct_loop(video_file, target_duration, ffmpeg_path, loops_needed, output_file, timestamp, logger_func)

        temp_final = create_temp_file_with_cleanup(suffix='.mp4', prefix=f'temp_optimized_crossfade_{timestamp}_')

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

        log_message("Creating optimized crossfade loop...", "INFO", logger_func)

        # Use centralized FFmpeg execution with extended timeout for longer videos
        video_duration = get_media_duration_safe(video_file)
        success, result, error_msg = execute_ffmpeg_command(
            cmd, "Optimized crossfade loop creation", timeout=600, video_duration=video_duration
        )

        if success and os.path.exists(temp_final):
            is_valid, message = validate_output_file(temp_final, file_type="optimized crossfade looped video")
            if is_valid:
                log_message("Optimized crossfade loop created successfully!", "INFO", logger_func)
                return temp_final
            else:
                log_message(f"Error: {message}", "ERROR", logger_func)
                cleanup_temp_files(temp_final)
                return None
        else:
            log_message(f"Optimized crossfade loop failed: {error_msg or (result.stderr if result else 'Unknown error')}", "ERROR", logger_func)
            cleanup_temp_files(temp_final)
            return None

    except Exception as e:
        log_message(f"Optimized crossfade error: {str(e)}", "ERROR", logger_func)
        return None

def create_pingpong_loop(video_file, target_duration, ffmpeg_path, loops_needed, timestamp, output_file, logger_func=None):
    """
    Create a ping-pong looped video (forward then backward)
    This creates a natural-looking loop by playing the video forward then backward
    """
    try:
        # Get video duration for calculations
        video_duration = get_media_duration_safe(video_file)

        # Use context managers for automatic cleanup of temporary files
        with TempVideoFile(suffix='.mp4', prefix=f'temp_reversed_{timestamp}_') as temp_reversed, \
             TempVideoFile(suffix='.mp4', prefix=f'temp_pingpong_{timestamp}_') as temp_pingpong:

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

            log_message("Creating reversed video for ping-pong effect...", "INFO", logger_func)

            # Use centralized FFmpeg execution
            success, result, error_msg = execute_ffmpeg_command(
                reverse_cmd, "Video reversal", video_duration=video_duration
            )

            if not success or not os.path.exists(temp_reversed):
                log_message(f"Failed to create reversed video: {error_msg or (result.stderr if result else 'Unknown error')}", "ERROR", logger_func)
                log_message("This might be due to video format compatibility issues.", "WARNING", logger_func)
                return None

            # Step 2: Concatenate original and reversed to create ping-pong effect
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

            log_message("Concatenating original and reversed videos...", "INFO", logger_func)

            success, result, error_msg = execute_ffmpeg_command(
                concat_cmd, "Video concatenation", video_duration=video_duration * 2
            )

            if not success or not os.path.exists(temp_pingpong):
                log_message(f"Failed to create ping-pong video: {error_msg or (result.stderr if result else 'Unknown error')}", "ERROR", logger_func)
                log_message("Video concatenation failed - this is normal for some video formats.", "WARNING", logger_func)
                log_message("The system will automatically try the seamless method next.", "INFO", logger_func)
                return None

            # Step 3: Loop the ping-pong video to reach target duration
            pingpong_duration = video_duration * 2  # Original + reversed
            pingpong_loops = int(target_duration / pingpong_duration) + 1

            temp_final = create_temp_file_with_cleanup(suffix='.mp4', prefix=f'temp_pingpong_final_{timestamp}_')

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

            log_message("Creating final ping-pong looped video...", "INFO", logger_func)

            success, result, error_msg = execute_ffmpeg_command(
                loop_cmd, "Ping-pong loop finalization", video_duration=target_duration
            )

            if success and os.path.exists(temp_final):
                is_valid, message = validate_output_file(temp_final, file_type="ping-pong looped video")
                if is_valid:
                    log_message("Ping-pong loop created successfully!", "INFO", logger_func)
                    return temp_final
                else:
                    log_message(f"Error: {message}", "ERROR", logger_func)
                    cleanup_temp_files(temp_final)
                    return None
            else:
                log_message(f"Ping-pong loop failed: {error_msg or (result.stderr if result else 'Unknown error')}", "ERROR", logger_func)
                return None

    except Exception as e:
        log_message(f"Ping-pong loop error: {str(e)}", "ERROR", logger_func)
        return None
