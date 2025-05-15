"""
Audio service for generating speech from text
"""
import os
import sys
import platform
import subprocess

def generate_audio(text, output_file):
    """
    Generate audio from text
    
    Args:
        text: Text to convert to speech
        output_file: Path to output audio file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Import the voice_ai module
        try:
            from voice_ai import generateAudio
            print(f"Generating audio for text: {text[:50]}...")
            result = generateAudio(text, output_file)
            
            # Check if the file was created
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"Audio generated successfully: {output_file}")
                return True
            else:
                print(f"Audio file not created or empty: {output_file}")
                return False
                
        except ImportError:
            print("Error importing voice_ai module. Trying fallback method.")
            
            # Fallback to system text-to-speech
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
        print(f"Error generating audio: {e}")
        return False

