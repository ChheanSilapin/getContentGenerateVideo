import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os


class VideoEntry:
    """Individual video entry with file selector and prompt input"""

    def __init__(self, parent_frame, main_gui, remove_callback, entry_id):
        self.parent_frame = parent_frame
        self.main_gui = main_gui
        self.remove_callback = remove_callback
        self.entry_id = entry_id

        # Entry data
        self.video_file_path = tk.StringVar()
        self.prompt_text = tk.StringVar()

        # UI components
        self.entry_frame = None
        self.setup_entry()

    def setup_entry(self):
        """Set up the UI for this video entry"""
        # Main entry frame with better styling
        self.entry_frame = ttk.LabelFrame(
            self.parent_frame,
            text=f"🎥 Video {self.entry_id}",
            padding=8
        )
        self.entry_frame.pack(fill="x", padx=6, pady=4)

        # Video file selection section
        file_section = ttk.Frame(self.entry_frame)
        file_section.pack(fill="x", pady=(0, 6))

        # File label with icon
        file_label_frame = ttk.Frame(file_section)
        file_label_frame.pack(fill="x", pady=(0, 3))

        ttk.Label(
            file_label_frame,
            text="📁 Video File:",
            font=("Helvetica", 10, "bold")
        ).pack(side="left")

        # File input row
        file_input_frame = ttk.Frame(file_section)
        file_input_frame.pack(fill="x")

        file_entry = ttk.Entry(
            file_input_frame,
            textvariable=self.video_file_path,
            state="readonly",
            font=("Helvetica", 10),
            width=50
        )
        file_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        browse_button = self.main_gui.ui_factory.create_styled_button(
            file_input_frame, "📂 Browse", self.browse_video_file,
            bg_color=self.main_gui.colors["secondary"], width=12
        )
        browse_button.pack(side="right")

        # Prompt input section
        prompt_section = ttk.Frame(self.entry_frame)
        prompt_section.pack(fill="x")

        # Prompt label with icon
        prompt_label_frame = ttk.Frame(prompt_section)
        prompt_label_frame.pack(fill="x", pady=(0, 3))

        ttk.Label(
            prompt_label_frame,
            text="💬 Voice-over Prompt:",
            font=("Helvetica", 10, "bold")
        ).pack(side="left")

        # Prompt input row
        prompt_input_frame = ttk.Frame(prompt_section)
        prompt_input_frame.pack(fill="x")

        prompt_text = tk.Text(
            prompt_input_frame,
            height=2,
            wrap="word",
            font=("Helvetica", 10),
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=4
        )
        prompt_text.pack(side="left", fill="x", expand=True, padx=(0, 12))

        # Bind text changes to update the StringVar
        prompt_text.bind('<KeyRelease>', lambda e: self.prompt_text.set(prompt_text.get("1.0", tk.END).strip()))

        # Remove button with better styling
        remove_button = self.main_gui.ui_factory.create_styled_button(
            prompt_input_frame, "🗑️ Remove", lambda: self.remove_callback(self.entry_id),
            bg_color=self.main_gui.colors["accent"], hover_color="#c0392b", width=12
        )
        remove_button.pack(side="right", anchor="n", pady=(0, 0))

        # Store text widget reference for getting content
        self.prompt_widget = prompt_text

    def browse_video_file(self):
        """Open file dialog to select a video file"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.video_file_path.set(file_path)
            self.main_gui.log(f"Selected video file: {os.path.basename(file_path)}")

    def get_data(self):
        """Get the video file path and prompt text"""
        return {
            "video_file": self.video_file_path.get(),
            "prompt": self.prompt_widget.get("1.0", tk.END).strip()
        }

    def is_valid(self):
        """Check if this entry has valid data"""
        data = self.get_data()
        return bool(data["video_file"] and data["prompt"])

    def destroy(self):
        """Remove this entry from the UI"""
        if self.entry_frame:
            self.entry_frame.destroy()


class VideoTab:
    """Video tab component for multi-video processing with individual prompts"""

    def __init__(self, parent_frame, main_gui):
        self.parent_frame = parent_frame
        self.main_gui = main_gui

        # Video entries management
        self.video_entries = {}  # Dictionary to store VideoEntry objects
        self.next_entry_id = 1

        # Audio settings
        self.mute_original_audio = tk.BooleanVar(value=False)  # Default: keep original audio
        self.original_audio_volume = tk.DoubleVar(value=0.3)  # Default: 30% volume

        # UI components
        self.video_progress_bar = None
        self.video_progress_label = None
        self.generate_button = None
        self.stop_button = None
        self.entries_frame = None
        self.scroll_canvas = None
        self.scrollable_frame = None

        # Set up the tab
        self.setup_video_tab()

    def setup_video_tab(self):
        """Set up the video tab UI"""
        # Main container with scrolling
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Header section
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 15))

        # Title with icon-like styling
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(fill="x")

        title_label = ttk.Label(
            title_frame,
            text="🎬 Multi-Video Generation",
            font=("Helvetica", 20, "bold")
        )
        title_label.pack(anchor="w")

        # Description with better styling
        desc_label = ttk.Label(
            header_frame,
            text="Process multiple videos with individual voice-overs and subtitles while preserving original video duration",
            font=("Helvetica", 11),
            foreground="#666666"
        )
        desc_label.pack(anchor="w", pady=(5, 0))

        # Audio settings section
        self.setup_audio_settings(main_frame)

        # Scrollable area for video entries
        self.setup_scrollable_area(main_frame)

        # Progress section with better styling
        progress_frame, self.video_progress_bar, self.video_progress_label = self.main_gui.ui_factory.create_progress_section(
            main_frame, "⚡ Processing Progress"
        )
        progress_frame.pack(fill="x", pady=(0, 10))

        # Action buttons with better layout
        self.setup_action_buttons(main_frame)

        # Add initial video entry
        self.add_video_entry()

    def setup_action_buttons(self, parent):
        """Set up action buttons with better styling"""
        # Action buttons container
        button_container = ttk.Frame(parent)
        button_container.pack(fill="x", pady=(0, 5))

        # Left side - main action
        left_buttons = ttk.Frame(button_container)
        left_buttons.pack(side="left", fill="x", expand=True)

        self.generate_button = self.main_gui.ui_factory.create_styled_button(
            left_buttons, "🚀 Generate All Videos", self.start_video_generation,
            bg_color=self.main_gui.colors["success"], hover_color="#27ae60", width=25
        )
        self.generate_button.pack(side="left")

        # Right side - control actions
        right_buttons = ttk.Frame(button_container)
        right_buttons.pack(side="right")

        self.stop_button = self.main_gui.ui_factory.create_styled_button(
            right_buttons, "⏹️ Stop", self.stop_video_generation,
            bg_color=self.main_gui.colors["accent"], hover_color="#c0392b", state="disabled", width=12
        )
        self.stop_button.pack(side="right")

    def setup_audio_settings(self, parent):
        """Set up audio settings section"""
        # Audio settings frame with better styling
        audio_frame = ttk.LabelFrame(
            parent,
            text="🔊 Audio Settings",
            padding=8
        )
        audio_frame.pack(fill="x", pady=(0, 8))

        # Settings grid container
        settings_container = ttk.Frame(audio_frame)
        settings_container.pack(fill="x")

        # Mute original audio checkbox with better styling
        mute_frame = ttk.Frame(settings_container)
        mute_frame.pack(fill="x", pady=(0, 6))

        mute_checkbox = ttk.Checkbutton(
            mute_frame,
            text="🔇 Mute original video audio (voice-over only)",
            variable=self.mute_original_audio,
            command=self.on_mute_setting_changed
        )
        mute_checkbox.pack(side="left")

        # Volume control section
        volume_section = ttk.Frame(settings_container)
        volume_section.pack(fill="x")

        # Volume label with icon
        volume_label_frame = ttk.Frame(volume_section)
        volume_label_frame.pack(fill="x", pady=(0, 4))

        ttk.Label(
            volume_label_frame,
            text="🔉 Original audio volume:",
            font=("Helvetica", 10, "bold")
        ).pack(side="left")

        # Volume control frame
        volume_control_frame = ttk.Frame(volume_section)
        volume_control_frame.pack(fill="x")

        # Volume scale with better styling
        self.volume_scale = ttk.Scale(
            volume_control_frame,
            from_=0.0,
            to=1.0,
            orient="horizontal",
            variable=self.original_audio_volume,
            length=300
        )
        self.volume_scale.pack(side="left", padx=(0, 15))

        # Volume percentage label with better styling
        self.volume_label = ttk.Label(
            volume_control_frame,
            text="30%",
            font=("Helvetica", 10, "bold"),
            foreground="#2c3e50"
        )
        self.volume_label.pack(side="left")

        # Bind scale changes to update label
        self.volume_scale.configure(command=self.on_volume_changed)

        # Initial state
        self.on_mute_setting_changed()

    def on_mute_setting_changed(self):
        """Handle mute setting change"""
        if self.mute_original_audio.get():
            # Disable volume controls when muted
            self.volume_scale.configure(state="disabled")
            self.volume_label.configure(text="Muted", foreground="gray")
        else:
            # Enable volume controls
            self.volume_scale.configure(state="normal")
            self.volume_label.configure(foreground="black")
            self.on_volume_changed(self.original_audio_volume.get())

    def on_volume_changed(self, value):
        """Handle volume scale change"""
        if not self.mute_original_audio.get():
            volume_percent = int(float(value) * 100)
            self.volume_label.configure(text=f"{volume_percent}%")

    def setup_scrollable_area(self, parent):
        """Set up scrollable area for video entries"""
        # Video entries section header
        entries_header = ttk.Frame(parent)
        entries_header.pack(fill="x", pady=(0, 10))

        entries_title = ttk.Label(
            entries_header,
            text="📹 Video Entries",
            font=("Helvetica", 14, "bold")
        )
        entries_title.pack(side="left")

        # Add video button moved to header
        add_video_button = self.main_gui.ui_factory.create_styled_button(
            entries_header, "➕ Add Video", self.add_video_entry,
            bg_color=self.main_gui.colors["primary"], width=12
        )
        add_video_button.pack(side="right")

        # Create canvas and scrollbar with better styling
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Canvas with better styling - much smaller height for compact fit
        self.scroll_canvas = tk.Canvas(
            canvas_frame,
            height=120,
            bg="#f0f0f0",
            highlightthickness=1,
            highlightbackground="#e1e8ed",
            relief="solid",
            borderwidth=1
        )

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.scroll_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.scroll_canvas, style="Card.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        )

        # Create window and configure it to fill the canvas width
        canvas_window = self.scroll_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)

        # Bind canvas resize to update the scrollable frame width
        def configure_scroll_region(event):
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
            # Make the scrollable frame fill the canvas width
            canvas_width = event.width
            self.scroll_canvas.itemconfig(canvas_window, width=canvas_width)

        self.scroll_canvas.bind('<Configure>', configure_scroll_region)

        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        self.scroll_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Store reference to entries frame
        self.entries_frame = self.scrollable_frame

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling in the canvas"""
        self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_video_entry(self):
        """Add a new video entry to the list"""
        entry_id = self.next_entry_id
        self.next_entry_id += 1

        # Create new video entry
        video_entry = VideoEntry(
            self.entries_frame,
            self.main_gui,
            self.remove_video_entry,
            entry_id
        )

        # Store the entry
        self.video_entries[entry_id] = video_entry

        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

        self.main_gui.log(f"Added video entry #{entry_id}")

    def remove_video_entry(self, entry_id):
        """Remove a video entry from the list"""
        if entry_id in self.video_entries:
            # Don't allow removing the last entry
            if len(self.video_entries) <= 1:
                messagebox.showwarning("Cannot Remove", "At least one video entry must remain.")
                return

            # Remove the entry
            self.video_entries[entry_id].destroy()
            del self.video_entries[entry_id]

            # Update scroll region
            self.scrollable_frame.update_idletasks()
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

            self.main_gui.log(f"Removed video entry #{entry_id}")

    def get_valid_entries(self):
        """Get all valid video entries"""
        valid_entries = []
        for entry_id, entry in self.video_entries.items():
            if entry.is_valid():
                valid_entries.append(entry.get_data())
        return valid_entries

    def start_video_generation(self):
        """Start the multi-video generation process"""
        # Check if generation is already running
        if self.main_gui.generation_thread and self.main_gui.generation_thread.is_alive():
            messagebox.showwarning("Process Running", "Video generation is already in progress")
            return

        # Get valid entries
        valid_entries = self.get_valid_entries()

        if not valid_entries:
            messagebox.showwarning("No Valid Entries", "Please add at least one video with a prompt.")
            return

        # Confirm with user
        response = messagebox.askyesno(
            "Confirm Generation",
            f"Generate videos for {len(valid_entries)} entries?\n\nThis may take a while."
        )

        if not response:
            return

        # Clear any existing batch jobs
        self.main_gui.model.batch_jobs.clear()

        # Add video jobs to batch processing with audio settings
        for i, entry_data in enumerate(valid_entries):
            # Add audio settings to the entry data
            entry_data["mute_original_audio"] = self.mute_original_audio.get()
            entry_data["original_audio_volume"] = self.original_audio_volume.get()

            # For video processing, we'll use the video file as the "image source"
            # and the prompt as the text input
            job_id = self.main_gui.model.add_video_batch_job(
                text_input=entry_data["prompt"],
                video_file=entry_data["video_file"],
                audio_settings={
                    "mute_original": entry_data["mute_original_audio"],
                    "original_volume": entry_data["original_audio_volume"]
                }
            )
            self.main_gui.log(f"Added video job #{job_id}: {os.path.basename(entry_data['video_file'])}")

        # Set up progress callback
        self.main_gui.model.set_progress_callback(self.update_video_progress)

        # Start processing
        self.video_progress_bar["value"] = 0
        self.video_progress_label.config(text="0%")
        self.generate_button.config(state="disabled")
        self.stop_button.config(state="normal")

        # Create stop event and start thread
        self.main_gui.stop_event = threading.Event()
        self.main_gui.generation_thread = threading.Thread(target=self.process_video_batch)
        self.main_gui.generation_thread.daemon = True
        self.main_gui.generation_thread.start()

        self.main_gui.log(f"Started processing {len(valid_entries)} video(s)")

    def process_video_batch(self):
        """Process the video batch in a separate thread"""
        try:
            results = self.main_gui.model.process_video_batch(self.main_gui.stop_event)

            if self.main_gui.stop_event.is_set():
                self.main_gui.root.after(0, lambda: self.main_gui.log("Video processing stopped by user"))
                self.main_gui.root.after(0, lambda: self.reset_video_ui())
                return

            # Process results
            successful = len([r for _, r in results if r])
            total = len(results)

            self.main_gui.root.after(0, lambda: self.video_batch_completed(successful, total, results))

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.main_gui.root.after(0, lambda: self.main_gui.log(f"Error processing videos: {e}"))
            self.main_gui.root.after(0, lambda: self.reset_video_ui())

    def video_batch_completed(self, successful, total, results):
        """Handle completion of video batch processing"""
        self.main_gui.log(f"Video processing completed: {successful}/{total} successful")
        self.update_video_progress(100, f"Completed: {successful}/{total} videos")
        self.reset_video_ui()

        # Show completion message
        if successful > 0:
            message = f"Successfully generated {successful} out of {total} videos.\n\nWould you like to open the output folder?"
            response = messagebox.askyesno("Processing Complete", message)
            if response and results:
                # Open the output folder of the first successful result
                for job, video_path in results:
                    if video_path:
                        output_dir = os.path.dirname(video_path)
                        self.main_gui.open_file(output_dir)
                        break
        else:
            messagebox.showerror("Processing Failed", "No videos were generated successfully.")

    def stop_video_generation(self):
        """Stop the video generation process"""
        if self.main_gui.stop_event:
            self.main_gui.stop_event.set()
            self.main_gui.log("Stopping video processing...")
            self.main_gui.root.after(1000, self.reset_video_ui)

    def update_video_progress(self, value, message=None):
        """Update the video processing progress"""
        self.video_progress_bar["value"] = value
        if message:
            self.video_progress_label.config(text=message)
        else:
            self.video_progress_label.config(text=f"{value}%")

    def reset_video_ui(self):
        """Reset the video tab UI to initial state"""
        self.generate_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.video_progress_bar["value"] = 0
        self.video_progress_label.config(text="0%")