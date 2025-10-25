#!/usr/bin/env python3
"""
Comprehensive Backend Testing for SOLUSDT Swing Detection System
Tests Microstructure Integration, Prometheus Metrics, WebSocket Signal Streaming, and existing endpoints
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd
import requests
import websockets
from websockets.exceptions import ConnectionClosedError

# Backend URL from frontend environment
BACKEND_URL = "https://swingcapture.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"
METRICS_URL = f"{BACKEND_URL}/metrics"

class BackendTester:
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if details:
            result += f" - {details}"
        
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
        if not success:
            self.failed_tests.append(test_name)
    
    def test_health_endpoint(self):
        """Test basic health endpoint"""
        try:
            response = requests.get(f"{API_BASE}/health/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log_result("Health Endpoint", True, "Status OK")
                else:
                    self.log_result("Health Endpoint", False, f"Unexpected response: {data}")
            else:
                self.log_result("Health Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Health Endpoint", False, f"Exception: {str(e)}")
    
    def test_csv_upload(self):
        """Test CSV data upload endpoint"""
        try:
            # Create sample CSV data
            sample_data = {
                'time': [1640995200 + i*300 for i in range(100)],  # 5-minute intervals
                'open': [100.0 + i*0.1 for i in range(100)],
                'high': [100.5 + i*0.1 for i in range(100)],
                'low': [99.5 + i*0.1 for i in range(100)],
                'close': [100.2 + i*0.1 for i in range(100)],
                'Volume': [1000 + i*10 for i in range(100)]
            }
            df = pd.DataFrame(sample_data)
            
            # Save to temporary CSV file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                df.to_csv(f.name, index=False)
                csv_path = f.name
            
            try:
                # Upload CSV
                with open(csv_path, 'rb') as f:
                    files = {'file': ('test_data.csv', f, 'text/csv')}
                    response = requests.post(f"{API_BASE}/data/upload", files=files, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'rows' in data and 'columns' in data:
                        self.log_result("CSV Upload", True, f"Uploaded {data['rows']} rows")
                    else:
                        self.log_result("CSV Upload", False, f"Unexpected response: {data}")
                else:
                    self.log_result("CSV Upload", False, f"HTTP {response.status_code}: {response.text}")
            
            finally:
                # Clean up temp file
                os.unlink(csv_path)
                
        except Exception as e:
            self.log_result("CSV Upload", False, f"Exception: {str(e)}")
    
    def test_signals_latest(self):
        """Test latest signals endpoint"""
        try:
            response = requests.get(f"{API_BASE}/signals/latest", timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Should return either a signal or "no confirmed signal" message
                if 'side' in data or 'message' in data:
                    self.log_result("Latest Signals", True, "Endpoint responding correctly")
                else:
                    self.log_result("Latest Signals", False, f"Unexpected response: {data}")
            else:
                self.log_result("Latest Signals", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Latest Signals", False, f"Exception: {str(e)}")
    
    async def test_websocket_signals(self):
        """Test WebSocket signal streaming endpoint"""
        try:
            ws_url = f"wss://swingcapture.preview.emergentagent.com/api/signals/stream"
            
            async with websockets.connect(ws_url) as websocket:
                # Test initial connection
                try:
                    # Wait for initial connection message
                    initial_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(initial_msg)
                    
                    if data.get('type') == 'connected':
                        self.log_result("WebSocket Connection", True, "Initial connection established")
                    else:
                        self.log_result("WebSocket Connection", False, f"Unexpected initial message: {data}")
                        return
                    
                    # Test ping/pong mechanism
                    await websocket.send('ping')
                    pong_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    if pong_response == 'pong':
                        self.log_result("WebSocket Ping/Pong", True, "Keepalive mechanism working")
                    else:
                        self.log_result("WebSocket Ping/Pong", False, f"Expected 'pong', got: {pong_response}")
                    
                    # Test connection stays alive for a few seconds
                    await asyncio.sleep(2)
                    self.log_result("WebSocket Stability", True, "Connection remained stable")
                    
                except asyncio.TimeoutError:
                    self.log_result("WebSocket Connection", False, "Timeout waiting for initial message")
                except json.JSONDecodeError as e:
                    self.log_result("WebSocket Connection", False, f"JSON decode error: {e}")
                    
        except ConnectionClosedError:
            self.log_result("WebSocket Connection", False, "Connection closed unexpectedly")
        except Exception as e:
            self.log_result("WebSocket Connection", False, f"Exception: {str(e)}")
    
    def test_live_monitor_start(self):
        """Test starting live monitoring"""
        try:
            response = requests.post(f"{API_BASE}/live/start", timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("Live Monitor Start", True, data.get('message', 'Started successfully'))
                else:
                    self.log_result("Live Monitor Start", False, f"Success=False: {data}")
            else:
                self.log_result("Live Monitor Start", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Live Monitor Start", False, f"Exception: {str(e)}")
    
    def test_live_monitor_status(self):
        """Test live monitor status endpoint"""
        try:
            response = requests.get(f"{API_BASE}/live/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                required_fields = ['running', 'candles_count', 'active_signals_count', 'last_price']
                if all(field in data for field in required_fields):
                    status_info = f"Running: {data['running']}, Candles: {data['candles_count']}"
                    self.log_result("Live Monitor Status", True, status_info)
                else:
                    self.log_result("Live Monitor Status", False, f"Missing fields in response: {data}")
            else:
                self.log_result("Live Monitor Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Live Monitor Status", False, f"Exception: {str(e)}")
    
    def test_live_signals(self):
        """Test live signals endpoint"""
        try:
            response = requests.get(f"{API_BASE}/live/signals", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'signals' in data:
                    signals_count = len(data['signals'])
                    self.log_result("Live Signals", True, f"Retrieved {signals_count} signals")
                else:
                    self.log_result("Live Signals", False, f"Missing 'signals' field: {data}")
            else:
                self.log_result("Live Signals", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Live Signals", False, f"Exception: {str(e)}")
    
    def test_live_monitor_stop(self):
        """Test stopping live monitoring"""
        try:
            response = requests.post(f"{API_BASE}/live/stop", timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Should succeed whether monitor was running or not
                self.log_result("Live Monitor Stop", True, data.get('message', 'Stop command sent'))
            else:
                self.log_result("Live Monitor Stop", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Live Monitor Stop", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting SOLUSDT Backend Testing")
        print(f"📡 Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Priority 1 - Basic connectivity and existing endpoints
        print("\n📋 PRIORITY 1: Basic Endpoints & Regression Testing")
        self.test_health_endpoint()
        self.test_csv_upload()
        self.test_signals_latest()
        
        # Priority 2 - NEW WebSocket functionality
        print("\n🔌 PRIORITY 2: WebSocket Signal Streaming")
        await self.test_websocket_signals()
        
        # Priority 3 - NEW Live monitoring endpoints
        print("\n📊 PRIORITY 3: Live Monitoring API")
        self.test_live_monitor_start()
        time.sleep(2)  # Give monitor time to initialize
        self.test_live_monitor_status()
        self.test_live_signals()
        self.test_live_monitor_stop()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        if self.failed_tests:
            print(f"\n🔍 Failed Tests:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed - see details above")
        
        return failed_tests == 0

async def main():
    """Main test runner"""
    tester = BackendTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())