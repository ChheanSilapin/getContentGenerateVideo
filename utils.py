import requests
from bs4 import BeautifulSoup

def getTitleContent(url):
    """Get the title and content from a website URL"""
    try:
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
        return title, content
    except Exception as e:
        print(f"Error fetching website content: {e}")
        return "Video Title", "Video content could not be retrieved."
