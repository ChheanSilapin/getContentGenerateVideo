from utils.common_imports import subprocess, os, traceback, shutil, sys, tempfile, glob

# Use centralized path management
try:
    from utils.path_manager import setup_project_paths
    # Set up all project paths at once
    setup_project_paths()
except ImportError:
    # Fallback path setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    utils_dir = os.path.join(current_dir, 'utils')
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

def merge_video_subtitle(video_path, subtitle_path, output_file="final_output.mp4"):
    """Merge video and subtitle into a final output video"""
    print(f"Merging video with subtitles: {os.path.basename(video_path)}")

    # Verify input files
    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}")
        return None

    if not os.path.exists(subtitle_path):
        print(f"ERROR: Subtitle file not found: {subtitle_path}")
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

    # If all subtitle methods failed, try to use the original video
    if not success:
        print("All subtitle embedding methods failed. Using original video.")
        if ffmpeg_available:
            try:
                # Convert the original video to a more compatible format using centralized command builder
                cmd = build_ffmpeg_command(ffmpeg_cmd, video_path, output_file, "compatibility")
                print(f"Trying to convert original video: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
                print(f"Final video saved to {output_file}")
                return output_file
            except Exception as e:
                print(f"Error converting video: {e}")

        # Last resort: try to use the backup or original video
        if os.path.exists(backup_video):
            try:
                shutil.copy2(backup_video, output_file)
                print(f"Copied backup video to {output_file}")
                return output_file
            except Exception as backup_e:
                print(f"Error copying backup video: {backup_e}")

        # Final fallback: copy original video directly
        try:
            shutil.copy2(video_path, output_file)
            print(f"Copied original video to {output_file}")
            return output_file
        except Exception as copy_e:
            print(f"Error copying original video: {copy_e}")
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
        # Reduced logging: print(f"Output file created successfully. Size: {file_size} bytes")
        return output_file
    else:
        print(f"ERROR: Output file was not created: {output_file}")
        return None
