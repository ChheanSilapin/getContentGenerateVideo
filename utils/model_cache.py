"""
Centralized Model Cache System
Singleton pattern for TTS and speech recognition models to eliminate loading overhead
"""
import threading
import time
import gc
from typing import Optional, Dict, Any
from utils.logging_utils import clean_log_message


class ModelCache:
    """Centralized cache for all AI models used in video generation"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return

        self._models = {}
        self._model_locks = {}
        self._load_times = {}
        self._access_counts = {}
        self._background_initialized = False
        self._initialized = True

        from utils.logging_utils import log_cache_operations
        log_cache_operations("Model cache system initialized")
    
    def get_kokoro_pipeline(self):
        """Get cached Kokoro TTS pipeline"""
        return self._get_or_load_model(
            'kokoro_pipeline',
            self._load_kokoro_pipeline,
            "Kokoro TTS Pipeline"
        )
    

    
    def get_whisper_model(self, model_name: str = "base"):
        """Get cached Whisper-timestamped model"""
        cache_key = f'whisper_model_{model_name}'
        return self._get_or_load_model(
            cache_key,
            lambda: self._load_whisper_model(model_name),
            f"Whisper Model ({model_name})"
        )

    def _initialize_background(self):
        """Initialize cache in background without loading models"""
        if self._background_initialized:
            return

        # Just mark as background initialized - models will load on-demand
        self._background_initialized = True

        from utils.logging_utils import log_cache_operations
        log_cache_operations("Model cache background initialization complete")
    
    def _get_or_load_model(self, cache_key: str, loader_func, model_name: str):
        """Generic method to get or load a model with thread safety"""
        # Check if model is already cached
        if cache_key in self._models:
            self._access_counts[cache_key] = self._access_counts.get(cache_key, 0) + 1
            return self._models[cache_key]
        
        # Get or create lock for this model
        if cache_key not in self._model_locks:
            self._model_locks[cache_key] = threading.Lock()
        
        # Load model with thread safety
        with self._model_locks[cache_key]:
            # Double-check pattern
            if cache_key in self._models:
                self._access_counts[cache_key] = self._access_counts.get(cache_key, 0) + 1
                return self._models[cache_key]
            
            # Load the model
            from utils.logging_utils import log_cache_operations
            log_cache_operations(f"Loading {model_name}...")
            start_time = time.time()
            
            try:
                model = loader_func()
                load_time = time.time() - start_time
                
                if model is not None:
                    self._models[cache_key] = model
                    self._load_times[cache_key] = load_time
                    self._access_counts[cache_key] = 1
                    log_cache_operations(f"{model_name} loaded and cached ({load_time:.2f}s)")
                    return model
                else:
                    print(clean_log_message(f"❌ Failed to load {model_name}"))
                    return None
                    
            except Exception as e:
                print(clean_log_message(f"❌ Error loading {model_name}: {e}"))
                return None
    
    def _load_kokoro_pipeline(self):
        """Load Kokoro TTS pipeline"""
        try:
            import sys
            from io import StringIO
            from kokoro import KPipeline
            import os
            from utils.logging_utils import clean_log_message

            # Temporarily suppress warnings during model loading
            old_stderr = sys.stderr
            sys.stderr = StringIO()

            try:
                # Check if running as PyInstaller executable
                if getattr(sys, 'frozen', False):
                    # Running as PyInstaller executable
                    # Set environment variable to use bundled models
                    import pathlib

                    # Find the bundled models directory
                    base_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)

                    # Check for models in the new structure first
                    kokoro_model_dir = os.path.join(base_dir, 'models', 'kokoro', 'Kokoro-82M')
                    if os.path.exists(kokoro_model_dir):
                        # Set up HuggingFace cache to point to our model location
                        hf_cache_dir = os.path.join(base_dir, 'huggingface')
                        os.environ['HF_HOME'] = hf_cache_dir
                        os.environ['TRANSFORMERS_CACHE'] = hf_cache_dir
                        os.environ['KOKORO_MODEL_PATH'] = kokoro_model_dir

                        from utils.logging_utils import log_cache_operations
                        log_cache_operations(f"Using Kokoro models from: {kokoro_model_dir}")
                    else:
                        # Legacy: check for old HuggingFace structure
                        hf_cache_dir = os.path.join(base_dir, 'huggingface')
                        if os.path.exists(hf_cache_dir):
                            os.environ['HF_HOME'] = hf_cache_dir
                            os.environ['TRANSFORMERS_CACHE'] = hf_cache_dir

                            from utils.logging_utils import log_cache_operations
                            log_cache_operations(f"Using legacy bundled Kokoro models from: {hf_cache_dir}")
                
                print(clean_log_message("🔄 Loading Kokoro TTS pipeline (first time only)..."))

                # Check if we have a custom model path set
                custom_model_path = os.environ.get('KOKORO_MODEL_PATH')
                if custom_model_path and os.path.exists(custom_model_path):
                    print(clean_log_message(f"Using custom Kokoro model path: {custom_model_path}"))
                    # Try to initialize with custom path if KPipeline supports it
                    try:
                        pipeline = KPipeline(lang_code='a', model_path=custom_model_path)
                    except TypeError:
                        # Fallback: KPipeline doesn't support model_path parameter
                        print(clean_log_message("KPipeline doesn't support custom path, using default"))
                        pipeline = KPipeline(lang_code='a')
                else:
                    pipeline = KPipeline(lang_code='a')  # American English

                print(clean_log_message("✅ Kokoro TTS pipeline loaded and cached"))
                return pipeline
            finally:
                sys.stderr = old_stderr

        except ImportError:
            print(clean_log_message("❌ Kokoro TTS not available"))
            return None
        except Exception as e:
            print(clean_log_message(f"❌ Kokoro loading error: {e}"))
            return None
    

    
    def _load_whisper_model(self, model_name: str):
        """Load Whisper-timestamped model using lazy import system"""
        try:
            # Use the lazy import system from whisper service
            from services.whisper_timestamped_service import _lazy_import_whisper, whisper

            if not _lazy_import_whisper():
                print(clean_log_message("❌ Whisper-timestamped not available"))
                return None

            if not whisper:
                print(clean_log_message("❌ Whisper module not loaded"))
                return None

            return whisper.load_model(model_name)
        except ImportError:
            print(clean_log_message("❌ Whisper-timestamped not available"))
            return None
        except Exception as e:
            print(clean_log_message(f"❌ Whisper model loading error: {e}"))
            return None
    
    def clear_cache(self):
        """Clear all cached models and free memory"""
        print(clean_log_message("🧹 Clearing model cache..."))
        
        with self._lock:
            # Clear all models
            self._models.clear()
            self._load_times.clear()
            self._access_counts.clear()
            
            # Force garbage collection
            gc.collect()
            
        print(clean_log_message("✅ Model cache cleared"))
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cached_models': list(self._models.keys()),
            'load_times': self._load_times.copy(),
            'access_counts': self._access_counts.copy(),
            'total_models': len(self._models)
        }
    
    def print_cache_stats(self):
        """Print cache statistics"""
        stats = self.get_cache_stats()
        
        print(clean_log_message("📊 Model Cache Statistics:"))
        print(f"   Total cached models: {stats['total_models']}")
        
        if stats['cached_models']:
            print("   Cached models:")
            for model_key in stats['cached_models']:
                load_time = stats['load_times'].get(model_key, 0)
                access_count = stats['access_counts'].get(model_key, 0)
                print(f"     • {model_key}: {access_count} accesses, {load_time:.2f}s load time")


# Global cache instance
_model_cache = None
_cache_lock = threading.Lock()

def get_model_cache() -> ModelCache:
    """Get the global model cache instance"""
    global _model_cache
    if _model_cache is None:
        with _cache_lock:
            if _model_cache is None:
                _model_cache = ModelCache()
    return _model_cache

