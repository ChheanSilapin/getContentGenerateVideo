"""
Base UI component for the Video Generator application
Provides common functionality and standardized patterns for UI components
"""
from utils.common_imports import tk, messagebox, ttk

class BaseUIComponent:
    """Base class for UI components with common functionality"""
    
    def __init__(self, parent, main_gui):
        """
        Initialize the base component
        
        Args:
            parent: Parent tkinter widget
            main_gui: Reference to main GUI instance
        """
        self.parent = parent
        self.main_gui = main_gui
    
    def show_warning(self, title, message):
        """
        Standardized warning dialog
        
        Args:
            title: Dialog title
            message: Warning message
        """
        messagebox.showwarning(title, message)
    
    def show_error(self, title, message):
        """
        Standardized error dialog
        
        Args:
            title: Dialog title
            message: Error message
        """
        messagebox.showerror(title, message)
    
    def show_info(self, title, message):
        """
        Standardized info dialog
        
        Args:
            title: Dialog title
            message: Info message
        """
        messagebox.showinfo(title, message)
    
    def ask_yes_no(self, title, message):
        """
        Standardized yes/no dialog
        
        Args:
            title: Dialog title
            message: Question message
            
        Returns:
            bool: True if yes, False if no
        """
        return messagebox.askyesno(title, message)
    
    def check_process_running(self):
        """
        Check if video generation is already in progress
        
        Returns:
            bool: True if process is running, False otherwise
        """
        if self.main_gui.generation_thread and self.main_gui.generation_thread.is_alive():
            self.show_warning("Process Running", "Video generation is already in progress")
            return True
        return False
    
    def validate_text_input(self, text_widget):
        """
        Validate text input from a text widget
        
        Args:
            text_widget: tkinter Text widget
            
        Returns:
            str: Validated text or None if invalid
        """
        text = text_widget.get("1.0", tk.END).strip()
        if not text:
            self.show_warning("Input Error", "Please enter text for voice generation")
            return None
        return text
    
    def create_labeled_frame(self, parent, title, padding=10):
        """
        Create a labeled frame with consistent styling
        
        Args:
            parent: Parent widget
            title: Frame title
            padding: Internal padding
            
        Returns:
            tkinter.LabelFrame: Created frame
        """
        frame = tk.LabelFrame(parent, text=title, font=("Arial", 10, "bold"))
        frame.pack(fill="both", expand=True, padx=padding, pady=padding)
        return frame
    
    def create_button_frame(self, parent):
        """
        Create a frame for buttons with consistent styling
        
        Args:
            parent: Parent widget
            
        Returns:
            tkinter.Frame: Button frame
        """
        button_frame = tk.Frame(parent)
        button_frame.pack(fill="x", padx=10, pady=5)
        return button_frame
    
    def create_progress_frame(self, parent):
        """
        Create a progress frame with progress bar and label
        
        Args:
            parent: Parent widget
            
        Returns:
            tuple: (progress_frame, progress_bar, progress_label)
        """
        progress_frame = tk.Frame(parent)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        progress_bar.pack(fill="x", pady=(0, 5))
        
        progress_label = tk.Label(progress_frame, text="Ready", anchor="w")
        progress_label.pack(fill="x")
        
        return progress_frame, progress_bar, progress_label
    
    def log_message(self, message):
        """
        Log a message to the main GUI log
        
        Args:
            message: Message to log
        """
        if hasattr(self.main_gui, 'log'):
            self.main_gui.log(message)
        else:
            print(message)
    
    def update_progress(self, value, message=None):
        """
        Update progress through main GUI
        
        Args:
            value: Progress value (0-100)
            message: Optional progress message
        """
        if hasattr(self.main_gui, 'update_progress_ui'):
            self.main_gui.update_progress_ui(value, message)
    
    def get_selected_images(self):
        """
        Get selected images from main GUI
        
        Returns:
            list: List of selected image paths
        """
        if hasattr(self.main_gui, 'selected_images'):
            return self.main_gui.selected_images
        return []
    
    def set_selected_images(self, images):
        """
        Set selected images in main GUI
        
        Args:
            images: List of image paths
        """
        if hasattr(self.main_gui, 'selected_images'):
            self.main_gui.selected_images = images 