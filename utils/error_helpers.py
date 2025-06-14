"""
Error handling helper functions for the Video Generator application
Provides standardized error handling to eliminate duplication across UI components
"""

import traceback
from utils.common_imports import messagebox


def show_error_with_log(main_gui, title, message, exception=None, show_traceback=True):
    """
    Standardized error handling with logging and messagebox
    
    Args:
        main_gui: Main GUI instance for logging
        title: Error dialog title
        message: Error message to display
        exception: Optional exception object
        show_traceback: Whether to print traceback to console
        
    Returns:
        None
    """
    # Format the full error message
    if exception:
        full_message = f"{message}: {str(exception)}"
    else:
        full_message = message
    
    # Log the error
    if main_gui and hasattr(main_gui, 'log'):
        main_gui.log(f"ERROR: {full_message}")
    else:
        print(f"ERROR: {full_message}")
    
    # Show messagebox
    messagebox.showerror(title, full_message)
    
    # Print traceback if requested and exception exists
    if show_traceback and exception:
        traceback.print_exc()


def show_warning_with_log(main_gui, title, message):
    """
    Standardized warning handling with logging and messagebox
    
    Args:
        main_gui: Main GUI instance for logging
        title: Warning dialog title
        message: Warning message to display
        
    Returns:
        None
    """
    # Log the warning
    if main_gui and hasattr(main_gui, 'log'):
        main_gui.log(f"WARNING: {message}")
    else:
        print(f"WARNING: {message}")
    
    # Show messagebox
    messagebox.showwarning(title, message)


def show_info_with_log(main_gui, title, message):
    """
    Standardized info handling with logging and messagebox
    
    Args:
        main_gui: Main GUI instance for logging
        title: Info dialog title
        message: Info message to display
        
    Returns:
        None
    """
    # Log the info
    if main_gui and hasattr(main_gui, 'log'):
        main_gui.log(f"INFO: {message}")
    else:
        print(f"INFO: {message}")
    
    # Show messagebox
    messagebox.showinfo(title, message)


def handle_operation_error(main_gui, operation_name, exception, show_dialog=True):
    """
    Handle errors from operations with consistent formatting
    
    Args:
        main_gui: Main GUI instance for logging
        operation_name: Name of the operation that failed
        exception: Exception that occurred
        show_dialog: Whether to show error dialog
        
    Returns:
        None
    """
    error_message = f"{operation_name} failed"
    
    if show_dialog:
        show_error_with_log(main_gui, "Operation Failed", error_message, exception)
    else:
        # Just log without showing dialog
        if main_gui and hasattr(main_gui, 'log'):
            main_gui.log(f"ERROR: {error_message}: {str(exception)}")
        else:
            print(f"ERROR: {error_message}: {str(exception)}")
        
        traceback.print_exc()


def safe_operation(main_gui, operation_name, operation_func, *args, **kwargs):
    """
    Execute an operation with standardized error handling
    
    Args:
        main_gui: Main GUI instance for logging
        operation_name: Name of the operation
        operation_func: Function to execute
        *args: Arguments for the operation function
        **kwargs: Keyword arguments for the operation function
        
    Returns:
        tuple: (success: bool, result: any, error: Exception or None)
    """
    try:
        result = operation_func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        handle_operation_error(main_gui, operation_name, e, show_dialog=False)
        return False, None, e


def confirm_action(title, message, default_yes=False):
    """
    Show confirmation dialog with standardized formatting
    
    Args:
        title: Dialog title
        message: Confirmation message
        default_yes: Whether "Yes" should be the default button
        
    Returns:
        bool: True if user confirmed, False otherwise
    """
    return messagebox.askyesno(title, message, default='yes' if default_yes else 'no')
