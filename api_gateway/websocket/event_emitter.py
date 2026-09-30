"""
WebSocket Event Emitter
========================

Emits events to WebSocket clients for real-time updates.

Event Types:
- deployment.progress: Deployment progress updates
- deployment.log: Live log streaming
- drift.detected: Infrastructure drift alerts
- metrics.updated: Real-time metric updates
- error: Error notifications
- warning: Warning notifications

Author: PromptOps Team - Q3 2026
Date: June 22, 2026
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
from .connection_manager import connection_manager

logger = logging.getLogger(__name__)


class EventEmitter:
    """Emits events to WebSocket clients"""

    def __init__(self):
        self.connection_manager = connection_manager
        logger.info("EventEmitter initialized")

    async def emit_deployment_progress(
        self,
        user_email: str,
        deployment_id: str,
        status: str,
        progress: int,
        current_step: str,
        total_steps: int,
        completed_steps: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Emit deployment progress update

        Args:
            user_email: Target user
            deployment_id: Deployment identifier
            status: Current status (running, completed, failed)
            progress: Progress percentage (0-100)
            current_step: Current step description
            total_steps: Total number of steps
            completed_steps: Number of completed steps
            metadata: Additional metadata
        """
        message = {
            "type": "deployment.progress",
            "data": {
                "deployment_id": deployment_id,
                "status": status,
                "progress": progress,
                "current_step": current_step,
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "metadata": metadata or {}
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.connection_manager.broadcast_to_user(message, user_email)
        logger.info(f"Emitted deployment progress: {deployment_id} - {progress}%")

    async def emit_deployment_log(
        self,
        user_email: str,
        deployment_id: str,
        log_level: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Emit deployment log entry

        Args:
            user_email: Target user
            deployment_id: Deployment identifier
            log_level: Log level (info, warning, error, debug)
            message: Log message
            metadata: Additional metadata
        """
        log_message = {
            "type": "deployment.log",
            "data": {
                "deployment_id": deployment_id,
                "level": log_level,
                "message": message,
                "metadata": metadata or {}
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.connection_manager.broadcast_to_user(log_message, user_email)

    async def emit_drift_detected(
        self,
        user_email: str,
        resource_type: str,
        resource_id: str,
        field: str,
        expected_value: Any,
        actual_value: Any,
        severity: str,
        auto_fixable: bool
    ):
        """
        Emit infrastructure drift detection alert

        Args:
            user_email: Target user
            resource_type: Type of resource (ecs_service, rds_instance, etc.)
            resource_id: Resource identifier
            field: Field that drifted
            expected_value: Expected value
            actual_value: Actual detected value
            severity: Severity level (low, medium, high, critical)
            auto_fixable: Whether drift can be auto-fixed
        """
        message = {
            "type": "drift.detected",
            "data": {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "field": field,
                "expected_value": expected_value,
                "actual_value": actual_value,
                "severity": severity,
                "auto_fixable": auto_fixable
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.connection_manager.broadcast_to_user(message, user_email)
        logger.warning(f"Emitted drift alert: {resource_type}/{resource_id} - {field}")

    async def emit_metrics_update(
        self,
        user_email: str,
        metrics: Dict[str, Any]
    ):
        """
        Emit real-time metrics update

        Args:
            user_email: Target user
            metrics: Metrics dictionary
        """
        message = {
            "type": "metrics.updated",
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.connection_manager.broadcast_to_user(message, user_email)

    async def emit_error(
        self,
        user_email: str,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """
        Emit error notification

        Args:
            user_email: Target user
            error_type: Type of error
            error_message: Error message
            error_details: Additional error details
        """
        message = {
            "type": "error",
            "data": {
                "error_type": error_type,
                "message": error_message,
                "details": error_details or {}
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.connection_manager.broadcast_to_user(message, user_email)
        logger.error(f"Emitted error to {user_email}: {error_type} - {error_message}")

    async def emit_warning(
        self,
        user_email: str,
        warning_type: str,
        warning_message: str,
        warning_details: Optional[Dict[str, Any]] = None
    ):
        """
        Emit warning notification

        Args:
            user_email: Target user
            warning_type: Type of warning
            warning_message: Warning message
            warning_details: Additional warning details
        """
        message = {
            "type": "warning",
            "data": {
                "warning_type": warning_type,
                "message": warning_message,
                "details": warning_details or {}
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.connection_manager.broadcast_to_user(message, user_email)
        logger.warning(f"Emitted warning to {user_email}: {warning_type}")

    async def emit_notification(
        self,
        user_email: str,
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None
    ):
        """
        Emit general notification

        Args:
            user_email: Target user
            notification_type: Type of notification (success, info, warning, error)
            title: Notification title
            message: Notification message
            action_url: Optional URL for action button
        """
        notification = {
            "type": "notification",
            "data": {
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "action_url": action_url
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.connection_manager.broadcast_to_user(notification, user_email)

    async def emit_custom_event(
        self,
        user_email: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        Emit custom event

        Args:
            user_email: Target user
            event_type: Custom event type
            data: Event data
        """
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.connection_manager.broadcast_to_user(message, user_email)


# Global event emitter instance
event_emitter = EventEmitter()
