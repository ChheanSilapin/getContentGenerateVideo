"""
Emotion-Aware Visual Effects Service
Applies visual effects, color grading, and transitions based on content analysis
"""
import os
import numpy as np
from typing import Dict, Optional, Tuple
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips

# Try to import OpenCV for advanced effects
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("OpenCV not available - some advanced effects will be disabled")

class EmotionAwareEffects:
    """Applies emotion-aware visual effects to video content"""
    
    def __init__(self):
        self.color_palettes = {
            'historical': {
                'sepia_strength': 0.7,
                'saturation': 0.6,
                'contrast': 1.1,
                'brightness': -0.1,
                'vignette_strength': 0.3
            },
            'dramatic': {
                'saturation': 1.3,
                'contrast': 1.4,
                'brightness': -0.05,
                'vignette_strength': 0.4,
                'shadow_boost': 0.2
            },
            'reflective': {
                'saturation': 0.8,
                'contrast': 0.9,
                'brightness': 0.1,
                'warmth': 0.2,
                'softness': 0.3
            },
            'inspirational': {
                'saturation': 1.2,
                'contrast': 1.1,
                'brightness': 0.15,
                'warmth': 0.3,
                'glow_strength': 0.2
            },
            'nostalgic': {
                'sepia_strength': 0.5,
                'saturation': 0.7,
                'contrast': 0.95,
                'brightness': 0.05,
                'film_grain': 0.1
            },
            'mysterious': {
                'saturation': 0.9,
                'contrast': 1.3,
                'brightness': -0.2,
                'cool_tone': 0.3,
                'vignette_strength': 0.5
            }
        }
        
        self.transition_styles = {
            'historical': 'dissolve',
            'dramatic': 'crossfade_fast',
            'reflective': 'slow_fade',
            'inspirational': 'zoom_transition',
            'nostalgic': 'film_dissolve',
            'mysterious': 'fade_to_black'
        }

    def apply_emotion_aware_effects(self, clip, content_analysis, duration_per_image=4.0):
        """
        Apply emotion-aware effects to a video clip
        
        Args:
            clip: MoviePy video clip
            content_analysis: ContentAnalysis object
            duration_per_image: Duration for each image in slideshow
            
        Returns:
            Enhanced video clip
        """
        if not content_analysis:
            return clip
        
        # Reduced logging: print(f"Applying emotion-aware effects for {content_analysis.content_type.value} "
        #                       f"content with {content_analysis.emotional_tone.value} tone")
        
        # Get effect settings
        visual_effects = content_analysis.recommended_visual_effects
        color_palette = content_analysis.color_palette
        
        # Apply color grading
        enhanced_clip = self._apply_color_grading(clip, visual_effects, color_palette)
        
        # Apply content-specific effects
        enhanced_clip = self._apply_content_effects(enhanced_clip, content_analysis)
        
        # Apply emotional tone effects
        enhanced_clip = self._apply_emotional_effects(enhanced_clip, content_analysis.emotional_tone.value)
        
        return enhanced_clip

    def _apply_color_grading(self, clip, visual_effects, color_palette):
        """Apply color grading based on content analysis"""
        if not CV2_AVAILABLE:
            print("OpenCV not available - using basic color adjustments")
            return self._apply_basic_color_adjustments(clip, visual_effects)
        
        def color_grade_frame(frame):
            # Convert to float for processing
            frame_float = frame.astype(np.float32) / 255.0
            
            # Apply temperature adjustment
            temperature = color_palette.get('temperature', 'balanced')
            if temperature == 'warm':
                frame_float[:, :, 0] *= 1.1  # Boost red
                frame_float[:, :, 2] *= 0.9  # Reduce blue
            elif temperature == 'cool':
                frame_float[:, :, 0] *= 0.9  # Reduce red
                frame_float[:, :, 2] *= 1.1  # Boost blue
            
            # Apply saturation
            saturation = visual_effects.get('saturation', 1.0)
            if saturation != 1.0:
                gray = cv2.cvtColor((frame_float * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
                gray_rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB).astype(np.float32) / 255.0
                frame_float = gray_rgb + saturation * (frame_float - gray_rgb)
            
            # Apply contrast and brightness
            contrast = visual_effects.get('contrast_boost', 1.0)
            brightness = visual_effects.get('brightness', 0.0)
            frame_float = contrast * frame_float + brightness
            
            # Clip values and convert back
            frame_float = np.clip(frame_float, 0, 1)
            return (frame_float * 255).astype(np.uint8)
        
        return clip.fl_image(color_grade_frame)

    def _apply_basic_color_adjustments(self, clip, visual_effects):
        """Apply basic color adjustments without OpenCV"""
        # Simple brightness and contrast adjustment
        brightness = visual_effects.get('brightness', 0.0)
        contrast = visual_effects.get('contrast_boost', 1.0)
        
        if brightness != 0.0 or contrast != 1.0:
            def adjust_frame(frame):
                frame_float = frame.astype(np.float32)
                frame_float = contrast * frame_float + brightness * 255
                return np.clip(frame_float, 0, 255).astype(np.uint8)
            
            clip = clip.fl_image(adjust_frame)
        
        return clip

    def _apply_content_effects(self, clip, content_analysis):
        """Apply effects specific to content type"""
        content_type = content_analysis.content_type.value
        
        if content_type == 'historical':
            # Add vintage film effect
            clip = self._add_vintage_effect(clip)
            # Add subtle vignette
            clip = self._add_vignette(clip, strength=0.3)
            
        elif content_type == 'story_review':
            # Add cinematic letterbox effect
            clip = self._add_letterbox(clip)
            
        elif content_type == 'quote_reflection':
            # Add soft glow effect
            clip = self._add_soft_glow(clip)
            
        return clip

    def _apply_emotional_effects(self, clip, emotional_tone):
        """Apply effects based on emotional tone"""
        if emotional_tone == 'dramatic':
            # Increase contrast and add vignette
            clip = self._add_vignette(clip, strength=0.4)
            
        elif emotional_tone == 'nostalgic':
            # Add film grain and sepia tone
            clip = self._add_film_grain(clip)
            clip = self._add_sepia_tone(clip, strength=0.5)
            
        elif emotional_tone == 'mysterious':
            # Add dark vignette and cool tone
            clip = self._add_vignette(clip, strength=0.6)
            
        elif emotional_tone == 'inspirational':
            # Add subtle glow and warmth
            clip = self._add_soft_glow(clip, strength=0.2)
            
        return clip

    def _add_vintage_effect(self, clip):
        """Add vintage film effect"""
        if not CV2_AVAILABLE:
            return clip
            
        def vintage_frame(frame):
            # Add slight sepia tone
            sepia_kernel = np.array([[0.272, 0.534, 0.131],
                                   [0.349, 0.686, 0.168],
                                   [0.393, 0.769, 0.189]])
            sepia_frame = cv2.transform(frame, sepia_kernel)
            # Blend with original
            return cv2.addWeighted(frame, 0.3, sepia_frame, 0.7, 0)
        
        return clip.fl_image(vintage_frame)

    def _add_vignette(self, clip, strength=0.3):
        """Add vignette effect"""
        def vignette_frame(frame):
            h, w = frame.shape[:2]
            # Create vignette mask
            center_x, center_y = w // 2, h // 2
            Y, X = np.ogrid[:h, :w]
            dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
            max_dist = np.sqrt(center_x**2 + center_y**2)
            vignette = 1 - (dist_from_center / max_dist) * strength
            vignette = np.clip(vignette, 0, 1)
            
            # Apply vignette
            for i in range(3):  # RGB channels
                frame[:, :, i] = frame[:, :, i] * vignette
            
            return frame.astype(np.uint8)
        
        return clip.fl_image(vignette_frame)

    def _add_letterbox(self, clip, ratio=0.1):
        """Add cinematic letterbox bars"""
        def letterbox_frame(frame):
            h, w = frame.shape[:2]
            bar_height = int(h * ratio)
            # Add black bars
            frame[:bar_height, :] = 0
            frame[-bar_height:, :] = 0
            return frame
        
        return clip.fl_image(letterbox_frame)

    def _add_soft_glow(self, clip, strength=0.3):
        """Add soft glow effect"""
        if not CV2_AVAILABLE:
            return clip
            
        def glow_frame(frame):
            # Create glow by blurring and blending
            blurred = cv2.GaussianBlur(frame, (15, 15), 0)
            return cv2.addWeighted(frame, 1 - strength, blurred, strength, 0)
        
        return clip.fl_image(glow_frame)

    def _add_film_grain(self, clip, strength=0.1):
        """Add film grain effect"""
        def grain_frame(frame):
            h, w = frame.shape[:2]
            # Generate noise
            noise = np.random.normal(0, strength * 255, (h, w, 3))
            # Add noise to frame
            noisy_frame = frame.astype(np.float32) + noise
            return np.clip(noisy_frame, 0, 255).astype(np.uint8)
        
        return clip.fl_image(grain_frame)

    def _add_sepia_tone(self, clip, strength=0.5):
        """Add sepia tone effect"""
        if not CV2_AVAILABLE:
            return clip
            
        def sepia_frame(frame):
            sepia_kernel = np.array([[0.272, 0.534, 0.131],
                                   [0.349, 0.686, 0.168],
                                   [0.393, 0.769, 0.189]])
            sepia_frame = cv2.transform(frame, sepia_kernel)
            return cv2.addWeighted(frame, 1 - strength, sepia_frame, strength, 0)
        
        return clip.fl_image(sepia_frame)

    def create_emotion_aware_transitions(self, clips, content_analysis, transition_duration=0.5):
        """
        Create emotion-aware transitions between clips
        
        Args:
            clips: List of video clips
            content_analysis: ContentAnalysis object
            transition_duration: Duration of transitions
            
        Returns:
            Video with emotion-aware transitions
        """
        if len(clips) <= 1:
            return clips[0] if clips else None
        
        transition_style = self._get_transition_style(content_analysis)
        
        # Apply transitions based on emotional content
        final_clips = []
        
        for i, clip in enumerate(clips):
            if i == 0:
                # First clip - add fade in
                final_clips.append(clip.fadein(transition_duration))
            elif i == len(clips) - 1:
                # Last clip - add fade out
                final_clips.append(clip.fadeout(transition_duration))
            else:
                # Middle clips - apply transition style
                final_clips.append(self._apply_transition_style(clip, transition_style, transition_duration))
        
        return concatenate_videoclips(final_clips, method="compose")

    def _get_transition_style(self, content_analysis):
        """Get appropriate transition style based on content"""
        content_type = content_analysis.content_type.value
        emotional_tone = content_analysis.emotional_tone.value
        
        # Priority: emotional tone over content type
        if emotional_tone in self.transition_styles:
            return self.transition_styles[emotional_tone]
        elif content_type in self.transition_styles:
            return self.transition_styles[content_type]
        else:
            return 'fade'  # Default

    def _apply_transition_style(self, clip, style, duration):
        """Apply specific transition style to clip"""
        if style == 'slow_fade':
            return clip.fadeout(duration * 1.5).fadein(duration * 1.5)
        elif style == 'crossfade_fast':
            return clip.fadeout(duration * 0.5).fadein(duration * 0.5)
        elif style == 'dissolve':
            return clip.fadeout(duration).fadein(duration)
        else:
            return clip.fadeout(duration).fadein(duration)
