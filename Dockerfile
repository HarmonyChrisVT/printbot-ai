FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

COPY python/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY python/ ./python/
COPY dist/ /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/start.sh ./start.sh
RUN chmod +x ./start.sh

RUN mkdir -p /app/data /app/logs

ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/printbot.db
ENV LOG_LEVEL=INFO

EXPOSE 80 8000

CMD ["./start.sh"]