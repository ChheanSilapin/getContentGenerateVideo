"""
Dialog helper functions for the Video Generator application
Provides standardized file dialogs to eliminate duplication across UI components
"""

from tkinter import filedialog


def select_image_files(title="Select Images", multiple=True):
    """
    Standardized image file selection dialog
    
    Args:
        title: Dialog title
        multiple: Whether to allow multiple file selection
        
    Returns:
        list or str: Selected file paths (list if multiple=True, str if multiple=False)
    """
    filetypes = [
        ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
        ("JPEG files", "*.jpg *.jpeg"),
        ("PNG files", "*.png"),
        ("GIF files", "*.gif"),
        ("All files", "*.*")
    ]
    
    if multiple:
        return filedialog.askopenfilenames(title=title, filetypes=filetypes)
    else:
        return filedialog.askopenfilename(title=title, filetypes=filetypes)


def select_video_files(title="Select Videos", multiple=True):
    """
    Standardized video file selection dialog
    
    Args:
        title: Dialog title
        multiple: Whether to allow multiple file selection
        
    Returns:
        list or str: Selected file paths (list if multiple=True, str if multiple=False)
    """
    filetypes = [
        ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
        ("MP4 files", "*.mp4"),
        ("AVI files", "*.avi"),
        ("MOV files", "*.mov"),
        ("MKV files", "*.mkv"),
        ("All files", "*.*")
    ]
    
    if multiple:
        return filedialog.askopenfilenames(title=title, filetypes=filetypes)
    else:
        return filedialog.askopenfilename(title=title, filetypes=filetypes)


def select_folder(title="Select Folder"):
    """
    Standardized folder selection dialog
    
    Args:
        title: Dialog title
        
    Returns:
        str: Selected folder path
    """
    return filedialog.askdirectory(title=title)


def save_video_file(title="Save Video As", default_name="output.mp4"):
    """
    Standardized save video file dialog
    
    Args:
        title: Dialog title
        default_name: Default filename
        
    Returns:
        str: Selected save path
    """
    return filedialog.asksaveasfilename(
        title=title,
        defaultextension=".mp4",
        initialvalue=default_name,
        filetypes=[
            ("MP4 files", "*.mp4"),
            ("AVI files", "*.avi"),
            ("MOV files", "*.mov"),
            ("All files", "*.*")
        ]
    )


def save_file_generic(title="Save File As", default_extension=".txt", filetypes=None):
    """
    Generic save file dialog
    
    Args:
        title: Dialog title
        default_extension: Default file extension
        filetypes: List of (description, pattern) tuples
        
    Returns:
        str: Selected save path
    """
    if filetypes is None:
        filetypes = [("All files", "*.*")]
    
    return filedialog.asksaveasfilename(
        title=title,
        defaultextension=default_extension,
        filetypes=filetypes
    )
