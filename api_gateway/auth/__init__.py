"""
Authentication module for PromptOps API Gateway

Implements JWT-based authentication with role-based access control (RBAC)
"""

from .jwt import (
    create_access_token,
    decode_token,
    verify_password,
    get_password_hash
)
from .dependencies import (
    get_current_user,
    get_current_active_user
)
from .models import User

__all__ = [
    'create_access_token',
    'decode_token',
    'verify_password',
    'get_password_hash',
    'get_current_user',
    'get_current_active_user',
    'User'
]
