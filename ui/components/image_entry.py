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

        # Folder label
        folder_label = ttk.Label(
            folder_frame,
            text="📁 Image Folder:",
            font=("Cascadia Code", 8, "bold")
        )
        folder_label.pack(anchor="w", pady=(0, 4))

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

        # Browse button
        browse_button = self.main_gui.ui_factory.create_icon_button(
            path_row, "Browse", self.browse_folder,
            icon="📁", width=12
        )
        browse_button.pack(side="right")

    def setup_prompt_section(self):
        """Set up prompt input section"""
        # Clean text frame like the selected style
        text_frame = ttk.LabelFrame(self.entry_frame, text="📝 Text Prompt for Video", padding=8)
        text_frame.pack(fill="x", pady=(0, 8))

        # Text input row with remove button (like video entry)
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
        self.prompt_text_widget.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Remove button aligned with text input - compact size with text
        remove_button = self.main_gui.ui_factory.create_icon_button(
            prompt_input_frame, "🗑️ Remove", self.remove_entry,
            width=12
        )
        remove_button.pack(side="right", anchor="n", pady=(0, 0))

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

    def browse_folder(self):
        """Browse for image folder"""
        from utils.dialog_helpers import select_folder
        folder_path = select_folder(title="Select Image Folder")
        
        if folder_path:
            self.folder_path.set(folder_path)
            self.analyze_folder(folder_path)
            self.main_gui.log(f"Selected folder: {os.path.basename(folder_path)}")

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
        
        return (folder and 
                os.path.exists(folder) and 
                len(self.detected_images) > 0 and 
                prompt)

    def get_data(self):
        """Get the entry data"""
        return {
            'folder_path': self.folder_path.get(),
            'prompt': self.prompt_text_widget.get('1.0', tk.END).strip(),
            'images': self.detected_images.copy(),
            'text_file': self.detected_text_file,
            'entry_id': self.entry_id
        }

    def set_data(self, folder_path, prompt=None):
        """Set the entry data"""
        if folder_path:
            self.folder_path.set(folder_path)
            self.analyze_folder(folder_path)
        
        if prompt:
            self.prompt_text_widget.delete('1.0', tk.END)
            self.prompt_text_widget.insert('1.0', prompt)

    def destroy(self):
        """Clean up the entry"""
        if self.entry_frame:
            self.entry_frame.destroy()
