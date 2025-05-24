#!/usr/bin/env python3
"""
Video Generator GUI
A professional-looking UI for generating videos from a text and images
"""
import datetime
import os
import tkinter as tk
from tkinter import messagebox, ttk
import threading

from utils.gui_helpers import *


class UIComponentFactory:
    """Factory class for creating consistent UI components"""

    def __init__(self, colors):
        self.colors = colors

    def create_styled_button(self, parent, text, command, bg_color=None, width=12, **kwargs):
        """Create a consistently styled button"""
        bg_color = bg_color or self.colors["secondary"]
        hover_color = kwargs.pop('hover_color', self.colors["primary"])

        button = tk.Button(
            parent,
            text=text,
            bg=bg_color,
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            width=width,
            command=command,
            activebackground=hover_color,
            **kwargs
        )

        # Add hover effect
        HoverEffect(button, hover_bg=hover_color, normal_bg=bg_color)
        return button

    def create_progress_section(self, parent, title="Progress"):
        """Create a consistent progress section with bar and label"""
        frame = ttk.LabelFrame(parent, text=title, padding=10)

        progress_bar = ttk.Progressbar(frame, orient="horizontal", mode='determinate')
        progress_bar.pack(fill="x", padx=5, pady=5)

        progress_label = ttk.Label(frame, text="0%", font=("Helvetica", 10))
        progress_label.pack(pady=5)

        return frame, progress_bar, progress_label

    def create_labeled_frame(self, parent, title, padding=10):
        """Create a consistently styled labeled frame"""
        return ttk.LabelFrame(parent, text=title, padding=padding)

# Import the model and UI components
try:
    # Try to import OpenCV, but don't fail if it's not available
    try:
        import cv2
    except ImportError:
        print("OpenCV (cv2) not available. Some features may be limited.")

    from models.video_generator import VideoGeneratorModel
    from ui.image_selector import ImageSelector
    from ui.text_redirector import TextRedirector
    from ui.input_tab import InputTab
    from ui.image_tab import ImageTab
    from ui.video_tab import VideoTab
    from ui.option_tab import OptionTab
    from ui.batch_tab import BatchTab
except ImportError as e:
    print(f"Error importing required modules: {e}")
    # Create a fallback model class if import fails
    class VideoGeneratorModel:
        """Fallback model class when the real one can't be imported"""
        def __init__(self):
            print("WARNING: Using fallback VideoGeneratorModel")
            self.text_input = None
            self.image_source = None
            self.website_url = None
            self.local_folder = None
            self.selected_images = []
            self.processing_option = "cpu"
            self.progress_callback = None

        def set_progress_callback(self, callback):
            """Set a callback function for progress updates"""
            self.progress_callback = callback

        def generate_video(self, stop_event=None):
            """Generate a placeholder video"""
            _ = stop_event  # Acknowledge unused parameter
            print("Using fallback video generation")
            # Create output directory
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join("output", f"video_{timestamp}")
            os.makedirs(output_dir, exist_ok=True)

            # Create placeholder files
            subtitle_file = os.path.join(output_dir, "subtitles.ass")
            video_file = os.path.join(output_dir, "video.mp4")

            with open(subtitle_file, "w") as f:
                f.write("Placeholder subtitle file")

            with open(video_file, "w") as f:
                f.write("Placeholder video file")

            return subtitle_file, video_file, output_dir

        def finalize_video(self, subtitle_path, video_path, output_dir, stop_event=None):
            """Finalize the placeholder video"""
            # Acknowledge unused parameters
            _ = subtitle_path
            _ = video_path
            _ = stop_event

            final_output = os.path.join(output_dir, "final_output.mp4")

            with open(final_output, "w") as f:
                f.write("Placeholder final video file")

            return final_output

# Import services
try:
    from services.image_service import download_images, download_images_for_preview, copy_selected_images
except ImportError as e:
    print(f"Error importing image service functions: {e}")
    # Create fallback functions
    def download_images(url, output_folder, max_images=10):
        """Fallback download_images function"""
        print(f"Fallback: download_images({url}, {output_folder}, {max_images})")
        return []

    def download_images_for_preview(url, output_folder, max_images=10):
        """Fallback download_images_for_preview function"""
        print(f"Fallback: download_images_for_preview({url}, {output_folder}, {max_images})")
        return []

    def copy_selected_images(image_paths, output_folder):
        """Fallback copy_selected_images function"""
        print(f"Fallback: copy_selected_images({image_paths}, {output_folder})")
        return False

class VideoGeneratorGUI:
    """Main GUI class for the Video Generator application"""
    def __init__(self, root):
        self.root = root
        self.root.configure(bg="#ffffff")  # Set root background

        # Define modern color scheme
        self.colors = {
            "primary": "#2c3e50",      # Dark blue-gray
            "secondary": "#3498db",    # Blue
            "accent": "#e74c3c",       # Red
            "success": "#2ecc71",      # Green
            "background": "#ecf0f1",   # Light gray
            "text": "#34495e",         # Dark text
            "light_text": "#7f8c8d"    # Gray text
        }

        # Initialize UI component factory
        self.ui_factory = UIComponentFactory(self.colors)

        # Initialize all instance attributes that will be set in setup methods
        # Tab components
        self.input_tab_component = None
        self.image_tab_component = None
        self.video_tab_component = None
        self.option_tab_component = None
        self.batch_tab_component = None

        # Log tab components
        self.log_text = None

        # Batch processing components
        self.temp_dir = None
        self.photo_references = None
        self.image_vars = None

        # Configure ttk style
        self._configure_styles()

        # Initialize the model
        self.model = VideoGeneratorModel()

        # Initialize stop event for threading
        self.stop_event = None
        self.generation_thread = None
        self.download_thread = None

        # Track selected images
        self.selected_images = []

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)

        # Create tabs
        self.input_tab = ttk.Frame(self.notebook)
        self.image_tab = ttk.Frame(self.notebook)
        self.video_tab = ttk.Frame(self.notebook)
        self.option_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        self.batch_tab = ttk.Frame(self.notebook)

        # Add tabs to notebook
        self.notebook.add(self.input_tab, text=" Input ")
        self.notebook.add(self.image_tab, text=" Images ")
        self.notebook.add(self.video_tab, text=" Video ")
        self.notebook.add(self.option_tab, text=" Option ")
        self.notebook.add(self.batch_tab, text=" Batch Processing ")
        self.notebook.add(self.log_tab, text=" Log ")

        # Set up tabs (log tab first since other tabs may need to log messages)
        self.setup_log_tab()
        self.setup_input_tab()
        self.setup_image_tab()
        self.setup_video_tab()
        self.setup_option_tab()
        self.setup_batch_tab()

    def _configure_styles(self):
        """Configure ttk styles for consistent appearance"""
        style = ttk.Style()
        style.theme_use("clam")  # Modern theme
        style.configure("TButton", font=("Helvetica", 10), padding=8)
        style.configure("TLabel", font=("Helvetica", 10), background=self.colors["background"], foreground=self.colors["text"])
        style.configure("TFrame", background=self.colors["background"])
        style.configure("TLabelframe", background=self.colors["background"], foreground=self.colors["text"])
        style.configure("TLabelframe.Label", font=("Helvetica", 11, "bold"), background=self.colors["background"])
        style.configure("TProgressbar", thickness=20, background=self.colors["success"])

        # Configure checkbutton style to use checkmarks instead of X
        style.configure("TCheckbutton", background=self.colors["background"], foreground=self.colors["text"])
        style.map("TCheckbutton",
                 indicatorcolor=[("selected", self.colors["success"]), ("!selected", "white")],
                 indicatorrelief=[("pressed", "sunken"), ("!pressed", "raised")])

    def setup_input_tab(self):
        """Set up the input tab using the InputTab component"""
        # Create the InputTab component
        self.input_tab_component = InputTab(self.input_tab, self)

    def setup_image_tab(self):
        """Set up the image tab using the ImageTab component"""
        # Create the ImageTab component
        self.image_tab_component = ImageTab(self.image_tab, self)

    def setup_video_tab(self):
        """Set up the video tab using the VideoTab component"""
        # Create the VideoTab component
        self.video_tab_component = VideoTab(self.video_tab, self)

    def setup_option_tab(self):
        """Set up the option tab using the OptionTab component"""
        # Create the OptionTab component
        self.option_tab_component = OptionTab(self.option_tab, self)

    def setup_batch_tab(self):
        """Set up the batch tab using the BatchTab component"""
        # Create the BatchTab component
        self.batch_tab_component = BatchTab(self.batch_tab, self)

    def setup_log_tab(self):
        self.log_text = tk.Text(
            self.log_tab,
            wrap="word",
            font=("Consolas", 11),
            bg="#f8f9fa",
            fg=self.colors["text"],
            borderwidth=1,
            relief="solid"
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10, side="left")

        scrollbar = ttk.Scrollbar(self.log_tab, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.log_text.config(state="disabled")

        self.log("Welcome to Video Generator")
        self.log("Enter text and select images to create your video")

    def log(self, message):
        """Add a message to the log with timestamp"""
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")

        # Always print to console
        print(f"{timestamp} {message}")

        # Only update GUI log if log_text is available
        if self.log_text is not None:
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, f"{timestamp} {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")

    def update_image_progress(self, value, message=None):
        """Update the image progress bar and log message"""
        if self.image_tab_component:
            self.image_tab_component.update_image_progress(value, message)
        else:
            if message:
                self.log(message)

    def generate_video_thread(self):
        try:
            def progress_callback(value, message=None):
                self.root.after(0, lambda: self.update_progress_ui(value, message))
            self.model.set_progress_callback(progress_callback)

            # Update enhancement options before generating
            self.update_enhancement_options()

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
        self.log(f"Video generated successfully: {os.path.basename(final_video)}")
        self.update_progress_ui(100, "Video generated successfully")
        self.reset_ui()
        response = messagebox.askyesno(
            "Success",
            f"Video generated successfully: {os.path.basename(final_video)}\n\nDo you want to open it now?"
        )
        if response:
            self.open_file(final_video)

    def display_preview_images(self, image_paths):
        """Display preview images with checkboxes"""
        if self.image_tab_component:
            self.image_tab_component.display_preview_images(image_paths)
        else:
            self.log("Image tab component not available")
    def continue_with_selected_images(self):
        """Continue with selected images by delegating to ImageTab component"""
        if not self.image_tab_component:
            return

        # Get selected images from ImageTab component
        if not hasattr(self.image_tab_component, 'image_vars') or not self.image_tab_component.image_vars:
            messagebox.showwarning("No Images", "No images available to select")
            return

        selected = []
        for var, path in self.image_tab_component.image_vars:
            if var.get() == 1:
                selected.append(path)
        if not selected:
            messagebox.showwarning("No Images", "Please select at least one image")
            return

        # Update selected images and switch to input tab
        self.selected_images = selected
        self.log(f"Selected {len(selected)} images")
        self.notebook.select(0)

        # Delegate to InputTab component for video generation
        if self.input_tab_component:
            # Get text and URL from InputTab component
            text = self.input_tab_component.get_text_input()
            url = self.input_tab_component.get_url_input()

            if not text:
                messagebox.showwarning("Input Error", "Please enter text for voice generation")
                return

            # Use InputTab's video generation setup
            self.input_tab_component._setup_video_generation(text, url)

    def update_enhancement_options(self):
        """Update the model with current enhancement options"""
        if self.option_tab_component:
            self.option_tab_component.update_enhancement_options()
        else:
            self.log("Option tab component not available")

    def reset_enhancement_options(self):
        """Reset enhancement options to defaults"""
        if self.option_tab_component:
            self.option_tab_component.reset_enhancement_options()
        else:
            self.log("Option tab component not available")

    def reset_ui(self):
        """Reset UI components to default state"""
        # Reset input tab UI through a component
        if self.input_tab_component:
            self.input_tab_component.reset_ui()

        # Reset batch progress through the batch tab component
        if self.batch_tab_component:
            self.batch_tab_component.reset_batch_ui()

    def update_progress_ui(self, value, message=None):
        """Update the progress bar and log message"""
        # Update input tab progress bar through a component
        if self.input_tab_component:
            self.input_tab_component.progress_bar["value"] = value
            self.input_tab_component.progress_label.config(text=f"{value}%")

        # Always update batch progress bar during batch processing
        if self.batch_tab_component:
            self.batch_tab_component.update_batch_progress(value, None)  # Don't pass a message to avoid duplicate logging

        if message:
            self.log(message)

        # Force UI update
        self.root.update_idletasks()

    def open_file(self, file_path):
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

    def clean_button_click(self):
        """Clear all images by delegating to ImageTab component"""
        if self.image_tab_component:
            self.image_tab_component.clear_images()
        else:
            self.selected_images = []
            self.log("Cleaned all selected images")

def main():
    """Main function to run the GUI application"""
    root = tk.Tk()
    root.title("Video Generator")
    root.configure(bg="#ffffff")
    window_width = 900
    window_height = 650
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    root.minsize(800, 600)
    VideoGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
