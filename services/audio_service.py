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

# Speech recognition no longer needed - using only Whisper-timestamped

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
        # Step 1: Use raw text directly - no preprocessing needed for modern TTS
        # Edge TTS and Kokoro TTS can handle complex formatting naturally
        original_text = text

        # Step 2: Generate audio with Edge TTS or Kokoro TTS using raw text
        # Get TTS manager
        tts_manager = get_tts_manager()
        if not tts_manager:
            return AudioTimingResult(False, "", error="TTS manager not available",
                                   original_text=original_text, processed_text=original_text)

        # Generate audio using raw user text (no preprocessing)
        tts_params = {
            'language': language,
            'emotion': emotion,
            'speed': speed,
            'voice_actor': voice_actor
        }

        success = tts_manager.generate_speech(original_text, output_file, **tts_params)
        if not success:
            return AudioTimingResult(False, output_file, error="TTS generation failed",
                                   original_text=original_text, processed_text=original_text)

        # Step 3: Analyze generated audio for timing synchronization (use original text for analysis)
        timing_data = _analyze_audio_timing(output_file, original_text)

        processing_time = time.time() - start_time
        timing_data['processing_time'] = processing_time

        return AudioTimingResult(True, output_file, timing_data,
                               original_text=original_text, processed_text=original_text)

    except Exception as e:
        error_msg = f"Audio generation with timing analysis failed: {e}"
        print(clean_log_message(f"❌ {error_msg}"))
        return AudioTimingResult(False, output_file, error=error_msg,
                               original_text=text, processed_text="")


def _analyze_audio_timing(audio_file: str, original_text: str) -> Dict[str, Any]:
    """
    Analyze generated audio using cached speech recognition results

    Args:
        audio_file: Path to generated audio file
        original_text: Original text for reference

    Returns:
        Dictionary with timing analysis results
    """
    from utils.speech_recognition_cache import get_speech_recognition_cache

    # Check cache first
    cache = get_speech_recognition_cache()
    cached_result = cache.get_cached_result(audio_file, original_text)

    if cached_result:
        return {
            'whisper_segments': cached_result.whisper_segments,
            'combined_segments': cached_result.combined_segments,
            'confidence_score': cached_result.confidence_score,
            'method_used': cached_result.method_used
        }

    # Perform analysis if not cached
    timing_data = {
        'whisper_segments': [],
        'combined_segments': [],
        'confidence_score': 0.0,
        'method_used': 'none'
    }

    start_time = time.time()

    try:
        # SIMPLIFIED: Use ONLY Whisper-timestamped for best accuracy and consistency
        if WHISPER_AVAILABLE:
            whisper_result = _analyze_with_whisper(audio_file)
            if whisper_result:
                timing_data['whisper_segments'] = whisper_result
                timing_data['method_used'] = 'whisper'
                timing_data['confidence_score'] = _calculate_confidence_score(whisper_result)
            else:
                print(f"⚠️ Whisper-timestamped analysis failed")
        else:
            print(f"⚠️ Whisper-timestamped not available - required for subtitle timing")

        # Cache the result
        processing_time = time.time() - start_time
        cache.cache_result(
            audio_file=audio_file,
            original_text=original_text,
            whisper_segments=timing_data['whisper_segments'],
            combined_segments=timing_data['whisper_segments'],  # Same as whisper now
            confidence_score=timing_data['confidence_score'],
            method_used=timing_data['method_used'],
            processing_time=processing_time
        )

        return timing_data

    except Exception as e:
        print(f"⚠️ Audio timing analysis error: {e}")
        return timing_data





def _analyze_with_whisper(audio_file: str) -> list:
    """Analyze audio with Whisper for precise timing"""
    try:
        whisper_service = WhisperTimestampedService()
        if not whisper_service.is_available:
            return []

        # Analyze with Whisper
        result = whisper_service.analyze_audio_with_timestamps(
            audio_file=audio_file,
            language="en",
            use_vad=True
        )

        if result.success and result.segments:
            # Convert to timing segments with word-level data
            segments = []
            for segment in result.segments:
                segment_data = {
                    'text': segment.text,
                    'start': segment.start,
                    'end': segment.end,
                    'confidence': segment.confidence
                }

                # Add word-level data to segment if available
                if hasattr(segment, 'words') and segment.words:
                    # Convert WhisperTimestamp objects to dict format
                    word_data = []
                    for word in segment.words:
                        word_data.append({
                            'word': word.text,
                            'start': word.start,
                            'end': word.end,
                            'conf': word.confidence
                        })
                    segment_data['words'] = word_data

                segments.append(segment_data)

            return segments

        return []

    except Exception as e:
        print(f"⚠️ Whisper analysis error: {e}")
        return []





def _calculate_confidence_score(segments: list) -> float:
    """Calculate overall confidence score from timing segments"""
    if not segments:
        return 0.0
    
    total_confidence = sum(segment.get('confidence', 0.0) for segment in segments)
    return total_confidence / len(segments)


def extract_timing_from_video(video_file: str, original_text: str) -> AudioTimingResult:
    """
    Extract timing from video file with audio for perfect subtitle synchronization

    Args:
        video_file: Path to video file with audio
        original_text: Original text for reference

    Returns:
        AudioTimingResult with timing data extracted from video
    """
    try:
        # Extract audio from video to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name

        # Extract audio from video using FFmpeg
        from utils.helpers import get_ffmpeg_path
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path:
            return AudioTimingResult(False, "", error="FFmpeg not available")

        import subprocess
        cmd = [
            ffmpeg_path, '-i', video_file,
            '-vn', '-acodec', 'mp3', '-y', temp_audio_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=False)
        if result.returncode != 0:
            os.unlink(temp_audio_path)
            return AudioTimingResult(False, "", error="Failed to extract audio from video")

        # Analyze extracted audio for timing
        timing_data = _analyze_audio_timing(temp_audio_path, original_text)

        # Clean up temporary file
        os.unlink(temp_audio_path)

        return AudioTimingResult(True, video_file, timing_data,
                               original_text=original_text, processed_text=original_text)

    except Exception as e:
        error_msg = f"Video timing extraction failed: {e}"
        print(clean_log_message(f"❌ {error_msg}"))
        return AudioTimingResult(False, video_file, error=error_msg,
                               original_text=original_text, processed_text="")


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
