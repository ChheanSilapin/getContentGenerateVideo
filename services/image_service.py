"""
Image service functions for processing images
Website image download functionality removed - no longer needed
"""
import os
import shutil
import traceback
from PIL import Image

# Import from utils
from utils.helpers import ensure_directory_exists, is_image_file

# Website image download functionality removed - no longer need SUPPORTED_IMAGE_EXTENSIONS

   

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
            # Create a simple colored image with text (no web requests)
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
            print(f"✅ Created placeholder image {i + 1}")
            image_paths.append(img_path)

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
            # Create a simple colored image (no web requests)
            from PIL import Image, ImageDraw, ImageFont

            # Create different colored backgrounds for variety
            colors = [(76, 175, 80), (33, 150, 243), (255, 152, 0), (156, 39, 176), (244, 67, 54)]
            color = colors[i % len(colors)]

            img = Image.new('RGB', (640, 360), color=color)
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()

            text = f"Image {start_index + i + 1}"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            # Center the text
            x = (640 - text_width) // 2
            y = (360 - text_height) // 2

            draw.text((x, y), text, fill=(255, 255, 255), font=font)
            img.save(img_path, "JPEG")
            print(f"✅ Created placeholder image {start_index + i}")
            image_paths.append(img_path)
        except Exception as e:
            print(f"❌ Failed to create placeholder image: {e}")

    return image_paths

# Website image download functions removed - no longer needed

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
                    # URL downloads no longer supported
                    print(f"URL downloads not supported: {img_path}")
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



