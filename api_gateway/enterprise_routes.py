"""
Enterprise Features API Routes
===============================

API endpoints for Phase 5B enterprise features:
- Tenant management
- RBAC
- User management
- Audit logs

Author: PromptOps Team
Date: 2026-05-02
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase5-enterprise'))

from tenant_manager import TenantManager, TenantPlan, TenantStatus
from rbac import RBACManager, PermissionDenied
from audit_logger import AuditLogger, AuditSeverity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enterprise", tags=["enterprise"])


# Request/Response Models

class TenantCreateRequest(BaseModel):
    """Request model for creating a tenant."""
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, regex=r'^[a-z0-9-]+$')
    plan: TenantPlan = Field(default=TenantPlan.FREE)
    description: Optional[str] = None


class TenantUpdateRequest(BaseModel):
    """Request model for updating a tenant."""
    name: Optional[str] = None
    description: Optional[str] = None
    plan: Optional[TenantPlan] = None
    status: Optional[TenantStatus] = None


class RoleCreateRequest(BaseModel):
    """Request model for creating a role."""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    permissions: List[str] = Field(..., min_items=1)


class RoleAssignRequest(BaseModel):
    """Request model for assigning a role to a user."""
    user_id: str
    role_id: str
    expires_at: Optional[datetime] = None


class UserCreateRequest(BaseModel):
    """Request model for creating a user."""
    email: EmailStr
    first_name: str
    last_name: str
    password: Optional[str] = None
    role_ids: List[str] = Field(default_factory=list)


class AuditSearchRequest(BaseModel):
    """Request model for searching audit logs."""
    query: str
    limit: int = Field(default=100, ge=1, le=1000)


# Dependency to get current user (mock for now)
async def get_current_user():
    """Get current authenticated user."""
    # This should be replaced with actual JWT validation
    return {
        'id': 'user-123',
        'email': 'admin@example.com',
        'tenant_id': 'tenant-456'
    }


# Dependency to get database connection (mock for now)
async def get_db():
    """Get database connection."""
    # This should return actual database connection
    class MockDB:
        async def fetchrow(self, query, *args):
            return None
        async def fetch(self, query, *args):
            return []
        async def fetchval(self, query, *args):
            return None
        async def execute(self, query, *args):
            pass
    return MockDB()


# ===========================================================================
# Tenant Management Routes
# ===========================================================================

@router.post("/tenants", response_model=Dict[str, Any])
async def create_tenant(
    request: TenantCreateRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new tenant.

    Requires: admin:tenant permission
    """
    try:
        manager = TenantManager(db)

        result = await manager.create_tenant(
            name=request.name,
            slug=request.slug,
            plan=request.plan,
            created_by_user_id=current_user['id']
        )

        if result['success']:
            # Log audit trail
            audit_logger = AuditLogger(db)
            await audit_logger.log_action(
                tenant_id=current_user['tenant_id'],
                user_id=current_user['id'],
                user_email=current_user['email'],
                action='create',
                resource_type='tenant',
                resource_id=result['tenant']['id'],
                resource_name=request.name,
                new_values={'slug': request.slug, 'plan': request.plan.value},
                severity=AuditSeverity.INFO
            )

        return result

    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}", response_model=Dict[str, Any])
async def get_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Get tenant details."""
    try:
        manager = TenantManager(db)
        tenant = await manager.get_tenant(tenant_id)

        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        return {
            'success': True,
            'tenant': tenant
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants", response_model=Dict[str, Any])
async def list_tenants(
    status: Optional[TenantStatus] = None,
    plan: Optional[TenantPlan] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """List all tenants (admin only)."""
    try:
        manager = TenantManager(db)
        result = await manager.list_tenants(
            status=status,
            plan=plan,
            limit=limit,
            offset=offset
        )

        return result

    except Exception as e:
        logger.error(f"Failed to list tenants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tenants/{tenant_id}", response_model=Dict[str, Any])
async def update_tenant(
    tenant_id: str,
    request: TenantUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Update tenant details."""
    try:
        manager = TenantManager(db)

        updates = request.dict(exclude_none=True)
        result = await manager.update_tenant(tenant_id, updates)

        if result['success']:
            # Log audit trail
            audit_logger = AuditLogger(db)
            await audit_logger.log_action(
                tenant_id=current_user['tenant_id'],
                user_id=current_user['id'],
                user_email=current_user['email'],
                action='update',
                resource_type='tenant',
                resource_id=tenant_id,
                new_values=updates,
                severity=AuditSeverity.INFO
            )

        return result

    except Exception as e:
        logger.error(f"Failed to update tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/usage", response_model=Dict[str, Any])
async def get_tenant_usage(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Get tenant resource usage statistics."""
    try:
        manager = TenantManager(db)
        usage = await manager.get_tenant_usage(tenant_id)

        return usage

    except Exception as e:
        logger.error(f"Failed to get tenant usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================================
# Role & Permission Management Routes
# ===========================================================================

@router.post("/roles", response_model=Dict[str, Any])
async def create_role(
    request: RoleCreateRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new role."""
    try:
        rbac = RBACManager(db)

        result = await rbac.create_role(
            tenant_id=current_user['tenant_id'],
            name=request.name,
            permissions=request.permissions,
            description=request.description
        )

        if result['success']:
            # Log audit trail
            audit_logger = AuditLogger(db)
            await audit_logger.log_action(
                tenant_id=current_user['tenant_id'],
                user_id=current_user['id'],
                user_email=current_user['email'],
                action='create',
                resource_type='role',
                resource_id=result['role']['id'],
                resource_name=request.name,
                new_values={'permissions': request.permissions},
                severity=AuditSeverity.INFO
            )

        return result

    except Exception as e:
        logger.error(f"Failed to create role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roles", response_model=List[Dict[str, Any]])
async def list_roles(
    include_system: bool = True,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all roles for current tenant."""
    try:
        rbac = RBACManager(db)
        roles = await rbac.list_roles(
            tenant_id=current_user['tenant_id'],
            include_system=include_system
        )

        return roles

    except Exception as e:
        logger.error(f"Failed to list roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/permissions", response_model=List[Dict[str, Any]])
async def list_permissions(
    category: Optional[str] = None,
    db = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all available permissions."""
    try:
        rbac = RBACManager(db)
        permissions = await rbac.list_permissions(category=category)

        return permissions

    except Exception as e:
        logger.error(f"Failed to list permissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roles/assign", response_model=Dict[str, Any])
async def assign_role(
    request: RoleAssignRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Assign a role to a user."""
    try:
        rbac = RBACManager(db)

        result = await rbac.assign_role(
            user_id=request.user_id,
            role_id=request.role_id,
            assigned_by=current_user['id'],
            expires_at=request.expires_at
        )

        if result['success']:
            # Log audit trail
            audit_logger = AuditLogger(db)
            await audit_logger.log_action(
                tenant_id=current_user['tenant_id'],
                user_id=current_user['id'],
                user_email=current_user['email'],
                action='assign_role',
                resource_type='user_role',
                resource_id=request.user_id,
                new_values={'role_id': request.role_id},
                severity=AuditSeverity.INFO
            )

        return result

    except Exception as e:
        logger.error(f"Failed to assign role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/roles/{user_id}/{role_id}", response_model=Dict[str, Any])
async def revoke_role(
    user_id: str,
    role_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Revoke a role from a user."""
    try:
        rbac = RBACManager(db)
        result = await rbac.revoke_role(user_id, role_id)

        if result['success']:
            # Log audit trail
            audit_logger = AuditLogger(db)
            await audit_logger.log_action(
                tenant_id=current_user['tenant_id'],
                user_id=current_user['id'],
                user_email=current_user['email'],
                action='revoke_role',
                resource_type='user_role',
                resource_id=user_id,
                old_values={'role_id': role_id},
                severity=AuditSeverity.INFO
            )

        return result

    except Exception as e:
        logger.error(f"Failed to revoke role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/permissions", response_model=List[str])
async def get_user_permissions(
    user_id: str,
    db = Depends(get_db)
) -> List[str]:
    """Get all permissions for a user."""
    try:
        rbac = RBACManager(db)
        permissions = await rbac.get_user_permissions(user_id)

        return list(permissions)

    except Exception as e:
        logger.error(f"Failed to get user permissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/roles", response_model=List[Dict[str, Any]])
async def get_user_roles(
    user_id: str,
    db = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all roles assigned to a user."""
    try:
        rbac = RBACManager(db)
        roles = await rbac.get_user_roles(user_id)

        return roles

    except Exception as e:
        logger.error(f"Failed to get user roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================================
# Audit Log Routes
# ===========================================================================

@router.post("/audit/search", response_model=List[Dict[str, Any]])
async def search_audit_logs(
    request: AuditSearchRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Search audit logs using full-text search."""
    try:
        audit_logger = AuditLogger(db)
        results = await audit_logger.search_audit_log(
            tenant_id=current_user['tenant_id'],
            search_text=request.query,
            limit=request.limit
        )

        return results

    except Exception as e:
        logger.error(f"Failed to search audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/verify-integrity", response_model=Dict[str, Any])
async def verify_audit_integrity(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Verify audit log integrity using hash chains."""
    try:
        audit_logger = AuditLogger(db)
        result = await audit_logger.verify_integrity(current_user['tenant_id'])

        return result

    except Exception as e:
        logger.error(f"Failed to verify audit integrity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/user/{user_id}/activity", response_model=Dict[str, Any])
async def get_user_activity(
    user_id: str,
    days: int = 30,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Get user activity summary."""
    try:
        audit_logger = AuditLogger(db)
        result = await audit_logger.get_user_activity(user_id, days)

        return result

    except Exception as e:
        logger.error(f"Failed to get user activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/suspicious-activity", response_model=List[Dict[str, Any]])
async def detect_suspicious_activity(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Detect suspicious activity patterns."""
    try:
        audit_logger = AuditLogger(db)
        activities = await audit_logger.detect_suspicious_activity(
            current_user['tenant_id']
        )

        return activities

    except Exception as e:
        logger.error(f"Failed to detect suspicious activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/statistics", response_model=Dict[str, Any])
async def get_audit_statistics(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Get audit log statistics."""
    try:
        audit_logger = AuditLogger(db)
        result = await audit_logger.get_audit_statistics(
            tenant_id=current_user['tenant_id'],
            days=days
        )

        return result

    except Exception as e:
        logger.error(f"Failed to get audit statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================================
# Health Check
# ===========================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for enterprise features."""
    return {
        'status': 'healthy',
        'service': 'enterprise-features',
        'features': {
            'multi_tenancy': True,
            'rbac': True,
            'sso': True,
            'audit_logging': True
        },
        'timestamp': datetime.utcnow().isoformat()
    }
