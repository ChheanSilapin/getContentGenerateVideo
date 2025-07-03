# Enhanced Text Preprocessing for Speech Recognition

## Overview

When users input formatted text like your egg story example, the system now automatically preprocesses the text to optimize it for Text-to-Speech (TTS) generation and subsequent speech recognition validation. This improves the accuracy of the TTS-to-Speech-to-Text workflow used for subtitle synchronization.

## Your Example Text

**Original:**
```
Every morning, I start my day with a warm, freshly cooked egg. It's a simple routine, but it always brings me comfort. Some days, I boil it — soft and smooth, with just a pinch of salt. Other days, I fry it until the edges turn golden and crispy.

As the egg sizzles in the pan, the smell fills the kitchen, waking up my senses. It's a small moment, but it feels special — like a quiet gift before the day begins.

That first bite? Always warm, always satisfying. It gives me energy and a little joy.

It's funny how something so small can mean so much. A single egg. Simple. Honest. And somehow, it makes my whole morning feel just right
```

**Processed for TTS:**
```
Every morning, I start my day with a warm, freshly cooked egg. It is a simple routine, but it always brings me comfort. Some days, I boil it, soft and smooth, with just a pinch of salt. Other days, I fry it until the edges turn golden and crispy. As the egg sizzles in the pan, the smell fills the kitchen, waking up my senses. It is a small moment, but it feels special, like a quiet gift before the day begins. That first bite? Always warm, always satisfying. It gives me energy and a little joy. It is funny how something so small can mean so much. A single egg. Simple. Honest. And somehow, it makes my whole morning feel just right.
```

## Key Improvements Applied

### 1. Paragraph Break Handling
- **Before:** Multiple line breaks (`\n\n`) creating awkward pauses
- **After:** Converted to natural sentence breaks with proper spacing
- **Benefit:** Smoother speech flow and better timing synchronization

### 2. Contraction Expansion
- **Before:** `It's` → **After:** `It is`
- **Before:** `That's` → **After:** `That is`
- **Benefit:** Clearer pronunciation and more consistent speech recognition

### 3. Em Dash Conversion
- **Before:** `boil it — soft and smooth` 
- **After:** `boil it, soft and smooth`
- **Benefit:** Natural speech pauses instead of awkward dash pronunciation

### 4. Punctuation Normalization
- Consistent spacing around punctuation marks
- Proper sentence endings
- Removal of excessive punctuation

### 5. Whitespace Normalization
- Single spaces between words
- No trailing/leading whitespace
- Consistent formatting

## Technical Implementation

The preprocessing is automatically applied in two key places:

1. **Audio Generation** (`services/audio_service.py`)
   - Text is preprocessed before being sent to Edge TTS or Kokoro TTS
   - Results in cleaner, more natural speech synthesis

2. **Speech Recognition** (`services/speech_recognition_core.py`)
   - Text is preprocessed before TTS generation for validation
   - Improves accuracy of speech-to-text comparison

## Benefits for Your Workflow

### For TTS Generation:
- **Better Pronunciation:** Expanded contractions are pronounced more clearly
- **Natural Flow:** Proper punctuation creates appropriate pauses
- **Consistent Timing:** Normalized formatting ensures predictable speech patterns

### For Speech Recognition:
- **Higher Accuracy:** Cleaner input text produces more recognizable speech
- **Better Timestamps:** Consistent formatting improves word-level timing
- **Improved Validation:** More accurate comparison between original and recognized text

### For Subtitle Generation:
- **Synchronized Timing:** Better speech recognition leads to more accurate subtitle timing
- **Natural Breaks:** Proper sentence structure creates better subtitle segments
- **Consistent Display:** Normalized text produces more readable subtitles

## Usage

The preprocessing is **automatically applied** when you:

1. Generate videos with text prompts
2. Use the speech recognition validation feature
3. Create subtitles with timing synchronization

No manual intervention is required - just input your formatted text as usual, and the system will optimize it for the best speech recognition results.

## Testing

You can test the preprocessing function directly using:

```bash
python test_text_preprocessing.py
```

This will show you exactly how your text is being processed and what improvements are being applied.

## Advanced Features

The preprocessing function handles various text formatting scenarios:

- **Paragraph text** with multiple line breaks
- **Mixed punctuation** including em dashes, quotes, and special characters
- **Contractions** with proper capitalization preservation
- **Complex formatting** with multiple issues combined

## Result

Your egg story example now produces:
- **More natural TTS speech** with proper pauses and pronunciation
- **Higher speech recognition accuracy** for validation
- **Better synchronized subtitles** with accurate timing
- **Improved overall video quality** with professional-sounding narration

The system maintains the meaning and emotional tone of your original text while optimizing it for the technical requirements of speech synthesis and recognition.
