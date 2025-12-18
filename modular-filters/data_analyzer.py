from typing import Dict, List, Set, Tuple

class DataAnalyzer:
    def __init__(self):
        self.site_categories = {}      # site_name -> category
        self.category_sites = {}       # category -> list of site_names
        self.site_sources = {}         # site_name -> list of source files
        self.category_sources = {}     # category -> list of source files
    
    def build_relationships(self, data: List[Dict], file_entries: Dict) -> None:
        """Build mappings between sites, categories, and their sources"""
        self.site_categories = {}
        self.category_sites = {}
        self.site_sources = {}
        self.category_sources = {}
        
        # First, map sites to their source files
        for file_path, entries in file_entries.items():
            for item in entries:
                if 'name' in item and item['name']:
                    site_name = str(item['name'])
                    
                    # Map site to sources
                    if site_name not in self.site_sources:
                        self.site_sources[site_name] = []
                    if file_path not in self.site_sources[site_name]:
                        self.site_sources[site_name].append(file_path)
        
        # Then build category relationships
        for file_path, entries in file_entries.items():
            for item in entries:
                if 'name' in item and item['name']:
                    site_name = str(item['name'])
                    
                    if 'category' in item and item['category']:
                        category = str(item['category'])
                        
                        # Map site to category
                        self.site_categories[site_name] = category
                        
                        # Map category to sites
                        if category not in self.category_sites:
                            self.category_sites[category] = []
                        if site_name not in self.category_sites[category]:
                            self.category_sites[category].append(site_name)
                        
                        # Map category to sources
                        if category not in self.category_sources:
                            self.category_sources[category] = []
                        if file_path not in self.category_sources[category]:
                            self.category_sources[category].append(file_path)
    
    def get_sites_by_category(self, category: str) -> List[str]:
        """Get all sites in a specific category"""
        return self.category_sites.get(category, [])
    
    def get_category_for_site(self, site_name: str) -> str:
        """Get the category for a specific site"""
        return self.site_categories.get(site_name, "Unknown")
    
    def get_sources_for_site(self, site_name: str) -> List[str]:
        """Get source files for a specific site"""
        return self.site_sources.get(site_name, [])
    
    def get_sources_for_category(self, category: str) -> List[str]:
        """Get source files for a specific category"""
        return self.category_sources.get(category, [])
    
    def count_entries_by_site(self, data: List[Dict]) -> Dict[str, int]:
        """Count how many entries each site has"""
        counts = {}
        for item in data:
            if 'name' in item and item['name']:
                name = str(item['name'])
                counts[name] = counts.get(name, 0) + 1
        return counts
    
    def count_entries_by_category(self, data: List[Dict]) -> Dict[str, int]:
        """Count how many entries each category has"""
        counts = {}
        for item in data:
            if 'category' in item and item['category']:
                cat = str(item['category'])
                counts[cat] = counts.get(cat, 0) + 1
        return counts