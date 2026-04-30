"""
Mock authentication dependency that doesn't require database
For development and testing
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from auth.jwt import decode_token
from auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# In-memory user storage (shared with start_with_mock_db.py)
MOCK_USERS = {}

async def get_current_user_mock(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get current user from JWT token (mock version)

    Args:
        token: JWT token from Authorization header

    Returns:
        User object if valid token

    Raises:
        HTTPException: 401 if invalid token or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # Extract email
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    # Get user from mock storage
    user = MOCK_USERS.get(email)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return user


async def get_current_active_user_mock(
    current_user: User = Depends(get_current_user_mock)
) -> User:
    """
    Get current active user

    Args:
        current_user: User from get_current_user_mock dependency

    Returns:
        User object if active

    Raises:
        HTTPException: 400 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
