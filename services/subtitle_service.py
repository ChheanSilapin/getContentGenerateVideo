"""
Subtitle service for generating subtitles with modern styling
"""
import os
import sys
import traceback
import re
import emoji
from moviepy.editor import VideoFileClip, AudioFileClip
import time

# Import from utils
from utils.helpers import ensure_directory_exists, process_text_for_tts

# Import config
try:
    from config import DEFAULT_MAX_CHARS_PER_LINE
except ImportError:
    # Default value if config.py is not available
    DEFAULT_MAX_CHARS_PER_LINE = 56

# Try to import pydub for audio analysis
try:
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("pydub not available. Will use simple timing for subtitles.")

# Modern subtitle style presets
SUBTITLE_STYLES = {
    "modern_glow": {
        "name": "Modern Glow",
        "description": "White text with blue glow effect",
        "font": "Arial Black",
        "size": 48,
        "primary_color": "&H00FFFFFF",  # White
        "outline_color": "&H00FF8000",  # Blue glow
        "outline_width": 3,
        "shadow": 2,
        "bold": True,
        "alignment": 2,  # Bottom center
        "margin_v": 80
    },
    "neon_pink": {
        "name": "Neon Pink",
        "description": "Hot pink neon style with glow",
        "font": "Impact",
        "size": 52,
        "primary_color": "&H00FF00FF",  # Hot pink
        "outline_color": "&H00800080",  # Dark pink outline
        "outline_width": 4,
        "shadow": 3,
        "bold": True,
        "alignment": 2,
        "margin_v": 100
    },
    "gradient_gold": {
        "name": "Gradient Gold",
        "description": "Gold gradient with black shadow",
        "font": "Arial Black",
        "size": 46,
        "primary_color": "&H0000D7FF",  # Gold
        "secondary_color": "&H000080FF",  # Orange
        "outline_color": "&H00000000",  # Black
        "outline_width": 2,
        "shadow": 2,
        "bold": True,
        "alignment": 2,
        "margin_v": 90
    },
    "cyberpunk": {
        "name": "Cyberpunk",
        "description": "Cyan with electric effects",
        "font": "Consolas",
        "size": 44,
        "primary_color": "&H00FFFF00",  # Cyan
        "outline_color": "&H00FF0080",  # Purple outline
        "outline_width": 3,
        "shadow": 1,
        "bold": True,
        "alignment": 8,  # Top center
        "margin_v": 150
    },
    "classic_movie": {
        "name": "Classic Movie",
        "description": "Yellow text with black background",
        "font": "Times New Roman",
        "size": 42,
        "primary_color": "&H0000FFFF",  # Yellow
        "back_color": "&H80000000",  # Semi-transparent black
        "outline_color": "&H00000000",  # Black outline
        "outline_width": 1,
        "shadow": 0,
        "bold": False,
        "alignment": 2,
        "margin_v": 60
    },
    "fire_red": {
        "name": "Fire Red",
        "description": "Red to orange gradient with glow",
        "font": "Arial Black",
        "size": 50,
        "primary_color": "&H000000FF",  # Red
        "secondary_color": "&H000080FF",  # Orange
        "outline_color": "&H00000080",  # Dark red
        "outline_width": 3,
        "shadow": 2,
        "bold": True,
        "alignment": 2,
        "margin_v": 85
    },
    "ice_blue": {
        "name": "Ice Blue",
        "description": "Light blue with white glow",
        "font": "Arial",
        "size": 45,
        "primary_color": "&H00FFFF80",  # Light blue
        "outline_color": "&H00FFFFFF",  # White glow
        "outline_width": 2,
        "shadow": 1,
        "bold": True,
        "alignment": 2,
        "margin_v": 75
    },
    "retro_wave": {
        "name": "Retro Wave",
        "description": "Purple and pink 80s style",
        "font": "Impact",
        "size": 48,
        "primary_color": "&H00FF80FF",  # Pink
        "outline_color": "&H00800080",  # Purple
        "outline_width": 4,
        "shadow": 2,
        "bold": True,
        "alignment": 2,
        "margin_v": 95
    }
}

# ASS Header for subtitle files
ASS_HEADER = """[Script Info]
Title: Modern Styled Subtitle
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
Timer: 100.0000
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,42,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def get_available_styles():
    """Get list of available subtitle styles"""
    return list(SUBTITLE_STYLES.keys())

def generate_subtitles(text, video_file, audio_file, output_file, style="modern_glow"):
    """
    Generate subtitles for a video with modern styling
    
    Args:
        text: Text content for subtitles
        video_file: Path to video file
        audio_file: Path to audio file
        output_file: Path to output subtitle file
        style: Subtitle style preset (default: "modern_glow")
    """
    try:
        # Clean the text BEFORE saving it to file - THIS IS THE KEY FIX
        cleaned_text = process_text_for_subtitles(text)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir:
            ensure_directory_exists(output_dir)

        # Save the CLEANED text to a file that process_local_video will read
        text_file = f"{audio_file}.txt"
        try:
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(cleaned_text)  # Save cleaned text, not original
            print(f"Created text file for subtitles with cleaned text: {text_file}")
            
            # DEBUG: Show exact content being saved
            print(f"DEBUG: Text file content: '{cleaned_text}'")
            if "150" in cleaned_text:
                print("⚠️  DEBUG WARNING: Found '150' in text file content!")
                
        except Exception as e:
            print(f"Error creating text file: {e}")
            return False

        # Generate subtitles with specified style
        print(f"Generating subtitles for video: {video_file}")
        result = process_local_video(
            video_path=video_file,
            output_type="ass",
            maxChar=DEFAULT_MAX_CHARS_PER_LINE,
            output_file=output_file,
            audio_file=audio_file,
            style=style
        )
        
        return result is not None
    except Exception as e:
        print(f"Error generating subtitles: {e}")
        traceback.print_exc()
        return False

def process_text_for_subtitles(text):
    """
    Enhanced text processing that removes numbered lists and preserves important content
    
    Args:
        text: Text to process
        
    Returns:
        str: Processed text with preserved important content and removed numbering
    """
    
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

def process_local_video(video_path, output_type="ass", maxChar=40, output_file="subtitles.ass", audio_file=None, style="modern_glow"):
    """
    Generate subtitles for a video with modern styling

    Args:
        video_path: Path to video file
        output_type: Type of subtitle file to create (currently only 'ass' is supported)
        maxChar: Maximum characters per line
        output_file: Path to output subtitle file
        audio_file: Path to audio file (if different from video's audio)
        style: Subtitle style preset

    Returns:
        str: Path to subtitle file if successful, None otherwise
    """
    print(f"Generating subtitles for video: {os.path.basename(video_path)} with style: {style}")
    output_dir = os.path.dirname(output_file)
    if output_dir:
        ensure_directory_exists(output_dir)

    # Get style configuration
    style_config = SUBTITLE_STYLES.get(style, SUBTITLE_STYLES["modern_glow"])
    print(f"Using style configuration: {style_config['name']}")

    subtitle_path = output_file
    try:
        with open(subtitle_path, "w", encoding="utf-8") as f:
            # Enhanced script info for better quality
            f.write("[Script Info]\n")
            f.write("Title: Modern Styled Subtitle\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 720\n")
            f.write("PlayResY: 1280\n")
            f.write("Timer: 100.0000\n")
            f.write("WrapStyle: 0\n\n")
            
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")

            # Create the main style based on configuration
            font = style_config.get("font", "Arial")
            size = style_config.get("size", 42)
            primary = style_config.get("primary_color", "&H00FFFFFF")
            secondary = style_config.get("secondary_color", "&H000000FF")
            outline = style_config.get("outline_color", "&H00000000")
            back = style_config.get("back_color", "&H00000000")
            bold = 1 if style_config.get("bold", True) else 0
            outline_width = style_config.get("outline_width", 2)
            shadow = style_config.get("shadow", 0)
            alignment = style_config.get("alignment", 2)
            margin_v = style_config.get("margin_v", 80)

            # Main style
            f.write(f"Style: Default,{font},{size},{primary},{secondary},{outline},{back},{bold},0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},10,10,{margin_v},1\n")
            
            # Highlight style (for current word) - brighter version
            highlight_primary = primary.replace("&H00", "&H00").replace("FF", "FF")  # Keep same but could modify
            f.write(f"Style: Highlight,{font},{size + 4},{highlight_primary},{secondary},{outline},{back},{bold},0,0,0,110,110,0,0,1,{outline_width + 1},{shadow + 1},{alignment},10,10,{margin_v},1\n")
            
            # Fade in style for animations
            f.write(f"Style: FadeIn,{font},{size},{primary},{secondary},{outline},{back},{bold},0,0,0,80,80,0,0,1,{outline_width},{shadow},{alignment},10,10,{margin_v},1\n")
            
            # Create additional effect styles
            _create_effect_styles(f, style_config)
            
            f.write("\n[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    except Exception as e:
        print(f"Error creating subtitle file structure: {e}")
        return None

    try:
        # Load video and audio files
        if not os.path.exists(video_path):
            print(f"ERROR: Video file not found: {video_path}")
            raise FileNotFoundError(f"Video file not found: {video_path}")
        video = VideoFileClip(video_path)
        
        if audio_file is None:
            video_dir = os.path.dirname(video_path)
            audio_file = os.path.join(video_dir, "voice.mp3")
        if not os.path.exists(audio_file):
            print(f"ERROR: Audio file not found: {audio_file}")
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        audio = AudioFileClip(audio_file)
        
        # Load text content
        text_file = f"{audio_file}.txt"
        if not os.path.exists(text_file):
            print(f"ERROR: Text file not found: {text_file}")
            try:
                parent_dir = os.path.basename(os.path.dirname(audio_file))
                if "video_" in parent_dir:
                    default_text = "This video was generated automatically. Please enjoy the content."
                else:
                    default_text = "Default subtitle text created automatically."

                with open(text_file, "w", encoding="utf-8") as f:
                    f.write(default_text)
                print(f"Created default text file: {text_file}")
            except Exception as text_write_error:
                print(f"Failed to create default text file: {text_write_error}")
                raise FileNotFoundError(f"Text file not found and could not create default: {text_file}")
        
        with open(text_file, "r", encoding="utf-8") as text_file_handle:
            text = text_file_handle.read().strip()
        if not text:
            print("WARNING: Text file is empty, using default text")
            text = "Default subtitle text because original file was empty."
        
        # DEBUG: Show what we read from the text file
        print(f"DEBUG: Read from text file '{text_file}': '{text}'")
        if "150" in text:
            print("⚠️  DEBUG WARNING: Found '150' in text read from file!")
        
        text = process_text_for_subtitles(text)
        # Keep original case for better readability (remove uppercase conversion)
        # text = text.upper()  # Commented out for better readability

        # Additional text cleaning for subtitles
        print(f"Original text: '{text}'")
        
        # Remove any remaining problematic patterns
        text = re.sub(r'^\W+', '', text)  # Remove leading non-word characters
        text = re.sub(r'\W+$', '', text)  # Remove trailing non-word characters
        
        # Ensure we have clean text
        if not text or len(text.strip()) == 0:
            text = "Welcome to this video"
            print("Using fallback text due to empty or invalid input")
        
        print(f"Cleaned text for subtitles: '{text}'")

        # Split text into words - PRESERVE IMPORTANT CONTENT
        words = [word.strip() for word in text.split() if word.strip() and len(word.strip()) > 0]
        
        # ENHANCED: Preserve numbers, currency, contractions, and important content
        filtered_words = []
        for word in words:
            clean_word = word.strip()
            
            # Keep currency amounts like $17,190
            if re.match(r'\$[\d,]+(?:\.\d{2})?', clean_word):
                filtered_words.append(clean_word)
                continue
            
            # Keep years like 2025, 2026
            if re.match(r'\b(19|20)\d{2}\b', clean_word):
                filtered_words.append(clean_word)
                continue
            
            # Keep contractions like country's, Trump's, etc.
            if re.match(r"\w+[''](?:s|ll|ve|re|t|d|m)\b", clean_word, re.IGNORECASE):
                filtered_words.append(clean_word)
                continue
            
            # Keep words with numbers that are meaningful (like model names)
            if re.search(r'[a-zA-Z]', clean_word) and len(clean_word) > 1:
                # Only remove standalone numbers, not mixed content
                if not re.match(r'^\d+$', clean_word):  # Don't remove if it's ONLY numbers
                    # Clean but preserve structure
                    clean_word = re.sub(r'^[^\w$]+|[^\w$]+$', '', clean_word)
                    if clean_word:
                        filtered_words.append(clean_word)

        words = filtered_words
        
        if not words:
            words = ["Welcome", "to", "this", "video"]
            print("Using fallback words due to no valid words found")
        
        print(f"Processing {len(words)} words for subtitles (preserved currency, years, contractions)")

        # Create optimized word groups for better readability
        word_groups = create_optimized_word_groups(text)
        print(f"Created {len(word_groups)} optimized subtitle groups")

        # Calculate timing for word groups instead of individual words
        group_timings = _calculate_optimized_timing(audio_file, word_groups, audio.duration)

        # Generate subtitle events with word groups
        subtitle_events = _generate_group_subtitle_events(word_groups, group_timings, style_config)
        
        # Write events to file
        with open(subtitle_path, "a", encoding="utf-8") as f:
            for event in subtitle_events:
                line = f"Dialogue: 0,{_seconds_to_ass_time(event['start'])},{_seconds_to_ass_time(event['end'])},Default,,0,0,0,,{event['text']}\n"
                f.write(line)

        print(f"Successfully created modern styled subtitles: {style_config['name']}")
        return subtitle_path
        
    except Exception as e:
        print(f"ERROR in subtitle generation: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        return _create_fallback_subtitle(subtitle_path, str(e))

def _create_effect_styles(f, style_config):
    """Create additional effect styles for animations"""
    font = style_config.get("font", "Arial")
    size = style_config.get("size", 42)
    primary = style_config.get("primary_color", "&H00FFFFFF")
    secondary = style_config.get("secondary_color", "&H000000FF")
    outline = style_config.get("outline_color", "&H00000000")
    back = style_config.get("back_color", "&H00000000")
    bold = 1 if style_config.get("bold", True) else 0
    outline_width = style_config.get("outline_width", 2)
    shadow = style_config.get("shadow", 0)
    alignment = style_config.get("alignment", 2)
    margin_v = style_config.get("margin_v", 80)
    
    # Glow effect style
    glow_outline = primary  # Use primary color for glow
    f.write(f"Style: Glow,{font},{size + 2},{primary},{secondary},{glow_outline},{back},{bold},0,0,0,105,105,0,0,1,{outline_width + 2},{shadow + 2},{alignment},10,10,{margin_v},1\n")
    
    # Pop effect style (larger)
    f.write(f"Style: Pop,{font},{size + 8},{primary},{secondary},{outline},{back},{bold},0,0,0,120,120,0,0,1,{outline_width + 1},{shadow + 1},{alignment},10,10,{margin_v},1\n")

def _calculate_word_timings(audio_file, words, total_duration):
    """Calculate sophisticated word timings using audio analysis"""
    word_timings = []
    
    if PYDUB_AVAILABLE:
        try:
            print("Starting audio analysis for word timing...")
            audio_segment = AudioSegment.from_file(audio_file)
            non_silent_ranges = detect_nonsilent(
                audio_segment,
                min_silence_len=100,  # More sensitive
                silence_thresh=-30    # More sensitive
            )

            if non_silent_ranges:
                print(f"Found {len(non_silent_ranges)} non-silent ranges for {len(words)} words")
                offset_ms = 50  # Smaller offset for better sync
                
                # Distribute words across speech segments
                segment_durations = [end - start for start, end in non_silent_ranges]
                total_speech_duration = sum(segment_durations)
                
                words_per_segment = []
                for dur in segment_durations:
                    words_in_segment = max(1, round(len(words) * dur / total_speech_duration))
                    words_per_segment.append(words_in_segment)
                
                # Adjust to match total word count with safety counter
                adjustment_count = 0
                max_adjustments = len(words) * 2  # Safety limit
                
                while sum(words_per_segment) != len(words) and adjustment_count < max_adjustments:
                    adjustment_count += 1
                    
                    if sum(words_per_segment) > len(words):
                        # Find segment with most words and reduce by 1
                        max_idx = words_per_segment.index(max(words_per_segment))
                        if words_per_segment[max_idx] > 1:
                            words_per_segment[max_idx] -= 1
                    else:
                        # Find segment with longest duration and add 1 word
                        max_idx = segment_durations.index(max(segment_durations))
                        words_per_segment[max_idx] += 1
                
                # If we couldn't balance perfectly, use simple distribution
                if sum(words_per_segment) != len(words):
                    print(f"Warning: Could not perfectly distribute words. Using simple fallback.")
                    print("Using simple timing fallback")
                    word_duration = total_duration / len(words) if words else 1.0
                    overlap = word_duration * 0.15  # 15% overlap
                    
                    for i in range(len(words)):
                        word_start = max(0, i * word_duration - overlap)
                        word_end = (i + 1) * word_duration + overlap
                        word_timings.append((word_start, word_end))
                    
                    return word_timings

                # Create timings
                print("Creating word timings from audio analysis...")
                word_idx = 0
                for i, (start_ms, end_ms) in enumerate(non_silent_ranges):
                    segment_word_count = words_per_segment[i]
                    segment_duration_ms = end_ms - start_ms

                    for j in range(segment_word_count):
                        if word_idx < len(words):
                            word_start = max(0, start_ms - offset_ms) + (j * segment_duration_ms / segment_word_count)
                            word_end = start_ms + ((j + 1) * segment_duration_ms / segment_word_count) + offset_ms
                            word_timings.append((word_start / 1000, word_end / 1000))
                            word_idx += 1

                print(f"Using advanced audio analysis: {len(word_timings)} timings for {len(words)} words")
                return word_timings
                
        except Exception as e:
            print(f"Audio analysis failed: {e}")
    
    # Fallback to simple timing
    print("Using simple timing fallback")
    word_duration = total_duration / len(words) if words else 1.0
    overlap = word_duration * 0.15  # 15% overlap
    
    for i in range(len(words)):
        word_start = max(0, i * word_duration - overlap)
        word_end = (i + 1) * word_duration + overlap
        word_timings.append((word_start, word_end))
    
    return word_timings

def _generate_group_subtitle_events(word_groups, group_timings, style_config):
    """Generate subtitle events for word groups with preserved content"""
    
    print(f"Generating subtitle events for {len(word_groups)} groups...")
    
    subtitle_events = []
    
    for i, group in enumerate(word_groups):
        
        # Progress indicator every 10 groups
        if i % 10 == 0:
            print(f"Processing group {i+1}/{len(word_groups)}: '{group['text'][:50]}...'")
        
        if i < len(group_timings):
            group_start, group_end = group_timings[i]
            
            # Use the original group text - DON'T remove important content
            clean_text = group['text'].strip()
            
            # Only remove clearly problematic characters, preserve currency, years, contractions
            # Remove only leading/trailing non-essential punctuation
            clean_text = re.sub(r'^[,\.\)\]\}]+\s*', '', clean_text)
            clean_text = re.sub(r'\s*[,\.\(\[\{]+$', '', clean_text)
            
            # Skip empty groups
            if not clean_text:
                continue
            
            # Escape special characters for ASS format but preserve content
            safe_text = clean_text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
            
            # DEBUG: Check for "150" in subtitle text
            if "150" in safe_text:
                print(f"⚠️  DEBUG WARNING: Found '150' in subtitle text for group {i+1}: '{safe_text}'")
            
            # Choose style based on content
            style_name = "Default"
            effect = ""
            
            # Add emphasis for important content
            text_lower = clean_text.lower()
            if any(keyword in text_lower for keyword in ['$', 'trump', 'tariffs', 'nissan']):
                style_name = "Highlight"
                effect = ""  # Use no effect to avoid display issues
            
            # Add subtitle event with numeric times (NOT formatted strings)
            subtitle_events.append({
                'text': safe_text,
                'start': group_start,  # Keep as numeric seconds
                'end': group_end,      # Keep as numeric seconds
                'style': style_name,
                'effect': effect
            })
    
    print(f"Completed generating {len(word_groups)} subtitle events with preserved content")
    return subtitle_events

def _format_time(seconds):
    """Format time in H:MM:SS.ms format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"

def _get_word_effect(word_index, total_words):
    """Get animation effect for word based on its position"""
    effects = [
        "",  # No effect
        "\\fad(200,200)",  # Fade in/out
        "\\t(\\fscx120\\fscy120)",  # Scale up
        "\\move(360,640,360,600)",  # Slight upward movement
        "\\t(0,300,\\3c&H00FF00&)",  # Color transition
    ]
    
    # Use different effects for different parts of the text
    if word_index < total_words * 0.2:  # First 20%
        return "\\fad(300,100)"  # Fade in
    elif word_index > total_words * 0.8:  # Last 20%
        return "\\fad(100,300)"  # Fade out
    else:
        return effects[word_index % len(effects)]

def _choose_word_style(word, index):
    """Choose style based on word characteristics"""
    # Highlight important words
    important_words = ["amazing", "incredible", "wow", "fantastic", "awesome", "great", "best", "perfect"]
    
    if any(imp_word in word.lower() for imp_word in important_words):
        return "Glow"
    elif index % 10 == 0:  # Every 10th word gets pop effect
        return "Pop"
    elif len(word) > 8:  # Long words get highlight
        return "Highlight"
    else:
        return "Default"

def _create_fallback_subtitle(subtitle_path, error_msg):
    """Create a fallback subtitle file with error information"""
    try:
        with open(subtitle_path, "w", encoding="utf-8") as f:
            f.write("[Script Info]\nTitle: Error Subtitle\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\n\n")
            f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write("Style: Default,Arial,32,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,80,1\n\n")
            f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            f.write(f"Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Error: {error_msg[:50]}...\n")
            f.write(f"Dialogue: 0,0:00:05.00,0:00:10.00,Default,,0,0,0,,Please check the console for details.\n")
            f.write(f"Dialogue: 0,0:00:10.00,0:05:00.00,Default,,0,0,0,,This is a fallback subtitle.\n")
        print(f"Created fallback subtitle file: {subtitle_path}")
        return subtitle_path
    except Exception as fallback_error:
        print(f"Failed to create fallback subtitle file: {fallback_error}")
        return None

def create_optimized_word_groups(text):
    """
    ENHANCED: Create optimized word groups with adaptive sizing based on text length
    """
    if not text or not text.strip():
        return []
    
    print("Creating optimized word groups...")
    
    # Clean and split words
    words = text.strip().split()
    total_words = len(words)
    
    if total_words == 0:
        return []
    
    print(f"Processing {total_words} words")
    
    # PERFORMANCE OPTIMIZATION: Adaptive group sizing based on text length
    if total_words > 200:  # Very long text - use larger groups for speed
        words_per_group = 3
        print("Using large groups (3 words) for long text - optimizing for speed")
    elif total_words > 100:  # Medium text - balanced approach
        words_per_group = 2  
        print("Using medium groups (2 words) for medium text")
    else:  # Short text - smaller groups for precision
        words_per_group = 2
        print("Using standard groups (2 words) for short text")
    
    word_groups = []
    
    # OPTIMIZED: Process in batches for better memory usage
    for i in range(0, total_words, words_per_group):
        group_words = words[i:i + words_per_group]
        group_text = ' '.join(group_words)
        
        # Quick calculations without complex analysis for speed
        word_count = len(group_words)
        char_count = len(group_text)
        
        word_groups.append({
            'text': group_text,
            'word_count': word_count,
            'char_count': char_count,
            'start_index': i,
            'end_index': min(i + words_per_group - 1, total_words - 1)
        })
    
    print(f"✅ Created {len(word_groups)} optimized groups")
    return word_groups

def _calculate_optimized_timing(audio_file, word_groups, total_duration):
    """
    OPTIMIZED: Calculate faster timing for word groups with special handling for long audio
    """
    group_timings = []
    
    print("Using optimized fast timing calculation...")
    
    total_groups = len(word_groups)
    if total_groups == 0:
        return group_timings
    
    # PERFORMANCE OPTIMIZATION: Use ultra-fast timing for long audio
    if total_duration > 10.0:  # For audio longer than 10 seconds
        print(f"Long audio detected ({total_duration:.1f}s) - using ultra-fast timing mode")
        
        # Ultra-simplified timing for performance
        avg_duration_per_group = total_duration / total_groups
        overlap = 0.05  # Minimal overlap for speed
        
        for i, group in enumerate(word_groups):
            group_start = max(0, i * avg_duration_per_group - overlap)
            group_end = (i + 1) * avg_duration_per_group + overlap
            
            # Clamp to total duration
            group_end = min(group_end, total_duration)
            
            group_timings.append((group_start, group_end))
        
        print(f"Ultra-fast timing completed for {total_groups} groups in long audio")
        return group_timings
    
    # Standard timing for shorter audio (< 10 seconds)
    reading_speed_wpm = 200  # Increased from 180 for faster pace
    current_time = 0
    
    for i, group in enumerate(word_groups):
        word_count = group['word_count']
        char_count = group['char_count']
        
        # Simplified duration calculation for speed
        base_duration = (word_count / reading_speed_wpm) * 60
        
        # Quick adjustments
        if '$' in group['text']:
            base_duration *= 1.1  # Slight pause for currency
        if group['text'].endswith(('.', '!', '?')):
            base_duration *= 1.05  # Brief pause for sentences
        
        # Minimum duration for readability
        group_duration = max(base_duration, 0.8)  # Reduced minimum from 1.0
        
        # Reduced overlap for faster pace
        overlap = 0.1  # Reduced from 0.2
        group_start = max(0, current_time - overlap)
        group_end = current_time + group_duration + overlap
        
        group_timings.append((group_start, group_end))
        current_time += group_duration * 0.95  # 5% overlap
    
    return group_timings

def _analyze_speech_timing(audio_file, word_groups, total_duration):
    """
    ENHANCED: Analyze audio to detect speech segments for better text-speech sync
    """
    try:
        from pydub import AudioSegment
        from pydub.silence import detect_nonsilent
        
        print("Analyzing audio for speech pattern synchronization...")
        
        # Load audio
        audio = AudioSegment.from_file(audio_file)
        
        # Detect speech segments (non-silent parts)
        # Adjusted for better speech detection
        non_silent_segments = detect_nonsilent(
            audio,
            min_silence_len=200,  # 200ms of silence
            silence_thresh=audio.dBFS - 14  # Threshold for silence
        )
        
        if not non_silent_segments:
            print("No speech segments detected, using fallback timing")
            return None
        
        print(f"Detected {len(non_silent_segments)} speech segments")
        
        # Convert to seconds and create timing map
        speech_segments = []
        for start_ms, end_ms in non_silent_segments:
            start_sec = start_ms / 1000.0
            end_sec = end_ms / 1000.0
            speech_segments.append((start_sec, end_sec))
        
        # Map word groups to speech segments
        group_timings = []
        total_groups = len(word_groups)
        
        # Distribute groups across detected speech segments
        if len(speech_segments) >= total_groups:
            # More speech segments than groups - use best segments
            for i, group in enumerate(word_groups):
                if i < len(speech_segments):
                    start_time, end_time = speech_segments[i]
                    group_timings.append((start_time, end_time))
                else:
                    # Fallback for remaining groups
                    last_end = group_timings[-1][1] if group_timings else 0
                    duration = 2.0  # Default duration
                    group_timings.append((last_end, last_end + duration))
        else:
            # Fewer speech segments than groups - distribute groups across segments
            groups_per_segment = total_groups / len(speech_segments)
            current_group = 0
            
            for segment_start, segment_end in speech_segments:
                segment_duration = segment_end - segment_start
                groups_in_this_segment = min(int(groups_per_segment) + 1, total_groups - current_group)
                
                if groups_in_this_segment <= 0:
                    break
                
                # Distribute groups within this speech segment
                for j in range(groups_in_this_segment):
                    if current_group >= total_groups:
                        break
                    
                    # Calculate position within segment
                    group_start = segment_start + (j * segment_duration / groups_in_this_segment)
                    group_end = segment_start + ((j + 1) * segment_duration / groups_in_this_segment)
                    
                    group_timings.append((group_start, group_end))
                    current_group += 1
        
        print(f"Speech-synced timing created for {len(group_timings)} groups")
        return group_timings
        
    except Exception as e:
        print(f"Speech analysis failed: {e}, using fallback timing")
        return None

def generate_subtitle_events(content, audio_file):
    """
    Generate subtitle events with enhanced speed optimization and speech sync
    """
    print("Starting optimized subtitle generation...")
    
    try:
        # Get audio duration
        duration = _get_audio_duration(audio_file)
        if duration is None or duration <= 0:
            duration = 10.0  # Fallback duration
        
        print(f"Audio duration: {duration:.2f} seconds")
        
        # Clean and process text
        cleaned_content = _enhanced_text_cleaning(content)
        print(f"Original text length: {len(content)}")
        print(f"Cleaned text length: {len(cleaned_content)}")
        
        # Create optimized word groups
        word_groups = create_optimized_word_groups(cleaned_content)
        print(f"Created {len(word_groups)} word groups")
        
        if not word_groups:
            print("WARNING: No word groups created, generating single subtitle")
            return _create_fallback_subtitle(cleaned_content, duration)
        
        # ENHANCED: Try speech analysis first for better sync
        group_timings = None
        if duration <= 15.0:  # Only use speech analysis for reasonable length audio
            group_timings = _analyze_speech_timing(audio_file, word_groups, duration)
        
        # Fallback to optimized timing if speech analysis fails or audio is too long
        if group_timings is None:
            print("Using optimized timing calculation...")
            group_timings = _calculate_optimized_timing(audio_file, word_groups, duration)
        
        # Generate subtitle events
        subtitle_events = _generate_group_subtitle_events(word_groups, group_timings)
        
        print(f"Generated {len(subtitle_events)} subtitle events")
        return subtitle_events
        
    except Exception as e:
        print(f"ERROR in subtitle generation: {e}")
        import traceback
        traceback.print_exc()
        return _create_fallback_subtitle(content, 10.0)

def generate_subtitle_file(content, audio_file, output_dir):
    """
    Generate an optimized .ass subtitle file for given content
    """
    print(f"Generating subtitle file in: {output_dir}")
    
    try:
        # OPTIMIZED: Create unique temporary file names to avoid conflicts
        timestamp = int(time.time() * 1000)  # Millisecond timestamp for uniqueness
        
        subtitle_events = generate_subtitle_events(content, audio_file)
        
        if not subtitle_events:
            print("No subtitle events generated, creating minimal subtitle")
            subtitle_events = [
                {'text': content[:50] + "...", 'start': 0, 'end': 5}
            ]

        # ENHANCED: Use unique temporary file name
        temp_subtitle_file = os.path.join(output_dir, f"subtitles_{timestamp}.ass")
        final_subtitle_file = os.path.join(output_dir, "subtitles.ass")
        
        # Write to temporary file first
        with open(temp_subtitle_file, 'w', encoding='utf-8') as f:
            f.write(ASS_HEADER)
            for event in subtitle_events:
                line = f"Dialogue: 0,{_seconds_to_ass_time(event['start'])},{_seconds_to_ass_time(event['end'])},Default,,0,0,0,,{event['text']}\n"
                f.write(line)
        
        # Atomic move to final location
        import shutil
        shutil.move(temp_subtitle_file, final_subtitle_file)
        
        print(f"✅ Subtitle file generated: {final_subtitle_file}")
        print(f"📊 Generated {len(subtitle_events)} subtitle events")
        return final_subtitle_file
        
    except Exception as e:
        print(f"❌ Error generating subtitle file: {e}")
        import traceback
        traceback.print_exc()
        return None

def _get_audio_duration(audio_file):
    """
    Get duration of audio file in seconds
    
    Args:
        audio_file: Path to audio file
        
    Returns:
        float: Duration in seconds, or None if failed
    """
    try:
        # Try using moviepy first
        from moviepy.editor import AudioFileClip
        with AudioFileClip(audio_file) as audio:
            duration = audio.duration
        print(f"Audio duration: {duration:.2f} seconds")
        return duration
    except Exception as e:
        print(f"Failed to get audio duration with moviepy: {e}")
        
        # Fallback: try pydub
        try:
            if PYDUB_AVAILABLE:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(audio_file)
                duration = len(audio) / 1000.0  # Convert from ms to seconds
                print(f"Audio duration (pydub): {duration:.2f} seconds")
                return duration
        except Exception as e2:
            print(f"Failed to get audio duration with pydub: {e2}")
        
        # Final fallback
        print("Using default audio duration: 10.0 seconds")
        return 10.0

def _enhanced_text_cleaning(content):
    """
    Enhanced text cleaning that preserves important content
    
    Args:
        content: Text content to clean
        
    Returns:
        str: Cleaned text with preserved important elements
    """
    if not content:
        return ""
    
    # Use the existing process_text_for_subtitles function
    return process_text_for_subtitles(content)

def _seconds_to_ass_time(seconds):
    """
    Convert seconds to ASS time format (H:MM:SS.cs)
    
    Args:
        seconds: Time in seconds (float)
        
    Returns:
        str: Time in ASS format
    """
    if seconds < 0:
        seconds = 0
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    # ASS format uses centiseconds (1/100 of a second)
    return f"{hours}:{minutes:02d}:{secs:05.2f}"

def _create_fallback_subtitle(content, duration):
    """
    Create a fallback subtitle event list
    
    Args:
        content: Text content
        duration: Duration in seconds
        
    Returns:
        list: List of subtitle events
    """
    return [
        {
            'text': content[:100] + "..." if len(content) > 100 else content,
            'start': 0,
            'end': min(duration, 10.0)
        }
    ]


