"""
Helper functions for the Video Generator application
"""
import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
from config import SUPPORTED_IMAGE_EXTENSIONS

def get_title_content(url):
    """
    Get the title and content from a website URL
    
    Args:
        url: Website URL to extract content from
        
    Returns:
        tuple: (title, content) extracted from the website
    """
    try:
        # Check if the URL is a direct image file
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path.lower()
        if path.endswith(SUPPORTED_IMAGE_EXTENSIONS):
            print("Direct image URL detected")
            
            # Extract a title from the filename
            filename = os.path.basename(parsed_url.path)
            title = os.path.splitext(filename)[0]
            
            # For direct image URLs, create a simple content description
            content = f"Image file: {filename}. This is a direct image URL without additional text content."
            
            # Download the image directly to the first image slot
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Return the title and a placeholder content
                return title, content
            except Exception as img_error:
                print(f"Error downloading direct image: {img_error}")
                return "Image Download Error", "Failed to download the direct image URL."
        
        # Regular website processing
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get the title
        title_tag = soup.find('title')
        title = title_tag.text if title_tag else "Untitled Page"
        
        # Get the content (prioritize article content, then main, then body)
        content = ""
        
        # Try to find article content
        article = soup.find('article')
        if article:
            paragraphs = article.find_all('p')
            content = ' '.join([p.text for p in paragraphs])
        
        # If no article content, try main content
        if not content:
            main = soup.find('main')
            if main:
                paragraphs = main.find_all('p')
                content = ' '.join([p.text for p in paragraphs])
        
        # If still no content, get all paragraphs from body
        if not content:
            paragraphs = soup.find_all('p')
            content = ' '.join([p.text for p in paragraphs])
        
        # If still no content, use all text from body
        if not content:
            body = soup.find('body')
            if body:
                content = body.text
        
        # Clean up the content
        content = content.strip()
        
        # If still no content, use a placeholder
        if not content:
            content = f"No text content found on {url}. This is a placeholder text for the video."
        
        return title, content
        
    except Exception as e:
        print(f"Error getting title and content: {e}")
        return "Error", f"Failed to retrieve content from {url}. Error: {str(e)}"
