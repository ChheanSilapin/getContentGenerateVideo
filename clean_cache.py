#!/usr/bin/env python3
"""
Script to clean Python cache files
"""
import os
import shutil
import argparse

def clean_pycache(directory='.', verbose=True, include_venv=False):
    """
    Remove all __pycache__ directories and .pyc files
    
    Args:
        directory: Root directory to start cleaning from
        verbose: Whether to print removed files
        include_venv: Whether to clean cache files in virtual environment
    
    Returns:
        int: Number of cache files/directories cleaned
    """
    count = 0
    
    # Walk through all directories
    for root, dirs, files in os.walk(directory):
        # Skip virtual environment if not included
        if not include_venv and ('venv' in root.split(os.path.sep) or 'env' in root.split(os.path.sep)):
            continue
            
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            if verbose:
                print(f"Removing: {cache_dir}")
            shutil.rmtree(cache_dir)
            count += 1
            
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                cache_file = os.path.join(root, file)
                if verbose:
                    print(f"Removing: {cache_file}")
                os.remove(cache_file)
                count += 1
                
    if verbose:
        print(f"Cleaned {count} cache files/directories")
    return count

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Clean Python cache files')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress output')
    parser.add_argument('-a', '--all', action='store_true', help='Include virtual environment directories')
    parser.add_argument('-d', '--directory', default='.', help='Root directory to clean')
    
    args = parser.parse_args()
    
    clean_pycache(
        directory=args.directory,
        verbose=not args.quiet,
        include_venv=args.all
    )

if __name__ == "__main__":
    main()
