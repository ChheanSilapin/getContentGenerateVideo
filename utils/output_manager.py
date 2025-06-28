#!/usr/bin/env python3
"""
Output Manager - Handles final video placement, filename conflict resolution, and centralized cleanup
"""

import os
import shutil
import glob
import time
import gc
from pathlib import Path
from utils.filename_validator import sanitize_filename


class OutputManager:
    """Manages final video output placement, filename conflicts, and centralized cleanup"""

    def __init__(self, user_output_directory):
        """
        Initialize OutputManager

        Args:
            user_output_directory (str): User's chosen output directory
        """
        self.user_output_directory = user_output_directory
        self.ensure_output_directory()

        # Centralized cleanup configuration
        self.cleanup_config = {
            'video_retry_attempts': 5,
            'file_retry_attempts': 3,
            'retry_delay': 0.5,
            'moviepy_cleanup_delay': 2.0,
            'force_cleanup_delay': 3.0
        }
    
    def ensure_output_directory(self):
        """Ensure the output directory exists"""
        try:
            os.makedirs(self.user_output_directory, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create output directory {self.user_output_directory}: {e}")
    
    def get_unique_filename(self, desired_filename, extension=".mp4"):
        """
        Get a unique filename in the output directory, handling conflicts with numbering
        
        Args:
            desired_filename (str): Desired filename without extension
            extension (str): File extension (default: .mp4)
            
        Returns:
            str: Unique filename with extension
        """
        # Sanitize the desired filename
        clean_filename = sanitize_filename(desired_filename) if desired_filename else "video"
        
        # Create the full path
        base_path = os.path.join(self.user_output_directory, f"{clean_filename}{extension}")
        
        # If file doesn't exist, use it as-is
        if not os.path.exists(base_path):
            return f"{clean_filename}{extension}"
        
        # File exists, find a unique name with numbering
        counter = 1
        while True:
            numbered_filename = f"{clean_filename}_{counter}{extension}"
            numbered_path = os.path.join(self.user_output_directory, numbered_filename)
            
            if not os.path.exists(numbered_path):
                return numbered_filename
            
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 9999:
                import time
                timestamp = int(time.time())
                return f"{clean_filename}_{timestamp}{extension}"
    
    def move_final_video(self, temp_video_path, custom_filename=None, source_files=None, default_name="video"):
        """
        Move final video from temporary location to user's output directory

        Args:
            temp_video_path (str): Path to the temporary video file
            custom_filename (str): Custom filename provided by user (optional)
            source_files (list): List of source file paths for intelligent default naming
            default_name (str): Fallback name to use if no custom filename or source files

        Returns:
            str: Path to the final video file in user's output directory
        """
        try:
            if not os.path.exists(temp_video_path):
                print(f"Error: Temporary video file not found: {temp_video_path}")
                return None

            # Determine the desired filename with intelligent defaults
            desired_name = self._determine_output_filename(custom_filename, source_files, default_name)

            # Get unique filename with conflict resolution
            final_filename = self.get_unique_filename(desired_name)
            final_path = os.path.join(self.user_output_directory, final_filename)

            # Move the file
            shutil.move(temp_video_path, final_path)

            print(f"✅ Final video saved: {final_path}")
            return final_path

        except Exception as e:
            print(f"Error moving final video: {e}")
            # Try copying as fallback
            try:
                desired_name = self._determine_output_filename(custom_filename, source_files, default_name)
                final_filename = self.get_unique_filename(desired_name)
                final_path = os.path.join(self.user_output_directory, final_filename)
                shutil.copy2(temp_video_path, final_path)
                print(f"✅ Final video copied: {final_path}")
                return final_path
            except Exception as copy_e:
                print(f"Error copying final video: {copy_e}")
                return None
    
    # ===== CENTRALIZED CLEANUP SYSTEM =====

    def cleanup_after_video_complete(self, output_dir, keep_debug_files=False):
        """
        Centralized cleanup after video completion - consolidates all cleanup logic

        Args:
            output_dir (str): Directory to clean up
            keep_debug_files (bool): Whether to keep debug files

        Returns:
            int: Number of files cleaned up
        """
        try:
            if not keep_debug_files:
                print("🧹 Starting centralized post-completion cleanup...")

            # Force MoviePy cleanup first
            self._force_moviepy_cleanup()
            time.sleep(self.cleanup_config['moviepy_cleanup_delay'])

            cleaned_count = 0

            # Clean up images directory
            cleaned_count += self._cleanup_images_directory(output_dir)

            # Clean up intermediate files
            cleaned_count += self._cleanup_intermediate_files(output_dir, keep_debug_files)

            # Clean up temporary file patterns
            cleaned_count += self._cleanup_temp_patterns(output_dir)

            # Clean up individual video files if this is a batch operation
            cleaned_count += self._cleanup_individual_videos(output_dir)

            if not keep_debug_files and cleaned_count > 0:
                print(f"✅ Centralized cleanup: removed {cleaned_count} files")
            return cleaned_count

        except Exception as e:
            print(f"❌ Error in centralized cleanup: {e}")
            return 0

    def cleanup_temp_directory(self, temp_dir):
        """
        Clean up temporary directory with enhanced safety checks

        Args:
            temp_dir (str): Path to temporary directory to clean up
        """
        try:
            if not os.path.exists(temp_dir) or not os.path.isdir(temp_dir):
                return

            # SAFETY CHECK: Don't remove the main user output directory
            if temp_dir == self.user_output_directory:
                print(f"⚠️ Skipping cleanup of main output directory: {temp_dir}")
                return

            # Additional safety check: Only remove directories with timestamp patterns
            dir_name = os.path.basename(temp_dir)
            if not (dir_name.startswith("video_") and "_" in dir_name):
                print(f"⚠️ Skipping cleanup of non-temporary directory: {dir_name}")
                return

            # Force cleanup before directory removal
            self._force_moviepy_cleanup()
            time.sleep(1.0)

            shutil.rmtree(temp_dir)

        except Exception as e:
            print(f"⚠️ Could not clean up temporary directory {temp_dir}: {e}")

    def cleanup_individual_temp_directories(self, processed_videos):
        """
        Clean up temporary directories created during individual video processing

        Args:
            processed_videos (list): List of processed video data
        """
        if not processed_videos:
            print("🗂️ No temporary directories to clean up")
            return

        print(f"🗂️ Cleaning up temporary directories for {len(processed_videos)} videos...")

        # Force comprehensive cleanup
        self._force_moviepy_cleanup()
        time.sleep(1.0)

        cleaned_dirs = 0
        for video_data in processed_videos:
            if isinstance(video_data, dict) and 'output_dir' in video_data:
                temp_dir = video_data['output_dir']
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        self.cleanup_temp_directory(temp_dir)
                        cleaned_dirs += 1
                    except Exception as e:
                        print(f"⚠️ Could not clean up directory {temp_dir}: {e}")

        print(f"✅ Cleaned up {cleaned_dirs} temporary directories")

    def cleanup_on_stop(self, output_dir):
        """
        Clean up files when process is stopped by user

        Args:
            output_dir (str): Directory to clean up
        """
        if output_dir and os.path.exists(output_dir):
            try:
                print(f"🛑 Cleaning up after stop: {output_dir}")

                # Force cleanup first
                self._force_moviepy_cleanup()
                time.sleep(1.0)

                shutil.rmtree(output_dir)
                print(f"🗑️ Removed output directory after stop: {output_dir}")
            except Exception as e:
                print(f"⚠️ Could not clean up output directory: {e}")

    def cleanup_extracted_frames(self, images_dir):
        """
        Clean up extracted frames from video processing

        Args:
            images_dir (str): Directory containing extracted frames
        """
        try:
            if os.path.exists(images_dir):
                shutil.rmtree(images_dir)
        except Exception as e:
            print(f"⚠️ Could not clean up extracted frames: {e}")

    def cleanup_temp_files(self, *file_paths):
        """
        Clean up individual temporary files with retry mechanism

        Args:
            *file_paths: Variable number of file paths to clean up
        """
        cleaned_count = 0
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                if file_path.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    cleaned_count += self._remove_video_file_with_retry(file_path)
                else:
                    cleaned_count += self._remove_file_with_retry(file_path)
        return cleaned_count

    # ===== PRIVATE CLEANUP HELPER METHODS =====

    def _force_moviepy_cleanup(self):
        """Force cleanup of MoviePy resources and file handles"""
        try:
            # Force garbage collection multiple times
            for _ in range(3):
                gc.collect()
                time.sleep(0.1)

            # Try to clear MoviePy's internal caches
            try:
                import moviepy.config as mp_config
                if hasattr(mp_config, '_FFMPEG_BINARY'):
                    mp_config._FFMPEG_BINARY = None
            except (ImportError, AttributeError):
                pass

            # Additional delay to ensure all file handles are released
            time.sleep(0.5)

        except Exception:
            pass  # Silent failure - best effort cleanup

    def _cleanup_images_directory(self, output_dir):
        """Clean up images directory"""
        cleaned_count = 0
        images_dir = os.path.join(output_dir, "images")
        if os.path.exists(images_dir):
            try:
                shutil.rmtree(images_dir)
                print(f" Cleaned up images directory: {images_dir}")
                cleaned_count = 1
            except Exception as e:
                print(f"Could not clean up images directory: {e}")
        return cleaned_count

    def _cleanup_intermediate_files(self, output_dir, keep_debug_files):
        """Clean up intermediate files based on configuration"""
        # Core intermediate files (always remove)
        intermediate_files = [
            os.path.join(output_dir, "slideshow.mp4"),
            os.path.join(output_dir, "video_with_audio.mp4"),
            os.path.join(output_dir, "original_video_backup.mp4"),
            os.path.join(output_dir, "slideshow_temp.mp4"),
            os.path.join(output_dir, "slideshow_enhanced_temp.mp4"),
            os.path.join(output_dir, "temp_audio.mp3"),
            os.path.join(output_dir, "temp_video.mp4"),
        ]

        # Add debug files if not keeping them
        if not keep_debug_files:
            intermediate_files.extend([
                os.path.join(output_dir, "subtitles.ass"),
                os.path.join(output_dir, "voice.mp3"),
                os.path.join(output_dir, "voice.mp3.txt"),
                os.path.join(output_dir, "temp_audio_voiceover.m4a"),
                os.path.join(output_dir, "temp-audio.m4a"),
            ])

        cleaned_count = 0
        for file_path in intermediate_files:
            if os.path.exists(file_path):
                if file_path.endswith(('.mp4', '.avi', '.mov')):
                    cleaned_count += self._remove_video_file_with_retry(file_path)
                else:
                    cleaned_count += self._remove_file_with_retry(file_path)

        # Handle wildcard patterns
        wildcard_patterns = [
            os.path.join(output_dir, "temp_subtitle_*.ass"),
        ]

        for pattern in wildcard_patterns:
            matching_files = glob.glob(pattern)
            for match_file in matching_files:
                if os.path.exists(match_file):
                    cleaned_count += self._remove_file_with_retry(match_file)

        return cleaned_count

    def _cleanup_temp_patterns(self, output_dir):
        """Clean up temporary files with common patterns"""
        cleaned_count = 0
        temp_patterns = [
            os.path.join(output_dir, "*TEMP_MPY_wvf_snd.mp3"),  # MoviePy temp audio
            os.path.join(output_dir, "*_temp*"),                # General temp files
            os.path.join(output_dir, "temp_*"),                 # Temp prefixed files
        ]

        for pattern in temp_patterns:
            matching_files = glob.glob(pattern)
            for temp_file in matching_files:
                # Don't remove final_output.mp4 or other important files
                if "final_output" not in os.path.basename(temp_file).lower():
                    cleaned_count += self._remove_file_with_retry(temp_file)

        return cleaned_count

    def _cleanup_individual_videos(self, output_dir):
        """Clean up individual video files after batch processing"""
        cleaned_count = 0

        # For group processing, we should NOT clean up numbered files automatically
        # because the final merged file might have a number suffix due to conflict resolution
        # This function should only be called with explicit file lists, not pattern matching

        # Skip automatic cleanup of numbered files to prevent deleting final merged videos
        # Individual video cleanup should be handled explicitly by the batch processor
        # with specific file paths, not pattern matching

        return cleaned_count

    def _remove_video_file_with_retry(self, file_path):
        """
        Remove a video file with enhanced retry mechanism for MoviePy file locks

        Args:
            file_path (str): Path to video file to remove

        Returns:
            int: 1 if removed successfully, 0 if failed
        """
        max_retries = self.cleanup_config['video_retry_attempts']

        def _remove_file():
            gc.collect()
            os.remove(file_path)
            if not file_path.endswith('original_video_backup.mp4'):
                print(f" Cleaned: {os.path.basename(file_path)}")

        # Try with retry mechanism
        for attempt in range(max_retries):
            try:
                _remove_file()
                return 1
            except PermissionError:
                if attempt < max_retries - 1:
                    print(f" Video file locked, retrying: {os.path.basename(file_path)} (attempt {attempt + 1}/{max_retries})")
                    time.sleep(self.cleanup_config['retry_delay'] * (attempt + 1))
                else:
                    # Final attempt with MoviePy cleanup
                    try:
                        print(f" Final attempt with MoviePy cleanup: {os.path.basename(file_path)}")
                        self._force_moviepy_cleanup()
                        time.sleep(self.cleanup_config['force_cleanup_delay'])
                        _remove_file()
                        return 1
                    except Exception as final_e:
                        print(f" Could not remove video file {os.path.basename(file_path)}: {final_e}")
                        return 0
            except Exception as e:
                print(f"Error removing video file {os.path.basename(file_path)}: {e}")
                return 0

        return 0

    def _remove_file_with_retry(self, file_path):
        """
        Remove a file with retry mechanism for locked files

        Args:
            file_path (str): Path to file to remove

        Returns:
            int: 1 if removed successfully, 0 if failed
        """
        max_retries = self.cleanup_config['file_retry_attempts']

        for attempt in range(max_retries):
            try:
                os.remove(file_path)
                return 1
            except PermissionError:
                if attempt < max_retries - 1:
                    print(f"File locked, retrying: {os.path.basename(file_path)} (attempt {attempt + 1}/{max_retries})")
                    time.sleep(self.cleanup_config['retry_delay'])
                else:
                    print(f" Could not remove {os.path.basename(file_path)}: File still locked after {max_retries} attempts")
                    return 0
            except Exception as e:
                print(f"Could not remove {os.path.basename(file_path)}: {e}")
                return 0

        return 0

    def _determine_output_filename(self, custom_filename, source_files, default_name):
        """
        Determine the output filename using intelligent defaults

        Args:
            custom_filename (str): Custom filename provided by user
            source_files (list): List of source file paths
            default_name (str): Fallback default name

        Returns:
            str: Determined filename (without extension)
        """
        # Check if custom filename is provided and not placeholder text
        if custom_filename and custom_filename.strip():
            cleaned_custom = custom_filename.strip()
            # Check if it's not placeholder text
            if cleaned_custom not in ["Custom filename (optional)", "Enter custom filename (optional)"]:
                return cleaned_custom

        # Use intelligent default based on source files
        if source_files and len(source_files) > 0:
            # Get the first source file
            first_file = source_files[0]
            if first_file:
                # Extract filename without extension (don't require file to exist for naming)
                base_name = os.path.splitext(os.path.basename(first_file))[0]
                if base_name:
                    # Sanitize the source filename to ensure compatibility
                    sanitized_base_name = sanitize_filename(base_name)
                    if sanitized_base_name:
                        return sanitized_base_name

        # Fallback to default name
        return default_name

    def get_final_output_path(self, custom_filename=None, source_files=None, default_name="video"):
        """
        Get the final output path without actually creating the file

        Args:
            custom_filename (str): Custom filename provided by user (optional)
            source_files (list): List of source file paths for intelligent default naming
            default_name (str): Default name to use if no custom filename or source files

        Returns:
            str: Full path where the final video will be saved
        """
        # Determine the desired filename with intelligent defaults
        desired_name = self._determine_output_filename(custom_filename, source_files, default_name)

        # Get unique filename with conflict resolution
        final_filename = self.get_unique_filename(desired_name)
        return os.path.join(self.user_output_directory, final_filename)


def get_output_manager(user_settings=None):
    """
    Get OutputManager instance with user's output directory
    
    Args:
        user_settings (dict): User settings containing output folder preference
        
    Returns:
        OutputManager: Configured OutputManager instance
    """
    from utils.helpers import get_output_directory
    
    # Get user's preferred output directory
    output_dir = get_output_directory(user_settings)
    
    return OutputManager(output_dir)
