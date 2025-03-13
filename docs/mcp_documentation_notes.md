# MCP Documentation Notes

## Core MCP Concepts

MCP servers can provide three main types of capabilities:

1. **Resources**: File-like data that can be read by clients (like API responses or file contents)
2. **Tools**: Functions that can be called by the LLM (with user approval)
3. **Prompts**: Pre-written templates that help users accomplish specific tasks

## Implementation with Python SDK

The Python SDK provides a `FastMCP` class that uses Python type hints and docstrings to automatically generate tool definitions, making it easy to create and maintain MCP tools.

### Setup Requirements

- Python 3.10 or higher
- Python MCP SDK 1.2.0 or higher
- Dependencies: `mcp[cli]` and other required packages (like `httpx` for HTTP requests)

### Basic Server Structure

1. **Imports and Server Initialization**:
   ```python
   from typing import Any
   import httpx
   from mcp.server.fastmcp import FastMCP

   # Initialize FastMCP server
   mcp = FastMCP("server-name")
   ```

2. **Helper Functions**:
   - Functions for API requests, data formatting, etc.
   - Example:
   ```python
   async def make_api_request(url: str) -> dict[str, Any] | None:
       """Make a request to an API with proper error handling."""
       headers = {
           "User-Agent": USER_AGENT,
           "Accept": "application/json"
       }
       async with httpx.AsyncClient() as client:
           try:
               response = await client.get(url, headers=headers)
               response.raise_for_status()
               return response.json()
           except Exception:
               return None
   ```

3. **Tool Implementation**:
   - Use `@mcp.tool()` decorator
   - Define functions with type hints and docstrings
   - Example:
   ```python
   @mcp.tool()
   async def get_data(param: str) -> str:
       """Get data from an API.
       
       Args:
           param: Description of parameter
           
       Returns:
           Formatted response data
       """
       url = f"{API_BASE}/endpoint/{param}"
       data = await make_api_request(url)
       
       if not data:
           return "Unable to fetch data."
           
       # Process data and return formatted result
       return formatted_result
   ```

4. **Server Execution**:
   ```python
   if __name__ == "__main__":
       mcp.run()
   ```

## Key Insights for eRegulations MCP Server

1. The FastMCP class automatically generates tool definitions from Python type hints and docstrings
2. Tools are implemented as async functions with the `@mcp.tool()` decorator
3. Helper functions can be used for common operations like API requests and data formatting
4. Error handling is important for robust tool execution
5. The server can be run with a simple `mcp.run()` call

This structure will be useful for designing our eRegulations MCP server architecture, where we'll need to implement tools for querying the eRegulations API and formatting the responses for LLM consumption.
