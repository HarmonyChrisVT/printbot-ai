#!/bin/bash
# PrintBot AI - Docker Startup Script
# ====================================

set -e

echo "Starting PrintBot AI..."

# Start Python backend first so it's ready before nginx
echo "Starting AI agents and API server..."
cd /app/python
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Wait for uvicorn to be ready before starting nginx
echo "Waiting for API server to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/api/status > /dev/null 2>&1; then
        echo "API server is ready."
        break
    fi
    sleep 1
done

# Start nginx
echo "Starting web server..."
nginx -g "daemon off;" &

echo "PrintBot AI is running!"
echo "   Dashboard: http://localhost"
echo "   API: http://localhost:8000"

# Wait for all background processes
wait
