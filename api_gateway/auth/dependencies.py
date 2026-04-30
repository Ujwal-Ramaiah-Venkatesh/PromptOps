"""
FastAPI dependencies for authentication

Provides dependency injection for current user validation
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.jwt import decode_token
from auth.models import User

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_db():
    """Database session dependency - imported from main server"""
    # This is overridden by the main server's get_db
    # Import here to avoid circular dependency
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/promptops")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token

    Args:
        token: JWT token from Authorization header
        db: Database session

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

    # Get user from database (placeholder for now)
    # In production, this will query the actual database
    # For now, return a mock user for testing
    if db is None:
        # Mock user for development/testing
        user = User(
            id="mock-user-id",
            email=email,
            full_name="Mock User",
            role=payload.get("role", "pm"),
            is_active=True
        )
        return user

    # Real database query (will be enabled once DB connection is set up)
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user

    Args:
        current_user: User from get_current_user dependency

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


def require_role(*allowed_roles: str):
    """
    Dependency to require specific roles

    Usage:
        @app.post("/api/v1/execute")
        async def execute(user: User = Depends(require_role("engineer", "lead", "admin"))):
            ...

    Args:
        allowed_roles: Roles that are allowed to access the endpoint

    Returns:
        Dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(allowed_roles)}. Your role: {current_user.role}"
            )
        return current_user
    return role_checker
