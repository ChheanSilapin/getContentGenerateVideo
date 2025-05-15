import os
import requests
import urllib.parse
from PIL import Image
from moviepy.editor import ImageClip, ColorClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip
import traceback



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

def createSideShowWithFFmpeg(folderName, title, content, audioFile, outputVideo, zoomFactor=0.5, frameRarte=25, use_gpu_encoding=False):
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

    # Load audio first to get duration
    try:
        audio = AudioFileClip(audioFile)
        audio_duration = audio.duration
        print(f"Audio duration: {audio_duration} seconds")
    except Exception as e:
        print(f"Error loading audio: {e}")
        audio_duration = 15  # Default duration if audio can't be loaded
        audio = None

    # Get all image files from the folder
    image_files = []
    for filename in sorted(os.listdir(folderName)):
        if filename.endswith((".jpg", ".jpeg", ".png")):
            image_files.append(os.path.join(folderName, filename))

    if not image_files:
        print("No images found in folder")
        return None

    # Calculate how many times we need to loop through images to match audio duration
    # Each image will be shown for 3 seconds by default
    image_count = len(image_files)
    single_loop_duration = image_count * 3  # 3 seconds per image
    
    # If audio is longer than one loop of images, we'll need multiple loops
    loops_needed = max(1, int(audio_duration / single_loop_duration) + 1)
    
    print(f"Using {image_count} images, looping {loops_needed} times to match {audio_duration}s audio")
    
    # Process each image, applying effects
    for loop in range(loops_needed):
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

                    # Calculate scaling factor to fit image within the frame without cropping
                    width_ratio = target_width / img_width
                    height_ratio = target_height / img_height

                    # Use the smaller ratio to ensure the entire image fits
                    scale_factor = min(width_ratio, height_ratio) * 0.9  # 90% of max size for a small margin

                    # Apply zoom effect - start slightly smaller and zoom in
                    # Vary the effect based on the image index to create diversity
                    img_index = int(filename.split('.')[0])
                    
                    # Choose effect type based on image index
                    effect_type = img_index % 4
                    
                    if effect_type == 0:
                        # Zoom in effect
                        start_scale = scale_factor * 0.8
                        end_scale = scale_factor * 1.1
                        
                        def zoom(t):
                            current_scale = start_scale + (end_scale - start_scale) * t / 3
                            new_w = int(img_width * current_scale)
                            new_h = int(img_height * current_scale)
                            return new_w, new_h
                            
                        resized_img = img.resize(zoom)
                    elif effect_type == 1:
                        # Zoom out effect
                        start_scale = scale_factor * 1.1
                        end_scale = scale_factor * 0.9
                        
                        def zoom_out(t):
                            current_scale = start_scale + (end_scale - start_scale) * t / 3
                            new_w = int(img_width * current_scale)
                            new_h = int(img_height * current_scale)
                            return new_w, new_h
                            
                        resized_img = img.resize(zoom_out)
                    elif effect_type == 2:
                        # Pan from left to right
                        new_width = int(img_width * scale_factor)
                        new_height = int(img_height * scale_factor)
                        
                        # First resize the image
                        from moviepy.video.fx.resize import resize
                        resized_img = resize(img, width=new_width, height=new_height)
                        
                        # Then apply the pan effect
                        from moviepy.video.fx.scroll import scroll
                        resized_img = scroll(resized_img, w=target_width, h=target_height, x_speed=10, y_speed=0)
                    else:
                        # Simple fade in/out with fixed size
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

                    # Set duration and position the image in the center
                    final_img = resized_img.set_duration(3).set_position(("center", "center"))
                    
                    # Apply fade in/out effect
                    from moviepy.video.fx.fadein import fadein
                    from moviepy.video.fx.fadeout import fadeout
                    final_img = fadein(final_img, 0.5)
                    final_img = fadeout(final_img, 0.5)

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
                
                # Check if we have enough clips to match audio duration
                total_duration = sum(clip.duration for clip in image_clips)
                if total_duration >= audio_duration:
                    break
        
        # Check if we have enough clips to match audio duration
        total_duration = sum(clip.duration for clip in image_clips)
        if total_duration >= audio_duration:
            break

    # If no images were processed successfully, create a blank clip
    if not image_clips:
        print("No images were processed successfully. Creating a blank video.")
        blank = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=3)
        image_clips = [blank]

    # Concatenate all image clips
    video = concatenate_videoclips(image_clips, method="compose")

    # Trim video to match audio duration exactly
    if video.duration > audio_duration:
        video = video.subclip(0, audio_duration)
    
    # Load audio
    try:
        if audio is None:
            audio = AudioFileClip(audioFile)
        # If audio is longer than video, extend video duration
        if audio.duration > video.duration:
            print(f"Audio ({audio.duration}s) is longer than video ({video.duration}s). Extending video duration.")
            # This shouldn't happen now with our looping, but just in case
            # Create a blank clip to extend the video
            blank = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=audio.duration - video.duration)
            video = concatenate_videoclips([video, blank])
    except Exception as e:
        print(f"Error loading audio: {e}")
        # Create silent audio
        audio = AudioClip(lambda t: 0, duration=video.duration)

    # Set audio to video
    video = video.set_audio(audio)

    # Write the final video file with appropriate encoding
    print(f"Writing video to {outputVideo}")

    # Always use CPU encoding for final output to ensure compatibility
    video.write_videofile(outputVideo, fps=frameRarte, codec='libx264')

    return outputVideo
