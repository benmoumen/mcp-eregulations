# Deployment Documentation for MCP eRegulations Server

This document provides comprehensive instructions for deploying the MCP eRegulations server in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
   - [Docker Deployment](#docker-deployment)
   - [Kubernetes Deployment](#kubernetes-deployment)
   - [Manual Deployment](#manual-deployment)
3. [Configuration](#configuration)
4. [Monitoring](#monitoring)
5. [Backup and Restore](#backup-and-restore)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the MCP eRegulations server, ensure you have the following:

- Docker and Docker Compose (for container-based deployment)
- Python 3.10 or higher (for manual deployment)
- Access to the eRegulations API instance you want to connect to
- Git access to the repository: `git@github.com:benmoumen/mcp-eregulations.git`

## Deployment Options

### Docker Deployment

The recommended way to deploy the MCP eRegulations server is using Docker and Docker Compose.

#### Quick Start

1. Clone the repository:
   ```bash
   git clone git@github.com:benmoumen/mcp-eregulations.git
   cd mcp-eregulations
   ```

2. Configure the environment:
   - Edit the environment variables in `docker-compose.yml` to match your eRegulations instance
   - By default, it's configured to use the Tanzania instance

3. Set up monitoring (optional):
   ```bash
   ./setup_monitoring.sh
   ```

4. Start the server:
   ```bash
   docker-compose up -d
   ```

5. Verify the deployment:
   ```bash
   curl http://localhost:8000/health
   ```

#### Production Deployment

For production environments, we recommend the following additional steps:

1. Use a reverse proxy (like Nginx or Traefik) to handle SSL termination
2. Set up proper authentication for the monitoring services
3. Configure persistent volumes for data storage
4. Set up log aggregation

Example production `docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  mcp-eregulations:
    restart: always
    volumes:
      - /path/to/persistent/data:/app/data
    environment:
      - LOG_LEVEL=WARNING
      - CACHE_TTL=7200
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  prometheus:
    volumes:
      - /path/to/prometheus/data:/prometheus
    environment:
      - PROMETHEUS_ADMIN_USER=admin
      - PROMETHEUS_ADMIN_PASSWORD=secure_password

  grafana:
    volumes:
      - /path/to/grafana/data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secure_password
      - GF_SECURITY_ADMIN_USER=admin
```

### Kubernetes Deployment

For large-scale deployments, Kubernetes is recommended.

1. Create a namespace:
   ```bash
   kubectl create namespace mcp-eregulations
   ```

2. Create ConfigMap for environment variables:
   ```bash
   kubectl create configmap mcp-eregulations-config \
     --from-literal=EREGULATIONS_API_URL=https://api-tanzania.tradeportal.org \
     --from-literal=EREGULATIONS_API_VERSION=v1 \
     --from-literal=MCP_SERVER_NAME=eregulations \
     --from-literal=MCP_SERVER_PORT=8000 \
     --from-literal=CACHE_ENABLED=true \
     --from-literal=CACHE_TTL=3600 \
     --from-literal=LOG_LEVEL=INFO \
     -n mcp-eregulations
   ```

3. Apply the Kubernetes manifests:
   ```bash
   kubectl apply -f kubernetes/deployment.yaml -n mcp-eregulations
   kubectl apply -f kubernetes/service.yaml -n mcp-eregulations
   kubectl apply -f kubernetes/ingress.yaml -n mcp-eregulations
   ```

4. Verify the deployment:
   ```bash
   kubectl get pods -n mcp-eregulations
   ```

### Manual Deployment

For environments where containers are not available, you can deploy manually:

1. Clone the repository:
   ```bash
   git clone git@github.com:benmoumen/mcp-eregulations.git
   cd mcp-eregulations
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   export EREGULATIONS_API_URL=https://api-tanzania.tradeportal.org
   export EREGULATIONS_API_VERSION=v1
   export MCP_SERVER_NAME=eregulations
   export MCP_SERVER_PORT=8000
   export CACHE_ENABLED=true
   export CACHE_TTL=3600
   export LOG_LEVEL=INFO
   ```

5. Start the server:
   ```bash
   python -m mcp_eregulations.main
   ```

6. For production, use a process manager like Supervisor or systemd.

Example systemd service file (`/etc/systemd/system/mcp-eregulations.service`):

```ini
[Unit]
Description=MCP eRegulations Server
After=network.target

[Service]
User=mcp
WorkingDirectory=/opt/mcp-eregulations
ExecStart=/opt/mcp-eregulations/.venv/bin/python -m mcp_eregulations.main
Restart=on-failure
Environment=EREGULATIONS_API_URL=https://api-tanzania.tradeportal.org
Environment=EREGULATIONS_API_VERSION=v1
Environment=MCP_SERVER_NAME=eregulations
Environment=MCP_SERVER_PORT=8000
Environment=CACHE_ENABLED=true
Environment=CACHE_TTL=3600
Environment=LOG_LEVEL=WARNING

[Install]
WantedBy=multi-user.target
```

## Configuration

The MCP eRegulations server can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| EREGULATIONS_API_URL | Base URL of the eRegulations API | https://api-tanzania.tradeportal.org |
| EREGULATIONS_API_VERSION | API version | v1 |
| MCP_SERVER_NAME | Name of the MCP server | eregulations |
| MCP_SERVER_PORT | Port to run the server on | 8000 |
| CACHE_ENABLED | Enable caching | true |
| CACHE_TTL | Cache time-to-live in seconds | 3600 |
| LOG_LEVEL | Logging level | INFO |

## Monitoring

The MCP eRegulations server includes monitoring capabilities using Prometheus and Grafana.

### Metrics

The server exposes metrics at the `/metrics` endpoint, which can be scraped by Prometheus.

Key metrics include:
- HTTP request counts and durations
- Cache hit/miss ratios
- API call latencies
- Memory and CPU usage

### Dashboards

Pre-configured Grafana dashboards are available in the `monitoring/grafana/dashboards` directory.

To access Grafana:
1. Navigate to `http://your-server:3000`
2. Log in with the credentials specified in your configuration
3. Import the dashboards if they're not already available

## Backup and Restore

### Data Backup

The MCP eRegulations server stores data in the following locations:

- `/app/data/auth`: Authentication data
- `/app/data/index`: Indexed procedure data

To back up this data:

```bash
# For Docker deployment
docker-compose exec mcp-eregulations tar -czf /tmp/mcp-backup.tar.gz /app/data
docker cp mcp-eregulations:/tmp/mcp-backup.tar.gz ./mcp-backup.tar.gz

# For manual deployment
tar -czf mcp-backup.tar.gz /path/to/data
```

### Restore from Backup

To restore from a backup:

```bash
# For Docker deployment
docker cp ./mcp-backup.tar.gz mcp-eregulations:/tmp/
docker-compose exec mcp-eregulations tar -xzf /tmp/mcp-backup.tar.gz -C /

# For manual deployment
tar -xzf mcp-backup.tar.gz -C /
```

## Troubleshooting

### Common Issues

1. **Connection to eRegulations API fails**
   - Check the EREGULATIONS_API_URL environment variable
   - Verify network connectivity to the API
   - Check if the API requires authentication

2. **Server starts but tools are not available**
   - Check the logs for initialization errors
   - Verify that the MCP server is properly configured

3. **Performance issues**
   - Increase cache TTL
   - Check system resources (CPU, memory)
   - Monitor API call latencies

### Logs

Logs are output to stdout/stderr and can be viewed:

```bash
# Docker deployment
docker-compose logs -f mcp-eregulations

# Kubernetes deployment
kubectl logs -f deployment/mcp-eregulations -n mcp-eregulations

# Manual deployment
journalctl -u mcp-eregulations.service -f
```

### Health Check

The server provides a health check endpoint at `/health` that returns the status of various components:

```bash
curl http://localhost:8000/health
```

Example response:
```json
{
  "status": "healthy",
  "api_connection": "ok",
  "cache": "ok",
  "uptime": "3h 24m 12s"
}
```

For more detailed troubleshooting, refer to the user documentation or contact support.

# Deployment Guide

This guide covers deploying the MCP eRegulations server in various environments.

## Environment Configuration

### Required Environment Variables

The following environment variables must be configured:

```bash
# Server Configuration
MCP_SERVER_NAME=eregulations  # Name of the MCP server instance
MCP_SERVER_PORT=8000          # Port to run the server on
MCP_HOST=0.0.0.0             # Host interface to bind to
MCP_TRANSPORT=auto           # Transport mode (auto, stdio, or sse)

# eRegulations API Configuration
EREGULATIONS_API_URL         # Base URL of the eRegulations API instance
EREGULATIONS_API_VERSION     # API version to use (default: v1)
EREGULATIONS_API_KEY         # Optional API key for authentication

# Optional Configuration
CACHE_ENABLED=true           # Enable response caching
CACHE_TTL=3600              # Cache TTL in seconds
```

### Docker Deployment

When using Docker, you can configure the API URL in several ways:

1. Environment file:
```bash
# .env file
EREGULATIONS_API_URL=https://api-example.eregulations.org
```

2. Docker run command:
```bash
docker run -e EREGULATIONS_API_URL=https://api-example.eregulations.org -p 8000:8000 mcp-eregulations
```

3. Docker Compose:
```yaml
version: '3'
services:
  mcp-server:
    build: .
    environment:
      - EREGULATIONS_API_URL=https://api-example.eregulations.org
    ports:
      - "8000:8000"
```

### Kubernetes Deployment

For Kubernetes deployments, configure the API URL using:

1. ConfigMap:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-eregulations-config
data:
  EREGULATIONS_API_URL: "https://api-example.eregulations.org"
```

2. Environment variables in deployment:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-eregulations
spec:
  template:
    spec:
      containers:
      - name: mcp-eregulations
        env:
        - name: EREGULATIONS_API_URL
          valueFrom:
            configMapKeyRef:
              name: mcp-eregulations-config
              key: EREGULATIONS_API_URL
```

## Health Checks

The server provides a health check endpoint that returns the current API URL configuration:

```bash
curl http://localhost:8000/health
```

## Monitoring

Monitor the API connection status using the provided Prometheus metrics:
- `mcp_api_requests_total`: Total number of API requests
- `mcp_api_request_duration_seconds`: API request duration
- `mcp_api_errors_total`: Total number of API errors

## Troubleshooting

### Common Deployment Issues

1. API Connection Issues
   - Verify the API URL is accessible from the deployment environment
   - Check network policies and firewall rules
   - Validate SSL certificates if using HTTPS

2. Configuration Issues
   - Ensure environment variables are properly set
   - Check for typos in the API URL
   - Verify the API version is supported

### Logs

Enable debug logging by setting:
```bash
MCP_LOG_LEVEL=DEBUG
```

This will show detailed API connection information in the logs.
