"""
Video Entry Component - Individual video input entry
Extracted from video_tab.py for reusability and maintainability
"""
from utils.common_imports import tk, ttk

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
        self.custom_filename = tk.StringVar()

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

        # File label with icon, custom filename, and remove button
        file_label_frame = ttk.Frame(file_section)
        file_label_frame.pack(fill="x", pady=(0, 3))

        ttk.Label(
            file_label_frame,
            text="📁 Video File:",
            font=("Cascadia Code", 8, "bold")
        ).pack(side="left")

        # Custom filename section (small, inline)
        filename_section = ttk.Frame(file_label_frame)
        filename_section.pack(side="left", padx=(20, 0))

        # Small filename label
        filename_label = ttk.Label(
            filename_section,
            text="📝 Custom Filename:",
            font=("Cascadia Code", 8, "bold")
        )
        filename_label.pack(side="left")

        # Small filename entry
        self.filename_entry = ttk.Entry(
            filename_section,
            textvariable=self.custom_filename,
            font=("Cascadia Code", 9),
            width=25
        )
        self.filename_entry.pack(side="left", padx=(5, 2))

        # .mp4 label
        mp4_label = ttk.Label(
            filename_section,
            text=".mp4",
            font=("Cascadia Code", 9),
            foreground="#7f8c8d"
        )
        mp4_label.pack(side="left")

        # Placeholder text
        self.filename_entry.insert(0, "Enter custom filename (optional)")
        self.filename_entry.config(foreground="#999999")

        # Bind events for placeholder behavior
        self.filename_entry.bind('<FocusIn>', self._on_filename_focus_in)
        self.filename_entry.bind('<FocusOut>', self._on_filename_focus_out)
        self.filename_entry.bind('<KeyRelease>', self._on_filename_change)

        # Add remove icon button aligned with video file label
        from config import GUI_COLORS
        remove_button = tk.Button(
            file_label_frame,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            fg=GUI_COLORS["text"],  # Dark text color instead of red
            bg=GUI_COLORS["background"],  # Light gray background
            relief="flat",
            borderwidth=0,
            width=2,
            height=1,
            command=lambda: self.remove_callback(self.entry_id),
            cursor="hand2",
            highlightthickness=0,
            takefocus=False
        )
        remove_button.pack(side="right")

        # File input row
        file_input_frame = ttk.Frame(file_section)
        file_input_frame.pack(fill="x")

        file_entry = ttk.Entry(
            file_input_frame,
            textvariable=self.video_file_path,
            state="readonly",
            font=("Cascadia Code", 10),
            width=50
        )
        file_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        # Clean text frame like the selected style
        text_frame = ttk.LabelFrame(self.entry_frame, text="📝 Text Prompt for Video", padding=8)
        text_frame.pack(fill="x", pady=(0, 8))

        # Text input row
        prompt_input_frame = ttk.Frame(text_frame)
        prompt_input_frame.pack(fill="x")

        prompt_text = tk.Text(
            prompt_input_frame,
            height=2,
            wrap="word",
            font=("Cascadia Code", 10),
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=4
        )
        prompt_text.pack(fill="x", expand=True)

        # Bind text changes to update the StringVar
        prompt_text.bind('<KeyRelease>', lambda e: self.prompt_text.set(prompt_text.get("1.0", tk.END).strip()))

        # Store text widget reference for getting content
        self.prompt_widget = prompt_text

    def _on_filename_focus_in(self, event):
        """Handle filename entry focus in (remove placeholder)"""
        if self.filename_entry.get() == "Enter custom filename (optional)":
            self.filename_entry.delete(0, tk.END)
            self.filename_entry.config(foreground="black")

    def _on_filename_focus_out(self, event):
        """Handle filename entry focus out (add placeholder if empty)"""
        if not self.filename_entry.get().strip():
            self.filename_entry.delete(0, tk.END)
            self.filename_entry.insert(0, "Enter custom filename (optional)")
            self.filename_entry.config(foreground="#999999")
            self.custom_filename.set("")
        else:
            self.custom_filename.set(self.filename_entry.get().strip())

    def _on_filename_change(self, event):
        """Handle filename entry changes with validation"""
        current_text = self.filename_entry.get()
        if current_text != "Enter custom filename (optional)":
            # Validate filename in real-time
            from utils.filename_validator import validate_and_suggest_filename
            result = validate_and_suggest_filename(current_text)

            # Update the StringVar with the current value
            self.custom_filename.set(current_text.strip())




    def get_data(self):
        """Get the video file path and prompt text"""
        return {
            "video_file": self.video_file_path.get(),
            "prompt": self.prompt_widget.get("1.0", tk.END).strip(),
            "custom_filename": self.custom_filename.get().strip()
        }

    def is_valid(self):
        """Check if this entry has valid data"""
        data = self.get_data()
        return bool(data["video_file"] and data["prompt"])

    def set_data(self, video_file, prompt):
        """Set the video file and prompt data"""
        self.video_file_path.set(video_file)
        self.prompt_widget.delete("1.0", tk.END)
        self.prompt_widget.insert("1.0", prompt)
        self.prompt_text.set(prompt)

    def destroy(self):
        """Remove this entry from the UI"""
        if self.entry_frame:
            self.entry_frame.destroy()