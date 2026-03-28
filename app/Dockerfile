# PrintBot AI - Docker Configuration
# ===================================
# Multi-stage build for production deployment

# Stage 1: Build React Dashboard
FROM node:20-alpine AS dashboard-builder

WORKDIR /app/dashboard

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Python Backend
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY python/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python source
COPY python/ ./python/

# Stage 3: Final Production Image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment from backend stage
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin

# Copy application files
COPY python/ ./python/
COPY --from=dashboard-builder /app/dashboard/dist /usr/share/nginx/html

# Create data directories
RUN mkdir -p /app/data /app/data/designs /app/data/backups /app/logs

# Copy nginx configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Copy startup script
COPY docker/start.sh ./start.sh
RUN chmod +x ./start.sh

# Environment variables
ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/printbot.db
ENV LOG_LEVEL=INFO

# Expose ports
EXPOSE 80 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start command
CMD ["./start.sh"]
