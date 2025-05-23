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

        # Initialize UI components
        self.jobs_listbox = None
        self.batch_progress_bar = None
        self.batch_progress_label = None

        # Set up the tab
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

        message = f"Batch processing completed:\n{successes} videos generated successfully\n{failures} jobs failed"

        if successes > 0:
            # Ask if user wants to open the output folder
            response = messagebox.askyesno(
                "Batch Complete",
                f"{message}\n\nDo you want to open the output folder?"
            )
            if response and results[0][1]:  # If there's at least one successful result
                # Open the folder containing the first successful video
                output_dir = os.path.dirname(results[0][1])
                self.main_gui.open_file(output_dir)
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
