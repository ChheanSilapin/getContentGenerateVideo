"""
Helper functions for the Video Generator application
"""
import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
from config import SUPPORTED_IMAGE_EXTENSIONS

def get_title_content(text):
    """
    Extract title and content from text
    
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

