"""
Button Factory Component - Standardized button creation
Creates consistent buttons, toolbars, and button groups across the application
"""
from utils.common_imports import tk, ttk

class ButtonFactory:
    """Factory for creating standardized buttons and button groups"""
    
    # Standard button styles
    STYLES = {
        'primary': {
            'style': 'Accent.TButton',
            'padding': (15, 8),
            'font': ('Cascadia Code', 10, 'bold')
        },
        'secondary': {
            'style': 'TButton',
            'padding': (12, 6),
            'font': ('Cascadia Code', 9)
        },
        'action': {
            'style': 'Accent.TButton',
            'padding': (10, 6),
            'font': ('Cascadia Code', 9)
        },
        'tool': {
            'style': 'Toolbutton',
            'padding': (8, 4),
            'font': ('Cascadia Code', 8)
        }
    }
    
    @classmethod
    def create_button(cls, parent, text, command=None, style='secondary', icon=None, tooltip=None, state='normal'):
        """Create a standardized button
        
        Args:
            parent: Parent widget
            text: Button text
            command: Command to execute
            style: Button style ('primary', 'secondary', 'action', 'tool')
            icon: Optional icon (emoji or symbol)
            tooltip: Optional tooltip text
            state: Button state ('normal', 'disabled')
        
        Returns:
            ttk.Button: Created button
        """
        button_config = cls.STYLES.get(style, cls.STYLES['secondary']).copy()
        
        # Add icon to text if provided
        if icon:
            display_text = f"{icon} {text}"
        else:
            display_text = text
        
        # Create button
        button = ttk.Button(
            parent,
            text=display_text,
            command=command,
            state=state
        )
        
        # Apply styling if available
        if 'style' in button_config:
            button.configure(style=button_config['style'])
        
        return button
    
    @classmethod
    def create_toolbar(cls, parent, buttons_config, pack_side='left', pack_padx=5):
        """Create a toolbar with multiple buttons
        
        Args:
            parent: Parent widget
            buttons_config: List of button configurations
            pack_side: Side to pack buttons ('left', 'right')
            pack_padx: Padding between buttons
        
        Returns:
            tuple: (toolbar_frame, list_of_buttons)
        """
        toolbar = ttk.Frame(parent)
        buttons = []
        
        for config in buttons_config:
            button = cls.create_button(
                toolbar,
                text=config.get('text', ''),
                command=config.get('command'),
                style=config.get('style', 'tool'),
                icon=config.get('icon'),
                state=config.get('state', 'normal')
            )
            button.pack(side=pack_side, padx=pack_padx)
            buttons.append(button)
        
        return toolbar, buttons
    
    @classmethod
    def create_file_operations_toolbar(cls, parent, callbacks):
        """Create standard file operations toolbar
        
        Args:
            parent: Parent widget
            callbacks: Dict with callback functions
        
        Returns:
            tuple: (toolbar_frame, dict_of_buttons)
        """
        buttons_config = [
            {
                'text': 'Add Files',
                'icon': '📁',
                'command': callbacks.get('add_files'),
                'style': 'action'
            },
            {
                'text': 'Clear All',
                'icon': '🧹',
                'command': callbacks.get('clear_all'),
                'style': 'secondary'
            },
            {
                'text': 'Remove Selected',
                'icon': '🗑️',
                'command': callbacks.get('remove_selected'),
                'style': 'secondary'
            }
        ]
        
        toolbar, button_list = cls.create_toolbar(parent, buttons_config)
        
        # Return named buttons
        buttons = {
            'add_files': button_list[0],
            'clear_all': button_list[1],
            'remove_selected': button_list[2]
        }
        
        return toolbar, buttons
    
    @classmethod
    def create_selection_toolbar(cls, parent, callbacks):
        """Create standard selection toolbar
        
        Args:
            parent: Parent widget
            callbacks: Dict with callback functions
        
        Returns:
            tuple: (toolbar_frame, dict_of_buttons)
        """
        buttons_config = [
            {
                'text': 'Select All',
                'command': callbacks.get('select_all'),
                'style': 'secondary'
            },
            {
                'text': 'Deselect All',
                'command': callbacks.get('deselect_all'),
                'style': 'secondary'
            }
        ]
        
        toolbar, button_list = cls.create_toolbar(parent, buttons_config)
        
        buttons = {
            'select_all': button_list[0],
            'deselect_all': button_list[1]
        }
        
        return toolbar, buttons
    
    @classmethod
    def create_process_toolbar(cls, parent, callbacks, process_text="Process", stop_text="Stop"):
        """Create standard process control toolbar
        
        Args:
            parent: Parent widget
            callbacks: Dict with callback functions
            process_text: Text for process button
            stop_text: Text for stop button
        
        Returns:
            tuple: (toolbar_frame, dict_of_buttons)
        """
        buttons_config = [
            {
                'text': process_text,
                'icon': '▶️',
                'command': callbacks.get('start_process'),
                'style': 'primary'
            },
            {
                'text': stop_text,
                'icon': '⏹️',
                'command': callbacks.get('stop_process'),
                'style': 'secondary',
                'state': 'disabled'
            }
        ]
        
        toolbar, button_list = cls.create_toolbar(parent, buttons_config, pack_side='right')
        
        buttons = {
            'process': button_list[0],
            'stop': button_list[1]
        }
        
        return toolbar, buttons
    
    @classmethod
    def create_navigation_buttons(cls, parent, callbacks):
        """Create navigation buttons (Previous/Next)
        
        Args:
            parent: Parent widget
            callbacks: Dict with callback functions
        
        Returns:
            tuple: (toolbar_frame, dict_of_buttons)
        """
        buttons_config = [
            {
                'text': 'Previous',
                'icon': '⬅️',
                'command': callbacks.get('previous'),
                'style': 'tool'
            },
            {
                'text': 'Next',
                'icon': '➡️',
                'command': callbacks.get('next'),
                'style': 'tool'
            }
        ]
        
        toolbar, button_list = cls.create_toolbar(parent, buttons_config)
        
        buttons = {
            'previous': button_list[0],
            'next': button_list[1]
        }
        
        return toolbar, buttons 