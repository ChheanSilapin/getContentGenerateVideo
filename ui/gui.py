#!/usr/bin/env python3
"""
Video Generator GUI
A professional-looking UI for generating videos from a text and images
"""
from utils.common_imports import tk, messagebox, ttk, filedialog

import datetime
import os
import sys

from utils.gui_helpers import *


class UIComponentFactory:
    """Factory class for creating consistent UI components"""

    def __init__(self, colors):
        self.colors = colors

    def create_styled_button(self, parent, text, command, bg_color=None, width=8, style="default", **kwargs):
        """Create a button that looks exactly like ttk.Button to match merge tab styling"""
        # Use ttk.Button for consistent styling with merge tab
        button = ttk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            **kwargs
        )
        return button

    def create_icon_button(self, parent, text, command, icon="", bg_color=None, width=12, **kwargs):
        """Create a button with icon and text matching merge tab ttk.Button style"""
        display_text = f"{icon} {text}" if icon else text
        return ttk.Button(parent, text=display_text, command=command, width=width, **kwargs)

    def create_primary_button(self, parent, text, command, width=15, **kwargs):
        """Create a ttk.Button matching merge tab style"""
        return ttk.Button(parent, text=text, command=command, width=width, **kwargs)

    def create_secondary_button(self, parent, text, command, width=12, **kwargs):
        """Create a ttk.Button matching merge tab style"""  
        return ttk.Button(parent, text=text, command=command, width=width, **kwargs)

    def create_danger_button(self, parent, text, command, width=12, **kwargs):
        """Create a ttk.Button matching merge tab style"""
        return ttk.Button(parent, text=text, command=command, width=width, **kwargs)

    def create_light_button(self, parent, text, command, width=12, **kwargs):
        """Create a ttk.Button matching merge tab style"""
        return ttk.Button(parent, text=text, command=command, width=width, **kwargs)

    def create_progress_section(self, parent, title="Progress"):
        """Create a consistent progress section with bar and prominent percentage label"""
        frame = ttk.LabelFrame(parent, text=title, padding=8)

        # Progress container for side-by-side layout
        progress_container = ttk.Frame(frame)
        progress_container.pack(fill="x", padx=5, pady=5)

        # Progress bar
        progress_bar = ttk.Progressbar(
            progress_container, 
            orient="horizontal", 
            mode='determinate',
            length=400
        )
        progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Enhanced percentage label - more prominent and visible
        progress_label = ttk.Label(
            progress_container, 
            text="0%", 
            font=("Cascadia Code", 14, "bold"),
            foreground="#2c3e50",
            background="#ecf0f1",
            relief="solid",
            borderwidth=1,
            width=8,
            anchor="center"
        )
        progress_label.pack(side="right", padx=(5, 0))

        return frame, progress_bar, progress_label

    def create_labeled_frame(self, parent, title, padding=2):  # Minimal default padding for 800x800
        """Create a consistently styled labeled frame"""
        return ttk.LabelFrame(parent, text=title, padding=padding)

    def create_output_folder_section(self, parent, title="Output Folder", initial_folder=None):
        """Create a reusable output folder selection section"""
        frame = ttk.LabelFrame(parent, text=title, padding=8)

        # Output folder container
        folder_container = ttk.Frame(frame)
        folder_container.pack(fill="x", padx=5, pady=5)

        # Label
        ttk.Label(
            folder_container,
            text="Save to:",
            font=("Cascadia Code", 10, "bold")
        ).pack(anchor="w", pady=(0, 4))

        # Path display and browse button row
        path_row = ttk.Frame(folder_container)
        path_row.pack(fill="x")

        # Output folder variable
        output_folder_var = tk.StringVar()
        
        # Set initial value
        if initial_folder:
            output_folder_var.set(initial_folder)
        else:
            try:
                from utils.helpers import get_output_directory
                default_folder = get_output_directory()
                output_folder_var.set(default_folder)
            except:
                output_folder_var.set("Default (Auto)")

        # Path entry (readonly)
        path_entry = ttk.Entry(
            path_row,
            textvariable=output_folder_var,
            state="readonly",
            font=("Cascadia Code", 10),
            width=50
        )
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        # Browse button
        def browse_folder():
            folder_path = filedialog.askdirectory(
                title="Select Output Folder",
                initialdir=output_folder_var.get() if output_folder_var.get() != "Default (Auto)" else None
            )
            if folder_path:
                output_folder_var.set(folder_path)

        browse_button = self.create_icon_button(
            path_row, "Browse", browse_folder,
            icon="📂", width=12
        )
        browse_button.pack(side="right")

        # Current folder info
        info_label = ttk.Label(
            folder_container,
            text="",
            font=("Cascadia Code", 9),
            foreground="#7f8c8d"
        )
        info_label.pack(anchor="w", pady=(4, 0))

        # Update info label when folder changes
        def update_info_label(*args):
            current_path = output_folder_var.get()
            if current_path and current_path != "Default (Auto)":
                info_label.config(text=f"Current: {os.path.basename(current_path)}")
            else:
                info_label.config(text="Using default output folder")

        output_folder_var.trace("w", update_info_label)
        update_info_label()  # Set initial value

        return frame, output_folder_var

# Import the model and UI components
try:
    # Try to import OpenCV, but don't fail if it's not available
    try:
        import cv2
    except ImportError:
        print("OpenCV (cv2) not available. Some features may be limited.")

    # Import config
    from config import GUI_WINDOW_SIZE, GUI_TITLE, GUI_MIN_WIDTH, GUI_MIN_HEIGHT, GUI_RESIZABLE, GUI_CENTER_ON_SCREEN, GUI_COLORS, GUI_FONTS, get_tab_visibility
    from models.video_generator_refactored import VideoGeneratorModel
    from ui.image_selector import ImageSelector
    from ui.text_redirector import TextRedirector
except ImportError as e:
    print(f"Error importing required modules: {e}")
    # Simplified config import with proper error handling
    try:
        from config import GUI_WINDOW_SIZE, GUI_TITLE, GUI_MIN_WIDTH, GUI_MIN_HEIGHT, GUI_RESIZABLE, GUI_CENTER_ON_SCREEN, GUI_COLORS, GUI_FONTS, get_tab_visibility
    except ImportError as config_error:
        print(f"CRITICAL: Could not import config values: {config_error}")
        print("Please ensure config.py is present and accessible.")
        # Exit gracefully rather than using hardcoded duplicates
        sys.exit(1)

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

    def download_images_for_preview(url, output_folder, max_images=5):
        """Fallback download_images_for_preview function"""
        print(f"Fallback: download_images_for_preview({url}, {output_folder}, {max_images})")
        return []

    def copy_selected_images(image_paths, output_folder):
        """Fallback copy_selected_images function"""
        print(f"Fallback: copy_selected_images({image_paths}, {output_folder})")

# Import UI components - if they fail, the application should exit gracefully
try:
    from ui.input_tab import InputTab
    from ui.image_tab import ImageTab
    from ui.video_tab import VideoTab
    from ui.merge_video_tab import MergeVideoTab
    from ui.option_tab import OptionTab
    from ui.batch_tab import BatchTab
except ImportError as ui_error:
    print(f"CRITICAL: Could not import UI components: {ui_error}")
    print("Please ensure all UI modules are present and accessible.")
    sys.exit(1)

class VideoGeneratorGUI:
    """Main GUI class for the Video Generator application"""
    def __init__(self, root):
        self.root = root
        self.root.configure(bg="#ffffff")  # Set root background

        # Use colors from config instead of hardcoded values
        self.colors = GUI_COLORS

        # Initialize UI component factory
        self.ui_factory = UIComponentFactory(self.colors)

        # Initialize all instance attributes that will be set in setup methods
        # Tab components
        self.input_tab_component = None
        self.image_tab_component = None
        self.video_tab_component = None
        self.merge_video_tab_component = None
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
        self.notebook.pack(fill="both", expand=True, padx=2, pady=2)  # Minimal padding for 800x800 window

        # Create tabs
        self.input_tab = ttk.Frame(self.notebook)
        self.image_tab = ttk.Frame(self.notebook)
        self.video_tab = ttk.Frame(self.notebook)
        self.merge_video_tab = ttk.Frame(self.notebook)
        self.option_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        self.batch_tab = ttk.Frame(self.notebook)

        # Get tab visibility configuration
        self.tabs_to_show = get_tab_visibility()
        
        # Conditionally add tabs to notebook based on configuration
        if self.tabs_to_show['input']:
            self.notebook.add(self.input_tab, text="Input")
        if self.tabs_to_show['images']:
            self.notebook.add(self.image_tab, text="Images")
        if self.tabs_to_show['video']:
            self.notebook.add(self.video_tab, text="Video")
        if self.tabs_to_show['merge']:
            self.notebook.add(self.merge_video_tab, text="Merge Video")
        if self.tabs_to_show['options']:
            self.notebook.add(self.option_tab, text="Options")
        if self.tabs_to_show['batch']:
            self.notebook.add(self.batch_tab, text="Batch")
        if self.tabs_to_show['log']:
            self.notebook.add(self.log_tab, text="Log")

        # Set up tabs (log tab first since other tabs may need to log messages)
        if self.tabs_to_show['log']:
            self.setup_log_tab()
        if self.tabs_to_show['input']:
            self.setup_input_tab()
        if self.tabs_to_show['images']:
            self.setup_image_tab()
        if self.tabs_to_show['video']:
            self.setup_video_tab()
        if self.tabs_to_show['merge']:
            self.setup_merge_tab()
        if self.tabs_to_show['options']:
            self.setup_option_tab()
        if self.tabs_to_show['batch']:
            self.setup_batch_tab()

    def _configure_styles(self):
        """Configure ttk styles for consistent appearance"""
        style = ttk.Style()
        style.theme_use("clam")  # Modern theme
        style.configure("TButton", font=GUI_FONTS["button"], padding=3)  # Use config font
        style.configure("TLabel", font=GUI_FONTS["label"], background=self.colors["background"], foreground=self.colors["text"])  # Use config font
        style.configure("TFrame", background=self.colors["background"])
        style.configure("TLabelframe", background=self.colors["background"], foreground=self.colors["text"])
        style.configure("TLabelframe.Label", font=GUI_FONTS["heading"], background=self.colors["background"])  # Use config font
        style.configure("TProgressbar", thickness=10, background=self.colors["success"])  # Thinner for 800x800

        # Configure checkbutton style to use checkmarks instead of X
        style.configure("TCheckbutton", background=self.colors["background"], foreground=self.colors["text"], font=GUI_FONTS["label"])  # Use config font
        style.map("TCheckbutton",
                 indicatorcolor=[("selected", self.colors["success"]), ("!selected", "white")],
                 indicatorrelief=[("pressed", "sunken"), ("!pressed", "raised")])
        
        # Configure notebook tabs to be very compact for 800x800
        style.configure("TNotebook.Tab", padding=[4, 1], font=GUI_FONTS["tab"])  # Tab padding and font

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
    def setup_merge_tab(self):
        """Set up the merge video tab using the MergeVideoTab component"""
        self.merge_video_tab_component = MergeVideoTab(self.merge_video_tab, self)

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
            font=GUI_FONTS["console"],  # Use config font
            bg="#f8f9fa",
            fg=self.colors["text"],
            borderwidth=1,
            relief="solid"
        )
        self.log_text.pack(fill="both", expand=True, padx=1, pady=1, side="left")  # Minimal padding for 800x800

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
        
        # FIXED: Add a post-completion cleanup option
        cleanup_response = messagebox.askyesno(
            "Cleanup Files", 
            "Video generated successfully!\n\nDo you want to clean up intermediate files (voice.mp3, subtitles.ass, etc.) to save space?\n\nClick 'No' to keep them for debugging."
        )
        
        if cleanup_response:
            try:
                output_dir = os.path.dirname(final_video)
                cleaned_count = self.model.cleanup_after_video_complete(
                    output_dir, 
                    keep_debug_files=False  # Full cleanup when user requests it
                )
                if cleaned_count > 0:
                    self.log(f"Cleaned up {cleaned_count} intermediate files to save space")
            except Exception as e:
                self.log(f"Cleanup failed: {e}")
        else:
            self.log("Keeping all intermediate files for debugging")
        
        # Ask if user wants to open the video
        open_response = messagebox.askyesno(
            "Success",
            f"Video generated successfully: {os.path.basename(final_video)}\n\nDo you want to open it now?"
        )
        if open_response:
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
        # Ensure progress value is within valid range (0-100)
        value = max(0, min(100, int(value)))
        
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
            from utils.common_imports import platform, subprocess
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", file_path], check=True)
            else:
                subprocess.run(["xdg-open", file_path], check=True)
            self.log(f"Opened file: {os.path.basename(file_path)}")
        except Exception as e:
            from utils.error_helpers import show_error_with_log
            show_error_with_log(self, "Error", f"Could not open file", e)

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
    root.title(GUI_TITLE)
    root.configure(bg="#ffffff")
    
    # Set icon using the correct path
    try:
        # Get the base path for the application
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(sys.executable)
        else:
            # Running as a script
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        icon_path = os.path.join(base_path, 'app_icon.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Could not set icon: {e}")
    
    # Use all window settings from config
    root.geometry(GUI_WINDOW_SIZE)
    root.minsize(GUI_MIN_WIDTH, GUI_MIN_HEIGHT)
    root.resizable(GUI_RESIZABLE, GUI_RESIZABLE)
    
    # Center the window if configured to do so
    if GUI_CENTER_ON_SCREEN:
        root.update_idletasks()  # Ensure geometry is calculated
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Parse window size from config
        width_str, height_str = GUI_WINDOW_SIZE.split('x')
        window_width = int(width_str)
        window_height = int(height_str)
        
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    # Make a window responsive
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    VideoGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
