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
from services.video_service import create_slideshow
from services.subtitle_service import generate_subtitles
from Final_Video import merge_video_subtitle
from utils.helpers import get_title_content  # Import the missing function

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
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use custom output folder if provided
        if self.output_folder and os.path.isdir(self.output_folder):
            output_dir = os.path.join(self.output_folder, f"video_{timestamp}")
        else:
            output_dir = os.path.join("output", f"video_{timestamp}")
            
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory: {output_dir}")
        self.update_progress(5, "Created output directory")
        
        # Step 1: Generate Audio
        print("\n--- Step 1: Generating Audio ---")
        self.update_progress(10, "Generating audio...")
        audio_file = os.path.join(output_dir, "voice.mp3")
        if not generate_audio(self.text_input, output_file=audio_file):
            print("ERROR: Audio generation failed.")
            self.update_progress(0, "Audio generation failed")
            return None, None, None
            
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            return None, None, None
            
        self.update_progress(25, "Audio generated successfully")
        
        # Step 2: Get images
        print("\n--- Step 2: Getting Images ---")
        self.update_progress(30, "Getting images...")
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        if self.image_source == "1":  # Website URL
            print(f"Downloading images from: {self.website_url}")
            self.update_progress(35, f"Downloading images from: {self.website_url}")
            if not download_images(self.website_url, images_dir):
                print("ERROR: Failed to download images.")
                self.update_progress(0, "Failed to download images")
                return None, None, None
        else:  # Local folder or selected images
            if self.selected_images:
                print(f"Using {len(self.selected_images)} selected images")
                self.update_progress(35, f"Copying {len(self.selected_images)} selected images")
                if not copy_selected_images(self.selected_images, images_dir):
                    print("ERROR: Failed to copy selected images.")
                    self.update_progress(0, "Failed to copy selected images")
                    return None, None, None
            else:
                print(f"Copying images from: {self.local_folder}")
                self.update_progress(35, f"Copying images from: {self.local_folder}")
                if not copy_images_from_folder(self.local_folder, images_dir):
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
        
        # Pass the processing option to the create_slideshow function
        if not create_slideshow(images_dir, title, content, audio_file, video_file, use_gpu=(self.processing_option == "gpu")):
            print("ERROR: Failed to create video.")
            self.update_progress(0, "Failed to create video")
            return None, None, None
            
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            self.update_progress(0, "Process stopped by user")
            return None, None, None
            
        self.update_progress(75, "Video created successfully")
        
        # Step 4: Generate subtitles
        print("\n--- Step 4: Generating Subtitles ---")
        self.update_progress(80, "Generating subtitles...")
        subtitle_file = os.path.join(output_dir, "subtitles.ass")
        
        if not generate_subtitles(video_file, subtitle_file, audio_file):
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
            # Keep only the necessary files
            if self.image_source == "1":  # Website URL
                # For website URL, keep images, final video, voice.mp3, and subtitles
                pass  # No need to delete anything
            else:  # Local folder or selected images
                # For local folder, keep only final video, voice.mp3, and subtitles
                images_dir = os.path.join(output_dir, "images")
                if os.path.exists(images_dir):
                    import shutil
                    shutil.rmtree(images_dir)
                    print(f"Removed images directory: {images_dir}")
                
                # Remove the slideshow.mp4 file (intermediate file)
                slideshow_file = os.path.join(output_dir, "slideshow.mp4")
                if os.path.exists(slideshow_file):
                    os.remove(slideshow_file)
                    print(f"Removed intermediate video: {slideshow_file}")
        except Exception as e:
            print(f"Error organizing output folder: {e}")





