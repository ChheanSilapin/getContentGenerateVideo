"""
Group Entry Component - UI component for managing grouped video entries
Handles display and editing of video groups that will be combined into single outputs
"""
from utils.common_imports import tk, messagebox, ttk
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
        self.setup_group_entry()

    def setup_group_entry(self):
        """Set up the UI for this group entry"""
        # Main group frame with distinctive styling
        self.entry_frame = ttk.LabelFrame(
            self.parent_frame,
            text=f"📦 Group: {self.group_info['folder_name']} ({len(self.group_info['pairs'])} videos)",
            padding=8
        )
        self.entry_frame.pack(fill="x", padx=6, pady=4)

        # Group summary section
        self.setup_group_summary()

        # Expandable details section (collapsed by default)
        self.details_frame = None

    def setup_group_summary(self):
        """Set up the group summary display"""
        # Summary row
        summary_frame = ttk.Frame(self.entry_frame)
        summary_frame.pack(fill="x", pady=(0, 6))

        # Left side - group info
        info_frame = ttk.Frame(summary_frame)
        info_frame.pack(side="left", fill="x", expand=True)

        # Output file info
        output_label = ttk.Label(
            info_frame,
            text=f"📁 Output: {self.group_info['output_name']}",
            font=("Cascadia Code", 10, "bold")
        )
        output_label.pack(anchor="w")

        # Video list preview
        video_names = [os.path.basename(pair['video_file']) for pair in self.group_info['pairs']]
        preview_text = ", ".join(video_names[:3])  # Show first 3
        if len(video_names) > 3:
            preview_text += f", ... (+{len(video_names) - 3} more)"

        video_preview_label = ttk.Label(
            info_frame,
            text=f"🎥 Videos: {preview_text}",
            font=("Cascadia Code", 9),
            foreground="#666666"
        )
        video_preview_label.pack(anchor="w")

        # Right side - action buttons
        button_frame = ttk.Frame(summary_frame)
        button_frame.pack(side="right")

        # Expand/collapse button (icon only)
        self.expand_button = self.main_gui.ui_factory.create_icon_button(
            button_frame, "", self.toggle_details,
            icon="🔽", width=4
        )
        self.expand_button.pack(side="right", padx=(4, 0))

        # Remove group button (icon only)
        remove_button = self.main_gui.ui_factory.create_icon_button(
            button_frame, "", lambda: self.remove_callback(self.group_id),
            icon="🗑️", width=4
        )
        remove_button.pack(side="right", padx=(4, 0))

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
        # Individual video frame
        video_frame = ttk.LabelFrame(
            parent,
            text=f"🎬 Video {index + 1}: {os.path.basename(pair['video_file'])}",
            padding=6
        )
        video_frame.pack(fill="x", pady=2)

        # Video file path (read-only)
        path_frame = ttk.Frame(video_frame)
        path_frame.pack(fill="x", pady=(0, 4))

        ttk.Label(
            path_frame,
            text="📁 File:",
            font=("Cascadia Code", 9, "bold")
        ).pack(side="left")

        path_entry = ttk.Entry(
            path_frame,
            font=("Cascadia Code", 9),
            state="readonly",
            width=60
        )
        path_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        path_entry.config(state="normal")
        path_entry.insert(0, pair['video_file'])
        path_entry.config(state="readonly")

        # Prompt text (editable)
        prompt_frame = ttk.Frame(video_frame)
        prompt_frame.pack(fill="x")

        ttk.Label(
            prompt_frame,
            text="💬 Prompt:",
            font=("Cascadia Code", 9, "bold")
        ).pack(anchor="w", pady=(0, 2))

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

    def get_group_data(self):
        """Get the current group data with any user modifications"""
        # Update prompts from UI if details are expanded
        if self.expanded and self.details_frame:
            for pair in self.group_info['pairs']:
                if 'prompt_widget' in pair:
                    pair['prompt'] = pair['prompt_widget'].get("1.0", tk.END).strip()

        return {
            "group_id": self.group_id,
            "folder_name": self.group_info['folder_name'],
            "output_name": self.group_info['output_name'],
            "pairs": self.group_info['pairs']
        }

    def is_valid(self):
        """Check if this group has valid data"""
        if not self.group_info or not self.group_info.get('pairs'):
            self.main_gui.log(f"Group {self.group_id} invalid: No group info or pairs")
            return False
        
        # Check if at least one pair has both video file and prompt
        valid_pairs = 0
        for i, pair in enumerate(self.group_info['pairs']):
            video_file = pair.get('video_file', '').strip()
            prompt = pair.get('prompt', '').strip()
            
            self.main_gui.log(f"Group {self.group_id} Pair {i+1}: video_file='{video_file}', prompt_len={len(prompt)}")
            
            if video_file and prompt:
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