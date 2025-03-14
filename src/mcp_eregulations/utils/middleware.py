"""
Middleware and monitoring functionality for MCP server.
"""
import logging
import time
from functools import wraps
from typing import Optional, Dict, Callable, Any

from prometheus_client import Counter, Gauge, Histogram
from mcp.server.fastmcp import Context
from mcp import types

from mcp_eregulations.config.settings import settings
from mcp_eregulations.utils.auth import auth_manager

# Configure logging
logger = logging.getLogger(__name__)

# Define metrics
ACTIVE_CLIENTS = Gauge(
    "mcp_active_clients",
    "Number of currently connected MCP clients",
    ["transport"]
)

RESOURCE_REQUESTS = Counter(
    "mcp_resource_requests_total",
    "Total number of resource requests",
    ["resource_type", "status"]
)

TOOL_EXECUTIONS = Counter(
    "mcp_tool_executions_total",
    "Total number of tool executions",
    ["tool_name", "status"]
)

PROMPT_USAGE = Counter(
    "mcp_prompt_usage_total",
    "Total number of prompt usages",
    ["prompt_name"]
)

REQUEST_DURATION = Histogram(
    "mcp_request_duration_seconds",
    "Time spent processing requests",
    ["type", "name"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

SUBSCRIPTION_COUNT = Gauge(
    "mcp_active_subscriptions",
    "Number of active resource subscriptions",
    ["pattern"]
)

COMPLETION_LATENCY = Histogram(
    "mcp_completion_latency_seconds",
    "Time spent generating completions",
    ["argument_type"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)

ERROR_COUNT = Counter(
    "mcp_errors_total",
    "Total number of errors",
    ["type", "code"]
)


class MetricsMiddleware:
    """Middleware for collecting MCP metrics."""

    def __init__(self):
        """Initialize metrics state."""
        self.start_times = {}
    
    async def on_connect(
        self,
        client_id: str,
        capabilities: Optional[types.ClientCapabilities],
        ctx: Context
    ) -> None:
        """Handle client connection."""
        transport = capabilities.transport if capabilities else "unknown"
        ACTIVE_CLIENTS.labels(transport=transport).inc()
        logger.info(f"Client connected: {client_id} using {transport}")
    
    async def on_disconnect(
        self,
        client_id: str,
        ctx: Context
    ) -> None:
        """Handle client disconnection."""
        if hasattr(ctx.request_context, "transport"):
            ACTIVE_CLIENTS.labels(
                transport=ctx.request_context.transport
            ).dec()
        logger.info(f"Client disconnected: {client_id}")
    
    async def pre_resource(
        self,
        resource_id: str,
        ctx: Context
    ) -> None:
        """Pre-process resource request."""
        # Extract resource type from ID
        resource_type = resource_id.split("://")[0] if "://" in resource_id else "unknown"
        
        # Store start time
        req_id = id(ctx)
        self.start_times[req_id] = time.time()
        
        # Update metrics
        RESOURCE_REQUESTS.labels(
            resource_type=resource_type,
            status="started"
        ).inc()
    
    async def post_resource(
        self,
        resource_id: str,
        result: Optional[str],
        error: Optional[Exception],
        ctx: Context
    ) -> None:
        """Post-process resource request."""
        resource_type = resource_id.split("://")[0] if "://" in resource_id else "unknown"
        req_id = id(ctx)
        
        if req_id in self.start_times:
            duration = time.time() - self.start_times[req_id]
            REQUEST_DURATION.labels(
                type="resource",
                name=resource_type
            ).observe(duration)
            del self.start_times[req_id]
        
        status = "error" if error else "success"
        RESOURCE_REQUESTS.labels(
            resource_type=resource_type,
            status=status
        ).inc()
        
        if error:
            error_type = type(error).__name__
            error_code = getattr(error, "code", "unknown")
            ERROR_COUNT.labels(
                type=error_type,
                code=error_code
            ).inc()
    
    async def pre_tool(
        self,
        tool_name: str,
        ctx: Context
    ) -> None:
        """Pre-process tool execution."""
        req_id = id(ctx)
        self.start_times[req_id] = time.time()
        TOOL_EXECUTIONS.labels(
            tool_name=tool_name,
            status="started"
        ).inc()
    
    async def post_tool(
        self,
        tool_name: str,
        result: Optional[str],
        error: Optional[Exception],
        ctx: Context
    ) -> None:
        """Post-process tool execution."""
        req_id = id(ctx)
        
        if req_id in self.start_times:
            duration = time.time() - self.start_times[req_id]
            REQUEST_DURATION.labels(
                type="tool",
                name=tool_name
            ).observe(duration)
            del self.start_times[req_id]
        
        status = "error" if error else "success"
        TOOL_EXECUTIONS.labels(
            tool_name=tool_name,
            status=status
        ).inc()
        
        if error:
            error_type = type(error).__name__
            error_code = getattr(error, "code", "unknown")
            ERROR_COUNT.labels(
                type=error_type,
                code=error_code
            ).inc()
    
    async def on_prompt_used(
        self,
        prompt_name: str,
        ctx: Context
    ) -> None:
        """Handle prompt usage."""
        PROMPT_USAGE.labels(prompt_name=prompt_name).inc()
    
    async def on_subscription_change(
        self,
        pattern: str,
        count: int,
        ctx: Context
    ) -> None:
        """Handle subscription count changes."""
        SUBSCRIPTION_COUNT.labels(pattern=pattern).set(count)
    
    async def on_completion_generated(
        self,
        argument_type: str,
        duration: float,
        ctx: Context
    ) -> None:
        """Handle completion generation."""
        COMPLETION_LATENCY.labels(argument_type=argument_type).observe(duration)


# Create global middleware instance
metrics_middleware = MetricsMiddleware()

def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for MCP tools.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function that requires authentication
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract authentication information from context
        # In a real implementation, this would come from the MCP request context
        # For now, we'll use a simplified approach
        
        # Check if API key is provided in the request
        api_key = kwargs.pop("api_key", None)
        
        if not api_key:
            return "Authentication required. Please provide a valid API key."
        
        # Verify the API key
        result = auth_manager.verify_api_key(api_key)
        
        if not result["success"]:
            return f"Authentication failed: {result['message']}"
        
        # Authentication successful, proceed with the function call
        return await func(*args, **kwargs)
    
    return wrapper

def require_admin(func: Callable) -> Callable:
    """
    Decorator to require admin privileges for MCP tools.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function that requires admin privileges
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract authentication information from context
        api_key = kwargs.pop("api_key", None)
        
        if not api_key:
            return "Authentication required. Please provide a valid API key."
        
        # Verify the API key
        result = auth_manager.verify_api_key(api_key)
        
        if not result["success"]:
            return f"Authentication failed: {result['message']}"
        
        # Check if the user has admin privileges
        # In a real implementation, this would check against a list of admin users
        # For now, we'll use a simplified approach
        username = result["username"]
        
        # Placeholder for admin check
        is_admin = username == "admin"  # This should be replaced with a proper check
        
        if not is_admin:
            return "Admin privileges required for this operation."
        
        # Authentication and authorization successful, proceed with the function call
        return await func(*args, **kwargs)
    
    return wrapper

def log_access(func: Callable) -> Callable:
    """
    Decorator to log access to MCP tools.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function that logs access
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract authentication information from context
        api_key = kwargs.get("api_key")
        
        if api_key:
            result = auth_manager.verify_api_key(api_key)
            username = result.get("username", "unknown") if result.get("success") else "unknown"
        else:
            username = "anonymous"
        
        # Log the access
        logger.info(f"Access to {func.__name__} by {username}")
        
        # Proceed with the function call
        return await func(*args, **kwargs)
    
    return wrapper
