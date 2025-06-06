"""
Audio Settings Component - Reusable audio configuration UI
Extracted from video_tab.py for reusability across different tabs
"""
from utils.common_imports import tk, ttk

class AudioSettings:
    """Reusable audio settings component with voice, speed, and volume controls"""
    
    def __init__(self, parent, title="Audio Settings"):
        self.parent = parent
        self.title = title
        
        # Audio variables
        self.voice_actor_var = tk.StringVar()
        self.speed_var = tk.DoubleVar(value=0.8)
        self.emotion_var = tk.StringVar()
        self.mute_var = tk.BooleanVar(value=False)
        self.volume_var = tk.DoubleVar(value=0.7)
        
        # UI components
        self.main_frame = None
        self.speed_label = None
        self.volume_label = None
        
        # Callbacks
        self.on_mute_changed = None
        self.on_volume_changed = None
        
        self.create_audio_settings()
    
    def create_audio_settings(self):
        """Create the audio settings UI"""
        self.main_frame = ttk.LabelFrame(self.parent, text=self.title, padding=10)
        
        # Voice Actor selection
        voice_frame = ttk.Frame(self.main_frame)
        voice_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(voice_frame, text="Voice Actor:").pack(side="left")
        
        voice_combo = ttk.Combobox(
            voice_frame,
            textvariable=self.voice_actor_var,
            values=[
                "Default", "Male 1", "Male 2", "Female 1", "Female 2",
                "Child", "Robot", "Narrator", "Custom"
            ],
            state="readonly",
            width=15
        )
        voice_combo.set("Default")
        voice_combo.pack(side="left", padx=(10, 0))
        
        # Emotion selection
        emotion_frame = ttk.Frame(self.main_frame)
        emotion_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(emotion_frame, text="Emotion:").pack(side="left")
        
        emotion_combo = ttk.Combobox(
            emotion_frame,
            textvariable=self.emotion_var,
            values=["neutral", "excited", "calm", "dramatic", "energetic"],
            state="readonly",
            width=15
        )
        emotion_combo.set("neutral")
        emotion_combo.pack(side="left", padx=(10, 0))
        
        # Speed control
        speed_frame = ttk.Frame(self.main_frame)
        speed_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(speed_frame, text="Speed:").pack(side="left")
        
        self.speed_label = ttk.Label(speed_frame, text="0.8x")
        self.speed_label.pack(side="right")
        
        speed_scale = ttk.Scale(
            speed_frame,
            from_=0.5,
            to=2.0,
            variable=self.speed_var,
            orient="horizontal",
            command=self._on_speed_change
        )
        speed_scale.pack(side="left", fill="x", expand=True, padx=(10, 10))
        
        # Volume controls
        volume_frame = ttk.Frame(self.main_frame)
        volume_frame.pack(fill="x", pady=(0, 5))
        
        # Mute checkbox
        mute_checkbox = ttk.Checkbutton(
            volume_frame,
            text="Mute Audio",
            variable=self.mute_var,
            command=self._on_mute_change
        )
        mute_checkbox.pack(side="left")
        
        # Volume label
        self.volume_label = ttk.Label(volume_frame, text="70%")
        self.volume_label.pack(side="right")
        
        # Volume scale
        self.volume_scale = ttk.Scale(
            volume_frame,
            from_=0.0,
            to=1.0,
            variable=self.volume_var,
            orient="horizontal",
            command=self._on_volume_change
        )
        self.volume_scale.pack(side="left", fill="x", expand=True, padx=(10, 10))
        
        # Initialize volume state
        self._update_volume_state()
    
    def _on_speed_change(self, value):
        """Handle speed change"""
        speed_value = float(value)
        self.speed_label.config(text=f"{speed_value:.1f}x")
    
    def _on_mute_change(self):
        """Handle mute setting change"""
        self._update_volume_state()
        
        # Call external callback if set
        if self.on_mute_changed:
            self.on_mute_changed(self.mute_var.get())
    
    def _on_volume_change(self, value):
        """Handle volume change"""
        if not self.mute_var.get():
            volume_value = float(value)
            self.volume_label.config(text=f"{int(volume_value * 100)}%")
            
            # Call external callback if set
            if self.on_volume_changed:
                self.on_volume_changed(volume_value)
    
    def _update_volume_state(self):
        """Update volume controls based on mute state"""
        is_muted = self.mute_var.get()
        
        if is_muted:
            self.volume_scale.config(state="disabled")
            self.volume_label.config(text="Muted", foreground="gray")
        else:
            self.volume_scale.config(state="normal")
            volume_value = self.volume_var.get()
            self.volume_label.config(text=f"{int(volume_value * 100)}%", foreground="black")
    
    def get_settings(self):
        """Get all audio settings"""
        return {
            'voice_actor': self.voice_actor_var.get(),
            'speed': self.speed_var.get(),
            'emotion': self.emotion_var.get(),
            'mute': self.mute_var.get(),
            'volume': self.volume_var.get()
        }
    
    def set_settings(self, settings):
        """Set audio settings from dictionary"""
        if 'voice_actor' in settings:
            self.voice_actor_var.set(settings['voice_actor'])
        if 'speed' in settings:
            self.speed_var.set(settings['speed'])
        if 'emotion' in settings:
            self.emotion_var.set(settings['emotion'])
        if 'mute' in settings:
            self.mute_var.set(settings['mute'])
        if 'volume' in settings:
            self.volume_var.set(settings['volume'])
        
        self._update_volume_state()
    
    def set_callbacks(self, on_mute_changed=None, on_volume_changed=None):
        """Set callback functions for events"""
        self.on_mute_changed = on_mute_changed
        self.on_volume_changed = on_volume_changed
    
    def pack(self, **kwargs):
        """Pack the main frame"""
        if self.main_frame:
            self.main_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the main frame"""
        if self.main_frame:
            self.main_frame.grid(**kwargs)
    
    def place(self, **kwargs):
        """Place the main frame"""
        if self.main_frame:
            self.main_frame.place(**kwargs) 