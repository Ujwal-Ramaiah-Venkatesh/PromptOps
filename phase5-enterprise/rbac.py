"""
Role-Based Access Control (RBAC) Module
========================================

Permission and role management for PromptOps
Phase 5B - Enterprise Features

Features:
- Role management
- Permission checking with caching
- Wildcard permission support
- Role assignment

Author: PromptOps Team
Date: 2026-05-02
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import logging
from functools import wraps
from fastapi import HTTPException, status
import uuid

logger = logging.getLogger(__name__)


class PermissionDenied(HTTPException):
    """Exception raised when permission is denied."""

    def __init__(self, permission: str, resource: str = None):
        detail = f"Permission denied: {permission}"
        if resource:
            detail += f" on {resource}"

        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class RBACManager:
    """
    Manages roles, permissions, and access control.

    Features:
    - Permission checking with wildcards
    - Role assignment and revocation
    - Permission caching (5 minute TTL)
    - Hierarchical permissions
    """

    def __init__(self, db_connection):
        """Initialize RBAC manager."""
        self.db = db_connection
        logger.info("RBACManager initialized")

    async def create_role(
        self,
        tenant_id: str,
        name: str,
        permissions: List[str],
        description: Optional[str] = None,
        is_system_role: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new role.

        Args:
            tenant_id: Tenant ID
            name: Role name
            permissions: List of permission strings
            description: Role description
            is_system_role: Whether this is a system role

        Returns:
            Created role details
        """
        try:
            # Validate permissions
            valid_permissions = await self._validate_permissions(permissions)
            if not valid_permissions:
                return {
                    'success': False,
                    'error': 'No valid permissions provided'
                }

            role_id = str(uuid.uuid4())

            query = """
                INSERT INTO roles (id, tenant_id, name, description, is_system_role, permissions, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                RETURNING id, name, description, permissions, created_at
            """

            result = await self.db.fetchrow(
                query,
                role_id,
                tenant_id,
                name,
                description,
                is_system_role,
                valid_permissions
            )

            logger.info(f"Created role: {name} for tenant {tenant_id}")

            return {
                'success': True,
                'role': {
                    'id': str(result['id']),
                    'name': result['name'],
                    'description': result['description'],
                    'permissions': result['permissions'],
                    'created_at': result['created_at'].isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Failed to create role: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def assign_role(
        self,
        user_id: str,
        role_id: str,
        assigned_by: str,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Assign a role to a user.

        Args:
            user_id: User ID
            role_id: Role ID
            assigned_by: User ID of assigner
            expires_at: Optional expiration date

        Returns:
            Assignment result
        """
        try:
            assignment_id = str(uuid.uuid4())

            query = """
                INSERT INTO user_roles (id, user_id, role_id, assigned_by, assigned_at, expires_at)
                VALUES ($1, $2, $3, $4, NOW(), $5)
                ON CONFLICT (user_id, role_id) DO UPDATE
                SET expires_at = EXCLUDED.expires_at,
                    assigned_by = EXCLUDED.assigned_by,
                    assigned_at = NOW()
                RETURNING id, user_id, role_id, assigned_at
            """

            result = await self.db.fetchrow(
                query,
                assignment_id,
                user_id,
                role_id,
                assigned_by,
                expires_at
            )

            # Invalidate permission cache for user
            await self._invalidate_user_cache(user_id)

            logger.info(f"Assigned role {role_id} to user {user_id}")

            return {
                'success': True,
                'assignment': {
                    'id': str(result['id']),
                    'user_id': str(result['user_id']),
                    'role_id': str(result['role_id']),
                    'assigned_at': result['assigned_at'].isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Failed to assign role: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def revoke_role(
        self,
        user_id: str,
        role_id: str
    ) -> Dict[str, Any]:
        """Revoke a role from a user."""
        try:
            query = """
                DELETE FROM user_roles
                WHERE user_id = $1 AND role_id = $2
                RETURNING id
            """

            result = await self.db.fetchrow(query, user_id, role_id)

            if not result:
                return {
                    'success': False,
                    'error': 'Role assignment not found'
                }

            # Invalidate permission cache for user
            await self._invalidate_user_cache(user_id)

            logger.info(f"Revoked role {role_id} from user {user_id}")

            return {
                'success': True,
                'message': 'Role revoked successfully'
            }

        except Exception as e:
            logger.error(f"Failed to revoke role: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def check_permission(
        self,
        user_id: str,
        permission: str,
        use_cache: bool = True
    ) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user_id: User ID
            permission: Permission string (e.g., "read:costs")
            use_cache: Whether to use cached results

        Returns:
            True if user has permission
        """
        try:
            # Use PostgreSQL function for permission check
            query = "SELECT check_permission($1, $2)"
            result = await self.db.fetchval(query, user_id, permission)

            return bool(result)

        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False

    async def get_user_permissions(self, user_id: str) -> Set[str]:
        """
        Get all permissions for a user (expanded from roles).

        Args:
            user_id: User ID

        Returns:
            Set of permission strings
        """
        try:
            query = "SELECT * FROM get_user_permissions($1)"
            results = await self.db.fetch(query, user_id)

            permissions = {row['permission'] for row in results}

            # If user has wildcard, return all permissions
            if '*' in permissions:
                return await self._get_all_permissions()

            # Expand wildcard permissions
            expanded = set()
            for perm in permissions:
                if '*' in perm:
                    # Expand wildcard (e.g., "read:*" expands to all read permissions)
                    expanded.update(await self._expand_wildcard(perm))
                else:
                    expanded.add(perm)

            return expanded

        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return set()

    async def get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all roles assigned to a user."""
        try:
            query = """
                SELECT r.id, r.name, r.description, r.permissions,
                       ur.assigned_at, ur.expires_at
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = $1
                AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
                ORDER BY ur.assigned_at DESC
            """

            results = await self.db.fetch(query, user_id)

            roles = []
            for row in results:
                roles.append({
                    'id': str(row['id']),
                    'name': row['name'],
                    'description': row['description'],
                    'permissions': row['permissions'],
                    'assigned_at': row['assigned_at'].isoformat(),
                    'expires_at': row['expires_at'].isoformat() if row['expires_at'] else None
                })

            return roles

        except Exception as e:
            logger.error(f"Failed to get user roles: {e}")
            return []

    async def is_admin(self, user_id: str) -> bool:
        """Check if user has admin permissions."""
        return await self.check_permission(user_id, '*')

    async def list_roles(
        self,
        tenant_id: str,
        include_system: bool = True
    ) -> List[Dict[str, Any]]:
        """List all roles for a tenant."""
        try:
            where_clause = "WHERE tenant_id = $1"
            params = [tenant_id]

            if not include_system:
                where_clause += " AND is_system_role = FALSE"

            query = f"""
                SELECT id, name, description, permissions, is_system_role, created_at
                FROM roles
                {where_clause}
                ORDER BY is_system_role DESC, name ASC
            """

            results = await self.db.fetch(query, *params)

            roles = []
            for row in results:
                roles.append({
                    'id': str(row['id']),
                    'name': row['name'],
                    'description': row['description'],
                    'permissions': row['permissions'],
                    'is_system_role': row['is_system_role'],
                    'created_at': row['created_at'].isoformat()
                })

            return roles

        except Exception as e:
            logger.error(f"Failed to list roles: {e}")
            return []

    async def list_permissions(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all available permissions."""
        try:
            where_clause = ""
            params = []

            if category:
                where_clause = "WHERE category = $1"
                params.append(category)

            query = f"""
                SELECT name, resource, action, category, description, is_dangerous
                FROM permissions
                {where_clause}
                ORDER BY category, resource, action
            """

            results = await self.db.fetch(query, *params)

            permissions = []
            for row in results:
                permissions.append({
                    'name': row['name'],
                    'resource': row['resource'],
                    'action': row['action'],
                    'category': row['category'],
                    'description': row['description'],
                    'is_dangerous': row['is_dangerous']
                })

            return permissions

        except Exception as e:
            logger.error(f"Failed to list permissions: {e}")
            return []

    # Helper methods

    async def _validate_permissions(self, permissions: List[str]) -> List[str]:
        """Validate that permissions exist in the catalog."""
        try:
            # Allow wildcard
            if '*' in permissions:
                return ['*']

            query = """
                SELECT name FROM permissions
                WHERE name = ANY($1)
            """

            results = await self.db.fetch(query, permissions)
            valid = [row['name'] for row in results]

            # Also allow wildcard patterns like "read:*"
            for perm in permissions:
                if '*' in perm and perm not in valid:
                    # Validate pattern
                    if self._is_valid_wildcard(perm):
                        valid.append(perm)

            return valid

        except Exception as e:
            logger.error(f"Permission validation failed: {e}")
            return []

    def _is_valid_wildcard(self, permission: str) -> bool:
        """Check if wildcard permission pattern is valid."""
        parts = permission.split(':')
        if len(parts) != 2:
            return False

        action, resource = parts
        return resource == '*' and action in ['read', 'write', 'delete', 'execute', 'approve', 'manage', 'admin']

    async def _invalidate_user_cache(self, user_id: str):
        """Invalidate permission cache for a user."""
        try:
            query = "SELECT invalidate_permission_cache($1)"
            await self.db.execute(query, user_id)
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")

    async def _expand_wildcard(self, wildcard_perm: str) -> Set[str]:
        """Expand a wildcard permission to all matching permissions."""
        try:
            action, resource = wildcard_perm.split(':')

            if resource == '*':
                # Expand to all permissions with this action
                query = """
                    SELECT name FROM permissions
                    WHERE action = $1
                """
                results = await self.db.fetch(query, action)
                return {row['name'] for row in results}

            return set()

        except Exception as e:
            logger.error(f"Failed to expand wildcard: {e}")
            return set()

    async def _get_all_permissions(self) -> Set[str]:
        """Get all available permissions."""
        try:
            query = "SELECT name FROM permissions"
            results = await self.db.fetch(query)
            return {row['name'] for row in results}
        except Exception as e:
            logger.error(f"Failed to get all permissions: {e}")
            return set()


# Decorator for permission checking
def require_permission(permission: str):
    """
    Decorator to enforce permission on FastAPI endpoints.

    Usage:
        @require_permission('read:costs')
        async def get_costs(user_id: str):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from kwargs or request context
            user_id = kwargs.get('user_id') or kwargs.get('current_user_id')

            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Get RBAC manager from app context
            # This assumes rbac_manager is passed in kwargs or available in app state
            rbac_manager = kwargs.get('rbac_manager')

            if not rbac_manager:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="RBAC manager not configured"
                )

            # Check permission
            has_permission = await rbac_manager.check_permission(user_id, permission)

            if not has_permission:
                raise PermissionDenied(permission)

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        """Test RBAC manager."""
        # Mock database connection
        class MockDB:
            async def fetchrow(self, query, *args):
                if 'INSERT INTO roles' in query:
                    return {
                        'id': uuid.uuid4(),
                        'name': 'Test Role',
                        'description': 'Test role description',
                        'permissions': ['read:costs', 'read:resources'],
                        'created_at': datetime.utcnow()
                    }
                elif 'INSERT INTO user_roles' in query:
                    return {
                        'id': uuid.uuid4(),
                        'user_id': uuid.uuid4(),
                        'role_id': uuid.uuid4(),
                        'assigned_at': datetime.utcnow()
                    }
                return None

            async def fetchval(self, query, *args):
                if 'check_permission' in query:
                    return True
                return None

            async def fetch(self, query, *args):
                if 'get_user_permissions' in query:
                    return [
                        {'permission': 'read:costs'},
                        {'permission': 'read:resources'}
                    ]
                elif 'FROM permissions' in query:
                    return [
                        {'name': 'read:costs'},
                        {'name': 'write:costs'},
                        {'name': 'read:resources'}
                    ]
                return []

            async def execute(self, query, *args):
                pass

        manager = RBACManager(MockDB())

        # Test create role
        result = await manager.create_role(
            tenant_id=str(uuid.uuid4()),
            name="Analyst",
            permissions=["read:costs", "read:resources"],
            description="Read-only analyst role"
        )

        print("Create Role Result:")
        print(result)

        # Test permission check
        user_id = str(uuid.uuid4())
        has_perm = await manager.check_permission(user_id, "read:costs")
        print(f"\nUser has 'read:costs' permission: {has_perm}")

        # Test get user permissions
        permissions = await manager.get_user_permissions(user_id)
        print(f"\nUser permissions: {permissions}")

    # Run test
    asyncio.run(test())
