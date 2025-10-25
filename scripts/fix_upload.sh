#!/bin/bash
# Quick fix for data upload issues

echo "🔧 Fixing Data Upload..."

# 1. Check backend
echo "1. Checking backend..."
sudo supervisorctl status backend

# 2. Restart if needed
if ! curl -s http://localhost:8001/api/health/ > /dev/null; then
    echo "⚠️  Backend not responding, restarting..."
    sudo supervisorctl restart backend
    sleep 5
fi

# 3. Test with sample data
echo "2. Testing upload with sample data..."
cat > /tmp/test_upload.csv << 'EOF'
time,open,high,low,close,Volume
1,100,101,99,100.5,1000
2,100.5,102,100,101,1200
3,101,103,101,102,1400
4,102,104,101.5,103,1600
5,103,105,102.5,104,1800
EOF

RESULT=$(curl -s -X POST http://localhost:8001/api/data/upload -F "file=@/tmp/test_upload.csv")

if echo "$RESULT" | grep -q "rows"; then
    echo "✅ Upload working! Uploaded $(echo $RESULT | grep -oP '"rows":\K[0-9]+') rows"
    echo "$RESULT" | python3 -m json.tool
else
    echo "❌ Upload failed:"
    echo "$RESULT"
    echo ""
    echo "Try:"
    echo "1. Check your CSV has columns: time,open,high,low,close,Volume"
    echo "2. Check file size < 10MB"
    echo "3. Check backend logs: tail /var/log/supervisor/backend.err.log"
fi

echo ""
echo "Current data status:"
curl -s http://localhost:8001/api/swings/ | python3 -m json.tool
