"""
Content Analysis Service for Emotion-Aware Video Generation
Analyzes content type, emotional tone, and provides recommendations for video generation
Includes smart caching to prevent duplicate analysis and improve performance
"""
import re
import os
import hashlib
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class ContentType(Enum):
    """Content type classifications"""
    HISTORICAL = "historical"
    STORY_REVIEW = "story_review"
    QUOTE_REFLECTION = "quote_reflection"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    DOCUMENTARY = "documentary"
    PERSONAL = "personal"
    UNKNOWN = "unknown"

class EmotionalTone(Enum):
    """Emotional tone classifications"""
    SERIOUS = "serious"
    DRAMATIC = "dramatic"
    REFLECTIVE = "reflective"
    INSPIRATIONAL = "inspirational"
    NOSTALGIC = "nostalgic"
    MELANCHOLIC = "melancholic"
    UPLIFTING = "uplifting"
    MYSTERIOUS = "mysterious"
    ENERGETIC = "energetic"
    CALM = "calm"
    NEUTRAL = "neutral"

@dataclass
class ContentAnalysis:
    """Results of content analysis"""
    content_type: ContentType
    emotional_tone: EmotionalTone
    confidence: float
    keywords: List[str]
    themes: List[str]
    recommended_voice_settings: Dict
    recommended_visual_effects: Dict
    recommended_timing: Dict
    color_palette: Dict

class ContentAnalyzer:
    """Analyzes content to determine type, emotion, and generation recommendations with smart caching"""

    def __init__(self):
        # Smart caching system
        self._analysis_cache = {}
        self._cache_timestamps = {}
        self._load_config()

        self.content_keywords = {
            ContentType.HISTORICAL: [
                'history', 'historical', 'ancient', 'century', 'war', 'battle', 'empire', 
                'civilization', 'dynasty', 'revolution', 'medieval', 'renaissance', 'colonial',
                'artifact', 'archaeological', 'timeline', 'era', 'period', 'legacy', 'heritage'
            ],
            ContentType.STORY_REVIEW: [
                'story', 'plot', 'character', 'narrative', 'chapter', 'book', 'novel', 'tale',
                'protagonist', 'antagonist', 'climax', 'twist', 'ending', 'review', 'analysis',
                'theme', 'symbolism', 'metaphor', 'literature', 'author', 'writing'
            ],
            ContentType.QUOTE_REFLECTION: [
                'quote', 'said', 'wisdom', 'philosophy', 'reflection', 'thought', 'insight',
                'meaning', 'truth', 'life lesson', 'inspiration', 'motivational', 'profound',
                'deep', 'contemplation', 'meditation', 'perspective', 'understanding'
            ],
            ContentType.EDUCATIONAL: [
                'learn', 'education', 'explain', 'understand', 'concept', 'theory', 'principle',
                'science', 'research', 'study', 'analysis', 'method', 'process', 'technique',
                'knowledge', 'information', 'facts', 'data', 'evidence'
            ],
            ContentType.DOCUMENTARY: [
                'documentary', 'investigation', 'expose', 'reveal', 'uncover', 'truth',
                'reality', 'behind the scenes', 'hidden', 'secret', 'mystery', 'discovery'
            ]
        }
        
        self.emotional_keywords = {
            EmotionalTone.SERIOUS: [
                'serious', 'grave', 'important', 'critical', 'significant', 'solemn',
                'formal', 'official', 'urgent', 'crucial', 'vital', 'essential'
            ],
            EmotionalTone.DRAMATIC: [
                'dramatic', 'intense', 'powerful', 'shocking', 'stunning', 'overwhelming',
                'climactic', 'tension', 'conflict', 'struggle', 'crisis', 'turning point'
            ],
            EmotionalTone.REFLECTIVE: [
                'reflective', 'thoughtful', 'contemplative', 'introspective', 'meditative',
                'pensive', 'philosophical', 'deep', 'meaningful', 'profound'
            ],
            EmotionalTone.INSPIRATIONAL: [
                'inspiring', 'motivational', 'uplifting', 'encouraging', 'empowering',
                'hopeful', 'positive', 'optimistic', 'triumphant', 'successful'
            ],
            EmotionalTone.NOSTALGIC: [
                'nostalgic', 'memories', 'remember', 'past', 'childhood', 'old days',
                'vintage', 'classic', 'traditional', 'bygone', 'reminiscent'
            ],
            EmotionalTone.MELANCHOLIC: [
                'sad', 'melancholy', 'sorrowful', 'tragic', 'loss', 'grief', 'mourning',
                'regret', 'longing', 'wistful', 'bittersweet', 'poignant'
            ],
            EmotionalTone.MYSTERIOUS: [
                'mysterious', 'enigmatic', 'puzzling', 'cryptic', 'hidden', 'secret',
                'unknown', 'unexplained', 'strange', 'curious', 'intriguing'
            ]
        }

    def _load_config(self):
        """Load configuration settings for caching"""
        try:
            import config
            self.cache_enabled = getattr(config, 'ENABLE_CONTENT_ANALYSIS_CACHE', True)
            self.cache_max_size = getattr(config, 'CONTENT_CACHE_MAX_SIZE', 100)
            self.cache_ttl_hours = getattr(config, 'CONTENT_CACHE_TTL_HOURS', 24)
        except ImportError:
            # Fallback if config not available
            self.cache_enabled = True
            self.cache_max_size = 100
            self.cache_ttl_hours = 24

    def _get_content_hash(self, text: str, title: str = "", context: str = "") -> str:
        """Generate a hash for content to use as cache key"""
        content = f"{title}|{text}|{context}".strip()
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached analysis is still valid"""
        if not self.cache_enabled or cache_key not in self._cache_timestamps:
            return False

        cache_time = self._cache_timestamps[cache_key]
        current_time = time.time()
        age_hours = (current_time - cache_time) / 3600

        return age_hours < self.cache_ttl_hours

    def _cleanup_cache(self):
        """Remove old or excess cache entries"""
        if not self.cache_enabled:
            return

        current_time = time.time()

        # Remove expired entries
        expired_keys = []
        for key, timestamp in self._cache_timestamps.items():
            age_hours = (current_time - timestamp) / 3600
            if age_hours >= self.cache_ttl_hours:
                expired_keys.append(key)

        for key in expired_keys:
            self._analysis_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)

        # Remove excess entries if cache is too large
        if len(self._analysis_cache) > self.cache_max_size:
            # Remove oldest entries
            sorted_items = sorted(self._cache_timestamps.items(), key=lambda x: x[1])
            excess_count = len(self._analysis_cache) - self.cache_max_size

            for key, _ in sorted_items[:excess_count]:
                self._analysis_cache.pop(key, None)
                self._cache_timestamps.pop(key, None)

    def analyze_content(self, text: str, title: str = "", context: str = "") -> ContentAnalysis:
        """
        Analyze content to determine type, emotional tone, and recommendations with smart caching

        Args:
            text: Main content text
            title: Optional title for additional context
            context: Optional additional context

        Returns:
            ContentAnalysis object with complete analysis
        """
        if not text:
            return self._create_default_analysis()

        # Check cache first for performance optimization
        if self.cache_enabled:
            cache_key = self._get_content_hash(text, title, context)

            if self._is_cache_valid(cache_key):
                print(f"🚀 Using cached content analysis (key: {cache_key[:8]}...)")
                return self._analysis_cache[cache_key]

            # Clean up cache periodically
            if len(self._analysis_cache) % 10 == 0:  # Every 10th analysis
                self._cleanup_cache()

        # Perform analysis if not cached
        # Reduced logging: print(f"🔍 Analyzing content: {len(text)} characters")

        # Combine all text for analysis
        full_text = f"{title} {text} {context}".lower()

        # Analyze content type
        content_type, content_confidence = self._analyze_content_type(full_text)

        # Analyze emotional tone
        emotional_tone, emotion_confidence = self._analyze_emotional_tone(full_text)

        # Extract keywords and themes
        keywords = self._extract_keywords(full_text, content_type, emotional_tone)
        themes = self._extract_themes(full_text, content_type)

        # Generate recommendations
        voice_settings = self._get_voice_recommendations(content_type, emotional_tone)
        visual_effects = self._get_visual_recommendations(content_type, emotional_tone)
        timing_settings = self._get_timing_recommendations(content_type, emotional_tone)
        color_palette = self._get_color_recommendations(content_type, emotional_tone)

        # Calculate overall confidence
        overall_confidence = (content_confidence + emotion_confidence) / 2

        # Create analysis result
        analysis = ContentAnalysis(
            content_type=content_type,
            emotional_tone=emotional_tone,
            confidence=overall_confidence,
            keywords=keywords,
            themes=themes,
            recommended_voice_settings=voice_settings,
            recommended_visual_effects=visual_effects,
            recommended_timing=timing_settings,
            color_palette=color_palette
        )

        # Cache the result for future use
        if self.cache_enabled:
            self._analysis_cache[cache_key] = analysis
            self._cache_timestamps[cache_key] = time.time()
            # Reduced logging: print(f"💾 Cached analysis result (cache size: {len(self._analysis_cache)})")

        return analysis

    def _analyze_content_type(self, text: str) -> Tuple[ContentType, float]:
        """Analyze and determine content type"""
        scores = {}
        
        for content_type, keywords in self.content_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[content_type] = score / len(keywords)
        
        if not scores:
            return ContentType.UNKNOWN, 0.0
        
        best_type = max(scores, key=scores.get)
        confidence = min(scores[best_type] * 2, 1.0)  # Scale confidence
        
        return best_type, confidence

    def _analyze_emotional_tone(self, text: str) -> Tuple[EmotionalTone, float]:
        """Analyze and determine emotional tone"""
        scores = {}
        
        for emotion, keywords in self.emotional_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[emotion] = score / len(keywords)
        
        if not scores:
            return EmotionalTone.NEUTRAL, 0.5
        
        best_emotion = max(scores, key=scores.get)
        confidence = min(scores[best_emotion] * 2, 1.0)
        
        return best_emotion, confidence

    def _extract_keywords(self, text: str, content_type: ContentType, emotional_tone: EmotionalTone) -> List[str]:
        """Extract relevant keywords from text"""
        keywords = []
        
        # Add content-specific keywords found in text
        if content_type in self.content_keywords:
            keywords.extend([kw for kw in self.content_keywords[content_type] if kw in text])
        
        # Add emotion-specific keywords found in text
        if emotional_tone in self.emotional_keywords:
            keywords.extend([kw for kw in self.emotional_keywords[emotional_tone] if kw in text])
        
        return list(set(keywords))[:10]  # Limit to top 10 unique keywords

    def _extract_themes(self, text: str, content_type: ContentType) -> List[str]:
        """Extract main themes from content"""
        themes = []
        
        # Theme extraction based on content type
        if content_type == ContentType.HISTORICAL:
            themes = ['heritage', 'legacy', 'time', 'change', 'civilization']
        elif content_type == ContentType.STORY_REVIEW:
            themes = ['narrative', 'character development', 'plot', 'symbolism']
        elif content_type == ContentType.QUOTE_REFLECTION:
            themes = ['wisdom', 'life lessons', 'philosophy', 'truth']
        else:
            themes = ['knowledge', 'understanding', 'insight']
        
        return themes

    def _get_voice_recommendations(self, content_type: ContentType, emotional_tone: EmotionalTone) -> Dict:
        """Get voice settings recommendations based on content analysis"""
        base_settings = {
            'speed': 1.0,
            'emotion': 'neutral',
            'language': 'en',
            'voice_actor': 'Default',
            'volume': 0.8,
            'pitch_variation': 0.1
        }

        # Adjust based on content type
        if content_type == ContentType.HISTORICAL:
            base_settings.update({
                'speed': 0.9,
                'emotion': 'serious',
                'pitch_variation': 0.05
            })
        elif content_type == ContentType.STORY_REVIEW:
            base_settings.update({
                'speed': 1.0,
                'emotion': 'dramatic',
                'pitch_variation': 0.15
            })
        elif content_type == ContentType.QUOTE_REFLECTION:
            base_settings.update({
                'speed': 0.8,
                'emotion': 'reflective',
                'pitch_variation': 0.08
            })

        # Adjust based on emotional tone
        if emotional_tone == EmotionalTone.DRAMATIC:
            base_settings.update({
                'speed': 0.85,
                'volume': 0.9,
                'pitch_variation': 0.2
            })
        elif emotional_tone == EmotionalTone.REFLECTIVE:
            base_settings.update({
                'speed': 0.75,
                'volume': 0.7,
                'pitch_variation': 0.05
            })
        elif emotional_tone == EmotionalTone.INSPIRATIONAL:
            base_settings.update({
                'speed': 1.1,
                'volume': 0.85,
                'pitch_variation': 0.12
            })

        return base_settings

    def _get_visual_recommendations(self, content_type: ContentType, emotional_tone: EmotionalTone) -> Dict:
        """Get visual effects recommendations"""
        effects = {
            'transitions': 'fade',
            'zoom_effect': True,
            'pan_effect': False,
            'color_grading': 'neutral',
            'contrast_boost': 1.0,
            'saturation': 1.0,
            'brightness': 0.0,
            'vignette': False,
            'film_grain': False
        }

        # Content-specific adjustments
        if content_type == ContentType.HISTORICAL:
            effects.update({
                'transitions': 'dissolve',
                'pan_effect': True,
                'color_grading': 'vintage',
                'saturation': 0.8,
                'film_grain': True,
                'vignette': True
            })
        elif content_type == ContentType.STORY_REVIEW:
            effects.update({
                'transitions': 'crossfade',
                'zoom_effect': True,
                'color_grading': 'cinematic',
                'contrast_boost': 1.2
            })
        elif content_type == ContentType.QUOTE_REFLECTION:
            effects.update({
                'transitions': 'slow_fade',
                'zoom_effect': False,
                'color_grading': 'warm',
                'brightness': 0.1,
                'vignette': True
            })

        # Emotional adjustments
        if emotional_tone == EmotionalTone.NOSTALGIC:
            effects.update({
                'color_grading': 'sepia',
                'saturation': 0.7,
                'film_grain': True
            })
        elif emotional_tone == EmotionalTone.DRAMATIC:
            effects.update({
                'contrast_boost': 1.3,
                'saturation': 1.2,
                'vignette': True
            })
        elif emotional_tone == EmotionalTone.MELANCHOLIC:
            effects.update({
                'color_grading': 'cool',
                'saturation': 0.6,
                'brightness': -0.1
            })

        return effects

    def _get_timing_recommendations(self, content_type: ContentType, emotional_tone: EmotionalTone) -> Dict:
        """Get timing recommendations for video generation"""
        timing = {
            'image_duration': 4.0,
            'transition_duration': 0.5,
            'pause_emphasis': 1.0,
            'rhythm_variation': 0.1,
            'sync_precision': 'high'
        }

        # Content-specific timing
        if content_type == ContentType.HISTORICAL:
            timing.update({
                'image_duration': 5.0,
                'transition_duration': 0.8,
                'pause_emphasis': 1.2
            })
        elif content_type == ContentType.QUOTE_REFLECTION:
            timing.update({
                'image_duration': 6.0,
                'transition_duration': 1.0,
                'pause_emphasis': 1.5,
                'rhythm_variation': 0.05
            })
        elif content_type == ContentType.STORY_REVIEW:
            timing.update({
                'image_duration': 3.5,
                'transition_duration': 0.4,
                'rhythm_variation': 0.15
            })

        # Emotional timing adjustments
        if emotional_tone == EmotionalTone.DRAMATIC:
            timing.update({
                'pause_emphasis': 1.3,
                'rhythm_variation': 0.2
            })
        elif emotional_tone == EmotionalTone.REFLECTIVE:
            timing.update({
                'image_duration': timing['image_duration'] * 1.2,
                'pause_emphasis': 1.4,
                'rhythm_variation': 0.05
            })

        return timing

    def _get_color_recommendations(self, content_type: ContentType, emotional_tone: EmotionalTone) -> Dict:
        """Get color palette recommendations"""
        colors = {
            'primary_hue': 'neutral',
            'temperature': 'balanced',
            'saturation_level': 'normal',
            'contrast_style': 'medium',
            'mood_overlay': None
        }

        # Content-based colors
        if content_type == ContentType.HISTORICAL:
            colors.update({
                'primary_hue': 'brown',
                'temperature': 'warm',
                'saturation_level': 'low',
                'mood_overlay': 'vintage'
            })
        elif content_type == ContentType.QUOTE_REFLECTION:
            colors.update({
                'primary_hue': 'gold',
                'temperature': 'warm',
                'saturation_level': 'medium'
            })

        # Emotional color adjustments
        if emotional_tone == EmotionalTone.MELANCHOLIC:
            colors.update({
                'primary_hue': 'blue',
                'temperature': 'cool',
                'saturation_level': 'low'
            })
        elif emotional_tone == EmotionalTone.INSPIRATIONAL:
            colors.update({
                'primary_hue': 'orange',
                'temperature': 'warm',
                'saturation_level': 'high'
            })
        elif emotional_tone == EmotionalTone.MYSTERIOUS:
            colors.update({
                'primary_hue': 'purple',
                'temperature': 'cool',
                'contrast_style': 'high'
            })

        return colors

    def _get_default_voice_settings(self) -> Dict:
        """Default voice settings"""
        return {
            'speed': 1.0,
            'emotion': 'neutral',
            'language': 'en',
            'voice_actor': 'Default',
            'volume': 0.8,
            'pitch_variation': 0.1
        }

    def _get_default_visual_effects(self) -> Dict:
        """Default visual effects"""
        return {
            'transitions': 'fade',
            'zoom_effect': True,
            'pan_effect': False,
            'color_grading': 'neutral',
            'contrast_boost': 1.0,
            'saturation': 1.0,
            'brightness': 0.0,
            'vignette': False,
            'film_grain': False
        }

    def _get_default_timing(self) -> Dict:
        """Default timing settings"""
        return {
            'image_duration': 4.0,
            'transition_duration': 0.5,
            'pause_emphasis': 1.0,
            'rhythm_variation': 0.1,
            'sync_precision': 'high'
        }

    def _get_default_colors(self) -> Dict:
        """Default color settings"""
        return {
            'primary_hue': 'neutral',
            'temperature': 'balanced',
            'saturation_level': 'normal',
            'contrast_style': 'medium',
            'mood_overlay': None
        }

    def _create_default_analysis(self) -> ContentAnalysis:
        """Create default analysis for empty or invalid content"""
        return ContentAnalysis(
            content_type=ContentType.UNKNOWN,
            emotional_tone=EmotionalTone.NEUTRAL,
            confidence=0.0,
            keywords=[],
            themes=[],
            recommended_voice_settings=self._get_default_voice_settings(),
            recommended_visual_effects=self._get_default_visual_effects(),
            recommended_timing=self._get_default_timing(),
            color_palette=self._get_default_colors()
        )
