"""
VideoGeneratorModel - Core model for video generation process
"""
import os
import sys
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import config
from config import DEFAULT_ASPECT_RATIO

from services.audio_service import generate_audio
from services.image_service import copy_selected_images
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

        # Video aspect ratio
        self.aspect_ratio = DEFAULT_ASPECT_RATIO

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
            "noise_reduction": True,
            "apply_ffmpeg": False,  # Disable FFmpeg enhancements by default
            "aspect_ratio": DEFAULT_ASPECT_RATIO  # Add aspect ratio to enhancement options
        }

        # Ensure enhancement_options is properly initialized
        self.option_options = self.enhancement_options.copy()

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

            # Make sure the images directory exists
            if not os.path.exists(images_dir):
                os.makedirs(images_dir, exist_ok=True)

            # Copy the selected images to the images directory
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

        # Get aspect ratio settings
        aspect_ratio = getattr(self, 'aspect_ratio', DEFAULT_ASPECT_RATIO)

        # Update enhancement options with current aspect ratio
        enhancement_options = getattr(self, 'enhancement_options', {}).copy()
        enhancement_options['aspect_ratio'] = aspect_ratio

        # Set environment variables for image fitting
        if 'image_fit_method' in enhancement_options:
            os.environ["IMAGE_FIT_METHOD"] = enhancement_options["image_fit_method"]
            print(f"Setting image fit method to: {enhancement_options['image_fit_method']}")
        else:
            os.environ["IMAGE_FIT_METHOD"] = "contain"  # Default

        # Pass the processing option, effect settings, and aspect ratio to the create_enhanced_slideshow function
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
            enhancement_options=enhancement_options,
            stop_event=stop_event,  # Pass the stop event
            aspect_ratio=aspect_ratio  # Pass the aspect ratio
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

        print("\n--- DEBUG: Video creation completed, about to update progress ---")
        self.update_progress(70, "Video created successfully")
        print("\n--- DEBUG: Progress updated, about to start subtitle generation ---")

        # Step 4: Generate subtitles
        print("\n--- Step 4: Generating Subtitles ---")
        self.update_progress(75, "Generating subtitles...")
        subtitle_file = os.path.join(output_dir, "subtitles.ass")
        print(f"\n--- DEBUG: About to call generate_subtitles with: {self.text_input}, {video_file}, {audio_file}, {subtitle_file} ---")
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
        Organize the output folder - clean up images to keep only final video files
        """
        try:
            # Always remove images directory to keep output folder clean
            images_dir = os.path.join(output_dir, "images")
            if os.path.exists(images_dir):
                import shutil
                shutil.rmtree(images_dir)
                print(f"Cleaned up images directory: {images_dir}")

            # Also clean up intermediate files
            intermediate_files = [
                os.path.join(output_dir, "slideshow.mp4"),  # Intermediate video before subtitles
                os.path.join(output_dir, "subtitles.ass"),  # Subtitle file
                os.path.join(output_dir, "voice.mp3")       # Audio file
            ]

            for file_path in intermediate_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"Cleaned up intermediate file: {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"Warning: Could not remove {os.path.basename(file_path)}: {e}")

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
        total_jobs = len(self.batch_jobs)

        for i, job in enumerate(self.batch_jobs):
            if stop_event and stop_event.is_set():
                break

            # Calculate overall progress percentage
            overall_progress = int((i / total_jobs) * 100)
            self.update_progress(overall_progress, f"Starting job {i+1}/{total_jobs}")

            # Set up the current job
            self.text_input = job["text_input"]
            self.image_source = job["image_source"]
            self.selected_images = job["selected_images"].copy() if job["selected_images"] else []
            self.website_url = job["website_url"]
            self.local_folder = job["local_folder"]
            self.processing_option = "cpu"  # Default to CPU for batch processing

            # Process the job
            try:
                job["status"] = "processing"

                # Create a wrapper for the progress callback to show both job progress and overall progress
                original_callback = self.progress_callback

                def job_progress_callback(value, message=None):
                    # Calculate combined progress: base progress for completed jobs + partial progress for current job
                    job_weight = 100 / total_jobs  # Each job contributes this much to total progress
                    # Base progress from completed jobs
                    base_progress = int(i * job_weight)
                    # Current job contribution (scaled by job weight)
                    current_job_progress = int((value / 100) * job_weight)
                    # Combined progress
                    combined_progress = base_progress + current_job_progress

                    job_message = f"Job {i+1}/{total_jobs}: {message}" if message else f"Job {i+1}/{total_jobs}"
                    if original_callback:
                        original_callback(combined_progress, job_message)

                # Temporarily replace the callback
                self.progress_callback = job_progress_callback

                # Generate the video
                subtitle_path, video_path, output_dir = self.generate_video(stop_event)

                if subtitle_path and video_path and output_dir:
                    final_video = self.finalize_video(subtitle_path, video_path, output_dir, stop_event)
                    results.append((job, final_video))
                    job["status"] = "completed"
                    # Update progress to show this job is complete
                    if original_callback:
                        job_complete_progress = int((i + 1) * (100 / total_jobs))
                        original_callback(job_complete_progress, f"Completed job {i+1}/{total_jobs}")
                else:
                    results.append((job, None))
                    job["status"] = "failed"
                    # Update progress to show this job is complete but failed
                    if original_callback:
                        job_complete_progress = int((i + 1) * (100 / total_jobs))
                        original_callback(job_complete_progress, f"Failed job {i+1}/{total_jobs}")

                # Restore the original callback
                self.progress_callback = original_callback

            except Exception as e:
                print(f"Error processing job {i+1}: {e}")
                results.append((job, None))
                job["status"] = "failed"

                # Restore the original callback
                self.progress_callback = original_callback

            # Update the current job index
            self.current_job_index = i + 1

        # Final progress update
        self.update_progress(100, f"Batch processing completed: {len([r for _, r in results if r])} of {total_jobs} successful")
        return results

    def add_video_batch_job(self, text_input, video_file, audio_settings=None):
        """Add a video processing job to the batch queue"""
        job = {
            "text_input": text_input,
            "video_file": video_file,
            "job_type": "video",
            "status": "pending",
            "audio_settings": audio_settings or {"mute_original": False, "original_volume": 0.3}
        }
        self.batch_jobs.append(job)
        return len(self.batch_jobs)  # Return job ID (1-based index)

    def process_video_batch(self, stop_event=None):
        """Process all video jobs in the batch queue"""
        results = []
        self.current_job_index = 0
        total_jobs = len(self.batch_jobs)

        for i, job in enumerate(self.batch_jobs):
            if stop_event and stop_event.is_set():
                break

            # Skip non-video jobs
            if job.get("job_type") != "video":
                continue

            # Calculate overall progress percentage
            overall_progress = int((i / total_jobs) * 100)
            self.update_progress(overall_progress, f"Starting video job {i+1}/{total_jobs}")

            # Set up the current job for video processing
            self.text_input = job["text_input"]
            video_file = job["video_file"]

            # Store audio settings for this job
            self.current_audio_settings = job.get("audio_settings", {"mute_original": False, "original_volume": 0.3})

            # For video processing, we'll extract frames from the video to use as images
            self.processing_option = "cpu"  # Default to CPU for batch processing

            # Process the job
            try:
                job["status"] = "processing"

                # Create a wrapper for the progress callback to show both job progress and overall progress
                original_callback = self.progress_callback

                def job_progress_callback(value, message=None):
                    # Calculate combined progress: base progress for completed jobs + partial progress for current job
                    job_weight = 100 / total_jobs  # Each job contributes this much to total progress
                    # Base progress from completed jobs
                    base_progress = int(i * job_weight)
                    # Current job contribution (scaled by job weight)
                    current_job_progress = int((value / 100) * job_weight)
                    # Combined progress
                    combined_progress = base_progress + current_job_progress

                    job_message = f"Video {i+1}/{total_jobs}: {message}" if message else f"Video {i+1}/{total_jobs}"
                    if original_callback:
                        original_callback(combined_progress, job_message)

                # Temporarily replace the callback
                self.progress_callback = job_progress_callback

                # Process the video file to generate a new video with the prompt
                final_video = self.process_video_with_prompt(video_file, stop_event)

                if final_video:
                    results.append((job, final_video))
                    job["status"] = "completed"
                    # Update progress to show this job is complete
                    if original_callback:
                        job_complete_progress = int((i + 1) * (100 / total_jobs))
                        original_callback(job_complete_progress, f"Completed video {i+1}/{total_jobs}")
                else:
                    results.append((job, None))
                    job["status"] = "failed"
                    # Update progress to show this job is complete but failed
                    if original_callback:
                        job_complete_progress = int((i + 1) * (100 / total_jobs))
                        original_callback(job_complete_progress, f"Failed video {i+1}/{total_jobs}")

                # Restore the original callback
                self.progress_callback = original_callback

            except Exception as e:
                print(f"Error processing video job {i+1}: {e}")
                results.append((job, None))
                job["status"] = "failed"

                # Restore the original callback
                self.progress_callback = original_callback

            # Update the current job index
            self.current_job_index = i + 1

        # Final progress update
        self.update_progress(100, f"Video batch processing completed: {len([r for _, r in results if r])} of {total_jobs} successful")
        return results

    def process_video_with_prompt(self, video_file, stop_event=None):
        """
        Process a video file with a text prompt to add voice-over and subtitles
        while preserving the original video duration

        Args:
            video_file: Path to the input video file
            stop_event: Threading event to stop the process

        Returns:
            str: Path to the generated video file
        """
        try:
            # Check if we should stop
            if stop_event and stop_event.is_set():
                print("Process stopped by user.")
                self.update_progress(0, "Process stopped by user")
                return None

            # Create output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_name = os.path.splitext(os.path.basename(video_file))[0]

            # Use custom output folder if provided
            if self.output_folder and os.path.isdir(self.output_folder):
                output_dir = os.path.join(self.output_folder, f"video_{video_name}_{timestamp}")
            else:
                output_dir = os.path.join("output", f"video_{video_name}_{timestamp}")

            os.makedirs(output_dir, exist_ok=True)
            print(f"Created output directory: {output_dir}")

            # Store output_dir as instance variable for cleanup if needed
            self.current_output_dir = output_dir

            # Step 1: Generate audio from text
            print("\n--- Step 1: Generating Audio ---")
            self.update_progress(20, "Generating audio from text...")
            audio_file = os.path.join(output_dir, "voice.mp3")
            if not generate_audio(self.text_input, audio_file):
                print("ERROR: Failed to generate audio.")
                self.update_progress(0, "Failed to generate audio")
                return None

            # Check if we should stop
            if stop_event and stop_event.is_set():
                print("Process stopped by user.")
                self.update_progress(0, "Process stopped by user")
                return None

            self.update_progress(40, "Audio generated successfully")

            # Step 2: Add voice-over to original video while preserving video duration
            print("\n--- Step 2: Adding voice-over to video ---")
            self.update_progress(50, "Adding voice-over to video...")
            video_with_audio = os.path.join(output_dir, "video_with_audio.mp4")

            if not self._add_voiceover_to_video(video_file, audio_file, video_with_audio, stop_event):
                print("ERROR: Failed to add voice-over to video.")
                self.update_progress(0, "Failed to add voice-over to video")
                return None

            # Check if we should stop
            if stop_event and stop_event.is_set():
                print("Process stopped by user.")
                self.update_progress(0, "Process stopped by user")
                return None

            self.update_progress(70, "Voice-over added successfully")

            # Step 3: Generate subtitles
            print("\n--- Step 3: Generating Subtitles ---")
            self.update_progress(75, "Generating subtitles...")
            subtitle_file = os.path.join(output_dir, "subtitles.ass")
            if not generate_subtitles(self.text_input, video_with_audio, audio_file, subtitle_file):
                print("ERROR: Failed to generate subtitles.")
                self.update_progress(0, "Failed to generate subtitles")
                return None

            # Check if we should stop
            if stop_event and stop_event.is_set():
                print("Process stopped by user.")
                self.update_progress(0, "Process stopped by user")
                return None

            self.update_progress(90, "Subtitles generated successfully")

            # Step 4: Finalize video with subtitles
            final_video = self.finalize_video(subtitle_file, video_with_audio, output_dir, stop_event)

            if final_video:
                print(f"Video processing completed successfully: {final_video}")
                return final_video
            else:
                print("Failed to finalize video")
                return None

        except Exception as e:
            print(f"Error processing video with prompt: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _add_voiceover_to_video(self, video_file, audio_file, output_file, stop_event=None):
        """
        Add voice-over audio to a video while preserving the original video duration

        Args:
            video_file: Path to the input video file
            audio_file: Path to the generated audio file
            output_file: Path to the output video file
            stop_event: Threading event to stop the process

        Returns:
            bool: True if successful, False otherwise
        """
        # Check if we should stop
        if stop_event and stop_event.is_set():
            return False

        # Get audio settings from current job
        audio_settings = getattr(self, 'current_audio_settings', {"mute_original": False, "original_volume": 0.3})

        # Use the video service function with audio settings
        from services.video_service import add_voiceover_to_video
        return add_voiceover_to_video(
            video_file,
            audio_file,
            output_file,
            mix_with_original=not audio_settings["mute_original"],
            original_volume=audio_settings["original_volume"]
        )

    def _extract_video_frames(self, video_file, output_dir, stop_event=None, max_frames=20):
        """
        Extract frames from a video file

        Args:
            video_file: Path to the input video file
            output_dir: Directory to save extracted frames
            stop_event: Threading event to stop the process
            max_frames: Maximum number of frames to extract

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import cv2

            # Open the video file
            cap = cv2.VideoCapture(video_file)
            if not cap.isOpened():
                print(f"ERROR: Could not open video file: {video_file}")
                return False

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            print(f"Video has {total_frames} frames at {fps} FPS")

            # Calculate frame interval to extract evenly distributed frames
            if total_frames <= max_frames:
                frame_interval = 1
                frames_to_extract = total_frames
            else:
                frame_interval = total_frames // max_frames
                frames_to_extract = max_frames

            print(f"Extracting {frames_to_extract} frames with interval {frame_interval}")

            frame_count = 0
            extracted_count = 0

            while True:
                # Check if we should stop
                if stop_event and stop_event.is_set():
                    cap.release()
                    return False

                ret, frame = cap.read()
                if not ret:
                    break

                # Extract frame at specified intervals
                if frame_count % frame_interval == 0 and extracted_count < max_frames:
                    frame_filename = os.path.join(output_dir, f"frame_{extracted_count:04d}.jpg")
                    cv2.imwrite(frame_filename, frame)
                    extracted_count += 1

                    # Update progress
                    progress = int((extracted_count / frames_to_extract) * 20) + 10  # 10-30% range
                    self.update_progress(progress, f"Extracted {extracted_count}/{frames_to_extract} frames")

                frame_count += 1

            cap.release()

            print(f"Successfully extracted {extracted_count} frames")
            return extracted_count > 0

        except ImportError:
            print("ERROR: OpenCV (cv2) is required for video frame extraction")
            print("Please install it with: pip install opencv-python")
            return False
        except Exception as e:
            print(f"ERROR: Failed to extract frames from video: {e}")
            return False

    def _cleanup_extracted_frames(self, images_dir):
        """
        Clean up extracted frames from video processing to keep output folder clean

        Args:
            images_dir: Directory containing extracted frames
        """
        try:
            if os.path.exists(images_dir):
                import shutil
                shutil.rmtree(images_dir)
                print(f"Cleaned up extracted frames directory: {images_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up extracted frames directory: {e}")

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
