import sys
import subprocess
import os
import json
import requests
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, 
                             QCheckBox, QGroupBox, QFormLayout, QSpinBox, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
    # Import the separate save and load functions
from pathlib import Path
from save_settings import save_settings
from load_settings import load_settings
from build_blackbird_command import build_blackbird_command
from tor_spoofing import TORSpoofer
from tor_api_setup import TORAPISetup
# Worker class that handles executing the Blackbird command in a separate thread
class BlackbirdWorker(QThread):
    output_signal = pyqtSignal(str)
    
    def __init__(self, command, needs_ai_confirmation=False, is_setup_ai=False, tor_spoofer=None):
        super().__init__()
        self.command = command
        self.process = None
        self.needs_ai_confirmation = needs_ai_confirmation
        self.is_setup_ai = is_setup_ai
        self.tor_spoofer = tor_spoofer
    
    def run(self):
        # If TOR is enabled for AI, set environment variable to signal the blackbird.py
        # to use TOR for AI requests
        if self.tor_spoofer and self.tor_spoofer.tor_enabled:
            # Set environment variable that blackbird.py can check
            import os
            os.environ["BLACKBIRD_USE_TOR"] = "1"
            os.environ["TOR_PORT"] = str(self.tor_spoofer.tor_port)
        self.process = subprocess.Popen(
            self.command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            stdin=subprocess.PIPE,
            text=True, 
            shell=True,
            bufsize=1
        )
        
        # For setup-ai, send confirmation immediately
        if self.is_setup_ai:
            try:
                # Wait a bit for the prompt to appear
                import time
                time.sleep(2)
                # Send 'Y' and newline
                self.process.stdin.write('Y\n')
                self.process.stdin.flush()
                self.output_signal.emit("✓ Sent confirmation for API key setup")
            except Exception as e:
                self.output_signal.emit(f"Setup confirmation error: {e}")
        
        # For regular AI analysis, wait for the specific prompt
        elif self.needs_ai_confirmation:
            confirmation_sent = False
            for line in self.process.stdout:
                text = line.strip()
                self.output_signal.emit(text)
                
                # Check for AI analysis prompt
                if not confirmation_sent and ('analyzing with ai' in text.lower() or 'consent' in text.lower()):
                    try:
                        self.process.stdin.write('Y\n')
                        self.process.stdin.flush()
                        confirmation_sent = True
                        self.output_signal.emit("✓ Automatically confirmed AI analysis")
                    except Exception as e:
                        self.output_signal.emit(f"AI confirmation error: {e}")
            return
        
        # Read output line by line for non-AI or after confirmation
        for line in self.process.stdout:
            self.output_signal.emit(line.strip())
        
        self.process.stdout.close()
        self.process.wait()

    def terminate(self):
        # Terminate the process if it's running
        if self.process:
            self.process.terminate()
            self.process.wait()

# Main GUI class for the Blackbird OSINT tool
class BlackbirdGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set window properties
        self.setWindowTitle("Crow")
        self.setGeometry(100, 100, 1000, 800)
        self.worker = None

        # Create the central widget and layout for the main window
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Input Group: For entering usernames, emails, and file selection
        input_group = QGroupBox("Blackbird Search")
        input_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        input_layout.addRow("Username(s):", self.username_input)
        
        self.email_input = QLineEdit()
        input_layout.addRow("Email(s):", self.email_input)
        
        # File inputs for usernames and emails
        self.username_file_input = QLineEdit()
        username_file_button = QPushButton("Select Username File")
        username_file_button.clicked.connect(self.select_username_file)
        username_file_layout = QHBoxLayout()
        username_file_layout.addWidget(self.username_file_input)
        username_file_layout.addWidget(username_file_button)
        input_layout.addRow("Username File:", username_file_layout)
        
        self.email_file_input = QLineEdit()
        email_file_button = QPushButton("Select Email File")
        email_file_button.clicked.connect(self.select_email_file)
        email_file_layout = QHBoxLayout()
        email_file_layout.addWidget(self.email_file_input)
        email_file_layout.addWidget(email_file_button)
        input_layout.addRow("Email File:", email_file_layout)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Options Group: Various checkboxes for additional configuration
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        AI_layout = QHBoxLayout()
        self.AI_checkbox = QCheckBox("Extract metadata AI")
        AI_layout.addWidget(self.AI_checkbox)

        # Add setup button for AI API key
        AI_setup_button = QPushButton("Setup API Key")
        AI_setup_button.clicked.connect(self.setup_ai_api_key)
        AI_layout.addWidget(AI_setup_button)

        AI_help_button = QPushButton("?")
        AI_help_button.setFixedSize(30, 30)
        AI_help_button.clicked.connect(self.show_AI_help)
        AI_layout.addWidget(AI_help_button)
        options_layout.addLayout(AI_layout)
        
        # TOR Spoofing setup - ADD THIS RIGHT AFTER AI LAYOUT
        self.tor_spoofer = TORSpoofer(self)
        self.setup_tor_ui(options_layout)  # Pass the options_layout to the method
        
        # Permute username checkbox with help button on the right
        permute_layout = QHBoxLayout()
        self.permute_checkbox = QCheckBox("Permute username")
        permute_layout.addWidget(self.permute_checkbox)
        permute_help_button = QPushButton("?")
        permute_help_button.setFixedSize(30, 30)
        permute_help_button.clicked.connect(self.show_permute_help)
        permute_layout.addWidget(permute_help_button)
        options_layout.addLayout(permute_layout)

        # Permute all elements checkbox with help button on the right
        permuteall_layout = QHBoxLayout()
        self.permuteall_checkbox = QCheckBox("Permute all")
        permuteall_layout.addWidget(self.permuteall_checkbox)
        permuteall_help_button = QPushButton("?")
        permuteall_help_button.setFixedSize(30, 30)
        permuteall_help_button.clicked.connect(self.show_permuteall_help)
        permuteall_layout.addWidget(permuteall_help_button)
        options_layout.addLayout(permuteall_layout)

        
        self.no_nsfw_checkbox = QCheckBox("Exclude NSFW sites")
        options_layout.addWidget(self.no_nsfw_checkbox)
        
        # Proxy input
        proxy_layout = QHBoxLayout()
        proxy_layout.addWidget(QLabel("Proxy:"))
        self.proxy_input = QLineEdit()
        proxy_layout.addWidget(self.proxy_input)
        options_layout.addLayout(proxy_layout)
        
        # Timeout input with spinner for seconds
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Timeout (seconds):"))
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(1, 300)  # Limit timeout to 1-300 seconds
        self.timeout_spinbox.setValue(30)  # Default timeout is 30 seconds
        timeout_layout.addWidget(self.timeout_spinbox)
        options_layout.addLayout(timeout_layout)
        
        # Checkbox to disable update checks
        self.no_update_checkbox = QCheckBox("Don't check for updates")
        options_layout.addWidget(self.no_update_checkbox)
        
        # Filter input field with a help button
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_input = QLineEdit()
        filter_layout.addWidget(self.filter_input)

        # Create a help button and connect it to the help function
        filter_help_button = QPushButton("?")
        filter_help_button.clicked.connect(self.show_filter_help)  # Connect the button to the help function
        filter_layout.addWidget(filter_help_button)

        options_layout.addLayout(filter_layout)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)


        # Output Options Group: Allows user to specify output types
        output_group = QGroupBox("Output Options")
        output_layout = QHBoxLayout()
        self.csv_checkbox = QCheckBox("CSV (Results)")
        self.pdf_checkbox = QCheckBox("PDF (Results)")
        self.json_checkbox = QCheckBox("JSON (Results)")
        self.verbose_checkbox = QCheckBox("Verbose (LOGS)")
        self.dump_checkbox = QCheckBox("Dump HTML (Results)")
        output_layout.addWidget(self.csv_checkbox)
        output_layout.addWidget(self.pdf_checkbox)
        output_layout.addWidget(self.json_checkbox)        
        output_layout.addWidget(self.verbose_checkbox)
        output_layout.addWidget(self.dump_checkbox)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Instagram session ID input for enhanced metadata extraction
        instagram_group = QGroupBox("Instagram Enhanced Metadata")
        instagram_layout = QHBoxLayout()
        self.instagram_session_id = QLineEdit()
        instagram_layout.addWidget(QLabel("Instagram Session ID:"))
        instagram_layout.addWidget(self.instagram_session_id)
        instagram_help_button = QPushButton("?")
        instagram_help_button.clicked.connect(self.show_instagram_help)  # Show help on click
        instagram_layout.addWidget(instagram_help_button)
        instagram_group.setLayout(instagram_layout)
        layout.addWidget(instagram_group)

        button_layout = QHBoxLayout()
        # Save and Load buttons connected to the functions
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)

        load_button = QPushButton("Load Settings")
        load_button.clicked.connect(self.load_settings)
        button_layout.addWidget(load_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Run and Stop buttons
        button_layout = QHBoxLayout()
        self.run_button = QPushButton("Run Blackbird")
        self.run_button.clicked.connect(self.run_blackbird)  # Start Blackbird on click
        button_layout.addWidget(self.run_button)
        
        self.stop_button = QPushButton("Stop Blackbird")
        self.stop_button.clicked.connect(self.stop_blackbird)  # Stop Blackbird on click
        self.stop_button.setEnabled(False)  # Disable initially
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)

        # Output area for displaying logs and results
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

        # Easter egg setup
        self.key_sequence = ""
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def setup_ai_api_key(self):
        """Configure AI API key through TOR for anonymous registration ONLY when TOR is enabled"""
        self.output_area.clear()
        self.output_area.append("🔧 Starting API Key setup...")
        
        # Check if TOR is explicitly enabled by the user
        tor_enabled = hasattr(self, 'tor_checkbox') and self.tor_checkbox.isChecked()
        
        if tor_enabled:
            self.output_area.append("🕶️  TOR enabled - setting up anonymous registration")
            self.output_area.append("This will register your TOR IP instead of your real IP")
            
            # Use existing TOR connection
            tor_port = self.tor_spoofer.tor_port
            control_port = self.tor_spoofer.control_port
            tor_password = self.tor_spoofer.tor_password
            
            # ONLY delete existing API key when TOR is explicitly enabled
            self.delete_existing_api_key()
            
            # Start TOR setup
            self.tor_setup_worker = TORAPISetup(tor_port, control_port, tor_password)
            self.tor_setup_worker.output_signal.connect(self.update_output)
            self.tor_setup_worker.finished_signal.connect(self.on_tor_setup_finished)
            self.tor_setup_worker.start()
            
        else:
            # TOR NOT enabled - use direct connection and PRESERVE existing API key
            self.output_area.append("🔗 Setting up direct connection (TOR not enabled)")
            self.output_area.append("Your real IP will be registered with Blackbird AI")
            self.setup_ai_api_key_direct()

            return  # Return early since direct setup handles its own flow
        
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def delete_existing_api_key(self):
        """Delete existing API key file ONLY when using TOR for fresh registration"""
        import os
        import json
        
        # Only proceed if TOR is explicitly enabled
        if not (hasattr(self, 'tor_checkbox') and self.tor_checkbox.isChecked()):
            return  # Don't delete anything if TOR is not enabled
        
        config_paths = [
            os.path.expanduser("~/.ai_key.json"),
            ".ai_key.json"
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    os.remove(config_path)
                    self.output_area.append(f"🗑️  Deleted existing API key for TOR registration: {config_path}")
                    break
                except Exception as e:
                    self.output_area.append(f"⚠️  Could not delete {config_path}: {e}")

    def setup_ai_api_key_direct(self):
        """Fallback direct setup without TOR"""
        self.output_area.append("🔄 Starting direct API setup (without TOR)...")
        
        # Build the setup command
        command = ["python", "blackbird.py", "--setup-ai"]
        
        # Create and start the worker for setup
        self.worker = BlackbirdWorker(" ".join(command), is_setup_ai=True)
        self.worker.output_signal.connect(self.update_output)
        self.worker.finished.connect(lambda: self.on_tor_setup_finished(True))
        self.worker.start()
        
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def on_tor_setup_finished(self, success):
        """Handle completion of TOR API setup"""
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        if success:
            self.output_area.append("✅ API setup completed successfully!")
            self.check_api_key_config()
        else:
            self.output_area.append("❌ API setup failed")
            
            reply = QMessageBox.question(
                self,
                "Setup Failed",
                "API setup failed.\n\n"
                "Do you want to try again?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.setup_ai_api_key()

    def check_api_key_config(self):
        """Check if API key was successfully configured"""
        import os
        import json
        
        api_key_found = False
        config_paths = [
            os.path.expanduser("~/.ai_key.json"),
            ".ai_key.json"
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        if config.get("ai_api_key"):
                            api_key_found = True
                            self.ai_api_key = config["ai_api_key"]
                            os.environ["BLACKBIRD_AI_API_KEY"] = config["ai_api_key"]
                            self.output_area.append("✅ AI API Key configured and loaded!")
                            break
                        elif config.get("api_key"):
                            api_key_found = True
                            self.ai_api_key = config["api_key"]
                            os.environ["BLACKBIRD_AI_API_KEY"] = config["api_key"]
                            self.output_area.append("✅ AI API Key configured and loaded!")
                            break
                except (json.JSONDecodeError, KeyError):
                    continue
        
        if not api_key_found:
            self.output_area.append("⚠️  API key setup completed, but couldn't automatically detect the key.")
            self.output_area.append("You may need to manually check the configuration.")

        def on_setup_finished(self):
            """Handle completion of AI setup"""
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            # Check if setup was successful by looking for the API key
            import os
            import json
            import os.path
            
            api_key_found = False
            config_paths = [
                os.path.expanduser("~/.ai_key.json"),
                ".ai_key.json"
            ]
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                            if config.get("ai_api_key"):
                                api_key_found = True
                                self.ai_api_key = config["ai_api_key"]
                                os.environ["BLACKBIRD_AI_API_KEY"] = config["ai_api_key"]
                                self.output_area.append("✅ AI API Key setup completed and loaded!")
                                break
                            elif config.get("api_key"):
                                api_key_found = True
                                self.ai_api_key = config["api_key"]
                                os.environ["BLACKBIRD_AI_API_KEY"] = config["api_key"]
                                self.output_area.append("✅ AI API Key setup completed and loaded!")
                                break
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            if not api_key_found:
                self.output_area.append("⚠️  API key setup completed, but couldn't automatically detect the key.")
                self.output_area.append("You may need to manually enter the API key using the 'Setup API Key' button.")

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.key_sequence += event.text()
        
        if 'iddqd' in self.key_sequence.lower():
            self.trigger_easter_egg()
            self.key_sequence = ''
        
        if len(self.key_sequence) > 10:
            self.key_sequence = self.key_sequence[-10:]

    def trigger_easter_egg(self):
        easter_egg = """
Crows mimic, crows are intelligent!
        """
        self.output_area.append("Easter egg activated!")
        self.output_area.append(easter_egg)

    def select_username_file(self):
        # Open a file dialog to select a username file and set its path in the input field
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Username File")
        if file_name:
            self.username_file_input.setText(file_name)

    def select_email_file(self):
        # Open a file dialog to select an email file and set its path in the input field
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Email File")
        if file_name:
            self.email_file_input.setText(file_name)

    def search_hudson_rock(self):
        self.output_area.clear()
        query = self.hudson_email_input.text().strip()

        # We assume the query could be either an email or username, so we check it
        if "@" in query:
            query_type = "email"
        else:
            self.update_output("Invalid email address. Please enter a valid email.\n")
            return

        base_url = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/"
        endpoint = f"search-by-email?email={query}"

        url = base_url + endpoint

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            self.update_output(json.dumps(data, indent=2))
        except requests.exceptions.RequestException as e:
            self.update_output(f"An error occurred: {e}")

    def save_settings(self):
        # Use the modular save_settings function
        save_settings(self)

    def load_settings(self):
        # Use the modular load_settings function
        load_settings(self)

    def show_instagram_help(self):
        QMessageBox.information(self, "Instagram Session ID Help",
                                "To use enhanced Instagram metadata extraction:\n\n"
                                "1. Log in to Instagram in your browser\n"
                                "2. Open developer tools (F12)\n"
                                "3. Go to Application > Cookies\n"
                                "4. Find the 'sessionid' cookie\n"
                                "5. Copy its value and paste it here")

    def show_filter_help(self):
        QMessageBox.information(self, "Filter Help",
                                "Create custom search filters using specific properties and operators.\n\n"
                                "Properties: name, cat, uri_check, e_code, e_string, m_string, m_code\n"
                                "Operators: =, ~, >, <, >=, <=, !=\n\n"
                                "Examples:\n"
                                "1. name~Mastodon\n"
                                "2. e_code>200\n"
                                "3. cat=social and uri_check~101010\n"
                                "4. e_string=@101010.pl or m_code<=404\n\n"
                                "Concatenate commands with \"\" for multiple filters.\n\n"
                                "Visit https://p1ngul1n0.gitbook.io/blackbird/advanced-usage")

    def show_permute_help(self):
        QMessageBox.information(self, "Permute Username Help",
                                "The '--permute' option generates variations of a username.\n\n"
                                "For 'balestek86', permutations include:\n"
                                "balestek86, _balestek86, balestek86_, balestek_86, balestek-86, balestek.86\n"
                                "86balestek, _86balestek, 86balestek_, 86_balestek, 86-balestek, 86.balestek")

    def show_permuteall_help(self):
        QMessageBox.information(self, "Permute All Elements Help",
                                "The '--permuteall' option generates a broader set of permutations.\n\n"
                                "For 'balestek86', permutations include:\n"
                                "balestek, _balestek, balestek_, 86, _86, 86_,\n"
                                "balestek86, _balestek86, balestek86_, balestek_86, balestek-86, balestek.86,\n"
                                "86balestek, _86balestek, 86balestek_, 86_balestek, 86-balestek, 86.balestek")

    def show_AI_help(self):
        QMessageBox.information(self, "AI Metadata Help",
                               "The '--ai' option performs AI analysis on found results.\n\n"
                               "Features:\n"
                               "• Generates comprehensive profile summaries\n"
                               "• Identifies profile types and interests\n"
                               "• Provides risk assessment flags\n"
                               "• Adds relevant tags for categorization\n"
                               "• Shows remaining daily AI query quota\n\n"
                               "Results are marked with a robot emoji (🤖) and include:\n"
                               "- Summary of online presence\n"
                               "- Profile type classification\n" 
                               "- Key insights and interests\n"
                               "- Risk flags and warnings\n"
                               "- Relevant tags\n\n"
                               "Note: Uses Blackbird AI API with daily query limits.")
    
    def setup_tor_ui(self, options_layout):
        """Add TOR configuration to the options group"""
        # Add TOR section to options group
        tor_group = QGroupBox("TOR IP Spoofing (for AI)")
        tor_layout = QHBoxLayout()
        
        self.tor_checkbox = QCheckBox("Enable TOR for AI requests")
        self.tor_checkbox.stateChanged.connect(self.toggle_tor_spoofing)
        tor_layout.addWidget(self.tor_checkbox)
        
        tor_setup_button = QPushButton("TOR Settings")
        tor_setup_button.clicked.connect(self.configure_tor_settings)
        tor_layout.addWidget(tor_setup_button)
        
        tor_help_button = QPushButton("?")
        tor_help_button.setFixedSize(30, 30)
        tor_help_button.clicked.connect(self.show_tor_help)
        tor_layout.addWidget(tor_help_button)
        
        tor_group.setLayout(tor_layout)
        
        # Insert TOR group after AI options but before permute options
        # We need to find the correct position in the layout
        # Since we're calling this during setup, we can add it directly
        options_layout.addWidget(tor_group)
    
    def toggle_tor_spoofing(self, state):
        """Enable/disable TOR spoofing"""
        if state == Qt.CheckState.Checked.value:
            # Try to enable TOR with default settings
            if not self.tor_spoofer.enable_tor_for_ai():
                QMessageBox.warning(self, "TOR Not Available", 
                                  "TOR connection failed. Please ensure TOR is running and configured.")
                self.tor_checkbox.setChecked(False)
        else:
            self.tor_spoofer.disable_tor()
    
    def configure_tor_settings(self):
        """Open dialog to configure TOR settings"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("TOR Configuration")
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        tor_port_input = QLineEdit(str(self.tor_spoofer.tor_port))
        control_port_input = QLineEdit(str(self.tor_spoofer.control_port))
        
        # Show current password (masked) but don't allow changing in this version
        password_info = QLabel(f"Current password: {'*' * 20} (hardcoded for testing)")
        password_info.setWordWrap(True)
        
        form_layout.addRow("TOR Port:", tor_port_input)
        form_layout.addRow("Control Port:", control_port_input)
        form_layout.addRow("Password:", password_info)
        
        help_label = QLabel("Note: Using hardcoded password for testing. Port changes will be applied.")
        help_label.setWordWrap(True)
        form_layout.addRow("", help_label)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                 QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.tor_spoofer.tor_port = int(tor_port_input.text())
                self.tor_spoofer.control_port = int(control_port_input.text())
                
                # Test new configuration
                if self.tor_checkbox.isChecked():
                    if not self.tor_spoofer.enable_tor_for_ai():
                        QMessageBox.warning(self, "TOR Configuration Failed", 
                                          "New TOR settings are invalid.")
                        self.tor_checkbox.setChecked(False)
                    else:
                        QMessageBox.information(self, "Success", "TOR configuration updated successfully!")
                            
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Port numbers must be integers.")
    
    def show_tor_help(self):
        """Show TOR help information"""
        QMessageBox.information(self, "TOR IP Spoofing Help",
                              "TOR IP Spoofing for AI Requests:\n\n"
                              "• Routes AI API calls through TOR network\n"
                              "• Automatically renews IP for each request\n"
                              "• Enhances privacy and anonymity\n"
                              "• Bypasses IP-based rate limits\n\n"
                              "Requirements:\n"
                              "• TOR service must be running locally\n"
                              "• Default ports: 9050 (TOR), 9051 (control)\n"
                              "• TOR control protocol enabled\n\n"
                              "Note: This only affects AI metadata extraction requests.")


    def run_blackbird(self):
        # Check if AI is enabled but no API key is set
        if self.AI_checkbox.isChecked():
            # If TOR is also enabled, set it up
            if hasattr(self, 'tor_checkbox') and self.tor_checkbox.isChecked():
                if not self.tor_spoofer.tor_enabled:
                    if not self.tor_spoofer.enable_tor_for_ai():
                        self.output_area.append("⚠️  TOR spoofing failed, continuing with direct connection")
            
            import os
            import json
            import os.path
            
            # Check multiple locations for API key
            api_key_found = False
            
            # 1. Check environment variable
            if os.environ.get("BLACKBIRD_AI_API_KEY"):
                api_key_found = True
            
            # 2. Check Blackbird config file
            if not api_key_found:
                config_paths = [
                    os.path.expanduser(".ai_key.json"),
                    ".ai_key.json",  # Current directory
                ]
                
                for config_path in config_paths:
                    if os.path.exists(config_path):
                        try:
                            with open(config_path, 'r') as f:
                                config = json.load(f)
                                if config.get("ai_api_key") or config.get("api_key"):
                                    api_key_found = True
                                    break
                        except (json.JSONDecodeError, KeyError):
                            continue
            
            # 3. Check if we have a stored API key in the GUI instance
            if not api_key_found and hasattr(self, 'ai_api_key') and self.ai_api_key:
                api_key_found = True
            
            if not api_key_found:
                reply = QMessageBox.question(
                    self, 
                    "AI API Key Required",
                    "AI analysis requires an API key. Would you like to configure it now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.setup_ai_api_key()
                    return  # Don't proceed with regular search until setup is complete
                else:
                    QMessageBox.warning(self, "Warning", "AI analysis disabled - no API key configured.")
                    self.AI_checkbox.setChecked(False)
        
        # Rest of the existing run_blackbird method...
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        # Get all input values
        username_input = self.username_input.text()
        email_input = self.email_input.text()
        username_file_input = self.username_file_input.text()
        email_file_input = self.email_file_input.text()
        permute_checkbox = self.permute_checkbox.isChecked()
        permuteall_checkbox = self.permuteall_checkbox.isChecked()
        AI_checkbox = self.AI_checkbox.isChecked()
        no_nsfw_checkbox = self.no_nsfw_checkbox.isChecked()
        no_update_checkbox = self.no_update_checkbox.isChecked()
        csv_checkbox = self.csv_checkbox.isChecked()
        pdf_checkbox = self.pdf_checkbox.isChecked()
        json_checkbox = self.json_checkbox.isChecked()
        verbose_checkbox = self.verbose_checkbox.isChecked()
        dump_checkbox = self.dump_checkbox.isChecked()
        proxy_input = self.proxy_input.text()
        timeout_spinbox = self.timeout_spinbox.value()
        filter_input = self.filter_input.text()
        instagram_session_id = self.instagram_session_id.text()

        # Show AI info if enabled
        if AI_checkbox:
            self.output_area.append("🤖 AI Analysis Enabled")
            self.output_area.append("Note: This will analyze results using Blackbird AI")
            self.output_area.append("")

        command = build_blackbird_command(username_input, email_input, username_file_input, 
                                          email_file_input, permute_checkbox, permuteall_checkbox, 
                                          AI_checkbox, no_nsfw_checkbox, no_update_checkbox, 
                                          csv_checkbox, pdf_checkbox, json_checkbox, verbose_checkbox, 
                                          dump_checkbox, proxy_input, timeout_spinbox, 
                                          filter_input, instagram_session_id)

        self.output_area.clear()
        # Pass AI_checkbox to determine if we need to auto-confirm
        self.worker = BlackbirdWorker(" ".join(command), needs_ai_confirmation=AI_checkbox)
        self.worker.output_signal.connect(self.update_output)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
    
    def stop_blackbird(self):
        # Stop the Blackbird process if running
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        self.run_button.setEnabled(True)  # Re-enable Run button
        self.stop_button.setEnabled(False)  # Disable Stop button

    def update_output(self, text):
        # Initialize AI results buffer if it doesn't exist
        if not hasattr(self, 'ai_results_buffer'):
            self.ai_results_buffer = []
            self.ai_results_started = False
        
        # Check if AI analysis is starting
        if 'analyzing with ai' in text.lower() or '✨ analyzing with ai' in text.lower():
            self.ai_results_started = True
            self.ai_results_buffer = [
                "🤖 BLACKBIRD AI ANALYSIS REPORT",
                "=" * 60,
                f"Generated: {self.get_current_timestamp()}",
                "=" * 60,
                ""
            ]
            
            # Add search context
            username = self.username_input.text().strip()
            email = self.email_input.text().strip()
            if username:
                self.ai_results_buffer.append(f"Target Username: {username}")
            if email:
                self.ai_results_buffer.append(f"Target Email: {email}")
            if username or email:
                self.ai_results_buffer.append("")
        
        # Buffer AI results
        if self.ai_results_started:
            # Clean and format the text for file output
            clean_text = text.replace('🤖', '').replace('📊', '').strip()
            self.ai_results_buffer.append(clean_text)
            
            # Check if AI analysis is complete
            if 'ai queries left' in text.lower():
                self.ai_results_buffer.extend([
                    "",
                    "=" * 60,
                    f"Analysis complete - {self.get_current_timestamp()}",
                    "=" * 60
                ])
                self.auto_save_ai_results()  # Auto-save instead of dialog
                self.ai_results_started = False
        
        # Format for GUI display
        formatted_text = self.format_ai_text_for_gui(text)
        
        # Update GUI
        self.append_to_output_area(formatted_text)

    def format_ai_text_for_gui(self, text):
        """Format AI text for GUI display with emojis"""
        if any(keyword in text.lower() for keyword in ['analyzing with ai', 'ai queries left', '✨']):
            return f"🤖 {text}"
        elif text.startswith('[Summary]'):
            return f"📋 {text}"
        elif text.startswith('[Profile Type]'):
            return f"🎯 {text}"
        elif text.startswith('[Insights]'):
            return f"💡 {text}"
        elif text.startswith('[Risk Flags]'):
            return f"⚠️  {text}"
        elif text.startswith('[Tags]'):
            return f"🏷️  {text}"
        else:
            return text

    def get_current_timestamp(self):
        """Get current timestamp for file naming and reports"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def auto_save_ai_results(self):
        """Automatically save AI results to file"""
        if not self.ai_results_buffer:
            return
        
        try:
            # Generate filename with timestamp and target info
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            username = self.username_input.text().strip()
            email = self.email_input.text().strip()
            
            # Create descriptive filename
            if username:
                base_name = username
            elif email:
                base_name = email.split('@')[0]
            else:
                base_name = "analysis"

            # Clean filename
            safe_name = re.sub(r'[^\w\-_.]', '_', base_name)
            filename = f"blackbird_ai_{safe_name}_{timestamp}.txt"

            # Directory path where you want to save the file (e.g., "output_files")
            directory_path = "results"

            # Create directory if it doesn't exist
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            # Full file path with directory
            full_path = os.path.join(directory_path, filename)

            # Save to file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.ai_results_buffer))
            
            # Notify user
            self.append_to_output_area(f"💾 AI results auto-saved to: {filename}")
            
        except Exception as e:
            self.append_to_output_area(f"❌ Error auto-saving AI results: {e}")

    def append_to_output_area(self, text):
        """Helper method to append text to output area with auto-scroll"""
        scrollbar = self.output_area.verticalScrollBar()
        was_at_bottom = scrollbar.value() == scrollbar.maximum()
        
        self.output_area.append(text)
        
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def on_worker_finished(self):
        # Re-enable the Run button and disable the Stop button when worker finishes
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

if __name__ == "__main__":
    # Create and run the application
    app = QApplication(sys.argv)
    window = BlackbirdGUI()
    window.show()
    sys.exit(app.exec())