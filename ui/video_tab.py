# Use centralized UI imports
from utils.common_imports import tk, messagebox, ttk, filedialog
from ui.components.settings_popup import show_settings_popup
from ui.components.group_entry import GroupEntry, SmartNotification
from ui.components.video_entry import VideoEntry

import threading
import os
import config
from config import GUI_FONTS
from utils.helpers import get_output_directory

# Import folder processing utilities
from utils.folder_processor import FolderProcessor
from utils.settings_manager import SettingsManager


class VideoTab:
    """Video tab component for multi-video processing with individual prompts"""

    def __init__(self, parent_frame, main_gui):
        """Initialize the video tab"""
        self.parent_frame = parent_frame
        self.main_gui = main_gui

        # Video entries management
        self.video_entries = {}  # Dictionary to store VideoEntry objects
        self.group_entries = {}  # Dictionary to store GroupEntry objects
        self.next_entry_id = 1
        self.next_group_id = 1
        self.current_mode = "individual"  # "individual" or "grouped"

        # Settings manager for persistence
        self.settings_manager = SettingsManager()
        
        # Settings popup and current settings (load from persistent storage)
        self.settings_popup = None
        self.current_settings = self.settings_manager.get_tab_settings('video_tab')
        
        # Sync settings with model when the application starts
        if hasattr(self.main_gui, 'model'):
            if 'output_folder' in self.current_settings:
                self.main_gui.model.output_folder = self.current_settings['output_folder']
        
        # Audio settings variables (for backward compatibility)
        # Check both new and legacy mute setting names
        mute_value = self.current_settings.get('mute_original_audio', self.current_settings.get('mute', False))
        volume_value = self.current_settings.get('original_audio_volume', self.current_settings.get('volume', 0.7))
        self.mute_original_audio = tk.BooleanVar(value=mute_value)
        self.original_audio_volume = tk.DoubleVar(value=volume_value)

        # Folder processing components
        self.folder_processor = FolderProcessor()
        self.folder_processor.set_logger(self.main_gui.log)

        # Progress manager for UI operations
        self.progress_manager = None

        # UI components
        self.video_progress_bar = None
        self.video_progress_label = None
        self.generate_button = None
        self.stop_button = None
        self.entries_frame = None
        self.scroll_canvas = None
        self.scrollable_frame = None
        self.settings_info_label = None
        
        # Set up the tab
        self.setup_video_tab()
        # In VideoTab.__init__, after self.setup_video_tab():
         # This would activate Phase 1

    def setup_video_tab(self):
        """Set up the video tab UI"""
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
            text=" Video Generation",
            font=GUI_FONTS["heading"]
        )
        title_label.pack(anchor="w")

        # Settings control section - compact settings button instead of full audio settings
        self.setup_settings_section(main_frame)

        # Scrollable area for video entries
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
        self.video_progress_bar = self.progress_manager.progress_bar
        self.video_progress_label = self.progress_manager.progress_label

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
        icon_label = ttk.Label(center_frame, text="🎥", font=("Cascadia Code", 48))
        icon_label.pack(pady=(0, 10))

        title_label = ttk.Label(
            center_frame,
            text="Add videos to start processing",
            font=("Cascadia Code", 14, "bold"),
            foreground="#333333"
        )
        title_label.pack(pady=(0, 20))

        # Instructions
        instructions = [
            "Step 1: Click 'Add Content ▾' above",
            "Step 2: Choose your content source:",
            "   • Add Folder - Import video folders",
            "   • Add Files - Pick individual video files",
            "Step 3: Add text prompts (optional - can be added later)",
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

    def setup_settings_section(self, parent):
        """Set up compact settings section"""
        # Settings control row
        settings_row = ttk.Frame(parent)
        settings_row.pack(fill="x", pady=(0, 8))

        # Settings info label
        self.settings_info_label = ttk.Label(
            settings_row,
            text="Audio: Default Voice, 80% Speed, 70% Volume | Output: Default Folder",
            font=GUI_FONTS["small"],
            foreground="#7f8c8d"
        )
        self.settings_info_label.pack(side="left", anchor="w")

        # Update info label with current settings
        self._update_settings_info_label()

        # Refresh settings from file to ensure sync
        self._refresh_settings_from_file()

    def _show_settings_popup(self):
        """Show the settings popup dialog"""
        if self.settings_popup and hasattr(self.settings_popup, 'popup_window') and self.settings_popup.popup_window and self.settings_popup.popup_window.winfo_exists():
            # Popup already exists, bring it to front
            self.settings_popup.popup_window.lift()
            self.settings_popup.popup_window.focus_set()
            return
        
        # Show settings popup with audio, TTS, and output folder settings (speech recognition is automatic)
        self.settings_popup = show_settings_popup(
            parent=self.main_gui.root,
            title="Video Generation Settings",
            main_gui=self.main_gui,
            callback=self._on_settings_applied,
            include_audio=True,
            include_output_folder=True,
            include_tts=True,
            include_speech_recognition=False,  # Now automatic
            current_tab="video_tab",  # Specify this is for video tab
            current_settings=self.current_settings  # Pass current settings explicitly
        )
        
        # Settings are loaded automatically from the settings manager

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

        # Settings are already saved by the popup's settings manager
        
        # Sync output folder with the model
        if 'output_folder' in settings:
            self.main_gui.model.output_folder = settings['output_folder']
        
        # Sync audio settings with tkinter variables (for backward compatibility)
        # Handle both new and legacy setting names
        if 'mute' in settings:
            self.mute_original_audio.set(settings['mute'])
        elif 'mute_original_audio' in settings:
            self.mute_original_audio.set(settings['mute_original_audio'])

        if 'volume' in settings:
            self.original_audio_volume.set(settings['volume'])
        elif 'original_audio_volume' in settings:
            self.original_audio_volume.set(settings['original_audio_volume'])
        
        # Update the info label
        self._update_settings_info_label()

        # Notify other tabs about shared settings changes
        self._notify_other_tabs_of_settings_change(settings)

    def _update_settings_info_label(self):
        """Update the settings info label with current settings"""
        # TTS info (primary - matches image tab style)
        tts_voice = self.current_settings.get('tts_voice_actor', 'Default')
        tts_speed = f"{self.current_settings.get('tts_speed', 1.0):.1f}x"
        tts_emotion = self.current_settings.get('tts_emotion', 'neutral').title()

        # Output info
        output_folder = self.current_settings.get('output_folder', 'Default (Auto)')
        output_name = "Default" if output_folder == "Default (Auto)" else "Custom"

        # Clean label matching image tab style
        info_text = f"TTS: {tts_voice}, {tts_speed} Speed, {tts_emotion} | Output: {output_name}"
        self.settings_info_label.config(text=info_text)

    def _notify_other_tabs_of_settings_change(self, settings):
        """Notify other tabs when shared settings change"""
        try:
            # Check if settings contain shared TTS settings
            shared_keys = ['tts_language', 'tts_voice_actor', 'tts_speed', 'tts_emotion', 'output_folder']
            has_shared_changes = any(key in settings for key in shared_keys)

            if has_shared_changes and hasattr(self.main_gui, 'image_tab_component'):
                # Check if image tab component is properly initialized with current_settings
                if hasattr(self.main_gui.image_tab_component, 'current_settings') and hasattr(self.main_gui.image_tab_component, '_update_settings_info_label'):
                    # Update image tab's current settings and refresh its label
                    self.main_gui.image_tab_component.current_settings.update(settings)
                    self.main_gui.image_tab_component._update_settings_info_label()

                # Apply TTS settings to model from image tab perspective too
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
            tab_settings = settings_manager.get_tab_settings('video_tab')

            # Update current settings with latest from file
            self.current_settings.update(tab_settings)

            # Update the label to reflect any changes
            self._update_settings_info_label()

        except Exception as e:
            print(f"Warning: Could not refresh settings from file: {e}")

    def setup_scrollable_area(self, parent):
        """Set up scrollable area for video entries"""
        # Video entries section header
        entries_header = ttk.Frame(parent)
        entries_header.pack(fill="x", pady=(0, 10))

        entries_title = ttk.Label(
            entries_header,
            text="📹 Entries",
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
        from ui.components.dropdown_menu import create_video_content_dropdown
        self.content_dropdown = create_video_content_dropdown(
            entries_header,
            load_folder_command=self.load_videos_from_folder,
            select_multiple_command=self.select_multiple_videos,
            width=20
        )
        self.content_dropdown.pack(side="right", padx=(0, 4))

        # Create canvas and scrollbar with better styling
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Canvas with better styling - much smaller height for compact fit
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

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling in the canvas"""
        self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_video_entry(self, video_file=None, prompt=None):
        """Add a new video entry to the list with duplicate prevention"""
        # Hide empty state when adding first entry
        self.hide_empty_state()

        # Check for duplicates if video_file is provided
        if video_file:
            existing_files = self._get_existing_video_files()
            if video_file in existing_files:
                # Skip logging for individual duplicates to reduce clutter
                return None

        entry_id = self.next_entry_id
        self.next_entry_id += 1

        # Create new video entry
        video_entry = VideoEntry(
            self.entries_frame,
            self.main_gui,
            self.remove_video_entry,
            entry_id
        )

        # Set data if provided
        if video_file is not None:
            video_entry.set_data(video_file, prompt or "")

        # Store the entry
        self.video_entries[entry_id] = video_entry

        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

        self.main_gui.log(f"Added video entry #{entry_id}")
        return entry_id

    def remove_video_entry(self, entry_id):
        """Remove a video entry from the list"""
        if entry_id in self.video_entries:
            # Remove the entry
            self.video_entries[entry_id].destroy()
            del self.video_entries[entry_id]

            # If no entries left, show empty state
            if not self.video_entries and not self.group_entries:
                self.show_empty_state()

            # Update scroll region
            self.scrollable_frame.update_idletasks()
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

            self.main_gui.log(f"Removed video entry #{entry_id}")

    def get_valid_entries(self):
        """Get all valid video entries (individual or grouped)"""
        if self.current_mode == "grouped":
            return self.get_valid_groups()
        else:
            return self.get_valid_individual_entries()

    def get_valid_individual_entries(self):
        """Get all valid individual video entries"""
        valid_entries = []
        for entry_id, entry in self.video_entries.items():
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
                    has_video = bool(pair.get('video_file'))
                    has_prompt = bool(pair.get('prompt'))
                    self.main_gui.log(f"  - Pair {i+1}: Video={has_video}, Prompt={has_prompt}")
        
        self.main_gui.log(f"Found {len(valid_groups)} valid groups")
        return valid_groups

    def clear_all_entries(self):
        """Clear all video entries (both individual and grouped)"""
        # Remove all individual entries
        for entry_id in list(self.video_entries.keys()):
            self.video_entries[entry_id].destroy()
        
        # Remove all group entries  
        for group_id in list(self.group_entries.keys()):
            self.group_entries[group_id].destroy()
        
        # Clear the dictionaries
        self.video_entries.clear()
        self.group_entries.clear()
        self.next_entry_id = 1
        self.next_group_id = 1
        
        # Reset to individual mode
        self.current_mode = "individual"

        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def load_videos_from_folder(self):
        """SMART AUTO-DETECTION: Load videos with intelligent grouping detection"""
        # Show simple Windows folder dialog
        folder_path = filedialog.askdirectory(
            title="Select Folder to Load Videos From",
            mustexist=True
        )
        
        if not folder_path:
            return
            
        try:
            self.main_gui.log(f"Loading videos from: {os.path.basename(folder_path)}")

            # Use smart auto-detection logic
            detection_result = self.folder_processor.smart_analyze_folder(folder_path)
            
            # Check if any videos were found
            if detection_result['processing_mode'] == 'grouped':
                if not detection_result.get('groups'):
                    self._show_no_videos_found()
                    return
            else:
                if not detection_result.get('pairs'):
                    self._show_no_videos_found()
                    return
            
            # Apply the smart detection result
            if detection_result['processing_mode'] == 'grouped':
                self._load_as_groups(detection_result)
            else:
                self._load_as_individual(detection_result)
            
            # Show smart notification
            SmartNotification.show_detection_result(
                self.scrollable_frame, 
                detection_result, 
                self._handle_detection_override
            )
            

            
        except Exception as e:
            from utils.error_helpers import show_error_with_log
            show_error_with_log(self.main_gui, "Error Loading Folder", "Unexpected error occurred", e)

    def _show_no_videos_found(self):
        """Show user-friendly message when no videos are found"""
        messagebox.showwarning(
            "No Videos Found",
            "No video files found in the selected folder.\n\n"
            "Supported video formats:\n"
            "• .mp4, .avi, .mov, .mkv, .wmv, .flv\n\n"
            "Text prompts are optional - you can:\n"
            "• Include text files for automatic pairing\n"
            "• Add prompts manually after loading videos"
        )

    def _load_as_groups(self, detection_result):
        """Load videos as grouped entries with duplicate prevention"""
        groups = detection_result['groups']

        # Check for duplicate folder paths if we're not clearing all entries
        existing_folder_paths = self._get_existing_folder_paths()
        new_groups = {}
        duplicate_count = 0

        for group_name, group_info in groups.items():
            folder_path = group_info.get('folder_path', '')
            if folder_path and folder_path in existing_folder_paths:
                duplicate_count += 1
                continue
            new_groups[group_name] = group_info

        # Only clear if we have new groups to add
        if new_groups:
            # If this is the first load or user wants to replace, clear existing entries
            if not self.group_entries:
                self.clear_all_entries()

            # Set to grouped mode AFTER clearing (since clear resets to individual)
            self.current_mode = "grouped"

            # Create group entries for new groups only
            for group_name, group_info in new_groups.items():
                self.add_group_entry(group_info)

            if duplicate_count > 0:
                self.main_gui.log(f"Loaded {len(new_groups)} new groups, skipped {duplicate_count} duplicates")
            else:
                self.main_gui.log(f"Loaded {len(new_groups)} groups")
        else:
            if duplicate_count > 0:
                self.main_gui.log(f"No new groups loaded, skipped {duplicate_count} duplicates")
            else:
                self.main_gui.log("No groups found to load")

    def _load_as_individual(self, detection_result):
        """Load videos as individual entries"""
        self.current_mode = "individual"
        
        # Extract all pairs from all groups
        all_pairs = []
        if 'groups' in detection_result:
            groups = detection_result['groups']
            if isinstance(groups, dict):
                # groups is a dictionary {group_name: group_info}
                for group_name, group_info in groups.items():
                    all_pairs.extend(group_info.get('pairs', []))
            else:
                # groups is a list of group_info objects
                for group_info in groups:
                    all_pairs.extend(group_info.get('pairs', []))
        else:
            # Fallback for direct pairs (shouldn't happen in current implementation)
            all_pairs = detection_result.get('pairs', [])
        
        # Check for duplicates and handle them
        existing_files = self._get_existing_video_files()
        new_pairs = [pair for pair in all_pairs if pair['video_file'] not in existing_files]

        # Add individual entries with smart population
        empty_entry_id = self._find_empty_entry()
        created_entries = []
        populated_entries = []

        # Process pairs one by one
        for i, pair in enumerate(new_pairs):
            if i == 0 and empty_entry_id is not None:
                # Populate the first empty entry with the first pair
                entry = self.video_entries[empty_entry_id]
                entry.set_data(pair['video_file'], pair['prompt'])
                populated_entries.append(empty_entry_id)
            else:
                # Create new entries for remaining pairs
                entry_id = self.add_video_entry(pair['video_file'], pair['prompt'])
                if entry_id is not None:
                    created_entries.append(entry_id)

        # Log results concisely
        total_pairs = len(all_pairs)
        new_count = len(new_pairs)
        duplicate_count = total_pairs - new_count

        if new_count > 0:
            if duplicate_count > 0:
                self.main_gui.log(f"Loaded {new_count} videos, skipped {duplicate_count} duplicates")
            else:
                self.main_gui.log(f"Loaded {new_count} videos")
        else:
            if duplicate_count > 0:
                self.main_gui.log(f"No new videos loaded, skipped {duplicate_count} duplicates")
            else:
                self.main_gui.log("No videos found to load")

    def _handle_detection_override(self, detection_result):
        """Handle user override of smart detection"""
        # Toggle between modes
        if detection_result['processing_mode'] == 'grouped':
            # Switch to individual mode
            self._load_as_individual(detection_result)
            self.main_gui.log("Switched to individual video mode")
        else:
            # Switch to grouped mode
            self._load_as_groups(detection_result)
            self.main_gui.log("Switched to grouped video mode")

    def add_group_entry(self, group_info):
        """Add a new group entry to the UI"""
        # Hide empty state when adding first entry
        self.hide_empty_state()

        group_id = self.next_group_id
        self.next_group_id += 1
        
        # Create group entry
        group_entry = GroupEntry(
            self.scrollable_frame, 
            self.main_gui, 
            self.remove_group_entry, 
            group_id, 
            group_info
        )
        
        self.group_entries[group_id] = group_entry
        return group_id

    def remove_group_entry(self, group_id):
        """Remove a group entry from the UI"""
        if group_id in self.group_entries:
            self.group_entries[group_id].destroy()
            del self.group_entries[group_id]

            # If no entries left, show empty state
            if not self.video_entries and not self.group_entries:
                self.show_empty_state()

            # Update scroll region
            self.scrollable_frame.update_idletasks()
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

            self.main_gui.log(f"Removed group entry #{group_id}")

    def _scan_folder_for_pairs(self, folder_path):
        """Scan folder for video+text file pairs"""
        from utils.media_helpers import scan_folder_for_media_pairs

        # Use centralized media pair scanning
        media_pairs = scan_folder_for_media_pairs(folder_path, media_type="video")

        # Convert to expected format
        pairs = []
        for pair in media_pairs:
            pairs.append({
                'video_file': pair['media_file'],
                'text_file': pair['text_file'],
                'directory': pair['directory']
            })

        return pairs

    def _match_video_text_pairs(self, videos, texts):
        """Match video and text files with priority-based matching"""
        pairs = []
        used_texts = set()
        
        for video_path in videos:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            best_match = None
            best_priority = 0
            
            for text_path in texts:
                if text_path in used_texts:
                    continue
                
                text_name = os.path.splitext(os.path.basename(text_path))[0]
                priority = 0
                
                # Priority 1: Exact name match
                if video_name.lower() == text_name.lower():
                    priority = 3
                # Priority 2: Common prompt names
                elif text_name.lower() in ['prompt', 'script', 'text', 'voiceover']:
                    priority = 2
                # Priority 3: Text name contained in video name or vice versa
                elif (text_name.lower() in video_name.lower() or 
                      video_name.lower() in text_name.lower()):
                    priority = 1
                
                if priority > best_priority:
                    best_match = text_path
                    best_priority = priority
            
            # If we found a match, create pair
            if best_match:
                try:
                    with open(best_match, 'r', encoding='utf-8') as f:
                        prompt_text = f.read().strip()
                    
                    if prompt_text:  # Only add if there's actual text content
                        pairs.append({
                            'video_file': video_path,
                            'prompt': prompt_text,
                            'confidence': best_priority
                        })
                        used_texts.add(best_match)
                
                except Exception as e:
                    self.main_gui.log(f"Failed to read text file {os.path.basename(best_match)}: {e}")
        
        return pairs

    def _get_existing_video_files(self):
        """Get list of video files already loaded in entries"""
        existing_files = []
        for entry in self.video_entries.values():
            data = entry.get_data()
            if data['video_file']:
                existing_files.append(data['video_file'])
        return existing_files

    def _get_existing_folder_paths(self):
        """Get list of folder paths already loaded in group entries"""
        existing_paths = []
        for group_entry in self.group_entries.values():
            group_data = group_entry.get_group_data()
            folder_path = group_data.get('folder_path', '')
            if folder_path:
                existing_paths.append(folder_path)
        return existing_paths

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
        """Find the first empty entry (no video file and no prompt)"""
        for entry_id, entry in self.video_entries.items():
            data = entry.get_data()
            # Check if entry is empty (no video file and no prompt)
            has_video = data.get('video_file', '').strip()
            has_prompt = data.get('prompt', '').strip()

            # Entry is empty if it has no video file and no prompt
            if not has_video and not has_prompt:
                return entry_id
        return None

    def select_multiple_videos(self):
        """Select multiple individual video files and create entries"""
        from utils.dialog_helpers import select_video_files

        try:
            # Show file selection dialog
            selected_files = select_video_files(title="Select Multiple Videos", multiple=True)

            if not selected_files:
                return

            # Convert to list if it's a tuple
            if isinstance(selected_files, tuple):
                selected_files = list(selected_files)
            elif isinstance(selected_files, str):
                selected_files = [selected_files]

            # Get existing videos to handle duplicates with numbering
            existing_videos = self._get_existing_video_files()

            # Generate unique names for duplicates
            processed_videos = []
            for vid in selected_files:
                if vid in existing_videos:
                    # Generate unique name with numbering
                    unique_name = self._generate_unique_name(vid, existing_videos)
                    processed_videos.append(unique_name)
                    existing_videos.append(unique_name)  # Add to list to avoid conflicts
                else:
                    processed_videos.append(vid)
                    existing_videos.append(vid)

            new_videos = processed_videos

            # Try to find an existing empty entry to populate first
            empty_entry_id = self._find_empty_entry()
            created_entries = []
            populated_entries = []

            # Process videos one by one
            for i, video_file in enumerate(new_videos):
                if i == 0 and empty_entry_id is not None:
                    # Populate the first empty entry with the first video
                    entry = self.video_entries[empty_entry_id]
                    entry.set_data(video_file, "")
                    populated_entries.append(empty_entry_id)
                else:
                    # Create new entries for remaining videos
                    entry_id = self.add_video_entry(video_file, "")
                    if entry_id is not None:
                        created_entries.append(entry_id)

            # Log results
            duplicate_count = len(selected_files) - len([vid for vid in selected_files if vid not in self._get_existing_video_files()])
            if populated_entries and created_entries:
                if duplicate_count > 0:
                    self.main_gui.log(f"Populated entry #{populated_entries[0]}, created {len(created_entries)} new entries, {duplicate_count} duplicates renamed with numbers")
                else:
                    self.main_gui.log(f"Populated entry #{populated_entries[0]}, created {len(created_entries)} new entries")
            elif populated_entries:
                if duplicate_count > 0:
                    self.main_gui.log(f"Populated entry #{populated_entries[0]}, {duplicate_count} duplicates renamed with numbers")
                else:
                    self.main_gui.log(f"Populated entry #{populated_entries[0]}")
            elif created_entries:
                if duplicate_count > 0:
                    self.main_gui.log(f"Created {len(created_entries)} new video entries, {duplicate_count} duplicates renamed with numbers")
                else:
                    self.main_gui.log(f"Created {len(created_entries)} new video entries")

        except Exception as e:
            self.main_gui.log(f"Error selecting multiple videos: {str(e)}")
            if self.progress_manager:
                self.progress_manager.show_error("Selection Error", f"Failed to select videos: {str(e)}")
            else:
                messagebox.showerror("Selection Error", f"Failed to select videos: {str(e)}")

    def start_video_generation(self):
        """Start the multi-video generation process"""
        self.main_gui.log(f"DEBUG: start_video_generation called, current_mode={self.current_mode}")
        
        # Check if generation is already running
        if self.main_gui.generation_thread and self.main_gui.generation_thread.is_alive():
            messagebox.showwarning("Process Running", "Video generation is already in progress")
            return

        # Get valid entries
        self.main_gui.log("DEBUG: About to call get_valid_entries()")
        valid_entries = self.get_valid_entries()
        self.main_gui.log(f"DEBUG: get_valid_entries returned {len(valid_entries) if valid_entries else 0} entries")

        if not valid_entries:
            if self.current_mode == "grouped":
                messagebox.showwarning("No Valid Groups", "Please add at least one group with videos.")
            else:
                messagebox.showwarning("No Valid Entries", "Please add at least one video file.")
            return

        # Confirm with user
        if self.current_mode == "grouped":
            total_videos = sum(len(group['pairs']) for group in valid_entries)
            response = messagebox.askyesno(
                "Confirm Group Generation",
                f"Generate {len(valid_entries)} combined videos from {total_videos} source videos?\n\nThis may take a while."
            )
        else:
            response = messagebox.askyesno(
                "Confirm Generation",
                f"Generate videos for {len(valid_entries)} entries?\n\nThis may take a while."
            )

        if not response:
            return

        # Use the selected output folder from the current settings with improved logic
        output_folder_value = self.current_settings.get('output_folder', 'Default (Auto)')

        if output_folder_value and output_folder_value.strip() and output_folder_value != "Default (Auto)" and os.path.exists(output_folder_value):
            self.main_gui.log(f"Using selected output folder: {output_folder_value}")
            self.main_gui.model.output_folder = output_folder_value
        else:
            # Use improved output folder logic that respects user settings
            from utils.helpers import get_output_directory
            default_folder = get_output_directory(self.current_settings)
            self.main_gui.model.output_folder = default_folder
            self.main_gui.log(f"Using output folder: {default_folder}")

        # Clear any existing batch jobs
        self.main_gui.model.batch_jobs.clear()

        # Process differently based on current mode
        if self.current_mode == "grouped":
            self._add_grouped_batch_jobs(valid_entries)
        else:
            self._add_individual_batch_jobs(valid_entries)

        # Apply current TTS settings to model before generation
        self.main_gui.model.tts_settings = {
            'language': self.current_settings.get('tts_language', 'en'),
            'voice_actor': self.current_settings.get('tts_voice_actor', 'Guy'),
            'speed': self.current_settings.get('tts_speed', 1.0),
            'emotion': self.current_settings.get('tts_emotion', 'neutral')
        }

        # Set up progress callback
        self.main_gui.model.set_progress_callback(self.update_video_progress)

        # Start processing
        self.video_progress_bar["value"] = 0
        self.video_progress_label.config(text="0%")
        self.generate_button.config(state="disabled")
        self.stop_button.config(state="normal")

        # Create stop event and start thread
        self.main_gui.stop_event = threading.Event()
        self.main_gui.generation_thread = threading.Thread(target=self.process_video_batch)
        self.main_gui.generation_thread.daemon = True
        self.main_gui.generation_thread.start()

        entry_count = len(valid_entries)
        mode_text = "group(s)" if self.current_mode == "grouped" else "video(s)"
        self.main_gui.log(f"Started processing {entry_count} {mode_text}")

    def _add_individual_batch_jobs(self, valid_entries):
        """Add individual video jobs to batch processing"""
        for i, entry_data in enumerate(valid_entries):
            # Add audio settings to the entry data from current settings
            # Check both new and legacy setting names
            mute_value = self.current_settings.get('mute_original_audio', self.current_settings.get('mute', False))
            volume_value = self.current_settings.get('original_audio_volume', self.current_settings.get('volume', 0.7))
            entry_data["mute_original_audio"] = mute_value
            entry_data["original_audio_volume"] = volume_value

            # For video processing, we'll use the video file as the "image source"
            # and the prompt as the text input
            job_id = self.main_gui.model.add_video_batch_job(
                text_input=entry_data["prompt"],
                video_file=entry_data["video_file"],
                audio_settings={
                    "mute_original": entry_data["mute_original_audio"],
                    "original_volume": entry_data["original_audio_volume"]
                },
                custom_filename=entry_data.get("custom_filename", "")
            )
            self.main_gui.log(f"Added video job #{job_id}: {os.path.basename(entry_data['video_file'])}")

    def _add_grouped_batch_jobs(self, valid_groups):
        """Add grouped video jobs to batch processing"""
        for group_data in valid_groups:
            # Add group job to batch processing
            # Check both new and legacy setting names
            mute_value = self.current_settings.get('mute_original_audio', self.current_settings.get('mute', False))
            volume_value = self.current_settings.get('original_audio_volume', self.current_settings.get('volume', 0.7))
            job_id = self.main_gui.model.add_group_batch_job(
                group_data=group_data,
                audio_settings={
                    "mute_original": mute_value,
                    "original_volume": volume_value
                }
            )
            self.main_gui.log(f"Added group job #{job_id}: {group_data['output_name']} ({len(group_data['pairs'])} videos)")

    def process_video_batch(self):
        """Process the video batch in a separate thread"""
        try:
            results = self.main_gui.model.process_video_batch(self.main_gui.stop_event)

            if self.main_gui.stop_event.is_set():
                self.main_gui.root.after(0, lambda: self.main_gui.log("Video processing stopped by user"))
                self.main_gui.root.after(0, lambda: self.reset_video_ui())
                return

            # Process results
            successful = len([r for _, r in results if r])
            total = len(results)

            self.main_gui.root.after(0, lambda: self.video_batch_completed(successful, total, results))

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.main_gui.root.after(0, lambda: self.main_gui.log(f"Error processing videos: {e}"))
            self.main_gui.root.after(0, lambda: self.reset_video_ui())

    def video_batch_completed(self, successful, total, results):
        """Handle completion of video batch processing"""
        self.main_gui.log(f"Video processing completed: {successful}/{total} successful")
        self.update_video_progress(100, f"Completed: {successful}/{total} videos")
        self.reset_video_ui()

        # Initialize total_cleaned variable to prevent UnboundLocalError
        total_cleaned = 0

        # Auto-cleanup for ALL video generation to keep only final outputs
        cleanup_enabled = getattr(config, 'AUTO_CLEANUP_AFTER_COMPLETION', True)
        
        if successful > 0 and cleanup_enabled:  # Clean up if any videos were successful and cleanup is enabled
            self.main_gui.log("Starting automatic cleanup of intermediate files...")
            
            # Track which output directories we've already cleaned to avoid duplicates
            cleaned_dirs = set()
            
            for job, video_path in results:  # Fixed: correct order (job, video_path)
                try:
                    # Check if video_path is valid and not None
                    if video_path and isinstance(video_path, str) and os.path.exists(video_path):
                        # Extract output directory from the video path
                        output_dir = os.path.dirname(video_path)
                        
                        # Skip if we've already cleaned this directory
                        if output_dir in cleaned_dirs:
                            continue
                        
                        cleaned_dirs.add(output_dir)
                        
                        # Extract video name from the path for context
                        video_name = os.path.splitext(os.path.basename(video_path))[0]
                        
                        # Clean up intermediate files for this video
                        cleaned_count = self._cleanup_intermediate_files(video_path)
                        total_cleaned += cleaned_count
                        
                        if cleaned_count > 0:
                            self.main_gui.log(f"Cleaned {cleaned_count} files for {video_name}")
                        else:
                            self.main_gui.log(f"No cleanup needed for {video_name}")
                except Exception as e:
                    self.main_gui.log(f"Cleanup failed for a video: {e}")
            
            if total_cleaned > 0:
                self.main_gui.log(f"Auto-cleanup completed: Removed {total_cleaned} intermediate files")
                self.main_gui.log("Only final_output.mp4 files remain for each video")
            else:
                self.main_gui.log("No intermediate files needed cleanup")
        elif not cleanup_enabled:
            self.main_gui.log("Auto-cleanup disabled in config - keeping all files")
        else:
            self.main_gui.log("No successful videos to clean up")

        # Create completion message
        message = f"Successfully generated {successful} out of {total} videos."
        
        if successful > 0 and total_cleaned > 0:
            message += f"\n\nAuto-cleanup completed\nRemoved {total_cleaned} intermediate files\nOnly final_output.mp4 files remain"
        
        # Show completion message
        if successful > 0:
            message += "\n\nWould you like to open the output folder?"
            response = messagebox.askyesno("Processing Complete", message)
            if response and results:
                # Find the first successful result and open its parent directory
                for job, video_path in results:  # Fixed: correct order (job, video_path)
                    if video_path and isinstance(video_path, str) and os.path.exists(video_path):
                        # Go up one level to show all video folders
                        video_dir = os.path.dirname(video_path)
                        parent_dir = os.path.dirname(video_dir)
                        if os.path.exists(parent_dir):
                            self.main_gui.open_file(parent_dir)
                        else:
                            self.main_gui.open_file(video_dir)
                        break
        else:
            messagebox.showerror("Processing Failed", "No videos were generated successfully.")

    def stop_video_generation(self):
        """Stop the video generation process"""
        if self.main_gui.stop_event:
            self.main_gui.stop_event.set()
            self.main_gui.log("Stopping video processing...")
            self.main_gui.root.after(1000, self.reset_video_ui)

    def update_video_progress(self, value, message=None):
        """Update the video processing progress"""
        if self.progress_manager:
            # Use progress manager if available
            self.progress_manager.update_progress(value, message)
            return

        # Use standardized progress update function
        from utils.gui_helpers import standardize_progress_update
        standardize_progress_update(self.video_progress_bar, self.video_progress_label, value, message)

    def reset_video_ui(self):
        """Reset the video tab UI to initial state"""
        self.generate_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        if self.progress_manager:
            # Use progress manager if available
            self.progress_manager.reset()
        else:
            # Legacy fallback
            self.video_progress_bar["value"] = 0
            self.video_progress_label.config(text="0%")

    def _cleanup_intermediate_files(self, video_path):
        """Clean up intermediate files for a video - calls main cleanup function"""
        output_dir = os.path.dirname(video_path)
        try:
            # Use the consolidated cleanup function from the model
            cleaned_count = self.main_gui.model.cleanup_after_video_complete(
                output_dir, 
                keep_debug_files=False  # For multi-video, always clean everything except final_output.mp4
            )
            return cleaned_count
        except Exception as e:
            self.main_gui.log(f"Cleanup failed for {os.path.basename(video_path)}: {e}")
            return 0
    
    