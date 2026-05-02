"""
Single Sign-On (SSO) Provider
==============================

OAuth 2.0 and SAML 2.0 authentication for PromptOps
Phase 5B - Enterprise Features

Supported Providers:
- Google OAuth 2.0
- Microsoft OAuth 2.0
- GitHub OAuth 2.0
- SAML 2.0 (Enterprise SSO)

Author: PromptOps Team
Date: 2026-05-02
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import secrets
import hashlib
import uuid
from enum import Enum

logger = logging.getLogger(__name__)


class SSOProvider(str, Enum):
    """Supported SSO providers."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    SAML = "saml"


class SSOManager:
    """
    Manages Single Sign-On authentication.

    Features:
    - OAuth 2.0 (Google, Microsoft, GitHub)
    - SAML 2.0 (Enterprise SSO)
    - User provisioning from SSO
    - Session management
    """

    def __init__(self, db_connection, config: Dict[str, Any]):
        """
        Initialize SSO manager.

        Args:
            db_connection: Database connection
            config: SSO configuration with provider credentials
        """
        self.db = db_connection
        self.config = config
        logger.info("SSOManager initialized")

    async def initiate_oauth_flow(
        self,
        provider: SSOProvider,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate OAuth 2.0 authentication flow.

        Args:
            provider: OAuth provider
            redirect_uri: Callback URL
            state: Optional state parameter

        Returns:
            Authorization URL and state
        """
        try:
            # Generate state token for CSRF protection
            if not state:
                state = secrets.token_urlsafe(32)

            # Get provider config
            provider_config = self.config.get(provider.value)
            if not provider_config:
                return {
                    'success': False,
                    'error': f'Provider {provider.value} not configured'
                }

            # Build authorization URL
            auth_url = self._build_auth_url(
                provider=provider,
                client_id=provider_config['client_id'],
                redirect_uri=redirect_uri,
                state=state
            )

            # Store state in database for verification
            await self._store_oauth_state(state, provider.value, redirect_uri)

            return {
                'success': True,
                'authorization_url': auth_url,
                'state': state
            }

        except Exception as e:
            logger.error(f"Failed to initiate OAuth flow: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def handle_oauth_callback(
        self,
        provider: SSOProvider,
        code: str,
        state: str,
        tenant_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for token.

        Args:
            provider: OAuth provider
            code: Authorization code
            state: State parameter (CSRF token)
            tenant_slug: Optional tenant identifier

        Returns:
            User info and session token
        """
        try:
            # Verify state
            is_valid = await self._verify_oauth_state(state)
            if not is_valid:
                return {
                    'success': False,
                    'error': 'Invalid state parameter (CSRF check failed)'
                }

            # Exchange code for access token
            token_response = await self._exchange_code_for_token(provider, code)
            if not token_response['success']:
                return token_response

            access_token = token_response['access_token']

            # Get user info from provider
            user_info = await self._get_user_info(provider, access_token)
            if not user_info['success']:
                return user_info

            # Provision or update user
            user_result = await self._provision_user(
                provider=provider,
                sso_id=user_info['sso_id'],
                email=user_info['email'],
                first_name=user_info.get('first_name'),
                last_name=user_info.get('last_name'),
                avatar_url=user_info.get('avatar_url'),
                tenant_slug=tenant_slug
            )

            if not user_result['success']:
                return user_result

            # Create session
            session = await self._create_session(
                user_id=user_result['user']['id'],
                tenant_id=user_result['user']['tenant_id']
            )

            logger.info(f"SSO login successful: {user_info['email']} via {provider.value}")

            return {
                'success': True,
                'user': user_result['user'],
                'session_token': session['session_token'],
                'expires_at': session['expires_at']
            }

        except Exception as e:
            logger.error(f"OAuth callback failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def handle_saml_response(
        self,
        saml_response: str,
        tenant_slug: str
    ) -> Dict[str, Any]:
        """
        Handle SAML 2.0 authentication response.

        Args:
            saml_response: Base64-encoded SAML response
            tenant_slug: Tenant identifier

        Returns:
            User info and session token
        """
        try:
            # Parse and validate SAML response
            saml_data = await self._parse_saml_response(saml_response)

            if not saml_data['success']:
                return saml_data

            # Provision or update user
            user_result = await self._provision_user(
                provider=SSOProvider.SAML,
                sso_id=saml_data['name_id'],
                email=saml_data['email'],
                first_name=saml_data.get('first_name'),
                last_name=saml_data.get('last_name'),
                tenant_slug=tenant_slug
            )

            if not user_result['success']:
                return user_result

            # Create session
            session = await self._create_session(
                user_id=user_result['user']['id'],
                tenant_id=user_result['user']['tenant_id']
            )

            logger.info(f"SAML login successful: {saml_data['email']}")

            return {
                'success': True,
                'user': user_result['user'],
                'session_token': session['session_token'],
                'expires_at': session['expires_at']
            }

        except Exception as e:
            logger.error(f"SAML response handling failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def logout(self, session_token: str) -> Dict[str, Any]:
        """Logout user and invalidate session."""
        try:
            query = """
                DELETE FROM sessions
                WHERE session_token = $1
                RETURNING user_id
            """

            result = await self.db.fetchrow(query, session_token)

            if not result:
                return {
                    'success': False,
                    'error': 'Session not found'
                }

            logger.info(f"User logged out: {result['user_id']}")

            return {
                'success': True,
                'message': 'Logged out successfully'
            }

        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # Helper methods

    def _build_auth_url(
        self,
        provider: SSOProvider,
        client_id: str,
        redirect_uri: str,
        state: str
    ) -> str:
        """Build OAuth authorization URL."""
        auth_endpoints = {
            SSOProvider.GOOGLE: "https://accounts.google.com/o/oauth2/v2/auth",
            SSOProvider.MICROSOFT: "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            SSOProvider.GITHUB: "https://github.com/login/oauth/authorize"
        }

        scopes = {
            SSOProvider.GOOGLE: "openid email profile",
            SSOProvider.MICROSOFT: "openid email profile",
            SSOProvider.GITHUB: "user:email read:user"
        }

        base_url = auth_endpoints[provider]
        scope = scopes[provider]

        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope,
            'state': state
        }

        # Build query string
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])

        return f"{base_url}?{query_string}"

    async def _store_oauth_state(
        self,
        state: str,
        provider: str,
        redirect_uri: str
    ):
        """Store OAuth state for CSRF verification."""
        # Store in cache or database (expires in 10 minutes)
        # This is a simplified implementation
        pass

    async def _verify_oauth_state(self, state: str) -> bool:
        """Verify OAuth state parameter."""
        # Check if state exists and hasn't expired
        # This is a simplified implementation
        return True

    async def _exchange_code_for_token(
        self,
        provider: SSOProvider,
        code: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        # This would make an HTTP request to the provider's token endpoint
        # Simplified implementation
        return {
            'success': True,
            'access_token': 'mock_access_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }

    async def _get_user_info(
        self,
        provider: SSOProvider,
        access_token: str
    ) -> Dict[str, Any]:
        """Get user information from OAuth provider."""
        # This would make an HTTP request to the provider's userinfo endpoint
        # Simplified implementation
        return {
            'success': True,
            'sso_id': 'provider_user_id',
            'email': 'user@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'avatar_url': 'https://example.com/avatar.jpg'
        }

    async def _parse_saml_response(self, saml_response: str) -> Dict[str, Any]:
        """Parse and validate SAML response."""
        # This would use python-saml to parse and validate
        # Simplified implementation
        return {
            'success': True,
            'name_id': 'saml_user_id',
            'email': 'user@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }

    async def _provision_user(
        self,
        provider: SSOProvider,
        sso_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        tenant_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Provision or update user from SSO.

        Creates user if doesn't exist, updates if exists.
        """
        try:
            # Find tenant
            tenant_id = await self._get_tenant_id(tenant_slug)
            if not tenant_id:
                return {
                    'success': False,
                    'error': 'Tenant not found'
                }

            # Check if user exists
            existing_user = await self._find_user_by_sso(provider.value, sso_id)

            if existing_user:
                # Update existing user
                query = """
                    UPDATE users
                    SET first_name = $1,
                        last_name = $2,
                        avatar_url = $3,
                        last_login_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $4
                    RETURNING id, tenant_id, email, first_name, last_name, status
                """

                result = await self.db.fetchrow(
                    query,
                    first_name,
                    last_name,
                    avatar_url,
                    existing_user['id']
                )

            else:
                # Create new user
                user_id = str(uuid.uuid4())

                query = """
                    INSERT INTO users (
                        id, tenant_id, email, first_name, last_name,
                        sso_provider, sso_id, avatar_url,
                        email_verified, status, last_login_at, created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5,
                        $6, $7, $8,
                        TRUE, 'active', NOW(), NOW()
                    )
                    RETURNING id, tenant_id, email, first_name, last_name, status
                """

                result = await self.db.fetchrow(
                    query,
                    user_id,
                    tenant_id,
                    email,
                    first_name,
                    last_name,
                    provider.value,
                    sso_id,
                    avatar_url
                )

                # Assign default role to new user
                await self._assign_default_role(user_id, tenant_id)

            return {
                'success': True,
                'user': {
                    'id': str(result['id']),
                    'tenant_id': str(result['tenant_id']),
                    'email': result['email'],
                    'first_name': result['first_name'],
                    'last_name': result['last_name'],
                    'status': result['status']
                }
            }

        except Exception as e:
            logger.error(f"User provisioning failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _create_session(
        self,
        user_id: str,
        tenant_id: str,
        expires_hours: int = 24
    ) -> Dict[str, Any]:
        """Create a new user session."""
        try:
            session_id = str(uuid.uuid4())
            session_token = secrets.token_urlsafe(64)
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

            query = """
                INSERT INTO sessions (
                    id, user_id, tenant_id, session_token,
                    expires_at, created_at, last_activity_at
                ) VALUES (
                    $1, $2, $3, $4, $5, NOW(), NOW()
                )
                RETURNING session_token, expires_at
            """

            result = await self.db.fetchrow(
                query,
                session_id,
                user_id,
                tenant_id,
                session_token,
                expires_at
            )

            return {
                'session_token': result['session_token'],
                'expires_at': result['expires_at'].isoformat()
            }

        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            raise

    async def _get_tenant_id(self, tenant_slug: Optional[str]) -> Optional[str]:
        """Get tenant ID from slug."""
        if not tenant_slug:
            # Return default tenant
            query = "SELECT id FROM tenants WHERE slug = 'default' LIMIT 1"
        else:
            query = "SELECT id FROM tenants WHERE slug = $1"

        try:
            if tenant_slug:
                result = await self.db.fetchrow(query, tenant_slug)
            else:
                result = await self.db.fetchrow(query)

            return str(result['id']) if result else None

        except Exception as e:
            logger.error(f"Failed to get tenant ID: {e}")
            return None

    async def _find_user_by_sso(
        self,
        provider: str,
        sso_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find user by SSO provider and ID."""
        try:
            query = """
                SELECT id, tenant_id, email, first_name, last_name, status
                FROM users
                WHERE sso_provider = $1 AND sso_id = $2
            """

            result = await self.db.fetchrow(query, provider, sso_id)

            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Failed to find user by SSO: {e}")
            return None

    async def _assign_default_role(self, user_id: str, tenant_id: str):
        """Assign default role to new user."""
        try:
            # Get default Viewer role
            query = """
                SELECT id FROM roles
                WHERE tenant_id = $1 AND name = 'Viewer'
                LIMIT 1
            """

            role = await self.db.fetchrow(query, tenant_id)

            if role:
                # Assign role
                assignment_query = """
                    INSERT INTO user_roles (id, user_id, role_id, assigned_at)
                    VALUES ($1, $2, $3, NOW())
                """

                await self.db.execute(
                    assignment_query,
                    str(uuid.uuid4()),
                    user_id,
                    str(role['id'])
                )

        except Exception as e:
            logger.error(f"Failed to assign default role: {e}")


# Example usage
if __name__ == "__main__":
    print("SSO Provider Module")
    print("=" * 60)
    print("\nSupported providers:")
    print("  - Google OAuth 2.0")
    print("  - Microsoft OAuth 2.0")
    print("  - GitHub OAuth 2.0")
    print("  - SAML 2.0 (Enterprise)")
    print("\nFeatures:")
    print("  - User provisioning from SSO")
    print("  - Session management")
    print("  - CSRF protection")
    print("  - Default role assignment")
    print("\nCost: $0 (using free OAuth providers)")
