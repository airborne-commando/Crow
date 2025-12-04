import json
import os
import glob
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Dict, List, Any, Tuple, Optional

class BlackbirdFilterGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Blackbird Filter Generator")
        self.root.geometry("1000x900")
        
        # Field mapping - using exact JSON field names
        self.field_mapping = {
            'category': 'cat',  # JSON 'category' becomes Blackbird 'cat'
            'name': 'name',     # JSON 'name' becomes Blackbird 'name'
            'uri_check': 'uri_check', 
            'e_code': 'e_code',
            'e_string': 'e_string',
            'm_string': 'm_string',
            'm_code': 'm_code'
        }
        self.available_fields = ['name', 'cat', 'uri_check', 'e_code', 'e_string', 'm_string', 'm_code']
        self.operators = ['=', '~', '>', '<', '>=', '<=', '!=']
        
        self.filters = []
        self.loaded_data = []
        self.loaded_files = []
        
        # Store site-category relationships
        self.site_categories = {}  # site_name -> category
        self.category_sites = {}   # category -> list of site_names
        
        # Store file-source relationships
        self.site_sources = {}  # site_name -> list of source files
        self.category_sources = {}  # category -> list of source files
        self.file_entries = {}  # file_path -> list of entries
        
        self.setup_gui()
    
    def setup_gui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)  # This gives the JSON frame proper weight
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Data Source", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Button(file_frame, text="Browse File/Directory", 
                  command=self.browse_file).grid(row=0, column=0, padx=(0, 10))
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, state='readonly').grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_frame, text="Search Subdirectories", 
                       variable=self.recursive_var).grid(row=0, column=2, padx=(10, 0))
        
        ttk.Button(file_frame, text="Load Data", 
                  command=self.load_data).grid(row=0, column=3, padx=(10, 0))
        

        ttk.Button(file_frame, text="Export JSON Analysis", 
                  command=self.export_json_analysis).grid(row=0, column=4, padx=(10, 0))

        # JSON Structure Display
        json_frame = ttk.LabelFrame(main_frame, text="JSON Structure Preview", padding="5")
        json_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        json_frame.columnconfigure(0, weight=1)
        json_frame.rowconfigure(0, weight=1)  # This makes the text widget expand

        # Create a Text widget for JSON preview
        self.json_structure_text = tk.Text(json_frame, wrap=tk.WORD, height=10)
        self.json_structure_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create a Scrollbar
        scrollbar = ttk.Scrollbar(json_frame, orient=tk.VERTICAL, command=self.json_structure_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E))

        # Link the Text widget to the Scrollbar
        self.json_structure_text.config(yscrollcommand=scrollbar.set)

        # Insert sample text (replace with your JSON string)
        self.json_structure_text.insert(tk.END, "No data loaded - JSON structure will appear here")
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Left panel - Filter creation
        left_frame = ttk.LabelFrame(content_frame, text="Create Filters", padding="5")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(2, weight=1)
        
        # Category filters
        cat_frame = ttk.LabelFrame(left_frame, text="Category Filters", padding="5")
        cat_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        cat_frame.columnconfigure(0, weight=1)

        self.category_listbox = tk.Listbox(cat_frame, selectmode=tk.MULTIPLE, height=6)
        self.category_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        cat_btn_frame = ttk.Frame(cat_frame)
        cat_btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        ttk.Button(cat_btn_frame, text="Select All", 
                  command=self.select_all_categories).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cat_btn_frame, text="Clear Selection", 
                  command=self.clear_category_selection).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cat_btn_frame, text="Exclude Selected", 
                  command=self.exclude_selected_categories).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cat_btn_frame, text="Include Selected", 
                  command=self.include_selected_categories).pack(side=tk.LEFT)
        
        # Website filters with category info
        website_frame = ttk.LabelFrame(left_frame, text="Website Filters", padding="5")
        website_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        website_frame.columnconfigure(0, weight=1)
        
        # Search box for websites
        search_frame = ttk.Frame(website_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.website_search_var = tk.StringVar()
        self.website_search_var.trace('w', self.filter_websites)
        ttk.Entry(search_frame, textvariable=self.website_search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Category filter for websites
        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT, padx=(10, 0))
        self.website_category_var = tk.StringVar(value="All Categories")
        self.website_category_combo = ttk.Combobox(search_frame, textvariable=self.website_category_var, state="readonly")
        self.website_category_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.website_category_combo.bind('<<ComboboxSelected>>', self.filter_websites_by_category)
        
        self.website_listbox = tk.Listbox(website_frame, selectmode=tk.MULTIPLE, height=6)
        self.website_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        website_btn_frame = ttk.Frame(website_frame)
        website_btn_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(website_btn_frame, text="Select All", 
                  command=self.select_all_websites).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(website_btn_frame, text="Clear Selection", 
                  command=self.clear_website_selection).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(website_btn_frame, text="Exclude Selected", 
                  command=self.exclude_selected_websites).pack(side=tk.LEFT)
        ttk.Button(website_btn_frame, text="Include Selected", 
                  command=self.include_selected_websites).pack(side=tk.LEFT)
        
        # Custom filter section
        custom_frame = ttk.LabelFrame(left_frame, text="Custom Filters", padding="5")
        custom_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        custom_frame.columnconfigure(1, weight=1)
        
        ttk.Label(custom_frame, text="Field:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.custom_field_var = tk.StringVar()
        custom_field_combo = ttk.Combobox(custom_frame, textvariable=self.custom_field_var, 
                                         values=self.available_fields, state="readonly")
        custom_field_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(5, 0))
        custom_field_combo.set('cat')
        
        ttk.Label(custom_frame, text="Operator:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.custom_operator_var = tk.StringVar()
        custom_operator_combo = ttk.Combobox(custom_frame, textvariable=self.custom_operator_var,
                                            values=self.operators, state="readonly")
        custom_operator_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(5, 0))
        custom_operator_combo.set('!=')
        
        ttk.Label(custom_frame, text="Value:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.custom_value_var = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.custom_value_var).grid(row=2, column=1, sticky=(tk.W, tk.E), 
                                                                        pady=(0, 5), padx=(5, 0))
        
        ttk.Button(custom_frame, text="Add Custom Filter", 
                  command=self.add_custom_filter).grid(row=3, column=0, columnspan=2, pady=(5, 0))
        
        # Right panel - Current filters and output
        right_frame = ttk.LabelFrame(content_frame, text="Current Filters & Output", padding="5")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Current filters with reordering
        ttk.Label(right_frame, text="Current Filters (drag to reorder):").grid(row=0, column=0, sticky=tk.W)
        
        filter_btn_frame = ttk.Frame(right_frame)
        filter_btn_frame.grid(row=0, column=0, sticky=(tk.E), pady=(0, 5))
        
        ttk.Button(filter_btn_frame, text="Clear All", 
                  command=self.clear_all_filters).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(filter_btn_frame, text="Remove Selected", 
                  command=self.remove_selected_filter).pack(side=tk.RIGHT)
        
        # Use a Listbox for filters but we'll handle reordering manually
        self.filters_listbox = tk.Listbox(right_frame, height=10)
        self.filters_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Add move up/down buttons for reordering
        reorder_frame = ttk.Frame(right_frame)
        reorder_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
            
        ttk.Button(reorder_frame, text="Move Up", 
                  command=self.move_filter_up).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(reorder_frame, text="Move Down", 
                  command=self.move_filter_down).pack(side=tk.LEFT)
        
        # Generated filter string
        ttk.Label(right_frame, text="Generated Filter String:").grid(row=3, column=0, sticky=tk.W, pady=(10, 0))
        
        self.filter_output_text = scrolledtext.ScrolledText(right_frame, height=6, width=50)
        self.filter_output_text.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # Special filters section (for filters with spaces)
        ttk.Label(right_frame, text="Special Filters (with spaces):").grid(row=5, column=0, sticky=tk.W, pady=(10, 0))
        
        self.special_filters_text = scrolledtext.ScrolledText(right_frame, height=4, width=50)
        self.special_filters_text.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # Action buttons
        action_frame = ttk.Frame(right_frame)
        action_frame.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(action_frame, text="Generate Filter", 
                  command=self.generate_filter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Save to File", 
                  command=self.save_to_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Copy to Clipboard", 
                  command=self.copy_to_clipboard).pack(side=tk.LEFT)
        
        # Store original website list for filtering
        self.all_websites = []
        self.all_websites_with_categories = []  # Store (website, category) tuples
        
        # Initialize UI state
        self.update_ui_state()
    
    def export_json_analysis(self):
        """Export analysis for each JSON file"""
        if not self.loaded_files:
            messagebox.showwarning("Warning", "No data loaded to export")
            return
        
        # Ask for export directory
        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if not export_dir:
            return
        
        try:
            # Create analysis for each file
            for file_path in self.loaded_files:
                self.export_single_file_analysis(file_path, export_dir)
            
            # Generate summary report
            self.generate_summary_report(export_dir)
            
            messagebox.showinfo("Success", f"JSON analysis exported to:\n{export_dir}\n\n"
                                          f"• Individual file analysis: {len(self.loaded_files)} files\n"
                                          f"• Summary report: summary_report.json")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export analysis: {str(e)}")
    
    def export_single_file_analysis(self, file_path, export_dir):
        """Export analysis for a single JSON file"""
        if file_path not in self.file_entries:
            return
        
        entries = self.file_entries[file_path]
        if not entries:
            return
        
        # Create filename for export
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        export_filename = f"{base_name}_analysis.json"
        export_path = os.path.join(export_dir, export_filename)
        
        # Analyze the file data
        analysis = {
            "relative_path": self.get_relative_source_path(file_path),
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
        
        # Add sample entries (first 10)
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

    def generate_summary_report(self, export_dir):
        """Generate a summary report of all files"""
        summary = {
            "export_timestamp": str(datetime.now()),
            "total_files_analyzed": len(self.loaded_files),
            "total_entries": len(self.loaded_data),
            "files": []
        }

        for file_path in self.loaded_files:
            if file_path in self.file_entries:
                entries = self.file_entries[file_path]
                # Count categories
                categories = {}
                for entry in entries:
                    if 'category' in entry and entry['category']:
                        category = str(entry['category'])
                        categories[category] = categories.get(category, 0) + 1
                # Sort categories by count
                categories = dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))
                file_info = {
                    "relative_path": self.get_relative_source_path(file_path),
                    "entry_count": len(entries),
                    "categories_count": len(categories),
                    "categories": categories,  # Include category breakdown
                    "websites_count": len(self.get_unique_values(entries, 'name'))
                }
                summary["files"].append(file_info)

        # Write summary report
        summary_path = os.path.join(export_dir, "summary_report.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def browse_file(self):
        path = filedialog.askdirectory(title="Select Directory with JSON Files")
        if not path:
            path = filedialog.askopenfilename(
                title="Select JSON File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
        if path:
            self.file_path_var.set(path)
    
    def load_data(self):
        path = self.file_path_var.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Please select a valid file or directory")
            return
        
        try:
            self.loaded_data, self.loaded_files = self.load_json_files(path, self.recursive_var.get())
            if not self.loaded_data:
                messagebox.showwarning("Warning", "No data loaded from the selected path")
                return
            
            # Build site-category relationships with sources
            self.build_site_category_relationships()
            
            # Update JSON structure display
            self.update_json_structure_display()
            
            self.populate_category_list()
            self.populate_website_list()
            self.update_ui_state()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
    
    def update_json_structure_display(self):
        """Show the actual JSON structure found in the files"""
        # Clear the text widget first
        self.json_structure_text.delete(1.0, tk.END)
        
        if not self.loaded_data:
            self.json_structure_text.insert(tk.END, "No data loaded")
            return
        
        # Fields to exclude from display
        exclude_fields = {'url', 'status', 'metadata'}
        
        # Analyze the first few entries to show JSON structure
        sample_entries = self.loaded_data[:1000]  # Show first 1000 entries as samples
        
        structure_info = "JSON Structure Found:\n\n"
        
        for i, entry in enumerate(sample_entries):
            # Extract username from URL if available, otherwise use index
            username = f"Entry {i+1}"
            if 'url' in entry and entry['url']:
                # Extract username from URL like "https://t.me/cssunshine"
                url = entry['url']
                if '/' in url:
                    # Get the last part of the URL after the last slash
                    username = url.split('/')[-1]
            
            # Find which file this entry came from
            file_source = "Unknown source"
            for file_path, entries in self.file_entries.items():
                if entry in entries:
                    # Get relative path from the base directory
                    rel_path = self.get_relative_source_path(file_path)
                    file_source = rel_path
                    break
            
            structure_info += f"Sample {username} (from: {file_source}):\n"
            for key, value in entry.items():
                # Skip excluded fields
                if key in exclude_fields:
                    continue
                structure_info += f"  \"{key}\": \"{value}\"\n"
            structure_info += "\n"
        
        # Show field mapping
        structure_info += "Field Mapping (JSON → Blackbird):\n"
        for json_field, blackbird_field in self.field_mapping.items():
            if any(json_field in entry for entry in self.loaded_data):
                unique_count = len(self.get_unique_values(self.loaded_data, json_field))
                structure_info += f"  \"{json_field}\" → {blackbird_field} ({unique_count} unique values)\n"
        
        # Insert the structure info into the Text widget
        self.json_structure_text.insert(tk.END, structure_info)
    
    def build_site_category_relationships(self):
        """Build mappings between sites and their categories, and track sources"""
        self.site_categories = {}
        self.category_sites = {}
        self.site_sources = {}
        self.category_sources = {}
        
        for file_path, entries in self.file_entries.items():
            for item in entries:
                # Use exact JSON field names
                if 'name' in item and item['name']:
                    site_name = str(item['name'])
                    
                    # Map site to sources
                    if site_name not in self.site_sources:
                        self.site_sources[site_name] = []
                    if file_path not in self.site_sources[site_name]:
                        self.site_sources[site_name].append(file_path)
                    
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
    
    def load_json_files(self, path: str, recursive: bool = True) -> Tuple[List[Dict[str, Any]], List[str]]:
        data = []
        loaded_files = []
        
        if os.path.isfile(path):
            file_data = self._load_single_file(path)
            if file_data:
                data.extend(file_data)
                loaded_files.append(path)
                # Track source for this file
                self.file_entries[path] = file_data
        elif os.path.isdir(path):
            if recursive:
                json_files = self._find_json_files_recursive(path)
            else:
                json_pattern = os.path.join(path, "*.json")
                json_files = glob.glob(json_pattern)
            
            for json_file in json_files:
                file_data = self._load_single_file(json_file)
                if file_data:
                    data.extend(file_data)
                    loaded_files.append(json_file)
                    # Track source for this file
                    self.file_entries[json_file] = file_data
        
        return data, loaded_files
    
    def _find_json_files_recursive(self, directory: str) -> List[str]:
        json_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.json'):
                    full_path = os.path.join(root, file)
                    json_files.append(full_path)
        return json_files
    
    def _load_single_file(self, file_path: str) -> List[Dict[str, Any]]:
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
        values = set()
        for item in data:
            if json_field in item and item[json_field] is not None:
                values.add(str(item[json_field]))
        return sorted(list(values))
    
    def get_relative_source_path(self, full_path):
        """Convert full file path to a more readable relative format"""
        base_path = self.file_path_var.get()
        if base_path and full_path.startswith(base_path):
            return os.path.relpath(full_path, base_path)
        
        # If no base path or path doesn't match, show the last 2 directory components
        dirname = os.path.dirname(full_path)
        basename = os.path.basename(full_path)
        parent_dir = os.path.basename(os.path.dirname(dirname))
        current_dir = os.path.basename(dirname)
        
        if parent_dir and parent_dir != current_dir:
            return os.path.join(parent_dir, current_dir, basename)
        else:
            return os.path.join(current_dir, basename)

    def populate_category_list(self):
        self.category_listbox.delete(0, tk.END)
        categories = self.get_unique_values(self.loaded_data, 'category')
        
        # Count occurrences and sites per category
        cat_count = {}
        for item in self.loaded_data:
            if 'category' in item and item['category']:
                cat = str(item['category'])
                cat_count[cat] = cat_count.get(cat, 0) + 1
        
        # Sort by count descending
        sorted_categories = sorted(categories, key=lambda x: (-cat_count.get(x, 0), x))
        
        for cat in sorted_categories:
            count = cat_count.get(cat, 0)
            site_count = len(self.category_sites.get(cat, []))
            source_count = len(self.category_sources.get(cat, []))
            
            source_info = f" [from {source_count} sources]" if source_count > 1 else ""
            self.category_listbox.insert(tk.END, f"{cat} ({count} entries, {site_count} sites{source_info})")
    
    def populate_website_list(self):
        self.website_listbox.delete(0, tk.END)
        
        # Build list of websites with their categories and sources
        self.all_websites_with_categories = []
        site_count = {}
        
        for item in self.loaded_data:
            if 'name' in item and item['name']:
                name = str(item['name'])
                category = self.site_categories.get(name, "Unknown")
                site_count[name] = site_count.get(name, 0) + 1
                self.all_websites_with_categories.append((name, category))
        
        # Remove duplicates and sort by count descending
        unique_sites = {}
        for name, category in self.all_websites_with_categories:
            if name not in unique_sites:
                source_count = len(self.site_sources.get(name, []))
                source_info = f" [{source_count} sources]" if source_count > 1 else ""
                unique_sites[name] = (category, site_count.get(name, 0), source_info)
        
        sorted_websites = sorted(unique_sites.items(), key=lambda x: (-x[1][1], x[0]))
        self.all_websites = [site[0] for site in sorted_websites]
        
        # Populate website list with category and source info
        for website, (category, count, source_info) in sorted_websites:
            self.website_listbox.insert(tk.END, f"{website} [{category}] ({count} entries{source_info})")
        
        # Populate category filter for websites
        categories = ["All Categories"] + sorted(self.get_unique_values(self.loaded_data, 'category'))
        self.website_category_combo['values'] = categories
        self.website_category_combo.set("All Categories")
    
    def filter_websites(self, *args):
        search_term = self.website_search_var.get().lower()
        selected_category = self.website_category_var.get()
        self.website_listbox.delete(0, tk.END)
        
        # Rebuild the display list with source information
        display_data = {}
        for website, category in self.all_websites_with_categories:
            if website not in display_data:
                count = 0
                for item in self.loaded_data:
                    if 'name' in item and item['name'] and str(item['name']) == website:
                        count += 1
                source_count = len(self.site_sources.get(website, []))
                source_info = f" [{source_count} sources]" if source_count > 1 else ""
                display_data[website] = (category, count, source_info)
        
        for website, (category, count, source_info) in display_data.items():
            # Apply search filter
            matches_search = search_term in website.lower()
            
            # Apply category filter
            matches_category = (selected_category == "All Categories" or selected_category == category)
            
            if matches_search and matches_category:
                self.website_listbox.insert(tk.END, f"{website} [{category}] ({count} entries{source_info})")
    
    def filter_websites_by_category(self, event=None):
        """Filter websites when category selection changes"""
        self.filter_websites()
    
    def select_all_categories(self):
        self.category_listbox.select_set(0, tk.END)
    
    def clear_category_selection(self):
        self.category_listbox.selection_clear(0, tk.END)
    
    def select_all_websites(self):
        self.website_listbox.select_set(0, tk.END)
    
    def clear_website_selection(self):
        self.website_listbox.selection_clear(0, tk.END)
    
    def exclude_selected_categories(self):
        selected_indices = self.category_listbox.curselection()
        for idx in selected_indices:
            item_text = self.category_listbox.get(idx)
            # Extract category name (remove count part)
            category = item_text.split(' (')[0]
            # Exclude the entire category - using 'cat' for Blackbird filter
            self.add_filter('cat', '!=', category)
        self.update_filters_display()

    def include_selected_categories(self):
        selected_indices = self.category_listbox.curselection()
        for idx in selected_indices:
            item_text = self.category_listbox.get(idx)
            # Extract category name (remove count part)
            category = item_text.split(' (')[0]
            # Include the entire category - using 'cat' for Blackbird filter
            self.add_filter('cat', '=', category)
        self.update_filters_display()
    
    def exclude_selected_websites(self):
        selected_indices = self.website_listbox.curselection()
        for idx in selected_indices:
            item_text = self.website_listbox.get(idx)
            # Extract website name (remove category and count parts)
            website = item_text.split(' [')[0]
            # Exclude website - using 'name' for Blackbird filter
            self.add_filter('name', '!=', website)
        self.update_filters_display()
    
    def include_selected_websites(self):
        selected_indices = self.website_listbox.curselection()
        for idx in selected_indices:
            item_text = self.website_listbox.get(idx)
            # Extract website name (remove category and count parts)
            website = item_text.split(' [')[0]
            # Include website - using 'name' for Blackbird filter
            self.add_filter('name', '=', website)
        self.update_filters_display()
    
    def add_custom_filter(self):
        field = self.custom_field_var.get()
        operator = self.custom_operator_var.get()
        value = self.custom_value_var.get()
        
        if not field or not operator or not value:
            messagebox.showwarning("Warning", "Please fill in all custom filter fields")
            return
        
        self.add_filter(field, operator, value)
        self.custom_value_var.set('')  # Clear value field
        self.update_filters_display()
    
    def add_filter(self, filter_field: str, operator: str, value: str):
        # Check if value contains spaces - if so, use single quotes
        if ' ' in value and operator in ['=', '!=', '~']:
            # Escape any single quotes in the value
            escaped_value = value.replace("'", "\\'")
            filter_str = f"{filter_field}{operator}'{escaped_value}'"
        else:
            # For values without spaces
            filter_str = f"{filter_field}{operator}{value}"
        
        self.filters.append(filter_str)
    
    def remove_selected_filter(self):
        selected_indices = self.filters_listbox.curselection()
        for idx in selected_indices[::-1]:  # Reverse to maintain indices
            if 0 <= idx < len(self.filters):
                self.filters.pop(idx)
        self.update_filters_display()
    
    def move_filter_up(self):
        selected_indices = self.filters_listbox.curselection()
        if not selected_indices:
            return
        
        idx = selected_indices[0]
        if idx > 0:
            # Swap with previous filter
            self.filters[idx], self.filters[idx-1] = self.filters[idx-1], self.filters[idx]
            self.update_filters_display()
            self.filters_listbox.select_set(idx-1)
    
    def move_filter_down(self):
        selected_indices = self.filters_listbox.curselection()
        if not selected_indices:
            return
        
        idx = selected_indices[0]
        if idx < len(self.filters) - 1:
            # Swap with next filter
            self.filters[idx], self.filters[idx+1] = self.filters[idx+1], self.filters[idx]
            self.update_filters_display()
            self.filters_listbox.select_set(idx+1)
    
    def clear_all_filters(self):
        self.filters.clear()
        self.update_filters_display()
    
    def update_filters_display(self):
        self.filters_listbox.delete(0, tk.END)
        for filter_str in self.filters:
            self.filters_listbox.insert(tk.END, filter_str)
    
    def generate_filter(self):
        """Generate the complete filter string"""
        # Clear both text areas
        self.filter_output_text.delete(1.0, tk.END)
        self.special_filters_text.delete(1.0, tk.END)
        
        if not self.filters:
            messagebox.showwarning("Warning", "No filters to generate")
            return
        
        # Separate filters into two groups: regular and special (with spaces)
        regular_filters = []
        special_filters = []
        
        for filter_str in self.filters:
            # Check if the filter has a space in the value part (not just in the field part)
            # This looks for patterns like name!='Mastodon API' or name='Some Site'
            if "'" in filter_str or " " in filter_str.split("=")[-1].split("!=")[-1].split("~")[-1]:
                special_filters.append(filter_str)
            else:
                regular_filters.append(filter_str)
        
        # Generate regular filter string (joined with 'and')
        if regular_filters:
            regular_string = " and ".join(regular_filters)
            # Wrap in quotes
            self.filter_output_text.insert(1.0, f'"{regular_string}"')
        
        # Generate special filters (each on its own line, wrapped in quotes)
        if special_filters:
            for i, filter_str in enumerate(special_filters):
                # Wrap each special filter in quotes
                self.special_filters_text.insert(tk.END, f'"{filter_str}"')
                if i < len(special_filters) - 1:
                    self.special_filters_text.insert(tk.END, '\n')
        
        # Show a warning if there are potential issues
        self.validate_filters()
    
    def join_filters_safely(self) -> str:
        """
        Generate the complete filter string for copying/saving
        """
        if not self.filters:
            return ""
        
        # Separate filters into two groups
        regular_filters = []
        special_filters = []
        
        for filter_str in self.filters:
            # Check if the filter has a space in the value part
            if "'" in filter_str or " " in filter_str.split("=")[-1].split("!=")[-1].split("~")[-1]:
                special_filters.append(filter_str)
            else:
                regular_filters.append(filter_str)
        
        result = []
        
        # Add regular filters first
        if regular_filters:
            regular_string = " and ".join(regular_filters)
            result.append(f'"{regular_string}"')
        
        # Add special filters
        for filter_str in special_filters:
            result.append(f'"{filter_str}"')
        
        return "\n".join(result)
    
    def validate_filters(self):
        """Check for potential issues in the generated filter"""
        warnings = []
        
        # Check for duplicate filters
        seen = set()
        duplicates = set()
        for filter_str in self.filters:
            if filter_str in seen:
                duplicates.add(filter_str)
            seen.add(filter_str)
        
        if duplicates:
            warnings.append(f"Duplicate filters found: {', '.join(duplicates)}")
        
        if warnings:
            messagebox.showwarning("Filter Validation", "\n".join(warnings))
    
    def save_to_file(self):
        filter_string = self.join_filters_safely()
        if not filter_string:
            messagebox.showwarning("Warning", "No filters to save")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Filter",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(filter_string)
                messagebox.showinfo("Success", f"Filter saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def copy_to_clipboard(self):
        filter_string = self.join_filters_safely()
        if not filter_string:
            messagebox.showwarning("Warning", "No filters to copy")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(filter_string)
        messagebox.showinfo("Success", "Filter copied to clipboard!")
    
    def update_ui_state(self):
        has_data = len(self.loaded_data) > 0
        state = tk.NORMAL if has_data else tk.DISABLED
        
        # Enable/disable widgets based on data availability
        self.category_listbox.config(state=state)
        self.website_listbox.config(state=state)
        self.website_category_combo.config(state=state)

def main():
    root = tk.Tk()
    app = BlackbirdFilterGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()