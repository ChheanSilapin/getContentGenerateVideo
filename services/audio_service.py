"""
Audio service for generating speech from text with gTTS and Vosk speech recognition
"""
from utils.common_imports import os, sys, subprocess, traceback
import platform
import re
import emoji
import tempfile
import io

# Try to import gTTS for text-to-speech
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("gTTS not available. Will use system TTS as fallback.")

# Try to import Vosk for speech recognition
try:
    import vosk
    import json
    import pyaudio
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Vosk or PyAudio not available. Speech recognition will be disabled.")

# Try to import pydub for audio processing
try:
    from pydub import AudioSegment
    from pydub.playback import play
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("pydub not available. Some audio processing features may be limited.")

# Import from utils
from utils.helpers import ensure_directory_exists
from utils.text_processing import process_text_for_tts

def generate_audio(text, output_file, voice_actor=None, speed=0.8, emotion="neutral", language='en'):
    """
    Generate audio from text using gTTS with emotional expression

    Args:
        text: Text to convert to speech
        output_file: Path to output audio file
        voice_actor: Optional voice actor to use (for gTTS, this affects language/accent)
        speed: Speed of speech (0.5 to 2.0, with 1.0 being normal speed)
        emotion: Emotion to apply ("neutral", "excited", "dramatic", "calm", "energetic")
        language: Language code for gTTS (default: 'en')

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
    if GTTS_AVAILABLE:
        if generate_audio_gtts(processed_text, output_file, speed, emotion, language, voice_actor):
            return True

    # Fallback to system TTS
    return generate_audio_system_emotional(processed_text, output_file, emotion)

def generate_audio_gtts(text, output_file, speed=0.8, emotion="neutral", language='en', voice_actor=None):
    """
    Generate audio using gTTS with emotional settings and speed adjustment

    Args:
        text: Text to convert to speech
        output_file: Path to output audio file
        speed: Speed of speech (0.5 to 2.0, with 1.0 being normal speed)
        emotion: Emotion to apply
        language: Language code for gTTS
        voice_actor: Voice actor preference (affects language/accent selection)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Map voice_actor to language variants if available
        lang_code = get_language_for_voice_actor(voice_actor, language)

        # Adjust text based on emotion for better gTTS output
        emotional_text = enhance_text_for_emotion(text, emotion)

        print(f"Generating audio with gTTS using language: {lang_code}")
        print(f"Emotion: {emotion}, Speed: {speed}")

        # Create gTTS object
        tts = gTTS(text=emotional_text, lang=lang_code, slow=False)

        # Save to temporary file first (gTTS saves as MP3)
        temp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_mp3.close()

        try:
            # Generate the audio file
            tts.save(temp_mp3.name)
            print(f"gTTS audio saved to temporary file: {temp_mp3.name}")

            # Convert and adjust speed if needed
            if PYDUB_AVAILABLE and speed != 1.0:
                # Load the MP3 file
                audio = AudioSegment.from_mp3(temp_mp3.name)

                # Adjust speed (playback rate)
                if speed != 1.0:
                    # Speed up or slow down the audio
                    new_sample_rate = int(audio.frame_rate * speed)
                    audio_with_speed = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate})
                    audio = audio_with_speed.set_frame_rate(audio.frame_rate)

                # Apply emotional adjustments
                audio = apply_emotional_effects(audio, emotion)

                # Export to the desired format
                if output_file.lower().endswith('.mp3'):
                    audio.export(output_file, format="mp3")
                elif output_file.lower().endswith('.wav'):
                    audio.export(output_file, format="wav")
                else:
                    # Default to WAV for compatibility
                    audio.export(output_file, format="wav")

            else:
                # No speed adjustment needed, just copy/convert the file
                if PYDUB_AVAILABLE:
                    audio = AudioSegment.from_mp3(temp_mp3.name)
                    audio = apply_emotional_effects(audio, emotion)

                    if output_file.lower().endswith('.mp3'):
                        audio.export(output_file, format="mp3")
                    else:
                        audio.export(output_file, format="wav")
                else:
                    # Simple file copy if pydub not available
                    import shutil
                    if output_file.lower().endswith('.mp3'):
                        shutil.copy2(temp_mp3.name, output_file)
                    else:
                        # Can't convert without pydub, keep as MP3
                        shutil.copy2(temp_mp3.name, output_file.rsplit('.', 1)[0] + '.mp3')

            # Clean up temporary file
            try:
                os.unlink(temp_mp3.name)
            except:
                pass

            # Verify the file was created
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"Audio generated successfully with gTTS ({emotion} emotion): {output_file}")
                return True
            else:
                print(f"Error: Audio file not created or empty: {output_file}")
                return False

        except Exception as e:
            # Clean up temporary file on error
            try:
                os.unlink(temp_mp3.name)
            except:
                pass
            raise e

    except Exception as e:
        print(f"Error generating audio with gTTS: {e}")
        traceback.print_exc()
        return False

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

def get_language_for_voice_actor(voice_actor, default_language='en'):
    """Map voice actor preferences to gTTS language codes"""
    if not voice_actor or voice_actor == "Default":
        return default_language

    # Map common voice actor preferences to language variants
    voice_mapping = {
        "British": "en-uk",
        "American": "en-us",
        "Australian": "en-au",
        "Canadian": "en-ca",
        "Indian": "en-in",
        "French": "fr",
        "German": "de",
        "Spanish": "es",
        "Italian": "it",
        "Portuguese": "pt",
        "Russian": "ru",
        "Japanese": "ja",
        "Korean": "ko",
        "Chinese": "zh"
    }

    return voice_mapping.get(voice_actor, default_language)

def enhance_text_for_emotion(text, emotion):
    """Enhance text for better emotional expression with gTTS"""
    if emotion == "excited":
        # Add emphasis and exclamation
        text = text.replace(".", "!")
        text = text.replace("?", "?!")
        # Add pauses for emphasis
        text = text.replace(",", ", ")

    elif emotion == "dramatic":
        # Add dramatic pauses
        text = text.replace(".", "... ")
        text = text.replace("!", "... ")
        text = text.replace(",", "... ")

    elif emotion == "calm":
        # Add gentle pauses
        text = text.replace(".", ". ")
        text = text.replace(",", ", ")
        text = text.replace("!", ".")  # Convert exclamations to periods

    elif emotion == "energetic":
        # Add energy with varied punctuation
        text = text.replace(".", "!")
        text = text.replace(",", ", ")

    return text

def apply_emotional_effects(audio, emotion):
    """Apply audio effects to enhance emotional expression"""
    if not PYDUB_AVAILABLE:
        return audio

    try:
        if emotion == "excited":
            # Increase volume and add slight pitch variation
            audio = audio + 3  # Increase volume by 3dB

        elif emotion == "dramatic":
            # Lower volume slightly and add reverb effect (simulated)
            audio = audio - 2  # Decrease volume by 2dB

        elif emotion == "calm":
            # Lower volume for calming effect
            audio = audio - 4  # Decrease volume by 4dB

        elif emotion == "energetic":
            # Slight volume boost
            audio = audio + 2  # Increase volume by 2dB

        return audio

    except Exception as e:
        print(f"Warning: Could not apply emotional effects: {e}")
        return audio

# Speech Recognition Functions using Vosk
def initialize_speech_recognition(model_path=None, language="en-us"):
    """
    Initialize Vosk speech recognition

    Args:
        model_path: Path to Vosk model directory (optional)
        language: Language code for recognition

    Returns:
        tuple: (model, recognizer) or (None, None) if failed
    """
    if not VOSK_AVAILABLE:
        print("Vosk not available for speech recognition")
        return None, None

    try:
        # Set log level to reduce Vosk output
        vosk.SetLogLevel(-1)

        if model_path and os.path.exists(model_path):
            model = vosk.Model(model_path)
        else:
            # Try to find a default model
            default_models = [
                f"vosk-model-{language}",
                f"vosk-model-small-{language}",
                "vosk-model-en-us-0.22",
                "vosk-model-small-en-us-0.15"
            ]

            model = None
            for model_name in default_models:
                try:
                    model = vosk.Model(model_name)
                    print(f"Using Vosk model: {model_name}")
                    break
                except:
                    continue

            if not model:
                print("No Vosk model found. Please download a model from https://alphacephei.com/vosk/models")
                return None, None

        recognizer = vosk.KaldiRecognizer(model, 16000)
        print("Speech recognition initialized successfully")
        return model, recognizer

    except Exception as e:
        print(f"Error initializing speech recognition: {e}")
        return None, None

def recognize_speech_from_microphone(duration=5, model=None, recognizer=None):
    """
    Recognize speech from microphone using Vosk

    Args:
        duration: Recording duration in seconds
        model: Vosk model (optional, will initialize if not provided)
        recognizer: Vosk recognizer (optional, will initialize if not provided)

    Returns:
        str: Recognized text or empty string if failed
    """
    if not VOSK_AVAILABLE:
        print("Vosk not available for speech recognition")
        return ""

    # Initialize if not provided
    if not model or not recognizer:
        model, recognizer = initialize_speech_recognition()
        if not model or not recognizer:
            return ""

    try:
        # Initialize PyAudio
        p = pyaudio.PyAudio()

        # Open microphone stream
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000
        )

        print(f"Recording for {duration} seconds...")

        # Record and recognize
        for _ in range(0, int(16000 / 8000 * duration)):
            data = stream.read(8000)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                if result.get('text'):
                    print(f"Recognized: {result['text']}")

        # Get final result
        final_result = json.loads(recognizer.FinalResult())
        recognized_text = final_result.get('text', '')

        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()

        print(f"Final recognized text: {recognized_text}")
        return recognized_text

    except Exception as e:
        print(f"Error during speech recognition: {e}")
        return ""

def recognize_speech_from_file(audio_file, model=None, recognizer=None):
    """
    Recognize speech from audio file using Vosk

    Args:
        audio_file: Path to audio file
        model: Vosk model (optional, will initialize if not provided)
        recognizer: Vosk recognizer (optional, will initialize if not provided)

    Returns:
        str: Recognized text or empty string if failed
    """
    if not VOSK_AVAILABLE or not PYDUB_AVAILABLE:
        print("Vosk or pydub not available for speech recognition")
        return ""

    # Initialize if not provided
    if not model or not recognizer:
        model, recognizer = initialize_speech_recognition()
        if not model or not recognizer:
            return ""

    try:
        # Load audio file and convert to required format
        audio = AudioSegment.from_file(audio_file)

        # Convert to mono, 16kHz, 16-bit
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)

        # Get raw audio data
        raw_data = audio.raw_data

        # Process audio in chunks
        chunk_size = 8000
        recognized_text = ""

        for i in range(0, len(raw_data), chunk_size):
            chunk = raw_data[i:i+chunk_size]
            if recognizer.AcceptWaveform(chunk):
                result = json.loads(recognizer.Result())
                if result.get('text'):
                    recognized_text += result['text'] + " "

        # Get final result
        final_result = json.loads(recognizer.FinalResult())
        if final_result.get('text'):
            recognized_text += final_result['text']

        recognized_text = recognized_text.strip()
        print(f"Recognized text from file: {recognized_text}")
        return recognized_text

    except Exception as e:
        print(f"Error recognizing speech from file: {e}")
        return ""
