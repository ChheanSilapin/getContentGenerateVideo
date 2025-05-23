#!/usr/bin/env python3
"""
Option Tab Component for Video Generator GUI
Handles video enhancement options, aspect ratio settings, and advanced controls
"""
import os
import tkinter as tk
from tkinter import ttk


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

        # Set up the tab
        self.setup_option_tab()

    def setup_option_tab(self):
        """Set up the option tab with video optimization options"""
        main_frame = ttk.Frame(self.parent_frame, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', padx=5, pady=(5, 10))

        label = ttk.Label(header_frame, text="Video Enhancement Options", font=("Helvetica", 14, "bold"))
        label.pack(side="left")

        # Video Ratio section
        ratio_frame = ttk.LabelFrame(main_frame, text="Video Aspect Ratio", padding=10)
        ratio_frame.pack(fill='x', padx=5, pady=5)

        # Create variable for aspect ratio
        self.aspect_ratio = tk.StringVar(value="9:16")

        # Create a grid layout for radio buttons
        ratio_label = ttk.Label(ratio_frame, text="Select video aspect ratio:")
        ratio_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        # Radio buttons for aspect ratios
        ttk.Radiobutton(
            ratio_frame,
            text="9:16 (Vertical - Best for mobile)",
            variable=self.aspect_ratio,
            value="9:16"
        ).grid(row=1, column=0, sticky=tk.W, padx=20, pady=2)

        ttk.Radiobutton(
            ratio_frame,
            text="16:9 (Horizontal - Best for YouTube/TV)",
            variable=self.aspect_ratio,
            value="16:9"
        ).grid(row=2, column=0, sticky=tk.W, padx=20, pady=2)

        ttk.Radiobutton(
            ratio_frame,
            text="1:1 (Square - Best for Instagram/Facebook)",
            variable=self.aspect_ratio,
            value="1:1"
        ).grid(row=3, column=0, sticky=tk.W, padx=20, pady=2)

        # Basic options section
        basic_frame = ttk.LabelFrame(main_frame, text="Basic Options", padding=10)
        basic_frame.pack(fill="x", padx=5, pady=5)

        # Create variables for enhancement options
        self.color_correction = tk.BooleanVar(value=True)
        self.audio_option = tk.BooleanVar(value=True)
        self.framing = tk.BooleanVar(value=True)
        self.motion_graphics = tk.BooleanVar(value=False)
        self.noise_reduction = tk.BooleanVar(value=True)
        self.apply_ffmpeg = tk.BooleanVar(value=False)  # FFmpeg enhancements off by default

        # Create a grid layout for checkboxes
        tk.Checkbutton(basic_frame, text="Color Correction", variable=self.color_correction,
                      bg=self.main_gui.colors["background"], selectcolor=self.main_gui.colors["background"],
                      indicatoron=True, onvalue=True, offvalue=False,
                      font=("Helvetica", 10)).grid(row=0, column=0, sticky=tk.W, padx=20, pady=5)

        tk.Checkbutton(basic_frame, text="Audio Enhancement", variable=self.audio_option,
                      bg=self.main_gui.colors["background"], selectcolor=self.main_gui.colors["background"],
                      indicatoron=True, onvalue=True, offvalue=False,
                      font=("Helvetica", 10)).grid(row=0, column=1, sticky=tk.W, padx=20, pady=5)

        # Continue with remaining checkboxes
        tk.Checkbutton(basic_frame, text="Framing", variable=self.framing,
                      bg=self.main_gui.colors["background"], selectcolor=self.main_gui.colors["background"],
                      indicatoron=True, onvalue=True, offvalue=False,
                      font=("Helvetica", 10)).grid(row=1, column=0, sticky=tk.W, padx=20, pady=5)

        tk.Checkbutton(basic_frame, text="Motion Graphics", variable=self.motion_graphics,
                      bg=self.main_gui.colors["background"], selectcolor=self.main_gui.colors["background"],
                      indicatoron=True, onvalue=True, offvalue=False,
                      font=("Helvetica", 10)).grid(row=1, column=1, sticky=tk.W, padx=20, pady=5)

        tk.Checkbutton(basic_frame, text="Noise Reduction", variable=self.noise_reduction,
                      bg=self.main_gui.colors["background"], selectcolor=self.main_gui.colors["background"],
                      indicatoron=True, onvalue=True, offvalue=False,
                      font=("Helvetica", 10)).grid(row=2, column=0, sticky=tk.W, padx=20, pady=5)

        tk.Checkbutton(basic_frame, text="FFmpeg Enhancements", variable=self.apply_ffmpeg,
                      bg=self.main_gui.colors["background"], selectcolor=self.main_gui.colors["background"],
                      indicatoron=True, onvalue=True, offvalue=False,
                      font=("Helvetica", 10)).grid(row=2, column=1, sticky=tk.W, padx=20, pady=5)

        self._setup_advanced_options(main_frame)
        self._setup_buttons(main_frame)

    def _setup_advanced_options(self, main_frame):
        """Set up the advanced options section"""
        # Advanced options section
        advanced_frame = ttk.LabelFrame(main_frame, text="Advanced Options", padding=10)
        advanced_frame.pack(fill="x", padx=5, pady=5)

        # Create sliders for advanced options
        self.color_intensity = tk.DoubleVar(value=1.0)
        self.crop_percent = tk.DoubleVar(value=0.95)
        self.volume_boost = tk.DoubleVar(value=1.2)
        self.contrast = tk.DoubleVar(value=1.1)
        self.brightness = tk.DoubleVar(value=0.05)
        self.saturation = tk.DoubleVar(value=1.2)
        self.sharpness = tk.DoubleVar(value=1.0)
        self.image_fit_method = tk.StringVar(value="contain")

        # Left column
        left_frame = ttk.Frame(advanced_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=10)

        ttk.Label(left_frame, text="Color Intensity:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Scale(left_frame, from_=0.5, to=2.0, variable=self.color_intensity, length=200).grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=10)

        ttk.Label(left_frame, text="Framing Crop:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Scale(left_frame, from_=0.8, to=1.0, variable=self.crop_percent, length=200).grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=10)

        ttk.Label(left_frame, text="Volume Boost:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Scale(left_frame, from_=0.8, to=1.5, variable=self.volume_boost, length=200).grid(row=2, column=1, sticky=tk.W+tk.E, pady=5, padx=10)

        ttk.Label(left_frame, text="Image Fit Method:").grid(row=5, column=0, sticky=tk.W, pady=5)
        fit_method_frame = ttk.Frame(left_frame)
        fit_method_frame.grid(row=5, column=1, sticky=tk.W+tk.E, pady=5, padx=10)

        fit_methods = [
            ("Contain (Show All)", "contain"),
            ("Cover (Crop to Fill)", "cover"),
            ("Stretch", "stretch")
        ]

        for i, (text, value) in enumerate(fit_methods):
            tk.Radiobutton(fit_method_frame, text=text, variable=self.image_fit_method,
                          value=value, bg=self.main_gui.colors["background"]).grid(row=0, column=i, padx=5)

        # Right column
        right_frame = ttk.Frame(advanced_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=10)

        ttk.Label(right_frame, text="Contrast:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Scale(right_frame, from_=0.8, to=1.5, variable=self.contrast, length=200).grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=10)

        ttk.Label(right_frame, text="Brightness:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Scale(right_frame, from_=0.0, to=0.2, variable=self.brightness, length=200).grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=10)

        ttk.Label(right_frame, text="Saturation:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Scale(right_frame, from_=0.8, to=1.5, variable=self.saturation, length=200).grid(row=2, column=1, sticky=tk.W+tk.E, pady=5, padx=10)

        ttk.Label(right_frame, text="Sharpness:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Scale(right_frame, from_=0.0, to=2.0, variable=self.sharpness, length=200).grid(row=3, column=1, sticky=tk.W+tk.E, pady=5, padx=10)

    def _setup_buttons(self, main_frame):
        """Set up the action buttons"""
        # Apply button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)

        apply_button = self.main_gui.ui_factory.create_styled_button(
            button_frame, "Apply Settings", self.update_enhancement_options,
            bg_color=self.main_gui.colors["success"], hover_color="#27ae60", width=15
        )
        apply_button.pack(side="right", padx=5)

        reset_button = self.main_gui.ui_factory.create_styled_button(
            button_frame, "Reset to Defaults", self.reset_enhancement_options,
            bg_color=self.main_gui.colors["secondary"], hover_color="#2980b9", width=15
        )
        reset_button.pack(side="right", padx=5)

    def update_enhancement_options(self):
        """Update the model with current enhancement options"""
        # Get the current image fit method
        fit_method = self.image_fit_method.get()
        print(f"Selected image fit method: {fit_method}")

        # Update basic options
        self.main_gui.model.enhancement_options = {
            "color_correction": self.color_correction.get(),
            "audio_option": self.audio_option.get(),
            "framing": self.framing.get(),
            "motion_graphics": self.motion_graphics.get(),
            "noise_reduction": self.noise_reduction.get(),
            "apply_ffmpeg": self.apply_ffmpeg.get(),  # Add FFmpeg enhancement option

            # Advanced options
            "color_correction_intensity": self.color_intensity.get(),
            "framing_crop_percent": self.crop_percent.get(),
            "audio_volume_boost": self.volume_boost.get(),
            "contrast": self.contrast.get(),
            "brightness": self.brightness.get(),
            "saturation": self.saturation.get(),
            "sharpness": self.sharpness.get(),
            "image_fit_method": fit_method,

            # Aspect ratio
            "aspect_ratio": self.aspect_ratio.get()
        }

        # Also set the environment variable directly for immediate effect
        os.environ["IMAGE_FIT_METHOD"] = fit_method

        # Update the model's aspect ratio property
        self.main_gui.model.aspect_ratio = self.aspect_ratio.get()

        # Update effect flags
        self.main_gui.model.use_effects = any([self.color_correction.get(), self.motion_graphics.get(), self.framing.get()])

        # Log the changes
        self.main_gui.log(f"Enhancement options updated with {self.aspect_ratio.get()} aspect ratio")

        # Switch back to input tab
        self.main_gui.notebook.select(self.main_gui.input_tab)

    def reset_enhancement_options(self):
        """Reset enhancement options to defaults"""
        # Reset basic options
        self.color_correction.set(True)
        self.audio_option.set(True)
        self.framing.set(True)
        self.motion_graphics.set(False)
        self.noise_reduction.set(True)
        self.apply_ffmpeg.set(False)  # FFmpeg enhancements off by default

        # Reset aspect ratio to default (9:16)
        self.aspect_ratio.set("9:16")

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
        self.main_gui.log("Enhancement options reset to defaults with 9:16 aspect ratio")

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
            "aspect_ratio": self.aspect_ratio.get()
        }
