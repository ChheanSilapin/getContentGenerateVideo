"""
WordPress Post Scraper - Extract content from WordPress posts
Downloads text and images from a single post URL
"""
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tempfile
import hashlib


class WordPressScraper:
    """Scrape content from WordPress posts"""
    
    def __init__(self, timeout=30):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_post(self, url, output_dir=None):
        """
        Scrape a WordPress post and extract content
        
        Args:
            url: Post URL
            output_dir: Directory to save images (uses temp if None)
            
        Returns:
            dict: {
                'title': str,
                'text': str,
                'images': list of file paths,
                'success': bool,
                'error': str or None
            }
        """
        try:
            # Create output directory
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix="wp_scrape_")
            os.makedirs(output_dir, exist_ok=True)
            
            # Fetch page
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content text
            text = self._extract_text(soup)
            
            # Download images
            images = self._download_images(soup, url, output_dir)
            
            return {
                'title': title,
                'text': text,
                'images': images,
                'image_dir': output_dir,
                'success': True,
                'error': None
            }
            
        except Exception as e:
            return {
                'title': '',
                'text': '',
                'images': [],
                'image_dir': None,
                'success': False,
                'error': str(e)
            }
    
    def _extract_title(self, soup):
        """Extract article title"""
        # Try common WordPress title selectors
        selectors = [
            'h1.entry-title',
            'h1.post-title',
            '.entry-header h1',
            'article h1',
            'h1',
        ]
        
        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)
        
        # Fallback to page title
        if soup.title:
            return soup.title.get_text(strip=True)
        
        return "Untitled"
    
    def _extract_text(self, soup):
        """Extract main article text"""
        # Try common WordPress content selectors
        selectors = [
            '.entry-content',
            '.post-content',
            'article .content',
            '.article-content',
            'article',
            '.post',
        ]
        
        content_elem = None
        for selector in selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                break
        
        if not content_elem:
            return ""
        
        # Remove script, style, and navigation elements
        for tag in content_elem.find_all(['script', 'style', 'nav', 'aside', 'footer']):
            tag.decompose()
        
        # Get paragraphs
        paragraphs = []
        for p in content_elem.find_all(['p', 'h2', 'h3', 'h4']):
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Skip short/empty paragraphs
                paragraphs.append(text)
        
        return '\n\n'.join(paragraphs)
    
    def _download_images(self, soup, base_url, output_dir):
        """Download all images from the article"""
        downloaded = []
        
        # Find article content first
        content_selectors = ['.entry-content', '.post-content', 'article', '.post']
        content = None
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                break
        
        if not content:
            content = soup
        
        # Find images
        images = content.find_all('img')
        
        for i, img in enumerate(images):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not src:
                continue
            
            # Skip small icons, avatars, etc.
            if any(skip in src.lower() for skip in ['avatar', 'icon', 'logo', 'emoji', 'gravatar']):
                continue
            
            # Get full URL
            full_url = urljoin(base_url, src)
            
            # Download image
            try:
                img_response = requests.get(full_url, headers=self.headers, timeout=15)
                img_response.raise_for_status()
                
                # Determine file extension
                content_type = img_response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                elif 'gif' in content_type:
                    ext = '.gif'
                else:
                    ext = os.path.splitext(urlparse(full_url).path)[1] or '.jpg'
                
                # Generate filename
                filename = f"image_{i+1:02d}{ext}"
                filepath = os.path.join(output_dir, filename)
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(img_response.content)
                
                downloaded.append(filepath)
                print(f"Downloaded: {filename}")
                
            except Exception as e:
                print(f"Failed to download image: {e}")
        
        return downloaded


def scrape_wordpress_post(url, output_dir=None):
    """
    Convenience function to scrape a WordPress post
    
    Args:
        url: Post URL
        output_dir: Directory to save images
        
    Returns:
        dict with title, text, images, success, error
    """
    scraper = WordPressScraper()
    return scraper.scrape_post(url, output_dir)
