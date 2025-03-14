FROM python:3.10-slim

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -s /root/.local/bin/uv /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies using uv
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . .

# Add src directory to PYTHONPATH
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Create data directory with proper permissions
RUN mkdir -p /app/data && chmod 777 /app/data

# Default environment variables
ENV MCP_SERVER_NAME=eregulations \
    MCP_SERVER_PORT=8000 \
    MCP_HOST=0.0.0.0 \
    MCP_TRANSPORT=auto \
    MCP_LOG_LEVEL=INFO \
    EREGULATIONS_API_URL=https://api.eregulations.org \
    EREGULATIONS_API_VERSION=v1 \
    CACHE_ENABLED=true \
    CACHE_TTL=3600

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:${MCP_SERVER_PORT}/health || exit 1

# Run the server
CMD ["python", "-m", "mcp_eregulations.main"]
