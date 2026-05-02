"""
WebSocket Server for Real-Time Updates
=======================================

WebSocket server for real-time scan progress, notifications, and updates.

Author: PromptOps Team
Date: 2026-04-30
Phase: 2 - Real-Time Updates
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set, List
import json
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Supports:
    - Multiple concurrent connections
    - Broadcast to all clients
    - Targeted messages to specific clients
    - Connection tracking
    """

    def __init__(self):
        # Active connections by connection ID
        self.active_connections: Dict[str, WebSocket] = {}

        # Subscriptions: scan_id -> set of connection IDs
        self.scan_subscriptions: Dict[str, Set[str]] = {}

        logger.info("WebSocket ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id} (total: {len(self.active_connections)})")

        # Send welcome message
        await self.send_message(connection_id, {
            "type": "connection",
            "status": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id} (remaining: {len(self.active_connections)})")

        # Remove from all subscriptions
        for scan_id, subscribers in list(self.scan_subscriptions.items()):
            if connection_id in subscribers:
                subscribers.remove(connection_id)
                if not subscribers:
                    del self.scan_subscriptions[scan_id]

    async def send_message(self, connection_id: str, message: dict):
        """Send message to specific connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []

        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {connection_id}: {e}")
                disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)

    def subscribe_to_scan(self, connection_id: str, scan_id: str):
        """Subscribe connection to scan updates."""
        if scan_id not in self.scan_subscriptions:
            self.scan_subscriptions[scan_id] = set()

        self.scan_subscriptions[scan_id].add(connection_id)
        logger.info(f"Connection {connection_id} subscribed to scan {scan_id}")

    def unsubscribe_from_scan(self, connection_id: str, scan_id: str):
        """Unsubscribe connection from scan updates."""
        if scan_id in self.scan_subscriptions:
            self.scan_subscriptions[scan_id].discard(connection_id)
            logger.info(f"Connection {connection_id} unsubscribed from scan {scan_id}")

    async def send_scan_update(self, scan_id: str, update: dict):
        """Send update to all connections subscribed to this scan."""
        if scan_id not in self.scan_subscriptions:
            return

        message = {
            "type": "scan_update",
            "scan_id": scan_id,
            "timestamp": datetime.utcnow().isoformat(),
            **update
        }

        subscribers = self.scan_subscriptions[scan_id].copy()
        disconnected = []

        for connection_id in subscribers:
            if connection_id in self.active_connections:
                try:
                    websocket = self.active_connections[connection_id]
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send scan update to {connection_id}: {e}")
                    disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)

    async def send_notification(self, notification: dict):
        """Send notification to all connected clients."""
        message = {
            "type": "notification",
            "timestamp": datetime.utcnow().isoformat(),
            **notification
        }
        await self.broadcast(message)

    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "active_connections": len(self.active_connections),
            "active_subscriptions": len(self.scan_subscriptions),
            "subscriptions_detail": {
                scan_id: len(subscribers)
                for scan_id, subscribers in self.scan_subscriptions.items()
            }
        }


# Global connection manager instance
manager = ConnectionManager()


# ============================================================================
# WebSocket Endpoint
# ============================================================================

async def websocket_endpoint(websocket: WebSocket, connection_id: str):
    """
    WebSocket endpoint for real-time updates.

    Usage from client:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/your-connection-id');

    // Subscribe to scan updates
    ws.send(JSON.stringify({
        action: 'subscribe',
        scan_id: 'scan_20260430_123456'
    }));

    // Receive updates
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received:', data);
    };
    ```
    """
    await manager.connect(websocket, connection_id)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get('action')

                if action == 'subscribe':
                    # Subscribe to scan updates
                    scan_id = message.get('scan_id')
                    if scan_id:
                        manager.subscribe_to_scan(connection_id, scan_id)
                        await manager.send_message(connection_id, {
                            "type": "subscribed",
                            "scan_id": scan_id,
                            "message": f"Subscribed to scan {scan_id}"
                        })
                    else:
                        await manager.send_message(connection_id, {
                            "type": "error",
                            "message": "scan_id required for subscription"
                        })

                elif action == 'unsubscribe':
                    # Unsubscribe from scan updates
                    scan_id = message.get('scan_id')
                    if scan_id:
                        manager.unsubscribe_from_scan(connection_id, scan_id)
                        await manager.send_message(connection_id, {
                            "type": "unsubscribed",
                            "scan_id": scan_id,
                            "message": f"Unsubscribed from scan {scan_id}"
                        })

                elif action == 'ping':
                    # Heartbeat / keep-alive
                    await manager.send_message(connection_id, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif action == 'get_stats':
                    # Get connection statistics
                    stats = manager.get_stats()
                    await manager.send_message(connection_id, {
                        "type": "stats",
                        **stats
                    })

                else:
                    await manager.send_message(connection_id, {
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })

            except json.JSONDecodeError:
                await manager.send_message(connection_id, {
                    "type": "error",
                    "message": "Invalid JSON"
                })

    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        manager.disconnect(connection_id)


# ============================================================================
# Helper Functions for Sending Updates
# ============================================================================

async def send_scan_progress(scan_id: str, progress: int, status: str, resources_found: int = 0):
    """Send scan progress update to subscribed clients."""
    await manager.send_scan_update(scan_id, {
        "progress": progress,
        "status": status,
        "resources_found": resources_found
    })


async def send_scan_complete(scan_id: str, resources_found: int, duration_seconds: float):
    """Send scan completion notification."""
    await manager.send_scan_update(scan_id, {
        "progress": 100,
        "status": "completed",
        "resources_found": resources_found,
        "duration_seconds": duration_seconds
    })


async def send_scan_error(scan_id: str, error: str):
    """Send scan error notification."""
    await manager.send_scan_update(scan_id, {
        "status": "failed",
        "error": error
    })


async def send_notification(title: str, message: str, level: str = "info"):
    """Send notification to all connected clients."""
    await manager.send_notification({
        "title": title,
        "message": message,
        "level": level  # info, success, warning, error
    })


# Test function
if __name__ == "__main__":
    print("=" * 60)
    print("  WebSocket Server Test")
    print("=" * 60)
    print("\nConnection Manager initialized")
    print(f"Active connections: {len(manager.active_connections)}")
    print(f"Active subscriptions: {len(manager.scan_subscriptions)}")
    print("\nTo test:")
    print("1. Start FastAPI server with WebSocket route")
    print("2. Connect from browser:")
    print("   const ws = new WebSocket('ws://localhost:8000/ws/test-123');")
    print("3. Subscribe to scan:")
    print("   ws.send(JSON.stringify({action: 'subscribe', scan_id: 'scan_123'}));")
    print("4. Send test update:")
    print("   await send_scan_progress('scan_123', 50, 'running', 10)")
    print("=" * 60)
