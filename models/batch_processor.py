"""
Batch Processing Component - Handles batch video operations
Extracted from VideoGeneratorModel to reduce complexity
"""
import os
from utils.error_helpers import handle_operation_error


class BatchProcessor:
    """Handles batch processing operations"""
    
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.batch_jobs = []
        self.current_job_index = 0
        self.processed_files = set()  # Track processed files to prevent duplicates
        
    def update_progress(self, value, message=None):
        """Update progress value and message"""
        if self.progress_callback:
            self.progress_callback(value, message)
    
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
    
    def add_video_batch_job(self, text_input, video_file, audio_settings=None, custom_filename=None):
        """Add a video processing job to the batch queue"""
        job = {
            "text_input": text_input,
            "video_file": video_file,
            "job_type": "video",
            "status": "pending",
            "audio_settings": audio_settings or {"mute_original": False, "original_volume": 0.3},
            "custom_filename": custom_filename or ""
        }
        self.batch_jobs.append(job)
        return len(self.batch_jobs)  # Return job ID (1-based index)
    
    def add_group_batch_job(self, group_data, audio_settings=None):
        """Add a grouped video processing job to the batch queue"""
        job = {
            "group_data": group_data,
            "job_type": "group",
            "status": "pending",
            "audio_settings": audio_settings or {"mute_original": False, "original_volume": 0.3}
        }
        self.batch_jobs.append(job)
        return len(self.batch_jobs)  # Return job ID (1-based index)
    
    def process_batch(self, video_generator, stop_event=None):
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
            video_generator.text_input = job["text_input"]
            video_generator.image_source = job["image_source"]
            video_generator.selected_images = job["selected_images"].copy() if job["selected_images"] else []
            video_generator.website_url = job["website_url"]
            video_generator.local_folder = job["local_folder"]
            video_generator.processing_option = "cpu"  # Default to CPU for batch processing

            # Process the job
            try:
                job["status"] = "processing"

                # Create a wrapper for the progress callback
                original_callback = self.progress_callback
                job_progress_callback = self._create_job_progress_callback(i, total_jobs, original_callback)

                # Temporarily replace the callback
                self.progress_callback = job_progress_callback

                # Generate the video
                subtitle_path, video_path, output_dir = video_generator.generate_video(stop_event)

                if subtitle_path and video_path and output_dir:
                    final_video = video_generator.finalize_video(subtitle_path, video_path, output_dir, stop_event)
                    results.append((job, final_video))
                    job["status"] = "completed"
                    # Update progress to show this job is complete
                    if original_callback:
                        job_complete_progress = int((i + 1) * (100 / total_jobs))
                        original_callback(job_complete_progress, f"✅ Completed video {i+1} of {total_jobs}")
                else:
                    results.append((job, None))
                    job["status"] = "failed"
                    # Update progress to show this job is complete but failed
                    if original_callback:
                        job_complete_progress = int((i + 1) * (100 / total_jobs))
                        original_callback(job_complete_progress, f"❌ Failed video {i+1} of {total_jobs}")

                # Restore the original callback
                self.progress_callback = original_callback

            except Exception as e:
                handle_operation_error(None, f"Batch job {i+1}", e, show_dialog=False)
                results.append((job, None))
                job["status"] = "failed"
                # Restore the original callback
                self.progress_callback = original_callback

            # Update the current job index
            self.current_job_index = i + 1

        # Final progress update
        successful_count = len([r for _, r in results if r])
        self.update_progress(100, f"Batch processing completed: {successful_count} of {total_jobs} successful")
        return results
    
    def process_video_batch(self, video_processor, stop_event=None, output_folder=None):
        """Process all video jobs in the batch queue"""
        results = []
        self.current_job_index = 0
        total_jobs = len(self.batch_jobs)

        # Clear processed files tracking for new batch
        self.processed_files.clear()

        for i, job in enumerate(self.batch_jobs):
            if stop_event and stop_event.is_set():
                break

            # Handle different job types
            job_type = job.get("job_type")
            if job_type == "video":
                result = self._process_individual_video_job(job, i, total_jobs, video_processor, stop_event, output_folder)
            elif job_type == "group":
                result = self._process_group_video_job(job, i, total_jobs, video_processor, stop_event, output_folder)
            else:
                continue  # Skip unknown job types

            results.append((job, result))

        return results
    
    def _create_job_progress_callback(self, job_index, total_jobs, original_callback):
        """Create a progress callback wrapper for batch jobs"""
        def job_progress_callback(value, message=None):
            # Calculate combined progress: base progress for completed jobs + partial progress for current job
            job_weight = 100 / total_jobs
            base_progress = int(job_index * job_weight)
            current_job_progress = int((value / 100) * job_weight)
            combined_progress = base_progress + current_job_progress
            combined_progress = min(combined_progress, 100)

            # Create cleaner progress message
            if message:
                job_message = f"Video {job_index+1}/{total_jobs}: {message}"
            else:
                job_message = f"{combined_progress}% - Processing video {job_index+1} of {total_jobs}"
            
            if original_callback:
                original_callback(combined_progress, job_message)
        
        return job_progress_callback
    
    def _process_individual_video_job(self, job, job_index, total_jobs, video_processor, stop_event, output_folder=None):
        """Process an individual video job"""
        try:
            job["status"] = "processing"

            # Handle duplicates with automatic numbering instead of skipping
            video_file = job["video_file"]
            prompt = job.get("prompt", "")
            raw_custom_filename = job.get("custom_filename", "")

            # Clean custom filename - ignore placeholder text
            custom_filename = ""
            if raw_custom_filename and raw_custom_filename.strip():
                cleaned_custom = raw_custom_filename.strip()
                # Check if it's not placeholder text
                if cleaned_custom not in ["Custom filename (optional)", "Enter custom filename (optional)"]:
                    custom_filename = cleaned_custom

            # Create a unique job identifier
            base_job_id = f"{video_file}|{prompt}|{custom_filename}"

            # If this is a duplicate, add automatic numbering to make it unique
            if base_job_id in self.processed_files:
                counter = 2  # Start with 2 since the first one doesn't have a number
                while True:
                    # Create numbered filename based on whether custom filename exists
                    if custom_filename:
                        # User provided custom filename - add number to it
                        numbered_custom_filename = f"{custom_filename}_{counter}"
                    else:
                        # No custom filename - use video file name as base
                        video_base_name = os.path.splitext(os.path.basename(video_file))[0]
                        numbered_custom_filename = f"{video_base_name}_{counter}"

                    numbered_job_id = f"{video_file}|{prompt}|{numbered_custom_filename}"

                    if numbered_job_id not in self.processed_files:
                        # Update the job with the numbered filename
                        job["custom_filename"] = numbered_custom_filename
                        job_id = numbered_job_id
                        print(f"Auto-numbered duplicate: {os.path.basename(video_file)} → {numbered_custom_filename}")
                        break

                    counter += 1
                    # Safety check to prevent infinite loop
                    if counter > 999:
                        import time
                        timestamp = int(time.time())
                        if custom_filename:
                            numbered_custom_filename = f"{custom_filename}_{timestamp}"
                        else:
                            video_base_name = os.path.splitext(os.path.basename(video_file))[0]
                            numbered_custom_filename = f"{video_base_name}_{timestamp}"
                        job["custom_filename"] = numbered_custom_filename
                        job_id = f"{video_file}|{prompt}|{numbered_custom_filename}"
                        break
            else:
                job_id = base_job_id
                # Update the job to remove placeholder text even if not a duplicate
                job["custom_filename"] = custom_filename

            # Mark as being processed
            self.processed_files.add(job_id)

            # Set up video processor
            video_processor.current_audio_settings = job.get("audio_settings", {"mute_original": False, "original_volume": 0.3})
            video_processor.custom_filename = job.get("custom_filename", "")
            # Set source files for intelligent default naming
            video_processor.source_files = [job["video_file"]]

            # Create progress callback wrapper
            original_callback = self.progress_callback
            job_progress_callback = self._create_job_progress_callback(job_index, total_jobs, original_callback)
            video_processor.progress_callback = job_progress_callback

            # Process the video with output folder
            final_video = video_processor.process_video_with_prompt(
                job["video_file"],
                job["text_input"],
                stop_event,
                output_folder
            )
            
            # Restore original callback
            video_processor.progress_callback = original_callback
            
            if final_video:
                job["status"] = "completed"
                if original_callback:
                    job_complete_progress = int((job_index + 1) * (100 / total_jobs))
                    original_callback(job_complete_progress, f"✅ Completed video {job_index+1} of {total_jobs}")
                return final_video
            else:
                job["status"] = "failed"
                if original_callback:
                    job_complete_progress = int((job_index + 1) * (100 / total_jobs))
                    original_callback(job_complete_progress, f"❌ Failed video {job_index+1} of {total_jobs}")
                return None
                
        except Exception as e:
            handle_operation_error(None, f"Video job {job_index+1}", e, show_dialog=False)
            job["status"] = "failed"
            return None
    
    def _process_group_video_job(self, job, job_index, total_jobs, video_processor, stop_event, output_folder=None):
        """Process a grouped video job (multiple videos combined into one)"""
        try:
            job["status"] = "processing"
            group_data = job["group_data"]

            # Process each video in the group
            processed_videos = []
            pairs = group_data['pairs']

            for i, pair in enumerate(pairs):
                if stop_event and stop_event.is_set():
                    break

                # Update progress for this video in the group
                job_weight = 100 / total_jobs
                video_progress_within_job = (i / len(pairs)) * 80  # 0-80% of this job for individual videos
                current_progress = int((job_index / total_jobs) * 100) + int((video_progress_within_job / 100) * job_weight)
                current_progress = min(current_progress, 100)
                self.update_progress(current_progress,
                                   f"Group {job_index+1}: Processing video {i+1}/{len(pairs)} - {os.path.basename(pair['video_file'])}")

                # Process individual video with output folder (skip auto-cleanup for group processing)
                # Individual videos use default naming since only final group output uses custom filename
                video_processor.custom_filename = ""
                # Set source files for intelligent default naming
                video_processor.source_files = [pair['video_file']]

                # Ensure prompt is properly handled (convert None to empty string)
                prompt = pair.get('prompt', '') or ''

                # Log what we're processing
                has_prompt = bool(prompt.strip())
                print(f"Processing video {i+1}/{len(pairs)}: {os.path.basename(pair['video_file'])}")
                print(f"  - Has text prompt: {has_prompt}")
                if not has_prompt:
                    print(f"  - Processing without voice-over (video-only)")

                processed_video = video_processor.process_video_with_prompt(
                    pair['video_file'],
                    prompt,
                    stop_event,
                    output_folder,
                    skip_auto_cleanup=True  # Skip cleanup for group processing - we'll clean up after merge
                )
                
                if processed_video:
                    processed_videos.append(processed_video)
                    print(f"✅ Successfully processed: {os.path.basename(pair['video_file'])}")
                else:
                    print(f"❌ Failed to process video: {os.path.basename(pair['video_file'])}")
                    # Continue processing other videos instead of failing the entire group

            # If we have processed videos, combine them
            if processed_videos:
                print(f"📊 Group processing summary: {len(processed_videos)}/{len(pairs)} videos processed successfully")
                return self._combine_group_videos(processed_videos, group_data, job_index, total_jobs)
            else:
                print(f"❌ Group processing failed: No videos were processed successfully")
                job["status"] = "failed"
                return None
                
        except Exception as e:
            handle_operation_error(None, f"Group job {job_index+1}", e, show_dialog=False)
            job["status"] = "failed"
            return None
    
    def _combine_group_videos(self, processed_videos, group_data, job_index, total_jobs):
        """Combine processed videos into a single output with proper filename handling"""
        try:
            from services.merge_service import VideoService
            from utils.output_manager import get_output_manager
            from utils.error_helpers import handle_operation_error

            print(f"🔗 Starting merge process for group {job_index+1} with {len(processed_videos)} videos...")

            # Validate processed videos exist
            valid_videos = []
            for video_path in processed_videos:
                if video_path and os.path.exists(video_path):
                    valid_videos.append(video_path)
                    print(f"   ✅ Valid video: {os.path.basename(video_path)}")
                else:
                    print(f"   ❌ Missing video: {video_path}")

            if len(valid_videos) < len(processed_videos):
                print(f"⚠️ Warning: Only {len(valid_videos)}/{len(processed_videos)} videos are valid for merging")

            if not valid_videos:
                print("❌ No valid videos to merge")
                return None

            # Get output manager for user's directory
            try:
                from utils.settings_manager import SettingsManager
                settings_manager = SettingsManager()
                user_settings = settings_manager.load_settings()
            except Exception:
                user_settings = None

            output_manager = get_output_manager(user_settings)

            # Create temporary output path for combining
            temp_dir = os.path.dirname(valid_videos[0])
            base_name = os.path.splitext(group_data['output_name'])[0]
            temp_combined_output = os.path.join(temp_dir, f"temp_combined_{base_name}.mp4")

            print(f"🎯 Merging to temporary file: {temp_combined_output}")

            # Update progress for merging
            job_weight = 100 / total_jobs
            merge_start_progress = int((job_index / total_jobs) * 100) + int((80 / 100) * job_weight)
            merge_start_progress = min(merge_start_progress, 95)
            self.update_progress(merge_start_progress, f"Group {job_index+1}: Combining {len(valid_videos)} videos...")

            # Merge videos
            def merge_progress_callback(p, m):
                merge_progress_range = 15  # 95% - 80% = 15%
                scaled_merge_progress = int((p / 100) * merge_progress_range * (job_weight / 100))
                final_progress = merge_start_progress + scaled_merge_progress
                final_progress = min(final_progress, 99)
                self.update_progress(final_progress, f"Group {job_index+1}: {m}")

            print(f"🚀 Starting video merge with VideoService.merge_videos_optimized...")
            merge_result = VideoService.merge_videos_optimized(
                valid_videos,
                temp_combined_output,
                progress_callback=merge_progress_callback
            )

            print(f"📊 Merge result: {merge_result}, File exists: {os.path.exists(temp_combined_output) if temp_combined_output else False}")

            if merge_result and os.path.exists(temp_combined_output):
                print(f"✅ Merge successful! Moving to final location...")

                # Get source files for intelligent default naming (first file from group)
                source_files = []
                if group_data.get('pairs') and len(group_data['pairs']) > 0:
                    first_pair = group_data['pairs'][0]
                    if 'video_file' in first_pair:
                        source_files = [first_pair['video_file']]
                    elif 'images' in first_pair and first_pair['images']:
                        source_files = [first_pair['images'][0]]

                # Move final combined video to user's output directory with conflict resolution
                custom_filename = group_data.get('custom_filename', '')
                print(f"📁 Moving to output directory with custom_filename: '{custom_filename}', base_name: '{base_name}'")

                final_video_path = output_manager.move_final_video(
                    temp_video_path=temp_combined_output,
                    custom_filename=custom_filename,
                    source_files=source_files,
                    default_name=base_name
                )

                if final_video_path:
                    print(f"🎉 Final merged video saved: {final_video_path}")

                    # Check if auto-cleanup is enabled before removing individual folders
                    import config
                    cleanup_enabled = getattr(config, 'AUTO_CLEANUP_AFTER_COMPLETION', True)

                    print(f"🧹 Cleanup enabled: {cleanup_enabled}")
                    if cleanup_enabled:
                        print(f"🗑️ Cleaning up {len(valid_videos)} individual video files...")
                        # Use centralized OutputManager cleanup system
                        output_manager.cleanup_after_video_complete(temp_dir, keep_debug_files=False)
                        # Clean up individual video temporary directories
                        output_manager.cleanup_individual_temp_directories(valid_videos)
                        # Also clean up the temporary directory
                        output_manager.cleanup_temp_directory(temp_dir)
                        print(f"✅ Cleanup completed successfully")
                    else:
                        print(f"🔧 Keeping individual video folders for debugging (AUTO_CLEANUP_AFTER_COMPLETION = False)")
                        print(f"📁 Individual folders preserved: {len(valid_videos)} folders with debug files")

                        # Log the specific folders being preserved for debugging
                        for video_path in valid_videos:
                            individual_folder = os.path.dirname(video_path)
                            folder_name = os.path.basename(individual_folder)
                            print(f"   📂 Debug folder: {folder_name} (contains subtitles.ass, voice.mp3, etc.)")

                    self.update_progress(int((job_index + 1) * (100 / total_jobs)),
                                       f"✅ Completed group {job_index+1}: {os.path.basename(final_video_path)}")
                    return final_video_path
                else:
                    print(f"❌ ERROR: Failed to move combined video to output directory")
                    return temp_combined_output  # Return temp path as fallback
            else:
                print(f"❌ ERROR: Video merge failed - merge_result: {merge_result}, file_exists: {os.path.exists(temp_combined_output) if temp_combined_output else False}")
                return None
                
        except Exception as e:
            print(f"ERROR: Video merge failed: {e}")
            return None
    
    # Cleanup methods removed - now handled by centralized OutputManager
