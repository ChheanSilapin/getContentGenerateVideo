"""
Portable Model Manager for Video Generator
Handles AI model downloads and management for portable installations
"""
import os
import sys
import json
import requests
import threading
from pathlib import Path
from typing import Dict, Callable, Optional
from utils.path_manager import get_application_paths, ensure_portable_directories


class PortableModelManager:
    """Manages AI models for portable Video Generator installation"""
    
    def __init__(self):
        self.paths = ensure_portable_directories()
        self.models_dir = self.paths['models_dir']
        self.config_file = os.path.join(self.paths['config_dir'], 'models_config.json')
        self.download_progress = {}
        self.download_threads = {}
        
        # Model configurations
        self.model_configs = {
            'whisper_tiny': {
                'name': 'Whisper Tiny',
                'url': 'https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt',
                'local_path': os.path.join(self.models_dir, 'whisper', 'tiny.pt'),
                'size_mb': 39,
                'required': True
            },
            'kokoro_82m': {
                'name': 'Kokoro TTS 82M',
                'huggingface_repo': 'hexgrad/Kokoro-82M',
                'local_path': os.path.join(self.models_dir, 'kokoro', 'Kokoro-82M'),
                'size_mb': 95,  # Full model + 3 voices (was 15 with voices only)
                'required': True,
                'download_full_model': True,  # Download complete model structure
                'voices_only': ['voices/am_michael.pt', 'voices/am_adam.pt', 'voices/af_heart.pt']  # Limit to these voices
            }
        }
        
        self.load_config()
    
    def load_config(self):
        """Load model configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.model_configs.update(config.get('models', {}))
        except Exception as e:
            print(f"Warning: Could not load model config: {e}")
    
    def save_config(self):
        """Save model configuration to file"""
        try:
            config = {
                'models': self.model_configs,
                'last_check': self.get_current_timestamp()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save model config: {e}")
    
    def get_current_timestamp(self):
        """Get current timestamp for tracking"""
        import time
        return int(time.time())
    
    def check_model_status(self) -> Dict[str, bool]:
        """Check which models are available locally"""
        status = {}

        for model_key, config in self.model_configs.items():
            local_path = config['local_path']

            # For all models, also check the executable's model directory
            # This handles the case where models were downloaded by the executable
            # but we're now running as a script
            if not getattr(sys, 'frozen', False):
                # Running as script - also check executable's model directory
                exe_model_path = local_path.replace(
                    os.path.join(self.paths['exe_dir'], 'models'),
                    os.path.join(self.paths['exe_dir'], 'dist', 'VideoGenerator_1.0.9', 'models')
                )
                if os.path.exists(exe_model_path):
                    local_path = exe_model_path

            if model_key == 'whisper_tiny':
                # Check for single file
                status[model_key] = os.path.exists(local_path)
            elif model_key == 'kokoro_82m':
                # Check for complete model structure
                download_full_model = config.get('download_full_model', False)
                voices_only = config.get('voices_only', [])

                if download_full_model:
                    # Check for complete model: core files + specific voices
                    core_files_exist = (
                        os.path.exists(local_path) and
                        os.path.isdir(local_path) and
                        # Check for essential model files (config, tokenizer, etc.)
                        any(f.endswith(('.json', '.txt', '.pt', '.bin'))
                            for f in os.listdir(local_path)
                            if os.path.isfile(os.path.join(local_path, f)))
                    )

                    voices_exist = all(
                        os.path.exists(os.path.join(local_path, voice_file))
                        for voice_file in voices_only
                    )

                    status[model_key] = core_files_exist and voices_exist
                elif voices_only:
                    # Legacy: check for specific voice files only
                    all_voices_exist = all(
                        os.path.exists(os.path.join(local_path, voice_file))
                        for voice_file in voices_only
                    )
                    status[model_key] = all_voices_exist
                else:
                    # Fallback: check for directory with any files
                    status[model_key] = (
                        os.path.exists(local_path) and
                        os.path.isdir(local_path) and
                        len(os.listdir(local_path)) > 0
                    )
            else:
                status[model_key] = os.path.exists(local_path)

        return status
    
    def get_missing_models(self) -> list:
        """Get list of missing required models"""
        status = self.check_model_status()
        missing = []
        
        for model_key, config in self.model_configs.items():
            if config.get('required', False) and not status.get(model_key, False):
                missing.append(model_key)
        
        return missing
    
    def is_setup_complete(self) -> bool:
        """Check if all required models are available"""
        return len(self.get_missing_models()) == 0
    
    def download_whisper_model(self, progress_callback: Optional[Callable] = None):
        """Download Whisper tiny model with retry and resume capability"""
        config = self.model_configs['whisper_tiny']
        url = config['url']
        local_path = config['local_path']

        # Ensure directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        return self._download_file_with_retry(url, local_path, 'whisper_tiny', progress_callback)

    def _download_file_with_retry(self, url: str, local_path: str, model_key: str,
                                  progress_callback: Optional[Callable] = None, max_retries: int = 3):
        """Download file with retry logic and resume capability"""

        for attempt in range(max_retries):
            try:
                # Check if partial file exists
                resume_pos = 0
                if os.path.exists(local_path):
                    resume_pos = os.path.getsize(local_path)

                # Set up headers for resume
                headers = {}
                if resume_pos > 0:
                    headers['Range'] = f'bytes={resume_pos}-'

                # Make request with timeout and headers
                response = requests.get(url, stream=True, timeout=60, headers=headers)

                # Handle partial content or full content
                if response.status_code == 206:  # Partial content
                    print("Resuming partial download...")
                    total_size = resume_pos + int(response.headers.get('content-length', 0))
                elif response.status_code == 200:  # Full content
                    print("Starting fresh download...")
                    total_size = int(response.headers.get('content-length', 0))
                    resume_pos = 0  # Start fresh
                else:
                    response.raise_for_status()

                print(f"Total size: {total_size} bytes ({total_size / (1024*1024):.1f} MB)")

                downloaded = resume_pos
                if progress_callback:
                    progress_callback(model_key, (downloaded / total_size) * 100 if total_size > 0 else 0, downloaded, total_size)

                # Open file in append mode if resuming, write mode if starting fresh
                mode = 'ab' if resume_pos > 0 and response.status_code == 206 else 'wb'

                with open(local_path, mode) as f:
                    last_progress_update = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # Update progress only every 1% or 1MB to reduce spam
                            if progress_callback and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                mb_downloaded = downloaded / (1024 * 1024)

                                # Update every 1% or every 1MB, whichever is less frequent
                                if (progress - last_progress_update >= 1.0) or (mb_downloaded % 1 < 0.1):
                                    progress_callback(model_key, progress, downloaded, total_size)
                                    last_progress_update = progress

                print(f"Download completed: {downloaded} bytes")

                # Verify file size
                if os.path.exists(local_path):
                    actual_size = os.path.getsize(local_path)
                    if actual_size == total_size:
                        print("✅ Download verification successful")
                        return True
                    else:
                        print(f"❌ Size mismatch: expected {total_size}, got {actual_size}")
                        continue  # Retry

                return True

            except Exception as e:
                print(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                else:
                    print("All download attempts failed")
                    # Clean up partial download on final failure
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    return False

        return False
    
    def download_kokoro_model(self, progress_callback: Optional[Callable] = None):
        """Download complete Kokoro TTS model with specific voices only"""
        try:
            # Try to import huggingface_hub
            try:
                from huggingface_hub import hf_hub_download, snapshot_download
                hf_available = True
            except ImportError:
                hf_available = False

            if not hf_available:
                print("HuggingFace Hub not available, trying direct download...")
                return self._download_kokoro_direct(progress_callback)

            config = self.model_configs['kokoro_82m']
            repo_id = config['huggingface_repo']
            local_path = config['local_path']
            voices_only = config.get('voices_only', [])
            download_full_model = config.get('download_full_model', False)

            if download_full_model:
                print(f"Downloading complete Kokoro model with specific voices: {voices_only}")

                # Ensure directory exists
                os.makedirs(local_path, exist_ok=True)

                # Step 1: Download core model files (excluding all voices)
                if progress_callback:
                    progress_callback('kokoro_82m', 10, 1, 4)

                print("Downloading core model files...")
                try:
                    # Download all files except voices directory
                    snapshot_download(
                        repo_id=repo_id,
                        local_dir=local_path,
                        local_dir_use_symlinks=False,
                        ignore_patterns=["voices/*"]  # Exclude all voices initially
                    )
                    print("✅ Core model files downloaded")
                except Exception as e:
                    print(f"Failed to download core model: {e}")
                    return False

                # Step 2: Download only specific voice files
                if progress_callback:
                    progress_callback('kokoro_82m', 50, 2, 4)

                total_voices = len(voices_only)
                for i, voice_file in enumerate(voices_only):
                    try:
                        voice_progress = 50 + (i / total_voices) * 40  # 50-90% for voices
                        if progress_callback:
                            progress_callback('kokoro_82m', voice_progress, i + 2, total_voices + 2)

                        print(f"Downloading {voice_file}...")
                        hf_hub_download(
                            repo_id=repo_id,
                            filename=voice_file,
                            local_dir=local_path,
                            local_dir_use_symlinks=False
                        )

                    except Exception as e:
                        print(f"Failed to download {voice_file}: {e}")
                        return False

                if progress_callback:
                    progress_callback('kokoro_82m', 100, total_voices + 2, total_voices + 2)

                print(f"✅ Downloaded complete Kokoro model with {total_voices} voices successfully")
                return True
            else:
                # Legacy: voices only (keeping for compatibility)
                return self._download_voices_only(voices_only, repo_id, local_path, progress_callback)

        except Exception as e:
            print(f"Error downloading Kokoro model: {e}")
            return self._download_kokoro_direct(progress_callback)

    def _download_voices_only(self, voices_only, repo_id, local_path, progress_callback):
        """Helper method to download only specific voice files"""
        from huggingface_hub import hf_hub_download

        print(f"Downloading only specific Kokoro voices: {voices_only}")

        # Ensure directory exists
        os.makedirs(local_path, exist_ok=True)

        # Download each voice file individually
        total_voices = len(voices_only)
        for i, voice_file in enumerate(voices_only):
            try:
                if progress_callback:
                    progress = (i / total_voices) * 100
                    progress_callback('kokoro_82m', progress, i, total_voices)

                print(f"Downloading {voice_file}...")
                hf_hub_download(
                    repo_id=repo_id,
                    filename=voice_file,
                    local_dir=local_path,
                    local_dir_use_symlinks=False
                )

            except Exception as e:
                print(f"Failed to download {voice_file}: {e}")
                return False

        if progress_callback:
            progress_callback('kokoro_82m', 100, total_voices, total_voices)

        print(f"✅ Downloaded {total_voices} Kokoro voices successfully")
        return True

    def _download_kokoro_direct(self, progress_callback: Optional[Callable] = None):
        """Fallback direct download for Kokoro model"""
        try:
            config = self.model_configs['kokoro_82m']
            repo_id = config['huggingface_repo']
            local_path = config['local_path']
            voices_only = config.get('voices_only', [])

            print(f"Downloading Kokoro voices directly from HuggingFace: {voices_only}")

            # Ensure directory exists
            os.makedirs(local_path, exist_ok=True)

            # Base URL for HuggingFace file downloads
            base_url = f"https://huggingface.co/{repo_id}/resolve/main"

            total_voices = len(voices_only)
            for i, voice_file in enumerate(voices_only):
                try:
                    if progress_callback:
                        progress = (i / total_voices) * 100
                        progress_callback('kokoro_82m', progress, i, total_voices)

                    file_url = f"{base_url}/{voice_file}"
                    # Save with just the filename (not the voices/ prefix)
                    local_file_path = os.path.join(local_path, os.path.basename(voice_file))

                    print(f"Downloading {voice_file} from {file_url}...")

                    # Download with progress tracking
                    response = requests.get(file_url, stream=True)
                    response.raise_for_status()

                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0

                    with open(local_file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)

                                # Update progress within this file
                                if total_size > 0 and progress_callback:
                                    file_progress = (downloaded / total_size) * 100
                                    overall_progress = ((i + file_progress/100) / total_voices) * 100
                                    progress_callback('kokoro_82m', overall_progress, downloaded, total_size)

                    print(f"✅ Downloaded {voice_file} successfully")

                except Exception as e:
                    print(f"Failed to download {voice_file}: {e}")
                    return False

            if progress_callback:
                progress_callback('kokoro_82m', 100, total_voices, total_voices)

            print(f"✅ Downloaded {total_voices} Kokoro voices successfully via direct download")
            return True

        except Exception as e:
            print(f"Error in direct Kokoro download: {e}")
            return False
    
    def download_all_missing_models(self, progress_callback: Optional[Callable] = None):
        """Download all missing required models"""
        missing = self.get_missing_models()
        
        if not missing:
            return True
        
        success = True
        
        for model_key in missing:
            if model_key == 'whisper_tiny':
                if not self.download_whisper_model(progress_callback):
                    success = False
            elif model_key == 'kokoro_82m':
                if not self.download_kokoro_model(progress_callback):
                    success = False
        
        if success:
            self.save_config()
        
        return success
    
    def get_model_info(self) -> Dict:
        """Get comprehensive model information"""
        status = self.check_model_status()
        missing = self.get_missing_models()
        
        total_size = sum(config['size_mb'] for config in self.model_configs.values() if config.get('required', False))
        
        return {
            'models_dir': self.models_dir,
            'status': status,
            'missing': missing,
            'setup_complete': self.is_setup_complete(),
            'total_download_size_mb': total_size,
            'configs': self.model_configs
        }


def get_portable_model_manager() -> PortableModelManager:
    """Get singleton instance of portable model manager"""
    if not hasattr(get_portable_model_manager, '_instance'):
        get_portable_model_manager._instance = PortableModelManager()
    return get_portable_model_manager._instance
