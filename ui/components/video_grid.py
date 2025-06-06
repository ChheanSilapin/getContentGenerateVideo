"""
Video Grid Component - Reusable video display grid with selection
Extracted from merge_video_tab.py for reusability
"""
from utils.common_imports import tk, threading

try:
    from PIL import Image, ImageTk
    from moviepy.editor import VideoFileClip
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class VideoGrid:
    """Reusable video grid component with thumbnails and selection"""
    
    def __init__(self, parent_canvas, main_gui):
        self.parent_canvas = parent_canvas
        self.main_gui = main_gui
        
        # Grid management
        self.photo_references = []
        self.video_vars = []
        self.video_paths = []
        
        # Threading for thumbnail loading
        self.thumbnail_thread = None
        self.thumbnail_stop_event = None
        
    def display_videos(self, video_paths, title_text="Videos"):
        """Display videos in a grid layout with thumbnails and checkboxes"""
        self.video_paths = video_paths
        self._create_video_display(video_paths, title_text)
        
    def _create_video_display(self, video_paths, title_text):
        """Create video display layout with checkboxes"""
        self.parent_canvas.delete("all")
        self.photo_references = []
        self.video_vars = []
        
        video_frame = tk.Frame(self.parent_canvas, bg="white")
        self.parent_canvas.create_window(0, 0, window=video_frame, anchor="nw")
        
        # Title
        title_label = tk.Label(
            video_frame,
            text=title_text,
            font=("Cascadia Code", 14, "bold"),
            bg="white",
            fg="#2c3e50",
            pady=10
        )
        title_label.pack(pady=(10, 20))
        
        # Video grid
        grid_frame = tk.Frame(video_frame, bg="white")
        grid_frame.pack(padx=20, pady=10)
        
        # Calculate grid dimensions
        videos_per_row = 4
        
        for i, video_path in enumerate(video_paths):
            row = i // videos_per_row
            col = i % videos_per_row
            
            self._create_video_item(grid_frame, video_path, row, col)
        
        # Update scroll region
        video_frame.update_idletasks()
        self.parent_canvas.configure(scrollregion=self.parent_canvas.bbox("all"))
    
    def _create_video_item(self, parent, video_path, row, col):
        """Create individual video item with thumbnail and checkbox"""
        item_frame = tk.Frame(parent, bg="white", relief="solid", borderwidth=1)
        item_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Thumbnail
        thumbnail_label = tk.Label(item_frame, text="Loading...", width=20, height=10, bg="#f0f0f0")
        thumbnail_label.pack(pady=5)
        
        # Video info
        filename = video_path.split('/')[-1] if '/' in video_path else video_path.split('\\')[-1]
        name_label = tk.Label(
            item_frame,
            text=filename[:25] + "..." if len(filename) > 25 else filename,
            font=("Cascadia Code", 8),
            bg="white",
            wraplength=160
        )
        name_label.pack(pady=2)
        
        # Checkbox for selection
        var = tk.BooleanVar(value=True)
        self.video_vars.append(var)
        
        checkbox = tk.Checkbutton(
            item_frame,
            text="Include",
            variable=var,
            font=("Cascadia Code", 8),
            bg="white",
            command=lambda: self._on_selection_change(var, video_path)
        )
        checkbox.pack(pady=5)
        
        # Start thumbnail loading
        self._load_thumbnail(video_path, thumbnail_label)
    
    def _load_thumbnail(self, video_path, thumbnail_label):
        """Load video thumbnail asynchronously"""
        if not PIL_AVAILABLE:
            thumbnail_label.config(text="No Preview\nAvailable")
            return
            
        def load_thumb():
            try:
                thumbnail = self._create_video_thumbnail(video_path)
                if thumbnail:
                    # Update UI in main thread
                    self.main_gui.root.after(0, lambda: self._update_thumbnail_ui(thumbnail_label, thumbnail))
                else:
                    self.main_gui.root.after(0, lambda: thumbnail_label.config(text="Preview\nUnavailable"))
            except Exception as e:
                self.main_gui.root.after(0, lambda: thumbnail_label.config(text="Error\nLoading"))
        
        # Run in background thread
        threading.Thread(target=load_thumb, daemon=True).start()
    
    def _create_video_thumbnail(self, video_path):
        """Create thumbnail from video file"""
        if not PIL_AVAILABLE:
            return None
            
        try:
            with VideoFileClip(video_path) as clip:
                # Get frame at 10% of video duration or 1 second, whichever is smaller
                timestamp = min(clip.duration * 0.1, 1.0) if clip.duration > 1 else 0
                frame = clip.get_frame(timestamp)
                
                # Convert to PIL Image
                pil_image = Image.fromarray(frame)
                
                # Resize for thumbnail
                pil_image.thumbnail((150, 100), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)
                self.photo_references.append(photo)
                return photo
                
        except Exception as e:
            print(f"Error creating thumbnail for {video_path}: {e}")
            return None
    
    def _update_thumbnail_ui(self, thumbnail_label, photo):
        """Update thumbnail in UI thread"""
        thumbnail_label.config(image=photo, text="")
        thumbnail_label.image = photo  # Keep reference
    
    def _on_selection_change(self, var, video_path):
        """Handle video selection change"""
        if hasattr(self.main_gui, 'update_duration_display'):
            self.main_gui.update_duration_display()
    
    def get_selected_videos(self):
        """Get list of selected video paths"""
        selected = []
        for i, var in enumerate(self.video_vars):
            if var.get() and i < len(self.video_paths):
                selected.append(self.video_paths[i])
        return selected
    
    def select_all(self, select=True):
        """Select or deselect all videos"""
        for var in self.video_vars:
            var.set(select)
        if hasattr(self.main_gui, 'update_duration_display'):
            self.main_gui.update_duration_display()
    
    def clear_grid(self):
        """Clear the video grid"""
        self.parent_canvas.delete("all")
        self.photo_references = []
        self.video_vars = []
        self.video_paths = [] 