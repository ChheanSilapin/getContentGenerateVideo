#!/usr/bin/env python3
"""
Clear all caches to force regeneration of voice settings
Run this script to clear both content analysis and TTS caches
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Clear all caches"""
    try:
        from services.audio_service import clear_all_caches
        
        print("🧹 Clearing all caches...")
        clear_all_caches()
        print("✅ Cache clearing complete!")
        print("")
        print("🎯 Next video generation will use the new voice settings:")
        print("   • Educational content: speed=1.0, emotion=neutral")
        print("   • All other content: speed=1.0, emotion=dramatic")
        print("   • No more emotional tone speed variations")
        print("")
        print("🔄 Please run your video generation again to test the fixes.")
        
    except Exception as e:
        print(f"❌ Error clearing caches: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
