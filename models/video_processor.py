"""
Video Processing Component - Handles individual video operations
Extracted from VideoGeneratorModel to reduce complexity
"""
import os
from datetime import datetime
from utils.error_helpers import handle_operation_error


class VideoProcessor:
    """Handles individual video processing operations"""
    
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.current_output_dir = None
        self.enhancement_options = {}
        
    def update_progress(self, value, message=None):
        """Update progress value and message"""
        if self.progress_callback:
            self.progress_callback(value, message)
    
    def process_video_with_prompt(self, video_file, text_input, stop_event=None, output_folder=None):
        """
        Process a video file with a text prompt to add voice-over and subtitles
        
        Args:
            video_file: Path to the input video file
            text_input: Text prompt for voice-over
            stop_event: Threading event to stop the process
            output_folder: Custom output folder
            
        Returns:
            str: Path to the generated video file
        """
        try:
            # Check if we should stop
            if stop_event and stop_event.is_set():
                self.update_progress(0, "Process stopped by user")
                return None

            # Create output directory
            output_dir = self._create_output_directory(video_file, output_folder)
            self.current_output_dir = output_dir

            # Step 1: Generate audio from text
            audio_file = self._generate_audio(text_input, output_dir, stop_event)
            if not audio_file:
                return None

            # Step 2: Add voice-over to original video
            video_with_audio = self._add_voiceover(video_file, audio_file, output_dir, stop_event)
            if not video_with_audio:
                return None

            # Step 3: Generate subtitles
            subtitle_file = self._generate_subtitles(text_input, video_with_audio, audio_file, output_dir, stop_event)
            if not subtitle_file:
                return None

            # Step 4: Finalize video with subtitles
            final_video = self._finalize_video(subtitle_file, video_with_audio, output_dir, stop_event)
            
            return final_video

        except Exception as e:
            handle_operation_error(None, "Video processing", e, show_dialog=False)
            return None
    
    def _create_output_directory(self, video_file, output_folder=None):
        """Create output directory for video processing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = os.path.splitext(os.path.basename(video_file))[0]

        if output_folder and os.path.isdir(output_folder):
            output_dir = os.path.join(output_folder, f"video_{video_name}_{timestamp}")
        else:
            base_output_dir = os.environ.get('VIDEO_GENERATOR_OUTPUT_DIR', 'output')
            output_dir = os.path.join(base_output_dir, f"video_{video_name}_{timestamp}")

        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
        return output_dir
    
    def _generate_audio(self, text_input, output_dir, stop_event):
        """Generate audio from text input"""
        if stop_event and stop_event.is_set():
            return None
            
        print("\n--- Step 1: Generating Audio ---")
        self.update_progress(20, "Generating audio from text...")
        
        from services.audio_service import generate_audio
        audio_file = os.path.join(output_dir, "voice.mp3")
        
        if not generate_audio(text_input, audio_file):
            print("ERROR: Failed to generate audio.")
            self.update_progress(0, "Failed to generate audio")
            return None

        self.update_progress(40, "Audio generated successfully")
        return audio_file
    
    def _add_voiceover(self, video_file, audio_file, output_dir, stop_event):
        """Add voice-over to video"""
        if stop_event and stop_event.is_set():
            return None
            
        print("\n--- Step 2: Adding voice-over to video ---")
        self.update_progress(50, "Adding voice-over to video...")
        
        video_with_audio = os.path.join(output_dir, "video_with_audio.mp4")
        
        # Get audio settings
        audio_settings = getattr(self, 'current_audio_settings', {"mute_original": False, "original_volume": 0.3})
        
        from services.video_service import add_voiceover_to_video
        success = add_voiceover_to_video(
            video_file,
            audio_file,
            video_with_audio,
            mix_with_original=not audio_settings["mute_original"],
            original_volume=audio_settings["original_volume"]
        )
        
        if not success:
            print("ERROR: Failed to add voice-over to video.")
            self.update_progress(0, "Failed to add voice-over to video")
            return None

        self.update_progress(70, "Voice-over added successfully")
        return video_with_audio
    
    def _generate_subtitles(self, text_input, video_file, audio_file, output_dir, stop_event):
        """Generate subtitles for video"""
        if stop_event and stop_event.is_set():
            return None
            
        print("\n--- Step 3: Generating Subtitles ---")
        self.update_progress(75, "Generating subtitles...")
        
        from services.subtitle_service import generate_subtitles
        subtitle_file = os.path.join(output_dir, "subtitles.ass")
        
        # Get subtitle style from enhancement options
        subtitle_style = self.enhancement_options.get("subtitle_style", "modern_glow")
        
        if not generate_subtitles(text_input, video_file, audio_file, subtitle_file, subtitle_style):
            print("ERROR: Failed to generate subtitles.")
            self.update_progress(0, "Failed to generate subtitles")
            return None

        self.update_progress(90, "Subtitles generated successfully")
        return subtitle_file
    
    def _finalize_video(self, subtitle_file, video_file, output_dir, stop_event):
        """Finalize video by merging with subtitles"""
        if stop_event and stop_event.is_set():
            return None
            
        print("\n--- Step 4: Finalizing Video ---")
        self.update_progress(95, "Finalizing video...")
        
        from Final_Video import merge_video_subtitle
        final_output = os.path.join(output_dir, "final_output.mp4")
        
        result = merge_video_subtitle(video_file, subtitle_file, final_output)
        
        if result:
            self.update_progress(100, f"Video generated successfully: {os.path.basename(result)}")
            return result
        else:
            print("Failed to finalize video")
            self.update_progress(0, "Failed to finalize video")
            return None
