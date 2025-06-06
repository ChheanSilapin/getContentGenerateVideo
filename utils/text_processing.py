"""
Centralized text processing utilities for Video Generator
Consolidates all text processing functions from across the codebase
"""
import re
import emoji


def process_text_for_tts(text, emotion="neutral"):
    """
    Process text for text-to-speech with optional emotional enhancement
    
    Args:
        text: Text to process
        emotion: Emotion to apply ("neutral", "excited", "dramatic", "calm", "energetic")
        
    Returns:
        str: Processed text ready for TTS
    """
    if not text:
        return ""

    # Remove emojis but keep emotional context
    text = emoji.replace_emoji(text, replace='')
    
    # Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    # Add emotional pauses and emphasis based on emotion
    if emotion == "excited":
        # Add excitement with emphasis and shorter pauses
        text = re.sub(r'[.!?]', '!', text)  # Convert periods to exclamations
        text = re.sub(r'([.!?])', r'\1 ', text)  # Add short pauses
        text = text.replace(' ', ' ')  # Slightly faster pacing
        
    elif emotion == "dramatic":
        # Add dramatic pauses and emphasis
        text = re.sub(r'([.!?])', r'\1... ', text)  # Add dramatic pauses
        text = re.sub(r'(\w+)', r'\1', text)  # Slight emphasis on words
        
    elif emotion == "calm":
        # Add calming pauses
        text = re.sub(r'([.!?])', r'\1... ', text)  # Add longer pauses
        text = text.replace('!', '.')  # Convert exclamations to periods
        
    elif emotion == "energetic":
        # Add energy with varied intonation
        text = re.sub(r'([.!?])', r'\1 ', text)  # Quick pauses
        # Add emphasis to important words
        important_words = ['amazing', 'incredible', 'fantastic', 'awesome', 'great', 'wonderful']
        for word in important_words:
            text = re.sub(rf'\b{word}\b', f'{word.upper()}', text, flags=re.IGNORECASE)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def process_text_for_subtitles(text):
    """
    Enhanced text processing that removes numbered lists and preserves important content
    
    Args:
        text: Text to process
        
    Returns:
        str: Processed text with preserved important content and removed numbering
    """
    if not text:
        return ""
    
    # First, handle number emojis
    number_emoji_map = {
        '0️⃣': '0', '1️⃣': '1', '2️⃣': '2', '3️⃣': '3', '4️⃣': '4',
        '5️⃣': '5', '6️⃣': '6', '7️⃣': '7', '8️⃣': '8', '9️⃣': '9'
    }
    for emoji_num, real_num in number_emoji_map.items():
        text = text.replace(emoji_num, real_num)
    
    # Remove all other emojis but preserve text
    text = emoji.replace_emoji(text, replace='')
    
    # AGGRESSIVE: Remove numbered list patterns first (before protecting content)
    # Remove patterns like "150)," or "150)" at the beginning or anywhere
    text = re.sub(r'\b\d+\)[,\s]*', '', text)  # Remove "150)," or "150) "
    text = re.sub(r'^\s*\d+[.)\]]\s*', '', text)  # Remove "150." or "150)" at start
    text = re.sub(r'\(\d+\)[,\s]*', '', text)  # Remove "(150)," 
    
    # Preserve important patterns AFTER removing numbering
    # Protect currency amounts like $17,190 and $21,590
    currency_pattern = r'\$[\d,]+(?:\.\d{2})?'
    currency_matches = re.findall(currency_pattern, text)
    currency_placeholders = {}
    for i, match in enumerate(currency_matches):
        placeholder = f"__CURRENCY_{i}__"
        currency_placeholders[placeholder] = match
        text = text.replace(match, placeholder, 1)
    
    # Protect years like 2025, 2026
    year_pattern = r'\b(19|20)\d{2}\b'
    year_matches = re.findall(year_pattern, text)
    year_placeholders = {}
    for i, match in enumerate(year_matches):
        placeholder = f"__YEAR_{i}__"
        year_placeholders[placeholder] = match
        text = text.replace(match, placeholder, 1)
    
    # Protect contractions like 's, 'll, 've, 're, 't, 'd
    contraction_pattern = r"\b\w+[''](?:s|ll|ve|re|t|d|m)\b"
    contraction_matches = re.findall(contraction_pattern, text, re.IGNORECASE)
    contraction_placeholders = {}
    for i, match in enumerate(contraction_matches):
        placeholder = f"__CONTRACTION_{i}__"
        contraction_placeholders[placeholder] = match
        text = text.replace(match, placeholder, 1)
    
    # Remove non-ASCII characters that might cause issues (but preserve placeholders)
    text = re.sub(r'[^\x00-\x7F_]+', ' ', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # ADDITIONAL aggressive cleaning for any remaining numbered patterns
    text = re.sub(r'^\s*\d+[.)\]\}:,-]\s*', '', text)  # Remove any number with punct at start
    text = re.sub(r'\s+\d+[.)\]\}:,-]\s+', ' ', text)  # Remove numbered items in middle
    
    # Restore protected content
    for placeholder, original in currency_placeholders.items():
        text = text.replace(placeholder, original)
    
    for placeholder, original in year_placeholders.items():
        text = text.replace(placeholder, original)
    
    for placeholder, original in contraction_placeholders.items():
        text = text.replace(placeholder, original)
    
    # Final cleanup
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove leading punctuation and any remaining artifacts
    text = re.sub(r'^[,\.\)\]\}:;-]+\s*', '', text)
    text = re.sub(r'^[^\w$]+', '', text)  # Remove any non-word chars at start (except $)
    
    return text


def get_title_content(text):
    """
    Extract title and content from a text

    Args:
        text: Input text

    Returns:
        tuple: (title, content)
    """
    if not text:
        return "", ""
        
    lines = text.strip().split('\n')

    # If there's only one line, use it as both title and content
    if len(lines) == 1:
        return lines[0], lines[0]

    # Use the first line as title and the rest as content
    title = lines[0]
    content = '\n'.join(lines[1:])

    return title, content


def clean_text_basic(text):
    """
    Basic text cleaning for general purposes
    
    Args:
        text: Text to clean
        
    Returns:
        str: Cleaned text
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