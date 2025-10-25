#!/bin/bash
# Quick fix for live monitor issues

echo "🔧 Fixing Live Monitor..."

# 1. Stop existing monitor
echo "1. Stopping existing monitor..."
curl -s -X POST http://localhost:8001/api/live/stop > /dev/null
sleep 2

# 2. Start fresh
echo "2. Starting live monitor..."
START_RESULT=$(curl -s -X POST http://localhost:8001/api/live/start)

if echo "$START_RESULT" | grep -q "success"; then
    echo "✅ Monitor started successfully"
    echo "$START_RESULT" | python3 -m json.tool
else
    echo "❌ Failed to start monitor:"
    echo "$START_RESULT"
    exit 1
fi

# 3. Wait for data
echo ""
echo "3. Waiting for price data..."
sleep 5

# 4. Check status
echo "4. Monitor status:"
STATUS=$(curl -s http://localhost:8001/api/live/status)
echo "$STATUS" | python3 -m json.tool

if echo "$STATUS" | grep -q '"running": true'; then
    PRICE=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['last_price'])")
    echo ""
    echo "✅ Monitor is live! Current SOL price: \$${PRICE}"
else
    echo ""
    echo "⚠️  Monitor started but no data yet. This is normal, wait 30s for Pyth Network."
fi

echo ""
echo "To stop monitor: curl -X POST http://localhost:8001/api/live/stop"
