import os
import sys
import gc  # For garbage collection
from moviepy.editor import VideoFileClip, concatenate_videoclips

# Import centralized utility functions
from utils.helpers import create_temp_file_with_cleanup, cleanup_temp_files, get_media_duration_safe
from services.video_utils import get_media_duration

class VideoService:
    @staticmethod
    def get_video_info(video_path):
        """Get video metadata with enhanced error handling using centralized duration function"""
        try:
            # Use centralized duration function for better reliability
            duration = get_media_duration_safe(video_path)

            # Get other metadata with MoviePy
            with VideoFileClip(video_path) as clip:
                return {
                    'duration': duration,  # Use centralized duration
                    'size': clip.size,
                    'fps': clip.fps,
                    'audio': clip.audio is not None,
                    'filename': os.path.basename(video_path)
                }
        except Exception as e:
            raise Exception(f"Could not read video info from {os.path.basename(video_path)}: {str(e)}")

    @staticmethod
    def merge_videos_optimized(video_paths, output_path, progress_callback=None):
        """
        OPTIMIZED MERGE: Handles large video sets to prevent memory crashes
        
        Features:
        - Batch processing (10 videos per batch) to reduce memory usage
        - Memory usage: ~800MB instead of ~6GB for large merges
        - Automatic garbage collection between batches
        - Two-tier approach: small merges use existing method, large merges use batching
        """
        total_videos = len(video_paths)
        
        # For small merges (≤20 videos), use the existing fast method
        if total_videos <= 20:
            if progress_callback:
                progress_callback(0, f"🚀 Using fast merge for {total_videos} videos...")
            return VideoService.merge_videos(video_paths, output_path, progress_callback)
        
        # For large merges (>20 videos), use optimized batch processing
        if progress_callback:
            progress_callback(0, f"🔧 Using optimized merge for {total_videos} videos (batch processing)...")
        
        batch_files = []
        try:
            # Validate all videos first (5% progress)
            if progress_callback:
                progress_callback(5, "✅ Validating all videos...")
            
            for i, path in enumerate(video_paths):
                if not os.path.exists(path):
                    raise Exception(f"Video file not found: {os.path.basename(path)}")
            
            # Calculate batches
            batch_size = 10
            batches = [video_paths[i:i + batch_size] for i in range(0, len(video_paths), batch_size)]
            batch_count = len(batches)
            
            if progress_callback:
                progress_callback(10, f"📦 Processing {batch_count} batches of up to {batch_size} videos each...")
            
            # Create temp directory for intermediate files
            temp_dir = os.path.dirname(output_path)
            
            # Process each batch (10% - 80% progress)
            for batch_idx, batch_paths in enumerate(batches):
                batch_start_progress = 10 + (batch_idx / batch_count) * 70
                batch_end_progress = 10 + ((batch_idx + 1) / batch_count) * 70
                
                if progress_callback:
                    progress_callback(batch_start_progress, f"🔄 Processing batch {batch_idx + 1}/{batch_count} ({len(batch_paths)} videos)...")
                
                # Create temporary output file for this batch
                batch_output = os.path.join(temp_dir, f"temp_batch_{batch_idx + 1}.mp4")
                
                # Merge this batch using the single batch method
                VideoService._merge_single_batch(
                    batch_paths, 
                    batch_output, 
                    lambda progress, msg: progress_callback(
                        batch_start_progress + (progress / 100) * (batch_end_progress - batch_start_progress),
                        f"  Batch {batch_idx + 1}: {msg}"
                    ) if progress_callback else None
                )
                
                batch_files.append(batch_output)
                
                # Force garbage collection to free memory between batches
                gc.collect()
                
                if progress_callback:
                    progress_callback(batch_end_progress, f"✅ Batch {batch_idx + 1}/{batch_count} completed")
            
            # Final merge of all batch files (80% - 95% progress)
            if progress_callback:
                progress_callback(85, f"🔗 Final merge: combining {len(batch_files)} batch files...")
            
            VideoService._merge_single_batch(
                batch_files, 
                output_path,
                lambda progress, msg: progress_callback(
                    85 + (progress / 100) * 10,
                    f"  Final merge: {msg}"
                ) if progress_callback else None
            )
            
            # Cleanup temporary batch files (95% - 100% progress)
            if progress_callback:
                progress_callback(95, "🧹 Cleaning up temporary files...")

            # Use centralized cleanup function
            cleanup_temp_files(*batch_files)
            
            if progress_callback:
                progress_callback(100, f"🎉 Successfully merged {total_videos} videos with optimized processing!")
            
            return True
            
        except Exception as e:
            # Cleanup any temporary files in case of error using centralized function
            cleanup_temp_files(*batch_files)
            
            if progress_callback:
                progress_callback(0, f"❌ Error in optimized merge: {str(e)}")
            raise e

    @staticmethod
    def _merge_single_batch(video_paths, output_path, progress_callback=None):
        """
        Internal method to merge a single batch of videos
        Optimized for memory efficiency with proper cleanup
        """
        clips = []
        temp_audio_path = None
        
        try:
            total_videos = len(video_paths)
            
            # Load clips with progress updates
            for i, path in enumerate(video_paths):
                if progress_callback:
                    progress = (i / total_videos) * 40  # 0-40% for loading
                    progress_callback(progress, f"Loading {os.path.basename(path)}")
                
                try:
                    clip = VideoFileClip(path)
                    clips.append(clip)
                except Exception as e:
                    raise Exception(f"Could not load video {os.path.basename(path)}: {str(e)}")
            
            if progress_callback:
                progress_callback(45, "Concatenating videos...")
            
            # Merge videos WITHOUT transitions/fades
            final_clip = concatenate_videoclips(clips, method="compose")
            
            if progress_callback:
                progress_callback(50, "Exporting video...")
            
            # Handle temp file path for bundled executables using centralized function
            if getattr(sys, 'frozen', False):
                temp_dir = os.path.dirname(output_path)
                temp_audio_path = create_temp_file_with_cleanup(suffix='.m4a', prefix='temp_batch_audio_', directory=temp_dir)
            else:
                temp_audio_path = create_temp_file_with_cleanup(suffix='.m4a', prefix='temp_batch_audio_')
            
            # Write with enhanced settings
            final_clip.write_videofile(
                output_path,
                temp_audiofile=temp_audio_path,
                verbose=False,
                logger=None,
                codec='libx264',
                audio_codec='aac'
            )
            
            if progress_callback:
                progress_callback(100, "Batch completed!")
            
        finally:
            # Critical: Clean up all clips to free memory immediately
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            
            # Clean up final clip
            try:
                if 'final_clip' in locals():
                    final_clip.close()
            except:
                pass
            
            # Clean up temp audio file using centralized function
            cleanup_temp_files(temp_audio_path)
            
            # Force garbage collection
            gc.collect()

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
            
            # Merge videos WITHOUT transitions/fades
            final_clip = concatenate_videoclips(clips, method="compose")
            
            if progress_callback:
                progress_callback(60, " Exporting merged video...")
            
            # Enhanced output with proper temp file handling for bundled executables using centralized function
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller executable - use output directory for temp files
                temp_dir = os.path.dirname(output_path)
                temp_audio_path = create_temp_file_with_cleanup(suffix='.m4a', prefix='temp_merge_audio_', directory=temp_dir)
            else:
                # Running as script - use relative path
                temp_audio_path = create_temp_file_with_cleanup(suffix='.m4a', prefix='temp_merge_audio_')
            
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
                progress_callback(100, "🎉 Merge completed successfully!")
            
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
            
            # Clean up temp audio file using centralized function
            cleanup_temp_files(temp_audio_path)

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
            
            for path in video_paths[1:]:
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
        """Calculate total duration of all videos using centralized duration function"""
        try:
            total_duration = 0
            for path in video_paths:
                # Use centralized duration function directly for better performance
                duration = get_media_duration_safe(path)
                total_duration += duration
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