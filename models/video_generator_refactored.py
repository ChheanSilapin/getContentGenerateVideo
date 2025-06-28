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

        # Speech recognition validation settings (enabled by default)
        self.enable_speech_validation = True
        self.speech_validation_threshold = 0.7  # Minimum similarity score to pass validation
        self.speech_validation_settings = {}

        # TTS settings (initialized with defaults)
        self.tts_settings = {
            'language': 'en',
            'voice_actor': 'Default',
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
        Finalize video by merging with subtitles and move to user's output directory

        Args:
            subtitle_path: Path to subtitle file
            video_path: Path to video file
            output_dir: Temporary output directory
            stop_event: Threading event to stop the process

        Returns:
            str: Path to final video file in user's output directory
        """
        try:
            if stop_event and stop_event.is_set():
                return None

            self.update_progress(95, "Finalizing video...")

            from services.video_finalization import merge_video_subtitle
            from utils.filename_validator import get_final_output_filename
            from utils.output_manager import get_output_manager

            # Use custom filename if provided, otherwise use default
            custom_filename = getattr(self, 'custom_filename', '')
            temp_filename = get_final_output_filename(custom_filename, "final_output")
            temp_output = os.path.join(output_dir, temp_filename)

            # Merge video with subtitles in temporary location
            result = merge_video_subtitle(video_path, subtitle_path, temp_output)

            if result:
                # Get output manager for user's directory
                try:
                    from utils.settings_manager import SettingsManager
                    settings_manager = SettingsManager()
                    user_settings = settings_manager.load_settings()
                except Exception:
                    user_settings = None

                output_manager = get_output_manager(user_settings)

                # Get source files for intelligent default naming
                source_files = getattr(self, 'source_files', None)

                # Move final video to user's output directory with conflict resolution
                final_video_path = output_manager.move_final_video(
                    temp_video_path=result,
                    custom_filename=custom_filename,
                    source_files=source_files,
                    default_name="video"
                )

                if final_video_path:
                    self.update_progress(100, f"Video saved: {os.path.basename(final_video_path)}")

                    # Clean up temporary directory
                    output_manager.cleanup_temp_directory(output_dir)

                    return final_video_path
                else:
                    self.update_progress(0, "Failed to move video to output directory")
                    return result  # Return temp path as fallback
            else:
                self.update_progress(0, "Failed to finalize video")
                return None

        except Exception as e:
            handle_operation_error(None, "Video finalization", e, show_dialog=False)
            return None
    
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

        if self.image_source == "website" and not self.website_url.strip():
            self.update_progress(0, "Error: No website URL provided")
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
            from utils.helpers import get_output_directory
            # Load current user settings to respect output folder preference
            try:
                from utils.settings_manager import SettingsManager
                settings_manager = SettingsManager()
                user_settings = settings_manager.load_settings()
            except Exception as e:
                print(f"Could not load user settings: {e}")
                user_settings = None

            base_output_dir = get_output_directory(user_settings)
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
        try:
            os.makedirs(images_dir, exist_ok=True)
        except OSError as e:
            raise Exception(f"Failed to create images directory: {e}")

        # Copy selected images to output directory
        import shutil
        for i, image_path in enumerate(self.selected_images):
            if os.path.exists(image_path):
                try:
                    ext = os.path.splitext(image_path)[1]
                    dest_path = os.path.join(images_dir, f"image_{i:03d}{ext}")
                    shutil.copy2(image_path, dest_path)
                except (OSError, shutil.Error) as e:
                    print(f"Warning: Failed to copy image {image_path}: {e}")
                    continue

        self.update_progress(20, f"Copied {len(self.selected_images)} selected images")
        return images_dir

    def _handle_website_images(self, output_dir, stop_event):
        """Handle website image download"""
        from services.image_service import download_images_from_website

        images_dir = os.path.join(output_dir, "images")
        try:
            os.makedirs(images_dir, exist_ok=True)
        except OSError as e:
            raise Exception(f"Failed to create images directory: {e}")

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
        # output_dir parameter kept for interface consistency
        if not os.path.exists(self.local_folder):
            self.update_progress(0, "Error: Local folder does not exist")
            return None

        # Use the local folder directly
        self.update_progress(20, f"Using images from local folder: {self.local_folder}")
        return self.local_folder

    def _generate_audio(self, output_dir, stop_event):
        """Generate audio from text input using gTTS with settings"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(30, "Analyzing content and generating audio...")

        # Perform content analysis for emotion-aware generation
        from services.content_analysis import ContentAnalyzer
        analyzer = ContentAnalyzer()
        content_analysis = analyzer.analyze_content(self.text_input, title="", context="")

        print(f"Content Analysis: Type={content_analysis.content_type.value}, "
              f"Emotion={content_analysis.emotional_tone.value}, "
              f"Confidence={content_analysis.confidence:.2f}")

        from services.audio_service import generate_audio_with_timing_analysis
        audio_file = os.path.join(output_dir, "voice.mp3")

        # Get TTS settings from enhancement options or use defaults
        tts_settings = getattr(self, 'tts_settings', {})
        voice_actor = tts_settings.get('voice_actor', self.enhancement_options.get('voice_emotion', 'Default'))
        speed = tts_settings.get('speed', 1.0)
        emotion = tts_settings.get('emotion', self.enhancement_options.get('voice_emotion', 'neutral'))
        language = tts_settings.get('language', 'en')

        print(f"Using TTS settings: voice={voice_actor}, speed={speed}, emotion={emotion}, language={language}")

        # Store content analysis for later use
        self.content_analysis = content_analysis

        # Generate audio with timing analysis for subtitle synchronization
        audio_timing_result = generate_audio_with_timing_analysis(
            self.text_input, audio_file, voice_actor=voice_actor, speed=speed,
            emotion=emotion, language=language, content_analysis=content_analysis
        )

        if not audio_timing_result.success:
            print("ERROR: Failed to generate audio with timing analysis.")
            self.update_progress(0, "Failed to generate audio")
            return None

        # Store timing result for subtitle generation
        self.audio_timing_result = audio_timing_result
        self.update_progress(40, "Audio generated with timing analysis for subtitle synchronization")

        # Speech recognition validation disabled for speed optimization
        # enable_speech_validation = getattr(self, 'enable_speech_validation', False)
        # if enable_speech_validation:
        #     validation_result = self._validate_speech_recognition(audio_file, stop_event)
        #     if validation_result is not None and not validation_result:
        #         self.update_progress(45, "⚠️ Speech recognition validation failed, but continuing...")
        #     elif validation_result:
        #         self.update_progress(45, "✅ Speech recognition validation passed")

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

            print(f"Using user-selected aspect ratio: {user_aspect_ratio} -> {aspect_ratio_str}")
        except Exception:
            print(f"Could not load user aspect ratio, using default: {aspect_ratio_str}")

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

        print(f"Using aspect ratio: {aspect_ratio} (from {aspect_ratio_str})")

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

        # Add content analysis to enhancement options if available
        if hasattr(self, 'content_analysis'):
            enhancement_options['content_analysis'] = self.content_analysis
            # Reduced logging: print(f"Using emotion-aware video generation for {self.content_analysis.content_type.value} content")

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
            fit_method=fit_method
        )

        if success:
            self.update_progress(80, "Video slideshow created successfully")
            return video_file
        else:
            self.update_progress(0, "Failed to create video slideshow")
            return None

    def _generate_subtitles(self, video_file, audio_file, output_dir, stop_event):
        """Generate subtitles for the video using TTS-to-Text timing synchronization"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(85, "Generating subtitles...")

        # Use audio timing result for synchronized subtitle generation
        audio_timing_result = getattr(self, 'audio_timing_result', None)
        if not audio_timing_result:
            print("ERROR: No audio timing result available for subtitle synchronization.")
            self.update_progress(0, "Failed to generate subtitles - no timing data")
            return None

        from services.subtitle_service import generate_subtitles_with_timing_sync
        subtitle_file = os.path.join(output_dir, "subtitles.ass")

        # Get subtitle style from enhancement options or config default
        from config import SUBTITLE_CONFIG
        default_style = SUBTITLE_CONFIG.get("default_style", "modern_glow")
        subtitle_style = self.enhancement_options.get("subtitle_style", default_style)

        # Use validated text if available, otherwise use original text
        text_for_subtitles = getattr(self, 'validated_text', self.text_input)

        if generate_subtitles_with_timing_sync(text_for_subtitles, audio_timing_result, subtitle_file, subtitle_style):
            self.update_progress(90, "Subtitles generated successfully with TTS-to-Text timing synchronization")
            if hasattr(self, 'validated_text') and self.validated_text != self.text_input:
                from utils.logging_utils import log_speech_recognition
                log_speech_recognition(f"📝 Subtitles generated using validated text")
            print("✅ Subtitles generated with TTS-to-Text timing synchronization")
            return subtitle_file
        else:
            print("ERROR: Failed to generate synchronized subtitles.")
            self.update_progress(0, "Failed to generate subtitles")
            return None

    def _validate_speech_recognition(self, audio_file, stop_event=None):
        """
        Validate speech recognition accuracy for the generated audio

        Args:
            audio_file: Path to the generated audio file
            stop_event: Threading event to stop the process

        Returns:
            bool: True if validation passes, False if fails, None if error
        """
        try:
            if stop_event and stop_event.is_set():
                return None

            self.update_progress(52, "Validating speech recognition accuracy...")

            # Import enhanced speech recognition service
            from services.enhanced_speech_recognition import EnhancedSpeechRecognitionService

            # Initialize enhanced speech recognition service
            speech_service = EnhancedSpeechRecognitionService()

            if not speech_service.is_available():
                print("⚠️ Speech recognition service not available, skipping validation")
                return None

            # Prepare voice settings for validation
            voice_settings = {
                'speed': getattr(self, 'tts_settings', {}).get('speed', 1.0),
                'emotion': getattr(self, 'tts_settings', {}).get('emotion', 'neutral'),
                'language': getattr(self, 'tts_settings', {}).get('language', 'en'),
                'voice_actor': getattr(self, 'tts_settings', {}).get('voice_actor', None)
            }

            # Update voice settings with any speech validation specific settings
            voice_settings.update(self.speech_validation_settings)

            # Use content-type aware speech recognition with post-processing
            content_analysis = getattr(self, 'content_analysis', None)
            content_type = content_analysis.content_type if content_analysis else None

            # Use enhanced speech recognition with multiple validation methods
            enhanced_result = speech_service.validate_audio_with_enhanced_methods(
                audio_file=audio_file,
                original_text=self.text_input,
                content_type=content_type
            )

            if not enhanced_result.success:
                print("⚠️ Enhanced speech recognition failed")
                return False

            recognized_text = enhanced_result.final_text
            confidence_score = enhanced_result.confidence_score
            method_used = enhanced_result.method_used

            # Check if validation passes threshold (with content-type aware thresholds)
            threshold = self._get_content_aware_threshold(content_type)
            passes_validation = confidence_score >= threshold

            # Log validation results with method information
            print(f"Enhanced Speech Recognition: {confidence_score:.1%} via {method_used} ({'✅ PASS' if passes_validation else '❌ FAIL'})")

            # Log service status for transparency
            service_status = speech_service.get_service_status()
            if service_status['enhanced_mode']:
                print(f"🔧 Enhanced mode: Vosk={service_status['vosk_available']}, Whisper={service_status['whisper_available']}")
            else:
                print(f"🔧 Standard mode: Vosk={service_status['vosk_available']}")

            # Store enhanced validation results for potential use by UI
            self.last_speech_validation_result = {
                'original_text': self.text_input,
                'recognized_text': recognized_text,
                'confidence_score': confidence_score,
                'method_used': method_used,
                'passes_validation': passes_validation,
                'threshold': threshold,
                'vosk_available': service_status['vosk_available'],
                'whisper_available': service_status['whisper_available'],
                'enhanced_mode': service_status['enhanced_mode']
            }

            # Automatically apply recognized text to final output if validation passes
            if passes_validation and confidence_score >= 0.8:  # High confidence threshold
                from utils.logging_utils import log_speech_recognition
                log_speech_recognition(f"🎯 Applying recognized text to video output (confidence: {confidence_score:.1%}, method: {method_used})")
                # Update the text input with the recognized text for consistency
                self.validated_text = recognized_text
                # Log the change for transparency (condensed)
                if recognized_text != self.text_input:
                    log_speech_recognition(f"📝 Text refined for better accuracy using {method_used}")
            else:
                # Keep original text if validation fails or confidence is low
                self.validated_text = self.text_input
                if not passes_validation:
                    print(f"⚠️ Using original text due to validation failure")
                else:
                    print(f"⚠️ Using original text due to low confidence ({confidence_score:.1%})")

            return passes_validation

        except Exception as e:
            print(f"❌ Error during speech recognition validation: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_content_aware_threshold(self, content_type):
        """Get content-type specific validation threshold"""
        from services.content_analysis import ContentType

        # Content-type specific thresholds
        thresholds = {
            ContentType.HISTORICAL: 0.75,      # Higher threshold for historical content (more proper nouns)
            ContentType.STORY_REVIEW: 0.70,    # Standard threshold for stories
            ContentType.QUOTE_REFLECTION: 0.65, # Lower threshold for philosophical content
            ContentType.EDUCATIONAL: 0.72,     # Slightly higher for educational content
            ContentType.ENTERTAINMENT: 0.68,   # Lower for entertainment (more casual language)
            ContentType.DOCUMENTARY: 0.74,     # Higher for documentary (technical terms)
            ContentType.PERSONAL: 0.66,        # Lower for personal content (informal language)
            ContentType.UNKNOWN: 0.70          # Default threshold
        }

        # Use content-specific threshold or fall back to configured threshold
        return thresholds.get(content_type, self.speech_validation_threshold)

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

        print(f"Speech validation configured: enabled={enable}, threshold={threshold:.1%}")

    def get_last_speech_validation_result(self):
        """Get the results of the last speech validation"""
        return getattr(self, 'last_speech_validation_result', None)


def show_version():
    return f"Video Generator v{__version__}"
