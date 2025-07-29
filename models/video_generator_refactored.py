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
        self.local_folder = ""
        self.processing_option = "cpu"
        self.enhancement_options = {}

        # Speech recognition validation settings (enabled by default)
        self.enable_speech_validation = True
        self.speech_validation_threshold = 0.7  # Minimum similarity score to pass validation
        self.speech_validation_settings = {}

        # TTS settings (initialized with defaults)
        self.tts_settings = {
            'language': 'en',
            'voice_actor': 'Guy',
            'speed': 1.0,
            'emotion': 'neutral'
        }

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
            from utils.memory_manager import memory_optimized_operation, get_memory_manager

            with memory_optimized_operation("Complete Video Generation"):
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

            # Step 4: Generate improved phrase-based subtitles
            # Word-by-word option removed per user request
            subtitle_type = "phrase"
            subtitle_file = self._generate_subtitles(video_file, audio_file, output_dir, stop_event, subtitle_type)
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
        Finalize video by merging with subtitles and move to user's output directory
        Delegates to VideoProcessor for consistent finalization logic

        Args:
            subtitle_path: Path to subtitle file
            video_path: Path to video file
            output_dir: Temporary output directory
            stop_event: Threading event to stop the process

        Returns:
            str: Path to final video file in user's output directory
        """
        if stop_event and stop_event.is_set():
            return None

        # Set up the video processor with current settings
        self.video_processor.enhancement_options = self.enhancement_options.copy()
        custom_filename = getattr(self, 'custom_filename', '')
        self.video_processor.custom_filename = custom_filename
        source_files = getattr(self, 'source_files', None)
        self.video_processor.source_files = source_files

        # Delegate to video processor's finalization method
        return self.video_processor._finalize_video(
            subtitle_path, video_path, output_dir, stop_event, skip_auto_cleanup=False
        )
    
    def process_video_with_prompt(self, video_file, text_input, stop_event=None, output_folder=None, skip_auto_cleanup=False):
        """
        Process a video file with a text prompt - delegates to VideoProcessor

        Args:
            video_file: Path to the input video file
            text_input: Text prompt for voice-over
            stop_event: Threading event to stop the process
            output_folder: Custom output folder
            skip_auto_cleanup: Skip automatic cleanup (for group processing)

        Returns:
            str: Path to the generated video file
        """
        # Set up the video processor with current settings
        self.video_processor.enhancement_options = self.enhancement_options.copy()
        self.video_processor.tts_settings = self.tts_settings.copy()

        # Delegate to video processor
        return self.video_processor.process_video_with_prompt(
            video_file, text_input, stop_event, output_folder, skip_auto_cleanup
        )
    
    def add_batch_job(self, text_input, image_source, selected_images=None, website_url=None, local_folder=None):
        """Add a job to the batch processing queue - delegates to BatchProcessor"""
        return self.batch_processor.add_batch_job(
            text_input, image_source, selected_images, website_url, local_folder
        )
    
    def add_video_batch_job(self, text_input, video_file, audio_settings=None, custom_filename=None):
        """Add a video processing job to the batch queue - delegates to BatchProcessor"""
        return self.batch_processor.add_video_batch_job(text_input, video_file, audio_settings, custom_filename)
    
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
        # Text input is required for image generation
        if not self.text_input.strip():
            self.update_progress(0, "Error: Please provide a text prompt for image generation")
            return False

        if self.image_source == "selected" and not self.selected_images:
            self.update_progress(0, "Error: No images selected")
            return False

        if self.image_source == "folder" and not self.local_folder.strip():
            self.update_progress(0, "Error: No local folder provided")
            return False

        return True

    def _create_output_directory(self):
        """Create output directory for video generation with improved settings handling"""
        import time
        # Use more precise timestamp with milliseconds to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        milliseconds = int(time.time() * 1000) % 1000
        unique_timestamp = f"{timestamp}_{milliseconds:03d}"


        
        if self.output_folder and os.path.isdir(self.output_folder):
            output_dir = os.path.join(self.output_folder, f"video_{unique_timestamp}")
            print(f"Using specified output folder: {self.output_folder}")
        else:
            # Load current user settings to respect output folder preference
            try:
                from utils.settings_manager import SettingsManager
                settings_manager = SettingsManager()
                user_settings = settings_manager.load_settings()
                
                # Get output directory from settings
                if user_settings and 'output_folder' in user_settings and os.path.isdir(user_settings['output_folder']):
                    base_output_dir = user_settings['output_folder']
                else:
                    # Fallback to default
                    base_output_dir = os.environ.get('VIDEO_GENERATOR_OUTPUT_DIR', 'output')
                    if not os.path.isdir(base_output_dir):
                        import tempfile
                        base_output_dir = os.path.join(tempfile.gettempdir(), "Video Generator", "output")
                        os.makedirs(base_output_dir, exist_ok=True)
            except Exception as e:
                print(f"Could not load user settings: {e}")
                base_output_dir = os.environ.get('VIDEO_GENERATOR_OUTPUT_DIR', 'output')
                if not os.path.isdir(base_output_dir):
                    import tempfile
                    base_output_dir = os.path.join(tempfile.gettempdir(), "Video Generator", "output")
                    os.makedirs(base_output_dir, exist_ok=True)
                
            output_dir = os.path.join(base_output_dir, f"video_{unique_timestamp}")

        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created output directory: {output_dir}")
            return output_dir
        except OSError as e:
            raise Exception(f"Failed to create output directory {output_dir}: {e}")

    def _get_images(self, output_dir, stop_event):
        """Get images based on the selected source"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(10, "Getting images...")

        if self.image_source == "selected":
            return self._handle_selected_images(output_dir)
        elif self.image_source == "folder":
            return self._handle_folder_images(output_dir)
        else:
            self.update_progress(0, "Error: Invalid image source")
            return None

    def _handle_selected_images(self, output_dir):
        """Handle selected images (optimized - use original paths instead of copying)"""
        # Validate that all selected images exist
        valid_images = []
        for image_path in self.selected_images:
            if os.path.exists(image_path):
                valid_images.append(image_path)
            else:
                print(f"Warning: Image not found: {image_path}")

        if not valid_images:
            raise Exception("No valid images found in selection")

        self.update_progress(20, f"Using {len(valid_images)} selected images (no copying needed)")

        # Return the directory containing the images for slideshow creation
        # The slideshow service will use the original image paths directly
        return valid_images

    def _handle_folder_images(self, output_dir):
        """Handle local folder images"""
        # output_dir parameter kept for interface consistency
        if not os.path.exists(self.local_folder):
            self.update_progress(0, "Error: Local folder does not exist")
            return None

        # Use the local folder directly
        self.update_progress(20, f"Using images from local folder: {self.local_folder}")
        return self.local_folder

    def _generate_audio(self, output_dir, stop_event):
        """Generate audio from text input - delegates to VideoProcessor for consistency"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(30, "Analyzing content and generating audio...")

        # Delegate to video processor for consistent audio generation
        # Set up the video processor with current settings
        self.video_processor.enhancement_options = self.enhancement_options.copy()
        self.video_processor.tts_settings = self.tts_settings.copy()
        self.video_processor.text_input = self.text_input

        # Use video processor's audio generation method
        audio_file = self.video_processor._generate_audio(self.text_input, output_dir, stop_event)

        # Copy timing result back to main model for subtitle generation
        if hasattr(self.video_processor, 'audio_timing_result'):
            self.audio_timing_result = self.video_processor.audio_timing_result

        return audio_file

    def _create_video_slideshow(self, images_dir, audio_file, output_dir, stop_event):
        """Create video slideshow from images"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(60, "Creating video slideshow...")

        from services.video_slideshow import create_slideshow
        video_file = os.path.join(output_dir, "slideshow.mp4")

        # Prepare parameters for create_slideshow function
        title = "Generated Video"  # Default title
        # Use validated text if available, otherwise use original text
        content = getattr(self, 'validated_text', self.text_input)
        use_gpu = (self.processing_option == "gpu")
        enhancement_options = self.enhancement_options or {}

        # Get aspect ratio from user settings first, then fall back to config
        aspect_ratio_str = getattr(config, 'DEFAULT_ASPECT_RATIO', '9:16')
        try:
            from utils.settings_manager import SettingsManager
            settings_manager = SettingsManager()
            # Use image tab specific settings for aspect ratio
            image_tab_settings = settings_manager.get_tab_settings('image_tab')
            user_aspect_ratio = image_tab_settings.get('aspect_ratio', '16:9 (Landscape)')

            # Convert user aspect ratio preset to simple ratio string
            if '16:9' in user_aspect_ratio:
                aspect_ratio_str = '16:9'
            elif '9:16' in user_aspect_ratio:
                aspect_ratio_str = '9:16'
            elif '1:1' in user_aspect_ratio:
                aspect_ratio_str = '1:1'
            elif '4:3' in user_aspect_ratio:
                aspect_ratio_str = '4:3'
            elif '21:9' in user_aspect_ratio:
                aspect_ratio_str = '21:9'

        except Exception:
            pass

        # Convert aspect ratio string to dimensions tuple
        if isinstance(aspect_ratio_str, str) and ':' in aspect_ratio_str:
            # Convert "9:16" to actual dimensions
            ratio_parts = aspect_ratio_str.split(':')
            if len(ratio_parts) == 2:
                width_ratio, height_ratio = int(ratio_parts[0]), int(ratio_parts[1])
                # Use standard resolutions based on aspect ratio
                if width_ratio == 9 and height_ratio == 16:
                    aspect_ratio = (1080, 1920)  # 9:16 portrait
                elif width_ratio == 16 and height_ratio == 9:
                    aspect_ratio = (1920, 1080)  # 16:9 landscape
                elif width_ratio == 1 and height_ratio == 1:
                    aspect_ratio = (1080, 1080)  # 1:1 square
                elif width_ratio == 4 and height_ratio == 3:
                    aspect_ratio = (1440, 1080)  # 4:3 classic
                elif width_ratio == 21 and height_ratio == 9:
                    aspect_ratio = (2560, 1080)  # 21:9 ultrawide
                else:
                    # Calculate based on 1080p base
                    base_size = 1080
                    if width_ratio > height_ratio:
                        aspect_ratio = (base_size, int(base_size * height_ratio / width_ratio))
                    else:
                        aspect_ratio = (int(base_size * width_ratio / height_ratio), base_size)
            else:
                aspect_ratio = (1080, 1920)  # Default to 9:16
        else:
            aspect_ratio = (1080, 1920)  # Default to 9:16
        # Get fit method from settings
        fit_method = "cover"  # Default
        try:
            from utils.settings_manager import SettingsManager
            settings_manager = SettingsManager()
            # Use image tab specific settings for image processing
            image_tab_settings = settings_manager.get_tab_settings('image_tab')
            fit_method = image_tab_settings.get('image_fit_method', 'cover')
        except Exception:
            pass  # Use default

        # Use default enhancement options

        # Pass audio timing result for content-aware image timing
        audio_timing_result = getattr(self, 'audio_timing_result', None)

        success = create_slideshow(
            images_dir,
            title,
            content,
            audio_file,
            video_file,
            use_gpu=use_gpu,
            enhancement_options=enhancement_options,
            stop_event=stop_event,
            aspect_ratio=aspect_ratio,
            fit_method=fit_method,
            audio_timing_result=audio_timing_result
        )

        if success:
            self.update_progress(80, "Video slideshow created successfully")
            return video_file
        else:
            self.update_progress(0, "Failed to create video slideshow")
            return None

    def _generate_subtitles(self, video_file, audio_file, output_dir, stop_event, subtitle_type="phrase"):
        """Generate subtitles - delegates to VideoProcessor for consistency"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(85, "Generating improved phrase-based subtitles...")

        # Delegate to video processor for consistent subtitle generation
        # Set up the video processor with current settings and timing data
        self.video_processor.enhancement_options = self.enhancement_options.copy()
        if hasattr(self, 'audio_timing_result'):
            self.video_processor.audio_timing_result = self.audio_timing_result
        self.video_processor.text_input = self.text_input

        # Use video processor's subtitle generation method
        return self.video_processor._generate_subtitles(
            self.text_input, video_file, audio_file, output_dir, stop_event, subtitle_type
        )
    
    def set_speech_validation_settings(self, enable=False, threshold=0.7, voice_settings=None):
        """
        Configure speech recognition validation settings

        Args:
            enable: Whether to enable speech validation
            threshold: Minimum similarity score to pass validation (0.0 to 1.0)
            voice_settings: Optional voice settings for validation
        """
        self.enable_speech_validation = enable
        self.speech_validation_threshold = max(0.0, min(1.0, threshold))
        if voice_settings:
            self.speech_validation_settings = voice_settings.copy()

    def get_last_speech_validation_result(self):
        """Get the results of the last speech validation - delegates to VideoProcessor"""
        # Check both main model and video processor for validation results
        main_result = getattr(self, 'last_speech_validation_result', None)
        processor_result = getattr(self.video_processor, 'last_speech_validation_result', None)
        # Return the most recent result (processor result takes precedence)
        return processor_result if processor_result is not None else main_result

def show_version():
    return f"Video Generator v{__version__}"

