"""
Settings Popup Component - Reusable settings dialog for any tab
Leverages existing AudioSettings and UI Factory components to avoid duplication
"""
from utils.common_imports import tk, messagebox, ttk, filedialog
from .audio_settings import AudioSettings
from utils.settings_manager import SettingsManager
import os

class SettingsPopup:
    """Reusable settings popup dialog that uses existing components"""
    
    def __init__(self, parent, title="Settings", main_gui=None, include_audio=True, include_output_folder=True):
        self.parent = parent
        self.title = title
        self.main_gui = main_gui
        self.popup_window = None
        
        # Configuration options
        self.include_audio = include_audio
        self.include_output_folder = include_output_folder
        
        # Settings variables
        self.output_folder = tk.StringVar()
        
        # Reusable components
        self.audio_settings = None
        
        # Settings manager for persistence
        self.settings_manager = SettingsManager()
        
        # Callbacks
        self.on_settings_changed = None
        
        # Initialize default values
        if self.include_output_folder:
            self._initialize_output_folder()
    
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
        height = 200  # Base height
        if self.include_output_folder:
            height += 120
        if self.include_audio:
            height += 200
            
        self.popup_window.geometry(f"520x{height}")
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
        
        if self.include_audio:
            self._create_audio_section(main_frame)
        
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
    
    def _create_audio_section(self, parent):
        """Create audio settings section using existing AudioSettings component"""
        # Create container for the audio settings
        audio_container = ttk.Frame(parent)
        audio_container.pack(fill="x", pady=(0, 15))
        
        # Use existing AudioSettings component to avoid duplication
        self.audio_settings = AudioSettings(audio_container, "🔊 Audio Settings")
        self.audio_settings.pack(fill="x")
    
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
    
    def _apply_settings(self):
        """Apply the settings and close popup"""
        settings = self.get_settings()
        
        # Save settings using settings manager
        self.settings_manager.save_settings(settings)
        
        if self.on_settings_changed:
            self.on_settings_changed(settings)
        
        if self.main_gui:
            self.main_gui.log("Settings applied successfully")
        
        self.close()
    
    def _reset_settings(self):
        """Reset settings to defaults"""
        # Get default settings from settings manager
        default_settings = self.settings_manager.default_settings
        
        if self.include_output_folder:
            self.output_folder.set(default_settings.get('output_folder', 'Default (Auto)'))
        
        if self.include_audio and self.audio_settings:
            # Reset audio settings to defaults
            self.audio_settings.set_settings({
                'voice_actor': default_settings.get('voice_actor', 'Default'),
                'speed': default_settings.get('speed', 0.8),
                'emotion': default_settings.get('emotion', 'neutral'),
                'mute': default_settings.get('mute', False),
                'volume': default_settings.get('volume', 0.7)
            })
        
        if self.main_gui:
            self.main_gui.log("Settings reset to defaults")
    
    def get_settings(self):
        """Get all current settings"""
        settings = {}
        
        if self.include_output_folder:
            settings['output_folder'] = self.output_folder.get()
        
        if self.include_audio and self.audio_settings:
            audio_settings = self.audio_settings.get_settings()
            settings.update(audio_settings)
        
        return settings
    
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
        
        if self.include_audio and self.audio_settings:
            # Filter out non-audio settings
            audio_keys = ['voice_actor', 'speed', 'emotion', 'mute', 'volume']
            audio_settings = {k: v for k, v in settings.items() if k in audio_keys}
            if audio_settings:
                self.audio_settings.set_settings(audio_settings)
    
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
                       callback=None, include_audio=True, include_output_folder=True):
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
    
    Returns:
        SettingsPopup: The created popup instance
    """
    popup = SettingsPopup(parent, title, main_gui, include_audio, include_output_folder)
    
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