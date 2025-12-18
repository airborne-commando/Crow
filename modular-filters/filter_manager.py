from typing import List

class FilterManager:
    def __init__(self):
        self.filters: List[str] = []
    
    def add_filter(self, filter_field: str, operator: str, value: str) -> None:
        """Add a new filter to the list"""
        # Check if value contains spaces - if so, use single quotes
        if ' ' in value and operator in ['=', '!=', '~']:
            # Escape any single quotes in the value
            escaped_value = value.replace("'", "\\'")
            filter_str = f"{filter_field}{operator}'{escaped_value}'"
        else:
            # For values without spaces
            filter_str = f"{filter_field}{operator}{value}"
        
        self.filters.append(filter_str)
    
    def remove_filter(self, index: int) -> None:
        """Remove filter at specified index"""
        if 0 <= index < len(self.filters):
            self.filters.pop(index)
    
    def clear_filters(self) -> None:
        """Clear all filters"""
        self.filters.clear()
    
    def move_filter_up(self, index: int) -> None:
        """Move filter up in the list"""
        if index > 0:
            self.filters[index], self.filters[index-1] = self.filters[index-1], self.filters[index]
    
    def move_filter_down(self, index: int) -> None:
        """Move filter down in the list"""
        if index < len(self.filters) - 1:
            self.filters[index], self.filters[index+1] = self.filters[index+1], self.filters[index]
    
    def get_filter_string(self) -> str:
        """Generate the complete filter string for copying/saving"""
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
    
    def validate_filters(self) -> List[str]:
        """Check for potential issues in the filters"""
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
        
        return warnings
    
    def get_regular_filters(self) -> List[str]:
        """Get filters without spaces in values"""
        regular = []
        for filter_str in self.filters:
            if not ("'" in filter_str or " " in filter_str.split("=")[-1].split("!=")[-1].split("~")[-1]):
                regular.append(filter_str)
        return regular
    
    def get_special_filters(self) -> List[str]:
        """Get filters with spaces in values"""
        special = []
        for filter_str in self.filters:
            if "'" in filter_str or " " in filter_str.split("=")[-1].split("!=")[-1].split("~")[-1]:
                special.append(filter_str)
        return special