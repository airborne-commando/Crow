import os
import json
import re
import time
import requests
from datetime import datetime
from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog)
from PyQt6.QtCore import QThread, pyqtSignal

class BreachVIP(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Breach.vip Search")
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()

        # Create email input section
        email_label = QLabel("Email to Search:")
        self.hudson_email_input = QLineEdit()
        layout.addWidget(email_label)
        layout.addWidget(self.hudson_email_input)

        # File input section
        # file_label = QLabel("Email File:")
        self.breach_email_file_input = QLineEdit()
        self.breach_email_file_button = QPushButton("Select Email File")
        self.breach_email_file_button.clicked.connect(self.select_breach_email_file)
        
        email_file_layout = QHBoxLayout()
        email_file_layout.addWidget(self.breach_email_file_input)
        email_file_layout.addWidget(self.breach_email_file_button)
        
        # layout.addWidget(file_label)
        layout.addLayout(email_file_layout)

        # Search button
        self.breach_search_button = QPushButton("Search Breach.VIP")
        self.breach_search_button.clicked.connect(self.search_breach_rock)
        layout.addWidget(self.breach_search_button)

        self.setLayout(layout)

    def select_breach_email_file(self):
        """Select email file specifically for Breach.vip search"""
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Email File for Breach.vip")
        if file_name:
            self.breach_email_file_input.setText(file_name)

    def get_output_area(self):
        """Get the output area from parent"""
        return self.parent.output_area if self.parent else None

    # INDENT ALL THESE METHODS TO BE PART OF THE CLASS
    def search_breach_rock(self):
        """Search Breach.vip for email information using the official API"""
        # Use Breach.vip specific inputs
        email = self.hudson_email_input.text().strip()
        file_path = self.breach_email_file_input.text().strip()
        
        # Check if we have file input
        if file_path and os.path.isfile(file_path):
            self.process_breach_email_file(file_path)
        elif email:
            # Validate single email format
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                QMessageBox.warning(self, "Input Error", "Please enter a valid email address or file path.")
                return
            self.process_single_breach_email(email)
        else:
            QMessageBox.warning(self, "Input Error", "Please enter an email address or select an email file.")

    def process_breach_email_file(self, file_path):
        """Process a file containing multiple emails for Breach.vip search"""
        output_area = self.get_output_area()
        if not output_area:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                emails = [line.strip() for line in f if line.strip()]
                
            if not emails:
                QMessageBox.warning(self, "File Error", "The file is empty or contains no valid emails.")
                return
                
            valid_emails = []
            invalid_emails = []
            
            # Validate emails
            for email in emails:
                if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                    valid_emails.append(email)
                else:
                    invalid_emails.append(email)
                    
            if not valid_emails:
                QMessageBox.warning(self, "File Error", "No valid email addresses found in the file.")
                return
                
            # Show confirmation dialog for multiple emails
            if len(valid_emails) > 1:
                reply = QMessageBox.question(
                    self,
                    "Multiple Emails Found",
                    f"Found {len(valid_emails)} valid email(s) and {len(invalid_emails)} invalid entry(s).\n\n"
                    f"Do you want to search all {len(valid_emails)} emails? This may take a while due to rate limits.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
                    
            # Process all valid emails
            output_area.append(f"📁 Processing {len(valid_emails)} email(s) from file: {os.path.basename(file_path)}")
            if invalid_emails:
                output_area.append(f"⚠️  Skipped {len(invalid_emails)} invalid entries")
                
            output_area.append("=" * 60)
        
            # Create results directory if it doesn't exist
            results_dir = "results"
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
                
            # Generate batch filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_filename = f"breach_vip_batch_{timestamp}.txt"
            batch_filepath = os.path.join(results_dir, batch_filename)
            
            all_results = []
            
            for i, email in enumerate(valid_emails, 1):
                output_area.append(f"\n🔍 [{i}/{len(valid_emails)}] Searching: {email}")
                
                try:
                    result = self.search_single_breach_email_api(email)
                    all_results.append({
                        'email': email,
                        'result': result,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
                    # Display brief result
                    if result.get('success', False) and result.get('data'):
                        data = result['data']
                        if data.get('results') and len(data['results']) > 0:
                            record_count = len(data['results'])
                            unique_breaches = len(set(r.get('source', '') for r in data['results']))
                            output_area.append(f"   🚨 Found {record_count} records across {unique_breaches} breaches")
                        else:
                            output_area.append(f"   ✅ No breach records found")
                    else:
                        output_area.append(f"   ❌ Search failed: {result.get('error', 'Unknown error')}")
                        
                    # Respect rate limit - wait between requests
                    if i < len(valid_emails):  # Don't wait after the last one
                        time.sleep(4)  # 4 seconds between requests to stay under 15/minute
                        
                except Exception as e:
                    output_area.append(f"   ❌ Error searching {email}: {e}")
                    all_results.append({
                        'email': email,
                        'result': {'success': False, 'error': str(e)},
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
            # Save batch results
            self.save_breach_batch_results(all_results, batch_filepath)
            output_area.append(f"\n💾 Batch results saved to: {batch_filepath}")
            output_area.append("🎉 Batch search completed!")
            
        except Exception as e:
            output_area.append(f"❌ Error processing file: {e}")

    def process_single_breach_email(self, email):
        """Process a single email for Breach.vip search"""
        output_area = self.get_output_area()
        if not output_area:
            return
            
        output_area.append(f"🔍 Searching Breach.vip for: {email}")
        
        try:
            result = self.search_single_breach_email_api(email)
            
            if result.get('success', False):
                data = result['data']
                self.display_breach_results(data, email)
            else:
                output_area.append(f"❌ Search failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            output_area.append(f"❌ Error searching {email}: {e}")

    def search_single_breach_email_api(self, email):
        """Make API call to Breach.vip for a single email"""
        try:
            url = "https://breach.vip/api/search"
            
            payload = {
                "term": email,
                "fields": ["email"],
                "categories": None,
                "wildcard": False,
                "case_sensitive": False
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }
            else:
                error_msg = f"API returned status {response.status_code}"
                if response.status_code == 429:
                    error_msg = "Rate limited - please wait 1 minute"
                elif response.status_code == 400:
                    error_msg = "Bad request"
                elif response.status_code == 500:
                    error_msg = "Internal server error"
                    
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Network error: {e}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {e}"
            }

    def save_breach_batch_results(self, all_results, filepath):
        """Save batch Breach.vip results to file"""
        output_area = self.get_output_area()
        try:
            # Calculate summary stats BEFORE opening the file
            successful_searches = sum(1 for r in all_results if r['result'].get('success'))
            total_records = sum(len(r['result'].get('data', {}).get('results', [])) 
                              for r in all_results if r['result'].get('success'))
            emails_with_breaches = sum(1 for r in all_results 
                                     if r['result'].get('success') and 
                                     r['result'].get('data', {}).get('results'))
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("BREACH.VIP BATCH SEARCH RESULTS\n")
                f.write("=" * 60 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Emails Searched: {len(all_results)}\n")
                f.write("=" * 60 + "\n\n")
                
                for result in all_results:
                    email = result['email']
                    search_result = result['result']
                    timestamp = result['timestamp']
                    
                    f.write(f"EMAIL: {email}\n")
                    f.write(f"SEARCH TIME: {timestamp}\n")
                    f.write(f"STATUS: {'SUCCESS' if search_result.get('success') else 'FAILED'}\n")
                    
                    if search_result.get('success') and search_result.get('data'):
                        data = search_result['data']
                        if data.get('results') and len(data['results']) > 0:
                            records = data['results']
                            f.write(f"RECORDS FOUND: {len(records)}\n")
                            
                            # Group by breach source
                            breaches_by_source = {}
                            for record in records:
                                source = record.get('source', 'Unknown Source')
                                if source not in breaches_by_source:
                                    breaches_by_source[source] = []
                                breaches_by_source[source].append(record)
                                
                            f.write("BREACHES:\n")
                            for source, source_records in breaches_by_source.items():
                                f.write(f"  - {source}: {len(source_records)} record(s)\n")
                                
                            # Show sample data from first record of each source
                            f.write("SAMPLE DATA:\n")
                            for source, source_records in breaches_by_source.items():
                                f.write(f"  {source}:\n")
                                sample_record = source_records[0]
                                for key, value in sample_record.items():
                                    if key not in ['source', 'categories'] and value:
                                        f.write(f"    {key}: {value}\n")
                        else:
                            f.write("RECORDS FOUND: 0\n")
                            f.write("STATUS: No breach records found\n")
                    else:
                        f.write(f"ERROR: {search_result.get('error', 'Unknown error')}\n")
                        
                    f.write("-" * 40 + "\n\n")
                    
                # Add summary INSIDE the with block
                f.write("SUMMARY\n")
                f.write("=" * 60 + "\n")
                f.write(f"Successful searches: {successful_searches}/{len(all_results)}\n")
                f.write(f"Emails with breaches: {emails_with_breaches}\n")
                f.write(f"Total breach records found: {total_records}\n")
                f.write("=" * 60 + "\n")
                
        except Exception as e:
            if output_area:
                output_area.append(f"❌ Error saving batch results: {e}")

    def display_breach_results(self, data, email):
        """Display Breach.vip results in a formatted way and save to file"""
        output_area = self.get_output_area()
        if not output_area:
            return
            
        output_area.append(f"\n📊 BREACH.VIP RESULTS FOR: {email}")
        output_area.append("=" * 60)
        
        # Create results directory if it doesn't exist
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_email = re.sub(r'[^\w\-_.]', '_', email.split('@')[0])
        filename = f"breach_vip_{safe_email}_{timestamp}.txt"
        filepath = os.path.join(results_dir, filename)
        
        # Prepare content for both display and file
        display_lines = []
        file_lines = []
        
        try:
            # Check if we have results according to the API response format
            if 'results' in data and isinstance(data['results'], list):
                results = data['results']
                
                if len(results) > 0:
                    display_lines.append(f"🚨 Found {len(results)} breach record(s)")
                    file_lines.append(f"BREACH.VIP RESULTS FOR: {email}")
                    file_lines.append(f"Search Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    file_lines.append(f"Records Found: {len(results)}")
                    file_lines.append("=" * 60)
                    file_lines.append("")
                    
                    # Display each result
                    for i, result in enumerate(results, 1):
                        display_lines.append(f"📦 Record #{i}:")
                        file_lines.append(f"RECORD #{i}:")
                        
                        # Source (breach name)
                        source = result.get('source', 'Unknown Source')
                        display_lines.append(f"   📛 Breach: {source}")
                        file_lines.append(f"Breach: {source}")
                        
                        # Categories
                        categories = result.get('categories')
                        if categories:
                            if isinstance(categories, list):
                                display_lines.append(f"   🏷️  Categories: {', '.join(categories)}")
                                file_lines.append(f"Categories: {', '.join(categories)}")
                            else:
                                display_lines.append(f"   🏷️  Category: {categories}")
                                file_lines.append(f"Category: {categories}")
                                
                        # Show all other fields (excluding source and categories)
                        other_fields = {k: v for k, v in result.items() if k not in ['source', 'categories']}
                        for field_name, field_value in other_fields.items():
                            if field_value:  # Only show non-empty fields
                                # Truncate long values for display
                                display_value = str(field_value)
                                file_value = str(field_value)
                                
                                if len(display_value) > 100:
                                    display_value = display_value[:100] + "..."
                                    
                                display_lines.append(f"   🔍 {field_name}: {display_value}")
                                file_lines.append(f"{field_name}: {file_value}")
                                
                        display_lines.append("")  # Empty line between records
                        file_lines.append("")     # Empty line between records
                        
                    # Summary
                    unique_breaches = len(set(result.get('source', '') for result in results))
                    display_lines.append(f"📈 Summary: {len(results)} records across {unique_breaches} unique breaches")
                    file_lines.append(f"SUMMARY: {len(results)} records across {unique_breaches} unique breaches")
                    
                else:
                    display_lines.append("✅ No breach records found for this email")
                    display_lines.append("💡 This email appears clean in Breach.vip database")
                    
                    file_lines.append(f"BREACH.VIP RESULTS FOR: {email}")
                    file_lines.append(f"Search Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    file_lines.append("RESULTS: No breach records found")
                    file_lines.append("STATUS: Email appears clean in Breach.vip database")
            else:
                display_lines.append("❌ Unexpected response format from API")
                file_lines.append(f"BREACH.VIP RESULTS FOR: {email}")
                file_lines.append(f"Search Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                file_lines.append("ERROR: Unexpected response format from API")
                file_lines.append(f"RAW_RESPONSE: {json.dumps(data, indent=2)}")
                
        except Exception as e:
            error_msg = f"❌ Error processing results: {e}"
            display_lines.append(error_msg)
            file_lines.append(f"BREACH.VIP RESULTS FOR: {email}")
            file_lines.append(f"Search Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            file_lines.append(f"ERROR: {error_msg}")
            file_lines.append(f"RAW_RESPONSE: {json.dumps(data, indent=2)}")
            
        # Add footer
        display_lines.append("=" * 60)
        display_lines.append("💡 Note: Rate limit is 15 requests per minute")
        
        file_lines.append("=" * 60)
        file_lines.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        file_lines.append("Note: Breach.vip rate limit is 15 requests per minute")
        
        # Display results in GUI
        for line in display_lines:
            output_area.append(line)
            
        # Save to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(file_lines))
            output_area.append(f"💾 Results saved to: {filepath}")
        except Exception as e:
            output_area.append(f"❌ Error saving results to file: {e}")