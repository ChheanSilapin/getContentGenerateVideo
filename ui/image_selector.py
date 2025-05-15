"""
ImageSelector - Component for selecting images from a folder or URL
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import tempfile
import threading
import requests
from bs4 import BeautifulSoup
import urllib.parse
from config import SUPPORTED_IMAGE_EXTENSIONS

class ImageSelector:
    """Class to handle image selection functionality"""
    def __init__(self, parent_frame, colors=None, log_callback=None):
        """
        Initialize the image selector

        Args:
            parent_frame: Parent frame to place the selector in
            colors: Dictionary of colors for UI elements
            log_callback: Function to log messages
        """
        self.parent_frame = parent_frame
        self.colors = colors or {}
        self.log_callback = log_callback
        self.selected_images = []
        self.image_references = []  # To prevent garbage collection
        self.temp_dir = None
        self.download_thread = None
        self.stop_event = None
        self.update_callback = None
        
        # Clear any existing widgets in the parent frame
        for widget in self.parent_frame.winfo_children():
            widget.destroy()

        # Create header frame
        header_frame = tk.Frame(self.parent_frame, bg=self.colors.get("background", "#ecf0f1"))
        header_frame.pack(fill=tk.X, padx=15, pady=10)

        # Add title
        title_label = tk.Label(
            header_frame, 
            text="Image Selection", 
            font=("Helvetica", 14, "bold"),
            bg=self.colors.get("background", "#ecf0f1"),
            fg=self.colors.get("text", "#34495e")
        )
        title_label.pack(side=tk.LEFT, anchor=tk.W)

        # Add Choose Images button
        choose_btn = tk.Button(
            header_frame,
            text="Choose Images",
            bg=self.colors.get("secondary", "#3498db"),
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            command=self.select_images
        )
        choose_btn.pack(side=tk.LEFT, padx=10)

        # Add help text
        help_text = tk.Label(
            header_frame,
            text="Select images from your device or load from a website URL",
            bg=self.colors.get("background", "#ecf0f1"),
            fg=self.colors.get("light_text", "#7f8c8d")
        )
        help_text.pack(side=tk.LEFT, padx=5)

        # Add progress bar
        self.progress_frame = tk.Frame(self.parent_frame, bg=self.colors.get("background", "#ecf0f1"))
        self.progress_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            orient="horizontal",
            length=100,
            mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="0%",
            width=5,
            bg=self.colors.get("background", "#ecf0f1")
        )
        self.progress_label.pack(side=tk.RIGHT, padx=5)

        # Create image display area
        self.image_display_frame = tk.Frame(self.parent_frame)
        self.image_display_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Add initial message
        self.message_label = tk.Label(
            self.image_display_frame, 
            text="Click 'Choose Images' to select files or enter a URL in the Input tab",
            fg=self.colors.get("light_text", "#7f8c8d")
        )
        self.message_label.pack(pady=20)

        # Create button frame at the bottom
        button_frame = tk.Frame(self.parent_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=10)
        
        # Add action buttons
        select_all_btn = tk.Button(
            button_frame,
            text="Select All",
            bg="#2ecc71",  # Green
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            command=lambda: self.select_all_images(True)
        )
        select_all_btn.pack(side=tk.LEFT, padx=5)
        
        deselect_all_btn = tk.Button(
            button_frame,
            text="Deselect All",
            bg="#e74c3c",  # Red
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            command=lambda: self.select_all_images(False)
        )
        deselect_all_btn.pack(side=tk.LEFT, padx=5)
        
        use_selected_btn = tk.Button(
            button_frame,
            text="Use Selected",
            bg="#3498db",  # Blue
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            command=self.use_selected
        )
        use_selected_btn.pack(side=tk.LEFT, padx=5)
        
        clear_images_btn = tk.Button(
            button_frame,
            text="Clear Images",
            bg="#95a5a6",  # Gray
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            command=self.clear_images
        )
        clear_images_btn.pack(side=tk.LEFT, padx=5)

    def clear(self):
        """Clear all selected images"""
        self.selected_images.clear()
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        tk.Label(self.parent_frame, text="Select a folder to view and choose images").pack(pady=20)
        if self.update_callback:
            self.update_callback()

    def clear_images(self):
        """Clear all selected images"""
        self.clear()
        if self.log_callback:
            self.log_callback("Cleared all selected images")

    def get_selected_images(self):
        """Get the list of selected images"""
        return self.selected_images

    def select_images(self):
        """Open file dialog to select images"""
        file_paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp")]
        )
        if file_paths:
            self.selected_images = list(file_paths)
            if self.log_callback:
                self.log_callback(f"Selected {len(self.selected_images)} images")
            self.load_images_from_paths(self.selected_images)

    def select_all_images(self, select=True):
        """Select or deselect all images"""
        # Find all checkboxes in the parent frame
        checkboxes = []
        self._find_all_widgets_of_type(self.parent_frame, tk.Checkbutton, checkboxes)

        if not checkboxes:
            if self.log_callback:
                self.log_callback("No images available to select")
            return

        # Update all checkboxes
        for checkbox in checkboxes:
            if hasattr(checkbox, 'var'):
                checkbox.var.set(1 if select else 0)

        # Update the selected_images list
        if select:
            self.selected_images = []
            widgets_with_path = []
            self._find_widgets_with_attribute(self.parent_frame, 'img_path', widgets_with_path)
            for widget in widgets_with_path:
                self.selected_images.append(widget.img_path)
            if self.log_callback:
                self.log_callback(f"Selected all {len(self.selected_images)} images")
        else:
            self.selected_images = []
            if self.log_callback:
                self.log_callback("Deselected all images")

    def _find_all_widgets_of_type(self, parent, widget_type, result_list):
        """Recursively find all widgets of a specific type"""
        for child in parent.winfo_children():
            if isinstance(child, widget_type):
                result_list.append(child)
            self._find_all_widgets_of_type(child, widget_type, result_list)

    def _find_widgets_with_attribute(self, parent, attribute, result_list):
        """Recursively find all widgets with a specific attribute"""
        for child in parent.winfo_children():
            if hasattr(child, attribute):
                result_list.append(child)
            self._find_widgets_with_attribute(child, attribute, result_list)

    def download_images_from_url(self, url):
        """Download images from a URL for preview"""
        if not url:
            return

        if self.download_thread and self.download_thread.is_alive():
            if self.log_callback:
                self.log_callback("Image download already in progress")
            return

        if self.log_callback:
            self.log_callback(f"Downloading images from: {url}")

        self.temp_dir = tempfile.mkdtemp(prefix="preview_")
        self.stop_event = threading.Event()

        def download_thread():
            try:
                image_paths = []
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }

                # Parse the URL
                parsed_url = urllib.parse.urlparse(url)
                path = parsed_url.path.lower()

                # Check if it's a direct image URL
                if path.endswith(SUPPORTED_IMAGE_EXTENSIONS):
                    if self.log_callback:
                        self.log_callback("Direct image URL detected")
                    img_path = os.path.join(self.temp_dir, "0.jpg")
                    try:
                        img_response = requests.get(url, headers=headers, timeout=10)
                        img_response.raise_for_status()
                        with open(img_path, "wb") as f:
                            f.write(img_response.content)
                        image_paths.append(img_path)
                    except Exception as e:
                        if self.log_callback:
                            self.log_callback(f"Failed to download image: {e}")
                else:
                    # Regular website
                    if self.log_callback:
                        self.log_callback("Downloading webpage...")
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                    img_tags = soup.find_all("img")

                    if self.log_callback:
                        self.log_callback(f"Found {len(img_tags)} image tags")

                    img_urls = []
                    for img in img_tags:
                        img_url = img.get("src")
                        if img_url:
                            if not img_url.startswith(("http://", "https://")):
                                img_url = urllib.parse.urljoin(url, img_url)
                            img_urls.append(img_url)

                    # Limit to first 10 images for preview
                    img_urls = img_urls[:10]

                    if self.log_callback:
                        self.log_callback(f"Downloading {len(img_urls)} images...")

                    for i, img_url in enumerate(img_urls):
                        if self.stop_event and self.stop_event.is_set():
                            break

                        img_path = os.path.join(self.temp_dir, f"{i}.jpg")
                        try:
                            img_response = requests.get(img_url, headers=headers, timeout=10)
                            img_response.raise_for_status()
                            with open(img_path, "wb") as f:
                                f.write(img_response.content)
                            image_paths.append(img_path)
                        except Exception as e:
                            if self.log_callback:
                                self.log_callback(f"Failed to download image {i+1}: {e}")

                if self.stop_event and self.stop_event.is_set():
                    if self.log_callback:
                        self.log_callback("Image download stopped")
                    return

                if image_paths:
                    self.load_images_from_paths(image_paths)
                else:
                    if self.log_callback:
                        self.log_callback("No images found or downloaded")
            except Exception as e:
                import traceback
                traceback.print_exc()
                if self.log_callback:
                    self.log_callback(f"Error downloading images: {e}")

        self.download_thread = threading.Thread(target=download_thread)
        self.download_thread.daemon = True
        self.download_thread.start()

    def load_images_from_folder(self, folder_path):
        """
        Load and display images from a folder with selection checkboxes

        Args:
            folder_path: Path to folder containing images

        Returns:
            bool: True if images were loaded, False otherwise
        """
        if not folder_path or not os.path.isdir(folder_path):
            return False

        # Clear previous images
        for widget in self.parent_frame.winfo_children():
            widget.destroy()

        self.selected_images.clear()
        self.image_references.clear()

        # Find all image files in the folder
        image_files = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    image_files.append(file_path)

        if not image_files:
            tk.Label(self.parent_frame, text="No images found in the selected folder", fg="red").pack(pady=20)
            return False

        # Create a canvas with scrollbar for the images
        canvas = tk.Canvas(self.parent_frame)
        scrollbar = tk.Scrollbar(self.parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Display images with checkboxes
        for i, img_path in enumerate(image_files):
            try:
                # Create a frame for each image and its checkbox
                img_frame = tk.Frame(scrollable_frame)
                img_frame.pack(pady=5, fill="x")

                # Variable to track if this image is selected
                var = tk.IntVar()

                # Create checkbox
                chk = tk.Checkbutton(img_frame, variable=var, onvalue=1, offvalue=0)
                chk.pack(side="left")

                # Load and resize image for display
                img = Image.open(img_path)
                img.thumbnail((100, 100))  # Resize for thumbnail
                photo = ImageTk.PhotoImage(img)

                # Store the photo to prevent garbage collection
                self.image_references.append(photo)

                # Create image label
                img_label = tk.Label(img_frame, image=photo)
                img_label.image = photo  # Keep a reference
                img_label.pack(side="left", padx=5)

                # Display filename
                name_label = tk.Label(img_frame, text=os.path.basename(img_path))
                name_label.pack(side="left", padx=5)

                # Store the path and checkbox variable for later use
                chk.img_path = img_path
                chk.var = var

                # Function to update selected images when checkbox is clicked
                def update_selection(event=None, chk=chk, path=img_path):
                    if chk.var.get() == 1:
                        if path not in self.selected_images:
                            self.selected_images.append(path)
                    else:
                        if path in self.selected_images:
                            self.selected_images.remove(path)
                    self.update_callback()

                # Bind the checkbox to the update function
                chk.config(command=update_selection)

            except Exception as e:
                print(f"Error loading image {img_path}: {e}")

        return True

    def load_images_from_paths(self, image_paths):
        """
        Load and display images from a list of paths with selection checkboxes

        Args:
            image_paths: List of paths to image files

        Returns:
            bool: True if images were loaded, False otherwise
        """
        if not image_paths:
            return False

        # Clear previous images
        for widget in self.parent_frame.winfo_children():
            widget.destroy()

        self.selected_images.clear()
        self.image_references.clear()

        if not image_paths:
            tk.Label(self.parent_frame, text="No images found", fg="red").pack(pady=20)
            return False

        # Create a canvas with scrollbar for the images
        canvas = tk.Canvas(self.parent_frame)
        scrollbar = tk.Scrollbar(self.parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Display images with checkboxes
        for i, img_path in enumerate(image_paths):
            try:
                # Create a frame for each image and its checkbox
                img_frame = tk.Frame(scrollable_frame)
                img_frame.pack(pady=5, fill="x")

                # Variable to track if this image is selected
                var = tk.IntVar()

                # Create checkbox
                chk = tk.Checkbutton(img_frame, variable=var, onvalue=1, offvalue=0)
                chk.pack(side="left")

                # Load and resize image for display
                img = Image.open(img_path)
                img.thumbnail((100, 100))  # Resize for thumbnail
                photo = ImageTk.PhotoImage(img)

                # Store the photo to prevent garbage collection
                self.image_references.append(photo)

                # Create image label
                img_label = tk.Label(img_frame, image=photo)
                img_label.image = photo  # Keep a reference
                img_label.pack(side="left", padx=5)

                # Display filename
                name_label = tk.Label(img_frame, text=os.path.basename(img_path))
                name_label.pack(side="left", padx=5)

                # Store the path and checkbox variable for later use
                chk.img_path = img_path
                chk.var = var

                # Function to update selected images when checkbox is clicked
                def update_selection(event=None, chk=chk, path=img_path):
                    if chk.var.get() == 1:
                        if path not in self.selected_images:
                            self.selected_images.append(path)
                    else:
                        if path in self.selected_images:
                            self.selected_images.remove(path)
                    self.update_callback()

                # Bind the checkbox to the update function
                chk.config(command=update_selection)

            except Exception as e:
                print(f"Error loading image {img_path}: {e}")

        return True

    def use_selected(self):
        """Use the selected images and notify parent"""
        selected_images = self.get_selected_images()
        if selected_images:
            if self.log_callback:
                self.log_callback(f"Selected {len(selected_images)} images for use")
            if self.update_callback:
                self.update_callback()
        else:
            import tkinter.messagebox as messagebox
            messagebox.showwarning("No Images", "Please select at least one image")








