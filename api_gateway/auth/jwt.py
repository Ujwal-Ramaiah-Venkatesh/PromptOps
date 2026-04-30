"""
JWT token creation and validation

Uses python-jose for JWT encoding/decoding and passlib for password hashing
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

# JWT Configuration
# SECURITY-005: Load from secrets manager in production
def get_jwt_secret() -> str:
    """Get JWT secret key (lazy loaded to allow secrets manager initialization)"""
    try:
        from utils.secrets import get_secrets_manager
        return get_secrets_manager().get_jwt_secret()
    except Exception:
        # Fallback for development if secrets manager not initialized
        return os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production-1234567890")

SECRET_KEY = get_jwt_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password

    Args:
        plain_password: Password entered by user
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing in database

    Args:
        password: Plain text password

    Returns:
        Bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Data to encode in token (typically {"sub": email, "role": role})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    # Encode token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print(f"JWT decode error: {e}")
        return None


def get_token_email(token: str) -> Optional[str]:
    """
    Extract email from token

    Args:
        token: JWT token string

    Returns:
        Email from token or None if invalid
    """
    payload = decode_token(token)
    if payload:
        return payload.get("sub")
    return None


def get_token_role(token: str) -> Optional[str]:
    """
    Extract role from token

    Args:
        token: JWT token string

    Returns:
        Role from token or None if invalid
    """
    payload = decode_token(token)
    if payload:
        return payload.get("role")
    return None
