"""
Audio service for generating speech from text with emotional expression
"""
from utils.common_imports import os, sys, subprocess, traceback
import platform
import re
import emoji

# Try to import pyttsx3 for TTS
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("pyttsx3 not available. Will use system TTS as fallback.")

# Import from utils
from utils.helpers import ensure_directory_exists
from utils.text_processing import process_text_for_tts

def generate_audio(text, output_file, voice_actor=None, speed=0.8, emotion="neutral"):
    """
    Generate audio from text with emotional expression

    Args:
        text: Text to convert to speech
        output_file: Path to output audio file
        voice_actor: Optional voice actor to use (not implemented in all backends)
        speed: Speed of speech (0.5 to 2.0, with 1.0 being normal speed)
        emotion: Emotion to apply ("neutral", "excited", "dramatic", "calm", "energetic")

    Returns:
        bool: True if successful, False otherwise
    """
    if not text:
        print("No text input provided.")
        return False

    # Ensure we're using absolute paths if not already
    if not os.path.isabs(output_file):
        output_file = os.path.abspath(output_file)

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir:
        ensure_directory_exists(output_dir)

    print(f"Generating audio for text: {text[:50]}...")
    print("Processing text for TTS...")

    # Process text for TTS with emotional enhancement
    processed_text = process_text_for_tts(text, emotion)
    print(f"Processed text: {processed_text[:100]}...")

    # Try different TTS methods in order of preference
    if PYTTSX3_AVAILABLE:
        if generate_audio_pyttsx3_emotional(processed_text, output_file, speed, emotion):
            return True

    # Fallback to system TTS
    return generate_audio_system_emotional(processed_text, output_file, emotion)

def generate_audio_pyttsx3_emotional(text, output_file, speed=0.8, emotion="neutral"):
    """
    Generate audio using pyttsx3 with emotional settings

    Args:
        text: Text to convert to speech
        output_file: Path to output audio file
        speed: Speed of speech (0.5 to 2.0, with 1.0 being normal speed)
        emotion: Emotion to apply

    Returns:
        bool: True if successful, False otherwise
    """
    engine = None
    try:
        engine = pyttsx3.init()
        
        # Get available voices
        voices = engine.getProperty('voices')
        
        # Select best voice based on emotion and availability
        selected_voice = None
        if voices:
            # Prefer female voices for emotional expression (generally more expressive)
            female_voices = [v for v in voices if 'female' in v.name.lower() or 'zira' in v.name.lower() or 'hazel' in v.name.lower()]
            male_voices = [v for v in voices if 'male' in v.name.lower() or 'david' in v.name.lower() or 'mark' in v.name.lower()]
            
            if emotion in ["excited", "energetic"] and female_voices:
                selected_voice = female_voices[0]
            elif emotion == "dramatic" and male_voices:
                selected_voice = male_voices[0]
            elif female_voices:  # Default to female for better emotional range
                selected_voice = female_voices[0]
            elif voices:
                selected_voice = voices[0]
        
        if selected_voice:
            engine.setProperty('voice', selected_voice.id)
            print(f"Using voice: {selected_voice.name}")
        
        # Adjust speech parameters based on emotion
        base_rate = engine.getProperty('rate')
        
        if emotion == "excited":
            engine.setProperty('rate', int(base_rate * speed * 1.2))  # Faster for excitement
            engine.setProperty('volume', 0.9)  # Louder
        elif emotion == "dramatic":
            engine.setProperty('rate', int(base_rate * speed * 0.8))  # Slower for drama
            engine.setProperty('volume', 0.8)  # Moderate volume
        elif emotion == "calm":
            engine.setProperty('rate', int(base_rate * speed * 0.7))  # Slower for calm
            engine.setProperty('volume', 0.7)  # Softer
        elif emotion == "energetic":
            engine.setProperty('rate', int(base_rate * speed * 1.1))  # Slightly faster
            engine.setProperty('volume', 0.85)  # Good volume
        else:  # neutral
            engine.setProperty('rate', int(base_rate * speed))
            engine.setProperty('volume', 0.8)

        print(f"Saving audio to: {output_file}")
        engine.save_to_file(text, output_file)
        engine.runAndWait()

        # IMPORTANT: Properly clean up the engine to release file handles
        try:
            engine.stop()  # Stop any ongoing speech
        except:
            pass
        
        # Give a small delay to ensure file handle is released
        import time
        time.sleep(0.1)

        # Verify the file was actually created and has content
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"Audio generated successfully with {emotion} emotion: {output_file}")
            return True
        else:
            print(f"Error: Audio file not created or empty: {output_file}")
            return False
            
    except Exception as e:
        print(f"Error generating audio with pyttsx3: {e}")
        traceback.print_exc()
        return False
    finally:
        # Ensure engine is always cleaned up, even on exceptions
        if engine:
            try:
                engine.stop()
                # Small delay to ensure proper cleanup
                import time
                time.sleep(0.1)
            except:
                pass  # Ignore cleanup errors

def generate_audio_system_emotional(text, output_file, emotion="neutral"):
    """
    Generate audio using system TTS with emotional settings

    Args:
        text: Text to convert to speech
        output_file: Path to output audio file
        emotion: Emotion to apply

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use system-specific TTS with emotional parameters
        if platform.system() == "Windows":
            # Use PowerShell's text-to-speech with voice selection
            voice_name = "Microsoft Zira Desktop"  # Default to Zira (female, more expressive)
            
            if emotion == "dramatic":
                voice_name = "Microsoft David Desktop"  # Male voice for drama
            elif emotion in ["excited", "energetic"]:
                voice_name = "Microsoft Zira Desktop"  # Female voice for excitement
            
            # Create PowerShell script with emotional settings
            ps_script = f'''
            Add-Type -AssemblyName System.Speech
            $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
            
            # Try to set voice
            try {{
                $speak.SelectVoice("{voice_name}")
            }} catch {{
                Write-Host "Could not select voice {voice_name}, using default"
            }}
            
            # Set rate based on emotion
            $speak.Rate = {get_rate_for_emotion(emotion)}
            
            # Set volume based on emotion
            $speak.Volume = {get_volume_for_emotion(emotion)}
            
            # Set output to file
            $speak.SetOutputToWaveFile("{output_file}")
            
            # Speak the text
            $speak.Speak("{text}")
            
            # Clean up
            $speak.Dispose()
            '''
            
            subprocess.run(["powershell", "-Command", ps_script], check=True)
            
        elif platform.system() == "Darwin":  # macOS
            # Use macOS say command with voice selection
            voice_option = []
            if emotion == "excited":
                voice_option = ["-v", "Samantha"]  # Energetic female voice
            elif emotion == "dramatic":
                voice_option = ["-v", "Alex"]  # Deep male voice
            elif emotion == "calm":
                voice_option = ["-v", "Victoria"]  # Calm female voice
            
            cmd = ["say"] + voice_option + ["-o", output_file, text]
            subprocess.run(cmd, check=True)
            
        else:  # Linux
            # Try using espeak with emotional parameters
            pitch = 50  # Default pitch
            speed = 175  # Default speed
            
            if emotion == "excited":
                pitch = 70
                speed = 200
            elif emotion == "dramatic":
                pitch = 30
                speed = 150
            elif emotion == "calm":
                pitch = 40
                speed = 140
            elif emotion == "energetic":
                pitch = 60
                speed = 190
            
            subprocess.run([
                "espeak", 
                "-w", output_file, 
                "-p", str(pitch),
                "-s", str(speed),
                text
            ], check=True)

        # Check if the file was created
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"Audio generated successfully using system TTS with {emotion} emotion: {output_file}")
            return True
        else:
            print(f"Audio file not created or empty: {output_file}")
            return False
    except Exception as e:
        print(f"Error generating audio with system TTS: {e}")
        traceback.print_exc()
        return False

def get_rate_for_emotion(emotion):
    """Get speech rate for emotion (Windows TTS)"""
    rates = {
        "excited": 2,
        "energetic": 1,
        "neutral": 0,
        "dramatic": -2,
        "calm": -3
    }
    return rates.get(emotion, 0)

def get_volume_for_emotion(emotion):
    """Get speech volume for emotion (Windows TTS)"""
    volumes = {
        "excited": 90,
        "energetic": 85,
        "neutral": 80,
        "dramatic": 75,
        "calm": 70
    }
    return volumes.get(emotion, 80)
