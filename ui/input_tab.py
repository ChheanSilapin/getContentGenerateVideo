#!/usr/bin/env python3
"""
Input Tab Component for Video Generator GUI
Handles text input, image source selection, and processing options
"""
import os
import tempfile
import threading
import tkinter as tk
import tkinter.simpledialog
import urllib.parse
from tkinter import messagebox, ttk

import requests
from bs4 import BeautifulSoup


class InputTab:
    """Input tab component for the Video Generator GUI"""

    def __init__(self, parent_frame, main_gui):
        """
        Initialize the input tab

        Args:
            parent_frame: The parent frame to contain this tab
            main_gui: Reference to the main GUI instance for callbacks and shared data
        """
        self.parent_frame = parent_frame
        self.main_gui = main_gui

        # Initialize UI components
        self.text_input = None
        self.website_url = None
        self.url_entry = None
        self.cpu_gpu = None
        self.progress_bar = None
        self.progress_label = None
        self.generate_button = None
        self.stop_button = None

        # Set up the tab
        self.setup_input_tab()

    def setup_input_tab(self):
        """Set up the input tab with all its components"""
        # Main frame for input tab
        main_frame = ttk.Frame(self.parent_frame, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Text input section
        text_frame = ttk.LabelFrame(main_frame, text="Text Input", padding=10)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create a frame to contain the text widget and its scrollbar
        text_container = ttk.Frame(text_frame)
        text_container.pack(fill="both", expand=True)

        # Text input with scrollbar
        self.text_input = tk.Text(
            text_container,
            wrap='word',
            height=8,
            font=("Helvetica", 11),
            borderwidth=1,
            relief="solid"
        )
        self.text_input.pack(side="left", fill="both", expand=True)

        text_scrollbar = ttk.Scrollbar(text_container, command=self.text_input.yview)
        text_scrollbar.pack(side="right", fill="y")
        self.text_input.config(yscrollcommand=text_scrollbar.set)

        # Image source section
        image_frame = ttk.LabelFrame(main_frame, text="Image Source", padding=10)
        image_frame.pack(fill='x', padx=5, pady=5)

        # Website URL input
        url_frame = ttk.Frame(image_frame)
        url_frame.pack(fill="x", padx=5, pady=5)

        url_label = ttk.Label(url_frame, text="Website URL:")
        url_label.pack(side="left", padx=5)

        self.website_url = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.website_url, width=40)
        self.url_entry.pack(side="left", padx=5, fill="x", expand=True)

        url_button = self.main_gui.ui_factory.create_styled_button(
            url_frame, "Browse", self.url_button_click, width=8
        )
        url_button.pack(side="left", padx=5)

        # Processing options
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding=10)
        options_frame.pack(fill="x", padx=5, pady=5)

        cpu_gpu_frame = ttk.Frame(options_frame)
        cpu_gpu_frame.pack(fill="x", padx=5, pady=5)

        cpu_gpu_label = ttk.Label(cpu_gpu_frame, text="Processing Unit:")
        cpu_gpu_label.pack(side="left", padx=5)

        self.cpu_gpu = tk.StringVar(value="CPU")
        cpu_radio = ttk.Radiobutton(cpu_gpu_frame, text="CPU", variable=self.cpu_gpu, value="CPU")
        cpu_radio.pack(side="left", padx=10)

        gpu_radio = ttk.Radiobutton(cpu_gpu_frame, text="GPU", variable=self.cpu_gpu, value="GPU")
        gpu_radio.pack(side="left", padx=10)

        # Progress section
        progress_frame, self.progress_bar, self.progress_label = self.main_gui.ui_factory.create_progress_section(
            main_frame, "Progress"
        )
        progress_frame.pack(fill="x", padx=5, pady=5)

        # Button frame
        button_frame = ttk.Frame(main_frame, padding=10)
        button_frame.pack(fill="x")

        # Action buttons
        self.generate_button = self.main_gui.ui_factory.create_styled_button(
            button_frame, "Generate Video", self.start_button_click,
            bg_color=self.main_gui.colors["success"], hover_color="#27ae60"
        )
        self.generate_button.pack(side="left", padx=5)

        self.stop_button = self.main_gui.ui_factory.create_styled_button(
            button_frame, "Stop", self.stop_button_click,
            bg_color=self.main_gui.colors["accent"], hover_color="#c0392b", state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)

        clear_button = self.main_gui.ui_factory.create_styled_button(
            button_frame, "Clear All", self.clear_input_button_click
        )
        clear_button.pack(side="left", padx=5)

    def url_button_click(self):
        """Handle URL button click to open input dialog"""
        url = tk.simpledialog.askstring("Enter URL", "Enter website URL:")
        if url:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
            self.main_gui.log(f"Set URL: {url}")

    def start_button_click(self):
        """Handle start button click to begin video generation"""
        if self.main_gui.generation_thread and self.main_gui.generation_thread.is_alive():
            messagebox.showwarning("Process Running", "Video generation is already in progress")
            return

        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Input Error", "Please enter text for voice generation")
            return

        url = self.url_entry.get().strip()
        if not url and not self.main_gui.selected_images:
            messagebox.showwarning("Input Error", "Please provide either a website URL or select images")
            return

        if url and not self.main_gui.selected_images:
            self._handle_url_image_download(url)
            return

        # Continue with video generation setup
        self._setup_video_generation(text, url)

    def _handle_url_image_download(self, url):
        """Handle downloading images from URL for preview"""
        self.main_gui.log("Downloading images for preview...")
        self.progress_bar["value"] = 10
        self.progress_label.config(text="10%")
        self.main_gui.update_image_progress(10, "Starting image download...")
        self.generate_button.config(state="active")
        self.stop_button.config(state="normal")
        self.main_gui.stop_event = threading.Event()
        self.main_gui.notebook.select(self.main_gui.image_tab)
        self.main_gui.temp_dir = tempfile.mkdtemp(prefix="preview_")

        def download_thread():
            try:
                image_paths = []
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                self.main_gui.root.after(0, lambda: self.main_gui.update_image_progress(20, "Downloading webpage..."))
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                img_tags = soup.find_all("img")
                self.main_gui.root.after(0, lambda: self.main_gui.update_image_progress(30, "Finding images..."))
                img_urls = []
                for img in img_tags:
                    img_url = img.get("src")
                    if img_url:
                        if not img_url.startswith(("http://", "https://")):
                            img_url = urllib.parse.urljoin(url, img_url)
                        img_urls.append(img_url)
                img_urls = img_urls[:10]
                self.main_gui.root.after(0, lambda: self.main_gui.update_image_progress(40, f"Found {len(img_urls)} images"))
                for i, img_url in enumerate(img_urls):
                    progress = 40 + int((i / len(img_urls)) * 50)
                    self.main_gui.root.after(0, lambda p=progress: self.main_gui.update_image_progress(p, f"Downloading image {i+1}/{len(img_urls)}..."))
                    img_path = os.path.join(self.main_gui.temp_dir, f"{i}.jpg")
                    try:
                        img_response = requests.get(img_url, headers=headers, timeout=10)
                        img_response.raise_for_status()
                        with open(img_path, "wb") as f:
                            f.write(img_response.content)
                        image_paths.append(img_path)
                    except Exception as e:
                        print(f"Failed to download image {i}: {e}")
                if self.main_gui.stop_event.is_set():
                    self.main_gui.root.after(0, lambda: self.main_gui.log("Image download stopped by user"))
                    self.main_gui.root.after(0, lambda: self.main_gui.reset_ui())
                    return
                self.main_gui.root.after(0, lambda: self.main_gui.update_image_progress(90, "Processing images..."))
                self.main_gui.root.after(0, lambda: self.main_gui.display_preview_images(image_paths))
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.main_gui.root.after(0, lambda: self.main_gui.log(f"Error downloading images: {e}"))
                self.main_gui.root.after(0, lambda: self.main_gui.reset_ui())

        self.main_gui.download_thread = threading.Thread(target=download_thread)
        self.main_gui.download_thread.daemon = True
        self.main_gui.download_thread.start()

    def _setup_video_generation(self, text, url):
        """Setup video generation with the provided text and URL"""
        self.main_gui.model.text_input = text
        self.main_gui.model.processing_option = self.cpu_gpu.get().lower()

        if self.main_gui.selected_images:
            # Check if images were downloaded from a URL
            if url:
                self.main_gui.model.image_source = "1"  # Website URL
                self.main_gui.model.selected_images = self.main_gui.selected_images
                self.main_gui.model.website_url = url
                self.main_gui.model.local_folder = ""
            else:
                self.main_gui.model.image_source = "3"  # Selected images
                self.main_gui.model.selected_images = self.main_gui.selected_images
                self.main_gui.model.website_url = ""
                self.main_gui.model.local_folder = ""
        elif url:
            # No images selected but URL provided - this shouldn't happen normally
            # as we redirect to image selection first
            self.main_gui.model.image_source = "1"
            self.main_gui.model.website_url = url
            self.main_gui.model.local_folder = ""
            self.main_gui.model.selected_images = []

        self.main_gui.log(f"Starting video generation with {self.cpu_gpu.get()}")
        self.main_gui.log(f"Text: {text[:50]}..." if len(text) > 50 else f"Text: {text}")
        if url and not self.main_gui.selected_images:
            self.main_gui.log(f"URL: {url}")
        if self.main_gui.selected_images:
            self.main_gui.log(f"Using {len(self.main_gui.selected_images)} selected images")

        self.progress_bar["value"] = 0
        self.progress_label.config(text="0%")
        self.generate_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.main_gui.stop_event = threading.Event()
        self.main_gui.generation_thread = threading.Thread(target=self.main_gui.generate_video_thread)
        self.main_gui.generation_thread.daemon = True
        self.main_gui.generation_thread.start()

    def stop_button_click(self):
        """Handle stop button click to stop video generation"""
        if self.main_gui.stop_event:
            self.main_gui.stop_event.set()
            self.main_gui.log("Stopping process...")
            self.main_gui.root.after(1000, self.main_gui.reset_ui)

    def clear_input_button_click(self):
        """Handle clear button click to clear all inputs"""
        self.text_input.delete("1.0", tk.END)
        self.url_entry.delete(0, tk.END)
        self.progress_bar["value"] = 0
        self.progress_label.config(text="0%")
        self.main_gui.update_image_progress(0, "Cleared image progress")
        self.main_gui.clean_button_click()
        self.main_gui.log("Cleared all inputs")

    def get_text_input(self):
        """Get the current text input"""
        return self.text_input.get("1.0", tk.END).strip()

    def get_url_input(self):
        """Get the current URL input"""
        return self.url_entry.get().strip()

    def get_processing_option(self):
        """Get the current processing option (CPU/GPU)"""
        return self.cpu_gpu.get()

    def reset_ui(self):
        """Reset the input tab UI to default state"""
        if self.generate_button:
            self.generate_button.config(state=tk.NORMAL)
        if self.stop_button:
            self.stop_button.config(state=tk.DISABLED)
        if self.progress_bar:
            self.progress_bar["value"] = 0
        if self.progress_label:
            self.progress_label.config(text="0%")
