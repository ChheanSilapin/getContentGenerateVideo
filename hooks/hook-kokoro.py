# PyInstaller hook for Kokoro TTS - ENHANCED VERSION for v1.0.9
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs
import os
import pathlib

# Collect all Kokoro submodules
hiddenimports = collect_submodules('kokoro')
datas = collect_data_files('kokoro')
binaries = collect_dynamic_libs('kokoro')

# Enhanced hidden imports for Kokoro TTS
hiddenimports.extend([
    # Core dependencies
    'soundfile', '_soundfile', 'cffi', '_cffi_backend',
    'torch', 'torch.nn', 'torch.nn.functional', 'torch.jit',
    'numpy', 'scipy', 'scipy.signal',

    # Kokoro-specific dependencies (correct module names)
    'kokoro', 'kokoro.models', 'kokoro.utils',
    'kokoro.phonemizer', 'kokoro.tokenizer',

    # Audio processing
    'librosa', 'librosa.core', 'librosa.feature',
    'resampy', 'numba', 'numba.core',

    # Text processing for TTS
    'phonemizer', 'phonemizer.backend',
    'segments', 'segments.tokenizer',
    'misaki', 'misaki.en', 'misaki.espeak',

    # Additional dependencies
    'transformers', 'transformers.models',
    'huggingface_hub', 'huggingface_hub.utils',
])

try:
    import kokoro
    kokoro_dir = os.path.dirname(kokoro.__file__)

    for file in os.listdir(kokoro_dir):
        if file.endswith(('.pt', '.pth', '.bin', '.json', '.yaml', '.yml', '.wav', '.mp3', '.txt')):
            full_path = os.path.join(kokoro_dir, file)
            datas.append((full_path, 'kokoro'))
            if file.endswith(('.dll', '.so', '.dylib')):
                binaries.append((full_path, 'kokoro'))

    for root, dirs, files in os.walk(kokoro_dir):
        for file in files:
            if 'time' in file.lower() or 'timing' in file.lower() or 'phoneme' in file.lower():
                full_path = os.path.join(root, file)
                datas.append((full_path, os.path.join('kokoro', os.path.relpath(root, kokoro_dir))))

    # Add Hugging Face cache for Kokoro models
    hf_cache_dir = pathlib.Path.home() / '.cache' / 'huggingface'
    kokoro_model_dir = hf_cache_dir / 'hub' / 'models--hexgrad--Kokoro-82M'
    
    if kokoro_model_dir.exists():
        # Find the snapshot directory (it has a hash name)
        for snapshot_dir in kokoro_model_dir.glob('snapshots/*'):
            if snapshot_dir.is_dir():
                # Add the main model file
                main_model = snapshot_dir / 'kokoro-v1_0.pth'
                if main_model.exists():
                    datas.append((str(main_model), 'huggingface/hub/models--hexgrad--Kokoro-82M/snapshots/' + snapshot_dir.name))
                
                # Add the config file
                config_file = snapshot_dir / 'config.json'
                if config_file.exists():
                    datas.append((str(config_file), 'huggingface/hub/models--hexgrad--Kokoro-82M/snapshots/' + snapshot_dir.name))
                
                # Add voice model files
                voices_dir = snapshot_dir / 'voices'
                if voices_dir.exists():
                    for voice_file in voices_dir.glob('*.pt'):
                        datas.append((str(voice_file), 'huggingface/hub/models--hexgrad--Kokoro-82M/snapshots/' + snapshot_dir.name + '/voices'))

except ImportError:
    pass
