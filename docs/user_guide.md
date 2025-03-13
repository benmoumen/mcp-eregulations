# User Documentation for MCP eRegulations Server

This document provides comprehensive guidance for using the MCP eRegulations server with Model Context Protocol (MCP) clients.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Available Tools](#available-tools)
4. [Authentication](#authentication)
5. [Example Usage](#example-usage)
6. [Integration with LLMs](#integration-with-llms)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Introduction

The MCP eRegulations server provides a Model Context Protocol (MCP) interface to eRegulations platform data. It allows Large Language Models (LLMs) to access structured information about administrative procedures, requirements, costs, and institutions documented in the eRegulations platform.

### What is Model Context Protocol (MCP)?

Model Context Protocol (MCP) is a standard for connecting LLMs to external tools and data sources. It allows LLMs to:
- Access real-time information
- Perform actions in external systems
- Process structured data

### What is eRegulations?

eRegulations is a platform that documents administrative procedures in various countries. It provides detailed information about:
- Official procedures (like registering a business)
- Step-by-step guides
- Required documents
- Associated costs
- Relevant institutions
- Legal frameworks

## Getting Started

### Prerequisites

To use the MCP eRegulations server, you need:
- An MCP-compatible client or LLM
- API access credentials (if authentication is enabled)
- The URL of the deployed MCP eRegulations server

### Connecting to the Server

The MCP eRegulations server exposes an HTTP endpoint that follows the MCP specification. To connect:

1. Obtain the server URL (e.g., `https://mcp-eregulations.example.com`)
2. Configure your MCP client to use this URL
3. If authentication is required, obtain and configure API credentials

Example configuration for an MCP client:

```python
from mcp.client import Client

# Initialize the client
client = Client(
    server_url="https://mcp-eregulations.example.com",
    api_key="your_api_key"  # If authentication is enabled
)

# List available tools
tools = client.list_tools()
print(tools)
```

## Available Tools

The MCP eRegulations server provides the following tools:

### Basic Procedure Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `get_procedure` | Get basic information about a procedure | `procedure_id: int` |
| `get_procedure_steps` | Get steps for a procedure | `procedure_id: int` |
| `get_procedure_requirements` | Get requirements for a procedure | `procedure_id: int` |
| `get_procedure_costs` | Get costs for a procedure | `procedure_id: int` |

### Detailed Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `get_procedure_detailed` | Get comprehensive information about a procedure | `procedure_id: int` |
| `get_institution_info` | Get information about an institution | `institution_id: int` |
| `get_country_info` | Get information about a country | `country_id: int` |

### Search Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `search_procedures_by_keyword` | Search for procedures using keywords | `query: str, limit: int = 5` |

### Query Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `process_natural_language_query` | Process a natural language query about eRegulations | `query: str` |
| `answer_procedure_question` | Answer a specific question about a procedure | `procedure_id: int, question: str` |

### Authentication Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `register_user` | Register a new user | `username: str, password: str` |
| `authenticate_user` | Authenticate a user and get a token | `username: str, password: str` |
| `create_api_key` | Create a new API key for a user | `username: str, api_key: str` |
| `list_api_keys` | List API keys for a user | `username: str, api_key: str` |
| `revoke_api_key` | Revoke an API key | `username: str, target_api_key: str, api_key: str` |

## Authentication

The MCP eRegulations server supports authentication using API keys. Here's how to use it:

### Registering a User

```python
result = await client.invoke("register_user", {
    "username": "your_username",
    "password": "your_password"
})
print(result)
```

### Authenticating and Getting a Token

```python
result = await client.invoke("authenticate_user", {
    "username": "your_username",
    "password": "your_password"
})
print(result)  # Contains the authentication token
```

### Creating an API Key

```python
result = await client.invoke("create_api_key", {
    "username": "your_username",
    "api_key": "your_auth_token"  # From authenticate_user
})
print(result)  # Contains the new API key
```

### Using an API Key

Once you have an API key, include it in all authenticated requests:

```python
result = await client.invoke("get_procedure", {
    "procedure_id": 123,
    "api_key": "your_api_key"
})
```

## Example Usage

Here are some examples of how to use the MCP eRegulations server:

### Getting Information About a Procedure

```python
# Get basic procedure information
procedure_info = await client.invoke("get_procedure", {
    "procedure_id": 123
})
print(procedure_info)

# Get procedure steps
steps_info = await client.invoke("get_procedure_steps", {
    "procedure_id": 123
})
print(steps_info)

# Get detailed procedure information
detailed_info = await client.invoke("get_procedure_detailed", {
    "procedure_id": 123
})
print(detailed_info)
```

### Searching for Procedures

```python
# Search for procedures related to business registration
search_results = await client.invoke("search_procedures_by_keyword", {
    "query": "business registration",
    "limit": 5
})
print(search_results)
```

### Processing Natural Language Queries

```python
# Ask a question in natural language
response = await client.invoke("process_natural_language_query", {
    "query": "What are the steps to register a business in Tanzania?"
})
print(response)

# Ask a specific question about a procedure
answer = await client.invoke("answer_procedure_question", {
    "procedure_id": 123,
    "question": "What documents do I need for this procedure?"
})
print(answer)
```

## Integration with LLMs

The MCP eRegulations server is designed to be used with Large Language Models (LLMs) that support the Model Context Protocol. Here's how to integrate it with different LLM frameworks:

### OpenAI with MCP Client

```python
from openai import OpenAI
from mcp.client import Client

# Initialize the MCP client
mcp_client = Client(
    server_url="https://mcp-eregulations.example.com",
    api_key="your_api_key"
)

# Initialize the OpenAI client
openai_client = OpenAI(api_key="your_openai_api_key")

# Get available tools from MCP server
tools = mcp_client.list_tools()

# Create a chat completion with tool use
response = openai_client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant with access to eRegulations data."},
        {"role": "user", "content": "What are the steps to register a business in Tanzania?"}
    ],
    tools=tools,
    tool_choice="auto"
)

# Process tool calls
for tool_call in response.choices[0].message.tool_calls:
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)
    
    # Call the MCP server
    tool_result = mcp_client.invoke(tool_name, tool_args)
    
    # Send the result back to the model
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant with access to eRegulations data."},
            {"role": "user", "content": "What are the steps to register a business in Tanzania?"},
            response.choices[0].message,
            {"role": "tool", "tool_call_id": tool_call.id, "content": tool_result}
        ]
    )

print(response.choices[0].message.content)
```

### LangChain Integration

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from mcp.client import Client

# Initialize the MCP client
mcp_client = Client(
    server_url="https://mcp-eregulations.example.com",
    api_key="your_api_key"
)

# Create LangChain tools from MCP tools
tools = []
for tool_name in ["get_procedure", "search_procedures_by_keyword", "process_natural_language_query"]:
    tools.append(
        Tool(
            name=tool_name,
            func=lambda **kwargs, tn=tool_name: mcp_client.invoke(tn, kwargs),
            description=mcp_client.get_tool_description(tool_name)
        )
    )

# Create an agent with the tools
llm = ChatOpenAI(model="gpt-4-turbo")
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Run the agent
result = agent_executor.invoke({"input": "What are the steps to register a business in Tanzania?"})
print(result["output"])
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify the server URL is correct
   - Check network connectivity
   - Ensure the server is running

2. **Authentication Errors**
   - Verify your API key is valid
   - Check if the API key has the necessary permissions
   - Try regenerating your API key

3. **Tool Invocation Errors**
   - Check that you're using the correct tool name
   - Verify all required parameters are provided
   - Check parameter types (e.g., procedure_id should be an integer)

### Debugging

The MCP client provides debugging options:

```python
from mcp.client import Client

# Enable debug mode
client = Client(
    server_url="https://mcp-eregulations.example.com",
    api_key="your_api_key",
    debug=True  # Enables detailed logging
)

# Test connection
client.ping()
```

## FAQ

**Q: Can I use the MCP eRegulations server with any LLM?**
A: The server can be used with any LLM that supports the Model Context Protocol or has an MCP client adapter.

**Q: How do I know which eRegulations instance the server is connected to?**
A: The server is configured with a specific eRegulations instance (e.g., Tanzania). You can check the server configuration or ask the administrator.

**Q: Is the data real-time?**
A: Yes, the server connects to the live eRegulations API. However, some data may be cached for performance reasons.

**Q: How do I handle rate limits?**
A: The server implements rate limiting to prevent abuse. If you encounter rate limit errors, reduce the frequency of your requests.

**Q: Can I deploy my own instance of the MCP eRegulations server?**
A: Yes, refer to the deployment documentation for instructions on deploying your own instance.

**Q: How do I report issues or request features?**
A: Contact the repository maintainers at github.com/benmoumen/mcp-eregulations or open an issue on the GitHub repository.
