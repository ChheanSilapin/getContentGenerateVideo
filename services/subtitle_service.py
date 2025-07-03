"""
Optimized Subtitle Service - Natural Speech Group Synchronization
Simplified implementation using Whisper-timestamped (word-level) and Vosk (fallback) for precise subtitle timing
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
        Generate subtitles using optimized speech recognition timing synchronization

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

            # Use TTS-processed text for timing alignment (same text used for audio generation)
            # but prepare subtitle-formatted text for display
            from utils.text_processing import normalize_text_for_subtitles

            # Get the processed text that was actually used for TTS generation
            tts_text = audio_timing_result.processed_text or text
            subtitle_text = normalize_text_for_subtitles(text)

            print(f"[SUBTITLE] Using TTS text for timing alignment, subtitle text for display")

            # Create word groups using TTS text for accurate timing synchronization
            word_groups = self._create_word_groups(tts_text)

            # Create corresponding subtitle groups for display formatting
            subtitle_groups = self._create_word_groups(subtitle_text)
            if not word_groups or not subtitle_groups:
                return False

            # Handle group count mismatch intelligently
            if len(word_groups) != len(subtitle_groups):
                print(f"[SUBTITLE] Group count mismatch: TTS groups ({len(word_groups)}) != subtitle groups ({len(subtitle_groups)})")
                # Create aligned subtitle groups that match TTS group timing
                subtitle_groups = self._align_subtitle_groups_to_timing(subtitle_groups, word_groups)
                print(f"[SUBTITLE] Aligned to {len(subtitle_groups)} groups for timing synchronization")

            # Extract timing from speech recognition analysis using TTS-aligned word groups
            timing_result = self._extract_timing_from_analysis(audio_timing_result, word_groups)
            print(f"[SUBTITLE] Timing method: {timing_result.method}")

            if timing_result.success:
                # Use precise timing from speech recognition with subtitle text for display
                events = self._create_subtitle_events_from_timing(subtitle_groups, timing_result.segments)
            else:
                # Fallback to calculated timing with subtitle text for display
                print(f"[SUBTITLE] Using fallback timing calculation")
                audio_duration = get_media_duration_safe(audio_timing_result.audio_file)
                timings = self._calculate_fallback_timing(word_groups, audio_duration)
                events = self._create_subtitle_events(subtitle_groups, timings)

            # Write subtitle file
            self._write_subtitle_file(output_file, events, style)
            print(f"[SUBTITLE] Generated {len(events)} subtitle events")

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

    def _align_subtitle_groups_to_timing(self, subtitle_groups: List[Dict], timing_groups: List[Dict]) -> List[Dict]:
        """
        Align subtitle groups to match timing groups for proper synchronization.
        This handles cases where TTS processing changes word count.
        """
        if len(subtitle_groups) == len(timing_groups):
            return subtitle_groups

        # If subtitle groups are fewer, redistribute subtitle text across timing groups
        if len(subtitle_groups) < len(timing_groups):
            return self._redistribute_subtitle_groups(subtitle_groups, len(timing_groups))

        # If subtitle groups are more, combine them to match timing groups
        else:
            return self._combine_subtitle_groups(subtitle_groups, len(timing_groups))

    def _redistribute_subtitle_groups(self, groups: List[Dict], target_count: int) -> List[Dict]:
        """Redistribute subtitle groups to match target count"""
        if not groups or target_count <= 0:
            return groups

        # Combine all text and redistribute
        all_words = []
        for group in groups:
            all_words.extend(group['text'].split())

        # Create new groups with approximately equal word distribution
        words_per_group = max(1, len(all_words) // target_count)
        new_groups = []

        for i in range(target_count):
            start_idx = i * words_per_group
            if i == target_count - 1:  # Last group gets remaining words
                end_idx = len(all_words)
            else:
                end_idx = (i + 1) * words_per_group

            group_words = all_words[start_idx:end_idx]
            if group_words:
                new_groups.append({
                    'text': ' '.join(group_words),
                    'word_count': len(group_words)
                })

        return new_groups

    def _combine_subtitle_groups(self, groups: List[Dict], target_count: int) -> List[Dict]:
        """Combine subtitle groups to match target count"""
        if not groups or target_count <= 0:
            return groups

        if target_count >= len(groups):
            return groups

        # Calculate how many original groups to combine for each target group
        groups_per_target = len(groups) / target_count
        new_groups = []

        for i in range(target_count):
            start_idx = int(i * groups_per_target)
            end_idx = int((i + 1) * groups_per_target) if i < target_count - 1 else len(groups)

            # Combine text from multiple groups
            combined_text = []
            combined_word_count = 0

            for j in range(start_idx, end_idx):
                if j < len(groups):
                    combined_text.append(groups[j]['text'])
                    combined_word_count += groups[j].get('word_count', len(groups[j]['text'].split()))

            if combined_text:
                new_groups.append({
                    'text': ' '.join(combined_text),
                    'word_count': combined_word_count
                })

        return new_groups

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
        """Properly tokenize text preserving contractions, possessives, hyphens, currency, and percentages"""
        import re

        # Clean up extra whitespace
        text = ' '.join(text.split())

        # Enhanced pattern to match:
        # - Regular words: hello, world
        # - Contractions: don't, can't, let's, we're, I'm, etc.
        # - Possessives: John's, cat's, etc.
        # - Hyphenated words: well-known, twenty-one, etc.
        # - Currency amounts: $1.2, $17,190, $21,590.50
        # - Percentages: 19.7%, 100%
        # - Numbers with decimals: 1.2, 19.7
        # - Numbers with commas: 1,200, 30,000

        # Split on whitespace but preserve special tokens
        tokens = []

        # Pattern for currency: $123.45, $1,234.56, $1.2
        currency_pattern = r'\$[\d,]+(?:\.\d+)?'

        # Pattern for percentages: 19.7%, 100%
        percentage_pattern = r'\d+(?:\.\d+)?%'

        # Pattern for numbers with decimals: 1.2, 19.7
        decimal_pattern = r'\d+\.\d+'

        # Pattern for numbers with commas: 1,200, 30,000
        comma_number_pattern = r'\d{1,3}(?:,\d{3})+'

        # Pattern for contractions and possessives: don't, John's
        contraction_pattern = r"\b\w+[''-]\w+(?:[''-]\w+)*\b"

        # Pattern for regular words
        word_pattern = r'\b\w+\b'

        # Combine all patterns in order of priority
        combined_pattern = f'({currency_pattern}|{percentage_pattern}|{decimal_pattern}|{comma_number_pattern}|{contraction_pattern}|{word_pattern})'

        # Find all tokens
        matches = re.findall(combined_pattern, text)

        # Clean and filter tokens
        for match in matches:
            if match.strip():
                tokens.append(match.strip())

        return tokens

    def _extract_timing_from_analysis(self, audio_timing_result, word_groups: List[Dict]) -> SubtitleTimingResult:
        """Extract timing segments from speech recognition analysis using best available method"""
        try:
            timing_data = audio_timing_result.timing_data

            # Priority 1: Whisper-timestamped for precise word-level timing
            if timing_data.get('whisper_segments'):
                segments = self._create_timing_from_whisper(timing_data['whisper_segments'], word_groups)
                if segments:
                    return SubtitleTimingResult(
                        success=True,
                        segments=segments,
                        method='whisper',
                        confidence=timing_data.get('confidence_score', 0.9)
                    )

            # Priority 2: Combined segments (fallback)
            elif timing_data.get('combined_segments'):
                segments = self._create_timing_from_segments(timing_data['combined_segments'], word_groups)
                if segments:
                    return SubtitleTimingResult(
                        success=True,
                        segments=segments,
                        method=timing_data.get('method_used', 'combined'),
                        confidence=timing_data.get('confidence_score', 0.7)
                    )

            # Priority 3: Vosk segments (basic fallback)
            elif timing_data.get('vosk_segments'):
                segments = self._create_timing_from_segments(timing_data['vosk_segments'], word_groups)
                if segments:
                    return SubtitleTimingResult(
                        success=True,
                        segments=segments,
                        method='vosk',
                        confidence=timing_data.get('confidence_score', 0.5)
                    )

            return SubtitleTimingResult(success=False, method='no_segments')

        except Exception as e:
            print(f"[SUBTITLE] Timing extraction error: {e}")
            return SubtitleTimingResult(success=False, method='error')

    def _create_timing_from_whisper(self, whisper_segments: List[Dict], word_groups: List[Dict]) -> List[Dict]:
        """Create optimized timing using Whisper word-level timestamps"""
        if not whisper_segments or not word_groups:
            return []

        # Check if we have word-level timing from Whisper
        has_word_timing = any(seg.get('words') for seg in whisper_segments)

        if has_word_timing:
            # Count total words available
            total_words = sum(len(seg.get('words', [])) for seg in whisper_segments)
            print(f"[SUBTITLE] Using Whisper word-level timing ({len(whisper_segments)} segments, {total_words} words)")
            return self._create_word_level_timing(whisper_segments, word_groups)
        else:
            print(f"[SUBTITLE] Using Whisper segment-level timing")
            return self._create_timing_from_segments(whisper_segments, word_groups)

    def _create_timing_from_segments(self, segments: List[Dict], word_groups: List[Dict]) -> List[Dict]:
        """Create timing from basic segment data (Vosk or segment-level Whisper)"""
        if not segments or not word_groups:
            return []

        timing_segments = []

        # If we have multiple segments, distribute groups across them
        if len(segments) > 1:
            # Distribute word groups proportionally across available segments
            groups_per_segment = len(word_groups) / len(segments)

            for i, segment in enumerate(segments):
                start_group_idx = int(i * groups_per_segment)
                end_group_idx = int((i + 1) * groups_per_segment)
                if i == len(segments) - 1:  # Last segment gets remaining groups
                    end_group_idx = len(word_groups)

                segment_groups = word_groups[start_group_idx:end_group_idx]
                if segment_groups:
                    # Distribute timing within this segment
                    segment_duration = segment['end'] - segment['start']
                    time_per_group = segment_duration / len(segment_groups)

                    for j, group in enumerate(segment_groups):
                        group_start = segment['start'] + (j * time_per_group)
                        group_end = segment['start'] + ((j + 1) * time_per_group)

                        timing_segments.append({
                            'text': group['text'],
                            'start': group_start,
                            'end': group_end,
                            'confidence': segment.get('confidence', 0.7)
                        })
        else:
            # Single segment - distribute groups evenly
            segment = segments[0]
            segment_duration = segment['end'] - segment['start']
            time_per_group = segment_duration / len(word_groups)

            for i, group in enumerate(word_groups):
                group_start = segment['start'] + (i * time_per_group)
                group_end = segment['start'] + ((i + 1) * time_per_group)

                timing_segments.append({
                    'text': group['text'],
                    'start': group_start,
                    'end': group_end,
                    'confidence': segment.get('confidence', 0.7)
                })

        return timing_segments

    def _create_subtitle_events_from_timing(self, word_groups: List[Dict], timing_segments: List[Dict]) -> List[Dict]:
        """Create subtitle events directly from timing segments (optimized path)"""
        events = []

        # Use timing segments directly if they match word groups
        if len(timing_segments) == len(word_groups):
            for group, timing in zip(word_groups, timing_segments):
                # Use exact Whisper timing for perfect voice synchronization
                adjusted_start = timing['start']
                adjusted_end = timing['end']

                # Clean text for ASS format
                text = group['text'].strip()
                text = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
                text = self._add_line_breaks_for_long_text(text)

                events.append({
                    'text': text,
                    'start': adjusted_start,
                    'end': adjusted_end,
                    'style': 'Default'
                })
        else:
            # Fallback to proportional mapping
            print(f"[SUBTITLE] Timing mismatch: {len(timing_segments)} segments vs {len(word_groups)} groups")
            timings = [(seg['start'], seg['end']) for seg in timing_segments]
            if len(timings) != len(word_groups):
                # Create proportional timings
                if timing_segments:
                    total_start = timing_segments[0]['start']
                    total_end = timing_segments[-1]['end']
                    total_duration = total_end - total_start

                    timings = []
                    for i in range(len(word_groups)):
                        group_ratio = i / len(word_groups)
                        next_group_ratio = (i + 1) / len(word_groups)
                        start_time = total_start + (group_ratio * total_duration)
                        end_time = total_start + (next_group_ratio * total_duration)
                        timings.append((start_time, end_time))

            events = self._create_subtitle_events(word_groups, timings)

        return events

    def _create_word_level_timing(self, segments: List[Dict], word_groups: List[Dict]) -> List[Dict]:
        """Create precise timing using Whisper word-level timestamps"""
        if not segments or not word_groups:
            return []

        # Flatten all word timestamps from all segments
        all_words = []
        for segment in segments:
            if segment.get('words'):
                for word in segment['words']:
                    # Handle WhisperTimestamp objects (they have .text, .start, .end attributes)
                    if hasattr(word, 'text'):
                        all_words.append({
                            'text': word.text.strip(),
                            'start': word.start,
                            'end': word.end,
                            'confidence': getattr(word, 'confidence', 0.9)
                        })
                    # Handle dictionary format (fallback)
                    elif isinstance(word, dict):
                        all_words.append({
                            'text': word.get('text', '').strip(),
                            'start': word.get('start', 0.0),
                            'end': word.get('end', 0.0),
                            'confidence': word.get('confidence', 0.9)
                        })

        if not all_words:
            print(f"[SUBTITLE] No word-level timing found, falling back to segment timing")
            return self._create_timing_from_segments(segments, word_groups)

        print(f"[SUBTITLE] Extracted {len(all_words)} words from Whisper for precise timing")

        # Use proportional timing distribution instead of word matching
        # This avoids the TTS vs subtitle word mismatch issue
        mapped_segments = []

        if all_words:
            total_start = all_words[0]['start']
            total_end = all_words[-1]['end']
            total_duration = total_end - total_start

            # Apply timing offset compensation for FFmpeg's -avoid_negative_ts make_zero
            # This parameter can shift audio timing in the final video
            timing_offset = self._calculate_timing_offset(total_start)

            print(f"[SUBTITLE] Distributing {len(word_groups)} groups across {total_duration:.2f}s of audio")
            if timing_offset != 0:
                print(f"[SUBTITLE] Applying timing offset compensation: {timing_offset:.3f}s")

            for i, group in enumerate(word_groups):
                # Calculate proportional timing for this group
                group_ratio_start = i / len(word_groups)
                group_ratio_end = (i + 1) / len(word_groups)

                group_start = total_start + (group_ratio_start * total_duration) + timing_offset
                group_end = total_start + (group_ratio_end * total_duration) + timing_offset

                # Ensure minimum duration
                min_duration = 0.8
                if group_end - group_start < min_duration:
                    group_end = group_start + min_duration

                # Prevent overlaps with previous group
                if mapped_segments:
                    prev_end = mapped_segments[-1]['end']
                    if group_start < prev_end:
                        group_start = prev_end
                        group_end = max(group_end, group_start + min_duration)

                mapped_segments.append({
                    'text': group['text'],
                    'start': group_start,
                    'end': group_end,
                    'confidence': 0.9  # High confidence for proportional timing
                })

        print(f"[SUBTITLE] Created {len(mapped_segments)} timed segments using proportional distribution")
        return mapped_segments

    def _calculate_timing_offset(self, audio_start_time: float) -> float:
        """
        Calculate timing offset to compensate for FFmpeg's -avoid_negative_ts make_zero

        This parameter can shift audio timing in the final video, causing subtitle misalignment.
        We apply a small compensation based on the original audio start time.

        Args:
            audio_start_time: Start time from original audio analysis

        Returns:
            float: Timing offset in seconds to apply to subtitles
        """
        # If audio starts very close to 0, FFmpeg might apply a small positive shift
        # to avoid negative timestamps during video processing
        if audio_start_time < 0.5:
            # Apply a small positive offset to account for FFmpeg timestamp correction
            return 0.1

        # For audio that starts later, no offset needed
        return 0.0

    def _calculate_word_match_score(self, word1: str, word2: str) -> float:
        """Calculate similarity score between two words (0.0 to 1.0)"""
        if not word1 or not word2:
            return 0.0

        # Normalize words for comparison
        w1 = word1.lower().strip('.,!?;:')
        w2 = word2.lower().strip('.,!?;:')

        # Exact match
        if w1 == w2:
            return 1.0

        # Check if one word contains the other
        if w1 in w2 or w2 in w1:
            return 0.8

        # Check for common prefixes/suffixes
        if len(w1) > 2 and len(w2) > 2:
            if w1[:3] == w2[:3] or w1[-3:] == w2[-3:]:
                return 0.6

        return 0.0

    def _words_match(self, word1: str, word2: str) -> bool:
        """Check if two words match (handles punctuation and case)"""
        import re
        # Remove punctuation and compare
        clean1 = re.sub(r'[^\w]', '', word1.lower())
        clean2 = re.sub(r'[^\w]', '', word2.lower())
        return clean1 == clean2





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

            # Use exact Whisper timing for perfect voice synchronization
            adjusted_start = max(0.0, start)  # Don't go below 0
            adjusted_end = end

            # Debug logging for timing verification
            if i < 3:  # Only log first 3 events to avoid spam
                print(f"[SUBTITLE TIMING] Event {i+1}: '{text[:30]}...' | Original: {start:.2f}-{end:.2f}s | Adjusted: {adjusted_start:.2f}-{adjusted_end:.2f}s")

            events.append({
                'text': text,
                'start': adjusted_start,
                'end': adjusted_end,
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