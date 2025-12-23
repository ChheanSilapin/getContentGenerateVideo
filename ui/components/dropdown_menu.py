"""
Dropdown Menu Component - Custom dropdown menu for content addition
Creates a dropdown button with menu options for adding content
"""
import tkinter as tk
from tkinter import ttk


class DropdownMenu:
    """Custom dropdown menu component for content addition"""
    
    def __init__(self, parent, button_text="Add Content ▾", width=20):
        """
        Initialize dropdown menu
        
        Args:
            parent: Parent widget
            button_text: Text to display on the button
            width: Button width
        """
        self.parent = parent
        self.button_text = button_text
        self.width = width
        self.menu_items = []
        self.menu = None
        self.button = None
        
    def add_menu_item(self, text, command, icon=""):
        """
        Add a menu item to the dropdown
        
        Args:
            text: Menu item text
            command: Function to call when item is clicked
            icon: Optional icon for the menu item
        """
        display_text = f"{icon} {text}" if icon else text
        self.menu_items.append({
            'text': display_text,
            'command': command
        })
        
    def create_dropdown(self):
        """Create the dropdown button and menu"""
        # Create the main button
        self.button = ttk.Button(
            self.parent,
            text=self.button_text,
            command=self._show_menu,
            width=self.width
        )
        
        # Create the popup menu
        self.menu = tk.Menu(self.parent, tearoff=0)
        
        # Add menu items
        for item in self.menu_items:
            self.menu.add_command(
                label=item['text'],
                command=item['command']
            )
        
        return self.button
    
    def _show_menu(self):
        """Show the dropdown menu"""
        if self.menu and self.button:
            try:
                # Get button position
                x = self.button.winfo_rootx()
                y = self.button.winfo_rooty() + self.button.winfo_height()
                
                # Show menu at button position
                self.menu.post(x, y)
            except tk.TclError:
                # Handle case where button is not visible
                pass
    
    def pack(self, **kwargs):
        """Pack the dropdown button"""
        if self.button:
            self.button.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the dropdown button"""
        if self.button:
            self.button.grid(**kwargs)
    
    def place(self, **kwargs):
        """Place the dropdown button"""
        if self.button:
            self.button.place(**kwargs)
    
    def config(self, **kwargs):
        """Configure the dropdown button"""
        if self.button:
            self.button.config(**kwargs)

    def update_menu_item(self, index, text=None, command=None):
        """Update a menu item's text or command"""
        if self.menu and 0 <= index < len(self.menu_items):
            if text is not None:
                self.menu_items[index]['text'] = text
                self.menu.entryconfig(index, label=text)
            if command is not None:
                self.menu_items[index]['command'] = command
                self.menu.entryconfig(index, command=command)

    def destroy(self):
        """Destroy the dropdown menu and button"""
        if self.menu:
            self.menu.destroy()
        if self.button:
            self.button.destroy()


def create_content_dropdown(parent, load_folder_command, add_single_command, width=20):
    """
    Convenience function to create a standard content dropdown

    Args:
        parent: Parent widget
        load_folder_command: Command for "Load from Folder" option
        add_single_command: Command for "Add Single Item" option
        width: Button width

    Returns:
        DropdownMenu: Configured dropdown menu
    """
    dropdown = DropdownMenu(parent, "Add Content ▾", width)

    # Add standard menu items
    dropdown.add_menu_item("Load from Folder", load_folder_command, "📁")
    dropdown.add_menu_item("Add Video Entry", add_single_command, "➕")

    # Create and return the dropdown
    dropdown.create_dropdown()
    return dropdown


def create_video_content_dropdown(parent, load_folder_command, select_multiple_command, width=20):
    """
    Convenience function to create an enhanced video content dropdown with two options

    Args:
        parent: Parent widget
        load_folder_command: Command for "Load from Folder" option
        select_multiple_command: Command for "Select Multiple Videos" option
        width: Button width

    Returns:
        DropdownMenu: Configured dropdown menu
    """
    dropdown = DropdownMenu(parent, "Add Content ▾", width)

    # Add enhanced menu items for video tab
    dropdown.add_menu_item("Add Folder", load_folder_command, "📁")
    dropdown.add_menu_item("Add Files", select_multiple_command, "🎥")

    # Create and return the dropdown
    dropdown.create_dropdown()
    return dropdown


def create_image_content_dropdown(parent, load_folder_command, select_multiple_command, import_url_command=None, width=20):
    """
    Convenience function to create an enhanced image content dropdown with multiple options

    Args:
        parent: Parent widget
        load_folder_command: Command for "Load from Folder" option
        select_multiple_command: Command for "Select Multiple Images" option
        import_url_command: Command for "Import from URL" option (optional)
        width: Button width

    Returns:
        DropdownMenu: Configured dropdown menu
    """
    dropdown = DropdownMenu(parent, "Add Content ▾", width)

    # Add enhanced menu items for image tab
    dropdown.add_menu_item("Add Folder", load_folder_command, "📁")
    dropdown.add_menu_item("Add Files", select_multiple_command, "🎞")
    
    # Add Import from URL option if command provided
    if import_url_command:
        dropdown.add_menu_item("Import from URL", import_url_command, "🌐")

    # Create and return the dropdown
    dropdown.create_dropdown()
    return dropdown

