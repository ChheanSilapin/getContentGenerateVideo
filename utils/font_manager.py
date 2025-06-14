#!/usr/bin/env python3
"""
Font Management Utility for Video Generator
Handles font detection, fallbacks, and bundling for consistent typography
"""
import os
import sys
import tkinter as tk
from tkinter import font
import warnings

# Suppress tkinter warnings during font detection
warnings.filterwarnings("ignore", category=UserWarning, module="tkinter")

def get_available_fonts():
    """
    Get list of available fonts on the system
    
    Returns:
        list: Available font families
    """
    try:
        # Create a temporary root window for font detection
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Get available fonts
        available_fonts = list(font.families())
        root.destroy()
        
        return available_fonts
    except Exception as e:
        print(f"⚠️ Font detection error: {e}")
        return []

def detect_best_font():
    """
    Detect the best available font with intelligent fallbacks
    
    Returns:
        str: Best available font name
    """
    # Font preferences in order of preference
    font_preferences = [
        "Cascadia Code",         # Microsoft's developer font (best choice)
        "Cascadia Mono",         # Alternative Cascadia variant
        "Fira Code",            # Popular developer font
        "JetBrains Mono",       # JetBrains developer font
        "Source Code Pro",      # Adobe's developer font
        "Inconsolata",          # Google's monospace font
        "Consolas",             # Windows default monospace
        "Monaco",               # macOS default monospace
        "Menlo",                # macOS alternative monospace
        "Ubuntu Mono",          # Ubuntu's monospace
        "DejaVu Sans Mono",     # Linux common monospace
        "Liberation Mono",      # Open source monospace
        "Courier New",          # Universal fallback
        "monospace",            # System default monospace
        "Arial",                # Final fallback
    ]
    
    try:
        available_fonts = get_available_fonts()
        
        # Find the first available font from preferences
        for preferred_font in font_preferences:
            if preferred_font in available_fonts:
                return preferred_font
        
        # If no preferred fonts found, use the first monospace-like font
        monospace_keywords = ["mono", "code", "console", "terminal", "fixed"]
        for font_name in available_fonts:
            for keyword in monospace_keywords:
                if keyword.lower() in font_name.lower():
                    return font_name
        
        # Last resort - use Arial
        return "Arial"
        
    except Exception as e:
        # Only print errors, not normal operation messages
        print(f"⚠️ Font detection failed: {e}")
        return "Arial"

def get_font_configuration():
    """
    Get complete font configuration with fallbacks
    
    Returns:
        dict: Font configuration for GUI
    """
    selected_font = detect_best_font()
    
    # Create font configuration
    font_config = {
        "default": (selected_font, 12),
        "button": (selected_font, 12),
        "label": (selected_font, 12),
        "heading": (selected_font, 12, "bold"),
        "console": (selected_font, 12),
        "tab": (selected_font, 12),
        "small": (selected_font, 10),
        "large": (selected_font, 14)
    }
    
    return font_config

def is_bundled_executable():
    """
    Check if running as a bundled executable
    
    Returns:
        bool: True if bundled, False if development
    """
    return getattr(sys, 'frozen', False)

def get_bundled_font_path():
    """
    Get path to bundled fonts directory
    
    Returns:
        str: Path to fonts directory
    """
    try:
        from utils.path_manager import get_base_path
        if is_bundled_executable():
            # In bundled executable, use base path from path_manager
            base_path = get_base_path()
            return os.path.join(base_path, 'fonts')
        else:
            # In development, fonts are in project fonts directory
            return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts')
    except ImportError:
        # Fallback if path_manager is not available
        if is_bundled_executable():
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
            return os.path.join(base_path, 'fonts')
        else:
            return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts')

def install_bundled_fonts():
    """
    Install bundled fonts for the session (if available)
    
    Returns:
        bool: True if fonts were installed, False otherwise
    """
    try:
        fonts_dir = get_bundled_font_path()
        
        if not os.path.exists(fonts_dir):
            return False
        
        # Look for font files
        font_extensions = ['.ttf', '.otf', '.woff', '.woff2']
        font_files = []
        
        for ext in font_extensions:
            font_files.extend([f for f in os.listdir(fonts_dir) if f.lower().endswith(ext)])
        
        if not font_files:
            return False
        
        # On Windows, we can temporarily install fonts for the session
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes
                
                # Windows API for adding fonts
                gdi32 = ctypes.windll.gdi32
                
                installed_count = 0
                for font_file in font_files:
                    font_path = os.path.join(fonts_dir, font_file)
                    if gdi32.AddFontResourceW(font_path):
                        installed_count += 1
                
                if installed_count > 0:
                    # Notify system of font changes
                    user32 = ctypes.windll.user32
                    user32.SendMessageW(0xFFFF, 0x001D, 0, 0)  # WM_FONTCHANGE
                    return True
                    
            except Exception as e:
                # Only print actual errors
                print(f"⚠️ Could not install Windows fonts: {e}")
        
        # For other platforms, fonts would need to be installed differently
        return False
        
    except Exception as e:
        print(f"⚠️ Error installing bundled fonts: {e}")
        return False

def initialize_fonts():
    """
    Initialize font system - install bundled fonts and get configuration
    
    Returns:
        dict: Font configuration
    """
    # Try to install bundled fonts first (silently)
    bundled_fonts_installed = install_bundled_fonts()
    
    # Get font configuration with current available fonts
    font_config = get_font_configuration()
    
    return font_config

# Font download instructions for development
CASCADIA_CODE_DOWNLOAD_INFO = """
📥 CASCADIA CODE DOWNLOAD INSTRUCTIONS:

1. Visit: https://github.com/microsoft/cascadia-code/releases
2. Download the latest "CascadiaCode-*.zip" file
3. Extract the ZIP file
4. Copy all .ttf files to the 'fonts' directory in your project
5. Rebuild the installer

Font files needed:
- CascadiaCode-Regular.ttf
- CascadiaCode-Bold.ttf
- CascadiaCode-Italic.ttf
- CascadiaCode-BoldItalic.ttf

Alternative: Use 'Consolas' (Windows) or 'Monaco' (macOS) which are system fonts.
"""

if __name__ == "__main__":
    # Test font detection
    print("🧪 Testing font detection...")
    available = get_available_fonts()
    print(f"📊 Found {len(available)} available fonts")
    
    best_font = detect_best_font()
    print(f"🎯 Best font: {best_font}")
    
    config = get_font_configuration()
    print(f"⚙️ Font configuration: {config}")
    
    # Check for Cascadia Code specifically
    if "Cascadia Code" not in available:
        print("\n" + CASCADIA_CODE_DOWNLOAD_INFO) 