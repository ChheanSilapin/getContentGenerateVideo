#!/usr/bin/env python3
"""
Option Tab Component for Video Generator GUI
Handles video enhancement options, aspect ratio settings, and advanced controls
"""
import os
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont


class OptionTab:
    """Option tab component for the Video Generator GUI"""

    def __init__(self, parent_frame, main_gui):
        """
        Initialize the option tab

        Args:
            parent_frame: The parent frame to contain this tab
            main_gui: Reference to the main GUI instance for callbacks and shared data
        """
        self.parent_frame = parent_frame
        self.main_gui = main_gui

        # Initialize option variables
        self.aspect_ratio = None
        self.color_correction = None
        self.audio_option = None
        self.framing = None
        self.motion_graphics = None
        self.noise_reduction = None
        self.apply_ffmpeg = None
        self.color_intensity = None
        self.crop_percent = None
        self.volume_boost = None
        self.contrast = None
        self.brightness = None
        self.saturation = None
        self.sharpness = None
        self.image_fit_method = None
        self.voice_emotion = None
        self.subtitle_style = None

        # Create tooltip system
        self.tooltips = {}

        # Set up the tab
        self.setup_option_tab()

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                           relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            
            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def create_toggle_switch(self, parent, text, variable, tooltip_text=None):
        """Create a modern toggle switch"""
        frame = tk.Frame(parent, bg=self.main_gui.colors["background"])
        
        # Toggle switch canvas
        canvas = tk.Canvas(frame, width=50, height=25, highlightthickness=0, 
                          bg=self.main_gui.colors["background"])
        canvas.pack(side="left", padx=(0, 10))
        
        # Label
        label = tk.Label(frame, text=text, bg=self.main_gui.colors["background"], 
                        font=("Cascadia Code", 10))
        label.pack(side="left")
        
        if tooltip_text:
            self.create_tooltip(label, tooltip_text)
        
        def draw_toggle():
            canvas.delete("all")
            if variable.get():
                # On state - green background, circle on right
                canvas.create_oval(2, 2, 48, 23, fill="#4CAF50", outline="#4CAF50")
                canvas.create_oval(28, 4, 44, 21, fill="white", outline="white")
            else:
                # Off state - gray background, circle on left
                canvas.create_oval(2, 2, 48, 23, fill="#CCCCCC", outline="#CCCCCC")
                canvas.create_oval(6, 4, 22, 21, fill="white", outline="white")
        
        def toggle():
            variable.set(not variable.get())
            draw_toggle()
        
        canvas.bind("<Button-1>", lambda e: toggle())
        draw_toggle()
        
        # Update when variable changes
        variable.trace_add("write", lambda *args: draw_toggle())
        
        return frame

    def create_aspect_ratio_visual(self, parent, text, value, variable):
        """Create visual aspect ratio selector with thumbnail"""
        frame = tk.Frame(parent, bg=self.main_gui.colors["background"])
        
        # Create visual representation
        canvas = tk.Canvas(frame, width=60, height=40, highlightthickness=1, 
                          highlightcolor="#007ACC", bg="white")
        canvas.pack(pady=(0, 5))
        
        # Draw aspect ratio representation
        if value == "9:16":
            # Vertical rectangle
            canvas.create_rectangle(20, 5, 40, 35, fill="#E3F2FD", outline="#2196F3", width=2)
        elif value == "16:9":
            # Horizontal rectangle
            canvas.create_rectangle(5, 15, 55, 25, fill="#E8F5E8", outline="#4CAF50", width=2)
        elif value == "1:1":
            # Square
            canvas.create_rectangle(15, 10, 45, 30, fill="#FFF3E0", outline="#FF9800", width=2)
        
        # Radio button and label
        radio_frame = tk.Frame(frame, bg=self.main_gui.colors["background"])
        radio_frame.pack()
        
        radio = tk.Radiobutton(radio_frame, text=text, variable=variable, value=value,
                              bg=self.main_gui.colors["background"], 
                              selectcolor=self.main_gui.colors["background"],
                              font=("Cascadia Code", 9, "bold"))
        radio.pack()
        
        # Make canvas clickable
        def select_ratio(event):
            variable.set(value)
        
        canvas.bind("<Button-1>", select_ratio)
        
        return frame

    def create_slider_with_input(self, parent, text, variable, from_val, to_val, resolution=0.01):
        """Create a slider with numerical input box"""
        frame = tk.Frame(parent)
        
        # Label
        label = ttk.Label(frame, text=text, font=("Cascadia Code", 11))
        label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Slider and input frame
        control_frame = tk.Frame(frame)
        control_frame.grid(row=1, column=0, sticky=tk.W+tk.E, padx=(0, 20))
        
        # Slider
        slider = ttk.Scale(control_frame, from_=from_val, to=to_val, variable=variable, 
                          length=200, orient="horizontal")
        slider.pack(side="left", fill="x", expand=True)
        
        # Numerical input
        input_var = tk.StringVar()
        input_var.set(f"{variable.get():.2f}")
        
        input_box = tk.Entry(control_frame, textvariable=input_var, width=8, 
                           font=("Cascadia Code", 11))
        input_box.pack(side="right", padx=(10, 0))
        
        # Sync slider and input
        def on_slider_change(*args):
            input_var.set(f"{variable.get():.2f}")
        
        def on_input_change(*args):
            try:
                val = float(input_var.get())
                if from_val <= val <= to_val:
                    variable.set(val)
            except ValueError:
                pass
        
        variable.trace_add("write", on_slider_change)
        input_var.trace_add("write", on_input_change)
        
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def create_subtitle_preview(self, parent):
        """Create subtitle style preview area"""
        preview_frame = ttk.LabelFrame(parent, text="Style Preview", padding=10)
        
        # Preview canvas
        self.preview_canvas = tk.Canvas(preview_frame, width=300, height=80, 
                                       bg="black", highlightthickness=1,
                                       highlightcolor="#CCCCCC")
        self.preview_canvas.pack(pady=(0, 10))
        
        # Sample text
        self.update_subtitle_preview()
        
        return preview_frame

    def update_subtitle_preview(self):
        """Update the subtitle preview based on selected style"""
        if not hasattr(self, 'preview_canvas'):
            return
            
        self.preview_canvas.delete("all")
        
        # Get current style
        style_key = self.subtitle_style.get() if self.subtitle_style else "modern_glow"
        
        # Style configurations for preview (adjusted for smaller canvas)
        preview_styles = {
            "modern_glow": {"color": "#FFFFFF", "outline": "#0080FF", "font": ("Arial", 10, "bold")},
            "neon_pink": {"color": "#FF00FF", "outline": "#800080", "font": ("Impact", 10, "bold")},
            "gradient_gold": {"color": "#FFD700", "outline": "#000000", "font": ("Arial", 10, "bold")},
            "cyberpunk": {"color": "#00FFFF", "outline": "#FF0080", "font": ("Consolas", 10, "bold")},
            "classic_movie": {"color": "#FFFF00", "outline": "#000000", "font": ("Times", 10)},
            "fire_red": {"color": "#FF0000", "outline": "#800000", "font": ("Arial", 10, "bold")},
            "ice_blue": {"color": "#80FFFF", "outline": "#FFFFFF", "font": ("Arial", 10, "bold")},
            "retro_wave": {"color": "#FF80FF", "outline": "#800080", "font": ("Impact", 10, "bold")}
        }
        
        style = preview_styles.get(style_key, preview_styles["modern_glow"])
        
        # Draw sample text with outline effect (adjusted for smaller canvas)
        sample_text = "Sample Text"
        x, y = 75, 25  # Center of 150x50 canvas
        
        # Create outline effect
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    self.preview_canvas.create_text(x+dx, y+dy, text=sample_text, 
                                                  fill=style["outline"], font=style["font"])
        
        # Main text
        self.preview_canvas.create_text(x, y, text=sample_text, 
                                       fill=style["color"], font=style["font"])

    def setup_option_tab(self):
        """Set up the option tab with simple layout showing all options"""
        # Main frame with minimal padding for 800x800
        main_frame = tk.Frame(self.parent_frame, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)  # Minimal padding for 800x800

        # Video Aspect Ratio section
        ratio_frame = tk.LabelFrame(main_frame, text="Video Aspect Ratio", 
                                   font=("Cascadia Code", 10, "bold"), bg="white", fg="#333",
                                   relief="solid", bd=1)
        ratio_frame.pack(fill='x', pady=(0, 2))  # Minimal spacing for 800x800

        self.aspect_ratio = tk.StringVar(value="9:16")

        tk.Label(ratio_frame, text="Select video aspect ratio:", 
                bg="white", font=("Cascadia Code", 10)).pack(anchor="w", padx=2, pady=(2, 1))  # Minimal padding

        # Aspect ratio options in horizontal layout
        ratio_options_frame = tk.Frame(ratio_frame, bg="white")
        ratio_options_frame.pack(fill="x", padx=2, pady=(0, 2))  # Minimal padding

        tk.Radiobutton(ratio_options_frame, text="9:16 (Mobile)", 
                      variable=self.aspect_ratio, value="9:16", bg="white", 
                      font=("Cascadia Code", 9)).pack(side="left", padx=(0, 2))  # Minimal spacing
        tk.Radiobutton(ratio_options_frame, text="16:9 (YouTube)", 
                      variable=self.aspect_ratio, value="16:9", bg="white", 
                      font=("Cascadia Code", 9)).pack(side="left", padx=(0, 2))
        tk.Radiobutton(ratio_options_frame, text="1:1 (Square)", 
                      variable=self.aspect_ratio, value="1:1", bg="white", 
                      font=("Cascadia Code", 9)).pack(side="left")

        # Basic Options section
        basic_frame = tk.LabelFrame(main_frame, text="Basic Options", 
                                   font=("Cascadia Code", 9, "bold"), bg="white", fg="#333",
                                   relief="solid", bd=1)
        basic_frame.pack(fill='x', pady=(0, 2))  # Minimal spacing

        # Create variables for basic options
        self.color_correction = tk.BooleanVar(value=True)
        self.audio_option = tk.BooleanVar(value=True)
        self.framing = tk.BooleanVar(value=True)
        self.motion_graphics = tk.BooleanVar(value=False)
        self.noise_reduction = tk.BooleanVar(value=True)
        self.apply_ffmpeg = tk.BooleanVar(value=False)

        # Basic options in 2 columns
        basic_options_frame = tk.Frame(basic_frame, bg="white")
        basic_options_frame.pack(fill="x", padx=2, pady=2)  # Minimal padding

        # Left column
        left_basic = tk.Frame(basic_options_frame, bg="white")
        left_basic.pack(side="left", fill="both", expand=True)

        tk.Checkbutton(left_basic, text="Color Correction", variable=self.color_correction, 
                      bg="white", font=("Cascadia Code", 10)).pack(anchor="w", pady=0)
        tk.Checkbutton(left_basic, text="Framing", variable=self.framing, 
                      bg="white", font=("Cascadia Code", 10)).pack(anchor="w", pady=0)
        tk.Checkbutton(left_basic, text="Noise Reduction", variable=self.noise_reduction, 
                      bg="white", font=("Cascadia Code", 10)).pack(anchor="w", pady=0)

        # Right column
        right_basic = tk.Frame(basic_options_frame, bg="white")
        right_basic.pack(side="left", fill="both", expand=True)

        tk.Checkbutton(right_basic, text="Audio Enhancement", variable=self.audio_option, 
                      bg="white", font=("Cascadia Code", 10)).pack(anchor="w", pady=0)
        tk.Checkbutton(right_basic, text="Motion Graphics", variable=self.motion_graphics, 
                      bg="white", font=("Cascadia Code", 10)).pack(anchor="w", pady=0)
        tk.Checkbutton(right_basic, text="FFmpeg Enhancements", variable=self.apply_ffmpeg, 
                      bg="white", font=("Cascadia Code", 10)).pack(anchor="w", pady=0)

        # Voice Emotion section
        emotion_frame = tk.LabelFrame(main_frame, text="Voice Emotion", 
                                     font=("Cascadia Code", 10, "bold"), bg="white", fg="#333",
                                     relief="solid", bd=1)
        emotion_frame.pack(fill='x', pady=(0, 0))  # Minimal spacing

        self.voice_emotion = tk.StringVar(value="neutral")

        tk.Label(emotion_frame, text="Select voice emotion:", 
                bg="white", font=("Cascadia Code", 10)).pack(anchor="w", padx=2, pady=(0, 0))  # Minimal padding

        # Voice emotion options in horizontal layout
        emotion_options_frame = tk.Frame(emotion_frame, bg="white")
        emotion_options_frame.pack(fill="x", padx=2, pady=(0, 2))  # Minimal padding

        emotions = [("Neutral", "neutral"), ("Excited", "excited"), ("Dramatic", "dramatic"), 
                   ("Calm", "calm"), ("Energetic", "energetic")]

        for text, value in emotions:
            tk.Radiobutton(emotion_options_frame, text=text, variable=self.voice_emotion, 
                          value=value, bg="white", font=("Cascadia Code", 10)).pack(side="left", padx=(0, 4))  # Minimal spacing

        # Subtitle Style section
        subtitle_frame = tk.LabelFrame(main_frame, text="Subtitle Style", 
                                      font=("Cascadia Code", 10, "bold"), bg="white", fg="#333",
                                      relief="solid", bd=1)
        subtitle_frame.pack(fill='x', pady=(0, 2))  # Minimal spacing

        self.subtitle_style = tk.StringVar(value="modern_glow")

        tk.Label(subtitle_frame, text="Select subtitle style:", 
                bg="white", font=("Cascadia Code", 10)).pack(anchor="w", padx=2, pady=(2, 1))  # Minimal padding

        # Subtitle options in 2 rows
        subtitle_content_frame = tk.Frame(subtitle_frame, bg="white")
        subtitle_content_frame.pack(fill="x", padx=2, pady=(0, 2))  # Minimal padding

        subtitle_styles = [
            ("Modern Glow", "modern_glow"), ("Neon Pink", "neon_pink"), 
            ("Gradient Gold", "gradient_gold"), ("Cyberpunk", "cyberpunk"),
            ("Classic Movie", "classic_movie"), ("Fire Red", "fire_red"), 
            ("Ice Blue", "ice_blue"), ("Retro Wave", "retro_wave")
        ]

        # First row (4 styles)
        subtitle_row1 = tk.Frame(subtitle_content_frame, bg="white")
        subtitle_row1.pack(fill="x", pady=(0, 1))

        for text, value in subtitle_styles[:4]:
            tk.Radiobutton(subtitle_row1, text=text, variable=self.subtitle_style, 
                          value=value, bg="white", font=("Cascadia Code", 10)).pack(side="left", padx=(0, 4))  # Minimal spacing

        # Second row (4 styles)
        subtitle_row2 = tk.Frame(subtitle_content_frame, bg="white")
        subtitle_row2.pack(fill="x")

        for text, value in subtitle_styles[4:]:
            tk.Radiobutton(subtitle_row2, text=text, variable=self.subtitle_style, 
                          value=value, bg="white", font=("Cascadia Code", 10)).pack(side="left", padx=(0, 4))  # Minimal spacing

        # Advanced Options section
        advanced_frame = tk.LabelFrame(main_frame, text="Advanced Options", 
                                      font=("Cascadia Code", 10, "bold"), bg="white", fg="#333",
                                      relief="solid", bd=1)
        advanced_frame.pack(fill='x', pady=(0, 2))  # Minimal spacing

        # Create variables for advanced options
        self.color_intensity = tk.DoubleVar(value=1.0)
        self.crop_percent = tk.DoubleVar(value=0.95)
        self.volume_boost = tk.DoubleVar(value=1.2)
        self.contrast = tk.DoubleVar(value=1.1)
        self.brightness = tk.DoubleVar(value=0.05)
        self.saturation = tk.DoubleVar(value=1.2)
        self.sharpness = tk.DoubleVar(value=1.0)
        self.image_fit_method = tk.StringVar(value="contain")

        # Advanced options in 2 columns
        advanced_content = tk.Frame(advanced_frame, bg="white")
        advanced_content.pack(fill="x", padx=2, pady=2)  # Minimal padding

        # Left column
        adv_left = tk.Frame(advanced_content, bg="white")
        adv_left.pack(side="left", fill="both", expand=True, padx=(0, 2))  # Minimal padding

        tk.Label(adv_left, text="Color Intensity:", bg="white", font=("Cascadia Code", 10)).pack(anchor="w")
        tk.Scale(adv_left, from_=0.5, to=2.0, resolution=0.1, orient="horizontal", 
                variable=self.color_intensity, bg="white", font=("Cascadia Code", 10), length=100).pack(fill="x", pady=(0, 1))  # Smaller length and spacing

        tk.Label(adv_left, text="Framing Crop:", bg="white", font=("Cascadia Code", 10)).pack(anchor="w")
        tk.Scale(adv_left, from_=0.8, to=1.0, resolution=0.01, orient="horizontal", 
                variable=self.crop_percent, bg="white", font=("Cascadia Code", 10), length=100).pack(fill="x", pady=(0, 1))

        tk.Label(adv_left, text="Volume Boost:", bg="white", font=("Cascadia Code", 10)).pack(anchor="w")
        tk.Scale(adv_left, from_=0.8, to=1.5, resolution=0.1, orient="horizontal", 
                variable=self.volume_boost, bg="white", font=("Cascadia Code", 10), length=100).pack(fill="x", pady=(0, 1))

        tk.Label(adv_left, text="Sharpness:", bg="white", font=("Cascadia Code", 10)).pack(anchor="w")
        tk.Scale(adv_left, from_=0.0, to=2.0, resolution=0.1, orient="horizontal", 
                variable=self.sharpness, bg="white", font=("Cascadia Code", 10), length=100).pack(fill="x")

        # Right column
        adv_right = tk.Frame(advanced_content, bg="white")
        adv_right.pack(side="left", fill="both", expand=True)

        tk.Label(adv_right, text="Contrast:", bg="white", font=("Cascadia Code", 10)).pack(anchor="w")
        tk.Scale(adv_right, from_=0.8, to=1.5, resolution=0.1, orient="horizontal", 
                variable=self.contrast, bg="white", font=("Cascadia Code", 10), length=100).pack(fill="x", pady=(0, 1))  # Smaller length and spacing

        tk.Label(adv_right, text="Brightness:", bg="white", font=("Cascadia Code", 10)).pack(anchor="w")
        tk.Scale(adv_right, from_=0.0, to=0.2, resolution=0.01, orient="horizontal", 
                variable=self.brightness, bg="white", font=("Cascadia Code", 10), length=100).pack(fill="x", pady=(0, 1))

        tk.Label(adv_right, text="Saturation:", bg="white", font=("Cascadia Code", 10)).pack(anchor="w")
        tk.Scale(adv_right, from_=0.8, to=1.5, resolution=0.1, orient="horizontal", 
                variable=self.saturation, bg="white", font=("Cascadia Code", 10), length=100).pack(fill="x", pady=(0, 1))

        # Image Fit Method
        tk.Label(adv_right, text="Image Fit Method:", bg="white", font=("Cascadia Code", 10)).pack(anchor="w")
        fit_frame = tk.Frame(adv_right, bg="white")
        fit_frame.pack(fill="x")

        tk.Radiobutton(fit_frame, text="Contain", variable=self.image_fit_method, 
                      value="contain", bg="white", font=("Cascadia Code", 10)).pack(anchor="w")
        tk.Radiobutton(fit_frame, text="Cover", variable=self.image_fit_method, 
                      value="cover", bg="white", font=("Cascadia Code", 10)).pack(anchor="w")
        tk.Radiobutton(fit_frame, text="Stretch", variable=self.image_fit_method, 
                      value="stretch", bg="white", font=("Cascadia Code", 10)).pack(anchor="w")

        # Buttons at bottom
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill="x", pady=(2, 0))  # Minimal spacing

        tk.Button(button_frame, text="Reset", command=self.reset_enhancement_options, 
                 bg="#2196F3", fg="white", font=("Cascadia Code", 10, "bold"),
                 width=8).pack(side="right", padx=1)  # Smaller width and padding

        tk.Button(button_frame, text="Apply", command=self.update_enhancement_options, 
                 bg="#4CAF50", fg="white", font=("Cascadia Code", 10, "bold"),
                 width=8).pack(side="right", padx=1)  # Smaller width and padding

    def update_enhancement_options(self):
        """Update the model with current enhancement options"""
        # Update all options
        self.main_gui.model.enhancement_options = {
            "color_correction": self.color_correction.get(),
            "audio_option": self.audio_option.get(),
            "framing": self.framing.get(),
            "motion_graphics": self.motion_graphics.get(),
            "noise_reduction": self.noise_reduction.get(),
            "apply_ffmpeg": self.apply_ffmpeg.get(),

            # Advanced options
            "color_correction_intensity": self.color_intensity.get(),
            "framing_crop_percent": self.crop_percent.get(),
            "audio_volume_boost": self.volume_boost.get(),
            "contrast": self.contrast.get(),
            "brightness": self.brightness.get(),
            "saturation": self.saturation.get(),
            "sharpness": self.sharpness.get(),
            "image_fit_method": self.image_fit_method.get(),

            # Aspect ratio
            "aspect_ratio": self.aspect_ratio.get(),

            # Voice emotion
            "voice_emotion": self.voice_emotion.get(),

            # Subtitle style
            "subtitle_style": self.subtitle_style.get()
        }

        # Update the model's aspect ratio property
        self.main_gui.model.aspect_ratio = self.aspect_ratio.get()

        # Update effect flags
        self.main_gui.model.use_effects = any([self.color_correction.get(), self.motion_graphics.get(), self.framing.get()])

        # Log the changes
        self.main_gui.log(f"All options updated with {self.aspect_ratio.get()} aspect ratio")

        # Switch back to input tab
        self.main_gui.notebook.select(self.main_gui.input_tab)

    def reset_enhancement_options(self):
        """Reset all options to defaults"""
        # Reset basic options
        self.color_correction.set(True)
        self.audio_option.set(True)
        self.framing.set(True)
        self.motion_graphics.set(False)
        self.noise_reduction.set(True)
        self.apply_ffmpeg.set(False)

        # Reset aspect ratio to default (9:16)
        self.aspect_ratio.set("9:16")

        # Reset voice emotion to default (neutral)
        self.voice_emotion.set("neutral")

        # Reset subtitle style to default (modern_glow)
        self.subtitle_style.set("modern_glow")

        # Reset advanced options
        self.color_intensity.set(1.0)
        self.crop_percent.set(0.95)
        self.volume_boost.set(1.2)
        self.contrast.set(1.1)
        self.brightness.set(0.05)
        self.saturation.set(1.2)
        self.sharpness.set(1.0)
        self.image_fit_method.set("contain")

        # Log the changes
        self.main_gui.log("All options reset to defaults")

    def get_aspect_ratio(self):
        """Get the current aspect ratio setting"""
        return self.aspect_ratio.get()

    def get_enhancement_options(self):
        """Get all current enhancement options as a dictionary"""
        return {
            "color_correction": self.color_correction.get(),
            "audio_option": self.audio_option.get(),
            "framing": self.framing.get(),
            "motion_graphics": self.motion_graphics.get(),
            "noise_reduction": self.noise_reduction.get(),
            "apply_ffmpeg": self.apply_ffmpeg.get(),
            "color_correction_intensity": self.color_intensity.get(),
            "framing_crop_percent": self.crop_percent.get(),
            "audio_volume_boost": self.volume_boost.get(),
            "contrast": self.contrast.get(),
            "brightness": self.brightness.get(),
            "saturation": self.saturation.get(),
            "sharpness": self.sharpness.get(),
            "image_fit_method": self.image_fit_method.get(),
            "aspect_ratio": self.aspect_ratio.get(),
            "voice_emotion": self.voice_emotion.get(),
            "subtitle_style": self.subtitle_style.get()
        }
