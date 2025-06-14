"""
Refactored Video Generator Model - Simplified and modular
Reduced from 1,243 lines to ~300 lines by extracting components
"""
import os
import config
from datetime import datetime
from utils.error_helpers import handle_operation_error

# Import the extracted components
from .video_processor import VideoProcessor
from .batch_processor import BatchProcessor
from .cleanup_manager import CleanupManager

__version__ = "1.0.4"


class VideoGeneratorModel:
    """
    Simplified Video Generator Model with extracted components
    
    This class now focuses on:
    - Core video generation logic
    - Coordination between components
    - Configuration management
    
    Complex operations are delegated to specialized components:
    - VideoProcessor: Individual video operations
    - BatchProcessor: Batch processing operations  
    - CleanupManager: File cleanup operations
    """
    
    def __init__(self, progress_callback=None):
        # Core attributes
        self.text_input = ""
        self.image_source = "selected"
        self.selected_images = []
        self.website_url = ""
        self.local_folder = ""
        self.processing_option = "cpu"
        self.enhancement_options = {}
        
        # Progress tracking
        self.progress_callback = progress_callback
        
        # Initialize components
        self.video_processor = VideoProcessor(progress_callback)
        self.batch_processor = BatchProcessor(progress_callback)
        self.cleanup_manager = CleanupManager()

        # Link cleanup manager to batch processor for unified cleanup
        self.batch_processor.cleanup_manager = self.cleanup_manager
        
        # State tracking
        self.current_output_dir = None

        # Compatibility properties for UI
        self.output_folder = None
        self.current_job_index = 0
    
    def update_progress(self, value, message=None):
        """Update progress value and message"""
        if self.progress_callback:
            self.progress_callback(value, message)
    
    def generate_video(self, stop_event=None):
        """
        Main video generation method - simplified to focus on core logic
        
        Returns:
            tuple: (subtitle_path, video_path, output_dir)
        """
        try:
            # Validate inputs
            if not self._validate_inputs():
                return None
            
            # Check if we should stop
            if stop_event and stop_event.is_set():
                self.update_progress(0, "Process stopped by user")
                return None

            # Create output directory
            output_dir = self._create_output_directory()
            self.current_output_dir = output_dir

            # Step 1: Get images
            images_dir = self._get_images(output_dir, stop_event)
            if not images_dir:
                return None

            # Step 2: Generate audio
            audio_file = self._generate_audio(output_dir, stop_event)
            if not audio_file:
                return None

            # Step 3: Create video slideshow
            video_file = self._create_video_slideshow(images_dir, audio_file, output_dir, stop_event)
            if not video_file:
                return None

            # Step 4: Generate subtitles
            subtitle_file = self._generate_subtitles(video_file, audio_file, output_dir, stop_event)
            if not subtitle_file:
                return None

            # Organize output folder during generation
            self.cleanup_manager.organize_output_folder_during_generation(output_dir)

            return subtitle_file, video_file, output_dir

        except Exception as e:
            handle_operation_error(None, "Video generation", e, show_dialog=False)
            return None
    
    def finalize_video(self, subtitle_path, video_path, output_dir, stop_event=None):
        """
        Finalize video by merging with subtitles
        
        Args:
            subtitle_path: Path to subtitle file
            video_path: Path to video file
            output_dir: Output directory
            stop_event: Threading event to stop the process
            
        Returns:
            str: Path to final video file
        """
        try:
            if stop_event and stop_event.is_set():
                return None

            self.update_progress(95, "Finalizing video...")

            from Final_Video import merge_video_subtitle
            final_output = os.path.join(output_dir, "final_output.mp4")

            result = merge_video_subtitle(video_path, subtitle_path, final_output)

            if result:
                self.update_progress(100, f"Video generated successfully: {os.path.basename(result)}")
                
                # Auto-cleanup if enabled
                cleanup_enabled = getattr(config, 'AUTO_CLEANUP_AFTER_COMPLETION', True)
                if cleanup_enabled:
                    self.cleanup_manager.cleanup_after_video_complete(output_dir, keep_debug_files=False)
                
                return result
            else:
                self.update_progress(0, "Failed to finalize video")
                return None

        except Exception as e:
            handle_operation_error(None, "Video finalization", e, show_dialog=False)
            return None
    
    def process_video_with_prompt(self, video_file, text_input, stop_event=None, output_folder=None):
        """
        Process a video file with a text prompt - delegates to VideoProcessor
        
        Args:
            video_file: Path to the input video file
            text_input: Text prompt for voice-over
            stop_event: Threading event to stop the process
            output_folder: Custom output folder
            
        Returns:
            str: Path to the generated video file
        """
        # Set up the video processor with current settings
        self.video_processor.enhancement_options = self.enhancement_options.copy()
        
        # Delegate to video processor
        return self.video_processor.process_video_with_prompt(
            video_file, text_input, stop_event, output_folder
        )
    
    def add_batch_job(self, text_input, image_source, selected_images=None, website_url=None, local_folder=None):
        """Add a job to the batch processing queue - delegates to BatchProcessor"""
        return self.batch_processor.add_batch_job(
            text_input, image_source, selected_images, website_url, local_folder
        )
    
    def add_video_batch_job(self, text_input, video_file, audio_settings=None):
        """Add a video processing job to the batch queue - delegates to BatchProcessor"""
        return self.batch_processor.add_video_batch_job(text_input, video_file, audio_settings)
    
    def add_group_batch_job(self, group_data, audio_settings=None):
        """Add a grouped video processing job to the batch queue - delegates to BatchProcessor"""
        return self.batch_processor.add_group_batch_job(group_data, audio_settings)
    
    def process_batch(self, stop_event=None):
        """Process all jobs in the batch queue - delegates to BatchProcessor"""
        return self.batch_processor.process_batch(self, stop_event)
    
    def process_video_batch(self, stop_event=None):
        """Process all video jobs in the batch queue - delegates to BatchProcessor"""
        return self.batch_processor.process_video_batch(self.video_processor, stop_event, self.output_folder)

    # Compatibility properties and methods for UI
    @property
    def batch_jobs(self):
        """Compatibility property to access batch jobs"""
        return self.batch_processor.batch_jobs

    def set_progress_callback(self, callback):
        """Set progress callback for all components"""
        self.progress_callback = callback
        self.video_processor.progress_callback = callback
        self.batch_processor.progress_callback = callback

    def cleanup_after_video_complete(self, output_dir, keep_debug_files=False):
        """Cleanup after video completion - delegates to CleanupManager"""
        return self.cleanup_manager.cleanup_after_video_complete(output_dir, keep_debug_files)

    def _cleanup_extracted_frames(self, images_dir):
        """Clean up extracted frames - delegates to CleanupManager"""
        return self.cleanup_manager.cleanup_extracted_frames(images_dir)

    def _cleanup_on_stop(self):
        """Clean up files when process is stopped - delegates to CleanupManager"""
        if hasattr(self, 'current_output_dir') and self.current_output_dir:
            return self.cleanup_manager.cleanup_on_stop(self.current_output_dir)
    
    def _validate_inputs(self):
        """Validate input parameters"""
        if not self.text_input.strip():
            self.update_progress(0, "Error: No text input provided")
            return False

        if self.image_source == "selected" and not self.selected_images:
            self.update_progress(0, "Error: No images selected")
            return False

        if self.image_source == "website" and not self.website_url.strip():
            self.update_progress(0, "Error: No website URL provided")
            return False

        if self.image_source == "folder" and not self.local_folder.strip():
            self.update_progress(0, "Error: No local folder provided")
            return False

        return True

    def _create_output_directory(self):
        """Create output directory for video generation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_output_dir = os.environ.get('VIDEO_GENERATOR_OUTPUT_DIR', 'output')
        output_dir = os.path.join(base_output_dir, f"video_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
        return output_dir

    def _get_images(self, output_dir, stop_event):
        """Get images based on the selected source"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(10, "Getting images...")

        if self.image_source == "selected":
            return self._handle_selected_images(output_dir)
        elif self.image_source == "website":
            return self._handle_website_images(output_dir, stop_event)
        elif self.image_source == "folder":
            return self._handle_folder_images(output_dir)
        else:
            self.update_progress(0, "Error: Invalid image source")
            return None

    def _handle_selected_images(self, output_dir):
        """Handle selected images"""
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        # Copy selected images to output directory
        import shutil
        for i, image_path in enumerate(self.selected_images):
            if os.path.exists(image_path):
                ext = os.path.splitext(image_path)[1]
                dest_path = os.path.join(images_dir, f"image_{i:03d}{ext}")
                shutil.copy2(image_path, dest_path)

        self.update_progress(20, f"Copied {len(self.selected_images)} selected images")
        return images_dir

    def _handle_website_images(self, output_dir, stop_event):
        """Handle website image download"""
        from services.image_service import download_images_from_website

        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        success = download_images_from_website(
            self.website_url,
            images_dir,
            progress_callback=self.update_progress,
            stop_event=stop_event
        )

        if success:
            return images_dir
        else:
            self.update_progress(0, "Failed to download images from website")
            return None

    def _handle_folder_images(self, output_dir):
        """Handle local folder images"""
        if not os.path.exists(self.local_folder):
            self.update_progress(0, "Error: Local folder does not exist")
            return None

        # Use the local folder directly
        self.update_progress(20, f"Using images from local folder: {self.local_folder}")
        return self.local_folder

    def _generate_audio(self, output_dir, stop_event):
        """Generate audio from text input"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(30, "Generating audio...")

        from services.audio_service import generate_audio
        audio_file = os.path.join(output_dir, "voice.mp3")

        if generate_audio(self.text_input, audio_file):
            self.update_progress(50, "Audio generated successfully")
            return audio_file
        else:
            self.update_progress(0, "Failed to generate audio")
            return None

    def _create_video_slideshow(self, images_dir, audio_file, output_dir, stop_event):
        """Create video slideshow from images"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(60, "Creating video slideshow...")

        from services.video_slideshow import create_slideshow_video
        video_file = os.path.join(output_dir, "slideshow.mp4")

        success = create_slideshow_video(
            images_dir,
            audio_file,
            video_file,
            processing_option=self.processing_option,
            enhancement_options=self.enhancement_options,
            progress_callback=self.update_progress,
            stop_event=stop_event
        )

        if success:
            self.update_progress(80, "Video slideshow created successfully")
            return video_file
        else:
            self.update_progress(0, "Failed to create video slideshow")
            return None

    def _generate_subtitles(self, video_file, audio_file, output_dir, stop_event):
        """Generate subtitles for the video"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(85, "Generating subtitles...")

        from services.subtitle_service import generate_subtitles
        subtitle_file = os.path.join(output_dir, "subtitles.ass")

        # Get subtitle style from enhancement options
        subtitle_style = self.enhancement_options.get("subtitle_style", "modern_glow")

        if generate_subtitles(self.text_input, video_file, audio_file, subtitle_file, subtitle_style):
            self.update_progress(90, "Subtitles generated successfully")
            return subtitle_file
        else:
            self.update_progress(0, "Failed to generate subtitles")
            return None


def show_version():
    return f"Video Generator v{__version__}"
