"""
Smart Dependency Manager for Video Generator
Handles automatic download and installation of AI dependencies and models
"""
import os
import sys
import subprocess
import importlib
import json
from typing import Dict, List, Optional, Callable
from utils.path_manager import get_application_paths


class SmartDependencyManager:
    """Manages automatic installation of AI dependencies and models"""
    
    def __init__(self):
        self.paths = get_application_paths()
        self.dependency_config_file = os.path.join(self.paths['config_dir'], 'dependencies.json')
        
        # AI Dependencies that are excluded from PyInstaller build
        self.ai_dependencies = {
            'torch': {
                'name': 'PyTorch CPU',
                'install_command': [sys.executable, '-m', 'pip', 'install', 'torch', '--index-url', 'https://download.pytorch.org/whl/cpu'],
                'import_name': 'torch',
                'size_mb': 100,
                'required_for': ['whisper', 'kokoro'],
                'description': 'Deep learning framework for AI models'
            },
            'transformers': {
                'name': 'Transformers',
                'install_command': [sys.executable, '-m', 'pip', 'install', 'transformers'],
                'import_name': 'transformers',
                'size_mb': 50,
                'required_for': ['whisper', 'kokoro'],
                'description': 'Hugging Face transformers library'
            },
            'huggingface_hub': {
                'name': 'Hugging Face Hub',
                'install_command': [sys.executable, '-m', 'pip', 'install', 'huggingface_hub'],
                'import_name': 'huggingface_hub',
                'size_mb': 20,
                'required_for': ['kokoro'],
                'description': 'Model repository access'
            },
            'whisper_timestamped': {
                'name': 'Whisper Timestamped',
                'install_command': [sys.executable, '-m', 'pip', 'install', 'whisper-timestamped'],
                'import_name': 'whisper_timestamped',
                'size_mb': 30,
                'required_for': ['speech_recognition'],
                'description': 'Speech recognition with timestamps'
            },
            'kokoro': {
                'name': 'Kokoro TTS',
                'install_command': [sys.executable, '-m', 'pip', 'install', 'kokoro>=0.9.4'],
                'import_name': 'kokoro',
                'size_mb': 10,
                'required_for': ['tts'],
                'description': 'High-quality text-to-speech'
            },
            'silero_vad': {
                'name': 'Silero VAD',
                'install_command': [sys.executable, '-m', 'pip', 'install', 'silero-vad>=5.1.2'],
                'import_name': 'silero_vad',
                'size_mb': 15,
                'required_for': ['whisper'],
                'description': 'Voice activity detection'
            },
            'onnxruntime': {
                'name': 'ONNX Runtime',
                'install_command': [sys.executable, '-m', 'pip', 'install', 'onnxruntime>=1.15.0'],
                'import_name': 'onnxruntime',
                'size_mb': 40,
                'required_for': ['whisper', 'silero_vad'],
                'description': 'Optimized inference runtime'
            }
        }
        
        self.load_dependency_status()
    
    def load_dependency_status(self):
        """Load dependency installation status from config"""
        try:
            if os.path.exists(self.dependency_config_file):
                with open(self.dependency_config_file, 'r') as f:
                    config = json.load(f)
                    # Update installation status
                    for dep_key, status in config.get('installed', {}).items():
                        if dep_key in self.ai_dependencies:
                            self.ai_dependencies[dep_key]['installed'] = status
        except Exception as e:
            print(f"Warning: Could not load dependency status: {e}")
    
    def save_dependency_status(self):
        """Save dependency installation status to config"""
        try:
            os.makedirs(os.path.dirname(self.dependency_config_file), exist_ok=True)
            
            config = {
                'installed': {},
                'last_check': self.get_current_timestamp()
            }
            
            for dep_key, dep_info in self.ai_dependencies.items():
                config['installed'][dep_key] = dep_info.get('installed', False)
            
            with open(self.dependency_config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save dependency status: {e}")
    
    def get_current_timestamp(self):
        """Get current timestamp"""
        import time
        return int(time.time())
    
    def check_dependency_availability(self) -> Dict[str, bool]:
        """Check which AI dependencies are currently available"""
        availability = {}
        
        for dep_key, dep_info in self.ai_dependencies.items():
            try:
                importlib.import_module(dep_info['import_name'])
                availability[dep_key] = True
                dep_info['installed'] = True
            except ImportError:
                availability[dep_key] = False
                dep_info['installed'] = False
        
        return availability
    
    def get_missing_dependencies_for_feature(self, feature: str) -> List[str]:
        """Get missing dependencies required for a specific feature"""
        missing = []
        availability = self.check_dependency_availability()
        
        for dep_key, dep_info in self.ai_dependencies.items():
            if feature in dep_info.get('required_for', []):
                if not availability.get(dep_key, False):
                    missing.append(dep_key)
        
        return missing
    
    def get_all_missing_dependencies(self) -> List[str]:
        """Get all missing AI dependencies"""
        availability = self.check_dependency_availability()
        return [dep_key for dep_key, available in availability.items() if not available]
    
    def install_dependency(self, dep_key: str, progress_callback: Optional[Callable] = None) -> bool:
        """Install a specific AI dependency"""
        if dep_key not in self.ai_dependencies:
            print(f"Unknown dependency: {dep_key}")
            return False
        
        dep_info = self.ai_dependencies[dep_key]
        
        try:
            if progress_callback:
                progress_callback(dep_key, 0, f"Installing {dep_info['name']}...")
            
            # Run pip install command
            result = subprocess.run(
                dep_info['install_command'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Verify installation
                try:
                    importlib.import_module(dep_info['import_name'])
                    dep_info['installed'] = True
                    
                    if progress_callback:
                        progress_callback(dep_key, 100, f"{dep_info['name']} installed successfully")
                    
                    return True
                except ImportError:
                    if progress_callback:
                        progress_callback(dep_key, 0, f"Installation verification failed for {dep_info['name']}")
                    return False
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                if progress_callback:
                    progress_callback(dep_key, 0, f"Installation failed: {error_msg[:100]}")
                print(f"Failed to install {dep_key}: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            if progress_callback:
                progress_callback(dep_key, 0, f"Installation timeout for {dep_info['name']}")
            print(f"Installation timeout for {dep_key}")
            return False
        except Exception as e:
            if progress_callback:
                progress_callback(dep_key, 0, f"Installation error: {str(e)}")
            print(f"Error installing {dep_key}: {e}")
            return False
    
    def install_dependencies_for_feature(self, feature: str, progress_callback: Optional[Callable] = None) -> bool:
        """Install all dependencies required for a specific feature"""
        missing = self.get_missing_dependencies_for_feature(feature)
        
        if not missing:
            return True
        
        success = True
        for dep_key in missing:
            if not self.install_dependency(dep_key, progress_callback):
                success = False
        
        if success:
            self.save_dependency_status()
        
        return success
    
    def install_all_missing_dependencies(self, progress_callback: Optional[Callable] = None) -> bool:
        """Install all missing AI dependencies"""
        missing = self.get_all_missing_dependencies()
        
        if not missing:
            return True
        
        success = True
        total_deps = len(missing)
        
        for i, dep_key in enumerate(missing):
            if progress_callback:
                overall_progress = (i / total_deps) * 100
                progress_callback('overall', overall_progress, f"Installing {i+1}/{total_deps} dependencies...")
            
            if not self.install_dependency(dep_key, progress_callback):
                success = False
        
        if success:
            self.save_dependency_status()
            if progress_callback:
                progress_callback('overall', 100, "All dependencies installed successfully!")
        
        return success
    
    def get_dependency_info(self) -> Dict:
        """Get comprehensive dependency information"""
        availability = self.check_dependency_availability()
        missing = self.get_all_missing_dependencies()
        
        total_download_size = sum(
            dep_info['size_mb'] 
            for dep_key, dep_info in self.ai_dependencies.items() 
            if dep_key in missing
        )
        
        return {
            'availability': availability,
            'missing': missing,
            'total_download_size_mb': total_download_size,
            'dependencies': self.ai_dependencies,
            'all_available': len(missing) == 0
        }
    
    def is_feature_available(self, feature: str) -> bool:
        """Check if all dependencies for a feature are available"""
        missing = self.get_missing_dependencies_for_feature(feature)
        return len(missing) == 0


def get_smart_dependency_manager() -> SmartDependencyManager:
    """Get singleton instance of smart dependency manager"""
    if not hasattr(get_smart_dependency_manager, '_instance'):
        get_smart_dependency_manager._instance = SmartDependencyManager()
    return get_smart_dependency_manager._instance


# Convenience functions for common use cases
def ensure_whisper_available(progress_callback: Optional[Callable] = None) -> bool:
    """Ensure Whisper dependencies are available"""
    manager = get_smart_dependency_manager()
    return manager.install_dependencies_for_feature('speech_recognition', progress_callback)

def ensure_kokoro_available(progress_callback: Optional[Callable] = None) -> bool:
    """Ensure Kokoro TTS dependencies are available"""
    manager = get_smart_dependency_manager()
    return manager.install_dependencies_for_feature('tts', progress_callback)

def ensure_all_ai_features_available(progress_callback: Optional[Callable] = None) -> bool:
    """Ensure all AI dependencies are available"""
    manager = get_smart_dependency_manager()
    return manager.install_all_missing_dependencies(progress_callback)
