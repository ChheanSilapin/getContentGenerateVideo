# 🚀 Video Generator Setup Instructions

## 📋 Prerequisites

Before running the Video Generator, you need to download and set up the required dependencies that are not included in this repository.

## 🔧 Required Downloads

### 1. **FFmpeg Binaries** (Required for video processing)

**Download FFmpeg for Windows:**
- Go to: https://ffmpeg.org/download.html#build-windows
- Download the **Windows builds** (static version recommended)
- Extract the following files to your project root directory:
  - `ffmpeg.exe`
  - `ffplay.exe` 
  - `ffprobe.exe`

**File locations should be:**
```
your-project/
├── ffmpeg.exe
├── ffplay.exe
├── ffprobe.exe
└── main.py
```

### 2. **Vosk Speech Recognition Model** (Required for speech recognition)

**Download Vosk Model:**
- Go to: https://alphacephei.com/vosk/models
- Download: **vosk-model-small-en-us-0.15** (~40MB)
- Extract to: `models/vosk-model-small-en-us-0.15/`

**Directory structure should be:**
```
your-project/
├── models/
│   └── vosk-model-small-en-us-0.15/
│       ├── am/
│       ├── graph/
│       ├── ivector/
│       └── conf/
└── main.py
```

## 🐍 Python Environment Setup

### 1. **Create Virtual Environment:**
```bash
python -m venv video_generator_env
```

### 2. **Activate Environment:**
```bash
# Windows
.\video_generator_env\Scripts\activate

# Linux/Mac
source video_generator_env/bin/activate
```

### 3. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

## ✅ Verify Setup

### 1. **Check File Structure:**
```
your-project/
├── ffmpeg.exe                    ✅ Required
├── ffplay.exe                    ✅ Required
├── ffprobe.exe                   ✅ Required
├── models/
│   └── vosk-model-small-en-us-0.15/  ✅ Required
├── main.py                       ✅ Included
├── requirements.txt              ✅ Included
└── video_generator_env/          ✅ Created
```

### 2. **Test Run:**
```bash
python main.py
```

## 🎯 Quick Setup Script

You can also create this script to automate the setup:

```python
# setup.py
import os
import requests
import zipfile
from pathlib import Path

def download_ffmpeg():
    print("📥 Please download FFmpeg manually from:")
    print("https://ffmpeg.org/download.html#build-windows")
    print("Extract ffmpeg.exe, ffplay.exe, ffprobe.exe to project root")

def download_vosk_model():
    print("📥 Please download Vosk model manually from:")
    print("https://alphacephei.com/vosk/models")
    print("Download: vosk-model-small-en-us-0.15")
    print("Extract to: models/vosk-model-small-en-us-0.15/")

if __name__ == "__main__":
    download_ffmpeg()
    download_vosk_model()
    print("✅ Setup complete! Run 'python main.py' to start.")
```

## 🚨 Troubleshooting

### **Common Issues:**

1. **"FFmpeg not found"**
   - Ensure `ffmpeg.exe` is in the project root directory
   - Check file permissions

2. **"Vosk model not found"**
   - Verify the model is extracted to `models/vosk-model-small-en-us-0.15/`
   - Check directory structure matches exactly

3. **"Module not found"**
   - Activate virtual environment: `.\video_generator_env\Scripts\activate`
   - Install requirements: `pip install -r requirements.txt`

## 📦 For Distribution

When creating releases, include:
- Complete executable (PyInstaller output)
- FFmpeg binaries bundled
- Vosk model bundled
- No additional setup required for end users

## 🎉 Ready to Use!

Once setup is complete, you can:
- Generate videos from images
- Create video content with voice-over
- Use speech recognition validation
- Apply emotion-aware effects
- Export professional-quality videos

**Happy video generating!** 🎬✨
