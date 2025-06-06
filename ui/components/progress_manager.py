"""
Progress Manager Component - Reusable progress tracking and display
Handles progress bars, status messages, and threading integration
"""
from utils.common_imports import tk, ttk, threading

class ProgressManager:
    """Manages progress bars and status updates with threading support"""
    
    def __init__(self, progress_bar=None, progress_label=None, main_gui=None):
        self.progress_bar = progress_bar
        self.progress_label = progress_label
        self.main_gui = main_gui
        
        # Threading support
        self.current_thread = None
        self.stop_event = None
        
        # State tracking
        self.is_active = False
        self.current_operation = ""
        
    def create_progress_section(self, parent, title="Progress"):
        """Create a standard progress section with bar and label"""
        progress_frame = ttk.LabelFrame(parent, text=title, padding=10)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill="x", pady=(0, 5))
        
        # Progress label
        self.progress_label = ttk.Label(
            progress_frame,
            text="Ready",
            font=("Cascadia Code", 9)
        )
        self.progress_label.pack(fill="x")
        
        return progress_frame
    
    def start_operation(self, operation_name, target_function, *args, **kwargs):
        """Start a threaded operation with progress tracking"""
        if self.is_active:
            self.stop_current_operation()
        
        self.current_operation = operation_name
        self.is_active = True
        self.stop_event = threading.Event()
        
        # Reset progress
        self.update_progress(0, f"Starting {operation_name}...")
        
        # Start thread
        self.current_thread = threading.Thread(
            target=self._run_with_progress,
            args=(target_function, args, kwargs),
            daemon=True
        )
        self.current_thread.start()
    
    def _run_with_progress(self, target_function, args, kwargs):
        """Run the target function with progress tracking"""
        try:
            # Add progress callback to kwargs if not present
            if 'progress_callback' not in kwargs:
                kwargs['progress_callback'] = self.update_progress
            
            # Add stop event if not present
            if 'stop_event' not in kwargs:
                kwargs['stop_event'] = self.stop_event
            
            # Execute the target function
            result = target_function(*args, **kwargs)
            
            # Handle successful completion
            if not self.stop_event.is_set():
                self.operation_complete(result)
            else:
                self.operation_cancelled()
                
        except Exception as e:
            self.operation_failed(str(e))
        finally:
            self.is_active = False
    
    def update_progress(self, value, message=None):
        """Update progress bar and label (thread-safe)"""
        def _update():
            if self.progress_bar:
                self.progress_bar['value'] = value
            
            if self.progress_label and message:
                self.progress_label.config(text=message)
            
            # Update the GUI
            if self.main_gui and hasattr(self.main_gui, 'root'):
                self.main_gui.root.update_idletasks()
        
        # Ensure UI updates happen in main thread
        if self.main_gui and hasattr(self.main_gui, 'root'):
            self.main_gui.root.after(0, _update)
        else:
            _update()
    
    def stop_current_operation(self):
        """Stop the current operation"""
        if self.stop_event:
            self.stop_event.set()
        
        if self.current_thread and self.current_thread.is_alive():
            # Give thread time to clean up
            self.current_thread.join(timeout=2.0)
        
        self.is_active = False
        self.update_progress(0, "Operation stopped")
    
    def operation_complete(self, result=None):
        """Handle successful operation completion"""
        self.update_progress(100, f"{self.current_operation} completed successfully")
        
        if self.main_gui and hasattr(self.main_gui, 'log'):
            self.main_gui.log(f"{self.current_operation} completed")
        
        # Call completion callback if provided
        if hasattr(self, 'completion_callback') and self.completion_callback:
            self.completion_callback(result)
    
    def operation_failed(self, error_message):
        """Handle operation failure"""
        self.update_progress(0, f"{self.current_operation} failed: {error_message}")
        
        if self.main_gui and hasattr(self.main_gui, 'log'):
            self.main_gui.log(f"{self.current_operation} failed: {error_message}")
        
        # Call failure callback if provided
        if hasattr(self, 'failure_callback') and self.failure_callback:
            self.failure_callback(error_message)
    
    def operation_cancelled(self):
        """Handle operation cancellation"""
        self.update_progress(0, f"{self.current_operation} cancelled")
        
        if self.main_gui and hasattr(self.main_gui, 'log'):
            self.main_gui.log(f"{self.current_operation} cancelled by user")
    
    def set_callbacks(self, completion_callback=None, failure_callback=None):
        """Set callbacks for operation completion and failure"""
        self.completion_callback = completion_callback
        self.failure_callback = failure_callback
    
    def reset(self):
        """Reset progress manager to initial state"""
        self.stop_current_operation()
        self.update_progress(0, "Ready")
        self.current_operation = ""
    
    def is_operation_active(self):
        """Check if an operation is currently active"""
        return self.is_active
    
    def get_current_operation(self):
        """Get the name of the current operation"""
        return self.current_operation if self.is_active else None 