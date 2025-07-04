# 🎬 Video Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

A powerful, AI-enhanced application that creates professional videos with subtitles from text and images. Generate voice-overs with speech recognition validation, add intelligent subtitles, and create engaging video content with content-aware settings.

## 🌟 Key Highlights

- **🎤 Advanced Text-to-Speech**: Multi-language support with Hindi voice actors
- **🧠 AI Content Analysis**: Automatic content type detection and emotion-aware settings
- **🎯 Speech Recognition**: Whisper-timestamped for precise subtitle synchronization
- **🌍 Multi-language Support**: English, Hindi, and more with automatic language detection
- **⚡ Real-time Processing**: Live progress tracking and background processing
- **🎨 Professional Effects**: Content-aware transitions and visual enhancements

## � Table of Contents

- [🚀 Quick Start](#-quick-start)
- [✨ Features](#-features)
- [📱 Application Tabs](#-application-tabs)
- [🛠️ Development Setup](#️-development-setup)
- [💡 Tips & Best Practices](#-tips--best-practices)
- [🔧 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## �🚀 Quick Start

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

We welcome contributions from the community! Whether you're fixing bugs, adding features, improving documentation, or suggesting enhancements, your help is appreciated.

### 🌟 Ways to Contribute

#### 🐛 Bug Reports
- **Search existing issues** before creating new ones
- **Use the bug report template** with detailed information
- **Include logs** from the Log tab when reporting issues
- **Provide steps to reproduce** the problem

#### ✨ Feature Requests
- **Check existing feature requests** to avoid duplicates
- **Describe the use case** and why it would be valuable
- **Provide mockups or examples** if applicable
- **Consider implementation complexity** and user impact

#### 💻 Code Contributions
- **Start with good first issues** labeled `good-first-issue`
- **Follow the coding standards** outlined below
- **Write tests** for new functionality
- **Update documentation** as needed

#### 📚 Documentation
- **Improve README** sections that are unclear
- **Add code comments** for complex functions
- **Create tutorials** or usage examples
- **Translate documentation** to other languages

### 🛠️ Development Guidelines

#### Setting Up Development Environment
```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/getContentGenerateVideo
cd getContentGenerateVideo

# 2. Create virtual environment
python -m venv video_generator_env
video_generator_env\Scripts\activate  # Windows
source video_generator_env/bin/activate  # Linux/Mac

# 3. Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8  # Development tools

# 4. Run tests to ensure everything works
python -m pytest tests/

# 5. Start development
python main.py
```

#### Code Style & Standards
- **Python Style**: Follow PEP 8 guidelines
- **Code Formatting**: Use `black` for automatic formatting
- **Linting**: Use `flake8` for code quality checks
- **Docstrings**: Document all public functions and classes
- **Type Hints**: Add type hints for better code clarity

```bash
# Format code before committing
black .

# Check code quality
flake8 .

# Run tests
python -m pytest tests/ -v
```

#### Project Structure
```
getContentGenerateVideo/
├── main.py                 # Application entry point
├── models/                 # Core business logic
├── services/              # External service integrations
├── ui/                    # User interface components
├── utils/                 # Utility functions and helpers
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

#### Commit Guidelines
- **Use conventional commits**: `type(scope): description`
- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- **Examples**:
  - `feat(audio): add Hindi voice support`
  - `fix(ui): resolve settings dialog crash`
  - `docs(readme): update installation instructions`

### 🔄 Pull Request Process

1. **Fork the repository** and create your branch from `main`
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following the coding standards
4. **Add tests** for new functionality
5. **Update documentation** if needed
6. **Run the test suite** to ensure nothing breaks
7. **Commit your changes** with clear, descriptive messages
8. **Push to your fork**: `git push origin feature/amazing-feature`
9. **Create a Pull Request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots/videos for UI changes
   - Test results and verification steps

#### Pull Request Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Tests added for new functionality
- [ ] All tests pass locally
- [ ] Documentation updated if needed
- [ ] No breaking changes (or clearly documented)
- [ ] Screenshots included for UI changes

### 🧪 Testing

#### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_audio_service.py

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

#### Writing Tests
- **Unit tests** for individual functions
- **Integration tests** for component interactions
- **UI tests** for critical user workflows
- **Mock external dependencies** (APIs, file system)

### 🏷️ Issue Labels

| Label | Description |
|-------|-------------|
| `bug` | Something isn't working |
| `enhancement` | New feature or request |
| `good-first-issue` | Good for newcomers |
| `help-wanted` | Extra attention is needed |
| `documentation` | Improvements or additions to docs |
| `question` | Further information is requested |
| `wontfix` | This will not be worked on |

### 💬 Community Guidelines

- **Be respectful** and inclusive in all interactions
- **Help others** learn and contribute
- **Provide constructive feedback** in code reviews
- **Ask questions** if something is unclear
- **Share knowledge** and best practices

### 🎯 Priority Areas for Contribution

1. **Performance Optimization**: Video processing speed improvements
2. **Cross-platform Support**: Linux and macOS compatibility
3. **Accessibility**: Screen reader support and keyboard navigation
4. **Internationalization**: Multi-language UI support
5. **Advanced Features**: AI-powered content analysis
6. **Testing**: Increase test coverage and reliability

### 📞 Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Code Review**: Tag maintainers for review assistance
- **Documentation**: Check existing docs before asking

### 🙏 Recognition

Contributors will be:
- **Listed in CONTRIBUTORS.md** with their contributions
- **Mentioned in release notes** for significant contributions
- **Invited to join** the core contributor team for ongoing contributors

Thank you for helping make Video Generator better for everyone! 🚀

---

**Note**: This application includes FFmpeg for video processing. No additional downloads required!

