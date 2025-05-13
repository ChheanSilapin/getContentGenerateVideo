import os
import sys
import time
import urllib.parse
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
try:
    from voice_ai import generateAudio
    print("Successfully imported voice_ai module")
except ImportError as e:
    print(f"Error importing voice_ai module: {e}")
    print(f"Checking if file exists: {'voice_ai.py' in os.listdir('.')}")
except Exception as e:
    print(f"Unexpected error importing voice_ai: {e}")
try:
    print("Attempting to import create_video module...")
    try:
        from create_video import createSideShowWithFFmpeg, downloadImage
        print("Successfully imported create_video module")
    except FileNotFoundError as e:
        print(f"File Not Found Error in create_video module: {e}")
        print(f"File path: {e.filename}")
    except Exception as e:
        print(f"Error in create_video module: {e}")
        import traceback
        traceback.print_exc()
except Exception as outer_e:
    print(f"Outer exception: {outer_e}")
    
try:
    print("Attempting to import generate_ass module...")
    from generate_ass import process_local_video
    print("Successfully imported generate_ass module")
except ImportError as e:
    print(f"Error importing generate_ass module: {e}")
    print(f"Checking if file exists: {'generate_ass.py' in os.listdir('.')}")
except Exception as e:
    print(f"Unexpected error importing generate_ass: {e}")
try:
    print("Attempting to import Final_Video module...")
    from Final_Video import merge_video_subtitle
    print("Successfully imported Final_Video module")
except ImportError as e:
    print(f"Error importing Final_Video module: {e}")
    print(f"Checking if file exists: {'Final_Video.py' in os.listdir('.')}")
except Exception as e:
    print(f"Unexpected error importing Final_Video: {e}")
try:
    print("Attempting to import utils module...")
    from utils import getTitleContent
    print("Successfully imported utils module")
except ImportError as e:
    print(f"Error importing utils module: {e}")
    print(f"Checking if file exists: {'utils.py' in os.listdir('.')}")
except Exception as e:
    print(f"Unexpected error importing utils: {e}")

def create_gui():
    """Create a GUI for the video generation process"""
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk
    from PIL import Image, ImageTk
    import threading
    import queue
    import os
    
    # Create the main window
    root = tk.Tk()
    root.title("Video Generator")
    root.geometry("800x800")
    
    # Variables to store user inputs
    text_var = tk.StringVar()
    source_var = tk.IntVar(value=1)  # Default to website URL
    url_var = tk.StringVar()
    folder_var = tk.StringVar()
    
    # List to store selected image paths
    selected_images = []
    generation_thread = None
    stop_event = threading.Event()
    
    # Function to redirect print statements to the text widget
    import sys
    class TextRedirector:
        def __init__(self, text_widget):
            self.text_widget = text_widget
            self.buffer = ""
            
        def write(self, string):
            self.buffer += string
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", string)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
            
        def flush(self):
            pass
    
    # Create a notebook (tabbed interface)
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create tabs
    input_tab = ttk.Frame(notebook)
    images_tab = ttk.Frame(notebook)
    log_tab = ttk.Frame(notebook)
    
    notebook.add(input_tab, text="Input")
    notebook.add(images_tab, text="Images")
    notebook.add(log_tab, text="Log")
    
    # === INPUT TAB ===
    # Text input section
    tk.Label(input_tab, text="Enter text for voice generation:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
    text_entry = tk.Text(input_tab, height=5, width=50)
    text_entry.pack(fill="x", padx=10, pady=5)
    
    # Image source selection
    tk.Label(input_tab, text="Choose image source:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
    
    # Website URL option
    url_frame = tk.Frame(input_tab)
    url_frame.pack(fill="x", padx=10, pady=5)
    tk.Radiobutton(url_frame, text="Website URL", variable=source_var, value=1).pack(side="left")
    url_entry = tk.Entry(url_frame, textvariable=url_var, width=50)
    url_entry.pack(side="left", fill="x", expand=True, padx=5)
    
    # Local folder option
    folder_frame = tk.Frame(input_tab)
    folder_frame.pack(fill="x", padx=10, pady=5)
    tk.Radiobutton(folder_frame, text="Local folder", variable=source_var, value=2).pack(side="left")
    folder_entry = tk.Entry(folder_frame, textvariable=folder_var, width=40)
    folder_entry.pack(side="left", fill="x", expand=True, padx=5)
    
    # Function to load and display images from a folder
    def load_images_from_folder():
        folder_path = folder_var.get()
        if not folder_path or not os.path.isdir(folder_path):
            folder_path = filedialog.askdirectory(title="Select folder containing images")
            if not folder_path:
                return
            folder_var.set(folder_path)
            source_var.set(2)  # Auto-select local folder option
        
        # Clear previous images
        for widget in images_frame.winfo_children():
            widget.destroy()
        
        selected_images.clear()
        
        # Find all image files in the folder
        image_files = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    image_files.append(file_path)
        
        if not image_files:
            tk.Label(images_frame, text="No images found in the selected folder", fg="red").pack(pady=20)
            return
        
        # Create a canvas with scrollbar for the images
        canvas = tk.Canvas(images_frame)
        scrollbar = tk.Scrollbar(images_frame, orient="vertical", command=canvas.yview)
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
                chk.photo = photo
                
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
                        if path not in selected_images:
                            selected_images.append(path)
                    else:
                        if path in selected_images:
                            selected_images.remove(path)
                    update_status()
                
                # Bind the checkbox to the update function
                chk.config(command=update_selection)
                
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")
        
        # Switch to the Images tab
        notebook.select(images_tab)
        update_status()
    
    # Browse button for folder selection
    browse_button = tk.Button(folder_frame, text="Browse & Select Images", command=load_images_from_folder)
    browse_button.pack(side="right", padx=5)
    
    # === IMAGES TAB ===
    images_frame = tk.Frame(images_tab)
    images_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Initial message
    tk.Label(images_frame, text="Select a folder to view and choose images").pack(pady=20)
    
    # === LOG TAB ===
    log_frame = tk.Frame(log_tab)
    log_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create a scrolled text widget for the log
    log_text = scrolledtext.ScrolledText(log_frame, height=20)
    log_text.pack(fill="both", expand=True)
    log_text.configure(state="disabled")
    
    # Status bar
    status_frame = tk.Frame(root)
    status_frame.pack(fill="x", side="bottom", padx=10, pady=5)
    
    status_label = tk.Label(status_frame, text="Ready", bd=1, relief=tk.SUNKEN, anchor="w")
    status_label.pack(fill="x", side="left", expand=True)
    
    selected_count_label = tk.Label(status_frame, text="Selected: 0 images", bd=1, relief=tk.SUNKEN, anchor="e")
    selected_count_label.pack(side="right", padx=(5, 0))
    
    # Function to update status bar
    def update_status():
        selected_count_label.config(text=f"Selected: {len(selected_images)} images")
    
    # Control buttons frame
    control_frame = tk.Frame(root)
    control_frame.pack(fill="x", side="bottom", padx=10, pady=5)
    
    # Function to start the generation process
    def start_generation():
        # Get the text input
        text_input = text_entry.get("1.0", "end-1c").strip()
        if not text_input:
            messagebox.showerror("Error", "Please enter text for voice generation")
            return
        
        # Get the image source
        source = source_var.get()
        if source == 1:
            # Website URL
            url = url_var.get().strip()
            if not url:
                messagebox.showerror("Error", "Please enter a website URL")
                return
        else:
            # Local folder with selected images
            if not selected_images:
                messagebox.showerror("Error", "Please select at least one image")
                return
        
        # Disable the start button and enable the stop button
        start_button.config(state="disabled")
        stop_button.config(state="normal")
        clear_button.config(state="disabled")
        
        # Reset the stop event
        stop_event.clear()
        
        # Redirect stdout to the log text widget
        old_stdout = sys.stdout
        sys.stdout = TextRedirector(log_text)
        
        # Clear the log
        log_text.configure(state="normal")
        log_text.delete(1.0, tk.END)
        log_text.configure(state="disabled")
        
        # Switch to the log tab
        notebook.select(log_tab)
        
        # Run the generation process in a separate thread
        def run_process():
            nonlocal generation_thread
            try:
                # Set the global variables based on GUI inputs
                global gui_text_input, gui_image_source, gui_website_url, gui_local_folder, gui_selected_images
                gui_text_input = text_input
                gui_image_source = "1" if source == 1 else "2"
                gui_website_url = url_var.get().strip()
                gui_local_folder = folder_var.get().strip()
                gui_selected_images = selected_images.copy()
                
                # Run the main function
                main(stop_event)
                
                if not stop_event.is_set():
                    # Process completed successfully
                    root.after(0, lambda: messagebox.showinfo("Complete", "Video generation complete!"))
                
            except Exception as e:
                import traceback
                print(f"\nERROR: {e}")
                print("\nDetailed error information:")
                traceback.print_exc()
                if not stop_event.is_set():
                    root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
            finally:
                # Restore stdout
                sys.stdout = old_stdout
                # Re-enable buttons
                root.after(0, lambda: start_button.config(state="normal"))
                root.after(0, lambda: stop_button.config(state="disabled"))
                root.after(0, lambda: clear_button.config(state="normal"))
                generation_thread = None
        
        generation_thread = threading.Thread(target=run_process)
        generation_thread.daemon = True
        generation_thread.start()
    
    # Function to stop the generation process
    def stop_generation():
        if generation_thread and generation_thread.is_alive():
            stop_event.set()
            status_label.config(text="Stopping...")
            messagebox.showinfo("Stopping", "Stopping the generation process. Please wait...")
    
    # Function to clear all inputs
    def clear_inputs():
        # Clear text input
        text_entry.delete(1.0, tk.END)
        
        # Reset image source
        source_var.set(1)
        url_var.set("")
        folder_var.set("")
        
        # Clear selected images
        selected_images.clear()
        update_status()
        
        # Clear the images tab
        for widget in images_frame.winfo_children():
            widget.destroy()
        tk.Label(images_frame, text="Select a folder to view and choose images").pack(pady=20)
        
        # Clear the log
        log_text.configure(state="normal")
        log_text.delete(1.0, tk.END)
        log_text.configure(state="disabled")
        
        status_label.config(text="Ready")
    
    # Create control buttons
    start_button = tk.Button(control_frame, text="Start Generation", command=start_generation, 
                           font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=10, pady=5)
    start_button.pack(side="left", padx=5)
    
    stop_button = tk.Button(control_frame, text="Stop", command=stop_generation, 
                          font=("Arial", 12), bg="#f44336", fg="white", padx=10, pady=5, state="disabled")
    stop_button.pack(side="left", padx=5)
    
    clear_button = tk.Button(control_frame, text="Clear All", command=clear_inputs, 
                           font=("Arial", 12), padx=10, pady=5)
    clear_button.pack(side="right", padx=5)
    
    # Run the GUI
    root.mainloop()

# Global variables for GUI inputs
gui_text_input = None
gui_image_source = None
gui_website_url = None
gui_local_folder = None
gui_selected_images = None

def run_generation(stop_event=None):
    print("\n=== STARTING NEW VIDEO GENERATION ===")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Generation timestamp: {timestamp}")
    
    # Check if we should stop
    if stop_event and stop_event.is_set():
        print("Process stopped by user.")
        return None, None, None
    
    output_dir = f"output_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    audio_file = os.path.join(output_dir, "voice.mp3")
    video_file = os.path.join(output_dir, "slideshow.mp4")
    subtitle_file = os.path.join(output_dir, "subtitles.ass")
    final_output = os.path.join(output_dir, "final_output.mp4")
    
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    print(f"Created images directory: {images_dir}")
    
    # Check if we should stop
    if stop_event and stop_event.is_set():
        print("Process stopped by user.")
        return None, None, None
    
    print("\n--- Step 1: Generating Audio ---")
    # Use GUI input if available, otherwise prompt
    text_input = gui_text_input if gui_text_input is not None else input("Enter the text for voice generation: ")
    print(f"Text input: {text_input[:50]}..." if len(text_input) > 50 else f"Text input: {text_input}")
    
    if not generateAudio(text_input, output_file=audio_file):
        print("Failed to generate audio.")
        return None, None, None
    
    # Check if we should stop
    if stop_event and stop_event.is_set():
        print("Process stopped by user.")
        return None, None, None
    
    print("\n--- Step 2: Getting Images ---")
    # Use GUI input if available, otherwise prompt
    image_source = gui_image_source if gui_image_source is not None else input("Choose image source (1 for website URL, 2 for local folder): ")
    print(f"Image source: {'Website URL' if image_source == '1' else 'Local folder'}")
    
    if image_source == "1":
        # Website URL option
        websiteUrl = gui_website_url if gui_website_url is not None else input("Enter a website URL to get content: ")
        print(f"Website URL: {websiteUrl}")
        
        title, content = getTitleContent(websiteUrl)
        print(f"Retrieved title: {title[:50]}...")
        print(f"Content length: {len(content)} characters")
        
        # Check if the URL is a direct image file
        parsed_url = urllib.parse.urlparse(websiteUrl)
        path = parsed_url.path.lower()
        if path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
            # For direct image URLs, don't create placeholder images
            folderName = downloadImage(title, content, websiteUrl, folder_name=images_dir, placeholder_count=0)
        else:
            # For regular websites, use default behavior
            folderName = downloadImage(title, content, websiteUrl, folder_name=images_dir)
        print(f"Images downloaded to: {folderName}")
    else:
        # Local folder with selected images option
        image_count = 0  # Initialize image_count variable
        
        if gui_selected_images and len(gui_selected_images) > 0:
            # Use selected images from GUI
            print(f"Using {len(gui_selected_images)} selected images")
            
            # Copy selected images to our images directory
            import shutil
            image_count = len(gui_selected_images)  # Set image_count to the number of selected images
            for i, src_path in enumerate(gui_selected_images):
                if os.path.isfile(src_path):
                    # Rename to ensure sequential numbering
                    dst_path = os.path.join(images_dir, f"{i}.jpg")
                    try:
                        shutil.copy2(src_path, dst_path)
                        print(f"Copied {os.path.basename(src_path)} to {dst_path}")
                    except Exception as e:
                        print(f"Error copying {src_path}: {e}")
            
            folderName = images_dir
            title = "Selected Images Slideshow"
            content = f"Slideshow created from {image_count} selected images."
        else:
            # Local folder option (console mode or no selections)
            local_folder = gui_local_folder if gui_local_folder is not None else None
            
            if not local_folder:
                print("No folder selected. Exiting.")
                return None, None, None
            
            if not os.path.isdir(local_folder):
                print(f"Not a valid directory: {local_folder}")
                return None, None, None
                
            print(f"Selected folder: {local_folder}")
            
            # Copy images from local folder to our images directory
            import shutil
            image_count = 0
            for filename in os.listdir(local_folder):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
                    src_path = os.path.join(local_folder, filename)
                    if os.path.isfile(src_path):  # Make sure it's a file, not a directory
                        # Rename to ensure sequential numbering
                        dst_path = os.path.join(images_dir, f"{image_count}.jpg")
                        try:
                            shutil.copy2(src_path, dst_path)
                            print(f"Copied {filename} to {dst_path}")
                            image_count += 1
                        except Exception as e:
                            print(f"Error copying {filename}: {e}")
            
            if image_count == 0:
                print("No images found in the selected folder.")
                return None, None, None
                
            print(f"Copied {image_count} images to {images_dir}")
            folderName = images_dir
            title = "Local Images Slideshow"
            content = f"Slideshow created from {image_count} local images."


    print("\n--- Step 4: Creating Slideshow Video ---")
    createSideShowWithFFmpeg(
        folderName=folderName,
        title=title,
        content=content,
        audioFile=audio_file,
        outputVideo=video_file,
        zoomFactor=0.5,
        frameRarte=25
    )


    print("\n--- File Status Check ---")
    print(f"Audio file: {audio_file}")
    print(f"Video file: {video_file}")
    print(f"Text file: {audio_file}.txt")

    if not os.path.exists(audio_file):
        print(f"ERROR: Audio file not found: {audio_file}")
        return None, None, None
    if not os.path.exists(video_file):
        print(f"ERROR: Video file not found: {video_file}")
        return None, None, None
    if not os.path.exists(f"{audio_file}.txt"):
        print(f"WARNING: Text file not found: {audio_file}.txt")
        # Create text file if it doesn't exist
        with open(f"{audio_file}.txt", "w", encoding="utf-8") as f:
            f.write(text_input)
        print(f"Created text file: {audio_file}.txt")
    print("\n--- Step 5: Generating Subtitles ---")
    subtitlePath = process_local_video(
        video_path=video_file, 
        output_type="ass", 
        maxChar=56, 
        output_file=subtitle_file, 
        audio_file=audio_file
    )
    
    if subtitlePath:
        print(f"Subtitles generated: {subtitlePath}")
        return subtitlePath, video_file, output_dir
    else:
        print("ERROR: Subtitle generation failed.")
        return None, None, None

def main(stop_event=None):
    # If GUI inputs are available, use them
    if gui_text_input is not None:
        print("\n=== VIDEO GENERATION SYSTEM (GUI MODE) ===")
    else:
        print("\n=== VIDEO GENERATION SYSTEM (CONSOLE MODE) ===")
    
    print("This program will create a video with subtitles from text and images.")
    
    subtitlePath, videoPath, output_dir = run_generation(stop_event)
    
    if subtitlePath and videoPath and output_dir:
        print("\n--- Final Step: Merging Video and Subtitles ---")
        final_output = os.path.join(output_dir, "final_output.mp4")
        print(f"Merging video: {videoPath}")
        print(f"With subtitles: {subtitlePath}")
        
        result = merge_video_subtitle(videoPath, subtitlePath, output_file=final_output)
        if result:
            print(f"Final video with subtitles created: {result}")
            print(f"All output files are in directory: {output_dir}")
        else:
            print("Failed to create final video with subtitles")

if __name__ == "__main__":
    try:
        # Check if we should use GUI mode
        import sys
        if "--gui" in sys.argv or len(sys.argv) == 1:  # Default to GUI if no args
            create_gui()
        else:
            main()
    except Exception as e:
        import traceback
        print(f"\nERROR: {e}")
        print("\nDetailed error information:")
        traceback.print_exc()
        print("\nPlease check that all required files exist and are in the correct locations.")
