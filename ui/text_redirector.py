"""
TextRedirector - Redirects stdout to a tkinter Text widget
"""

class TextRedirector:
    """Class to redirect stdout to a tkinter Text widget"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, string):
        """Write text to the text widget"""
        self.buffer += string
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", string)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")
        
    def flush(self):
        """Required for file-like objects"""
        pass
