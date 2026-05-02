"""
Tenant Management Module
=========================

Multi-tenant organization management for PromptOps
Phase 5B - Enterprise Features

Features:
- Tenant CRUD operations
- Tenant isolation
- Subscription management
- Resource limit enforcement

Author: PromptOps Team
Date: 2026-05-02
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class TenantPlan(str, Enum):
    """Subscription plans."""
    FREE = "free"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class TenantLimits:
    """Resource limits by plan."""

    LIMITS = {
        TenantPlan.FREE: {
            "max_users": 5,
            "max_cloud_accounts": 3,
            "max_resources_tracked": 1000,
            "max_budgets": 5,
            "max_api_calls_per_hour": 100,
            "ml_features_enabled": False,
            "sso_enabled": False,
            "custom_branding": False,
            "support_level": "community"
        },
        TenantPlan.STANDARD: {
            "max_users": 25,
            "max_cloud_accounts": 10,
            "max_resources_tracked": 10000,
            "max_budgets": 50,
            "max_api_calls_per_hour": 1000,
            "ml_features_enabled": True,
            "sso_enabled": True,
            "custom_branding": False,
            "support_level": "email"
        },
        TenantPlan.ENTERPRISE: {
            "max_users": -1,  # Unlimited
            "max_cloud_accounts": -1,
            "max_resources_tracked": -1,
            "max_budgets": -1,
            "max_api_calls_per_hour": 10000,
            "ml_features_enabled": True,
            "sso_enabled": True,
            "custom_branding": True,
            "support_level": "priority"
        }
    }

    @classmethod
    def get_limits(cls, plan: TenantPlan) -> Dict[str, Any]:
        """Get limits for a plan."""
        return cls.LIMITS.get(plan, cls.LIMITS[TenantPlan.FREE])

    @classmethod
    def check_limit(cls, plan: TenantPlan, limit_name: str, current_value: int) -> bool:
        """Check if current value exceeds limit."""
        limits = cls.get_limits(plan)
        max_value = limits.get(limit_name, 0)

        if max_value == -1:  # Unlimited
            return True

        return current_value < max_value


class TenantManager:
    """
    Manages multi-tenant operations.

    Features:
    - Tenant lifecycle management
    - Resource limit enforcement
    - Tenant isolation
    - Settings management
    """

    def __init__(self, db_connection):
        """Initialize tenant manager."""
        self.db = db_connection
        logger.info("TenantManager initialized")

    async def create_tenant(
        self,
        name: str,
        slug: str,
        plan: TenantPlan = TenantPlan.FREE,
        created_by_user_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new tenant.

        Args:
            name: Tenant name
            slug: URL-safe identifier
            plan: Subscription plan
            created_by_user_id: User creating the tenant
            settings: Initial settings

        Returns:
            Created tenant details
        """
        try:
            # Validate slug format
            if not self._is_valid_slug(slug):
                return {
                    'success': False,
                    'error': 'Invalid slug format (alphanumeric and hyphens only)'
                }

            # Check if slug already exists
            existing = await self._get_tenant_by_slug(slug)
            if existing:
                return {
                    'success': False,
                    'error': f'Tenant with slug "{slug}" already exists'
                }

            # Get limits for plan
            limits = TenantLimits.get_limits(plan)

            # Create tenant
            tenant_id = str(uuid.uuid4())

            query = """
                INSERT INTO tenants (
                    id, name, slug, plan, status,
                    max_users, max_cloud_accounts, max_resources_tracked,
                    settings, created_by, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8,
                    $9, $10, NOW()
                )
                RETURNING id, name, slug, plan, status, created_at
            """

            result = await self.db.fetchrow(
                query,
                tenant_id,
                name,
                slug,
                plan.value,
                TenantStatus.ACTIVE.value,
                limits['max_users'],
                limits['max_cloud_accounts'],
                limits['max_resources_tracked'],
                settings or {},
                created_by_user_id
            )

            logger.info(f"Created tenant: {slug} (plan: {plan.value})")

            return {
                'success': True,
                'tenant': {
                    'id': str(result['id']),
                    'name': result['name'],
                    'slug': result['slug'],
                    'plan': result['plan'],
                    'status': result['status'],
                    'limits': limits,
                    'created_at': result['created_at'].isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID."""
        try:
            query = """
                SELECT id, name, slug, description, plan, status,
                       max_users, max_cloud_accounts, max_resources_tracked,
                       settings, created_at, updated_at
                FROM tenants
                WHERE id = $1
            """

            result = await self.db.fetchrow(query, tenant_id)

            if not result:
                return None

            return self._format_tenant(result)

        except Exception as e:
            logger.error(f"Failed to get tenant: {e}")
            return None

    async def get_tenant_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get tenant by slug."""
        result = await self._get_tenant_by_slug(slug)
        if result:
            return self._format_tenant(result)
        return None

    async def update_tenant(
        self,
        tenant_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update tenant details.

        Args:
            tenant_id: Tenant ID
            updates: Fields to update

        Returns:
            Update result
        """
        try:
            allowed_fields = ['name', 'description', 'plan', 'status', 'settings']

            # Build update query
            update_fields = []
            values = []
            param_count = 1

            for field, value in updates.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ${param_count}")
                    values.append(value)
                    param_count += 1

            if not update_fields:
                return {
                    'success': False,
                    'error': 'No valid fields to update'
                }

            # Add updated_at
            update_fields.append(f"updated_at = ${param_count}")
            values.append(datetime.utcnow())
            param_count += 1

            # Add tenant_id for WHERE clause
            values.append(tenant_id)

            query = f"""
                UPDATE tenants
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}
                RETURNING id, name, slug, plan, status
            """

            result = await self.db.fetchrow(query, *values)

            if not result:
                return {
                    'success': False,
                    'error': 'Tenant not found'
                }

            logger.info(f"Updated tenant: {result['slug']}")

            return {
                'success': True,
                'tenant': self._format_tenant(result)
            }

        except Exception as e:
            logger.error(f"Failed to update tenant: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def suspend_tenant(
        self,
        tenant_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """Suspend a tenant."""
        try:
            query = """
                UPDATE tenants
                SET status = $1,
                    suspended_at = NOW(),
                    updated_at = NOW(),
                    metadata = jsonb_set(
                        COALESCE(metadata, '{}'::jsonb),
                        '{suspension_reason}',
                        to_jsonb($2::text)
                    )
                WHERE id = $3
                RETURNING id, slug, status
            """

            result = await self.db.fetchrow(
                query,
                TenantStatus.SUSPENDED.value,
                reason,
                tenant_id
            )

            if not result:
                return {
                    'success': False,
                    'error': 'Tenant not found'
                }

            logger.warning(f"Suspended tenant: {result['slug']} (reason: {reason})")

            return {
                'success': True,
                'tenant_id': str(result['id']),
                'status': result['status']
            }

        except Exception as e:
            logger.error(f"Failed to suspend tenant: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def check_resource_limit(
        self,
        tenant_id: str,
        resource_type: str
    ) -> Dict[str, Any]:
        """
        Check if tenant has reached resource limit.

        Args:
            tenant_id: Tenant ID
            resource_type: Type of resource (users, cloud_accounts, etc.)

        Returns:
            Limit check result
        """
        try:
            tenant = await self.get_tenant(tenant_id)

            if not tenant:
                return {
                    'success': False,
                    'error': 'Tenant not found'
                }

            # Get current usage
            current_usage = await self._get_resource_count(tenant_id, resource_type)

            # Get limit for resource type
            limit_field = f"max_{resource_type}"
            max_allowed = tenant.get(limit_field, 0)

            if max_allowed == -1:  # Unlimited
                return {
                    'success': True,
                    'within_limit': True,
                    'current': current_usage,
                    'limit': 'unlimited'
                }

            within_limit = current_usage < max_allowed

            return {
                'success': True,
                'within_limit': within_limit,
                'current': current_usage,
                'limit': max_allowed,
                'remaining': max(0, max_allowed - current_usage)
            }

        except Exception as e:
            logger.error(f"Failed to check resource limit: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant resource usage statistics."""
        try:
            tenant = await self.get_tenant(tenant_id)

            if not tenant:
                return {
                    'success': False,
                    'error': 'Tenant not found'
                }

            # Get usage for all resource types
            usage = {}
            resource_types = ['users', 'cloud_accounts', 'resources', 'budgets']

            for resource_type in resource_types:
                count = await self._get_resource_count(tenant_id, resource_type)
                limit_field = f"max_{resource_type}"
                max_allowed = tenant.get(limit_field, 0)

                usage[resource_type] = {
                    'current': count,
                    'limit': 'unlimited' if max_allowed == -1 else max_allowed,
                    'percentage': 0 if max_allowed == -1 else (count / max_allowed * 100) if max_allowed > 0 else 0
                }

            return {
                'success': True,
                'tenant_id': tenant_id,
                'plan': tenant['plan'],
                'usage': usage
            }

        except Exception as e:
            logger.error(f"Failed to get tenant usage: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        plan: Optional[TenantPlan] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List tenants with filtering."""
        try:
            where_clauses = []
            params = []
            param_count = 1

            if status:
                where_clauses.append(f"status = ${param_count}")
                params.append(status.value)
                param_count += 1

            if plan:
                where_clauses.append(f"plan = ${param_count}")
                params.append(plan.value)
                param_count += 1

            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # Get total count
            count_query = f"SELECT COUNT(*) FROM tenants{where_sql}"
            total = await self.db.fetchval(count_query, *params)

            # Get tenants
            params.extend([limit, offset])
            query = f"""
                SELECT id, name, slug, plan, status, created_at
                FROM tenants
                {where_sql}
                ORDER BY created_at DESC
                LIMIT ${param_count} OFFSET ${param_count + 1}
            """

            results = await self.db.fetch(query, *params)

            tenants = [self._format_tenant(row) for row in results]

            return {
                'success': True,
                'tenants': tenants,
                'total': total,
                'limit': limit,
                'offset': offset
            }

        except Exception as e:
            logger.error(f"Failed to list tenants: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # Helper methods

    def _is_valid_slug(self, slug: str) -> bool:
        """Validate slug format."""
        import re
        return bool(re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', slug))

    async def _get_tenant_by_slug(self, slug: str):
        """Get tenant by slug (internal)."""
        query = "SELECT * FROM tenants WHERE slug = $1"
        return await self.db.fetchrow(query, slug)

    async def _get_resource_count(self, tenant_id: str, resource_type: str) -> int:
        """Get count of resources for a tenant."""
        table_map = {
            'users': 'users',
            'cloud_accounts': 'cloud_accounts',
            'resources': 'resources',
            'budgets': 'budgets'
        }

        table_name = table_map.get(resource_type)
        if not table_name:
            return 0

        try:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE tenant_id = $1"
            return await self.db.fetchval(query, tenant_id)
        except:
            return 0

    def _format_tenant(self, row) -> Dict[str, Any]:
        """Format tenant database row."""
        return {
            'id': str(row['id']),
            'name': row['name'],
            'slug': row['slug'],
            'description': row.get('description'),
            'plan': row['plan'],
            'status': row['status'],
            'max_users': row.get('max_users'),
            'max_cloud_accounts': row.get('max_cloud_accounts'),
            'max_resources_tracked': row.get('max_resources_tracked'),
            'settings': row.get('settings', {}),
            'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
            'updated_at': row['updated_at'].isoformat() if row.get('updated_at') else None
        }


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        """Test tenant manager."""
        # Mock database connection
        class MockDB:
            async def fetchrow(self, query, *args):
                return {
                    'id': uuid.uuid4(),
                    'name': 'Test Org',
                    'slug': 'test-org',
                    'plan': 'free',
                    'status': 'active',
                    'max_users': 5,
                    'max_cloud_accounts': 3,
                    'max_resources_tracked': 1000,
                    'settings': {},
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }

        manager = TenantManager(MockDB())

        # Test create tenant
        result = await manager.create_tenant(
            name="Test Organization",
            slug="test-org",
            plan=TenantPlan.FREE
        )

        print("Create Tenant Result:")
        print(result)

    # Run test
    asyncio.run(test())
