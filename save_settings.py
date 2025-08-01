# save_settings.py

import json
from PyQt6.QtWidgets import QFileDialog

def save_settings(gui_instance):
    # Open a file dialog to select where to save the JSON file
    file_name, _ = QFileDialog.getSaveFileName(gui_instance, "Save Settings", "", "JSON Files (*.json);;All Files (*)")
    if file_name:
        # Ensure the file name ends with .json if not already
        if not file_name.endswith('.json'):
            file_name += '.json'

        # Collect the current settings into a dictionary
        settings = {
            "hudson_email_input": gui_instance.hudson_email_input.text(),
            "username_input": gui_instance.username_input.text(),
            "email_input": gui_instance.email_input.text(),
            "permute_checkbox": gui_instance.permute_checkbox.isChecked(),
            "permuteall_checkbox": gui_instance.permuteall_checkbox.isChecked(),
            "no_nsfw_checkbox": gui_instance.no_nsfw_checkbox.isChecked(),
            "proxy_input": gui_instance.proxy_input.text(),
            "timeout_spinbox": gui_instance.timeout_spinbox.value(),
            "no_update_checkbox": gui_instance.no_update_checkbox.isChecked(),
            "csv_checkbox": gui_instance.csv_checkbox.isChecked(),
            "pdf_checkbox": gui_instance.pdf_checkbox.isChecked(),
            "verbose_checkbox": gui_instance.verbose_checkbox.isChecked(),
            "dump_checkbox": gui_instance.dump_checkbox.isChecked(),
            "instagram_session_id": gui_instance.instagram_session_id.text(),
#            "AI_checkbox": gui_instance.AI_checkbox.isChecked(),
            "filter": gui_instance.filter_input.text()
        }

        # Save the settings to the file with proper JSON format
        with open(file_name, 'w') as f:
            json.dump(settings, f, indent=4)
