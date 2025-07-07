"""
Whisper Service Manager - Singleton pattern to avoid multiple initializations
"""
from typing import Optional
from config import WHISPER_TIMESTAMPED_CONFIG

# Import logging utilities for emoji handling
from utils.logging_utils import clean_log_message

# Global singleton instance
_whisper_service_instance = None

def get_whisper_service():
    """Get shared whisper service instance (singleton pattern)"""
    global _whisper_service_instance
    
    if _whisper_service_instance is None:
        _whisper_service_instance = _create_whisper_service()
    
    return _whisper_service_instance

def _create_whisper_service():
    """Create whisper service instance"""
    try:
        from services.whisper_timestamped_service import WhisperTimestampedService
        
        config = WHISPER_TIMESTAMPED_CONFIG
        if not config.get("enable_service", True):
            return None
            
        service = WhisperTimestampedService(
            model_name=config.get("model_name", "tiny"),
            device=config.get("device", "auto"),
            preload_model=True  # Enable pre-loading for performance
        )
        
        if service.is_service_available():
            # Silent initialization for speed optimization
            return service
        else:
            return None

    except ImportError:
        print(clean_log_message(" whisper-timestamped not available. Install with: pip install whisper-timestamped"))
        return None
    except Exception as e:
        print(clean_log_message(f" Failed to initialize whisper-timestamped service: {e}"))
        return None

def reset_whisper_service():
    """Reset the whisper service (for testing/debugging)"""
    global _whisper_service_instance
    _whisper_service_instance = None

def is_whisper_available() -> bool:
    """Check if whisper service is available"""
    service = get_whisper_service()
    return service is not None and service.is_service_available()
