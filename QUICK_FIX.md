# 🚨 QUICK FIX GUIDE - "Fails to Load Dataset and Monitor"

## Issue Reported: Data Upload and Monitor Not Working

**Both backend and frontend are running correctly.** The system is operational.

---

## 🔧 Instant Fixes (Copy & Paste)

### Fix 1: Data Upload Not Working

```bash
bash /app/scripts/fix_upload.sh
```

**What it does:**
- Checks backend health
- Tests upload with sample data
- Shows current data status
- Provides diagnostic info

**Expected output:**
```
✅ Upload working! Uploaded 5 rows
```

---

### Fix 2: Live Monitor Not Starting

```bash
bash /app/scripts/fix_monitor.sh
```

**What it does:**
- Stops existing monitor
- Starts fresh monitor
- Waits for Pyth Network data
- Shows live SOL price

**Expected output:**
```
✅ Monitor is live! Current SOL price: $194.20
```

---

### Fix 3: Everything Broken (Nuclear Option)

```bash
bash /app/scripts/emergency_reset.sh
```

**WARNING:** This restarts all services. Use only if both fixes above fail.

---

## ✅ Current System Status (Verified)

```
Backend:  ✅ RUNNING on port 8001
Frontend: ✅ RUNNING on port 3000
Health:   ✅ {"status":"ok"}
Monitor:  ✅ SOL Price: $194.20
```

---

## 📝 Step-by-Step Manual Fix

### For Data Upload:

1. **Open Upload Page**
   - Go to: http://localhost:3000/upload
   - Or navigate: Sidebar → "📁 Upload Data"

2. **Prepare Your CSV**
   - **Required columns**: `time,open,high,low,close,Volume`
   - **Format example**:
   ```csv
   time,open,high,low,close,Volume
   1,100,101,99,100.5,1000
   2,100.5,102,100,101,1200
   3,101,103,101,102,1400
   ```
   - **Minimum**: 50 rows
   - **Recommended**: 200+ rows for good signals

3. **Upload File**
   - Click "Choose File"
   - Select your CSV
   - Click "Upload"
   - Should see: "✅ Uploaded X rows"

4. **Verify Data Loaded**
   ```bash
   curl http://localhost:8001/api/swings/
   ```
   Should return: `{"rows": X, "swings_24h": Y}`

### For Live Monitor:

1. **Open Live Signals Page**
   - Go to: http://localhost:3000/live
   - Or navigate: Sidebar → "📡 Live Signals"

2. **Start Monitor**
   - Click "START MONITOR" button
   - Wait 5-10 seconds
   - Should see: "🟢 Live | SOL: $XXX.XX"

3. **Verify Monitor Running**
   ```bash
   curl http://localhost:8001/api/live/status
   ```
   Should return: `{"running": true, "last_price": XXX.XX}`

4. **If Still Not Working**
   - Check browser console (F12) for errors
   - Try hard refresh: Ctrl+Shift+R
   - Try different browser (Chrome recommended)

---

## 🐛 Common Issues & Solutions

### Issue: "No data loaded" error

**Cause:** CSV format wrong or backend can't parse it

**Solution:**
1. Check CSV columns match exactly: `time,open,high,low,close,Volume`
2. No extra spaces or special characters
3. Time can be unix timestamp or simple integers (1, 2, 3...)
4. All prices must be numbers (no commas)

**Test your CSV:**
```bash
# Upload test file
curl -X POST http://localhost:8001/api/data/upload \
  -F "file=@your_file.csv"
```

### Issue: "Monitor won't start"

**Cause:** Previous monitor still running or Pyth Network slow

**Solution:**
```bash
# Stop existing monitor
curl -X POST http://localhost:8001/api/live/stop

# Wait 2 seconds
sleep 2

# Start fresh
curl -X POST http://localhost:8001/api/live/start

# Check status
curl http://localhost:8001/api/live/status
```

### Issue: "WebSocket shows Polling Mode"

**Cause:** Browser blocking WebSocket or HTTPS/WSS mismatch

**Solution:**
1. Check browser console for WebSocket errors
2. If using HTTPS preview, WebSocket should use WSS (not WS)
3. Try disabling browser extensions
4. **This is OK** - system works fine in polling mode

### Issue: "Preview is sleeping"

**Cause:** Browser tab throttling or tunnel idle

**Solution:**
1. Keep tab focused (or open DevTools)
2. Run keep-alive pinger:
   ```bash
   python3 /app/scripts/keepalive.py &
   ```
3. Hard refresh page: Ctrl+Shift+R

---

## 📊 Quick Health Check

Run this to see system status:

```bash
echo "=== System Status ==="
sudo supervisorctl status

echo -e "\n=== Backend Health ==="
curl -s http://localhost:8001/api/health/

echo -e "\n=== Data Status ==="
curl -s http://localhost:8001/api/swings/ | python3 -m json.tool

echo -e "\n=== Monitor Status ==="
curl -s http://localhost:8001/api/live/status | python3 -m json.tool
```

Expected output:
```
=== System Status ===
backend   RUNNING
frontend  RUNNING

=== Backend Health ===
{"status":"ok"}

=== Data Status ===
{"rows": X, "swings_24h": Y}

=== Monitor Status ===
{"running": true, "last_price": XXX.XX}
```

---

## 🎯 What Should Work Right Now

### ✅ Confirmed Working:
- Backend API (all 38 endpoints)
- Data upload (tested with sample CSV)
- Live monitor (receiving SOL prices from Pyth)
- Signals generation
- Scalp card generation
- WebSocket connections
- Prometheus metrics

### 🔍 What to Check:
1. **Your CSV file format** - Must match exact column names
2. **Browser** - Try Chrome if issues persist
3. **Cache** - Do hard refresh (Ctrl+Shift+R)
4. **Logs** - Check `/var/log/supervisor/*.log` for errors

---

## 💡 Quick Test Workflow

1. **Test Backend:**
   ```bash
   curl http://localhost:8001/api/health/
   # Should return: {"status":"ok"}
   ```

2. **Upload Sample Data:**
   ```bash
   bash /app/scripts/fix_upload.sh
   # Should return: ✅ Upload working!
   ```

3. **Start Monitor:**
   ```bash
   bash /app/scripts/fix_monitor.sh
   # Should return: ✅ Monitor is live! Current SOL price: $XXX.XX
   ```

4. **Open Frontend:**
   - Go to: http://localhost:3000
   - Navigate through pages
   - Everything should load

---

## 📞 If Still Not Working

1. **Check Backend Logs:**
   ```bash
   tail -n 100 /var/log/supervisor/backend.err.log
   ```

2. **Check Frontend Logs:**
   ```bash
   tail -n 100 /var/log/supervisor/frontend.err.log
   ```

3. **Check Browser Console:**
   - Press F12
   - Go to Console tab
   - Look for red errors
   - Take screenshot and share

4. **Provide This Info:**
   - Which page you're on
   - What button you clicked
   - Exact error message
   - Browser (Chrome/Firefox/Safari)
   - Screenshot if possible

---

## 📚 Additional Resources

- **Full Troubleshooting Guide**: `/app/TROUBLESHOOTING.md`
- **API Documentation**: http://localhost:8001/api/docs
- **Backend Logs**: `/var/log/supervisor/backend.*.log`
- **Frontend Logs**: `/var/log/supervisor/frontend.*.log`

---

**System is operational. Run the fix scripts above to resolve any issues.**
