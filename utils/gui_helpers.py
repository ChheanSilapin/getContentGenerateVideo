"""
GUI Helper Functions for Video Generator
Provides common GUI utilities and helper functions
"""
import config
import threading

class HoverEffect:
    def __init__(self, widget, hover_bg, normal_bg=None):
        self.widget = widget
        self.hover_bg = hover_bg
        # Use current bg if normal_bg is not specified
        self.normal_bg = normal_bg or widget.cget("background")
        self._bind_events()

    def _bind_events(self):
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        self.widget.config(bg=self.hover_bg)

    def _on_leave(self, event):
        self.widget.config(bg=self.normal_bg)


def apply_hover_to_widgets(widgets, hover_color, normal_color=None):
    for widget in widgets:
        HoverEffect(widget, hover_color, normal_color)


def standardize_progress_update(progress_bar, progress_label, value, message=None):
    """
    Standardized progress update function for consistent UI behavior

    Args:
        progress_bar: Progress bar widget to update
        progress_label: Label widget to update with text
        value: Progress value (0-100)
        message: Optional message to display

    Returns:
        None
    """
    if progress_bar:
        progress_bar["value"] = value

    if progress_label:
        # Get display mode from config
        display_mode = getattr(config, 'PROGRESS_DISPLAY_MODE', 'descriptive')
        percentage = int(round(value))

        if display_mode == "percentage":
            # Always show just percentage
            progress_label.config(text=f"{percentage}%")
        elif display_mode == "both":
            # Show both percentage and message
            if message:
                progress_label.config(text=f"{percentage}% - {message}")
            else:
                progress_label.config(text=f"{percentage}%")
        else:  # descriptive (default)
            # Show descriptive messages when available, percentage otherwise
            if message:
                progress_label.config(text=message)
            else:
                progress_label.config(text=f"{percentage}%")


def create_progress_callback(progress_bar, progress_label):
    """
    Create a standardized progress callback function

    Args:
        progress_bar: Progress bar widget
        progress_label: Label widget

    Returns:
        function: Progress callback function
    """
    def progress_callback(progress, message="Processing..."):
        standardize_progress_update(progress_bar, progress_label, progress, message)

    return progress_callback


class ThreadManager:
    """
    Utility class for managing threads with stop events and cleanup
    """

    def __init__(self):
        self.current_thread = None
        self.stop_event = None
        self.is_active = False

    def start_thread(self, target_function, *args, **kwargs):
        """
        Start a new thread with stop event management

        Args:
            target_function: Function to run in thread
            *args: Arguments for target function
            **kwargs: Keyword arguments for target function

        Returns:
            threading.Event: Stop event for the thread
        """
        # Stop any existing thread
        self.stop_current_thread()

        # Create new stop event
        self.stop_event = threading.Event()

        # Create and start new thread
        self.current_thread = threading.Thread(
            target=target_function,
            args=args + (self.stop_event,),
            kwargs=kwargs,
            daemon=True
        )

        self.current_thread.start()
        self.is_active = True

        return self.stop_event

    def stop_current_thread(self):
        """Stop the current thread if running"""
        if self.stop_event:
            self.stop_event.set()

        if self.current_thread and self.current_thread.is_alive():
            # Give thread time to clean up
            self.current_thread.join(timeout=2.0)

        self.is_active = False

    def is_thread_active(self):
        """Check if a thread is currently active"""
        return self.is_active and self.current_thread and self.current_thread.is_alive()
