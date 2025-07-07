# MINIMAL PyInstaller hook for Whisper-timestamped
# Only includes essential dependencies to reduce build size

from PyInstaller.utils.hooks import collect_data_files
import os
import pathlib

# Minimal hidden imports - only what's actually needed
hiddenimports = [
    'whisper_timestamped', 'whisper',
    'numpy', 'torch',  # Essential for Whisper
    'soundfile', '_soundfile',
]

# Collect only essential data files
datas = []

try:
    import whisper_timestamped
    whisper_dir = os.path.dirname(whisper_timestamped.__file__)
    
    # Only include essential files
    for root, dirs, files in os.walk(whisper_dir):
        for file in files:
            if file.endswith(('.pt', '.pth', '.json')):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, whisper_dir)
                if rel_path == '.':
                    datas.append((full_path, 'whisper_timestamped'))
                else:
                    datas.append((full_path, os.path.join('whisper_timestamped', rel_path)))
    
    # Add Whisper models from cache (only tiny model)
    whisper_cache = pathlib.Path.home() / '.cache' / 'whisper'
    if whisper_cache.exists():
        tiny_model = whisper_cache / 'tiny.pt'
        if tiny_model.exists():
            datas.append((str(tiny_model), 'whisper_models'))
            
except ImportError:
    pass

print(f"Whisper minimal hook: {len(hiddenimports)} imports, {len(datas)} data files")
