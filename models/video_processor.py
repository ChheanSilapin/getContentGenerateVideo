"""
Video Processing Component - Handles individual video operations
Extracted from VideoGeneratorModel to reduce complexity
"""
import os
from datetime import datetime
from utils.error_helpers import handle_operation_error

# Import logging utilities for emoji handling
from utils.logging_utils import clean_log_message


class VideoProcessor:
    """Handles individual video processing operations"""
    
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.current_output_dir = None
        self.enhancement_options = {}

        # TTS settings (load from user settings)
        self.tts_settings = self._load_tts_settings()

        # Speech recognition validation settings (disabled for speed optimization)
        self.enable_speech_validation = False
        self.speech_validation_threshold = 0.7

        # Processing state
        self.text_input = ""
        self.validated_text = None
        self.last_speech_validation_result = None

    def _load_tts_settings(self):
        """Load TTS settings from user_settings.json for video tab"""
        try:
            from utils.settings_manager import SettingsManager
            settings_manager = SettingsManager()
            video_tab_settings = settings_manager.get_tab_settings('video_tab')

            # Load video-specific settings
            self.enable_speech_validation = video_tab_settings.get('enable_speech_validation', False)
            self.auto_cleanup = video_tab_settings.get('auto_cleanup', True)

            # Load audio settings for video processing
            self.current_audio_settings = {
                'mute_original': video_tab_settings.get('mute_original_audio', True),
                'original_volume': video_tab_settings.get('original_audio_volume', 0.7)
            }

            return {
                'language': video_tab_settings.get('tts_language', 'en'),
                'voice_actor': video_tab_settings.get('tts_voice_actor', 'Guy'),
                'speed': video_tab_settings.get('tts_speed', 1.0),
                'emotion': video_tab_settings.get('tts_emotion', 'neutral')
            }
        except Exception as e:
            print(f"Warning: Could not load TTS settings from user_settings.json: {e}")
            # Return defaults if loading fails
            return {
                'language': 'en',
                'voice_actor': 'Guy',
                'speed': 1.0,
                'emotion': 'neutral'
            }

    def update_progress(self, value, message=None):
        """Update progress value and message"""
        if self.progress_callback:
            self.progress_callback(value, message)
    
    def process_video_with_prompt(self, video_file, text_input, stop_event=None, output_folder=None, skip_auto_cleanup=False):
        """
        Process a video file with a text prompt to add voice-over and subtitles

        Args:
            video_file: Path to the input video file
            text_input: Text prompt for voice-over
            stop_event: Threading event to stop the process
            output_folder: Custom output folder
            skip_auto_cleanup: Skip automatic cleanup (for group processing)

        Returns:
            str: Path to the generated video file
        """
        # Store source files for intelligent filename generation
        self.source_files = [video_file] if video_file else []

        try:
            # Check if we should stop
            if stop_event and stop_event.is_set():
                self.update_progress(0, "Process stopped by user")
                return None

            # Check if we have text input for voice-over
            has_text_input = text_input and text_input.strip()

            # Store text input for processing
            self.text_input = text_input if has_text_input else ""

            # Create output directory
            output_dir = self._create_output_directory(video_file, output_folder)
            self.current_output_dir = output_dir

            if has_text_input:
                # Step 1: Generate audio from text
                audio_file = self._generate_audio(text_input, output_dir, stop_event)
                if not audio_file:
                    return None

                # Step 2: Generate subtitles (using original video and audio)
                # Use improved phrase-based subtitles (word-by-word removed per user request)
                subtitle_type = "phrase"
                subtitle_file = self._generate_subtitles(text_input, video_file, audio_file, output_dir, stop_event, subtitle_type)
                if not subtitle_file:
                    return None

                # Step 3: Finalize video with voice-over and subtitles in one step
                final_video = self._finalize_video_with_voiceover_and_subtitles(video_file, audio_file, subtitle_file, output_dir, stop_event, skip_auto_cleanup)
            else:
                # No text input - finalize video without subtitles or voice-over
                self.update_progress(80, "Finalizing video without voice-over or subtitles")
                final_video = self._finalize_video_without_subtitles(video_file, output_dir, stop_event, skip_auto_cleanup)

            return final_video

        except Exception as e:
            handle_operation_error(None, "Video processing", e, show_dialog=False)
            return None
    
    def _create_output_directory(self, video_file, output_folder=None):
        """Create output directory for video processing"""
        import time
        # Use more precise timestamp with milliseconds to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        milliseconds = int(time.time() * 1000) % 1000
        unique_timestamp = f"{timestamp}_{milliseconds:03d}"
        video_name = os.path.splitext(os.path.basename(video_file))[0]

        # Sanitize video name for directory path to avoid filesystem issues
        from utils.filename_validator import sanitize_filename
        safe_video_name = sanitize_filename(video_name)

        if output_folder and os.path.isdir(output_folder):
            output_dir = os.path.join(output_folder, f"video_{safe_video_name}_{unique_timestamp}")
        else:
            base_output_dir = os.environ.get('VIDEO_GENERATOR_OUTPUT_DIR', 'output')
            output_dir = os.path.join(base_output_dir, f"video_{safe_video_name}_{unique_timestamp}")

        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
        return output_dir
    
    def _generate_audio(self, text_input, output_dir, stop_event):
        """Generate audio from text input using Edge TTS or Kokoro TTS with speech recognition"""
        if stop_event and stop_event.is_set():
            return None

        from utils.logging_utils import log_step, log_essential
        log_step(1, 3, "Generating Audio")
        self.update_progress(20, "Analyzing content and generating audio...")

        # Use default settings for all content types

        from services.audio_service import generate_audio_with_timing_analysis
        audio_file = os.path.join(output_dir, "voice.mp3")

        # Reload TTS settings from current user settings to ensure we have the latest values
        current_tts_settings = self._load_tts_settings()

        # Get TTS settings from current settings, then enhancement options, then defaults
        tts_settings = getattr(self, 'tts_settings', {})
        tts_settings.update(current_tts_settings)  # Update with latest settings
        voice_actor = tts_settings.get('voice_actor', self.enhancement_options.get('voice_emotion', 'Guy'))
        speed = tts_settings.get('speed', 1.0)
        emotion = tts_settings.get('emotion', self.enhancement_options.get('voice_emotion', 'neutral'))
        language = tts_settings.get('language', 'en')

        log_essential(f"Using TTS settings: voice={voice_actor}, speed={speed:.1f}, emotion={emotion}, language={language}")

        # Generate audio with timing analysis for subtitle synchronization
        audio_timing_result = generate_audio_with_timing_analysis(
            text_input, audio_file, voice_actor=voice_actor, speed=speed,
            emotion=emotion, language=language
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

            self.update_progress(42, "Validating speech recognition accuracy...")

            # Import enhanced speech recognition service
            from services.enhanced_speech_recognition import EnhancedSpeechRecognitionService

            # Initialize enhanced speech recognition service
            speech_service = EnhancedSpeechRecognitionService()

            if not speech_service.is_available():
                return None

            # Get voice settings for validation (use current TTS settings)
            tts_settings = getattr(self, 'tts_settings', {})
            voice_settings = {
                'voice_actor': tts_settings.get('voice_actor', 'Default'),
                'speed': tts_settings.get('speed', 1.0),
                'emotion': tts_settings.get('emotion', 'neutral'),
                'language': tts_settings.get('language', 'en')
            }

            # Use enhanced speech recognition with multiple validation methods

            # Use enhanced validation with whisper-timestamped
            enhanced_result = speech_service.validate_audio_with_enhanced_methods(
                audio_file=audio_file,
                original_text=self.text_input
            )

            if not enhanced_result.success:
                return False

            recognized_text = enhanced_result.final_text
            confidence_score = enhanced_result.confidence_score
            method_used = enhanced_result.method_used

            # Check if validation passes threshold
            threshold = self._get_content_aware_threshold(None)
            passes_validation = confidence_score >= threshold

            # Store enhanced validation results
            service_status = speech_service.get_service_status()
            self.last_speech_validation_result = {
                'original_text': self.text_input,
                'recognized_text': recognized_text,
                'confidence_score': confidence_score,
                'method_used': method_used,
                'passes_validation': passes_validation,
                'threshold': threshold,
                'whisper_available': service_status['whisper_available'],
                'enhanced_mode': service_status['enhanced_mode']
            }

            # Automatically apply recognized text if validation passes
            if passes_validation and confidence_score >= 0.8:  # High confidence threshold
                self.validated_text = recognized_text
            else:
                # Keep original text if validation fails or confidence is low
                self.validated_text = self.text_input

            return passes_validation

        except Exception as e:
            return None

    def _get_content_aware_threshold(self, content_type):
        """Get default validation threshold (content analysis removed)"""
        return 0.70

    def _add_voiceover(self, video_file, audio_file, output_dir, stop_event):
        """Add voice-over to video"""
        if stop_event and stop_event.is_set():
            return None
            
        from utils.logging_utils import log_step
        log_step(2, 3, "Adding voice-over to video")
        self.update_progress(50, "Adding voice-over to video...")
        
        video_with_audio = os.path.join(output_dir, "video_with_audio.mp4")
        
        # Get audio settings
        audio_settings = getattr(self, 'current_audio_settings', {"mute_original": False, "original_volume": 0.3})
        
        from services.video_service import add_voiceover_to_video
        success = add_voiceover_to_video(
            video_file,
            audio_file,
            video_with_audio,
            mix_with_original=not audio_settings["mute_original"],
            original_volume=audio_settings["original_volume"]
        )
        
        if not success:
            print("ERROR: Failed to add voice-over to video.")
            self.update_progress(0, "Failed to add voice-over to video")
            return None

        self.update_progress(70, "Voice-over added successfully")
        return video_with_audio
    
    def _generate_subtitles(self, text_input, video_file, audio_file, output_dir, stop_event, subtitle_type="phrase"):
        """
        Generate improved phrase-based subtitles with smart mapping

        Word-by-word subtitle option removed per user request.
        Now always uses improved phrase-based subtitles with smart timing.
        """
        if stop_event and stop_event.is_set():
            return None

        # Step 3: Generating Improved Phrase-Based Subtitles
        self.update_progress(75, "Generating improved phrase-based subtitles...")

        # Always use improved phrase-based subtitle generation
        from services.subtitle_service import generate_subtitles_with_timing_sync
        generate_function = generate_subtitles_with_timing_sync
        print("[SUBTITLE] Using improved phrase-based subtitle generation with smart mapping")

        subtitle_file = os.path.join(output_dir, "subtitles.ass")

        # Get subtitle style from enhancement options or config default
        from config import SUBTITLE_CONFIG
        default_style = SUBTITLE_CONFIG.get("default_style", "modern_glow")
        subtitle_style = self.enhancement_options.get("subtitle_style", default_style)

        # For video processing, extract timing from the final video with audio
        # This ensures perfect synchronization with the actual video timing
        print("[SUBTITLE] Using original audio timing for perfect synchronization...")

        # Use the original audio timing result instead of re-extracting from video
        # This avoids timing offsets introduced by video processing (avoid_negative_ts, etc.)
        if not hasattr(self, 'audio_timing_result') or not self.audio_timing_result or not self.audio_timing_result.success:
            print("ERROR: Original audio timing not available.")
            self.update_progress(0, "Failed to get original audio timing for subtitles")
            return None

        video_timing_result = self.audio_timing_result
        print(f"[SUBTITLE] Using original audio timing for perfect synchronization")

        # Always use original text for subtitles to preserve formatting ($1.2 trillion, June 28th, 2025, 19.7%)
        # The subtitle service preserves original formatting while using timing from speech recognition

        if not generate_function(text_input, video_timing_result, subtitle_file, subtitle_style):
            print(f"ERROR: Failed to generate improved phrase-based subtitles.")
            self.update_progress(0, f"Failed to generate improved phrase-based subtitles")
            return None

        self.update_progress(90, f"Improved phrase-based subtitles generated successfully")
        return subtitle_file
    
    def _finalize_video_with_voiceover_and_subtitles(self, video_file, audio_file, subtitle_file, output_dir, stop_event, skip_auto_cleanup=False):
        """Finalize video by adding voice-over and subtitles in one step (eliminates video_with_audio.mp4 intermediate)"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(95, "Finalizing video with voice-over and subtitles...")

        from services.video_finalization import merge_video_with_voiceover_and_subtitles
        from utils.filename_validator import get_final_output_filename
        from utils.output_manager import get_output_manager

        # Use custom filename if provided, otherwise use default
        custom_filename = getattr(self, 'custom_filename', '')
        temp_filename = get_final_output_filename(custom_filename, "final_output")
        temp_output = os.path.join(output_dir, temp_filename)

        # Merge video with voice-over and subtitles in one step
        result = merge_video_with_voiceover_and_subtitles(video_file, audio_file, subtitle_file, temp_output)

        if result:
            # Move to final output directory
            output_manager = get_output_manager()
            final_video_path = output_manager.move_final_video(result, custom_filename)

            if final_video_path:
                self.update_progress(100, f"Video saved: {os.path.basename(final_video_path)}")

                # Clean up temporary directory if not skipping cleanup
                if not skip_auto_cleanup:
                    output_manager.cleanup_temp_directory(output_dir)

                return final_video_path
            else:
                self.update_progress(0, "Failed to move video to output directory")
                return result  # Return temp path as fallback
        else:
            print("Failed to finalize video with voice-over and subtitles")
            self.update_progress(0, "Failed to finalize video")
            return None

    def _finalize_video(self, subtitle_file, video_file, output_dir, stop_event, skip_auto_cleanup=False):
        """Finalize video by merging with subtitles (legacy method - kept for compatibility)"""
        if stop_event and stop_event.is_set():
            return None

        # Reduced logging: print("\n--- Step 4: Finalizing Video ---")
        self.update_progress(95, "Finalizing video...")

        from services.video_finalization import merge_video_subtitle
        from utils.filename_validator import get_final_output_filename
        from utils.output_manager import get_output_manager

        # Use custom filename if provided, otherwise use default
        custom_filename = getattr(self, 'custom_filename', '')
        temp_filename = get_final_output_filename(custom_filename, "final_output")
        temp_output = os.path.join(output_dir, temp_filename)

        # Merge video with subtitles in temporary location
        result = merge_video_subtitle(video_file, subtitle_file, temp_output)

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

                # Clean up temporary directory if not skipping cleanup
                if not skip_auto_cleanup:
                    output_manager.cleanup_temp_directory(output_dir)

                return final_video_path
            else:
                self.update_progress(0, "Failed to move video to output directory")
                return result  # Return temp path as fallback
        else:
            print("Failed to finalize video")
            self.update_progress(0, "Failed to finalize video")
            return None

    def _finalize_video_without_subtitles(self, video_file, output_dir, stop_event, skip_auto_cleanup=False):
        """Finalize video without subtitles - just move to output directory"""
        if stop_event and stop_event.is_set():
            return None

        self.update_progress(95, "Finalizing video without subtitles...")

        from utils.filename_validator import get_final_output_filename
        from utils.output_manager import get_output_manager

        # Use custom filename if provided, otherwise use default
        custom_filename = getattr(self, 'custom_filename', '')
        temp_filename = get_final_output_filename(custom_filename, "final_output")
        temp_output = os.path.join(output_dir, temp_filename)

        # Copy video to final location in temp directory
        import shutil
        try:
            shutil.copy2(video_file, temp_output)
        except Exception as e:
            print(f"Failed to copy video: {e}")
            self.update_progress(0, "Failed to copy video")
            return None

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
            temp_video_path=temp_output,
            custom_filename=custom_filename,
            source_files=source_files,
            default_name="video"
        )

        if final_video_path:
            self.update_progress(100, f"Video saved: {os.path.basename(final_video_path)}")

            # Clean up temporary directory if not skipping cleanup
            if not skip_auto_cleanup:
                output_manager.cleanup_temp_directory(output_dir)

            return final_video_path
        else:
            self.update_progress(0, "Failed to move video to output directory")
            return temp_output  # Return temp path as fallback
