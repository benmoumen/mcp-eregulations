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
