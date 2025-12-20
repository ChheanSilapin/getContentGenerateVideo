"""
Viral Subtitle Service - Simplified Implementation
Based on process_video.py create_ass_file function

APPROACH:
- Viral-style subtitles with random word highlighting
- Direct Whisper chunks (2-3 words per line)
- UPPERCASE text for impact
- Random color highlighting for one word per line
"""
import os
import random
from typing import Dict, List

# Import centralized config
from config import SUBTITLE_CONFIG
from utils.helpers import ensure_directory_exists


# Viral Colors Palette (BGR format for ASS: &HBBGGRR)
VIRAL_COLORS = [
    "&H0000FFFF",  # Yellow
    "&H0000FF00",  # Green
    "&H00FFFF00",  # Cyan
    "&H00FF00FF",  # Pink
    "&H000080FF",  # Orange
]
WHITE_COLOR = "&H00FFFFFF"


def format_time_ass(seconds: float) -> str:
    """Format time for ASS subtitles (h:mm:ss.cc)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


class ViralSubtitleGenerator:
    """Viral-style subtitle generator with random word highlighting"""

    def __init__(self):
        self.config = SUBTITLE_CONFIG
        self.colors = VIRAL_COLORS
        self.white = WHITE_COLOR

    def generate_subtitles(self, text: str, audio_timing_result, output_file: str, style: str = "modern_glow") -> bool:
        """
        Generate viral-style subtitles with random word highlighting
        
        Args:
            text: Original text (not used in viral mode - we use Whisper directly)
            audio_timing_result: AudioTimingResult with Whisper timing data
            output_file: Output subtitle file path
            style: Subtitle style (used for font settings)
            
        Returns:
            bool: Success status
        """
        try:
            # Validate inputs
            if not audio_timing_result or not audio_timing_result.success:
                print("[VIRAL SUBTITLE] Invalid input parameters")
                return False

            # Create output directory
            ensure_directory_exists(os.path.dirname(output_file))

            # Extract Whisper timing data
            timing_data = audio_timing_result.timing_data
            if not timing_data or not timing_data.get('whisper_segments'):
                print("[VIRAL SUBTITLE] No Whisper timing data available")
                return False

            whisper_segments = timing_data['whisper_segments']
            print(f"[VIRAL SUBTITLE] Processing {len(whisper_segments)} Whisper segments")

            # Extract all words with timing (direct from Whisper)
            all_words = self._extract_words_from_segments(whisper_segments)
            
            if not all_words:
                print("[VIRAL SUBTITLE] No word-level timing data available")
                return False

            print(f"[VIRAL SUBTITLE] Extracted {len(all_words)} word timings")

            # Chunk words into groups of 2-3 for viral style
            chunks = self._create_viral_chunks(all_words)
            print(f"[VIRAL SUBTITLE] Created {len(chunks)} subtitle chunks")

            # Write ASS file with viral styling
            self._write_viral_ass_file(output_file, chunks, style)

            print(f"[VIRAL SUBTITLE] Successfully generated {len(chunks)} subtitle lines")
            return True

        except Exception as e:
            print(f"[VIRAL SUBTITLE] Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _extract_words_from_segments(self, segments: List[Dict]) -> List[Dict]:
        """Extract all words with timing from Whisper segments"""
        all_words = []
        
        for seg in segments:
            if seg.get('words') and isinstance(seg['words'], list):
                for word_data in seg['words']:
                    if isinstance(word_data, dict):
                        # Handle both formats: direct Whisper ('text') and audio service ('word')
                        word_text = word_data.get('text') or word_data.get('word', '')
                        if word_text and word_text.strip():
                            all_words.append({
                                'word': word_text.strip(),
                                'start': float(word_data.get('start', 0.0)),
                                'end': float(word_data.get('end', 0.0))
                            })
            else:
                # Fallback: split segment text and distribute timing evenly
                text_words = seg.get('text', '').strip().split()
                if not text_words:
                    continue
                    
                duration = seg.get('end', 0) - seg.get('start', 0)
                if duration <= 0:
                    continue
                    
                word_duration = duration / len(text_words)
                for i, w in enumerate(text_words):
                    all_words.append({
                        'word': w,
                        'start': seg['start'] + i * word_duration,
                        'end': seg['start'] + (i + 1) * word_duration
                    })
        
        return all_words

    def _create_viral_chunks(self, words: List[Dict]) -> List[Dict]:
        """Chunk words into groups of 2-3 for viral-style subtitles"""
        chunks = []
        i = 0
        
        while i < len(words):
            # Randomly choose chunk size 2 or 3
            chunk_size = random.randint(2, 3)
            chunk = words[i:i + chunk_size]
            
            if chunk:
                chunks.append({
                    'words': chunk,
                    'start': chunk[0]['start'],
                    'end': chunk[-1]['end']
                })
            i += chunk_size
        
        return chunks

    def _apply_viral_highlighting(self, words: List[Dict]) -> str:
        """Apply random color highlighting to one word per chunk"""
        if not words:
            return ""
        
        # Pick exactly one word index to highlight
        highlight_idx = random.randint(0, len(words) - 1)
        
        text_parts = []
        for idx, word_info in enumerate(words):
            word_text = word_info['word'].strip().upper()  # UPPERCASE for viral style
            
            if idx == highlight_idx:
                color = random.choice(self.colors)
                text_parts.append(f"{{\\1c{color}&}}{word_text}")
            else:
                text_parts.append(f"{{\\1c{self.white}&}}{word_text}")
        
        return ' '.join(text_parts)

    def _write_viral_ass_file(self, output_file: str, chunks: List[Dict], style: str):
        """Write viral-style ASS subtitle file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            # Script Info - optimized for 9:16 vertical video
            f.write("[Script Info]\n")
            f.write("Title: Viral Subtitles\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 1080\n")
            f.write("PlayResY: 1920\n")
            f.write("\n")
            
            # Styles - viral style with large font
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            
            # Get font from config or use Poppins as default for viral style
            style_config = self.config.get('available_styles', {}).get(style, {})
            font = style_config.get('font', 'Poppins')
            
            # Viral style: Large font, bold, black outline, bottom center
            f.write(f"Style: Default,{font},80,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,1,2,0,2,10,10,600,1\n")
            f.write("\n")
            
            # Events
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            for chunk in chunks:
                start_str = format_time_ass(chunk['start'])
                end_str = format_time_ass(chunk['end'])
                
                # Apply viral highlighting (random colored word)
                text_content = self._apply_viral_highlighting(chunk['words'])
                
                f.write(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_content}\n")
        
        print(f"[VIRAL SUBTITLE] Wrote {len(chunks)} dialogue lines to {output_file}")


# Global instance
_viral_generator = ViralSubtitleGenerator()


def generate_subtitles_with_timing_sync(text: str, audio_timing_result, output_file: str, style: str = "modern_glow") -> bool:
    """Generate viral-style subtitles (main function)"""
    return _viral_generator.generate_subtitles(text, audio_timing_result, output_file, style)


def generate_subtitles(text: str, audio_timing_result, output_file: str, style: str = "modern_glow") -> bool:
    """Legacy function name for backward compatibility"""
    return _viral_generator.generate_subtitles(text, audio_timing_result, output_file, style)
