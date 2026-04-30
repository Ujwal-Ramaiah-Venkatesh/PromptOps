"""
Permission checking utilities

Environment-based and operation-based permissions
"""

from auth.models import User
from fastapi import HTTPException, status


def require_environment_access(environment: str, user: User) -> bool:
    """
    Check if user can access specific environment

    Permissions:
    - viewer: No deployment access
    - pm: staging only
    - engineer: staging + production
    - lead: all environments
    - admin: all environments

    Args:
        environment: Target environment (production, staging, development)
        user: User object

    Returns:
        True if user has access, False otherwise
    """
    environment = environment.lower()

    if user.role == "admin" or user.role == "lead":
        return True

    if environment == "production":
        return user.role in ["engineer", "lead", "admin"]

    if environment == "staging":
        return user.role in ["pm", "engineer", "lead", "admin"]

    if environment == "development":
        return user.role in ["pm", "engineer", "lead", "admin"]

    # Unknown environment
    return False


def check_environment_access(environment: str, user: User):
    """
    Check environment access and raise exception if denied

    Args:
        environment: Target environment
        user: User object

    Raises:
        HTTPException: 403 if access denied
    """
    if not require_environment_access(environment, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User role '{user.role}' cannot access '{environment}' environment"
        )


def can_approve_production(user: User) -> bool:
    """
    Check if user can approve production deployments

    Args:
        user: User object

    Returns:
        True if user can approve production deployments
    """
    return user.role in ["engineer", "lead", "admin"]


def can_manage_users(user: User) -> bool:
    """
    Check if user can manage other users

    Args:
        user: User object

    Returns:
        True if user can manage users
    """
    return user.role in ["lead", "admin"]


def can_view_audit_log(user: User) -> bool:
    """
    Check if user can view audit log

    Args:
        user: User object

    Returns:
        True if user can view audit log (all roles can view)
    """
    return True  # All authenticated users can view audit log


def can_execute_deployment(environment: str, user: User) -> bool:
    """
    Check if user can execute deployment to environment

    Args:
        environment: Target environment
        user: User object

    Returns:
        True if user can execute deployment
    """
    if user.role == "viewer":
        return False

    return require_environment_access(environment, user)


# Role descriptions for documentation
ROLE_DESCRIPTIONS = {
    "viewer": "Read-only access to audit trail and drift detection",
    "pm": "Product Manager - can deploy to staging, scale services, view all data",
    "engineer": "Engineer - can deploy to staging and production (with approval), all PM permissions",
    "lead": "Team Lead - can do everything including user management",
    "admin": "Administrator - full system access including configuration"
}


def get_role_permissions(role: str) -> dict:
    """
    Get permissions for a role

    Args:
        role: Role name

    Returns:
        Dictionary of permissions
    """
    base_permissions = {
        "view_audit": True,
        "view_drift": True,
        "deploy_staging": False,
        "deploy_production": False,
        "scale_services": False,
        "manage_users": False,
        "approve_production": False
    }

    if role == "viewer":
        return base_permissions

    if role == "pm":
        base_permissions.update({
            "deploy_staging": True,
            "scale_services": True
        })
        return base_permissions

    if role == "engineer":
        base_permissions.update({
            "deploy_staging": True,
            "deploy_production": True,
            "scale_services": True,
            "approve_production": True
        })
        return base_permissions

    if role in ["lead", "admin"]:
        return {k: True for k in base_permissions.keys()}

    return base_permissions
