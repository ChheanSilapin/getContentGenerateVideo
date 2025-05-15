"""
MoviePy patch module to fix common issues with MoviePy
"""

def apply_patch():
    """Apply patches to MoviePy to fix common issues"""
    try:
        # Import required modules
        from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
        from moviepy.video.VideoClip import ImageClip
        import numpy as np
        from PIL import Image as PILImage
        
        # Patch for ImageSequenceClip to handle newer Pillow versions
        original_init = ImageSequenceClip.__init__
        
        def patched_init(self, sequence, fps=25, durations=None, with_mask=True, 
                        ismask=False, load_images=False):
            # Convert PIL/Pillow Image objects to numpy arrays
            for i, img in enumerate(sequence):
                if hasattr(img, 'getbands'):  # Check if it's a PIL/Pillow Image
                    # Convert to numpy array
                    sequence[i] = np.array(img)
            
            # Call the original __init__
            original_init(self, sequence, fps, durations, with_mask, ismask, load_images)
        
        # Apply the patch
        ImageSequenceClip.__init__ = patched_init
        
        # Check if img_to_array exists before patching
        if hasattr(ImageClip, 'img_to_array'):
            # Patch for ImageClip to handle newer Pillow versions
            original_img_to_array = ImageClip.img_to_array
            
            def patched_img_to_array(img, with_mask=True):
                if hasattr(img, 'getbands'):  # Check if it's a PIL/Pillow Image
                    # Convert to numpy array
                    img = np.array(img)
                return original_img_to_array(img, with_mask)
            
            # Apply the patch
            ImageClip.img_to_array = patched_img_to_array
        else:
            print("Note: ImageClip.img_to_array not found, skipping this patch")
        
        print("Applied MoviePy patches successfully")
        return True
    except Exception as e:
        print(f"Error applying MoviePy patches: {e}")
        return False

