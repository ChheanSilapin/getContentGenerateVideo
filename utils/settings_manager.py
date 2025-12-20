"""
Settings Manager - Handle persistent storage of user settings
Saves settings to a JSON file so they persist between sessions

REFACTORED: Reduced logging, better caching, debounced saves
"""
import json
import os
import sys
import time
from typing import Dict, Any


class SettingsManager:
    """Manage persistent storage of application settings"""

    # Class-level cache to avoid redundant file reads
    _settings_cache = {}
    _cache_timestamp = {}
    _pending_save = None
    _last_save_time = 0
    _save_debounce_seconds = 1.0  # Minimum time between saves
    
    # Logging control
    _verbose = False  # Set to True for debugging

    def __init__(self, settings_file: str = "user_settings.json"):
        """Initialize settings manager with specified settings file"""
        self.settings_file = self._resolve_settings_path(settings_file)
        self.default_settings = {
            # Output settings - use portable default
            'output_folder': self._get_default_output_folder(),

            # Migration tracking (internal use)
            '_migration_completed': False,

            # Modern TTS settings (Edge TTS + Kokoro TTS)
            'tts_language': 'en',
            'tts_voice_actor': 'Guy',
            'tts_speed': 1.0,
            'tts_emotion': 'neutral',

            # Speech recognition settings (Whisper-timestamped only)
            'sr_enabled': True,  # Automatically enabled
            'sr_language': 'en-us',

            # Professional TTS settings (Edge TTS + Kokoro TTS)
            'enabled_tts_providers': ['edge_tts', 'kokoro_tts'],
            'tts_provider_priority': ['edge_tts', 'kokoro_tts'],
            'prefer_offline_tts': False,  # Edge TTS requires internet, Kokoro is offline
            'tts_quality_threshold': 8,   # Higher quality threshold for neural voices
            'tts_fallback_enabled': True,

            # Content synchronization settings
            'timing_mode': 'balanced',  # balanced, fast, slow
            'min_image_duration': 0.8,  # seconds
            'max_image_duration': 8.0,  # seconds
            'optimal_image_duration': 3.0,  # seconds

            # Image processing settings
            'image_fit_method': 'contain',  # cover, contain, stretch
            'aspect_ratio': '1:1 (Square)'  # aspect ratio preset
        }

    def _log(self, message: str):
        """Print message only if verbose mode is enabled"""
        if self._verbose:
            print(message)

    def _get_default_output_folder(self) -> str:
        """Get a portable default output folder that works for any user"""
        import tempfile
        import platform

        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            if platform.system() == "Windows":
                try:
                    appdata_local = os.environ.get('LOCALAPPDATA')
                    if appdata_local:
                        output_dir = os.path.join(appdata_local, "Video Generator", "output")
                        os.makedirs(output_dir, exist_ok=True)
                        return output_dir
                except Exception:
                    pass

                try:
                    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
                    output_dir = os.path.join(documents_path, "Video Generator", "output")
                    os.makedirs(output_dir, exist_ok=True)
                    return output_dir
                except Exception:
                    pass
            else:
                try:
                    output_dir = os.path.join(os.path.expanduser("~"), ".video_generator", "output")
                    os.makedirs(output_dir, exist_ok=True)
                    return output_dir
                except Exception:
                    pass
        else:
            # Running as script
            try:
                documents_path = os.path.join(os.path.expanduser("~"), "Documents")
                output_dir = os.path.join(documents_path, "Video Generator", "output")
                os.makedirs(output_dir, exist_ok=True)
                return output_dir
            except Exception:
                try:
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    output_dir = os.path.join(os.path.dirname(script_dir), "output")
                    os.makedirs(output_dir, exist_ok=True)
                    return output_dir
                except Exception:
                    pass

        # Final fallback - temp directory
        try:
            fallback_dir = os.path.join(tempfile.gettempdir(), "Video Generator", "output")
            os.makedirs(fallback_dir, exist_ok=True)
            return fallback_dir
        except Exception:
            return os.path.join(os.getcwd(), "output")

    def _migrate_hardcoded_paths(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate hardcoded paths to portable ones (silent)"""
        if settings.get('_migration_completed', False):
            return settings

        hardcoded_paths = [
            'C:/Generate/PythonCode/getContentGenerateVideo/output',
            'C:\\Generate\\PythonCode\\getContentGenerateVideo\\output',
            'C:/Generate/PythonCode/getContentGenerateVideo',
            'C:\\Generate\\PythonCode\\getContentGenerateVideo',
            'C:/Users/USER/Documents/XuanZhi9/Pictures/elon1',  # Known invalid path
        ]

        portable_output = self._get_default_output_folder()
        migrated_settings = settings.copy()
        migration_done = False

        def replace_hardcoded_in_dict(d):
            nonlocal migration_done
            if isinstance(d, dict):
                for key, value in d.items():
                    if isinstance(value, str):
                        for hardcoded in hardcoded_paths:
                            if value == hardcoded or value.startswith(hardcoded):
                                d[key] = portable_output
                                migration_done = True
                                break
                    elif isinstance(value, dict):
                        replace_hardcoded_in_dict(value)
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, str):
                                for hardcoded in hardcoded_paths:
                                    if item == hardcoded or item.startswith(hardcoded):
                                        value[i] = portable_output
                                        migration_done = True
                                        break
                            elif isinstance(item, dict):
                                replace_hardcoded_in_dict(item)

        replace_hardcoded_in_dict(migrated_settings)
        migrated_settings['_migration_completed'] = True

        return migrated_settings

    def _resolve_settings_path(self, settings_file: str) -> str:
        """Resolve settings file path for both development and PyInstaller executable"""
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            settings_path = os.path.join(exe_dir, settings_file)

            if not os.path.exists(settings_path):
                bundled_path = os.path.join(sys._MEIPASS, settings_file)
                if os.path.exists(bundled_path):
                    try:
                        import shutil
                        shutil.copy2(bundled_path, settings_path)
                    except Exception:
                        pass

            return settings_path
        else:
            return os.path.abspath(settings_file)

    def _validate_output_folder(self, folder_path: str) -> str:
        """Validate output folder exists, return valid path or default"""
        if folder_path and os.path.exists(folder_path):
            return folder_path
        # Return default if invalid (silently)
        return self._get_default_output_folder()

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file with caching (silent mode)"""
        try:
            if os.path.exists(self.settings_file):
                file_mtime = os.path.getmtime(self.settings_file)

                # Return cached if still valid
                if (self.settings_file in self._settings_cache and
                    self.settings_file in self._cache_timestamp and
                    self._cache_timestamp[self.settings_file] >= file_mtime):
                    return self._settings_cache[self.settings_file].copy()

                # Load from disk
                self._log(f"Loading settings from: {self.settings_file}")
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)

                # Ensure structure
                if 'shared_settings' not in saved_settings:
                    saved_settings['shared_settings'] = {}
                if 'image_tab_settings' not in saved_settings:
                    saved_settings['image_tab_settings'] = {}
                if 'video_tab_settings' not in saved_settings:
                    saved_settings['video_tab_settings'] = {}

                # Migrate paths (silent)
                migrated_settings = self._migrate_hardcoded_paths(saved_settings)

                # Validate output folder
                if 'output_folder' in migrated_settings:
                    migrated_settings['output_folder'] = self._validate_output_folder(
                        migrated_settings.get('output_folder', '')
                    )
                if 'shared_settings' in migrated_settings and 'output_folder' in migrated_settings['shared_settings']:
                    migrated_settings['shared_settings']['output_folder'] = self._validate_output_folder(
                        migrated_settings['shared_settings'].get('output_folder', '')
                    )

                # Save if migration changed anything
                if migrated_settings != saved_settings:
                    self._save_to_disk(migrated_settings)

                # Cache
                self._settings_cache[self.settings_file] = migrated_settings.copy()
                self._cache_timestamp[self.settings_file] = file_mtime
                return migrated_settings
            else:
                self._log(f"Settings file not found, using defaults")
                return self.default_settings.copy()

        except Exception as e:
            self._log(f"Error loading settings: {e}")
            return self.default_settings.copy()

    def _save_to_disk(self, settings: Dict[str, Any]) -> bool:
        """Internal save to disk (no debouncing, for migration)"""
        try:
            settings_dir = os.path.dirname(self.settings_file)
            if settings_dir:
                os.makedirs(settings_dir, exist_ok=True)

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            # Clear cache
            if self.settings_file in self._settings_cache:
                del self._settings_cache[self.settings_file]
            if self.settings_file in self._cache_timestamp:
                del self._cache_timestamp[self.settings_file]

            return True
        except Exception as e:
            self._log(f"Error saving settings: {e}")
            return False
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file with debouncing to prevent excessive writes"""
        try:
            # Normalize TTS speed
            if 'tts_speed' in settings:
                settings['tts_speed'] = round(float(settings['tts_speed']), 1)
            if 'shared_settings' in settings and 'tts_speed' in settings['shared_settings']:
                settings['shared_settings']['tts_speed'] = round(float(settings['shared_settings']['tts_speed']), 1)
            for tab_key in ['image_tab_settings', 'video_tab_settings']:
                if tab_key in settings and 'tts_speed' in settings[tab_key]:
                    settings[tab_key]['tts_speed'] = round(float(settings[tab_key]['tts_speed']), 1)

            # Debounce: skip if saved recently
            current_time = time.time()
            if current_time - self._last_save_time < self._save_debounce_seconds:
                # Update cache without saving to disk
                self._settings_cache[self.settings_file] = settings.copy()
                self._pending_save = settings.copy()
                self._log("Settings cached (debounced)")
                return True

            # Actually save
            self._last_save_time = current_time
            self._pending_save = None
            
            result = self._save_to_disk(settings)
            if result:
                self._log("Settings saved")
            return result

        except Exception as e:
            self._log(f"Error saving settings: {e}")
            return False

    def flush_pending_save(self):
        """Force save any pending settings (call on app exit)"""
        if self._pending_save is not None:
            self._save_to_disk(self._pending_save)
            self._pending_save = None

    @classmethod
    def clear_cache(cls):
        """Clear the settings cache"""
        cls._settings_cache.clear()
        cls._cache_timestamp.clear()

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

        # Fallback to defaults if empty
        if not tab_settings or len(tab_settings) < 2:
            tab_settings = {
                'tts_language': 'en',
                'tts_voice_actor': 'Guy',
                'tts_speed': 1.0,
                'tts_emotion': 'neutral',
                'output_folder': self._get_default_output_folder()
            }

        # Add tab-specific defaults
        if tab_name == 'image_tab':
            if 'image_fit_method' not in tab_settings:
                tab_settings['image_fit_method'] = 'contain'
            if 'aspect_ratio' not in tab_settings:
                tab_settings['aspect_ratio'] = '9:16 (Portrait)'
        elif tab_name == 'video_tab':
            if 'mute_original_audio' not in tab_settings:
                tab_settings['mute_original_audio'] = False
            if 'original_audio_volume' not in tab_settings:
                tab_settings['original_audio_volume'] = 0.7
            if 'subtitle_style' not in tab_settings:
                tab_settings['subtitle_style'] = 'modern_glow'

        return tab_settings

    def get_shared_settings(self):
        """Get shared settings (for Edge TTS + Kokoro TTS system)"""
        try:
            settings = self.load_settings()
            shared_settings = settings.get('shared_settings', {})

            if 'enabled_tts_providers' not in shared_settings:
                shared_settings.update({
                    'enabled_tts_providers': ['edge_tts', 'kokoro_tts'],
                    'tts_provider_priority': ['edge_tts', 'kokoro_tts'],
                    'prefer_offline_tts': False,
                    'tts_quality_threshold': 8,
                    'tts_fallback_enabled': True
                })

            return shared_settings
        except Exception:
            return self.default_settings

    def save_tab_settings(self, tab_name: str, tab_settings: Dict[str, Any]) -> bool:
        """Save settings specific to a tab with clean structure"""
        settings = self.load_settings()

        # Ensure structure
        if 'shared_settings' not in settings:
            settings['shared_settings'] = {}
        if 'image_tab_settings' not in settings:
            settings['image_tab_settings'] = {}
        if 'video_tab_settings' not in settings:
            settings['video_tab_settings'] = {}

        shared_keys = ['tts_language', 'tts_voice_actor', 'tts_speed', 'tts_emotion', 'output_folder']

        for key, value in tab_settings.items():
            if key in shared_keys:
                settings['shared_settings'][key] = value
                if key == 'output_folder':
                    settings['output_folder'] = value
            else:
                tab_key = f"{tab_name}_settings"
                settings[tab_key][key] = value

        return self.save_settings(settings)