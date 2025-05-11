import os
import sys
import time
from datetime import datetime
try:
    from voice_ai import generateAudio
    print("Successfully imported voice_ai module")
except ImportError as e:
    print(f"Error importing voice_ai module: {e}")
    print(f"Checking if file exists: {'voice_ai.py' in os.listdir('.')}")
except Exception as e:
    print(f"Unexpected error importing voice_ai: {e}")
try:
    print("Attempting to import create_video module...")
    try:
        from create_video import createSideShowWithFFmpeg, downloadImage
        print("Successfully imported create_video module")
    except FileNotFoundError as e:
        print(f"File Not Found Error in create_video module: {e}")
        print(f"File path: {e.filename}")
    except Exception as e:
        print(f"Error in create_video module: {e}")
        import traceback
        traceback.print_exc()
except Exception as outer_e:
    print(f"Outer exception: {outer_e}")
    
try:
    print("Attempting to import generate_ass module...")
    from generate_ass import process_local_video
    print("Successfully imported generate_ass module")
except ImportError as e:
    print(f"Error importing generate_ass module: {e}")
    print(f"Checking if file exists: {'generate_ass.py' in os.listdir('.')}")
except Exception as e:
    print(f"Unexpected error importing generate_ass: {e}")
try:
    print("Attempting to import Final_Video module...")
    from Final_Video import merge_video_subtitle
    print("Successfully imported Final_Video module")
except ImportError as e:
    print(f"Error importing Final_Video module: {e}")
    print(f"Checking if file exists: {'Final_Video.py' in os.listdir('.')}")
except Exception as e:
    print(f"Unexpected error importing Final_Video: {e}")
try:
    print("Attempting to import utils module...")
    from utils import getTitleContent
    print("Successfully imported utils module")
except ImportError as e:
    print(f"Error importing utils module: {e}")
    print(f"Checking if file exists: {'utils.py' in os.listdir('.')}")
except Exception as e:
    print(f"Unexpected error importing utils: {e}")

def run_generation():
    print("\n=== STARTING NEW VIDEO GENERATION ===")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Generation timestamp: {timestamp}")
    
    output_dir = f"output_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    audio_file = os.path.join(output_dir, "voice.mp3")
    video_file = os.path.join(output_dir, "slideshow.mp4")
    subtitle_file = os.path.join(output_dir, "subtitles.ass")
    final_output = os.path.join(output_dir, "final_output.mp4")
    
   
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    print(f"Created images directory: {images_dir}")
    
    
    print("\n--- Step 1: Generating Audio ---")
    text_input = input("Enter the text for voice generation: ")
    
    if not generateAudio(text_input, output_file=audio_file):
        print("Failed to generate audio.")
        return None, None, None
    
    
    print("\n--- Step 2: Getting Website Content ---")
    websiteUrl = input("Enter a website URL to get content: ")
    title, content = getTitleContent(websiteUrl)
    print(f"Retrieved title: {title[:50]}...")
    print(f"Content length: {len(content)} characters")
    
    
    print("\n--- Step 3: Downloading Images ---")
    folderName = downloadImage(title, content, websiteUrl, folder_name=images_dir)
    print(f"Images downloaded to: {folderName}")
    

    print("\n--- Step 4: Creating Slideshow Video ---")
    createSideShowWithFFmpeg(
        folderName=folderName,
        title=title,
        content=content,
        audioFile=audio_file,
        outputVideo=video_file,
        zoomFactor=0.5,
        frameRarte=25
    )


    print("\n--- File Status Check ---")
    print(f"Audio file: {audio_file}")
    print(f"Video file: {video_file}")
    print(f"Text file: {audio_file}.txt")

    if not os.path.exists(audio_file):
        print(f"ERROR: Audio file not found: {audio_file}")
        return None, None, None
    if not os.path.exists(video_file):
        print(f"ERROR: Video file not found: {video_file}")
        return None, None, None
    if not os.path.exists(f"{audio_file}.txt"):
        print(f"WARNING: Text file not found: {audio_file}.txt")
        # Create text file if it doesn't exist
        with open(f"{audio_file}.txt", "w", encoding="utf-8") as f:
            f.write(text_input)
        print(f"Created text file: {audio_file}.txt")
    print("\n--- Step 5: Generating Subtitles ---")
    subtitlePath = process_local_video(
        video_path=video_file, 
        output_type="ass", 
        maxChar=56, 
        output_file=subtitle_file, 
        audio_file=audio_file
    )
    
    if subtitlePath:
        print(f"Subtitles generated: {subtitlePath}")
        return subtitlePath, video_file, output_dir
    else:
        print("ERROR: Subtitle generation failed.")
        return None, None, None

def main():
    print("\n=== VIDEO GENERATION SYSTEM ===")
    print("This program will create a video with subtitles from text and images.")
    
    subtitlePath, videoPath, output_dir = run_generation()
    
    if subtitlePath and videoPath and output_dir:
        print("\n--- Final Step: Merging Video and Subtitles ---")
        final_output = os.path.join(output_dir, "final_output.mp4")
        print(f"Merging video: {videoPath}")
        print(f"With subtitles: {subtitlePath}")
        
        result = merge_video_subtitle(videoPath, subtitlePath, output_file=final_output)
        if result:
            print(f"Final video with subtitles created: {result}")
            print(f"All output files are in directory: {output_dir}")
        else:
            print("Failed to create final video with subtitles")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"\nERROR: {e}")
        print("\nDetailed error information:")
        traceback.print_exc()
        print("\nPlease check that all required files exist and are in the correct locations.")
