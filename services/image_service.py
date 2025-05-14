"""
Image Service - Handles image acquisition and processing
"""
import os
import sys
import shutil
from pathlib import Path

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from create_video import downloadImage

def download_images(url, output_folder):
    """
    Download images from a website
    
    Args:
        url: Website URL
        output_folder: Folder to save images
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get title and content from URL
        from utils.helpers import get_title_content
        title, content = get_title_content(url)
        
        # Check if the URL is a direct image file
        import urllib.parse
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path.lower()
        
        # For direct image URLs, don't create placeholder images
        placeholder_count = 0 if path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')) else 4
        
        # Call downloadImage with all required parameters
        result = downloadImage(title, content, url, output_folder, placeholder_count)
        return result is not None
    except Exception as e:
        print(f"Error downloading images: {e}")
        return False

def copy_selected_images(selected_images, output_folder):
    """
    Copy selected images to the output folder
    
    Args:
        selected_images: List of image paths
        output_folder: Folder to copy images to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(output_folder, exist_ok=True)
        
        for i, img_path in enumerate(selected_images):
            # Get file extension
            _, ext = os.path.splitext(img_path)
            
            # Create destination path with sequential numbering
            dest_path = os.path.join(output_folder, f"{i:03d}{ext}")
            
            # Copy the file
            shutil.copy2(img_path, dest_path)
            print(f"Copied {img_path} to {dest_path}")
            
        return True
    except Exception as e:
        print(f"Error copying selected images: {e}")
        return False

def copy_images_from_folder(source_folder, output_folder):
    """
    Copy all images from source folder to output folder
    
    Args:
        source_folder: Source folder containing images
        output_folder: Folder to copy images to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(output_folder, exist_ok=True)
        
        # Get all image files
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
        image_files = [f for f in os.listdir(source_folder) 
                      if os.path.isfile(os.path.join(source_folder, f)) 
                      and f.lower().endswith(image_extensions)]
        
        if not image_files:
            print(f"No image files found in {source_folder}")
            return False
            
        # Copy each image with sequential numbering
        for i, filename in enumerate(sorted(image_files)):
            src_path = os.path.join(source_folder, filename)
            _, ext = os.path.splitext(filename)
            dest_path = os.path.join(output_folder, f"{i:03d}{ext}")
            
            shutil.copy2(src_path, dest_path)
            print(f"Copied {src_path} to {dest_path}")
            
        return True
    except Exception as e:
        print(f"Error copying images from folder: {e}")
        return False



