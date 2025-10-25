#!/usr/bin/env python3
"""
Keep-alive pinger for backend API.
Prevents cold starts by periodically hitting health and metrics endpoints.
Run this in background: python3 keepalive.py &
"""
import time
import requests
from datetime import datetime

BACKEND_URL = "http://localhost:8001"
PING_INTERVAL = 300  # 5 minutes

def ping():
    """Ping health and metrics endpoints."""
    endpoints = ["/api/health/", "/metrics"]
    
    for endpoint in endpoints:
        try:
            url = f"{BACKEND_URL}{endpoint}"
            response = requests.get(url, timeout=10)
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {status} {endpoint} ({response.status_code})")
        except Exception as e:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ✗ {endpoint} - Error: {e}")

if __name__ == "__main__":
    print(f"Starting keep-alive pinger (interval: {PING_INTERVAL}s)")
    print(f"Target: {BACKEND_URL}")
    
    while True:
        ping()
        time.sleep(PING_INTERVAL)
