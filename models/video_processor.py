"""
Video Processing Component - Handles individual video operations
Extracted from VideoGeneratorModel to reduce complexity
"""
import os
from datetime import datetime
from utils.error_helpers import handle_operation_error


class VideoProcessor:
    """Handles individual video processing operations"""
    
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.current_output_dir = None
        self.enhancement_options = {}

        # TTS settings (load from user settings)
        self.tts_settings = self._load_tts_settings()

        # Speech recognition validation settings (enabled by default)
        self.enable_speech_validation = True
        self.speech_validation_threshold = 0.7

        # Processing state
        self.text_input = ""
        self.content_analysis = None
        self.validated_text = None
        self.last_speech_validation_result = None

    def _load_tts_settings(self):
        """Load TTS settings from user_settings.json for video tab"""
        try:
            from utils.settings_manager import SettingsManager
            settings_manager = SettingsManager()
            video_tab_settings = settings_manager.get_tab_settings('video_tab')

            # Load video-specific settings
            self.enable_speech_validation = video_tab_settings.get('enable_speech_validation', True)
            self.content_analysis_enabled = video_tab_settings.get('content_analysis_enabled', True)
            self.auto_cleanup = video_tab_settings.get('auto_cleanup', True)

            # Load audio settings for video processing
            self.current_audio_settings = {
                'mute_original': video_tab_settings.get('mute_original_audio', True),
                'original_volume': video_tab_settings.get('original_audio_volume', 0.7)
            }

            return {
                'language': video_tab_settings.get('tts_language', 'en'),
                'voice_actor': video_tab_settings.get('tts_voice_actor', 'Default'),
                'speed': video_tab_settings.get('tts_speed', 1.0),
                'emotion': video_tab_settings.get('tts_emotion', 'neutral')
            }
        except Exception as e:
            print(f"Warning: Could not load TTS settings from user_settings.json: {e}")
            # Return defaults if loading fails
            return {
                'language': 'en',
                'voice_actor': 'Default',
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
        try:
            # Check if we should stop
            if stop_event and stop_event.is_set():
                self.update_progress(0, "Process stopped by user")
                return None

            # Store text input for processing
            self.text_input = text_input

            # Create output directory
            output_dir = self._create_output_directory(video_file, output_folder)
            self.current_output_dir = output_dir

            # Step 1: Generate audio from text
            audio_file = self._generate_audio(text_input, output_dir, stop_event)
            if not audio_file:
                return None

            # Step 2: Add voice-over to original video
            video_with_audio = self._add_voiceover(video_file, audio_file, output_dir, stop_event)
            if not video_with_audio:
                return None

            # Step 3: Generate subtitles
            subtitle_file = self._generate_subtitles(text_input, video_with_audio, audio_file, output_dir, stop_event)
            if not subtitle_file:
                return None

            # Step 4: Finalize video with subtitles
            final_video = self._finalize_video(subtitle_file, video_with_audio, output_dir, stop_event, skip_auto_cleanup)

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

        if output_folder and os.path.isdir(output_folder):
            output_dir = os.path.join(output_folder, f"video_{video_name}_{unique_timestamp}")
        else:
            base_output_dir = os.environ.get('VIDEO_GENERATOR_OUTPUT_DIR', 'output')
            output_dir = os.path.join(base_output_dir, f"video_{video_name}_{unique_timestamp}")

        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
        return output_dir
    
    def _generate_audio(self, text_input, output_dir, stop_event):
        """Generate audio from text input using gTTS with content analysis and speech recognition"""
        if stop_event and stop_event.is_set():
            return None

        from utils.logging_utils import log_step, log_essential
        log_step(1, 3, "Generating Audio with gTTS")
        self.update_progress(20, "Analyzing content and generating audio...")

        # Perform content analysis for emotion-aware generation
        from services.content_analysis import ContentAnalyzer
        analyzer = ContentAnalyzer()
        content_analysis = analyzer.analyze_content(text_input, title="", context="")

        print(f"Content Analysis: Type={content_analysis.content_type.value}, "
              f"Emotion={content_analysis.emotional_tone.value}, "
              f"Confidence={content_analysis.confidence:.2f}")

        # Store content analysis for later use
        self.content_analysis = content_analysis

        from services.audio_service import generate_audio
        audio_file = os.path.join(output_dir, "voice.mp3")

        # Get TTS settings from enhancement options or use defaults
        tts_settings = getattr(self, 'tts_settings', {})
        voice_actor = tts_settings.get('voice_actor', self.enhancement_options.get('voice_emotion', 'Default'))
        speed = tts_settings.get('speed', 1.0)
        emotion = tts_settings.get('emotion', self.enhancement_options.get('voice_emotion', 'neutral'))
        language = tts_settings.get('language', 'en')

        # Apply content-aware settings if content analysis is available
        if content_analysis:
            voice_settings = content_analysis.recommended_voice_settings
            # Only override if user hasn't specified custom settings
            if voice_actor == 'Default':
                voice_actor = voice_settings.get('voice_actor', voice_actor)
            if language == 'en':
                language = voice_settings.get('language', language)
            speed = voice_settings.get('speed', speed)
            emotion = voice_settings.get('emotion', emotion)

            print(f"Using content-aware settings: type={content_analysis.content_type.value}, "
                  f"tone={content_analysis.emotional_tone.value}, speed={speed}, emotion={emotion}")

        log_essential(f"Using TTS settings: voice={voice_actor}, speed={speed}, emotion={emotion}, language={language}")

        if not generate_audio(text_input, audio_file, voice_actor=voice_actor, speed=speed, emotion=emotion,
                             language=language, content_analysis=content_analysis):
            print("ERROR: Failed to generate audio.")
            self.update_progress(0, "Failed to generate audio")
            return None

        self.update_progress(40, "Audio generated successfully with content-aware settings")

        # Optional speech recognition validation (enable by default for video generation)
        enable_speech_validation = getattr(self, 'enable_speech_validation', True)
        if enable_speech_validation:
            validation_result = self._validate_speech_recognition(audio_file, stop_event)
            if validation_result is not None and not validation_result:
                # Validation failed, but continue with warning
                self.update_progress(45, "⚠️ Speech recognition validation failed, but continuing...")
            elif validation_result:
                self.update_progress(45, "✅ Speech recognition validation passed")

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
                print("⚠️ Speech recognition service not available, skipping validation")
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
            content_analysis = getattr(self, 'content_analysis', None)
            content_type = content_analysis.content_type if content_analysis else None

            # Use enhanced validation with both Vosk and whisper-timestamped
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

            # Store enhanced validation results
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

            # Automatically apply recognized text if validation passes
            if passes_validation and confidence_score >= 0.8:  # High confidence threshold
                print(f"🎯 Applying recognized text to video output (confidence: {confidence_score:.1%}, method: {method_used})")
                self.validated_text = recognized_text
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
            return None

    def _get_content_aware_threshold(self, content_type):
        """Get content-type specific validation threshold"""
        try:
            from services.content_analysis import ContentType

            # Content-specific thresholds (lower for complex content)
            thresholds = {
                ContentType.EDUCATIONAL: 0.65,
                ContentType.HISTORICAL: 0.60,
                ContentType.TECHNICAL: 0.55,
                ContentType.QUOTE_REFLECTION: 0.70,
                ContentType.STORY: 0.75,
                ContentType.GENERAL: 0.70
            }

            # Use content-specific threshold or fall back to default
            return thresholds.get(content_type, 0.70)
        except:
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
    
    def _generate_subtitles(self, text_input, video_file, audio_file, output_dir, stop_event):
        """Generate subtitles for video"""
        if stop_event and stop_event.is_set():
            return None
            
        # Step 3: Generating Subtitles
        self.update_progress(75, "Generating subtitles...")
        
        from services.subtitle_service import generate_subtitles
        subtitle_file = os.path.join(output_dir, "subtitles.ass")
        
        # Get subtitle style from enhancement options or config default
        from config import SUBTITLE_CONFIG
        default_style = SUBTITLE_CONFIG.get("default_style", "modern_glow")
        subtitle_style = self.enhancement_options.get("subtitle_style", default_style)
        
        # Use validated text if available, otherwise use original text
        text_for_subtitles = getattr(self, 'validated_text', text_input)

        if not generate_subtitles(text_for_subtitles, video_file, audio_file, subtitle_file, subtitle_style):
            print("ERROR: Failed to generate subtitles.")
            self.update_progress(0, "Failed to generate subtitles")
            return None

        # Log which text was used for subtitles
        if hasattr(self, 'validated_text') and self.validated_text != text_input:
            print("📝 Subtitles generated using validated text from speech recognition")

        self.update_progress(90, "Subtitles generated successfully")
        return subtitle_file
    
    def _finalize_video(self, subtitle_file, video_file, output_dir, stop_event, skip_auto_cleanup=False):
        """Finalize video by merging with subtitles"""
        if stop_event and stop_event.is_set():
            return None
            
        # Reduced logging: print("\n--- Step 4: Finalizing Video ---")
        self.update_progress(95, "Finalizing video...")
        
        from services.video_finalization import merge_video_subtitle
        from utils.filename_validator import get_final_output_filename

        # Use custom filename if provided, otherwise use default
        custom_filename = getattr(self, 'custom_filename', '')
        final_filename = get_final_output_filename(custom_filename, "final_output")
        final_output = os.path.join(output_dir, final_filename)
        
        result = merge_video_subtitle(video_file, subtitle_file, final_output)
        
        if result:
            self.update_progress(100, f"Video generated successfully: {os.path.basename(result)}")
            return result
        else:
            print("Failed to finalize video")
            self.update_progress(0, "Failed to finalize video")
            return None
