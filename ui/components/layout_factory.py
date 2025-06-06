"""
Layout Factory Component - Standardized layout creation
Creates consistent layouts, frames, and sections across the application
"""
from utils.common_imports import tk, ttk

class LayoutFactory:
    """Factory for creating standardized layouts and sections"""
    
    # Standard section styles
    SECTION_STYLES = {
        'header': {
            'padding': (10, 5),
            'relief': 'flat',
            'font': ('Cascadia Code', 14, 'bold'),
            'fg': '#2c3e50'
        },
        'content': {
            'padding': (10, 10),
            'relief': 'flat'
        },
        'controls': {
            'padding': (5, 5),
            'relief': 'flat'
        },
        'status': {
            'padding': (5, 2),
            'relief': 'sunken',
            'font': ('Cascadia Code', 8)
        }
    }
    
    @classmethod
    def create_main_layout(cls, parent, title):
        """Create a standard main layout for tabs
        
        Args:
            parent: Parent widget
            title: Tab title
        
        Returns:
            dict: Layout components
        """
        # Main container
        main_frame = ttk.Frame(parent, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Header section
        header_frame = cls.create_header_section(main_frame, title)
        
        # Content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(5, 0))
        
        return {
            'main': main_frame,
            'header': header_frame,
            'content': content_frame
        }
    
    @classmethod
    def create_header_section(cls, parent, title, subtitle=None):
        """Create a standardized header section
        
        Args:
            parent: Parent widget
            title: Main title text
            subtitle: Optional subtitle text
        
        Returns:
            ttk.Frame: Header frame
        """
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        # Main title
        title_label = ttk.Label(
            header_frame, 
            text=title, 
            font=("Cascadia Code", 14, "bold")
        )
        title_label.pack(side="left")
        
        # Optional subtitle
        if subtitle:
            subtitle_label = ttk.Label(
                header_frame,
                text=subtitle,
                font=("Cascadia Code", 10),
                foreground="#666666"
            )
            subtitle_label.pack(side="left", padx=(10, 0))
        
        return header_frame
    
    @classmethod
    def create_toolbar_section(cls, parent):
        """Create a toolbar section
        
        Args:
            parent: Parent widget
        
        Returns:
            ttk.Frame: Toolbar frame
        """
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill="x", padx=5, pady=5)
        
        return toolbar_frame
    
    @classmethod
    def create_content_with_sidebar(cls, parent, sidebar_width=250):
        """Create content area with sidebar
        
        Args:
            parent: Parent widget
            sidebar_width: Width of sidebar in pixels
        
        Returns:
            dict: Content and sidebar frames
        """
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Sidebar
        sidebar = ttk.Frame(container, width=sidebar_width)
        sidebar.pack(side="left", fill="y", padx=(0, 5))
        sidebar.pack_propagate(False)
        
        # Main content
        content = ttk.Frame(container)
        content.pack(side="left", fill="both", expand=True)
        
        return {
            'container': container,
            'sidebar': sidebar,
            'content': content
        }
    
    @classmethod
    def create_scrollable_area(cls, parent):
        """Create a scrollable content area
        
        Args:
            parent: Parent widget
        
        Returns:
            dict: Scrollable components
        """
        # Container frame
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Canvas for scrolling
        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Configure scrolling
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Scrollable frame
        scrollable_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window(0, 0, window=scrollable_frame, anchor="nw")
        
        # Update scroll region when frame changes
        def update_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Bind events
        scrollable_frame.bind("<Configure>", update_scrollregion)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        return {
            'container': container,
            'canvas': canvas,
            'scrollbar': scrollbar,
            'content': scrollable_frame
        }
    
    @classmethod
    def create_status_bar(cls, parent):
        """Create a status bar
        
        Args:
            parent: Parent widget
        
        Returns:
            dict: Status bar components
        """
        status_frame = ttk.Frame(parent, relief="sunken", borderwidth=1)
        status_frame.pack(fill="x", side="bottom", pady=(5, 0))
        
        # Status label
        status_label = ttk.Label(
            status_frame,
            text="Ready",
            font=("Cascadia Code", 8),
            padding=(5, 2)
        )
        status_label.pack(side="left")
        
        # Progress indicator (optional)
        progress_label = ttk.Label(
            status_frame,
            text="",
            font=("Cascadia Code", 8),
            padding=(5, 2)
        )
        progress_label.pack(side="right")
        
        return {
            'frame': status_frame,
            'status': status_label,
            'progress': progress_label
        }
    
    @classmethod
    def create_two_column_layout(cls, parent, left_weight=1, right_weight=1):
        """Create a two-column layout
        
        Args:
            parent: Parent widget
            left_weight: Weight for left column
            right_weight: Weight for right column
        
        Returns:
            dict: Column frames
        """
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure columns
        container.grid_columnconfigure(0, weight=left_weight)
        container.grid_columnconfigure(1, weight=right_weight)
        
        # Left column
        left_frame = ttk.Frame(container)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Right column
        right_frame = ttk.Frame(container)
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        return {
            'container': container,
            'left': left_frame,
            'right': right_frame
        }
    
    @classmethod
    def create_settings_section(cls, parent, title, settings_dict):
        """Create a settings section with labels and controls
        
        Args:
            parent: Parent widget
            title: Section title
            settings_dict: Dict of setting name -> control widget
        
        Returns:
            ttk.LabelFrame: Settings frame
        """
        settings_frame = ttk.LabelFrame(parent, text=title, padding=10)
        
        row = 0
        for setting_name, control_widget in settings_dict.items():
            # Label
            label = ttk.Label(settings_frame, text=f"{setting_name}:")
            label.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=2)
            
            # Control
            control_widget.grid(row=row, column=1, sticky="ew", pady=2)
            
            row += 1
        
        # Configure column weights
        settings_frame.grid_columnconfigure(1, weight=1)
        
        return settings_frame
    
    @classmethod
    def create_tabbed_interface(cls, parent):
        """Create a tabbed interface
        
        Args:
            parent: Parent widget
        
        Returns:
            ttk.Notebook: Notebook widget
        """
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        return notebook
    
    @classmethod
    def create_file_drop_area(cls, parent, text="Drop files here or click to browse"):
        """Create a file drop area
        
        Args:
            parent: Parent widget
            text: Display text
        
        Returns:
            dict: Drop area components
        """
        # Drop area frame
        drop_frame = ttk.Frame(parent, relief="solid", borderwidth=2)
        drop_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Drop label
        drop_label = ttk.Label(
            drop_frame,
            text=text,
            font=("Cascadia Code", 10),
            foreground="#666666",
            justify="center"
        )
        drop_label.pack(expand=True, fill="both", padx=20, pady=20)
        
        return {
            'frame': drop_frame,
            'label': drop_label
        } 