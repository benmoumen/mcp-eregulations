#!/bin/bash
set -e

echo "Setting up MCP monitoring infrastructure..."

# Create required directories
mkdir -p monitoring/data/prometheus
mkdir -p monitoring/data/grafana
mkdir -p monitoring/rules
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards

# Set correct permissions for Grafana and Prometheus
chmod -R 777 monitoring/data/

# Update Prometheus configuration
cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'mcp'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
EOF

# Set up alert rules
if [ ! -f monitoring/rules/mcp_alerts.yml ]; then
    echo "Error: mcp_alerts.yml not found"
    exit 1
fi

# Create Grafana datasource configuration
cat > monitoring/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# Create Grafana dashboard provisioning configuration
cat > monitoring/grafana/provisioning/dashboards/mcp.yml << EOF
apiVersion: 1

providers:
  - name: 'MCP Dashboards'
    orgId: 1
    folder: 'MCP'
    folderUid: ''
    type: file
    disableDeletion: false
    editable: true
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/dashboards
EOF

# Create docker-compose configuration if it doesn't exist
if [ ! -f docker-compose.yml ]; then
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  mcp-eregulations:
    build: .
    ports:
      - "8000:8000"
      - "9090:9090"
    environment:
      - MCP_SERVER_NAME=eregulations
      - MCP_SERVER_PORT=8000
      - MCP_TRANSPORT=auto
      - MCP_HOST=0.0.0.0
      - METRICS_ENABLED=true
      - METRICS_PORT=9090
    volumes:
      - ./data:/app/data
    depends_on:
      - prometheus
      - grafana

  prometheus:
    image: prom/prometheus:v2.45.0
    ports:
      - "9091:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/rules:/etc/prometheus/rules
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:10.0.3
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/etc/grafana/dashboards
EOF
fi

# Start monitoring stack using docker-compose
echo "Starting monitoring stack..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Verify services are running
echo "Verifying services..."
docker-compose ps

# Make the script executable
chmod +x setup_monitoring.sh

echo "Monitoring setup complete! Access:"
echo "- Grafana: http://localhost:3000 (admin/admin)"
echo "- Prometheus: http://localhost:9090"
echo "- Alert Manager: http://localhost:9093"

echo "Don't forget to:"
echo "1. Change the default Grafana password"
echo "2. Import the MCP dashboard"
echo "3. Configure alert notifications"
