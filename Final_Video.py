import subprocess
import os
import traceback
import shutil

def merge_video_subtitle(video_path, subtitle_path, output_file="final_output.mp4"):
    """Merge video and subtitle into a final output video"""
    print("\n=== VIDEO MERGING DEBUGGING ===")
    print(f"Video path: {video_path}")
    print(f"Subtitle path: {subtitle_path}")
    print(f"Output file: {output_file}")
    
    # Verify input files
    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}")
        return None
    
    if not os.path.exists(subtitle_path):
        print(f"ERROR: Subtitle file not found: {subtitle_path}")
        return None
    
    # Create output directory if needed
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
    
    # Check video file size and content
    video_size = os.path.getsize(video_path)
    print(f"Input video size: {video_size} bytes")
    if video_size < 1000:
        print("WARNING: Input video file is suspiciously small!")
    
    # Check subtitle content
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
    
    # First, make a backup copy of the video
    backup_video = os.path.join(output_dir, "original_video_backup.mp4")
    try:
        shutil.copy2(video_path, backup_video)
        print(f"Created backup of original video: {backup_video}")
    except Exception as e:
        print(f"Failed to create backup: {e}")
    
    # Try to merge with subtitles
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
            
            # Verify the output file exists and has content
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                print(f"Final video saved to {output_file}")
                success = True
                break
            else:
                print(f"WARNING: Output file is too small or doesn't exist")
        except subprocess.CalledProcessError as e:
            print(f"Method failed: {e}")
            print(f"Error output: {e.stderr}")
    
    # If all subtitle methods failed, try to use the original video
    if not success:
        print("All subtitle embedding methods failed. Using original video.")
        try:
            # Just copy the original video
            shutil.copy2(video_path, output_file)
            print(f"Copied original video to {output_file}")
            return output_file
        except Exception as e:
            print(f"Error copying video: {e}")
            
            # Last resort: try to use the backup
            if os.path.exists(backup_video):
                try:
                    shutil.copy2(backup_video, output_file)
                    print(f"Copied backup video to {output_file}")
                    return output_file
                except Exception as backup_e:
                    print(f"Error copying backup video: {backup_e}")
            
            return None
    
    # Final verification
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"Output file created successfully. Size: {file_size} bytes")
        return output_file
    else:
        print(f"ERROR: Output file was not created: {output_file}")
        return None
