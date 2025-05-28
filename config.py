"""
Configuration settings for the Video Generator application
"""

# Output settings
DEFAULT_FRAME_RATE = 25
DEFAULT_ZOOM_FACTOR = 0.5
DEFAULT_MAX_CHARS_PER_LINE = 56

# Video dimensions - Default is 9:16 (vertical)
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280

# Aspect ratio presets
RATIO_9_16 = {
    "name": "9:16 (Vertical)",
    "width": 720,
    "height": 1280
}

RATIO_16_9 = {
    "name": "16:9 (Horizontal)",
    "width": 1280,
    "height": 720
}

RATIO_1_1 = {
    "name": "1:1 (Square)",
    "width": 1080,
    "height": 1080
}

# Default aspect ratio
DEFAULT_ASPECT_RATIO = "9:16"

# File paths and extensions
SUPPORTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')

# GUI settings
GUI_WINDOW_SIZE = "900x780"
GUI_TITLE = "Video Generator"
GUI_MIN_WIDTH = 800
GUI_MIN_HEIGHT = 600
GUI_RESIZABLE = True
GUI_CENTER_ON_SCREEN = True

# GUI Colors
GUI_COLORS = {
    "primary": "#2c3e50",      # Dark blue-gray
    "secondary": "#3498db",    # Blue
    "accent": "#e74c3c",       # Red
    "success": "#2ecc71",      # Green
    "background": "#ecf0f1",   # Light gray
    "text": "#34495e",         # Dark text
    "light_text": "#7f8c8d"    # Gray text
}

# GUI Fonts
# GUI Fonts
GUI_FONTS = {
    "default": ("Cascadia Code", 12),
    "button": ("Cascadia Code", 12),
    "label": ("Cascadia Code", 12),
    "heading": ("Cascadia Code", 12, "bold"),
    "console": ("Cascadia Code", 12),
    "tab": ("Cascadia Code", 12)  # Add this line for tab headers
}