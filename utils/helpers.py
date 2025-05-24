"""
Helper functions for the Video Generator application
"""
import os
import sys
import platform
import re
import emoji
import shutil
import traceback
import requests
from bs4 import BeautifulSoup
import urllib.parse
from config import SUPPORTED_IMAGE_EXTENSIONS

def get_title_content(text):
    """
    Extract title and content from a text

    Args:
        text: Input text

    Returns:
        tuple: (title, content)
    """
    lines = text.strip().split('\n')

    # If there's only one line, use it as both title and content
    if len(lines) == 1:
        return lines[0], lines[0]

    # Use the first line as title and the rest as content
    title = lines[0]
    content = '\n'.join(lines[1:])

    return title, content

def process_text_for_tts(text):
    """
    Process text for text-to-speech by removing emojis and non-ASCII characters

    Args:
        text: Text to process

    Returns:
        str: Processed text
    """
    if not text:
        return ""

    # Remove emojis
    text = emoji.replace_emoji(text, replace='')

    # Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def ensure_directory_exists(directory_path):
    """
    Create a directory if it doesn't exist

    Args:
        directory_path: Path to directory

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            print(f"Created directory: {directory_path}")
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False

def get_file_extension(file_path):
    """
    Get the extension of a file

    Args:
        file_path: Path to file

    Returns:
        str: File extension (with dot)
    """
    return os.path.splitext(file_path)[1].lower()

def is_image_file(file_path):
    """
    Check if a file is an image based on its extension

    Args:
        file_path: Path to file

    Returns:
        bool: True if a file is an image, False otherwise
    """
    return get_file_extension(file_path) in SUPPORTED_IMAGE_EXTENSIONS

def copy_file(source, destination):
    """
    Copy a file from source to destination

    Args:
        source: Source file path
        destination: Destination file path

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create destination directory if it doesn't exist
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)

        # Copy the file
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(f"Error copying file from {source} to {destination}: {e}")
        return False

def get_platform_info():
    """
    Get information about the current platform

    Returns:
        dict: Platform information
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }

def print_exception(e, message="An error occurred"):
    """
    Print exception details with a custom message

    Args:
        e: Exception object
        message: Custom message to print before the exception
    """
    print(f"{message}: {str(e)}")
    traceback.print_exc()
