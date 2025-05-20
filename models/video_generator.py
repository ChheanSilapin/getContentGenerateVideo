"""
VideoGeneratorModel - Core model for video generation process
"""
import os
import sys
import urllib.parse
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.audio_service import generate_audio
from services.image_service import download_images, copy_selected_images
from services.video_service import create_enhanced_slideshow
from services.subtitle_service import generate_subtitles
from Final_Video import merge_video_subtitle
# Define get_title_content function directly to avoid import issues
def get_title_content(text):
    """
    Extract title and content from text

    Args:
        text: Input text

    Returns:
        tuple: (title, content)
    """
    lines = text.strip().split('\n')

    # If there's only one line, use it as both title and content
    if len(lines) == 1:
        return lines[0], lines[0]

    # Use the first line as title and the rest as content
    title = lines[0]
    content = '\n'.join(lines[1:])

    return title, content

class VideoGeneratorModel:
    """Model for handling video generation"""
    def __init__(self):
        """Initialize the model"""
        self.text_input = None
        self.image_source = None
        self.website_url = None
        self.local_folder = None
        self.selected_images = []
        self.output_folder = None
        self.processing_option = "cpu"  # Default to CPU
        self.progress_callback = None
        self.batch_jobs = []  # List to store multiple generation jobs
        self.current_job_index = 0
        
        # Enhancement options
        self.use_effects = True
        self.zoom_effect = True
        self.fade_effect = True
        self.enhancement_options = {
            "color_correction": True,
            "background_replacement": False,
            "audio_enhancement": True,
            "motion_graphics": False,
            "framing": True,
            "color_correction_intensity": 1.0,
            "framing_crop_percent": 0.95,
            "audio_volume_boost": 1.2,
            "motion_graphics_opacity": 0.15,
            "contrast": 1.1,
            "brightness": 0.05,
            "saturation": 1.2,
            "sharpness": 1.0,
            "noise_reduction": True
        }

    def set_progress_callback(self, callback):
        """Set a callback function for progress updates"""
        self.progress_callback = callback

    def update_progress(self, value, message=None):
        """Update progress value and message"""
        if self.progress_callback:
            self.progress_callback(value, message)

    def generate_video(self, stop_event=None):
        """
        Generate a video from text and images

        Args:
            stop_event: Threading event to stop the process

        Returns:
            tuple: (subtitle_path, video_path, output_dir)
        """
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            return None, None, None
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Store the stop_event as an instance variable so other methods can access it
        self.stop_event = stop_event

        # Use custom output folder if provided
        if self.output_folder and os.path.isdir(self.output_folder):
            output_dir = os.path.join(self.output_folder, f"video_{timestamp}")
        else:
            output_dir = os.path.join("output", f"video_{timestamp}")

        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
        
        # Store output_dir as instance variable for cleanup if needed
        self.current_output_dir = output_dir

        # Create subdirectories
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        # Step 1: Generate audio from text
        print("\n--- Step 1: Generating Audio ---")
        self.update_progress(10, "Generating audio from text...")
        audio_file = os.path.join(output_dir, "voice.mp3")
        if not generate_audio(self.text_input, audio_file):
            print("ERROR: Failed to generate audio.")
            self.update_progress(0, "Failed to generate audio")
            return None, None, None

        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            return None, None, None

        self.update_progress(30, "Audio generated successfully")

        # Step 2: Get images
        print("\n--- Step 2: Processing Images ---")

        if self.image_source == "1":  # Website URL
            # Skip downloading images if we already have selected images
            if not self.selected_images:
                print("ERROR: No images selected from website.")
                self.update_progress(0, "No images selected from website")
                return None, None, None
            
            print(f"Using {len(self.selected_images)} selected images from website")
            self.update_progress(35, f"Copying {len(self.selected_images)} selected images")
            if not copy_selected_images(self.selected_images, images_dir):
                print("ERROR: Failed to copy selected images.")
                self.update_progress(0, "Failed to copy selected images")
                return None, None, None
        elif self.image_source == "3":  # Selected images
            print(f"Using {len(self.selected_images)} selected images")
            self.update_progress(35, f"Copying {len(self.selected_images)} selected images")
            if not copy_selected_images(self.selected_images, images_dir):
                print("ERROR: Failed to copy selected images.")
                self.update_progress(0, "Failed to copy selected images")
                return None, None, None
        else:  # Local folder
            print(f"Copying images from: {self.local_folder}")
            self.update_progress(35, f"Copying images from: {self.local_folder}")
            # Use copy_selected_images instead of copy_images_from_folder
            import glob
            # Get all image files from the folder
            image_files = []
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                image_files.extend(glob.glob(os.path.join(self.local_folder, f"*{ext}")))
                image_files.extend(glob.glob(os.path.join(self.local_folder, f"*{ext.upper()}")))

            if not image_files:
                print("ERROR: No image files found in folder.")
                self.update_progress(0, "No image files found in folder")
                return None, None, None

            if not copy_selected_images(image_files, images_dir):
                print("ERROR: Failed to copy images from folder.")
                self.update_progress(0, "Failed to copy images from folder")
                return None, None, None

        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            return None, None, None

        self.update_progress(50, "Images processed successfully")

        # Step 3: Create video
        print("\n--- Step 3: Creating Video ---")
        self.update_progress(55, "Creating video...")
        video_file = os.path.join(output_dir, "slideshow.mp4")
        title, content = get_title_content(self.text_input)

        # Get effect settings
        use_effects = getattr(self, 'use_effects', True)
        zoom_effect = getattr(self, 'zoom_effect', True)
        fade_effect = getattr(self, 'fade_effect', True)

        # Pass the processing option and effect settings to the create_enhanced_slideshow function
        result = create_enhanced_slideshow(
            images_dir, 
            title, 
            content, 
            audio_file, 
            video_file, 
            use_gpu=(self.processing_option == "gpu"),
            use_effects=use_effects,
            zoom_effect=zoom_effect,
            fade_effect=fade_effect,
            enhance=True,  # Enable enhancements
            enhancement_options=getattr(self, 'enhancement_options', None),
            stop_event=stop_event  # Pass the stop event
        )

        # Check if the process was stopped by user
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            self._cleanup_on_stop()  # Clean up files
            return None, None, None

        # Only report an error if the result is False (not stopped by user)
        if not result:
            print("ERROR: Failed to create video.")
            self.update_progress(0, "Failed to create video")
            return None, None, None

        self.update_progress(70, "Video created successfully")

        # Step 4: Generate subtitles
        print("\n--- Step 4: Generating Subtitles ---")
        self.update_progress(75, "Generating subtitles...")
        subtitle_file = os.path.join(output_dir, "subtitles.ass")
        if not generate_subtitles(self.text_input, video_file, audio_file, subtitle_file):
            print("ERROR: Failed to generate subtitles.")
            self.update_progress(0, "Failed to generate subtitles")
            return None, None, None

        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            return None, None, None

        self.update_progress(90, "Subtitles generated successfully")

        return subtitle_file, video_file, output_dir

    def finalize_video(self, subtitlePath, videoPath, output_dir, stop_event=None):
        """
        Finalize the video by merging with subtitles

        Args:
            subtitlePath: Path to subtitle file
            videoPath: Path to video file
            output_dir: Output directory
            stop_event: Threading event to stop the process

        Returns:
            str: Path to final video
        """
        print("\n--- Step 5: Finalizing Video ---")
        self.update_progress(95, "Finalizing video...")
        final_output = os.path.join(output_dir, "final_output.mp4")

        result = merge_video_subtitle(videoPath, subtitlePath, final_output)

        if result:
            print(f"Video generated successfully: {result}")
            self.update_progress(100, f"Video generated successfully: {os.path.basename(result)}")

            # Clean up the output folder based on image source
            self._organize_output_folder(output_dir)

            return result
        else:
            print("Failed to finalize video")
            self.update_progress(0, "Failed to finalize video")
            return None

    def _organize_output_folder(self, output_dir):
        """
        Organize the output folder based on image source
        
        Args:
            output_dir: Output directory
        """
        try:
            # Keep only the final video and downloaded images
            # Remove intermediate files but preserve the images directory
            
            # Always keep the final output video
            final_video = os.path.join(output_dir, "final_output.mp4")
            
            # Files to remove (intermediate files)
            files_to_remove = [
                os.path.join(output_dir, "slideshow.mp4"),  # Intermediate video
                os.path.join(output_dir, "subtitles.ass"),  # Subtitle file
                os.path.join(output_dir, "voice.mp3")       # Voice file
            ]
            
            # Remove intermediate files
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Removed intermediate file: {file_path}")
            
            # Handle images based on source
            images_dir = os.path.join(output_dir, "images")
            if self.image_source == "1":  # Website URL
                # Keep downloaded images from website
                print(f"Keeping downloaded images in: {images_dir}")
            elif self.image_source == "2":  # Local folder
                # Remove images directory since they're copies from local folder
                if os.path.exists(images_dir):
                    import shutil
                    shutil.rmtree(images_dir)
                    print(f"Removed images directory (local folder source): {images_dir}")
            elif self.image_source == "3":  # Selected images
                # Keep selected images if they were downloaded, remove if they were from local folder
                # This is determined by checking if the images are in the selected_images list
                # and if they have a web URL pattern
                
                # Check if any selected image has a URL pattern
                has_downloaded_images = any(img.startswith(('http://', 'https://')) for img in self.selected_images)
                
                if not has_downloaded_images:
                    # If all images were local, remove the images directory
                    if os.path.exists(images_dir):
                        import shutil
                        shutil.rmtree(images_dir)
                        print(f"Removed images directory (local selected images): {images_dir}")
                else:
                    print(f"Keeping downloaded selected images in: {images_dir}")
                    
        except Exception as e:
            print(f"Error organizing output folder: {e}")

    def preview_images_from_url(self, url):
        """
        Download images from URL for preview

        Args:
            url: Website URL

        Returns:
            list: List of image paths
        """
        from services.image_service import download_images_for_preview

        # Create a temporary directory
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix="preview_")

        # Download images
        self.update_progress(10, f"Downloading images from: {url}")
        image_paths = download_images_for_preview(url, temp_dir)

        if not image_paths:
            self.update_progress(0, "Failed to download images for preview")
            return []

        self.update_progress(30, f"Downloaded {len(image_paths)} images for preview")
        return image_paths

    def add_batch_job(self, text_input, image_source, selected_images=None, website_url=None, local_folder=None):
        """Add a job to the batch processing queue"""
        job = {
            "text_input": text_input,
            "image_source": image_source,
            "selected_images": selected_images or [],
            "website_url": website_url or "",
            "local_folder": local_folder or "",
            "status": "pending"
        }
        self.batch_jobs.append(job)
        return len(self.batch_jobs)  # Return job ID (1-based index)
    
    def process_batch(self, stop_event=None):
        """Process all jobs in the batch queue"""
        results = []
        self.current_job_index = 0
        
        for i, job in enumerate(self.batch_jobs):
            if stop_event and stop_event.is_set():
                break
                
            self.current_job_index = i
            # Update model with current job parameters
            self.text_input = job["text_input"]
            self.image_source = job["image_source"]
            self.selected_images = job["selected_images"]
            self.website_url = job["website_url"]
            self.local_folder = job["local_folder"]
            
            # Update progress with job information
            self.update_progress(0, f"Starting job {i+1}/{len(self.batch_jobs)}")
            
            # Process the job
            subtitle_path, video_path, output_dir = self.generate_video(stop_event)
            if subtitle_path and video_path and output_dir:
                final_video = self.finalize_video(subtitle_path, video_path, output_dir, stop_event)
                job["status"] = "completed" if final_video else "failed"
                job["output_path"] = final_video if final_video else None
                results.append((job, final_video))
            else:
                job["status"] = "failed"
                results.append((job, None))
        
        return results

    def _cleanup_on_stop(self):
        """Clean up files when process is stopped by user"""
        if hasattr(self, 'current_output_dir') and self.current_output_dir:
            try:
                import shutil
                if os.path.exists(self.current_output_dir):
                    print(f"Cleaning up output directory: {self.current_output_dir}")
                    shutil.rmtree(self.current_output_dir)
                    print(f"Removed output directory after stop: {self.current_output_dir}")
            except Exception as e:
                print(f"Warning: Could not clean up output directory: {e}")
