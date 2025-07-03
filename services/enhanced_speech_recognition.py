"""
Enhanced Speech Recognition Service with Whisper-Timestamped Integration
Combines traditional Vosk-based validation with whisper-timestamped for improved accuracy
"""
import os
import time
from typing import Dict, Optional, List
from dataclasses import dataclass

from services.speech_recognition_core import SpeechRecognitionService
from services.speech_recognition_models import SpeechRecognitionResult

from config import WHISPER_TIMESTAMPED_CONFIG

# Import whisper-timestamped service
try:
    from services.whisper_timestamped_service import WhisperTimestampedService
    WHISPER_SERVICE_AVAILABLE = True
except ImportError:
    WHISPER_SERVICE_AVAILABLE = False

@dataclass
class EnhancedSpeechResult:
    """Enhanced speech recognition result with multiple validation methods"""
    vosk_result: SpeechRecognitionResult
    whisper_result: Optional[SpeechRecognitionResult]
    final_text: str
    confidence_score: float
    method_used: str  # "vosk", "whisper", "hybrid"
    processing_time: float
    success: bool

class EnhancedSpeechRecognitionService:
    """Enhanced speech recognition service with whisper-timestamped integration"""
    
    def __init__(self, model_path=None, temp_dir=None):
        """Initialize enhanced speech recognition service"""
        # Initialize traditional Vosk service
        self.vosk_service = SpeechRecognitionService(model_path, temp_dir)
        
        # Use shared whisper-timestamped service
        from services.whisper_service_manager import get_whisper_service
        self.whisper_service = get_whisper_service()
        self.whisper_config = WHISPER_TIMESTAMPED_CONFIG

        # Silent initialization for speed optimization (speech recognition validation disabled)
        if not self.whisper_service:
            print("⚠️ Whisper-timestamped service not available")
    
    def process_text_with_enhanced_validation(self,
                                            text: str,
                                            voice_settings: Dict = None,
                                            cleanup_audio: bool = True) -> EnhancedSpeechResult:
        """
        Process text with enhanced validation using both Vosk and whisper-timestamped

        Args:
            text: Original text to validate
            voice_settings: Voice generation settings
            cleanup_audio: Whether to cleanup audio files

        Returns:
            EnhancedSpeechResult with validation from multiple methods
        """
        start_time = time.time()
        
        # Step 1: Run traditional Vosk validation
        vosk_result = self.vosk_service.process_text_to_speech_to_text_with_postprocessing(
            text, None, voice_settings, cleanup_audio=False  # Keep audio for whisper
        )
        
        whisper_result = None
        final_text = text
        confidence_score = 0.0
        method_used = "none"
        
        if vosk_result.success and vosk_result.audio_file_path:
            # Step 2: Run whisper-timestamped validation if available
            if self.whisper_service:
                whisper_result = self._validate_with_whisper(
                    vosk_result.audio_file_path, text
                )
            
            # Step 3: Determine best result
            final_text, confidence_score, method_used = self._select_best_result(
                text, vosk_result, whisper_result
            )
            
            # Step 4: Cleanup audio if requested
            if cleanup_audio and os.path.exists(vosk_result.audio_file_path):
                try:
                    os.remove(vosk_result.audio_file_path)
                except Exception as e:
                    print(f"Warning: Could not cleanup audio file: {e}")
        
        return EnhancedSpeechResult(
            vosk_result=vosk_result,
            whisper_result=whisper_result,
            final_text=final_text,
            confidence_score=confidence_score,
            method_used=method_used,
            processing_time=time.time() - start_time,
            success=vosk_result.success
        )
    
    def validate_audio_with_enhanced_methods(self,
                                           audio_file: str,
                                           original_text: str) -> EnhancedSpeechResult:
        """
        Validate existing audio file using both Vosk and whisper-timestamped

        Args:
            audio_file: Path to audio file
            original_text: Original text for comparison

        Returns:
            EnhancedSpeechResult with validation from multiple methods
        """
        start_time = time.time()
        
        # Step 1: Run traditional Vosk validation
        vosk_result = self.vosk_service.recognize_speech_from_audio_with_postprocessing(
            audio_file, original_text, None
        )

        # Step 2: Run whisper-timestamped validation if available
        whisper_result = None
        if self.whisper_service:
            whisper_result = self._validate_with_whisper(audio_file, original_text)
        
        # Step 3: Determine best result
        final_text, confidence_score, method_used = self._select_best_result(
            original_text, vosk_result, whisper_result
        )
        
        return EnhancedSpeechResult(
            vosk_result=vosk_result,
            whisper_result=whisper_result,
            final_text=final_text,
            confidence_score=confidence_score,
            method_used=method_used,
            processing_time=time.time() - start_time,
            success=vosk_result.success or (whisper_result and whisper_result.success)
        )
    
    def _validate_with_whisper(self,
                              audio_file: str,
                              original_text: str) -> Optional[SpeechRecognitionResult]:
        """Validate audio using whisper-timestamped"""
        try:
            # Get language setting
            language = self.whisper_config.get("default_language", "en")
            use_vad = self.whisper_config.get("use_vad", True)
            
            # Run whisper analysis
            result = self.whisper_service.analyze_audio_with_timestamps(
                audio_file=audio_file,
                language=language,
                use_vad=use_vad
            )
            
            if not result.success:
                return None
            
            # Convert whisper result to SpeechRecognitionResult format
            # Calculate similarity with original text
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, original_text.lower(), result.text.lower()).ratio()
            
            # Get confidence score
            confidence = self.whisper_service.get_confidence_score(result)
            
            return SpeechRecognitionResult(
                original_text=original_text,
                recognized_text=result.text,
                similarity_score=similarity,
                word_accuracy=confidence,  # Use whisper confidence as word accuracy
                character_accuracy=similarity,
                differences=[],  # Could be enhanced to show detailed differences
                processing_time=result.processing_time,
                audio_file_path=audio_file,
                success=True
            )
            
        except Exception as e:
            print(f"⚠️ Whisper validation failed: {e}")
            return None
    
    def _select_best_result(self, 
                           original_text: str,
                           vosk_result: SpeechRecognitionResult,
                           whisper_result: Optional[SpeechRecognitionResult]) -> tuple:
        """
        Select the best result from Vosk and whisper-timestamped
        
        Returns:
            tuple: (final_text, confidence_score, method_used)
        """
        # If only Vosk succeeded
        if vosk_result.success and not whisper_result:
            return (
                vosk_result.recognized_text,
                vosk_result.similarity_score,
                "vosk"
            )
        
        # If only whisper succeeded
        if whisper_result and whisper_result.success and not vosk_result.success:
            return (
                whisper_result.recognized_text,
                whisper_result.word_accuracy,
                "whisper"
            )
        
        # If both succeeded, choose based on confidence and configuration
        if vosk_result.success and whisper_result and whisper_result.success:
            whisper_confidence = whisper_result.word_accuracy
            vosk_confidence = vosk_result.similarity_score
            
            # Check whisper confidence threshold
            min_whisper_confidence = self.whisper_config.get("min_confidence_threshold", 0.7)
            
            # Prefer whisper if it meets confidence threshold and is better than Vosk
            if (whisper_confidence >= min_whisper_confidence and 
                whisper_confidence > vosk_confidence):
                return (
                    whisper_result.recognized_text,
                    whisper_confidence,
                    "whisper"
                )
            else:
                return (
                    vosk_result.recognized_text,
                    vosk_confidence,
                    "vosk"
                )
        
        # Fallback to original text
        return (original_text, 0.0, "fallback")
    
    def is_available(self) -> bool:
        """Check if enhanced speech recognition is available"""
        return self.vosk_service.is_available()
    
    def get_service_status(self) -> Dict:
        """Get status of all available services with performance metrics"""
        status = {
            "vosk_available": self.vosk_service.is_available(),
            "whisper_available": self.whisper_service is not None and self.whisper_service.is_service_available(),
            "enhanced_mode": self.whisper_service is not None
        }

        # Add whisper cache statistics if available
        if self.whisper_service:
            try:
                cache_stats = self.whisper_service.get_cache_stats()
                status["whisper_cache"] = cache_stats
            except AttributeError:
                pass

        return status

    def optimize_performance(self):
        """Optimize performance by clearing caches and resetting services"""
        if self.whisper_service:
            self.whisper_service.clear_cache()

        # Could add Vosk optimization here if needed
        print("🔧 Enhanced speech recognition performance optimized")

    def get_performance_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []

        if self.whisper_service:
            cache_stats = self.whisper_service.get_cache_stats()

            if cache_stats["hit_rate_percent"] < 20:
                recommendations.append("Consider processing similar content to improve cache efficiency")

            if cache_stats["cache_size"] >= cache_stats["max_cache_size"]:
                recommendations.append("Cache is full - consider increasing cache size for better performance")

        if not self.whisper_service:
            recommendations.append("Install whisper-timestamped for enhanced accuracy and performance")

        return recommendations
