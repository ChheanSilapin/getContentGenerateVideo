# PyInstaller hook for Vosk speech recognition library
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
import os

# Collect all Vosk data files and DLLs
datas = collect_data_files('vosk')
binaries = collect_dynamic_libs('vosk')

# Ensure Vosk DLLs are included
hiddenimports = ['vosk_cffi', '_cffi_backend']

# Add specific DLL paths if they exist
try:
    import vosk
    vosk_dir = os.path.dirname(vosk.__file__)
    
    # List of required DLL files for Vosk
    required_dlls = [
        'libvosk.dll',
        'libgcc_s_seh-1.dll', 
        'libstdc++-6.dll',
        'libwinpthread-1.dll'
    ]
    
    for dll in required_dlls:
        dll_path = os.path.join(vosk_dir, dll)
        if os.path.exists(dll_path):
            binaries.append((dll_path, 'vosk'))
            
except ImportError:
    pass
