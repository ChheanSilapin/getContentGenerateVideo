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
from services.video_service import merge_video_with_subtitles

class VideoGeneratorModel:
    """Model class to handle the video generation logic"""
    def __init__(self):
        self.text_input = None
        self.image_source = None
        self.website_url = None
        self.local_folder = None
        self.selected_images = []
        
    def generate_video(self, stop_event=None):
        """
        Generate a video from text and images
        
        Args:
            stop_event: Threading event to signal process termination
            
        Returns:
            tuple: (subtitle_path, video_path, output_dir) or (None, None, None) on failure
        """
        if not self.text_input:
            print("No text input provided.")
            return None, None, None
            
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("output", f"video_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory: {output_dir}")
        
        # Step 1: Generate Audio
        print("\n--- Step 1: Generating Audio ---")
        audio_file = os.path.join(output_dir, "voice.mp3")
        if not generate_audio(self.text_input, output_file=audio_file):
            print("ERROR: Audio generation failed.")
            return None, None, None
            
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            return None, None, None
            
        # Step 2: Get Images
        print("\n--- Step 2: Getting Images ---")
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        title = "Video"
        content = self.text_input
        
        if self.image_source == "1":  # Website URL
            print(f"Downloading images from: {self.website_url}")
            folderName, title, content = download_images(self.website_url, images_dir, stop_event)
            if not folderName:
                print("ERROR: Image download failed.")
                return None, None, None
        else:  # Local folder
            if self.selected_images:
                print(f"Using {len(self.selected_images)} selected images")
                folderName = copy_selected_images(self.selected_images, images_dir)
            else:
                print(f"Using images from folder: {self.local_folder}")
                folderName = copy_selected_images(None, images_dir, self.local_folder)
                
            if not folderName:
                print("ERROR: No images found or copied.")
                return None, None, None
                
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            return None, None, None
            
        # Step 3: Create Video
        print("\n--- Step 3: Creating Video ---")
        video_file = os.path.join(output_dir, "video.mp4")
        if not create_slideshow(folderName, title, content, audio_file, video_file):
            print("ERROR: Video creation failed.")
            return None, None, None
            
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            return None, None, None
            
        # Step 4: Generate Subtitles
        print("\n--- Step 4: Generating Subtitles ---")
        subtitle_file = os.path.join(output_dir, "subtitles.ass")
        subtitlePath = generate_subtitles(
            video_path=video_file, 
            output_file=subtitle_file, 
            audio_file=audio_file
        )
        
        if subtitlePath:
            print(f"Subtitles generated: {subtitlePath}")
            return subtitlePath, video_file, output_dir
        else:
            print("ERROR: Subtitle generation failed.")
            return None, None, None
            
    def finalize_video(self, subtitlePath, videoPath, output_dir, stop_event=None):
        """
        Finalize the video by merging video and subtitles
        
        Args:
            subtitlePath: Path to the subtitle file
            videoPath: Path to the video file
            output_dir: Directory to save the output
            stop_event: Threading event to signal process termination
            
        Returns:
            str: Path to the final video or None on failure
        """
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("Process stopped by user.")
            return None
            
        if subtitlePath and videoPath and output_dir:
            print("\n--- Final Step: Merging Video and Subtitles ---")
            final_output = os.path.join(output_dir, "final_output.mp4")
            print(f"Merging video: {videoPath}")
            print(f"With subtitles: {subtitlePath}")
            
            result = merge_video_with_subtitles(videoPath, subtitlePath, output_file=final_output)
            if result:
                print(f"Final video with subtitles created: {result}")
                print(f"All output files are in directory: {output_dir}")
                return result
            else:
                print("Failed to create final video with subtitles")
                return None
        return None
