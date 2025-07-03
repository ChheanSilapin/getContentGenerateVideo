"""
Core speech recognition service - streamlined and focused
"""
import os
import tempfile
import time
import re
from typing import Dict, List, Optional
from difflib import SequenceMatcher

from services.speech_recognition_models import SpeechRecognitionResult, TextComparisonMetrics
# Content analysis removed

# Check for Vosk availability
try:
    import vosk
    import json
    import wave
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

# TTS is now handled by dedicated TTS providers (Edge TTS + Kokoro TTS)
# This module focuses on speech recognition only
GTTS_AVAILABLE = False  # Legacy - TTS moved to services/tts_providers.py

# Import logging utilities for emoji handling
from utils.logging_utils import clean_log_message


def initialize_speech_recognition(model_path: str):
    """Initialize Vosk speech recognition model and recognizer with word-level timestamps"""
    try:
        if not VOSK_AVAILABLE:
            return None, None

        model = vosk.Model(model_path)
        recognizer = vosk.KaldiRecognizer(model, 16000)

        # Enable word-level timestamps - this is the key fix!
        recognizer.SetWords(True)

        return model, recognizer
    except Exception as e:
        print(clean_log_message(f" Failed to initialize Vosk: {e}"))
        return None, None


def recognize_speech_from_file(audio_file: str, model, recognizer):
    """Recognize speech from audio file using Vosk with word-level timestamps"""
    try:
        if not VOSK_AVAILABLE or not model or not recognizer:
            return {"text": "", "words": []}

        # Convert MP3 to WAV if needed
        wav_file = _convert_to_wav_if_needed(audio_file)
        if not wav_file:
            return {"text": "", "words": []}

        # Open audio file
        wf = wave.open(wav_file, 'rb')

        # Check audio format
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            print(clean_log_message(" Audio file must be WAV format mono PCM."))
            wf.close()
            # Clean up temporary file if created
            if wav_file != audio_file and os.path.exists(wav_file):
                os.remove(wav_file)
            return {"text": "", "words": []}

        # Process audio and collect word-level timing data
        all_words = []
        text_parts = []

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                if 'result' in result:
                    # Extract word-level timing data
                    for word_data in result['result']:
                        all_words.append({
                            'word': word_data.get('word', ''),
                            'start': word_data.get('start', 0.0),
                            'end': word_data.get('end', 0.0),
                            'conf': word_data.get('conf', 0.0)
                        })
                if 'text' in result and result['text'].strip():
                    text_parts.append(result['text'])

        # Get final result
        final_result = json.loads(recognizer.FinalResult())
        if 'result' in final_result:
            # Extract word-level timing data from final result
            for word_data in final_result['result']:
                all_words.append({
                    'word': word_data.get('word', ''),
                    'start': word_data.get('start', 0.0),
                    'end': word_data.get('end', 0.0),
                    'conf': word_data.get('conf', 0.0)
                })
        if 'text' in final_result and final_result['text'].strip():
            text_parts.append(final_result['text'])

        wf.close()

        # Clean up temporary file if created
        if wav_file != audio_file and os.path.exists(wav_file):
            os.remove(wav_file)

        # Return both text and word-level timing data
        full_text = ' '.join(text_parts).strip()
        return {
            "text": full_text,
            "words": all_words
        }

    except Exception as e:
        print(clean_log_message(f" Speech recognition error: {e}"))
        return {"text": "", "words": []}


def _convert_to_wav_if_needed(audio_file: str) -> str:
    """Convert MP3 to WAV for Vosk if needed"""
    try:
        # Check if already WAV
        if audio_file.lower().endswith('.wav'):
            return audio_file

        # Try to import pydub for conversion
        try:
            from pydub import AudioSegment
        except ImportError:
            print(clean_log_message(" pydub not available for MP3 conversion. Install with: pip install pydub"))
            return None

        # Convert MP3 to WAV
        audio = AudioSegment.from_mp3(audio_file)

        # Convert to mono 16kHz 16-bit (Vosk requirements)
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_frame_rate(16000)  # 16kHz
        audio = audio.set_sample_width(2)  # 16-bit

        # Create temporary WAV file
        wav_file = audio_file.replace('.mp3', '_vosk_temp.wav')
        audio.export(wav_file, format="wav")

        return wav_file

    except Exception as e:
        print(clean_log_message(f" Audio conversion error: {e}"))
        return None


def generate_audio(text: str, output_file: str, voice_actor: str = "Guy",
                  speed: float = 1.0, emotion: str = "neutral", language: str = 'en',
                  title: str = "") -> bool:
    """Generate audio using Edge TTS or Kokoro TTS (redirects to new TTS system)"""
    try:
        # Import the new TTS manager
        from services.tts_providers import get_tts_manager

        tts_manager = get_tts_manager()
        if not tts_manager:
            print(clean_log_message(" TTS manager not available"))
            return False

        # Use new TTS system with parameters
        tts_params = {
            'language': language,
            'emotion': emotion,
            'speed': speed,
            'voice_actor': voice_actor
        }

        success = tts_manager.generate_speech(text, output_file, **tts_params)
        if success:
            print(clean_log_message(f" Audio generated with new TTS system: {output_file}"))
        else:
            print(clean_log_message(" Failed to generate audio with new TTS system"))

        return success

    except Exception as e:
        print(clean_log_message(f" TTS error: {e}"))
        return False


class SpeechRecognitionService:
    """Streamlined speech recognition service"""
    
    def __init__(self, model_path=None, temp_dir=None):
        """Initialize the speech recognition service"""
        self.model_path = model_path or self._find_vosk_model()
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.vosk_model = None
        self.vosk_recognizer = None
        # Post-processor removed for performance optimization
        
        # Initialize Vosk if available
        if VOSK_AVAILABLE and self.model_path:
            self.vosk_model, self.vosk_recognizer = initialize_speech_recognition(self.model_path)
            if self.vosk_model and self.vosk_recognizer:
                from utils.logging_utils import log_speech_recognition
                log_speech_recognition(f" Speech recognition ready")
            else:
                print(clean_log_message(" Speech recognition initialization failed"))
        else:
            print(clean_log_message(" Speech recognition unavailable"))
    
    def _find_vosk_model(self) -> Optional[str]:
        """Find available Vosk model in the models directory"""
        import sys

        # Check if running as PyInstaller executable
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller extracts files to sys._MEIPASS
                bundled_model = os.path.join(sys._MEIPASS, 'vosk-model')
                if os.path.exists(bundled_model) and self._is_valid_vosk_model(bundled_model):
                    from utils.logging_utils import log_speech_recognition
                    log_speech_recognition(f" Found bundled Vosk model: {bundled_model}")
                    return bundled_model

        # Fallback: check in models directory (for development)
        models_dir = "models"
        if not os.path.exists(models_dir):
            return None

        for item in os.listdir(models_dir):
            item_path = os.path.join(models_dir, item)
            if os.path.isdir(item_path) and "vosk-model" in item.lower():
                if self._is_valid_vosk_model(item_path):
                    from utils.logging_utils import log_speech_recognition
                    log_speech_recognition(f" Found development Vosk model: {item_path}")
                    return item_path
        return None
    
    def _is_valid_vosk_model(self, model_path: str) -> bool:
        """Check if a directory contains a valid Vosk model"""
        required_files = ["am", "graph", "conf"]
        return all(os.path.exists(os.path.join(model_path, f)) for f in required_files)
    
    def process_text_to_speech_to_text_with_postprocessing(self,
                                                         text: str,
                                                         content_type = None,
                                                         voice_settings: Dict = None,
                                                         cleanup_audio: bool = True) -> SpeechRecognitionResult:
        """
        Complete text-to-speech-to-text recognition workflow with post-processing
        """
        # First run the standard process
        result = self.process_text_to_speech_to_text(text, voice_settings, cleanup_audio)
        
        if result.success and result.recognized_text:
            # Skip post-processing for performance optimization
            post_processed_text = result.recognized_text

            # Recalculate metrics with post-processed text
            if post_processed_text != result.recognized_text:
                # Only show post-processing changes if significant
                if len(post_processed_text) > 50:  # Only for longer texts
                    from utils.logging_utils import log_speech_recognition
                    log_speech_recognition(f"📝 Post-processing applied: '{result.recognized_text[:50]}...' → '{post_processed_text[:50]}...'")

                # Update comparison metrics with post-processed text
                comparison_metrics = self._compare_texts(text, post_processed_text)
                
                # Create new result with post-processed text
                result = SpeechRecognitionResult(
                    original_text=result.original_text,
                    recognized_text=post_processed_text,
                    similarity_score=comparison_metrics.similarity_score,
                    word_accuracy=comparison_metrics.word_accuracy,
                    character_accuracy=comparison_metrics.character_accuracy,
                    differences=comparison_metrics.differences,
                    processing_time=result.processing_time,
                    audio_file_path=result.audio_file_path,
                    success=True
                )
        
        return result

    def recognize_speech_from_audio_with_postprocessing(self,
                                                       audio_file: str,
                                                       original_text: str,
                                                       content_type = None) -> SpeechRecognitionResult:
        """
        Recognize speech from existing audio file with post-processing
        This avoids redundant TTS generation when we already have the audio
        """
        try:
            start_time = time.time()

            # Step 1: Recognize speech from existing audio
            recognized_text = self._recognize_speech_from_audio(audio_file)

            # Step 2: Skip post-processing for performance
            if recognized_text:
                post_processed_text = recognized_text

                if post_processed_text != recognized_text:
                    # Only show post-processing changes if significant
                    if len(post_processed_text) > 50:  # Only for longer texts
                        from utils.logging_utils import log_speech_recognition
                        log_speech_recognition(f"📝 Post-processing applied: '{recognized_text[:50]}...' → '{post_processed_text[:50]}...'")

                recognized_text = post_processed_text

            # Step 3: Compare with original text
            comparison_metrics = self._compare_texts(original_text, recognized_text)

            # Step 4: Create result
            result = SpeechRecognitionResult(
                original_text=original_text,
                recognized_text=recognized_text,
                similarity_score=comparison_metrics.similarity_score,
                word_accuracy=comparison_metrics.word_accuracy,
                character_accuracy=comparison_metrics.character_accuracy,
                differences=comparison_metrics.differences,
                processing_time=time.time() - start_time,
                audio_file_path=audio_file,
                success=True
            )

            return result

        except Exception as e:
            print(f"Error in speech recognition from audio: {e}")
            return SpeechRecognitionResult(
                original_text=original_text,
                recognized_text="",
                similarity_score=0.0,
                word_accuracy=0.0,
                character_accuracy=0.0,
                differences=[],
                processing_time=time.time() - start_time,
                audio_file_path="",
                success=False
            )
    
    def process_text_to_speech_to_text(self,
                                     text: str,
                                     voice_settings: Dict = None,
                                     cleanup_audio: bool = True) -> SpeechRecognitionResult:
        """Complete text-to-speech-to-text recognition workflow"""
        start_time = time.time()

        # Validate inputs
        if not text or not text.strip():
            return self._create_error_result("", "Empty text provided", start_time)

        # TTS availability is now checked by the TTS manager
        # Legacy check removed - TTS handled by services/tts_providers.py

        if not self.vosk_model or not self.vosk_recognizer:
            return self._create_error_result(text, "Vosk speech recognition not available", start_time)

        # Use raw text directly - no preprocessing needed for modern TTS
        # Edge TTS and Kokoro TTS can handle complex formatting naturally
        processed_text = text
        
        try:
            # Step 1: Generate audio from processed text using Edge TTS or Kokoro TTS
            audio_file = self._generate_audio_file(processed_text, voice_settings)
            if not audio_file:
                return self._create_error_result(text, "Failed to generate audio", start_time)

            # Step 2: Recognize speech from audio using Vosk
            recognized_text = self._recognize_speech_from_audio(audio_file)

            # Step 3: Compare original and recognized text (use original for comparison)
            comparison_metrics = self._compare_texts(text, recognized_text)
            
            # Step 4: Create result
            result = SpeechRecognitionResult(
                original_text=text,
                recognized_text=recognized_text,
                similarity_score=comparison_metrics.similarity_score,
                word_accuracy=comparison_metrics.word_accuracy,
                character_accuracy=comparison_metrics.character_accuracy,
                differences=comparison_metrics.differences,
                processing_time=time.time() - start_time,
                audio_file_path=audio_file if not cleanup_audio else "",
                success=True
            )
            
            # Cleanup audio file if requested
            if cleanup_audio and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                except Exception as e:
                    print(f"Warning: Could not cleanup audio file {audio_file}: {e}")
            
            return result
            
        except Exception as e:
            return self._create_error_result(text, f"Error during processing: {str(e)}", start_time)
    
    def _create_error_result(self, text: str, error_message: str, start_time: float) -> SpeechRecognitionResult:
        """Create an error result"""
        return SpeechRecognitionResult(
            original_text=text,
            recognized_text="",
            similarity_score=0.0,
            word_accuracy=0.0,
            character_accuracy=0.0,
            differences=[],
            processing_time=time.time() - start_time,
            audio_file_path="",
            success=False,
            error_message=error_message
        )
    
    def _generate_audio_file(self, text: str, voice_settings: Dict = None) -> Optional[str]:
        """Generate audio file from text using Edge TTS or Kokoro TTS"""
        try:
            audio_file = os.path.join(self.temp_dir, f"speech_recognition_{int(time.time())}.mp3")
            
            settings = voice_settings or {}
            success = generate_audio(
                text=text,
                output_file=audio_file,
                voice_actor=settings.get('voice_actor', None),
                speed=settings.get('speed', 0.8),
                emotion=settings.get('emotion', 'neutral'),
                language=settings.get('language', 'en')
            )
            
            if success and os.path.exists(audio_file):
                print(clean_log_message(f" Audio generated: {audio_file}"))
                return audio_file
            else:
                print(clean_log_message(" Failed to generate audio"))
                return None

        except Exception as e:
            print(clean_log_message(f" Error generating audio: {e}"))
            return None
    
    def _recognize_speech_from_audio(self, audio_file: str) -> str:
        """Recognize speech from audio file using Vosk"""
        try:
            if not os.path.exists(audio_file):
                print(clean_log_message(f" Audio file not found: {audio_file}"))
                return ""

            result = recognize_speech_from_file(
                audio_file,
                self.vosk_model,
                self.vosk_recognizer
            )

            # Extract text from the new format
            if isinstance(result, dict):
                return result.get('text', '').strip()
            else:
                # Fallback for old format
                return str(result).strip()

        except Exception as e:
            print(clean_log_message(f" Speech recognition error: {e}"))
            return ""
    
    def _compare_texts(self, original: str, recognized: str) -> TextComparisonMetrics:
        """Compare original and recognized text with detailed metrics"""
        try:
            # Normalize texts for comparison
            original_normalized = self._normalize_text(original)
            recognized_normalized = self._normalize_text(recognized)
            
            # Calculate similarity using SequenceMatcher
            similarity_score = SequenceMatcher(None, original_normalized, recognized_normalized).ratio()
            
            # Word-level analysis
            original_words = original_normalized.split()
            recognized_words = recognized_normalized.split()
            
            # Calculate accuracies
            word_accuracy = self._calculate_word_accuracy(original_words, recognized_words)
            character_accuracy = self._calculate_character_accuracy(original_normalized, recognized_normalized)
            levenshtein_distance = self._levenshtein_distance(original_normalized, recognized_normalized)
            differences = self._find_differences(original, recognized)
            
            return TextComparisonMetrics(
                total_words_original=len(original_words),
                total_words_recognized=len(recognized_words),
                matching_words=sum(1 for w1, w2 in zip(original_words, recognized_words) if w1 == w2),
                word_accuracy=word_accuracy,
                character_accuracy=character_accuracy,
                similarity_score=similarity_score,
                levenshtein_distance=levenshtein_distance,
                differences=differences
            )
            
        except Exception as e:
            print(clean_log_message(f" Error comparing texts: {e}"))
            return TextComparisonMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0, [])
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\']', '', text)
        text = re.sub(r'\s\'\s', ' ', text)
        return text.strip()
    
    def _calculate_word_accuracy(self, original_words: List[str], recognized_words: List[str]) -> float:
        """Calculate word-level accuracy"""
        if not original_words:
            return 1.0 if not recognized_words else 0.0
        
        matcher = SequenceMatcher(None, original_words, recognized_words)
        matching_blocks = matcher.get_matching_blocks()
        total_matches = sum(block.size for block in matching_blocks)
        return total_matches / len(original_words)
    
    def _calculate_character_accuracy(self, original: str, recognized: str) -> float:
        """Calculate character-level accuracy"""
        if not original:
            return 1.0 if not recognized else 0.0
        return SequenceMatcher(None, original, recognized).ratio()
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _find_differences(self, original: str, recognized: str) -> List[Dict]:
        """Find specific differences between original and recognized text"""
        differences = []
        original_words = original.split()
        recognized_words = recognized.split()
        
        matcher = SequenceMatcher(None, original_words, recognized_words)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                differences.append({
                    'type': tag,
                    'original': ' '.join(original_words[i1:i2]) if i1 < i2 else '',
                    'recognized': ' '.join(recognized_words[j1:j2]) if j1 < j2 else '',
                    'position': i1
                })
        
        return differences
    
    def is_available(self):
        """Check if speech recognition service is available"""
        return (VOSK_AVAILABLE and GTTS_AVAILABLE and 
                self.vosk_model is not None and 
                self.vosk_recognizer is not None)
