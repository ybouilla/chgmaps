# enter docker: docker run -it pipeline sh
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    libpq-dev \
    postgresql-client \
    gcc \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app/ /app/app

# Optional data dir
RUN mkdir -p /app/data

# default to pipeline
ENV MODE=pipeline
ENV PYTHONPATH=/app
# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]

