import pyttsx3
import re
import emoji
import os

def generateAudio(text, output_file="voice.mp3", voice_actor=None, speed=0.8):  
    """
    Generate audio from text using local TTS engine
    Parameters:
    - text: The text to convert to speech
    - output_file: Path to save the generated audio
    - voice_actor: Not used in this simplified version
    - speed: Speed of speech (0.5 to 2.0, with 1.0 being normal speed)
    Returns:
    - True if successful, False otherwise
    """
    if not text:
        print("No text input provided.")
        return False
    
    # Ensure we're using absolute paths if not already
    if not os.path.isabs(output_file):
        output_file = os.path.abspath(output_file)
    
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    print(f"Generating audio for text: {text[:50]}...")
    print("Processing text for TTS...")
    
    text = emoji.replace_emoji(text, replace='')
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    print(f"Processed text: {text[:100]}...")
    try:
        engine = pyttsx3.init()
        rate = engine.getProperty('rate')
        engine.setProperty('rate', int(rate * speed))
        voices = engine.getProperty('voices')
        if voices:
            for voice in voices:
                if "english" in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
        
        print(f"Saving audio to: {output_file}")
        engine.save_to_file(text, output_file)
        engine.runAndWait()
        
        # Verify the file was actually created and has content
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"Audio generated successfully: {output_file}")
            return True
        else:
            print(f"Error: Audio file not created or empty: {output_file}")
            return False
    except Exception as e:
        print(f"Error generating audio: {e}")
        return False
