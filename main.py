#!/usr/bin/env python3
"""
Video Generator - Main Entry Point
Creates videos with subtitles from text and images
"""
import moviepy_patch
import tkinter as tk
from tkinter import filedialog
import os
import sys
import threading
from ui.gui import VideoGeneratorGUI

def create_gui():
    """Create and run the GUI application"""
    # Create the main window
    root = tk.Tk()
    app = VideoGeneratorGUI(root)
    root.mainloop()

def run_console_mode():
    """Run the application in console mode"""
    from models.video_generator import VideoGeneratorModel
    
    print("\n=== VIDEO GENERATION SYSTEM (CONSOLE MODE) ===")
    print("This program will create a video with subtitles from text and images.")
    
    # Create model instance
    model = VideoGeneratorModel()
    
    # Get text input
    model.text_input = input("Enter the text for voice generation: ")
    
    # Get image source
    model.image_source = input("Choose image source (1 for website URL, 2 for local folder): ")
    
    if model.image_source == "1":
        model.website_url = input("Enter a website URL to get content: ")
    else:
        model.local_folder = input("Enter the path to a folder containing images: ")
        if not os.path.isdir(model.local_folder):
            print(f"Not a valid directory: {model.local_folder}")
            return
    
    # Generate the video
    subtitlePath, videoPath, output_dir = model.generate_video()
    
    # Finalize the video
    if subtitlePath and videoPath and output_dir:
        model.finalize_video(subtitlePath, videoPath, output_dir)

if __name__ == "__main__":
    try:
        # Check if we should use GUI mode
        if "--console" in sys.argv:
            run_console_mode()
        else:
            create_gui()
    except Exception as e:
        import traceback
        print(f"\nERROR: {e}")
        print("\nDetailed error information:")
        traceback.print_exc()
        print("\nPlease check that all required files exist and are in the correct locations.")
