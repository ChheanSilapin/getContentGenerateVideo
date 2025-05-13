# Video Generator Architecture

This document explains the architecture of the Video Generator application, detailing each component, how they work, and how they integrate together.

## Overview

The Video Generator is a Python application that creates videos with subtitles from text and images. It follows a Model-View-Controller (MVC) architecture pattern:

- **Model**: Handles the core business logic and data processing
- **View**: Manages the user interface (GUI and console)
- **Services**: Provide specialized functionality for different aspects of video generation

## Project Structure

```
video_generator/
├── main.py                 # Entry point
├── config.py               # Configuration settings
├── models/
│   ├── __init__.py
│   └── video_generator.py  # VideoGeneratorModel class
├── ui/
│   ├── __init__.py
│   ├── gui.py              # Main GUI class
│   ├── image_selector.py   # Image selection component
│   └── text_redirector.py  # Console output redirection
├── services/
│   ├── __init__.py
│   ├── audio_service.py    # Audio generation wrapper
│   ├── image_service.py    # Image processing wrapper
│   ├── subtitle_service.py # Subtitle generation wrapper
│   └── video_service.py    # Video creation wrapper
└── utils/
    ├── __init__.py
    └── helpers.py          # Common utility functions
```

## Core Components

### 1. Entry Point (`main.py`)

The application starts in `main.py`, which:
- Parses command-line arguments
- Determines whether to run in GUI or console mode
- Initializes the appropriate interface

```python
# Simplified example
def main():
    # Parse arguments
    if args.console:
        run_console_mode()
    else:
        run_gui_mode()

def run_console_mode():
    # Initialize the model
    model = VideoGeneratorModel()
    # Get user input
    # Generate video
    
def run_gui_mode():
    # Create and start the GUI
    root = tk.Tk()
    app = VideoGeneratorGUI(root)
    root.mainloop()
```

### 2. Model (`models/video_generator.py`)

The `VideoGeneratorModel` class is the core of the application, orchestrating the entire video generation process:

```python
class VideoGeneratorModel:
    def __init__(self):
        # Initialize properties
        self.text_input = None
        self.image_source = None
        self.website_url = None
        self.local_folder = None
        self.selected_images = []
    
    def generate_video(self, stop_event=None):
        # 1. Generate audio from text
        # 2. Get images (from website or local folder)
        # 3. Create video slideshow
        # 4. Generate subtitles
        # Return paths to generated files
        
    def finalize_video(self, subtitlePath, videoPath, output_dir, stop_event=None):
        # Merge video with subtitles
        # Return path to final video
```

The model doesn't directly perform these operations but delegates to specialized service modules.

### 3. Services

#### 3.1 Audio Service (`services/audio_service.py`)

Handles text-to-speech conversion:

```python
def generate_audio(text, output_file):
    # Convert text to speech using pyttsx3 or other TTS engine
    # Save audio to output_file
    # Return path to generated audio file
```

#### 3.2 Image Service (`services/image_service.py`)

Manages image acquisition and processing:

```python
def download_images(url, output_folder):
    # Scrape images from the provided URL
    # Save images to output_folder
    # Return list of image paths

def copy_selected_images(source_folder, selected_images, output_folder):
    # Copy selected images from source_folder to output_folder
    # Return list of copied image paths
```

#### 3.3 Video Service (`services/video_service.py`)

Creates videos and handles video processing:

```python
def create_slideshow(images_folder, title, content, audio_file, output_file):
    # Create a slideshow video from images
    # Add title and content
    # Add audio track
    # Save to output_file
    # Return path to video file

def merge_video_with_subtitles(video_path, subtitle_path, output_file):
    # Merge video with subtitles
    # Save to output_file
    # Return path to final video
```

#### 3.4 Subtitle Service (`services/subtitle_service.py`)

Generates subtitles for the video:

```python
def generate_subtitles(video_path, output_file, audio_file=None):
    # Generate subtitles based on audio content
    # Save subtitles to output_file
    # Return path to subtitle file
```

### 4. User Interface

#### 4.1 GUI (`ui/gui.py`)

The graphical user interface built with Tkinter:

```python
class VideoGeneratorGUI:
    def __init__(self, root):
        # Initialize the GUI
        # Create text input field
        # Create image source selection
        # Create generate button
        # Create console output area
        
    def on_generate(self):
        # Get user input
        # Update model with user input
        # Start generation process in a separate thread
        
    def update_progress(self, message):
        # Update progress in the GUI
```

#### 4.2 Image Selector (`ui/image_selector.py`)

Component for selecting and previewing images:

```python
class ImageSelector:
    def __init__(self, parent):
        # Initialize image selection UI
        # Create file browser
        # Create image preview area
        
    def select_folder(self):
        # Open folder selection dialog
        # Display images from selected folder
        
    def get_selected_images(self):
        # Return list of selected images
```

#### 4.3 Text Redirector (`ui/text_redirector.py`)

Redirects console output to the GUI:

```python
class TextRedirector:
    def __init__(self, text_widget):
        # Initialize with a text widget
        
    def write(self, string):
        # Write string to the text widget
        
    def flush(self):
        # Required for compatibility with sys.stdout
```

## Integration Flow

1. **Initialization**:
   - `main.py` starts the application
   - Either console or GUI interface is initialized
   - The `VideoGeneratorModel` is created

2. **User Input**:
   - User provides text for speech generation
   - User selects image source (website URL or local folder)
   - If local folder, user selects specific images

3. **Video Generation Process**:
   - Model's `generate_video()` method is called
   - Audio is generated using `audio_service.py`
   - Images are acquired using `image_service.py`
   - Video slideshow is created using `video_service.py`
   - Subtitles are generated using `subtitle_service.py`

4. **Finalization**:
   - Model's `finalize_video()` method is called
   - Video and subtitles are merged using `video_service.py`
   - Final output is saved to the output directory

5. **Progress Updates**:
   - Throughout the process, progress messages are printed
   - In GUI mode, these messages are redirected to the GUI using `TextRedirector`

## Key Dependencies

1. **pyttsx3**: Text-to-speech conversion
2. **requests** & **beautifulsoup4**: Web scraping for images
3. **moviepy**: Video creation and editing
4. **pillow**: Image processing
5. **emoji**: Emoji handling in subtitles
6. **tkinter**: GUI framework

## Advanced Features

### Threading

The application uses threading to prevent the GUI from freezing during video generation:

```python
def start_generation(self):
    # Create a thread for video generation
    self.stop_event = threading.Event()
    self.thread = threading.Thread(target=self.generate_video_thread)
    self.thread.daemon = True
    self.thread.start()
    
def generate_video_thread(self):
    # Run the video generation process in a separate thread
    # Update GUI with progress
```

### Stop Mechanism

The application includes a mechanism to stop the generation process:

```python
def stop_generation(self):
    # Set the stop event
    if self.stop_event:
        self.stop_event.set()
```

The `stop_event` is passed to the model's methods, which periodically check if they should terminate.

## Conclusion

The Video Generator application follows a modular design with clear separation of concerns. The model orchestrates the process, services provide specialized functionality, and the UI handles user interaction. This architecture makes the code maintainable, extensible, and testable.