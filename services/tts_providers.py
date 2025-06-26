"""
Hybrid TTS Provider System for Advanced Text-to-Speech
Supports multiple TTS engines with intelligent fallbacks while maintaining backward compatibility

Priority Order:
1. gTTS (Google TTS, reliable, current default)
2. pyttsx3 (cross-platform offline TTS)
3. Windows SAPI (system fallback)
"""
import os
import tempfile
import time
import platform
import subprocess
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from utils.common_imports import traceback

# Import logging utilities for emoji handling
from utils.logging_utils import clean_log_message

# Chatterbox TTS removed from project

# Try to import pyttsx3
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("pyttsx3 not available. Install with: pip install pyttsx3")

# Try to import gTTS
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# Try to import PyDub for audio processing
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class TTSProvider(ABC):
    """Abstract base class for TTS providers"""
    
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority
        self.available = self.check_availability()
        self.last_error = None
    
    @abstractmethod
    def check_availability(self) -> bool:
        """Check if this TTS provider is available"""
        pass
    
    @abstractmethod
    def generate_speech(self, text: str, output_file: str, **kwargs) -> bool:
        """Generate speech from text"""
        pass
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return ['en']  # Default to English
    
    def supports_language(self, language: str) -> bool:
        """Check if provider supports given language"""
        return language.lower() in [lang.lower() for lang in self.get_supported_languages()]
    
    def get_quality_score(self) -> int:
        """Get quality score (1-10, higher is better)"""
        return 5  # Default medium quality


# ChatterboxTTSProvider class removed


class GTTSProvider(TTSProvider):
    """Google Text-to-Speech Provider - Current reliable system"""
    
    def __init__(self):
        super().__init__("Google TTS", priority=2)
    
    def check_availability(self) -> bool:
        """Check if gTTS is available"""
        if not GTTS_AVAILABLE:
            self.last_error = "gTTS package not installed"
            return False
        
        # Test internet connectivity
        try:
            import urllib.request
            urllib.request.urlopen('http://www.google.com', timeout=3)
            return True
        except:
            self.last_error = "Internet connection required for gTTS"
            return False
    
    def generate_speech(self, text: str, output_file: str, **kwargs) -> bool:
        """Generate speech using gTTS - maintains existing implementation"""
        if not self.available:
            return False
        
        try:
            # Import existing gTTS function to maintain compatibility
            from services.audio_service import generate_audio_gtts
            
            # Extract parameters
            speed = kwargs.get('speed', 0.8)
            emotion = kwargs.get('emotion', 'neutral')
            language = kwargs.get('language', 'en')
            voice_actor = kwargs.get('voice_actor', None)
            
            # Use existing gTTS implementation
            return generate_audio_gtts(text, output_file, speed, emotion, language, voice_actor)
            
        except Exception as e:
            self.last_error = f"gTTS generation failed: {e}"
            print(clean_log_message(f"❌ gTTS error: {e}"))
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages for gTTS"""
        return [
            'en', 'en-uk', 'en-us', 'en-au', 'en-ca', 'en-in',
            'fr', 'de', 'es', 'it', 'pt', 'ru', 'ja', 'ko', 'zh',
            'ar', 'hi', 'th', 'vi', 'tr', 'pl', 'nl', 'sv', 'da',
            'no', 'fi', 'cs', 'sk', 'hu', 'ro', 'bg', 'hr', 'sl',
            'et', 'lv', 'lt', 'mt', 'ga', 'cy', 'eu', 'ca', 'gl'
        ]
    
    def get_quality_score(self) -> int:
        """Get quality score"""
        return 8  # Very good quality


class Pyttsx3Provider(TTSProvider):
    """pyttsx3 Provider - Cross-platform offline TTS"""

    def __init__(self):
        super().__init__("pyttsx3", priority=3)
        self.engine = None

    def check_availability(self) -> bool:
        """Check if pyttsx3 is available"""
        if not PYTTSX3_AVAILABLE:
            self.last_error = "pyttsx3 package not installed"
            return False

        try:
            # Test engine initialization
            test_engine = pyttsx3.init()
            test_engine.stop()
            return True
        except Exception as e:
            self.last_error = f"pyttsx3 engine initialization failed: {e}"
            return False

    def _get_engine(self):
        """Get or create pyttsx3 engine"""
        if self.engine is None:
            try:
                self.engine = pyttsx3.init()
            except Exception as e:
                print(clean_log_message(f"❌ pyttsx3 engine creation failed: {e}"))
                return None
        return self.engine

    def generate_speech(self, text: str, output_file: str, **kwargs) -> bool:
        """Generate speech using pyttsx3"""
        if not self.available:
            return False

        try:
            engine = self._get_engine()
            if not engine:
                return False

            # Extract parameters
            speed = kwargs.get('speed', 1.0)
            emotion = kwargs.get('emotion', 'neutral')
            voice_actor = kwargs.get('voice_actor', None)

            # Configure engine
            self._configure_engine(engine, speed, emotion, voice_actor)

            # Generate speech to file
            engine.save_to_file(text, output_file)
            engine.runAndWait()

            # Verify file was created
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(clean_log_message(f"✅ pyttsx3 generated audio: {output_file}"))
                return True
            else:
                self.last_error = "pyttsx3 failed to create audio file"
                return False

        except Exception as e:
            self.last_error = f"pyttsx3 generation failed: {e}"
            print(clean_log_message(f"❌ pyttsx3 error: {e}"))
            return False

    def _configure_engine(self, engine, speed: float, emotion: str, voice_actor: str):
        """Configure pyttsx3 engine settings"""
        try:
            # Set speech rate (words per minute)
            base_rate = 200  # Default rate
            rate = int(base_rate * speed)
            engine.setProperty('rate', rate)

            # Set volume
            engine.setProperty('volume', 1.0)

            # Select voice based on voice_actor and emotion
            voices = engine.getProperty('voices')
            if voices:
                selected_voice = self._select_voice(voices, voice_actor, emotion)
                if selected_voice:
                    engine.setProperty('voice', selected_voice.id)

        except Exception as e:
            print(clean_log_message(f"⚠️ pyttsx3 configuration warning: {e}"))

    def _select_voice(self, voices, voice_actor: str, emotion: str):
        """Select appropriate voice based on preferences"""
        if not voices:
            return None

        # Voice selection preferences
        preferred_voices = []

        # Handle voice_actor preferences
        if voice_actor and voice_actor.lower() in ['british', 'uk']:
            # Prefer British voices
            for voice in voices:
                if any(term in voice.name.lower() for term in ['british', 'uk', 'hazel', 'george']):
                    preferred_voices.append(voice)

        # Handle emotion preferences
        if emotion in ['excited', 'energetic', 'happy']:
            # Prefer female voices for excited emotions
            for voice in voices:
                if any(term in voice.name.lower() for term in ['female', 'zira', 'hazel']):
                    preferred_voices.append(voice)
        elif emotion in ['dramatic', 'serious']:
            # Prefer male voices for dramatic emotions
            for voice in voices:
                if any(term in voice.name.lower() for term in ['male', 'david', 'mark']):
                    preferred_voices.append(voice)

        # Return preferred voice or default
        if preferred_voices:
            return preferred_voices[0]
        elif len(voices) > 1:
            return voices[1]  # Often female voice
        else:
            return voices[0]  # Default voice

    def get_supported_languages(self) -> List[str]:
        """Get supported languages for pyttsx3"""
        return ['en', 'en-us']  # Depends on system voices

    def get_quality_score(self) -> int:
        """Get quality score"""
        return 6  # Good quality


class WindowsSAPIProvider(TTSProvider):
    """Windows System TTS Provider - Final fallback"""

    def __init__(self):
        super().__init__("Windows SAPI", priority=4)

    def check_availability(self) -> bool:
        """Check if Windows SAPI is available"""
        if platform.system() != "Windows":
            self.last_error = "Windows SAPI only available on Windows"
            return False
        return True

    def generate_speech(self, text: str, output_file: str, **kwargs) -> bool:
        """Generate speech using Windows SAPI - maintains existing implementation"""
        if not self.available:
            return False

        try:
            # Import existing system TTS function to maintain compatibility
            from services.audio_service import generate_audio_system_emotional

            emotion = kwargs.get('emotion', 'neutral')
            return generate_audio_system_emotional(text, output_file, emotion)

        except Exception as e:
            self.last_error = f"Windows SAPI generation failed: {e}"
            print(clean_log_message(f"❌ Windows SAPI error: {e}"))
            return False

    def get_supported_languages(self) -> List[str]:
        """Get supported languages for Windows SAPI"""
        return ['en', 'en-us']  # Windows SAPI typically supports system languages

    def get_quality_score(self) -> int:
        """Get quality score"""
        return 5  # Medium quality


class HybridTTSManager:
    """
    Manages multiple TTS providers with intelligent priority-based fallbacks

    Priority Order:
    1. gTTS (Google TTS, reliable, current default)
    2. pyttsx3 (cross-platform offline TTS)
    3. Windows SAPI (system fallback)
    """

    def __init__(self):
        self.providers = {}
        self.priority_order = []
        self.settings = {}
        self._initialize_providers()
        self._load_settings()

    def _initialize_providers(self):
        """Initialize all TTS providers"""
        # Initialize providers in priority order
        providers = [
            GTTSProvider(),
            Pyttsx3Provider(),
            WindowsSAPIProvider()
        ]

        # Store available providers (only print once)
        if not hasattr(self, '_providers_initialized'):
            for provider in providers:
                if provider.available:
                    self.providers[provider.name.lower().replace(' ', '_')] = provider
                    print(clean_log_message(f"✅ {provider.name} initialized and available"))
                else:
                    print(clean_log_message(f"❌ {provider.name} not available: {provider.last_error}"))
            self._providers_initialized = True
        else:
            # Silent re-initialization
            for provider in providers:
                if provider.available:
                    self.providers[provider.name.lower().replace(' ', '_')] = provider

        # Set priority order based on available providers
        self.priority_order = [
            'google_tts',      # gTTS as primary (reliable system)
            'pyttsx3',
            'windows_sapi'
        ]

        # Filter to only available providers
        self.priority_order = [p for p in self.priority_order if p in self.providers]

        # Only print status once
        if not hasattr(self, '_status_printed'):
            print(clean_log_message(f"🎯 TTS Providers available: {list(self.providers.keys())}"))
            print(clean_log_message(f"📋 Priority order: {self.priority_order}"))
            self._status_printed = True

    def _load_settings(self):
        """Load TTS settings from configuration"""
        try:
            from utils.settings_manager import SettingsManager
            settings_manager = SettingsManager()

            # Load shared settings (maintains backward compatibility)
            shared_settings = settings_manager.get_shared_settings()
            self.settings = {
                'enabled_providers': shared_settings.get('enabled_tts_providers', list(self.providers.keys())),
                'prefer_offline': shared_settings.get('prefer_offline_tts', False),
                'quality_threshold': shared_settings.get('tts_quality_threshold', 7),
                'fallback_enabled': shared_settings.get('tts_fallback_enabled', True)
            }
        except Exception as e:
            print(clean_log_message(f"⚠️ Could not load TTS settings: {e}"))
            # Use defaults
            self.settings = {
                'enabled_providers': list(self.providers.keys()),
                'prefer_offline': False,
                'quality_threshold': 7,
                'fallback_enabled': True
            }

    def generate_speech(self, text: str, output_file: str, **kwargs) -> bool:
        """
        Generate speech using first available provider in priority order

        Args:
            text: Text to convert to speech
            output_file: Path to output audio file
            **kwargs: TTS parameters (voice_actor, speed, emotion, language, etc.)

        Returns:
            bool: True if successful, False if all providers failed
        """
        if not self.providers:
            print(clean_log_message("❌ No TTS providers available"))
            return False

        # Get enabled providers from settings
        enabled_providers = self._get_enabled_providers()

        # Get language for provider filtering
        language = kwargs.get('language', 'en')

        # Try each provider in priority order
        for provider_name in self.priority_order:
            if provider_name not in enabled_providers:
                continue

            provider = self.providers.get(provider_name)
            if not provider or not provider.available:
                continue

            # Check language support
            if not provider.supports_language(language):
                print(clean_log_message(f"⚠️ {provider.name} doesn't support language '{language}', trying next provider"))
                continue

            print(clean_log_message(f"🎯 Trying {provider.name} for TTS generation..."))

            try:
                success = provider.generate_speech(text, output_file, **kwargs)
                if success:
                    print(clean_log_message(f"✅ {provider.name} successfully generated audio"))
                    return True
                else:
                    print(clean_log_message(f"❌ {provider.name} failed: {provider.last_error}, trying next provider"))
            except Exception as e:
                print(clean_log_message(f"❌ {provider.name} error: {e}, trying next provider"))
                provider.last_error = str(e)

        print(clean_log_message("❌ All TTS providers failed"))
        return False

    def _get_enabled_providers(self) -> List[str]:
        """Get list of enabled providers from settings"""
        enabled = self.settings.get('enabled_providers', list(self.providers.keys()))

        # Ensure enabled providers exist
        return [p for p in enabled if p in self.providers]

    def set_provider_priority(self, priority_order: List[str]):
        """Set custom priority order for TTS providers"""
        # Validate that all providers in order exist
        valid_order = [p for p in priority_order if p in self.providers]
        self.priority_order = valid_order
        print(clean_log_message(f"🔄 TTS priority order updated: {self.priority_order}"))

    def enable_provider(self, provider_name: str, enabled: bool = True):
        """Enable or disable a specific TTS provider"""
        if provider_name in self.providers:
            if enabled and provider_name not in self.settings['enabled_providers']:
                self.settings['enabled_providers'].append(provider_name)
            elif not enabled and provider_name in self.settings['enabled_providers']:
                self.settings['enabled_providers'].remove(provider_name)
            print(clean_log_message(f"🔄 {provider_name} {'enabled' if enabled else 'disabled'}"))

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                'name': provider.name,
                'available': provider.available,
                'enabled': name in self.settings['enabled_providers'],
                'priority': provider.priority,
                'quality_score': provider.get_quality_score(),
                'supported_languages': provider.get_supported_languages(),
                'last_error': provider.last_error
            }
        return status

    def get_recommended_provider(self, **kwargs) -> Optional[str]:
        """Get recommended provider based on requirements"""
        language = kwargs.get('language', 'en')
        quality_required = kwargs.get('quality_threshold', self.settings['quality_threshold'])
        offline_preferred = kwargs.get('prefer_offline', self.settings['prefer_offline'])

        candidates = []

        for provider_name in self.priority_order:
            if provider_name not in self.settings['enabled_providers']:
                continue

            provider = self.providers.get(provider_name)
            if not provider or not provider.available:
                continue

            if not provider.supports_language(language):
                continue

            if provider.get_quality_score() < quality_required:
                continue

            # Check offline preference
            if offline_preferred:
                if provider_name in ['pyttsx3', 'windows_sapi']:
                    candidates.append(provider_name)
            else:
                candidates.append(provider_name)

        return candidates[0] if candidates else None


# Global instance for backward compatibility
_hybrid_tts_manager = None

def get_hybrid_tts_manager() -> HybridTTSManager:
    """Get global hybrid TTS manager instance"""
    global _hybrid_tts_manager
    if _hybrid_tts_manager is None:
        _hybrid_tts_manager = HybridTTSManager()
    return _hybrid_tts_manager
