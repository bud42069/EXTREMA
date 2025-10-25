# EXTREMA v1.0 - Troubleshooting Guide

## Quick Diagnosis & Fixes

### Issue: "Fails to Load Dataset"

**Symptoms:**
- Upload page doesn't accept CSV files
- "No data loaded" error messages
- Empty dashboard

**Quick Fix:**
```bash
# 1. Check backend is running
sudo supervisorctl status backend

# 2. Test upload directly
curl -X POST http://localhost:8001/api/data/upload \
  -F "file=@your_data.csv"

# 3. Verify data loaded
curl http://localhost:8001/api/swings/
```

**Root Causes & Solutions:**

1. **CORS Issue** - Frontend can't reach backend
   - Check `/app/frontend/.env` has correct `REACT_APP_BACKEND_URL`
   - Should be: `https://solana-impulse.preview.emergentagent.com` (for preview)
   - Or: `http://localhost:8001` (for local testing)

2. **File Size Too Large** - Proxy limits
   - Split large CSV files into chunks (< 10MB recommended)
   - Use streaming upload for large datasets

3. **CSV Format Issue** - Missing required columns
   - **Required columns**: `time`, `open`, `high`, `low`, `close`, `Volume`
   - Check CSV headers match exactly (case-sensitive)
   - No extra spaces in column names

4. **Backend Not Running**
   ```bash
   sudo supervisorctl restart backend
   sleep 3
   curl http://localhost:8001/api/health/
   ```

---

### Issue: "Monitor Fails to Start"

**Symptoms:**
- "Start Monitor" button doesn't work
- No live price data
- WebSocket shows "Polling Mode" forever

**Quick Fix:**
```bash
# 1. Start monitor via API
curl -X POST http://localhost:8001/api/live/start

# 2. Check status
curl http://localhost:8001/api/live/status

# 3. Verify price data flowing
watch -n 2 'curl -s http://localhost:8001/api/live/status | python3 -m json.tool'
```

**Root Causes & Solutions:**

1. **Pyth Network Connection** - External API issue
   - Pyth Network might be temporarily down
   - Check: https://pyth.network/price-feeds
   - Monitor auto-retries every 5 seconds

2. **WebSocket Connection** - Browser blocks WS
   - Check browser console for errors
   - Verify WSS (not WS) for HTTPS sites
   - Try different browser (Chrome/Firefox recommended)

3. **Memory/Resource** - Container out of memory
   ```bash
   # Check resource usage
   free -h
   df -h
   
   # Restart if needed
   sudo supervisorctl restart all
   ```

4. **Helius API Key** - On-chain data failing
   - This is optional; system works without it
   - If you have key, add to `/app/backend/.env`:
     ```
     HELIUS_API_KEY=your_key_here
     ```

---

### Issue: "Frontend Not Loading"

**Symptoms:**
- Blank page or "Preview Unavailable"
- 404 errors in console
- Changes not reflecting

**Quick Fix:**
```bash
# 1. Restart frontend
sudo supervisorctl restart frontend

# 2. Clear browser cache
# Press Ctrl+Shift+R (hard refresh)

# 3. Check frontend logs
tail -f /var/log/supervisor/frontend.err.log
```

**Root Causes & Solutions:**

1. **Build Error** - React compilation failed
   ```bash
   # Check for errors
   tail -n 50 /var/log/supervisor/frontend.err.log
   
   # Reinstall if needed
   cd /app/frontend
   yarn install
   sudo supervisorctl restart frontend
   ```

2. **Port Conflict** - 3000 already in use
   ```bash
   # Check what's using port 3000
   lsof -i :3000
   
   # Kill if needed
   sudo kill -9 <PID>
   sudo supervisorctl restart frontend
   ```

3. **Environment Variables** - Wrong backend URL
   ```bash
   # Check .env
   cat /app/frontend/.env
   
   # Should contain:
   # REACT_APP_BACKEND_URL=https://solana-impulse.preview.emergentagent.com
   ```

---

## Common User Errors

### 1. CSV Format Issues

**Wrong:**
```csv
Time,Open,High,Low,Close,Vol
2024-01-01 00:00:00,100,101,99,100.5,1000
```

**Correct:**
```csv
time,open,high,low,close,Volume
1704067200,100,101,99,100.5,1000
```

**Requirements:**
- Column names: lowercase (time, open, high, low, close), Volume (capital V)
- Time: Unix timestamp or integer sequence
- Numbers: No commas, use decimals
- No empty rows

### 2. Upload Size Limits

- **Maximum CSV size**: ~10MB per upload
- **Recommended rows**: 1000-10000 bars
- **For larger datasets**: Split into multiple files

### 3. Missing Data

- **Minimum bars needed**: 50 bars
- **For indicators**: Need 50+ bars for ATR, RSI, etc.
- **For signals**: Need 100+ bars for reliable detection

---

## Quick Health Check Script

Save as `/app/scripts/health_check.sh`:

```bash
#!/bin/bash
echo "=== EXTREMA Health Check ==="

echo "1. Services:"
sudo supervisorctl status backend frontend

echo -e "\n2. Backend Health:"
curl -s http://localhost:8001/api/health/

echo -e "\n3. Metrics:"
curl -s http://localhost:8001/metrics | grep -c "http_requests"

echo -e "\n4. Data Status:"
curl -s http://localhost:8001/api/swings/ | python3 -m json.tool

echo -e "\n5. Live Monitor:"
curl -s http://localhost:8001/api/live/status | python3 -m json.tool

echo -e "\n✅ Health check complete"
```

Run: `bash /app/scripts/health_check.sh`

---

## Emergency Reset

If everything is broken:

```bash
# 1. Stop all services
sudo supervisorctl stop all

# 2. Clear cache/temp files
rm -rf /tmp/*.csv
rm -rf /app/frontend/node_modules/.cache

# 3. Restart services
sudo supervisorctl start all

# 4. Wait for startup
sleep 10

# 5. Test
curl http://localhost:8001/api/health/
```

---

## Contact Points

- **Backend API**: http://localhost:8001
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8001/api/docs
- **Metrics**: http://localhost:8001/metrics
- **Logs**: `/var/log/supervisor/*.log`

---

## Performance Benchmarks

Expected response times:
- `/api/health/` - < 10ms
- `/api/data/upload` - < 500ms (100 rows)
- `/api/signals/latest` - < 150ms
- `/api/scalp/card` - < 150ms
- WebSocket ping-pong - < 100ms

If responses are slower, check system resources:
```bash
top -b -n 1 | head -20
free -h
df -h
```
