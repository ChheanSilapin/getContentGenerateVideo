#!/usr/bin/env python3
"""
Utility script to clean up accumulated temporary files in output folder
This will remove temporary directories while keeping final merged videos
"""

import os
import shutil
import json

def load_output_folder_from_settings():
    """Load the output folder path from user settings"""
    try:
        with open('user_settings.json', 'r') as f:
            settings = json.load(f)
            return settings.get('output_folder', 'output')
    except Exception as e:
        print(f"Could not load settings: {e}")
        return 'output'

def is_temp_video_directory(dir_path):
    """Check if a directory is a temporary video processing directory"""
    try:
        if not os.path.isdir(dir_path):
            return False
            
        dir_name = os.path.basename(dir_path)
        dir_contents = os.listdir(dir_path)
        
        # Check for temp directory naming pattern
        if not (dir_name.startswith('video_') and '_202' in dir_name):
            return False
            
        # Check for typical temporary video files
        temp_indicators = [
            'video_with_audio.mp4',
            'slideshow.mp4',
            'voice.mp3',
            'subtitles.ass'
        ]
        
        # If it contains any of these files, it's likely a temp directory
        for indicator in temp_indicators:
            if indicator in dir_contents:
                return True
                
        return False
        
    except Exception:
        return False

def cleanup_output_folder(output_folder):
    """Clean up temporary directories in the output folder"""
    if not os.path.exists(output_folder):
        print(f"Output folder not found: {output_folder}")
        return
        
    print(f"Scanning output folder: {output_folder}")
    
    temp_dirs_found = []
    final_videos_found = []
    
    # Scan the output folder
    try:
        for item in os.listdir(output_folder):
            item_path = os.path.join(output_folder, item)
            
            if os.path.isdir(item_path):
                if is_temp_video_directory(item_path):
                    temp_dirs_found.append(item_path)
                else:
                    print(f"Keeping directory (not temp): {item}")
            elif item.endswith('.mp4'):
                final_videos_found.append(item)
                print(f"Found final video: {item}")
            else:
                print(f"Found other file: {item}")
                
    except Exception as e:
        print(f"Error scanning output folder: {e}")
        return
    
    # Report findings
    print(f"\n📊 Scan Results:")
    print(f"  Final videos: {len(final_videos_found)}")
    print(f"  Temp directories: {len(temp_dirs_found)}")
    
    if not temp_dirs_found:
        print("✅ No temporary directories found - output folder is clean!")
        return
    
    # Show what will be removed
    print(f"\n🗑️ Temporary directories to remove:")
    for temp_dir in temp_dirs_found:
        dir_name = os.path.basename(temp_dir)
        print(f"  - {dir_name}")
    
    # Ask for confirmation
    response = input(f"\nRemove {len(temp_dirs_found)} temporary directories? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        removed_count = 0
        for temp_dir in temp_dirs_found:
            try:
                shutil.rmtree(temp_dir)
                removed_count += 1
                print(f"✅ Removed: {os.path.basename(temp_dir)}")
            except Exception as e:
                print(f"❌ Failed to remove {os.path.basename(temp_dir)}: {e}")
        
        print(f"\n🎉 Cleanup complete! Removed {removed_count}/{len(temp_dirs_found)} temporary directories")
        print(f"📁 Final videos preserved: {len(final_videos_found)}")
    else:
        print("Cleanup cancelled.")

def main():
    """Main function"""
    print("🧹 Output Folder Cleanup Utility")
    print("=" * 40)
    
    # Load output folder from settings
    output_folder = load_output_folder_from_settings()
    print(f"Using output folder: {output_folder}")
    
    # Clean up the folder
    cleanup_output_folder(output_folder)

if __name__ == "__main__":
    main()
