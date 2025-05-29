"""
Patch for MoviePy to work with newer versions of Pillow
"""
import PIL
from PIL import Image
from moviepy.video.fx.resize import resizer

# Check if ANTIALIAS is available, if not, use LANCZOS
if not hasattr(Image, 'ANTIALIAS'):
    # For newer versions of Pillow
    if hasattr(Image, 'Resampling') and hasattr(Image.Resampling, 'LANCZOS'):
        Image.ANTIALIAS = Image.Resampling.LANCZOS
    else:
        # Fallback for other versions
        Image.ANTIALIAS = Image.LANCZOS

# MoviePy patch applied: Added ANTIALIAS constant to PIL.Image
