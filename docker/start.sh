#!/bin/bash
# PrintBot AI - Docker Startup Script
# ====================================

set -e

echo "🚀 Starting PrintBot AI..."

# Start nginx in background
echo "🌐 Starting web server..."
nginx &

# Wait for nginx
sleep 2

# Start Python backend
echo "🤖 Starting AI agents..."
cd /app
python python/main.py &

# Keep container running
echo "✅ PrintBot AI is running!"
echo "   Dashboard: http://localhost"
echo "   API: http://localhost:8000"

# Wait for all background processes
wait
