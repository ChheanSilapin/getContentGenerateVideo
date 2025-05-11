import os
import sys
import traceback
import emoji
import re
from moviepy.editor import VideoFileClip, AudioFileClip

def process_text_for_subtitles(text):
    """Process text by converting number emojis to numbers and removing other emojis"""
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
    print("\n=== SUBTITLE GENERATION DEBUGGING ===")
    print(f"Video path: {video_path}")
    print(f"Output file: {output_file}")
    print(f"Audio file provided: {audio_file}")
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
    subtitle_path = output_file
    try:
        with open(subtitle_path, "w", encoding="utf-8") as f:
            f.write("[Script Info]\nTitle: Generated Subtitle\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\n\n")
            f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write("Style: Default,Arial,32,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,150,1\n")
            f.write("Style: Loud,Arial,36,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,150,1\n\n")
            f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    except Exception as e:
        print(f"Error creating subtitle file structure: {e}")
        return None
    
    try:
        if not os.path.exists(video_path):
            print(f"ERROR: Video file not found: {video_path}")
            raise FileNotFoundError(f"Video file not found: {video_path}")
        print(f"Loading video file: {video_path}")
        video = VideoFileClip(video_path)
        print(f"Video loaded successfully. Duration: {video.duration} seconds")
        if audio_file is None:
            video_dir = os.path.dirname(video_path)
            audio_file = os.path.join(video_dir, "voice.mp3")
            print(f"No audio file provided, trying: {audio_file}")
        if not os.path.exists(audio_file):
            print(f"ERROR: Audio file not found: {audio_file}")
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        print(f"Loading audio file: {audio_file}")
        audio = AudioFileClip(audio_file)
        print(f"Audio loaded successfully. Duration: {audio.duration} seconds")
        text_file = f"{audio_file}.txt"
        print(f"Looking for text file: {text_file}")
        if not os.path.exists(text_file):
            print(f"ERROR: Text file not found: {text_file}")
            try:
                with open(text_file, "w", encoding="utf-8") as f:
                    f.write("Default subtitle text created automatically.")
                print(f"Created default text file: {text_file}")
            except Exception as text_write_error:
                print(f"Failed to create default text file: {text_write_error}")
                raise FileNotFoundError(f"Text file not found and could not create default: {text_file}")
        with open(text_file, "r", encoding="utf-8") as text_file_handle:
            text = text_file_handle.read().strip()
            print(f"Text content loaded. Length: {len(text)} characters")
            print(f"First 100 chars: {text[:100]}...")
        if not text:
            print("WARNING: Text file is empty, using default text")
            text = "Default subtitle text because original file was empty."
        print("Processing text for subtitles...")
        text = process_text_for_subtitles(text)
        print(f"Processed text: {text[:100]}...")
        lines = []
        remaining_text = text
        while remaining_text:
            if len(remaining_text) <= maxChar:
                lines.append(remaining_text)
                break
            split_at = remaining_text[:maxChar].rfind(' ')
            if split_at == -1:
                split_at = maxChar
            lines.append(remaining_text[:split_at])
            remaining_text = remaining_text[split_at:].strip()
        
        print(f"Split text into {len(lines)} lines")
        with open(subtitle_path, "a", encoding="utf-8") as f:
            # Calculate timing
            line_duration = audio.duration / len(lines) if lines else audio.duration
            print(f"Each line will display for approximately {line_duration:.2f} seconds")
            for i, line in enumerate(lines):
                line_start = i * line_duration
                line_end = (i + 1) * line_duration
                # Format time as H:MM:SS.ms
                start = f"{int(line_start//3600)}:{int((line_start%3600)//60):02d}:{line_start%60:.2f}"
                end = f"{int(line_end//3600)}:{int((line_end%3600)//60):02d}:{line_end%60:.2f}"
                # Escape special characters
                line = line.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
                # Determine style
                style = "Loud" if "!" in line or line.isupper() else "Default"
                # Write the line
                f.write(f"Dialogue: 0,{start},{end},{style},,0,0,0,,{line}\n")
                # Debug first few lines
                if i < 3:
                    print(f"Line {i+1}: {start} -> {end}: {line[:30]}...")
        video.close()
        audio.close()
        print(f"Successfully created subtitles at {subtitle_path}")
        if os.path.exists(subtitle_path):
            file_size = os.path.getsize(subtitle_path)
            print(f"Subtitle file size: {file_size} bytes")
            if file_size < 100:
                print("WARNING: Subtitle file is suspiciously small!")
        else:
            print("ERROR: Subtitle file was not created!")
            
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
