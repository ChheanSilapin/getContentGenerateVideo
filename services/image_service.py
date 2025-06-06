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

        # ✅ ENHANCED URL VALIDATION AND USER GUIDANCE
        print(f"Analyzing URL: {url}")
        
        # Check for known problematic URL patterns
        problematic_patterns = [
            ('facebook.com', 'Facebook blocks image scraping. Try uploading images directly from the Images tab.'),
            ('instagram.com', 'Instagram blocks image scraping. Try uploading images directly from the Images tab.'),
            ('twitter.com', 'Twitter blocks image scraping. Try uploading images directly from the Images tab.'),
            ('x.com', 'X (Twitter) blocks image scraping. Try uploading images directly from the Images tab.'),
            ('linkedin.com', 'LinkedIn blocks image scraping. Try uploading images directly from the Images tab.'),
            ('google.com/url?', 'This is a Google search redirect URL. Please:\n- Use Google Images search\n- Right-click an image → "Copy image address"\n- Use that direct image URL instead'),
            ('youtube.com', 'YouTube doesn\'t allow image scraping. Try uploading images directly from the Images tab.'),
            ('reddit.com', 'Reddit may block scraping. Try direct image URLs or upload from the Images tab.'),
        ]
        
        for pattern, suggestion in problematic_patterns:
            if pattern in url.lower():
                print(f"WARNING: DETECTED PROBLEMATIC URL: {pattern}")
                print(f"SUGGESTION: {suggestion}")
                
                # For Google redirect URLs, try to extract the actual URL
                if 'google.com/url?' in url.lower():
                    try:
                        from urllib.parse import parse_qs, urlparse
                        parsed = urlparse(url)
                        query_params = parse_qs(parsed.query)
                        actual_url = query_params.get('url', [None])[0]
                        
                        if actual_url:
                            print(f"EXTRACTED ACTUAL URL: {actual_url}")
                            print(f"TIP: Use this direct URL instead: {actual_url}")
                            # Recursively try the extracted URL
                            return download_images(actual_url, output_folder, max_images, placeholder_count)
                    except Exception as extract_error:
                        print(f"ERROR: Could not extract URL: {extract_error}")
                
                # For social media sites, create placeholder images with helpful message
                print("Creating placeholder images since this site blocks scraping...")
                return create_helpful_placeholder_images(output_folder, max_images, f"Images from {pattern} cannot be scraped automatically")
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            print("ERROR: URL must start with http:// or https://")
            return create_helpful_placeholder_images(output_folder, max_images, "Invalid URL format")
        
        print("URL appears valid, proceeding with download...")

        # Add proper headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': url
        }

        # Check if the URL is a direct image file
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path.lower()
        if path.endswith(SUPPORTED_IMAGE_EXTENSIONS):
            print("Direct image URL detected, downloading as first image")
            img_path = os.path.join(output_folder, "0.jpg")
            try:
                print(f"Downloading direct image...")
                img_response = requests.get(url, headers=headers, timeout=15)
                img_response.raise_for_status()
                with open(img_path, "wb") as f:
                    f.write(img_response.content)
                print(f"Downloaded direct image to {img_path}")

                # Create placeholder images if requested
                if placeholder_count > 0:
                    print(f"Creating {placeholder_count} placeholder images")
                    placeholder_paths = create_placeholder_images(output_folder, placeholder_count, start_index=1)
                    return [img_path] + placeholder_paths
                
                return [img_path]
            except Exception as e:
                print(f"ERROR: Failed to download direct image: {e}")
                return create_helpful_placeholder_images(output_folder, max_images, f"Failed to download direct image: {str(e)}")

        # Regular website processing
        try:
            print("Downloading webpage...")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            print(f"Webpage downloaded successfully (Status: {response.status_code})")

            print("Finding images...")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for images in multiple ways
            img_tags = soup.find_all('img')
            
            # Also check for common image container patterns
            img_containers = soup.find_all(['div', 'figure', 'picture'], 
                                         class_=lambda x: x and any(keyword in x.lower() for keyword in ['image', 'photo', 'picture', 'gallery'] if x))
            
            # Extract image URLs from various sources
            img_urls = []
            
            # From img tags
            for img in img_tags:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src:
                    img_urls.append(src)
            
            # From background images in style attributes
            for element in soup.find_all(attrs={'style': True}):
                style = element['style']
                if 'background-image' in style:
                    import re
                    bg_match = re.search(r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)', style)
                    if bg_match:
                        img_urls.append(bg_match.group(1))
            
            print(f"Found {len(img_urls)} images")
            
            if len(img_urls) == 0:
                print("WARNING: No images found on this webpage")
                print("SUGGESTIONS:")
                print("   • Try a different website (like Unsplash, Pexels, or Pixabay)")
                print("   • Use a direct image URL")
                print("   • Upload images manually from the Images tab")
                return create_helpful_placeholder_images(output_folder, max_images, "No images found on this webpage")

            print("Processing images...")
            image_paths = []
            successful_downloads = 0
            
            for i, img_url in enumerate(img_urls[:max_images]):
                try:
                    # Make URL absolute if it's relative
                    if not img_url.startswith(('http://', 'https://')):
                        from urllib.parse import urljoin
                        img_url = urljoin(url, img_url)

                    # Skip very small images (likely icons)
                    if any(keyword in img_url.lower() for keyword in ['icon', 'logo', 'avatar', 'thumbnail']):
                        continue

                    img_path = os.path.join(output_folder, f"{successful_downloads}.jpg")
                    
                    print(f"Downloading image {successful_downloads + 1}: {img_url[:100]}...")
                    
                    img_response = requests.get(img_url, headers=headers, timeout=10)
                    img_response.raise_for_status()
                    
                    # Check if it's actually an image by content type
                    content_type = img_response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        print(f"WARNING: Skipping non-image content: {content_type}")
                        continue
                    
                    with open(img_path, "wb") as f:
                        f.write(img_response.content)
                    
                    # Verify the downloaded file is a valid image
                    try:
                        from PIL import Image
                        with Image.open(img_path) as test_img:
                            width, height = test_img.size
                            if width < 100 or height < 100:  # Skip very small images
                                print(f"⚠️  Skipping small image: {width}x{height}")
                                os.remove(img_path)
                                continue
                    except Exception as verify_error:
                        print(f"⚠️  Skipping invalid image file: {verify_error}")
                        try:
                            os.remove(img_path)
                        except:
                            pass
                        continue
                    
                    print(f"✅ Downloaded image {successful_downloads + 1}")
                    image_paths.append(img_path)
                    successful_downloads += 1
                    
                    if successful_downloads >= max_images:
                        break
                        
                except Exception as e:
                    print(f"❌ Failed to download image {i + 1}: {e}")
                    continue

            if successful_downloads == 0:
                print("❌ No images could be downloaded successfully")
                return create_helpful_placeholder_images(output_folder, max_images, "No images could be downloaded from this site")
            
            print(f"🎉 Successfully downloaded {successful_downloads} images")
            return image_paths

        except requests.exceptions.HTTPError as http_error:
            status_code = http_error.response.status_code if http_error.response else "Unknown"
            print(f"❌ HTTP Error {status_code}: {http_error}")
            
            if status_code == 400:
                message = "Website returned 'Bad Request' - the site may block automated requests"
            elif status_code == 403:
                message = "Website returned 'Forbidden' - access denied"
            elif status_code == 404:
                message = "Website returned 'Not Found' - check the URL"
            else:
                message = f"Website returned HTTP error {status_code}"
            
            print(f"💡 SUGGESTION: Try a different website or upload images manually")
            return create_helpful_placeholder_images(output_folder, max_images, message)
            
        except requests.exceptions.RequestException as req_error:
            print(f"❌ Network error: {req_error}")
            print("💡 SUGGESTION: Check your internet connection and try again")
            return create_helpful_placeholder_images(output_folder, max_images, f"Network error: {str(req_error)}")
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            traceback.print_exc()
            return create_helpful_placeholder_images(output_folder, max_images, f"Unexpected error: {str(e)}")

    except Exception as e:
        print(f"❌ Error downloading images: {e}")
        traceback.print_exc()
        return create_helpful_placeholder_images(output_folder, max_images, f"Download failed: {str(e)}")

def create_helpful_placeholder_images(output_folder, count, error_message):
    """
    Create placeholder images with helpful error messages
    
    Args:
        output_folder: Folder to save placeholder images
        count: Number of placeholder images to create
        error_message: Error message to include in logs
    
    Returns:
        list: Paths to created placeholder images
    """
    print(f"🎨 Creating {count} placeholder images...")
    print(f"📝 Reason: {error_message}")
    
    image_paths = []
    for i in range(count):
        img_path = os.path.join(output_folder, f"{i}.jpg")
        try:
            # Try multiple placeholder services
            placeholder_urls = [
                f"https://picsum.photos/640/360?random={i}",  # Lorem Picsum
                f"https://dummyimage.com/640x360/4CAF50/ffffff&text=Image+{i+1}",  # DummyImage
                "https://via.placeholder.com/640x360/2196F3/ffffff?text=Placeholder"  # Placeholder.com
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            for placeholder_url in placeholder_urls:
                try:
                    response = requests.get(placeholder_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    with open(img_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ Created placeholder image {i + 1}")
                    image_paths.append(img_path)
                    break  # Success, move to next image
                except Exception as placeholder_error:
                    print(f"⚠️  Placeholder service failed: {placeholder_error}")
                    continue  # Try next placeholder service
            else:
                # All placeholder services failed, create a simple colored image
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    
                    # Create a simple colored image with text
                    img = Image.new('RGB', (640, 360), color=(76, 175, 80))  # Green background
                    draw = ImageDraw.Draw(img)
                    
                    try:
                        # Try to use a system font
                        font = ImageFont.truetype("arial.ttf", 24)
                    except:
                        # Fallback to default font
                        font = ImageFont.load_default()
                    
                    text = f"Placeholder {i + 1}"
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    # Center the text
                    x = (640 - text_width) // 2
                    y = (360 - text_height) // 2
                    
                    draw.text((x, y), text, fill=(255, 255, 255), font=font)
                    img.save(img_path, "JPEG")
                    print(f"✅ Created fallback placeholder image {i + 1}")
                    image_paths.append(img_path)
                except Exception as fallback_error:
                    print(f"❌ Failed to create fallback placeholder: {fallback_error}")
                    
        except Exception as e:
            print(f"❌ Failed to create placeholder image {i}: {e}")

    return image_paths

def create_placeholder_images(output_folder, count, start_index=0):
    """
    Create placeholder images for padding
    
    Args:
        output_folder: Folder to save images
        count: Number of images to create
        start_index: Starting index for filenames
    
    Returns:
        list: Paths to created images
    """
    image_paths = []
    for i in range(count):
        img_path = os.path.join(output_folder, f"{start_index + i}.jpg")
        try:
            response = requests.get(f"https://picsum.photos/640/360?random={start_index + i}", timeout=10)
            response.raise_for_status()
            with open(img_path, "wb") as f:
                f.write(response.content)
            print(f"✅ Created placeholder image {start_index + i}")
            image_paths.append(img_path)
        except Exception as e:
            print(f"❌ Failed to create placeholder image: {e}")
            
    return image_paths

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



