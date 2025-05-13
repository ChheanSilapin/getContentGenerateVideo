import subprocess
import os
import traceback

def merge_video_subtitle(video_path, subtitle_path, output_file="final_output.mp4"):
    """Merge video and subtitle into a final output video"""
    print("\n=== VIDEO MERGING DEBUGGING ===")
    print(f"Video path: {video_path}")
    print(f"Subtitle path: {subtitle_path}")
    print(f"Output file: {output_file}")
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}")
        return None
    
    if not os.path.exists(subtitle_path):
        print(f"ERROR: Subtitle file not found: {subtitle_path}")
        return None
    try:
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            subtitle_content = f.read()
            subtitle_lines = subtitle_content.count('Dialogue:')
            print(f"Subtitle file contains {subtitle_lines} dialogue lines")
            if subtitle_lines == 0:
                print("WARNING: Subtitle file contains no dialogue lines!")
            elif subtitle_lines == 1 and "This is a sample subtitle" in subtitle_content:
                print("WARNING: Subtitle file contains only the default sample subtitle!")
    except Exception as e:
        print(f"Error reading subtitle file: {e}")
    
    ffmpeg_cmd = "ffmpeg"
    subtitle_path_escaped = subtitle_path.replace("\\", "/")
    methods = [
        f'ass={subtitle_path_escaped}',  # Try ASS format first
        f'subtitles={subtitle_path_escaped}',
        f'subtitles={subtitle_path_escaped}:force_style=\'FontSize=24,Outline=1,Shadow=1,MarginV=80\''  # Increased margin for phone ratio
    ]
    success = False
    for method in methods:
        cmd = f'{ffmpeg_cmd} -i "{video_path}" -vf "{method}" -c:a copy "{output_file}"'
        print(f"Trying command: {cmd}")
        try:
            result = subprocess.run(cmd, check=True, shell=True, capture_output=True, text=True)
            print(f"Command output: {result.stdout}")
            if result.stderr:
                print(f"Command errors: {result.stderr}")
            print(f"Final video saved to {output_file}")
            success = True
            break
        except subprocess.CalledProcessError as e:
            print(f"Method failed: {e}")
            print(f"Error output: {e.stderr}")
    if not success:
        print("All subtitle embedding methods failed. Trying to copy video without subtitles.")
        try:
            cmd = f'{ffmpeg_cmd} -i "{video_path}" -c copy "{output_file}"'
            subprocess.run(cmd, check=True, shell=True)
            print(f"Video copied without subtitles to {output_file}")
            return output_file
        except subprocess.CalledProcessError as e:
            print(f"Error copying video: {e}")
            print(f"Error output: {e.stderr if hasattr(e, 'stderr') else 'No error output'}")
            return None
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"Output file created successfully. Size: {file_size} bytes")
        return output_file
    else:
        print(f"ERROR: Output file was not created: {output_file}")
        return None
