"""
Optimized Audio Service - TTS-to-Text Workflow for Subtitle Synchronization
Clean implementation: Text → Edge TTS/Kokoro TTS → Speech Recognition Analysis → Synchronized Subtitles
"""
import os
import tempfile
import time
from typing import Optional, Dict, Any, Tuple

# Import logging utilities
from utils.logging_utils import clean_log_message

# Import TTS manager
from services.tts_providers import get_tts_manager

# Import speech recognition for timing analysis
try:
    from services.speech_recognition_core import SpeechRecognitionService
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

try:
    from services.whisper_timestamped_service import WhisperTimestampedService
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class AudioTimingResult:
    """Result from TTS-to-Text timing analysis"""
    def __init__(self, success: bool, audio_file: str, timing_data: Optional[Dict] = None, error: str = "",
                 original_text: str = "", processed_text: str = ""):
        self.success = success
        self.audio_file = audio_file
        self.timing_data = timing_data or {}
        self.error = error
        self.original_text = original_text  # Text user typed
        self.processed_text = processed_text  # Text sent to TTS
        self.vosk_segments = timing_data.get('vosk_segments', []) if timing_data else []
        self.whisper_segments = timing_data.get('whisper_segments', []) if timing_data else []
        self.processing_time = timing_data.get('processing_time', 0.0) if timing_data else 0.0


def generate_audio_with_timing_analysis(text: str, output_file: str, voice_actor: str = "Guy",
                                       speed: float = 1.0, emotion: str = "neutral",
                                       language: str = 'en') -> AudioTimingResult:
    """
    Generate audio with Edge TTS or Kokoro TTS and analyze timing for subtitle synchronization

    Args:
        text: Text to convert to speech (original text from user)
        output_file: Path for output audio file
        voice_actor: Voice actor preference (Guy, Connor, Aria, Michael, Adam, Heart)
        speed: Speech speed multiplier
        emotion: Emotional tone
        language: Language code


    Returns:
        AudioTimingResult with timing data for subtitle synchronization
    """
    start_time = time.time()

    try:
        # Step 1: Normalize text for natural speech (this is the key fix!)
        from utils.text_processing import normalize_text_for_natural_speech
        processed_text = normalize_text_for_natural_speech(text)

        # Store both original and processed text
        original_text = text

        # Step 2: Generate audio with Edge TTS or Kokoro TTS
        # Get TTS manager
        tts_manager = get_tts_manager()
        if not tts_manager:
            return AudioTimingResult(False, "", error="TTS manager not available",
                                   original_text=original_text, processed_text=processed_text)

        # Generate audio using processed text
        tts_params = {
            'language': language,
            'emotion': emotion,
            'speed': speed,
            'voice_actor': voice_actor
        }

        success = tts_manager.generate_speech(processed_text, output_file, **tts_params)
        if not success:
            return AudioTimingResult(False, output_file, error="TTS generation failed",
                                   original_text=original_text, processed_text=processed_text)

        # Step 3: Analyze generated audio for timing synchronization (use processed text for analysis)
        timing_data = _analyze_audio_timing(output_file, processed_text)

        processing_time = time.time() - start_time
        timing_data['processing_time'] = processing_time

        return AudioTimingResult(True, output_file, timing_data,
                               original_text=original_text, processed_text=processed_text)

    except Exception as e:
        error_msg = f"Audio generation with timing analysis failed: {e}"
        print(clean_log_message(f"❌ {error_msg}"))
        return AudioTimingResult(False, output_file, error=error_msg,
                               original_text=text, processed_text="")


def _analyze_audio_timing(audio_file: str, original_text: str) -> Dict[str, Any]:
    """
    Analyze generated audio using Vosk + Whisper for subtitle timing synchronization

    Args:
        audio_file: Path to generated audio file
        original_text: Original text for reference


    Returns:
        Dictionary with timing analysis results
    """
    timing_data = {
        'vosk_segments': [],
        'whisper_segments': [],
        'combined_segments': [],
        'confidence_score': 0.0,
        'method_used': 'none'
    }
    
    try:
        # Analyze with Vosk for fast sentence-level timing
        if VOSK_AVAILABLE:
            vosk_result = _analyze_with_vosk(audio_file, original_text)
            if vosk_result:
                timing_data['vosk_segments'] = vosk_result
                timing_data['method_used'] = 'vosk'

        # Analyze with Whisper for precise timing
        if WHISPER_AVAILABLE:
            whisper_result = _analyze_with_whisper(audio_file)
            if whisper_result:
                timing_data['whisper_segments'] = whisper_result
                timing_data['method_used'] = 'whisper' if not timing_data['vosk_segments'] else 'vosk+whisper'

        # Combine results for optimal timing
        combined_segments = _combine_timing_results(timing_data['vosk_segments'], timing_data['whisper_segments'])
        timing_data['combined_segments'] = combined_segments
        timing_data['confidence_score'] = _calculate_confidence_score(combined_segments)
        
        return timing_data
        
    except Exception as e:
        print(f"⚠️ Audio timing analysis error: {e}")
        return timing_data


def _analyze_with_vosk(audio_file: str, original_text: str) -> list:
    """Analyze audio with Vosk for sentence-level timing"""
    try:
        vosk_service = SpeechRecognitionService()

        if not vosk_service.vosk_model:
            return []

        # Get sentence-level segments from Vosk
        result = vosk_service.recognize_speech_from_audio_with_postprocessing(
            audio_file, original_text, None
        )

        if result and result.success:
            # Get actual audio duration for proper timing
            from utils.helpers import get_media_duration_safe
            audio_duration = get_media_duration_safe(audio_file)

            # Debug logging for timing verification
            print(f"[VOSK TIMING] Audio file: {os.path.basename(audio_file)} | Duration: {audio_duration:.2f}s")

            # Vosk doesn't provide detailed segments, create a single segment from the full result
            segments = []
            if result.recognized_text:
                segments.append({
                    'text': result.recognized_text,
                    'start': 0.0,
                    'end': audio_duration,  # Use actual audio duration instead of placeholder
                    'confidence': result.similarity_score
                })
                print(f"[VOSK TIMING] Created segment: 0.0-{audio_duration:.2f}s | Text: '{result.recognized_text[:50]}...'")
            return segments

        return []

    except Exception as e:
        print(f"⚠️ Vosk analysis error: {e}")
        return []


def _analyze_with_whisper(audio_file: str) -> list:
    """Analyze audio with Whisper for precise timing"""
    try:
        whisper_service = WhisperTimestampedService()
        if not whisper_service.is_available:
            print(f"[DEBUG] Whisper service not available - falling back to Vosk only")
            return []

        # Analyze with Whisper
        result = whisper_service.analyze_audio_with_timestamps(
            audio_file=audio_file,
            language="en",
            use_vad=True
        )

        if result.success and result.segments:
            # Convert to timing segments
            segments = []
            for segment in result.segments:
                segment_data = {
                    'text': segment.text,
                    'start': segment.start,
                    'end': segment.end,
                    'confidence': segment.confidence
                }
                segments.append(segment_data)

                # Add word-level data to segment if available
                if hasattr(segment, 'words') and segment.words:
                    segment_data['words'] = segment.words

            return segments

        return []

    except Exception as e:
        print(f"⚠️ Whisper analysis error: {e}")
        return []


def _combine_timing_results(vosk_segments: list, whisper_segments: list) -> list:
    """Combine Vosk and Whisper timing results for optimal synchronization"""
    if not vosk_segments and not whisper_segments:
        return []
    
    # Prefer Whisper for precision, fallback to Vosk for speed
    if whisper_segments:
        return whisper_segments
    elif vosk_segments:
        return vosk_segments
    
    return []


def _calculate_confidence_score(segments: list) -> float:
    """Calculate overall confidence score from timing segments"""
    if not segments:
        return 0.0
    
    total_confidence = sum(segment.get('confidence', 0.0) for segment in segments)
    return total_confidence / len(segments)


# Legacy function for backward compatibility
def generate_audio(text: str, output_file: str, voice_actor: str = "Guy",
                  speed: float = 1.0, emotion: str = "neutral", language: str = 'en',
                  content_analysis=None, title: str = "") -> bool:
    """
    Legacy function - generates audio without timing analysis
    Use generate_audio_with_timing_analysis for subtitle synchronization
    """
    result = generate_audio_with_timing_analysis(
        text, output_file, voice_actor, speed, emotion, language
    )
    return result.success
