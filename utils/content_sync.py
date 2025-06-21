"""
Content Synchronization Utilities for Video Generator
Handles intelligent timing and synchronization between text content and images
"""
import os
import math
from typing import List, Tuple, Dict, Optional


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
        Calculate optimized timing for images based on content analysis
        
        Args:
            text: The text content
            image_count: Number of available images
            audio_duration: Duration of generated audio
            timing_mode: Timing preference ("fast", "balanced", "slow", "custom")
            
        Returns:
            Dict with optimized timing information
        """
        analysis = self.analyze_content_mismatch(text, image_count, audio_duration)
        
        timing_result = {
            'strategy': 'basic',
            'duration_per_image': audio_duration / image_count if image_count > 0 else 0,
            'image_sequence': list(range(image_count)),
            'total_images_used': image_count,
            'effects_recommended': [],
            'analysis': analysis
        }
        
        # Apply timing mode adjustments
        mode_multipliers = {
            'fast': 0.8,
            'balanced': 1.0,
            'slow': 1.3
        }
        
        base_multiplier = mode_multipliers.get(timing_mode, 1.0)
        
        if analysis['mismatch_type'] == 'too_many_images':
            timing_result = self._handle_too_many_images(analysis, audio_duration, image_count, base_multiplier)
        elif analysis['mismatch_type'] == 'too_few_images':
            timing_result = self._handle_too_few_images(analysis, audio_duration, image_count, base_multiplier)
        else:
            # Balanced case - ensure we fill the entire audio duration
            calculated_duration = audio_duration / image_count

            # Use calculated duration to fill audio, but respect maximum limits
            if calculated_duration <= self.MAX_IMAGE_DURATION:
                timing_result['duration_per_image'] = calculated_duration
                timing_result['strategy'] = 'balanced_fill_audio'
            else:
                # If calculated duration exceeds max, handle as too_few_images
                timing_result = self._handle_too_few_images(analysis, audio_duration, image_count, base_multiplier)
                timing_result['strategy'] = 'balanced_with_repetition'
        
        return timing_result
    
    def _handle_too_many_images(self, analysis: Dict, audio_duration: float, 
                              image_count: int, base_multiplier: float) -> Dict:
        """Handle case where there are too many images for the audio duration"""
        
        # Calculate how many images we can reasonably show
        min_duration = self.MIN_IMAGE_DURATION * base_multiplier
        max_images_to_show = int(audio_duration / min_duration)
        
        if max_images_to_show < image_count:
            # Use image selection strategy
            strategy = 'image_selection'
            selected_images = self._select_representative_images(image_count, max_images_to_show)
            duration_per_image = audio_duration / len(selected_images)
        else:
            # Use all images but with minimum duration
            strategy = 'minimum_duration'
            selected_images = list(range(image_count))
            duration_per_image = min_duration
        
        return {
            'strategy': strategy,
            'duration_per_image': duration_per_image,
            'image_sequence': selected_images,
            'total_images_used': len(selected_images),
            'effects_recommended': ['fade_transition', 'subtle_zoom'],
            'analysis': analysis
        }
    
    def _handle_too_few_images(self, analysis: Dict, audio_duration: float, 
                             image_count: int, base_multiplier: float) -> Dict:
        """Handle case where there are too few images for the audio duration"""
        
        max_duration = self.MAX_IMAGE_DURATION * base_multiplier
        basic_duration = audio_duration / image_count
        
        if basic_duration > max_duration:
            # Need to repeat images to fill the entire audio duration
            slots_needed = math.ceil(audio_duration / max_duration)
            image_sequence = []

            # Create sequence that fills the entire audio duration
            for i in range(slots_needed):
                image_index = i % image_count
                image_sequence.append(image_index)

            # Calculate duration per slot to exactly fill audio duration
            duration_per_slot = audio_duration / len(image_sequence)

            strategy = 'image_repetition'
        else:
            # Can use each image once with extended duration
            image_sequence = list(range(image_count))
            duration_per_slot = basic_duration
            strategy = 'extended_duration'
        
        return {
            'strategy': strategy,
            'duration_per_image': duration_per_slot,
            'image_sequence': image_sequence,
            'total_images_used': len(image_sequence),
            'effects_recommended': ['slow_zoom', 'pan_effect', 'fade_transition'],
            'analysis': analysis
        }
    
    def _select_representative_images(self, total_images: int, target_count: int) -> List[int]:
        """Select representative images when we have too many"""
        if target_count >= total_images:
            return list(range(total_images))
        
        # Use evenly spaced selection
        step = total_images / target_count
        selected = []
        
        for i in range(target_count):
            index = int(i * step)
            selected.append(min(index, total_images - 1))
        
        return selected
    
    def get_timing_summary(self, timing_result: Dict) -> str:
        """Generate a human-readable summary of the timing strategy"""
        analysis = timing_result['analysis']
        strategy = timing_result['strategy']
        
        summary_parts = []
        
        # Basic info
        summary_parts.append(f"Strategy: {strategy.replace('_', ' ').title()}")
        summary_parts.append(f"Duration per image: {timing_result['duration_per_image']:.2f}s")
        summary_parts.append(f"Total images used: {timing_result['total_images_used']}")

        # Calculate and show total video duration vs audio duration
        image_sequence = timing_result.get('image_sequence', [])
        total_video_duration = timing_result['duration_per_image'] * len(image_sequence)
        audio_duration = analysis.get('audio_duration', 0)
        summary_parts.append(f"Video duration: {total_video_duration:.2f}s (Audio: {audio_duration:.2f}s)")

        # Add warning if video duration doesn't match audio
        if abs(total_video_duration - audio_duration) > 0.5:
            summary_parts.append("⚠️  Duration mismatch detected!")

        # Mismatch info
        if analysis['mismatch_type'] != 'balanced':
            mismatch_desc = analysis['mismatch_type'].replace('_', ' ').title()
            summary_parts.append(f"Content mismatch: {mismatch_desc} ({analysis['severity']})")
        
        # Recommendations
        if analysis['recommendations']:
            summary_parts.append("Recommendations:")
            for rec in analysis['recommendations']:
                summary_parts.append(f"  • {rec}")
        
        return "\n".join(summary_parts)


# Global instance for easy access
content_sync_manager = ContentSyncManager()
