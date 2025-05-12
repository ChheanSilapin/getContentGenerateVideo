import os
import requests
from PIL import Image
from moviepy.editor import ImageClip, ColorClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip
import traceback

# Add debugging to identify the file not found error
print("Loading create_video module...")

def downloadImage(title, content, websiteUrl, folder_name="images"):
    """Download images from a website URL"""
    print(f"downloadImage called with folder_name: {folder_name}")
    os.makedirs(folder_name, exist_ok=True)
    
    # Add proper headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': websiteUrl
    }
    
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
    
    for filename in sorted(os.listdir(folderName)):
        if filename.endswith((".jpg", ".jpeg", ".png")):
            img_path = os.path.join(folderName, filename)
            
            try:
                # Create a black background with target dimensions
                bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=3)
                
                # Load the image
                img = ImageClip(img_path)
                
                # Get original image dimensions
                img_width, img_height = img.size
                print(f"Processing image {filename}: {img_width}x{img_height}")
                
                # Calculate scaling factor to fit image within the frame without cropping
                # We'll scale based on the dimension that requires more scaling
                width_ratio = target_width / img_width
                height_ratio = target_height / img_height
                
                # Use the smaller ratio to ensure the entire image fits
                scale_factor = min(width_ratio, height_ratio) * 0.9  # 90% of max size for a small margin
                
                # Resize the image while maintaining aspect ratio
                resized_img = img.resize(scale_factor)
                print(f"Resized to: {resized_img.size[0]}x{resized_img.size[1]}")
                
                # Set duration and position the image in the center
                final_img = resized_img.set_duration(3).set_position(("center", "center"))
                
                # Composite the image on the background
                final_clip = CompositeVideoClip([bg, final_img])
                image_clips.append(final_clip)
                
            except Exception as e:
                print(f"Error processing image {filename}: {e}")
                traceback.print_exc()
    
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
    
    # Write the final video file
    print(f"Writing video to {outputVideo}")
    video.write_videofile(outputVideo, fps=frameRarte)
    
    return outputVideo
