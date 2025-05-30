import os
import sys
from moviepy.editor import VideoFileClip, concatenate_videoclips

class VideoService:
    @staticmethod
    def get_video_info(video_path):
        """Get video metadata with enhanced error handling"""
        try:
            with VideoFileClip(video_path) as clip:
                return {
                    'duration': clip.duration,
                    'size': clip.size,
                    'fps': clip.fps,
                    'audio': clip.audio is not None,
                    'filename': os.path.basename(video_path)
                }
        except Exception as e:
            raise Exception(f"Could not read video info from {os.path.basename(video_path)}: {str(e)}")

    @staticmethod
    def merge_videos(video_paths, output_path, progress_callback=None):
        """Merge multiple videos with enhanced error handling and PyInstaller compatibility"""
        clips = []
        temp_audio_path = None
        
        try:
            total_videos = len(video_paths)
            
            # Validate all videos first
            if progress_callback:
                progress_callback(5, " Validating videos...")
            
            for i, path in enumerate(video_paths):
                if not os.path.exists(path):
                    raise Exception(f"Video file not found: {os.path.basename(path)}")
            
            # Load all clips with progress updates
            for i, path in enumerate(video_paths):
                if progress_callback:
                    progress = 10 + (i / total_videos) * 40  # 10-50% for loading
                    progress_callback(progress, f" Loading video {i+1}/{total_videos}: {os.path.basename(path)}")
                
                try:
                    clip = VideoFileClip(path)
                    clips.append(clip)
                except Exception as e:
                    raise Exception(f"Could not load video {os.path.basename(path)}: {str(e)}")
            
            if progress_callback:
                progress_callback(55, " Concatenating videos...")
            
            # Merge videos
            final_clip = concatenate_videoclips(clips)
            
            if progress_callback:
                progress_callback(60, " Exporting merged video...")
            
            # Enhanced output with proper temp file handling for bundled executables
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller executable - use output directory for temp files
                temp_dir = os.path.dirname(output_path)
                temp_audio_path = os.path.join(temp_dir, 'temp_merge_audio.m4a')
            else:
                # Running as script - use relative path
                temp_audio_path = 'temp_merge_audio.m4a'
            
            # Write with enhanced settings for better compatibility
            final_clip.write_videofile(
                output_path,
                temp_audiofile=temp_audio_path,
                verbose=False,
                logger=None,
                codec='libx264',
                audio_codec='aac'
            )
            
            if progress_callback:
                progress_callback(100, " Merge completed successfully!")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, f" Error: {str(e)}")
            raise e
        finally:
            # Clean up clips to free memory
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            
            # Clean up temp audio file
            try:
                if temp_audio_path and os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
            except:
                pass

    @staticmethod
    def validate_video_compatibility(video_paths):
        """Check if videos are compatible for merging"""
        if len(video_paths) < 2:
            return False, "Need at least 2 videos to merge"
        
        try:
            # Get info from first video as reference
            reference_info = VideoService.get_video_info(video_paths[0])
            reference_fps = reference_info['fps']
            reference_size = reference_info['size']
            
            compatibility_warnings = []
            
            for i, path in enumerate(video_paths[1:], 1):
                info = VideoService.get_video_info(path)
                
                # Check for major incompatibilities
                if abs(info['fps'] - reference_fps) > 1:  # Allow 1 FPS difference
                    return False, f"FPS mismatch: {reference_info['filename']} ({reference_fps:.1f}) vs {info['filename']} ({info['fps']:.1f})"
                
                # Collect warnings for size differences (not blocking)
                if info['size'] != reference_size:
                    compatibility_warnings.append(f"Size difference: {info['filename']} ({info['size'][0]}x{info['size'][1]})")
            
            if compatibility_warnings:
                warning_msg = "Videos are compatible but have differences:\n" + "\n".join(compatibility_warnings)
                return True, warning_msg
            else:
                return True, "All videos are fully compatible"
            
        except Exception as e:
            return False, f"Error validating videos: {str(e)}"

    @staticmethod
    def get_total_duration(video_paths):
        """Calculate total duration of all videos"""
        try:
            total_duration = 0
            for path in video_paths:
                info = VideoService.get_video_info(path)
                total_duration += info['duration']
            return total_duration
        except Exception as e:
            raise Exception(f"Error calculating total duration: {str(e)}")

    @staticmethod
    def format_duration(seconds):
        """Format duration in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"