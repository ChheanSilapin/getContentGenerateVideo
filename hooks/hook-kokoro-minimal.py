# MINIMAL PyInstaller hook for Kokoro TTS
# Only includes essential dependencies to reduce build size

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

# Collect only essential Kokoro modules
hiddenimports = [
    'kokoro',
    'soundfile', '_soundfile', 'cffi', '_cffi_backend',
    'numpy',
]

# Collect only essential data files
datas = []
try:
    import kokoro
    kokoro_dir = os.path.dirname(kokoro.__file__)
    
    # Only include essential model files (not all transformers data)
    for root, dirs, files in os.walk(kokoro_dir):
        for file in files:
            if file.endswith(('.json', '.txt', '.pt', '.pth')):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, kokoro_dir)
                if rel_path == '.':
                    datas.append((full_path, 'kokoro'))
                else:
                    datas.append((full_path, os.path.join('kokoro', rel_path)))
                    
except ImportError:
    pass

print(f"Kokoro minimal hook: {len(hiddenimports)} imports, {len(datas)} data files")
