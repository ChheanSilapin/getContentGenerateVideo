"""
Cleanup Manager Component - Handles file cleanup operations
Extracted from VideoGeneratorModel to reduce complexity
"""
import os
import time
import gc
import glob
import shutil
import config


class CleanupManager:
    """Handles file cleanup operations with retry mechanisms"""
    
    def __init__(self):
        pass
    
    def cleanup_after_video_complete(self, output_dir, keep_debug_files=False):
        """
        Consolidated cleanup function - single source of truth for all temporary file cleanup
        
        Args:
            output_dir: Directory to clean up
            keep_debug_files: Whether to keep debug files
            
        Returns:
            int: Number of files cleaned up
        """
        try:
            print("Starting consolidated post-completion cleanup...")
            
            # Enhanced delay to allow MoviePy and TTS processes to fully release file handles
            gc.collect()
            time.sleep(1.0)  # Longer delay for video processing
            
            # Handle images directory
            self._cleanup_images_directory(output_dir)
            
            # Get list of files to clean up
            intermediate_files = self._get_intermediate_files(output_dir, keep_debug_files)
            
            # Clean up files with enhanced retry for video files
            cleaned_count = self._cleanup_files(intermediate_files)
            
            # Clean up temporary files with patterns
            cleaned_count += self._cleanup_temp_patterns(output_dir)
            
            print(f"✅ Consolidated cleanup: removed {cleaned_count} files, keeping only final_output.mp4")
            return cleaned_count
            
        except Exception as e:
            print(f"Error in consolidated cleanup: {e}")
            return 0
    
    def _cleanup_images_directory(self, output_dir):
        """Clean up images directory if not from URL download"""
        images_dir = os.path.join(output_dir, "images")
        if os.path.exists(images_dir):
            # Note: This assumes the calling class has website_url attribute
            # In a real refactor, this would be passed as a parameter
            try:
                shutil.rmtree(images_dir)
                print(f"Cleaned up images directory: {images_dir}")
            except Exception as e:
                print(f"Warning: Could not clean up images directory: {e}")
    
    def _get_intermediate_files(self, output_dir, keep_debug_files):
        """Get list of intermediate files to clean up"""
        # Core intermediate files (always remove)
        intermediate_files = [
            os.path.join(output_dir, "slideshow.mp4"),
            os.path.join(output_dir, "video_with_audio.mp4"),
        ]
        
        # Add debug files if not keeping them
        if not keep_debug_files:
            intermediate_files.extend([
                os.path.join(output_dir, "subtitles.ass"),
                os.path.join(output_dir, "voice.mp3"),
                os.path.join(output_dir, "voice.mp3.txt"),
                os.path.join(output_dir, "temp_audio_voiceover.m4a"),
                os.path.join(output_dir, "temp-audio.m4a"),
                os.path.join(output_dir, "temp_subtitle_*.ass"),
            ])
        
        return intermediate_files
    
    def _cleanup_files(self, file_list):
        """Clean up individual files with retry mechanism"""
        cleaned_count = 0
        
        for file_path in file_list:
            if "*" in file_path:
                # Handle wildcard patterns
                matching_files = glob.glob(file_path)
                for match_file in matching_files:
                    if os.path.exists(match_file):
                        if match_file.endswith(('.mp4', '.avi', '.mov')):
                            cleaned_count += self._remove_video_file_with_retry(match_file)
                        else:
                            cleaned_count += self._remove_file_with_retry(match_file)
            else:
                # Handle regular files
                if os.path.exists(file_path):
                    if file_path.endswith(('.mp4', '.avi', '.mov')):
                        cleaned_count += self._remove_video_file_with_retry(file_path)
                    else:
                        cleaned_count += self._remove_file_with_retry(file_path)
        
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
    
    def _remove_video_file_with_retry(self, file_path, max_retries=5):
        """
        Remove a video file with enhanced retry mechanism for MoviePy file locks
        
        Args:
            file_path: Path to video file to remove
            max_retries: Maximum number of retry attempts
            
        Returns:
            int: 1 if removed successfully, 0 if failed
        """
        for attempt in range(max_retries):
            try:
                # Force garbage collection before each attempt
                gc.collect()
                
                # Longer delay for video files (MoviePy needs more time)
                if attempt > 0:
                    time.sleep(1.0)
                
                os.remove(file_path)
                print(f"Consolidated cleanup: {os.path.basename(file_path)}")
                return 1
            except PermissionError:
                if attempt < max_retries - 1:
                    print(f"Video file locked, retrying in 1.0s: {os.path.basename(file_path)} (attempt {attempt + 1}/{max_retries})")
                    time.sleep(1.0)
                else:
                    print(f"Warning: Could not remove video file {os.path.basename(file_path)} after {max_retries} attempts: MoviePy still has file lock")
                    return 0
            except Exception as e:
                print(f"Warning: Could not remove video file {os.path.basename(file_path)}: {e}")
                return 0
        
        return 0
    
    def _remove_file_with_retry(self, file_path, max_retries=3):
        """
        Remove a file with retry mechanism for locked files
        
        Args:
            file_path: Path to file to remove
            max_retries: Maximum number of retry attempts
            
        Returns:
            int: 1 if removed successfully, 0 if failed
        """
        for attempt in range(max_retries):
            try:
                os.remove(file_path)
                print(f"Consolidated cleanup: {os.path.basename(file_path)}")
                return 1
            except PermissionError:
                if attempt < max_retries - 1:
                    print(f"File locked, retrying in 0.5s: {os.path.basename(file_path)} (attempt {attempt + 1}/{max_retries})")
                    time.sleep(0.5)
                else:
                    print(f"Warning: Could not remove {os.path.basename(file_path)} after {max_retries} attempts: File still locked")
                    return 0
            except Exception as e:
                print(f"Warning: Could not remove {os.path.basename(file_path)}: {e}")
                return 0
        
        return 0
    
    def organize_output_folder_during_generation(self, output_dir):
        """
        Organize the output folder DURING generation - keep all important files
        Only remove truly temporary files that are no longer needed
        """
        try:
            # Only clean up intermediate files that are definitely not needed anymore
            truly_temp_files = [
                os.path.join(output_dir, "slideshow_temp.mp4"),
                os.path.join(output_dir, "slideshow_enhanced_temp.mp4"),
                os.path.join(output_dir, "original_video_backup.mp4"),
                os.path.join(output_dir, "temp_audio.mp3"),
                os.path.join(output_dir, "temp_video.mp4"),
            ]

            cleaned_count = 0
            for file_path in truly_temp_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"Cleaned up temp file during generation: {os.path.basename(file_path)}")
                        cleaned_count += 1
                    except Exception as e:
                        print(f"Warning: Could not remove {os.path.basename(file_path)}: {e}")

            print(f"✅ Cleaned {cleaned_count} temporary files during generation")
            
        except Exception as e:
            print(f"Error organizing during generation: {e}")
    
    def cleanup_on_stop(self, output_dir):
        """Clean up files when process is stopped by user"""
        if output_dir and os.path.exists(output_dir):
            try:
                print(f"Cleaning up output directory: {output_dir}")
                shutil.rmtree(output_dir)
                print(f"Removed output directory after stop: {output_dir}")
            except Exception as e:
                print(f"Warning: Could not clean up output directory: {e}")
    
    def cleanup_extracted_frames(self, images_dir):
        """
        Clean up extracted frames from video processing to keep output folder clean
        
        Args:
            images_dir: Directory containing extracted frames
        """
        try:
            if os.path.exists(images_dir):
                shutil.rmtree(images_dir)
                print(f"Cleaned up extracted frames directory: {images_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up extracted frames directory: {e}")
