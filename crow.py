import sys
import subprocess
import os
import json
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, 
                             QCheckBox, QGroupBox, QFormLayout, QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Worker class that handles executing the Blackbird command in a separate thread
class BlackbirdWorker(QThread):
    # Signal to send output to the main thread
    output_signal = pyqtSignal(str)

    def __init__(self, command):
        # Initialize with the command to run
        super().__init__()
        self.command = command
        self.process = None

    def run(self):
        # Run the command using subprocess and capture output
        self.process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
        for line in self.process.stdout:
            # Emit output line by line to update the UI
            self.output_signal.emit(line.strip())
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

        # Adding Hudson Rock section for email/username search
        hudson_group = QGroupBox("Hudson Rock Search")
        hudson_layout = QVBoxLayout()
        
        self.hudson_email_input = QLineEdit()
        hudson_layout.addWidget(QLabel("Email to Search:"))
        hudson_layout.addWidget(self.hudson_email_input)

        self.hudson_search_button = QPushButton("Search Hudson Rock")
        self.hudson_search_button.clicked.connect(self.search_hudson_rock)
        hudson_layout.addWidget(self.hudson_search_button)

        hudson_group.setLayout(hudson_layout)
        layout.addWidget(hudson_group)

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
        AI_help_button = QPushButton("?")
        AI_help_button.setFixedSize(30, 30)
        AI_help_button.clicked.connect(self.show_AI_help)
        AI_layout.addWidget(AI_help_button)
        options_layout.addLayout(AI_layout)
        
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
        self.verbose_checkbox = QCheckBox("Verbose (LOGS)")
        self.dump_checkbox = QCheckBox("Dump HTML (Results)")
        output_layout.addWidget(self.csv_checkbox)
        output_layout.addWidget(self.pdf_checkbox)
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

        # Now you can initialize the button_layout here
        button_layout = QHBoxLayout()  # Initialize button_layout first
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

        if not query:
            self.update_output("Please enter an email to search.\n")
            return

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
        # Open a file dialog to select where to save the JSON file
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Settings", "", "JSON Files (*.json);;All Files (*)")
        if file_name:
            # Ensure the file name ends with .json if not already
            if not file_name.endswith('.json'):
                file_name += '.json'

            # Collect the current settings into a dictionary
            settings = {
                "hudson_email_input": self.hudson_email_input.text(),
                "username_input": self.username_input.text(),
                "email_input": self.email_input.text(),
                "permute_checkbox": self.permute_checkbox.isChecked(),
                "permuteall_checkbox": self.permuteall_checkbox.isChecked(),
                "no_nsfw_checkbox": self.no_nsfw_checkbox.isChecked(),
                "proxy_input": self.proxy_input.text(),
                "timeout_spinbox": self.timeout_spinbox.value(),
                "no_update_checkbox": self.no_update_checkbox.isChecked(),
                "csv_checkbox": self.csv_checkbox.isChecked(),
                "pdf_checkbox": self.pdf_checkbox.isChecked(),
                "verbose_checkbox": self.verbose_checkbox.isChecked(),
                "dump_checkbox": self.dump_checkbox.isChecked(),
                "instagram_session_id": self.instagram_session_id.text(),
                "AI_checkbox": self.AI_checkbox.isChecked()
            }

            # Save the settings to the file with proper JSON format
            with open(file_name, 'w') as f:
                json.dump(settings, f, indent=4)

    def load_settings(self):
        # Open a file dialog to select a JSON file to load
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Settings", "", "JSON Files (*.json);;All Files (*)")
        if file_name:
            # Load the settings from the JSON file
            with open(file_name, 'r') as f:
                settings = json.load(f)

            # Define a mapping of setting keys to widget methods and types
            setting_mappings = {
                "hudson_email_input": (self.hudson_email_input.setText, str),
                "username_input": (self.username_input.setText, str),
                "email_input": (self.email_input.setText, str),
                "permute_checkbox": (self.permute_checkbox.setChecked, bool),
                "permuteall_checkbox": (self.permuteall_checkbox.setChecked, bool),
                "no_nsfw_checkbox": (self.no_nsfw_checkbox.setChecked, bool),
                "proxy_input": (self.proxy_input.setText, str),
                "timeout_spinbox": (self.timeout_spinbox.setValue, int),
                "no_update_checkbox": (self.no_update_checkbox.setChecked, bool),
                "csv_checkbox": (self.csv_checkbox.setChecked, bool),
                "pdf_checkbox": (self.pdf_checkbox.setChecked, bool),
                "verbose_checkbox": (self.verbose_checkbox.setChecked, bool),
                "dump_checkbox": (self.dump_checkbox.setChecked, bool),
                "instagram_session_id": (self.instagram_session_id.setText, str),
                "AI_checkbox": (self.AI_checkbox.setChecked, bool)
            }

            # Apply the loaded settings
            for key, (set_method, value_type) in setting_mappings.items():
                if key in settings:
                    set_method(value_type(settings[key]))

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
                                "Concatenate commands with \"\" for multiple filters.")

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
                                "The '--ai' option extracts metadata using AI.\n\n"
                                "For 'balestek86', results will be marked with a robot emoji (🤖).\n"
                                "Note: AI results may be inaccurate, so use your own judgment.")


    def run_blackbird(self):
        # Ensure any previous worker is stopped before starting a new one
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        # Initialize the Blackbird command with the basic parameters
        command = ["python", "blackbird.py"]

        # Function to handle appending parameters if text is present
        def add_params(param, text, cmd_list):
            if text:
                items = [item.strip() for item in text.split(',')]
                for item in items:
                    cmd_list.extend([param, item])

        # Add parameters for username and email
        add_params("-u", self.username_input.text(), command)
        add_params("-e", self.email_input.text(), command)

        # Add file parameters if selected
        file_params = {
            "--username-file": self.username_file_input.text(),
            "--email-file": self.email_file_input.text()
        }
        command.extend([param for param, value in file_params.items() if value])

        # Add permute options if selected and exactly one username is provided
        if self.username_input.text() and len(self.username_input.text().split(',')) == 1:
            if self.permute_checkbox.isChecked():
                command.append("--permute")
            elif self.permuteall_checkbox.isChecked():
                command.append("--permuteall")

        # Add other options based on checkbox states
        checkboxes = {
            "--ai": self.AI_checkbox.isChecked(),
            "--no-nsfw": self.no_nsfw_checkbox.isChecked(),
            "--no-update": self.no_update_checkbox.isChecked(),
            "--csv": self.csv_checkbox.isChecked(),
            "--pdf": self.pdf_checkbox.isChecked(),
            "--verbose": self.verbose_checkbox.isChecked(),
            "--dump": self.dump_checkbox.isChecked()
        }
        command.extend([param for param, checked in checkboxes.items() if checked])

        # Add proxy and timeout options
        if self.proxy_input.text():
            command.extend(["--proxy", self.proxy_input.text()])
        
        command.extend(["--timeout", str(self.timeout_spinbox.value())])

        # Add filter option if text is present
        if self.filter_input.text():
            command.extend(["--filter", self.filter_input.text()])

        # Set the Instagram session ID environment variable if entered
        if self.instagram_session_id.text():
            os.environ["INSTAGRAM_SESSION_ID"] = self.instagram_session_id.text()

        # Clear previous output and start the worker thread
        self.output_area.clear()
        self.worker = BlackbirdWorker(" ".join(command))
        self.worker.output_signal.connect(self.update_output)  # Connect output signal to update method
        self.worker.finished.connect(self.on_worker_finished)  # Handle when worker finishes
        self.worker.start()
        
        # Disable Run button and enable Stop button during execution
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
        # Update the output area with new text (logs/results)
        scrollbar = self.output_area.verticalScrollBar()
        was_at_bottom = scrollbar.value() == scrollbar.maximum()

        self.output_area.append(text)

        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())  # Auto-scroll to the bottom

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
