"""
Subtitle service for generating subtitles with modern styling
"""
from utils.common_imports import os, sys, traceback, time
import re
import emoji
from moviepy.editor import VideoFileClip, AudioFileClip

# Import from utils
from utils.helpers import ensure_directory_exists
from utils.text_processing import process_text_for_subtitles

# Import config
try:
    from config import DEFAULT_MAX_CHARS_PER_LINE, SUBTITLE_CONFIG
except ImportError:
    # Default value if config.py is not available
    DEFAULT_MAX_CHARS_PER_LINE = 56
    # Fallback subtitle config
    SUBTITLE_CONFIG = {
        "default_font": "Times New Roman",
        "font_size": 48,
        "font_bold": True,
        "words_per_group_short": 5,
        "words_per_group_medium": 4,
        "words_per_group_long": 3,
        "reading_speed_wpm": 150,
        "min_display_time": 1.2,
        "early_start_offset": 0.3,
        "overlap_time": 0.2,
        "use_speech_analysis": True,
        "speech_analysis_max_duration": 25.0,
        "silence_threshold_db": 16,
        "min_silence_length_ms": 150,
        "default_style": "modern_glow",
        "available_styles": {
            "modern_glow": {
                "name": "Modern Glow",
                "font": "Times New Roman",
                "size": 48,
                "primary_color": "&H00FFFFFF",
                "outline_color": "&H00FF8000",
                "outline_width": 3,
                "shadow": 2,
                "bold": True,
                "alignment": 2,
                "margin_v": 80
            }
        }
    }

# Try to import pydub for audio analysis
try:
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("pydub not available. Will use simple timing for subtitles.")

def get_subtitle_styles():
    """Get available subtitle styles from centralized config"""
    return SUBTITLE_CONFIG.get("available_styles", {})

def get_available_styles():
    """Get list of available subtitle styles"""
    return list(get_subtitle_styles().keys())

# Legacy SUBTITLE_STYLES for backward compatibility - DEPRECATED
SUBTITLE_STYLES = get_subtitle_styles()

# Create ASS header dynamically from config
def create_ass_header():
    """Create ASS header using centralized config"""
    config = SUBTITLE_CONFIG
    font = config.get("default_font", "Times New Roman")
    size = config.get("font_size", 42)
    bold = 1 if config.get("font_bold", True) else 0
    
    return f"""[Script Info]
Title: Modern Styled Subtitle
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
Timer: 100.0000
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,{bold},0,0,0,100,100,0,0,1,2,0,2,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Dynamic ASS Header
ASS_HEADER = create_ass_header()

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

def process_local_video(video_path, output_type="ass", maxChar=40, output_file="subtitles.ass", audio_file=None, style="modern_glow"):
    """
    Generate subtitles for a video using centralized styling configuration

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

    # USE CENTRALIZED CONFIG for style configuration
    available_styles = SUBTITLE_CONFIG.get("available_styles", {})
    default_style = SUBTITLE_CONFIG.get("default_style", "modern_glow")
    
    # Get style configuration from centralized config
    if style in available_styles:
        style_config = available_styles[style]
    elif default_style in available_styles:
        print(f"Style '{style}' not found, using default style '{default_style}'")
        style_config = available_styles[default_style]
        style = default_style
    else:
        # Ultimate fallback
        print(f"No valid styles found in config, using hardcoded fallback")
        style_config = {
            "name": "Fallback Style",
            "font": SUBTITLE_CONFIG.get("default_font", "Times New Roman"),
            "size": SUBTITLE_CONFIG.get("font_size", 48),
            "primary_color": "&H00FFFFFF",
            "outline_color": "&H00FF8000",
            "outline_width": 3,
            "shadow": 2,
            "bold": SUBTITLE_CONFIG.get("font_bold", True),
            "alignment": 2,
            "margin_v": 80
        }
    
    print(f"Using style configuration from centralized config: {style_config.get('name', style)}")

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

            # Create the main style based on centralized configuration
            font = style_config.get("font", SUBTITLE_CONFIG.get("default_font", "Times New Roman"))
            size = style_config.get("size", SUBTITLE_CONFIG.get("font_size", 42))
            primary = style_config.get("primary_color", "&H00FFFFFF")
            secondary = style_config.get("secondary_color", "&H000000FF")
            outline = style_config.get("outline_color", "&H00000000")
            back = style_config.get("back_color", "&H00000000")
            bold = 1 if style_config.get("bold", SUBTITLE_CONFIG.get("font_bold", True)) else 0
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

        # Create optimized word groups
        word_groups = create_optimized_word_groups(text)
        print(f"Created {len(word_groups)} optimized subtitle groups")

        # Calculate timing for word groups instead of individual words
        group_timings = _calculate_optimized_timing(audio_file, word_groups, audio.duration)

        # Generate subtitle events with word groups
        # For this function, we need a default style config since we don't have style_config here
        default_style_config = SUBTITLE_CONFIG.get("available_styles", {}).get(SUBTITLE_CONFIG.get("default_style", "modern_glow"), {})
        subtitle_events = _generate_group_subtitle_events(word_groups, group_timings, default_style_config)
        
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
        try:
            events = _create_fallback_subtitle(f"Error: {str(e)}", 10.0)
            with open(subtitle_path, "w", encoding="utf-8") as f:
                f.write(ASS_HEADER)
                for event in events:
                    f.write(f"Dialogue: 0,{_seconds_to_ass_time(event['start'])},{_seconds_to_ass_time(event['end'])},Default,,0,0,0,,{event['text']}\n")
            return subtitle_path
        except:
            return None

def _create_effect_styles(f, style_config):
    """Create additional effect styles for animations"""
    font = style_config.get("font", "Times New Roman")
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

def _calculate_optimized_timing(audio_file, word_groups, total_duration):
    """
    Calculate timing using centralized configuration for better voice sync
    """
    group_timings = []
    
    print("Using voice-synchronized timing from centralized config...")
    
    total_groups = len(word_groups)
    if total_groups == 0:
        return group_timings
    
    # USE CENTRALIZED CONFIG for timing settings
    config = SUBTITLE_CONFIG
    reading_speed_wpm = config.get("reading_speed_wpm", 150)
    min_display_time = config.get("min_display_time", 1.2)
    early_start_offset = config.get("early_start_offset", 0.3)
    overlap_time = config.get("overlap_time", 0.2)
    
    print(f"Config: {reading_speed_wpm} WPM, {min_display_time}s min display, {early_start_offset}s early start")
    
    # TIMING: Better timing for all audio lengths with earlier subtitle appearance
    if total_duration > 10.0:  # For longer audio
        print(f"Voice-sync timing for longer audio ({total_duration:.1f}s) - subtitles appear early")
        
        # Better timing calculation with early subtitle appearance
        avg_duration_per_group = total_duration / total_groups
        base_duration = max(avg_duration_per_group, min_display_time)
        
        for i, group in enumerate(word_groups):
            # Enhanced duration based on content
            group_duration = base_duration
            
            # Adjust for content complexity
            if group['char_count'] > 20:  # Longer text needs more time
                group_duration *= 1.2
            if group['has_punctuation']:  # Pause for punctuation
                group_duration *= 1.1
            if '$' in group['text']:  # Extra time for numbers/currency
                group_duration *= 1.15
            
            # Calculate start time with early offset
            if i == 0:
                group_start = 0  # First subtitle starts immediately
            else:
                # Start earlier than previous subtitle ends for better voice sync
                prev_end = group_timings[i-1][1]
                group_start = prev_end - early_start_offset
            
            # Ensure start time is not negative
            group_start = max(0, group_start)
            group_end = group_start + group_duration
            
            # Ensure we don't exceed total duration
            if group_end > total_duration:
                group_end = total_duration
                if group_start >= total_duration:
                    group_start = max(0, total_duration - group_duration)
            
            group_timings.append((group_start, group_end))
        
        print(f"Voice-synchronized timing completed - subtitles start early for better sync")
        return group_timings
    
    # Better timing for shorter audio with early subtitle start
    print("Using optimized timing for shorter audio with early subtitle sync")
    
    current_time = 0
    
    for i, group in enumerate(word_groups):
        word_count = group['word_count']
        char_count = group['char_count']
        
        # Calculate when speech likely occurs
        words_per_second = reading_speed_wpm / 60
        speech_time = word_count / words_per_second
        
        # Content-based adjustments
        if char_count > 25:  # Longer phrases
            speech_time *= 1.2
        if group['has_punctuation']:  # Pause for sentence boundaries
            speech_time *= 1.15
        if '$' in group['text'] or any(char.isdigit() for char in group['text']):
            speech_time *= 1.1
        
        # Minimum duration for comfortable reading
        group_duration = max(speech_time, min_display_time)
        
        # Start subtitles EARLY for voice sync
        if i == 0:
            group_start = 0  # First subtitle starts immediately
        else:
            # Start before the calculated speech time
            group_start = max(0, current_time - overlap_time)
        
        group_end = group_start + group_duration
        group_timings.append((group_start, group_end))
        
        # Less overlap, faster progression for better voice sync
        advance_time = speech_time * 0.9  # Faster progression
        current_time += advance_time
    
    return group_timings

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
            config = SUBTITLE_CONFIG
            if config.get("uppercase", False):
                clean_text = group['text'].upper()
            else:
                clean_text = group['text'].strip()
            
            clean_text = re.sub(r'^[,\.\)\]\}]+\s*', '', clean_text)
            clean_text = re.sub(r'\s*[,\.\(\[\{]+$', '', clean_text)
            
            # Skip empty groups
            if not clean_text:
                continue
            
            # Escape special characters for ASS format but preserve content
            safe_text = clean_text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
            
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

def create_optimized_word_groups(text):
    """
    ENHANCED: Create optimized word groups using centralized config
    """
    if not text or not text.strip():
        return []
    
    print("Creating optimized word groups using centralized configuration...")
    
    # Clean and split words
    words = text.strip().split()
    total_words = len(words)
    
    if total_words == 0:
        return []
    
    print(f"Processing {total_words} words")
    
    # USE CENTRALIZED CONFIG for word grouping
    config = SUBTITLE_CONFIG
    if total_words > 200:  # Very long text
        words_per_group = config.get("words_per_group_long", 3)
        print(f"Using {words_per_group} words per group for long text (>200 words)")
    elif total_words > 100:  # Medium text
        words_per_group = config.get("words_per_group_medium", 4)
        print(f"Using {words_per_group} words per group for medium text (100-200 words)")
    else:  # Short text
        words_per_group = config.get("words_per_group_short", 5)
        print(f"Using {words_per_group} words per group for short text (<100 words)")
    
    word_groups = []
    
    # Process in batches with better phrase awareness
    for i in range(0, total_words, words_per_group):
        group_words = words[i:i + words_per_group]
        group_text = ' '.join(group_words)
        
        # Enhanced calculations for better timing
        word_count = len(group_words)
        char_count = len(group_text)
        
        # Check for natural phrase boundaries
        has_punctuation = any(p in group_text for p in '.!?,:;')
        
        word_groups.append({
            'text': group_text,
            'word_count': word_count,
            'char_count': char_count,
            'start_index': i,
            'end_index': min(i + words_per_group - 1, total_words - 1),
            'has_punctuation': has_punctuation
        })
    
    print(f"✅ Created {len(word_groups)} optimized groups using centralized config")
    return word_groups

def _analyze_speech_timing(audio_file, word_groups, total_duration):
    """
    Analyze audio using centralized config to detect speech segments for better text-speech sync
    """
    try:
        from pydub import AudioSegment
        from pydub.silence import detect_nonsilent
        
        print("Analyzing audio using centralized config for enhanced speech pattern synchronization...")
        
        # USE CENTRALIZED CONFIG for speech analysis
        config = SUBTITLE_CONFIG
        silence_threshold_db = config.get("silence_threshold_db", 16)
        min_silence_length_ms = config.get("min_silence_length_ms", 150)
        early_start_offset = config.get("early_start_offset", 0.3)
        
        print(f"Speech analysis config: {silence_threshold_db}dB threshold, {min_silence_length_ms}ms silence, {early_start_offset}s early start")
        
        # Load audio
        audio = AudioSegment.from_file(audio_file)
        
        # Detect speech segments (non-silent parts) with config settings
        non_silent_segments = detect_nonsilent(
            audio,
            min_silence_len=min_silence_length_ms,
            silence_thresh=audio.dBFS - silence_threshold_db
        )
        
        if not non_silent_segments:
            print("No speech segments detected, using enhanced fallback timing")
            return None
        
        print(f"Detected {len(non_silent_segments)} speech segments for {len(word_groups)} word groups")
        
        # Convert to seconds and create timing map
        speech_segments = []
        for start_ms, end_ms in non_silent_segments:
            start_sec = start_ms / 1000.0
            end_sec = end_ms / 1000.0
            duration = end_sec - start_sec
            
            # Filter out very short segments (likely noise)
            if duration > 0.3:  # At least 300ms of speech
                speech_segments.append((start_sec, end_sec))
        
        if not speech_segments:
            print("No valid speech segments found after filtering")
            return None
        
        print(f"Using {len(speech_segments)} valid speech segments")
        
        # Better mapping of word groups to speech segments
        group_timings = []
        total_groups = len(word_groups)
        
        # Calculate total speech time for better distribution
        total_speech_time = sum(end - start for start, end in speech_segments)
        
        if len(speech_segments) >= total_groups:
            # More speech segments than groups - select best segments
            print("Using one-to-one mapping with best speech segments")
            
            # Sort by segment duration (longer = better for subtitles)
            sorted_segments = sorted(speech_segments, key=lambda x: x[1] - x[0], reverse=True)
            
            for i, group in enumerate(word_groups):
                if i < len(sorted_segments):
                    start_time, end_time = sorted_segments[i]
                    
                    # Start subtitles BEFORE speech for better sync using config
                    start_time = max(0, start_time - early_start_offset)
                    
                    # Adjust timing based on word group complexity
                    duration = end_time - start_time
                    
                    # Minimum duration for readability
                    min_duration = 1.2 + (group['char_count'] / 30)
                    if duration < min_duration:
                        end_time = start_time + min_duration
                        if end_time > total_duration:
                            end_time = min(total_duration, start_time + min_duration)
                            start_time = max(0, end_time - min_duration)
                    
                    group_timings.append((start_time, end_time))
                else:
                    # Fallback for remaining groups
                    if group_timings:
                        last_end = group_timings[-1][1]
                        duration = 1.5 + (group['char_count'] / 25)
                        start_time = max(0, last_end - 0.3)
                        group_timings.append((start_time, start_time + duration))
                    else:
                        group_timings.append((0, 2.0))
        else:
            # Fewer speech segments than groups - distribute groups across segments
            print("Distributing word groups across available speech segments")
            
            # Weighted distribution based on speech segment duration
            segment_weights = []
            for start_seg, end_seg in speech_segments:
                seg_duration = end_seg - start_seg
                weight = seg_duration * 1.0
                segment_weights.append(weight)
            
            total_weight = sum(segment_weights)
            current_group = 0
            
            for seg_idx, (segment_start, segment_end) in enumerate(speech_segments):
                segment_duration = segment_end - segment_start
                
                # Calculate how many groups this segment should handle
                segment_weight = segment_weights[seg_idx]
                groups_for_this_segment = max(1, round((segment_weight / total_weight) * total_groups))
                groups_for_this_segment = min(groups_for_this_segment, total_groups - current_group)
                
                if groups_for_this_segment <= 0:
                    continue
                
                print(f"Segment {seg_idx+1}: {groups_for_this_segment} groups in {segment_duration:.1f}s")
                
                # Start subtitles BEFORE speech in this segment using config
                early_segment_start = max(0, segment_start - early_start_offset)
                
                # Distribute groups within this speech segment
                for j in range(groups_for_this_segment):
                    if current_group >= total_groups:
                        break
                    
                    group = word_groups[current_group]
                    
                    # Calculate position within segment with better spacing
                    if groups_for_this_segment == 1:
                        group_start = early_segment_start
                        group_end = segment_end
                    else:
                        segment_portion = segment_duration / groups_for_this_segment
                        group_start = early_segment_start + (j * segment_portion)
                        
                        # Adaptive duration based on content
                        base_duration = segment_portion * 1.3
                        if group['char_count'] > 20:
                            base_duration *= 1.15
                        if group['has_punctuation']:
                            base_duration *= 1.1
                        
                        group_end = group_start + base_duration
                        group_end = min(group_end, segment_end + 0.2)
                    
                    # Ensure minimum readable duration
                    min_duration = 1.0 + (group['char_count'] / 40)
                    if group_end - group_start < min_duration:
                        group_end = group_start + min_duration
                    
                    group_timings.append((group_start, group_end))
                    current_group += 1
                
                if current_group >= total_groups:
                    break
            
            # Handle any remaining groups with early start
            while current_group < total_groups:
                if group_timings:
                    last_end = group_timings[-1][1]
                    remaining_group = word_groups[current_group]
                    duration = 1.5 + (remaining_group['char_count'] / 30)
                    start_time = max(0, last_end - 0.2)
                    group_timings.append((start_time, start_time + duration))
                else:
                    group_timings.append((0, 2.0))
                current_group += 1
        
        # Validate and adjust timings
        validated_timings = []
        for i, (start, end) in enumerate(group_timings):
            start = max(0, start)
            end = min(end, total_duration)
            
            if end - start < 1.0:
                end = start + 1.0
                if end > total_duration:
                    end = total_duration
                    start = max(0, end - 1.0)
            
            validated_timings.append((start, end))
        
        print(f"Enhanced speech-synced timing created for {len(validated_timings)} groups using centralized config")
        return validated_timings
        
    except Exception as e:
        print(f"Enhanced speech analysis failed: {e}, using improved fallback timing")
        return None

def generate_subtitle_events(content, audio_file):
    """
    Generate subtitle events using centralized config for optimization and speech sync
    """
    print("Starting optimized subtitle generation using centralized config...")
    
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
        
        # Create optimized word groups using centralized config
        word_groups = create_optimized_word_groups(cleaned_content)
        print(f"Created {len(word_groups)} word groups using centralized config")
        
        if not word_groups:
            print("WARNING: No word groups created, generating single subtitle")
            return _create_fallback_subtitle(cleaned_content, duration)
        
        # USE CENTRALIZED CONFIG for speech analysis decision
        config = SUBTITLE_CONFIG
        use_speech_analysis = config.get("use_speech_analysis", True)
        max_duration_for_analysis = config.get("speech_analysis_max_duration", 25.0)
        
        # Try speech analysis first for better sync
        group_timings = None
        if use_speech_analysis and duration <= max_duration_for_analysis:
            print(f"Attempting enhanced speech analysis (audio <= {max_duration_for_analysis}s)...")
            group_timings = _analyze_speech_timing(audio_file, word_groups, duration)
        else:
            if not use_speech_analysis:
                print("Speech analysis disabled in config, using optimized timing")
            else:
                print(f"Audio too long ({duration:.1f}s) for speech analysis, using optimized timing")
        
        # Fallback to enhanced timing if speech analysis fails
        if group_timings is None:
            print("Using enhanced optimized timing calculation from centralized config...")
            group_timings = _calculate_optimized_timing(audio_file, word_groups, duration)
        
        # Generate subtitle events
        # For this function, we need a default style config since we don't have style_config here
        default_style_config = config.get("available_styles", {}).get(config.get("default_style", "modern_glow"), {})
        subtitle_events = _generate_group_subtitle_events(word_groups, group_timings, default_style_config)
        
        print(f"Generated {len(subtitle_events)} subtitle events using centralized config")
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
        
        print(f" Subtitle file generated: {final_subtitle_file}")
        print(f" Generated {len(subtitle_events)} subtitle events")
        return final_subtitle_file
        
    except Exception as e:
        print(f" Error generating subtitle file: {e}")
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
