#!/usr/bin/env python3
"""
Simple Video Generator UI
A professional-looking UI for generating videos from text and images
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import tempfile
import datetime
import requests
from bs4 import BeautifulSoup
import urllib.parse

# Import the model
try:
    from models.video_generator import VideoGeneratorModel
except ImportError:
    print("Error importing VideoGeneratorModel")

# Import services
try:
    from services.image_service import download_images, download_images_for_preview, copy_selected_images
except ImportError:
    print("Error importing image service functions")

class SimpleVideoGeneratorUI:
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

        # Configure ttk style
        style = ttk.Style()
        style.theme_use("clam")  # Modern theme
        style.configure("TButton", font=("Helvetica", 10), padding=8)
        style.configure("TLabel", font=("Helvetica", 10), background=self.colors["background"], foreground=self.colors["text"])
        style.configure("TFrame", background=self.colors["background"])
        style.configure("TLabelframe", background=self.colors["background"], foreground=self.colors["text"])
        style.configure("TLabelframe.Label", font=("Helvetica", 11, "bold"), background=self.colors["background"])
        style.configure("TProgressbar", thickness=20, background=self.colors["success"])

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
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Create tabs
        self.input_tab = ttk.Frame(self.notebook)
        self.image_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)

        # Add tabs to notebook
        self.notebook.add(self.input_tab, text=" Input ")
        self.notebook.add(self.image_tab, text=" Images ")
        self.notebook.add(self.log_tab, text=" Log ")

        # Set up tabs
        self.setup_input_tab()
        self.setup_image_tab()
        self.setup_log_tab()

    def setup_input_tab(self):
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
            bg=self.colors["accent"],
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
        self.stop_button.bind("<Leave>", lambda e: self.stop_button.config(bg=self.colors["accent"]))

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

    def setup_image_tab(self):
        main_frame = ttk.Frame(self.image_tab, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=(5, 10))

        label = ttk.Label(header_frame, text="Image Selection", font=("Helvetica", 14, "bold"))
        label.pack(side=tk.LEFT)

        # Button and help text
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        select_button = tk.Button(
            button_frame,
            text="Choose Images",
            bg=self.colors["secondary"],
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            command=self.select_images,
            activebackground=self.colors["primary"]
        )
        select_button.pack(side=tk.LEFT, padx=5)
        select_button.bind("<Enter>", lambda e: select_button.config(bg=self.colors["primary"]))
        select_button.bind("<Leave>", lambda e: select_button.config(bg=self.colors["secondary"]))

        help_label = ttk.Label(
            button_frame,
            text="Select images from your device or load from a website URL",
            font=("Helvetica", 9),
            foreground=self.colors["light_text"]
        )
        help_label.pack(side=tk.LEFT, padx=10)

        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)

        self.image_progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.image_progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=5)

        self.image_progress_label = ttk.Label(progress_frame, text="0%", font=("Helvetica", 10))
        self.image_progress_label.pack(side=tk.RIGHT, padx=5)

        # Canvas for images
        canvas_frame = ttk.Frame(main_frame, borderwidth=1, relief="solid")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.image_canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.image_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        self.image_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_canvas.configure(yscrollcommand=self.image_scrollbar.set)

        self.image_canvas.bind('<Configure>', lambda e: self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all")))

        # Instructions on canvas
        self.image_canvas.create_text(
            400, 150,
            text="Click 'Choose Images' to select files or enter a URL in the Input tab",
            font=("Helvetica", 11),
            fill=self.colors["light_text"],
            justify=tk.CENTER
        )

        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame, padding=10)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        select_all_btn = tk.Button(
            bottom_frame,
            text="Select All",
            bg=self.colors["success"],
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            width=12,
            command=lambda: self.select_all_images(True),
            activebackground="#27ae60"
        )
        select_all_btn.pack(side=tk.LEFT, padx=5)
        select_all_btn.bind("<Enter>", lambda e: select_all_btn.config(bg="#27ae60"))
        select_all_btn.bind("<Leave>", lambda e: select_all_btn.config(bg=self.colors["success"]))

        deselect_all_btn = tk.Button(
            bottom_frame,
            text="Deselect All",
            bg=self.colors["accent"],
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            width=12,
            command=lambda: self.select_all_images(False),
            activebackground="#c0392b"
        )
        deselect_all_btn.pack(side=tk.LEFT, padx=5)
        deselect_all_btn.bind("<Enter>", lambda e: deselect_all_btn.config(bg="#c0392b"))
        deselect_all_btn.bind("<Leave>", lambda e: deselect_all_btn.config(bg=self.colors["accent"]))

        continue_btn = tk.Button(
            bottom_frame,
            text="Use Selected",
            bg=self.colors["secondary"],
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            width=12,
            command=self.continue_with_selected_images,
            activebackground=self.colors["primary"]
        )
        continue_btn.pack(side=tk.LEFT, padx=5)
        continue_btn.bind("<Enter>", lambda e: continue_btn.config(bg=self.colors["primary"]))
        continue_btn.bind("<Leave>", lambda e: continue_btn.config(bg=self.colors["secondary"]))

        clear_all_btn = tk.Button(
            bottom_frame,
            text="Clear Images",
            bg=self.colors["light_text"],
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            width=12,
            command=self.clean_button_click,
            activebackground="#95a5a6"
        )
        clear_all_btn.pack(side=tk.LEFT, padx=5)
        clear_all_btn.bind("<Enter>", lambda e: clear_all_btn.config(bg="#95a5a6"))
        clear_all_btn.bind("<Leave>", lambda e: clear_all_btn.config(bg=self.colors["light_text"]))

    def setup_log_tab(self):
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

    def url_button_click(self):
        url = tk.simpledialog.askstring("Enter URL", "Enter website URL:")
        if url:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
            self.log(f"Set URL: {url}")

    def folder_button_click(self):
        folder_path = filedialog.askdirectory(title="Select Image Folder")
        if folder_path:
            self.folder_entry.config(state="normal")
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)
            self.folder_entry.config(state="readonly")
            self.log(f"Selected folder: {folder_path}")

    def start_button_click(self):
        if self.generation_thread and self.generation_thread.is_alive():
            messagebox.showwarning("Process Running", "Video generation is already in progress")
            return

        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Input Error", "Please enter text for voice generation")
            return

        url = self.url_entry.get().strip()
        if not url and not self.selected_images:
            messagebox.showwarning("Input Error", "Please provide either a website URL or select images")
            return

        if url and not self.selected_images:
            self.log("Downloading images for preview...")
            self.progress_bar["value"] = 10
            self.progress_label.config(text="10%")
            self.image_progress_bar["value"] = 10
            self.image_progress_label.config(text="10%")
            self.generate_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.stop_event = threading.Event()
            self.notebook.select(self.image_tab)
            self.temp_dir = tempfile.mkdtemp(prefix="preview_")

            def download_thread():
                try:
                    image_paths = []
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    self.root.after(0, lambda: self.update_image_progress(20, "Downloading webpage..."))
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                    img_tags = soup.find_all("img")
                    self.root.after(0, lambda: self.update_image_progress(30, "Finding images..."))
                    img_urls = []
                    for img in img_tags:
                        img_url = img.get("src")
                        if img_url:
                            if not img_url.startswith(("http://", "https://")):
                                img_url = urllib.parse.urljoin(url, img_url)
                            img_urls.append(img_url)
                    img_urls = img_urls[:10]
                    self.root.after(0, lambda: self.update_image_progress(40, f"Found {len(img_urls)} images"))
                    for i, img_url in enumerate(img_urls):
                        progress = 40 + int((i / len(img_urls)) * 50)
                        self.root.after(0, lambda p=progress: self.update_image_progress(p, f"Downloading image {i+1}/{len(img_urls)}..."))
                        img_path = os.path.join(self.temp_dir, f"{i}.jpg")
                        try:
                            img_response = requests.get(img_url, headers=headers, timeout=10)
                            img_response.raise_for_status()
                            with open(img_path, "wb") as f:
                                f.write(img_response.content)
                            image_paths.append(img_path)
                        except Exception as e:
                            print(f"Failed to download image {i}: {e}")
                    if self.stop_event.is_set():
                        self.root.after(0, lambda: self.log("Image download stopped by user"))
                        self.root.after(0, lambda: self.reset_ui())
                        return
                    self.root.after(0, lambda: self.update_image_progress(90, "Processing images..."))
                    self.root.after(0, lambda: self.display_preview_images(image_paths))
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self.root.after(0, lambda: self.log(f"Error downloading images: {e}"))
                    self.root.after(0, lambda: self.reset_ui())

            self.download_thread = threading.Thread(target=download_thread)
            self.download_thread.daemon = True
            self.download_thread.start()
            return

        self.model.text_input = text
        self.model.processing_option = self.cpu_gpu.get().lower()
        if self.selected_images:
            self.model.image_source = "3"
            self.model.selected_images = self.selected_images
            self.model.website_url = ""
            self.model.local_folder = ""
        elif url:
            self.model.image_source = "1"
            self.model.website_url = url
            self.model.local_folder = ""

        self.log(f"Starting video generation with {self.cpu_gpu.get()}")
        self.log(f"Text: {text[:50]}..." if len(text) > 50 else f"Text: {text}")
        if url and not self.selected_images:
            self.log(f"URL: {url}")
        if self.selected_images:
            self.log(f"Using {len(self.selected_images)} selected images")

        self.progress_bar["value"] = 0
        self.progress_label.config(text="0%")
        self.generate_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.stop_event = threading.Event()
        self.generation_thread = threading.Thread(target=self.generate_video_thread)
        self.generation_thread.daemon = True
        self.generation_thread.start()

    def generate_video_thread(self):
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
        if not image_paths:
            self.log("No images found or downloaded from the URL")
            messagebox.showwarning("No Images", "No images found or downloaded from the URL")
            self.reset_ui()
            return

        self.image_canvas.delete("all")
        self.photo_references = []
        self.image_vars = []  # Clear previous image variables

        image_frame = tk.Frame(self.image_canvas, bg="white")
        self.image_canvas.create_window(0, 0, window=image_frame, anchor="nw")

        title_label = tk.Label(
            image_frame,
            text=f"{len(image_paths)} Images Available",
            font=("Helvetica", 14, "bold"),
            bg="white",
            fg=self.colors["text"]
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=15)

        # Display images with checkboxes
        for i, img_path in enumerate(image_paths):
            try:
                row = (i // 3) + 1
                col = i % 3
                img_container = tk.Frame(
                    image_frame,
                    bg="white",
                    padx=10,
                    pady=10,
                    relief="solid",
                    borderwidth=1
                )
                img_container.grid(row=row, column=col, padx=10, pady=10)
                
                # Create IntVar and store it with the path
                var = tk.IntVar(value=1)  # Default to selected
                
                # Create checkbox with the variable
                checkbox = tk.Checkbutton(
                    img_container, 
                    variable=var, 
                    bg="white",
                    command=lambda v=var, p=img_path: self.update_image_selection(v, p)
                )
                checkbox.grid(row=0, column=0, sticky="nw")
                
                # Store the variable and path
                self.image_vars.append((var, img_path))
                
                # Print debug info
                print(f"Added checkbox for image {img_path} with var {var}")
                
                img = Image.open(img_path)
                img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(img)
                self.photo_references.append(photo)
                img_label = tk.Label(img_container, image=photo, bg="white")
                img_label.grid(row=1, column=0, pady=5)
                filename = os.path.basename(img_path)
                if len(filename) > 20:
                    filename = filename[:17] + "..."
                name_label = tk.Label(img_container, text=filename, bg="white", fg=self.colors["text"], font=("Helvetica", 9))
                name_label.grid(row=2, column=0)
                try:
                    with Image.open(img_path) as img_info:
                        dimensions = f"{img_info.width} x {img_info.height} px"
                        dim_label = tk.Label(img_container, text=dimensions, bg="white", fg=self.colors["light_text"], font=("Helvetica", 8))
                        dim_label.grid(row=3, column=0)
                except:
                    pass
            except Exception as e:
                self.log(f"Error displaying image {i+1}: {e}")

        image_frame.update_idletasks()
        self.image_canvas.config(scrollregion=self.image_canvas.bbox("all"))
        self.image_progress_bar["value"] = 100
        self.image_progress_label.config(text="100%")
        self.log(f"Loaded {len(image_paths)} images. Select images to use.")
        self.reset_ui()

    def select_all_images(self, select=True):
        """Select or deselect all images"""
        # Simpler approach - directly use image_vars if available
        if hasattr(self, 'image_vars') and self.image_vars:
            # Update all checkboxes using the stored variables
            for var, path in self.image_vars:
                var.set(1 if select else 0)
                
            # Update the selected_images list
            if select:
                self.selected_images = [path for _, path in self.image_vars]
                self.log(f"Selected all {len(self.selected_images)} images")
            else:
                self.selected_images = []
                self.log("Deselected all images")
            
            # Force update of the UI
            self.root.update_idletasks()
            return
            
        # Fallback approach - find all checkbuttons in the image tab
        checkboxes = []
        self._find_all_widgets_of_type(self.image_tab, tk.Checkbutton, checkboxes)
        
        if not checkboxes:
            messagebox.showinfo("No Images", "No images available to select")
            return
            
        # Update all checkboxes
        for checkbox in checkboxes:
            if hasattr(checkbox, 'var'):
                checkbox.var.set(1 if select else 0)
                
        # Update the selected_images list
        if select:
            self.selected_images = []
            widgets_with_path = []
            self._find_widgets_with_attribute(self.image_tab, 'img_path', widgets_with_path)
            for widget in widgets_with_path:
                self.selected_images.append(widget.img_path)
            self.log(f"Selected all {len(self.selected_images)} images")
        else:
            self.selected_images = []
            self.log("Deselected all images")
        
        # Force update of the UI
        self.root.update_idletasks()
    
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

    def continue_with_selected_images(self):
        if not hasattr(self, 'image_vars'):
            return
        selected = []
        for var, path in self.image_vars:
            if var.get() == 1:
                selected.append(path)
        if not selected:
            messagebox.showwarning("No Images", "Please select at least one image")
            return
        self.selected_images = selected
        self.log(f"Selected {len(selected)} images")
        self.notebook.select(0)
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Input Error", "Please enter text for voice generation")
            return
        self.model.text_input = text
        self.model.processing_option = self.cpu_gpu.get().lower()
        self.model.image_source = "3"
        self.model.selected_images = self.selected_images
        self.model.website_url = ""
        self.model.local_folder = ""
        self.log(f"Starting video generation with {self.cpu_gpu.get()}")
        self.log(f"Text: {text[:50]}..." if len(text) > 50 else f"Text: {text}")
        self.log(f"Using {len(self.selected_images)} selected images")
        self.progress_bar["value"] = 0
        self.progress_label.config(text="0%")
        self.generate_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.stop_event = threading.Event()
        self.generation_thread = threading.Thread(target=self.generate_video_thread)
        self.generation_thread.daemon = True
        self.generation_thread.start()

    def stop_button_click(self):
        if self.stop_event:
            self.stop_event.set()
            self.log("Stopping process...")
            self.root.after(1000, self.reset_ui)

    def reset_ui(self):
        self.generate_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar["value"] = 0
        self.progress_label.config(text="0%")

    def update_progress_ui(self, value, message=None):
        self.progress_bar["value"] = value
        self.progress_label.config(text=f"{value}%")
        if message:
            self.log(message)

    def show_success_message(self, video_path):
        result = messagebox.askquestion("Success",
                                       f"Video generated successfully!\n\nPath: {video_path}\n\nDo you want to open it?",
                                       icon="info")
        if result == "yes":
            self.open_file(video_path)

    def clear_input_button_click(self):
        self.text_input.delete("1.0", tk.END)
        self.url_entry.delete(0, tk.END)
        self.progress_bar["value"] = 0
        self.progress_label.config(text="0%")
        self.image_progress_bar["value"] = 0
        self.image_progress_label.config(text="0%")
        self.clean_button_click()
        self.log("Cleared all inputs")

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
        self.image_canvas.delete("all")
        self.selected_images = []
        self.log("Cleaned all selected images")

    def select_images(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp")]
        )
        if file_paths:
            self.selected_images = list(file_paths)
            self.log(f"Selected {len(self.selected_images)} images")
            self.display_selected_images()

    def display_selected_images(self):
        if not self.selected_images:
            return
        self.image_canvas.delete("all")
        self.photo_references = []
        image_frame = tk.Frame(self.image_canvas, bg="white")
        self.image_canvas.create_window(0, 0, window=image_frame, anchor="nw")
        title_label = tk.Label(
            image_frame,
            text=f"{len(self.selected_images)} Images Selected",
            font=("Helvetica", 14, "bold"),
            bg="white",
            fg=self.colors["text"]
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=15)
        for i, img_path in enumerate(self.selected_images):
            try:
                row = (i // 3) + 1
                col = i % 3
                img_container = tk.Frame(
                    image_frame,
                    bg="white",
                    padx=10,
                    pady=10,
                    relief="solid",
                    borderwidth=1,
                    highlightbackground="#dfe6e9",
                    highlightthickness=1
                )
                img_container.grid(row=row, column=col, padx=10, pady=10)
                var = tk.IntVar(value=1)
                checkbox = tk.Checkbutton(img_container, variable=var, bg="white")
                checkbox.grid(row=0, column=0, sticky="nw")
                
                # Store the path with the checkbox for later reference
                checkbox.img_path = img_path
                checkbox.var = var
                
                # Add command to update selection
                checkbox.config(command=lambda v=var, p=img_path: self.update_image_selection(v, p))
                
                img = Image.open(img_path)
                img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(img)
                self.photo_references.append(photo)
                img_label = tk.Label(img_container, image=photo, bg="white")
                img_label.grid(row=1, column=0, pady=5)
                filename = os.path.basename(img_path)
                if len(filename) > 20:
                    filename = filename[:17] + "..."
                name_label = tk.Label(img_container, text=filename, bg="white", fg=self.colors["text"], font=("Helvetica", 9))
                name_label.grid(row=2, column=0)
            except Exception as e:
                self.log(f"Error displaying image {i+1}: {e}")
        image_frame.update_idletasks()
        self.image_canvas.config(scrollregion=self.image_canvas.bbox("all"))

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        print(formatted_message)

    def update_image_progress(self, value, message=None):
        self.image_progress_bar["value"] = value
        self.image_progress_label.config(text=f"{value}%")
        if message:
            self.log(message)

    def update_image_selection(self, var, path):
        """Update selected images when a checkbox is clicked"""
        if var.get() == 1:
            if path not in self.selected_images:
                self.selected_images.append(path)
        else:
            if path in self.selected_images:
                self.selected_images.remove(path)
        
        print(f"Selected images: {len(self.selected_images)}")

def main():
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
    app = SimpleVideoGeneratorUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()




