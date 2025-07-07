# OPTIMIZED PyInstaller hook for Whisper-timestamped
# Research-based minimal approach to reduce build size and complexity

from PyInstaller.utils.hooks import collect_data_files
import os
import pathlib

print("🔧 Loading optimized Whisper-timestamped hook...")

# MINIMAL hidden imports - only what's absolutely required
hiddenimports = [
    # Core Whisper modules
    'whisper_timestamped', 'whisper',
    'whisper.model', 'whisper.audio', 'whisper.decoding',
    'whisper.tokenizer', 'whisper.normalizers',
    
    # Essential PyTorch (shared with Kokoro)
    'torch', 'torch.nn', 'torch.nn.functional',
    
    # Essential transformers (minimal subset, shared with Kokoro)
    'transformers.models.whisper',
    'transformers.tokenization_utils',
    
    # Essential audio I/O (shared with Kokoro)
    'soundfile', '_soundfile',
    
    # Essential scientific computing
    'numpy', 'scipy',
]

# EXCLUDE heavy optional dependencies that cause build issues
# These are commented out to show what we're NOT including:
excluded_heavy_deps = [
    # VAD (Voice Activity Detection) - heavy and optional
    # 'silero_vad',        # 200MB+ VAD model - not essential
    # 'onnxruntime',       # 100MB+ ONNX runtime - not essential
    # 'onnx',              # 50MB+ ONNX format - not essential
    # 'webrtcvad',         # 20MB+ WebRTC VAD - not essential
    # 'auditok',           # 10MB+ audio tokenization - not essential
    
    # Heavy audio processing - optional
    # 'librosa',           # 150MB+ audio processing - not essential for basic transcription
    # 'librosa.core',      # Heavy core functions
    # 'librosa.feature',   # Heavy feature extraction
    # 'librosa.filters',   # Heavy filter functions
    
    # Heavy scientific computing - optional
    # 'numba',             # 100MB+ JIT compilation - not essential
    # 'numba.core',        # Heavy core functions
    # 'numba.typed',       # Heavy typed containers
    
    # Heavy tokenization - optional
    # 'tokenizers',        # 50MB+ fast tokenizers - not essential for basic use
    # 'tokenizers.implementations',
    
    # Heavy torch audio - optional
    # 'torchaudio',        # 100MB+ torch audio - not essential
    # 'torchaudio.transforms',
    # 'torchaudio.functional',
]

# Collect only essential data files
datas = []

try:
    import whisper_timestamped
    whisper_dir = os.path.dirname(whisper_timestamped.__file__)
    
    # Only include essential configuration files (not model files - those are handled separately)
    for root, dirs, files in os.walk(whisper_dir):
        for file in files:
            if file.endswith(('.json', '.txt', '.yaml', '.yml')):  # Config files only
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, whisper_dir)
                if rel_path == '.':
                    datas.append((full_path, 'whisper_timestamped'))
                else:
                    datas.append((full_path, os.path.join('whisper_timestamped', rel_path)))
    
    print(f"✅ Whisper optimized hook: {len(hiddenimports)} imports, {len(datas)} data files")
    print(f"❌ Excluded {len(excluded_heavy_deps)} heavy dependencies for size optimization")
                    
except ImportError:
    print("⚠️  Whisper-timestamped not available - hook will be skipped")
    pass

# Note: Model files (tiny.pt) are handled in the main spec file
# This separation allows for better control over what gets bundled
