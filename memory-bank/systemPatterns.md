# System Patterns: Video Generator

## Architecture
The application follows the Model-View-Controller (MVC) pattern:
- **Model**: `VideoGeneratorModel` handles core business logic
- **View**: GUI and console interfaces for user interaction
- **Services**: Specialized components for different aspects of video generation

## Key Components
1. **Video Generator Model**: Orchestrates the entire process
2. **Audio Service**: Handles text-to-speech conversion
3. **Image Service**: Manages image acquisition and processing
4. **Video Service**: Creates slideshow videos with effects
5. **Subtitle Service**: Generates synchronized subtitles
6. **Final Video**: Merges video and subtitles

## Process Flow
1. User provides text and selects image source
2. System generates audio from text
3. System acquires images (from web or local folder)
4. System creates video slideshow with effects
5. System generates subtitles
6. System merges video and subtitles into final output

## Threading Model
- Video generation runs in separate threads to prevent UI freezing
- Stop mechanism allows cancellation of processing
- Progress updates are communicated to UI via callbacks