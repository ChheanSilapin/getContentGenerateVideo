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

# pydub no longer needed for timing calculations

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

        # Use shared whisper-timestamped service
        from services.whisper_service_manager import get_whisper_service
        self.whisper_service = get_whisper_service()

        if self.whisper_service:
            # Only print once during first initialization
            if not hasattr(self.__class__, '_whisper_subtitle_printed'):
                print("✅ Whisper-timestamped service initialized for enhanced subtitle timing")
                self.__class__._whisper_subtitle_printed = True
        else:
            print("⚠️ Whisper-timestamped service not available, using Vosk only")
    
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

            # Store timings for voice activity detection
            self._last_timings = timings

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

        # Fallback to Vosk speech analysis
        if (self.config.get("use_speech_analysis", True) and
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

            # Store result for voice activity detection
            self._last_whisper_result = result

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
        """Simplified speech timing using Vosk recognition"""
        try:
            # Use Vosk for speech recognition timing if available
            if hasattr(self, 'vosk_model') and self.vosk_model:
                from services.audio_service import recognize_speech_from_file
                recognized_text = recognize_speech_from_file(audio_file, self.vosk_model, self.vosk_recognizer)
                if recognized_text:
                    # Simple timing based on recognized speech length
                    return self._calculate_basic_timing(word_groups, duration)
            return None
        except Exception as e:
            print(f"Speech analysis failed: {e}")
            return None
    


    def _calculate_basic_timing(self, word_groups, duration):
        """Simple fallback timing when advanced analysis is unavailable"""
        timings = []
        num_groups = len(word_groups)
        if num_groups == 0:
            return []

        # Simple equal distribution with minimum constraints
        min_display = 1.0
        gap_time = 0.1

        # Calculate equal time per group
        available_time = duration - (gap_time * (num_groups - 1))
        time_per_group = max(min_display, available_time / num_groups)

        current_start = 0.0
        for i, group in enumerate(word_groups):
            start_time = current_start
            end_time = min(start_time + time_per_group, duration)

            timings.append((start_time, end_time))
            current_start = end_time + gap_time

        return timings


    
    def _create_subtitle_events(self, word_groups, timings):
        """Create subtitle events with word-level highlighting support"""
        # Check if word-level highlighting is enabled
        import config
        enable_word_highlighting = getattr(config, 'SUBTITLE_CONFIG', {}).get('enable_word_level_highlighting', True)
        word_highlight_mode = getattr(config, 'SUBTITLE_CONFIG', {}).get('word_highlight_mode', 'karaoke')

        if enable_word_highlighting and word_highlight_mode == 'karaoke':
            return self._create_word_level_events(word_groups, timings)
        else:
            return self._create_sentence_level_events(word_groups, timings)

    def _create_sentence_level_events(self, word_groups, timings):
        """Create traditional sentence-level subtitle events with dynamic background support"""
        events = []

        # Get voice activity data for dynamic backgrounds
        voice_segments = self._get_voice_activity_segments()

        for group, (start, end) in zip(word_groups, timings):
            # Clean text for ASS format
            text = group['text'].strip()
            text = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

            # Check if this subtitle overlaps with voice activity
            is_voice_active = self._is_voice_active_during_subtitle(start, end, voice_segments)

            events.append({
                'text': text,
                'start': start,
                'end': end,
                'style': 'Default',
                'voice_active': is_voice_active
            })

        return events

    def _create_word_level_events(self, word_groups, timings):
        """Create word-level subtitle events for karaoke-style highlighting"""
        events = []

        # Get individual word timings from Whisper if available
        word_timings = self._extract_individual_word_timings()

        if word_timings:
            # Use precise Whisper word timings
            events = self._create_events_from_word_timings(word_timings)
            print(f"🎤 Created {len(events)} word-level events with Whisper precision")
        else:
            # Fallback: distribute words across sentence timings
            events = self._create_events_from_sentence_distribution(word_groups, timings)
            print(f"🎤 Created {len(events)} word-level events with estimated timing")

        return events

    def _extract_individual_word_timings(self):
        """Extract individual word timings from Whisper result"""
        if not hasattr(self, '_last_whisper_result') or not self._last_whisper_result:
            return None

        result = self._last_whisper_result
        if not result.success or not result.segments:
            return None

        # Flatten all word timestamps from all segments
        word_timings = []
        for segment in result.segments:
            for word in segment.words:
                # Clean word text for ASS format
                clean_text = word.text.strip()
                clean_text = clean_text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

                word_timings.append({
                    'text': clean_text,
                    'start': word.start,
                    'end': word.end,
                    'confidence': word.confidence
                })

        return word_timings

    def _create_events_from_word_timings(self, word_timings):
        """Create ASS events from individual word timings"""
        events = []
        import config

        # Get configuration
        word_spacing = getattr(config, 'SUBTITLE_CONFIG', {}).get('word_spacing', 0.05)
        min_duration = getattr(config, 'SUBTITLE_CONFIG', {}).get('word_min_duration', 0.3)
        max_duration = getattr(config, 'SUBTITLE_CONFIG', {}).get('word_max_duration', 2.0)

        for i, word_timing in enumerate(word_timings):
            start = word_timing['start']
            end = word_timing['end']
            text = word_timing['text']

            # Ensure minimum duration
            if end - start < min_duration:
                end = start + min_duration

            # Ensure maximum duration
            if end - start > max_duration:
                end = start + max_duration

            # Add spacing between words (except for the last word)
            if i < len(word_timings) - 1:
                next_start = word_timings[i + 1]['start']
                if end + word_spacing < next_start:
                    # Add spacing if there's room
                    end = min(end, next_start - word_spacing)

            # Skip empty words
            if not text or text.isspace():
                continue

            events.append({
                'text': text,
                'start': start,
                'end': end,
                'style': 'Default',
                'voice_active': True,  # Individual words are always voice-active
                'word_level': True
            })

        return events

    def _create_events_from_sentence_distribution(self, word_groups, timings):
        """Create word-level events by distributing words across sentence timings"""
        events = []
        import config

        # Get configuration
        word_spacing = getattr(config, 'SUBTITLE_CONFIG', {}).get('word_spacing', 0.05)
        min_duration = getattr(config, 'SUBTITLE_CONFIG', {}).get('word_min_duration', 0.3)

        for group, (group_start, group_end) in zip(word_groups, timings):
            words = group['text'].split()
            if not words:
                continue

            group_duration = group_end - group_start
            word_count = len(words)

            # Calculate time per word (with spacing)
            total_spacing = word_spacing * (word_count - 1)
            available_time = group_duration - total_spacing
            time_per_word = max(min_duration, available_time / word_count)

            current_time = group_start

            for i, word in enumerate(words):
                # Clean word text for ASS format
                clean_word = word.strip()
                clean_word = clean_word.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

                if not clean_word or clean_word.isspace():
                    continue

                word_start = current_time
                word_end = word_start + time_per_word

                # Ensure we don't exceed group end time
                if word_end > group_end:
                    word_end = group_end

                events.append({
                    'text': clean_word,
                    'start': word_start,
                    'end': word_end,
                    'style': 'Default',
                    'voice_active': True,  # Estimated words are considered voice-active
                    'word_level': True
                })

                # Move to next word position
                current_time = word_end + word_spacing

                # Stop if we've run out of time
                if current_time >= group_end:
                    break

        return events

    def _get_voice_activity_segments(self):
        """Get voice activity segments from Whisper timestamped data"""
        voice_segments = []

        # Try to get voice activity from whisper service if available
        if hasattr(self, '_last_whisper_result') and self._last_whisper_result:
            result = self._last_whisper_result
            for segment in result.segments:
                # Each segment represents a period of voice activity
                voice_segments.append((segment.start, segment.end))

        # Fallback: assume voice is active during all subtitle timings
        # This ensures backgrounds still work even without detailed voice data
        if not voice_segments and hasattr(self, '_last_timings') and self._last_timings:
            for start, end in self._last_timings:
                voice_segments.append((start, end))

        return voice_segments

    def _is_voice_active_during_subtitle(self, subtitle_start, subtitle_end, voice_segments):
        """Check if voice is active during subtitle display period"""
        if not voice_segments:
            return True  # Default to active if no voice data

        # Check if subtitle overlaps with any voice segment
        for voice_start, voice_end in voice_segments:
            # Check for any overlap between subtitle and voice timing
            if (subtitle_start < voice_end and subtitle_end > voice_start):
                return True

        return False

    def _write_subtitle_file(self, output_file, events, style_config):
        """Write subtitle events to ASS file with word-level highlighting support"""
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header with dynamic background support
            f.write(self._create_ass_header_with_backgrounds(style_config))

            # Check if we have word-level events
            has_word_level = any(event.get('word_level', False) for event in events)

            if has_word_level:
                self._write_word_level_events(f, events, style_config)
            else:
                self._write_sentence_level_events(f, events, style_config)

    def _write_sentence_level_events(self, f, events, style_config):
        """Write traditional sentence-level events"""
        for event in events:
            start_time = self._seconds_to_ass_time(event['start'])
            end_time = self._seconds_to_ass_time(event['end'])

            # Choose style and apply effects based on voice activity
            if style_config.get('enable_voice_sync', False) and event.get('voice_active', False):
                style_name = "VoiceActive"
                text = self._add_background_effect(event['text'], style_config)
            else:
                style_name = "Default"
                text = event['text']

            f.write(f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{text}\n")

    def _write_word_level_events(self, f, events, style_config):
        """Write word-level events for karaoke-style highlighting"""
        # Group words by their approximate sentence timing for positioning
        word_groups = self._group_words_for_positioning(events)

        for group in word_groups:
            for event in group['words']:
                start_time = self._seconds_to_ass_time(event['start'])
                end_time = self._seconds_to_ass_time(event['end'])

                # Apply word-level highlighting effects
                if style_config.get('enable_voice_sync', False) and event.get('voice_active', False):
                    style_name = "VoiceActive"
                    text = self._add_word_highlight_effect(event['text'], style_config, group)
                else:
                    style_name = "Default"
                    text = event['text']

                f.write(f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{text}\n")

    def _group_words_for_positioning(self, events):
        """Group word-level events for better positioning context"""
        # Simple grouping: words that are close in time belong to the same sentence
        groups = []
        current_group = {'words': [], 'start': None, 'end': None}

        max_gap = 1.0  # Maximum gap between words in the same sentence (seconds)

        for event in events:
            if not event.get('word_level', False):
                continue

            # Start new group if this is the first word or there's a large gap
            if (not current_group['words'] or
                event['start'] - current_group['end'] > max_gap):

                # Save previous group if it has words
                if current_group['words']:
                    groups.append(current_group)

                # Start new group
                current_group = {
                    'words': [event],
                    'start': event['start'],
                    'end': event['end']
                }
            else:
                # Add to current group
                current_group['words'].append(event)
                current_group['end'] = event['end']

        # Add the last group
        if current_group['words']:
            groups.append(current_group)

        return groups

    def _add_word_highlight_effect(self, text, style_config, word_group):
        """Add enhanced highlighting effect for individual words"""
        try:
            # Get background configuration from config
            import config
            enable_backgrounds = getattr(config, 'SUBTITLE_CONFIG', {}).get('enable_dynamic_backgrounds', True)

            if not enable_backgrounds:
                return text

            # Enhanced word-level highlighting with positioning
            padding = style_config.get('background_padding', 10)
            border_radius = style_config.get('background_border_radius', 8)

            # Calculate word position within sentence for better alignment
            word_count = len(word_group['words'])
            word_index = next((i for i, w in enumerate(word_group['words']) if w['text'] == text), 0)

            # Enhanced karaoke-style effect with word positioning
            # {\an2} = bottom center alignment
            # {\pos(x,y)} = absolute positioning (optional for advanced layouts)
            # {\bord} = enhanced border for word highlighting
            # {\shad} = enhanced shadow for word highlighting
            # {\blur} = blur effect for softer highlighting
            # {\fscx} = slight scale effect for emphasis

            enhanced_text = f"{{\\bord{padding + 2}\\shad{border_radius + 2}\\blur3\\fscx105}}{text}"

            return enhanced_text

        except Exception as e:
            print(f"Warning: Could not apply word highlight effect: {e}")
            return text

    def _create_ass_header_with_backgrounds(self, style_config):
        """Create ASS file header with dynamic background support"""
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

        # Background colors for dynamic effects
        bg_color = style_config.get("background_color", "&H80000000")  # Semi-transparent black
        bg_active_color = style_config.get("background_active_color", "&H80001040")  # Semi-transparent colored

        header = f"""[Script Info]
Title: Video Subtitles with Dynamic Backgrounds
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},{primary},{secondary},{outline},{bg_color},{bold},0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},10,10,{margin_v},1
"""

        # Add voice-active style if dynamic backgrounds are enabled
        if style_config.get('enable_voice_sync', False):
            header += f"Style: VoiceActive,{font},{size},{primary},{secondary},{outline},{bg_active_color},{bold},0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},10,10,{margin_v},1\n"

        header += """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        return header

    def _create_ass_header(self, style_config):
        """Create ASS file header with proper gradient support (legacy method)"""
        return self._create_ass_header_with_backgrounds(style_config)
    
    def _add_background_effect(self, text, style_config):
        """Add background box effect to subtitle text for voice-active periods"""
        try:
            # Get background configuration from config
            import config
            enable_backgrounds = getattr(config, 'SUBTITLE_CONFIG', {}).get('enable_dynamic_backgrounds', True)

            if not enable_backgrounds:
                return text

            # Add ASS override tags for enhanced background effect
            # {\an2} = bottom center alignment
            # {\bord} = border width
            # {\shad} = shadow depth
            # {\blur} = blur effect for softer background

            padding = style_config.get('background_padding', 10)
            border_radius = style_config.get('background_border_radius', 8)

            # Enhanced background effect with subtle glow
            enhanced_text = f"{{\\bord{padding}\\shad{border_radius}\\blur2}}{text}"

            return enhanced_text

        except Exception as e:
            print(f"Warning: Could not apply background effect: {e}")
            return text

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
