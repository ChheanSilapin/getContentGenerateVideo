"""
Base Tab Component - Shared functionality for Image and Video tabs
Provides common UI setup, scrolling, entry management, and settings handling
"""
import tkinter as tk
from tkinter import ttk
from config import GUI_FONTS


class BaseTab:
    """Base class with shared tab functionality"""

    # Maximum entries to prevent memory issues
    MAX_ENTRIES = 50
    MAX_GROUPS = 20

    def __init__(self, parent_frame, main_gui, tab_name):
        """
        Initialize base tab functionality
        
        Args:
            parent_frame: The parent frame to contain this tab
            main_gui: Reference to the main GUI instance
            tab_name: Name of the tab ('image_tab' or 'video_tab')
        """
        self.parent_frame = parent_frame
        self.main_gui = main_gui
        self.tab_name = tab_name

        # Entry management
        self.entries = {}  # Generic entries dict
        self.group_entries = {}
        self.next_entry_id = 1
        self.next_group_id = 1
        self.current_mode = "individual"

        # Batch loading state (prevents excessive UI updates)
        self._is_batch_loading = False

        # UI components (to be set by subclass)
        self.scroll_canvas = None
        self.scrollable_frame = None
        self.entries_frame = None
        self.empty_state_frame = None
        self.progress_bar = None
        self.progress_label = None
        self.generate_button = None
        self.stop_button = None
        self.settings_info_label = None

    def setup_scrollable_area(self, parent, title="📁 Entries", 
                               add_content_callback=None,
                               settings_callback=None):
        """Set up scrollable area for entries"""
        # Entries section header
        entries_header = ttk.Frame(parent)
        entries_header.pack(fill="x", pady=(0, 10))

        entries_title = ttk.Label(
            entries_header,
            text=title,
            font=GUI_FONTS["heading"]
        )
        entries_title.pack(side="left")

        # Settings button (rightmost)
        if settings_callback:
            settings_button = self.main_gui.ui_factory.create_icon_button(
                entries_header, "⚙️", settings_callback,
                width=5
            )
            settings_button.pack(side="right", padx=(0, 4))

        # Add Content dropdown
        if add_content_callback and hasattr(self, 'create_content_dropdown'):
            self.create_content_dropdown(entries_header)

        # Create canvas and scrollbar
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.scroll_canvas = tk.Canvas(
            canvas_frame,
            height=120,
            bg="#f0f0f0",
            highlightthickness=1,
            highlightbackground="#e1e8ed",
            relief="solid",
            borderwidth=1
        )

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", 
                                   command=self.scroll_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.scroll_canvas, style="Card.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.scroll_canvas.configure(
                scrollregion=self.scroll_canvas.bbox("all")
            )
        )

        canvas_window = self.scroll_canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)

        def configure_scroll_region(event):
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
            self.scroll_canvas.itemconfig(canvas_window, width=event.width)

        self.scroll_canvas.bind('<Configure>', configure_scroll_region)
        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        self.scroll_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Store reference
        self.entries_frame = self.scrollable_frame

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def show_empty_state(self, icon="📁", title="Add content to start", 
                          instructions=None):
        """Show empty state with instructions"""
        if self.empty_state_frame:
            return

        self.empty_state_frame = ttk.Frame(self.entries_frame)
        self.empty_state_frame.pack(fill="both", expand=True, padx=20, pady=40)

        center_frame = ttk.Frame(self.empty_state_frame)
        center_frame.pack(expand=True)

        icon_label = ttk.Label(center_frame, text=icon, font=("Cascadia Code", 48))
        icon_label.pack(pady=(0, 10))

        title_label = ttk.Label(
            center_frame,
            text=title,
            font=("Cascadia Code", 14, "bold"),
            foreground="#333333"
        )
        title_label.pack(pady=(0, 20))

        if instructions:
            for instruction in instructions:
                label = ttk.Label(
                    center_frame,
                    text=instruction,
                    font=("Cascadia Code", 10),
                    foreground="#666666"
                )
                label.pack(anchor="w", pady=2)

    def hide_empty_state(self):
        """Hide empty state when entries are added"""
        if self.empty_state_frame:
            self.empty_state_frame.destroy()
            self.empty_state_frame = None

    def setup_action_buttons(self, parent, generate_callback, stop_callback,
                              generate_text="Generate All", generate_icon="🚀"):
        """Set up action buttons"""
        button_container = ttk.Frame(parent)
        button_container.pack(fill="x", pady=(0, 5))

        left_buttons = ttk.Frame(button_container)
        left_buttons.pack(side="left", fill="x", expand=True)

        self.generate_button = self.main_gui.ui_factory.create_icon_button(
            left_buttons, generate_text, generate_callback,
            icon=generate_icon, width=25
        )
        self.generate_button.pack(side="left")

        right_buttons = ttk.Frame(button_container)
        right_buttons.pack(side="right")

        self.stop_button = self.main_gui.ui_factory.create_icon_button(
            right_buttons, "Stop", stop_callback,
            icon="⏹️", state="disabled", width=12
        )
        self.stop_button.pack(side="right")

    def setup_settings_section(self, parent, default_text=""):
        """Set up compact settings section"""
        settings_row = ttk.Frame(parent)
        settings_row.pack(fill="x", pady=(0, 8))

        self.settings_info_label = ttk.Label(
            settings_row,
            text=default_text,
            font=GUI_FONTS["small"],
            foreground="#7f8c8d"
        )
        self.settings_info_label.pack(side="left", anchor="w")

    def update_scroll_region(self):
        """Update scroll region after entry changes"""
        if not self._is_batch_loading:
            self.scrollable_frame.update_idletasks()
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def clear_all_entries(self):
        """Clear all entries (both individual and grouped)"""
        # Remove all individual entries
        for entry_id in list(self.entries.keys()):
            if hasattr(self.entries[entry_id], 'destroy'):
                self.entries[entry_id].destroy()

        # Remove all group entries
        for group_id in list(self.group_entries.keys()):
            if hasattr(self.group_entries[group_id], 'destroy'):
                self.group_entries[group_id].destroy()

        # Clear dictionaries
        self.entries.clear()
        self.group_entries.clear()
        self.next_entry_id = 1
        self.next_group_id = 1
        self.current_mode = "individual"

        self.update_scroll_region()

    def get_valid_entries(self):
        """Get all valid entries (individual or grouped)"""
        if self.current_mode == "grouped":
            return self.get_valid_groups()
        else:
            return self.get_valid_individual_entries()

    def get_valid_individual_entries(self):
        """Get all valid individual entries"""
        valid_entries = []
        for entry_id, entry in self.entries.items():
            if hasattr(entry, 'is_valid') and entry.is_valid():
                valid_entries.append(entry.get_data())
        return valid_entries

    def get_valid_groups(self):
        """Get all valid group entries"""
        valid_groups = []
        for group_id, group_entry in self.group_entries.items():
            if hasattr(group_entry, 'is_valid') and group_entry.is_valid():
                valid_groups.append(group_entry.get_group_data())
        return valid_groups

    def check_entry_limit(self):
        """Check if entry limit is reached"""
        if len(self.entries) >= self.MAX_ENTRIES:
            if not self._is_batch_loading:
                self.main_gui.log(
                    f"⚠️ Maximum entries ({self.MAX_ENTRIES}) reached. "
                    "Remove some entries first."
                )
            return True
        return False

    def update_progress(self, value, message=None):
        """Update progress bar and label"""
        if self.progress_bar:
            self.progress_bar["value"] = value
        if self.progress_label and message:
            self.progress_label.config(text=message)
        elif self.progress_label:
            self.progress_label.config(text=f"{value}%")

    def reset_ui(self):
        """Reset UI after generation completes"""
        if self.generate_button:
            self.generate_button.config(state="normal")
        if self.stop_button:
            self.stop_button.config(state="disabled")
