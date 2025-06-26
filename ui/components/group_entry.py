"""
Group Entry Component - UI component for managing grouped video entries
Handles display and editing of video groups that will be combined into single outputs
"""
from utils.common_imports import tk, ttk
import os


class GroupEntry:
    """Group entry component for managing grouped video processing"""

    def __init__(self, parent_frame, main_gui, remove_callback, group_id, group_info):
        self.parent_frame = parent_frame
        self.main_gui = main_gui
        self.remove_callback = remove_callback
        self.group_id = group_id
        self.group_info = group_info

        # UI components
        self.entry_frame = None
        self.expanded = False

        # Custom filename support
        self.custom_filename = tk.StringVar()
        self.filename_entry = None

        self.setup_group_entry()

    def setup_group_entry(self):
        """Set up the UI for this group entry"""
        # Main group frame without title - we'll create custom header
        self.entry_frame = ttk.LabelFrame(
            self.parent_frame,
            text="",  # Empty title, we'll create custom header
            padding=8
        )
        self.entry_frame.pack(fill="x", padx=6, pady=4)

        # Header row with group label, custom filename, and buttons on same line
        self.setup_group_header()

        # Group summary section
        self.setup_group_summary()

        # Expandable details section (collapsed by default)
        self.details_frame = None

    def setup_group_header(self):
        """Set up the group header with group label, custom filename, and buttons on same line"""
        # Header row with group label, custom filename, and buttons on same line
        header_frame = ttk.Frame(self.entry_frame)
        header_frame.pack(fill="x", pady=(0, 8))

        # Group label on the left
        group_label = ttk.Label(
            header_frame,
            text=f"📦 {self.group_info['folder_name']} ({len(self.group_info['pairs'])} videos)",
            font=("Cascadia Code", 10, "bold")
        )
        group_label.pack(side="left")

        # Custom filename section in the middle
        filename_section = ttk.Frame(header_frame)
        filename_section.pack(side="left", padx=(20, 0))

        # Custom filename entry
        self.filename_entry = ttk.Entry(
            filename_section,
            textvariable=self.custom_filename,
            font=("Cascadia Code", 9),
            width=30
        )
        self.filename_entry.pack(side="left", padx=(0, 2))

        # .mp4 label
        mp4_label = ttk.Label(
            filename_section,
            text=".mp4",
            font=("Cascadia Code", 9),
            foreground="#7f8c8d"
        )
        mp4_label.pack(side="left")

        # Placeholder text - make it shorter and cleaner
        self.filename_entry.insert(0, "Custom filename (optional)")
        self.filename_entry.config(foreground="#999999")

        # Bind events for placeholder behavior
        self.filename_entry.bind('<FocusIn>', self._on_filename_focus_in)
        self.filename_entry.bind('<FocusOut>', self._on_filename_focus_out)
        self.filename_entry.bind('<KeyRelease>', self._on_filename_change)

        # Right side - action buttons
        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side="right")

        # Expand/collapse icon (consistent with remove icon)
        from config import GUI_COLORS
        self.expand_button = tk.Button(
            button_frame,
            text="🔽",
            font=("Segoe UI", 10, "bold"),
            fg=GUI_COLORS["text"],  # Dark text color
            bg=GUI_COLORS["background"],  # Light gray background
            relief="flat",
            borderwidth=0,
            width=2,
            height=1,
            command=self.toggle_details,
            cursor="hand2",
            highlightthickness=0,
            takefocus=False
        )
        self.expand_button.pack(side="right", padx=(4, 0))

        # Remove group button (icon only) - consistent with single entries
        remove_button = tk.Button(
            button_frame,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            fg=GUI_COLORS["text"],  # Dark text color instead of red
            bg=GUI_COLORS["background"],  # Light gray background
            relief="flat",
            borderwidth=0,
            width=2,
            height=1,
            command=lambda: self.remove_callback(self.group_id),
            cursor="hand2",
            highlightthickness=0,
            takefocus=False
        )
        remove_button.pack(side="right", padx=(4, 0))

    def setup_group_summary(self):
        """Set up the group summary display"""
        # Summary row with video list preview
        summary_frame = ttk.Frame(self.entry_frame)
        summary_frame.pack(fill="x", pady=(0, 6))

        # Video list preview
        video_names = [os.path.basename(pair['video_file']) for pair in self.group_info['pairs']]
        preview_text = ", ".join(video_names[:3])  # Show first 3
        if len(video_names) > 3:
            preview_text += f", ... (+{len(video_names) - 3} more)"

        video_preview_label = ttk.Label(
            summary_frame,
            text=f"🎥 {preview_text}",
            font=("Cascadia Code", 9),
            foreground="#666666"
        )
        video_preview_label.pack(anchor="w")

    def toggle_details(self):
        """Toggle the expanded details view"""
        if self.expanded:
            self.collapse_details()
        else:
            self.expand_details()

    def expand_details(self):
        """Show detailed view of all videos in the group"""
        self.expanded = True
        self.expand_button.config(text="🔼")

        # Create details frame
        self.details_frame = ttk.Frame(self.entry_frame)
        self.details_frame.pack(fill="x", pady=(6, 0))

        # Add separator
        separator = ttk.Separator(self.details_frame, orient="horizontal")
        separator.pack(fill="x", pady=(0, 8))

        # Individual video entries
        for i, pair in enumerate(self.group_info['pairs']):
            self.create_video_detail_entry(self.details_frame, i, pair)

    def collapse_details(self):
        """Hide the detailed view"""
        self.expanded = False
        self.expand_button.config(text="🔽")

        if self.details_frame:
            self.details_frame.destroy()
            self.details_frame = None

    def create_video_detail_entry(self, parent, index, pair):
        """Create a detailed entry for one video in the group"""
        # Individual video frame - cleaner title
        video_frame = ttk.LabelFrame(
            parent,
            text=f"🎬 {index + 1}: {os.path.basename(pair['video_file'])}",
            padding=6
        )
        video_frame.pack(fill="x", pady=2)

        # Video file path (read-only) - remove redundant label
        path_frame = ttk.Frame(video_frame)
        path_frame.pack(fill="x", pady=(0, 4))

        path_entry = ttk.Entry(
            path_frame,
            font=("Cascadia Code", 9),
            state="readonly",
            width=60
        )
        path_entry.pack(fill="x", expand=True)
        path_entry.config(state="normal")
        path_entry.insert(0, pair['video_file'])
        path_entry.config(state="readonly")

        # Prompt text (editable) - remove redundant label
        prompt_frame = ttk.Frame(video_frame)
        prompt_frame.pack(fill="x")

        prompt_text = tk.Text(
            prompt_frame,
            height=2,
            wrap="word",
            font=("Cascadia Code", 9),
            relief="solid",
            borderwidth=1,
            padx=4,
            pady=2
        )
        prompt_text.pack(fill="x")
        prompt_text.insert("1.0", pair['prompt'])

        # Store reference to update data later
        pair['prompt_widget'] = prompt_text

    def _on_filename_focus_in(self, event):
        """Handle filename entry focus in (remove placeholder)"""
        if self.filename_entry.get() == "Custom filename (optional)":
            self.filename_entry.delete(0, tk.END)
            self.filename_entry.config(foreground="black")

    def _on_filename_focus_out(self, event):
        """Handle filename entry focus out (add placeholder if empty)"""
        if not self.filename_entry.get().strip():
            self.filename_entry.delete(0, tk.END)
            self.filename_entry.insert(0, "Custom filename (optional)")
            self.filename_entry.config(foreground="#999999")
            self.custom_filename.set("")
        else:
            self.custom_filename.set(self.filename_entry.get().strip())

    def _on_filename_change(self, event):
        """Handle filename entry changes with validation"""
        current_text = self.filename_entry.get()
        if current_text != "Custom filename (optional)":
            # Validate filename in real-time
            from utils.filename_validator import validate_and_suggest_filename
            validate_and_suggest_filename(current_text)

            # Update the StringVar with the current value
            self.custom_filename.set(current_text.strip())

    def get_group_data(self):
        """Get the current group data with any user modifications"""
        # Update prompts from UI if details are expanded
        if self.expanded and self.details_frame:
            for pair in self.group_info['pairs']:
                # Update prompt
                if 'prompt_widget' in pair:
                    pair['prompt'] = pair['prompt_widget'].get("1.0", tk.END).strip()

        # Get group custom filename or use default
        custom_filename = self.custom_filename.get().strip()
        if custom_filename and custom_filename != "Custom filename (optional)":
            # Use custom filename with .mp4 extension
            from utils.filename_validator import get_final_output_filename
            output_name = get_final_output_filename(custom_filename, os.path.splitext(self.group_info['output_name'])[0])
        else:
            # Use default output name
            output_name = self.group_info['output_name']

        return {
            "group_id": self.group_id,
            "folder_name": self.group_info['folder_name'],
            "output_name": output_name,
            "custom_filename": custom_filename,
            "pairs": self.group_info['pairs']
        }

    def is_valid(self):
        """Check if this group has valid data"""
        if not self.group_info or not self.group_info.get('pairs'):
            self.main_gui.log(f"Group {self.group_id} invalid: No group info or pairs")
            return False

        # Check if at least one pair has a video file (prompt is optional)
        valid_pairs = 0
        for i, pair in enumerate(self.group_info['pairs']):
            video_file = pair.get('video_file', '').strip()
            prompt = pair.get('prompt', '').strip()

            self.main_gui.log(f"Group {self.group_id} Pair {i+1}: video_file='{video_file}', prompt_len={len(prompt)}")

            # Only require video file - prompt is optional
            if video_file:
                valid_pairs += 1

        is_valid = valid_pairs > 0
        self.main_gui.log(f"Group {self.group_id} validation result: {valid_pairs} valid pairs, is_valid={is_valid}")
        return is_valid

    def destroy(self):
        """Remove this group entry from the UI"""
        if self.entry_frame:
            self.entry_frame.destroy()


class SmartNotification:
    """Smart notification component for auto-detection feedback"""

    @staticmethod
    def show_detection_result(parent, detection_result, override_callback=None):
        """Show smart detection notification with optional override"""
        # Create notification frame
        notification_frame = ttk.Frame(parent)
        notification_frame.pack(fill="x", pady=(4, 8))

        # Notification content
        content_frame = ttk.Frame(notification_frame)
        content_frame.pack(side="left", fill="x", expand=True)

        # Smart detection icon and message
        message_label = ttk.Label(
            content_frame,
            text=f"🧠 {detection_result['notification_message']}",
            font=("Cascadia Code", 10),
            foreground="#2ecc71"  # Green for success
        )
        message_label.pack(anchor="w")

        # Detection reason (smaller text)
        reason_label = ttk.Label(
            content_frame,
            text=f"   {detection_result['detection_reason']}",
            font=("Cascadia Code", 8),
            foreground="#7f8c8d"  # Gray for explanation
        )
        reason_label.pack(anchor="w")

        # Override button if available
        if detection_result.get('override_option') and override_callback:
            override_button = ttk.Button(
                notification_frame,
                text=detection_result['override_option'],
                command=lambda: override_callback(detection_result)
            )
            override_button.pack(side="right", padx=(8, 0))

        # Auto-hide notification after 5 seconds
        parent.after(5000, notification_frame.destroy)

        return notification_frame 