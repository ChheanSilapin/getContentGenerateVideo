"""
Subtitle service for generating subtitles
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

def generate_subtitles(text, video_file, audio_file, output_file):
    """
    Generate subtitles for a video

    Args:
        text: Text for subtitles
        video_file: Path to video file
        audio_file: Path to audio file
        output_file: Path to output subtitle file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir:
            ensure_directory_exists(output_dir)

        # First, save the text to a file that process_local_video will read
        text_file = f"{audio_file}.txt"
        try:
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Created text file for subtitles: {text_file}")
        except Exception as e:
            print(f"Error creating text file: {e}")
            return False

        # Generate subtitles
        print(f"Generating subtitles for video: {video_file}")
        result = process_local_video(
            video_path=video_file,
            output_type="ass",
            maxChar=DEFAULT_MAX_CHARS_PER_LINE,
            output_file=output_file,
            audio_file=audio_file
        )

        # Check if the file was created
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"Subtitles generated successfully: {output_file}")
            return True
        else:
            print(f"Subtitle file not created or empty: {output_file}")
            return False
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
    number_emoji_map = {
        '0️⃣': '0', '1️⃣': '1', '2️⃣': '2', '3️⃣': '3', '4️⃣': '4',
        '5️⃣': '5', '6️⃣': '6', '7️⃣': '7', '8️⃣': '8', '9️⃣': '9'
    }
    for emoji_num, real_num in number_emoji_map.items():
        text = text.replace(emoji_num, real_num)
    text = emoji.replace_emoji(text, replace='')
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def process_local_video(video_path, output_type="ass", maxChar=40, output_file="subtitles.ass", audio_file=None):
    """
    Generate subtitles for a video

    Args:
        video_path: Path to video file
        output_type: Type of subtitle file to create (currently only 'ass' is supported)
        maxChar: Maximum characters per line
        output_file: Path to output subtitle file
        audio_file: Path to audio file (if different from video's audio)

    Returns:
        str: Path to subtitle file if successful, None otherwise
    """
    print(f"Generating subtitles for video: {os.path.basename(video_path)}")
    output_dir = os.path.dirname(output_file)
    if output_dir:
        ensure_directory_exists(output_dir)

    subtitle_path = output_file
    try:
        with open(subtitle_path, "w", encoding="utf-8") as f:
            f.write("[Script Info]\nTitle: Generated Subtitle\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\n\n")
            f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")

            # Alignment=8 positions text at the top center of the screen
            # MarginV=200 adds space from the top (lower value = higher position)

            # White text with black outline, no background - positioned higher
            f.write("Style: Default,Arial,42,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,250,1\n")
            # Red text style - positioned higher
            f.write("Style: Red,Arial,42,&H000000FF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,250,1\n")
            # Blue text style - positioned higher
            f.write("Style: Blue,Arial,42,&H00FF0000,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,250,1\n")
            # Cyan text style - positioned higher
            f.write("Style: Cyan,Arial,42,&H00FFFF00,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,250,1\n")
            # Red background style - positioned higher
            f.write("Style: RedBG,Arial,42,&H00FFFFFF,&H000000FF,&H00000000,&H000000FF,1,0,0,0,100,100,0,0,4,0,0,2,10,10,250,1\n\n")

            f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    except Exception as e:
        print(f"Error creating subtitle file structure: {e}")
        return None

    try:
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
        text_file = f"{audio_file}.txt"
        if not os.path.exists(text_file):
            print(f"ERROR: Text file not found: {text_file}")
            try:
                # Create a text file with the original text from the audio file name
                # Extract text from the parent directory name (which often contains the timestamp)
                parent_dir = os.path.basename(os.path.dirname(audio_file))
                if "video_" in parent_dir:
                    # Use a more meaningful default text
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
        # Convert text to uppercase
        text = text.upper()

        # Split text into words
        words = text.split()

        # Calculate approximate duration per word based on audio length
        word_duration = audio.duration / len(words) if words else 1.0

        # Try to use more sophisticated audio analysis for word timing if possible
        sophisticated_timing = False
        if PYDUB_AVAILABLE:
            try:
                audio_segment = AudioSegment.from_file(audio_file)

                # Detect non-silent parts with more sensitive parameters
                non_silent_ranges = detect_nonsilent(
                    audio_segment,
                    min_silence_len=150,  # Shorter silence detection (was 200)
                    silence_thresh=-35    # More sensitive threshold (was -40)
                )

                # If we have detected speech segments
                if non_silent_ranges:
                    # Add a small offset to start highlighting slightly before the sound
                    offset_ms = 100  # 100ms offset

                    # Use detected speech segments for timing
                    word_timings = []
                    segment_duration = [end - start for start, end in non_silent_ranges]
                    total_speech_duration = sum(segment_duration)

                    # Distribute words across speech segments
                    words_per_segment = [max(1, round(len(words) * dur / total_speech_duration)) for dur in segment_duration]

                    # Adjust to match total word count
                    while sum(words_per_segment) > len(words):
                        idx = segment_duration.index(max(segment_duration))
                        if words_per_segment[idx] > 1:
                            words_per_segment[idx] -= 1
                        segment_duration[idx] *= 0.9

                    while sum(words_per_segment) < len(words):
                        idx = segment_duration.index(max(segment_duration))
                        words_per_segment[idx] += 1
                        segment_duration[idx] *= 0.9

                    # Create word timings with offset
                    word_idx = 0
                    for i, (start_ms, end_ms) in enumerate(non_silent_ranges):
                        segment_word_count = words_per_segment[i]
                        segment_duration_ms = end_ms - start_ms

                        for j in range(segment_word_count):
                            if word_idx < len(words):
                                # Apply offset to start highlighting earlier
                                word_start = max(0, start_ms - offset_ms) + (j * segment_duration_ms / segment_word_count)
                                # Extend the end time slightly to ensure overlap with next word
                                word_end = start_ms + ((j + 1) * segment_duration_ms / segment_word_count) + offset_ms
                                word_timings.append((word_start / 1000, word_end / 1000))
                                word_idx += 1

                    print(f"Using audio analysis for word timing: {len(word_timings)} timings for {len(words)} words")
                    sophisticated_timing = True
                else:
                    sophisticated_timing = False
                    print("Audio analysis didn't produce usable word timings, using simple timing")
            except Exception as audio_error:
                print(f"Advanced audio analysis not available: {audio_error}")
                sophisticated_timing = False

        # Define color patterns - alternate between different colors
        colors = ["Cyan", "Default", "Blue", "Default"]
        highlight_color = "RedBG"  # Red background for the current word

        with open(subtitle_path, "a", encoding="utf-8") as f:
            if sophisticated_timing:
                # Use the detected word timings with overlap
                for i, word in enumerate(words):
                    if i < len(word_timings):
                        word_start, word_end = word_timings[i]

                        # Format time as H:MM:SS.ms
                        start = f"{int(word_start//3600)}:{int((word_start%3600)//60):02d}:{word_start%60:.2f}"
                        end = f"{int(word_end//3600)}:{int((word_end%3600)//60):02d}:{word_end%60:.2f}"

                        # Escape special characters
                        safe_word = word.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

                        # Write a separate line for each word with its own style
                        # This creates a cleaner look with only the current word highlighted
                        f.write(f"Dialogue: 0,{start},{end},{highlight_color},,0,0,0,,{safe_word}\n")
            else:
                # Use simple timing with overlap
                word_duration = audio.duration / (len(words) * 1.2)  # 20% faster to catch up with audio
                overlap = word_duration * 0.1  # 10% overlap between words

                for i, word in enumerate(words):
                    # Start slightly earlier and end slightly later for better sync
                    word_start = max(0, i * word_duration - overlap)
                    word_end = (i + 1) * word_duration + overlap

                    # Format time as H:MM:SS.ms
                    start = f"{int(word_start//3600)}:{int((word_start%3600)//60):02d}:{word_start%60:.2f}"
                    end = f"{int(word_end//3600)}:{int((word_end%3600)//60):02d}:{word_end%60:.2f}"

                    # Escape special characters
                    safe_word = word.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

                    # Write a separate line for each word with its own style
                    f.write(f"Dialogue: 0,{start},{end},{highlight_color},,0,0,0,,{safe_word}\n")

        print(f"Successfully created subtitles with dynamic word highlighting")
        return subtitle_path
    except Exception as e:
        print(f"ERROR in subtitle generation: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()

        # Create a fallback subtitle file with error information
        try:
            with open(subtitle_path, "w", encoding="utf-8") as f:
                f.write("[Script Info]\nTitle: Error Subtitle\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\n\n")
                f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                f.write("Style: Default,Arial,32,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,150,1\n\n")
                f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                f.write(f"Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Error: {str(e)[:50]}...\n")
                f.write(f"Dialogue: 0,0:00:05.00,0:00:10.00,Default,,0,0,0,,Please check the console for details.\n")
                f.write(f"Dialogue: 0,0:00:10.00,0:05:00.00,Default,,0,0,0,,This is a fallback subtitle.\n")
            print(f"Created fallback subtitle file with error information: {subtitle_path}")
            return subtitle_path
        except Exception as fallback_error:
            print(f"Failed to create fallback subtitle file: {fallback_error}")
            return None


