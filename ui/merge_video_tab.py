import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

# Import service layer instead of direct MoviePy usage
from services.merge_service import VideoService

# For video thumbnails
try:
    from PIL import Image, ImageTk
    from moviepy.editor import VideoFileClip
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class MergeVideoTab:
    def __init__(self, parent_frame, main_gui):
        self.parent_frame = parent_frame
        self.main_gui = main_gui
        
        # Initialize UI components
        self.video_canvas = None
        self.video_scrollbar = None
        self.selected_videos = []
        self.progress_bar = None
        self.progress_label = None
        self.stop_button = None
        self.merge_button = None
        self.duration_label = None
        
        # Video thumbnail management (same as image tab)
        self.photo_references = []
        self.video_vars = []
        
        # Threading components
        self.merge_thread = None
        self.stop_event = None
        
        self.setup_merge_tab()

    def setup_merge_tab(self):
        """Set up the merge video tab with grid layout exactly like image selection"""
        main_frame = ttk.Frame(self.parent_frame, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Header with consistent styling (same as image tab)
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        label = ttk.Label(header_frame, text="Video Merger", font=("Cascadia Code", 14, "bold"))
        label.pack(side="left")

        # Button frame exactly like image tab
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        # Create buttons with exact same style as image tab
        add_button = ttk.Button(button_frame, text="📁 Add Videos", command=self.add_videos)
        add_button.pack(side="left", padx=5)
        
        # Validation checkbox - Simplified styling to match button appearance
        self.validate_var = tk.BooleanVar(value=True)
        validate_cb = tk.Checkbutton(
            button_frame, 
            text="Validate Compatibility",  
            variable=self.validate_var,
            bg="#ffffff",  # Clean white background
            fg="#333333",  # Dark text matching buttons
            font=("Cascadia Code", 9),  # Match button font
            relief="flat",  # Flat appearance like buttons
            borderwidth=0,  # No border for cleaner look
            highlightthickness=0,  # No highlight border
            activebackground="#f5f5f5",  # Subtle hover effect
            selectcolor="#ffffff"  # White checkbox background
        )
        validate_cb.pack(side="left", padx=15)  # Consistent spacing with buttons
        
        # Clear button and Stop button on the right side
        clear_button = ttk.Button(button_frame, text="🧹 Clear All", command=self.clear_all_videos)
        clear_button.pack(side="right", padx=5)
        
        # Stop button positioned near clear all button
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop", command=self.stop_merge, state="disabled")
        self.stop_button.pack(side="right", padx=5)

        # Progress section using UI factory
        progress_frame, self.progress_bar, self.progress_label = self.main_gui.ui_factory.create_progress_section(
            main_frame, "Video Processing Progress"
        )
        progress_frame.pack(fill="x", padx=5, pady=5)
        
        # Video display area with scrollbar (exactly like image tab)
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.video_canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        self.video_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.video_canvas.yview)
        self.video_canvas.configure(yscrollcommand=self.video_scrollbar.set)

        self.video_canvas.pack(side="left", fill="both", expand=True)
        self.video_scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel to canvas
        self.video_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Control buttons frame - main action buttons (same as image tab)
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=10)

        # Left side - selection controls (same as image tab)
        select_all_button = ttk.Button(control_frame, text="Select All", command=lambda: self.select_all_videos(True))
        select_all_button.pack(side="left", padx=5)

        deselect_all_button = ttk.Button(control_frame, text="Deselect All", command=lambda: self.select_all_videos(False))
        deselect_all_button.pack(side="left", padx=5)

        remove_button = ttk.Button(control_frame, text="🗑️Remove Selected", command=self.remove_selected_videos)
        remove_button.pack(side="left", padx=5)

        # Duration display
        self.duration_label = ttk.Label(control_frame, text="Total Duration: --", font=("Cascadia Code", 9))
        self.duration_label.pack(side="left", padx=10)

        # Right side - primary action (same as image tab)
        self.merge_button = ttk.Button(control_frame, text="🎬 Merge Selected Videos", command=self.merge_videos)
        self.merge_button.pack(side="right", padx=5)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling in the video canvas"""
        self.video_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_videos(self):
        """Add videos to the merge list with enhanced file filtering"""
        files = filedialog.askopenfilenames(
            title="Select Videos to Merge",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("MOV files", "*.mov"),
                ("All files", "*.*")
            ]
        )
        
        if not files:
            return
        
        added_count = 0
        for file in files:
            if file not in self.selected_videos:
                self.selected_videos.append(file)
                added_count += 1
        
        if added_count > 0:
            self.main_gui.log(f"Added {added_count} video(s) to merge list")
            self.display_video_grid()
            self.update_duration_display()
        else:
            self.main_gui.log("No new videos added (duplicates ignored)")

    def display_video_grid(self):
        """Display videos in a grid layout exactly like image selection"""
        if not self.selected_videos:
            return

        title_text = f"{len(self.selected_videos)} Videos Selected"
        self._create_video_display(self.selected_videos, title_text)

    def _create_video_display(self, video_paths, title_text):
        """Create video display layout exactly like image selection with checkboxes"""
        self.video_canvas.delete("all")
        self.photo_references = []
        self.video_vars = []  # Clear previous video variables

        video_frame = tk.Frame(self.video_canvas, bg="white")
        self.video_canvas.create_window(0, 0, window=video_frame, anchor="nw")

        # Title exactly like image selection
        title_label = tk.Label(
            video_frame,
            text=title_text,
            font=("Cascadia Code", 14, "bold"),
            bg="white",
            fg="#333333"
        )
        title_label.grid(row=0, column=0, columnspan=5, pady=15)

        # Display videos with checkboxes in a grid (exactly like image selection - 5 per row)
        for i, video_path in enumerate(video_paths):
            try:
                row = (i // 5) + 1  # 5 videos per row
                col = i % 5

                # Create a container for each video (exactly like image selection)
                video_container = tk.Frame(
                    video_frame,
                    bg="white",
                    relief="solid",
                    borderwidth=1,
                    width=150,
                    height=180
                )
                video_container.grid(row=row, column=col, padx=5, pady=5)
                video_container.grid_propagate(False)  # Force the frame to keep its size

                # Create IntVar and store it with the path (exactly like image selection)
                var = tk.IntVar(value=1)  # Default selected

                # Create checkbox with the variable (exactly like image selection)
                checkbox = tk.Checkbutton(
                    video_container,
                    variable=var,
                    bg="white",
                    command=lambda v=var, p=video_path: self.update_video_selection(v, p)
                )
                checkbox.grid(row=0, column=0, sticky="nw", padx=2, pady=2)

                # Store the variable and path
                self.video_vars.append((var, video_path))

                # Create video thumbnail
                thumbnail = self._create_video_thumbnail(video_path)
                if thumbnail:
                    self.photo_references.append(thumbnail)

                    # Create a frame to center the thumbnail (exactly like image selection)
                    thumb_frame = tk.Frame(video_container, bg="white")
                    thumb_frame.grid(row=1, column=0, sticky="nsew")
                    video_container.grid_rowconfigure(1, weight=1)
                    video_container.grid_columnconfigure(0, weight=1)

                    thumb_label = tk.Label(thumb_frame, image=thumbnail, bg="white")
                    thumb_label.pack(expand=True, fill="both", padx=5, pady=2)
                else:
                    # Fallback for videos without thumbnails (similar to image selection placeholder)
                    placeholder_frame = tk.Frame(video_container, bg="#f0f0f0")
                    placeholder_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=2)
                    video_container.grid_rowconfigure(1, weight=1)
                    video_container.grid_columnconfigure(0, weight=1)
                    
                    placeholder_label = tk.Label(
                        placeholder_frame, 
                        text="🎬\nVIDEO", 
                        bg="#f0f0f0", 
                        fg="#666666",
                        font=("Cascadia Code", 9, "bold"),
                        justify="center"
                    )
                    placeholder_label.pack(expand=True)

                # Display filename below (exactly like image selection)
                filename = os.path.basename(video_path)
                if len(filename) > 15:
                    filename = filename[:12] + "..."
                
                # Add file size info (like image selection)
                try:
                    size_mb = os.path.getsize(video_path) / (1024 * 1024)
                    info_text = f"{filename}\n({size_mb:.1f} MB)"
                except:
                    info_text = filename

                name_label = tk.Label(
                    video_container,
                    text=info_text,
                    bg="white",
                    fg="#333333",
                    font=("Cascadia Code", 8),
                    justify="center"
                )
                name_label.grid(row=2, column=0, padx=5, pady=(0, 5))

            except Exception as e:
                self.main_gui.log(f"Error displaying video {i+1}: {e}")

        video_frame.update_idletasks()
        self.video_canvas.config(scrollregion=self.video_canvas.bbox("all"))

    def _create_video_thumbnail(self, video_path):
        """Create a thumbnail for the video (same size as image thumbnails)"""
        if not PIL_AVAILABLE:
            return None
        
        try:
            # Extract frame from video for thumbnail
            with VideoFileClip(video_path) as clip:
                # Get frame at 10% duration or 1 second, whichever is smaller
                time_position = min(clip.duration * 0.1, 1.0)
                frame = clip.get_frame(time_position)
                
                # Convert to PIL Image
                img = Image.fromarray(frame)
                img.thumbnail((120, 120))  # Same size as image thumbnails
                return ImageTk.PhotoImage(img)
                
        except Exception as e:
            self.main_gui.log(f"Could not create thumbnail for {os.path.basename(video_path)}: {e}")
            return None

    def update_video_selection(self, var, path):
        """Update the selected videos list when a checkbox is clicked"""
        # Track which videos are selected via checkboxes
        pass

    def get_selected_videos(self):
        """Get list of currently selected videos from checkboxes (like image selection)"""
        selected = []
        for var, path in self.video_vars:
            if var.get() == 1:
                selected.append(path)
        return selected

    def select_all_videos(self, select=True):
        """Select or deselect all videos (exactly like image selection)"""
        if not self.video_vars:
            messagebox.showinfo("No Videos", "No videos available to select")
            return

        # Update all checkboxes using the stored variables
        for var, path in self.video_vars:
            var.set(1 if select else 0)

        action_text = "Selected" if select else "Deselected"
        self.main_gui.log(f"{action_text} all {len(self.video_vars)} videos")
        self.update_duration_display()

    def remove_selected_videos(self):
        """Remove selected videos from the list (like image selection)"""
        if not self.video_vars:
            messagebox.showinfo("No Videos", "No videos available to remove")
            return

        # Get selected videos
        selected_videos = []
        remaining_videos = []
        
        for var, path in self.video_vars:
            if var.get() == 1:
                selected_videos.append(path)
            else:
                remaining_videos.append(path)
        
        if not selected_videos:
            messagebox.showinfo("No Selection", "No videos selected for removal")
            return
        
        # Update the lists
        self.selected_videos = remaining_videos
        
        # Refresh the display
        if remaining_videos:
            self.display_video_grid()
        else:
            self.video_canvas.delete("all")
            self.photo_references.clear()
            self.video_vars.clear()
        
        self.update_duration_display()
        self.main_gui.log(f"Removed {len(selected_videos)} selected video(s)")

    def clear_all_videos(self):
        """Clear all videos from the list (exactly like image selection)"""
        if not self.selected_videos:
            messagebox.showinfo("Info", "No videos to clear")
            return
        
        count = len(self.selected_videos)
        self.video_canvas.delete("all")
        self.selected_videos.clear()
        self.video_vars.clear()
        self.photo_references.clear()
        self.duration_label.config(text="Total Duration: --")
        self.main_gui.log(f"Cleared all {count} video(s) from merge list")

    def update_duration_display(self):
        """Update the total duration display"""
        selected_videos = self.get_selected_videos()
        if not selected_videos:
            self.duration_label.config(text="Total Duration: --")
            return
        
        try:
            total_duration = VideoService.get_total_duration(selected_videos)
            formatted_duration = VideoService.format_duration(total_duration)
            self.duration_label.config(text=f"Total Duration: {formatted_duration} ({len(selected_videos)} videos)")
        except Exception as e:
            self.duration_label.config(text="Total Duration: Error")
            self.main_gui.log(f"Error calculating total duration: {str(e)}")

    def merge_videos(self):
        """Start video merge process with enhanced validation"""
        selected_videos = self.get_selected_videos()
        if len(selected_videos) < 2:
            messagebox.showwarning("Merge Error", "Please select at least 2 videos to merge")
            return

        # Validate if enabled
        if self.validate_var.get():
            try:
                is_compatible, message = VideoService.validate_video_compatibility(selected_videos)
                if not is_compatible:
                    response = messagebox.askyesno(
                        "Compatibility Warning", 
                        f"⚠️ {message}\n\nDo you want to continue anyway?"
                    )
                    if not response:
                        return
            except Exception as e:
                messagebox.showwarning("Validation Error", f"Could not validate videos: {e}")

        # Get output location
        output_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
            title="Save Merged Video As"
        )
        
        if not output_path:
            return
        
        # Confirm merge operation
        video_count = len(selected_videos)
        try:
            total_duration = VideoService.get_total_duration(selected_videos)
            duration_str = VideoService.format_duration(total_duration)
            confirm_msg = f"Merge {video_count} selected videos?\n\nTotal Duration: {duration_str}\nOutput: {os.path.basename(output_path)}"
        except:
            confirm_msg = f"Merge {video_count} selected videos?\n\nOutput: {os.path.basename(output_path)}"
        
        if not messagebox.askyesno("Confirm Merge", confirm_msg):
            return
        
        # Start merge in separate thread
        self.stop_event = threading.Event()
        self.merge_thread = threading.Thread(
            target=self.process_merge, 
            args=(selected_videos, output_path)
        )
        
        # Update UI for processing state
        self.merge_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_bar['value'] = 0
        self.progress_label.config(text="🚀 Starting video merge...")
        
        self.main_gui.log(f"Starting merge of {video_count} videos...")
        self.merge_thread.start()

    def process_merge(self, selected_videos, output_path):
        """Process video merge using the service layer with threading"""
        try:
            def progress_callback(progress, message=None):
                """Update progress in the UI thread"""
                self.parent_frame.after(0, lambda: self.update_progress(progress, message))
            
            # Check if operation was cancelled before starting
            if self.stop_event.is_set():
                self.parent_frame.after(0, lambda: self.merge_cancelled())
                return
            
            # Use the enhanced service for merging
            success = VideoService.merge_videos(
                selected_videos, 
                output_path, 
                progress_callback
            )
            
            if self.stop_event.is_set():
                self.parent_frame.after(0, lambda: self.merge_cancelled())
                return
            
            if success:
                self.parent_frame.after(0, lambda: self.merge_complete(output_path))
            else:
                self.parent_frame.after(0, lambda: self.merge_failed("Merge operation failed"))
            
        except Exception as e:
            if not self.stop_event.is_set():
                self.parent_frame.after(0, lambda: self.merge_failed(str(e)))

    def update_progress(self, progress, message=None):
        """Update progress bar and label in UI thread"""
        self.progress_bar['value'] = progress
        if message:
            self.progress_label.config(text=message)
        self.parent_frame.update_idletasks()

    def merge_complete(self, output_path):
        """Handle successful merge completion"""
        self.progress_bar['value'] = 100
        self.progress_label.config(text="✅ Merge completed successfully!")
        
        # Reset UI state
        self.merge_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        self.main_gui.log(f"Videos merged successfully: {os.path.basename(output_path)}")
        
        # Ask user if they want to open the merged video
        open_response = messagebox.askyesno(
            "Merge Complete", 
            f"Videos merged successfully!\n\nOutput: {os.path.basename(output_path)}\n\nDo you want to open the merged video now?"
        )
        if open_response:
            self.main_gui.open_file(output_path)

    def merge_failed(self, error_message):
        """Handle merge failure with enhanced error reporting"""
        self.progress_bar['value'] = 0
        self.progress_label.config(text="❌ Merge failed")
        
        # Reset UI state
        self.merge_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        self.main_gui.log(f"Video merge failed: {error_message}")
        messagebox.showerror("Merge Failed", f"Error merging videos:\n\n{error_message}")

    def merge_cancelled(self):
        """Handle merge cancellation"""
        self.progress_bar['value'] = 0
        self.progress_label.config(text="⏹️ Merge cancelled by user")
        
        # Reset UI state
        self.merge_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        self.main_gui.log("Video merge cancelled by user")

    def stop_merge(self):
        """Stop the current merge operation"""
        if self.stop_event:
            self.stop_event.set()
            self.main_gui.log("Stopping video merge...")