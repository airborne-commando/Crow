# build_blackbird_command.py
import os

def build_blackbird_command(username_input, email_input, username_file_input, email_file_input, 
                            permute_checkbox, permuteall_checkbox, AI_checkbox, no_nsfw_checkbox, 
                            no_update_checkbox, csv_checkbox, pdf_checkbox, json_checkbox, verbose_checkbox, 
                            dump_checkbox, proxy_input, timeout_spinbox, filter_input, 
                            instagram_session_id):
    command = ["python", "blackbird.py"]

    # Function to handle appending parameters if text is present
    def add_params(param, text, cmd_list):
        if text:
            items = [item.strip() for item in text.split(',')]
            for item in items:
                cmd_list.extend([param, item])

    # Add parameters for username and email
    add_params("-u", username_input, command)
    add_params("-e", email_input, command)

    # Add file parameters if selected
    if username_file_input:
        command.extend(["--username-file", username_file_input])
    if email_file_input:
        command.extend(["--email-file", email_file_input])

    # Add permute options if selected and exactly one username is provided
    if username_input and len(username_input.split(',')) == 1:
        if permute_checkbox:
            command.append("--permute")
        elif permuteall_checkbox:
            command.append("--permuteall")

    # Add other options based on checkbox states
    checkboxes = {
        "--ai": AI_checkbox,
        "--no-nsfw": no_nsfw_checkbox,
        "--no-update": no_update_checkbox,
        "--csv": csv_checkbox,
        "--pdf": pdf_checkbox,
        "--json": json_checkbox,
        "--verbose": verbose_checkbox,
        "--dump": dump_checkbox
    }
    command.extend([param for param, checked in checkboxes.items() if checked])

    # Add proxy and timeout options
    if proxy_input:
        command.extend(["--proxy", proxy_input])

    command.extend(["--timeout", str(timeout_spinbox)])

    # Add filter option if text is present
    if filter_input:
        command.extend(["--filter", filter_input])

    # Set the Instagram session ID environment variable if entered
    if instagram_session_id:
        os.environ["INSTAGRAM_SESSION_ID"] = instagram_session_id

    return command