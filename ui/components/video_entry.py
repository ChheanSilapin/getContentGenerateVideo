"""
Video Entry Component - Individual video input entry
Extracted from video_tab.py for reusability and maintainability
"""
import tkinter as tk
from tkinter import ttk

class VideoEntry:
    """Individual video entry with file selector and prompt input"""

    def __init__(self, parent_frame, main_gui, remove_callback, entry_id):
        self.parent_frame = parent_frame
        self.main_gui = main_gui
        self.remove_callback = remove_callback
        self.entry_id = entry_id

        # Entry data
        self.video_file_path = tk.StringVar()
        self.prompt_text = tk.StringVar()
        self.custom_filename = tk.StringVar()

        # UI components
        self.entry_frame = None
        self.setup_entry()

    def setup_entry(self):
        """Set up the UI for this video entry - optimized with fewer frames"""
        # Main entry frame
        self.entry_frame = ttk.LabelFrame(self.parent_frame, text="", padding=8)
        self.entry_frame.pack(fill="x", padx=6, pady=4)

        # Single header row: label + filename + remove button
        header_row = ttk.Frame(self.entry_frame)
        header_row.pack(fill="x", pady=(0, 4))
        
        # Entry label on left
        #ttk.Label(header_row, text=f"🎬 {self.entry_id}", font=("Cascadia Code", 10, "bold")).pack(side="left")
        
        # Filename entry in middle
        self.filename_entry = ttk.Entry(header_row, textvariable=self.custom_filename, font=("Cascadia Code", 9), width=20)
        self.filename_entry.pack(side="left", padx=(10, 0))
        ttk.Label(header_row, text=".mp4", font=("Cascadia Code", 9), foreground="#7f8c8d").pack(side="left")
        
        # Remove button on right
        from config import GUI_COLORS
        tk.Button(
            header_row, text="✕", font=("Segoe UI", 10, "bold"),
            fg=GUI_COLORS["text"], bg=GUI_COLORS["background"],
            relief="flat", borderwidth=0, width=2,
            command=lambda: self.remove_callback(self.entry_id),
            cursor="hand2", highlightthickness=0, takefocus=False
        ).pack(side="right")

        # Placeholder text
        self.filename_entry.insert(0, "Custom filename (optional)")
        self.filename_entry.config(foreground="#999999")
        self.filename_entry.bind('<FocusIn>', self._on_filename_focus_in)
        self.filename_entry.bind('<FocusOut>', self._on_filename_focus_out)
        self.filename_entry.bind('<KeyRelease>', self._on_filename_change)

        # Video file entry directly
        self.display_filename = tk.StringVar()
        ttk.Entry(self.entry_frame, textvariable=self.display_filename, state="readonly", font=("Cascadia Code", 10)).pack(fill="x", pady=(0, 4))

        # Prompt directly in entry_frame (no wrapper frames)
        prompt_text = tk.Text(self.entry_frame, height=2, wrap="word", font=("Cascadia Code", 10), relief="solid", borderwidth=1, padx=6, pady=4)
        prompt_text.pack(fill="x")
        prompt_text.bind('<KeyRelease>', lambda e: self.prompt_text.set(prompt_text.get("1.0", tk.END).strip()))
        self.prompt_widget = prompt_text

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




    def get_data(self):
        """Get the video file path and prompt text"""
        # Normalize the video file path when retrieving data
        import os
        video_file = self.video_file_path.get()
        if video_file:
            video_file = os.path.normpath(video_file)

        return {
            "video_file": video_file,
            "prompt": self.prompt_widget.get("1.0", tk.END).strip(),
            "custom_filename": self.custom_filename.get().strip()
        }

    def is_valid(self):
        """Check if this entry has valid data"""
        data = self.get_data()
        # Only require video file - prompt is optional and can be added manually
        return bool(data["video_file"])

    def set_data(self, video_file, prompt):
        """Set the video file and prompt data"""
        # Normalize the video file path to fix mixed path separators
        import os
        if video_file:
            video_file = os.path.normpath(video_file)

        self.video_file_path.set(video_file)

        # Update display filename to show only the basename for cleaner UI
        if video_file:
            self.display_filename.set(os.path.basename(video_file))
        else:
            self.display_filename.set("")

        self.prompt_widget.delete("1.0", tk.END)
        self.prompt_widget.insert("1.0", prompt)
        self.prompt_text.set(prompt)

    def destroy(self):
        """Remove this entry from the UI"""
        if self.entry_frame:
            self.entry_frame.destroy()