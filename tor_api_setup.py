import sys
import os
import subprocess
import requests
import socket
import time
from PyQt6.QtCore import QThread, pyqtSignal

class TORAPISetup(QThread):
    """Thread to handle API setup through TOR"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, tor_port=9050, control_port=9051, tor_password=None):
        super().__init__()
        self.tor_port = tor_port
        self.control_port = control_port
        self.tor_password = tor_password
        self.process = None
    
    def enable_tor(self):
        """Enable and test TOR connection"""
        try:
            session = requests.Session()
            session.proxies = {
                'http': f'socks5h://127.0.0.1:{self.tor_port}',
                'https': f'socks5h://127.0.0.1:{self.tor_port}'
            }
            
            response = session.get('http://httpbin.org/ip', timeout=30)
            if response.status_code == 200:
                self.output_signal.emit(f"🔒 TOR connected - IP: {response.json()['origin']}")
                return True
        except Exception as e:
            self.output_signal.emit(f"❌ TOR connection failed: {e}")
            return False

    def renew_tor_ip(self):
        """Get fresh TOR IP with configurable authentication"""
        try:
            # Use socket-based authentication to match tor_spoofing.py
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect(('127.0.0.1', self.control_port))
            
            # Authenticate with password if provided
            if self.tor_password:
                auth_cmd = f'AUTHENTICATE "{self.tor_password}"\r\n'
                sock.send(auth_cmd.encode())
                response = sock.recv(1024).decode()
                
                if '250 OK' in response:
                    self.output_signal.emit("🔐 Authenticated with password")
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
                self.output_signal.emit(f"❌ Authentication failed: {response}")
                sock.close()
                return False
            
            # Send NEWNYM signal
            sock.send(b'SIGNAL NEWNYM\r\n')
            response = sock.recv(1024).decode()
            
            if '250 OK' not in response:
                self.output_signal.emit(f"❌ NEWNYM failed: {response}")
                sock.close()
                return False
            
            self.output_signal.emit("🔄 Renewed TOR circuit - New IP address")
            sock.send(b'QUIT\r\n')
            sock.close()
            
            # Wait for circuit to establish
            time.sleep(3)
            return True
                
        except Exception as e:
            self.output_signal.emit(f"❌ TOR renewal failed: {e}")
            return True  # Don't fail the setup, continue with current IP
    
    def run(self):
        """Execute API setup through TOR"""
        self.output_signal.emit("🚀 Starting API setup through TOR...")
        
        # Enable TOR
        if not self.enable_tor():
            self.finished_signal.emit(False)
            return
        
        # Renew to get fresh IP for registration
        self.renew_tor_ip()
        
        # Set up environment for TOR
        env = os.environ.copy()
        env['ALL_PROXY'] = f'socks5h://127.0.0.1:{self.tor_port}'
        env['HTTP_PROXY'] = f'socks5h://127.0.0.1:{self.tor_port}'
        env['HTTPS_PROXY'] = f'socks5h://127.0.0.1:{self.tor_port}'
        
        try:
            # Run blackbird setup through TOR
            self.process = subprocess.Popen(
                ['python', 'blackbird.py', '--setup-ai'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1
            )
            
            # Handle the interactive prompt
            confirmation_sent = False
            for line in self.process.stdout:
                text = line.strip()
                self.output_signal.emit(text)
                
                # Auto-confirm the IP registration prompt
                if not confirmation_sent and ('ip is registered' in text.lower() or '[y/n]' in text.lower()):
                    try:
                        self.process.stdin.write('Y\n')
                        self.process.stdin.flush()
                        confirmation_sent = True
                        self.output_signal.emit("✅ Automatically confirmed IP registration through TOR")
                    except Exception as e:
                        self.output_signal.emit(f"❌ Confirmation failed: {e}")
            
            self.process.stdout.close()
            self.process.wait()
            self.finished_signal.emit(True)
            
        except Exception as e:
            self.output_signal.emit(f"❌ Setup failed: {e}")
            self.finished_signal.emit(False)
    
    def stop(self):
        """Stop the setup process"""
        if self.process:
            self.process.terminate()
            self.process.wait()