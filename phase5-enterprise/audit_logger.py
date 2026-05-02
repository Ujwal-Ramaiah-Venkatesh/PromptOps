"""
Audit Logger Module
===================

Comprehensive audit logging for compliance and security
Phase 5B - Enterprise Features

Features:
- Tamper-proof logging with hash chains
- Multiple log types (actions, logins, data access, config changes)
- Suspicious activity detection
- Log integrity verification
- Full-text search

Author: PromptOps Team
Date: 2026-05-02
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import hashlib
import json
import uuid

logger = logging.getLogger(__name__)


class AuditSeverity:
    """Audit log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogger:
    """
    Comprehensive audit logging system.

    Features:
    - Tamper-proof hash chains
    - Multiple log types
    - Integrity verification
    - Search and analytics
    """

    def __init__(self, db_connection):
        """Initialize audit logger."""
        self.db = db_connection
        logger.info("AuditLogger initialized")

    async def log_action(
        self,
        tenant_id: str,
        user_id: Optional[str],
        user_email: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        status: str = 'success',
        severity: str = AuditSeverity.INFO,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        error_message: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a user action to the audit trail.

        Args:
            tenant_id: Tenant ID
            user_id: User who performed the action
            user_email: User's email
            action: Action performed (create, update, delete, etc.)
            resource_type: Type of resource affected
            resource_id: ID of resource
            resource_name: Name of resource
            old_values: Previous state (for updates)
            new_values: New state (for creates/updates)
            status: Action outcome (success, failure, error)
            severity: Log severity
            ip_address: Client IP address
            request_id: Request tracking ID
            error_message: Error message if failed
            additional_data: Extra metadata

        Returns:
            Audit log entry ID
        """
        try:
            # Use PostgreSQL function for audit logging
            query = """
                SELECT create_audit_log(
                    $1::uuid,  -- tenant_id
                    $2::uuid,  -- user_id
                    $3,        -- user_email
                    $4,        -- action
                    $5,        -- resource_type
                    $6,        -- resource_id
                    $7,        -- resource_name
                    $8::jsonb, -- old_values
                    $9::jsonb, -- new_values
                    $10,       -- status
                    $11,       -- severity
                    $12::inet, -- ip_address
                    $13::jsonb -- additional_data
                )
            """

            # Prepare values
            old_json = json.dumps(old_values) if old_values else None
            new_json = json.dumps(new_values) if new_values else None
            additional_json = json.dumps(additional_data or {})

            if request_id:
                additional_json = json.dumps({
                    **(additional_data or {}),
                    'request_id': request_id
                })

            if error_message:
                additional_json = json.dumps({
                    **(additional_data or {}),
                    'error_message': error_message
                })

            audit_id = await self.db.fetchval(
                query,
                tenant_id,
                user_id,
                user_email,
                action,
                resource_type,
                resource_id,
                resource_name,
                old_json,
                new_json,
                status,
                severity,
                ip_address,
                additional_json
            )

            return str(audit_id)

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise - audit logging should not break main functionality
            return ""

    async def log_login_attempt(
        self,
        tenant_id: Optional[str],
        email: str,
        user_id: Optional[str],
        success: bool,
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        mfa_required: bool = False,
        mfa_success: Optional[bool] = None
    ) -> str:
        """
        Log a login attempt.

        Args:
            tenant_id: Tenant ID
            email: Email address used
            user_id: User ID (if found)
            success: Whether login succeeded
            failure_reason: Reason for failure
            ip_address: Client IP
            user_agent: Browser user agent
            mfa_required: Whether MFA was required
            mfa_success: Whether MFA succeeded

        Returns:
            Login attempt ID
        """
        try:
            attempt_id = str(uuid.uuid4())

            query = """
                INSERT INTO login_attempts (
                    id, tenant_id, email, user_id,
                    success, failure_reason,
                    ip_address, user_agent,
                    mfa_required, mfa_success,
                    attempted_at
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6,
                    $7, $8,
                    $9, $10,
                    NOW()
                )
                RETURNING id
            """

            result = await self.db.fetchrow(
                query,
                attempt_id,
                tenant_id,
                email,
                user_id,
                success,
                failure_reason,
                ip_address,
                user_agent,
                mfa_required,
                mfa_success
            )

            # Also log to main audit trail
            if success:
                await self.log_action(
                    tenant_id=tenant_id or "",
                    user_id=user_id,
                    user_email=email,
                    action="login",
                    resource_type="session",
                    status="success",
                    severity=AuditSeverity.INFO,
                    ip_address=ip_address
                )
            else:
                await self.log_action(
                    tenant_id=tenant_id or "",
                    user_id=user_id,
                    user_email=email,
                    action="login_failed",
                    resource_type="session",
                    status="failure",
                    severity=AuditSeverity.WARNING,
                    ip_address=ip_address,
                    error_message=failure_reason
                )

            return str(result['id'])

        except Exception as e:
            logger.error(f"Failed to log login attempt: {e}")
            return ""

    async def log_data_access(
        self,
        tenant_id: str,
        user_id: str,
        user_email: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        record_count: Optional[int] = None,
        action: str = 'read',
        query_filters: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        query_duration_ms: Optional[int] = None
    ) -> str:
        """
        Log sensitive data access.

        Args:
            tenant_id: Tenant ID
            user_id: User who accessed data
            user_email: User's email
            resource_type: Type of data accessed
            resource_id: Specific resource ID
            record_count: Number of records accessed
            action: Action type (read, export, download)
            query_filters: Filters applied
            ip_address: Client IP
            query_duration_ms: Query execution time

        Returns:
            Data access log ID
        """
        try:
            access_id = str(uuid.uuid4())

            query = """
                INSERT INTO data_access_log (
                    id, tenant_id, user_id, user_email,
                    resource_type, resource_id, record_count,
                    action, query_filters,
                    ip_address, query_duration_ms,
                    accessed_at
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6, $7,
                    $8, $9,
                    $10, $11,
                    NOW()
                )
                RETURNING id
            """

            filters_json = json.dumps(query_filters) if query_filters else None

            result = await self.db.fetchrow(
                query,
                access_id,
                tenant_id,
                user_id,
                user_email,
                resource_type,
                resource_id,
                record_count,
                action,
                filters_json,
                ip_address,
                query_duration_ms
            )

            return str(result['id'])

        except Exception as e:
            logger.error(f"Failed to log data access: {e}")
            return ""

    async def log_config_change(
        self,
        tenant_id: str,
        user_id: str,
        user_email: str,
        config_type: str,
        config_key: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        change_reason: Optional[str] = None,
        requires_approval: bool = False
    ) -> str:
        """
        Log configuration change.

        Args:
            tenant_id: Tenant ID
            user_id: User who made change
            user_email: User's email
            config_type: Type of config (system, tenant, user)
            config_key: Configuration key
            old_value: Previous value
            new_value: New value
            change_reason: Reason for change
            requires_approval: Whether change needs approval

        Returns:
            Config change log ID
        """
        try:
            change_id = str(uuid.uuid4())

            query = """
                INSERT INTO config_changes_log (
                    id, tenant_id, user_id, user_email,
                    config_type, config_key,
                    old_value, new_value,
                    change_reason, requires_approval,
                    changed_at
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6,
                    $7, $8,
                    $9, $10,
                    NOW()
                )
                RETURNING id
            """

            result = await self.db.fetchrow(
                query,
                change_id,
                tenant_id,
                user_id,
                user_email,
                config_type,
                config_key,
                old_value,
                new_value,
                change_reason,
                requires_approval
            )

            # Also log to main audit trail
            await self.log_action(
                tenant_id=tenant_id,
                user_id=user_id,
                user_email=user_email,
                action="config_change",
                resource_type=config_type,
                resource_id=config_key,
                old_values={'value': old_value} if old_value else None,
                new_values={'value': new_value} if new_value else None,
                severity=AuditSeverity.WARNING if requires_approval else AuditSeverity.INFO
            )

            return str(result['id'])

        except Exception as e:
            logger.error(f"Failed to log config change: {e}")
            return ""

    async def search_audit_log(
        self,
        tenant_id: str,
        search_text: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Full-text search in audit logs.

        Args:
            tenant_id: Tenant ID
            search_text: Search query
            limit: Maximum results

        Returns:
            List of matching audit log entries
        """
        try:
            query = "SELECT * FROM search_audit_log($1, $2, $3)"

            results = await self.db.fetch(query, tenant_id, search_text, limit)

            logs = []
            for row in results:
                logs.append({
                    'id': str(row['id']),
                    'user_email': row['user_email'],
                    'action': row['action'],
                    'resource_type': row['resource_type'],
                    'resource_name': row['resource_name'],
                    'created_at': row['created_at'].isoformat(),
                    'rank': float(row['rank'])
                })

            return logs

        except Exception as e:
            logger.error(f"Audit log search failed: {e}")
            return []

    async def verify_integrity(self, tenant_id: str) -> Dict[str, Any]:
        """
        Verify audit log integrity (check hash chain).

        Args:
            tenant_id: Tenant ID

        Returns:
            Integrity check result
        """
        try:
            query = "SELECT * FROM verify_audit_log_integrity($1)"

            result = await self.db.fetchrow(query, tenant_id)

            return {
                'success': True,
                'is_valid': result['is_valid'],
                'total_records': result['total_records'],
                'invalid_records': result['invalid_records'],
                'first_invalid_id': str(result['first_invalid_id']) if result['first_invalid_id'] else None
            }

        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get user activity summary.

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Activity summary
        """
        try:
            query = "SELECT * FROM get_user_activity_summary($1, $2)"

            result = await self.db.fetchrow(query, user_id, days)

            return {
                'success': True,
                'total_actions': result['total_actions'],
                'successful_actions': result['successful_actions'],
                'failed_actions': result['failed_actions'],
                'most_common_action': result['most_common_action'],
                'last_activity': result['last_activity'].isoformat() if result['last_activity'] else None
            }

        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def detect_suspicious_activity(
        self,
        tenant_id: str
    ) -> List[Dict[str, Any]]:
        """
        Detect suspicious activity patterns.

        Returns:
            List of suspicious activities detected
        """
        try:
            query = "SELECT * FROM detect_suspicious_activity($1)"

            results = await self.db.fetch(query, tenant_id)

            activities = []
            for row in results:
                activities.append({
                    'user_id': str(row['user_id']) if row['user_id'] else None,
                    'user_email': row['user_email'],
                    'issue_type': row['issue_type'],
                    'issue_description': row['issue_description'],
                    'occurrences': row['occurrences'],
                    'last_occurrence': row['last_occurrence'].isoformat()
                })

            return activities

        except Exception as e:
            logger.error(f"Suspicious activity detection failed: {e}")
            return []

    async def get_audit_statistics(
        self,
        tenant_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get audit log statistics.

        Args:
            tenant_id: Tenant ID
            days: Number of days to analyze

        Returns:
            Statistics summary
        """
        try:
            query = """
                SELECT
                    COUNT(*) as total_events,
                    COUNT(*) FILTER (WHERE status = 'success') as successful_events,
                    COUNT(*) FILTER (WHERE status != 'success') as failed_events,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT resource_type) as unique_resource_types
                FROM audit_log
                WHERE tenant_id = $1
                AND created_at > NOW() - ($2 || ' days')::INTERVAL
            """

            result = await self.db.fetchrow(query, tenant_id, days)

            # Get top actions
            top_actions_query = """
                SELECT action, COUNT(*) as count
                FROM audit_log
                WHERE tenant_id = $1
                AND created_at > NOW() - ($2 || ' days')::INTERVAL
                GROUP BY action
                ORDER BY count DESC
                LIMIT 10
            """

            top_actions = await self.db.fetch(top_actions_query, tenant_id, days)

            return {
                'success': True,
                'period_days': days,
                'total_events': result['total_events'],
                'successful_events': result['successful_events'],
                'failed_events': result['failed_events'],
                'unique_users': result['unique_users'],
                'unique_resource_types': result['unique_resource_types'],
                'success_rate': (result['successful_events'] / result['total_events'] * 100) if result['total_events'] > 0 else 0,
                'top_actions': [
                    {'action': row['action'], 'count': row['count']}
                    for row in top_actions
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get audit statistics: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Context manager for automatic audit logging
class AuditContext:
    """Context manager for automatic audit logging."""

    def __init__(
        self,
        audit_logger: AuditLogger,
        tenant_id: str,
        user_id: str,
        user_email: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None
    ):
        self.audit_logger = audit_logger
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_email = user_email
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.old_values = None
        self.new_values = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Log action on context exit
        status = 'success' if exc_type is None else 'error'
        severity = AuditSeverity.INFO if exc_type is None else AuditSeverity.ERROR
        error_message = str(exc_val) if exc_val else None

        await self.audit_logger.log_action(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            user_email=self.user_email,
            action=self.action,
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            old_values=self.old_values,
            new_values=self.new_values,
            status=status,
            severity=severity,
            error_message=error_message
        )

    def set_values(self, old_values: Optional[Dict] = None, new_values: Optional[Dict] = None):
        """Set before/after values."""
        self.old_values = old_values
        self.new_values = new_values


# Example usage
if __name__ == "__main__":
    print("Audit Logger Module")
    print("=" * 60)
    print("\nFeatures:")
    print("  - Tamper-proof hash chains")
    print("  - Multiple log types (actions, logins, data access, config)")
    print("  - Full-text search")
    print("  - Integrity verification")
    print("  - Suspicious activity detection")
    print("  - User activity analytics")
    print("\nCompliance:")
    print("  - SOC 2 ready")
    print("  - ISO 27001 compatible")
    print("  - GDPR audit trail")
    print("\nCost: $0 (PostgreSQL + local storage)")
