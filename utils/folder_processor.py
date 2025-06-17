"""
Folder Processing Utility - Handle bulk video+text file processing
Separate module to maintain clean architecture and reusability
Enhanced with Smart Auto-Detection Logic for intelligent grouping
"""
import os
import glob
from typing import Dict, List, Tuple, Optional

class FolderProcessor:
    """Utility class for processing folders containing video+text pairs with smart auto-detection"""
    
    # Supported file extensions
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    TEXT_EXTENSIONS = {'.txt', '.md'}
    
    def __init__(self):
        """Initialize the folder processor"""
        self.logger = None
    
    def set_logger(self, logger_func):
        """Set logging function for debug output"""
        self.logger = logger_func
    
    def log(self, message: str):
        """Log a message if logger is available"""
        if self.logger:
            self.logger(message)
    
    def smart_analyze_folder(self, root_folder: str) -> Dict:
        """
        SMART AUTO-DETECTION: Analyze folder structure and determine optimal processing mode
        
        Args:
            root_folder: Root folder to analyze
            
        Returns:
            dict: Smart analysis with recommended processing mode
            
        Structure:
            {
                "processing_mode": "grouped" | "individual",
                "detection_reason": "explanation of why this mode was chosen",
                "groups": {...} if grouped mode,
                "pairs": [...] if individual mode,
                "notification_message": "user-friendly message"
            }
        """
        if not os.path.exists(root_folder):
            raise ValueError(f"Folder does not exist: {root_folder}")
        
        # Scan the structure first
        groups = self.scan_folder_structure(root_folder)
        individual_pairs = self._scan_for_individual_pairs(root_folder)
        
        # Apply smart detection logic
        detection_result = self._apply_smart_detection_rules(root_folder, groups, individual_pairs)
        
        return detection_result
    
    def _apply_smart_detection_rules(self, root_folder: str, groups: Dict, individual_pairs: List) -> Dict:
        """Apply intelligent rules to determine processing mode"""
        folder_name = os.path.basename(root_folder)
        
        # RULE 1: Single folder with 3+ videos -> AUTO-GROUP
        if len(groups) == 1 and len(list(groups.values())[0]['pairs']) >= 3:
            group_info = list(groups.values())[0]
            return {
                "processing_mode": "grouped",
                "detection_reason": f"Single folder with {len(group_info['pairs'])} videos - perfect for combining",
                "groups": groups,
                "notification_message": f"Smart-loaded: {folder_name} group ({len(group_info['pairs'])} videos combined)",
                "override_option": "Load as Individual Instead"
            }
        
        # RULE 2: Multiple clear subfolders -> AUTO-GROUP BY SUBFOLDER  
        if len(groups) > 1:
            total_videos = sum(len(group['pairs']) for group in groups.values())
            return {
                "processing_mode": "grouped", 
                "detection_reason": f"Clear subfolder structure - {len(groups)} groups detected",
                "groups": groups,
                "notification_message": f"Smart-loaded: {len(groups)} groups ({total_videos} videos total)",
                "override_option": "Load as Individual Instead"
            }
        
        # RULE 3: Single folder with 2 videos -> AUTO-GROUP (likely intro/outro or similar)
        if len(groups) == 1 and len(list(groups.values())[0]['pairs']) == 2:
            group_info = list(groups.values())[0]
            return {
                "processing_mode": "grouped",
                "detection_reason": "Two videos in folder - likely meant to be combined",
                "groups": groups,
                "notification_message": f"Smart-loaded: {folder_name} group (2 videos combined)",
                "override_option": "Load as Individual Instead"
            }
        
        # RULE 4: Mixed structure or unclear pattern -> INDIVIDUAL
        return {
            "processing_mode": "individual",
            "detection_reason": "Mixed structure or unclear grouping pattern detected",
            "pairs": individual_pairs,
            "notification_message": f"Smart-loaded: {len(individual_pairs)} individual videos",
            "override_option": "Load as Groups Instead" if groups else None
        }
    
    def _scan_for_individual_pairs(self, root_folder: str) -> List[Dict]:
        """Scan folder for individual video+text pairs (flattened)"""
        video_extensions = self.VIDEO_EXTENSIONS
        text_extensions = self.TEXT_EXTENSIONS
        
        pairs = []
        
        # Scan recursively for all files
        all_files = []
        for root, dirs, files in os.walk(root_folder):
            for file in files:
                all_files.append(os.path.join(root, file))
        
        # Group files by directory
        dir_files = {}
        for file_path in all_files:
            dir_name = os.path.dirname(file_path)
            if dir_name not in dir_files:
                dir_files[dir_name] = {'videos': [], 'texts': []}
            
            ext = os.path.splitext(file_path)[1].lower()
            if ext in video_extensions:
                dir_files[dir_name]['videos'].append(file_path)
            elif ext in text_extensions:
                dir_files[dir_name]['texts'].append(file_path)
        
        # Find pairs in each directory (individual processing)
        for dir_path, files in dir_files.items():
            videos = files['videos']
            texts = files['texts']
            
            if not videos or not texts:
                continue
            
            # Try to match pairs
            matched_pairs = self._match_video_text_pairs_individual(videos, texts)
            pairs.extend(matched_pairs)
        
        return pairs
    
    def _match_video_text_pairs_individual(self, videos: List[str], texts: List[str]) -> List[Dict]:
        """Match video and text files for individual processing"""
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
                    self.log(f"Failed to read text file {os.path.basename(best_match)}: {e}")
        
        return pairs

    def _get_match_confidence(self, match_type: str) -> int:
        """Get confidence score for different match types"""
        confidence_map = {
            "exact_name": 3,
            "single_pair": 2,
            "common_name_prompt": 2,
            "common_name_script": 2,
            "common_name_text": 2,
            "common_name_content": 2
        }
        return confidence_map.get(match_type, 1)
    
    def scan_folder_structure(self, root_folder: str) -> Dict[str, Dict]:
        """
        Scan folder and group video/text pairs by immediate parent folder
        
        Args:
            root_folder: Root folder to scan recursively
            
        Returns:
            dict: Groups organized by folder path with metadata
            
        Example:
            {
                "project": {
                    "folder_path": "/path/to/project",
                    "folder_name": "project", 
                    "pairs": [{"video_file": "...", "text_file": "...", "prompt": "..."}],
                    "output_name": "project.mp4"
                }
            }
        """
        if not os.path.exists(root_folder):
            raise ValueError(f"Folder does not exist: {root_folder}")
        
        groups = {}
        
        # Walk through all folders and subfolders
        for current_root, dirs, files in os.walk(root_folder):
            # Get relative folder path from selected root
            rel_folder = os.path.relpath(current_root, root_folder)
            if rel_folder == '.':
                rel_folder = os.path.basename(root_folder)  # Use root folder name
            
            # Find video and text files in current directory
            video_files = {}
            text_files = {}
            
            for file in files:
                name, ext = os.path.splitext(file)
                file_path = os.path.join(current_root, file)
                
                if ext.lower() in self.VIDEO_EXTENSIONS:
                    video_files[name.lower()] = {
                        'path': file_path,
                        'name': file,
                        'base_name': name
                    }
                elif ext.lower() in self.TEXT_EXTENSIONS:
                    text_files[name.lower()] = {
                        'path': file_path,
                        'name': file,
                        'base_name': name
                    }
            
            # Match video files with text files in this folder
            folder_pairs = self._match_files_in_folder(video_files, text_files)
            
            # If this folder has pairs, add to groups
            if folder_pairs:
                # Sort pairs by filename for consistent ordering
                folder_pairs.sort(key=lambda x: x['order_key'])
                
                groups[rel_folder] = {
                    'folder_path': current_root,
                    'folder_name': os.path.basename(current_root),
                    'pairs': folder_pairs,
                    'output_name': f"{os.path.basename(current_root)}.mp4",
                    'relative_path': rel_folder
                }
        
        return groups
    
    def _match_files_in_folder(self, video_files: Dict, text_files: Dict) -> List[Dict]:
        """
        Match video files with text files using priority-based logic
        
        Args:
            video_files: Dictionary of video files in folder
            text_files: Dictionary of text files in folder
            
        Returns:
            list: List of matched video+text pairs
        """
        pairs = []
        matched_videos = set()
        
        for video_key, video_info in video_files.items():
            if video_key in matched_videos:
                continue
                
            text_info = None
            match_type = None
            
            # PRIORITY 1: Exact name match (BEST)
            if video_key in text_files:
                text_info = text_files[video_key]
                match_type = "exact_name"
            
            # PRIORITY 2: If only one video and one text in folder
            elif len(video_files) == 1 and len(text_files) == 1:
                text_info = list(text_files.values())[0]
                match_type = "single_pair"
            
            # PRIORITY 3: Common prompt file names (if no exact match)
            elif not text_info:
                for common_name in ['prompt', 'script', 'text', 'content']:
                    if common_name in text_files:
                        text_info = text_files[common_name]
                        match_type = f"common_name_{common_name}"
                        break
            
            # If we found a text file, process and add the pair
            if text_info:
                try:
                    with open(text_info['path'], 'r', encoding='utf-8') as f:
                        prompt_content = f.read().strip()
                    
                    if prompt_content:  # Only add if text file has content
                        pairs.append({
                            'video_file': video_info['path'],
                            'text_file': text_info['path'],
                            'prompt': prompt_content,
                            'video_name': video_info['name'],
                            'text_name': text_info['name'],
                            'order_key': video_info['base_name'].lower(),
                            'match_type': match_type,
                            'confidence': self._get_match_confidence(match_type)
                        })
                        
                        matched_videos.add(video_key)
                        
                except Exception as e:
                    self.log(f"Error reading {text_info['path']}: {e}")
                    continue
        
        return pairs
    
    def _get_match_confidence(self, match_type: str) -> int:
        """Get confidence score for match type"""
        confidence_scores = {
            'exact_name': 100,           # video1.mp4 ↔ video1.txt
            'single_pair': 90,           # Only 1 video + 1 text in folder
            'common_name_prompt': 80,    # video.mp4 ↔ prompt.txt
            'common_name_script': 80,    # video.mp4 ↔ script.txt  
            'common_name_text': 70,      # video.mp4 ↔ text.txt
            'common_name_content': 70    # video.mp4 ↔ content.txt
        }
        return confidence_scores.get(match_type, 50)
    
    def validate_groups(self, groups: Dict) -> Tuple[bool, List[str]]:
        """
        Validate that all groups have valid files
        
        Args:
            groups: Groups dictionary from scan_folder_structure
            
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        if not groups:
            errors.append("No video+text pairs found in folder structure")
            return False, errors
        
        for folder_name, group_info in groups.items():
            pairs = group_info.get('pairs', [])
            
            if not pairs:
                errors.append(f"No valid pairs in folder: {folder_name}")
                continue
            
            for pair in pairs:
                # Check video file exists
                if not os.path.exists(pair['video_file']):
                    errors.append(f"Video file not found: {pair['video_name']}")
                
                # Check text file exists
                if not os.path.exists(pair['text_file']):
                    errors.append(f"Text file not found: {pair['text_name']}")
                
                # Check prompt content
                if not pair.get('prompt', '').strip():
                    errors.append(f"Empty prompt in: {pair['text_name']}")
        
        return len(errors) == 0, errors
    
    def get_processing_summary(self, groups: Dict) -> Dict:
        """
        Get summary of what will be processed
        
        Args:
            groups: Groups dictionary from scan_folder_structure
            
        Returns:
            dict: Processing summary with counts and details
        """
        total_groups = len(groups)
        total_videos = sum(len(group['pairs']) for group in groups.values())
        total_outputs = total_groups
        
        # Group by match type for statistics
        match_types = {}
        for group in groups.values():
            for pair in group['pairs']:
                match_type = pair['match_type']
                match_types[match_type] = match_types.get(match_type, 0) + 1
        
        return {
            'total_groups': total_groups,
            'total_input_videos': total_videos,
            'total_output_videos': total_outputs,
            'match_statistics': match_types,
            'folder_names': list(groups.keys())
        }


    def process_folder_structure(self, root_folder: str) -> List[Dict]:
        """
        Process folder structure for image-to-video generation

        Args:
            root_folder: Root folder to process

        Returns:
            list: List of folder data with images and text
        """
        if not os.path.exists(root_folder):
            raise ValueError(f"Folder does not exist: {root_folder}")

        folder_data = []

        # Check root level first
        root_images, root_text = self._scan_folder_for_images_and_text(root_folder)
        if root_images:
            folder_data.append({
                'type': 'root',
                'folder_path': root_folder,
                'folder_name': os.path.basename(root_folder),
                'images': root_images,
                'prompt': root_text,
                'text_file': None  # We read the content directly
            })

        # Check subfolders
        for item in os.listdir(root_folder):
            item_path = os.path.join(root_folder, item)
            if os.path.isdir(item_path):
                subfolder_images, subfolder_text = self._scan_folder_for_images_and_text(item_path)
                if subfolder_images:
                    folder_data.append({
                        'type': 'subfolder',
                        'folder_path': item_path,
                        'folder_name': item,
                        'subfolder_name': item,
                        'images': subfolder_images,
                        'prompt': subfolder_text,
                        'text_file': None
                    })

        return folder_data

    def _scan_folder_for_images_and_text(self, folder_path: str) -> Tuple[List[str], str]:
        """
        Scan a single folder for images and text files

        Args:
            folder_path: Path to folder to scan

        Returns:
            tuple: (list_of_image_paths, text_content)
        """
        images = []
        text_files = []

        try:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.IMAGE_EXTENSIONS:
                        images.append(file_path)
                    elif ext in self.TEXT_EXTENSIONS:
                        text_files.append(file_path)

            # Sort images naturally
            images.sort()

            # Find best text file and read content
            text_content = ""
            if text_files:
                best_text_file = self._find_best_text_file(text_files)
                if best_text_file:
                    try:
                        with open(best_text_file, 'r', encoding='utf-8') as f:
                            text_content = f.read().strip()
                    except Exception as e:
                        self.log(f"Error reading text file {best_text_file}: {e}")

            return images, text_content

        except Exception as e:
            self.log(f"Error scanning folder {folder_path}: {e}")
            return [], ""

    def _find_best_text_file(self, text_files: List[str]) -> Optional[str]:
        """
        Find the best text file to use as prompt

        Args:
            text_files: List of text file paths

        Returns:
            str: Path to best text file or None
        """
        if not text_files:
            return None

        # Priority order for text file names
        priority_names = ['main.txt', 'prompt.txt', 'script.txt', 'text.txt', 'content.txt']

        # Check for priority names first
        for priority_name in priority_names:
            for text_file in text_files:
                if os.path.basename(text_file).lower() == priority_name:
                    return text_file

        # If no priority match, return the first text file
        return text_files[0]


class FolderProcessingError(Exception):
    """Custom exception for folder processing errors"""
    pass