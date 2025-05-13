"""
Image Service - Handles image processing functionality
"""
import os
import sys
import shutil
import urllib.parse

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import get_title_content
from create_video import downloadImage
from config import SUPPORTED_IMAGE_EXTENSIONS

def download_images(website_url, images_dir, stop_event=None):
    """
    Download images from a website URL
    
    Args:
        website_url: URL to download images from
        images_dir: Directory to save images to
        stop_event: Threading event to signal process termination
        
    Returns:
        tuple: (folder_name, title, content) or (None, None, None) on failure
    """
    if stop_event and stop_event.is_set():
        print("Process stopped by user.")
        return None, None, None
        
    title, content = get_title_content(website_url)
    print(f"Retrieved title: {title[:50]}...")
    print(f"Content length: {len(content)} characters")
    
    # Check if the URL is a direct image file
    parsed_url = urllib.parse.urlparse(website_url)
    path = parsed_url.path.lower()
    
    if path.endswith(SUPPORTED_IMAGE_EXTENSIONS):
        # For direct image URLs, don't create placeholder images
        folderName = downloadImage(title, content, website_url, folder_name=images_dir, placeholder_count=0)
    else:
        # For regular websites, use default behavior
        folderName = downloadImage(title, content, website_url, folder_name=images_dir)
        
    print(f"Images downloaded to: {folderName}")
    return folderName, title, content

def copy_selected_images(selected_images=None, images_dir="images", source_folder=None):
    """
    Copy selected images to the images directory
    
    Args:
        selected_images: List of paths to selected images
        images_dir: Directory to save images to
        source_folder: Folder containing images to copy
        
    Returns:
        str: Path to the images directory or None on failure
    """
    try:
        # Create the images directory if it doesn't exist
        os.makedirs(images_dir, exist_ok=True)
        
        image_count = 0
        
        if selected_images:
            # Copy specific selected images
            for i, src_path in enumerate(selected_images):
                if os.path.isfile(src_path):
                    # Rename to ensure sequential numbering
                    dst_path = os.path.join(images_dir, f"{i}.jpg")
                    try:
                        shutil.copy2(src_path, dst_path)
                        print(f"Copied {os.path.basename(src_path)} to {dst_path}")
                        image_count += 1
                    except Exception as e:
                        print(f"Error copying {src_path}: {e}")
        elif source_folder:
            # Copy all images from source folder
            for filename in os.listdir(source_folder):
                if filename.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
                    src_path = os.path.join(source_folder, filename)
                    if os.path.isfile(src_path):  # Make sure it's a file, not a directory
                        # Rename to ensure sequential numbering
                        dst_path = os.path.join(images_dir, f"{image_count}.jpg")
                        try:
                            shutil.copy2(src_path, dst_path)
                            print(f"Copied {filename} to {dst_path}")
                            image_count += 1
                        except Exception as e:
                            print(f"Error copying {src_path}: {e}")
        
        if image_count == 0:
            print("No images were copied. Creating placeholder images.")
            # Create placeholder images
            try:
                import requests
                for i in range(3):
                    img_path = os.path.join(images_dir, f"{i}.jpg")
                    response = requests.get("https://dummyimage.com/640x360/eee/aaa", timeout=10)
                    response.raise_for_status()
                    with open(img_path, "wb") as f:
                        f.write(response.content)
                    print(f"Created placeholder image {i}")
                    image_count += 1
            except Exception as e:
                print(f"Error creating placeholder images: {e}")
                return None
        
        print(f"Total images copied: {image_count}")
        return images_dir
        
    except Exception as e:
        print(f"Error copying images: {e}")
        return None
