"""
Main window UI for the Video Generator application
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import datetime

# Import the model
from models.video_generator import VideoGeneratorModel

# Import UI components
from ui.image_selector import ImageSelector
from ui.text_redirector import TextRedirector

class MainWindow:
    """Main window UI for the Video Generator application"""
    def __init__(self, root):
        """Initialize the main window"""
        self.root = root
        self.root.title("Video Generator")
        self.root.geometry("800x800")
        self.root.minsize(800, 600)
        
        # Set colors
        self.colors = {
            "primary": "#3498db",
            "secondary": "#2980b9",
            "success": "#2ecc71",
            "danger": "#e74c3c",
            "warning": "#f39c12",
            "background": "#ecf0f1",
            "text": "#34495e",
            "light_text": "#7f8c8d",
            "accent": "#9b59b6"  # Add the missing accent color
        }
        
        # Create main frame
        self.main_frame = tk.Frame(self.root, bg=self.colors["background"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.input_tab = ttk.Frame(self.notebook)
        self.image_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.input_tab, text="Input")
        self.notebook.add(self.image_tab, text="Images")
        self.notebook.add(self.log_tab, text="Log")
        
        # Initialize model
        self.model = VideoGeneratorModel()
        
        # Initialize variables
        self.stop_event = None
        self.generation_thread = None
        
        # Set up tabs
        self.setup_input_tab()
        self.setup_image_tab()
        self.setup_log_tab()
        
        # Remove any duplicate image selectors
        self.image_selector = None
        self.setup_image_tab()

    def setup_input_tab(self):
        """Set up the input tab"""
        # Main frame for input tab
        main_frame = ttk.Frame(self.input_tab, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Text input section
        text_frame = ttk.LabelFrame(main_frame, text="Text Input", padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create a frame to contain the text widget and its scrollbar
        text_container = ttk.Frame(text_frame)
        text_container.pack(fill=tk.BOTH, expand=True)

        # Text input with scrollbar
        self.text_input = tk.Text(
            text_container,
            wrap=tk.WORD,
            height=8,
            font=("Helvetica", 11),
            borderwidth=1,
            relief="solid"
        )
        self.text_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        text_scrollbar = ttk.Scrollbar(text_container, command=self.text_input.yview)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_input.config(yscrollcommand=text_scrollbar.set)

        # Image source section
        image_source_frame = ttk.LabelFrame(main_frame, text="Image Source", padding=10)
        image_source_frame.pack(fill=tk.X, padx=5, pady=5)

        url_frame = ttk.Frame(image_source_frame)
        url_frame.pack(fill=tk.X, padx=5, pady=5)

        url_label = ttk.Label(url_frame, text="Website URL:")
        url_label.pack(side=tk.LEFT, padx=5)

        self.url_entry = ttk.Entry(url_frame, width=50, font=("Helvetica", 10))
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Image selection button with hover effect
        image_select_button = tk.Button(
            url_frame,
            text="Browse Images",
            bg=self.colors["secondary"],
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            activebackground=self.colors["primary"],
            command=lambda: self.notebook.select(self.image_tab)
        )
        image_select_button.pack(side=tk.LEFT, padx=5)
        image_select_button.bind("<Enter>", lambda e: image_select_button.config(bg=self.colors["primary"]))
        image_select_button.bind("<Leave>", lambda e: image_select_button.config(bg=self.colors["secondary"]))

        # Processing options
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding=10)
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        cpu_gpu_frame = ttk.Frame(options_frame)
        cpu_gpu_frame.pack(fill=tk.X, padx=5, pady=5)

        cpu_gpu_label = ttk.Label(cpu_gpu_frame, text="Processing Unit:")
        cpu_gpu_label.pack(side=tk.LEFT, padx=5)

        self.cpu_gpu = tk.StringVar(value="CPU")
        cpu_radio = ttk.Radiobutton(cpu_gpu_frame, text="CPU", variable=self.cpu_gpu, value="CPU")
        cpu_radio.pack(side=tk.LEFT, padx=10)

        gpu_radio = ttk.Radiobutton(cpu_gpu_frame, text="GPU", variable=self.cpu_gpu, value="GPU")
        gpu_radio.pack(side=tk.LEFT, padx=10)

        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=10)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        self.progress_label = ttk.Label(progress_frame, text="0%", font=("Helvetica", 10))
        self.progress_label.pack(pady=5)

        # Button frame
        button_frame = ttk.Frame(main_frame, padding=10)
        button_frame.pack(fill=tk.X)

        # Action buttons
        self.generate_button = tk.Button(
            button_frame,
            text="Generate Video",
            bg=self.colors["success"],
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            width=12,
            command=self.start_button_click,
            activebackground="#27ae60"
        )
        self.generate_button.pack(side=tk.LEFT, padx=5)
        self.generate_button.bind("<Enter>", lambda e: self.generate_button.config(bg="#27ae60"))
        self.generate_button.bind("<Leave>", lambda e: self.generate_button.config(bg=self.colors["success"]))

        self.stop_button = tk.Button(
            button_frame,
            text="Stop",
            bg=self.colors["danger"],  # Change from "accent" to "danger"
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            width=12,
            command=self.stop_button_click,
            activebackground="#c0392b",
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.bind("<Enter>", lambda e: self.stop_button.config(bg="#c0392b"))
        self.stop_button.bind("<Leave>", lambda e: self.stop_button.config(bg=self.colors["danger"]))  # Change from "accent" to "danger"

        clear_button = tk.Button(
            button_frame,
            text="Clear All",
            bg=self.colors["secondary"],
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            width=12,
            command=self.clear_input_button_click,
            activebackground=self.colors["primary"]
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        clear_button.bind("<Enter>", lambda e: clear_button.config(bg=self.colors["primary"]))
        clear_button.bind("<Leave>", lambda e: clear_button.config(bg=self.colors["secondary"]))

    def setup_log_tab(self):
        """Set up the log tab"""
        self.log_text = tk.Text(
            self.log_tab,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#f8f9fa",
            fg=self.colors["text"],
            borderwidth=1,
            relief="solid",
            height=15
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(self.log_tab, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.log_text.config(state="disabled")

        self.log("Welcome to Video Generator")
        self.log("Enter text and select images to create your video")

    def start_button_click(self):
        """Start the video generation process"""
        if self.generation_thread and self.generation_thread.is_alive():
            messagebox.showwarning("Process Running", "Video generation is already in progress")
            return

        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Input Error", "Please enter text for voice generation")
            return

        url = self.url_entry.get().strip()
        selected_images = self.image_selector.get_selected_images()

        if not url and not selected_images:
            messagebox.showwarning("Input Error", "Please provide either a website URL or select images")
            return

        if url and not selected_images:
            # Redirect to image selector to download and select images
            self.log("Downloading images for preview...")
            self.notebook.select(self.image_tab)
            self.image_selector.download_images_from_url(url)
            return

        self.model.text_input = text
        self.model.processing_option = self.cpu_gpu.get().lower()

        if selected_images:
            self.model.image_source = "3"  # Selected images
            self.model.selected_images = selected_images
            self.model.website_url = ""
            self.model.local_folder = ""
        elif url:
            self.model.image_source = "1"  # Website URL
            self.model.website_url = url
            self.model.local_folder = ""

        self.log(f"Starting video generation with {self.cpu_gpu.get()}")
        self.log(f"Text: {text[:50]}..." if len(text) > 50 else f"Text: {text}")

        if url and not selected_images:
            self.log(f"URL: {url}")
        if selected_images:
            self.log(f"Using {len(selected_images)} selected images")

        self.progress_bar["value"] = 0
        self.progress_label.config(text="0%")
        self.generate_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.stop_event = threading.Event()
        self.generation_thread = threading.Thread(target=self.generate_video_thread)
        self.generation_thread.daemon = True
        self.generation_thread.start()

    def generate_video_thread(self):
        """Run the video generation process in a separate thread"""
        try:
            def progress_callback(value, message=None):
                self.root.after(0, lambda: self.update_progress_ui(value, message))

            self.model.set_progress_callback(progress_callback)
            self.model.use_effects = True
            self.model.zoom_effect = True
            self.model.fade_effect = True

            subtitle_path, video_path, output_dir = self.model.generate_video(self.stop_event)

            if self.stop_event.is_set():
                self.root.after(0, lambda: self.log("Video generation stopped by user"))
                self.root.after(0, lambda: self.reset_ui())
                return

            if subtitle_path and video_path and output_dir:
                final_video = self.model.finalize_video(subtitle_path, video_path, output_dir, self.stop_event)

                if self.stop_event.is_set():
                    self.root.after(0, lambda: self.log("Video finalization stopped by user"))
                    self.root.after(0, lambda: self.reset_ui())
                    return

                if final_video:
                    self.root.after(0, lambda: self.video_completed(final_video))
                else:
                    self.root.after(0, lambda: self.log("Failed to finalize video"))
                    self.root.after(0, lambda: self.reset_ui())
            else:
                self.root.after(0, lambda: self.log("Failed to generate video"))
                self.root.after(0, lambda: self.reset_ui())
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self.log(f"Error: {e}"))
            self.root.after(0, lambda: self.reset_ui())

    def video_completed(self, final_video):
        """Handle video completion"""
        self.log(f"Video generated successfully: {os.path.basename(final_video)}")
        self.update_progress_ui(100, "Video generated successfully")
        self.reset_ui()
        response = messagebox.askyesno(
            "Success",
            f"Video generated successfully: {os.path.basename(final_video)}\n\nDo you want to open it now?"
        )
        if response:
            self.open_file(final_video)

    def stop_button_click(self):
        """Stop the video generation process"""
        if self.stop_event:
            self.stop_event.set()
            self.log("Stopping process...")
            self.root.after(1000, self.reset_ui)

    def reset_ui(self):
        """Reset the UI after processing"""
        self.generate_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar["value"] = 0
        self.progress_label.config(text="0%")

    def update_progress_ui(self, value, message=None):
        """Update the progress UI"""
        self.progress_bar["value"] = value
        self.progress_label.config(text=f"{value}%")
        if message:
            self.log(message)

    def clear_input_button_click(self):
        """Clear all input fields"""
        self.text_input.delete("1.0", tk.END)
        self.url_entry.delete(0, tk.END)
        self.progress_bar["value"] = 0
        self.progress_label.config(text="0%")
        self.image_selector.clear_images()
        self.log("Cleared all inputs")

    def open_file(self, file_path):
        """Open a file with the default application"""
        try:
            import platform
            import subprocess
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", file_path], check=True)
            else:
                subprocess.run(["xdg-open", file_path], check=True)
            self.log(f"Opened file: {os.path.basename(file_path)}")
        except Exception as e:
            self.log(f"Error opening file: {e}")
            messagebox.showerror("Error", f"Could not open file: {e}")

    def log(self, message):
        """Log a message to the log tab"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        print(formatted_message)

    def use_selected_images(self):
        """Use the selected images and return to input tab"""
        selected_images = self.image_selector.get_selected_images()
        if selected_images:
            self.log(f"Selected {len(selected_images)} images for use")
            self.notebook.select(self.input_tab)
        else:
            messagebox.showwarning("No Images", "Please select at least one image")

    def setup_image_tab(self):
        """Set up the image tab"""
        # Clear any existing widgets in the image tab
        for widget in self.image_tab.winfo_children():
            widget.destroy()
            
        # Create image selector with callback
        self.image_selector = ImageSelector(
            self.image_tab, 
            colors=self.colors, 
            log_callback=self.log
        )
        
        # Set update callback
        self.image_selector.update_callback = self.use_selected_images







