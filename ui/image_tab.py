#!/usr/bin/env python3
"""
Image Tab Component for Video Generator GUI
Handles image selection, display, and management functionality
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk


class ImageTab:
    """Image tab component for the Video Generator GUI"""

    def __init__(self, parent_frame, main_gui):
        """
        Initialize the image tab

        Args:
            parent_frame: The parent frame to contain this tab
            main_gui: Reference to the main GUI instance for callbacks and shared data
        """
        self.parent_frame = parent_frame
        self.main_gui = main_gui

        # Initialize UI components
        self.image_progress_bar = None
        self.image_progress_label = None
        self.image_canvas = None
        self.image_scrollbar = None

        # Image management
        self.photo_references = []
        self.image_vars = []

        # Set up the tab
        self.setup_image_tab()

    def setup_image_tab(self):
        """Set up the image tab with all its components"""
        main_frame = ttk.Frame(self.parent_frame, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", padx=5, pady=(5, 10))

        label = ttk.Label(header_frame, text="Image Selection", font=("Helvetica", 14, "bold"))
        label.pack(side="left")

        # Button and help text
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        select_button = self.main_gui.ui_factory.create_styled_button(
            button_frame, "Choose Images", self.select_images, width=12
        )
        select_button.pack(side="left", padx=5)

        help_label = ttk.Label(
            button_frame,
            text="Select images from your device or load from a website URL",
            font=("Helvetica", 9),
            foreground=self.main_gui.colors["light_text"]
        )
        help_label.pack(side="left", padx=10)

        # Progress section
        progress_frame, self.image_progress_bar, self.image_progress_label = self.main_gui.ui_factory.create_progress_section(
            main_frame, "Image Loading Progress"
        )
        progress_frame.pack(fill="x", padx=5, pady=5)

        # Image display area with scrollbar
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.image_canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        self.image_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.image_canvas.yview)
        self.image_canvas.configure(yscrollcommand=self.image_scrollbar.set)

        self.image_canvas.pack(side="left", fill="both", expand=True)
        self.image_scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel to canvas
        self.image_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Action buttons section (positioned below the image display)
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill="x", padx=5, pady=10)

        # Left side buttons (selection controls)
        select_all_button = self.main_gui.ui_factory.create_styled_button(
            action_frame, "Select All", lambda: self.select_all_images(True),
            bg_color=self.main_gui.colors["secondary"], hover_color="#2980b9", width=10
        )
        select_all_button.pack(side="left", padx=5)

        deselect_all_button = self.main_gui.ui_factory.create_styled_button(
            action_frame, "Deselect All", lambda: self.select_all_images(False),
            bg_color=self.main_gui.colors["secondary"], hover_color="#2980b9", width=10
        )
        deselect_all_button.pack(side="left", padx=5)

        # Clear images button
        clear_button = self.main_gui.ui_factory.create_styled_button(
            action_frame, "Clear Images", self.clear_images,
            bg_color=self.main_gui.colors["accent"], hover_color="#c0392b", width=12
        )
        clear_button.pack(side="left", padx=5)

        # Right side button (primary action)
        continue_button = self.main_gui.ui_factory.create_styled_button(
            action_frame, "Continue with Selected", self.main_gui.continue_with_selected_images,
            bg_color=self.main_gui.colors["success"], hover_color="#27ae60", width=18
        )
        continue_button.pack(side="right", padx=5)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling in the image canvas"""
        self.image_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def select_images(self):
        """Open a file dialog to select images"""
        file_paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp")]
        )
        if file_paths:
            self.main_gui.selected_images = list(file_paths)
            self.main_gui.log(f"Selected {len(self.main_gui.selected_images)} images")
            self.display_selected_images()

    def display_selected_images(self):
        """Display the selected images in the canvas"""
        if not self.main_gui.selected_images:
            return

        title_text = f"{len(self.main_gui.selected_images)} Images Selected"
        self._create_image_display(self.main_gui.selected_images, title_text)
        self.main_gui.log(f"Displayed {len(self.main_gui.selected_images)} selected images")

    def display_preview_images(self, image_paths):
        """Display preview images with checkboxes"""
        if not image_paths:
            self.main_gui.log("No images found or downloaded from the URL")
            messagebox.showwarning("No Images", "No images found or downloaded from the URL")
            self.main_gui.reset_ui()
            return

        title_text = f"{len(image_paths)} Images Available"
        self._create_image_display(image_paths, title_text)

        self.image_progress_bar["value"] = 100
        self.image_progress_label.config(text="100%")
        self.main_gui.log(f"Loaded {len(image_paths)} images. Select images to use.")
        self.main_gui.reset_ui()

    def _create_image_display(self, image_paths, title_text):
        """Create the common image display layout with checkboxes"""
        self.image_canvas.delete("all")
        self.photo_references = []
        self.image_vars = []  # Clear previous image variables

        image_frame = tk.Frame(self.image_canvas, bg="white")
        self.image_canvas.create_window(0, 0, window=image_frame, anchor="nw")

        title_label = tk.Label(
            image_frame,
            text=title_text,
            font=("Helvetica", 14, "bold"),
            bg="white",
            fg=self.main_gui.colors["text"]
        )
        title_label.grid(row=0, column=0, columnspan=5, pady=15)

        # Display images with checkboxes in a grid
        for i, img_path in enumerate(image_paths):
            try:
                row = (i // 5) + 1  # 5 images per row
                col = i % 5

                # Create a container for each image
                img_container = tk.Frame(
                    image_frame,
                    bg="white",
                    relief="solid",
                    borderwidth=1,
                    width=150,
                    height=180
                )
                img_container.grid(row=row, column=col, padx=5, pady=5)
                img_container.grid_propagate(False)  # Force the frame to keep its size

                # Create IntVar and store it with the path
                var = tk.IntVar(value=1)  # Default selected

                # Create checkbox with the variable
                checkbox = tk.Checkbutton(
                    img_container,
                    variable=var,
                    bg="white",
                    command=lambda v=var, p=img_path: self.update_image_selection(v, p)
                )
                checkbox.grid(row=0, column=0, sticky="nw", padx=2, pady=2)

                # Store the variable and path
                self.image_vars.append((var, img_path))

                # Load and display the image
                img = Image.open(img_path)
                img.thumbnail((120, 120))  # Smaller thumbnails to fit more in a row
                photo = ImageTk.PhotoImage(img)
                self.photo_references.append(photo)

                # Create a frame to center the image
                img_frame = tk.Frame(img_container, bg="white")
                img_frame.grid(row=1, column=0, sticky="nsew")
                img_container.grid_rowconfigure(1, weight=1)
                img_container.grid_columnconfigure(0, weight=1)

                img_label = tk.Label(img_frame, image=photo, bg="white")
                img_label.pack(expand=True, fill="both", padx=5, pady=2)

                # Display filename below the image
                filename = os.path.basename(img_path)
                if len(filename) > 15:
                    filename = filename[:12] + "..."
                name_label = tk.Label(
                    img_container,
                    text=filename,
                    bg="white",
                    fg=self.main_gui.colors["text"],
                    font=("Helvetica", 9)
                )
                name_label.grid(row=2, column=0, padx=5, pady=(0, 5))

            except Exception as e:
                self.main_gui.log(f"Error displaying image {i+1}: {e}")

        image_frame.update_idletasks()
        self.image_canvas.config(scrollregion=self.image_canvas.bbox("all"))

    def update_image_selection(self, var, path):
        """Update the selected images list when a checkbox is clicked"""
        if var.get() == 1:
            if path not in self.main_gui.selected_images:
                self.main_gui.selected_images.append(path)
        else:
            if path in self.main_gui.selected_images:
                self.main_gui.selected_images.remove(path)

    def select_all_images(self, select=True):
        """Select or deselect all images"""
        # Use image_vars if available
        if hasattr(self, 'image_vars') and self.image_vars:
            # Update all checkboxes using the stored variables
            for var, path in self.image_vars:
                var.set(1 if select else 0)

            # Update the selected_images list
            if select:
                self.main_gui.selected_images = [path for _, path in self.image_vars]
                self.main_gui.log(f"Selected all {len(self.main_gui.selected_images)} images")
            else:
                self.main_gui.selected_images = []
                self.main_gui.log("Deselected all images")

            # Force update of the UI
            self.main_gui.root.update_idletasks()
            return

        # Fallback approach - find all check buttons in the image tab
        checkboxes = []
        self._find_all_widgets_of_type(self.parent_frame, tk.Checkbutton, checkboxes)

        if not checkboxes:
            messagebox.showinfo("No Images", "No images available to select")
            return

        # Update all checkboxes
        for checkbox in checkboxes:
            if hasattr(checkbox, 'var'):
                checkbox.var.set(1 if select else 0)

        # Update the selected_images list
        if select:
            self.main_gui.selected_images = []
            widgets_with_path = []
            self._find_widgets_with_attribute(self.parent_frame, 'img_path', widgets_with_path)
            for widget in widgets_with_path:
                self.main_gui.selected_images.append(widget.img_path)
            self.main_gui.log(f"Selected all {len(self.main_gui.selected_images)} images")
        else:
            self.main_gui.selected_images = []
            self.main_gui.log("Deselected all images")

    def _find_all_widgets_of_type(self, parent, widget_type, result_list):
        """Recursively find all widgets of a specific type"""
        for child in parent.winfo_children():
            if isinstance(child, widget_type):
                result_list.append(child)
            self._find_all_widgets_of_type(child, widget_type, result_list)

    def _find_widgets_with_attribute(self, parent, attribute_name, result_list):
        """Recursively find all widgets with a specific attribute"""
        for child in parent.winfo_children():
            if hasattr(child, attribute_name):
                result_list.append(child)
            self._find_widgets_with_attribute(child, attribute_name, result_list)

    def update_image_progress(self, value, message):
        """Update the image progress bar and label"""
        if self.image_progress_bar:
            self.image_progress_bar["value"] = value
        if self.image_progress_label:
            self.image_progress_label.config(text=f"{value}%")
        if message:
            self.main_gui.log(message)

    def clear_images(self):
        """Clear all displayed images"""
        if self.image_canvas:
            self.image_canvas.delete("all")
        self.photo_references = []
        self.image_vars = []
        self.main_gui.selected_images = []
        if self.image_progress_bar:
            self.image_progress_bar["value"] = 0
        if self.image_progress_label:
            self.image_progress_label.config(text="0%")
        self.main_gui.log("Cleared all images")