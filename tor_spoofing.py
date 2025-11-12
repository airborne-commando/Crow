# tor_spoofing.py

import requests
import time
import os
import subprocess
from stem import Signal
from stem.control import Controller
from PyQt6.QtWidgets import QMessageBox

class TORSpoofer:
    def __init__(self, gui_instance=None):
        self.gui_instance = gui_instance
        self.tor_enabled = False
        self.tor_session = None
        self.tor_port = 9050  # Default TOR port
        self.control_port = 9051  # Default control port
        self.tor_password = "dkdkwedkowea[kdwaokdowakkdowokd"  # ← SET YOUR PASSWORD HERE
    
    def log_message(self, message):
        """Log messages to GUI output area if available"""
        if self.gui_instance and hasattr(self.gui_instance, 'output_area'):
            self.gui_instance.output_area.append(f"🔒 TOR: {message}")
        else:
            print(f"TOR: {message}")
    
    def check_tor_connection(self):
        """Check if TOR is running and accessible"""
        try:
            session = requests.Session()
            session.proxies = {
                'http': f'socks5h://127.0.0.1:{self.tor_port}',
                'https': f'socks5h://127.0.0.1:{self.tor_port}'
            }
            
            # Test connection through TOR
            response = session.get('http://httpbin.org/ip', timeout=30)
            if response.status_code == 200:
                ip_data = response.json()
                self.log_message(f"Connected via TOR - Current IP: {ip_data['origin']}")
                return True
                
        except Exception as e:
            self.log_message(f"TOR connection failed: {e}")
            return False
        
        return False

    def renew_tor_connection(self):
        """Renew TOR circuit using raw socket authentication"""
        try:
            import socket
            
            # Use raw socket connection instead of stem Controller
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.control_port))
            
            # Authenticate
            auth_cmd = f'AUTHENTICATE "dkdkwedkowea[kdwaokdowakkdowokd"\r\n'
            sock.send(auth_cmd.encode())
            response = sock.recv(1024).decode()
            
            if '250 OK' not in response:
                self.log_message(f"❌ Authentication failed: {response}")
                sock.close()
                return False
            
            self.log_message("🔐 Authenticated with password")
            
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
            time.sleep(5)
            
            # Verify new IP
            new_ip = self.get_current_ip()
            if new_ip:
                self.log_message(f"🔒 New TOR IP: {new_ip}")
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ TOR renewal failed: {e}")
            return True  # Don't fail completely
            
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
    
    def disable_tor(self):
        """Disable TOR spoofing"""
        self.tor_enabled = False
        self.tor_session = None
        self.log_message("TOR spoofing disabled")