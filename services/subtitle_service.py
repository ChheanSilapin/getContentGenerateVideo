"""
Optimized Subtitle Service - TTS-to-Text Timing Synchronization
Clean implementation using speech recognition analysis for perfect subtitle timing
"""
import os
from typing import Dict, List, Tuple

# Import centralized config
from config import SUBTITLE_CONFIG
from utils.helpers import ensure_directory_exists, get_media_duration_safe



class SubtitleTimingResult:
    """Result from subtitle timing analysis"""
    def __init__(self, success: bool, segments: List[Dict] = None, method: str = "", confidence: float = 0.0):
        self.success = success
        self.segments = segments or []
        self.method = method
        self.confidence = confidence


class SynchronizedSubtitleGenerator:
    """Subtitle generator using TTS-to-Text timing synchronization"""

    def __init__(self):
        self.config = SUBTITLE_CONFIG

    def generate_subtitles_with_timing_sync(self, text: str, audio_timing_result, 
                                          output_file: str, style: str = "modern_glow") -> bool:
        """
        Generate subtitles using TTS-to-Text timing synchronization
        
        Args:
            text: Original text
            audio_timing_result: AudioTimingResult from audio generation
            output_file: Output subtitle file path
            style: Subtitle style
            
        Returns:
            bool: Success status
        """
        try:
            # Validate inputs
            if not text or not audio_timing_result or not audio_timing_result.success:
                return False

            # Create output directory
            ensure_directory_exists(os.path.dirname(output_file))

            # Text is already preprocessed when passed from video generation
            cleaned_text = text

            # Debug: Log what text the subtitle service receives
            print(f"[SUBTITLE DEBUG] Received text: '{text[:50]}...'")
            if "It's" in text or "Let's" in text or "I'll" in text:
                print("[SUBTITLE DEBUG] ✅ Received properly preserved contractions")
            elif "It s" in text or "Let s" in text or "I ll" in text:
                print("[SUBTITLE DEBUG] ❌ Received text with broken contractions")
            else:
                print("[SUBTITLE DEBUG] ℹ️ No contractions found in received text")

            # Create natural speech groups for subtitle timing
            word_groups = self._create_word_groups(cleaned_text)
            if not word_groups:
                return False

            # Extract timing from speech recognition analysis
            timing_result = self._extract_timing_from_analysis(audio_timing_result, word_groups)
            if not timing_result.success:
                # Fallback to calculated timing
                audio_duration = get_media_duration_safe(audio_timing_result.audio_file)
                timings = self._calculate_fallback_timing(word_groups, audio_duration)
            else:
                timings = [(seg['start'], seg['end']) for seg in timing_result.segments]

            # Create subtitle events
            events = self._create_subtitle_events(word_groups, timings)

            # Write subtitle file
            self._write_subtitle_file(output_file, events, style)

            return True

        except Exception as e:
            print(f"Subtitle generation failed: {e}")
            return False

    def _create_word_groups(self, text: str) -> List[Dict]:
        """Create natural speech groups with proper word tokenization"""
        # Properly tokenize words (handle contractions, possessives, hyphens)
        words = self._tokenize_words_properly(text)

        # Create natural speech groups instead of fixed 5-word chunks
        word_groups = self._create_natural_speech_groups(words)

        return word_groups

    def _create_natural_speech_groups(self, words: List[str]) -> List[Dict]:
        """Create natural speech groups based on punctuation and speech patterns"""
        if not words:
            return []

        groups = []
        current_group = []
        max_words_per_group = 6  # Slightly larger for natural breaks

        for word in words:
            current_group.append(word)

            # Check for natural break points
            should_break = False

            # Break at sentence endings
            if word.endswith(('.', '!', '?')):
                should_break = True
            # Break at commas if group is getting long
            elif word.endswith(',') and len(current_group) >= 3:
                should_break = True
            # Break at conjunctions if group is getting long
            elif word.lower() in ['and', 'but', 'or', 'so', 'yet', 'through', 'while'] and len(current_group) >= 4:
                should_break = True
            # Force break if group gets too long
            elif len(current_group) >= max_words_per_group:
                should_break = True

            if should_break:
                # Create group
                group_text = ' '.join(current_group)
                groups.append({
                    'text': group_text,
                    'words': current_group.copy(),
                    'word_count': len(current_group)
                })
                current_group = []

        # Add remaining words as final group
        if current_group:
            group_text = ' '.join(current_group)
            groups.append({
                'text': group_text,
                'words': current_group,
                'word_count': len(current_group)
            })

        return groups

    def _tokenize_words_properly(self, text: str) -> List[str]:
        """Properly tokenize text preserving contractions, possessives, and hyphens"""
        import re

        # Clean up extra whitespace
        text = ' '.join(text.split())

        # Use regex to split on whitespace but preserve contractions and hyphens
        # This pattern splits on whitespace but keeps:
        # - Contractions: don't, can't, let's, we're, I'm, etc.
        # - Possessives: John's, cat's, etc.
        # - Hyphenated words: well-known, twenty-one, etc.
        # - Compound contractions: shouldn't've, etc.

        # Use a better tokenization approach that preserves contractions
        # Pattern to match words with contractions, possessives, and hyphens
        word_pattern = r"\b\w+(?:[''-]\w+)*\b"

        # Find all words using the pattern
        words = re.findall(word_pattern, text)

        # Clean up any remaining punctuation while preserving internal apostrophes/hyphens
        cleaned_words = []
        for word in words:
            # Remove leading/trailing punctuation but keep internal apostrophes and hyphens
            clean_word = re.sub(r'^[^\w\'-]+|[^\w\'-]+$', '', word)
            if clean_word and re.search(r'\w', clean_word):
                cleaned_words.append(clean_word)

        return cleaned_words

    def _extract_timing_from_analysis(self, audio_timing_result, word_groups: List[Dict]) -> SubtitleTimingResult:
        """Extract timing segments from speech recognition analysis"""
        try:
            timing_data = audio_timing_result.timing_data
            
            # Try combined segments first (best quality)
            if timing_data.get('combined_segments'):
                segments = self._map_segments_to_groups(timing_data['combined_segments'], word_groups)
                return SubtitleTimingResult(
                    success=True, 
                    segments=segments, 
                    method=timing_data.get('method_used', 'combined'),
                    confidence=timing_data.get('confidence_score', 0.0)
                )
            
            # Try Whisper segments
            if timing_data.get('whisper_segments'):
                segments = self._map_segments_to_groups(timing_data['whisper_segments'], word_groups)
                return SubtitleTimingResult(
                    success=True, 
                    segments=segments, 
                    method='whisper',
                    confidence=timing_data.get('confidence_score', 0.0)
                )
            
            # Try Vosk segments
            if timing_data.get('vosk_segments'):
                segments = self._map_segments_to_groups(timing_data['vosk_segments'], word_groups)
                return SubtitleTimingResult(
                    success=True, 
                    segments=segments, 
                    method='vosk',
                    confidence=timing_data.get('confidence_score', 0.0)
                )
            
            return SubtitleTimingResult(success=False, method='no_segments')

        except Exception as e:
            return SubtitleTimingResult(success=False, method='error')

    def _map_segments_to_groups(self, segments: List[Dict], word_groups: List[Dict]) -> List[Dict]:
        """Map natural speech groups to Whisper timing for synchronized subtitles"""
        if not segments:
            return []

        # Use Whisper timing to synchronize natural speech groups
        return self._create_group_level_timing(segments, word_groups)

    def _create_group_level_timing(self, segments: List[Dict], word_groups: List[Dict]) -> List[Dict]:
        """Create precise timing for 5-word groups using Whisper-timestamped word-level timing"""
        if not segments or not word_groups:
            return []

        mapped_segments = []

        # Try to use word-level timing if available
        try:
            # Check if we have proper Whisper result with word-level timing
            if hasattr(segments[0], 'words') or 'words' in segments[0]:
                # We have word-level timing, use it directly
                whisper_words = []
                for segment in segments:
                    if hasattr(segment, 'words'):
                        # WhisperSegment object
                        for word in segment.words:
                            whisper_words.append({
                                'word': word.text.strip().lower(),
                                'start': word.start,
                                'end': word.end
                            })
                    elif 'words' in segment and segment['words']:
                        # Dictionary with words
                        for word_info in segment['words']:
                            # Handle both dictionary and object formats
                            if isinstance(word_info, dict):
                                word_text = word_info.get('word', '').strip().lower()
                                # Get segment fallback values
                                segment_start = getattr(segment, 'start', 0) if hasattr(segment, 'start') else segment.get('start', 0)
                                segment_end = getattr(segment, 'end', 0) if hasattr(segment, 'end') else segment.get('end', 0)
                                word_start = word_info.get('start', segment_start)
                                word_end = word_info.get('end', segment_end)
                            else:
                                # Whisper word object
                                word_text = getattr(word_info, 'text', '').strip().lower()
                                word_start = getattr(word_info, 'start', 0)
                                word_end = getattr(word_info, 'end', 0)

                            whisper_words.append({
                                'word': word_text,
                                'start': word_start,
                                'end': word_end
                            })

                # Map each natural speech group to corresponding Whisper words
                whisper_word_index = 0

                for i, word_group in enumerate(word_groups):
                    group_words = word_group['words']  # Use the properly tokenized words

                    # Find timing for this group's words
                    group_start = None
                    group_end = None
                    words_matched = 0

                    # Try to match group words with Whisper words
                    for group_word in group_words:
                        if whisper_word_index < len(whisper_words):
                            whisper_word = whisper_words[whisper_word_index]

                            # Set start time from first word
                            if group_start is None:
                                group_start = whisper_word['start']

                            # Update end time with each word
                            group_end = whisper_word['end']

                            whisper_word_index += 1
                            words_matched += 1
                        else:
                            # No more Whisper words, use fallback timing
                            break

                    # Fallback if no timing found
                    if group_start is None or group_end is None:
                        if mapped_segments:
                            # Continue from last segment
                            group_start = mapped_segments[-1]['end']
                            group_end = group_start + 1.5  # Default 1.5s per group
                        else:
                            # First group, use segment timing
                            if hasattr(segments[0], 'start'):
                                group_start = segments[0].start
                            elif isinstance(segments[0], dict):
                                group_start = segments[0].get('start', 0)
                            else:
                                group_start = 0
                            group_end = group_start + 1.5

                    # Ensure minimum duration
                    if group_end - group_start < 0.8:
                        group_end = group_start + 0.8

                    mapped_segments.append({
                        'text': word_group['text'],
                        'start': group_start,
                        'end': group_end,
                        'confidence': 0.9 if words_matched > 0 else 0.5
                    })

                return mapped_segments

        except ImportError:
            pass

        # If word-level timing failed, return empty to use fallback timing
        return mapped_segments

    def _calculate_fallback_timing(self, word_groups: List[Dict], duration: float) -> List[Tuple[float, float]]:
        """Calculate fallback timing when speech recognition fails"""
        if not word_groups or duration <= 0:
            return []

        # Simple even distribution
        num_groups = len(word_groups)
        time_per_group = duration / num_groups

        timings = []
        for i in range(num_groups):
            start_time = i * time_per_group
            end_time = (i + 1) * time_per_group
            timings.append((start_time, end_time))

        return timings

    def _create_subtitle_events(self, word_groups: List[Dict], timings: List[Tuple[float, float]]) -> List[Dict]:
        """Create subtitle events from word groups and timings"""
        events = []

        for i, (group, (start, end)) in enumerate(zip(word_groups, timings)):
            # Clean text for ASS format
            text = group['text'].strip()
            text = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

            # Add manual line breaks for long sentences to prevent word wrapping
            text = self._add_line_breaks_for_long_text(text)

            events.append({
                'text': text,
                'start': start,
                'end': end,
                'style': 'Default'
            })

        return events

    def _add_line_breaks_for_long_text(self, text: str, max_chars_per_line: int = 35, max_lines: int = 2) -> str:
        """
        Add manual line breaks following professional subtitle best practices

        Based on industry standards:
        - 30-40 characters per line maximum
        - 2 lines maximum per subtitle
        - Break at natural speech pauses when possible
        """
        if len(text) <= max_chars_per_line:
            return text

        # Try to break at natural pauses first (commas, semicolons, etc.)
        natural_breaks = [', ', '; ', ' - ', ' and ', ' or ', ' but ', ' so ', ' that ', ' which ', ' when ', ' where ']

        # If text is short enough for 2 lines, use smart line breaking
        if len(text) <= max_chars_per_line * max_lines:
            return self._smart_line_break(text, max_chars_per_line, natural_breaks)

        # For 5-word groups, simple line breaking is sufficient
        # Split into 2 lines if text is long
        words = text.split()
        if len(words) <= 3:
            return text

        # Split roughly in the middle
        mid_point = len(words) // 2
        line1 = ' '.join(words[:mid_point])
        line2 = ' '.join(words[mid_point:])

        return f"{line1}\\N{line2}"

    def _smart_line_break(self, text: str, max_chars_per_line: int, natural_breaks: List[str]) -> str:
        """
        Smart line breaking that tries to break at natural pauses
        """
        # Try to find a good break point
        best_break_pos = -1
        best_break_score = 0

        for break_phrase in natural_breaks:
            pos = text.find(break_phrase)
            if pos > 0:
                # Calculate how close this break is to the ideal midpoint
                ideal_pos = len(text) // 2
                distance_from_ideal = abs(pos - ideal_pos)

                # Score based on how close to ideal and length of first line
                line1_len = pos + len(break_phrase)
                if line1_len <= max_chars_per_line:
                    score = max_chars_per_line - distance_from_ideal
                    if score > best_break_score:
                        best_break_score = score
                        best_break_pos = pos + len(break_phrase)

        # If we found a good natural break, use it
        if best_break_pos > 0:
            line1 = text[:best_break_pos].strip()
            line2 = text[best_break_pos:].strip()
            return f"{line1}\\N{line2}"

        # Fallback: break at word boundaries near the middle
        words = text.split()
        if len(words) <= 2:
            return text

        # Find the best word boundary to break at
        mid_point = len(words) // 2
        line1 = ' '.join(words[:mid_point])
        line2 = ' '.join(words[mid_point:])

        # Adjust if first line is too long
        while len(line1) > max_chars_per_line and mid_point > 1:
            mid_point -= 1
            line1 = ' '.join(words[:mid_point])
            line2 = ' '.join(words[mid_point:])

        return f"{line1}\\N{line2}"

    def _write_subtitle_file(self, output_file: str, events: List[Dict], style: str):
        """Write subtitle events to ASS file"""
        # Get style configuration with fallback
        styles = self.config.get("styles", {})
        if not styles:
            # Fallback style configuration
            styles = {
                "modern_glow": {
                    "font": "Arial",
                    "size": 12,  # Reduced from 48 to prevent word wrapping
                    "primary_color": "&H00FFFFFF",
                    "secondary_color": "&H00000000",
                    "outline_color": "&H00000000",
                    "back_color": "&H80000000",
                    "bold": True,
                    "outline_width": 2,
                    "shadow": 1,
                    "alignment": 2,
                    "margin_v": 50  # Reduced margin for better positioning
                }
            }

        style_config = styles.get(style, styles.get("modern_glow", styles[list(styles.keys())[0]]))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write ASS header
            f.write(self._create_ass_header(style_config))
            
            # Write events
            for event in events:
                start_time = self._format_ass_time(event['start'])
                end_time = self._format_ass_time(event['end'])
                text = event['text']
                style_name = event.get('style', 'Default')
                
                f.write(f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{text}\n")

    def _create_ass_header(self, style_config: Dict) -> str:
        """Create ASS file header with style"""
        return f"""[Script Info]
Title: Synchronized Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style_config.get('font', 'Arial')},{style_config.get('size', 20)},{style_config.get('primary_color', '&H00FFFFFF')},{style_config.get('secondary_color', '&H00000000')},{style_config.get('outline_color', '&H00000000')},{style_config.get('back_color', '&H80000000')},{1 if style_config.get('bold', False) else 0},0,0,0,100,100,0,0,1,{style_config.get('outline_width', 2)},{style_config.get('shadow', 1)},{style_config.get('alignment', 2)},10,10,{style_config.get('margin_v', 75)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def _format_ass_time(self, seconds: float) -> str:
        """Format time for ASS subtitle format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:01d}:{minutes:02d}:{secs:05.2f}"

# Global instance
_generator = SynchronizedSubtitleGenerator()

def generate_subtitles_with_timing_sync(text: str, audio_timing_result, output_file: str,
                                       style: str = "modern_glow") -> bool:
    """Global function for subtitle generation with timing synchronization"""
    return _generator.generate_subtitles_with_timing_sync(text, audio_timing_result, output_file, style)

def generate_subtitles(text: str, audio_timing_result, output_file: str,
                      style: str = "modern_glow") -> bool:
    """Legacy function name for backward compatibility"""
    return _generator.generate_subtitles_with_timing_sync(text, audio_timing_result, output_file, style)