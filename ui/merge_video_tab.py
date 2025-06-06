"""
Merge Video Tab - Streamlined using factory components
Now using ButtonFactory and LayoutFactory for maximum code reuse
"""
from utils.common_imports import os, tk, ttk, messagebox, filedialog, threading

# Import our new components and factories
from ui.components import VideoGrid, VideoLoader, ProgressManager, ButtonFactory, LayoutFactory

# Import service layer
from services.merge_service import VideoService

class MergeVideoTab:
    """Ultra-streamlined merge video tab using factory architecture"""
    
    def __init__(self, parent_frame, main_gui):
        self.parent_frame = parent_frame
        self.main_gui = main_gui
        
        # Core data
        self.selected_videos = []
        
        # UI Components will be created by factories
        self.video_canvas = None
        self.duration_label = None
        
        # Component instances
        self.video_grid = None
        self.video_loader = None
        self.progress_manager = None
        
        # UI controls (managed by factories)
        self.buttons = {}
        self.layout = {}
        
        # Threading
        self.merge_thread = None
        self.stop_event = None
        
        self.setup_merge_tab()

    def setup_merge_tab(self):
        """Set up the merge video tab using factory components"""
        # Create main layout using factory
        self.layout = LayoutFactory.create_main_layout(self.parent_frame, "Video Merger")
        
        # Create button toolbars using factory
        self._create_toolbars()
        
        # Create progress section
        self._create_progress_section()
        
        # Create video display area
        self._create_video_display_area()
        
        # Create control section
        self._create_control_section()
        
        # Initialize components
        self._initialize_components()

    def _create_toolbars(self):
        """Create toolbars using ButtonFactory"""
        toolbar_container = LayoutFactory.create_toolbar_section(self.layout['content'])
        
        # File operations toolbar
        file_toolbar, file_buttons = ButtonFactory.create_file_operations_toolbar(
            toolbar_container,
            {
                'add_files': self.add_videos,
                'clear_all': self.clear_all_videos,
                'remove_selected': self.remove_selected_videos
            }
        )
        file_toolbar.pack(side="left")
        self.buttons.update(file_buttons)
        
        # Validation checkbox (custom)
        self.validate_var = tk.BooleanVar(value=True)
        validate_cb = tk.Checkbutton(
            toolbar_container, 
            text="Validate Compatibility",  
            variable=self.validate_var,
            font=("Cascadia Code", 9),
            bg="#ffffff",
            fg="#333333"
        )
        validate_cb.pack(side="left", padx=15)
        
        # Process controls toolbar
        process_toolbar, process_buttons = ButtonFactory.create_process_toolbar(
            toolbar_container,
            {
                'start_process': self.merge_videos,
                'stop_process': self.stop_merge
            },
            process_text="Merge Videos",
            stop_text="Stop"
        )
        process_toolbar.pack(side="right")
        self.buttons.update(process_buttons)

    def _create_progress_section(self):
        """Create progress section using ProgressManager"""
        self.progress_manager = ProgressManager(main_gui=self.main_gui)
        progress_frame = self.progress_manager.create_progress_section(
            self.layout['content'], 
            "Video Processing Progress"
        )
        progress_frame.pack(fill="x", padx=5, pady=5)

    def _create_video_display_area(self):
        """Create video display area using LayoutFactory"""
        scrollable = LayoutFactory.create_scrollable_area(self.layout['content'])
        self.video_canvas = scrollable['canvas']

    def _create_control_section(self):
        """Create control section using ButtonFactory"""
        control_container = LayoutFactory.create_toolbar_section(self.layout['content'])
        
        # Selection controls
        selection_toolbar, selection_buttons = ButtonFactory.create_selection_toolbar(
            control_container,
            {
                'select_all': lambda: self.select_all_videos(True),
                'deselect_all': lambda: self.select_all_videos(False)
            }
        )
        selection_toolbar.pack(side="left")
        self.buttons.update(selection_buttons)
        
        # Duration display
        self.duration_label = ttk.Label(
            control_container, 
            text="Total Duration: --", 
            font=("Cascadia Code", 9)
        )
        self.duration_label.pack(side="left", padx=10)

    def _initialize_components(self):
        """Initialize component instances"""
        self.video_grid = VideoGrid(self.video_canvas, self.main_gui)
        self.video_loader = VideoLoader(self.main_gui)

    def add_videos(self):
        """Add videos using VideoLoader component"""
        new_files = self.video_loader.add_videos_from_dialog(self.selected_videos)
        
        if not new_files:
            return
        
        # Add to our list
        self.selected_videos.extend(new_files)
        
        # Load using component with progress tracking
        self.video_loader.start_loading(
            new_files, 
            progress_callback=self.progress_manager.update_progress
        )
        
        # Update display
        self.display_video_grid()

    def display_video_grid(self):
        """Display videos using VideoGrid component"""
        if not self.selected_videos:
            self.video_grid.clear_grid()
            return

        title_text = f"{len(self.selected_videos)} Videos Selected"
        self.video_grid.display_videos(self.selected_videos, title_text)
        self.update_duration_display()

    def get_selected_videos(self):
        """Get selected videos from grid component"""
        if self.video_grid:
            return self.video_grid.get_selected_videos()
        return []

    def select_all_videos(self, select=True):
        """Select/deselect all videos"""
        if self.video_grid:
            self.video_grid.select_all(select)
        self.update_duration_display()

    def remove_selected_videos(self):
        """Remove selected videos"""
        selected = self.get_selected_videos()
        
        if not selected:
            messagebox.showwarning("No Selection", "Please select videos to remove.")
            return
        
        # Remove from main list
        for video in selected:
            if video in self.selected_videos:
                self.selected_videos.remove(video)
        
        # Update display
        self.display_video_grid()
        self.main_gui.log(f"Removed {len(selected)} videos")

    def clear_all_videos(self):
        """Clear all videos"""
        if self.selected_videos:
            count = len(self.selected_videos)
            self.selected_videos.clear()
            self.video_grid.clear_grid()
            self.duration_label.config(text="Total Duration: --")
            self.main_gui.log(f"Cleared {count} videos")

    def update_duration_display(self):
        """Update duration display for selected videos"""
        selected = self.get_selected_videos()
        
        if not selected:
            self.duration_label.config(text="Total Duration: --")
            return
        
        # Update in background to avoid UI blocking
        def calculate_duration():
            try:
                # This would call the actual duration calculation
                # For now, just show count
                duration_text = f"Total Duration: {len(selected)} videos selected"
                self.main_gui.root.after(0, lambda: self.duration_label.config(text=duration_text))
            except Exception as e:
                self.main_gui.root.after(0, lambda: self.duration_label.config(text="Duration: Error calculating"))
        
        threading.Thread(target=calculate_duration, daemon=True).start()

    def merge_videos(self):
        """Start video merge process using ProgressManager"""
        selected = self.get_selected_videos()
        
        if len(selected) < 2:
            messagebox.showerror("Insufficient Videos", "Please select at least 2 videos to merge.")
            return
        
        # Get output path
        output_path = filedialog.asksaveasfilename(
            title="Save Merged Video As",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        
        if not output_path:
            return
        
        # Start merge using ProgressManager
        self.progress_manager.set_callbacks(
            completion_callback=self.merge_complete,
            failure_callback=self.merge_failed
        )
        
        self.progress_manager.start_operation(
            "Video Merge",
            self.process_merge,
            selected,
            output_path
        )
        
        # Update UI state using button references
        self.buttons['process'].config(state="disabled")
        self.buttons['stop'].config(state="normal")

    def process_merge(self, selected_videos, output_path, progress_callback=None, stop_event=None):
        """Process video merge using service layer"""
        try:
            # Use VideoService for actual merging
            service = VideoService()
            
            # Configure progress callback
            def service_progress(progress, message="Processing..."):
                if progress_callback:
                    progress_callback(progress, message)
            
            # Perform merge
            result = service.merge_videos(
                selected_videos, 
                output_path,
                progress_callback=service_progress,
                stop_event=stop_event,
                validate_compatibility=self.validate_var.get()
            )
            
            return result
            
        except Exception as e:
            raise Exception(f"Merge failed: {str(e)}")

    def merge_complete(self, result):
        """Handle successful merge completion"""
        self.buttons['process'].config(state="normal")
        self.buttons['stop'].config(state="disabled")
        
        if result:
            messagebox.showinfo("Success", f"Videos merged successfully!\n\nOutput: {result}")
            self.main_gui.log("Video merge completed successfully")
        else:
            self.merge_failed("Merge completed but output file not found")

    def merge_failed(self, error_message):
        """Handle merge failure"""
        self.buttons['process'].config(state="normal")
        self.buttons['stop'].config(state="disabled")
        
        messagebox.showerror("Merge Failed", f"Failed to merge videos:\n\n{error_message}")
        self.main_gui.log(f"Video merge failed: {error_message}")

    def stop_merge(self):
        """Stop the merge process"""
        if self.progress_manager.is_operation_active():
            self.progress_manager.stop_current_operation()
            self.buttons['process'].config(state="normal")
            self.buttons['stop'].config(state="disabled")
            self.main_gui.log("Video merge stopped by user")