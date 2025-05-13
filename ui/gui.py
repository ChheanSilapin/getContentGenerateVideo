"""
VideoGeneratorGUI - Main GUI class for the application
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog
import threading

from models.video_generator import VideoGeneratorModel
from ui.image_selector import ImageSelector
from ui.text_redirector import TextRedirector
from config import GUI_WINDOW_SIZE, GUI_TITLE

class VideoGeneratorGUI:
    """Main GUI class for the Video Generator application"""
    def __init__(self, root):
        """
        Initialize the GUI
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title(GUI_TITLE)
        self.root.geometry(GUI_WINDOW_SIZE)
        
        # Model for handling video generation
        self.model = VideoGeneratorModel()
        
        # Variables to store user inputs
        self.text_var = tk.StringVar()
        self.source_var = tk.IntVar(value=1)  # Default to website URL
        self.url_var = tk.StringVar()
        self.folder_var = tk.StringVar()
        
        # Thread control
        self.generation_thread = None
        self.stop_event = None
        
        # Create the GUI components
        self._create_notebook()
        self._create_status_bar()
        self._create_control_buttons()
        
    def _create_notebook(self):
        """Create the tabbed interface"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.input_tab = ttk.Frame(self.notebook)
        self.images_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.input_tab, text="Input")
        self.notebook.add(self.images_tab, text="Images")
        self.notebook.add(self.log_tab, text="Log")
        
        # Setup each tab
        self._setup_input_tab()
        self._setup_images_tab()
        self._setup_log_tab()
        
    def _setup_input_tab(self):
        """Setup the input tab with text entry and source selection"""
        # Text input section
        tk.Label(self.input_tab, text="Enter text for voice generation:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.text_entry = tk.Text(self.input_tab, height=5, width=50)
        self.text_entry.pack(fill="x", padx=10, pady=5)
        
        # Image source selection
        tk.Label(self.input_tab, text="Choose image source:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        
        # Website URL option
        url_frame = tk.Frame(self.input_tab)
        url_frame.pack(fill="x", padx=10, pady=5)
        tk.Radiobutton(url_frame, text="Website URL", variable=self.source_var, value=1).pack(side="left")
        self.url_entry = tk.Entry(url_frame, textvariable=self.url_var, width=50)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Local folder option
        folder_frame = tk.Frame(self.input_tab)
        folder_frame.pack(fill="x", padx=10, pady=5)
        tk.Radiobutton(folder_frame, text="Local folder", variable=self.source_var, value=2).pack(side="left")
        self.folder_entry = tk.Entry(folder_frame, textvariable=self.folder_var, width=40)
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Browse button for folder selection
        browse_button = tk.Button(folder_frame, text="Browse & Select Images", command=self._browse_folder)
        browse_button.pack(side="right", padx=5)
        
    def _setup_images_tab(self):
        """Setup the images tab for displaying and selecting images"""
        self.images_frame = tk.Frame(self.images_tab)
        self.images_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create image selector
        self.image_selector = ImageSelector(self.images_frame, self._update_image_count)
        
    def _setup_log_tab(self):
        """Setup the log tab for displaying console output"""
        # Create a text widget for log output
        self.log_text = tk.Text(self.log_tab, wrap="word", height=20, width=80)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text.configure(state="disabled")
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
        # Redirect stdout to the text widget
        self.stdout_redirector = TextRedirector(self.log_text)
        sys.stdout = self.stdout_redirector
        
    def _create_status_bar(self):
        """Create the status bar at the bottom of the window"""
        self.status_frame = tk.Frame(self.root)
        self.status_frame.pack(fill="x", side="bottom", padx=10, pady=5)
        
        # Status label
        self.status_label = tk.Label(self.status_frame, text="Ready", anchor="w")
        self.status_label.pack(side="left")
        
        # Image count label
        self.image_count_label = tk.Label(self.status_frame, text="No images selected", anchor="e")
        self.image_count_label.pack(side="right")
        
    def _create_control_buttons(self):
        """Create the control buttons at the bottom of the window"""
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(fill="x", side="bottom", padx=10, pady=5)
        
        # Generate button
        self.generate_button = tk.Button(self.button_frame, text="Generate Video", command=self._start_generation, bg="#4CAF50", fg="white", height=2)
        self.generate_button.pack(side="left", padx=5, fill="x", expand=True)
        
        # Stop button (initially disabled)
        self.stop_button = tk.Button(self.button_frame, text="Stop", command=self._stop_generation, state="disabled", bg="#F44336", fg="white", height=2)
        self.stop_button.pack(side="left", padx=5, fill="x", expand=True)
        
        # Clear button
        self.clear_button = tk.Button(self.button_frame, text="Clear", command=self._clear_form, height=2)
        self.clear_button.pack(side="left", padx=5, fill="x", expand=True)
        
    def _browse_folder(self):
        """Open a folder browser dialog and load images from the selected folder"""
        folder_path = filedialog.askdirectory(title="Select Folder Containing Images")
        if folder_path:
            self.folder_var.set(folder_path)
            self.source_var.set(2)  # Set to local folder option
            
            # Switch to images tab
            self.notebook.select(self.images_tab)
            
            # Load images from the folder
            if not self.image_selector.load_images_from_folder(folder_path):
                self.status_label.config(text="No images found in the selected folder")
            else:
                self.status_label.config(text=f"Loaded images from {folder_path}")
                
    def _update_image_count(self):
        """Update the image count label"""
        count = len(self.image_selector.selected_images)
        if count == 0:
            self.image_count_label.config(text="No images selected")
        else:
            self.image_count_label.config(text=f"{count} images selected")
            
    def _clear_form(self):
        """Clear all form inputs"""
        self.text_entry.delete("1.0", "end")
        self.url_var.set("")
        self.folder_var.set("")
        self.source_var.set(1)  # Reset to website URL option
        self.image_selector.clear()
        self.status_label.config(text="Form cleared")
        
    def _start_generation(self):
        """Start the video generation process in a separate thread"""
        # Get text input
        text_input = self.text_entry.get("1.0", "end-1c").strip()
        if not text_input:
            self.status_label.config(text="Please enter text for voice generation")
            return
            
        # Get image source
        image_source = str(self.source_var.get())
        website_url = self.url_var.get().strip()
        local_folder = self.folder_var.get().strip()
        
        if image_source == "1" and not website_url:
            self.status_label.config(text="Please enter a website URL")
            return
            
        if image_source == "2" and not local_folder and not self.image_selector.selected_images:
            self.status_label.config(text="Please select a folder or individual images")
            return
            
        # Update model with user inputs
        self.model.text_input = text_input
        self.model.image_source = image_source
        self.model.website_url = website_url
        self.model.local_folder = local_folder
        self.model.selected_images = self.image_selector.selected_images.copy()
        
        # Create a stop event for the thread
        self.stop_event = threading.Event()
        
        # Disable generate button and enable stop button
        self.generate_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_label.config(text="Generating video...")
        
        # Start generation in a separate thread
        self.generation_thread = threading.Thread(target=self._run_generation)
        self.generation_thread.daemon = True
        self.generation_thread.start()
        
    def _run_generation(self):
        """Run the video generation process"""
        try:
            # Generate the video
            subtitlePath, videoPath, output_dir = self.model.generate_video(self.stop_event)
            
            # Check if we were stopped
            if self.stop_event and self.stop_event.is_set():
                self.root.after(0, lambda: self.status_label.config(text="Generation stopped by user"))
                self.root.after(0, self._reset_buttons)
                return
                
            # Finalize the video
            if subtitlePath and videoPath and output_dir:
                result = self.model.finalize_video(subtitlePath, videoPath, output_dir, self.stop_event)
                if result:
                    self.root.after(0, lambda: self.status_label.config(text=f"Video generated successfully: {result}"))
                else:
                    self.root.after(0, lambda: self.status_label.config(text="Failed to finalize video"))
            else:
                self.root.after(0, lambda: self.status_label.config(text="Video generation failed"))
                
        except Exception as e:
            import traceback
            print(f"\nERROR in generation thread: {e}")
            traceback.print_exc()
            self.root.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}"))
            
        finally:
            # Reset buttons
            self.root.after(0, self._reset_buttons)
            
    def _stop_generation(self):
        """Stop the video generation process"""
        if self.stop_event:
            self.stop_event.set()
            self.status_label.config(text="Stopping generation...")
            self.stop_button.config(state="disabled")
            
    def _reset_buttons(self):
        """Reset button states after generation completes or is stopped"""
        self.generate_button.config(state="normal")
        self.stop_button.config(state="disabled")