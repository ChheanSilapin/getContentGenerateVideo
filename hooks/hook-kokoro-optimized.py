# OPTIMIZED PyInstaller hook for Kokoro TTS
# Research-based minimal approach to reduce build size and complexity

from PyInstaller.utils.hooks import collect_data_files
import os
import pathlib

print("🔧 Loading optimized Kokoro TTS hook...")

# MINIMAL hidden imports - only what's absolutely required
hiddenimports = [
    # Core Kokoro module
    'kokoro',
    
    # Essential audio I/O
    'soundfile', '_soundfile', 'cffi', '_cffi_backend',
    
    # Essential PyTorch (shared with Whisper)
    'torch', 'torch.nn', 'torch.nn.functional',
    
    # Essential transformers (minimal subset)
    'transformers',
    'transformers.models',
    'transformers.tokenization_utils',
    
    # Essential HuggingFace Hub
    'huggingface_hub',
    'huggingface_hub.utils',
    
    # Essential scientific computing
    'numpy',
]

# EXCLUDE heavy optional dependencies that cause build issues
# These are commented out to show what we're NOT including:
excluded_heavy_deps = [
    # 'librosa',           # 150MB+ audio processing - not essential
    # 'resampy',           # 50MB+ resampling - not essential  
    # 'numba',             # 100MB+ JIT compilation - not essential
    # 'phonemizer',        # 50MB+ text processing - not essential
    # 'segments',          # 30MB+ segmentation - not essential
    # 'misaki',            # 20MB+ text processing - not essential
    # 'language_tags',     # 10MB+ language detection - not essential
]

# Collect only essential data files
datas = []

try:
    import kokoro
    kokoro_dir = os.path.dirname(kokoro.__file__)
    
    # Only include essential configuration files (not model files - those are handled separately)
    for root, dirs, files in os.walk(kokoro_dir):
        for file in files:
            if file.endswith(('.json', '.txt', '.yaml', '.yml')):  # Config files only
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, kokoro_dir)
                if rel_path == '.':
                    datas.append((full_path, 'kokoro'))
                else:
                    datas.append((full_path, os.path.join('kokoro', rel_path)))
    
    print(f"✅ Kokoro optimized hook: {len(hiddenimports)} imports, {len(datas)} data files")
    print(f"❌ Excluded {len(excluded_heavy_deps)} heavy dependencies for size optimization")
                    
except ImportError:
    print("⚠️  Kokoro not available - hook will be skipped")
    pass

# Note: Model files (kokoro-v1_0.pth, voices/*.pt) are handled in the main spec file
# This separation allows for better control over what gets bundled
