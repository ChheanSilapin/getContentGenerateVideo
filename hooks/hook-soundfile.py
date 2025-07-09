import os
import soundfile

# CUSTOM HOOK - Override built-in soundfile hook
print("🔧 CUSTOM soundfile hook loading...")

datas = []
binaries = []
hiddenimports = ['_soundfile', 'cffi', '_cffi_backend', 'kokoro']

# Get the directory where soundfile's DLLs are stored
soundfile_dir = os.path.dirname(soundfile.__file__)
soundfile_data_dir = os.path.join(os.path.dirname(soundfile_dir), '_soundfile_data')

# Check for DLLs in the standard _soundfile_data directory
if os.path.exists(soundfile_data_dir):
    # Find all DLL files in the _soundfile_data directory
    for file in os.listdir(soundfile_data_dir):
        if file.endswith('.dll'):
            source_path = os.path.join(soundfile_data_dir, file)
            # Add to binaries with the correct destination path
            binaries.append((source_path, '.'))  # Put DLLs in the root directory
            print(f"Added soundfile DLL from _soundfile_data: {source_path}")

# Also check for libsndfile DLLs in the project root directory
# This handles cases where the DLL is manually placed in the project root
# Get the actual project root by going up from the hooks directory
import sys
if hasattr(sys, '_MEIPASS'):
    # Running in PyInstaller bundle
    project_root = sys._MEIPASS
else:
    # Running in development - get the directory containing the hooks folder
    hooks_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(hooks_dir)

libsndfile_dlls = ['libsndfile.dll', 'libsndfile_x64.dll']

print(f"Hook: Looking for DLLs in project root: {project_root}")
for dll_name in libsndfile_dlls:
    dll_path = os.path.join(project_root, dll_name)
    print(f"Hook: Checking for {dll_name} at: {dll_path}")
    if os.path.exists(dll_path):
        binaries.append((dll_path, '.'))  # Put DLL in the root directory
        print(f"Hook: Added libsndfile DLL from project root: {dll_path}")
    else:
        print(f"Hook: {dll_name} not found at {dll_path}")

print(f"Total soundfile binaries added: {len(binaries)}")
