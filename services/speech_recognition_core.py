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
from services.speech_recognition_postprocessor import SpeechRecognitionPostProcessor
from services.content_analysis import ContentType
from services.audio_service import (
    generate_audio, 
    initialize_speech_recognition, 
    recognize_speech_from_file,
    VOSK_AVAILABLE,
    GTTS_AVAILABLE
)

class SpeechRecognitionService:
    """Streamlined speech recognition service"""
    
    def __init__(self, model_path=None, temp_dir=None):
        """Initialize the speech recognition service"""
        self.model_path = model_path or self._find_vosk_model()
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.vosk_model = None
        self.vosk_recognizer = None
        self.post_processor = SpeechRecognitionPostProcessor()
        
        # Initialize Vosk if available
        if VOSK_AVAILABLE and self.model_path:
            self.vosk_model, self.vosk_recognizer = initialize_speech_recognition(self.model_path)
            if self.vosk_model and self.vosk_recognizer:
                print(f"✅ Speech recognition initialized with model: {self.model_path}")
            else:
                print("⚠️ Failed to initialize speech recognition")
        else:
            print("⚠️ Vosk not available or model not found")
    
    def _find_vosk_model(self) -> Optional[str]:
        """Find available Vosk model in the models directory"""
        models_dir = "models"
        if not os.path.exists(models_dir):
            return None
        
        for item in os.listdir(models_dir):
            item_path = os.path.join(models_dir, item)
            if os.path.isdir(item_path) and "vosk-model" in item.lower():
                if self._is_valid_vosk_model(item_path):
                    return item_path
        return None
    
    def _is_valid_vosk_model(self, model_path: str) -> bool:
        """Check if a directory contains a valid Vosk model"""
        required_files = ["am", "graph", "conf"]
        return all(os.path.exists(os.path.join(model_path, f)) for f in required_files)
    
    def process_text_to_speech_to_text_with_postprocessing(self, 
                                                         text: str, 
                                                         content_type: ContentType = None,
                                                         voice_settings: Dict = None,
                                                         cleanup_audio: bool = True) -> SpeechRecognitionResult:
        """
        Complete text-to-speech-to-text recognition workflow with post-processing
        """
        # First run the standard process
        result = self.process_text_to_speech_to_text(text, voice_settings, cleanup_audio)
        
        if result.success and result.recognized_text:
            # Apply post-processing to improve accuracy
            post_processed_text = self.post_processor.post_process_recognized_text(
                result.recognized_text,
                content_type,
                text
            )

            # Recalculate metrics with post-processed text
            if post_processed_text != result.recognized_text:
                # Only show post-processing changes if significant
                if len(post_processed_text) > 50:  # Only for longer texts
                    print(f"📝 Post-processing applied: '{result.recognized_text[:50]}...' → '{post_processed_text[:50]}...'")
                
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
                                                       content_type: ContentType = None) -> SpeechRecognitionResult:
        """
        Recognize speech from existing audio file with post-processing
        This avoids redundant TTS generation when we already have the audio
        """
        try:
            start_time = time.time()

            # Step 1: Recognize speech from existing audio
            recognized_text = self._recognize_speech_from_audio(audio_file)

            # Step 2: Apply post-processing
            if recognized_text:
                post_processed_text = self.post_processor.post_process_recognized_text(
                    recognized_text,
                    content_type,
                    original_text
                )

                if post_processed_text != recognized_text:
                    # Only show post-processing changes if significant
                    if len(post_processed_text) > 50:  # Only for longer texts
                        print(f"📝 Post-processing applied: '{recognized_text[:50]}...' → '{post_processed_text[:50]}...'")

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
        
        if not GTTS_AVAILABLE:
            return self._create_error_result(text, "gTTS not available", start_time)
        
        if not self.vosk_model or not self.vosk_recognizer:
            return self._create_error_result(text, "Vosk speech recognition not available", start_time)
        
        try:
            # Step 1: Generate audio from text using gTTS
            audio_file = self._generate_audio_file(text, voice_settings)
            if not audio_file:
                return self._create_error_result(text, "Failed to generate audio", start_time)
            
            # Step 2: Recognize speech from audio using Vosk
            recognized_text = self._recognize_speech_from_audio(audio_file)
            
            # Step 3: Compare original and recognized text
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
                except:
                    pass  # Ignore cleanup errors
            
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
        """Generate audio file from text using gTTS"""
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
                print(f"✅ Audio generated: {audio_file}")
                return audio_file
            else:
                print("❌ Failed to generate audio")
                return None
                
        except Exception as e:
            print(f"❌ Error generating audio: {e}")
            return None
    
    def _recognize_speech_from_audio(self, audio_file: str) -> str:
        """Recognize speech from audio file using Vosk"""
        try:
            if not os.path.exists(audio_file):
                print(f"❌ Audio file not found: {audio_file}")
                return ""
            
            recognized_text = recognize_speech_from_file(
                audio_file,
                self.vosk_model,
                self.vosk_recognizer
            )
            
            print(f"✅ Speech recognized: '{recognized_text}'")
            return recognized_text.strip()
            
        except Exception as e:
            print(f"❌ Error recognizing speech: {e}")
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
            print(f"❌ Error comparing texts: {e}")
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
