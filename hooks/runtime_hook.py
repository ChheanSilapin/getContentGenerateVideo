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

    # CRITICAL FIX: Point HuggingFace to the actual model location
    # Check if models are in the new structure (models/kokoro/Kokoro-82M)
    kokoro_model_dir = os.path.join(base_dir, 'models', 'kokoro', 'Kokoro-82M')
    if os.path.exists(kokoro_model_dir):
        # Create HuggingFace cache structure pointing to our models
        hf_cache_dir = os.path.join(base_dir, 'huggingface')
        hf_hub_dir = os.path.join(hf_cache_dir, 'hub')
        hf_model_dir = os.path.join(hf_hub_dir, 'models--hexgrad--Kokoro-82M')

        # Set up environment variables
        os.environ['HF_HOME'] = hf_cache_dir
        os.environ['TRANSFORMERS_CACHE'] = hf_cache_dir
        os.environ['HUGGINGFACE_HUB_CACHE'] = hf_hub_dir

        # Create symlink or copy structure if needed
        try:
            os.makedirs(hf_hub_dir, exist_ok=True)
            if not os.path.exists(hf_model_dir):
                # Create a symlink to the actual model directory
                if hasattr(os, 'symlink'):
                    os.symlink(kokoro_model_dir, hf_model_dir)
                    print(f"Runtime hook: Created symlink from {kokoro_model_dir} to {hf_model_dir}")
                else:
                    # Fallback: set environment variable to point directly to model
                    os.environ['KOKORO_MODEL_PATH'] = kokoro_model_dir
                    print(f"Runtime hook: Set KOKORO_MODEL_PATH to {kokoro_model_dir}")

            print(f"Runtime hook: Using Kokoro models from: {kokoro_model_dir}")
            print(f"Runtime hook: HuggingFace cache: {hf_cache_dir}")

        except Exception as e:
            print(f"Runtime hook: Error setting up Kokoro paths: {e}")
            # Fallback: set direct path
            os.environ['KOKORO_MODEL_PATH'] = kokoro_model_dir

    # Legacy: Check for old HuggingFace structure
    hf_bundled_dir = os.path.join(base_dir, 'huggingface')
    if os.path.exists(hf_bundled_dir) and not os.path.exists(kokoro_model_dir):
        os.environ['HF_HOME'] = hf_bundled_dir
        os.environ['TRANSFORMERS_CACHE'] = hf_bundled_dir
        os.environ['HUGGINGFACE_HUB_CACHE'] = hf_bundled_dir
        print(f"Runtime hook: Using legacy bundled HF models: {hf_bundled_dir}")

    # Point Whisper to bundled models
    whisper_bundled_dir = os.path.join(base_dir, 'whisper_models')
    if os.path.exists(whisper_bundled_dir):
        os.environ['TORCH_HOME'] = whisper_bundled_dir
        os.environ['WHISPER_CACHE'] = whisper_bundled_dir
        print(f"Runtime hook: Using bundled Whisper models: {whisper_bundled_dir}")

    # Set up Whisper model paths (additional check)
    whisper_models_dir = os.path.join(base_dir, 'whisper_models')
    if os.path.exists(whisper_models_dir):
        os.environ['WHISPER_MODELS_PATH'] = whisper_models_dir
        # List available models for debugging
        try:
            models = os.listdir(whisper_models_dir)
            print(f"Runtime hook: Available Whisper models: {models}")
        except:
            print("Runtime hook: Could not list Whisper models")

    # Preload critical DLLs to avoid loading issues
    critical_dlls = ['libsndfile.dll', 'libsndfile_x64.dll']
    for dll_name in critical_dlls:
        # Check multiple possible locations for DLLs
        dll_locations = [
            os.path.join(base_dir, dll_name),  # Root directory (preferred)
            os.path.join(base_dir, '_internal', dll_name),  # _internal directory (fallback)
            os.path.join(os.path.dirname(base_dir), dll_name),  # Parent directory
        ]

        dll_loaded = False
        for dll_path in dll_locations:
            if os.path.exists(dll_path):
                try:
                    # Try to load the DLL
                    handle = ctypes.CDLL(dll_path)
                    print(f"Runtime hook: Successfully preloaded {dll_name} from {dll_path}")
                    dll_loaded = True

                    # Also add the directory to PATH for future DLL loading
                    dll_dir = os.path.dirname(dll_path)
                    if dll_dir not in os.environ.get('PATH', ''):
                        os.environ['PATH'] = dll_dir + os.pathsep + os.environ.get('PATH', '')
                    break
                except Exception as e:
                    print(f"Runtime hook: Failed to preload {dll_name} from {dll_path}: {e}")
                    continue

        if not dll_loaded:
            print(f"Runtime hook: {dll_name} not found in any location")
            # List all DLL files in base_dir for debugging
            try:
                dll_files = [f for f in os.listdir(base_dir) if f.lower().endswith('.dll')]
                print(f"Runtime hook: Available DLLs in {base_dir}: {dll_files}")
            except:
                pass

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