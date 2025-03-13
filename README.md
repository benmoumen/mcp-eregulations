# MCP eRegulations Server

A Model Context Protocol (MCP) server for the eRegulations platform that enables LLMs to answer user questions about documented administrative procedures.

## Overview

The MCP eRegulations server provides a Model Context Protocol interface to eRegulations platform data. It allows Large Language Models (LLMs) to access structured information about administrative procedures, requirements, costs, and institutions documented in the eRegulations platform.

This server can be configured to work with different eRegulations instances (e.g., Tanzania, Kenya, Rwanda) and provides a standardized interface for LLMs to query and retrieve information.

## Features

- **MCP-compatible API**: Follows the Model Context Protocol specification for seamless integration with LLMs
- **Comprehensive Tools**: Access procedures, steps, requirements, costs, and institutions
- **Natural Language Processing**: Process queries in natural language about administrative procedures
- **Authentication & Security**: API key-based authentication and security features
- **Performance Optimized**: Caching, rate limiting, and connection pooling for optimal performance
- **Containerized**: Docker and Kubernetes deployment options
- **Monitoring**: Prometheus and Grafana integration for monitoring and alerting

## Quick Start

### Using Docker

```bash
# Clone the repository
git clone git@github.com:benmoumen/mcp-eregulations.git
cd mcp-eregulations

# Start the server
docker-compose up -d

# Test the server
curl http://localhost:8000/health
```

### Using Python

```bash
# Clone the repository
git clone git@github.com:benmoumen/mcp-eregulations.git
cd mcp-eregulations

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m mcp_eregulations.main
```

## Configuration

The server can be configured using environment variables:

```bash
# eRegulations API configuration
export EREGULATIONS_API_URL=https://api-tanzania.tradeportal.org
export EREGULATIONS_API_VERSION=v1

# MCP server configuration
export MCP_SERVER_NAME=eregulations
export MCP_SERVER_PORT=8000

# Performance configuration
export CACHE_ENABLED=true
export CACHE_TTL=3600
export LOG_LEVEL=INFO
```

## Documentation

- [User Guide](docs/user_guide.md): How to use the MCP eRegulations server with MCP clients
- [Deployment Guide](docs/deployment.md): How to deploy the server in various environments
- [Architecture](docs/architecture.md): Technical architecture and design decisions

## Available Tools

The MCP eRegulations server provides the following tools:

- `get_procedure`: Get basic information about a procedure
- `get_procedure_steps`: Get steps for a procedure
- `get_procedure_requirements`: Get requirements for a procedure
- `get_procedure_costs`: Get costs for a procedure
- `get_procedure_detailed`: Get comprehensive information about a procedure
- `search_procedures_by_keyword`: Search for procedures using keywords
- `process_natural_language_query`: Process a natural language query about eRegulations
- `answer_procedure_question`: Answer a specific question about a procedure

## Example Usage

```python
from mcp.client import Client

# Initialize the client
client = Client(
    server_url="https://mcp-eregulations.example.com",
    api_key="your_api_key"  # If authentication is enabled
)

# Get information about a procedure
procedure_info = await client.invoke("get_procedure", {
    "procedure_id": 123
})
print(procedure_info)

# Ask a question in natural language
response = await client.invoke("process_natural_language_query", {
    "query": "What are the steps to register a business in Tanzania?"
})
print(response)
```

## Development

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for containerized development)
- Access to an eRegulations API instance

### Setup Development Environment

```bash
# Clone the repository
git clone git@github.com:benmoumen/mcp-eregulations.git
cd mcp-eregulations

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest src/tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP specification
- [eRegulations Platform](https://api-tanzania.tradeportal.org/swagger/ui/index) for the API and data
