"""
ImageSelector - Component for selecting images from a folder
"""
import os
import tkinter as tk
from PIL import Image, ImageTk
from config import SUPPORTED_IMAGE_EXTENSIONS

class ImageSelector:
    """Class to handle image selection functionality"""
    def __init__(self, parent_frame, update_callback):
        """
        Initialize the image selector
        
        Args:
            parent_frame: Parent frame to place the selector in
            update_callback: Function to call when selection changes
        """
        self.parent_frame = parent_frame
        self.update_callback = update_callback
        self.selected_images = []
        self.image_references = []  # To prevent garbage collection
        
        # Add initial message
        tk.Label(self.parent_frame, text="Select a folder to view and choose images").pack(pady=20)
        
    def clear(self):
        """Clear all selected images"""
        self.selected_images.clear()
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        tk.Label(self.parent_frame, text="Select a folder to view and choose images").pack(pady=20)
        self.update_callback()
        
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