"""
Video Entry Component - Individual video input entry
Extracted from video_tab.py for reusability and maintainability
"""
from utils.common_imports import tk, ttk, filedialog, os

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
            font=("Cascadia Code", 10, "bold")
        ).pack(side="left")

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

        browse_button = self.main_gui.ui_factory.create_icon_button(
            file_input_frame, "Browse", self.browse_video_file,
            icon="📂", width=12
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
            font=("Cascadia Code", 10, "bold")
        ).pack(side="left")

        # Prompt input row
        prompt_input_frame = ttk.Frame(prompt_section)
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
        prompt_text.pack(side="left", fill="x", expand=True, padx=(0, 12))

        # Bind text changes to update the StringVar
        prompt_text.bind('<KeyRelease>', lambda e: self.prompt_text.set(prompt_text.get("1.0", tk.END).strip()))

        # Remove button with clean styling
        remove_button = self.main_gui.ui_factory.create_icon_button(
            prompt_input_frame, "Remove", lambda: self.remove_callback(self.entry_id),
            icon="🗑️", width=12
        )
        remove_button.pack(side="right", anchor="n", pady=(0, 0))

        # Store text widget reference for getting content
        self.prompt_widget = prompt_text

    def browse_video_file(self):
        """Open file dialog to select a video file"""
        from utils.dialog_helpers import select_video_files

        file_path = select_video_files(title="Select Video File", multiple=False)
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