"""
Audio Service - Handles audio generation functionality
"""
import os
import sys

# Add the parent directory to the path to find voice_ai
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from voice_ai import generateAudio

def generate_audio(text, voice_actor=None, speed=0.8, output_file="voice.mp3"):
    """
    Generate audio from text
    
    Args:
        text: The text to convert to speech
        voice_actor: Voice actor to use (optional)
        speed: Speed of speech (default: 0.8)
        output_file: Path to save the generated audio
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not text:
        print("No text input provided.")
        return False
        
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    return generateAudio(text, voice_actor, speed, output_file)
