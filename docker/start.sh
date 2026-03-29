#!/bin/bash
# PrintBot AI - Docker Startup Script
# ====================================

set -e

# Railway injects PORT; default to 8080 for local/other environments
export PORT="${PORT:-8080}"

echo "Starting PrintBot AI on port ${PORT}..."

# Generate nginx config from template with actual PORT value
# Only substitute ${PORT} - leave nginx variables like $uri, $host untouched
envsubst '${PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

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
echo "   Dashboard: http://localhost:${PORT}"
echo "   API: http://localhost:8000"

# Wait for all background processes
wait
