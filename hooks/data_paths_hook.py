
"""
Runtime hook to set up data paths for various libraries
"""
import os
import sys

# When running as a frozen application
if getattr(sys, 'frozen', False):
    # Get the directory where the executable is located
    base_dir = os.path.dirname(sys.executable)
    
    # Set environment variables for data directories
    os.environ['LANGUAGE_TAGS_DATA'] = os.path.join(base_dir, 'language_tags', 'data')
    os.environ['ESPEAK_DATA_PATH'] = os.path.join(base_dir, 'espeakng_loader', 'espeak-ng-data')
    
    # Set up kokoro paths
    kokoro_dir = os.path.join(base_dir, 'huggingface', 'hub', 'models--hexgrad--Kokoro-82M', 'snapshots')
    if os.path.exists(kokoro_dir):
        snapshots = os.listdir(kokoro_dir)
        if snapshots:
            os.environ['KOKORO_MODEL_DIR'] = os.path.join(kokoro_dir, snapshots[0])
            print(f"Set KOKORO_MODEL_DIR to {os.environ['KOKORO_MODEL_DIR']}")
    
    print(f"Set LANGUAGE_TAGS_DATA to {os.environ['LANGUAGE_TAGS_DATA']}")
    print(f"Set ESPEAK_DATA_PATH to {os.environ['ESPEAK_DATA_PATH']}")
