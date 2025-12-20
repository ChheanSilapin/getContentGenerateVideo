
import os
import sys
import logging
import static_ffmpeg
static_ffmpeg.add_paths()
import ffmpeg
import torch
import omegaconf

import collections
import typing
import pyannote.audio.core.model

import pyannote.audio.core.task

# Fix for PyTorch 2.6+ security change preventing model loading
# We add omegaconf classes to safe globals
torch.serialization.add_safe_globals([
    omegaconf.listconfig.ListConfig,
    omegaconf.dictconfig.DictConfig,
    omegaconf.base.ContainerMetadata,
    omegaconf.base.Metadata,
    omegaconf.nodes.AnyNode,
    typing.Any,
    list,
    dict,
    collections.defaultdict,
    set,
    int,
    float,
    str,
    torch.torch_version.TorchVersion,
    pyannote.audio.core.model.Introspection,
    pyannote.audio.core.task.Specifications,
    pyannote.audio.core.task.Problem,
    pyannote.audio.core.task.Resolution
])

# Also monkey-patch torch.load as a fallback for other potential issues in dependencies
original_load = torch.load
def safe_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return original_load(*args, **kwargs)
torch.load = safe_load



# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_time_ass(seconds):
    """Format time for ASS subtitles (h:mm:ss.cc)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

import random

def create_ass_file(segments, filename="captions.ass"):
    """Create an ASS subtitle file with short segments and single random highlight."""
    # Viral Colors Palette (BGR format for ASS: &HBBGGRR)
    colors = [
        "&H0000FFFF", # Yellow
        "&H0000FF00", # Green
        "&H00FFFF00", # Cyan
        "&H00FF00FF", # Pink
        "&H000080FF", # Orange
    ]
    white_color = "&H00FFFFFF"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("[Script Info]\n")
        f.write("ScriptType: v4.00+\n")
        f.write("PlayResX: 1080\n")
        f.write("PlayResY: 1920\n")
        f.write("\n")
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        # Style: Large Arial font, Black outline
        f.write("Style: Default,Poppins,80,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,1,2,0,2,10,10,600,1\n")
        f.write("\n")
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        
        # 1. Flatten all words
        all_words = []
        for seg in segments:
            if 'words' in seg:
                all_words.extend(seg['words'])
            else:
                # Fallback if no word timestamps, fake it based on duration?
                # For now, just split text and distribute time evenly
                text_words = seg['text'].strip().split()
                if not text_words: continue
                duration = seg['end'] - seg['start']
                word_duration = duration / len(text_words)
                for i, w in enumerate(text_words):
                    all_words.append({
                        'word': w,
                        'start': seg['start'] + i * word_duration,
                        'end': seg['start'] + (i + 1) * word_duration
                    })

        if not all_words:
            return filename

        # 2. Chunk into groups of 3-4 words
        i = 0
        chunks = []
        while i < len(all_words):
            # Randomly choose chunk size 3 or 4
            chunk_size = random.randint(2, 3)
            chunk = all_words[i : i + chunk_size]
            if chunk:
                chunks.append(chunk)
            i += chunk_size

        # 3. Create Dialogue events for each chunk
        for chunk in chunks:
            start_time = chunk[0]['start']
            end_time = chunk[-1]['end']
            
            start_str = format_time_ass(start_time)
            end_str = format_time_ass(end_time)
            
            # Pick exactly one word index to highlight
            highlight_idx = random.randint(0, len(chunk) - 1)
            
            text_content = ""
            for idx, word_info in enumerate(chunk):
                word_text = word_info['word'].strip().upper()
                if idx == highlight_idx:
                    color = random.choice(colors)
                    text_content += f"{{\\1c{color}&}}{word_text} "
                else:
                    text_content += f"{{\\1c{white_color}&}}{word_text} "
            
            text_content = text_content.strip()
            f.write(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_content}\n")
            
    logger.info(f"Wrote {len(segments)} segments (re-chunked) to {filename}")
    return filename

def process_video(input_video, num_clips=5):
    import whisper
    from clipsai import Transcriber
    if not os.path.exists(input_video):
        logger.error(f"Input video not found: {input_video}")
        return

    logger.info(f"Processing {input_video}")
    
    # 1. Transcribe
    logger.info("Transcribing video (this may take a while)...")
    
    transcription = None
    
    # Use Whisper (OpenAI) directly for performance and reliability
    logger.info("Using Whisper (OpenAI)...")
    try:
        model = whisper.load_model("medium")
        # Enable word timestamps for karaoke effect
        transcription = model.transcribe(input_video, word_timestamps=True)
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return

    logger.info(f"Transcription type: {type(transcription)}")
    if isinstance(transcription, dict):
        logger.info(f"Transcription keys: {transcription.keys()}")
        if 'segments' in transcription:
            logger.info(f"Number of segments: {len(transcription['segments'])}")
            if len(transcription['segments']) > 0:
                logger.info(f"First segment: {transcription['segments'][0]}")
        else:
            logger.warning("No 'segments' key in transcription dict")
            logger.info(f"Full transcription dict: {transcription}")
    else:
        logger.info(f"Transcription dir: {dir(transcription)}")
        if hasattr(transcription, 'segments'):
             logger.info(f"Number of segments: {len(transcription.segments)}")
             if len(transcription.segments) > 0:
                logger.info(f"First segment: {transcription.segments[0]}")
        else:
             logger.warning("No 'segments' attribute in transcription object")

    # 2. Chunking
    logger.info("Chunking video into 60s segments...")
    
    try:
        probe = ffmpeg.probe(input_video)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        total_duration = float(video_info['duration'])
    except Exception as e:
        logger.error(f"Could not get video duration: {e}")
        return

    chunk_duration = 60.0
    clips = []
    current_time = 0.0
    
    while current_time < total_duration:
        end_time = min(current_time + chunk_duration, total_duration)
        # Ensure last clip is not too short (e.g. < 5 seconds)
        if end_time - current_time < 5.0:
            break
            
        clips.append({
            'start_time': current_time,
            'end_time': end_time
        })
        current_time += chunk_duration

    logger.info(f"Created {len(clips)} chunks.")
    
    generated_files = []
    for i, clip in enumerate(clips):
        logger.info(f"Processing clip {i+1}/{len(clips)}")
        
        # Extract times
        start_time = clip['start_time']
        end_time = clip['end_time']
        duration = end_time - start_time
        
        clip_filename = f"temp_clip_{i}.mp4"
        cropped_filename = f"temp_cropped_{i}.mp4"
        final_filename = f"viral_short_{i+1}.mp4"
        ass_filename = f"captions_{i}.ass"
        
        try:
            # Cut
            logger.info(f"Cutting clip ({duration:.2f}s)...")
            # We need to split audio and video here to ensure we have streams to work with
            # But for simple cutting 'copy' is fine, it copies all streams
            (
                ffmpeg
                .input(input_video, ss=start_time, t=duration)
                .output(clip_filename, c='copy')
                .run(overwrite_output=True, quiet=True)
            )
            
            # Gaussian Blur Background Effect (Blurred Fill)
            # 1. Background: Scale to height 1920 (to fill vertical frame), crop to 1080x1920, blur
            # 2. Foreground: Scale to width 1080 (to fit width)
            # 3. Overlay foreground on background
            logger.info("Applying Gaussian Blur Background effect...")
            
            input_stream = ffmpeg.input(clip_filename)
            split_streams = input_stream.video.split()
            
            # Background stream
            bg_stream = (
                split_streams[0]
                .filter('scale', -1, 1920)
                .filter('crop', 1080, 1920)
                .filter('gblur', sigma=20)
               #.filter('eq', brightness=0.1)
            )
            
            # Foreground stream
            fg_stream = (
                split_streams[1]
                .filter('scale', 1080, -1)
            )
            
            # Combine
            video_stream = ffmpeg.overlay(bg_stream, fg_stream, x='(W-w)/2', y='(H-h)/2')
            audio_stream = input_stream.audio
            
            (
                ffmpeg
                .output(video_stream, audio_stream, cropped_filename, vcodec='libx264', acodec='copy')
                .run(overwrite_output=True, quiet=True)
            )
            
            # Prepare captions
            clip_segments = []
            # transcription.segments is a list of dicts
            segments_list = []
            if hasattr(transcription, 'segments'):
                segments_list = transcription.segments
            elif isinstance(transcription, dict) and 'segments' in transcription:
                segments_list = transcription['segments']
            elif hasattr(transcription, '__getitem__'):
                try:
                    segments_list = transcription['segments']
                except (KeyError, TypeError):
                    pass
            
            if segments_list is None or not isinstance(segments_list, list):
                logger.error(f"Could not find segments in transcription object. Type: {type(transcription)}")
                logger.debug(f"Dir: {dir(transcription)}")
                if hasattr(transcription, 'keys'):
                     logger.debug(f"Keys: {transcription.keys()}")
                # Try to proceed or return? Let's return to avoid crash
                logger.warning("Skipping caption generation for this clip due to missing segments.")
                continue

            logger.info(f"Clip time: {start_time} - {end_time}")
            if segments_list:
                logger.info(f"Total transcription segments: {len(segments_list)}")
                logger.info(f"First segment: {segments_list[0]}")

            for seg in segments_list:
                # Check overlap
                seg_start = seg['start']
                seg_end = seg['end']
                
                # If segment is within clip (or overlaps significantly)
                if seg_end > start_time and seg_start < end_time:
                    # Adjust times relative to clip start
                    new_start = max(0, seg_start - start_time)
                    new_end = min(duration, seg_end - start_time)
                    
                    if new_end > new_start:
                        new_seg = seg.copy()
                        new_seg['start'] = new_start
                        new_seg['end'] = new_end
                        clip_segments.append(new_seg)
            
            logger.info(f"Found {len(clip_segments)} subtitle segments for this clip.")
            create_ass_file(clip_segments, ass_filename)
            
            # Burn captions
            logger.info("Burning captions...")
            
            # Again, explicitly map streams. 'ass' filter applies to video.
            input_stream = ffmpeg.input(cropped_filename)
            video_stream = input_stream.video.filter('ass', ass_filename)
            audio_stream = input_stream.audio
            
            (
                ffmpeg
                .output(video_stream, audio_stream, final_filename, vcodec='libx264', acodec='copy')
                .run(overwrite_output=True, quiet=True)
            )
            
            logger.info(f"Created {final_filename}")
            generated_files.append(final_filename)
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error processing clip {i}: {e.stderr.decode() if e.stderr else str(e)}")
        finally:
            # Cleanup temp files
            print("Cleanup temp files...")
            if os.path.exists(clip_filename):
                os.remove(clip_filename)
            if os.path.exists(cropped_filename):
                os.remove(cropped_filename)
            if os.path.exists(ass_filename):
                os.remove(ass_filename)

    return generated_files

if __name__ == "__main__":
    if len(sys.argv) > 1:
        video = sys.argv[1]
    else:
        video = "test.mp4"
    
    process_video(video)
