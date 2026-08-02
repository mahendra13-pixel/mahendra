#!/usr/bin/env python
"""
Django Windows Service Launcher
Run as Windows Service with NSSM
"""

import os
import sys
import subprocess
import socket
import time

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def main():
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ff_infotech.settings')
    
    # Get IPs
    local_ip = get_local_ip()
    your_ip = '172.31.100.19'
    
    print("\n" + "="*60)
    print("🚀 Django Server Running as Windows Service")
    print("="*60)
    print(f"📍 Localhost:   http://127.0.0.1:8000")
    print(f"📍 Local IP:    http://{local_ip}:8000")
    print(f"📍 Your IP:     http://{your_ip}:8000")
    print("="*60)
    print("Service is running in background...")
    print("To stop: nssm stop DjangoServer")
    print("To uninstall: nssm remove DjangoServer")
    print("="*60 + "\n")
    
    # Run server
    subprocess.call([
        sys.executable, 
        'manage.py', 
        'runserver', 
        '0.0.0.0:8000'
    ])

if __name__ == '__main__':
    main()