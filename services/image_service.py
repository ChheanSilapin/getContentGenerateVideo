"""
Image service functions for downloading and processing images
"""
import os
import shutil
import requests
from bs4 import BeautifulSoup
import urllib.parse
import traceback
from PIL import Image

# Import from utils
from utils.helpers import ensure_directory_exists, is_image_file

# Import from config
from config import SUPPORTED_IMAGE_EXTENSIONS

def download_images(url, output_folder, max_images=10, placeholder_count=4):
    """
    Download images from a website

    Args:
        url: Website URL
        output_folder: Folder to save images
        max_images: Maximum number of images to download
        placeholder_count: Number of placeholder images to create for direct image URLs

    Returns:
        list: Paths to downloaded images
    """
    try:
        ensure_directory_exists(output_folder)

        # Add proper headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': url
        }

        # Check if the URL is a direct image file
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path.lower()
        if path.endswith(SUPPORTED_IMAGE_EXTENSIONS):
            print("Direct image URL detected, downloading as first image")
            img_path = os.path.join(output_folder, "0.jpg")
            try:
                img_response = requests.get(url, headers=headers, timeout=10)
                img_response.raise_for_status()
                with open(img_path, "wb") as f:
                    f.write(img_response.content)
                print(f"Downloaded direct image to {img_path}")

                # Create placeholder images if requested
                if placeholder_count > 0:
                    print(f"Creating {placeholder_count} placeholder images")
                    for i in range(1, placeholder_count + 1):
                        placeholder_path = os.path.join(output_folder, f"{i}.jpg")
                        try:
                            response = requests.get("https://dummyimage.com/640x360/eee/aaa", timeout=10)
                            response.raise_for_status()
                            with open(placeholder_path, "wb") as f:
                                f.write(response.content)
                            print(f"Created placeholder image {i}")
                        except Exception as e:
                            print(f"Failed to download placeholder image: {e}")

                return [img_path] + [os.path.join(output_folder, f"{i}.jpg") for i in range(1, placeholder_count + 1)]
            except Exception as e:
                print(f"Failed to download direct image: {e}")

        # Regular website processing
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            img_tags = soup.find_all('img')
            img_urls = [img.get('src') for img in img_tags if img.get('src')]

            image_paths = []
            for i, img_url in enumerate(img_urls[:max_images]):
                if not img_url.startswith(('http://', 'https://')):
                    img_url = f"{url.rstrip('/')}/{img_url.lstrip('/')}"

                img_path = os.path.join(output_folder, f"{i}.jpg")
                try:
                    print(f"Downloading image from: {img_url}")
                    # Use the same headers for image requests
                    img_response = requests.get(img_url, headers=headers, timeout=10)
                    img_response.raise_for_status()
                    with open(img_path, "wb") as f:
                        f.write(img_response.content)
                    print(f"Downloaded image {i+1} to {img_path}")
                    image_paths.append(img_path)
                except Exception as e:
                    print(f"Failed to download image {i}: {e}")
                    # Try to download a placeholder image
                    try:
                        response = requests.get("https://dummyimage.com/640x360/eee/aaa", timeout=10)
                        response.raise_for_status()
                        with open(img_path, "wb") as f:
                            f.write(response.content)
                        print(f"Used placeholder for image {i}")
                        image_paths.append(img_path)
                    except Exception as e:
                        print(f"Failed to download placeholder image: {e}")

            return image_paths

        except Exception as e:
            print(f"Failed to download images: {e}")
            # Fallback to placeholder images
            image_paths = []
            for i in range(3):
                img_path = os.path.join(output_folder, f"{i}.jpg")
                try:
                    response = requests.get("https://dummyimage.com/640x360/eee/aaa", timeout=10)
                    response.raise_for_status()
                    with open(img_path, "wb") as f:
                        f.write(response.content)
                    print(f"Created placeholder image {i}")
                    image_paths.append(img_path)
                except requests.exceptions.RequestException as e:
                    print(f"Failed to download image {i}: {e}")

            return image_paths
    except Exception as e:
        print(f"Error downloading images: {e}")
        traceback.print_exc()
        return []

def download_images_for_preview(url, output_folder, max_images=10):
    """
    Download images from a website for preview

    Args:
        url: Website URL
        output_folder: Folder to save images
        max_images: Maximum number of images to download

    Returns:
        list: Paths to downloaded images
    """
    return download_images(url, output_folder, max_images, placeholder_count=0)

def copy_selected_images(image_paths, output_folder):
    """
    Copy selected images to output folder

    Args:
        image_paths: List of image paths
        output_folder: Folder to copy images to

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        ensure_directory_exists(output_folder)

        # Track if we successfully copied at least one image
        copied_at_least_one = False

        for i, img_path in enumerate(image_paths):
            try:
                if os.path.exists(img_path):
                    # Use a numbered filename to ensure order
                    ext = os.path.splitext(img_path)[1].lower()
                    if not ext:
                        ext = ".jpg"  # Default extension
                    dest_path = os.path.join(output_folder, f"{i}{ext}")
                    shutil.copy2(img_path, dest_path)
                    print(f"Copied image {i+1}/{len(image_paths)}: {os.path.basename(img_path)} -> {os.path.basename(dest_path)}")
                    copied_at_least_one = True
                elif img_path.startswith(('http://', 'https://')):
                    # It's a URL, try to download it
                    print(f"Image path is a URL, attempting to download: {img_path}")
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(img_path, headers=headers, timeout=10)
                    response.raise_for_status()

                    # Determine file extension from content type or URL
                    content_type = response.headers.get('content-type', '')
                    if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                        ext = '.jpg'
                    elif 'image/png' in content_type:
                        ext = '.png'
                    elif 'image/gif' in content_type:
                        ext = '.gif'
                    elif 'image/webp' in content_type:
                        ext = '.webp'
                    else:
                        # Try to get extension from URL
                        url_ext = os.path.splitext(img_path)[1].lower()
                        ext = url_ext if url_ext in SUPPORTED_IMAGE_EXTENSIONS else '.jpg'

                    dest_path = os.path.join(output_folder, f"{i}{ext}")
                    with open(dest_path, "wb") as f:
                        f.write(response.content)
                    print(f"Downloaded image {i+1}/{len(image_paths)} from URL: {img_path} -> {os.path.basename(dest_path)}")
                    copied_at_least_one = True
                else:
                    print(f"Image not found: {img_path}")
            except Exception as e:
                print(f"Error processing image {i+1}: {e}")
                # Continue with next image instead of failing completely

        # Return success only if we copied at least one image
        return copied_at_least_one
    except Exception as e:
        print(f"Error copying images: {e}")
        traceback.print_exc()
        return False

def get_images_from_folder(folder_path, max_images=None):
    """
    Get all image files from a folder

    Args:
        folder_path: Path to folder
        max_images: Maximum number of images to return (None for all)

    Returns:
        list: Paths to image files
    """
    try:
        if not os.path.isdir(folder_path):
            print(f"Error: {folder_path} is not a directory")
            return []

        image_files = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) and is_image_file(file_path):
                image_files.append(file_path)

        # Sort files to ensure consistent order
        image_files.sort()

        # Limit to max_images if specified
        if max_images is not None:
            image_files = image_files[:max_images]

        return image_files
    except Exception as e:
        print(f"Error getting images from folder: {e}")
        traceback.print_exc()
        return []

def resize_image(image_path, output_path, width=None, height=None, maintain_aspect=True):
    """
    Resize an image

    Args:
        image_path: Path to input image
        output_path: Path to output image
        width: Target width (None to calculate from height)
        height: Target height (None to calculate from width)
        maintain_aspect: Whether to maintain aspect ratio

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(image_path):
            print(f"Error: Image file not found: {image_path}")
            return False

        img = Image.open(image_path)

        # Get original dimensions
        orig_width, orig_height = img.size

        # Calculate new dimensions
        if width is None and height is None:
            # No resize needed
            if image_path != output_path:
                img.save(output_path)
            return True

        if width is None:
            # Calculate width from height
            width = int(orig_width * (height / orig_height)) if maintain_aspect else orig_width

        if height is None:
            # Calculate height from width
            height = int(orig_height * (width / orig_width)) if maintain_aspect else orig_height

        # Resize the image
        resized_img = img.resize((width, height), Image.LANCZOS)

        # Save the resized image
        resized_img.save(output_path)

        return True
    except Exception as e:
        print(f"Error resizing image: {e}")
        traceback.print_exc()
        return False



