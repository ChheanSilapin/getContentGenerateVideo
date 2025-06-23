"""
Image Entry Component - Individual image folder input entry
Similar to VideoEntry but for image folders with text files
"""
from utils.common_imports import tk, ttk, os

class ImageEntry:
    """Individual image folder entry with folder selector and prompt input"""
    
    def __init__(self, parent_frame, main_gui, remove_callback, entry_id):
        self.parent_frame = parent_frame
        self.main_gui = main_gui
        self.remove_callback = remove_callback
        self.entry_id = entry_id
        
        # Entry data
        self.folder_path = tk.StringVar()
        self.prompt_text = tk.StringVar()
        self.detected_images = []
        self.detected_text_file = None

        # UI components
        self.entry_frame = None
        self.setup_entry()

    def setup_entry(self):
        """Set up the UI for this image entry"""
        # Main entry frame with better styling
        self.entry_frame = ttk.LabelFrame(
            self.parent_frame,
            text=f"🖼️ Image Folder {self.entry_id}",
            padding=8
        )
        self.entry_frame.pack(fill="x", padx=6, pady=4)

        # Folder selection section
        self.setup_folder_section()
        
        # Prompt section
        self.setup_prompt_section()
        
        # Status and remove section
        self.setup_status_section()

    def setup_folder_section(self):
        """Set up folder selection section"""
        folder_frame = ttk.Frame(self.entry_frame)
        folder_frame.pack(fill="x", pady=(0, 8))

        # Folder label row with remove button
        label_row = ttk.Frame(folder_frame)
        label_row.pack(fill="x", pady=(0, 4))

        # Folder label
        folder_label = ttk.Label(
            label_row,
            text="📁 Image Folder:",
            font=("Cascadia Code", 8, "bold")
        )
        folder_label.pack(side="left", anchor="w")

        # Add remove icon button aligned with folder label
        from config import GUI_COLORS
        remove_button = tk.Button(
            label_row,
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

        # Folder path row
        path_row = ttk.Frame(folder_frame)
        path_row.pack(fill="x")

        # Folder path entry
        self.folder_entry = ttk.Entry(
            path_row,
            textvariable=self.folder_path,
            font=("Cascadia Code", 10),
            state="readonly"
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))



    def setup_prompt_section(self):
        """Set up prompt input section"""
        # Clean text frame like the selected style
        text_frame = ttk.LabelFrame(self.entry_frame, text="📝 Text Prompt for Video", padding=8)
        text_frame.pack(fill="x", pady=(0, 8))

        # Text input row
        prompt_input_frame = ttk.Frame(text_frame)
        prompt_input_frame.pack(fill="x")

        # Clean text area - reduced height for more compact design
        self.prompt_text_widget = tk.Text(
            prompt_input_frame,
            height=2,
            wrap="word",
            font=("Cascadia Code", 10),
            borderwidth=1,
            relief="solid",
            padx=4,
            pady=2
        )
        self.prompt_text_widget.pack(fill="x", expand=True)

        # Bind text changes
        self.prompt_text_widget.bind('<KeyRelease>', self.on_prompt_change)

    def setup_status_section(self):
        """Set up status section"""
        status_frame = ttk.Frame(self.entry_frame)
        status_frame.pack(fill="x")

        # Status info
        self.status_label = ttk.Label(
            status_frame,
            text="No folder selected",
            font=("Cascadia Code", 8),
            foreground="#7f8c8d"
        )
        self.status_label.pack(side="left", anchor="w")



    def analyze_folder(self, folder_path):
        """Analyze the selected folder for images and text files"""
        try:
            # Use centralized media analysis
            from utils.media_helpers import analyze_media_folder, load_text_file_content

            analysis = analyze_media_folder(folder_path, media_type="image")

            # Store results
            self.detected_images = analysis['media_files']
            self.detected_text_file = analysis['best_text_file']

            # Load text content if found
            if self.detected_text_file:
                content = load_text_file_content(self.detected_text_file)
                if content:
                    self.prompt_text_widget.delete('1.0', tk.END)
                    self.prompt_text_widget.insert('1.0', content)
                else:
                    self.main_gui.log(f"Warning: Could not read text file: {self.detected_text_file}")

            # Update status
            self.update_status()

        except Exception as e:
            self.main_gui.log(f"Error analyzing folder: {e}")
            self.status_label.config(text="Error analyzing folder")



    def update_status(self):
        """Update the status label"""
        from utils.media_helpers import get_media_folder_status

        # Create analysis result for status generation
        analysis_result = {
            'media_files': self.detected_images,
            'best_text_file': self.detected_text_file,
            'media_count': len(self.detected_images),
            'media_type': 'image'
        }

        status_text = get_media_folder_status(analysis_result)
        self.status_label.config(text=status_text)

    def on_prompt_change(self, event=None):
        """Handle prompt text changes"""
        # Update the prompt_text variable when text widget changes
        content = self.prompt_text_widget.get('1.0', tk.END).strip()
        self.prompt_text.set(content)

    def remove_entry(self):
        """Remove this entry"""
        if self.remove_callback:
            self.remove_callback(self.entry_id)

    def is_valid(self):
        """Check if this entry has valid data"""
        folder = self.folder_path.get().strip()
        prompt = self.prompt_text_widget.get('1.0', tk.END).strip()

        # Valid if we have images and prompt, regardless of whether it's folder-based or file-based
        has_images = len(self.detected_images) > 0
        has_prompt = bool(prompt)

        # For folder-based entries, check if folder exists
        # For file-based entries (multiple selected images), folder path will be a display string
        if folder.startswith("Multiple Selected Images"):
            # File-based entry - just check images and prompt
            return has_images and has_prompt
        else:
            # Folder-based entry - check folder exists too
            return (folder and
                    os.path.exists(folder) and
                    has_images and
                    has_prompt)

    def get_data(self):
        """Get the entry data"""
        folder_path_value = self.folder_path.get()

        # For file-based entries, set folder_path to None since it's not a real folder
        if folder_path_value.startswith("Multiple Selected Images"):
            folder_path_value = None

        return {
            'folder_path': folder_path_value,
            'prompt': self.prompt_text_widget.get('1.0', tk.END).strip(),
            'images': self.detected_images.copy(),
            'text_file': self.detected_text_file,
            'entry_id': self.entry_id,
            'is_file_based': folder_path_value is None  # Flag to indicate file-based entry
        }

    def set_data(self, folder_path, prompt=None):
        """Set the entry data"""
        if folder_path:
            self.folder_path.set(folder_path)
            self.analyze_folder(folder_path)

        if prompt:
            self.prompt_text_widget.delete('1.0', tk.END)
            self.prompt_text_widget.insert('1.0', prompt)

    def set_images_directly(self, image_files):
        """Set images directly without using folder path (for multiple file selection)"""
        try:
            # Validate that all files exist and are images
            valid_images = []
            for img_file in image_files:
                if os.path.exists(img_file) and self._is_image_file(img_file):
                    valid_images.append(img_file)
                else:
                    self.main_gui.log(f"Warning: Skipping invalid image file: {os.path.basename(img_file)}")

            if not valid_images:
                raise ValueError("No valid image files provided")

            # Set the detected images directly
            self.detected_images = valid_images
            self.detected_text_file = None  # No text file for direct selection

            # Update the folder path display to show "Multiple Selected Images"
            self.folder_path.set(f"Multiple Selected Images ({len(valid_images)} files)")

            # Update the entry title to reflect it's a file-based entry
            if self.entry_frame:
                self.entry_frame.config(text=f"🖼️ Selected Images {self.entry_id}")

            # Update status
            self.update_status()

            self.main_gui.log(f"Set {len(valid_images)} images directly for entry #{self.entry_id}")

        except Exception as e:
            self.main_gui.log(f"Error setting images directly: {e}")
            self.status_label.config(text="Error setting images")

    def _is_image_file(self, file_path):
        """Check if file is a valid image file"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
        return os.path.splitext(file_path.lower())[1] in image_extensions

    def destroy(self):
        """Clean up the entry"""
        if self.entry_frame:
            self.entry_frame.destroy()
