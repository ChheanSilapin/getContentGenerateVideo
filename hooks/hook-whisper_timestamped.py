# PyInstaller hook for Whisper-timestamped - ENHANCED VERSION for v1.0.9
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs
import os
import pathlib

# Collect all whisper-timestamped submodules
hiddenimports = collect_submodules('whisper_timestamped')
datas = collect_data_files('whisper_timestamped')
binaries = collect_dynamic_libs('whisper_timestamped')

# Enhanced hidden imports for Whisper-timestamped
hiddenimports.extend([
    # Core Whisper dependencies
    'whisper', 'whisper.model', 'whisper.audio', 'whisper.decoding',
    'whisper.tokenizer', 'whisper.normalizers',

    # Transformers and tokenizers
    'transformers', 'transformers.models', 'transformers.models.whisper',
    'transformers.tokenization_utils', 'transformers.tokenization_utils_base',
    'tokenizers', 'tokenizers.implementations',

    # Audio processing
    'torch', 'torch.nn', 'torch.nn.functional', 'torch.jit',
    'torchaudio', 'torchaudio.transforms', 'torchaudio.functional',
    'librosa', 'librosa.core', 'librosa.feature', 'librosa.filters',
    'soundfile', '_soundfile', 'cffi', '_cffi_backend',

    # VAD (Voice Activity Detection)
    'silero_vad', 'onnxruntime', 'onnx',
    'webrtcvad', 'auditok',

    # Scientific computing
    'numpy', 'scipy', 'scipy.signal', 'scipy.ndimage',
    'numba', 'numba.core', 'numba.typed',

    # Additional dependencies
    'regex', 'ftfy', 'more_itertools',
    'huggingface_hub', 'huggingface_hub.utils',
])

try:
    import whisper_timestamped
    whisper_dir = os.path.dirname(whisper_timestamped.__file__)

    # Add all data files from whisper_timestamped
    for root, dirs, files in os.walk(whisper_dir):
        for file in files:
            if file.endswith(('.pt', '.pth', '.json', '.txt', '.yaml', '.yml')):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, whisper_dir)
                if rel_path == '.':
                    datas.append((full_path, 'whisper_timestamped'))
                else:
                    datas.append((full_path, os.path.join('whisper_timestamped', rel_path)))

    # Add Whisper models from cache
    whisper_cache = pathlib.Path.home() / '.cache' / 'whisper'
    if whisper_cache.exists():
        for model_file in whisper_cache.glob('*.pt'):
            datas.append((str(model_file), 'whisper_models'))

except ImportError:
    pass