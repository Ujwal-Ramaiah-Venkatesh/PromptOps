"""
Secret Management and Rotation API Routes
==========================================

ENH-005: Secret rotation UI and automation endpoints.

Author: PromptOps Team
Date: 2026-04-30
Phase: 2 - Secret Rotation (ENH-005)
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import sys
import os
import logging
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase2-aws'))

try:
    from vault_manager import VaultManager, generate_database_password, generate_api_key
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    logging.warning("Vault Manager module not available")

# Import database dependencies
try:
    from auth.dependencies import get_current_active_user, get_db
    from auth.models import User as AuthUser
    from database import crud
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logging.warning("Database not available")

router = APIRouter(prefix="/api/v1/secrets", tags=["secrets"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class SecretCreateRequest(BaseModel):
    """Request to create a secret."""
    path: str
    secret_data: Dict[str, Any]
    secret_type: str = "generic"
    rotation_enabled: bool = False
    rotation_interval_days: int = 90


class SecretResponse(BaseModel):
    """Secret response (without actual secret data)."""
    path: str
    secret_type: str
    version: int
    created_time: str
    rotation_enabled: bool
    rotation_interval_days: Optional[int] = None
    next_rotation_at: Optional[str] = None


class SecretRotateRequest(BaseModel):
    """Request to rotate a secret."""
    path: str
    auto_generate: bool = True
    new_secret_data: Optional[Dict[str, Any]] = None


class SecretVersionResponse(BaseModel):
    """Secret version info."""
    version: int
    created_time: str
    deleted: bool


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/", response_model=SecretResponse)
async def create_secret(
    request: SecretCreateRequest,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Create a new secret in Vault.

    **Request body:**
    ```json
    {
        "path": "database/prod-postgres",
        "secret_data": {
            "username": "admin",
            "password": "secure_password"
        },
        "secret_type": "database",
        "rotation_enabled": true,
        "rotation_interval_days": 90
    }
    ```

    **Requires:** Admin or Engineer role
    """
    # Check permissions
    if current_user and current_user.role not in ["admin", "engineer"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    if not VAULT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Vault not configured. Please set up HashiCorp Vault."
        )

    try:
        vault = VaultManager()

        # Create secret in Vault
        result = vault.create_secret(
            path=request.path,
            secret_data=request.secret_data,
            secret_type=request.secret_type
        )

        # Calculate next rotation if enabled
        next_rotation = None
        if request.rotation_enabled:
            next_rotation = (
                datetime.utcnow() + timedelta(days=request.rotation_interval_days)
            ).isoformat()

        # Store in database if available
        if DB_AVAILABLE and db:
            crud.create_secret(
                db=db,
                name=request.path,
                vault_path=f"promptops/{request.path}",
                secret_type=request.secret_type,
                rotation_enabled=request.rotation_enabled,
                rotation_interval_days=request.rotation_interval_days,
                metadata={'created_by': current_user.email if current_user else 'system'}
            )

        logger.info(f"Secret created at {request.path} by {current_user.email if current_user else 'system'}")

        return SecretResponse(
            path=request.path,
            secret_type=request.secret_type,
            version=result['version'],
            created_time=result['created_time'],
            rotation_enabled=request.rotation_enabled,
            rotation_interval_days=request.rotation_interval_days if request.rotation_enabled else None,
            next_rotation_at=next_rotation
        )

    except Exception as e:
        logger.error(f"Failed to create secret: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create secret: {str(e)}"
        )


@router.get("/")
async def list_secrets(
    path: str = "",
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    List all secrets at a path.

    **Query Parameters:**
    - path: Path to list (default: root)

    **Requires:** Any authenticated user
    """
    if not VAULT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Vault not configured")

    try:
        vault = VaultManager()
        secrets = vault.list_secrets(path)

        # Get additional info from database if available
        secret_list = []
        for secret_path in secrets:
            secret_info = {'path': secret_path}

            if DB_AVAILABLE and db:
                db_secret = crud.get_secret_by_name(db, secret_path)
                if db_secret:
                    secret_info.update({
                        'secret_type': db_secret.secret_type,
                        'rotation_enabled': db_secret.rotation_enabled,
                        'next_rotation_at': db_secret.next_rotation_at.isoformat() if db_secret.next_rotation_at else None
                    })

            secret_list.append(secret_info)

        return {
            'secrets': secret_list,
            'count': len(secret_list),
            'path': path
        }

    except Exception as e:
        logger.error(f"Failed to list secrets: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list secrets: {str(e)}"
        )


@router.get("/{secret_path:path}")
async def get_secret(
    secret_path: str,
    version: Optional[int] = None,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Get a secret from Vault.

    **Path Parameters:**
    - secret_path: Secret path (e.g., 'database/prod-postgres')

    **Query Parameters:**
    - version: Specific version to retrieve (default: latest)

    **Requires:** Any authenticated user

    **Note:** Returns actual secret data. Use with caution.
    """
    if not VAULT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Vault not configured")

    try:
        vault = VaultManager()
        secret = vault.read_secret(secret_path, version=version)

        return {
            'path': secret_path,
            'data': secret['data'],
            'version': secret['version'],
            'metadata': secret['metadata']
        }

    except Exception as e:
        logger.error(f"Failed to get secret: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Secret not found: {str(e)}"
        )


@router.post("/rotate")
async def rotate_secret(
    request: SecretRotateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Rotate a secret (create new version).

    **Request body:**
    ```json
    {
        "path": "database/prod-postgres",
        "auto_generate": true
    }
    ```

    If `auto_generate` is true, generates new password/key automatically.
    Otherwise, provide `new_secret_data`.

    **Requires:** Admin or Engineer role
    """
    # Check permissions
    if current_user and current_user.role not in ["admin", "engineer"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    if not VAULT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Vault not configured")

    try:
        vault = VaultManager()

        # Get current secret to determine type
        current = vault.read_secret(request.path)

        # Generate new secret data if auto_generate
        if request.auto_generate:
            # Determine secret type and generate accordingly
            new_secret_data = current['data'].copy()

            # Auto-generate password or key
            if 'password' in new_secret_data:
                new_secret_data['password'] = generate_database_password()
            elif 'api_key' in new_secret_data:
                new_secret_data['api_key'] = generate_api_key()
            elif 'secret_key' in new_secret_data:
                new_secret_data['secret_key'] = generate_api_key()
        else:
            if not request.new_secret_data:
                raise HTTPException(
                    status_code=400,
                    detail="new_secret_data required when auto_generate is false"
                )
            new_secret_data = request.new_secret_data

        # Rotate secret
        result = vault.rotate_secret(request.path, new_secret_data)

        # Update database if available
        if DB_AVAILABLE and db:
            db_secret = crud.get_secret_by_name(db, request.path)
            if db_secret:
                next_rotation = datetime.utcnow() + timedelta(days=db_secret.rotation_interval_days)
                crud.update_secret_rotation(
                    db=db,
                    secret_id=db_secret.id,
                    status='completed',
                    next_rotation_at=next_rotation
                )

        logger.info(f"Secret rotated at {request.path} by {current_user.email if current_user else 'system'}")

        return {
            'success': True,
            'path': request.path,
            'old_version': result['old_version'],
            'new_version': result['new_version'],
            'rotated_at': result['rotated_at']
        }

    except Exception as e:
        logger.error(f"Failed to rotate secret: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rotate secret: {str(e)}"
        )


@router.get("/{secret_path:path}/versions")
async def get_secret_versions(
    secret_path: str,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Get all versions of a secret.

    **Path Parameters:**
    - secret_path: Secret path

    **Requires:** Any authenticated user
    """
    if not VAULT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Vault not configured")

    try:
        vault = VaultManager()
        versions = vault.get_secret_versions(secret_path)

        return {
            'path': secret_path,
            'versions': versions,
            'total_versions': len(versions)
        }

    except Exception as e:
        logger.error(f"Failed to get secret versions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get versions: {str(e)}"
        )


@router.delete("/{secret_path:path}")
async def delete_secret(
    secret_path: str,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Delete a secret.

    **Path Parameters:**
    - secret_path: Secret path

    **Requires:** Admin role only
    """
    # Check permissions
    if current_user and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    if not VAULT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Vault not configured")

    try:
        vault = VaultManager()
        vault.delete_secret(secret_path)

        logger.info(f"Secret deleted at {secret_path} by {current_user.email if current_user else 'system'}")

        return {
            'success': True,
            'message': f"Secret {secret_path} deleted successfully"
        }

    except Exception as e:
        logger.error(f"Failed to delete secret: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete secret: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Check secrets service health."""
    health_status = {
        "status": "healthy",
        "service": "secrets",
        "version": "2.0.0",
        "vault_available": VAULT_AVAILABLE
    }

    if VAULT_AVAILABLE:
        try:
            vault = VaultManager()
            vault_health = vault.check_health()
            health_status['vault_health'] = vault_health
        except Exception as e:
            health_status['vault_health'] = {'healthy': False, 'error': str(e)}

    return health_status
