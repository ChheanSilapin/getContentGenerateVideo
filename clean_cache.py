#!/usr/bin/env python3
"""
Script to clean Python cache files
"""
import os
import shutil

def clean_pycache():
    """Remove all __pycache__ directories and .pyc files"""
    count = 0
    
    # Walk through all directories
    for root, dirs, files in os.walk('.'):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            print(f"Removing: {cache_dir}")
            shutil.rmtree(cache_dir)
            count += 1
            
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                cache_file = os.path.join(root, file)
                print(f"Removing: {cache_file}")
                os.remove(cache_file)
                count += 1
                
    print(f"Cleaned {count} cache files/directories")

if __name__ == "__main__":
    clean_pycache()