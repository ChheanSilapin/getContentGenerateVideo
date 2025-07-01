# PyInstaller hook for whisper-timestamped
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules
import os

# Collect all whisper-timestamped data files and submodules
datas = collect_data_files('whisper_timestamped')
binaries = collect_dynamic_libs('whisper_timestamped')

# Collect all submodules
hiddenimports = collect_submodules('whisper_timestamped')

# Add openai-whisper dependencies
try:
    import whisper
    whisper_datas = collect_data_files('whisper')
    whisper_binaries = collect_dynamic_libs('whisper')
    whisper_hiddenimports = collect_submodules('whisper')
    
    datas.extend(whisper_datas)
    binaries.extend(whisper_binaries)
    hiddenimports.extend(whisper_hiddenimports)
except ImportError:
    pass

# Add PyTorch dependencies for whisper
hiddenimports.extend([
    'torch',
    'torch.nn',
    'torch.nn.functional',
    'torch.optim',
    'torch.utils',
    'torch.utils.data',
    'torch.jit',
    'torch.hub',
    'torchaudio',
    'torchaudio.transforms',
    'torchaudio.functional',
    'numba',
    'numba.core',
    'numba.typed',
    'tiktoken',
    'tiktoken.core',
    'regex',
    'ftfy',
    'more_itertools'
])

# Ensure whisper models can be found
try:
    import whisper
    whisper_dir = os.path.dirname(whisper.__file__)
    
    # Add whisper assets
    assets_dir = os.path.join(whisper_dir, 'assets')
    if os.path.exists(assets_dir):
        datas.append((assets_dir, 'whisper/assets'))
        
except ImportError:
    pass
