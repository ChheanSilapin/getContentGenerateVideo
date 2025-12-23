#!/usr/bin/env python3
"""
Image Tab Component for Video Generator GUI
Handles folder-based image-to-video generation with multi-folder support
"""
import os

# Use centralized UI imports
import tkinter as tk
from tkinter import ttk, filedialog
import threading
from config import GUI_FONTS

from ui.components.settings_popup import show_settings_popup
from ui.components.group_entry import GroupEntry, SmartNotification
from utils.settings_manager import SettingsManager
from utils.folder_processor import FolderProcessor


class ImageTab:
    """Image tab component for multi-folder image-to-video generation"""

    # Maximum entries to prevent memory issues
    MAX_ENTRIES = 50
    MAX_GROUPS = 20

    def __init__(self, parent_frame, main_gui):
        """
        Initialize the image tab

        Args:
            parent_frame: The parent frame to contain this tab
            main_gui: Reference to the main GUI instance for callbacks and shared data
        """
        self.parent_frame = parent_frame
        self.main_gui = main_gui

        # Image entries management (similar to video tab)
        self.image_entries = {}  # Dictionary to store ImageEntry objects
        self.group_entries = {}  # Dictionary to store GroupEntry objects
        self.next_entry_id = 1
        self.next_group_id = 1
        self.current_mode = "individual"  # "individual" or "grouped"

        # Batch loading state (prevents excessive UI updates)
        self._is_batch_loading = False

        # Settings manager for persistence
        self.settings_manager = SettingsManager()

        # Settings popup and current settings (load from persistent storage)
        self.settings_popup = None
        self.current_settings = self.settings_manager.load_settings()

        # Sync settings with model when the application starts
        if hasattr(self.main_gui, 'model'):
            if 'output_folder' in self.current_settings:
                self.main_gui.model.output_folder = self.current_settings['output_folder']

        # Folder processing components
        self.folder_processor = FolderProcessor()
        self.folder_processor.set_logger(self.main_gui.log)

        # Progress manager for UI operations
        self.progress_manager = None

        # UI components
        self.image_progress_bar = None
        self.image_progress_label = None
        self.generate_button = None
        self.stop_button = None
        self.entries_frame = None
        self.scroll_canvas = None
        self.scrollable_frame = None
        self.settings_info_label = None

        # Set up the tab
        self.setup_image_tab()

    def setup_image_tab(self):
        """Set up the image tab with video-like functionality"""
        # Main container with scrolling
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Header section
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 15))

        # Title with icon-like styling
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(fill="x")

        title_label = ttk.Label(
            title_frame,
            text="Image-to-Video Generation",
            font=GUI_FONTS["heading"]
        )
        title_label.pack(anchor="w")

        # Settings control section - compact settings button
        self.setup_settings_section(main_frame)

        # Scrollable area for image entries
        self.setup_scrollable_area(main_frame)

        # Initialize progress manager
        from ui.components import ProgressManager
        self.progress_manager = ProgressManager(main_gui=self.main_gui)

        # Progress section with better styling using progress manager
        progress_frame = self.progress_manager.create_progress_section(
            main_frame, "⚡ Processing Progress"
        )
        progress_frame.pack(fill="x", pady=(0, 10))

        # Store references to progress bar and label
        self.image_progress_bar = self.progress_manager.progress_bar
        self.image_progress_label = self.progress_manager.progress_label

        # Action buttons with better layout
        self.setup_action_buttons(main_frame)

        # Start with empty state - no initial entries
        self.empty_state_frame = None
        self.show_empty_state()

    def show_empty_state(self):
        """Show empty state with instructions"""
        if self.empty_state_frame:
            return  # Already showing

        # Create empty state frame
        self.empty_state_frame = ttk.Frame(self.entries_frame)
        self.empty_state_frame.pack(fill="both", expand=True, padx=20, pady=40)

        # Center container
        center_frame = ttk.Frame(self.empty_state_frame)
        center_frame.pack(expand=True)

        # Icon and title
        icon_label = ttk.Label(center_frame, text="📁", font=("Cascadia Code", 48))
        icon_label.pack(pady=(0, 10))

        title_label = ttk.Label(
            center_frame,
            text="Add images to start creating videos",
            font=("Cascadia Code", 14, "bold"),
            foreground="#333333"
        )
        title_label.pack(pady=(0, 20))

        # Instructions
        instructions = [
            "Step 1: Click 'Add Content ▾' above",
            "Step 2: Choose your content source:",
            "   • Add Folder - Import image folders",
            "   • Add Files - Pick individual image files",
            "Step 3: Add text prompts for each entry",
            "Step 4: Click 'Generate All Videos' to start"
        ]

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

    def setup_settings_section(self, parent):
        """Set up compact settings section"""
        # Settings control row
        settings_row = ttk.Frame(parent)
        settings_row.pack(fill="x", pady=(0, 8))

        # Settings info label
        self.settings_info_label = ttk.Label(
            settings_row,
            text="TTS: Default Voice, 1.0x Speed, Neutral | Output: Default Folder",
            font=GUI_FONTS["small"],
            foreground="#7f8c8d"
        )
        self.settings_info_label.pack(side="left", anchor="w")

        # Update info label with current settings
        self._update_settings_info_label()

        # Refresh settings from file to ensure sync
        self._refresh_settings_from_file()

    def setup_scrollable_area(self, parent):
        """Set up scrollable area for image entries"""
        # Image entries section header
        entries_header = ttk.Frame(parent)
        entries_header.pack(fill="x", pady=(0, 10))

        entries_title = ttk.Label(
            entries_header,
            text="🖼️ Entries",
            font=GUI_FONTS["heading"]
        )
        entries_title.pack(side="left")

        # Settings button (rightmost)
        settings_button = self.main_gui.ui_factory.create_icon_button(
            entries_header, "⚙️", self._show_settings_popup,
            width=5
        )
        settings_button.pack(side="right", padx=(0, 4))

        # Add Content dropdown button with enhanced options
        from ui.components.dropdown_menu import create_image_content_dropdown
        self.content_dropdown = create_image_content_dropdown(
            entries_header,
            load_folder_command=self.load_images_from_folder,
            select_multiple_command=self.select_multiple_images,
            import_url_command=self.import_from_url,
            width=20
        )
        self.content_dropdown.pack(side="right", padx=(0, 4))

        # Create canvas and scrollbar with better styling
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Canvas with better styling - smaller height for compact fit
        self.scroll_canvas = tk.Canvas(
            canvas_frame,
            height=120,
            bg="#f0f0f0",
            highlightthickness=1,
            highlightbackground="#e1e8ed",
            relief="solid",
            borderwidth=1
        )

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.scroll_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.scroll_canvas, style="Card.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        )

        # Create window and configure it to fill the canvas width
        canvas_window = self.scroll_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)

        # Bind canvas resize to update the scrollable frame width
        def configure_scroll_region(event):
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
            # Make the scrollable frame fill the canvas width
            canvas_width = event.width
            self.scroll_canvas.itemconfig(canvas_window, width=canvas_width)

        self.scroll_canvas.bind('<Configure>', configure_scroll_region)

        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        self.scroll_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Store reference to entries frame
        self.entries_frame = self.scrollable_frame



    def setup_action_buttons(self, parent):
        """Set up action buttons with better styling"""
        # Action buttons container
        button_container = ttk.Frame(parent)
        button_container.pack(fill="x", pady=(0, 5))

        # Left side - main action
        left_buttons = ttk.Frame(button_container)
        left_buttons.pack(side="left", fill="x", expand=True)

        self.generate_button = self.main_gui.ui_factory.create_icon_button(
            left_buttons, "Generate Video", self.start_video_generation,
            icon="🚀", width=25
        )
        self.generate_button.pack(side="left")

        # Right side - control actions
        right_buttons = ttk.Frame(button_container)
        right_buttons.pack(side="right")

        self.stop_button = self.main_gui.ui_factory.create_icon_button(
            right_buttons, "Stop", self.stop_video_generation,
            icon="⏹️", state="disabled", width=12
        )
        self.stop_button.pack(side="right")

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling in the canvas"""
        self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_image_entry(self, folder_path=None, prompt=None):
        """Add a new image entry to the list"""
        # Check entry limit
        if len(self.image_entries) >= self.MAX_ENTRIES:
            if not self._is_batch_loading:
                self.main_gui.log(f"⚠️ Maximum entries ({self.MAX_ENTRIES}) reached. Remove some entries first.")
            return None

        from ui.components.image_entry import ImageEntry

        # Hide empty state when adding first entry
        self.hide_empty_state()

        entry_id = self.next_entry_id
        self.next_entry_id += 1

        # Create new image entry
        image_entry = ImageEntry(
            self.entries_frame,
            self.main_gui,
            self.remove_image_entry,
            entry_id
        )

        # Set data if provided
        if folder_path:
            image_entry.set_data(folder_path, prompt or "")

        # Store the entry
        self.image_entries[entry_id] = image_entry

        # Only update scroll region if not batch loading (performance optimization)
        if not self._is_batch_loading:
            self.scrollable_frame.update_idletasks()
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
            self.main_gui.log(f"Added image folder entry #{entry_id}")

        return entry_id

    def add_image_entry_with_images(self, image_files):
        """Add a new image entry with specific image files (not folder-based)"""
        # Check entry limit
        if len(self.image_entries) >= self.MAX_ENTRIES:
            self.main_gui.log(f"⚠️ Maximum entries ({self.MAX_ENTRIES}) reached. Remove some entries first.")
            return None

        from ui.components.image_entry import ImageEntry

        # Hide empty state when adding first entry
        self.hide_empty_state()

        entry_id = self.next_entry_id
        self.next_entry_id += 1

        # Create new image entry
        image_entry = ImageEntry(
            self.entries_frame,
            self.main_gui,
            self.remove_image_entry,
            entry_id
        )

        # Set the images directly instead of using folder path
        image_entry.set_images_directly(image_files)

        # Store the entry
        self.image_entries[entry_id] = image_entry

        # Only update scroll region if not batch loading
        if not self._is_batch_loading:
            self.scrollable_frame.update_idletasks()
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

        self.main_gui.log(f"Added image entry #{entry_id} with {len(image_files)} selected images")
        return entry_id

    def remove_image_entry(self, entry_id):
        """Remove an image entry from the list"""
        if entry_id in self.image_entries:
            # Remove the entry
            self.image_entries[entry_id].destroy()
            del self.image_entries[entry_id]

            # If no entries left, show empty state
            if not self.image_entries and not self.group_entries:
                self.show_empty_state()

            # Update scroll region
            self.scrollable_frame.update_idletasks()
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

            self.main_gui.log(f"Removed image folder entry #{entry_id}")

    def get_valid_entries(self):
        """Get all valid image entries (individual or grouped)"""
        if self.current_mode == "grouped":
            return self.get_valid_groups()
        else:
            return self.get_valid_individual_entries()

    def get_valid_individual_entries(self):
        """Get all valid individual image entries"""
        valid_entries = []
        for entry_id, entry in self.image_entries.items():
            if entry.is_valid():
                valid_entries.append(entry.get_data())
        return valid_entries

    def get_valid_groups(self):
        """Get all valid group entries"""
        valid_groups = []
        self.main_gui.log(f"Checking {len(self.group_entries)} group entries for validity...")

        for group_id, group_entry in self.group_entries.items():
            group_data = group_entry.get_group_data()
            is_valid = group_entry.is_valid()

            self.main_gui.log(f"Group {group_id} ({group_data.get('folder_name', 'Unknown')}): {'Valid' if is_valid else 'Invalid'}")

            if is_valid:
                valid_groups.append(group_data)
            else:
                # Debug invalid groups
                pairs = group_data.get('pairs', [])
                self.main_gui.log(f"  - Has {len(pairs)} pairs")
                for i, pair in enumerate(pairs):
                    has_images = bool(pair.get('images'))
                    has_prompt = bool(pair.get('prompt'))
                    self.main_gui.log(f"  - Pair {i+1}: Images={has_images}, Prompt={has_prompt}")

        self.main_gui.log(f"Found {len(valid_groups)} valid groups")
        return valid_groups

    def _get_existing_folder_paths(self):
        """Get list of folder paths already loaded in entries (only folder-based entries)"""
        existing_folders = []
        for entry in self.image_entries.values():
            data = entry.get_data()
            # Only include actual folder paths, not file-based entries
            if data['folder_path'] and not data.get('is_file_based', False):
                existing_folders.append(data['folder_path'])
        return existing_folders

    def _get_existing_image_files(self):
        """Get list of individual image files already loaded in entries"""
        existing_images = set()
        for entry in self.image_entries.values():
            data = entry.get_data()
            if data.get('images'):
                existing_images.update(data['images'])
        return existing_images

    def _find_existing_folder_entry(self, folder_path):
        """Find existing entry with the same folder path"""
        if not folder_path:
            return None

        for entry_id, entry in self.image_entries.items():
            data = entry.get_data()
            existing_folder_path = data.get('folder_path')
            if existing_folder_path and os.path.normpath(existing_folder_path) == os.path.normpath(folder_path):
                return entry_id
        return None

    def _generate_unique_name(self, base_path, existing_paths):
        """Generate a unique name by adding numbers if duplicates exist"""
        if base_path not in existing_paths:
            return base_path

        # Extract directory and filename
        directory = os.path.dirname(base_path)
        filename = os.path.basename(base_path)
        name, ext = os.path.splitext(filename)

        # Try numbered versions
        counter = 1
        while True:
            new_filename = f"{name}({counter}){ext}"
            new_path = os.path.join(directory, new_filename)
            if new_path not in existing_paths:
                return new_path
            counter += 1

    def _find_empty_entry(self):
        """Find the first empty entry (no folder path and no images)"""
        for entry_id, entry in self.image_entries.items():
            data = entry.get_data()
            # Check if entry is empty (no folder path and no images)
            has_folder = data.get('folder_path') and not data.get('is_file_based', False)
            has_images = data.get('images') and len(data['images']) > 0
            has_prompt = data.get('prompt', '').strip()

            # Entry is empty if it has no folder, no images, and no prompt
            if not has_folder and not has_images and not has_prompt:
                return entry_id
        return None

    def select_multiple_images(self):
        """Select multiple individual image files and create entries"""
        from utils.dialog_helpers import select_image_files

        try:
            # Show file selection dialog
            selected_files = select_image_files(title="Select Multiple Images", multiple=True)

            if not selected_files:
                return

            # Convert to list if it's a tuple
            if isinstance(selected_files, tuple):
                selected_files = list(selected_files)
            elif isinstance(selected_files, str):
                selected_files = [selected_files]

            # Get existing images to handle duplicates with numbering
            existing_images = self._get_existing_image_files()

            # Generate unique names for duplicates
            processed_images = []
            for img in selected_files:
                if img in existing_images:
                    # Generate unique name with numbering
                    unique_name = self._generate_unique_name(img, existing_images)
                    processed_images.append(unique_name)
                    existing_images.add(unique_name)  # Add to set to avoid conflicts
                else:
                    processed_images.append(img)
                    existing_images.add(img)

            new_images = processed_images

            # Try to find an existing empty entry to populate first
            empty_entry_id = self._find_empty_entry()

            if empty_entry_id is not None:
                # Populate the existing empty entry
                entry = self.image_entries[empty_entry_id]
                entry.set_images_directly(new_images)
                entry_id = empty_entry_id
                action = "populated"
            else:
                # Create a new entry with all selected images
                entry_id = self.add_image_entry_with_images(new_images)
                action = "created"

            # Log results
            duplicate_count = len(selected_files) - len([img for img in selected_files if img not in self._get_existing_image_files()])
            if duplicate_count > 0:
                self.main_gui.log(f"Added {len(new_images)} images to entry #{entry_id} ({action}), {duplicate_count} duplicates renamed with numbers")
            else:
                self.main_gui.log(f"Added {len(new_images)} images to entry #{entry_id} ({action})")

        except Exception as e:
            self.main_gui.log(f"Error selecting images: {e}")
            from utils.error_helpers import show_error_with_log
            show_error_with_log(self.main_gui, "Error", "Failed to select images", e)

    def import_from_url(self):
        """Import content from a WordPress post URL"""
        from tkinter import simpledialog, messagebox
        import threading
        
        # Ask for URL
        url = simpledialog.askstring(
            "Import from URL",
            "Enter WordPress post URL:",
            parent=self.parent_frame
        )
        
        if not url or not url.strip():
            return
        
        url = url.strip()
        self.main_gui.log(f"Importing content from: {url}")
        
        # Run scraping in background thread
        def scrape_thread():
            try:
                from utils.wordpress_scraper import scrape_wordpress_post
                import tempfile
                import os
                
                # Create temp directory for images
                output_dir = tempfile.mkdtemp(prefix="wp_import_")
                
                # Scrape the post
                result = scrape_wordpress_post(url, output_dir)
                
                if not result['success']:
                    self.parent_frame.after(0, lambda: messagebox.showerror(
                        "Import Failed", 
                        f"Failed to import content:\n{result['error']}"
                    ))
                    return
                
                # Log results
                self.parent_frame.after(0, lambda: self.main_gui.log(
                    f"Scraped: {result['title']} - {len(result['images'])} images"
                ))
                
                # Create entry on main thread
                def create_entry():
                    if result['images']:
                        # Create entry with scraped images
                        entry_id = self.add_image_entry_with_images(result['images'])
                        
                        if entry_id and entry_id in self.image_entries:
                            entry = self.image_entries[entry_id]
                            
                            # Set the text content as prompt
                            if result['text']:
                                entry.prompt_text_widget.delete('1.0', 'end')
                                entry.prompt_text_widget.insert('1.0', result['text'])
                            
                            # Set custom filename from title
                            if result['title']:
                                # Clean title for filename
                                clean_title = "".join(c for c in result['title'] if c.isalnum() or c in ' -_')[:50]
                                entry.custom_filename.set(clean_title)
                                entry.filename_entry.delete(0, 'end')
                                entry.filename_entry.insert(0, clean_title)
                                entry.filename_entry.config(foreground="black")
                            
                            self.main_gui.log(f"Created entry #{entry_id} from URL import")
                    else:
                        messagebox.showwarning(
                            "No Images Found",
                            "No images were found in the article.\nPlease try a different URL."
                        )
                
                self.parent_frame.after(0, create_entry)
                
            except Exception as e:
                self.parent_frame.after(0, lambda: messagebox.showerror(
                    "Import Error",
                    f"Error importing from URL:\n{str(e)}"
                ))
        
        # Start background thread
        thread = threading.Thread(target=scrape_thread, daemon=True)
        thread.start()

    def clear_all_entries(self):
        """Clear all image entries (both individual and grouped)"""
        # Remove all individual entries
        for entry_id in list(self.image_entries.keys()):
            self.image_entries[entry_id].destroy()

        # Remove all group entries
        for group_id in list(self.group_entries.keys()):
            self.group_entries[group_id].destroy()

        # Clear the dictionaries
        self.image_entries.clear()
        self.group_entries.clear()
        self.next_entry_id = 1
        self.next_group_id = 1

        # Reset to individual mode
        self.current_mode = "individual"

        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def load_images_from_folder(self):
        """Load image folder(s) - intelligently handles single folders or parent folders with subfolders"""
        from utils.dialog_helpers import select_folder
        folder_path = select_folder(title="Select Image Folder or Parent Folder")

        if not folder_path:
            return

        try:
            # Process the selected folder
            folder_data = self.folder_processor.process_folder_structure(folder_path)

            if not folder_data:
                from utils.error_helpers import show_warning_with_log
                show_warning_with_log(self.main_gui, "No Data", "No valid images found in the selected folder.")
                return

            # Determine if this is a single folder or multiple subfolders
            has_subfolders = any(item.get('type') == 'subfolder' for item in folder_data)

            if len(folder_data) == 1 and not has_subfolders:
                # Single folder - use individual loading logic
                folder_item = folder_data[0]
                selected_folder_path = folder_item.get('folder_path')
                prompt = folder_item.get('prompt', '')

                # Check if this folder already exists in current entries
                existing_entry_id = self._find_existing_folder_entry(selected_folder_path)

                if existing_entry_id is not None:
                    # Update existing entry for the same folder
                    existing_entry = self.image_entries[existing_entry_id]
                    existing_entry.set_data(selected_folder_path, prompt)
                    self.main_gui.log(f"Updated existing entry #{existing_entry_id} with folder: {os.path.basename(selected_folder_path)}")
                else:
                    # Create new entry for different folder
                    entry_id = self.add_image_entry(selected_folder_path, prompt)
                    if entry_id:
                        self.main_gui.log(f"Added new entry #{entry_id} with folder: {os.path.basename(selected_folder_path)}")
            else:
                # Multiple folders/subfolders - always use individual entries for better control
                # This allows updating existing entries and adding new ones
                self.load_as_individual_entries(folder_data)
                self.main_gui.log(f"Processed {len(folder_data)} image folder(s) from: {os.path.basename(folder_path)}")

        except Exception as e:
            self.main_gui.log(f"Error loading folder: {e}")
            from utils.error_helpers import show_error_with_log
            show_error_with_log(self.main_gui, "Error", "Failed to load folder", e)

    def load_multiple_folders_from_parent(self):
        """Load multiple image folders from a parent directory (bulk loading)"""
        from utils.dialog_helpers import select_folder
        folder_path = select_folder(title="Select Parent Folder Containing Multiple Image Folders")

        if not folder_path:
            return

        try:
            # Don't clear existing entries - we want to update/add as needed
            # Process the folder structure
            folder_data = self.folder_processor.process_folder_structure(folder_path)

            if not folder_data:
                from utils.error_helpers import show_warning_with_log
                show_warning_with_log(self.main_gui, "No Data", "No valid image folders found in the selected directory.")
                return

            # Determine if we should use grouped or individual mode
            has_subfolders = any(item.get('type') == 'subfolder' for item in folder_data)
            has_root_content = any(item.get('type') == 'root' for item in folder_data)

            if has_subfolders and len(folder_data) > 1:
                # Use grouped mode for complex folder structures
                self.load_as_groups(folder_data, folder_path)
            else:
                # Use individual mode for simple structures - now with update/add logic
                self.load_as_individual_entries(folder_data)

            self.main_gui.log(f"Processed {len(folder_data)} image folder(s) from: {os.path.basename(folder_path)}")

        except Exception as e:
            self.main_gui.log(f"Error loading folders: {e}")
            from utils.error_helpers import show_error_with_log
            show_error_with_log(self.main_gui, "Error", "Failed to load folders", e)
            # Ensure we have at least one entry if none exist
            if not self.image_entries and not self.group_entries:
                self.add_image_entry()

    def load_as_individual_entries(self, folder_data):
        """Load folder data as individual entries with update/add logic"""
        self.current_mode = "individual"

        # Enable batch loading mode to prevent excessive UI updates
        self._is_batch_loading = True
        
        updated_count = 0
        new_count = 0
        skipped_count = 0

        try:
            for item in folder_data:
                folder_path = item.get('folder_path')
                prompt = item.get('prompt', '')

                if not folder_path:
                    continue

                # Check entry limit
                if len(self.image_entries) >= self.MAX_ENTRIES:
                    skipped_count = len(folder_data) - (updated_count + new_count)
                    break

                # Check if this folder already exists in current entries
                existing_entry_id = self._find_existing_folder_entry(folder_path)

                if existing_entry_id is not None:
                    # Update existing entry for the same folder
                    existing_entry = self.image_entries[existing_entry_id]
                    existing_entry.set_data(folder_path, prompt)
                    updated_count += 1
                else:
                    # Create new entry for different folder
                    entry_id = self.add_image_entry(folder_path, prompt)
                    if entry_id:
                        new_count += 1
        finally:
            # Disable batch loading mode
            self._is_batch_loading = False
            
            # Single UI update at the end
            self.scrollable_frame.update_idletasks()
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

        # Log summary (consolidated - not per entry)
        total_processed = updated_count + new_count
        if skipped_count > 0:
            self.main_gui.log(f"⚠️ Loaded {total_processed} folders, {skipped_count} skipped (max {self.MAX_ENTRIES} entries)")
        elif total_processed > 0:
            self.main_gui.log(f"Loaded {total_processed} folders ({new_count} new, {updated_count} updated)")

        # Ensure we have at least one entry if none exist
        if not self.image_entries:
            self.add_image_entry()

    def load_as_groups(self, folder_data, parent_folder):
        """Load folder data as grouped entries"""
        self.current_mode = "grouped"

        # Group the data by parent folder
        groups = {}

        for item in folder_data:
            if item.get('type') == 'root':
                # Root level content
                group_name = os.path.basename(parent_folder)
                if group_name not in groups:
                    groups[group_name] = []
                groups[group_name].append(item)
            elif item.get('type') == 'subfolder':
                # Subfolder content
                subfolder_name = item.get('subfolder_name', 'Unknown')
                if subfolder_name not in groups:
                    groups[subfolder_name] = []
                groups[subfolder_name].append(item)

        # Create group entries with natural sorting
        def natural_sort_key(text):
            """Convert text to a list of strings and numbers for natural sorting"""
            import re
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]

        # Sort group names naturally (1, 2, 3, 10 instead of 1, 10, 2, 3)
        sorted_groups = sorted(groups.items(), key=lambda x: natural_sort_key(x[0]))

        for group_name, items in sorted_groups:
            self.add_group_entry(group_name, items)

        # Ensure we have at least one group
        if not self.group_entries:
            self.add_group_entry("Default Group", [])

    def add_group_entry(self, group_name, items):
        """Add a new group entry"""
        # Hide empty state when adding first entry
        self.hide_empty_state()

        group_id = self.next_group_id
        self.next_group_id += 1

        # Create group info structure that GroupEntry expects
        group_info = {
            'folder_name': group_name,
            'output_name': f"{group_name}.mp4",
            'pairs': []
        }

        # Add items to the group info
        for item in items:
            folder_path = item.get('folder_path')
            prompt = item.get('prompt', '')
            images = item.get('images', [])

            if folder_path and images:
                group_info['pairs'].append({
                    'video_file': folder_path,
                    'prompt': prompt,
                    'images': images
                })

        # Create new group entry with proper group_info structure
        group_entry = GroupEntry(
            self.entries_frame,
            self.main_gui,
            self.remove_group_entry,
            group_id,
            group_info
        )

        # Store the group entry
        self.group_entries[group_id] = group_entry

        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

        self.main_gui.log(f"Added group entry: {group_name}")
        return group_id

    def remove_group_entry(self, group_id):
        """Remove a group entry"""
        if group_id in self.group_entries:
            # Remove the group entry
            self.group_entries[group_id].destroy()
            del self.group_entries[group_id]

            # If no entries left, show empty state
            if not self.image_entries and not self.group_entries:
                self.show_empty_state()

            # Update scroll region
            self.scrollable_frame.update_idletasks()
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

            self.main_gui.log(f"Removed group entry #{group_id}")

    def setup_action_buttons(self, parent):
        """Set up action buttons with better styling"""
        # Action buttons container
        button_container = ttk.Frame(parent)
        button_container.pack(fill="x", pady=(0, 5))

        # Left side - main action
        left_buttons = ttk.Frame(button_container)
        left_buttons.pack(side="left", fill="x", expand=True)

        self.generate_button = self.main_gui.ui_factory.create_icon_button(
            left_buttons, "Generate All Videos", self.start_video_generation,
            icon="🚀", width=25
        )
        self.generate_button.pack(side="left")

        # Right side - control actions
        right_buttons = ttk.Frame(button_container)
        right_buttons.pack(side="right")

        self.stop_button = self.main_gui.ui_factory.create_icon_button(
            right_buttons, "Stop", self.stop_video_generation,
            icon="⏹️", state="disabled", width=12
        )
        self.stop_button.pack(side="right")

    def start_video_generation(self):
        """Start video generation from all valid entries"""
        # Get valid entries
        valid_entries = self.get_valid_entries()

        if not valid_entries:
            from utils.error_helpers import show_warning_with_log
            show_warning_with_log(self.main_gui, "No Valid Entries", "Please add at least one valid image folder.")
            return

        # Check if generation is already running
        if hasattr(self.main_gui, 'generation_thread') and self.main_gui.generation_thread and self.main_gui.generation_thread.is_alive():
            show_warning_with_log(self.main_gui, "Process Running", "Video generation is already in progress")
            return

        self.main_gui.log(f"Starting generation for {len(valid_entries)} image folder(s)")

        # Show optimization status
        try:
            from services.video_optimization import get_optimization_manager
            opt_manager = get_optimization_manager()
            opt_manager.print_optimization_status()
        except ImportError:
            pass

        # Update UI state
        self.image_progress_bar["value"] = 0
        self.image_progress_label.config(text="0%")
        self.generate_button.config(state="disabled")
        self.stop_button.config(state="normal")

        # Start generation thread
        self.main_gui.stop_event = threading.Event()
        self.main_gui.generation_thread = threading.Thread(
            target=self.generate_videos_thread,
            args=(valid_entries,)
        )
        self.main_gui.generation_thread.daemon = True
        self.main_gui.generation_thread.start()

    def generate_videos_thread(self, entries):
        """Generate videos in a separate thread"""
        try:
            total_entries = len(entries)
            successful_count = 0
            failed_count = 0
            missing_prompt_count = 0

            for i, entry_data in enumerate(entries):
                if self.main_gui.stop_event.is_set():
                    self.main_gui.log("Video generation stopped by user")
                    break

                # Update progress
                progress = int((i / total_entries) * 100)
                self.main_gui.root.after(0, lambda p=progress: self.update_progress(p, f"Processing entry {i+1}/{total_entries}"))

                # Check if this is a group entry or individual entry
                if self.current_mode == "grouped" and 'pairs' in entry_data:
                    # Handle group generation
                    result = self.generate_group_video(entry_data)
                else:
                    # Handle individual entry generation
                    result = self.generate_single_video(entry_data)

                if result is True:
                    successful_count += 1
                elif result == "missing_prompt":
                    missing_prompt_count += 1
                else:
                    failed_count += 1

            # Final progress update with accurate results
            if not self.main_gui.stop_event.is_set():
                total_failed = failed_count + missing_prompt_count
                if successful_count > 0:
                    self.main_gui.root.after(0, lambda: self.update_progress(100, f"Generation complete! {successful_count} successful, {total_failed} failed"))
                    if total_failed == 0:
                        self.main_gui.root.after(0, lambda: self.main_gui.log(f"Successfully generated all {successful_count} video(s)"))
                        # Show completion message box
                        self.main_gui.root.after(0, lambda: self._show_completion_message(successful_count, total_failed))
                    else:
                        self.main_gui.root.after(0, lambda: self.main_gui.log(f"Generated {successful_count} video(s), {total_failed} failed"))
                        # Show completion message box
                        self.main_gui.root.after(0, lambda: self._show_completion_message(successful_count, total_failed))
                else:
                    # Only show generic failure message if there are actual failures (not just missing prompts)
                    if failed_count > 0:
                        self.main_gui.root.after(0, lambda: self.update_progress(0, "All video generation attempts failed"))
                        self.main_gui.root.after(0, lambda: self.main_gui.log(f"Failed to generate any videos ({failed_count} attempts failed)"))
                        # Show failure message box
                        self.main_gui.root.after(0, lambda: self._show_failure_message(failed_count))
                    elif missing_prompt_count > 0:
                        # All failures were due to missing prompts - don't show generic failure message
                        self.main_gui.root.after(0, lambda: self.update_progress(0, "No videos generated - missing text prompts"))
                        self.main_gui.root.after(0, lambda: self.main_gui.log(f"No videos generated - {missing_prompt_count} entries missing text prompts"))

        except Exception as e:
            self.main_gui.root.after(0, lambda: self.main_gui.log(f"Error during video generation: {e}"))
            from utils.error_helpers import show_error_with_log
            self.main_gui.root.after(0, lambda: show_error_with_log(self.main_gui, "Generation Error", "An error occurred", e))
        finally:
            # Reset UI state
            self.main_gui.root.after(0, self.reset_ui)

    def generate_group_video(self, group_data):
        """Generate videos for a group entry (multiple image folders combined) with smart optimizations"""
        try:
            group_name = group_data.get('folder_name', 'Unknown Group')
            pairs = group_data.get('pairs', [])

            if not pairs:
                self.main_gui.log(f"Skipping invalid group: {group_name} - no pairs")
                return False

            self.main_gui.log(f"Generating videos for group: {group_name} ({len(pairs)} folders)")

            # Import optimization service
            from services.video_optimization import get_optimization_manager
            opt_manager = get_optimization_manager()

            # Process each pair in the group
            successful_pairs = 0
            for i, pair in enumerate(pairs):
                if self.main_gui.stop_event.is_set():
                    break

                # Extract pair data - note that groups use 'video_file' instead of 'folder_path'
                folder_path = pair.get('video_file')  # This is actually the folder path for image groups
                prompt = pair.get('prompt', '')
                images = pair.get('images', [])

                if not folder_path or not prompt or not images:
                    self.main_gui.log(f"Skipping invalid pair {i+1} in group {group_name}: folder_path={folder_path}")
                    continue

                # Check for duplicate content to avoid redundant processing
                duplicate_result = opt_manager.check_duplicate_content(prompt, folder_path)
                if duplicate_result:
                    self.main_gui.log(f"🔄 Reusing result for duplicate content: {os.path.basename(folder_path)}")
                    successful_pairs += 1
                    continue

                # Create individual entry data structure for this pair
                pair_entry_data = {
                    'folder_path': folder_path,
                    'prompt': prompt,
                    'images': images,
                    'custom_filename': group_data.get('custom_filename', '')
                }

                # Generate video for this pair
                self.main_gui.log(f"Processing pair {i+1}/{len(pairs)} in group {group_name}: {os.path.basename(folder_path)}")
                success = self.generate_single_video(pair_entry_data)
                if success:
                    successful_pairs += 1
                    # Register successful result for future duplicate detection
                    opt_manager.register_content_result(prompt, folder_path, "generated_successfully")

            # Return success if at least one pair was processed successfully
            if successful_pairs > 0:
                self.main_gui.log(f"Group {group_name}: {successful_pairs}/{len(pairs)} videos generated successfully")
                return True
            else:
                self.main_gui.log(f"Group {group_name}: All video generation attempts failed")
                return False

        except Exception as e:
            self.main_gui.log(f"Error generating videos for group {group_data.get('folder_name', 'unknown')}: {e}")
            return False

    def generate_single_video(self, entry_data):
        """Generate a single video from entry data"""
        try:
            # Extract data
            folder_path = entry_data.get('folder_path')
            prompt = entry_data.get('prompt', '')
            images = entry_data.get('images', [])
            custom_filename = entry_data.get('custom_filename', '')
            is_file_based = entry_data.get('is_file_based', False)

            # For file-based entries, folder_path will be None, so check differently
            if not images:
                self.main_gui.log(f"Skipping invalid entry: no images found")
                return False

            # Check if prompt is provided
            if not prompt:
                self.main_gui.log(f"Skipping entry: no text prompt provided")
                from utils.error_helpers import show_warning_with_log
                show_warning_with_log(self.main_gui, "Missing Text Prompt",
                                    "Please add a text prompt for this image entry before generating video.")
                return "missing_prompt"  # Return special value to indicate missing prompt

            # For folder-based entries, we still need a valid folder path
            if not is_file_based and not folder_path:
                self.main_gui.log(f"Skipping invalid folder-based entry: no folder path")
                return False

            # Setup model with entry data
            self.main_gui.model.text_input = prompt
            self.main_gui.model.selected_images = images
            self.main_gui.model.image_source = "selected"  # Use "selected" instead of "3"
            self.main_gui.model.website_url = ""
            self.main_gui.model.local_folder = ""
            self.main_gui.model.custom_filename = custom_filename
            # Set source files for intelligent default naming
            self.main_gui.model.source_files = images

            # Set up progress callback for this generation
            def progress_callback(value, message=None):
                self.main_gui.root.after(0, lambda: self.update_progress(value, message))
            self.main_gui.model.set_progress_callback(progress_callback)

            # Get tab-specific settings
            from utils.settings_manager import SettingsManager
            settings_manager = SettingsManager()
            image_tab_settings = settings_manager.get_tab_settings('image_tab')

            # Apply TTS settings to model (from shared settings)
            self.main_gui.model.tts_settings = {
                'language': image_tab_settings.get('tts_language', 'en'),
                'voice_actor': image_tab_settings.get('tts_voice_actor', 'Guy'),
                'speed': image_tab_settings.get('tts_speed', 1.0),
                'emotion': image_tab_settings.get('tts_emotion', 'neutral')
            }

            # Apply image-specific settings
            self.main_gui.model.enable_speech_validation = image_tab_settings.get('enable_speech_validation', True)
            self.main_gui.model.content_analysis_enabled = image_tab_settings.get('content_analysis_enabled', True)

            # Set output folder if user selected one
            output_folder_value = self.current_settings.get('output_folder', 'Default (Auto)')
            if output_folder_value and output_folder_value != "Default (Auto)":
                if os.path.isdir(output_folder_value):
                    self.main_gui.model.output_folder = output_folder_value
                else:
                    self.main_gui.model.output_folder = None
            else:
                self.main_gui.model.output_folder = None

            # Generate the video
            if is_file_based:
                entry_name = f"Selected Images ({len(images)} files)"
            else:
                entry_name = os.path.basename(folder_path)
            self.main_gui.log(f"Generating video for: {entry_name}")

            # Call the model's generate method
            result = self.main_gui.model.generate_video(self.main_gui.stop_event)

            # Check if generation was successful
            # generate_video returns (subtitle_path, video_path, output_dir) on success, None on failure
            if result and len(result) == 3:
                subtitle_path, video_path, output_dir = result

                # Try to finalize the video (merge with subtitles)
                final_video = self.main_gui.model.finalize_video(subtitle_path, video_path, output_dir, self.main_gui.stop_event)

                if final_video and os.path.exists(final_video):
                    self.main_gui.log(f"Successfully generated video for: {entry_name} -> {os.path.basename(final_video)}")
                    return True
                else:
                    self.main_gui.log(f"Failed to finalize video for: {entry_name}")
                    return False
            else:
                self.main_gui.log(f"Failed to generate video for: {entry_name}")
                return False

        except Exception as e:
            self.main_gui.log(f"Error generating video for {entry_data.get('folder_path', 'unknown')}: {e}")
            return False

    def stop_video_generation(self):
        """Stop video generation"""
        if hasattr(self.main_gui, 'stop_event') and self.main_gui.stop_event:
            self.main_gui.stop_event.set()
            self.main_gui.log("Stopping video generation...")
            self.main_gui.root.after(1000, self.reset_ui)

    def update_progress(self, value, text):
        """Update progress bar and label"""
        from utils.gui_helpers import standardize_progress_update
        standardize_progress_update(self.image_progress_bar, self.image_progress_label, value, text)

    def _show_completion_message(self, successful_count, failed_count):
        """Show completion message box with option to open output folder"""
        import tkinter.messagebox as messagebox

        if failed_count == 0:
            message = f"🎉 All {successful_count} video(s) generated successfully!"
            title = "Generation Complete"
        else:
            message = f"Generation completed!\n\n✅ {successful_count} successful\n❌ {failed_count} failed"
            title = "Generation Complete"

        # Ask if user wants to open output folder
        message += "\n\nWould you like to open the output folder?"
        response = messagebox.askyesno(title, message)

        if response:
            # Open the output folder
            output_folder = self.current_settings.get('output_folder', 'Default (Auto)')
            if output_folder and output_folder != "Default (Auto)" and os.path.exists(output_folder):
                self.main_gui.open_file(output_folder)
            else:
                # Use default output directory
                from utils.helpers import get_output_directory
                default_folder = get_output_directory(self.current_settings)
                if os.path.exists(default_folder):
                    self.main_gui.open_file(default_folder)

    def _show_failure_message(self, failed_count):
        """Show failure message box"""
        import tkinter.messagebox as messagebox

        message = f"❌ All {failed_count} video generation attempts failed.\n\nPlease check the logs for error details."
        messagebox.showerror("Generation Failed", message)

    def reset_ui(self):
        """Reset the UI to default state"""
        if self.generate_button:
            self.generate_button.config(state=tk.NORMAL)
        if self.stop_button:
            self.stop_button.config(state=tk.DISABLED)
        if self.image_progress_bar:
            self.image_progress_bar["value"] = 0
        if self.image_progress_label:
            self.image_progress_label.config(text="Ready")

    def _show_settings_popup(self):
        """Show the settings popup dialog"""
        if self.settings_popup and hasattr(self.settings_popup, 'popup_window') and self.settings_popup.popup_window and self.settings_popup.popup_window.winfo_exists():
            # Popup already exists, bring it to front
            self.settings_popup.popup_window.lift()
            self.settings_popup.popup_window.focus_set()
            return

        # Show settings popup with TTS, output folder, and image processing settings (speech recognition is automatic)
        self.settings_popup = show_settings_popup(
            parent=self.main_gui.root,
            title="Multi-Folder Image-to-Video Settings",
            main_gui=self.main_gui,
            callback=self._on_settings_applied,
            include_audio=False,  # Use TTS instead
            current_tab="image_tab",  # Specify this is for image tab
            include_output_folder=True,
            include_tts=True,
            include_speech_recognition=False,  # Now automatic
            include_image_processing=True,  # Include image processing for Image tab
            include_audio_controls=False,  # No mute/volume controls for image tab
            current_settings=self.current_settings
        )

    def _on_settings_applied(self, settings):
        """Handle when settings are applied from the popup"""
        # Update current settings
        self.current_settings.update(settings)

        # Apply TTS settings to model immediately
        if hasattr(self.main_gui, 'model'):
            self.main_gui.model.tts_settings = {
                'language': self.current_settings.get('tts_language', 'en'),
                'voice_actor': self.current_settings.get('tts_voice_actor', 'Guy'),
                'speed': self.current_settings.get('tts_speed', 1.0),
                'emotion': self.current_settings.get('tts_emotion', 'neutral')
            }

        # Sync output folder with the model
        if 'output_folder' in settings:
            self.main_gui.model.output_folder = settings['output_folder']

        # Update the info label
        self._update_settings_info_label()

        # Notify other tabs about shared settings changes
        self._notify_other_tabs_of_settings_change(settings)

    def _update_settings_info_label(self):
        """Update the settings info label with current settings"""
        # TTS info
        voice = self.current_settings.get('tts_voice_actor', 'Default')
        speed = f"{self.current_settings.get('tts_speed', 1.0):.1f}x"
        emotion = self.current_settings.get('tts_emotion', 'neutral').title()

        # Output info
        output_folder = self.current_settings.get('output_folder', 'Default (Auto)')
        output_name = "Default" if output_folder == "Default (Auto)" else "Custom"

        # Update label
        info_text = f"TTS: {voice}, {speed} Speed, {emotion} | Output: {output_name} Folder"
        self.settings_info_label.config(text=info_text)

    def _notify_other_tabs_of_settings_change(self, settings):
        """Notify other tabs when shared settings change"""
        try:
            # Check if settings contain shared TTS settings
            shared_keys = ['tts_language', 'tts_voice_actor', 'tts_speed', 'tts_emotion', 'output_folder']
            has_shared_changes = any(key in settings for key in shared_keys)

            if has_shared_changes and hasattr(self.main_gui, 'video_tab_component'):
                # Check if video tab component is properly initialized with current_settings
                if hasattr(self.main_gui.video_tab_component, 'current_settings') and hasattr(self.main_gui.video_tab_component, '_update_settings_info_label'):
                    # Update video tab's current settings and refresh its label
                    self.main_gui.video_tab_component.current_settings.update(settings)
                    self.main_gui.video_tab_component._update_settings_info_label()

                # Apply TTS settings to model from video tab perspective too
                if hasattr(self.main_gui, 'model'):
                    self.main_gui.model.tts_settings = {
                        'language': settings.get('tts_language', self.main_gui.model.tts_settings.get('language', 'en')),
                        'voice_actor': settings.get('tts_voice_actor', self.main_gui.model.tts_settings.get('voice_actor', 'Guy')),
                        'speed': settings.get('tts_speed', self.main_gui.model.tts_settings.get('speed', 1.0)),
                        'emotion': settings.get('tts_emotion', self.main_gui.model.tts_settings.get('emotion', 'neutral'))
                    }
        except Exception as e:
            print(f"Warning: Could not notify other tabs of settings change: {e}")

    def _refresh_settings_from_file(self):
        """Refresh current settings from the settings file to ensure sync"""
        try:
            from utils.settings_manager import SettingsManager
            settings_manager = SettingsManager()
            tab_settings = settings_manager.get_tab_settings('image_tab')

            # Update current settings with latest from file
            self.current_settings.update(tab_settings)

            # Update the label to reflect any changes
            self._update_settings_info_label()

        except Exception as e:
            print(f"Warning: Could not refresh settings from file: {e}")

