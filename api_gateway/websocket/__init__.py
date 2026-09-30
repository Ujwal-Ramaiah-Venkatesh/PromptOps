"""
WebSocket Module for Real-Time Updates
=======================================

Phase 7, Week 1: WebSocket Real-Time Updates
Provides real-time communication between backend and frontend.

Features:
- Real-time deployment progress
- Live log streaming
- Instant drift alerts
- Real-time metric updates

Author: PromptOps Team - Q3 2026
Date: June 22, 2026
"""

from .ws_server import router as websocket_router
from .connection_manager import ConnectionManager
from .event_emitter import EventEmitter

__all__ = ['websocket_router', 'ConnectionManager', 'EventEmitter']
