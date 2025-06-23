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

                # Handle clean structure
                if 'shared_settings' in saved_settings:
                    # Clean structure - return the saved settings directly
                    # Only add missing sections if they don't exist
                    if 'shared_settings' not in saved_settings:
                        saved_settings['shared_settings'] = {}
                    if 'image_tab_settings' not in saved_settings:
                        saved_settings['image_tab_settings'] = {}
                    if 'video_tab_settings' not in saved_settings:
                        saved_settings['video_tab_settings'] = {}

                    return saved_settings
                else:
                    # Legacy structure - merge with defaults for backward compatibility
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

    def get_tab_settings(self, tab_name: str) -> Dict[str, Any]:
        """Get settings specific to a tab (image_tab or video_tab)"""
        settings = self.load_settings()

        # Start with shared settings
        tab_settings = {}
        if 'shared_settings' in settings:
            tab_settings.update(settings['shared_settings'])

        # Add tab-specific settings
        tab_key = f"{tab_name}_settings"
        if tab_key in settings:
            tab_settings.update(settings[tab_key])

        # Fallback to defaults if no settings found
        if not tab_settings or len(tab_settings) < 2:
            # Use defaults from default_settings
            tab_settings = {
                'tts_language': 'en',
                'tts_voice_actor': 'Default',
                'tts_speed': 1.0,
                'tts_emotion': 'neutral',
                'output_folder': self.default_settings.get('output_folder', 'Default (Auto)')
            }

            if tab_name == 'image_tab':
                tab_settings.update({
                    'image_fit_method': self.default_settings.get('image_fit_method', 'cover'),
                    'aspect_ratio': self.default_settings.get('aspect_ratio', '16:9 (Landscape)')
                })
            elif tab_name == 'video_tab':
                tab_settings.update({
                    'mute_original_audio': False,
                    'original_audio_volume': 0.7,
                    'subtitle_style': 'modern_glow'
                })

        return tab_settings

    def save_tab_settings(self, tab_name: str, tab_settings: Dict[str, Any]) -> bool:
        """Save settings specific to a tab with clean structure"""
        settings = self.load_settings()

        # Ensure the clean structure exists
        if 'shared_settings' not in settings:
            settings['shared_settings'] = {}
        if 'image_tab_settings' not in settings:
            settings['image_tab_settings'] = {}
        if 'video_tab_settings' not in settings:
            settings['video_tab_settings'] = {}

        # Separate shared settings from tab-specific settings
        shared_keys = ['tts_language', 'tts_voice_actor', 'tts_speed', 'tts_emotion', 'output_folder']

        for key, value in tab_settings.items():
            if key in shared_keys:
                # Update shared settings
                settings['shared_settings'][key] = value
                # Also update root level output_folder for global access
                if key == 'output_folder':
                    settings['output_folder'] = value
            else:
                # Update tab-specific settings
                tab_key = f"{tab_name}_settings"
                settings[tab_key][key] = value

        return self.save_settings(settings)