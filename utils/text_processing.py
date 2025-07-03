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
    # Only remove numbered lists at start of line, not decimal numbers
    text = re.sub(r'^\s*\d+\.\s+', '', text)  # Remove "150. " at start (with space after dot)
    text = re.sub(r'^\s*\d+\)\s*', '', text)  # Remove "150)" at start
    text = re.sub(r'^\s*\d+\]\s*', '', text)  # Remove "150]" at start
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


def normalize_text_for_natural_speech(text, mode="tts"):
    """
    Convert complex formatted text into clean text for TTS or subtitles.
    Preserves contractions throughout the entire processing pipeline.

    Args:
        text: Raw text input (may contain complex formatting, special chars, etc.)
        mode: "tts" for spoken format, "subtitle" for visual format

    Returns:
        str: Clean text ready for TTS or subtitles
    """
    if not text:
        return ""

    # Step 1: Protect existing contractions FIRST before any other processing
    # This prevents them from being broken by subsequent steps
    # Enhanced pattern to catch contractions even when adjacent to complex punctuation
    contraction_pattern = r"\b\w+[''](?:s|ll|ve|re|t|d|m)\b"
    contraction_matches = re.findall(contraction_pattern, text, re.IGNORECASE)
    contraction_placeholders = {}

    # Optional debug logging (can be enabled for troubleshooting)
    # if contraction_matches:
    #     print(f"[DEBUG] Contractions detected: {contraction_matches}")

    for i, match in enumerate(contraction_matches):
        placeholder = f"__CONTRACTION_{i}__"
        contraction_placeholders[placeholder] = match
        text = text.replace(match, placeholder, 1)

    # Step 2: Handle paragraph breaks and line endings
    text = re.sub(r'\n\s*\n+', '. ', text)  # Double line breaks become sentence breaks
    text = re.sub(r'\n+', ' ', text)  # Single line breaks become spaces

    # Step 3: Convert complex formatting based on mode
    if mode == "tts":
        # TTS mode: Handle dates and years for natural speech
        def convert_date_tts(match):
            month, day, year = match.groups()
            day_num = int(day.replace('th', '').replace('st', '').replace('nd', '').replace('rd', ''))
            day_ordinal = f"{day_num}th" if 11 <= day_num <= 13 else {
                1: "first", 2: "second", 3: "third", 21: "twenty-first", 22: "twenty-second", 23: "twenty-third"
            }.get(day_num, f"{day_num}th")
            # Convert year to natural speech: 2025 -> twenty twenty-five
            year_int = int(year)
            if 2000 <= year_int <= 2099:
                decade = year_int - 2000
                if decade == 0:
                    year_spoken = "two thousand"
                elif decade < 10:
                    year_spoken = f"two thousand {decade}"
                else:
                    # Convert 25 to "twenty twenty-five", 24 to "twenty twenty-four", etc.
                    # For 2020-2029: "twenty twenty", "twenty twenty-one", etc.
                    # For 2030-2099: "twenty thirty", "twenty thirty-one", etc.
                    tens = decade // 10
                    ones = decade % 10
                    if tens == 2:  # 2020-2029
                        if ones == 0:
                            year_spoken = "twenty twenty"
                        else:
                            ones_word = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"][ones]
                            year_spoken = f"twenty twenty-{ones_word}"
                    else:  # 2030+
                        tens_word = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"][tens]
                        if ones == 0:
                            year_spoken = f"twenty {tens_word}"
                        else:
                            ones_word = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"][ones]
                            year_spoken = f"twenty {tens_word}-{ones_word}"
            else:
                year_spoken = " ".join(str(int(year[i:i+1])) for i in range(0, 4))
            return f"{month} {day_ordinal}, {year_spoken}"

        text = re.sub(r'(\w+)\s+(\d{1,2}(?:st|nd|rd|th)?),\s+(\d{4})', convert_date_tts, text, flags=re.IGNORECASE)

        # Also handle standalone years: 2025 -> twenty twenty-five
        def convert_year_tts(match):
            year = int(match.group(1))
            if 2000 <= year <= 2099:
                decade = year - 2000
                if decade == 0:
                    return "two thousand"
                elif decade < 10:
                    return f"two thousand {decade}"
                else:
                    # Convert 25 to "twenty twenty-five", 24 to "twenty twenty-four", etc.
                    # For 2020-2029: "twenty twenty", "twenty twenty-one", etc.
                    # For 2030-2099: "twenty thirty", "twenty thirty-one", etc.
                    tens = decade // 10
                    ones = decade % 10
                    if tens == 2:  # 2020-2029
                        if ones == 0:
                            return "twenty twenty"
                        else:
                            ones_word = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"][ones]
                            return f"twenty twenty-{ones_word}"
                    else:  # 2030+
                        tens_word = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"][tens]
                        if ones == 0:
                            return f"twenty {tens_word}"
                        else:
                            ones_word = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"][ones]
                            return f"twenty {tens_word}-{ones_word}"
            return match.group(1)

        text = re.sub(r'\b(20\d{2})\b', convert_year_tts, text)
    # Subtitle mode: preserve date formatting as-is

    # Handle currency amounts first (before number processing)
    # This prevents currency numbers from being processed as regular numbers
    if mode == "tts":
        # TTS mode: $1.2 trillion -> one point two trillion dollars
        def convert_currency_tts(match):
            amount = match.group(1).replace(',', ' ')  # Replace commas with spaces for TTS
            unit = match.group(2) or ""
            if '.' in amount:
                whole, decimal = amount.split('.')
                if unit:
                    return f"{whole} point {decimal} {unit} dollars"
                else:
                    return f"{whole} point {decimal} dollars"
            return f"{amount} {unit} dollars" if unit else f"{amount} dollars"

        text = re.sub(r'\$([\d,]+(?:\.\d+)?)\s*(trillion|billion|million)?(?=\s|,|\.|\?|!|$)', convert_currency_tts, text)
    else:
        # Subtitle mode: preserve currency formatting but clean up spacing
        text = re.sub(r'\$\s*(\d)', r'$\1', text)  # Remove space after $

    # Handle numbers with commas based on mode (after currency processing)
    if mode == "tts":
        # TTS mode: remove commas for better pronunciation: 1,200 -> 1 200
        # But skip numbers that are part of currency (already processed above)
        text = re.sub(r'(?<!\$)(\d{1,3}),(\d{3})(?!\s*(trillion|billion|million))', r'\1 \2', text)  # 1,200 -> 1 200
        text = re.sub(r'(?<!\$)(\d{1,3}),(\d{3}),(\d{3})(?!\s*(trillion|billion|million))', r'\1 \2 \3', text)  # 1,000,000 -> 1 000 000
    # Subtitle mode: preserve comma formatting for readability

    # Handle percentages based on mode
    if mode == "tts":
        # TTS mode: 19.7% -> nineteen point seven percent
        def convert_percent_tts(match):
            num = match.group(1).replace('%', '')
            if '.' in num:
                whole, decimal = num.split('.')
                return f"{whole} point {decimal} percent"
            return f"{num} percent"

        text = re.sub(r'(\d+\.?\d*)%', convert_percent_tts, text)
    # Subtitle mode: preserve % symbol as-is

    # Handle emphasized text: THIRTY. THOUSAND! -> thirty thousand
    text = re.sub(r'\b([A-Z]+)\.\s*([A-Z]+)!?', r'\1 \2', text)  # THIRTY. THOUSAND! -> THIRTY THOUSAND
    text = re.sub(r'\b([A-Z]+)!\s*([A-Z]+)!?', r'\1 \2', text)  # THIRTY! THOUSAND! -> THIRTY THOUSAND
    text = re.sub(r'\b[A-Z]{2,}\b', lambda m: m.group().lower(), text)  # Convert ALL CAPS to lowercase

    # Handle common abbreviations for better TTS pronunciation
    text = re.sub(r'\bQ(\d)\b', r'quarter \1', text, flags=re.IGNORECASE)  # Q2 -> quarter 2
    text = re.sub(r'\bUSA\b', 'United States', text, flags=re.IGNORECASE)
    text = re.sub(r'\bUK\b', 'United Kingdom', text, flags=re.IGNORECASE)
    text = re.sub(r'\bCEO\b', 'C E O', text, flags=re.IGNORECASE)
    text = re.sub(r'\bFBI\b', 'F B I', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNASA\b', 'N A S A', text, flags=re.IGNORECASE)

    # Step 4: Simplify punctuation for natural speech
    text = re.sub(r'[—–]', ' - ', text)  # Em/en dashes to simple dash
    text = re.sub(r'[?!]{2,}', '!', text)  # Multiple ?! to single !

    # Handle ellipsis carefully to avoid spacing issues
    text = re.sub(r'\.{3,}', ' ELLIPSIS_PLACEHOLDER ', text)  # Protect ellipsis temporarily
    text = re.sub(r'\.{2}', '.', text)  # Double dots to single period

    # Handle other common symbols based on mode
    if mode == "tts":
        text = re.sub(r'&', ' and ', text)  # & -> and for TTS
    # Subtitle mode: preserve & symbol as-is

    # Improve spacing around punctuation based on mode
    if mode == "tts":
        # TTS mode: normalize spacing for natural speech
        text = re.sub(r'\s*([.!?])\s*', r'\1 ', text)  # Normalize spacing after punctuation
        text = re.sub(r'\s*([,;:])\s*', r'\1 ', text)  # Normalize spacing after commas, semicolons, colons
    else:
        # Subtitle mode: preserve tight formatting for numbers and currency
        text = re.sub(r'\s*([!?])\s*', r'\1 ', text)  # Only normalize spacing after ! and ?
        text = re.sub(r'\s*([;:])\s*', r'\1 ', text)  # Normalize spacing after semicolons and colons
        # Don't normalize periods and commas to preserve number/currency formatting

    # Step 5: Remove emojis
    text = emoji.replace_emoji(text, replace='')

    # Step 6: Fix apostrophe encoding (but contractions are already protected)
    text = re.sub(r'[''`´]', "'", text)  # Replace smart apostrophes with standard ASCII

    # Step 7: Clean up whitespace and remove non-ASCII characters (preserve placeholders)
    text = re.sub(r'[^\x00-\x7F\'\"_]+', ' ', text)  # Keep apostrophes, quotes, and underscores for placeholders
    text = re.sub(r'\s+', ' ', text).strip()

    # Step 8: Restore protected contractions and ellipsis
    for placeholder, original in contraction_placeholders.items():
        text = text.replace(placeholder, original)

    # Restore ellipsis (handle both with and without spaces)
    text = text.replace(' ELLIPSIS_PLACEHOLDER ', '...')
    text = text.replace('ELLIPSIS_PLACEHOLDER', '...')

    # Step 9: Only fix genuinely broken contractions (not already correct ones)
    # This step only applies to contractions that were actually broken, not existing ones
    broken_contraction_fixes = {
        r'\b(\w+) s\b(?=\s|$)': lambda m: f"{m.group(1)}'s" if m.group(1).lower() in ['that', 'it', 'let', 'there', 'here', 'what', 'who', 'he', 'she'] else m.group(0),
        r'\b(\w+) ll\b(?=\s|$)': lambda m: f"{m.group(1)}'ll" if m.group(1).lower() in ['i', 'you', 'he', 'she', 'it', 'we', 'they'] else m.group(0),
        r'\b(\w+) re\b(?=\s|$)': lambda m: f"{m.group(1)}'re" if m.group(1).lower() in ['you', 'we', 'they'] else m.group(0),
        r'\b(\w+) ve\b(?=\s|$)': lambda m: f"{m.group(1)}'ve" if m.group(1).lower() in ['i', 'you', 'we', 'they'] else m.group(0),
        r'\b(\w+) d\b(?=\s|$)': lambda m: f"{m.group(1)}'d" if m.group(1).lower() in ['i', 'you', 'he', 'she', 'it', 'we', 'they'] else m.group(0),
        r'\b(\w+) m\b(?=\s|$)': lambda m: f"{m.group(1)}'m" if m.group(1).lower() == 'i' else m.group(0),
        r'\b(\w+) t\b(?=\s|$)': lambda m: f"{m.group(1)}'t" if m.group(1).lower() in ['don', 'can', 'won', 'shouldn', 'wouldn', 'couldn', 'isn', 'aren', 'wasn', 'weren'] else m.group(0)
    }

    for pattern, replacement_func in broken_contraction_fixes.items():
        text = re.sub(pattern, replacement_func, text, flags=re.IGNORECASE)

    # Final cleanup
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def normalize_text_for_subtitles(text):
    """
    Normalize text specifically for subtitle display.
    Preserves visual formatting (currency symbols, percentages, commas in numbers)
    while cleaning up for readability and maintaining synchronization with TTS.

    Args:
        text: Raw text input

    Returns:
        str: Clean text optimized for subtitle display
    """
    return normalize_text_for_natural_speech(text, mode="subtitle")


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


def process_text_for_speech_recognition(text):
    """
    Enhanced text preprocessing specifically for better speech recognition results.
    Handles formatted text with paragraphs, varied sentence structures, and natural speech patterns.

    Args:
        text: Raw text input (may contain paragraphs, varied formatting)

    Returns:
        str: Processed text optimized for TTS and speech recognition
    """
    if not text:
        return ""

    # Step 1: Start processing

    # Step 2: Handle paragraph breaks and line endings
    # Convert multiple line breaks to natural speech pauses
    text = re.sub(r'\n\s*\n+', '. ', text)  # Double line breaks become sentence breaks
    text = re.sub(r'\n+', ' ', text)  # Single line breaks become spaces

    # Step 3: Remove emojis but preserve emotional context
    text = emoji.replace_emoji(text, replace='')

    # Step 4: Fix apostrophe encoding issues while preserving contractions and possessives
    # Replace various apostrophe characters with standard ASCII apostrophe
    text = re.sub(r'[’`´]', "'", text)  # Replace smart apostrophes with standard ASCII
    # REMOVED: The problematic regex that was breaking contractions
    # The overly broad pattern r'\b(\w+) s\b(?!\w)' was incorrectly matching contractions
    # Contractions should be preserved, not reconstructed from broken parts

    # Step 5: Normalize quotation marks for speech
    text = re.sub(r'["""]', '"', text)

    # Step 6: Remove non-ASCII characters EXCEPT standard apostrophes and quotes
    # This preserves contractions and possessives while removing problematic characters
    text = re.sub(r'[^\x00-\x7F\'\"]+', ' ', text)

    # Step 7: Fix broken contractions that may have been created by encoding issues
    # This repairs cases where apostrophes were lost, creating "It s" instead of "It's"
    broken_contractions = {
        r'\bIt s\b': "It's",
        r'\bit s\b': "it's",
        r'\bThat s\b': "That's",
        r'\bthat s\b': "that's",
        r'\bLet s\b': "Let's",
        r'\blet s\b': "let's",
        r'\bI ll\b': "I'll",
        r'\bI m\b': "I'm",
        r'\bI ve\b': "I've",
        r'\bI d\b': "I'd",
        r'\bWe re\b': "We're",
        r'\bwe re\b': "we're",
        r'\bThey re\b': "They're",
        r'\bthey re\b': "they're",
        r'\bYou re\b': "You're",
        r'\byou re\b': "you're",
        r'\bHe s\b': "He's",
        r'\bhe s\b': "he's",
        r'\bShe s\b': "She's",
        r'\bshe s\b': "she's",
        r'\bThere s\b': "There's",
        r'\bthere s\b': "there's",
        r'\bHere s\b': "Here's",
        r'\bhere s\b': "here's",
        r'\bWhat s\b': "What's",
        r'\bwhat s\b': "what's",
        r'\bWhere s\b': "Where's",
        r'\bwhere s\b': "where's",
        r'\bHow s\b': "How's",
        r'\bhow s\b': "how's",
        r'\bWho s\b': "Who's",
        r'\bwho s\b': "who's",
        r'\bWhen s\b': "When's",
        r'\bwhen s\b': "when's"
    }

    for pattern, fixed_contraction in broken_contractions.items():
        text = re.sub(pattern, fixed_contraction, text)

    # Step 8: Improve sentence flow for speech
    # The text already has good natural pauses, so we'll skip aggressive comma insertion

    # Step 9: Handle punctuation for better speech flow
    # Ensure proper spacing around punctuation
    text = re.sub(r'\s*([.!?])\s*', r'\1 ', text)
    text = re.sub(r'\s*([,;:])\s*', r'\1 ', text)

    # Step 10: Handle special cases for better pronunciation
    # Convert em dashes to commas for better speech flow
    text = re.sub(r'\s*—\s*', ', ', text)
    text = re.sub(r'\s*–\s*', ', ', text)

    # Step 11: Clean up excessive punctuation
    # Remove multiple consecutive punctuation marks
    text = re.sub(r'([.!?]){2,}', r'\1', text)
    text = re.sub(r'([,;:]){2,}', r'\1', text)

    # Step 12: Ensure proper sentence endings
    # Make sure sentences end with proper punctuation
    sentences = re.split(r'([.!?])', text)
    processed_sentences = []

    for i in range(0, len(sentences), 2):
        if i < len(sentences):
            sentence = sentences[i].strip()
            if sentence:
                # Add punctuation if missing
                if i + 1 < len(sentences):
                    punct = sentences[i + 1]
                else:
                    punct = '.' if not re.search(r'[.!?]$', sentence) else ''

                processed_sentences.append(sentence + punct)

    text = ' '.join(processed_sentences)

    # Step 13: Final cleanup
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove leading/trailing punctuation artifacts
    text = re.sub(r'^[,;:\-\s]+', '', text)
    text = re.sub(r'[,;:\-\s]+$', '', text)

    # Ensure text ends with proper punctuation
    if text and not re.search(r'[.!?]$', text):
        text += '.'

    return text