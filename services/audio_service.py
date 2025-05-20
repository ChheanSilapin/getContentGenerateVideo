"""
Audio service for generating speech from text
"""
import os
import sys
import platform
import subprocess
import re
import emoji
import traceback

# Try to import pyttsx3 for TTS
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("pyttsx3 not available. Will use system TTS as fallback.")

# Import from utils
from utils.helpers import process_text_for_tts, ensure_directory_exists

def generate_audio(text, output_file, voice_actor=None, speed=0.8):
    """
    Generate audio from text

    Args:
        text: Text to convert to speech
        output_file: Path to output audio file
        voice_actor: Optional voice actor to use (not implemented in all backends)
        speed: Speed of speech (0.5 to 2.0, with 1.0 being normal speed)

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

    # Process text for TTS
    processed_text = process_text_for_tts(text)
    print(f"Processed text: {processed_text[:100]}...")

    # Try different TTS methods in order of preference
    if PYTTSX3_AVAILABLE:
        if generate_audio_pyttsx3(processed_text, output_file, speed):
            return True

    # Fallback to system TTS
    return generate_audio_system(processed_text, output_file)

def generate_audio_pyttsx3(text, output_file, speed=0.8):
    """
    Generate audio using pyttsx3

    Args:
        text: Text to convert to speech
        output_file: Path to output audio file
        speed: Speed of speech (0.5 to 2.0, with 1.0 being normal speed)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        engine = pyttsx3.init()
        rate = engine.getProperty('rate')
        engine.setProperty('rate', int(rate * speed))

        # Try to find an English voice
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
        print(f"Error generating audio with pyttsx3: {e}")
        traceback.print_exc()
        return False

def generate_audio_system(text, output_file):
    """
    Generate audio using system TTS

    Args:
        text: Text to convert to speech
        output_file: Path to output audio file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use system-specific TTS
        if platform.system() == "Windows":
            # Use PowerShell's text-to-speech
            ps_script = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{text}"); $speak.SetOutputToWaveFile("{output_file}"); $speak.Speak("{text}"); $speak.Dispose()'
            subprocess.run(["powershell", "-Command", ps_script], check=True)
        elif platform.system() == "Darwin":  # macOS
            # Use macOS say command
            subprocess.run(["say", "-o", output_file, text], check=True)
        else:  # Linux
            # Try using espeak
            subprocess.run(["espeak", "-w", output_file, text], check=True)

        # Check if the file was created
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"Audio generated successfully using system TTS: {output_file}")
            return True
        else:
            print(f"Audio file not created or empty: {output_file}")
            return False
    except Exception as e:
        print(f"Error generating audio with system TTS: {e}")
        traceback.print_exc()
        return False
