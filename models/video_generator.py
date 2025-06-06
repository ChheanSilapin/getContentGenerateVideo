"""
VideoGeneratorModel - Core model for video generation process
"""
import os
import sys
from datetime import datetime
from version import __version__
import config  # Import config for cleanup settings

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import config
from config import DEFAULT_ASPECT_RATIO

# Import the generation functions
try:
    from services.audio_service import generate_audio
    from services.image_service import copy_selected_images
    from services.video_service import create_enhanced_slideshow
    from services.subtitle_service import generate_subtitles
    from Final_Video import merge_video_subtitle
except ImportError as e:
    print(f"Warning: Could not import some services: {e}")
    # Try individual imports as fallback
    try:
        from services.audio_service import generate_audio
    except ImportError:
        generate_audio = None
        print("Could not import generate_audio")
    
    try:
        from services.image_service import copy_selected_images
    except ImportError:
        copy_selected_images = None
        print("Could not import copy_selected_images")
    
    try:
        from services.video_service import create_enhanced_slideshow
    except ImportError:
        create_enhanced_slideshow = None
        print("Could not import create_enhanced_slideshow")
    
    try:
        from services.subtitle_service import generate_subtitles
    except ImportError:
        generate_subtitles = None
        print("Could not import generate_subtitles")
    
    try:
        from Final_Video import merge_video_subtitle
    except ImportError:
        merge_video_subtitle = None
        print("Could not import merge_video_subtitle")

# Import title/content extraction from centralized location
from utils.text_processing import get_title_content

class VideoGeneratorModel:
    """Model for handling video generation"""
    def __init__(self):
        """Initialize the model"""
        self.text_input = None
        self.image_source = None
        self.website_url = None
        self.local_folder = None
        self.selected_images = []
        self.output_folder = None
        self.processing_option = "cpu"  # Default to CPU
        self.progress_callback = None
        self.batch_jobs = []  # List to store multiple generation jobs
        self.current_job_index = 0

        # Video aspect ratio
        self.aspect_ratio = DEFAULT_ASPECT_RATIO

        # Enhancement options
        self.use_effects = True
        self.zoom_effect = True
        self.fade_effect = True
        self.enhancement_options = {
            "color_correction": True,
            "background_replacement": False,
            "audio_enhancement": True,
            "motion_graphics": False,
            "framing": True,
            "color_correction_intensity": 1.0,
            "framing_crop_percent": 0.95,
            "audio_volume_boost": 1.2,
            "motion_graphics_opacity": 0.15,
            "contrast": 1.1,
            "brightness": 0.05,
            "saturation": 1.2,
            "sharpness": 1.0,
            "noise_reduction": True,
            "apply_ffmpeg": False,  # Disable FFmpeg enhancements by default
            "aspect_ratio": DEFAULT_ASPECT_RATIO,  # Add aspect ratio to enhancement options
            "voice_emotion": "neutral",  # Added voice_emotion to enhancement options
            "subtitle_style": "modern_glow"  # Added subtitle_style to enhancement options
        }

        # Ensure enhancement_options is properly initialized
        self.option_options = self.enhancement_options.copy()

    def set_progress_callback(self, callback):
        """Set a callback function for progress updates"""
        self.progress_callback = callback

    def update_progress(self, value, message=None):
        """Update progress value and message"""
        if self.progress_callback:
            self.progress_callback(value, message)

    def generate_video(self, stop_event=None):
        """
        Generate a video from text and images

        Args:
            stop_event: Threading event to stop the process

        Returns:
            tuple: (subtitle_path, video_path, output_dir)
        """
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            return None, None, None

        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Store the stop_event as an instance variable so other methods can access it
        self.stop_event = stop_event

        # Use custom output folder if provided
        if self.output_folder and os.path.isdir(self.output_folder):
            output_dir = os.path.join(self.output_folder, f"video_{timestamp}")
        else:
            # Use the output directory set by main.py, or fallback to default
            base_output_dir = os.environ.get('VIDEO_GENERATOR_OUTPUT_DIR', 'output')
            output_dir = os.path.join(base_output_dir, f"video_{timestamp}")

        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")

        # Store output_dir as instance variable for cleanup if needed
        self.current_output_dir = output_dir

        # Create subdirectories
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        # Step 1: Generate audio from text
        print("\n--- Step 1: Generating Audio ---")
        self.update_progress(10, "Generating audio from text...")
        audio_file = os.path.join(output_dir, "voice.mp3")
        
        # Get voice emotion from enhancement options
        enhancement_options = getattr(self, 'enhancement_options', {})
        voice_emotion = enhancement_options.get('voice_emotion', 'neutral')
        print(f"Using voice emotion: {voice_emotion}")
        
        if not generate_audio(self.text_input, audio_file, emotion=voice_emotion):
            print("ERROR: Failed to generate audio.")
            self.update_progress(0, "Failed to generate audio")
            return None, None, None

        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            return None, None, None

        self.update_progress(30, "Audio generated successfully")

        # Step 2: Get images
        print("\n--- Step 2: Processing Images ---")

        if self.image_source == "1":  # Website URL
            # Skip downloading images if we already have selected images
            if not self.selected_images:
                print("ERROR: No images selected from website.")
                self.update_progress(0, "No images selected from website")
                return None, None, None

            print(f"Using {len(self.selected_images)} selected images from website")
            self.update_progress(35, f"Copying {len(self.selected_images)} selected images")

            # Make sure the images directory exists
            if not os.path.exists(images_dir):
                os.makedirs(images_dir, exist_ok=True)

            # Copy the selected images to the images directory
            if not copy_selected_images(self.selected_images, images_dir):
                print("ERROR: Failed to copy selected images.")
                self.update_progress(0, "Failed to copy selected images")
                return None, None, None
        elif self.image_source == "3":  # Selected images
            print(f"Using {len(self.selected_images)} selected images")
            self.update_progress(35, f"Copying {len(self.selected_images)} selected images")
            if not copy_selected_images(self.selected_images, images_dir):
                print("ERROR: Failed to copy selected images.")
                self.update_progress(0, "Failed to copy selected images")
                return None, None, None
        else:  # Local folder
            print(f"Copying images from: {self.local_folder}")
            self.update_progress(35, f"Copying images from: {self.local_folder}")
            # Use copy_selected_images instead of copy_images_from_folder
            import glob
            # Get all image files from the folder
            image_files = []
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                image_files.extend(glob.glob(os.path.join(self.local_folder, f"*{ext}")))
                image_files.extend(glob.glob(os.path.join(self.local_folder, f"*{ext.upper()}")))

            if not image_files:
                print("ERROR: No image files found in folder.")
                self.update_progress(0, "No image files found in folder")
                return None, None, None

            if not copy_selected_images(image_files, images_dir):
                print("ERROR: Failed to copy images from folder.")
                self.update_progress(0, "Failed to copy images from folder")
                return None, None, None

        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            return None, None, None

        self.update_progress(50, "Images processed successfully")

        # Step 3: Create video
        print("\n--- Step 3: Creating Video ---")
        self.update_progress(55, "Creating video...")
        video_file = os.path.join(output_dir, "slideshow.mp4")
        title, content = get_title_content(self.text_input)

        # Get effect settings
        use_effects = getattr(self, 'use_effects', True)
        zoom_effect = getattr(self, 'zoom_effect', True)
        fade_effect = getattr(self, 'fade_effect', True)

        # Get aspect ratio settings
        aspect_ratio = getattr(self, 'aspect_ratio', DEFAULT_ASPECT_RATIO)

        # Update enhancement options with current aspect ratio
        enhancement_options = getattr(self, 'enhancement_options', {}).copy()
        enhancement_options['aspect_ratio'] = aspect_ratio

        # Set environment variables for image fitting
        if 'image_fit_method' in enhancement_options:
            os.environ["IMAGE_FIT_METHOD"] = enhancement_options["image_fit_method"]
            print(f"Setting image fit method to: {enhancement_options['image_fit_method']}")
        else:
            os.environ["IMAGE_FIT_METHOD"] = "contain"  # Changed back to "contain" to show improved version
 
        # Pass the processing option, effect settings, and aspect ratio to the create_enhanced_slideshow function
        result = create_enhanced_slideshow(
            images_dir,
            title,
            content,
            audio_file,
            video_file,
            use_gpu=(self.processing_option == "gpu"),
            use_effects=use_effects,
            zoom_effect=zoom_effect,
            fade_effect=fade_effect,
            enhance=True,  # Enable enhancements
            enhancement_options=enhancement_options,
            stop_event=stop_event,  # Pass the stop event
            aspect_ratio=aspect_ratio  # Pass the aspect ratio
        )

        # Check if the process was stopped by user
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            self._cleanup_on_stop()  # Clean up files
            return None, None, None

        # Only report an error if the result is False (not stopped by user)
        if not result:
            print("ERROR: Failed to create video.")
            self.update_progress(0, "Failed to create video")
            return None, None, None

        # Video creation completed, starting subtitle generation
        self.update_progress(70, "Video created successfully")

        # Step 4: Generate subtitles
        print("\n--- Step 4: Generating Subtitles ---")
        self.update_progress(75, "Generating subtitles...")
        subtitle_file = os.path.join(output_dir, "subtitles.ass")
        
        # Get subtitle style from enhancement options
        subtitle_style = self.enhancement_options.get("subtitle_style", "modern_glow")
        print(f"Using subtitle style: {subtitle_style}")
        
        # Generate subtitles for the video
        if not generate_subtitles(self.text_input, video_file, audio_file, subtitle_file, subtitle_style):
            print("ERROR: Failed to generate subtitles.")
            self.update_progress(0, "Failed to generate subtitles")
            return None, None, None

        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            return None, None, None

        self.update_progress(90, "Subtitles generated successfully")

        # Step 5: Finalize video with subtitles
        final_video = self.finalize_video(subtitle_file, video_file, output_dir, stop_event)

        # EXPLICIT MOVIEPY CLEANUP - Release file handles immediately after processing
        try:
            import gc
            # Force garbage collection to release MoviePy references
            gc.collect()
            print("Released MoviePy file handles")
        except Exception as e:
            print(f"Note: MoviePy cleanup attempt: {e}")

        if final_video:
            print(f"Video processing completed successfully: {final_video}")
            
            # AUTO-CLEANUP for single videos - same as batch processing
            cleanup_enabled = getattr(config, 'AUTO_CLEANUP_AFTER_COMPLETION', True)
            if cleanup_enabled:
                print("Starting automatic cleanup for single video...")
                try:
                    # Use the consolidated cleanup function
                    cleaned_count = self.cleanup_after_video_complete(
                        output_dir, 
                        keep_debug_files=False  # Clean everything except final_output.mp4
                    )
                    if cleaned_count > 0:
                        print(f"Auto-cleanup completed: Removed {cleaned_count} intermediate files")
                        print("Only final_output.mp4 remains")
                    else:
                        print("No cleanup needed - files already clean")
                except Exception as e:
                    print(f"Warning: Cleanup failed for single video: {e}")
            else:
                print("Auto-cleanup disabled in config - keeping all files")
            
            # Return tuple format expected by UI (subtitle_file, final_video, output_dir)
            return subtitle_file, final_video, output_dir
        else:
            print("Failed to finalize video")
            return None, None, None

    def finalize_video(self, subtitlePath, videoPath, output_dir, stop_event=None):
        """
        Finalize the video by merging with subtitles

        Args:
            subtitlePath: Path to subtitle file
            videoPath: Path to video file
            output_dir: Output directory
            stop_event: Threading event to stop the process

        Returns:
            str: Path to final video
        """
        print("\n--- Step 5: Finalizing Video ---")
        self.update_progress(95, "Finalizing video...")
        final_output = os.path.join(output_dir, "final_output.mp4")

        result = merge_video_subtitle(videoPath, subtitlePath, final_output)

        if result:
            print(f"Video generated successfully: {result}")
            self.update_progress(100, f"Video generated successfully: {os.path.basename(result)}")

            # FIXED: Only organize during generation, not cleanup final files yet
            self._organize_output_folder_during_generation(output_dir)
            
            # Return result first, cleanup will happen separately
            return result
        else:
            print("Failed to finalize video")
            self.update_progress(0, "Failed to finalize video")
            return None

    def _organize_output_folder_during_generation(self, output_dir):
        """
        Organize the output folder DURING generation - keep all important files
        Only remove truly temporary files that are no longer needed
        """
        try:
            # Only clean up intermediate files that are definitely not needed anymore
            truly_temp_files = [
                os.path.join(output_dir, "slideshow_temp.mp4"),               # Temp video
                os.path.join(output_dir, "slideshow_enhanced_temp.mp4"),      # Enhanced temp video
                os.path.join(output_dir, "original_video_backup.mp4"),        # Backup video
                os.path.join(output_dir, "temp_audio.mp3"),                   # Temp audio
                os.path.join(output_dir, "temp_video.mp4"),                   # Any temp video
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

    def cleanup_after_video_complete(self, output_dir, keep_debug_files=False):
        """
        Consolidated cleanup function - single source of truth for all temporary file cleanup
        This should be called by the UI after video generation is complete
        """
        try:
            print("Starting consolidated post-completion cleanup...")
            
            # Enhanced delay to allow MoviePy and TTS processes to fully release file handles
            import time
            import gc
            
            # Force garbage collection to release any lingering references
            gc.collect()
            
            # Longer delay for video processing (MoviePy needs more time)
            time.sleep(1.0)
            
            # Check if images were downloaded from URL - if so, keep them
            images_dir = os.path.join(output_dir, "images")
            if os.path.exists(images_dir):
                if hasattr(self, 'website_url') and self.website_url:
                    print(f"Keeping downloaded images from URL: {images_dir}")
                else:
                    import shutil
                    shutil.rmtree(images_dir)
                    print(f"Cleaned up images directory: {images_dir}")

            # CONSOLIDATED: All intermediate files to remove (keep only final_output.mp4)
            intermediate_files = [
                os.path.join(output_dir, "slideshow.mp4"),                    # Intermediate video
                os.path.join(output_dir, "video_with_audio.mp4"),             # ADDED: Video with audio (main intermediate file)
            ]
            
            # Add all temporary/debug files to cleanup list if not keeping them
            if not keep_debug_files:
                intermediate_files.extend([
                    # Core temporary files
                    os.path.join(output_dir, "subtitles.ass"),                 # Subtitle file
                    os.path.join(output_dir, "voice.mp3"),                     # Generated voice
                    os.path.join(output_dir, "voice.mp3.txt"),                 # Voice metadata
                    # Additional temporary files
                    os.path.join(output_dir, "temp_audio_voiceover.m4a"),      # Voice-over temp
                    os.path.join(output_dir, "temp-audio.m4a"),                # Audio temp
                    os.path.join(output_dir, "temp_subtitle_*.ass"),           # Temp subtitles (pattern)
                ])

            cleaned_count = 0
            
            # Clean up individual files with enhanced retry for video files
            for file_path in intermediate_files:
                if "*" in file_path:
                    # Handle wildcard patterns
                    import glob
                    matching_files = glob.glob(file_path)
                    for match_file in matching_files:
                        if os.path.exists(match_file):
                            # Use enhanced retry for video files
                            if match_file.endswith(('.mp4', '.avi', '.mov')):
                                cleaned_count += self._remove_video_file_with_retry(match_file)
                            else:
                                cleaned_count += self._remove_file_with_retry(match_file)
                else:
                    # Handle regular files
                    if os.path.exists(file_path):
                        # Use enhanced retry for video files
                        if file_path.endswith(('.mp4', '.avi', '.mov')):
                            cleaned_count += self._remove_video_file_with_retry(file_path)
                        else:
                            cleaned_count += self._remove_file_with_retry(file_path)

            # Clean up MoviePy and other temporary files with common patterns
            import glob
            temp_patterns = [
                os.path.join(output_dir, "*TEMP_MPY_wvf_snd.mp3"),             # MoviePy temp audio
                os.path.join(output_dir, "*_temp*"),                           # General temp files
                os.path.join(output_dir, "temp_*"),                            # Temp prefixed files
            ]
            
            for pattern in temp_patterns:
                matching_files = glob.glob(pattern)
                for temp_file in matching_files:
                    # Don't remove final_output.mp4 or other important files
                    if "final_output" not in os.path.basename(temp_file).lower():
                        cleaned_count += self._remove_file_with_retry(temp_file)

            if keep_debug_files:
                debug_files_kept = []
                debug_files = ["subtitles.ass", "voice.mp3", "voice.mp3.txt"]
                for debug_file in debug_files:
                    file_path = os.path.join(output_dir, debug_file)
                    if os.path.exists(file_path):
                        debug_files_kept.append(debug_file)
                
                            # Keep debug files if requested

            print(f"✅ Consolidated cleanup: removed {cleaned_count} files, keeping only final_output.mp4")
            return cleaned_count
            
        except Exception as e:
            print(f"Error in consolidated cleanup: {e}")
            return 0

    def _remove_video_file_with_retry(self, file_path, max_retries=5):
        """
        Remove a video file with enhanced retry mechanism for MoviePy file locks
        
        Args:
            file_path: Path to video file to remove
            max_retries: Maximum number of retry attempts (increased for video files)
            
        Returns:
            int: 1 if removed successfully, 0 if failed
        """
        import time
        import gc
        
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
            except PermissionError as e:
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
        import time
        
        for attempt in range(max_retries):
            try:
                os.remove(file_path)
                print(f"Consolidated cleanup: {os.path.basename(file_path)}")
                return 1
            except PermissionError as e:
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

    def preview_images_from_url(self, url):
        """
        Download images from URL for preview

        Args:
            url: Website URL

        Returns:
            list: List of image paths
        """
        from services.image_service import download_images_for_preview

        # Create a temporary directory
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix="preview_")

        # Download images
        self.update_progress(10, f"Downloading images from: {url}")
        image_paths = download_images_for_preview(url, temp_dir)

        if not image_paths:
            self.update_progress(0, "Failed to download images for preview")
            return []

        self.update_progress(30, f"Downloaded {len(image_paths)} images for preview")
        return image_paths

    def add_batch_job(self, text_input, image_source, selected_images=None, website_url=None, local_folder=None):
        """Add a job to the batch processing queue"""
        job = {
            "text_input": text_input,
            "image_source": image_source,
            "selected_images": selected_images or [],
            "website_url": website_url or "",
            "local_folder": local_folder or "",
            "status": "pending"
        }
        self.batch_jobs.append(job)
        return len(self.batch_jobs)  # Return job ID (1-based index)

    def process_batch(self, stop_event=None):
        """Process all jobs in the batch queue"""
        results = []
        self.current_job_index = 0
        total_jobs = len(self.batch_jobs)

        for i, job in enumerate(self.batch_jobs):
            if stop_event and stop_event.is_set():
                break

            # Calculate overall progress percentage
            overall_progress = int((i / total_jobs) * 100)
            self.update_progress(overall_progress, f"Starting job {i+1}/{total_jobs}")

            # Set up the current job
            self.text_input = job["text_input"]
            self.image_source = job["image_source"]
            self.selected_images = job["selected_images"].copy() if job["selected_images"] else []
            self.website_url = job["website_url"]
            self.local_folder = job["local_folder"]
            self.processing_option = "cpu"  # Default to CPU for batch processing

            # Process the job
            try:
                job["status"] = "processing"

                # Create a wrapper for the progress callback to show both job progress and overall progress
                original_callback = self.progress_callback

                def job_progress_callback(value, message=None):
                    # Calculate combined progress: base progress for completed jobs + partial progress for current job
                    # Each job contributes equally to the total progress
                    job_weight = 100 / total_jobs
                    # Base progress from completed jobs
                    base_progress = int(i * job_weight)
                    # Current job contribution (scaled by job weight)
                    current_job_progress = int((value / 100) * job_weight)
                    # Combined progress
                    combined_progress = base_progress + current_job_progress
                    # Ensure we never exceed 100%
                    combined_progress = min(combined_progress, 100)

                    # Create cleaner progress message - show percentage instead of confusing slash
                    if message:
                        job_message = f"Video {i+1}/{total_jobs}: {message}"
                    else:
                        # Default to percentage when no specific message
                        job_message = f"{combined_progress}% - Processing video {i+1} of {total_jobs}"
                    
                    if original_callback:
                        original_callback(combined_progress, job_message)

                # Temporarily replace the callback
                self.progress_callback = job_progress_callback

                # Generate the video
                subtitle_path, video_path, output_dir = self.generate_video(stop_event)

                if subtitle_path and video_path and output_dir:
                    final_video = self.finalize_video(subtitle_path, video_path, output_dir, stop_event)
                    results.append((job, final_video))
                    job["status"] = "completed"
                    # Update progress to show this job is complete
                    if original_callback:
                        job_complete_progress = int((i + 1) * (100 / total_jobs))
                        original_callback(job_complete_progress, f"✅ Completed video {i+1} of {total_jobs}")
                else:
                    results.append((job, None))
                    job["status"] = "failed"
                    # Update progress to show this job is complete but failed
                    if original_callback:
                        job_complete_progress = int((i + 1) * (100 / total_jobs))
                        original_callback(job_complete_progress, f"❌ Failed video {i+1} of {total_jobs}")

                # Restore the original callback
                self.progress_callback = original_callback

            except Exception as e:
                print(f"Error processing job {i+1}: {e}")
                results.append((job, None))
                job["status"] = "failed"

                # Restore the original callback
                self.progress_callback = original_callback

            # Update the current job index
            self.current_job_index = i + 1

        # Final progress update
        self.update_progress(100, f"Batch processing completed: {len([r for _, r in results if r])} of {total_jobs} successful")
        return results

    def add_video_batch_job(self, text_input, video_file, audio_settings=None):
        """Add a video processing job to the batch queue"""
        job = {
            "text_input": text_input,
            "video_file": video_file,
            "job_type": "video",
            "status": "pending",
            "audio_settings": audio_settings or {"mute_original": False, "original_volume": 0.3}
        }
        self.batch_jobs.append(job)
        return len(self.batch_jobs)  # Return job ID (1-based index)

    def add_group_batch_job(self, group_data, audio_settings=None):
        """Add a grouped video processing job to the batch queue"""
        job = {
            "group_data": group_data,
            "job_type": "group",
            "status": "pending",
            "audio_settings": audio_settings or {"mute_original": False, "original_volume": 0.3}
        }
        self.batch_jobs.append(job)
        return len(self.batch_jobs)  # Return job ID (1-based index)

    def process_video_batch(self, stop_event=None):
        """Process all video jobs in the batch queue"""
        results = []
        self.current_job_index = 0
        total_jobs = len(self.batch_jobs)

        for i, job in enumerate(self.batch_jobs):
            if stop_event and stop_event.is_set():
                break

            # Handle different job types
            job_type = job.get("job_type")
            if job_type == "video":
                result = self._process_individual_video_job(job, i, total_jobs, stop_event)
            elif job_type == "group":
                result = self._process_group_video_job(job, i, total_jobs, stop_event)
            else:
                continue  # Skip unknown job types
            
            results.append((job, result))

        return results

    def _process_individual_video_job(self, job, job_index, total_jobs, stop_event):
        """Process an individual video job"""
        # Calculate overall progress percentage
        overall_progress = int((job_index / total_jobs) * 100)
        self.update_progress(overall_progress, f"Starting video job {job_index+1}/{total_jobs}")

        # Set up the current job for video processing
        self.text_input = job["text_input"]
        video_file = job["video_file"]

        # Store audio settings for this job
        self.current_audio_settings = job.get("audio_settings", {"mute_original": False, "original_volume": 0.3})

        # For video processing, we'll extract frames from the video to use as images
        self.processing_option = "cpu"  # Default to CPU for batch processing

        # Process the job
        try:
            job["status"] = "processing"

            # Create a wrapper for the progress callback to show both job progress and overall progress
            original_callback = self.progress_callback

            def job_progress_callback(value, message=None):
                # Calculate combined progress: base progress for completed jobs + partial progress for current job
                # Each job contributes equally to the total progress
                job_weight = 100 / total_jobs
                # Base progress from completed jobs
                base_progress = int(job_index * job_weight)
                # Current job contribution (scaled by job weight)
                current_job_progress = int((value / 100) * job_weight)
                # Combined progress
                combined_progress = base_progress + current_job_progress
                # Ensure we never exceed 100%
                combined_progress = min(combined_progress, 100)

                # Create cleaner progress message
                if message:
                    job_message = f"Video {job_index+1}/{total_jobs}: {message}"
                else:
                    # Default to percentage when no specific message
                    job_message = f"{combined_progress}% - Processing video {job_index+1} of {total_jobs}"
                
                if original_callback:
                    original_callback(combined_progress, job_message)

            # Temporarily replace the callback
            self.progress_callback = job_progress_callback

            # Process the video file to generate a new video with the prompt
            final_video = self.process_video_with_prompt(video_file, stop_event)

            # Restore the original callback
            self.progress_callback = original_callback

            if final_video:
                job["status"] = "completed"
                # Update progress to show this job is complete
                if original_callback:
                    job_complete_progress = int((job_index + 1) * (100 / total_jobs))
                    original_callback(job_complete_progress, f"✅ Completed video {job_index+1} of {total_jobs}")
                return final_video
            else:
                job["status"] = "failed"
                # Update progress to show this job is complete but failed
                if original_callback:
                    job_complete_progress = int((job_index + 1) * (100 / total_jobs))
                    original_callback(job_complete_progress, f"❌ Failed video {job_index+1} of {total_jobs}")
                return None

        except Exception as e:
            print(f"Error processing video job {job_index+1}: {e}")
            job["status"] = "failed"
            # Restore the original callback
            if 'original_callback' in locals():
                self.progress_callback = original_callback
            return None

    def _process_group_video_job(self, job, job_index, total_jobs, stop_event):
        """Process a grouped video job (multiple videos combined into one)"""
        group_data = job["group_data"]
        
        # Calculate overall progress percentage
        overall_progress = int((job_index / total_jobs) * 100)
        self.update_progress(overall_progress, f"Starting group job {job_index+1}/{total_jobs}: {group_data['output_name']}")

        # Store audio settings for this job
        self.current_audio_settings = job.get("audio_settings", {"mute_original": False, "original_volume": 0.3})

        try:
            job["status"] = "processing"
            
            # Create a list to store processed individual videos
            processed_videos = []
            pairs = group_data['pairs']
            
            # Process each video in the group
            for i, pair in enumerate(pairs):
                if stop_event and stop_event.is_set():
                    break
                
                # Set up for individual video processing
                self.text_input = pair['prompt']
                video_file = pair['video_file']
                
                # Update progress for this video in the group
                # Calculate progress within the current job's allocated range (0-80% of job weight)
                job_weight = 100 / total_jobs
                video_progress_within_job = (i / len(pairs)) * 80  # 0-80% of this job for individual videos
                current_progress = overall_progress + int((video_progress_within_job / 100) * job_weight)
                current_progress = min(current_progress, 100)  # Ensure we never exceed 100%
                self.update_progress(current_progress, 
                                   f"Group {job_index+1}: Processing video {i+1}/{len(pairs)} - {os.path.basename(video_file)}")
                
                # Process individual video
                processed_video = self.process_video_with_prompt(video_file, stop_event)
                if processed_video:
                    processed_videos.append(processed_video)
                else:
                    print(f"Failed to process video: {os.path.basename(video_file)}")
            
            # If we have processed videos, combine them
            if processed_videos:
                        # Combine processed videos
                
                # Import the merge service
                from services.merge_service import VideoService
                
                # Create output path for combined video
                output_dir = os.path.dirname(processed_videos[0])
                parent_dir = os.path.dirname(output_dir)
                combined_output = os.path.join(parent_dir, group_data['output_name'])
                # Merge videos into combined output
                
                # Update progress for merging (80-95% of this job's weight)
                job_weight = 100 / total_jobs
                merge_start_progress = overall_progress + int((80 / 100) * job_weight)
                merge_start_progress = min(merge_start_progress, 95)  # Cap at 95% to leave room for completion
                self.update_progress(merge_start_progress, f"Group {job_index+1}: Combining {len(processed_videos)} videos...")
                
                # Merge videos
                try:
                    def merge_progress_callback(p, m):
                        # Scale merge progress to remaining 15% of job weight (80-95%)
                        merge_progress_range = 15  # 95% - 80% = 15%
                        scaled_merge_progress = int((p / 100) * merge_progress_range * (job_weight / 100))
                        final_progress = merge_start_progress + scaled_merge_progress
                        final_progress = min(final_progress, 99)  # Never exceed 99% during processing
                        self.update_progress(final_progress, f"Group {job_index+1}: {m}")
                    
                    merge_result = VideoService.merge_videos_optimized(
                        processed_videos, 
                        combined_output,
                        progress_callback=merge_progress_callback
                    )
                    # Check merge result
                    if not (merge_result and os.path.exists(combined_output)):
                        print(f"ERROR: Video merge failed")
                except Exception as e:
                    print(f"ERROR: Video merge failed: {e}")
                    merge_result = False
                
                if merge_result:
                    job["status"] = "completed"
                    
                                    # Clean up individual video folders after successful merge
                cleaned_folders = 0
                for video_path in processed_videos:
                    individual_folder = os.path.dirname(video_path)
                    try:
                        if os.path.exists(individual_folder):
                            import shutil
                            shutil.rmtree(individual_folder)
                            cleaned_folders += 1
                    except Exception as e:
                        pass  # Continue cleanup even if some folders fail
                    
                    self.update_progress(int((job_index + 1) * (100 / total_jobs)), 
                                       f"✅ Completed group {job_index+1}: {group_data['output_name']}")
                    return combined_output
                else:
                    job["status"] = "failed"
                    self.update_progress(int((job_index + 1) * (100 / total_jobs)), 
                                       f"❌ Failed to combine group {job_index+1}")
                    return None
            else:
                job["status"] = "failed"
                self.update_progress(int((job_index + 1) * (100 / total_jobs)), 
                                   f"❌ No videos processed in group {job_index+1}")
                return None
                
        except Exception as e:
            print(f"Error processing group job {job_index+1}: {e}")
            job["status"] = "failed"
            return None

    def process_video_with_prompt(self, video_file, stop_event=None):
        """
        Process a video file with a text prompt to add voice-over and subtitles
        while preserving the original video duration

        Args:
            video_file: Path to the input video file
            stop_event: Threading event to stop the process

        Returns:
            str: Path to the generated video file
        """
        try:
            # Check if we should stop
            if stop_event and stop_event.is_set():
                print("Process stopped by user.")
                self.update_progress(0, "Process stopped by user")
                return None

            # Create output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_name = os.path.splitext(os.path.basename(video_file))[0]

            # Use custom output folder if provided
            if self.output_folder and os.path.isdir(self.output_folder):
                output_dir = os.path.join(self.output_folder, f"video_{video_name}_{timestamp}")
            else:
                # Use the output directory set by main.py, or fallback to default
                base_output_dir = os.environ.get('VIDEO_GENERATOR_OUTPUT_DIR', 'output')
                output_dir = os.path.join(base_output_dir, f"video_{video_name}_{timestamp}")

            os.makedirs(output_dir, exist_ok=True)
            print(f"Created output directory: {output_dir}")

            # Store output_dir as instance variable for cleanup if needed
            self.current_output_dir = output_dir

            # Step 1: Generate audio from text
            print("\n--- Step 1: Generating Audio ---")
            self.update_progress(20, "Generating audio from text...")
            audio_file = os.path.join(output_dir, "voice.mp3")
            if not generate_audio(self.text_input, audio_file):
                print("ERROR: Failed to generate audio.")
                self.update_progress(0, "Failed to generate audio")
                return None

            # Check if we should stop
            if stop_event and stop_event.is_set():
                print("Process stopped by user.")
                self.update_progress(0, "Process stopped by user")
                return None

            self.update_progress(40, "Audio generated successfully")

            # Step 2: Add voice-over to original video while preserving video duration
            print("\n--- Step 2: Adding voice-over to video ---")
            self.update_progress(50, "Adding voice-over to video...")
            video_with_audio = os.path.join(output_dir, "video_with_audio.mp4")

            if not self._add_voiceover_to_video(video_file, audio_file, video_with_audio, stop_event):
                print("ERROR: Failed to add voice-over to video.")
                self.update_progress(0, "Failed to add voice-over to video")
                return None

            # Check if we should stop
            if stop_event and stop_event.is_set():
                print("Process stopped by user.")
                self.update_progress(0, "Process stopped by user")
                return None

            self.update_progress(70, "Voice-over added successfully")

            # Step 3: Generate subtitles
            print("\n--- Step 3: Generating Subtitles ---")
            self.update_progress(75, "Generating subtitles...")
            subtitle_file = os.path.join(output_dir, "subtitles.ass")
            
            # Get subtitle style from enhancement options
            subtitle_style = self.enhancement_options.get("subtitle_style", "modern_glow")
            print(f"Using subtitle style: {subtitle_style}")
            
            if not generate_subtitles(self.text_input, video_with_audio, audio_file, subtitle_file, subtitle_style):
                print("ERROR: Failed to generate subtitles.")
                self.update_progress(0, "Failed to generate subtitles")
                return None

            # Check if we should stop
            if stop_event and stop_event.is_set():
                print("Process stopped by user.")
                self.update_progress(0, "Process stopped by user")
                return None

            self.update_progress(90, "Subtitles generated successfully")

            # Step 4: Finalize video with subtitles
            final_video = self.finalize_video(subtitle_file, video_with_audio, output_dir, stop_event)

            # EXPLICIT MOVIEPY CLEANUP - Release file handles immediately after processing
            try:
                import gc
                # Force garbage collection to release MoviePy references
                gc.collect()
                print("Released MoviePy file handles")
            except Exception as e:
                print(f"Note: MoviePy cleanup attempt: {e}")

            if final_video:
                print(f"Video processing completed successfully: {final_video}")
                
                # AUTO-CLEANUP for single videos - same as batch processing
                cleanup_enabled = getattr(config, 'AUTO_CLEANUP_AFTER_COMPLETION', True)
                if cleanup_enabled:
                    print("Starting automatic cleanup for single video...")
                    try:
                        # Use the consolidated cleanup function
                        cleaned_count = self.cleanup_after_video_complete(
                            output_dir, 
                            keep_debug_files=False  # Clean everything except final_output.mp4
                        )
                        if cleaned_count > 0:
                            print(f"Auto-cleanup completed: Removed {cleaned_count} intermediate files")
                            print("Only final_output.mp4 remains")
                        else:
                            print("No cleanup needed - files already clean")
                    except Exception as e:
                        print(f"Warning: Cleanup failed for single video: {e}")
                else:
                    print("Auto-cleanup disabled in config - keeping all files")
                
                # Return just the final video path (this method is used by video processing, not UI)
                return final_video
            else:
                print("Failed to finalize video")
                return None

        except Exception as e:
            print(f"Error processing video with prompt: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _add_voiceover_to_video(self, video_file, audio_file, output_file, stop_event=None):
        """
        Add voice-over audio to a video while preserving the original video duration

        Args:
            video_file: Path to the input video file
            audio_file: Path to the generated audio file
            output_file: Path to the output video file
            stop_event: Threading event to stop the process

        Returns:
            bool: True if successful, False otherwise
        """
        # Check if we should stop
        if stop_event and stop_event.is_set():
            return False

        # Get audio settings from current job
        audio_settings = getattr(self, 'current_audio_settings', {"mute_original": False, "original_volume": 0.3})

        # Use the video service function with audio settings
        from services.video_service import add_voiceover_to_video
        return add_voiceover_to_video(
            video_file,
            audio_file,
            output_file,
            mix_with_original=not audio_settings["mute_original"],
            original_volume=audio_settings["original_volume"]
        )

    def _extract_video_frames(self, video_file, output_dir, stop_event=None, max_frames=20):
        """
        Extract frames from a video file

        Args:
            video_file: Path to the input video file
            output_dir: Directory to save extracted frames
            stop_event: Threading event to stop the process
            max_frames: Maximum number of frames to extract

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import cv2

            # Open the video file
            cap = cv2.VideoCapture(video_file)
            if not cap.isOpened():
                print(f"ERROR: Could not open video file: {video_file}")
                return False

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            print(f"Video has {total_frames} frames at {fps} FPS")

            # Calculate frame interval to extract evenly distributed frames
            if total_frames <= max_frames:
                frame_interval = 1
                frames_to_extract = total_frames
            else:
                frame_interval = total_frames // max_frames
                frames_to_extract = max_frames

            print(f"Extracting {frames_to_extract} frames with interval {frame_interval}")

            frame_count = 0
            extracted_count = 0

            while True:
                # Check if we should stop
                if stop_event and stop_event.is_set():
                    cap.release()
                    return False

                ret, frame = cap.read()
                if not ret:
                    break

                # Extract frame at specified intervals
                if frame_count % frame_interval == 0 and extracted_count < max_frames:
                    frame_filename = os.path.join(output_dir, f"frame_{extracted_count:04d}.jpg")
                    cv2.imwrite(frame_filename, frame)
                    extracted_count += 1

                    # Update progress
                    progress = int((extracted_count / frames_to_extract) * 20) + 10  # 10-30% range
                    self.update_progress(progress, f"Extracted {extracted_count}/{frames_to_extract} frames")

                frame_count += 1

            cap.release()

            print(f"Successfully extracted {extracted_count} frames")
            return extracted_count > 0

        except ImportError:
            print("ERROR: OpenCV (cv2) is required for video frame extraction")
            print("Please install it with: pip install opencv-python")
            return False
        except Exception as e:
            print(f"ERROR: Failed to extract frames from video: {e}")
            return False

    def _cleanup_extracted_frames(self, images_dir):
        """
        Clean up extracted frames from video processing to keep output folder clean

        Args:
            images_dir: Directory containing extracted frames
        """
        try:
            if os.path.exists(images_dir):
                import shutil
                shutil.rmtree(images_dir)
                print(f"Cleaned up extracted frames directory: {images_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up extracted frames directory: {e}")

    def _cleanup_on_stop(self):
        """Clean up files when process is stopped by user"""
        if hasattr(self, 'current_output_dir') and self.current_output_dir:
            try:
                import shutil
                if os.path.exists(self.current_output_dir):
                    print(f"Cleaning up output directory: {self.current_output_dir}")
                    shutil.rmtree(self.current_output_dir)
                    print(f"Removed output directory after stop: {self.current_output_dir}")
            except Exception as e:
                print(f"Warning: Could not clean up output directory: {e}")

def show_version():
    return f"Video Generator v{__version__}"
