import json
from datetime import datetime
from typing import Dict, Any

class ConfigManager:
    @staticmethod
    def save_configuration(
        filename: str,
        filters: list,
        data_source_path: str,
        recursive: bool,
        loaded_files_count: int,
        entries_count: int,
        custom_field: str,
        custom_operator: str,
        custom_value: str,
        website_search: str,
        website_category_filter: str
    ) -> None:
        """Save current configuration to a file"""
        config = {
            "metadata": {
                "version": "1.0",
                "created": str(datetime.now()),
                "tool": "Blackbird Filter Generator"
            },
            "data_source": {
                "path": data_source_path,
                "recursive": recursive,
                "files_loaded": loaded_files_count,
                "entries_loaded": entries_count
            },
            "filters": {
                "list": filters[:],  # Copy of filters list
                "count": len(filters)
            },
            "custom_filter_settings": {
                "field": custom_field,
                "operator": custom_operator,
                "value": custom_value
            },
            "ui_state": {
                "website_search": website_search,
                "website_category_filter": website_category_filter
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_configuration(filename: str) -> Dict[str, Any]:
        """Load configuration from a file"""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def parse_imported_filters(content: str) -> list:
        """Parse filters from imported file content"""
        # Try to parse as JSON first
        try:
            config = json.loads(content)
            if isinstance(config, dict) and 'filters' in config:
                return config['filters'].get('list', [])
            return []
        except json.JSONDecodeError:
            # Not JSON, treat as plain text with filters
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            filters_to_add = []
            
            for line in lines:
                # Remove surrounding quotes if present
                line = line.strip('"\'')
                
                # Split by "and" if present
                if ' and ' in line:
                    parts = line.split(' and ')
                    filters_to_add.extend([part.strip() for part in parts if part.strip()])
                else:
                    filters_to_add.append(line)
            
            return filters_to_add