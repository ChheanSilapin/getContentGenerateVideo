"""
Settings Manager - Handle persistent storage of user settings
Saves settings to a JSON file so they persist between sessions
"""
import json
import os
from typing import Dict, Any


class SettingsManager:
    """Manage persistent storage of application settings"""
    
    def __init__(self, settings_file: str = "user_settings.json"):
        """Initialize settings manager with specified settings file"""
        self.settings_file = settings_file
        self.default_settings = {
            # Output settings
            'output_folder': 'Default (Auto)',

            # Legacy audio settings (for backward compatibility)
            'voice_actor': 'Default',
            'speed': 0.8,
            'emotion': 'neutral',
            'mute': False,
            'volume': 0.7,

            # New TTS settings (gTTS)
            'tts_language': 'en',
            'tts_voice_actor': 'Default',
            'tts_speed': 1.0,
            'tts_emotion': 'neutral',

            # Speech recognition settings (Vosk) - Auto-enabled
            'sr_enabled': True,  # Automatically enabled
            'sr_language': 'en-us',
            'sr_model_path': '',  # Auto-detected

            # Content synchronization settings
            'timing_mode': 'balanced',  # balanced, fast, slow
            'min_image_duration': 0.8,  # seconds
            'max_image_duration': 8.0,  # seconds
            'optimal_image_duration': 3.0,  # seconds

            # Image processing settings
            'image_fit_method': 'cover',  # cover, contain, stretch
            'aspect_ratio': '16:9 (Landscape)'  # aspect ratio preset
        }
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file, return defaults if file doesn't exist"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                settings = self.default_settings.copy()
                settings.update(saved_settings)
                return settings
            else:
                return self.default_settings.copy()
        
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_setting(self, key: str, default=None):
        """Get a specific setting value"""
        settings = self.load_settings()
        return settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a specific setting value and save"""
        settings = self.load_settings()
        settings[key] = value
        return self.save_settings(settings)
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        return self.save_settings(self.default_settings.copy()) 