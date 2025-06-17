"""
Media Helper Functions for Video Generator
Provides common media file analysis and processing utilities
"""
import os
import config


def analyze_media_folder(folder_path, media_type="image"):
    """
    Analyze a folder for media files and text files
    
    Args:
        folder_path: Path to folder to analyze
        media_type: Type of media to look for ("image" or "video")
        
    Returns:
        dict: Analysis results with media files, text files, and best text file
    """
    try:
        # Get appropriate extensions based on media type
        if media_type == "image":
            media_extensions = config.IMAGE_EXTENSIONS
        elif media_type == "video":
            media_extensions = config.VIDEO_EXTENSIONS
        else:
            raise ValueError(f"Unsupported media type: {media_type}")
        
        text_extensions = config.TEXT_EXTENSIONS
        
        media_files = []
        text_files = []
        
        # Scan folder for files
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in media_extensions:
                    media_files.append(file_path)
                elif ext in text_extensions:
                    text_files.append(file_path)
        
        # Sort media files naturally
        media_files.sort()
        
        # Find best text file
        best_text_file = find_best_text_file(text_files)
        
        return {
            'media_files': media_files,
            'text_files': text_files,
            'best_text_file': best_text_file,
            'media_count': len(media_files),
            'text_count': len(text_files),
            'media_type': media_type
        }
        
    except Exception as e:
        return {
            'media_files': [],
            'text_files': [],
            'best_text_file': None,
            'media_count': 0,
            'text_count': 0,
            'media_type': media_type,
            'error': str(e)
        }


def find_best_text_file(text_files):
    """
    Find the best text file to use as prompt based on priority names
    
    Args:
        text_files: List of text file paths
        
    Returns:
        str or None: Path to best text file, or None if no files
    """
    if not text_files:
        return None
    
    # Get priority names from config
    priority_names = config.TEXT_FILE_PRIORITY
    
    # Check for priority names first
    for priority_name in priority_names:
        for text_file in text_files:
            if os.path.basename(text_file).lower() == priority_name:
                return text_file
    
    # If no priority match, return the first text file
    return text_files[0]


def load_text_file_content(text_file_path):
    """
    Load content from a text file with error handling
    
    Args:
        text_file_path: Path to text file
        
    Returns:
        str: File content, or empty string if error
    """
    if not text_file_path or not os.path.exists(text_file_path):
        return ""
    
    try:
        with open(text_file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return ""


def get_media_folder_status(analysis_result):
    """
    Generate a status message for media folder analysis
    
    Args:
        analysis_result: Result from analyze_media_folder()
        
    Returns:
        str: Status message
    """
    if analysis_result.get('error'):
        return f"Error analyzing folder: {analysis_result['error']}"
    
    media_count = analysis_result['media_count']
    media_type = analysis_result['media_type']
    has_text = analysis_result['best_text_file'] is not None
    
    if media_count == 0:
        return f"No {media_type} files found in folder"
    
    text_status = "with text file" if has_text else "no text file"
    return f"{media_count} {media_type}(s) found, {text_status}"


def scan_folder_for_media_pairs(folder_path, media_type="video"):
    """
    Scan folder recursively for media+text file pairs
    
    Args:
        folder_path: Root folder to scan
        media_type: Type of media to look for ("image" or "video")
        
    Returns:
        list: List of media-text pairs found
    """
    # Get appropriate extensions
    if media_type == "image":
        media_extensions = config.IMAGE_EXTENSIONS
    elif media_type == "video":
        media_extensions = config.VIDEO_EXTENSIONS
    else:
        raise ValueError(f"Unsupported media type: {media_type}")
    
    text_extensions = config.TEXT_EXTENSIONS
    pairs = []
    
    # Scan recursively for all files
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            all_files.append(os.path.join(root, file))
    
    # Group files by directory
    dir_files = {}
    for file_path in all_files:
        dir_name = os.path.dirname(file_path)
        if dir_name not in dir_files:
            dir_files[dir_name] = {'media': [], 'texts': []}
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext in media_extensions:
            dir_files[dir_name]['media'].append(file_path)
        elif ext in text_extensions:
            dir_files[dir_name]['texts'].append(file_path)
    
    # Find pairs in each directory
    for dir_path, files in dir_files.items():
        media_files = files['media']
        text_files = files['texts']
        
        if media_files:
            # Find best text file for this directory
            best_text = find_best_text_file(text_files)
            
            for media_file in media_files:
                pairs.append({
                    'media_file': media_file,
                    'text_file': best_text,
                    'directory': dir_path,
                    'media_type': media_type
                })
    
    return pairs
