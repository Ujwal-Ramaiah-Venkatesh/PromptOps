"""
WebSocket Server
================

FastAPI WebSocket endpoint for real-time communication.

Endpoints:
- GET /ws: WebSocket connection endpoint
- GET /api/v1/websocket/stats: Connection statistics
- POST /api/v1/websocket/broadcast: Broadcast message to users

Author: PromptOps Team - Q3 2026
Date: June 22, 2026
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import logging
import json

from .connection_manager import connection_manager
from .event_emitter import event_emitter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/websocket", tags=["WebSocket"])


# ============================================================================
# WebSocket Connection Endpoint
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """
    WebSocket connection endpoint

    Query Parameters:
        token: JWT authentication token

    WebSocket Message Format:
        {
            "type": "event_type",
            "data": {},
            "timestamp": "ISO8601"
        }

    Event Types:
        - ping/pong: Heartbeat
        - deployment.progress: Deployment progress updates
        - deployment.log: Live log streaming
        - drift.detected: Infrastructure drift alerts
        - metrics.updated: Real-time metric updates
        - error: Error notifications
        - warning: Warning notifications
        - notification: General notifications
    """
    user_email = None

    try:
        # Connect and authenticate
        user_email = await connection_manager.connect(websocket, token)

        if not user_email:
            return  # Authentication failed, already handled in connect()

        # Keep connection alive and handle incoming messages
        while True:
            # Wait for incoming message
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                # Handle pong response
                if message_type == "pong":
                    logger.debug(f"Received pong from {user_email}")
                    continue

                # Handle other message types
                elif message_type == "subscribe":
                    # Subscribe to specific event types
                    event_types = message.get("events", [])
                    await websocket.send_json({
                        "type": "subscribed",
                        "events": event_types
                    })

                elif message_type == "unsubscribe":
                    # Unsubscribe from specific event types
                    event_types = message.get("events", [])
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "events": event_types
                    })

                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON message"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {user_email}")
    except Exception as e:
        logger.error(f"WebSocket error for {user_email}: {e}")
    finally:
        if user_email:
            await connection_manager.disconnect(websocket)


# ============================================================================
# WebSocket Management APIs
# ============================================================================

@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics

    Returns:
        {
            "total_connections": int,
            "active_users": int,
            "users": [{"email": str, "connections": int, "connected_at": str}]
        }
    """
    stats = connection_manager.get_stats()
    return JSONResponse(content=stats)


class BroadcastMessage(BaseModel):
    """Broadcast message model"""
    user_email: Optional[EmailStr] = None
    event_type: str
    data: Dict[str, Any]
    broadcast_to_all: bool = False


@router.post("/broadcast")
async def broadcast_message(message: BroadcastMessage):
    """
    Broadcast message to WebSocket clients

    Request Body:
        {
            "user_email": "user@example.com",  // Optional, required if not broadcast_to_all
            "event_type": "custom.event",
            "data": {},
            "broadcast_to_all": false
        }

    Response:
        {
            "success": true,
            "message": "Message broadcast successfully",
            "recipients": int
        }
    """
    try:
        if message.broadcast_to_all:
            # Broadcast to all connected users
            await event_emitter.emit_custom_event(
                user_email="",  # Will be ignored for broadcast_to_all
                event_type=message.event_type,
                data=message.data
            )
            recipients = connection_manager.get_connection_count()
        else:
            if not message.user_email:
                raise HTTPException(status_code=400, detail="user_email required when not broadcasting to all")

            # Broadcast to specific user
            await event_emitter.emit_custom_event(
                user_email=message.user_email,
                event_type=message.event_type,
                data=message.data
            )
            recipients = connection_manager.get_connection_count(message.user_email)

        return {
            "success": True,
            "message": "Message broadcast successfully",
            "recipients": recipients
        }

    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def get_connected_users():
    """
    Get list of currently connected users

    Returns:
        {
            "users": [
                {
                    "email": "user@example.com",
                    "connections": 2,
                    "connected_at": "2026-06-22T10:30:00Z"
                }
            ],
            "total_users": int,
            "total_connections": int
        }
    """
    stats = connection_manager.get_stats()
    return {
        "users": stats["users"],
        "total_users": stats["active_users"],
        "total_connections": stats["total_connections"]
    }


# ============================================================================
# Event Emission Helper APIs (for testing)
# ============================================================================

class TestDeploymentProgress(BaseModel):
    """Test deployment progress message"""
    user_email: EmailStr
    deployment_id: str
    status: str
    progress: int
    current_step: str
    total_steps: int = 6
    completed_steps: int = 0


@router.post("/test/deployment-progress")
async def test_deployment_progress(message: TestDeploymentProgress):
    """
    Test endpoint to emit deployment progress event

    Use this to test WebSocket real-time updates from the API
    """
    await event_emitter.emit_deployment_progress(
        user_email=message.user_email,
        deployment_id=message.deployment_id,
        status=message.status,
        progress=message.progress,
        current_step=message.current_step,
        total_steps=message.total_steps,
        completed_steps=message.completed_steps
    )

    return {
        "success": True,
        "message": "Deployment progress event emitted"
    }


class TestDriftAlert(BaseModel):
    """Test drift alert message"""
    user_email: EmailStr
    resource_type: str
    resource_id: str
    field: str
    expected_value: Any
    actual_value: Any
    severity: str = "medium"
    auto_fixable: bool = False


@router.post("/test/drift-alert")
async def test_drift_alert(message: TestDriftAlert):
    """
    Test endpoint to emit drift detection event

    Use this to test real-time drift alerts
    """
    await event_emitter.emit_drift_detected(
        user_email=message.user_email,
        resource_type=message.resource_type,
        resource_id=message.resource_id,
        field=message.field,
        expected_value=message.expected_value,
        actual_value=message.actual_value,
        severity=message.severity,
        auto_fixable=message.auto_fixable
    )

    return {
        "success": True,
        "message": "Drift alert event emitted"
    }
