# Crow - Blackbird GUI Frontend

A PyQt6-based graphical user interface for the Blackbird OSINT tool, providing an intuitive way to conduct username and email investigations across multiple platforms.

## Features

- **User-Friendly Interface**: Easy-to-use GUI for Blackbird OSINT operations
- **Multiple Input Methods**: Support for direct username/email input and file-based inputs
- **Advanced Search Options**: Permutation, filtering, and AI-powered analysis
- **Flexible Output Formats**: CSV, PDF, JSON, verbose logs, and HTML dumps
- **Session Management**: Save and load search configurations
- **Real-time Output**: Live monitoring of search progress and results
- **Instagram Integration**: Enhanced metadata extraction with session ID
- **AI Analysis**: Automated profile analysis and risk assessment

## Installation

### Prerequisites

1. Python 3 or higher
2. Blackbird OSINT tool (must be in the same directory)
3. Required Python packages:

```
pip install -r requirements_GUI.txt
```

## Python

### Arch users

### Python 311

```
yay -S python311
```

### Python 312

```
yay -S python312
```

### Installs:

In one command:

    git clone https://github.com/p1ngul1n0/blackbird.git && git clone https://github.com/airborne-commando/crow.git && mv crow/*.txt ./blackbird/ && mv crow/*.py ./blackbird/ && cd ./blackbird/ && python3 -m venv venv && source venv/bin/activate && pip3 install -r requirements.txt && pip3 install -r requirements_GUI.txt


### python311

    git clone https://github.com/p1ngul1n0/blackbird.git && git clone https://github.com/airborne-commando/crow.git && mv crow/*.txt ./blackbird/ && mv crow/*.py ./blackbird/ && cd ./blackbird/ && python3.11 -m venv venv && source venv/bin/activate && pip3 install -r requirements.txt && pip3 install -r requirements_GUI.txt

### python312

    git clone https://github.com/p1ngul1n0/blackbird.git && git clone https://github.com/airborne-commando/crow.git && mv crow/*.txt ./blackbird/ && mv crow/*.py ./blackbird/ && cd ./blackbird/ && python3.12 -m venv venv && source venv/bin/activate && pip3 install -r requirements.txt && pip3 install -r requirements_GUI.txt


### For the dev-tor:

      git clone https://github.com/p1ngul1n0/blackbird.git && git clone --branch dev-tor --single-branch https://github.com/airborne-commando/crow.git && mv crow/*.txt ./blackbird/ && mv crow/*.py ./blackbird/ && cd ./blackbird/ && python3 -m venv venv && source venv/bin/activate && pip3 install -r requirements.txt && pip3 install -r requirements_GUI.txt

### File Structure

Ensure the following files are in your working directory:

```
project/
├── crow.py                 # Main GUI application
├── build_blackbird_command.py  # Command builder utility
├── save_settings.py        # Settings save functionality
├── load_settings.py        # Settings load functionality
├── requirements_GUI.txt # GUI requirements
├── tor_api_setup.py # Tor functions
├── tor_hook.py
├── tor_spoofing.py
└── blackbird.py           # Blackbird OSINT tool (required)
```

### Tor Usage:

Can Bypass daily limits on AI summary, but the password is hard coded, you'll need to edit this value inside tor_spoofing.py:

      class TORSpoofer:
          def __init__(self, gui_instance=None):
              self.gui_instance = gui_instance
              self.tor_enabled = False
              self.tor_session = None
              self.tor_port = 9050  # Default TOR port
              self.control_port = 9051  # Default control port
              self.tor_password = "hashbrownyummy"  # ← SET YOUR PASSWORD HERE

you'll need to also install tor inside your system and do the following.

### Password gen example

      tor --hash-password hashbrownyummy

New value of hashbrownyummy

      16:173F2CE915F54E88606A84E39D3750633B34E57F384910306004433BE9

Then edit, uncomment HashedControlPassword and ControlPort:

**sudo nano /etc/tor/torrc**

      #ControlPort 9051
      ## If you enable the controlport, be sure to enable one of these
      ## authentication methods, to prevent attackers from accessing it.
      #HashedControlPassword 16:173F2CE915F54E88606A84E39D3750633B34E57F384910306004433BE9
      #CookieAuthentication 1

Restart the tor service with **sudo systemctl restart tor**

Be sure to enable and start

## Usage

### Basic Operation

1. **Launch the Application**:
   ```
   python crow.py
   ```

2. **Input Targets**:
   - Enter usernames in the "Username(s)" field (comma-separated for multiple)
   - Enter emails in the "Email(s)" field (comma-separated for multiple)
   - Or select files containing lists of usernames/emails

3. **Configure Options**:
   - **Permutation**: Generate username variations (requires single username)
   - **AI Analysis**: Enable AI-powered metadata extraction (requires API key setup)
   - **Output Formats**: Select desired output formats (CSV, PDF, JSON, etc.)
   - **Filters**: Apply custom search filters
   - **Proxy**: Configure proxy settings for requests
   - **Timeout**: Set request timeout in seconds

4. **Execute Search**:
   - Click "Run Blackbird" to start the investigation
   - Monitor real-time progress in the output area
   - Use "Stop Blackbird" to cancel ongoing searches

### Advanced Features

#### AI Analysis Setup

1. Click "Setup API Key" to configure AI analysis
2. Follow the automated setup process
3. API key is automatically saved and loaded for future sessions

#### Instagram Enhanced Metadata

1. Obtain Instagram Session ID:
   - Log into Instagram in your browser
   - Open Developer Tools (F12)
   - Go to Application > Cookies
   - Copy the "sessionid" cookie value
2. Paste the Session ID in the dedicated field
3. Enhanced metadata will be extracted during searches

#### Custom Filters

Create advanced search filters using properties and operators:

**Properties**: `name`, `cat`, `uri_check`, `e_code`, `e_string`, `m_string`, `m_code`

**Operators**: `=`, `~`, `>`, `<`, `>=`, `<=`, `!=`

**Examples**:
- `name~Mastodon` - Sites containing "Mastodon" in name
- `e_code>200` - Sites with error codes greater than 200
- `cat=social and uri_check~101010` - Social sites with specific URI patterns

#### Permutation Options

- **Permute Username**: Generates common variations of a single username
- **Permute All**: Creates broader permutations including sub-components

## Configuration

### Settings Management

- **Save Settings**: Store current configuration to JSON file
- **Load Settings**: Restore previous configuration from JSON file

Saved settings include:
- Input fields (usernames, emails, filters)
- Checkbox states (options, output formats)
- API keys and session IDs
- Proxy and timeout configurations

### Environment Variables

The application automatically manages:
- `INSTAGRAM_SESSION_ID`: For enhanced Instagram metadata
- `BLACKBIRD_AI_API_KEY`: For AI analysis functionality

## Output Handling

### Real-time Monitoring

- Live output display with formatted AI results
- Automatic scrolling to latest content
- Color-coded and emoji-enhanced status messages

### Auto-save Features

- AI analysis results automatically saved to timestamped files
- Files named: `blackbird_ai_{target}_{timestamp}.txt`
- Includes comprehensive analysis reports with timestamps

### File Outputs

Based on selected options, generates:
- **CSV**: Structured results data
- **PDF**: Formatted reports
- **JSON**: Machine-readable results
- **HTML Dumps**: Raw page content
- **Verbose Logs**: Detailed process information

## Troubleshooting

### Common Issues

1. **Blackbird Not Found**: Ensure `blackbird.py` is in the same directory
2. **AI Analysis Fails**: Verify API key setup and internet connectivity
3. **Instagram Metadata Issues**: Check session ID validity and login status
4. **Permission Errors**: Ensure write permissions for output files

### Help System

Comprehensive help buttons (`?`) provide detailed information about:
- AI analysis capabilities and limitations
- Permutation examples and patterns
- Filter syntax and examples
- Instagram session ID acquisition

## Dependencies

- PyQt6 >= 6.0.0
- requests >= 2.25.0
- Blackbird OSINT tool

## License

This project is designed as a frontend for the [Blackbird OSINT tool](https://github.com/p1ngul1n0/blackbird/tree/main). Please ensure compliance with Blackbird's license terms and applicable laws when conducting investigations.

## Contributing

This is a GUI wrapper for the Blackbird tool. For issues related to the core OSINT functionality, refer to the main [Blackbird repository](https://github.com/p1ngul1n0/blackbird/tree/main).

---

**Note**: Always use OSINT tools responsibly and in compliance with applicable laws, terms of service, and ethical guidelines.
