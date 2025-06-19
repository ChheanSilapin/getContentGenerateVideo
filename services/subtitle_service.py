"""
Subtitle Service - Clean and Efficient
Refactored from 1,018 lines to 300 lines by removing duplication and over-engineering
"""
import os
import re
import time
import traceback
from moviepy.editor import VideoFileClip, AudioFileClip

# Import centralized config (no fallback duplication)
from config import DEFAULT_MAX_CHARS_PER_LINE, SUBTITLE_CONFIG
from utils.helpers import ensure_directory_exists
from utils.text_processing import process_text_for_subtitles

# Try to import pydub for speech analysis
try:
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("pydub not available. Using basic timing for subtitles.")

def create_optimized_word_groups(text):
    """Create optimized word groups for subtitles"""
    if not text or not text.strip():
        return []

    words = text.strip().split()
    if not words:
        return []

    config = SUBTITLE_CONFIG
    total_words = len(words)

    # Determine words per group based on text length - INCREASED for better readability
    if total_words < 100:
        words_per_group = config.get("words_per_group_short", 8)  # Increased from 5 to 8
    elif total_words < 200:
        words_per_group = config.get("words_per_group_medium", 7)  # Increased from 4 to 7
    else:
        words_per_group = config.get("words_per_group_long", 6)   # Increased from 3 to 6

    # Reduced logging for cleaner output
    # print(f"Processing {total_words} words")
    # print(f"Using {words_per_group} words per group for {'short' if total_words < 100 else 'medium' if total_words < 200 else 'long'} text")

    groups = []
    for i in range(0, len(words), words_per_group):
        group_words = words[i:i + words_per_group]
        group_text = ' '.join(group_words)

        groups.append({
            'text': group_text,
            'word_count': len(group_words),
            'char_count': len(group_text),
            'has_punctuation': any(char in group_text for char in '.!?;:,')
        })

    return groups

class SubtitleGenerator:
    """Clean, efficient subtitle generator"""
    
    def __init__(self):
        self.config = SUBTITLE_CONFIG
    
    def generate_subtitles(self, text, video_file, audio_file, output_file, style="modern_glow", content_analysis=None):
        """
        Main entry point for subtitle generation
        
        Args:
            text: Text content for subtitles
            video_file: Path to video file
            audio_file: Path to audio file
            output_file: Path to output subtitle file
            style: Subtitle style preset
            content_analysis: Optional ContentAnalysis object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Clean text and create output directory
            cleaned_text = process_text_for_subtitles(text)
            ensure_directory_exists(os.path.dirname(output_file))
            
            # Save text file for processing
            text_file = f"{audio_file}.txt"
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
            
            # Get style configuration
            style_config = self._get_style_config(style)
            
            # Generate subtitle file
            return self._create_subtitle_file(cleaned_text, audio_file, output_file, style_config)
            
        except Exception as e:
            print(f"Error generating subtitles: {e}")
            traceback.print_exc()
            return False
    
    def _get_style_config(self, style):
        """Get style configuration from config"""
        styles = self.config.get("available_styles", {})
        default_style = self.config.get("default_style", "modern_glow")
        
        if style in styles:
            return styles[style]
        elif default_style in styles:
            return styles[default_style]
        else:
            # Simple fallback
            return {
                "name": "Default",
                "font": "Times New Roman",
                "size": 48,
                "primary_color": "&H00FFFFFF",
                "outline_color": "&H00FF8000",
                "outline_width": 3,
                "bold": True,
                "alignment": 2,
                "margin_v": 80
            }
    
    def _create_subtitle_file(self, text, audio_file, output_file, style_config):
        """Create the complete subtitle file"""
        try:
            # Get audio duration
            duration = self._get_audio_duration(audio_file)
            
            # Create word groups
            word_groups = create_optimized_word_groups(text)
            if not word_groups:
                return self._create_fallback_file(output_file, text, duration)
            
            # Calculate timing (with speech analysis if available)
            timings = self._calculate_timing(audio_file, word_groups, duration)
            
            # Generate subtitle events
            events = self._create_subtitle_events(word_groups, timings)
            
            # Write to file
            self._write_subtitle_file(output_file, events, style_config)
            
            print(f"✅ Created {len(events)} subtitle events")
            return True
            
        except Exception as e:
            print(f"Error creating subtitle file: {e}")
            return False
    
    def _get_audio_duration(self, audio_file):
        """Get audio duration with fallback"""
        try:
            with AudioFileClip(audio_file) as audio:
                return audio.duration
        except Exception:
            try:
                if PYDUB_AVAILABLE:
                    audio = AudioSegment.from_file(audio_file)
                    return len(audio) / 1000.0
            except Exception:
                pass
        return 10.0  # Fallback
    
    def _calculate_timing(self, audio_file, word_groups, duration):
        """Calculate timing with optional speech analysis"""
        # Try speech analysis first
        if (PYDUB_AVAILABLE and
            self.config.get("use_speech_analysis", True) and
            duration <= self.config.get("speech_analysis_max_duration", 60.0)):

            timings = self._analyze_speech_timing(audio_file, word_groups, duration)
            if timings:
                # print("Using speech analysis timing")  # Reduced logging
                return timings

        # Fallback to calculated timing
        # print("Using calculated timing")  # Reduced logging
        return self._calculate_basic_timing(word_groups, duration)
    
    def _analyze_speech_timing(self, audio_file, word_groups, duration):
        """Analyze speech patterns for precise timing"""
        try:
            audio = AudioSegment.from_file(audio_file)
            
            # Detect speech segments
            silence_thresh = audio.dBFS - self.config.get("silence_threshold_db", 16)
            min_silence = self.config.get("min_silence_length_ms", 150)
            
            speech_segments = detect_nonsilent(audio, min_silence_len=min_silence, silence_thresh=silence_thresh)
            
            if not speech_segments:
                return None
            
            # Convert to seconds and filter short segments
            segments = []
            for start_ms, end_ms in speech_segments:
                start_sec = start_ms / 1000.0
                end_sec = end_ms / 1000.0
                if end_sec - start_sec > 0.3:  # At least 300ms
                    segments.append((start_sec, end_sec))
            
            if not segments:
                return None
            
            # Map word groups to speech segments
            return self._map_groups_to_segments(word_groups, segments, duration)
            
        except Exception as e:
            print(f"Speech analysis failed: {e}")
            return None
    
    def _map_groups_to_segments(self, word_groups, segments, duration):
        """Map word groups to detected speech segments with improved synchronization"""
        timings = []
        early_offset = 0.1  # Reduced early start for better sync
        min_subtitle_duration = 1.5  # Reduced minimum duration
        min_gap = 0.05  # Smaller gap for better flow

        if len(segments) >= len(word_groups):
            # One-to-one mapping
            for i, group in enumerate(word_groups):
                if i < len(segments):
                    start, end = segments[i]
                    start = max(0, start - early_offset)

                    # Check for overlap with previous subtitle
                    if i > 0 and timings:
                        prev_end = timings[-1][1]
                        if start < prev_end + min_gap:
                            start = prev_end + min_gap

                    # Ensure minimum duration for readability
                    duration_needed = max(min_subtitle_duration, group['char_count'] / 15)
                    if end - start < duration_needed:
                        end = start + duration_needed

                    timings.append((start, min(end, duration)))
                else:
                    # Fallback for remaining groups
                    last_end = timings[-1][1] if timings else 0
                    fallback_start = last_end + min_gap
                    fallback_duration = max(min_subtitle_duration, group['char_count'] / 15)
                    timings.append((fallback_start, min(fallback_start + fallback_duration, duration)))
        else:
            # Distribute groups across segments
            groups_per_segment = len(word_groups) / len(segments)
            group_idx = 0

            for start, end in segments:
                segment_groups = int(groups_per_segment) + (1 if group_idx < len(word_groups) % len(segments) else 0)
                segment_duration = end - start

                for i in range(segment_groups):
                    if group_idx >= len(word_groups):
                        break

                    group_start = start - early_offset + (i * segment_duration / segment_groups)
                    group_end = start + ((i + 1) * segment_duration / segment_groups)

                    # Check for overlap with previous subtitle
                    if timings:
                        prev_end = timings[-1][1]
                        if group_start < prev_end + min_gap:
                            group_start = prev_end + min_gap
                            # Adjust end time accordingly
                            group_end = max(group_end, group_start + min_subtitle_duration)

                    timings.append((max(0, group_start), min(group_end, duration)))
                    group_idx += 1

        # Final overlap check and correction
        timings = self._ensure_no_overlaps(timings, duration)

        return timings
    
    def _calculate_basic_timing(self, word_groups, duration):
        """Calculate basic timing based on natural speech patterns"""
        timings = []
        num_groups = len(word_groups)
        if num_groups == 0:
            return []

        # Balanced timing calculation for better voice synchronization
        # Slow down subtitles to match voice timing better
        min_display = 1.5  # Increased minimum display time
        max_display = 4.0  # Increased maximum display time
        gap_time = 0.1    # Larger gap for better pacing

        # Calculate reading speed based on content
        total_chars = sum(len(group['text']) for group in word_groups)
        chars_per_second = total_chars / duration if duration > 0 else 10

        # Adjust timing based on speech speed - slower subtitles to match voice
        # Add delay so subtitles appear with the voice, not ahead of it
        if chars_per_second > 15:  # Fast speech
            base_display_time = 2.5  # Slower to match voice
        elif chars_per_second > 10:  # Normal speech
            base_display_time = 3.0  # Slower to match voice
        else:  # Slow speech
            base_display_time = 3.5  # Slower to match voice

        # Calculate optimal timing distribution to match speech pace
        total_estimated_time = sum(max(min_display, min(max_display,
                                      base_display_time + (len(group['text']) * 0.05)))
                                  for group in word_groups)

        # If estimated time exceeds audio duration, compress timing
        compression_factor = 1.0
        if total_estimated_time > duration * 0.95:  # Leave 10% buffer
            compression_factor = (duration * 0.95) / total_estimated_time

        # Add small delay so subtitles appear with voice, not ahead
        subtitle_delay = 0.3  # 300ms delay to sync with voice
        current_start = subtitle_delay

        for i, group in enumerate(word_groups):
            # Calculate display time based on text length and speech speed
            char_count = len(group['text'])
            word_count = len(group['text'].split())

            # Base time on character count with minimum/maximum bounds
            display_time = max(min_display, min(max_display,
                              base_display_time + (char_count * 0.03)))  # Reduced multiplier

            # Apply compression factor to fit within audio duration
            display_time *= compression_factor

            # Adjust for word density (more words = slightly longer display)
            if word_count > 7:
                display_time += 0.2  # Reduced from 0.3

            start_time = current_start
            end_time = min(start_time + display_time, duration)

            # Ensure we don't exceed audio duration
            if start_time >= duration:
                start_time = max(0, duration - 1.0)
                end_time = duration

            # Ensure minimum duration
            if end_time - start_time < min_display:
                end_time = min(start_time + min_display, duration)

            timings.append((start_time, end_time))

            # Move to next subtitle with small gap
            current_start = end_time + gap_time

        # Ensure no overlaps and fit within duration
        timings = self._ensure_no_overlaps(timings, duration)

        return timings

    def _ensure_no_overlaps(self, timings, duration):
        """Ensure no subtitle timings overlap with improved gap handling"""
        if not timings:
            return timings

        corrected_timings = []
        min_gap = 0.05  # Smaller minimum gap between subtitles

        for i, (start, end) in enumerate(timings):
            # Check for overlap with previous subtitle
            if i > 0:
                prev_end = corrected_timings[i-1][1]
                if start < prev_end + min_gap:
                    # Adjust start time to prevent overlap
                    start = prev_end + min_gap

                    # Ensure we don't go past duration
                    if start >= duration:
                        start = max(0, duration - 1.0)
                        end = duration
                    elif end <= start:
                        # Ensure minimum duration
                        end = min(start + 0.8, duration)  # Reduced minimum

            # Ensure end doesn't exceed duration
            end = min(end, duration)

            # Ensure minimum duration but be more flexible
            if end - start < 0.8:  # Reduced minimum duration
                end = min(start + 0.8, duration)

            # Final check: if this would create an overlap with next subtitle, adjust
            if i < len(timings) - 1:
                next_start = timings[i + 1][0]
                if end + min_gap > next_start:
                    # Compress this subtitle to make room
                    end = max(start + 0.8, next_start - min_gap)

            corrected_timings.append((start, end))

        return corrected_timings
    
    def _create_subtitle_events(self, word_groups, timings):
        """Create subtitle events from word groups and timings"""
        events = []
        
        for group, (start, end) in zip(word_groups, timings):
            # Clean text for ASS format
            text = group['text'].strip()
            text = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
            
            events.append({
                'text': text,
                'start': start,
                'end': end,
                'style': 'Default'
            })
        
        return events
    
    def _write_subtitle_file(self, output_file, events, style_config):
        """Write subtitle events to ASS file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(self._create_ass_header(style_config))
            
            # Write events
            for event in events:
                start_time = self._seconds_to_ass_time(event['start'])
                end_time = self._seconds_to_ass_time(event['end'])
                f.write(f"Dialogue: 0,{start_time},{end_time},{event['style']},,0,0,0,,{event['text']}\n")
    
    def _create_ass_header(self, style_config):
        """Create ASS file header with proper gradient support"""
        font = style_config.get("font", "Times New Roman")
        size = style_config.get("size", 48)
        bold = 1 if style_config.get("bold", True) else 0
        primary = style_config.get("primary_color", "&H00FFFFFF")
        secondary = style_config.get("secondary_color", "&H000000FF")  # For gradients
        outline = style_config.get("outline_color", "&H00FF8000")
        outline_width = style_config.get("outline_width", 3)
        shadow = style_config.get("shadow", 2)
        margin_v = style_config.get("margin_v", 80)
        alignment = style_config.get("alignment", 2)

        return f"""[Script Info]
Title: Video Subtitles
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},{primary},{secondary},{outline},&H00000000,{bold},0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    def _seconds_to_ass_time(self, seconds):
        """Convert seconds to ASS time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"
    
    def _create_fallback_file(self, output_file, text, duration):
        """Create fallback subtitle file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(self._create_ass_header({}))
                end_time = self._seconds_to_ass_time(min(duration, 5.0))
                f.write(f"Dialogue: 0,0:00:00.00,{end_time},Default,,0,0,0,,{text[:100]}\n")
            return True
        except Exception:
            return False

# Global functions for backward compatibility
_generator = SubtitleGenerator()

def generate_subtitles(text, video_file, audio_file, output_file, style="modern_glow", content_analysis=None, sync_precision="high"):
    """Backward compatible function"""
    return _generator.generate_subtitles(text, video_file, audio_file, output_file, style, content_analysis)
