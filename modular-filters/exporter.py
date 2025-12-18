import json
import os
from datetime import datetime
from typing import Dict, List, Set

class Exporter:
    def __init__(self, data_loader):
        self.data_loader = data_loader
    
    def export_json_analysis(self, loaded_files: List[str], file_entries: Dict, export_dir: str) -> None:
        """Export analysis for each JSON file"""
        # Create analysis for each file
        for file_path in loaded_files:
            self._export_single_file_analysis(file_path, export_dir)
        
        # Generate summary report
        self._generate_summary_report(loaded_files, file_entries, export_dir)
    
    def _export_single_file_analysis(self, file_path: str, export_dir: str) -> None:
        """Export analysis for a single JSON file"""
        if file_path not in self.data_loader.file_entries:
            return
        
        entries = self.data_loader.file_entries[file_path]
        if not entries:
            return
        
        # Create filename for export
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        export_filename = f"{base_name}_analysis.json"
        export_path = os.path.join(export_dir, export_filename)
        
        # Analyze the file data
        analysis = {
            "relative_path": self.data_loader.get_relative_source_path(file_path, ""),  # base path not needed here
            "total_entries": len(entries),
            "export_timestamp": str(datetime.now()),
            "categories": {},
            "websites": {},
            "unique_fields": set(),
            "sample_entries": []
        }
        
        # Analyze categories and websites
        for entry in entries:
            # Track unique fields
            analysis["unique_fields"].update(entry.keys())
            
            # Analyze categories
            if 'category' in entry and entry['category']:
                category = str(entry['category'])
                if category not in analysis["categories"]:
                    analysis["categories"][category] = 0
                analysis["categories"][category] += 1
            
            # Analyze websites
            if 'name' in entry and entry['name']:
                website = str(entry['name'])
                if website not in analysis["websites"]:
                    analysis["websites"][website] = 0
                analysis["websites"][website] += 1
        
        # Convert set to list for JSON serialization
        analysis["unique_fields"] = list(analysis["unique_fields"])
        
        # Add sample entries (first 1000)
        for entry in entries[:1000]:
            sample_entry = {}
            for key, value in entry.items():
                if key not in {'url', 'status', 'metadata'}:  # Exclude sensitive/verbose fields
                    sample_entry[key] = value
            analysis["sample_entries"].append(sample_entry)
        
        # Sort categories and websites by count
        analysis["categories"] = dict(sorted(
            analysis["categories"].items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        analysis["websites"] = dict(sorted(
            analysis["websites"].items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        # Write analysis to file
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    def _generate_summary_report(self, loaded_files: List[str], file_entries: Dict, export_dir: str) -> None:
        """Generate a summary report of all files"""
        summary = {
            "export_timestamp": str(datetime.now()),
            "total_files_analyzed": len(loaded_files),
            "total_entries": sum(len(entries) for entries in file_entries.values()),
            "files": []
        }
        
        for file_path in loaded_files:
            if file_path in file_entries:
                entries = file_entries[file_path]
                
                # Count categories
                categories = {}
                for entry in entries:
                    if 'category' in entry and entry['category']:
                        category = str(entry['category'])
                        categories[category] = categories.get(category, 0) + 1
                
                # Sort categories by count
                categories = dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))
                
                file_info = {
                    "relative_path": self.data_loader.get_relative_source_path(file_path, ""),
                    "entry_count": len(entries),
                    "categories_count": len(categories),
                    "categories": categories,
                    "websites_count": len(self._get_unique_values(entries, 'name'))
                }
                summary["files"].append(file_info)
        
        # Write summary report
        summary_path = os.path.join(export_dir, "summary_report.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def _get_unique_values(self, data: List[Dict], field: str) -> Set[str]:
        """Get unique values for a field"""
        values = set()
        for item in data:
            if field in item and item[field]:
                values.add(str(item[field]))
        return values