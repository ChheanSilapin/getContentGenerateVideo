import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Try to import the function with the syntax error
try:
    from services.video_optimization import apply_ffmpeg_enhancements
    print("Successfully imported apply_ffmpeg_enhancements")
except SyntaxError as e:
    print(f"Syntax error: {e}")
except Exception as e:
    print(f"Other error: {e}")

print("Test completed")
