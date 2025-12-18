import json
import os
import glob
from typing import List, Dict, Any, Tuple

class DataLoader:
    def __init__(self):
        self.file_entries = {}  # file_path -> list of entries
    
    def load_json_files(self, path: str, recursive: bool = True) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Load JSON files from a path (file or directory)"""
        data = []
        loaded_files = []
        
        if os.path.isfile(path):
            file_data = self._load_single_file(path)
            if file_data:
                data.extend(file_data)
                loaded_files.append(path)
                self.file_entries[path] = file_data
        elif os.path.isdir(path):
            json_files = self._find_json_files(path, recursive)
            
            for json_file in json_files:
                file_data = self._load_single_file(json_file)
                if file_data:
                    data.extend(file_data)
                    loaded_files.append(json_file)
                    self.file_entries[json_file] = file_data
        
        return data, loaded_files
    
    def _find_json_files(self, directory: str, recursive: bool) -> List[str]:
        """Find JSON files in directory, optionally recursive"""
        if recursive:
            json_files = []
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith('.json'):
                        full_path = os.path.join(root, file)
                        json_files.append(full_path)
            return json_files
        else:
            json_pattern = os.path.join(directory, "*.json")
            return glob.glob(json_pattern)
    
    def _load_single_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load a single JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            return []
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []
    
    def get_unique_values(self, data: List[Dict[str, Any]], json_field: str) -> List[str]:
        """Get unique values for a specific field from data"""
        values = set()
        for item in data:
            if json_field in item and item[json_field] is not None:
                values.add(str(item[json_field]))
        return sorted(list(values))
    
    def get_relative_source_path(self, full_path: str, base_path: str) -> str:
        """Convert full file path to a relative format"""
        if base_path and full_path.startswith(base_path):
            return os.path.relpath(full_path, base_path)
        
        # Show the last 2 directory components if not relative to base
        dirname = os.path.dirname(full_path)
        basename = os.path.basename(full_path)
        parent_dir = os.path.basename(os.path.dirname(dirname))
        current_dir = os.path.basename(dirname)
        
        if parent_dir and parent_dir != current_dir:
            return os.path.join(parent_dir, current_dir, basename)
        else:
            return os.path.join(current_dir, basename)