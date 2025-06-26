#!/usr/bin/env python3
"""
Output Manager - Handles final video placement and filename conflict resolution
"""

import os
import shutil
from pathlib import Path
from utils.filename_validator import sanitize_filename


class OutputManager:
    """Manages final video output placement and filename conflicts"""
    
    def __init__(self, user_output_directory):
        """
        Initialize OutputManager
        
        Args:
            user_output_directory (str): User's chosen output directory
        """
        self.user_output_directory = user_output_directory
        self.ensure_output_directory()
    
    def ensure_output_directory(self):
        """Ensure the output directory exists"""
        try:
            os.makedirs(self.user_output_directory, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create output directory {self.user_output_directory}: {e}")
    
    def get_unique_filename(self, desired_filename, extension=".mp4"):
        """
        Get a unique filename in the output directory, handling conflicts with numbering
        
        Args:
            desired_filename (str): Desired filename without extension
            extension (str): File extension (default: .mp4)
            
        Returns:
            str: Unique filename with extension
        """
        # Sanitize the desired filename
        clean_filename = sanitize_filename(desired_filename) if desired_filename else "video"
        
        # Create the full path
        base_path = os.path.join(self.user_output_directory, f"{clean_filename}{extension}")
        
        # If file doesn't exist, use it as-is
        if not os.path.exists(base_path):
            return f"{clean_filename}{extension}"
        
        # File exists, find a unique name with numbering
        counter = 1
        while True:
            numbered_filename = f"{clean_filename}_{counter}{extension}"
            numbered_path = os.path.join(self.user_output_directory, numbered_filename)
            
            if not os.path.exists(numbered_path):
                return numbered_filename
            
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 9999:
                import time
                timestamp = int(time.time())
                return f"{clean_filename}_{timestamp}{extension}"
    
    def move_final_video(self, temp_video_path, custom_filename=None, source_files=None, default_name="video"):
        """
        Move final video from temporary location to user's output directory

        Args:
            temp_video_path (str): Path to the temporary video file
            custom_filename (str): Custom filename provided by user (optional)
            source_files (list): List of source file paths for intelligent default naming
            default_name (str): Fallback name to use if no custom filename or source files

        Returns:
            str: Path to the final video file in user's output directory
        """
        try:
            if not os.path.exists(temp_video_path):
                print(f"Error: Temporary video file not found: {temp_video_path}")
                return None

            # Determine the desired filename with intelligent defaults
            desired_name = self._determine_output_filename(custom_filename, source_files, default_name)

            # Get unique filename with conflict resolution
            final_filename = self.get_unique_filename(desired_name)
            final_path = os.path.join(self.user_output_directory, final_filename)

            # Move the file
            shutil.move(temp_video_path, final_path)

            print(f"✅ Final video saved: {final_path}")
            return final_path

        except Exception as e:
            print(f"Error moving final video: {e}")
            # Try copying as fallback
            try:
                desired_name = self._determine_output_filename(custom_filename, source_files, default_name)
                final_filename = self.get_unique_filename(desired_name)
                final_path = os.path.join(self.user_output_directory, final_filename)
                shutil.copy2(temp_video_path, final_path)
                print(f"✅ Final video copied: {final_path}")
                return final_path
            except Exception as copy_e:
                print(f"Error copying final video: {copy_e}")
                return None
    
    def cleanup_temp_directory(self, temp_dir):
        """
        Clean up temporary directory after moving final video

        Args:
            temp_dir (str): Path to temporary directory to clean up
        """
        try:
            if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
                # SAFETY CHECK: Don't remove the main user output directory
                # Only remove actual temporary directories
                if temp_dir == self.user_output_directory:
                    print(f"⚠️ Skipping cleanup of main output directory: {temp_dir}")
                    return

                # Additional safety check: Only remove directories with timestamp patterns
                dir_name = os.path.basename(temp_dir)
                if not (dir_name.startswith("video_") and "_" in dir_name):
                    print(f"⚠️ Skipping cleanup of non-temporary directory: {dir_name}")
                    return

                shutil.rmtree(temp_dir)
                print(f"🗑️ Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up temporary directory {temp_dir}: {e}")
    
    def _determine_output_filename(self, custom_filename, source_files, default_name):
        """
        Determine the output filename using intelligent defaults

        Args:
            custom_filename (str): Custom filename provided by user
            source_files (list): List of source file paths
            default_name (str): Fallback default name

        Returns:
            str: Determined filename (without extension)
        """
        # Check if custom filename is provided and not placeholder text
        if custom_filename and custom_filename.strip():
            cleaned_custom = custom_filename.strip()
            # Check if it's not placeholder text
            if cleaned_custom not in ["Custom filename (optional)", "Enter custom filename (optional)"]:
                return cleaned_custom

        # Use intelligent default based on source files
        if source_files and len(source_files) > 0:
            # Get the first source file
            first_file = source_files[0]
            if first_file:
                # Extract filename without extension (don't require file to exist for naming)
                base_name = os.path.splitext(os.path.basename(first_file))[0]
                if base_name:
                    # Sanitize the source filename to ensure compatibility
                    sanitized_base_name = sanitize_filename(base_name)
                    if sanitized_base_name:
                        return sanitized_base_name

        # Fallback to default name
        return default_name

    def get_final_output_path(self, custom_filename=None, source_files=None, default_name="video"):
        """
        Get the final output path without actually creating the file

        Args:
            custom_filename (str): Custom filename provided by user (optional)
            source_files (list): List of source file paths for intelligent default naming
            default_name (str): Default name to use if no custom filename or source files

        Returns:
            str: Full path where the final video will be saved
        """
        # Determine the desired filename with intelligent defaults
        desired_name = self._determine_output_filename(custom_filename, source_files, default_name)

        # Get unique filename with conflict resolution
        final_filename = self.get_unique_filename(desired_name)
        return os.path.join(self.user_output_directory, final_filename)


def get_output_manager(user_settings=None):
    """
    Get OutputManager instance with user's output directory
    
    Args:
        user_settings (dict): User settings containing output folder preference
        
    Returns:
        OutputManager: Configured OutputManager instance
    """
    from utils.helpers import get_output_directory
    
    # Get user's preferred output directory
    output_dir = get_output_directory(user_settings)
    
    return OutputManager(output_dir)
