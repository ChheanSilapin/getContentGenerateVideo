"""
Performance Optimization Service for Video Generator
Provides smart optimizations to improve generation speed while maintaining quality
"""
import os
import hashlib
from typing import Dict, List, Optional

class OptimizationManager:
    """Manages performance optimizations across the video generation pipeline"""
    
    def __init__(self):
        self._load_config()
        self._duplicate_tracker = {}
        
    def _load_config(self):
        """Load optimization configuration"""
        try:
            import config
            self.enable_duplicate_detection = getattr(config, 'ENABLE_DUPLICATE_DETECTION', True)
            self.duplicate_threshold = getattr(config, 'DUPLICATE_SIMILARITY_THRESHOLD', 0.95)
            self.processing_opts = getattr(config, 'PROCESSING_OPTIMIZATIONS', {})
            self.ffmpeg_opts = getattr(config, 'FFMPEG_OPTIMIZATION', {})
        except ImportError:
            # Fallback settings
            self.enable_duplicate_detection = True
            self.duplicate_threshold = 0.95
            self.processing_opts = {}
            self.ffmpeg_opts = {}
    
    def get_content_hash(self, text: str, additional_data: str = "") -> str:
        """Generate hash for content to detect duplicates"""
        content = f"{text}|{additional_data}".strip()
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def check_duplicate_content(self, text: str, folder_path: str = "") -> Optional[str]:
        """Check if content is duplicate and return previous result if found"""
        if not self.enable_duplicate_detection:
            return None
            
        content_hash = self.get_content_hash(text, folder_path)
        
        if content_hash in self._duplicate_tracker:
            previous_result = self._duplicate_tracker[content_hash]
            print(f"🔄 Duplicate content detected (hash: {content_hash[:8]}...)")
            print(f"   Previous result: {previous_result}")
            return previous_result
        
        return None
    
    def register_content_result(self, text: str, folder_path: str, result_path: str):
        """Register successful generation result for duplicate detection"""
        if not self.enable_duplicate_detection:
            return
            
        content_hash = self.get_content_hash(text, folder_path)
        self._duplicate_tracker[content_hash] = result_path
        print(f"📝 Registered content result (hash: {content_hash[:8]}...)")
    
    def get_optimized_ffmpeg_params(self) -> Dict:
        """Get optimized FFmpeg parameters for faster encoding"""
        base_params = {
            "preset": "fast",
            "crf": "22",
            "threads": "0",
            "tune": "film",
            "profile:v": "high",
            "level": "4.0",
            "pix_fmt": "yuv420p",
            "c:a": "aac",
            "b:a": "128k",
            "movflags": "+faststart"
        }
        
        # Apply configuration overrides
        if self.ffmpeg_opts:
            base_params.update({
                "preset": self.ffmpeg_opts.get("preset", "fast"),
                "crf": str(self.ffmpeg_opts.get("crf", 22)),
                "threads": str(self.ffmpeg_opts.get("threads", 0)),
                "tune": self.ffmpeg_opts.get("tune", "film"),
                "profile:v": self.ffmpeg_opts.get("profile", "high"),
                "level": self.ffmpeg_opts.get("level", "4.0"),
                "pix_fmt": self.ffmpeg_opts.get("pixel_format", "yuv420p"),
                "c:a": self.ffmpeg_opts.get("audio_codec", "aac"),
                "b:a": self.ffmpeg_opts.get("audio_bitrate", "128k")
            })
            
            # Add x264 specific parameters if available
            x264_params = self.ffmpeg_opts.get("x264_params", {})
            if x264_params:
                x264_string = ":".join([f"{k}={v}" for k, v in x264_params.items()])
                base_params["x264opts"] = x264_string
        
        return base_params
    
    def should_skip_analysis(self, content_hash: str) -> bool:
        """Check if content analysis should be skipped for performance"""
        return self.processing_opts.get("skip_redundant_analysis", True) and \
               content_hash in self._duplicate_tracker
    
    def should_reuse_effects(self, content_type: str, emotional_tone: str) -> bool:
        """Check if effects can be reused for similar content"""
        return self.processing_opts.get("reuse_similar_effects", True)
    
    def should_batch_audio(self) -> bool:
        """Check if audio generation should be batched"""
        return self.processing_opts.get("batch_audio_generation", True)
    
    def should_optimize_images(self) -> bool:
        """Check if image loading should be optimized"""
        return self.processing_opts.get("optimize_image_loading", True)
    
    def should_cleanup_during_processing(self) -> bool:
        """Check if temporary files should be cleaned during processing"""
        return self.processing_opts.get("smart_temp_cleanup", True)
    
    def is_memory_efficient_mode(self) -> bool:
        """Check if memory-efficient mode is enabled"""
        return self.processing_opts.get("memory_efficient_mode", True)
    
    def get_optimization_summary(self) -> Dict:
        """Get summary of current optimization settings"""
        return {
            "duplicate_detection": self.enable_duplicate_detection,
            "duplicate_threshold": self.duplicate_threshold,
            "ffmpeg_preset": self.ffmpeg_opts.get("preset", "fast"),
            "ffmpeg_crf": self.ffmpeg_opts.get("crf", 22),
            "processing_optimizations": self.processing_opts,
            "tracked_content": len(self._duplicate_tracker)
        }
    
    def print_optimization_status(self):
        """Print current optimization status"""
        summary = self.get_optimization_summary()
        print("\n🚀 Performance Optimization Status:")
        print(f"   Duplicate Detection: {'✅' if summary['duplicate_detection'] else '❌'}")
        print(f"   FFmpeg Preset: {summary['ffmpeg_preset']} (CRF: {summary['ffmpeg_crf']})")
        print(f"   Tracked Content: {summary['tracked_content']} items")
        
        enabled_opts = [k for k, v in summary['processing_optimizations'].items() if v]
        if enabled_opts:
            print(f"   Enabled Optimizations: {', '.join(enabled_opts)}")

# Global optimization manager instance
optimization_manager = OptimizationManager()

def get_optimization_manager() -> OptimizationManager:
    """Get the global optimization manager instance"""
    return optimization_manager

def apply_ffmpeg_optimizations(cmd_args: List[str]) -> List[str]:
    """Apply FFmpeg optimizations to command arguments"""
    optimized_params = optimization_manager.get_optimized_ffmpeg_params()
    
    # Insert optimization parameters before output file
    if len(cmd_args) >= 2:
        # Find the output file (usually the last argument)
        output_file = cmd_args[-1]
        base_cmd = cmd_args[:-1]
        
        # Add optimization parameters
        for key, value in optimized_params.items():
            if key not in [arg.lstrip('-') for arg in base_cmd]:  # Avoid duplicates
                base_cmd.extend([f"-{key}", value])
        
        return base_cmd + [output_file]
    
    return cmd_args

def log_performance_improvement(operation: str, original_time: float, optimized_time: float):
    """Log performance improvement for an operation"""
    if optimized_time < original_time:
        improvement = ((original_time - optimized_time) / original_time) * 100
        print(f"⚡ {operation}: {improvement:.1f}% faster ({original_time:.1f}s → {optimized_time:.1f}s)")
    else:
        print(f"📊 {operation}: {optimized_time:.1f}s")
