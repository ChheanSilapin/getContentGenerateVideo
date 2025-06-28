"""
Optimized TTS Provider System - gTTS Only
Simplified for speed and reliability
"""
import os
import tempfile
import time
from typing import Optional, Dict, Any

# Import logging utilities for emoji handling
from utils.logging_utils import clean_log_message

# Import gTTS
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("❌ gTTS not available. Install with: pip install gtts")


class GTTSProvider:
    """Google Text-to-Speech Provider - Optimized for speed"""
    
    def __init__(self):
        self.name = "Google TTS"
        self.available = GTTS_AVAILABLE
        self.last_error = None
    
    def check_availability(self) -> bool:
        """Check if gTTS is available"""
        return GTTS_AVAILABLE
    
    def generate_speech(self, text: str, output_file: str, **kwargs) -> bool:
        """Generate speech using gTTS"""
        if not self.available:
            self.last_error = "gTTS not available"
            return False
        
        try:
            # Get parameters
            language = kwargs.get('language', 'en')
            emotion = kwargs.get('emotion', 'neutral')
            
            # Create gTTS object
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to temporary file first
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_path = temp_file.name
                tts.save(temp_path)
                print(f"gTTS audio saved to temporary file: {temp_path}")
            
            # Move to final location
            if os.path.exists(temp_path):
                os.rename(temp_path, output_file)
                return True
            else:
                self.last_error = "Failed to generate audio file"
                return False
                
        except Exception as e:
            self.last_error = str(e)
            print(clean_log_message(f"❌ gTTS error: {e}"))
            return False
    
    def get_supported_languages(self):
        """Get supported languages for gTTS"""
        return [
            'en', 'en-uk', 'en-us', 'en-au', 'en-ca', 'en-in',
            'fr', 'de', 'es', 'it', 'pt', 'ru', 'ja', 'ko', 'zh'
        ]
    
    def supports_language(self, language: str) -> bool:
        """Check if language is supported"""
        return language in self.get_supported_languages()


class TTSManager:
    """Simplified TTS Manager - gTTS only"""
    
    def __init__(self):
        self.providers = {}
        self.priority_order = []
        self.settings = {}
        self._initialize_providers()
        self._load_settings()

    def _initialize_providers(self):
        """Initialize only gTTS provider (optimized for speed)"""
        # Initialize only gTTS provider
        gtts_provider = GTTSProvider()
        
        if gtts_provider.available:
            self.providers['google_tts'] = gtts_provider
            self.priority_order = ['google_tts']
        else:
            print(clean_log_message(f"❌ gTTS not available: {gtts_provider.last_error}"))

    def _load_settings(self):
        """Load TTS settings from config"""
        try:
            from config import GTTS_CONFIG
            self.settings = GTTS_CONFIG.copy()
        except ImportError:
            self.settings = {
                "language_support": ["en", "en-au", "en-us"],
                "emotion_processing": True,
                "speed_adjustment": True
            }

    def generate_speech(self, text: str, output_file: str, **kwargs) -> bool:
        """Generate speech using gTTS (direct, no fallbacks)"""
        # Direct gTTS generation (no provider checking overhead)
        gtts_provider = self.providers.get('google_tts')
        if not gtts_provider:
            print(clean_log_message("❌ gTTS not available"))
            return False

        try:
            return gtts_provider.generate_speech(text, output_file, **kwargs)
        except Exception as e:
            print(clean_log_message(f"❌ gTTS error: {e}"))
            return False

    def get_available_providers(self):
        """Get list of available providers"""
        return list(self.providers.keys())

    def is_provider_available(self, provider_name: str) -> bool:
        """Check if specific provider is available"""
        return provider_name in self.providers

    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific provider"""
        if provider_name not in self.providers:
            return None
        
        provider = self.providers[provider_name]
        return {
            'name': provider.name,
            'available': provider.available,
            'supported_languages': provider.get_supported_languages()
        }


# Global TTS manager instance
_tts_manager = None

def get_tts_manager() -> TTSManager:
    """Get global TTS manager instance"""
    global _tts_manager
    if _tts_manager is None:
        _tts_manager = TTSManager()
    return _tts_manager

def generate_speech_simple(text: str, output_file: str, **kwargs) -> bool:
    """Simple function to generate speech"""
    manager = get_tts_manager()
    return manager.generate_speech(text, output_file, **kwargs)
