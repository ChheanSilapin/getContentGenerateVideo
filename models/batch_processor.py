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

            # Check for duplicates
            video_file = job["video_file"]
            if video_file in self.processed_files:
                print(f"Skipping duplicate video: {os.path.basename(video_file)}")
                job["status"] = "skipped"
                return None

            # Mark as being processed
            self.processed_files.add(video_file)

            # Set up video processor
            video_processor.current_audio_settings = job.get("audio_settings", {"mute_original": False, "original_volume": 0.3})

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

                # Process individual video with output folder
                processed_video = video_processor.process_video_with_prompt(
                    pair['video_file'],
                    pair['prompt'],
                    stop_event,
                    output_folder
                )
                
                if processed_video:
                    processed_videos.append(processed_video)
                else:
                    print(f"Failed to process video: {os.path.basename(pair['video_file'])}")
            
            # If we have processed videos, combine them
            if processed_videos:
                return self._combine_group_videos(processed_videos, group_data, job_index, total_jobs)
            else:
                job["status"] = "failed"
                return None
                
        except Exception as e:
            handle_operation_error(None, f"Group job {job_index+1}", e, show_dialog=False)
            job["status"] = "failed"
            return None
    
    def _combine_group_videos(self, processed_videos, group_data, job_index, total_jobs):
        """Combine processed videos into a single output"""
        try:
            from services.merge_service import VideoService
            
            # Create output path for combined video
            output_dir = os.path.dirname(processed_videos[0])
            parent_dir = os.path.dirname(output_dir)
            combined_output = os.path.join(parent_dir, group_data['output_name'])
            
            # Update progress for merging
            job_weight = 100 / total_jobs
            merge_start_progress = int((job_index / total_jobs) * 100) + int((80 / 100) * job_weight)
            merge_start_progress = min(merge_start_progress, 95)
            self.update_progress(merge_start_progress, f"Group {job_index+1}: Combining {len(processed_videos)} videos...")
            
            # Merge videos
            def merge_progress_callback(p, m):
                merge_progress_range = 15  # 95% - 80% = 15%
                scaled_merge_progress = int((p / 100) * merge_progress_range * (job_weight / 100))
                final_progress = merge_start_progress + scaled_merge_progress
                final_progress = min(final_progress, 99)
                self.update_progress(final_progress, f"Group {job_index+1}: {m}")
            
            merge_result = VideoService.merge_videos_optimized(
                processed_videos, 
                combined_output,
                progress_callback=merge_progress_callback
            )
            
            if merge_result and os.path.exists(combined_output):
                # Clean up individual video folders after successful merge using unified cleanup
                cleanup_manager = getattr(self, 'cleanup_manager', None)
                self._cleanup_individual_folders(processed_videos, cleanup_manager)
                self.update_progress(int((job_index + 1) * (100 / total_jobs)),
                                   f"✅ Completed group {job_index+1}: {group_data['output_name']}")
                return combined_output
            else:
                print(f"ERROR: Video merge failed")
                return None
                
        except Exception as e:
            print(f"ERROR: Video merge failed: {e}")
            return None
    
    def _cleanup_individual_folders(self, processed_videos, cleanup_manager=None):
        """Clean up individual video folders after successful merge using unified cleanup system"""
        cleaned_folders = 0
        for video_path in processed_videos:
            individual_folder = os.path.dirname(video_path)
            try:
                if os.path.exists(individual_folder):
                    # Use unified cleanup system if available
                    if cleanup_manager:
                        cleanup_manager.cleanup_after_video_complete(individual_folder, keep_debug_files=False)
                    else:
                        # Fallback: remove only intermediate files, keep final_output.mp4
                        import os
                        for file in os.listdir(individual_folder):
                            if file != "final_output.mp4":
                                file_path = os.path.join(individual_folder, file)
                                try:
                                    os.remove(file_path)
                                except Exception:
                                    pass
                    cleaned_folders += 1
            except Exception as e:
                print(f"Warning: Could not clean up folder {individual_folder}: {e}")
                pass  # Continue cleanup even if some folders fail
