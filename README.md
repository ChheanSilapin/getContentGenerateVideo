# 🎬 Video Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![Version](https://img.shields.io/badge/version-1.0.9-blue.svg)](version.py)

A powerful, AI-enhanced desktop application that creates professional videos with synchronized subtitles from text and images. Features advanced text-to-speech, speech recognition validation, and intelligent subtitle generation with content-aware timing.

## 🌟 Key Features

- **🎤 Professional Text-to-Speech**: Edge TTS (Microsoft Neural) + Kokoro TTS with 6 high-quality voices
- **🎯 Precise Speech Recognition**: Whisper-timestamped for word-level subtitle synchronization
- **🎨 Smart Video Creation**: Automated slideshow generation with content-aware image timing
- **📝 Advanced Subtitles**: Netflix-standard formatting with dynamic backgrounds and voice sync
- **⚡ Optimized Performance**: Hardware acceleration, parallel processing, and memory management
- **🖥️ User-Friendly GUI**: Tabbed interface with real-time progress tracking and batch processing

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [🎯 Core Functionality](#-core-functionality)
- [🏗️ Architecture Overview](#️-architecture-overview)
- [🎤 AI & Voice Features](#-ai--voice-features)
- [📱 User Interface](#-user-interface)
- [🛠️ Development Setup](#️-development-setup)
- [📦 Deployment](#-deployment)
- [🔧 Configuration](#-configuration)
- [💡 Tips & Best Practices](#-tips--best-practices)
- [🔧 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## 🚀 Quick Start

### For End Users
1. **Download** the portable installer from releases
2. **Run** the installer - models download automatically on first launch
3. **Launch** Video Generator and start creating videos immediately!

### Basic Workflow (3 Steps)
1. **Enter Text**: Input your script or content in the main tab
2. **Select Images**: Choose from web scraping or local folders
3. **Generate**: Click "Generate Video" for automatic voice-over, subtitles, and effects

### System Requirements
- **OS**: Windows 10/11 (primary platform)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB for application + models
- **Internet**: Required for initial model download and web scraping

## 🎯 Core Functionality

### Primary Workflow: Text → Voice → Video
The application follows a streamlined workflow:
1. **Text Input**: User provides script/content
2. **Voice Generation**: AI converts text to natural speech using Edge TTS or Kokoro TTS
3. **Speech Analysis**: Whisper-timestamped extracts word-level timing data
4. **Subtitle Creation**: Generates Netflix-standard subtitles synchronized with voice
5. **Video Assembly**: Combines images, audio, and subtitles into final video

### 🎨 Video Creation Features
- **Automated Slideshow Generation**: Creates professional video slideshows from images
- **Content-Aware Image Timing**: Adjusts image display duration based on speech content
- **Professional Transitions**: Zoom, fade, and other cinematic effects
- **Multiple Aspect Ratios**: 9:16 (vertical), 16:9 (horizontal), 1:1 (square)
- **Batch Processing**: Process multiple videos simultaneously
- **Voice-over for Existing Videos**: Add narration to pre-existing video files

### 🖼️ Image Sources & Processing
- **Web Scraping**: Intelligent image extraction from any website with content filtering
- **Local Folders**: Support for personal image collections with auto-detection
- **Smart Image Selection**: Preview interface for manual image curation
- **Format Support**: JPG, PNG, GIF, WebP, BMP, TIFF
- **Auto-filtering**: Removes icons, logos, and unsuitable images automatically

## �️ Architecture Overview

### Clean Architecture Design
The application follows clean architecture principles with strict separation of concerns:

```
├── main.py                 # Application entry point with startup optimization
├── config.py              # Centralized configuration management
├── ui/                    # User Interface Layer
│   ├── gui.py            # Main GUI controller
│   ├── image_tab.py      # Image selection interface
│   └── video_tab.py      # Video processing interface
├── models/               # Business Logic Layer
│   ├── video_generator_refactored.py  # Core video generation logic
│   ├── batch_processor.py             # Batch processing management
│   └── cleanup_manager.py             # Resource cleanup
├── services/             # Service Layer (AI & Media Processing)
│   ├── tts_providers.py              # Text-to-speech services
│   ├── whisper_timestamped_service.py # Speech recognition
│   ├── subtitle_service.py           # Subtitle generation
│   ├── video_slideshow.py            # Video creation
│   └── audio_service.py              # Audio processing
└── utils/               # Utility Layer
    ├── memory_manager.py            # Memory optimization
    ├── settings_manager.py          # User settings
    └── path_manager.py             # File path management
```

### Key Design Patterns
- **Factory Pattern**: UI component creation and TTS provider management
- **Service Layer**: Decoupled AI services with fallback mechanisms
- **Observer Pattern**: Progress tracking and event handling
- **Strategy Pattern**: Multiple TTS providers with smart routing

## 🎤 AI & Voice Features

### Text-to-Speech Providers
The application supports two professional TTS providers with intelligent fallback:

#### Edge TTS (Microsoft Neural Voices)
- **Guy** (`en-US-GuyNeural`): US Male - Warm, friendly tone
- **Connor** (`en-IE-ConnorNeural`): Irish Male - Authentic accent
- **Aria** (`en-US-AriaNeural`): US Female - Natural, expressive

#### Kokoro TTS (82M Parameter Model)
- **Michael** (`am_michael`): Male - Friendly, warm tone
- **Adam** (`am_adam`): Male - Professional, clear delivery
- **Heart** (`af_heart`): Female - Warm, expressive voice

### Speech Recognition & Analysis
- **Whisper-timestamped**: Word-level timestamp extraction for precise subtitle synchronization
- **Voice Activity Detection (VAD)**: Silero VAD for natural pause detection
- **Confidence Scoring**: Quality assessment of speech recognition results
- **Caching System**: Optimized performance with intelligent result caching

### Subtitle Generation
- **Netflix Standards**: 42 characters per line, syntactic breaks, pyramid structure
- **Dynamic Backgrounds**: Voice-synchronized background effects with opacity control
- **Multiple Styles**: Modern glow, gradient gold, fire red, ice blue, bold outline
- **ASS Format**: Advanced SubStation Alpha for professional subtitle rendering
- **Smart Word Mapping**: Preserves original text formatting while maintaining voice sync

## 📱 User Interface

### Tabbed Interface Design
| Tab | Purpose | Key Features |
|-----|---------|-------------|
| **Images** | Image selection and preview | Web scraping, local folders, manual curation |
| **Video** | Video processing with voice-over | Existing video enhancement, audio mixing |
| **Log** | Progress monitoring | Real-time status, error tracking, performance metrics |

### User Experience Features
- **Real-time Progress**: Live updates during video generation
- **Memory Management**: Automatic cleanup and resource optimization
- **Settings Persistence**: User preferences saved automatically
- **Error Handling**: Graceful fallbacks with informative messages

## 🛠️ Development Setup

### System Requirements
- **Python**: 3.10+ (3.12 recommended)
- **OS**: Windows 10/11 (primary), Linux/macOS (experimental)
- **RAM**: 4GB minimum, 8GB recommended for AI models
- **Storage**: 2GB for application + models
- **GPU**: Optional (CUDA support for faster processing)

### Installation from Source
```bash
# Clone repository
git clone https://github.com/ChheanSilapin/getContentGenerateVideo
cd getContentGenerateVideo

# Create virtual environment
python -m venv video_generator_env
video_generator_env\Scripts\activate

# Install dependencies (handles conflicts automatically)
pip install -r requirements.txt

# Install PyTorch CPU (separate to avoid index conflicts)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Run application
python main.py
```

### Key Dependencies
```python
# Core AI & Speech
whisper-timestamped>=1.15.8    # Speech recognition with timestamps
edge-tts>=6.1.0                # Microsoft Neural TTS
kokoro>=0.9.4                   # High-quality neural TTS
silero-vad>=5.1.2              # Voice activity detection

# Video & Audio Processing
moviepy==1.0.3                 # Video editing and processing
pillow>=10.3.0                 # Image processing
pydub==0.25.1                  # Audio manipulation
soundfile>=0.12.0              # Audio I/O

# Scientific Computing (version-locked for stability)
numpy>=1.21.2,<2.0.0          # Numerical computing
scipy>=1.10.0                  # Scientific computing
```

## 📦 Deployment

### Portable Build System
The application uses a sophisticated portable build system for easy distribution:

#### Build Scripts
```bash
# Create portable executable
build_portable.bat

# Generate installer with NSIS
build_installer.bat

# Test complete workflow
test_portable_workflow.bat
```

#### Deployment Features
- **Single-file Executable**: PyInstaller-based with all dependencies bundled
- **First-run Setup**: Automatic AI model download on initial launch
- **Portable Operation**: Works from any location without installation
- **Smart Dependency Management**: Handles DLL inclusion and model caching
- **Professional Installer**: NSIS-based installer with proper uninstall support

## � Configuration

### Core Configuration (`config.py`)
The application uses centralized configuration with intelligent defaults:

#### Video Settings
```python
# Video dimensions and aspect ratios
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280  # Default 9:16 for mobile
DEFAULT_FRAME_RATE = 25

# Aspect ratio presets
RATIO_9_16 = {"name": "9:16 (Vertical)", "width": 720, "height": 1280}
RATIO_16_9 = {"name": "16:9 (Horizontal)", "width": 1280, "height": 720}
RATIO_1_1 = {"name": "1:1 (Square)", "width": 1080, "height": 1080}
```

#### TTS Configuration
```python
TTS_CONFIG = {
    "default_provider": "edge_tts",
    "fallback_enabled": True,
    "priority_order": ["edge_tts", "kokoro_tts"],
    "default_voice": "Guy",
    "emotion_processing": True,
    "speed_adjustment": True
}
```

#### Subtitle Settings
```python
SUBTITLE_CONFIG = {
    "reading_speed_wpm": 80,        # Comfortable reading speed
    "min_display_time": 4.0,        # Minimum subtitle duration
    "use_speech_analysis": True,    # Enable voice synchronization
    "default_style": "bold_outline" # Netflix-style formatting
}
```

#### Performance Optimization
```python
FFMPEG_OPTIMIZATION = {
    "preset": "ultrafast",          # Fastest encoding
    "hardware_acceleration": True,   # GPU acceleration when available
    "parallel_processing": True,     # Multi-core utilization
    "memory_optimization": True      # Smart memory management
}
```

### User Settings (`user_settings.json`)
Runtime settings are automatically saved and restored:
- Voice preferences and TTS provider selection
- Video quality and aspect ratio preferences
- UI layout and tab visibility
- Performance and memory settings

## � Tips & Best Practices

### Content Creation
- **Text Quality**: Use clear, well-punctuated sentences for better voice generation
- **Image Selection**: High-quality images (800x600+) with mixed orientations
- **Content Length**: Optimal video length is 30-120 seconds for engagement
- **Voice Pacing**: Use proper spacing and punctuation for natural speech rhythm

### Performance Optimization
- **Memory Management**: Close unnecessary applications during video generation
- **Storage Space**: Ensure 500MB+ free space per video project
- **Processing Mode**: Use CPU processing for stability (GPU optional for speed)
- **Batch Processing**: Process multiple videos during off-peak hours

### Quality Settings
- **Aspect Ratios**: 9:16 for mobile/social, 16:9 for desktop/TV, 1:1 for square posts
- **Voice Selection**: Match voice personality to content type (professional vs casual)
- **Subtitle Timing**: Enable speech analysis for precise voice-subtitle synchronization
- **Visual Effects**: Use content-aware timing for better image-speech alignment

## �🔧 Troubleshooting

### Common Issues & Solutions

#### Installation & Setup
- **FFmpeg Not Found**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or place `ffmpeg.exe` in application folder
- **Model Download Fails**: Check internet connection; models auto-download on first run
- **Import Errors**: Ensure all dependencies installed with `pip install -r requirements.txt`
- **PyTorch Issues**: Install CPU version separately: `pip install torch --index-url https://download.pytorch.org/whl/cpu`

#### Performance Issues
- **Slow Generation**: Check internet connection for image downloads and model access
- **Memory Errors**: Close other applications; reduce parallel processing in settings
- **Audio Problems**: Verify system audio not muted; check TTS provider availability
- **Video Quality**: Adjust FFmpeg preset in config (ultrafast → fast → medium for better quality)

#### AI & Voice Issues
- **TTS Failures**: Application automatically falls back between Edge TTS and Kokoro TTS
- **Subtitle Sync Problems**: Enable speech analysis in settings for better timing
- **Voice Quality**: Try different voice actors; adjust speed settings for clarity
- **Recognition Errors**: Whisper-timestamped handles most accents; check audio quality

#### File & Path Issues
- **Output Folder**: Application creates output directory automatically in temp folder if needed
- **Portable Mode**: Ensure application has write permissions in its directory
- **Long Paths**: Windows path length limits may affect deep folder structures
- **File Locks**: Close other applications that might lock video/audio files

### Debug Mode
Enable verbose logging for detailed troubleshooting:
```bash
python main.py --verbose
```

### Log Files
Check application logs for detailed error information:
- **Location**: `logs/` folder in application directory
- **Key Files**: `video_finalization.log` for processing details
- **Real-time**: Monitor Log tab in application for live updates
## 🤝 Contributing

We welcome contributions to improve Video Generator! This project follows clean architecture principles and modern development practices.

### Development Guidelines
- **Code Style**: Follow PEP 8 guidelines with Black formatting
- **Architecture**: Maintain separation of concerns (UI → Models → Services → Utils)
- **Testing**: Add unit tests for new features and bug fixes
- **Documentation**: Update docstrings and README for any changes
- **Dependencies**: Use package managers; avoid manual package file edits

### Contribution Areas
- **AI Models**: Improve TTS providers and speech recognition accuracy
- **Performance**: Optimize video processing and memory management
- **UI/UX**: Enhance user interface and experience
- **Platform Support**: Extend Linux/macOS compatibility
- **Documentation**: Improve guides and troubleshooting

### Getting Started
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes following architecture patterns
4. Test thoroughly with different content types
5. Submit pull request with detailed description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

```
MIT License

Copyright (c) 2024 Video Generator

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## � Project Status

- **Version**: 1.0.9 (Active Development)
- **Platform**: Windows 10/11 (Primary), Linux/macOS (Experimental)
- **AI Models**: Edge TTS, Kokoro TTS, Whisper-timestamped
- **Architecture**: Clean Architecture with Service Layer Pattern
- **Deployment**: Portable executable with automatic model download

**Made with ❤️ for content creators worldwide**

*Transform your ideas into professional videos with AI-powered voice generation and intelligent subtitle synchronization.*



