"""
Speech Recognition Cache System
Eliminates duplicate speech recognition processing by caching results
"""
import hashlib
import os
import time
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from utils.logging_utils import clean_log_message


@dataclass
class CachedSpeechResult:
    """Cached speech recognition result - Whisper-timestamped only"""
    audio_file: str
    original_text: str
    whisper_segments: list = field(default_factory=list)
    combined_segments: list = field(default_factory=list)
    confidence_score: float = 0.0
    method_used: str = "whisper"
    processing_time: float = 0.0
    timestamp: float = field(default_factory=time.time)
    file_hash: str = ""


class SpeechRecognitionCache:
    """Centralized cache for speech recognition results"""
    
    def __init__(self, max_cache_size: int = 100):
        self.cache: Dict[str, CachedSpeechResult] = {}
        self.max_cache_size = max_cache_size
        self.access_times: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.hit_count = 0
        self.miss_count = 0
        
        from utils.logging_utils import log_cache_operations
        log_cache_operations("Speech recognition cache initialized")
    
    def _get_cache_key(self, audio_file: str, original_text: str) -> str:
        """Generate cache key from audio file and text"""
        try:
            # Get file hash for audio file
            file_hash = self._get_file_hash(audio_file)
            
            # Create key from file hash and text hash
            text_hash = hashlib.md5(original_text.encode()).hexdigest()[:8]
            return f"{file_hash}_{text_hash}"
            
        except Exception as e:
            print(clean_log_message(f"❌ Error generating cache key: {e}"))
            # Fallback to simple hash
            combined = f"{audio_file}_{original_text}"
            return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    def _get_file_hash(self, file_path: str) -> str:
        """Get hash of audio file for cache key"""
        try:
            if not os.path.exists(file_path):
                return "missing_file"
                
            # Use file size and modification time for quick hash
            stat = os.stat(file_path)
            file_info = f"{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(file_info.encode()).hexdigest()[:8]
            
        except Exception:
            return "unknown_file"
    
    def get_cached_result(self, audio_file: str, original_text: str) -> Optional[CachedSpeechResult]:
        """Get cached speech recognition result"""
        cache_key = self._get_cache_key(audio_file, original_text)
        
        with self.lock:
            if cache_key in self.cache:
                # Update access time
                self.access_times[cache_key] = time.time()
                self.hit_count += 1
                
                result = self.cache[cache_key]
                from utils.logging_utils import log_cache_operations
                log_cache_operations(f"Cache hit for speech recognition ({result.method_used})")
                return result
            else:
                self.miss_count += 1
                return None
    
    def cache_result(self, audio_file: str, original_text: str,
                    whisper_segments: list = None, combined_segments: list = None,
                    confidence_score: float = 0.0, method_used: str = "whisper",
                    processing_time: float = 0.0) -> None:
        """Cache speech recognition result - Whisper-timestamped only"""
        cache_key = self._get_cache_key(audio_file, original_text)

        with self.lock:
            # Create cached result
            result = CachedSpeechResult(
                audio_file=audio_file,
                original_text=original_text,
                whisper_segments=whisper_segments or [],
                combined_segments=combined_segments or whisper_segments or [],
                confidence_score=confidence_score,
                method_used=method_used,
                processing_time=processing_time,
                file_hash=self._get_file_hash(audio_file)
            )
            
            # Add to cache
            self.cache[cache_key] = result
            self.access_times[cache_key] = time.time()
            
            # Cleanup if cache is too large
            self._cleanup_cache()
            
            from utils.logging_utils import log_cache_operations
            log_cache_operations(f"Cached speech recognition result ({method_used})")
    
    def _cleanup_cache(self):
        """Remove old entries if cache is too large"""
        if len(self.cache) <= self.max_cache_size:
            return
            
        # Remove oldest entries
        sorted_keys = sorted(self.access_times.keys(), key=lambda k: self.access_times[k])
        keys_to_remove = sorted_keys[:len(self.cache) - self.max_cache_size + 10]  # Remove extra for buffer
        
        for key in keys_to_remove:
            if key in self.cache:
                del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
                
        print(clean_log_message(f"🧹 Cleaned up {len(keys_to_remove)} old cache entries"))
    
    def clear_cache(self):
        """Clear all cached results"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.hit_count = 0
            self.miss_count = 0
            
        print(clean_log_message("🧹 Speech recognition cache cleared"))
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'cache_size': len(self.cache),
                'max_size': self.max_cache_size,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }
    
    def print_cache_stats(self):
        """Print cache statistics"""
        stats = self.get_cache_stats()
        
        print(clean_log_message("📊 Speech Recognition Cache Statistics:"))
        print(f"   Cache size: {stats['cache_size']}/{stats['max_size']}")
        print(f"   Hit rate: {stats['hit_rate']:.1f}% ({stats['hit_count']}/{stats['total_requests']})")
        print(f"   Requests: {stats['total_requests']} (hits: {stats['hit_count']}, misses: {stats['miss_count']})")


# Global cache instance
_speech_cache = None
_cache_lock = threading.Lock()

def get_speech_recognition_cache() -> SpeechRecognitionCache:
    """Get the global speech recognition cache instance"""
    global _speech_cache
    if _speech_cache is None:
        with _cache_lock:
            if _speech_cache is None:
                _speech_cache = SpeechRecognitionCache()
    return _speech_cache
