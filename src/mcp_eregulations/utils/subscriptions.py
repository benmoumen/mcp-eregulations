"""
Resource subscription management for MCP server.
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from mcp import types
from mcp.server.fastmcp import Context, FastMCP

logger = logging.getLogger(__name__)


@dataclass
class ResourceSubscription:
    """A subscription to a resource pattern."""
    pattern: str
    client_id: str
    created_at: datetime
    last_notified: datetime
    context: Context


class SubscriptionManager:
    """Manages resource subscriptions and notifications."""
    
    def __init__(self):
        """Initialize the subscription manager."""
        self._subscriptions: Dict[str, Set[ResourceSubscription]] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, pattern: str, client_id: str, ctx: Context) -> None:
        """
        Subscribe a client to a resource pattern.
        
        Args:
            pattern: The resource pattern to subscribe to
            client_id: Unique identifier for the client
            ctx: The request context
        """
        async with self._lock:
            if pattern not in self._subscriptions:
                self._subscriptions[pattern] = set()
            
            # Remove any existing subscription for this client
            self._subscriptions[pattern] = {
                sub for sub in self._subscriptions[pattern]
                if sub.client_id != client_id
            }
            
            # Add new subscription
            now = datetime.now()
            subscription = ResourceSubscription(
                pattern=pattern,
                client_id=client_id,
                created_at=now,
                last_notified=now,
                context=ctx
            )
            self._subscriptions[pattern].add(subscription)
            
            logger.debug(f"Client {client_id} subscribed to {pattern}")
    
    async def unsubscribe(self, pattern: str, client_id: str) -> None:
        """
        Unsubscribe a client from a resource pattern.
        
        Args:
            pattern: The resource pattern to unsubscribe from
            client_id: Unique identifier for the client
        """
        async with self._lock:
            if pattern in self._subscriptions:
                self._subscriptions[pattern] = {
                    sub for sub in self._subscriptions[pattern]
                    if sub.client_id != client_id
                }
                
                # Remove empty pattern
                if not self._subscriptions[pattern]:
                    del self._subscriptions[pattern]
                
                logger.debug(f"Client {client_id} unsubscribed from {pattern}")
    
    async def unsubscribe_all(self, client_id: str) -> None:
        """
        Unsubscribe a client from all patterns.
        
        Args:
            client_id: Unique identifier for the client
        """
        async with self._lock:
            for pattern in list(self._subscriptions.keys()):
                self._subscriptions[pattern] = {
                    sub for sub in self._subscriptions[pattern]
                    if sub.client_id != client_id
                }
                
                # Remove empty pattern
                if not self._subscriptions[pattern]:
                    del self._subscriptions[pattern]
            
            logger.debug(f"Client {client_id} unsubscribed from all patterns")
    
    async def notify_update(
        self,
        resource_id: str,
        content: Any,
        mime_type: Optional[str] = None
    ) -> None:
        """
        Notify subscribers about a resource update.
        
        Args:
            resource_id: The ID of the updated resource
            content: The new content of the resource
            mime_type: Optional MIME type of the content
        """
        async with self._lock:
            now = datetime.now()
            
            # Find matching patterns
            for pattern, subs in self._subscriptions.items():
                if self._matches_pattern(resource_id, pattern):
                    # Notify each subscriber
                    for sub in subs:
                        try:
                            await sub.context.notify_resource_changed(
                                resource_id,
                                content,
                                mime_type=mime_type
                            )
                            sub.last_notified = now
                            logger.debug(
                                f"Notified client {sub.client_id} about update to {resource_id}"
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to notify client {sub.client_id}: {e}"
                            )
    
    def get_subscriptions(self, client_id: str) -> List[str]:
        """
        Get all patterns a client is subscribed to.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            List of subscribed patterns
        """
        return [
            pattern
            for pattern, subs in self._subscriptions.items()
            if any(sub.client_id == client_id for sub in subs)
        ]
    
    @staticmethod
    def _matches_pattern(resource_id: str, pattern: str) -> bool:
        """
        Check if a resource ID matches a subscription pattern.
        
        Args:
            resource_id: The resource ID to check
            pattern: The pattern to match against
            
        Returns:
            True if the resource ID matches the pattern
        """
        # Convert pattern to regex-style matching
        # Replace {param} with wildcard
        import re
        pattern_regex = (
            "^" + 
            re.escape(pattern)
            .replace("\\{[^}]+\\}", "[^/]+")
            .replace("\\*\\*", ".*")
            .replace("\\*", "[^/]*") + 
            "$"
        )
        return bool(re.match(pattern_regex, resource_id))


# Global subscription manager instance
subscription_manager = SubscriptionManager()


def register_subscription_handlers(mcp: FastMCP) -> None:
    """
    Register subscription-related handlers with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool()
    async def subscribe_resource(pattern: str, ctx: Context) -> str:
        """
        Subscribe to updates for resources matching a pattern.
        
        Args:
            pattern: The resource pattern to subscribe to
            ctx: The request context
            
        Returns:
            Confirmation message
        """
        client_id = ctx.request_context.client_id
        await subscription_manager.subscribe(pattern, client_id, ctx)
        return f"Subscribed to resource pattern: {pattern}"
    
    @mcp.tool()
    async def unsubscribe_resource(pattern: str, ctx: Context) -> str:
        """
        Unsubscribe from updates for resources matching a pattern.
        
        Args:
            pattern: The resource pattern to unsubscribe from
            ctx: The request context
            
        Returns:
            Confirmation message
        """
        client_id = ctx.request_context.client_id
        await subscription_manager.unsubscribe(pattern, client_id)
        return f"Unsubscribed from resource pattern: {pattern}"
    
    @mcp.tool()
    async def list_subscriptions(ctx: Context) -> str:
        """
        List all active subscriptions for the current client.
        
        Args:
            ctx: The request context
            
        Returns:
            List of subscribed patterns
        """
        client_id = ctx.request_context.client_id
        patterns = subscription_manager.get_subscriptions(client_id)
        
        if not patterns:
            return "No active subscriptions"
        
        return "Active subscriptions:\n" + "\n".join(
            f"- {pattern}" for pattern in patterns
        )