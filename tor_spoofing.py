import requests
import time
import os
import subprocess
import socket  # ADD THIS IMPORT
from PyQt6.QtWidgets import QMessageBox

class TORSpoofer:
    def __init__(self, gui_instance=None):
        self.gui_instance = gui_instance
        self.tor_enabled = False
        self.tor_session = None
        self.tor_port = 9050  # Default TOR port
        self.control_port = 9051  # Default control port
        self.tor_password = "hashbrownyummy"  # Set your password here, change it
    
    def log_message(self, message):
        """Log messages to GUI output area if available"""
        if self.gui_instance and hasattr(self.gui_instance, 'output_area'):
            self.gui_instance.output_area.append(f"🔒 TOR: {message}")
        else:
            print(f"TOR: {message}")
    
    def check_tor_connection(self):
        """Check if TOR is running and accessible via multiple endpoints."""
        test_urls = [
            "https://httpbin.org/ip",          # Returns JSON
            "https://api.ipify.org?format=json",  # Returns JSON
            "https://icanhazip.com",           # Returns plain text
            "https://checkip.amazonaws.com"    # Returns plain text
        ]

        session = requests.Session()
        session.proxies = {
            'http': f'socks5h://127.0.0.1:{self.tor_port}',
            'https': f'socks5h://127.0.0.1:{self.tor_port}'
        }
        
        for url in test_urls:
            try:
                response = session.get(url, timeout=15)
                if response.status_code == 200:
                    try:
                        # Try parsing JSON response
                        ip_data = response.json()
                        ip = ip_data.get("origin") or ip_data.get("ip")
                    except ValueError:
                        # Fallback to plain text response
                        ip = response.text.strip()
                    
                    if ip:
                        self.log_message(f"Connected via TOR - Current IP: {ip}")
                        return True
            except Exception as e:
                self.log_message(f"TOR test failed for {url}: {e}")
                continue  # Try next endpoint

        self.log_message("TOR connection failed across all endpoints.")
        return False
        return False

    def renew_tor_connection(self):
        """Renew TOR circuit using raw socket authentication"""
        try:
            # Use raw socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect(('127.0.0.1', self.control_port))
            
            # Try authentication with password
            if self.tor_password:
                auth_cmd = f'AUTHENTICATE "{self.tor_password}"\r\n'
                sock.send(auth_cmd.encode())
                response = sock.recv(1024).decode()
                
                if '250 OK' in response:
                    self.log_message("🔐 Authenticated with password")
                else:
                    # Try without password
                    auth_cmd = 'AUTHENTICATE\r\n'
                    sock.send(auth_cmd.encode())
                    response = sock.recv(1024).decode()
            else:
                # Try without password
                auth_cmd = 'AUTHENTICATE\r\n'
                sock.send(auth_cmd.encode())
                response = sock.recv(1024).decode()
            
            if '250 OK' not in response:
                self.log_message(f"❌ Authentication failed: {response}")
                sock.close()
                return False
            
            # Send NEWNYM signal
            sock.send(b'SIGNAL NEWNYM\r\n')
            response = sock.recv(1024).decode()
            
            if '250 OK' not in response:
                self.log_message(f"❌ NEWNYM failed: {response}")
                sock.close()
                return False
            
            self.log_message("🔄 Renewed TOR circuit - New IP address")
            sock.send(b'QUIT\r\n')
            sock.close()
            
            # Wait for circuit to establish
            time.sleep(3)
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ TOR renewal failed: {e}")
            return False
            
    def setup_tor_session(self):
        """Set up a requests session that routes through TOR"""
        if not self.check_tor_connection():
            self.log_message("TOR not available. Please ensure TOR is running.")
            return None
        
        self.tor_session = requests.Session()
        self.tor_session.proxies = {
            'http': f'socks5h://127.0.0.1:{self.tor_port}',
            'https': f'socks5h://127.0.0.1:{self.tor_port}'
        }
        
        self.tor_enabled = True
        self.log_message("TOR session configured successfully")
        return self.tor_session
    
    def get_current_ip(self):
        """Get current public IP address through TOR"""
        if not self.tor_session:
            if not self.setup_tor_session():
                return None
        
        try:
            response = self.tor_session.get('http://httpbin.org/ip', timeout=30)
            if response.status_code == 200:
                return response.json()['origin']
        except Exception as e:
            self.log_message(f"Failed to get current IP: {e}")
        
        return None
    
    def enable_tor_for_ai(self, tor_port=9050, control_port=9051):
        """Enable TOR spoofing for AI requests"""
        self.tor_port = tor_port
        self.control_port = control_port
        
        # First, ensure TOR is running
        if not self.ensure_tor_running():
            self.log_message("❌ Failed to start TOR service")
            return False
        
        if self.setup_tor_session():
            self.tor_enabled = True
            # Test IP renewal
            try:
                if self.renew_tor_connection():
                    self.log_message("✅ TOR spoofing enabled with IP renewal")
                else:
                    self.log_message("✅ TOR spoofing enabled (IP renewal may not work)")
            except Exception as e:
                self.log_message(f"✅ TOR spoofing enabled (renewal issue: {e})")
            return True
        else:
            self.tor_enabled = False
            self.log_message("❌ Failed to enable TOR spoofing")
            return False
    
    def ensure_tor_running(self):
        """Ensure TOR service is running"""
        try:
            # Check if TOR is already running
            if self.check_tor_connection():
                return True
            
            # Try to start TOR service
            self.log_message("🔄 Starting TOR service...")
            result = subprocess.run(['sudo', 'systemctl', 'start', 'tor'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log_message("✅ TOR service started")
                # Wait for TOR to initialize
                time.sleep(5)
                return self.check_tor_connection()
            else:
                self.log_message(f"❌ Failed to start TOR: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ TOR service management failed: {e}")
            return False
    
    def disable_tor(self):
        """Disable TOR spoofing"""
        self.tor_enabled = False
        self.tor_session = None
        self.log_message("TOR spoofing disabled")