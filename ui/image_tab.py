#!/usr/bin/env python3
"""
Image Tab Component for Video Generator GUI
Handles folder-based image-to-video generation with multi-folder support
"""
import os

# Use centralized UI imports
from utils.common_imports import tk, messagebox, ttk, filedialog, threading

from ui.components.settings_popup import show_settings_popup
from ui.components.group_entry import GroupEntry, SmartNotification
from utils.settings_manager import SettingsManager
from utils.folder_processor import FolderProcessor


class ImageTab:
    """Image tab component for multi-folder image-to-video generation"""

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
            font=("Cascadia Code", 12, "bold")
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

        # Add initial image entry
        self.add_image_entry()

    def setup_settings_section(self, parent):
        """Set up compact settings section"""
        # Settings control row
        settings_row = ttk.Frame(parent)
        settings_row.pack(fill="x", pady=(0, 8))

        # Settings info label
        self.settings_info_label = ttk.Label(
            settings_row,
            text="TTS: Default Voice, 1.0x Speed, Neutral | Output: Default Folder",
            font=("Cascadia Code", 8),
            foreground="#7f8c8d"
        )
        self.settings_info_label.pack(side="left", anchor="w")

        # Update info label with current settings
        self._update_settings_info_label()

    def setup_scrollable_area(self, parent):
        """Set up scrollable area for image entries"""
        # Image entries section header
        entries_header = ttk.Frame(parent)
        entries_header.pack(fill="x", pady=(0, 10))

        entries_title = ttk.Label(
            entries_header,
            text="🖼️ Image Folder Entries",
            font=("Cascadia Code", 11, "bold")
        )
        entries_title.pack(side="left")

        # Settings button (rightmost)
        settings_button = self.main_gui.ui_factory.create_icon_button(
            entries_header, "⚙️", self._show_settings_popup,
            width=5
        )
        settings_button.pack(side="right", padx=(0, 4))

        # Add image folder button
        add_image_button = self.main_gui.ui_factory.create_icon_button(
            entries_header, "Add Image", self.add_image_entry,
            icon="➕", width=15
        )
        add_image_button.pack(side="right", padx=(0, 4))

        # Load from folder button
        load_folder_button = self.main_gui.ui_factory.create_icon_button(
            entries_header, "Load from Folder", self.load_images_from_folder,
            icon="📁", width=20
        )
        load_folder_button.pack(side="right", padx=(0, 4))

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

    def setup_text_input_section(self, parent):
        """Set up text input section for prompts"""
        text_frame = ttk.LabelFrame(parent, text="📝 Text Prompt for Video", padding=8)
        text_frame.pack(fill="x", pady=(0, 15))

        # Text input with scrollbar
        text_container = ttk.Frame(text_frame)
        text_container.pack(fill="x")

        self.text_input = tk.Text(
            text_container,
            wrap='word',
            height=4,
            font=("Cascadia Code", 10),
            borderwidth=1,
            relief="solid"
        )
        self.text_input.pack(side="left", fill="x", expand=True)

        text_scrollbar = ttk.Scrollbar(text_container, command=self.text_input.yview)
        text_scrollbar.pack(side="right", fill="y")
        self.text_input.config(yscrollcommand=text_scrollbar.set)

        # Help text
        help_label = ttk.Label(
            text_frame,
            text="Enter text that will be converted to speech and used as voiceover for the generated video",
            font=("Cascadia Code", 9),
            foreground="#7f8c8d"
        )
        help_label.pack(anchor="w", pady=(5, 0))

    def setup_image_selection_section(self, parent):
        """Set up image selection section"""
        image_frame = ttk.LabelFrame(parent, text="🖼️ Image Selection", padding=8)
        image_frame.pack(fill="x", pady=(0, 15))

        # Button and help text
        button_frame = ttk.Frame(image_frame)
        button_frame.pack(fill="x", pady=(0, 5))

        select_button = self.main_gui.ui_factory.create_icon_button(
            button_frame, "Choose Images", self.select_images, icon="📁", width=20
        )
        select_button.pack(side="left", padx=(0, 10))

        # Selection controls
        select_all_button = self.main_gui.ui_factory.create_secondary_button(
            button_frame, "Select All", lambda: self.select_all_images(True), width=12
        )
        select_all_button.pack(side="left", padx=(0, 5))

        deselect_all_button = self.main_gui.ui_factory.create_secondary_button(
            button_frame, "Deselect All", lambda: self.select_all_images(False), width=12
        )
        deselect_all_button.pack(side="left", padx=(0, 5))

        clear_button = self.main_gui.ui_factory.create_icon_button(
            button_frame, "Clear", self.clear_images, icon="🧹", width=12
        )
        clear_button.pack(side="left")

        help_label = ttk.Label(
            image_frame,
            text="Select images that will be used to create the video slideshow",
            font=("Cascadia Code", 9),
            foreground="#7f8c8d"
        )
        help_label.pack(anchor="w", pady=(5, 0))

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
        from ui.components.image_entry import ImageEntry

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
        if folder_path and prompt:
            image_entry.set_data(folder_path, prompt)

        # Store the entry
        self.image_entries[entry_id] = image_entry

        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

        self.main_gui.log(f"Added image folder entry #{entry_id}")
        return entry_id

    def remove_image_entry(self, entry_id):
        """Remove an image entry from the list"""
        if entry_id in self.image_entries:
            # Don't allow removing the last entry
            if len(self.image_entries) <= 1:
                if self.progress_manager:
                    self.progress_manager.show_warning("Cannot Remove", "At least one image folder entry must remain.")
                else:
                    messagebox.showwarning("Cannot Remove", "At least one image folder entry must remain.")
                return

            # Remove the entry
            self.image_entries[entry_id].destroy()
            del self.image_entries[entry_id]

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
        """Load image folders from a parent directory"""
        from utils.dialog_helpers import select_folder
        folder_path = select_folder(title="Select Parent Folder Containing Image Folders")

        if not folder_path:
            return

        try:
            # Clear existing entries first
            self.clear_all_entries()

            # Process the folder structure
            folder_data = self.folder_processor.process_folder_structure(folder_path)

            if not folder_data:
                from utils.error_helpers import show_warning_with_log
                show_warning_with_log(self.main_gui, "No Data", "No valid image folders found in the selected directory.")
                # Add back a default entry
                self.add_image_entry()
                return

            # Determine if we should use grouped or individual mode
            has_subfolders = any(item.get('type') == 'subfolder' for item in folder_data)
            has_root_content = any(item.get('type') == 'root' for item in folder_data)

            if has_subfolders and len(folder_data) > 1:
                # Use grouped mode for complex folder structures
                self.load_as_groups(folder_data, folder_path)
            else:
                # Use individual mode for simple structures
                self.load_as_individual_entries(folder_data)

            self.main_gui.log(f"Loaded {len(folder_data)} image folder(s) from: {os.path.basename(folder_path)}")

        except Exception as e:
            self.main_gui.log(f"Error loading folders: {e}")
            from utils.error_helpers import show_error_with_log
            show_error_with_log(self.main_gui, "Error", "Failed to load folders", e)
            # Ensure we have at least one entry
            if not self.image_entries and not self.group_entries:
                self.add_image_entry()

    def load_as_individual_entries(self, folder_data):
        """Load folder data as individual entries"""
        self.current_mode = "individual"

        for item in folder_data:
            folder_path = item.get('folder_path')
            prompt = item.get('prompt', '')

            if folder_path:
                self.add_image_entry(folder_path, prompt)

        # Ensure we have at least one entry
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
            # Don't allow removing the last group
            if len(self.group_entries) <= 1:
                if self.progress_manager:
                    self.progress_manager.show_warning("Cannot Remove", "At least one group must remain.")
                else:
                    messagebox.showwarning("Cannot Remove", "At least one group must remain.")
                return

            # Remove the group entry
            self.group_entries[group_id].destroy()
            del self.group_entries[group_id]

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
            show_warning_with_log(self.main_gui, "No Valid Entries", "Please add at least one valid image folder with prompt text.")
            return

        # Check if generation is already running
        if hasattr(self.main_gui, 'generation_thread') and self.main_gui.generation_thread and self.main_gui.generation_thread.is_alive():
            show_warning_with_log(self.main_gui, "Process Running", "Video generation is already in progress")
            return

        self.main_gui.log(f"Starting generation for {len(valid_entries)} image folder(s)")

        # Show optimization status
        try:
            from services.optimization_service import get_optimization_manager
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
                    success = self.generate_group_video(entry_data)
                else:
                    # Handle individual entry generation
                    success = self.generate_single_video(entry_data)

                if success:
                    successful_count += 1
                else:
                    failed_count += 1

            # Final progress update with accurate results
            if not self.main_gui.stop_event.is_set():
                if successful_count > 0:
                    self.main_gui.root.after(0, lambda: self.update_progress(100, f"Generation complete! {successful_count} successful, {failed_count} failed"))
                    if failed_count == 0:
                        self.main_gui.root.after(0, lambda: self.main_gui.log(f"Successfully generated all {successful_count} video(s)"))
                        # Show completion message box
                        self.main_gui.root.after(0, lambda: self._show_completion_message(successful_count, failed_count))
                    else:
                        self.main_gui.root.after(0, lambda: self.main_gui.log(f"Generated {successful_count} video(s), {failed_count} failed"))
                        # Show completion message box
                        self.main_gui.root.after(0, lambda: self._show_completion_message(successful_count, failed_count))
                else:
                    self.main_gui.root.after(0, lambda: self.update_progress(0, "All video generation attempts failed"))
                    self.main_gui.root.after(0, lambda: self.main_gui.log(f"Failed to generate any videos ({failed_count} attempts failed)"))
                    # Show failure message box
                    self.main_gui.root.after(0, lambda: self._show_failure_message(failed_count))

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
            from services.optimization_service import get_optimization_manager
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
                    'images': images
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

            if not folder_path or not prompt or not images:
                self.main_gui.log(f"Skipping invalid entry: {folder_path}")
                return False

            # Setup model with entry data
            self.main_gui.model.text_input = prompt
            self.main_gui.model.selected_images = images
            self.main_gui.model.image_source = "selected"  # Use "selected" instead of "3"
            self.main_gui.model.website_url = ""
            self.main_gui.model.local_folder = ""

            # Set up progress callback for this generation
            def progress_callback(value, message=None):
                self.main_gui.root.after(0, lambda: self.update_progress(value, message))
            self.main_gui.model.set_progress_callback(progress_callback)

            # Apply TTS settings to model
            if hasattr(self.main_gui.model, 'tts_settings'):
                self.main_gui.model.tts_settings = {
                    'language': self.current_settings.get('tts_language', 'en'),
                    'voice_actor': self.current_settings.get('tts_voice_actor', 'Default'),
                    'speed': self.current_settings.get('tts_speed', 1.0),
                    'emotion': self.current_settings.get('tts_emotion', 'neutral')
                }

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
            folder_name = os.path.basename(folder_path)
            self.main_gui.log(f"Generating video for folder: {folder_name}")

            # Call the model's generate method
            result = self.main_gui.model.generate_video(self.main_gui.stop_event)

            # Check if generation was successful
            # generate_video returns (subtitle_path, video_path, output_dir) on success, None on failure
            if result and len(result) == 3:
                subtitle_path, video_path, output_dir = result

                # Try to finalize the video (merge with subtitles)
                final_video = self.main_gui.model.finalize_video(subtitle_path, video_path, output_dir, self.main_gui.stop_event)

                if final_video and os.path.exists(final_video):
                    self.main_gui.log(f"Successfully generated video for: {folder_name} -> {os.path.basename(final_video)}")
                    return True
                else:
                    self.main_gui.log(f"Failed to finalize video for: {folder_name}")
                    return False
            else:
                self.main_gui.log(f"Failed to generate video for: {folder_name}")
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
            include_output_folder=True,
            include_tts=True,
            include_speech_recognition=False,  # Now automatic
            include_image_processing=True,  # Include image processing for Image tab
            current_settings=self.current_settings
        )

    def _on_settings_applied(self, settings):
        """Handle when settings are applied from the popup"""
        # Update current settings
        self.current_settings.update(settings)

        # Sync output folder with the model
        if 'output_folder' in settings:
            self.main_gui.model.output_folder = settings['output_folder']

        # Update the info label
        self._update_settings_info_label()

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

