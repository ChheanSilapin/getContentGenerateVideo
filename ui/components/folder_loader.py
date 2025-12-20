"""
Folder Loader Mixin - Shared folder loading functionality for tabs
Handles batch loading, entry limits, and consolidated logging
"""
import os


class FolderLoaderMixin:
    """Mixin class for folder loading functionality"""

    def load_entries_batch(self, items, create_entry_func, get_existing_func=None,
                           find_existing_func=None, update_existing_func=None):
        """
        Load entries in batch mode with optimized UI updates
        
        Args:
            items: List of items to load (each item is a dict with data)
            create_entry_func: Function to create a new entry
            get_existing_func: Optional function to get existing items for duplicate check
            find_existing_func: Optional function to find existing entry by key
            update_existing_func: Optional function to update existing entry
            
        Returns:
            dict: Statistics about the loading operation
        """
        # Enable batch loading mode
        self._is_batch_loading = True
        
        stats = {
            'new_count': 0,
            'updated_count': 0,
            'skipped_count': 0,
            'duplicate_count': 0
        }

        try:
            # Get existing items for duplicate detection
            existing_items = get_existing_func() if get_existing_func else set()
            
            for item in items:
                # Check entry limit
                if len(self.entries) >= self.MAX_ENTRIES:
                    stats['skipped_count'] = len(items) - (
                        stats['new_count'] + stats['updated_count'] + stats['duplicate_count']
                    )
                    break

                # Get the key for this item (usually a path)
                item_key = item.get('key') or item.get('folder_path') or item.get('file_path')
                
                # Check for duplicates
                if item_key and item_key in existing_items:
                    stats['duplicate_count'] += 1
                    continue

                # Try to find existing entry to update
                if find_existing_func and item_key:
                    existing_entry_id = find_existing_func(item_key)
                    if existing_entry_id is not None and update_existing_func:
                        update_existing_func(existing_entry_id, item)
                        stats['updated_count'] += 1
                        continue

                # Create new entry
                entry_id = create_entry_func(item)
                if entry_id is not None:
                    stats['new_count'] += 1
                    if item_key:
                        existing_items.add(item_key)

        finally:
            # Disable batch loading and do single UI update
            self._is_batch_loading = False
            self.update_scroll_region()

        return stats

    def log_batch_results(self, stats, item_name="items"):
        """Log consolidated batch loading results"""
        total = stats['new_count'] + stats['updated_count']
        
        if stats['skipped_count'] > 0:
            self.main_gui.log(
                f"⚠️ Loaded {total} {item_name}, "
                f"{stats['skipped_count']} skipped (max {self.MAX_ENTRIES} entries)"
            )
        elif total > 0:
            parts = []
            if stats['new_count'] > 0:
                parts.append(f"{stats['new_count']} new")
            if stats['updated_count'] > 0:
                parts.append(f"{stats['updated_count']} updated")
            if stats['duplicate_count'] > 0:
                parts.append(f"{stats['duplicate_count']} duplicates skipped")
            
            self.main_gui.log(f"Loaded {total} {item_name} ({', '.join(parts)})")
        elif stats['duplicate_count'] > 0:
            self.main_gui.log(
                f"No new {item_name}, {stats['duplicate_count']} duplicates skipped"
            )

    def load_as_individual_entries(self, folder_data, create_entry_func,
                                    get_existing_func=None, find_existing_func=None):
        """
        Load folder data as individual entries with batch optimization
        
        Args:
            folder_data: List of folder items to load
            create_entry_func: Function to create new entry
            get_existing_func: Function to get existing paths
            find_existing_func: Function to find existing entry by path
        """
        self.current_mode = "individual"
        self._is_batch_loading = True
        
        stats = {
            'new_count': 0,
            'updated_count': 0,
            'skipped_count': 0
        }

        try:
            for item in folder_data:
                folder_path = item.get('folder_path')
                prompt = item.get('prompt', '')

                if not folder_path:
                    continue

                # Check entry limit
                if len(self.entries) >= self.MAX_ENTRIES:
                    stats['skipped_count'] = len(folder_data) - (
                        stats['new_count'] + stats['updated_count']
                    )
                    break

                # Check if this folder already exists
                if find_existing_func:
                    existing_entry_id = find_existing_func(folder_path)
                    if existing_entry_id is not None:
                        # Update existing entry
                        entry = self.entries[existing_entry_id]
                        entry.set_data(folder_path, prompt)
                        stats['updated_count'] += 1
                        continue

                # Create new entry
                entry_id = create_entry_func(folder_path, prompt)
                if entry_id:
                    stats['new_count'] += 1

        finally:
            self._is_batch_loading = False
            self.update_scroll_region()

        # Log consolidated results
        self.log_batch_results(stats, "folders")

        # Ensure at least one entry exists
        if not self.entries:
            create_entry_func(None, None)

    def load_as_groups(self, folder_data, parent_folder, create_group_func):
        """
        Load folder data as grouped entries
        
        Args:
            folder_data: List of folder items
            parent_folder: Parent folder path
            create_group_func: Function to create group entry
        """
        self.current_mode = "grouped"
        self._is_batch_loading = True

        try:
            # Group the data by parent folder
            groups = {}

            for item in folder_data:
                if item.get('type') == 'root':
                    group_name = os.path.basename(parent_folder)
                    if group_name not in groups:
                        groups[group_name] = []
                    groups[group_name].append(item)
                elif item.get('type') == 'subfolder':
                    subfolder_name = item.get('subfolder_name', 'Unknown')
                    if subfolder_name not in groups:
                        groups[subfolder_name] = []
                    groups[subfolder_name].append(item)

            # Natural sort for group names
            def natural_sort_key(text):
                import re
                return [int(c) if c.isdigit() else c.lower() 
                        for c in re.split(r'(\d+)', text)]

            sorted_groups = sorted(groups.items(), key=lambda x: natural_sort_key(x[0]))

            # Create group entries
            for group_name, items in sorted_groups:
                if len(self.group_entries) >= self.MAX_GROUPS:
                    self.main_gui.log(
                        f"⚠️ Maximum groups ({self.MAX_GROUPS}) reached"
                    )
                    break
                create_group_func(group_name, items)

        finally:
            self._is_batch_loading = False
            self.update_scroll_region()

        # Ensure at least one group exists
        if not self.group_entries:
            create_group_func("Default Group", [])
