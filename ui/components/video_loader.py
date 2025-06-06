"""
Video Loader Component - Handles threaded video loading and processing
Extracted from merge_video_tab.py for reusability
"""
from utils.common_imports import threading, time, os, filedialog

class VideoLoader:
    """Handles video file loading with threading and progress tracking"""
    
    def __init__(self, main_gui):
        self.main_gui = main_gui
        
        # Threading components
        self.loading_thread = None
        self.loading_stop_event = None
        self.is_loading = False
        
        # Progress tracking
        self.progress_callback = None
        
    def add_videos_from_dialog(self, existing_videos=None):
        """Show file dialog and add selected videos"""
        if existing_videos is None:
            existing_videos = []
            
        files = filedialog.askopenfilenames(
            title="Select Videos to Merge",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("MOV files", "*.mov"),
                ("All files", "*.*")
            ]
        )
        
        if not files:
            return []
        
        # Filter out duplicates
        new_files = []
        for file in files:
            if file not in existing_videos:
                new_files.append(file)
        
        if not new_files:
            self.main_gui.log("No new videos added (duplicates ignored)")
            return []
        
        return new_files
    
    def start_loading(self, new_files, progress_callback=None):
        """Start loading videos with appropriate strategy based on count"""
        self.progress_callback = progress_callback
        
        if len(new_files) >= 10:
            self.main_gui.log(f"Loading {len(new_files)} videos with optimized processing...")
            self._start_optimized_loading(new_files)
        else:
            self.main_gui.log(f"Loading {len(new_files)} videos...")
            self._start_fast_loading(new_files)
    
    def _start_optimized_loading(self, new_files):
        """Start optimized loading for large numbers of videos"""
        if self.is_loading:
            return
        
        self.is_loading = True
        self.loading_stop_event = threading.Event()
        
        self.loading_thread = threading.Thread(
            target=self._process_optimized_loading,
            args=(new_files,),
            daemon=True
        )
        self.loading_thread.start()
    
    def _start_fast_loading(self, new_files):
        """Start fast loading for small numbers of videos"""
        if self.is_loading:
            return
        
        self.is_loading = True
        self.loading_stop_event = threading.Event()
        
        self.loading_thread = threading.Thread(
            target=self._process_fast_loading,
            args=(new_files,),
            daemon=True
        )
        self.loading_thread.start()
    
    def _process_optimized_loading(self, new_files):
        """Process videos with optimized loading strategy"""
        try:
            total_files = len(new_files)
            
            def progress_callback(progress, message):
                if self.progress_callback:
                    self.main_gui.root.after(0, lambda: self.progress_callback(progress, message))
            
            # Phase 1: Quick validation (20% of progress)
            progress_callback(10, "Validating video files...")
            valid_files = []
            
            for i, video_path in enumerate(new_files):
                if self.loading_stop_event.is_set():
                    return
                
                if self._validate_video_file(video_path):
                    valid_files.append(video_path)
                
                # Update progress for validation phase
                validation_progress = 10 + (i + 1) / total_files * 20
                progress_callback(validation_progress, f"Validating {i + 1}/{total_files} videos...")
            
            # Phase 2: Create placeholders (50% of progress)
            progress_callback(30, "Creating video grid...")
            self.main_gui.root.after(0, lambda: self._create_placeholders_ui(valid_files))
            progress_callback(50, "Grid created, loading thumbnails...")
            
            # Phase 3: Load thumbnails progressively (remaining 50%)
            self._load_thumbnails_progressively(valid_files, progress_callback, 50, 100)
            
            # Finalize
            self.main_gui.root.after(0, lambda: self._finalize_loading(len(valid_files)))
            
        except Exception as e:
            self.main_gui.root.after(0, lambda: self._loading_failed(str(e)))
        finally:
            self.is_loading = False
    
    def _process_fast_loading(self, new_files):
        """Process videos with fast loading strategy"""
        try:
            total_files = len(new_files)
            
            def progress_callback(progress, message):
                if self.progress_callback:
                    self.main_gui.root.after(0, lambda: self.progress_callback(progress, message))
            
            # Validate and load all at once
            valid_files = []
            
            for i, video_path in enumerate(new_files):
                if self.loading_stop_event.is_set():
                    return
                
                if self._validate_video_file(video_path):
                    valid_files.append(video_path)
                
                # Update progress
                loading_progress = (i + 1) / total_files * 90
                progress_callback(loading_progress, f"Processing {i + 1}/{total_files} videos...")
            
            # Create display
            progress_callback(95, "Creating video display...")
            self.main_gui.root.after(0, lambda: self._create_display_ui(valid_files))
            
            # Finalize
            self.main_gui.root.after(0, lambda: self._finalize_loading(len(valid_files)))
            
        except Exception as e:
            self.main_gui.root.after(0, lambda: self._loading_failed(str(e)))
        finally:
            self.is_loading = False
    
    def _validate_video_file(self, video_path):
        """Validate that a video file is accessible and not corrupted"""
        try:
            if not os.path.exists(video_path):
                return False
            
            # Check file size
            if os.path.getsize(video_path) < 1024:  # Less than 1KB
                return False
            
            # Basic extension check
            valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
            ext = os.path.splitext(video_path)[1].lower()
            
            return ext in valid_extensions
            
        except Exception:
            return False
    
    def _load_thumbnails_progressively(self, valid_files, progress_callback, start_progress, end_progress):
        """Load thumbnails progressively to avoid UI blocking"""
        total_files = len(valid_files)
        progress_range = end_progress - start_progress
        
        for i, video_path in enumerate(valid_files):
            if self.loading_stop_event.is_set():
                return
            
            # Load thumbnail in background
            self._load_single_thumbnail(video_path)
            
            # Update progress
            thumbnail_progress = start_progress + (i + 1) / total_files * progress_range
            progress_callback(thumbnail_progress, f"Loading thumbnail {i + 1}/{total_files}...")
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.1)
    
    def _load_single_thumbnail(self, video_path):
        """Load a single thumbnail (placeholder for actual implementation)"""
        # This would be implemented by the calling component
        # that has access to the UI elements
        pass
    
    def _create_placeholders_ui(self, valid_files):
        """Create UI placeholders (to be implemented by caller)"""
        pass
    
    def _create_display_ui(self, valid_files):
        """Create the display UI (to be implemented by caller)"""
        pass
    
    def _finalize_loading(self, total_videos):
        """Finalize the loading process"""
        if self.progress_callback:
            self.progress_callback(100, f"Loaded {total_videos} videos successfully")
        
        self.main_gui.log(f"Successfully loaded {total_videos} videos")
    
    def _loading_failed(self, error_message):
        """Handle loading failure"""
        if self.progress_callback:
            self.progress_callback(0, f"Loading failed: {error_message}")
        
        self.main_gui.log(f"Video loading failed: {error_message}")
    
    def stop_loading(self):
        """Stop the current loading process"""
        if self.loading_stop_event:
            self.loading_stop_event.set()
        
        if self.loading_thread and self.loading_thread.is_alive():
            self.loading_thread.join(timeout=2.0)
        
        self.is_loading = False 