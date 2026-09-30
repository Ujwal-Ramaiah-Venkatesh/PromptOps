"""
WebSocket Connection Manager
=============================

Manages WebSocket connections, authentication, and message broadcasting.

Features:
- Connection pooling and tracking
- JWT authentication for WebSocket
- Heartbeat mechanism (ping/pong every 30s)
- Automatic cleanup of dead connections
- User-specific message routing

Author: PromptOps Team - Q3 2026
Date: June 22, 2026
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Optional
import asyncio
import logging
import json
from datetime import datetime
import jwt
from jwt.exceptions import InvalidTokenError

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages all active WebSocket connections"""

    def __init__(self):
        # Active connections: {user_email: {websocket_instances}}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Connection metadata: {websocket: {user, connected_at, last_ping}}
        self.connection_metadata: Dict[WebSocket, Dict] = {}

        # Heartbeat task references
        self.heartbeat_tasks: Dict[WebSocket, asyncio.Task] = {}

        # JWT secret (should match auth module)
        self.jwt_secret = "your-secret-key-change-in-production"  # TODO: Load from env

        logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, token: Optional[str] = None) -> Optional[str]:
        """
        Accept WebSocket connection with JWT authentication

        Args:
            websocket: WebSocket connection
            token: JWT authentication token

        Returns:
            user_email if authenticated, None if failed
        """
        await websocket.accept()

        # Authenticate user
        user_email = await self._authenticate(token)

        if not user_email:
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed",
                "timestamp": datetime.utcnow().isoformat()
            })
            await websocket.close(code=4001)  # Unauthorized
            return None

        # Add to active connections
        if user_email not in self.active_connections:
            self.active_connections[user_email] = set()

        self.active_connections[user_email].add(websocket)

        # Store metadata
        self.connection_metadata[websocket] = {
            "user": user_email,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }

        # Start heartbeat for this connection
        heartbeat_task = asyncio.create_task(self._heartbeat(websocket))
        self.heartbeat_tasks[websocket] = heartbeat_task

        logger.info(f"WebSocket connected: {user_email} (Total: {len(self.active_connections[user_email])})")

        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connection established",
            "user": user_email,
            "timestamp": datetime.utcnow().isoformat()
        })

        return user_email

    async def disconnect(self, websocket: WebSocket):
        """
        Disconnect WebSocket and cleanup

        Args:
            websocket: WebSocket connection to disconnect
        """
        # Get user from metadata
        metadata = self.connection_metadata.get(websocket)
        if not metadata:
            return

        user_email = metadata["user"]

        # Cancel heartbeat task
        if websocket in self.heartbeat_tasks:
            self.heartbeat_tasks[websocket].cancel()
            del self.heartbeat_tasks[websocket]

        # Remove from active connections
        if user_email in self.active_connections:
            self.active_connections[user_email].discard(websocket)

            # Remove user entry if no more connections
            if not self.active_connections[user_email]:
                del self.active_connections[user_email]

        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        logger.info(f"WebSocket disconnected: {user_email}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send message to a specific WebSocket connection

        Args:
            message: Message dictionary to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)

    async def broadcast_to_user(self, message: dict, user_email: str):
        """
        Broadcast message to all connections of a specific user

        Args:
            message: Message dictionary to broadcast
            user_email: Target user email
        """
        if user_email not in self.active_connections:
            logger.warning(f"No active connections for user: {user_email}")
            return

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        # Send to all user's connections
        dead_connections = []
        for connection in self.active_connections[user_email]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {user_email}: {e}")
                dead_connections.append(connection)

        # Cleanup dead connections
        for connection in dead_connections:
            await self.disconnect(connection)

    async def broadcast_to_all(self, message: dict):
        """
        Broadcast message to all connected users

        Args:
            message: Message dictionary to broadcast
        """
        # Add timestamp
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        # Broadcast to all users
        for user_email in list(self.active_connections.keys()):
            await self.broadcast_to_user(message, user_email)

    async def _authenticate(self, token: Optional[str]) -> Optional[str]:
        """
        Authenticate WebSocket connection using JWT token

        Args:
            token: JWT token string

        Returns:
            user_email if valid, None if invalid
        """
        if not token:
            logger.warning("No token provided for WebSocket authentication")
            return None

        try:
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            user_email = payload.get("sub")

            if not user_email:
                logger.warning("Token missing 'sub' claim")
                return None

            return user_email

        except InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def _heartbeat(self, websocket: WebSocket):
        """
        Send periodic ping to keep connection alive

        Args:
            websocket: WebSocket connection to ping
        """
        try:
            while True:
                # Wait 30 seconds
                await asyncio.sleep(30)

                # Send ping
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Update last ping time
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_ping"] = datetime.utcnow()

        except asyncio.CancelledError:
            # Task cancelled (connection closed)
            pass
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            await self.disconnect(websocket)

    def get_active_users(self) -> list:
        """Get list of currently connected users"""
        return list(self.active_connections.keys())

    def get_connection_count(self, user_email: Optional[str] = None) -> int:
        """
        Get count of active connections

        Args:
            user_email: If provided, count for specific user. Otherwise total.

        Returns:
            Connection count
        """
        if user_email:
            return len(self.active_connections.get(user_email, set()))
        else:
            return sum(len(connections) for connections in self.active_connections.values())

    def get_stats(self) -> dict:
        """Get WebSocket statistics"""
        return {
            "total_connections": self.get_connection_count(),
            "active_users": len(self.active_connections),
            "users": [
                {
                    "email": email,
                    "connections": len(connections),
                    "connected_at": min(
                        self.connection_metadata[ws]["connected_at"]
                        for ws in connections
                        if ws in self.connection_metadata
                    ).isoformat()
                }
                for email, connections in self.active_connections.items()
            ]
        }


# Global connection manager instance
connection_manager = ConnectionManager()
