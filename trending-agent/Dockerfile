FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
# COPY ../shared /app/shared

# Copy application code
COPY . /app
# COPY app.py .
# # COPY .dockerignore* ./
# COPY base_executor.py .

EXPOSE 10020

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:10020/.well-known/agent.json || exit 1

CMD ["python", "app.py"]