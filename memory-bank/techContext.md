# Technical Context: Video Generator

## Core Technologies
- **Python 3.10+**: Primary development language
- **Tkinter**: GUI framework
- **MoviePy**: Video creation and editing
- **FFmpeg**: Backend for video processing
- **Pillow**: Image processing
- **pyttsx3**: Text-to-speech conversion
- **requests & beautifulsoup4**: Web scraping for images

## Development Environment
- Python virtual environment recommended
- FFmpeg binaries required in project root or system PATH
- Cross-platform compatibility (Windows, macOS, Linux)

## Technical Constraints
- CPU-intensive operations for video processing
- Optional GPU acceleration for enhanced performance
- Dependency on external FFmpeg binaries
- Memory usage scales with video length and quality

## File Structure
- `main.py`: Application entry point
- `models/`: Core business logic
- `services/`: Specialized functionality
- `ui/`: User interface components
- `output/`: Generated videos and assets