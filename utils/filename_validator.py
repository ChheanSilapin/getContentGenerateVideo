#!/usr/bin/env python3
"""
Filename validation utility for custom video output names
"""

import re
import os

def validate_filename(filename):
    """
    Validate a filename for use in video output
    
    Args:
        filename (str): The filename to validate (without extension)
        
    Returns:
        tuple: (is_valid, cleaned_filename, error_message)
    """
    if not filename or not filename.strip():
        return True, "", ""  # Empty filename is valid (will use default)
    
    filename = filename.strip()
    
    # Check for invalid characters (Windows and Unix)
    invalid_chars = r'[<>:"/\\|?*]'
    if re.search(invalid_chars, filename):
        cleaned = re.sub(invalid_chars, '_', filename)
        return False, cleaned, "Filename contains invalid characters. They will be replaced with underscores."
    
    # Check for reserved Windows names
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    if filename.upper() in reserved_names:
        cleaned = f"{filename}_video"
        return False, cleaned, f"'{filename}' is a reserved system name. '_video' will be added."
    
    # Check length (Windows has 255 char limit, but we'll be conservative)
    if len(filename) > 200:
        cleaned = filename[:200]
        return False, cleaned, "Filename is too long. It will be truncated to 200 characters."
    
    # Check for leading/trailing spaces or dots
    if filename != filename.strip(' .'):
        cleaned = filename.strip(' .')
        if not cleaned:
            cleaned = "video"
        return False, cleaned, "Filename cannot start or end with spaces or dots."
    
    # All checks passed
    return True, filename, ""

def sanitize_filename(filename):
    """
    Sanitize a filename by removing/replacing invalid characters
    
    Args:
        filename (str): The filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    if not filename or not filename.strip():
        return ""
    
    filename = filename.strip()
    
    # Replace invalid characters with underscores
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)
    
    # Handle reserved names
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    if filename.upper() in reserved_names:
        filename = f"{filename}_video"
    
    # Truncate if too long
    if len(filename) > 200:
        filename = filename[:200]
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # If empty after cleaning, provide default
    if not filename:
        filename = "video"
    
    return filename

def get_final_output_filename(custom_filename, default_name="final_output"):
    """
    Get the final output filename with .mp4 extension
    
    Args:
        custom_filename (str): Custom filename provided by user (without extension)
        default_name (str): Default name to use if custom_filename is empty
        
    Returns:
        str: Final filename with .mp4 extension
    """
    if custom_filename and custom_filename.strip():
        # Sanitize the custom filename
        sanitized = sanitize_filename(custom_filename)
        return f"{sanitized}.mp4"
    else:
        # Use default
        return f"{default_name}.mp4"

def validate_and_suggest_filename(filename):
    """
    Validate filename and provide suggestions for improvement
    
    Args:
        filename (str): The filename to validate
        
    Returns:
        dict: {
            'is_valid': bool,
            'filename': str,  # cleaned/suggested filename
            'message': str,   # user-friendly message
            'severity': str   # 'info', 'warning', 'error'
        }
    """
    if not filename or not filename.strip():
        return {
            'is_valid': True,
            'filename': "",
            'message': "Will use default filename",
            'severity': 'info'
        }
    
    is_valid, cleaned, error_msg = validate_filename(filename)
    
    if is_valid:
        return {
            'is_valid': True,
            'filename': filename,
            'message': "Filename is valid",
            'severity': 'info'
        }
    else:
        return {
            'is_valid': False,
            'filename': cleaned,
            'message': error_msg,
            'severity': 'warning'
        }
