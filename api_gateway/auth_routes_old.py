"""
Authentication routes for API Gateway

Login, register, user management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from utils.security_logger import (
    log_login_attempt, log_registration, log_permission_denied,
    log_user_created, log_user_updated, log_user_deactivated,
    get_client_ip, get_user_agent
)

from auth.jwt import create_access_token, get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from auth.models import User
from auth.dependencies import get_current_active_user, get_db
from auth.permissions import can_manage_users, get_role_permissions

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Rate limiter for auth endpoints
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Pydantic Models
# ============================================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "pm"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user

    **Rate Limit**: 3 requests per minute per IP (prevents registration abuse)

    **Note**: In production, this should require admin approval or be disabled.
    For now, allows self-registration for testing.
    """
    # Get client info for logging
    client_ip = get_client_ip(request)

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        log_registration(user_data.email, user_data.role, client_ip, False)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate role
    valid_roles = ["viewer", "pm", "engineer", "lead", "admin"]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    # Create user
    import uuid
    user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Log successful registration
    log_registration(user.email, user.role, client_ip, True)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password

    **Rate Limit**: 5 requests per minute per IP (prevents brute force attacks)

    Returns JWT access token for authentication
    """
    # Get client info for logging
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Authenticate user
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failed login attempt
        log_login_attempt(form_data.username, False, client_ip, user_agent)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        # Log login attempt for inactive user
        log_login_attempt(form_data.username, False, client_ip, user_agent)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Log successful login
    log_login_attempt(user.email, True, client_ip, user_agent)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        )
    )


@router.get("/me", response_model=UserResponse)
@limiter.limit("60/minute")
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information from token

    **Rate Limit**: 60 requests per minute per IP

    Requires: Valid JWT token
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active
    )


@router.get("/me/permissions")
@limiter.limit("60/minute")
async def get_my_permissions(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's permissions

    **Rate Limit**: 60 requests per minute per IP

    Requires: Valid JWT token
    """
    permissions = get_role_permissions(current_user.role)
    return {
        "user": current_user.email,
        "role": current_user.role,
        "permissions": permissions
    }


# ============================================================================
# User Management Endpoints (Admin only)
# ============================================================================

@router.get("/users")
@limiter.limit("30/minute")
async def list_users(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all users

    **Rate Limit**: 30 requests per minute per IP

    Requires: lead or admin role
    """
    if not can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only leads and admins can list users"
        )

    users = db.query(User).all()
    return {
        "users": [
            UserResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                is_active=u.is_active
            ) for u in users
        ],
        "total": len(users)
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user information

    Requires: lead or admin role
    """
    if not can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only leads and admins can update users"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.role is not None:
        user.role = user_update.role
    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate user (soft delete)

    Requires: admin role
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete users"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Soft delete
    user.is_active = False
    db.commit()

    return {"message": f"User {user.email} deactivated"}
