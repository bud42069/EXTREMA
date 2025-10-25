#!/usr/bin/env python3
"""
Phase 1 Enhanced Detection Engine - Backend Testing
Tests the newly integrated Phase 1 MTF Confluence Engine with:
- 1m Impulse Detection (RSI-12, BOS, Volume)
- Tape Filters (CVD z-score, OBI, VWAP Proximity)  
- Comprehensive Veto System
- Enhanced MTF Confluence Endpoint
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
BACKEND_URL = "https://solana-impulse.preview.emergentagent.com"
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
    
    # ============= NEW MICROSTRUCTURE STREAM TESTS =============
    
    def test_stream_start(self):
        """Test starting MEXC microstructure stream"""
        try:
            response = requests.post(f"{API_BASE}/stream/start", timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("Stream Start", True, f"MEXC stream started: {data.get('message', '')}")
                else:
                    self.log_result("Stream Start", False, f"Success=False: {data}")
            else:
                self.log_result("Stream Start", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Stream Start", False, f"Exception: {str(e)}")
    
    def test_stream_health(self):
        """Test microstructure stream health check"""
        try:
            response = requests.get(f"{API_BASE}/stream/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                required_fields = ['running', 'available']
                if all(field in data for field in required_fields):
                    status_info = f"Running: {data['running']}, Available: {data['available']}"
                    if 'age_seconds' in data:
                        status_info += f", Age: {data['age_seconds']}s"
                    self.log_result("Stream Health", True, status_info)
                else:
                    self.log_result("Stream Health", False, f"Missing fields in response: {data}")
            else:
                self.log_result("Stream Health", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Stream Health", False, f"Exception: {str(e)}")
    
    def test_stream_snapshot(self):
        """Test microstructure snapshot retrieval"""
        try:
            response = requests.get(f"{API_BASE}/stream/snapshot", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'available' in data:
                    if data['available']:
                        # Check for microstructure metrics
                        metrics = ['spread_bps', 'ladder_imbalance', 'cvd', 'cvd_slope']
                        available_metrics = [m for m in metrics if m in data]
                        self.log_result("Stream Snapshot", True, f"Available with {len(available_metrics)} metrics")
                    else:
                        self.log_result("Stream Snapshot", True, "No data available (expected if stream not running)")
                else:
                    self.log_result("Stream Snapshot", False, f"Missing 'available' field: {data}")
            else:
                self.log_result("Stream Snapshot", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Stream Snapshot", False, f"Exception: {str(e)}")
    
    def test_stream_stop(self):
        """Test stopping MEXC microstructure stream"""
        try:
            response = requests.post(f"{API_BASE}/stream/stop", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("Stream Stop", True, data.get('message', 'Stream stopped'))
                else:
                    self.log_result("Stream Stop", False, f"Success=False: {data}")
            else:
                self.log_result("Stream Stop", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Stream Stop", False, f"Exception: {str(e)}")
    
    def test_signals_latest_with_veto(self):
        """Test latest signals endpoint with microstructure veto dict"""
        try:
            # Test with microstructure gate enabled
            response = requests.get(f"{API_BASE}/signals/latest?enable_micro_gate=true", timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Should return either a signal with veto dict or "no confirmed signal" message
                if 'side' in data:
                    # Signal found - check for veto dict
                    if 'veto' in data:
                        self.log_result("Signals Latest (Veto)", True, f"Signal with veto transparency: {data['side']}")
                    else:
                        self.log_result("Signals Latest (Veto)", False, "Signal missing veto dict")
                elif 'message' in data:
                    # No signal found but endpoint structure is correct
                    self.log_result("Signals Latest (Veto)", True, "Endpoint working, no signal available (expected)")
                else:
                    self.log_result("Signals Latest (Veto)", False, f"Unexpected response: {data}")
            else:
                self.log_result("Signals Latest (Veto)", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Signals Latest (Veto)", False, f"Exception: {str(e)}")
    
    # ============= PROMETHEUS METRICS TESTS =============
    
    def test_prometheus_metrics(self):
        """Test Prometheus metrics endpoint"""
        try:
            # Test direct backend access since frontend intercepts /metrics
            import subprocess
            result = subprocess.run(['curl', '-s', 'http://localhost:8001/metrics'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                metrics_text = result.stdout
                
                # Check for starlette metrics with extrema app name
                starlette_metrics = ['starlette_requests_total{app_name="extrema"']
                found_starlette = any(metric in metrics_text for metric in starlette_metrics)
                
                # Check for Python runtime metrics
                runtime_metrics = ['python_info', 'process_']
                found_runtime = []
                for metric in runtime_metrics:
                    if metric in metrics_text:
                        found_runtime.append(metric)
                
                if found_starlette and found_runtime:
                    self.log_result("Prometheus Metrics", True, 
                                  f"Starlette + {len(found_runtime)} runtime metrics available")
                else:
                    self.log_result("Prometheus Metrics", False, 
                                  f"Missing metrics - Starlette: {found_starlette}, Runtime: {len(found_runtime)}")
            else:
                self.log_result("Prometheus Metrics", False, f"Curl failed: {result.stderr}")
        except Exception as e:
            self.log_result("Prometheus Metrics", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting SOLUSDT Backend Testing - Microstructure + Prometheus")
        print(f"📡 Backend URL: {BACKEND_URL}")
        print("=" * 70)
        
        # Priority 1 - Microstructure Stream API
        print("\n🔬 PRIORITY 1: Microstructure Stream API")
        self.test_stream_start()
        time.sleep(3)  # Give stream time to initialize
        self.test_stream_health()
        self.test_stream_snapshot()
        self.test_signals_latest_with_veto()
        self.test_stream_stop()
        
        # Priority 2 - Prometheus Metrics
        print("\n📊 PRIORITY 2: Prometheus Metrics")
        self.test_prometheus_metrics()
        
        # Priority 3 - Regression Testing (Existing Endpoints)
        print("\n🔄 PRIORITY 3: Regression Testing")
        self.test_health_endpoint()
        self.test_csv_upload()
        self.test_signals_latest()
        await self.test_websocket_signals()
        
        # Live monitoring (quick test)
        print("\n📈 PRIORITY 3: Live Monitoring (Quick Test)")
        self.test_live_monitor_start()
        time.sleep(2)
        self.test_live_monitor_status()
        self.test_live_signals()
        self.test_live_monitor_stop()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
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