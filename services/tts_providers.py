"""
Professional TTS Provider System - Edge TTS + Kokoro TTS
High-quality voice generation with your selected voices
"""
import os
import tempfile
import time
import asyncio
import subprocess
import sys
from typing import Optional, Dict, Any

# Import logging utilities for emoji handling
from utils.logging_utils import clean_log_message

# Import Edge TTS
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("❌ Edge TTS not available. Install with: pip install edge-tts")

# Import Kokoro TTS
try:
    from kokoro import KPipeline
    import soundfile as sf
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False
    print("❌ Kokoro TTS not available. Install with: pip install kokoro soundfile")


class EdgeTTSProvider:
    """Microsoft Edge Text-to-Speech Provider - High Quality Neural Voices"""

    def __init__(self):
        self.name = "Microsoft Edge TTS"
        self.available = EDGE_TTS_AVAILABLE
        self.last_error = None

        # Your selected Edge TTS voices
        self.voice_mapping = {
            'Guy': 'en-US-GuyNeural',
            'Connor': 'en-IE-ConnorNeural',
            'Aria': 'en-US-AriaNeural'
        }

    def check_availability(self) -> bool:
        """Check if Edge TTS is available"""
        return EDGE_TTS_AVAILABLE

    def generate_speech(self, text: str, output_file: str, **kwargs) -> bool:
        """Generate speech using Edge TTS"""
        if not self.available:
            self.last_error = "Edge TTS not available"
            return False

        try:
            # Get voice selection and speed
            voice_actor = kwargs.get('voice_actor', 'Guy')
            speed = kwargs.get('speed', 1.0)

            # Map to Edge TTS voice
            edge_voice = self.voice_mapping.get(voice_actor, 'en-US-GuyNeural')

            # Generate audio asynchronously with speed control
            success = asyncio.run(self._generate_async(text, output_file, edge_voice, speed))

            if success:
                return True
            else:
                self.last_error = "Failed to generate Edge TTS audio"
                return False

        except Exception as e:
            self.last_error = str(e)
            print(clean_log_message(f"❌ Edge TTS error: {e}"))
            return False

    async def _generate_async(self, text: str, output_file: str, voice: str, speed: float = 1.0) -> bool:
        """Async generation for Edge TTS with speed control"""
        try:
            # Apply speed control using SSML prosody rate
            if speed != 1.0:
                # Convert speed to percentage rate (0.8 -> "-20%", 1.2 -> "+20%")
                rate_percentage = f"{(speed - 1) * 100:+.0f}%"
                # Wrap text in SSML with prosody rate control
                ssml_text = f'<speak><prosody rate="{rate_percentage}">{text}</prosody></speak>'
                communicate = edge_tts.Communicate(ssml_text, voice)
            else:
                # Use normal text without SSML for default speed
                communicate = edge_tts.Communicate(text, voice)

            await communicate.save(output_file)
            return True
        except Exception as e:
            print(clean_log_message(f"❌ Edge TTS async error: {e}"))
            return False

    def get_supported_voices(self):
        """Get supported voices for Edge TTS"""
        return list(self.voice_mapping.keys())

    def supports_voice(self, voice: str) -> bool:
        """Check if voice is supported"""
        return voice in self.voice_mapping


class KokoroTTSProvider:
    """Kokoro TTS Provider - Fast, High-Quality 82M Parameter Model"""

    def __init__(self):
        self.name = "Kokoro TTS"
        self.available = KOKORO_AVAILABLE
        self.last_error = None
        self.pipeline = None

        # Your selected Kokoro voices
        self.voice_mapping = {
            'Michael': 'am_michael',
            'Adam': 'am_adam',
            'Heart': 'af_heart'
        }

    def check_availability(self) -> bool:
        """Check if Kokoro TTS is available"""
        return KOKORO_AVAILABLE

    def _get_pipeline(self):
        """Get cached Kokoro pipeline"""
        if not self.available:
            return None

        try:
            from utils.model_cache import get_model_cache
            cache = get_model_cache()
            pipeline = cache.get_kokoro_pipeline()

            if pipeline is None:
                self.available = False
                self.last_error = "Failed to load Kokoro pipeline"

            return pipeline

        except Exception as e:
            print(clean_log_message(f"❌ Error getting Kokoro pipeline: {e}"))
            self.available = False
            self.last_error = str(e)
            return None

    def generate_speech(self, text: str, output_file: str, **kwargs) -> bool:
        """Generate speech using Kokoro TTS with cached pipeline"""
        if not self.available:
            self.last_error = "Kokoro TTS not available"
            return False

        try:
            # Get cached pipeline
            pipeline = self._get_pipeline()
            if not pipeline:
                return False

            # Get voice selection and speed
            voice_actor = kwargs.get('voice_actor', 'Michael')
            speed = kwargs.get('speed', 1.0)

            # Map to Kokoro voice
            kokoro_voice = self.voice_mapping.get(voice_actor, 'am_michael')

            # Generate audio using cached pipeline with speed control
            generator = pipeline(text, voice=kokoro_voice, speed=speed)

            # Process the generator (Kokoro returns chunks)
            audio_chunks = []
            for i, (_, _, audio) in enumerate(generator):
                audio_chunks.append(audio)

            # Combine audio chunks if multiple
            if len(audio_chunks) == 1:
                final_audio = audio_chunks[0]
            else:
                import numpy as np
                final_audio = np.concatenate(audio_chunks)

            # Save audio file (Kokoro outputs WAV at 24kHz)
            sf.write(output_file, final_audio, 24000)

            return True

        except Exception as e:
            self.last_error = str(e)
            print(clean_log_message(f"❌ Kokoro TTS error: {e}"))
            return False

    def get_supported_voices(self):
        """Get supported voices for Kokoro TTS"""
        return list(self.voice_mapping.keys())

    def supports_voice(self, voice: str) -> bool:
        """Check if voice is supported"""
        return voice in self.voice_mapping


class TTSManager:
    """Professional TTS Manager - Edge TTS + Kokoro TTS"""

    def __init__(self):
        self.providers = {}
        self.priority_order = []
        self.settings = {}
        self._initialize_providers()
        self._load_settings()

    def _initialize_providers(self):
        """Initialize Edge TTS and Kokoro TTS providers"""
        # Initialize Edge TTS provider
        edge_provider = EdgeTTSProvider()
        if edge_provider.available:
            self.providers['edge_tts'] = edge_provider
            self.priority_order.append('edge_tts')
            print(clean_log_message("[OK] Edge TTS provider initialized"))

        # Initialize Kokoro TTS provider
        kokoro_provider = KokoroTTSProvider()
        if kokoro_provider.available:
            self.providers['kokoro_tts'] = kokoro_provider
            self.priority_order.append('kokoro_tts')
            print(clean_log_message("[OK] Kokoro TTS provider initialized"))

        if not self.providers:
            print(clean_log_message("❌ No TTS providers available!"))

    def _load_settings(self):
        """Load TTS settings from config"""
        try:
            from config import TTS_CONFIG
            self.settings = TTS_CONFIG.copy()
        except ImportError:
            self.settings = {
                "edge_voices": ["Guy", "Connor", "Aria"],
                "kokoro_voices": ["Michael", "Adam", "Heart"],
                "default_provider": "edge_tts",
                "fallback_enabled": True
            }

    def generate_speech(self, text: str, output_file: str, **kwargs) -> bool:
        """Generate speech using Edge TTS or Kokoro TTS with smart routing"""
        voice_actor = kwargs.get('voice_actor', 'Guy')

        # Determine which provider to use based on voice
        edge_voices = ['Guy', 'Connor', 'Aria']
        kokoro_voices = ['Michael', 'Adam', 'Heart']

        if voice_actor in edge_voices and 'edge_tts' in self.providers:
            provider = self.providers['edge_tts']
        elif voice_actor in kokoro_voices and 'kokoro_tts' in self.providers:
            provider = self.providers['kokoro_tts']
        else:
            # Fallback to first available provider
            if self.priority_order:
                provider_name = self.priority_order[0]
                provider = self.providers[provider_name]
            else:
                print(clean_log_message("❌ No TTS providers available"))
                return False

        try:
            return provider.generate_speech(text, output_file, **kwargs)
        except Exception as e:
            print(clean_log_message(f"❌ TTS error with {provider.name}: {e}"))

            # Try fallback if enabled
            if self.settings.get('fallback_enabled', True) and len(self.priority_order) > 1:
                for fallback_name in self.priority_order[1:]:
                    if fallback_name in self.providers:
                        fallback_provider = self.providers[fallback_name]
                        print(clean_log_message(f"🔄 Trying fallback: {fallback_provider.name}"))
                        try:
                            return fallback_provider.generate_speech(text, output_file, **kwargs)
                        except Exception as fallback_error:
                            print(clean_log_message(f"❌ Fallback failed: {fallback_error}"))
                            continue

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
            'supported_voices': provider.get_supported_voices()
        }

    def get_all_voices(self):
        """Get all available voices from all providers"""
        all_voices = []
        for provider in self.providers.values():
            if hasattr(provider, 'get_supported_voices'):
                all_voices.extend(provider.get_supported_voices())
        return all_voices

    def get_voice_provider(self, voice: str) -> Optional[str]:
        """Get which provider supports a specific voice"""
        for provider_name, provider in self.providers.items():
            if hasattr(provider, 'supports_voice') and provider.supports_voice(voice):
                return provider_name
        return None


# Global TTS manager instance
_tts_manager = None

def get_tts_manager() -> TTSManager:
    """Get global TTS manager instance"""
    global _tts_manager
    if _tts_manager is None:
        _tts_manager = TTSManager()
    return _tts_manager

def generate_speech_simple(text: str, output_file: str, **kwargs) -> bool:
    """Simple function to generate speech with Edge TTS or Kokoro TTS"""
    manager = get_tts_manager()
    return manager.generate_speech(text, output_file, **kwargs)

def get_available_voices():
    """Get all available voices"""
    manager = get_tts_manager()
    return manager.get_all_voices()

def install_dependencies():
    """Install required TTS dependencies"""
    try:
        print(clean_log_message("📦 Installing TTS dependencies..."))
        subprocess.run([sys.executable, "-m", "pip", "install", "edge-tts>=6.1.0"], check=True, capture_output=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "kokoro>=0.9.4", "soundfile>=0.12.0"], check=True, capture_output=True)
        print(clean_log_message("✅ TTS dependencies installed successfully"))
        return True
    except Exception as e:
        print(clean_log_message(f"❌ Failed to install TTS dependencies: {e}"))
        return False
