import pyttsx3
import re
import emoji
import os

def generateAudio(text, voice_actor=None, speed=1, output_file="voice.mp3"):  
    """
    Generate audio from text using local TTS engine
    Parameters:
    - text: The text to convert to speech
    - voice_actor: Not used in this simplified version
    - speed: Speed of speech (0.5 to 2.0, with 1.0 being normal speed)
    - output_file: Path to save the generated audio
    Returns:
    - True if successful, False otherwise
    """
    if not text:
        print("No text input provided.")
        return False
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    text_file = f"{output_file}.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(text)
    print("Processing text for TTS...")
    number_emoji_map = {
        '0️⃣': '0', '1️⃣': '1', '2️⃣': '2', '3️⃣': '3', '4️⃣': '4',
        '5️⃣': '5', '6️⃣': '6', '7️⃣': '7', '8️⃣': '8', '9️⃣': '9'
    }
    
    for emoji_num, real_num in number_emoji_map.items():
        text = text.replace(emoji_num, real_num)
    
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
        engine.save_to_file(text, output_file)
        engine.runAndWait()
        print(f"Audio generated successfully: {output_file}")
        return True
    except Exception as e:
        print(f"Error generating audio: {e}")
        return False
