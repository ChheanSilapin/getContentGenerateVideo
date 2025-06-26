"""
Content Synchronization Utilities for Video Generator
Simplified timing based on gTTS audio duration
"""
from typing import Dict, List


class ContentSyncManager:
    """Manages synchronization between text content and visual elements (images)"""
    
    # Timing constraints (in seconds)
    MIN_IMAGE_DURATION = 0.8  # Minimum time per image for readability
    MAX_IMAGE_DURATION = 8.0  # Maximum time per image to avoid boredom
    OPTIMAL_IMAGE_DURATION = 3.0  # Optimal time per image
    
    # Content analysis thresholds
    SHORT_TEXT_THRESHOLD = 50  # Words
    LONG_TEXT_THRESHOLD = 200  # Words
    
    def __init__(self, user_settings=None):
        self.timing_mode = "balanced"  # balanced, fast, slow, custom
        self._load_user_settings(user_settings)

    def _load_user_settings(self, user_settings=None):
        """Load user settings for content synchronization"""
        if user_settings:
            self.timing_mode = user_settings.get('timing_mode', 'balanced')
            self.MIN_IMAGE_DURATION = user_settings.get('min_image_duration', 0.8)
            self.MAX_IMAGE_DURATION = user_settings.get('max_image_duration', 8.0)
            self.OPTIMAL_IMAGE_DURATION = user_settings.get('optimal_image_duration', 3.0)
        else:
            # Try to load from settings manager
            try:
                from utils.settings_manager import SettingsManager
                settings_manager = SettingsManager()
                loaded_settings = settings_manager.load_settings()
                self.timing_mode = loaded_settings.get('timing_mode', 'balanced')
                self.MIN_IMAGE_DURATION = loaded_settings.get('min_image_duration', 0.8)
                self.MAX_IMAGE_DURATION = loaded_settings.get('max_image_duration', 8.0)
                self.OPTIMAL_IMAGE_DURATION = loaded_settings.get('optimal_image_duration', 3.0)
            except Exception:
                pass  # Use default values
        
    def analyze_content_mismatch(self, text: str, image_count: int, audio_duration: float) -> Dict:
        """
        Analyze the relationship between text length, image count, and audio duration
        
        Args:
            text: The text content
            image_count: Number of available images
            audio_duration: Duration of generated audio in seconds
            
        Returns:
            Dict with analysis results and recommendations
        """
        word_count = len(text.split()) if text else 0
        basic_duration_per_image = audio_duration / image_count if image_count > 0 else 0
        
        analysis = {
            'word_count': word_count,
            'image_count': image_count,
            'audio_duration': audio_duration,
            'basic_duration_per_image': basic_duration_per_image,
            'mismatch_type': 'balanced',
            'severity': 'none',
            'recommendations': []
        }
        
        # Determine mismatch type and severity
        if basic_duration_per_image < self.MIN_IMAGE_DURATION:
            analysis['mismatch_type'] = 'too_many_images'
            if basic_duration_per_image < 0.5:
                analysis['severity'] = 'severe'
            elif basic_duration_per_image < 0.8:
                analysis['severity'] = 'moderate'
            else:
                analysis['severity'] = 'mild'

        elif basic_duration_per_image > self.MAX_IMAGE_DURATION:
            analysis['mismatch_type'] = 'too_few_images'
            if basic_duration_per_image > 15.0:
                analysis['severity'] = 'severe'
            elif basic_duration_per_image > 10.0:
                analysis['severity'] = 'moderate'
            else:
                analysis['severity'] = 'mild'

        # Additional check: if calculated duration significantly exceeds optimal, consider as too_few_images
        elif basic_duration_per_image > self.OPTIMAL_IMAGE_DURATION * 1.5:
            analysis['mismatch_type'] = 'too_few_images'
            analysis['severity'] = 'mild'
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on content analysis"""
        recommendations = []
        
        if analysis['mismatch_type'] == 'too_many_images':
            if analysis['severity'] == 'severe':
                recommendations.append("Consider reducing the number of images or extending the text")
                recommendations.append("Will use image cycling to maintain minimum viewing time")
            else:
                recommendations.append("Will optimize timing to ensure each image is visible long enough")
                
        elif analysis['mismatch_type'] == 'too_few_images':
            if analysis['severity'] == 'severe':
                recommendations.append("Consider adding more images or shortening the text")
                recommendations.append("Will repeat images with variations to maintain visual interest")
            else:
                recommendations.append("Will use extended timing with subtle effects to maintain engagement")
        
        return recommendations
    
    def calculate_optimized_timing(self, text: str, image_count: int, audio_duration: float,
                                 timing_mode: str = "balanced") -> Dict:
        """
        Simple timing calculation - relies on gTTS duration for accuracy

        Args:
            text: The text content
            image_count: Number of available images
            audio_duration: Duration of generated audio (from gTTS)
            timing_mode: Timing preference (ignored - uses gTTS duration)

        Returns:
            Dict with basic timing information
        """
        return {
            'strategy': 'gTTS_based',
            'duration_per_image': audio_duration / image_count if image_count > 0 else 0,
            'image_sequence': list(range(image_count)),
            'total_images_used': image_count,
            'effects_recommended': [],
            'analysis': {'audio_duration': audio_duration, 'image_count': image_count}
        }
    

    
    def get_timing_summary(self, timing_result: Dict) -> str:
        """Generate a simple timing summary"""
        return f"Using gTTS-based timing: {timing_result['duration_per_image']:.2f}s per image"


# Global instance for easy access
content_sync_manager = ContentSyncManager()
