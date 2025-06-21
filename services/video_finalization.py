"""
Video Finalization Service - Centralized video-subtitle merging
Consolidated from Final_Video.py to eliminate duplicate implementations
"""
import time
import logging
from utils.common_imports import subprocess, os, traceback, shutil, sys, tempfile, glob

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
    from utils.helpers import check_ffmpeg_availability, build_ffmpeg_command, create_temp_file_with_cleanup, cleanup_temp_files
except ImportError:
    # Use fallback manager if available
    try:
        from utils.fallback_manager import get_helpers_with_fallback
        helpers = get_helpers_with_fallback()
        check_ffmpeg_availability = helpers.check_ffmpeg_availability
        # Import centralized functions - no need for fallback implementations
        from utils.helpers import build_ffmpeg_command, create_temp_file_with_cleanup, cleanup_temp_files
    except ImportError:
        # Critical error - should not happen in production
        print("CRITICAL: Cannot import FFmpeg utilities from utils.helpers or fallback_manager")
        raise ImportError("FFmpeg utilities are required but unavailable")


# Set up logging for monitoring
def _setup_monitoring_logger():
    """Set up logger for monitoring video finalization usage"""
    logger = logging.getLogger('video_finalization')
    if not logger.handlers:  # Avoid duplicate handlers
        logger.setLevel(logging.INFO)

        # Create file handler for monitoring logs
        try:
            from utils.helpers import get_app_data_dir
            log_dir = os.path.join(get_app_data_dir(), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'video_finalization.log')

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not set up monitoring logger: {e}")

    return logger

def _log_usage_metrics(logger, operation, duration, success, file_sizes=None, error=None):
    """Log usage metrics for monitoring"""
    try:
        metrics = {
            'operation': operation,
            'duration_seconds': round(duration, 2),
            'success': success,
            'timestamp': time.time()
        }

        if file_sizes:
            metrics.update(file_sizes)

        if error:
            metrics['error'] = str(error)

        logger.info(f"METRICS: {metrics}")
    except Exception as e:
        print(f"Warning: Could not log metrics: {e}")


def merge_video_subtitle(video_path, subtitle_path, output_file="final_output.mp4"):
    """
    Merge video and subtitle into a final output video
    
    This is the centralized implementation that consolidates all video-subtitle merging logic.
    Previously duplicated across Final_Video.py, services/video_service.py, and services/video_voiceover.py.
    
    Args:
        video_path (str): Path to input video file
        subtitle_path (str): Path to subtitle file (.ass format)
        output_file (str): Path to output video file (default: "final_output.mp4")
        
    Returns:
        str: Path to output file if successful, None if failed
        
    Features:
        - Comprehensive input validation
        - FFmpeg availability checking with fallbacks
        - Temporary file management for bundled executables
        - Multiple fallback strategies if subtitle embedding fails
        - Automatic cleanup of temporary files
        - Backup creation for safety
    """
    # Set up monitoring
    start_time = time.time()
    logger = _setup_monitoring_logger()
    success = False
    error_msg = None

    print(f"Merging video with subtitles: {os.path.basename(video_path)}")

    try:
        # Verify input files
        if not os.path.exists(video_path):
            error_msg = f"Video file not found: {video_path}"
            print(f"ERROR: {error_msg}")
            return None

        if not os.path.exists(subtitle_path):
            error_msg = f"Subtitle file not found: {subtitle_path}"
            print(f"ERROR: {error_msg}")
            return None

        # Create output directory if needed
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created output directory: {output_dir}")

        # Check video file size
        video_size = os.path.getsize(video_path)
        if video_size < 1000:
            print("WARNING: Input video file is suspiciously small!")

    except Exception as e:
        error_msg = f"Error during file verification: {str(e)}"
        print(f"ERROR: {error_msg}")
        return None

    # Check subtitle content
    try:
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            subtitle_content = f.read()
            subtitle_lines = subtitle_content.count('Dialogue:')
            if subtitle_lines == 0:
                print("WARNING: Subtitle file contains no dialogue lines!")
            elif subtitle_lines == 1 and "This is a sample subtitle" in subtitle_content:
                print("WARNING: Subtitle file contains only the default sample subtitle!")
    except Exception as e:
        print(f"Error reading subtitle file: {e}")

    # First, make a backup copy of the video
    backup_video = os.path.join(output_dir, "original_video_backup.mp4")
    try:
        shutil.copy2(video_path, backup_video)
        # Reduced logging: print(f"Created backup of original video: {backup_video}")
    except Exception as e:
        print(f"Failed to create backup: {e}")

    # Check FFmpeg availability first
    ffmpeg_available, ffmpeg_cmd, error_msg = check_ffmpeg_availability()
    if not ffmpeg_available:
        print(f"FFmpeg not available: {error_msg}")
        print("Skipping subtitle embedding, using original video")
        try:
            shutil.copy2(video_path, output_file)
            print(f"Copied original video to {output_file}")
            return output_file
        except Exception as e:
            print(f"Error copying video: {e}")
            return None

    # Use the working method: copy subtitle to current working directory with simple name
    print("Using the proven working method for subtitle embedding...")

    try:
        # For bundled executables, use a writable temporary directory
        
        if getattr(sys, 'frozen', False):
            # Running as bundled executable - use output directory for temp files
            temp_dir = os.path.dirname(output_file)
        else:
            # Running as script - use current directory
            temp_dir = os.getcwd()
            
        # ENHANCED: Create unique temp filename to avoid conflicts using centralized function
        local_subtitle_path = create_temp_file_with_cleanup(suffix='.ass', prefix='temp_subtitle_', directory=temp_dir)

        # ENHANCED: Ensure no leftover temp files exist using centralized cleanup
        temp_pattern = os.path.join(temp_dir, "temp_subtitle*.ass")
        old_temp_files = glob.glob(temp_pattern)
        if old_temp_files:
            cleanup_temp_files(*old_temp_files)
        
        shutil.copy2(subtitle_path, local_subtitle_path)
        print(f"Created local subtitle file: {local_subtitle_path}")
        temp_subtitle_path = local_subtitle_path
    except Exception as e:
        print(f"Error creating local subtitle file: {e}")
        # Fall back to using system temp directory
        try:
            temp_dir = tempfile.gettempdir()
            local_subtitle_path = create_temp_file_with_cleanup(suffix='.ass', prefix='temp_subtitle_', directory=temp_dir)
            shutil.copy2(subtitle_path, local_subtitle_path)
            print(f"Created temp subtitle file in system temp: {local_subtitle_path}")
            temp_subtitle_path = local_subtitle_path
        except Exception as temp_e:
            print(f"Error creating temp subtitle file: {temp_e}")
            # Final fallback to original path
            temp_subtitle_path = subtitle_path

    # Use the proven working method: local file with simple filename
    success = False

    # Remove any existing output file to ensure clean start
    if os.path.exists(output_file):
        try:
            os.remove(output_file)
        except Exception as e:
            print(f"Warning: Could not remove existing output file: {e}")

    try:
        # Use the full path to the subtitle file for better reliability
        subtitle_dir = os.path.dirname(temp_subtitle_path)

        # Use centralized FFmpeg command builder for subtitle embedding
        cmd = build_ffmpeg_command(ffmpeg_cmd, video_path, output_file, "subtitle", subtitle_file=temp_subtitle_path)

        print(f"Using working method with local file: {' '.join(cmd)}")

        # Change to the directory containing the subtitle file
        original_cwd = os.getcwd()
        if subtitle_dir and os.path.exists(subtitle_dir):
            os.chdir(subtitle_dir)
            print(f"Changed working directory to: {subtitle_dir}")
        else:
            print(f"Warning: Subtitle directory not found, staying in: {original_cwd}")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)

            # Verify the output file exists and has content
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                print(f"SUCCESS: Video with subtitles saved to {output_file}")
                print(f"Output file size: {os.path.getsize(output_file)} bytes")
                success = True
            else:
                print(f"WARNING: Method produced small or no output file")

        finally:
            # Always restore original working directory
            os.chdir(original_cwd)

    except Exception as e:
        print(f"Subtitle embedding failed: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"Error output: {e.stderr}")
        traceback.print_exc()

    # Enhanced error recovery with multiple fallback strategies
    if not success:
        print("🔄 Subtitle embedding failed. Attempting recovery strategies...")

        # Strategy 1: Try alternative FFmpeg subtitle method
        if ffmpeg_available:
            try:
                print("📝 Attempting alternative subtitle embedding method...")
                # Try using filter_complex instead of vf for better compatibility
                alt_cmd = [
                    ffmpeg_cmd, '-y', '-i', video_path, '-i', temp_subtitle_path,
                    '-filter_complex', '[0:v][1:s]overlay[v]',
                    '-map', '[v]', '-map', '0:a',
                    '-c:v', 'libx264', '-c:a', 'copy',
                    '-avoid_negative_ts', 'make_zero',
                    output_file
                ]
                subprocess.run(alt_cmd, check=True, capture_output=True, text=True, timeout=90)

                if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                    print("✅ Alternative subtitle method succeeded!")
                    return output_file
            except Exception as alt_e:
                print(f"⚠️ Alternative subtitle method failed: {alt_e}")

        # Strategy 2: Convert video to compatible format and retry
        if ffmpeg_available:
            try:
                print("🔧 Converting video to compatible format...")
                compatible_video = create_temp_file_with_cleanup(suffix='.mp4', prefix='compatible_video_')
                cmd = build_ffmpeg_command(ffmpeg_cmd, video_path, compatible_video, "compatibility")
                subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)

                # Retry subtitle embedding with compatible video
                print("🔄 Retrying subtitle embedding with compatible video...")
                retry_cmd = build_ffmpeg_command(ffmpeg_cmd, compatible_video, output_file, "subtitle", subtitle_file=temp_subtitle_path)
                subprocess.run(retry_cmd, check=True, capture_output=True, text=True, timeout=90)

                if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                    print("✅ Subtitle embedding succeeded with compatible video!")
                    cleanup_temp_files(compatible_video)
                    return output_file

                cleanup_temp_files(compatible_video)
            except Exception as compat_e:
                print(f"⚠️ Compatible format strategy failed: {compat_e}")

        # Strategy 3: Use original video without subtitles (graceful degradation)
        print("📹 Using original video without subtitles as fallback...")

        # Try backup first
        if os.path.exists(backup_video):
            try:
                shutil.copy2(backup_video, output_file)
                print(f"✅ Used backup video: {output_file}")
                return output_file
            except Exception as backup_e:
                print(f"⚠️ Backup copy failed: {backup_e}")

        # Final fallback: copy original video directly
        try:
            shutil.copy2(video_path, output_file)
            print(f"✅ Used original video: {output_file}")
            return output_file
        except Exception as copy_e:
            print(f"❌ All recovery strategies failed: {copy_e}")
            return None

    # Clean up temporary subtitle file if it was created using centralized cleanup
    if temp_subtitle_path != subtitle_path:
        cleanup_temp_files(temp_subtitle_path)

    # Clean up any remaining temp subtitle files in the area using centralized cleanup
    try:
        if getattr(sys, 'frozen', False):
            cleanup_dir = os.path.dirname(output_file)
        else:
            cleanup_dir = os.getcwd()

        temp_pattern = os.path.join(cleanup_dir, "temp_subtitle*.ass")
        remaining_temp_files = glob.glob(temp_pattern)
        if remaining_temp_files:
            cleanup_temp_files(*remaining_temp_files)
    except Exception as final_cleanup_e:
        print(f"Warning: Error in temp subtitle cleanup: {final_cleanup_e}")

    # Final verification
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        success = True
        # Log successful completion with file sizes
        video_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
        subtitle_size = os.path.getsize(subtitle_path) if os.path.exists(subtitle_path) else 0

        file_sizes = {
            'input_video_size': video_size,
            'subtitle_size': subtitle_size,
            'output_size': file_size
        }

        duration = time.time() - start_time
        _log_usage_metrics(logger, 'merge_video_subtitle', duration, True, file_sizes)

        # Reduced logging: print(f"Output file created successfully. Size: {file_size} bytes")
        return output_file
    else:
        error_msg = f"Output file was not created: {output_file}"
        print(f"ERROR: {error_msg}")
        # Log failure metrics
        duration = time.time() - start_time
        _log_usage_metrics(logger, 'merge_video_subtitle', duration, False, error=error_msg)

    return None


# Monitoring and analytics functions
def get_usage_statistics():
    """
    Get usage statistics from the monitoring logs

    Returns:
        dict: Usage statistics including success rate, average duration, etc.
    """
    try:
        from utils.helpers import get_app_data_dir
        log_file = os.path.join(get_app_data_dir(), 'logs', 'video_finalization.log')

        if not os.path.exists(log_file):
            return {"status": "No usage data available yet"}

        stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "average_duration": 0,
            "total_processing_time": 0,
            "success_rate": 0,
            "recent_errors": []
        }

        durations = []

        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if 'METRICS:' in line:
                    try:
                        # Extract metrics from log line
                        metrics_str = line.split('METRICS: ')[1].strip()
                        metrics = eval(metrics_str)  # Note: In production, use json.loads instead

                        stats["total_operations"] += 1
                        durations.append(metrics.get('duration_seconds', 0))

                        if metrics.get('success', False):
                            stats["successful_operations"] += 1
                        else:
                            stats["failed_operations"] += 1
                            if 'error' in metrics:
                                stats["recent_errors"].append(metrics['error'])

                    except Exception as e:
                        continue  # Skip malformed log lines

        if durations:
            stats["average_duration"] = round(sum(durations) / len(durations), 2)
            stats["total_processing_time"] = round(sum(durations), 2)

        if stats["total_operations"] > 0:
            stats["success_rate"] = round((stats["successful_operations"] / stats["total_operations"]) * 100, 1)

        # Keep only recent errors (last 5)
        stats["recent_errors"] = stats["recent_errors"][-5:]

        return stats

    except Exception as e:
        return {"status": f"Error reading usage statistics: {str(e)}"}


# Backward compatibility aliases
def merge_video_with_subtitles(video_path, subtitle_path, output_file):
    """
    Backward compatibility alias for merge_video_subtitle

    Args:
        video_path (str): Path to video file
        subtitle_path (str): Path to subtitle file
        output_file (str): Path to output file

    Returns:
        str: Path to output file if successful, None otherwise
    """
    return merge_video_subtitle(video_path, subtitle_path, output_file)
