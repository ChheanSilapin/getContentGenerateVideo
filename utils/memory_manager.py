"""
Memory Management Utilities
Optimizes memory usage and cleanup for video generation
"""
import gc
import os
import tempfile
import threading
import time
from contextlib import contextmanager
from typing import List, Optional, Any
from utils.logging_utils import clean_log_message


class MemoryManager:
    """Centralized memory management for video generation"""
    
    def __init__(self):
        self.temp_files: List[str] = []
        self.moviepy_clips: List[Any] = []
        self.lock = threading.Lock()
        self.cleanup_on_exit = True
        
    def register_temp_file(self, file_path: str):
        """Register a temporary file for cleanup"""
        with self.lock:
            if file_path and file_path not in self.temp_files:
                self.temp_files.append(file_path)
    
    def register_moviepy_clip(self, clip: Any):
        """Register a MoviePy clip for proper disposal"""
        with self.lock:
            if clip and clip not in self.moviepy_clips:
                self.moviepy_clips.append(clip)
    
    def cleanup_temp_files(self, keep_final_output: bool = True, final_output_path: str = None):
        """Clean up temporary files"""
        with self.lock:
            cleaned_count = 0
            
            for file_path in self.temp_files[:]:  # Copy list to avoid modification during iteration
                try:
                    if keep_final_output and final_output_path and file_path == final_output_path:
                        continue  # Keep the final output file
                        
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        cleaned_count += 1
                        
                    self.temp_files.remove(file_path)
                    
                except Exception as e:
                    print(clean_log_message(f"⚠️ Failed to remove temp file {file_path}: {e}"))
            
            if cleaned_count > 0:
                print(clean_log_message(f"🧹 Cleaned up {cleaned_count} temporary files"))
    
    def cleanup_moviepy_clips(self):
        """Properly dispose of MoviePy clips"""
        with self.lock:
            disposed_count = 0
            
            for clip in self.moviepy_clips[:]:  # Copy list to avoid modification during iteration
                try:
                    if hasattr(clip, 'close'):
                        clip.close()
                        disposed_count += 1
                    elif hasattr(clip, 'reader') and hasattr(clip.reader, 'close'):
                        clip.reader.close()
                        disposed_count += 1
                        
                    self.moviepy_clips.remove(clip)
                    
                except Exception as e:
                    print(clean_log_message(f"⚠️ Failed to dispose MoviePy clip: {e}"))
            
            if disposed_count > 0:
                print(clean_log_message(f"🧹 Disposed {disposed_count} MoviePy clips"))
    
    def force_garbage_collection(self):
        """Force garbage collection to free memory"""
        collected = gc.collect()
        if collected > 0:
            print(clean_log_message(f"🗑️ Garbage collected {collected} objects"))
        return collected
    
    def cleanup_all(self, keep_final_output: bool = True, final_output_path: str = None):
        """Perform complete cleanup"""
        print(clean_log_message("🧹 Starting memory cleanup..."))
        
        # Clean up MoviePy clips first
        self.cleanup_moviepy_clips()
        
        # Clean up temporary files
        self.cleanup_temp_files(keep_final_output, final_output_path)
        
        # Force garbage collection
        self.force_garbage_collection()
        
        print(clean_log_message("✅ Memory cleanup completed"))
    
    def get_temp_file_count(self) -> int:
        """Get number of registered temporary files"""
        with self.lock:
            return len(self.temp_files)
    
    def get_clip_count(self) -> int:
        """Get number of registered MoviePy clips"""
        with self.lock:
            return len(self.moviepy_clips)


# Global memory manager instance
_memory_manager = None
_manager_lock = threading.Lock()

def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        with _manager_lock:
            if _memory_manager is None:
                _memory_manager = MemoryManager()
    return _memory_manager


@contextmanager
def managed_temp_file(suffix: str = "", prefix: str = "temp_", dir: str = None, delete: bool = False):
    """Context manager for temporary files with automatic cleanup"""
    temp_file = None
    try:
        # Create temporary file
        fd, temp_file = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
        os.close(fd)  # Close file descriptor, keep the file
        
        # Register for cleanup
        memory_manager = get_memory_manager()
        memory_manager.register_temp_file(temp_file)
        
        yield temp_file
        
    except Exception as e:
        print(clean_log_message(f"❌ Error with managed temp file: {e}"))
        raise
    finally:
        # Cleanup if requested
        if delete and temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                print(clean_log_message(f"⚠️ Failed to delete temp file {temp_file}: {e}"))


@contextmanager
def managed_moviepy_clip(clip_factory, *args, **kwargs):
    """Context manager for MoviePy clips with automatic disposal"""
    clip = None
    try:
        # Create clip
        clip = clip_factory(*args, **kwargs)
        
        # Register for cleanup
        memory_manager = get_memory_manager()
        memory_manager.register_moviepy_clip(clip)
        
        yield clip
        
    except Exception as e:
        print(clean_log_message(f"❌ Error with managed MoviePy clip: {e}"))
        raise
    finally:
        # Dispose clip
        if clip:
            try:
                if hasattr(clip, 'close'):
                    clip.close()
                elif hasattr(clip, 'reader') and hasattr(clip.reader, 'close'):
                    clip.reader.close()
            except Exception as e:
                print(clean_log_message(f"⚠️ Failed to dispose clip: {e}"))


@contextmanager
def memory_optimized_operation(operation_name: str = "operation"):
    """Context manager for memory-optimized operations"""
    memory_manager = get_memory_manager()
    
    print(clean_log_message(f"🔧 Starting {operation_name}..."))
    start_time = time.time()
    
    try:
        yield memory_manager
        
    except Exception as e:
        print(clean_log_message(f"❌ Error in {operation_name}: {e}"))
        raise
    finally:
        # Force garbage collection after operation
        collected = memory_manager.force_garbage_collection()
        duration = time.time() - start_time
        
        print(clean_log_message(f"✅ {operation_name} completed ({duration:.2f}s, {collected} objects collected)"))


def cleanup_on_exit():
    """Cleanup function to be called on application exit"""
    memory_manager = get_memory_manager()
    if memory_manager.cleanup_on_exit:
        memory_manager.cleanup_all(keep_final_output=True)


# Register cleanup on exit
import atexit
atexit.register(cleanup_on_exit)
