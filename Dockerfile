FROM python:3.11-slim

WORKDIR /app

# Minimal system deps — no nginx needed (FastAPI serves the React app directly)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY python/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY python/ ./python/

# Pre-built React dashboard (already in dist/ — no Node.js build needed)
COPY dist/ /app/dist/

# Persistent data directories
RUN mkdir -p /app/data/designs /app/data/backups /app/logs

ENV PYTHONPATH=/app/python
ENV DATABASE_PATH=/app/data/printbot.db
ENV LOG_LEVEL=INFO

# Railway sets $PORT dynamically — uvicorn picks it up via the CMD

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/api/health || exit 1

CMD sh -c "cd /app/python && uvicorn main_v2:app --host 0.0.0.0 --port ${PORT:-8080}"
