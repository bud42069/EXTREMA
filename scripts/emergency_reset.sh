#!/bin/bash
# Emergency reset - use when everything is broken

echo "🚨 Emergency Reset Starting..."
echo ""

read -p "This will restart all services. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 1
fi

# 1. Stop all
echo "1. Stopping all services..."
sudo supervisorctl stop all
sleep 3

# 2. Clear temp files
echo "2. Clearing temp files..."
rm -f /tmp/*.csv
rm -f /tmp/test_*

# 3. Check ports
echo "3. Checking ports..."
BACKEND_PORT=$(lsof -ti:8001)
FRONTEND_PORT=$(lsof -ti:3000)

if [ ! -z "$BACKEND_PORT" ]; then
    echo "  Killing process on port 8001: $BACKEND_PORT"
    kill -9 $BACKEND_PORT 2>/dev/null
fi

if [ ! -z "$FRONTEND_PORT" ]; then
    echo "  Killing process on port 3000: $FRONTEND_PORT"
    kill -9 $FRONTEND_PORT 2>/dev/null
fi

# 4. Start all
echo "4. Starting all services..."
sudo supervisorctl start all

echo "5. Waiting for startup (15s)..."
sleep 15

# 6. Health check
echo "6. Health check:"
echo ""

echo "Backend:"
BACKEND_HEALTH=$(curl -s http://localhost:8001/api/health/)
if echo "$BACKEND_HEALTH" | grep -q "ok"; then
    echo "  ✅ Backend running"
else
    echo "  ❌ Backend failed:"
    echo "  $BACKEND_HEALTH"
    echo ""
    echo "  Check logs: tail -n 50 /var/log/supervisor/backend.err.log"
fi

echo ""
echo "Frontend:"
FRONTEND_CHECK=$(curl -s -I http://localhost:3000 | head -1)
if echo "$FRONTEND_CHECK" | grep -q "200"; then
    echo "  ✅ Frontend running"
else
    echo "  ❌ Frontend failed:"
    echo "  $FRONTEND_CHECK"
    echo ""
    echo "  Check logs: tail -n 50 /var/log/supervisor/frontend.err.log"
fi

echo ""
echo "Services:"
sudo supervisorctl status

echo ""
echo "✅ Emergency reset complete"
echo ""
echo "Next steps:"
echo "1. Go to http://localhost:3000/upload"
echo "2. Upload your CSV file"
echo "3. Go to http://localhost:3000/scalp-cards"
echo "4. Click 'Generate Card'"
