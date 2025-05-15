"""
GUI for Video Generator using Tkinter
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the model
try:
    from models.video_generator import VideoGeneratorModel
except ImportError:
    print("Error importing VideoGeneratorModel")

class TextRedirector:
    """Redirect print statements to a tkinter Text widget"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, string):
        self.buffer += string
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")
        
    def flush(self):
        pass

class VideoGeneratorGUI:
    """GUI for Video Generator"""
    def __init__(self, root):
        """Initialize the GUI"""
        self.root = root
        self.root.title("Video Generator")
        self.root.geometry("800x800")
        self.root.minsize(600, 600)
        
        # Create the model
        self.model = VideoGeneratorModel()
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the input frame
        self.input_frame = ttk.LabelFrame(self.main_frame, text="Input", padding=10)
        self.input_frame.pack(fill=tk.BOTH, expand=False, pady=5)
        
        # Text input
        ttk.Label(self.input_frame, text="Text for voice generation:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.text_input = tk.Text(self.input_frame, height=5, width=50)
        self.text_input.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E, pady=5)
        
        # Image source
        ttk.Label(self.input_frame, text="Image source:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.image_source = tk.StringVar(value="1")
        ttk.Radiobutton(self.input_frame, text="Website URL", variable=self.image_source, value="1").grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(self.input_frame, text="Local folder", variable=self.image_source, value="2").grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Website URL
        ttk.Label(self.input_frame, text="Website URL:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.website_url = ttk.Entry(self.input_frame, width=50)
        self.website_url.grid(row=4, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Local folder
        ttk.Label(self.input_frame, text="Local folder:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.local_folder = ttk.Entry(self.input_frame, width=50)
        self.local_folder.grid(row=5, column=1, sticky=tk.W+tk.E, pady=5)
        self.browse_button = ttk.Button(self.input_frame, text="Browse...", command=self.browse_folder)
        self.browse_button.grid(row=5, column=2, sticky=tk.W, pady=5)
        
        # Processing option
        ttk.Label(self.input_frame, text="Processing option:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.processing_option = tk.StringVar(value="cpu")
        ttk.Radiobutton(self.input_frame, text="CPU", variable=self.processing_option, value="cpu").grid(row=6, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(self.input_frame, text="GPU", variable=self.processing_option, value="gpu").grid(row=7, column=1, sticky=tk.W, pady=5)
        
        # Output folder
        ttk.Label(self.input_frame, text="Output folder:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.output_folder = ttk.Entry(self.input_frame, width=50)
        self.output_folder.grid(row=8, column=1, sticky=tk.W+tk.E, pady=5)
        self.browse_output_button = ttk.Button(self.input_frame, text="Browse...", command=self.browse_output_folder)
        self.browse_output_button.grid(row=8, column=2, sticky=tk.W, pady=5)
        
        # Generate button
        self.generate_button = ttk.Button(self.input_frame, text="Generate Video", command=self.start_generation)
        self.generate_button.grid(row=9, column=0, columnspan=3, sticky=tk.W+tk.E, pady=10)
        
        # Progress bar
        ttk.Label(self.main_frame, text="Progress:").pack(anchor=tk.W, pady=(10, 0))
        self.progress_bar = ttk.Progressbar(self.main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Console output
        ttk.Label(self.main_frame, text="Console output:").pack(anchor=tk.W, pady=(10, 0))
        self.console_frame = ttk.Frame(self.main_frame)
        self.console_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.console_text = tk.Text(self.console_frame, wrap=tk.WORD, state="disabled")
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.console_scrollbar = ttk.Scrollbar(self.console_frame, orient=tk.VERTICAL, command=self.console_text.yview)
        self.console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console_text.configure(yscrollcommand=self.console_scrollbar.set)
        
        # Redirect stdout to the console
        self.stdout_redirector = TextRedirector(self.console_text)
        self.original_stdout = sys.stdout
        sys.stdout = self.stdout_redirector
        
        # Initialize thread and stop event
        self.thread = None
        self.stop_event = None
        
        # Print welcome message
        print("Welcome to Video Generator!")
        print("Enter text and select an image source to generate a video.")
        
    def browse_folder(self):
        """Browse for a folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.local_folder.delete(0, tk.END)
            self.local_folder.insert(0, folder)
    
    def browse_output_folder(self):
        """Browse for an output folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.delete(0, tk.END)
            self.output_folder.insert(0, folder)
    
    def start_generation(self):
        """Start the video generation process"""
        # Disable the generate button
        self.generate_button.configure(state="disabled")
        
        # Get the input values
        self.model.text_input = self.text_input.get("1.0", tk.END).strip()
        self.model.image_source = self.image_source.get()
        self.model.website_url = self.website_url.get()
        self.model.local_folder = self.local_folder.get()
        self.model.processing_option = self.processing_option.get()
        self.model.output_folder = self.output_folder.get()
        
        # Validate input
        if not self.model.text_input:
            messagebox.showerror("Error", "Please enter text for voice generation.")
            self.generate_button.configure(state="normal")
            return
        
        if self.model.image_source == "1" and not self.model.website_url:
            messagebox.showerror("Error", "Please enter a website URL.")
            self.generate_button.configure(state="normal")
            return
        
        if self.model.image_source == "2" and not self.model.local_folder:
            messagebox.showerror("Error", "Please select a local folder.")
            self.generate_button.configure(state="normal")
            return
        
        if self.model.image_source == "2" and not os.path.isdir(self.model.local_folder):
            messagebox.showerror("Error", f"Not a valid directory: {self.model.local_folder}")
            self.generate_button.configure(state="normal")
            return
        
        # Create a thread for video generation
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.generate_video_thread)
        self.thread.daemon = True
        self.thread.start()
    
    def generate_video_thread(self):
        """Run the video generation process in a separate thread"""
        try:
            # Override the update_progress method
            original_update_progress = self.model.update_progress
            
            def update_progress(progress, message=""):
                # Update the progress bar
                self.root.after(0, lambda: self.progress_bar.configure(value=progress))
                # Call the original method
                original_update_progress(progress, message)
            
            self.model.update_progress = update_progress
            
            # Generate the video
            subtitlePath, videoPath, output_dir = self.model.generate_video(self.stop_event)
            
            # Check if the process was stopped
            if self.stop_event and self.stop_event.is_set():
                print("Video generation stopped.")
                self.root.after(0, lambda: self.generate_button.configure(state="normal"))
                return
            
            # Finalize the video
            if subtitlePath and videoPath and output_dir:
                result = self.model.finalize_video(subtitlePath, videoPath, output_dir, self.stop_event)
                
                # Check if the process was stopped
                if self.stop_event and self.stop_event.is_set():
                    print("Video finalization stopped.")
                    self.root.after(0, lambda: self.generate_button.configure(state="normal"))
                    return
                
                if result:
                    print(f"Video generated successfully: {result}")
                    
                    # Show a message box
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Video generated successfully: {result}"))
                    
                    # Try to open the video
                    try:
                        if os.path.exists(result):
                            if sys.platform == "win32":
                                os.startfile(result)
                            elif sys.platform == "darwin":  # macOS
                                os.system(f"open {result}")
                            else:  # Linux
                                os.system(f"xdg-open {result}")
                    except Exception as e:
                        print(f"Could not open video automatically: {e}")
                else:
                    print("Failed to finalize video")
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to finalize video"))
            else:
                print("Video generation failed")
                self.root.after(0, lambda: messagebox.showerror("Error", "Video generation failed"))
        except Exception as e:
            print(f"Error generating video: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error generating video: {e}"))
        finally:
            # Re-enable the generate button
            self.root.after(0, lambda: self.generate_button.configure(state="normal"))
    
    def __del__(self):
        """Restore stdout when the object is deleted"""
        sys.stdout = self.original_stdout

