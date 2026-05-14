FROM python:3.12.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libzbar0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x app/scripts/docker-entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/app/app/scripts/docker-entrypoint.sh"]
