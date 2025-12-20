"""
UI Components Package
Reusable UI components for the Video Generator application
"""

# Import base classes
from .base_tab import BaseTab
from .folder_loader import FolderLoaderMixin

# Import components used by active tabs
from .settings_popup import show_settings_popup
from .progress_manager import ProgressManager
from .video_entry import VideoEntry
from .dropdown_menu import DropdownMenu
from .group_entry import GroupEntry
from .image_entry import ImageEntry

# Export active components
__all__ = [
    'BaseTab',
    'FolderLoaderMixin',
    'show_settings_popup',
    'ProgressManager',
    'VideoEntry',
    'DropdownMenu',
    'GroupEntry',
    'ImageEntry',
]