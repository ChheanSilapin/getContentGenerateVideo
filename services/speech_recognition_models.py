"""
Data models for speech recognition system
"""
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class SpeechRecognitionResult:
    """Results of speech recognition analysis"""
    original_text: str
    recognized_text: str
    similarity_score: float
    word_accuracy: float
    character_accuracy: float
    differences: List[Dict]
    processing_time: float
    audio_file_path: str
    success: bool
    error_message: str = ""

@dataclass
class TextComparisonMetrics:
    """Detailed metrics for text comparison"""
    total_words_original: int
    total_words_recognized: int
    matching_words: int
    word_accuracy: float
    character_accuracy: float
    similarity_score: float
    levenshtein_distance: int
    differences: List[Dict]
