#!/usr/bin/env python3
"""
Batch Tab Component for Video Generator GUI
Handles batch processing functionality
"""
import os
import tkinter as tk
from tkinter import messagebox, ttk
import threading


class BatchTab:
    """Batch tab component for the Video Generator GUI"""

    def __init__(self, parent_frame, main_gui):
        """
        Initialize the batch tab

        Args:
            parent_frame: The parent frame to contain this tab
            main_gui: Reference to the main GUI instance for callbacks and shared data
        """
        self.parent_frame = parent_frame
        self.main_gui = main_gui
        self.batch_progress_bar = None
        self.batch_progress_label = None
        self.jobs_listbox = None
        
        # ✅ ADD CLEANUP PREFERENCES FOR BATCH PROCESSING
        self.auto_cleanup_enabled = tk.BooleanVar(value=True)  # Default to cleanup for batch processing
        self.keep_debug_files = tk.BooleanVar(value=False)     # Default to clean for space saving
        
        self.setup_batch_tab()

    def setup_batch_tab(self):
        """Set up the batch processing tab"""
        # Main container
        batch_frame = ttk.Frame(self.parent_frame, padding=10)
        batch_frame.pack(fill="both", expand=True)

        # Batch jobs list
        jobs_frame = ttk.LabelFrame(batch_frame, text="Batch Jobs", padding=10)
        jobs_frame.pack(fill="both", expand=True, pady=10)

        # Jobs listbox with scrollbar
        jobs_scroll = ttk.Scrollbar(jobs_frame)
        jobs_scroll.pack(side="right", fill="y")

        self.jobs_listbox = tk.Listbox(jobs_frame, height=10,
                                       yscrollcommand=jobs_scroll.set,
                                       font=("Helvetica", 10))
        self.jobs_listbox.pack(side="left", fill="both", expand=True)
        jobs_scroll.config(command=self.jobs_listbox.yview)

        # Add a progress section
        progress_frame = ttk.LabelFrame(batch_frame, text="Batch Progress", padding=10)
        progress_frame.pack(fill="x", pady=10)

        self.batch_progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", mode='determinate')
        self.batch_progress_bar.pack(fill="x", padx=5, pady=5)

        self.batch_progress_label = ttk.Label(progress_frame, text="0%", font=("Helvetica", 10))
        self.batch_progress_label.pack(pady=5)

        # Buttons frame
        buttons_frame = ttk.Frame(batch_frame)
        buttons_frame.pack(fill="x", pady=10)

        # Add current settings as a job
        add_job_btn = ttk.Button(buttons_frame, text="Add Current Settings as Job",
                                command=self.add_current_as_job)
        add_job_btn.pack(side="left", padx=5)

        # Remove selected job
        remove_job_btn = ttk.Button(buttons_frame, text="Remove Selected Job",
                                   command=self.remove_selected_job)
        remove_job_btn.pack(side="left", padx=5)

        # Clear all jobs
        clear_jobs_btn = ttk.Button(buttons_frame, text="Clear All Jobs",
                                   command=self.clear_all_jobs)
        clear_jobs_btn.pack(side="left", padx=5)

        # Start batch processing
        start_batch_btn = ttk.Button(buttons_frame, text="Start Batch Processing",
                                    command=self.start_batch_processing,
                                    style="Accent.TButton")
        start_batch_btn.pack(side=tk.RIGHT, padx=5)
        
        # ✅ ADD CLEANUP PREFERENCES UI
        cleanup_frame = ttk.LabelFrame(batch_frame, text="File Cleanup Options", padding=5)
        cleanup_frame.pack(fill="x", pady=5)
        
        # Auto cleanup checkbox
        auto_cleanup_cb = ttk.Checkbutton(
            cleanup_frame, 
            text="🗑️ Auto-cleanup intermediate files (keep only final_output.mp4)",
            variable=self.auto_cleanup_enabled,
            command=self._on_cleanup_option_changed
        )
        auto_cleanup_cb.pack(anchor="w", pady=2)
        
        # Keep debug files checkbox (only enabled when auto-cleanup is on)
        self.keep_debug_cb = ttk.Checkbutton(
            cleanup_frame, 
            text="📁 Keep debug files (voice.mp3, subtitles.ass) for troubleshooting",
            variable=self.keep_debug_files
        )
        self.keep_debug_cb.pack(anchor="w", pady=2, padx=20)
        
        # Info label
        self.cleanup_info_label = ttk.Label(
            cleanup_frame, 
            text="💡 Recommended: Enable auto-cleanup for batch processing to save disk space",
            font=("Helvetica", 9),
            foreground="gray"
        )
        self.cleanup_info_label.pack(anchor="w", pady=2)
        
        # Update initial state
        self._on_cleanup_option_changed()

    def _on_cleanup_option_changed(self):
        """Handle cleanup option changes"""
        if self.auto_cleanup_enabled.get():
            self.keep_debug_cb.configure(state="normal")
            self.cleanup_info_label.configure(text="💡 Auto-cleanup enabled: Only final_output.mp4 will be kept per video")
        else:
            self.keep_debug_cb.configure(state="disabled")
            self.cleanup_info_label.configure(text="⚠️ Auto-cleanup disabled: All intermediate files will be kept (uses more disk space)")

    def add_current_as_job(self):
        """Add current settings as a batch job"""
        if not self.main_gui.input_tab_component:
            return

        text = self.main_gui.input_tab_component.get_text_input()
        if not text:
            messagebox.showwarning("Input Error", "Please enter text for voice generation")
            return

        # Determine image source and validate
        if self.main_gui.selected_images:
            image_source = "3"  # Selected images
            job_id = self.main_gui.model.add_batch_job(
                text_input=text,
                image_source=image_source,
                selected_images=self.main_gui.selected_images
            )
            self.jobs_listbox.insert(tk.END, f"Job #{job_id}: {text[:30]}... ({len(self.main_gui.selected_images)} images)")
            self.main_gui.log(f"Added batch job #{job_id} with {len(self.main_gui.selected_images)} images")
        elif self.main_gui.input_tab_component.get_url_input():
            image_source = "1"  # Website URL
            url = self.main_gui.input_tab_component.get_url_input()
            job_id = self.main_gui.model.add_batch_job(
                text_input=text,
                image_source=image_source,
                website_url=url
            )
            self.jobs_listbox.insert(tk.END, f"Job #{job_id}: {text[:30]}... (URL: {url[:20]}...)")
            self.main_gui.log(f"Added batch job #{job_id} with website URL")
        elif hasattr(self.main_gui, 'folder_path') and self.main_gui.folder_path:
            image_source = "2"  # Local folder
            job_id = self.main_gui.model.add_batch_job(
                text_input=text,
                image_source=image_source,
                local_folder=self.main_gui.folder_path
            )
            self.jobs_listbox.insert(tk.END, f"Job #{job_id}: {text[:30]}... (Folder: {os.path.basename(self.main_gui.folder_path)})")
            self.main_gui.log(f"Added batch job #{job_id} with local folder")
        else:
            messagebox.showwarning("Input Error", "Please provide either a website URL, select images, or choose a local folder")
            return

    def remove_selected_job(self):
        """Remove the selected job from the batch"""
        selected = self.jobs_listbox.curselection()
        if not selected:
            return

        index = selected[0]
        self.jobs_listbox.delete(index)
        self.main_gui.model.batch_jobs.pop(index)
        self.main_gui.log(f"Removed batch job #{index+1}")

    def clear_all_jobs(self):
        """Clear all batch jobs"""
        self.jobs_listbox.delete(0, tk.END)
        self.main_gui.model.batch_jobs = []
        self.main_gui.log("Cleared all batch jobs")

    def start_batch_processing(self):
        """Start processing all batch jobs"""
        if not self.main_gui.model.batch_jobs:
            messagebox.showwarning("No Jobs", "Please add at least one job to the batch")
            return

        if self.main_gui.generation_thread and self.main_gui.generation_thread.is_alive():
            messagebox.showwarning("Process Running", "Video generation is already in progress")
            return

        # ✅ RESPECT OUTPUT FOLDER FROM INPUT TAB
        # Apply the same output folder configuration that Input tab uses
        if self.main_gui.input_tab_component:
            output_folder_value = self.main_gui.input_tab_component.output_folder.get()
            if output_folder_value and output_folder_value != "Default (Auto)":
                if os.path.isdir(output_folder_value):
                    self.main_gui.model.output_folder = output_folder_value
                    self.main_gui.log(f"📦 Batch tab using custom output folder: {output_folder_value}")
                else:
                    self.main_gui.log(f"⚠️ Selected output folder doesn't exist, using default")
                    self.main_gui.model.output_folder = None
            else:
                self.main_gui.model.output_folder = None
                self.main_gui.log("📦 Batch tab using default output folder")
        else:
            self.main_gui.log("⚠️ Could not access Input tab settings, using default output folder")

        self.main_gui.log(f"Starting batch processing of {len(self.main_gui.model.batch_jobs)} jobs")

        # Reset progress bars
        if self.main_gui.input_tab_component:
            self.main_gui.input_tab_component.progress_bar["value"] = 0
            self.main_gui.input_tab_component.progress_label.config(text="0%")
        self.batch_progress_bar["value"] = 0
        self.batch_progress_label.config(text="0%")

        # Update buttons through InputTab component
        if self.main_gui.input_tab_component:
            self.main_gui.input_tab_component.generate_button.config(state=tk.DISABLED)
            self.main_gui.input_tab_component.stop_button.config(state=tk.NORMAL)
        self.main_gui.stop_event = threading.Event()
        self.main_gui.generation_thread = threading.Thread(target=self.process_batch_thread)
        self.main_gui.generation_thread.daemon = True
        self.main_gui.generation_thread.start()

    def process_batch_thread(self):
        """Process batch jobs in a separate thread"""
        try:
            # Make sure the progress callback is set
            def progress_callback(value, message=None):
                self.main_gui.root.after(0, lambda v=value, m=message: self.main_gui.update_progress_ui(v, m))

            self.main_gui.model.set_progress_callback(progress_callback)

            # Process the batch
            results = self.main_gui.model.process_batch(self.main_gui.stop_event)

            if self.main_gui.stop_event.is_set():
                self.main_gui.root.after(0, lambda: self.main_gui.log("Batch processing stopped by user"))
                self.main_gui.root.after(0, lambda: self.main_gui.reset_ui())
                return

            # Update UI with results
            self.main_gui.root.after(0, lambda: self.batch_completed(results))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.main_gui.root.after(0, lambda: self.main_gui.log(f"Error in batch processing: {e}"))
            self.main_gui.root.after(0, lambda: self.main_gui.reset_ui())

    def batch_completed(self, results):
        """Handle batch completion"""
        self.main_gui.log("Batch processing completed")
        self.main_gui.reset_ui()

        # Count successes and failures
        successes = sum(1 for _, video_path in results if video_path)
        failures = len(results) - successes

        # ✅ AUTOMATIC CLEANUP FOR BATCH PROCESSING
        if successes > 0 and self.auto_cleanup_enabled.get():
            self.main_gui.log("🧹 Starting automatic cleanup of intermediate files...")
            total_cleaned = 0
            
            for job, video_path in results:
                if video_path and os.path.exists(video_path):
                    output_dir = os.path.dirname(video_path)
                    try:
                        cleaned_count = self.main_gui.model.cleanup_after_video_complete(
                            output_dir, 
                            keep_debug_files=self.keep_debug_files.get()
                        )
                        total_cleaned += cleaned_count
                        
                        # Log cleanup for this specific video
                        video_name = os.path.basename(video_path)
                        if cleaned_count > 0:
                            self.main_gui.log(f"✅ Cleaned {cleaned_count} files for {video_name}")
                        else:
                            self.main_gui.log(f"ℹ️ No cleanup needed for {video_name}")
                            
                    except Exception as e:
                        self.main_gui.log(f"⚠️ Cleanup failed for {os.path.basename(video_path)}: {e}")
            
            # Summary of cleanup
            if total_cleaned > 0:
                self.main_gui.log(f"🎉 Cleanup completed: Removed {total_cleaned} intermediate files total")
                if self.keep_debug_files.get():
                    self.main_gui.log("📁 Debug files (voice.mp3, subtitles.ass) were kept for troubleshooting")
                else:
                    self.main_gui.log("🗑️ All intermediate files removed - only final_output.mp4 files remain")
            else:
                self.main_gui.log("ℹ️ No intermediate files needed cleanup")
        elif successes > 0:
            self.main_gui.log("📁 Keeping all intermediate files (auto-cleanup disabled)")

        # Create completion message
        message = f"Batch processing completed:\n✅ {successes} videos generated successfully\n❌ {failures} jobs failed"
        
        if successes > 0 and self.auto_cleanup_enabled.get():
            if self.keep_debug_files.get():
                message += f"\n\n🧹 Cleaned up intermediate files (kept debug files)\n📁 Removed {total_cleaned} temporary files"
            else:
                message += f"\n\n🧹 Auto-cleanup completed\n🗑️ Removed {total_cleaned} intermediate files\n💾 Only final_output.mp4 files remain"

        if successes > 0:
            # Ask if user wants to open the output folder
            response = messagebox.askyesno(
                "Batch Complete",
                f"{message}\n\nDo you want to open the output folder?"
            )
            if response:
                # Find the first successful result and open its parent directory
                for job, video_path in results:
                    if video_path and os.path.exists(video_path):
                        # Go up one level to show all video folders
                        video_dir = os.path.dirname(video_path)
                        parent_dir = os.path.dirname(video_dir)
                        if os.path.exists(parent_dir):
                            self.main_gui.open_file(parent_dir)
                        else:
                            self.main_gui.open_file(video_dir)
                        break
        else:
            messagebox.showinfo("Batch Complete", message)

    def update_batch_progress(self, value, message=None):
        """Update the batch progress bar and label"""
        if self.batch_progress_bar:
            self.batch_progress_bar["value"] = value
            self.batch_progress_label.config(text=f"{value}%")
        if message:
            self.main_gui.log(message)

    def reset_batch_ui(self):
        """Reset batch UI components to default state"""
        if self.batch_progress_bar:
            self.batch_progress_bar["value"] = 0
            self.batch_progress_label.config(text="0%")
