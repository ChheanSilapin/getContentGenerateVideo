"""
UI Components Package
Reusable UI components for the Video Generator application
"""

# Import all components for easy access
from .settings_popup import show_settings_popup
from .button_factory import ButtonFactory
from .audio_settings import AudioSettings
from .video_entry import VideoEntry
from .layout_factory import LayoutFactory
from .video_loader import VideoLoader
from .progress_manager import ProgressManager  # Enhanced with dialog helpers and UI utilities
from .video_grid import VideoGrid

# Export all components
__all__ = [
    # Existing components
    'show_settings_popup',
    'ButtonFactory',
    'AudioSettings',
    'VideoEntry',
    'LayoutFactory',
    'VideoLoader',
    'ProgressManager',  # Now includes BaseUIComponent functionality
    'VideoGrid',
] 