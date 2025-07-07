from PyInstaller.utils.hooks import collect_dynamic_libs
import os
import sys
import shutil
import soundfile

datas = []
binaries = []
hiddenimports = ['_soundfile', 'cffi', '_cffi_backend', 'kokoro']

# Get the directory where soundfile's DLLs are stored
soundfile_dir = os.path.dirname(soundfile.__file__)
soundfile_data_dir = os.path.join(os.path.dirname(soundfile_dir), '_soundfile_data')

if os.path.exists(soundfile_data_dir):
    # Find all DLL files in the _soundfile_data directory
    for file in os.listdir(soundfile_data_dir):
        if file.endswith('.dll'):
            source_path = os.path.join(soundfile_data_dir, file)
            # Add to binaries with the correct destination path
            binaries.append((source_path, '.'))  # Put DLLs in the root directory
            print(f"Added soundfile DLL: {source_path}")
