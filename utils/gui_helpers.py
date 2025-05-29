# utils/gui_helpers.py

class HoverEffect:
    def __init__(self, widget, hover_bg, normal_bg=None):
        self.widget = widget
        self.hover_bg = hover_bg
        # Use current bg if normal_bg is not specified
        self.normal_bg = normal_bg or widget.cget("background")
        self._bind_events()

    def _bind_events(self):
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        self.widget.config(bg=self.hover_bg)

    def _on_leave(self, event):
        self.widget.config(bg=self.normal_bg)


def apply_hover_to_widgets(widgets, hover_color, normal_color=None):
    for widget in widgets:
        HoverEffect(widget, hover_color, normal_color)
