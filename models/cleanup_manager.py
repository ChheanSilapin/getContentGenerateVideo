"""
Cleanup Manager Component - Delegates to centralized OutputManager cleanup system
Simplified to eliminate duplication with OutputManager
"""
import os
from utils.output_manager import get_output_manager


class CleanupManager:
    """Delegates file cleanup operations to centralized OutputManager"""

    def __init__(self):
        self._output_manager = None

    def _get_output_manager(self):
        """Get or create OutputManager instance"""
        if self._output_manager is None:
            self._output_manager = get_output_manager()
        return self._output_manager

    def cleanup_after_video_complete(self, output_dir, keep_debug_files=False):
        """
        Delegate to centralized OutputManager cleanup system

        Args:
            output_dir: Directory to clean up
            keep_debug_files: Whether to keep debug files

        Returns:
            int: Number of files cleaned up
        """
        output_manager = self._get_output_manager()
        return output_manager.cleanup_after_video_complete(output_dir, keep_debug_files)

    def cleanup_on_stop(self, output_dir):
        """Delegate to centralized OutputManager cleanup system"""
        output_manager = self._get_output_manager()
        return output_manager.cleanup_on_stop(output_dir)

    def cleanup_extracted_frames(self, images_dir):
        """Delegate to centralized OutputManager cleanup system"""
        output_manager = self._get_output_manager()
        return output_manager.cleanup_extracted_frames(images_dir)

    def organize_output_folder_during_generation(self, output_dir):
        """
        Organize the output folder DURING generation - keep all important files
        Only remove truly temporary files that are no longer needed
        """
        # Check if auto-cleanup is enabled before cleaning up during generation
        import config
        cleanup_enabled = getattr(config, 'AUTO_CLEANUP_AFTER_COMPLETION', True)

        if not cleanup_enabled:
            print(" Skipping during-generation cleanup (AUTO_CLEANUP_AFTER_COMPLETION = False)")
            return

        try:
            # Only clean up intermediate files that are definitely not needed anymore
            truly_temp_files = [
                os.path.join(output_dir, "slideshow_temp.mp4"),
                os.path.join(output_dir, "slideshow_enhanced_temp.mp4"),
                os.path.join(output_dir, "original_video_backup.mp4"),
                os.path.join(output_dir, "temp_audio.mp3"),
                os.path.join(output_dir, "temp_video.mp4"),
            ]

            # Use OutputManager for consistent cleanup
            output_manager = self._get_output_manager()
            cleaned_count = output_manager.cleanup_temp_files(*truly_temp_files)

            if cleaned_count > 0:
                print(f" Cleaned {cleaned_count} temporary files during generation")

        except Exception as e:
            print(f" Error organizing during generation: {e}")

