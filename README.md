# Video Generator

A powerful application that creates professional videos with subtitles from text and images. Generate voice-overs, add subtitles, and create engaging video content from any text input.

## 🚀 Quick Start

### Download & Install
1. **Download** the latest release: [Video Generator Setup v0.0.3](releases/Video%20Generator_Setup_0.0.3.exe)
2. **Run** the installer 
3. **Launch** Video Generator from your desktop
4. **Start creating** videos immediately!

### Basic Usage (3 Steps)
1. **Input Tab**: Enter your text and select image source
2. **Images Tab**: Preview and select your favorite images  
3. **Input Tab**: Click "Generate Video"

Your video will be created with voice-over, subtitles, and professional effects!

## ✨ Features

### 🎨 Content Creation
- **Text-to-Speech**: Natural-sounding voice generation
- **Image Slideshow**: Professional transitions and effects  
- **Subtitle Generation**: Automatic timing and styling
- **Voice-over Integration**: Add voice to existing videos
- **Multi-language Support**: Unicode and emoji compatibility

### 🖼️ Image Sources
- **Web Scraping**: Download images from any website
- **Local Folders**: Use your own image collections
- **Smart Selection**: Preview and choose specific images
- **Auto-filtering**: Skips icons, logos, and unsuitable images

### 🎬 Video Options
- **Multiple Aspect Ratios**: 9:16 (mobile), 16:9 (widescreen), 1:1 (square)
- **Quality Settings**: Adjustable resolution and frame rates
- **Visual Effects**: Zoom, fade transitions, color correction
- **Audio Mixing**: Blend voice-over with original audio

### 📦 Batch Processing
- **Multiple Projects**: Process several videos in sequence
- **Auto-cleanup**: Keeps only final output files
- **Progress Tracking**: Monitor all jobs in real-time

## 📱 Application Tabs

| Tab | Purpose |
|-----|---------|
| **Input** | Main video creation from text and images |
| **Images** | Preview and select specific images |
| **Video** | Add voice-over to existing video files |
| **Options** | Advanced settings and customization |
| **Batch** | Process multiple projects automatically |
| **Log** | Monitor progress and troubleshooting |

## 🛠️ Development Setup

### Requirements
- Python 3.10 or later
- Windows 10/11 (primary platform)

### From Source
```bash
# Clone repository
git clone https://github.com/ChheanSilapin/getContentGenerateVideo
cd getContentGenerateVideo

# Create virtual environment
python -m venv video_generator_env
video_generator_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Building
```bash
# Quick build
fast_build.bat

# Full installer build
build.bat
```

## 💡 Tips & Best Practices

### Image Selection
- Use high-quality images (minimum 800x600)
- Mix landscape and portrait orientations for visual variety
- Avoid copyrighted content

### Text Input
- Keep sentences clear and well-punctuated for better voice generation
- Use proper spacing for natural speech pacing
- Emojis are supported and will be described in voice-over

### Performance
- Use CPU processing for stability (default)
- Close other applications during video generation
- Allow sufficient disk space (500MB+ per video)

## 🔧 Troubleshooting

### Common Issues
- **Slow generation**: Check internet connection for image downloads
- **Audio issues**: Ensure system volume is not muted
- **Memory errors**: Close other applications and restart
- **File access**: Run as administrator if permission errors occur

### Getting Help
1. Check the **Log tab** for detailed error information
2. Ensure you have sufficient disk space
3. Try restarting the application
4. For persistent issues, create a GitHub issue with log details

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**Note**: This application includes FFmpeg for video processing. No additional downloads required!

