"""
Subtitle service for generating subtitles with modern styling
"""
import os
import sys
import traceback
import re
import emoji
from moviepy.editor import VideoFileClip, AudioFileClip

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
        print(f"\n--- DEBUG: Inside generate_subtitles function ---")
        print(f"Original text: {text}")
        print(f"Video file: {video_file}")
        print(f"Audio file: {audio_file}")
        print(f"Output file: {output_file}")
        print(f"Style: {style}")
        
        # Clean the text BEFORE saving it to file - THIS IS THE KEY FIX
        cleaned_text = process_text_for_subtitles(text)
        print(f"Cleaned text before saving: {cleaned_text}")
        
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
        
        print(f"\n--- DEBUG: process_local_video returned: {result} ---")
        return result is not None
    except Exception as e:
        print(f"Error generating subtitles: {e}")
        traceback.print_exc()
        return False

def process_text_for_subtitles(text):
    """
    Process text by converting number emojis to numbers and removing other emojis

    Args:
        text: Text to process

    Returns:
        str: Processed text
    """
    print(f"DEBUG: Original text input: '{text}'")
    
    # First, handle number emojis
    number_emoji_map = {
        '0️⃣': '0', '1️⃣': '1', '2️⃣': '2', '3️⃣': '3', '4️⃣': '4',
        '5️⃣': '5', '6️⃣': '6', '7️⃣': '7', '8️⃣': '8', '9️⃣': '9'
    }
    for emoji_num, real_num in number_emoji_map.items():
        text = text.replace(emoji_num, real_num)
    
    # Remove all other emojis
    text = emoji.replace_emoji(text, replace='')
    
    # Remove non-ASCII characters that might cause issues
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    # Clean up extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text).strip()
    
    print(f"DEBUG: After emoji and ASCII cleaning: '{text}'")
    
    # More comprehensive cleaning for problematic patterns
    # Remove patterns like "(100)," or "100)," or "(100)" at the beginning
    text = re.sub(r'^\s*\(?\d+\)[,\s]*', '', text)
    
    # Remove any remaining parentheses with numbers that might be causing issues
    text = re.sub(r'\(\d+\)[,\s]*', '', text)
    
    # Remove any standalone numbers followed by closing parenthesis and comma/space
    text = re.sub(r'\b\d+\)[,\s]*', '', text)
    
    # Remove any remaining standalone numbers at the beginning
    text = re.sub(r'^\s*\d+[,\s]*', '', text)
    
    # Clean up any double spaces created by the cleaning
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Ensure the text doesn't start with punctuation
    text = re.sub(r'^[,\.\)\]\}]+\s*', '', text)
    
    # Remove any remaining problematic characters at the start
    text = re.sub(r'^[^\w\s]*', '', text)
    
    print(f"DEBUG: After comprehensive cleaning: '{text}'")

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

        # Split text into words and filter out empty or invalid words
        words = [word.strip() for word in text.split() if word.strip() and len(word.strip()) > 0]
        
        # Enhanced word filtering to remove any numbers
        print(f"DEBUG: Original words before filtering: {words}")
        filtered_words = []
        for word in words:
            # Clean each word individually
            clean_word = word.strip()
            
            print(f"DEBUG: Processing word '{word}' -> '{clean_word}'")
            
            # Remove any numbers that might be contaminating the words
            clean_word = re.sub(r'^\d+', '', clean_word)  # Remove leading numbers
            clean_word = re.sub(r'\d+$', '', clean_word)  # Remove trailing numbers
            clean_word = re.sub(r'\d+', '', clean_word)   # Remove any embedded numbers
            
            # Remove any remaining punctuation except apostrophes and hyphens
            clean_word = re.sub(r'[^\w\s\'-]', '', clean_word)
            
            # Remove any remaining punctuation at start/end
            clean_word = re.sub(r'^[^\w]+|[^\w]+$', '', clean_word)
            
            clean_word = clean_word.strip()
            
            print(f"DEBUG: Word '{word}' -> cleaned to '{clean_word}'")
            
            # Only keep words that have at least one letter and are not empty
            if clean_word and re.search(r'[a-zA-Z]', clean_word) and len(clean_word) > 0:
                filtered_words.append(clean_word)
                print(f"DEBUG: Added word '{clean_word}' to filtered list")
            else:
                print(f"DEBUG: Rejected word '{clean_word}' (empty or no letters)")

        words = filtered_words
        
        if not words:
            words = ["Welcome", "to", "this", "video"]
            print("Using fallback words due to no valid words found")
        
        print(f"Final words for subtitles: {words}")

        # Calculate timing with sophisticated audio analysis
        word_timings = _calculate_word_timings(audio_file, words, audio.duration)

        # Generate subtitle events with modern effects
        _generate_subtitle_events(subtitle_path, words, word_timings, style_config)

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
            audio_segment = AudioSegment.from_file(audio_file)
            non_silent_ranges = detect_nonsilent(
                audio_segment,
                min_silence_len=100,  # More sensitive
                silence_thresh=-30    # More sensitive
            )

            if non_silent_ranges:
                offset_ms = 50  # Smaller offset for better sync
                
                # Distribute words across speech segments
                segment_durations = [end - start for start, end in non_silent_ranges]
                total_speech_duration = sum(segment_durations)
                
                words_per_segment = []
                for dur in segment_durations:
                    words_in_segment = max(1, round(len(words) * dur / total_speech_duration))
                    words_per_segment.append(words_in_segment)
                
                # Adjust to match total word count
                while sum(words_per_segment) != len(words):
                    if sum(words_per_segment) > len(words):
                        max_idx = words_per_segment.index(max(words_per_segment))
                        if words_per_segment[max_idx] > 1:
                            words_per_segment[max_idx] -= 1
                    else:
                        max_idx = segment_durations.index(max(segment_durations))
                        words_per_segment[max_idx] += 1

                # Create timings
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

def _generate_subtitle_events(subtitle_path, words, word_timings, style_config):
    """Generate subtitle events with modern effects and animations"""
    print(f"DEBUG: Starting subtitle event generation with {len(words)} words")
    print(f"DEBUG: Words list: {words}")
    
    with open(subtitle_path, "a", encoding="utf-8") as f:
        for i, word in enumerate(words):
            print(f"DEBUG: Processing word {i}: '{word}'")
            
            if i < len(word_timings):
                word_start, word_end = word_timings[i]
                
                # Format time
                start_time = _format_time(word_start)
                end_time = _format_time(word_end)
                
                print(f"DEBUG: Time for word '{word}': {start_time} to {end_time}")
                
                # Clean and escape the word properly - ENHANCED CLEANING
                clean_word = word.strip()
                
                # Remove any numbers that might have been added
                clean_word = re.sub(r'^\d+', '', clean_word)  # Remove leading numbers
                clean_word = re.sub(r'\d+$', '', clean_word)  # Remove trailing numbers
                clean_word = re.sub(r'\d+', '', clean_word)   # Remove any embedded numbers
                
                # Remove any remaining problematic characters
                clean_word = re.sub(r'[^\w\s\'-]', '', clean_word)
                clean_word = clean_word.strip()
                
                print(f"DEBUG: Word '{word}' cleaned to '{clean_word}'")
                
                # Skip empty words
                if not clean_word:
                    print(f"DEBUG: Skipping empty word at index {i}")
                    continue
                
                # Escape special characters for ASS format
                safe_word = clean_word.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
                
                print(f"DEBUG: Word '{clean_word}' escaped to '{safe_word}'")
                
                # Use simple effects to avoid number contamination
                effect = ""  # Disable effects temporarily to isolate the issue
                style_name = "Default"  # Use default style only
                
                print(f"DEBUG: Using effect '{effect}' and style '{style_name}' for word '{safe_word}'")
                
                # Write the subtitle event with minimal formatting
                subtitle_line = f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,{effect},{safe_word}\n"
                print(f"DEBUG: Writing subtitle line: {subtitle_line.strip()}")
                f.write(subtitle_line)
            else:
                print(f"DEBUG: No timing available for word {i}: '{word}'")
    
    print("DEBUG: Finished generating subtitle events")

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
            f.write("Style: Default,Arial,32,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,150,1\n\n")
            f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            f.write(f"Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Error: {error_msg[:50]}...\n")
            f.write(f"Dialogue: 0,0:00:05.00,0:00:10.00,Default,,0,0,0,,Please check the console for details.\n")
            f.write(f"Dialogue: 0,0:00:10.00,0:05:00.00,Default,,0,0,0,,This is a fallback subtitle.\n")
        print(f"Created fallback subtitle file: {subtitle_path}")
        return subtitle_path
    except Exception as fallback_error:
        print(f"Failed to create fallback subtitle file: {fallback_error}")
        return None


