"""
Whisper-Timestamped Service for precise word-level timestamp extraction
Integrates with existing gTTS + speech recognition workflow for improved subtitle synchronization
"""
import os
import time
import tempfile
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Try to import whisper-timestamped
try:
    import whisper_timestamped as whisper
    WHISPER_TIMESTAMPED_AVAILABLE = True
except ImportError:
    WHISPER_TIMESTAMPED_AVAILABLE = False
    # Only show warning in development, not in bundled executable
    import sys
    if not getattr(sys, 'frozen', False):
        print("⚠️ whisper-timestamped not available. Enhanced subtitle timing disabled.")
        print("   Install with: pip install whisper-timestamped (for better voice synchronization)")

from services.content_analysis import ContentType
from utils.logging_utils import log_speech_recognition

@dataclass
class WhisperTimestamp:
    """Individual word timestamp from whisper-timestamped"""
    text: str
    start: float
    end: float
    confidence: float

@dataclass
class WhisperSegment:
    """Segment with word-level timestamps"""
    text: str
    start: float
    end: float
    words: List[WhisperTimestamp]
    confidence: float

@dataclass
class WhisperResult:
    """Complete whisper-timestamped analysis result"""
    text: str
    language: str
    segments: List[WhisperSegment]
    processing_time: float
    success: bool
    error_message: str = ""
    total_words: int = 0

class WhisperTimestampedService:
    """Service for precise word-level timestamp extraction using whisper-timestamped"""

    def __init__(self, model_name: str = "tiny", device: str = "auto"):
        """
        Initialize the whisper-timestamped service

        Args:
            model_name: Whisper model size ("tiny", "base", "small", "medium", "large")
            device: Device to use ("auto", "cpu", "cuda")
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.is_available = WHISPER_TIMESTAMPED_AVAILABLE

        # Debug logging for PyInstaller builds
        print(f"[DEBUG] WhisperTimestampedService init: WHISPER_TIMESTAMPED_AVAILABLE={WHISPER_TIMESTAMPED_AVAILABLE}")

        if not self.is_available:
            print(f"[DEBUG] Whisper not available - import failed")
            return

        # Performance optimization: result caching
        self._result_cache = {}
        self._cache_max_size = 50
        self._cache_hits = 0
        self._cache_misses = 0

        if self.is_available:
            print(f"[DEBUG] Attempting to load Whisper model...")
            self._load_model()
            print(f"[DEBUG] After model loading: is_available={self.is_available}, model={self.model is not None}")
        else:
            print(f"[DEBUG] Skipping model loading - whisper not available")
            log_speech_recognition(" Whisper-timestamped service unavailable")
    
    def _load_model(self):
        """Load the whisper model with enhanced error handling and fallbacks"""
        try:
            log_speech_recognition(f" Loading Whisper model ({self.model_name})...")

            # Check if running as PyInstaller executable and set model cache
            import sys
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller executable
                bundled_models_dir = os.path.join(sys._MEIPASS, 'whisper_models')
                if os.path.exists(bundled_models_dir):
                    # Set environment variable for whisper to use bundled models
                    os.environ['TORCH_HOME'] = bundled_models_dir
                    log_speech_recognition(f" Using bundled models from: {bundled_models_dir}")

            # Try loading with different device configurations
            devices_to_try = []
            if self.device == "auto":
                devices_to_try = ["cpu", "cuda"] if self._is_cuda_available() else ["cpu"]
            else:
                devices_to_try = [self.device]

            for device in devices_to_try:
                try:
                    self.model = whisper.load_model(self.model_name, device=device)
                    self.device = device  # Update device to what actually worked
                    log_speech_recognition(f" Whisper model loaded successfully on {device}")
                    return
                except Exception as device_error:
                    log_speech_recognition(f" Failed to load on {device}: {device_error}")
                    continue

            # If all devices failed, try with minimal configuration
            try:
                log_speech_recognition(" Trying minimal configuration...")
                self.model = whisper.load_model("tiny", device="cpu")
                self.model_name = "tiny"
                self.device = "cpu"
                log_speech_recognition(f" Whisper model loaded with minimal config (tiny/cpu)")
                return
            except Exception as minimal_error:
                log_speech_recognition(f" Minimal config also failed: {minimal_error}")

            # Complete failure
            raise Exception("All loading attempts failed")

        except Exception as e:
            log_speech_recognition(f" Failed to load Whisper model: {e}")
            log_speech_recognition(" Falling back to Vosk-only mode for speech recognition")
            self.model = None
            self.is_available = False

    def _is_cuda_available(self):
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def analyze_audio_with_timestamps(self, 
                                    audio_file: str, 
                                    language: str = "en",
                                    use_vad: bool = True,
                                    content_type: ContentType = None) -> WhisperResult:
        """
        Analyze audio file and extract word-level timestamps
        
        Args:
            audio_file: Path to audio file
            language: Language code (e.g., "en", "hi", "es")
            use_vad: Whether to use Voice Activity Detection
            content_type: Content type for optimization
            
        Returns:
            WhisperResult with word-level timestamps
        """
        start_time = time.time()
        
        if not self.is_available or not self.model:
            return WhisperResult(
                text="", language="", segments=[], processing_time=0,
                success=False, error_message="Whisper-timestamped not available"
            )
        
        if not os.path.exists(audio_file):
            return WhisperResult(
                text="", language="", segments=[], processing_time=0,
                success=False, error_message=f"Audio file not found: {audio_file}"
            )
        
        try:
            # Check cache first for performance optimization
            cache_key = self._get_audio_cache_key(audio_file, language, use_vad)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result

            log_speech_recognition(f" Analyzing audio with whisper-timestamped...")

            # Configure transcription options based on content type
            transcribe_options = self._get_transcription_options(language, use_vad, content_type)

            # Run whisper-timestamped transcription
            result = whisper.transcribe(self.model, audio_file, **transcribe_options)

            # Process results
            whisper_result = self._process_whisper_result(result, time.time() - start_time)

            # Cache the result for future use
            self._cache_result(cache_key, whisper_result)

            log_speech_recognition(f" Whisper analysis completed: {whisper_result.total_words} words, "
                                 f"{len(whisper_result.segments)} segments")

            return whisper_result
            
        except Exception as e:
            error_msg = f"Whisper-timestamped analysis failed: {e}"
            log_speech_recognition(f" {error_msg}")
            return WhisperResult(
                text="", language="", segments=[], processing_time=time.time() - start_time,
                success=False, error_message=error_msg
            )

    def _get_audio_cache_key(self, audio_file: str, language: str, use_vad: bool) -> str:
        """Generate cache key for audio analysis"""
        import hashlib

        # Get file size and modification time for cache key
        try:
            stat = os.stat(audio_file)
            file_info = f"{stat.st_size}_{stat.st_mtime}"
        except OSError:
            file_info = "unknown"

        # Create cache key from file info and settings
        cache_data = f"{file_info}_{language}_{use_vad}_{self.model_name}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> WhisperResult:
        """Get cached analysis result"""
        if cache_key in self._result_cache:
            self._cache_hits += 1
            log_speech_recognition(f"🚀 Using cached whisper result (hits: {self._cache_hits})")
            return self._result_cache[cache_key]

        self._cache_misses += 1
        return None

    def _cache_result(self, cache_key: str, result: WhisperResult):
        """Cache analysis result with size management"""
        if len(self._result_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._result_cache))
            del self._result_cache[oldest_key]

        self._result_cache[cache_key] = result
        log_speech_recognition(f"💾 Cached whisper result (cache size: {len(self._result_cache)})")

    def clear_cache(self):
        """Clear the result cache"""
        self._result_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        log_speech_recognition("🗑️ Whisper result cache cleared")

    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_size": len(self._result_cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 1),
            "max_cache_size": self._cache_max_size
        }
    
    def _get_transcription_options(self, language: str, use_vad: bool, content_type: ContentType) -> Dict:
        """Get optimized transcription options based on content type"""
        options = {
            "language": language,
            "vad": use_vad,
            "compute_word_confidence": True,
            "verbose": False,
            "temperature": 0.0,  # Deterministic output
        }
        
        # Content-type specific optimizations
        if content_type == ContentType.HISTORICAL:
            # Historical content may have proper nouns and dates
            options["initial_prompt"] = "This is historical content with names, dates, and places."
        elif content_type == ContentType.STORY_REVIEW:
            # Story reviews may have emotional language
            options["initial_prompt"] = "This is a story review with descriptive and emotional language."
        elif content_type == ContentType.DOCUMENTARY:
            # Documentary content is typically formal
            options["initial_prompt"] = "This is documentary content with factual information."
        
        return options
    
    def _process_whisper_result(self, result: Dict, processing_time: float) -> WhisperResult:
        """Process raw whisper result into structured format"""
        segments = []
        total_words = 0
        
        for segment_data in result.get('segments', []):
            words = []
            
            for word_data in segment_data.get('words', []):
                word = WhisperTimestamp(
                    text=word_data['text'].strip(),
                    start=word_data['start'],
                    end=word_data['end'],
                    confidence=word_data.get('confidence', 0.0)
                )
                words.append(word)
                total_words += 1
            
            segment = WhisperSegment(
                text=segment_data['text'].strip(),
                start=segment_data['start'],
                end=segment_data['end'],
                words=words,
                confidence=segment_data.get('confidence', 0.0)
            )
            segments.append(segment)
        
        return WhisperResult(
            text=result.get('text', '').strip(),
            language=result.get('language', 'unknown'),
            segments=segments,
            processing_time=processing_time,
            success=True,
            total_words=total_words
        )
    
    def extract_word_timings_for_subtitle_groups(self, 
                                               whisper_result: WhisperResult,
                                               word_groups: List[Dict]) -> List[Tuple[float, float]]:
        """
        Extract precise timings for subtitle word groups based on whisper analysis
        
        Args:
            whisper_result: Result from whisper-timestamped analysis
            word_groups: Subtitle word groups to time
            
        Returns:
            List of (start_time, end_time) tuples for each word group
        """
        if not whisper_result.success or not whisper_result.segments:
            return []
        
        # Flatten all word timestamps
        all_word_timestamps = []
        for segment in whisper_result.segments:
            all_word_timestamps.extend(segment.words)
        
        if not all_word_timestamps:
            return []
        
        # Map word groups to timestamps
        group_timings = []
        word_index = 0
        
        for group in word_groups:
            group_words = group['text'].split()
            group_word_count = len(group_words)
            
            if word_index >= len(all_word_timestamps):
                # Fallback: estimate timing for remaining groups
                if group_timings:
                    last_end = group_timings[-1][1]
                    estimated_duration = 2.0  # 2 seconds per group fallback
                    group_timings.append((last_end + 0.1, last_end + estimated_duration))
                else:
                    group_timings.append((0.0, 2.0))
                continue
            
            # Find start and end times for this group
            start_time = all_word_timestamps[word_index].start
            
            # Find end time by looking at the last word in this group
            end_word_index = min(word_index + group_word_count - 1, len(all_word_timestamps) - 1)
            end_time = all_word_timestamps[end_word_index].end
            
            # Ensure minimum duration and no overlaps
            min_duration = 0.8
            if end_time - start_time < min_duration:
                end_time = start_time + min_duration
            
            # Prevent overlap with previous group
            if group_timings and start_time < group_timings[-1][1]:
                start_time = group_timings[-1][1] + 0.05
                end_time = max(end_time, start_time + min_duration)
            
            group_timings.append((start_time, end_time))
            word_index += group_word_count
        
        log_speech_recognition(f" Mapped {len(group_timings)} subtitle groups to whisper timestamps")
        return group_timings
    
    def get_confidence_score(self, whisper_result: WhisperResult) -> float:
        """Calculate overall confidence score from whisper result"""
        if not whisper_result.success or not whisper_result.segments:
            return 0.0
        
        total_confidence = 0.0
        word_count = 0
        
        for segment in whisper_result.segments:
            for word in segment.words:
                total_confidence += word.confidence
                word_count += 1
        
        return total_confidence / word_count if word_count > 0 else 0.0
    
    def is_service_available(self) -> bool:
        """Check if the service is available and ready"""
        return self.is_available and self.model is not None
