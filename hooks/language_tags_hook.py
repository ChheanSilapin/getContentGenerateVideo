
"""
Runtime hook to patch language_tags to find its data files
"""
import os
import sys
import json

# When running as a frozen application
if getattr(sys, 'frozen', False):
    # Get the directory where the executable is located
    base_dir = os.path.dirname(sys.executable)
    
    # Patch language_tags.data module
    try:
        import language_tags.data
        
        # Original get function
        original_get = language_tags.data.get
        
        # Override the get function to use the correct path
        def patched_get(filename):
            # First try the original function
            try:
                return original_get(filename)
            except FileNotFoundError:
                # If that fails, try our bundled path
                path = os.path.join(base_dir, 'language_tags', 'data', 'json', filename)
                if not os.path.exists(path):
                    print(f"WARNING: Data file not found: {path}")
                    # Last resort - try to find it anywhere in the bundle
                    for root, dirs, files in os.walk(base_dir):
                        if filename in files:
                            path = os.path.join(root, filename)
                            print(f"Found data file at: {path}")
                            with open(path, 'r', encoding='utf-8') as f:
                                return json.load(f)
                    return {}
                
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # Apply the patch
        language_tags.data.get = patched_get
        print("Patched language_tags.data.get to use correct path")
    except ImportError:
        print("Could not patch language_tags (not imported yet)")
