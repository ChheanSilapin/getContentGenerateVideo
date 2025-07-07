"""
Settings Manager - Handle persistent storage of user settings
Saves settings to a JSON file so they persist between sessions
"""
import json
import os
import sys
from typing import Dict, Any


class SettingsManager:
    """Manage persistent storage of application settings"""

    # Class-level cache to avoid redundant file reads
    _settings_cache = {}
    _cache_timestamp = {}

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

    def _get_default_output_folder(self) -> str:
        """Get a portable default output folder that works for any user"""
        import tempfile
        import os
        import platform

        # Use the same logic as get_app_data_dir but avoid circular imports
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            if platform.system() == "Windows":
                # Try AppData\Local first
                try:
                    appdata_local = os.environ.get('LOCALAPPDATA')
                    if appdata_local:
                        app_data_dir = os.path.join(appdata_local, "Video Generator")
                        os.makedirs(app_data_dir, exist_ok=True)
                        output_dir = os.path.join(app_data_dir, "output")
                        os.makedirs(output_dir, exist_ok=True)
                        return output_dir
                except Exception:
                    pass

                # Fallback to Documents folder
                try:
                    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
                    app_data_dir = os.path.join(documents_path, "Video Generator")
                    os.makedirs(app_data_dir, exist_ok=True)
                    output_dir = os.path.join(app_data_dir, "output")
                    os.makedirs(output_dir, exist_ok=True)
                    return output_dir
                except Exception:
                    pass
            else:
                # Use home directory on other systems
                try:
                    app_data_dir = os.path.join(os.path.expanduser("~"), ".video_generator")
                    os.makedirs(app_data_dir, exist_ok=True)
                    output_dir = os.path.join(app_data_dir, "output")
                    os.makedirs(output_dir, exist_ok=True)
                    return output_dir
                except Exception:
                    pass
        else:
            # Running as script - use a portable approach even in development
            # First try to use a user-specific directory
            try:
                # Try user's Documents folder first
                documents_path = os.path.join(os.path.expanduser("~"), "Documents")
                app_data_dir = os.path.join(documents_path, "Video Generator")
                os.makedirs(app_data_dir, exist_ok=True)
                output_dir = os.path.join(app_data_dir, "output")
                os.makedirs(output_dir, exist_ok=True)
                return output_dir
            except Exception:
                # Fallback to current directory only if Documents fails
                try:
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    app_data_dir = os.path.dirname(script_dir)  # Go up one level from utils/
                    output_dir = os.path.join(app_data_dir, "output")
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
            # Last resort - use current directory
            return os.path.join(os.getcwd(), "output")

    def _migrate_hardcoded_paths(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate hardcoded paths to portable ones"""
        # Check if migration has already been completed
        if settings.get('_migration_completed', False):
            # Migration already done, don't migrate again (respect user's manual changes)
            return settings

        # Known hardcoded paths that need to be replaced
        hardcoded_paths = [
            'C:/Generate/PythonCode/getContentGenerateVideo/output',
            'C:\\Generate\\PythonCode\\getContentGenerateVideo\\output',
            'C:/Generate/PythonCode/getContentGenerateVideo',
            'C:\\Generate\\PythonCode\\getContentGenerateVideo'
        ]

        # Get the portable replacement
        portable_output = self._get_default_output_folder()

        # Create a copy to avoid modifying the original
        migrated_settings = settings.copy()

        # Function to recursively replace hardcoded paths
        def replace_hardcoded_in_dict(d):
            if isinstance(d, dict):
                for key, value in d.items():
                    if isinstance(value, str):
                        # Check if this value is a hardcoded path
                        for hardcoded in hardcoded_paths:
                            if value == hardcoded or value.startswith(hardcoded):
                                print(f"Migrating hardcoded path: {value} -> {portable_output}")
                                d[key] = portable_output
                                break
                    elif isinstance(value, dict):
                        replace_hardcoded_in_dict(value)
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, str):
                                for hardcoded in hardcoded_paths:
                                    if item == hardcoded or item.startswith(hardcoded):
                                        print(f"Migrating hardcoded path in list: {item} -> {portable_output}")
                                        value[i] = portable_output
                                        break
                            elif isinstance(item, dict):
                                replace_hardcoded_in_dict(item)

        # Apply the migration
        replace_hardcoded_in_dict(migrated_settings)

        # Mark migration as completed so it doesn't run again
        migrated_settings['_migration_completed'] = True

        return migrated_settings

    def _resolve_settings_path(self, settings_file: str) -> str:
        """Resolve settings file path for both development and PyInstaller executable"""
        # For PyInstaller executable
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            # Save settings in the same directory as the executable
            exe_dir = os.path.dirname(sys.executable)
            settings_path = os.path.join(exe_dir, settings_file)

            # If settings don't exist in exe directory, try to copy from bundled version
            if not os.path.exists(settings_path):
                bundled_path = os.path.join(sys._MEIPASS, settings_file)
                if os.path.exists(bundled_path):
                    try:
                        import shutil
                        shutil.copy2(bundled_path, settings_path)
                        print(f"Copied bundled settings to: {settings_path}")
                    except Exception as e:
                        print(f"Could not copy bundled settings: {e}")

            return settings_path
        else:
            # Running in development - use current directory
            return os.path.abspath(settings_file)

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file with caching to avoid redundant reads"""
        try:
            # Check if file exists and get modification time
            if os.path.exists(self.settings_file):
                file_mtime = os.path.getmtime(self.settings_file)

                # Check cache
                if (self.settings_file in self._settings_cache and
                    self.settings_file in self._cache_timestamp and
                    self._cache_timestamp[self.settings_file] >= file_mtime):
                    # Return cached settings (no print to reduce log spam)
                    return self._settings_cache[self.settings_file].copy()

                # File changed or not cached, load from disk
                print(f"Loading settings from: {self.settings_file}")
                print(f"Settings file found, loading...")
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

                    # Migrate hardcoded paths before caching
                    migrated_settings = self._migrate_hardcoded_paths(saved_settings)

                    # If migration changed anything, save the migrated settings
                    if migrated_settings != saved_settings:
                        print("Saving migrated settings to make changes permanent...")
                        self.save_settings(migrated_settings)

                    # Cache the migrated settings
                    self._settings_cache[self.settings_file] = migrated_settings.copy()
                    self._cache_timestamp[self.settings_file] = file_mtime
                    return migrated_settings
                else:
                    # Legacy structure - merge with defaults for backward compatibility
                    settings = self.default_settings.copy()
                    settings.update(saved_settings)

                    # Migrate hardcoded paths before caching
                    migrated_settings = self._migrate_hardcoded_paths(settings)

                    # If migration changed anything, save the migrated settings
                    if migrated_settings != settings:
                        print("Saving migrated settings to make changes permanent...")
                        self.save_settings(migrated_settings)

                    # Cache the migrated settings
                    self._settings_cache[self.settings_file] = migrated_settings.copy()
                    self._cache_timestamp[self.settings_file] = file_mtime
                    return migrated_settings
            else:
                print(f"Settings file not found at: {self.settings_file}")
                print("Using default settings")
                return self.default_settings.copy()

        except Exception as e:
            print(f"Error loading settings from {self.settings_file}: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file and clear cache"""
        try:
            print(f"Saving settings to: {self.settings_file}")
            # Ensure directory exists (only if there is a directory part)
            settings_dir = os.path.dirname(self.settings_file)
            if settings_dir:  # Only create directory if there is one
                os.makedirs(settings_dir, exist_ok=True)

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            # Clear cache to ensure fresh load next time
            if self.settings_file in self._settings_cache:
                del self._settings_cache[self.settings_file]
            if self.settings_file in self._cache_timestamp:
                del self._cache_timestamp[self.settings_file]

            print(f"Settings saved successfully to: {self.settings_file}")
            return True

        except Exception as e:
            print(f"Error saving settings to {self.settings_file}: {e}")
            return False

    @classmethod
    def clear_cache(cls):
        """Clear the settings cache (useful for testing or when settings change externally)"""
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

        # Fallback to defaults if no settings found
        if not tab_settings or len(tab_settings) < 2:
            # Use defaults from default_settings
            tab_settings = {
                'tts_language': 'en',
                'tts_voice_actor': 'Guy',
                'tts_speed': 1.0,
                'tts_emotion': 'neutral',
                'output_folder': self.default_settings.get('output_folder', self._get_default_output_folder())
            }

        # Always ensure tab-specific defaults are present
        if tab_name == 'image_tab':
            # Add image-specific defaults if not present
            if 'image_fit_method' not in tab_settings:
                tab_settings['image_fit_method'] = self.default_settings.get('image_fit_method', 'contain')
            if 'aspect_ratio' not in tab_settings:
                tab_settings['aspect_ratio'] = self.default_settings.get('aspect_ratio', '9:16 (Portrait)')
        elif tab_name == 'video_tab':
            # Add video-specific defaults if not present
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

            # Add modern TTS defaults if not present
            if 'enabled_tts_providers' not in shared_settings:
                shared_settings.update({
                    'enabled_tts_providers': ['edge_tts', 'kokoro_tts'],
                    'tts_provider_priority': ['edge_tts', 'kokoro_tts'],
                    'prefer_offline_tts': False,  # Edge TTS requires internet, Kokoro is offline
                    'tts_quality_threshold': 8,   # Higher quality threshold for neural voices
                    'tts_fallback_enabled': True
                })

            return shared_settings
        except Exception as e:
            print(f"Warning: Could not load shared settings: {e}")
            return self.default_settings

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