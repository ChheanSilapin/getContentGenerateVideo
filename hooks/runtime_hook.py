"""
Enhanced Runtime hook for Video Generator v1.0.9
Sets up paths and environment for TTS and speech recognition components
"""
import os
import sys
import ctypes

# When running as a frozen application
if getattr(sys, 'frozen', False):
    # Get the directory where the executable is located
    base_dir = os.path.dirname(sys.executable)

    # Add the base directory to PATH for DLL loading
    os.environ['PATH'] = base_dir + os.pathsep + os.environ.get('PATH', '')

    # Set up cache directories for models
    cache_dir = os.path.join(base_dir, 'cache')
    os.makedirs(cache_dir, exist_ok=True)

    # Set environment variables for model caches
    os.environ['TRANSFORMERS_CACHE'] = cache_dir
    os.environ['HF_HOME'] = cache_dir
    os.environ['TORCH_HOME'] = cache_dir
    os.environ['WHISPER_CACHE'] = os.path.join(cache_dir, 'whisper')

    # Set up Kokoro TTS paths
    kokoro_model_dir = os.path.join(base_dir, 'huggingface', 'hub', 'models--hexgrad--Kokoro-82M')
    if os.path.exists(kokoro_model_dir):
        os.environ['KOKORO_MODEL_PATH'] = kokoro_model_dir
        # Find the snapshot directory
        snapshots_dir = os.path.join(kokoro_model_dir, 'snapshots')
        if os.path.exists(snapshots_dir):
            snapshots = os.listdir(snapshots_dir)
            if snapshots:
                os.environ['KOKORO_SNAPSHOT_PATH'] = os.path.join(snapshots_dir, snapshots[0])

    # Set up Whisper model paths
    whisper_models_dir = os.path.join(base_dir, 'whisper_models')
    if os.path.exists(whisper_models_dir):
        os.environ['WHISPER_MODELS_PATH'] = whisper_models_dir

    # Preload critical DLLs to avoid loading issues
    critical_dlls = ['libsndfile.dll', 'libsndfile_x64.dll']
    for dll_name in critical_dlls:
        dll_path = os.path.join(base_dir, dll_name)
        if os.path.exists(dll_path):
            try:
                ctypes.CDLL(dll_path)
                print(f"Runtime hook: Preloaded {dll_name}")
            except Exception as e:
                print(f"Runtime hook: Failed to preload {dll_name}: {e}")

    # Set up data paths for various libraries
    data_paths = {
        'LANGUAGE_TAGS_DATA': os.path.join(base_dir, 'language_tags', 'data'),
        'ESPEAK_DATA_PATH': os.path.join(base_dir, 'espeakng_loader', 'espeak-ng-data'),
        'PHONEMIZER_ESPEAK_PATH': os.path.join(base_dir, 'espeakng_loader'),
    }

    for env_var, path in data_paths.items():
        if os.path.exists(path):
            os.environ[env_var] = path
            print(f"Runtime hook: Set {env_var} to {path}")

    print(f"Runtime hook: Initialized Video Generator v1.0.9 environment")
    print(f"Runtime hook: Base directory: {base_dir}")
    print(f"Runtime hook: Cache directory: {cache_dir}")