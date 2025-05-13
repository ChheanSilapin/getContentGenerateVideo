# Video Generator

This application creates videos with subtitles from text and images.

## Features

- Generate speech from text
- Download images from a website or use local images from your computer
- Create a slideshow video with the images
- Generate subtitles for the video
- Merge the video and subtitles into a final output

## Installation

### Option 1: Run from Source

1. Install Python 3.10 or later
2. Clone this repository:
   ```
   git clone https://github.com/yourusername/video-generator.git
   cd video-generator
   ```
3. Create a virtual environment:
   ```
   python -m venv venv
   ```
4. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```
5. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
6. Install FFMPEG:
   - Download from: https://github.com/BtbN/FFmpeg-Builds/releases
   - Extract the files and place ffmpeg.exe, ffplay.exe, and ffprobe.exe in the root directory of the project

### Option 2: Run the Executable (Not yet available)

1. Download the latest release from the releases page
2. Extract the ZIP file
3. Run `VideoGenerator.exe`

## Usage

1. Activate the virtual environment (if running from source):
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

2. Run the application:
   ```
   python main.py
   ```

3. Enter the text you want to convert to speech

4. Choose your image source:
   - Option 1: Enter a website URL to get content and images
   - Option 2: Select a local folder containing images

5. Wait for the process to complete

6. The output directory will contain your generated video with subtitles

## For Developers

If you want to contribute to this project:

1. Fork the repository
2. Create a virtual environment and install dependencies as described above
3. Make your changes
4. Submit a pull request

## Troubleshooting

If you encounter any issues:

1. Check the console output for error messages
2. Make sure you have an active internet connection
3. Ensure ffmpeg is properly installed (included with the executable)
4. Try running the application as administrator
5. Make sure you've activated the virtual environment before running the application

## License

This project is licensed under the MIT License - see the LICENSE file for details.

