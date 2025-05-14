import os
import requests
import urllib.parse
from PIL import Image
from moviepy.editor import ImageClip, ColorClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip
import traceback

# Add debugging to identify the file not found error
print("Loading create_video module...")

def downloadImage(title, content, websiteUrl, folder_name="images", placeholder_count=4):
    """
    Download images from a website URL
    
    Parameters:
    - title: Title of the content
    - content: Content text
    - websiteUrl: URL to download images from
    - folder_name: Folder to save images to
    - placeholder_count: Number of placeholder images to create for direct image URLs (0 to disable)
    """
    print(f"downloadImage called with folder_name: {folder_name}")
    os.makedirs(folder_name, exist_ok=True)
    
    # Add proper headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': websiteUrl
    }
    
    if 'pinterest.com' in websiteUrl:
        headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.pinterest.com/',
            'sec-ch-ua': '"Google Chrome";v="91", "Chromium";v="91", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'image',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-site': 'cross-site'
        })
    
    # Check if the URL is a direct image file
    parsed_url = urllib.parse.urlparse(websiteUrl)
    path = parsed_url.path.lower()
    if path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
        print("Direct image URL detected, downloading as first image")
        img_path = os.path.join(folder_name, "0.jpg")
        try:
            img_response = requests.get(websiteUrl, headers=headers, timeout=10)
            img_response.raise_for_status()
            with open(img_path, "wb") as f:
                f.write(img_response.content)
            print(f"Downloaded direct image to {img_path}")
            
            # Create placeholder images if requested
            if placeholder_count > 0:
                print(f"Creating {placeholder_count} placeholder images")
                for i in range(1, placeholder_count + 1):
                    placeholder_path = os.path.join(folder_name, f"{i}.jpg")
                    try:
                        response = requests.get("https://dummyimage.com/640x360/eee/aaa", timeout=10)
                        response.raise_for_status()
                        with open(placeholder_path, "wb") as f:
                            f.write(response.content)
                        print(f"Created placeholder image {i}")
                    except Exception as e:
                        print(f"Failed to download placeholder image: {e}")
            
            return folder_name
        except Exception as e:
            print(f"Failed to download direct image: {e}")
    
    # Regular website processing
    try:
        response = requests.get(websiteUrl, headers=headers, timeout=10)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        img_tags = soup.find_all('img')
        img_urls = [img.get('src') for img in img_tags if img.get('src')]
        
        for i, img_url in enumerate(img_urls[:5]):
            if not img_url.startswith(('http://', 'https://')):
                img_url = f"{websiteUrl.rstrip('/')}/{img_url.lstrip('/')}"
            
            img_path = os.path.join(folder_name, f"{i}.jpg")
            try:
                print(f"Downloading image from: {img_url}")
                # Use the same headers for image requests
                img_response = requests.get(img_url, headers=headers, timeout=10)
                img_response.raise_for_status()
                with open(img_path, "wb") as f:
                    f.write(img_response.content)
                print(f"Downloaded image {i+1} to {img_path}")
            except Exception as e:
                print(f"Failed to download image {i}: {e}")
                # Try to download a placeholder image
                try:
                    response = requests.get("https://dummyimage.com/640x360/eee/aaa", timeout=10)
                    response.raise_for_status()
                    with open(img_path, "wb") as f:
                        f.write(response.content)
                    print(f"Used placeholder for image {i}")
                except Exception as e:
                    print(f"Failed to download placeholder image: {e}")
            
    except Exception as e:
        print(f"Failed to download images: {e}")
        # Fallback to placeholder images
        for i in range(3):
            img_path = os.path.join(folder_name, f"{i}.jpg")
            try:
                response = requests.get("https://dummyimage.com/640x360/eee/aaa", timeout=10)
                response.raise_for_status()
                with open(img_path, "wb") as f:
                    f.write(response.content)
                print(f"Created placeholder image {i}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to download image {i}: {e}")
    
    return folder_name

def createSideShowWithFFmpeg(folderName, title, content, audioFile, outputVideo, zoomFactor=0.5, frameRarte=25):
    image_clips = [] 
    target_width, target_height = 720, 1280  # Target dimensions for vertical video
    
    # Check if GPU is enabled
    use_gpu = os.environ.get("CUDA_VISIBLE_DEVICES", "") != ""
    if use_gpu:
        try:
            # Try to import moviepy with GPU support
            from moviepy.video.io.VideoFileClip import VideoFileClip
            print("MoviePy GPU acceleration enabled")
        except ImportError:
            print("MoviePy GPU acceleration not available, falling back to CPU")
            use_gpu = False
    
    for filename in sorted(os.listdir(folderName)):
        if filename.endswith((".jpg", ".jpeg", ".png")):
            img_path = os.path.join(folderName, filename)
            
            try:
                # Create a black background with target dimensions
                bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=3)
                
                # Load the image and convert to RGB
                try:
                    # First try to open with PIL to check channels
                    pil_img = Image.open(img_path)
                    # Convert to RGB mode to ensure 3 channels
                    if pil_img.mode != 'RGB':
                        print(f"Converting image {filename} from {pil_img.mode} to RGB")
                        pil_img = pil_img.convert('RGB')
                        # Save the converted image
                        converted_path = os.path.join(folderName, f"converted_{filename}")
                        pil_img.save(converted_path)
                        img = ImageClip(converted_path)
                    else:
                        img = ImageClip(img_path)
                except Exception as pil_error:
                    print(f"Error with PIL: {pil_error}, trying direct ImageClip")
                    img = ImageClip(img_path)
                
                # Get original image dimensions
                img_width, img_height = img.size
                print(f"Processing image {filename}: {img_width}x{img_height}")
                
                # Calculate scaling factor to fit image within the frame without cropping
                width_ratio = target_width / img_width
                height_ratio = target_height / img_height
                
                # Use the smaller ratio to ensure the entire image fits
                scale_factor = min(width_ratio, height_ratio) * 0.9  # 90% of max size for a small margin
                
                # Resize the image
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                
                # Use the resize method with proper parameters
                try:
                    resized_img = img.resize((new_width, new_height))
                except Exception as resize_error:
                    print(f"Error resizing with resize method: {resize_error}")
                    # Alternative approach using fx.resize
                    from moviepy.video.fx.resize import resize
                    resized_img = resize(img, width=new_width, height=new_height)
                
                print(f"Resized to: {resized_img.size[0]}x{resized_img.size[1]}")
                
                # Set duration and position the image in the center
                final_img = resized_img.set_duration(3).set_position(("center", "center"))
                
                # Composite the image on the background
                final_clip = CompositeVideoClip([bg, final_img])
                image_clips.append(final_clip)
                
            except Exception as e:
                print(f"Error processing image {filename}: {e}")
                traceback.print_exc()
                # Create a fallback clip with error message
                try:
                    bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=3)
                    image_clips.append(bg)
                except Exception as bg_error:
                    print(f"Failed to create fallback clip: {bg_error}")
    
    # If no images were processed successfully, create a blank clip
    if not image_clips:
        print("No images were processed successfully. Creating a blank video.")
        blank = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=3)
        image_clips = [blank]
    
    # Concatenate all image clips
    video = concatenate_videoclips(image_clips, method="compose")
    
    # Add audio
    audio = AudioFileClip(audioFile)
    
    # Adjust video length to match audio
    if audio.duration > video.duration:
        # If audio is longer, loop the video
        n_loops = int(audio.duration / video.duration) + 1
        video = concatenate_videoclips([video] * n_loops)
        video = video.subclip(0, audio.duration)
    else:
        # If video is longer, trim it to match audio
        video = video.subclip(0, audio.duration)
    
    # Set audio to video
    video = video.set_audio(audio)
    
    # Write the final video file with GPU acceleration if available
    print(f"Writing video to {outputVideo}")
    if use_gpu:
        # Use hardware acceleration if available
        video.write_videofile(outputVideo, fps=frameRarte, codec='h264_nvenc')
    else:
        # Use standard encoding
        video.write_videofile(outputVideo, fps=frameRarte)
    
    return outputVideo
