"""
Security Event Logging

Logs all security-relevant events for audit and monitoring
Week 13-15: SECURITY-006
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# File handler for security events
file_handler = logging.FileHandler('logs/security.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
security_logger.addHandler(file_handler)

# Console handler for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Only warnings and above to console
console_formatter = logging.Formatter('SECURITY: %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
security_logger.addHandler(console_handler)

# Prevent propagation to root logger
security_logger.propagate = False


def _format_event(event_type: str, details: Dict[str, Any]) -> str:
    """Format security event as JSON for structured logging"""
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        **details
    }
    return json.dumps(event)


# ============================================================================
# Authentication Events
# ============================================================================

def log_login_attempt(email: str, success: bool, ip: str, user_agent: Optional[str] = None):
    """
    Log login attempt (successful or failed)

    Args:
        email: User email attempting login
        success: Whether login was successful
        ip: IP address of request
        user_agent: Browser user agent string
    """
    level = logging.INFO if success else logging.WARNING
    event = _format_event("login_attempt", {
        "email": email,
        "success": success,
        "ip_address": ip,
        "user_agent": user_agent,
        "result": "SUCCESS" if success else "FAILED"
    })
    security_logger.log(level, event)


def log_logout(email: str, ip: str):
    """Log user logout"""
    event = _format_event("logout", {
        "email": email,
        "ip_address": ip
    })
    security_logger.info(event)


def log_registration(email: str, role: str, ip: str, success: bool):
    """Log user registration attempt"""
    level = logging.INFO if success else logging.WARNING
    event = _format_event("registration", {
        "email": email,
        "role": role,
        "ip_address": ip,
        "success": success
    })
    security_logger.log(level, event)


def log_token_validation_failed(token_prefix: str, reason: str, ip: str):
    """
    Log failed token validation

    Args:
        token_prefix: First 10 chars of token (for identification without exposing full token)
        reason: Reason for failure (expired, invalid, etc.)
        ip: IP address
    """
    event = _format_event("token_validation_failed", {
        "token_prefix": token_prefix,
        "reason": reason,
        "ip_address": ip
    })
    security_logger.warning(event)


# ============================================================================
# Authorization Events
# ============================================================================

def log_permission_denied(user: str, resource: str, action: str, reason: str, ip: str):
    """
    Log permission denial

    Args:
        user: User email
        resource: Resource being accessed (e.g., "/api/v1/execute")
        action: Action attempted (e.g., "deploy_production")
        reason: Why denied (e.g., "insufficient_role")
        ip: IP address
    """
    event = _format_event("permission_denied", {
        "user": user,
        "resource": resource,
        "action": action,
        "reason": reason,
        "ip_address": ip
    })
    security_logger.warning(event)


def log_environment_access_denied(user: str, role: str, environment: str, ip: str):
    """Log environment access denial (e.g., PM trying to access production)"""
    event = _format_event("environment_access_denied", {
        "user": user,
        "role": role,
        "environment": environment,
        "ip_address": ip
    })
    security_logger.warning(event)


# ============================================================================
# Operational Events
# ============================================================================

def log_deployment(user: str, role: str, service: str, environment: str,
                  version: str, deployment_id: str, ip: str):
    """
    Log deployment operation

    Args:
        user: User performing deployment
        role: User's role
        service: Service being deployed
        environment: Target environment (staging/production)
        version: Version being deployed
        deployment_id: Unique deployment identifier
        ip: IP address
    """
    level = logging.WARNING if environment == "production" else logging.INFO
    event = _format_event("deployment", {
        "user": user,
        "role": role,
        "service": service,
        "environment": environment,
        "version": version,
        "deployment_id": deployment_id,
        "ip_address": ip,
        "criticality": "HIGH" if environment == "production" else "MEDIUM"
    })
    security_logger.log(level, event)


def log_scaling_operation(user: str, service: str, environment: str,
                          from_count: int, to_count: int, ip: str):
    """Log service scaling operation"""
    event = _format_event("scaling_operation", {
        "user": user,
        "service": service,
        "environment": environment,
        "from_count": from_count,
        "to_count": to_count,
        "ip_address": ip
    })
    security_logger.info(event)


def log_approval_attempt(user: str, operation_id: str, approval_phrase: str,
                        success: bool, ip: str):
    """
    Log approval attempt for production operations

    Args:
        user: User attempting approval
        operation_id: Operation being approved
        approval_phrase: Phrase used for approval
        success: Whether approval was successful
        ip: IP address
    """
    level = logging.INFO if success else logging.WARNING
    event = _format_event("approval_attempt", {
        "user": user,
        "operation_id": operation_id,
        "approval_phrase": approval_phrase if not success else "***REDACTED***",
        "success": success,
        "ip_address": ip
    })
    security_logger.log(level, event)


# ============================================================================
# Rate Limiting Events
# ============================================================================

def log_rate_limit_exceeded(endpoint: str, ip: str, limit: str):
    """
    Log rate limit violation

    Args:
        endpoint: Endpoint that was rate limited
        ip: IP address
        limit: Rate limit that was exceeded (e.g., "5/minute")
    """
    event = _format_event("rate_limit_exceeded", {
        "endpoint": endpoint,
        "ip_address": ip,
        "limit": limit
    })
    security_logger.warning(event)


# ============================================================================
# Suspicious Activity
# ============================================================================

def log_suspicious_activity(activity_type: str, details: Dict[str, Any],
                           severity: str = "MEDIUM"):
    """
    Log suspicious activity

    Args:
        activity_type: Type of suspicious activity
        details: Additional details
        severity: LOW, MEDIUM, HIGH, CRITICAL
    """
    level_map = {
        "LOW": logging.INFO,
        "MEDIUM": logging.WARNING,
        "HIGH": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    level = level_map.get(severity, logging.WARNING)

    event = _format_event("suspicious_activity", {
        "activity_type": activity_type,
        "severity": severity,
        **details
    })
    security_logger.log(level, event)


def log_multiple_failed_logins(email: str, ip: str, attempt_count: int,
                               time_window_minutes: int):
    """Log multiple failed login attempts from same IP/email"""
    log_suspicious_activity(
        "multiple_failed_logins",
        {
            "email": email,
            "ip_address": ip,
            "attempt_count": attempt_count,
            "time_window_minutes": time_window_minutes
        },
        severity="HIGH"
    )


# ============================================================================
# User Management Events
# ============================================================================

def log_user_created(admin_user: str, new_user_email: str, role: str, ip: str):
    """Log user creation by admin"""
    event = _format_event("user_created", {
        "admin_user": admin_user,
        "new_user_email": new_user_email,
        "role": role,
        "ip_address": ip
    })
    security_logger.info(event)


def log_user_updated(admin_user: str, target_user: str, changes: Dict[str, Any], ip: str):
    """Log user update by admin"""
    event = _format_event("user_updated", {
        "admin_user": admin_user,
        "target_user": target_user,
        "changes": changes,
        "ip_address": ip
    })
    security_logger.info(event)


def log_user_deactivated(admin_user: str, target_user: str, reason: str, ip: str):
    """Log user deactivation"""
    event = _format_event("user_deactivated", {
        "admin_user": admin_user,
        "target_user": target_user,
        "reason": reason,
        "ip_address": ip
    })
    security_logger.warning(event)


# ============================================================================
# System Events
# ============================================================================

def log_secrets_access(user: str, secret_name: str, ip: str):
    """Log access to sensitive secrets"""
    event = _format_event("secrets_access", {
        "user": user,
        "secret_name": secret_name,
        "ip_address": ip
    })
    security_logger.info(event)


def log_config_change(user: str, config_key: str, old_value: str,
                     new_value: str, ip: str):
    """Log configuration changes"""
    event = _format_event("config_change", {
        "user": user,
        "config_key": config_key,
        "old_value": old_value,
        "new_value": new_value,
        "ip_address": ip
    })
    security_logger.warning(event)


def log_auto_execution(user: str, action_type: str, risk_level: str,
                       success: bool, ip: str):
    """
    Log auto-executed action.

    Args:
        user: User email who configured auto-execute
        action_type: Type of action (e.g., restart_pod)
        risk_level: Risk level (low/medium/high)
        success: Whether execution succeeded
        ip: IP address
    """
    level = logging.INFO if success else logging.ERROR
    event = _format_event("auto_execution", {
        "user": user,
        "action_type": action_type,
        "risk_level": risk_level,
        "success": success,
        "ip_address": ip,
        "result": "SUCCESS" if success else "FAILED",
        "approval_bypassed": True
    })
    security_logger.log(level, event)


# ============================================================================
# Utility Functions
# ============================================================================

def get_client_ip(request) -> str:
    """
    Extract client IP from request

    Handles proxies (X-Forwarded-For header)
    """
    if hasattr(request, 'headers'):
        # Check for proxy headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take first IP in chain (original client)
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

    # Fallback to direct connection IP
    if hasattr(request, 'client') and request.client:
        return request.client.host

    return "unknown"


def get_user_agent(request) -> Optional[str]:
    """Extract user agent from request"""
    if hasattr(request, 'headers'):
        return request.headers.get('User-Agent')
    return None


# ============================================================================
# CloudWatch Integration (Optional)
# ============================================================================

def setup_cloudwatch_logging(log_group: str, log_stream: str, region: str = 'us-east-1'):
    """
    Setup CloudWatch logging for production

    Args:
        log_group: CloudWatch log group name
        log_stream: CloudWatch log stream name
        region: AWS region
    """
    try:
        import boto3
        from botocore.exceptions import ClientError

        cloudwatch_logs = boto3.client('logs', region_name=region)

        # Create log group if doesn't exist
        try:
            cloudwatch_logs.create_log_group(logGroupName=log_group)
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                raise

        # Create log stream if doesn't exist
        try:
            cloudwatch_logs.create_log_stream(
                logGroupName=log_group,
                logStreamName=log_stream
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                raise

        # Add CloudWatch handler
        from watchtower import CloudWatchLogHandler
        cw_handler = CloudWatchLogHandler(
            log_group=log_group,
            stream_name=log_stream,
            boto3_client=cloudwatch_logs
        )
        cw_handler.setFormatter(file_formatter)
        security_logger.addHandler(cw_handler)

        security_logger.info("CloudWatch logging enabled")

    except ImportError:
        security_logger.warning("watchtower not installed - CloudWatch logging disabled")
    except Exception as e:
        security_logger.error(f"Failed to setup CloudWatch logging: {e}")
