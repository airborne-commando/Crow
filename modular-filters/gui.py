import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import List, Tuple

from data_loader import DataLoader
from data_analyzer import DataAnalyzer
from filter_manager import FilterManager
from exporter import Exporter
from config_manager import ConfigManager

class BlackbirdFilterGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Blackbird Filter Generator")
        self.root.geometry("1000x900")
        
        # Initialize modules
        self.data_loader = DataLoader()
        self.data_analyzer = DataAnalyzer()
        self.filter_manager = FilterManager()
        self.exporter = Exporter(self.data_loader)
        
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
        
        self.loaded_data = []
        self.loaded_files = []
        
        # Store original website list for filtering
        self.all_websites = []
        self.all_websites_with_categories = []  # Store (website, category) tuples
        
        self.setup_gui()
        self.update_ui_state()
    
    def setup_gui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
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
        
        # Configuration buttons in file frame
        ttk.Button(file_frame, text="Save Configuration", 
                  command=self.save_configuration).grid(row=0, column=4, padx=(10, 0))
        ttk.Button(file_frame, text="Load Configuration", 
                  command=self.load_configuration).grid(row=0, column=5, padx=(10, 0))

        ttk.Button(file_frame, text="Export JSON Analysis", 
                  command=self.export_json_analysis).grid(row=0, column=6, padx=(10, 0))

        # JSON Structure Display
        json_frame = ttk.LabelFrame(main_frame, text="JSON Structure Preview", padding="5")
        json_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        json_frame.columnconfigure(0, weight=1)
        json_frame.rowconfigure(0, weight=1)

        # Create a Text widget for JSON preview
        self.json_structure_text = tk.Text(json_frame, wrap=tk.WORD, height=10)
        self.json_structure_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create a Scrollbar
        scrollbar = ttk.Scrollbar(json_frame, orient=tk.VERTICAL, command=self.json_structure_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E))

        # Link the Text widget to the Scrollbar
        self.json_structure_text.config(yscrollcommand=scrollbar.set)
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
        
        # Import filters button
        ttk.Button(filter_btn_frame, text="Import Filters", 
                  command=self.import_filters).pack(side=tk.RIGHT, padx=(5, 0))
        
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
    
    # GUI event handlers (simplified versions using the modules)
    
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
            self.loaded_data, self.loaded_files = self.data_loader.load_json_files(
                path, self.recursive_var.get()
            )
            
            if not self.loaded_data:
                messagebox.showwarning("Warning", "No data loaded from the selected path")
                return
            
            # Build site-category relationships with sources
            self.data_analyzer.build_relationships(
                self.loaded_data, self.data_loader.file_entries
            )
            
            # Update JSON structure display
            self.update_json_structure_display()
            
            self.populate_category_list()
            self.populate_website_list()
            self.update_ui_state()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
    
    def update_json_structure_display(self):
        """Show the actual JSON structure found in the files"""
        self.json_structure_text.delete(1.0, tk.END)
        
        if not self.loaded_data:
            self.json_structure_text.insert(tk.END, "No data loaded")
            return
        
        structure_info = "JSON Structure Found:\n\n"
        
        # Show sample entries
        for i, entry in enumerate(self.loaded_data[:1000]):
            username = f"Entry {i+1}"
            if 'url' in entry and entry['url']:
                url = entry['url']
                if '/' in url:
                    username = url.split('/')[-1]
            
            # Find which file this entry came from
            file_source = "Unknown source"
            for file_path, entries in self.data_loader.file_entries.items():
                if entry in entries:
                    rel_path = self.data_loader.get_relative_source_path(file_path, self.file_path_var.get())
                    file_source = rel_path
                    break
            
            structure_info += f"Sample {username} (from: {file_source}):\n"
            for key, value in entry.items():
                if key not in {'url', 'status', 'metadata'}:
                    structure_info += f"  \"{key}\": \"{value}\"\n"
            structure_info += "\n"
        
        # Show field mapping
        structure_info += "Field Mapping (JSON → Blackbird):\n"
        for json_field, blackbird_field in self.field_mapping.items():
            if any(json_field in entry for entry in self.loaded_data):
                unique_count = len(self.data_loader.get_unique_values(self.loaded_data, json_field))
                structure_info += f"  \"{json_field}\" → {blackbird_field} ({unique_count} unique values)\n"
        
        self.json_structure_text.insert(tk.END, structure_info)
    
    def populate_category_list(self):
        self.category_listbox.delete(0, tk.END)
        categories = self.data_loader.get_unique_values(self.loaded_data, 'category')
        
        # Count occurrences and sites per category
        cat_counts = self.data_analyzer.count_entries_by_category(self.loaded_data)
        
        # Sort by count descending
        sorted_categories = sorted(categories, key=lambda x: (-cat_counts.get(x, 0), x))
        
        for cat in sorted_categories:
            count = cat_counts.get(cat, 0)
            site_count = len(self.data_analyzer.get_sites_by_category(cat))
            source_count = len(self.data_analyzer.get_sources_for_category(cat))
            
            source_info = f" [from {source_count} sources]" if source_count > 1 else ""
            self.category_listbox.insert(tk.END, f"{cat} ({count} entries, {site_count} sites{source_info})")
    
    def populate_website_list(self):
        self.website_listbox.delete(0, tk.END)
        
        # Build list of websites with their categories and sources
        self.all_websites_with_categories = []
        site_counts = self.data_analyzer.count_entries_by_site(self.loaded_data)
        
        for site_name in site_counts.keys():
            category = self.data_analyzer.get_category_for_site(site_name)
            self.all_websites_with_categories.append((site_name, category))
        
        # Sort by count descending
        self.all_websites = sorted(
            site_counts.keys(), 
            key=lambda x: (-site_counts.get(x, 0), x)
        )
        
        # Populate website list with category and source info
        for website in self.all_websites:
            category = self.data_analyzer.get_category_for_site(website)
            count = site_counts.get(website, 0)
            source_count = len(self.data_analyzer.get_sources_for_site(website))
            source_info = f" [{source_count} sources]" if source_count > 1 else ""
            self.website_listbox.insert(tk.END, f"{website} [{category}] ({count} entries{source_info})")
        
        # Populate category filter for websites
        categories = ["All Categories"] + self.data_loader.get_unique_values(self.loaded_data, 'category')
        self.website_category_combo['values'] = categories
        self.website_category_combo.set("All Categories")
    
    def filter_websites(self, *args):
        search_term = self.website_search_var.get().lower()
        selected_category = self.website_category_var.get()
        self.website_listbox.delete(0, tk.END)
        
        site_counts = self.data_analyzer.count_entries_by_site(self.loaded_data)
        
        for website, category in self.all_websites_with_categories:
            # Apply search filter
            matches_search = search_term in website.lower()
            
            # Apply category filter
            matches_category = (selected_category == "All Categories" or selected_category == category)
            
            if matches_search and matches_category:
                count = site_counts.get(website, 0)
                source_count = len(self.data_analyzer.get_sources_for_site(website))
                source_info = f" [{source_count} sources]" if source_count > 1 else ""
                self.website_listbox.insert(tk.END, f"{website} [{category}] ({count} entries{source_info})")
    
    def filter_websites_by_category(self, event=None):
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
            category = item_text.split(' (')[0]
            self.filter_manager.add_filter('cat', '!=', category)
        self.update_filters_display()
    
    def include_selected_categories(self):
        selected_indices = self.category_listbox.curselection()
        for idx in selected_indices:
            item_text = self.category_listbox.get(idx)
            category = item_text.split(' (')[0]
            self.filter_manager.add_filter('cat', '=', category)
        self.update_filters_display()
    
    def exclude_selected_websites(self):
        selected_indices = self.website_listbox.curselection()
        for idx in selected_indices:
            item_text = self.website_listbox.get(idx)
            website = item_text.split(' [')[0]
            self.filter_manager.add_filter('name', '!=', website)
        self.update_filters_display()
    
    def include_selected_websites(self):
        selected_indices = self.website_listbox.curselection()
        for idx in selected_indices:
            item_text = self.website_listbox.get(idx)
            website = item_text.split(' [')[0]
            self.filter_manager.add_filter('name', '=', website)
        self.update_filters_display()
    
    def add_custom_filter(self):
        field = self.custom_field_var.get()
        operator = self.custom_operator_var.get()
        value = self.custom_value_var.get()
        
        if not field or not operator or not value:
            messagebox.showwarning("Warning", "Please fill in all custom filter fields")
            return
        
        self.filter_manager.add_filter(field, operator, value)
        self.custom_value_var.set('')
        self.update_filters_display()
    
    def remove_selected_filter(self):
        selected_indices = self.filters_listbox.curselection()
        for idx in selected_indices[::-1]:
            self.filter_manager.remove_filter(idx)
        self.update_filters_display()
    
    def move_filter_up(self):
        selected_indices = self.filters_listbox.curselection()
        if not selected_indices:
            return
        
        idx = selected_indices[0]
        self.filter_manager.move_filter_up(idx)
        self.update_filters_display()
        self.filters_listbox.select_set(idx-1)
    
    def move_filter_down(self):
        selected_indices = self.filters_listbox.curselection()
        if not selected_indices:
            return
        
        idx = selected_indices[0]
        self.filter_manager.move_filter_down(idx)
        self.update_filters_display()
        self.filters_listbox.select_set(idx+1)
    
    def clear_all_filters(self):
        self.filter_manager.clear_filters()
        self.update_filters_display()
    
    def update_filters_display(self):
        self.filters_listbox.delete(0, tk.END)
        for filter_str in self.filter_manager.filters:
            self.filters_listbox.insert(tk.END, filter_str)
    
    def generate_filter(self):
        """Generate the complete filter string"""
        self.filter_output_text.delete(1.0, tk.END)
        self.special_filters_text.delete(1.0, tk.END)
        
        if not self.filter_manager.filters:
            messagebox.showwarning("Warning", "No filters to generate")
            return
        
        # Generate regular filter string
        regular_filters = self.filter_manager.get_regular_filters()
        if regular_filters:
            regular_string = " and ".join(regular_filters)
            self.filter_output_text.insert(1.0, f'"{regular_string}"')
        
        # Generate special filters
        special_filters = self.filter_manager.get_special_filters()
        if special_filters:
            for i, filter_str in enumerate(special_filters):
                self.special_filters_text.insert(tk.END, f'"{filter_str}"')
                if i < len(special_filters) - 1:
                    self.special_filters_text.insert(tk.END, '\n')
        
        # Show warnings if any
        warnings = self.filter_manager.validate_filters()
        if warnings:
            messagebox.showwarning("Filter Validation", "\n".join(warnings))
    
    def save_to_file(self):
        filter_string = self.filter_manager.get_filter_string()
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
        filter_string = self.filter_manager.get_filter_string()
        if not filter_string:
            messagebox.showwarning("Warning", "No filters to copy")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(filter_string)
        messagebox.showinfo("Success", "Filter copied to clipboard!")
    
    def save_configuration(self):
        if not self.filter_manager.filters:
            if not messagebox.askyesno("Save Configuration", 
                                      "No filters defined. Save empty configuration?"):
                return
        
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            ConfigManager.save_configuration(
                filename=filename,
                filters=self.filter_manager.filters,
                data_source_path=self.file_path_var.get(),
                recursive=self.recursive_var.get(),
                loaded_files_count=len(self.loaded_files),
                entries_count=len(self.loaded_data),
                custom_field=self.custom_field_var.get(),
                custom_operator=self.custom_operator_var.get(),
                custom_value=self.custom_value_var.get(),
                website_search=self.website_search_var.get(),
                website_category_filter=self.website_category_var.get()
            )
            
            messagebox.showinfo("Success", f"Configuration saved to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_configuration(self):
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            config = ConfigManager.load_configuration(filename)
            
            # Check if it's a valid configuration file
            if not isinstance(config, dict) or 'filters' not in config:
                messagebox.showerror("Error", "Invalid configuration file format")
                return
            
            # Ask user if they want to clear existing filters
            if self.filter_manager.filters and not messagebox.askyesno(
                "Load Configuration", "This will replace current filters. Continue?"
            ):
                return
            
            # Clear existing filters
            self.filter_manager.clear_filters()
            
            # Load filters
            if 'list' in config['filters']:
                for filter_str in config['filters']['list']:
                    # Parse the filter string to add it properly
                    # This is a simplified version - you might want to improve this
                    self.filter_manager.filters.append(filter_str)
            
            # Update data source settings if available
            if 'data_source' in config:
                data_source = config['data_source']
                if 'path' in data_source:
                    self.file_path_var.set(data_source.get('path', ''))
                if 'recursive' in data_source:
                    self.recursive_var.set(data_source.get('recursive', True))
            
            # Update custom filter settings if available
            if 'custom_filter_settings' in config:
                settings = config['custom_filter_settings']
                self.custom_field_var.set(settings.get('field', 'cat'))
                self.custom_operator_var.set(settings.get('operator', '!='))
                self.custom_value_var.set(settings.get('value', ''))
            
            # Update UI state if available
            if 'ui_state' in config:
                ui_state = config['ui_state']
                self.website_search_var.set(ui_state.get('website_search', ''))
                self.website_category_var.set(ui_state.get('website_category_filter', 'All Categories'))
            
            # Update UI
            self.update_filters_display()
            
            # If data was already loaded, regenerate the filter
            if self.loaded_data:
                self.generate_filter()
            
            messagebox.showinfo("Success", f"Configuration loaded from:\n{filename}\n\nLoaded {len(self.filter_manager.filters)} filters.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def import_filters(self):
        filename = filedialog.askopenfilename(
            title="Import Filters",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            filters_to_add = ConfigManager.parse_imported_filters(content)
            
            if not filters_to_add:
                messagebox.showwarning("Import Filters", "No valid filters found in the file")
                return
            
            # Ask user how to import
            import_option = messagebox.askyesnocancel(
                "Import Filters",
                f"Found {len(filters_to_add)} filter(s). How would you like to import them?\n\n"
                f"Yes: Replace existing filters\n"
                f"No: Append to existing filters\n"
                f"Cancel: Abort import"
            )
            
            if import_option is None:
                return
            elif import_option:
                self.filter_manager.filters = filters_to_add
            else:
                self.filter_manager.filters.extend(filters_to_add)
                # Remove duplicates while preserving order
                seen = set()
                unique_filters = []
                for f in self.filter_manager.filters:
                    if f not in seen:
                        seen.add(f)
                        unique_filters.append(f)
                self.filter_manager.filters = unique_filters
            
            # Update UI
            self.update_filters_display()
            
            # If data was already loaded, regenerate the filter
            if self.loaded_data:
                self.generate_filter()
            
            messagebox.showinfo("Success", f"Imported {len(filters_to_add)} filter(s)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import filters: {str(e)}")
    
    def export_json_analysis(self):
        if not self.loaded_files:
            messagebox.showwarning("Warning", "No data loaded to export")
            return
        
        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if not export_dir:
            return
        
        try:
            self.exporter.export_json_analysis(
                self.loaded_files, 
                self.data_loader.file_entries, 
                export_dir
            )
            
            messagebox.showinfo("Success", f"JSON analysis exported to:\n{export_dir}\n\n"
                                          f"• Individual file analysis: {len(self.loaded_files)} files\n"
                                          f"• Summary report: summary_report.json")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export analysis: {str(e)}")
    
    def update_ui_state(self):
        has_data = len(self.loaded_data) > 0
        state = tk.NORMAL if has_data else tk.DISABLED
        
        # Enable/disable widgets based on data availability
        self.category_listbox.config(state=state)
        self.website_listbox.config(state=state)
        self.website_category_combo.config(state=state)