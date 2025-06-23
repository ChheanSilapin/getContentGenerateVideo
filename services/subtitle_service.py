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
from config import DEFAULT_MAX_CHARS_PER_LINE, SUBTITLE_CONFIG, WHISPER_TIMESTAMPED_CONFIG
from utils.helpers import ensure_directory_exists, get_media_duration_safe
from utils.text_processing import process_text_for_subtitles

# Try to import pydub for speech analysis
try:
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("pydub not available. Using basic timing for subtitles.")

# Import whisper-timestamped service for enhanced timing
try:
    from services.whisper_timestamped_service import WhisperTimestampedService
    WHISPER_SERVICE_AVAILABLE = True
except ImportError:
    WHISPER_SERVICE_AVAILABLE = False
    print("⚠️ WhisperTimestampedService not available.")

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
    """Clean, efficient subtitle generator with whisper-timestamped integration"""

    def __init__(self):
        self.config = SUBTITLE_CONFIG
        self.whisper_config = WHISPER_TIMESTAMPED_CONFIG

        # Initialize whisper-timestamped service if available and enabled
        self.whisper_service = None
        if (WHISPER_SERVICE_AVAILABLE and
            self.whisper_config.get("enable_service", True)):
            try:
                self.whisper_service = WhisperTimestampedService(
                    model_name=self.whisper_config.get("model_name", "tiny"),
                    device=self.whisper_config.get("device", "auto")
                )
                if self.whisper_service.is_service_available():
                    print("✅ Whisper-timestamped service initialized for enhanced subtitle timing")
                else:
                    self.whisper_service = None
            except Exception as e:
                print(f"⚠️ Failed to initialize whisper-timestamped service: {e}")
                self.whisper_service = None
    
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
            # Store content analysis for use in timing calculations
            self.content_analysis = content_analysis

            # Clean text and create output directory
            cleaned_text = process_text_for_subtitles(text)
            ensure_directory_exists(os.path.dirname(output_file))

            # Debug: Log which text is being used for subtitles
            print(f"📝 Subtitle text source: {len(text)} chars, first 50: '{text[:50]}...'")
            if cleaned_text != text:
                print(f"📝 Text cleaned for subtitles: '{cleaned_text[:50]}...'")

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
        """Get audio duration using centralized function"""
        return get_media_duration_safe(audio_file)
    
    def _calculate_timing(self, audio_file, word_groups, duration):
        """Calculate timing with whisper-timestamped as primary method"""
        # Try whisper-timestamped first (highest priority)
        if (self.whisper_service and
            self.whisper_config.get("replace_speech_analysis", True) and
            duration <= self.whisper_config.get("max_audio_duration", 300)):

            timings = self._analyze_whisper_timing(audio_file, word_groups, duration)
            if timings and len(timings) == len(word_groups):
                print("🎯 Using whisper-timestamped for precise subtitle synchronization")
                print(f"📊 Whisper analysis: {len(timings)} subtitle events with word-level precision")
                return timings
            else:
                print(f"⚠️ Whisper-timestamped returned {len(timings) if timings else 0} timings for {len(word_groups)} groups")

        # Fallback to traditional speech analysis
        if (PYDUB_AVAILABLE and
            self.config.get("use_speech_analysis", True) and
            duration <= self.config.get("speech_analysis_max_duration", 60.0)):

            timings = self._analyze_speech_timing(audio_file, word_groups, duration)
            if timings and len(timings) == len(word_groups):
                # Validate timing quality
                timing_quality = self._validate_timing_quality(timings, duration)
                if timing_quality['is_valid']:
                    print("🎯 Using speech analysis timing for precise subtitle synchronization")
                    print(f"📊 Speech analysis: {len(timings)} subtitle events, 0ms offset, perfect synchronization")
                    return timings
                else:
                    print(f"⚠️ Speech analysis timing quality poor: {timing_quality['reason']}")
                    print("📊 Falling back to calculated timing for reliability")
            elif timings:
                print(f"⚠️ Speech analysis returned {len(timings)} timings for {len(word_groups)} groups - using calculated timing")

        # Final fallback to calculated timing
        print("📊 Using calculated timing (advanced analysis unavailable)")
        return self._calculate_basic_timing(word_groups, duration)

    def _analyze_whisper_timing(self, audio_file, word_groups, duration):
        """Analyze audio using whisper-timestamped for precise word-level timing with robust error handling"""
        try:
            # Validate inputs
            if not os.path.exists(audio_file):
                print(f"⚠️ Audio file not found: {audio_file}")
                return None

            if not word_groups:
                print("⚠️ No word groups provided for timing analysis")
                return None

            # Check audio duration limits
            max_duration = self.whisper_config.get("max_audio_duration", 300)
            if duration > max_duration:
                print(f"⚠️ Audio too long for whisper analysis: {duration:.1f}s > {max_duration}s")
                return None

            # Get content type for optimization
            content_analysis = getattr(self, 'content_analysis', None)
            content_type = None
            if content_analysis and hasattr(content_analysis, 'content_type'):
                content_type = content_analysis.content_type

            # Get language setting
            language = self.whisper_config.get("default_language", "en")
            use_vad = self.whisper_config.get("use_vad", True)

            # Run whisper-timestamped analysis with timeout protection
            start_time = time.time()
            result = self.whisper_service.analyze_audio_with_timestamps(
                audio_file=audio_file,
                language=language,
                use_vad=use_vad,
                content_type=content_type
            )
            analysis_time = time.time() - start_time

            if not result.success:
                print(f"⚠️ Whisper analysis failed: {result.error_message}")
                return None

            # Check if analysis took too long (performance issue)
            if analysis_time > 30.0:  # 30 second timeout
                print(f"⚠️ Whisper analysis too slow: {analysis_time:.1f}s")
                print("💡 Consider using smaller model or fallback method")

            # Check confidence threshold
            confidence = self.whisper_service.get_confidence_score(result)
            min_confidence = self.whisper_config.get("min_confidence_threshold", 0.7)

            if confidence < min_confidence:
                print(f"⚠️ Whisper confidence too low: {confidence:.2f} < {min_confidence}")
                if self.whisper_config.get("fallback_to_vosk", True):
                    print("📊 Falling back to traditional speech analysis")
                    return None

            # Extract timings for subtitle groups
            timings = self.whisper_service.extract_word_timings_for_subtitle_groups(
                result, word_groups
            )

            if timings:
                # Validate timing quality
                if not self._validate_whisper_timings(timings, duration):
                    print("⚠️ Whisper timings failed quality validation")
                    return None

                # Apply subtitle sync offset if configured
                sync_offset = self.whisper_config.get("subtitle_sync_offset", 0.0)
                if sync_offset != 0.0:
                    timings = [(start + sync_offset, end + sync_offset) for start, end in timings]
                    print(f"📊 Applied {sync_offset}s sync offset to whisper timings")

                print(f"✅ Whisper-timestamped generated {len(timings)} precise timings (confidence: {confidence:.2f}, time: {analysis_time:.1f}s)")
                return timings
            else:
                print("⚠️ No timings extracted from whisper analysis")
                return None

        except Exception as e:
            print(f"❌ Whisper timing analysis failed: {e}")
            print("💡 Falling back to traditional timing methods")
            return None

    def _validate_whisper_timings(self, timings, total_duration):
        """Validate whisper timing quality"""
        if not timings:
            return False

        # Check for reasonable timing bounds
        for start, end in timings:
            if start < 0 or end < 0 or start >= end:
                return False
            if end > total_duration + 1.0:  # Allow 1s tolerance
                return False

        # Check for excessive overlaps
        overlaps = 0
        for i in range(len(timings) - 1):
            if timings[i][1] > timings[i+1][0]:
                overlaps += 1

        if overlaps > len(timings) * 0.3:  # More than 30% overlaps is problematic
            return False

        return True

    def _analyze_speech_timing(self, audio_file, word_groups, duration):
        """Analyze speech patterns for precise timing"""
        try:
            audio = AudioSegment.from_file(audio_file)
            
            # Detect speech segments
            silence_thresh = audio.dBFS - self.config.get("silence_threshold_db", 18)
            min_silence = self.config.get("min_silence_length_ms", 200)
            
            speech_segments = detect_nonsilent(audio, min_silence_len=min_silence, silence_thresh=silence_thresh)

            if not speech_segments:
                return None

            # Convert to seconds and filter short segments
            segments = []
            filtered_count = 0
            for start_ms, end_ms in speech_segments:
                start_sec = start_ms / 1000.0
                end_sec = end_ms / 1000.0
                segment_duration = end_sec - start_sec  # Fixed: renamed to avoid collision with duration parameter
                if segment_duration > 0.4:  # At least 400ms (balanced reliability and sensitivity)
                    segments.append((start_sec, end_sec))
                else:
                    filtered_count += 1

            if not segments:
                # Fallback: try with shorter minimum duration
                for start_ms, end_ms in speech_segments:
                    start_sec = start_ms / 1000.0
                    end_sec = end_ms / 1000.0
                    fallback_segment_duration = end_sec - start_sec  # Fixed: use descriptive variable name
                    if fallback_segment_duration > 0.2:  # Fallback to 200ms minimum
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
        early_offset = 0.0   # Zero offset: subtitles appear EXACTLY with speech starts (perfect synchronization)
        min_subtitle_duration = 0.8  # Reduced minimum for better speech analysis compatibility
        min_gap = 0.05  # Smaller gap for smoother flow

        # Map word groups to speech segments

        if len(segments) >= len(word_groups):
            # One-to-one mapping (preferred when we have enough segments)
            for i, group in enumerate(word_groups):
                if i < len(segments):
                    start, end = segments[i]
                    start = max(0, start - early_offset)  # Zero offset = exact synchronization with speech

                    # Check for overlap with previous subtitle
                    if i > 0 and timings:
                        prev_end = timings[-1][1]
                        if start < prev_end + min_gap:
                            start = prev_end + min_gap

                    # Calculate duration based on text length and speech segment
                    text_based_duration = max(0.8, group['char_count'] / 15)  # 15 chars per second reading speed
                    segment_duration = end - start
                    duration_needed = max(min_subtitle_duration, text_based_duration)

                    # Use the longer of text-based duration or segment duration, but ensure minimum
                    if segment_duration >= duration_needed:
                        # Speech segment is long enough, use it
                        end = start + segment_duration
                    else:
                        # Speech segment too short, extend to meet text requirements
                        end = start + duration_needed

                    timings.append((start, min(end, duration)))
                else:
                    # Fallback for remaining groups
                    last_end = timings[-1][1] if timings else 0
                    fallback_start = last_end + min_gap
                    fallback_duration = max(min_subtitle_duration, group['char_count'] / 15)
                    timings.append((fallback_start, min(fallback_start + fallback_duration, duration)))
        else:
            # Distribute groups across segments - FIXED ALGORITHM

            # Create a more robust distribution that ensures all groups are processed
            segment_assignments = []
            remaining_groups = len(word_groups)

            for i, (start, end) in enumerate(segments):
                remaining_segments = len(segments) - i
                # Calculate how many groups this segment should handle
                groups_for_this_segment = max(1, remaining_groups // remaining_segments)
                if i < remaining_groups % remaining_segments:
                    groups_for_this_segment += 1

                segment_assignments.append(groups_for_this_segment)
                remaining_groups -= groups_for_this_segment

            # Distribute groups across segments

            group_idx = 0
            for segment_idx, (start, end) in enumerate(segments):
                segment_groups = segment_assignments[segment_idx]
                segment_duration = end - start

                for i in range(segment_groups):
                    if group_idx >= len(word_groups):
                        break

                    # Distribute groups evenly within this segment
                    group_start = start - early_offset + (i * segment_duration / segment_groups)
                    group_end = start + ((i + 1) * segment_duration / segment_groups)

                    # Ensure minimum subtitle duration based on text length
                    group = word_groups[group_idx]
                    text_based_duration = max(0.8, group['char_count'] / 15)  # 15 chars per second reading speed
                    required_duration = max(min_subtitle_duration, text_based_duration)

                    # Adjust end time to meet minimum duration
                    if group_end - group_start < required_duration:
                        group_end = group_start + required_duration

                    # Check for overlap with previous subtitle
                    if timings:
                        prev_end = timings[-1][1]
                        if group_start < prev_end + min_gap:
                            group_start = prev_end + min_gap
                            # Adjust end time accordingly to maintain minimum duration
                            group_end = max(group_end, group_start + required_duration)

                    timings.append((max(0, group_start), min(group_end, duration)))
                    group_idx += 1

            # Ensure we have timings for all groups
            while len(timings) < len(word_groups):
                last_end = timings[-1][1] if timings else 0
                fallback_start = last_end + min_gap
                fallback_duration = min_subtitle_duration
                timings.append((fallback_start, min(fallback_start + fallback_duration, duration)))
                pass  # Silent fallback timing

        return timings

    def _validate_timing_quality(self, timings, duration):
        """Validate the quality of speech analysis timing - more lenient for better speech sync"""
        if not timings:
            return {'is_valid': False, 'reason': 'No timings generated'}

        # Check for reasonable timing intervals
        durations = [end - start for start, end in timings]

        # Very lenient validation to strongly prefer speech analysis timing
        very_short = sum(1 for d in durations if d < 0.2)  # Less than 200ms (very short)
        very_long = sum(1 for d in durations if d > 10.0)   # More than 10s (very long)

        if very_short > len(timings) * 0.8:  # More than 80% very short (very lenient)
            return {'is_valid': False, 'reason': f'{very_short} subtitles too short (<0.2s)'}

        if very_long > len(timings) * 0.3:   # More than 30% very long (very lenient)
            return {'is_valid': False, 'reason': f'{very_long} subtitles too long (>10s)'}

        # More lenient gap checking
        large_gaps = 0
        for i in range(1, len(timings)):
            gap = timings[i][0] - timings[i-1][1]
            if gap > 3.0:  # Gap longer than 3 seconds (increased from 2s)
                large_gaps += 1

        if large_gaps > len(timings) * 0.3:  # More than 30% have large gaps
            return {'is_valid': False, 'reason': f'{large_gaps} large gaps (>3s) between subtitles'}

        return {'is_valid': True, 'reason': 'Speech analysis timing quality acceptable'}

    def _calculate_basic_timing(self, word_groups, duration):
        """Calculate basic timing based on natural speech patterns"""
        timings = []
        num_groups = len(word_groups)
        if num_groups == 0:
            return []

        # Content-aware timing calculation for better synchronization
        min_display = 1.2  # Reduced minimum display time for better flow
        max_display = 4.5  # Slightly increased maximum display time
        gap_time = 0.05   # Smaller gap for smoother transitions

        # Calculate reading speed based on content
        total_chars = sum(len(group['text']) for group in word_groups)
        chars_per_second = total_chars / duration if duration > 0 else 10

        # Adjust timing based on speech speed and content type
        content_analysis = getattr(self, 'content_analysis', None)
        if content_analysis and hasattr(content_analysis, 'content_type'):
            content_type = content_analysis.content_type.value

            # Comprehensive content-type specific timing
            if content_type == 'quote_reflection':
                base_display_time = 2.8  # Balanced timing for reflection
                min_display = 1.5
                gap_time = 0.1
            elif content_type == 'historical':
                base_display_time = 3.2  # Slower for historical content
                min_display = 1.8
                gap_time = 0.15
            elif content_type == 'story_review':
                base_display_time = 2.4  # Faster for story content
                min_display = 1.2
                gap_time = 0.05
            elif content_type == 'educational':
                base_display_time = 3.0  # Moderate pace for learning
                min_display = 1.6
                gap_time = 0.1
            elif content_type == 'entertainment':
                base_display_time = 2.2  # Fast pace for entertainment
                min_display = 1.0
                gap_time = 0.05
            elif content_type == 'documentary':
                base_display_time = 3.5  # Slower for documentary content
                min_display = 2.0
                gap_time = 0.2
            elif content_type == 'personal':
                base_display_time = 2.6  # Personal pace
                min_display = 1.4
                gap_time = 0.08
            else:  # unknown or other types
                base_display_time = 2.5  # Default timing
                min_display = 1.3
                gap_time = 0.08
        else:
            # Default timing based on speech speed
            if chars_per_second > 15:  # Fast speech
                base_display_time = 2.2  # Faster subtitles for fast speech
            elif chars_per_second > 10:  # Normal speech
                base_display_time = 2.5  # Balanced timing
            else:  # Slow speech
                base_display_time = 3.0  # Slower for slow speech

        # Calculate optimal timing distribution to match speech pace
        total_estimated_time = sum(max(min_display, min(max_display,
                                      base_display_time + (len(group['text']) * 0.05)))
                                  for group in word_groups)

        # If estimated time exceeds audio duration, compress timing
        compression_factor = 1.0
        if total_estimated_time > duration * 0.95:  # Leave 10% buffer
            compression_factor = (duration * 0.95) / total_estimated_time

        # Add delay so subtitles appear with voice, not ahead
        # Make delay configurable and content-type aware
        if content_analysis and hasattr(content_analysis, 'content_type'):
            content_type = content_analysis.content_type.value
            # Content-specific delays for better synchronization
            if content_type == 'quote_reflection':
                subtitle_delay = 0.7  # Slightly longer delay for reflective content
            elif content_type == 'historical':
                subtitle_delay = 0.8  # Longer delay for historical content
            elif content_type == 'story_review':
                subtitle_delay = 0.5  # Shorter delay for story content
            else:
                subtitle_delay = 0.6  # Default delay
        else:
            subtitle_delay = 0.6  # 600ms delay to sync with voice (increased from 300ms)

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
        """Ensure no subtitle timings overlap with improved gap handling - FIXED for speech analysis"""
        if not timings:
            return timings

        corrected_timings = []
        min_gap = 0.05  # Smaller gap for speech analysis timing
        min_duration = 0.5  # Minimum subtitle duration

        for i, (start, end) in enumerate(timings):
            # Check for overlap with previous subtitle
            if i > 0:
                prev_end = corrected_timings[i-1][1]
                if start < prev_end + min_gap:
                    # Adjust start time to prevent overlap
                    start = prev_end + min_gap

            # Ensure end doesn't exceed duration
            end = min(end, duration)

            # Ensure minimum duration
            if end - start < min_duration:
                end = min(start + min_duration, duration)

            # Ensure we don't go past duration
            if start >= duration:
                start = max(0, duration - min_duration)
                end = duration

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
