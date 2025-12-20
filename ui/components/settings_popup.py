"""
Settings Popup Component - Reusable settings dialog for any tab
Leverages existing AudioSettings and UI Factory components to avoid duplication
Includes Edge TTS + Kokoro TTS settings
"""
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from utils.settings_manager import SettingsManager
import os

class SettingsPopup:
    """Reusable settings popup dialog that uses existing components"""

    def __init__(self, parent, title="Settings", main_gui=None, include_audio=True, include_output_folder=True, include_tts=True, include_speech_recognition=True, include_image_processing=False, include_audio_controls=True):
        self.parent = parent
        self.title = title
        self.main_gui = main_gui
        self.popup_window = None

        # Configuration options
        self.include_audio = include_audio
        self.include_output_folder = include_output_folder
        self.include_tts = include_tts
        self.include_speech_recognition = include_speech_recognition
        self.include_image_processing = include_image_processing
        self.include_audio_controls = include_audio_controls

        # Settings variables
        self.output_folder = tk.StringVar()

        # TTS settings variables
        self.tts_language = tk.StringVar()
        self.tts_voice_actor = tk.StringVar()
        self.tts_speed = tk.DoubleVar()
        self.tts_emotion = tk.StringVar()

        # Audio control variables (moved from legacy audio settings)
        self.mute_audio = tk.BooleanVar()
        self.audio_volume = tk.DoubleVar(value=0.7)

        # Image processing settings variables
        self.image_fit_method = tk.StringVar()
        self.aspect_ratio = tk.StringVar()

        # Speech recognition settings variables
        self.sr_enabled = tk.BooleanVar()
        self.sr_language = tk.StringVar()
        self.sr_model_path = tk.StringVar()

        # Content synchronization is now automatic - no UI variables needed

        # Reusable components
        self.audio_settings = None

        # Settings manager for persistence
        self.settings_manager = SettingsManager()

        # Callbacks
        self.on_settings_changed = None

        # Initialize default values
        if self.include_output_folder:
            self._initialize_output_folder()
        if self.include_tts:
            self._initialize_tts_settings()
        if self.include_image_processing:
            self._initialize_image_processing_settings()
        if self.include_speech_recognition:
            self._initialize_speech_recognition_settings()

        # Content sync is now automatic - no initialization needed
    
    def _initialize_output_folder(self):
        """Initialize the output folder with default value"""
        try:
            # Try to load from settings manager first
            settings = self.settings_manager.load_settings()
            if 'output_folder' in settings:
                self.output_folder.set(settings['output_folder'])
                return

            # Fallback to helper function
            from utils.helpers import get_output_directory
            default_folder = get_output_directory()
            self.output_folder.set(default_folder)
        except Exception as e:
            self.output_folder.set("Default (Auto)")

    def _initialize_tts_settings(self):
        """Initialize TTS settings with default values"""
        try:
            # Determine which tab we're configuring for
            tab_name = getattr(self, 'current_tab', 'image_tab')  # Default to image_tab

            # Get tab-specific settings
            tab_settings = self.settings_manager.get_tab_settings(tab_name)

            # Set shared TTS settings
            self.tts_language.set(tab_settings.get('tts_language', 'en'))
            self.tts_voice_actor.set(tab_settings.get('tts_voice_actor', 'Guy'))  # Direct assignment - no mapping needed
            self.tts_speed.set(tab_settings.get('tts_speed', 1.0))
            self.tts_emotion.set(tab_settings.get('tts_emotion', 'neutral'))

        except Exception as e:
            # Set defaults
            self.tts_language.set('en')
            self.tts_voice_actor.set('Default')
            self.tts_speed.set(1.0)
            self.tts_emotion.set('neutral')

    def _initialize_image_processing_settings(self):
        """Initialize image processing settings with default values"""
        try:
            # Determine which tab we're configuring for
            tab_name = getattr(self, 'current_tab', 'image_tab')  # Default to image_tab

            # Get tab-specific settings
            tab_settings = self.settings_manager.get_tab_settings(tab_name)

            # Set image processing settings
            self.image_fit_method.set(tab_settings.get('image_fit_method', 'cover'))
            self.aspect_ratio.set(tab_settings.get('aspect_ratio', '16:9 (Landscape)'))

        except Exception as e:
            # Set defaults
            self.image_fit_method.set('cover')
            self.aspect_ratio.set('16:9 (Landscape)')

    def _initialize_speech_recognition_settings(self):
        """Initialize speech recognition settings with default values"""
        try:
            settings = self.settings_manager.load_settings()
            self.sr_enabled.set(settings.get('sr_enabled', False))
            self.sr_language.set(settings.get('sr_language', 'en-us'))
            self.sr_model_path.set(settings.get('sr_model_path', ''))
        except Exception as e:
            # Set defaults
            self.sr_enabled.set(False)
            self.sr_language.set('en-us')
            self.sr_model_path.set('')



    def show(self):
        """Show the settings popup dialog"""
        if self.popup_window and self.popup_window.winfo_exists():
            # Popup already exists, bring it to front
            self.popup_window.lift()
            self.popup_window.focus_set()
            return
        
        # Create popup window
        self.popup_window = tk.Toplevel(self.parent)
        self.popup_window.title(self.title)
        
        # Dynamic sizing based on included components
        height = 250  # Increased base height to ensure buttons are visible
        if self.include_output_folder:
            height += 120
        # Legacy audio section removed - audio controls moved to TTS section
        if self.include_tts:
            if self.include_audio_controls:
                height += 200  # TTS section with audio controls
            else:
                height += 160  # TTS section without audio controls (image tab)
        if self.include_image_processing:
            height += 150  # Image processing section height (fit method + aspect ratio)
        if self.include_speech_recognition:
            height += 150
        # Content sync is now automatic - no extra height needed

        self.popup_window.geometry(f"600x{height}")
        self.popup_window.resizable(False, False)
        
        # Make it modal
        self.popup_window.transient(self.parent)
        self.popup_window.grab_set()
        
        # Center the popup
        self._center_popup()
        
        # Create the content
        self._create_popup_content()
        
        # Apply any current settings after components are created
        if hasattr(self, '_pending_settings'):
            self.set_settings(self._pending_settings)
            delattr(self, '_pending_settings')
        
        # Handle close events
        self.popup_window.protocol("WM_DELETE_WINDOW", self.close)
    
    def _center_popup(self):
        """Center the popup on the parent window"""
        self.popup_window.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get popup size
        popup_width = self.popup_window.winfo_reqwidth()
        popup_height = self.popup_window.winfo_reqheight()
        
        # Calculate center position
        x = parent_x + (parent_width // 2) - (popup_width // 2)
        y = parent_y + (parent_height // 2) - (popup_height // 2)
        
        self.popup_window.geometry(f"+{x}+{y}")
    
    def _create_popup_content(self):
        """Create the content of the settings popup"""
        # Main container with padding
        main_frame = ttk.Frame(self.popup_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text=f"⚙️ {self.title}",
            font=("Cascadia Code", 12, "bold")
        )
        title_label.pack(anchor="w", pady=(0, 15))
        
        # Create sections based on configuration
        if self.include_output_folder:
            self._create_output_folder_section(main_frame)

        # Legacy audio section removed - audio controls moved to TTS section

        if self.include_tts:
            self._create_tts_section(main_frame)

        if self.include_image_processing:
            self._create_image_processing_section(main_frame)

        if self.include_speech_recognition:
            self._create_speech_recognition_section(main_frame)

        # Content synchronization is now automatic - no UI needed

        # Buttons
        self._create_buttons(main_frame)
    
    def _create_output_folder_section(self, parent):
        """Create output folder selection section using UI factory"""
        if self.main_gui and hasattr(self.main_gui, 'ui_factory'):
            # Use existing UI factory component to avoid duplication
            output_frame, output_var = self.main_gui.ui_factory.create_output_folder_section(
                parent, "📁 Output Folder"
            )
            output_frame.pack(fill="x", pady=(0, 15))
            
            # Sync with our internal variable
            self.output_folder = output_var
        else:
            # Fallback simple implementation
            output_frame = ttk.LabelFrame(parent, text="📁 Output Folder", padding=15)
            output_frame.pack(fill="x", pady=(0, 15))
            
            # Simple path display and browse
            path_row = ttk.Frame(output_frame)
            path_row.pack(fill="x")
            
            path_entry = ttk.Entry(
                path_row,
                textvariable=self.output_folder,
                state="readonly",
                font=("Cascadia Code", 10)
            )
            path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            browse_button = ttk.Button(
                path_row,
                text="📂 Browse",
                command=self._browse_output_folder,
                width=12
            )
            browse_button.pack(side="right")
    
    # Legacy audio section removed - audio controls moved to TTS section

    def _create_tts_section(self, parent):
        """Create TTS (Text-to-Speech) settings section"""
        tts_frame = ttk.LabelFrame(parent, text="🎤 Text-to-Speech (Edge TTS + Kokoro TTS)", padding=15)
        tts_frame.pack(fill="x", pady=(0, 15))

        # Language selection
        lang_row = ttk.Frame(tts_frame)
        lang_row.pack(fill="x", pady=(0, 10))

        ttk.Label(lang_row, text="Language:", font=("Cascadia Code", 10)).pack(side="left")

        language_combo = ttk.Combobox(
            lang_row,
            textvariable=self.tts_language,
            values=["en", "en-us", "en-uk", "en-au"],  # Simplified to essential English variants
            state="readonly",
            width=15
        )
        language_combo.pack(side="left", padx=(10, 0))

        # Auto-save when language changes
        language_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)

        # Voice actor selection
        voice_row = ttk.Frame(tts_frame)
        voice_row.pack(fill="x", pady=(0, 10))

        ttk.Label(voice_row, text="Voice Actor:", font=("Cascadia Code", 10)).pack(side="left")

        voice_combo = ttk.Combobox(
            voice_row,
            textvariable=self.tts_voice_actor,
            values=["Guy", "Connor", "Aria", "Michael", "Adam", "Heart"],
            state="readonly",
            width=25
        )
        voice_combo.pack(side="left", padx=(10, 0))

        # Auto-save when voice changes
        voice_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)

        # Speed control
        speed_row = ttk.Frame(tts_frame)
        speed_row.pack(fill="x", pady=(0, 10))

        ttk.Label(speed_row, text="Speed:", font=("Cascadia Code", 10)).pack(side="left")

        speed_scale = ttk.Scale(
            speed_row,
            from_=0.5,
            to=2.0,
            variable=self.tts_speed,
            orient="horizontal",
            length=200
        )
        speed_scale.pack(side="left", padx=(10, 10))

        speed_label = ttk.Label(speed_row, text="1.0x", font=("Cascadia Code", 9))
        speed_label.pack(side="left")

        # Update speed label when scale changes and auto-save
        def update_speed_label(*args):
            # Round speed to 1 decimal place to avoid floating point precision issues
            rounded_speed = round(self.tts_speed.get(), 1)
            self.tts_speed.set(rounded_speed)  # Update the variable with rounded value
            speed_label.config(text=f"{rounded_speed:.1f}x")
            self._on_setting_changed()  # Auto-save when speed changes
        self.tts_speed.trace_add("write", update_speed_label)

        # Emotion selection
        emotion_row = ttk.Frame(tts_frame)
        emotion_row.pack(fill="x")

        ttk.Label(emotion_row, text="Emotion:", font=("Cascadia Code", 10)).pack(side="left")

        emotion_combo = ttk.Combobox(
            emotion_row,
            textvariable=self.tts_emotion,
            values=["neutral", "excited", "dramatic", "calm", "energetic"],
            state="readonly",
            width=15
        )
        emotion_combo.pack(side="left", padx=(10, 0))

        # Auto-save when emotion changes
        emotion_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)

        # Audio controls section (only for video tab) - compact layout
        if self.include_audio_controls:
            audio_controls_frame = ttk.Frame(tts_frame)
            audio_controls_frame.pack(fill="x", pady=(10, 0))

            # Separator line
            separator = ttk.Separator(audio_controls_frame, orient="horizontal")
            separator.pack(fill="x", pady=(0, 5))

            # Compact audio controls in single row
            audio_row = ttk.Frame(audio_controls_frame)
            audio_row.pack(fill="x", pady=(0, 5))

            # Mute audio checkbox (left side)
            mute_checkbox = ttk.Checkbutton(
                audio_row,
                text="Mute Audio",
                variable=self.mute_audio,
                command=lambda: [self._on_mute_change(), self._on_setting_changed()]
            )
            mute_checkbox.pack(side="left")

            # Volume control (right side) - more compact
            ttk.Label(audio_row, text="Volume:", font=("Cascadia Code", 10)).pack(side="left", padx=(20, 5))

            self.volume_scale = ttk.Scale(
                audio_row,
                from_=0.0,
                to=1.0,
                variable=self.audio_volume,
                orient="horizontal",
                length=150,
                command=self._on_volume_change
            )
            self.volume_scale.pack(side="left", padx=(0, 5))

            self.volume_label = ttk.Label(audio_row, text="70%", font=("Cascadia Code", 9))
            self.volume_label.pack(side="left")

            # Initialize volume state
            self._update_volume_state()

    def _create_image_processing_section(self, parent):
        """Create Image Processing settings section"""
        img_frame = ttk.LabelFrame(parent, text="🖼️ Image Processing", padding=15)
        img_frame.pack(fill="x", pady=(0, 15))

        # Image fit method selection
        fit_row = ttk.Frame(img_frame)
        fit_row.pack(fill="x", pady=(0, 10))

        ttk.Label(fit_row, text="Image Fit Method:", font=("Cascadia Code", 10)).pack(side="left")

        fit_combo = ttk.Combobox(
            fit_row,
            textvariable=self.image_fit_method,
            values=["cover", "contain", "stretch"],
            state="readonly",
            width=15
        )
        fit_combo.pack(side="left", padx=(10, 0))

        # Auto-save when image fit method changes
        fit_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)

        # Aspect ratio presets
        aspect_row = ttk.Frame(img_frame)
        aspect_row.pack(fill="x", pady=(10, 0))

        ttk.Label(aspect_row, text="Aspect Ratio:", font=("Cascadia Code", 10)).pack(side="left")

        aspect_combo = ttk.Combobox(
            aspect_row,
            textvariable=self.aspect_ratio,
            values=["16:9 (Landscape)", "9:16 (Portrait)", "1:1 (Square)", "4:3 (Classic)", "21:9 (Ultrawide)"],
            state="readonly",
            width=20
        )
        aspect_combo.pack(side="left", padx=(10, 0))

        # Auto-save when aspect ratio changes
        aspect_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)

    def _create_speech_recognition_section(self, parent):
        """Speech recognition section removed - using only Whisper-timestamped"""
        # Note: Speech recognition settings removed as we now use only Whisper-timestamped
        # which is automatically configured and doesn't need user settings
        pass

    def _create_buttons(self, parent):
        """Create OK and Cancel buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="❌ Cancel",
            command=self.close,
            width=12
        )
        cancel_button.pack(side="right", padx=(10, 0))
        
        # OK button
        ok_button = ttk.Button(
            button_frame,
            text="✅ Apply",
            command=self._apply_settings,
            width=12
        )
        ok_button.pack(side="right")
        
        # Reset button
        reset_button = ttk.Button(
            button_frame,
            text="🔄 Reset",
            command=self._reset_settings,
            width=12
        )
        reset_button.pack(side="left")
    
    def _browse_output_folder(self):
        """Browse for output folder"""
        current_folder = self.output_folder.get()
        if current_folder == "Default (Auto)":
            initial_dir = None
        else:
            initial_dir = current_folder
        
        folder_path = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=initial_dir
        )
        if folder_path:
            self.output_folder.set(folder_path)
            if self.main_gui:
                self.main_gui.log(f"Output folder changed to: {folder_path}")

    # Speech recognition methods removed - using only Whisper-timestamped

    def _on_mute_change(self):
        """Handle mute setting change"""
        self._update_volume_state()

    def _on_volume_change(self, value):
        """Handle volume change"""
        if not self.mute_audio.get():
            volume_value = float(value)
            self.volume_label.config(text=f"{int(volume_value * 100)}%")

    def _update_volume_state(self):
        """Update volume controls based on mute state"""
        is_muted = self.mute_audio.get()

        if is_muted:
            self.volume_scale.config(state="disabled")
            self.volume_label.config(text="Muted", foreground="gray")
        else:
            self.volume_scale.config(state="normal")
            volume_value = self.audio_volume.get()
            self.volume_label.config(text=f"{int(volume_value * 100)}%", foreground="black")
    
    def _apply_settings(self):
        """Apply the settings and close popup"""
        settings = self.get_settings()

        # Determine which tab we're configuring for
        tab_name = getattr(self, 'current_tab', 'image_tab')  # Default to image_tab

        # Save tab-specific settings with error handling
        try:
            success = self.settings_manager.save_tab_settings(tab_name, settings)

            if success:
                if self.on_settings_changed:
                    self.on_settings_changed(settings)

                # Only log if main_gui exists, keep message concise
                # Removed verbose per-tab logging

                self.close()
            else:
                # Settings save failed
                if self.main_gui:
                    self.main_gui.log(f"ERROR: Failed to save settings for {tab_name.replace('_', ' ').title()}")

                # Show error dialog
                from utils.error_helpers import show_error_with_log
                show_error_with_log(
                    self.main_gui,
                    "Settings Save Error",
                    "Failed to save settings. Please check file permissions and try again.",
                    Exception("Settings save operation returned False")
                )
        except Exception as e:
            # Exception during settings save
            if self.main_gui:
                self.main_gui.log(f"ERROR: Exception while saving settings for {tab_name.replace('_', ' ').title()}: {e}")

            # Show error dialog
            from utils.error_helpers import show_error_with_log
            show_error_with_log(
                self.main_gui,
                "Settings Save Error",
                "An error occurred while saving settings.",
                e
            )
    
    def _reset_settings(self):
        """Reset settings to defaults"""
        # Get default settings from settings manager
        default_settings = self.settings_manager.default_settings

        if self.include_output_folder:
            self.output_folder.set(default_settings.get('output_folder', 'Default (Auto)'))

        # Legacy audio section removed - audio controls moved to TTS section

        if self.include_tts:
            self.tts_language.set(default_settings.get('tts_language', 'en'))
            self.tts_voice_actor.set(default_settings.get('tts_voice_actor', 'Guy'))  # Direct assignment - no mapping needed
            self.tts_speed.set(default_settings.get('tts_speed', 1.0))
            self.tts_emotion.set(default_settings.get('tts_emotion', 'neutral'))
            # Reset audio controls only if included (video tab)
            if self.include_audio_controls:
                # Check both new and legacy setting names for defaults
                mute_default = default_settings.get('mute_original_audio', default_settings.get('mute', False))
                volume_default = default_settings.get('original_audio_volume', default_settings.get('volume', 0.7))
                self.mute_audio.set(mute_default)
                self.audio_volume.set(volume_default)
                if hasattr(self, 'volume_scale'):
                    self._update_volume_state()

        # Speech recognition settings removed - using only Whisper-timestamped

        # Content sync settings are automatic - no reset needed

        if self.main_gui:
            self.main_gui.log("Settings reset to defaults")
    
    def get_settings(self):
        """Get all current settings"""
        settings = {}

        if self.include_output_folder:
            settings['output_folder'] = self.output_folder.get()

        # Legacy audio section removed - audio controls moved to TTS section

        if self.include_tts:
            settings['tts_language'] = self.tts_language.get()
            settings['tts_voice_actor'] = self.tts_voice_actor.get()  # Direct assignment - no mapping needed
            settings['tts_speed'] = self.tts_speed.get()
            settings['tts_emotion'] = self.tts_emotion.get()
            # Include audio controls only if included (video tab)
            if self.include_audio_controls:
                settings['mute'] = self.mute_audio.get()
                settings['volume'] = self.audio_volume.get()

        if self.include_image_processing:
            settings['image_fit_method'] = self.image_fit_method.get()
            settings['aspect_ratio'] = self.aspect_ratio.get()

        if self.include_speech_recognition:
            settings['sr_enabled'] = self.sr_enabled.get()
            settings['sr_language'] = self.sr_language.get()
            settings['sr_model_path'] = self.sr_model_path.get()

        # Content sync settings are now automatic - handled by defaults

        return settings

    def _map_display_voice_to_actual(self, display_voice: str) -> str:
        """Map display voice names to actual voice names for TTS (now simplified - no mapping needed)"""
        # Since we simplified the display names, they match the actual names
        return display_voice if display_voice in ["Guy", "Connor", "Aria", "Michael", "Adam", "Heart"] else "Guy"

    def _map_actual_voice_to_display(self, actual_voice: str) -> str:
        """Map actual voice names to display names for UI (now simplified - no mapping needed)"""
        # Since we simplified the display names, they match the actual names
        return actual_voice if actual_voice in ["Guy", "Connor", "Aria", "Michael", "Adam", "Heart"] else "Guy"

    def _on_setting_changed(self, event=None):
        """Auto-save settings when any setting changes"""
        try:
            # Get current settings
            current_settings = self.get_settings()

            # Save to settings manager
            self.settings_manager.save_settings(current_settings)

            # Update the current tab's settings immediately
            if hasattr(self, 'current_tab'):
                self.settings_manager.save_tab_settings(self.current_tab, current_settings)

            # Silent save - no logging on each change
        except Exception:
            pass  # Silent fail on auto-save

    def set_settings(self, settings=None):
        """Set settings from dictionary"""
        if settings is None:
            # Load from settings manager if no settings provided
            settings = self.settings_manager.load_settings()

        # If components aren't created yet, store settings for later
        if not hasattr(self, 'popup_window') or not self.popup_window:
            self._pending_settings = settings
            return

        if self.include_output_folder and 'output_folder' in settings:
            self.output_folder.set(settings['output_folder'])

        # Legacy audio section removed - audio controls moved to TTS section

        if self.include_tts:
            if 'tts_language' in settings:
                self.tts_language.set(settings['tts_language'])
            if 'tts_voice_actor' in settings:
                self.tts_voice_actor.set(settings['tts_voice_actor'])
            if 'tts_speed' in settings:
                self.tts_speed.set(settings['tts_speed'])
            if 'tts_emotion' in settings:
                self.tts_emotion.set(settings['tts_emotion'])
            # Set audio controls only if included (video tab)
            if self.include_audio_controls:
                # Check both new and legacy mute setting names
                if 'mute' in settings:
                    self.mute_audio.set(settings['mute'])
                elif 'mute_original_audio' in settings:
                    self.mute_audio.set(settings['mute_original_audio'])

                if 'volume' in settings:
                    self.audio_volume.set(settings['volume'])
                elif 'original_audio_volume' in settings:
                    self.audio_volume.set(settings['original_audio_volume'])

                # Update volume state after setting values
                if hasattr(self, 'volume_scale'):
                    self._update_volume_state()

        if self.include_image_processing:
            if 'image_fit_method' in settings:
                self.image_fit_method.set(settings['image_fit_method'])
            if 'aspect_ratio' in settings:
                self.aspect_ratio.set(settings['aspect_ratio'])

        # Speech recognition settings removed - using only Whisper-timestamped

        # Content sync settings are automatic - no UI controls to set
    
    def set_callback(self, callback):
        """Set callback function for when settings are applied"""
        self.on_settings_changed = callback
    
    def close(self):
        """Close the popup"""
        if self.popup_window:
            self.popup_window.grab_release()
            self.popup_window.destroy()
            self.popup_window = None

# Convenience functions for different popup configurations
def show_settings_popup(parent, title="Settings", main_gui=None, current_settings=None,
                       callback=None, include_audio=True, include_output_folder=True,
                       include_tts=True, include_speech_recognition=False, include_image_processing=False,
                       include_audio_controls=True, current_tab="image_tab"):
    """
    Convenience function to create and show a customizable settings popup

    Args:
        parent: Parent window
        title: Popup title
        main_gui: Reference to main GUI for logging and UI factory access
        current_settings: Dictionary of current settings to load
        callback: Function to call when settings are applied
        include_audio: Whether to include audio settings section
        include_output_folder: Whether to include output folder section
        include_tts: Whether to include TTS settings section
        include_speech_recognition: Whether to include speech recognition settings section
        include_image_processing: Whether to include image processing settings section
        include_audio_controls: Whether to include mute/volume controls in TTS section

    Returns:
        SettingsPopup: The created popup instance
    """
    popup = SettingsPopup(parent, title, main_gui, include_audio, include_output_folder,
                         include_tts, include_speech_recognition, include_image_processing, include_audio_controls)

    # Set the current tab for tab-specific settings
    popup.current_tab = current_tab

    # Set current settings before showing (will be stored as pending if needed)
    if current_settings:
        popup.set_settings(current_settings)

    if callback:
        popup.set_callback(callback)

    # Show the popup (this will apply pending settings after components are created)
    popup.show()
    return popup

def show_audio_settings_popup(parent, main_gui=None, current_settings=None, callback=None):
    """Show audio-only settings popup"""
    return show_settings_popup(
        parent, "Audio Settings", main_gui, current_settings, callback, 
        include_audio=True, include_output_folder=False
    )

def show_output_settings_popup(parent, main_gui=None, current_settings=None, callback=None):
    """Show output folder-only settings popup"""
    return show_settings_popup(
        parent, "Output Settings", main_gui, current_settings, callback,
        include_audio=False, include_output_folder=True
    ) 