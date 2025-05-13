import requests
from bs4 import BeautifulSoup
import os
import urllib.parse

def getTitleContent(url):
    """Get the title and content from a website URL"""
    try:
        # Check if the URL is a direct image file
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path.lower()
        if path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
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
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string if soup.title else "Video Title"
        content = ""
        article = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
        if article:
            paragraphs = article.find_all('p')
            content = ' '.join([p.text for p in paragraphs])
        
        if not content:
            paragraphs = soup.find_all('p')
            content = ' '.join([p.text for p in paragraphs[:5]])  # Limit to first 5 paragraphs
            
        if not content:
            content = "This website doesn't contain easily extractable text content."
            
        return title, content
    except Exception as e:
        print(f"Error fetching website content: {e}")
        return "Video Title", "Video content could not be retrieved."
