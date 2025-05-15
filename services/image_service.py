"""
Image service for downloading and processing images
"""
import os
import sys
import shutil
import urllib.parse
import requests
from bs4 import BeautifulSoup

def download_images(website_url, output_folder):
    """
    Download images from a website
    
    Args:
        website_url: URL of the website
        output_folder: Folder to save images
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)
        
        # Set up headers for the request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Check if the URL is a direct image file
        parsed_url = urllib.parse.urlparse(website_url)
        path = parsed_url.path.lower()
        if path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
            print("Direct image URL detected, downloading as first image")
            img_path = os.path.join(output_folder, "0.jpg")
            try:
                img_response = requests.get(website_url, headers=headers, timeout=10)
                img_response.raise_for_status()
                with open(img_path, "wb") as f:
                    f.write(img_response.content)
                print(f"Downloaded direct image to {img_path}")
                return True
            except Exception as e:
                print(f"Failed to download direct image: {e}")
                return False
        
        # Get the webpage content
        print(f"Downloading webpage: {website_url}")
        response = requests.get(website_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all image tags
        img_tags = soup.find_all("img")
        
        # Extract image URLs
        img_urls = []
        for img in img_tags:
            img_url = img.get("src")
            if img_url:
                # Convert relative URLs to absolute URLs
                if not img_url.startswith(("http://", "https://")):
                    img_url = urllib.parse.urljoin(website_url, img_url)
                img_urls.append(img_url)
        
        if not img_urls:
            print("No images found on the webpage")
            return False
        
        # Download images
        for i, img_url in enumerate(img_urls):
            img_path = os.path.join(output_folder, f"{i}.jpg")
            try:
                print(f"Downloading image from: {img_url}")
                img_response = requests.get(img_url, headers=headers, timeout=10)
                img_response.raise_for_status()
                with open(img_path, "wb") as f:
                    f.write(img_response.content)
                print(f"Downloaded image {i+1} to {img_path}")
            except Exception as e:
                print(f"Failed to download image {i}: {e}")
        
        return True
    except Exception as e:
        print(f"Error downloading images: {e}")
        return False

def copy_images_from_folder(source_folder, output_folder):
    """
    Copy images from a local folder
    
    Args:
        source_folder: Source folder containing images
        output_folder: Folder to save images
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)
        
        # Get all image files
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
        image_files = [f for f in os.listdir(source_folder) if f.lower().endswith(image_extensions)]
        
        if not image_files:
            print(f"No image files found in {source_folder}")
            return False
        
        # Copy images
        for i, image_file in enumerate(image_files):
            source_path = os.path.join(source_folder, image_file)
            output_path = os.path.join(output_folder, f"{i}.jpg")
            
            try:
                shutil.copy2(source_path, output_path)
                print(f"Copied image {i+1}: {source_path} -> {output_path}")
            except Exception as e:
                print(f"Failed to copy image {i}: {e}")
        
        return True
    except Exception as e:
        print(f"Error copying images: {e}")
        return False

def copy_selected_images(image_paths, output_folder):
    """
    Copy selected images to output folder
    
    Args:
        image_paths: List of image paths
        output_folder: Folder to save images
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)
        
        if not image_paths:
            print("No images selected")
            return False
        
        # Copy images
        for i, image_path in enumerate(image_paths):
            output_path = os.path.join(output_folder, f"{i}.jpg")
            
            try:
                shutil.copy2(image_path, output_path)
                print(f"Copied selected image {i+1}: {image_path} -> {output_path}")
            except Exception as e:
                print(f"Failed to copy image {i}: {e}")
        
        return True
    except Exception as e:
        print(f"Error copying selected images: {e}")
        return False



