FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies - with fix for GPG issues
RUN apt-get update -y --allow-insecure-repositories && \
    apt-get install -y --no-install-recommends --allow-unauthenticated \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/

# Create directories for data
RUN mkdir -p /app/data/auth /app/data/index

# Set default environment variables
ENV EREGULATIONS_API_URL="https://api-tanzania.tradeportal.org"
ENV EREGULATIONS_API_VERSION="v1"
ENV MCP_SERVER_NAME="eregulations"
ENV MCP_SERVER_PORT=8000
ENV CACHE_ENABLED=true
ENV CACHE_TTL=3600
ENV LOG_LEVEL="INFO"

# Expose the port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "mcp_eregulations.main"]
