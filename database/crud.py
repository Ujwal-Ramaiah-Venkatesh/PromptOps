"""
CRUD Operations for PostgreSQL Database
========================================

Database operations replacing mock in-memory storage.

Author: PromptOps Team
Date: 2026-04-30
Phase: 2 - Database Persistence
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from database.models import (
    User, Resource, Scan, AutonomySetting,
    ExecutionHistory, Secret, CostData,
    AuditLog, Decomposition, Execution
)


# ============================================================================
# User CRUD Operations
# ============================================================================

def create_user(
    db: Session,
    email: str,
    hashed_password: str,
    role: str = "viewer",
    full_name: Optional[str] = None
) -> User:
    """Create a new user."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hashed_password,
        role=role,
        full_name=full_name,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()


def update_user_last_login(db: Session, user_id: uuid.UUID):
    """Update user's last login timestamp."""
    user = get_user_by_id(db, user_id)
    if user:
        user.last_login = datetime.utcnow()
        db.commit()


# ============================================================================
# Resource CRUD Operations
# ============================================================================

def create_resource(
    db: Session,
    resource_id: str,
    resource_type: str,
    name: str,
    region: str,
    state: Optional[str] = None,
    tags: Dict[str, Any] = None,
    metadata: Dict[str, Any] = None
) -> Resource:
    """Create a discovered resource."""
    resource = Resource(
        id=uuid.uuid4(),
        resource_id=resource_id,
        resource_type=resource_type,
        name=name,
        region=region,
        state=state,
        tags=tags or {},
        metadata=metadata or {}
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def get_resources(
    db: Session,
    resource_type: Optional[str] = None,
    region: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Resource]:
    """Get resources with optional filtering."""
    query = db.query(Resource)

    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)
    if region:
        query = query.filter(Resource.region == region)

    return query.offset(skip).limit(limit).all()


def get_resource_by_id(db: Session, resource_id: str) -> Optional[Resource]:
    """Get resource by AWS resource ID."""
    return db.query(Resource).filter(Resource.resource_id == resource_id).first()


def update_resource_last_seen(db: Session, resource_id: str):
    """Update resource's last seen timestamp."""
    resource = get_resource_by_id(db, resource_id)
    if resource:
        resource.last_seen_at = datetime.utcnow()
        db.commit()


def delete_stale_resources(db: Session, days: int = 7) -> int:
    """Delete resources not seen in N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    count = db.query(Resource).filter(Resource.last_seen_at < cutoff).delete()
    db.commit()
    return count


# ============================================================================
# Scan CRUD Operations
# ============================================================================

def create_scan(
    db: Session,
    scan_id: str,
    region: str,
    user_id: uuid.UUID
) -> Scan:
    """Create a new scan record."""
    scan = Scan(
        id=uuid.uuid4(),
        scan_id=scan_id,
        region=region,
        status='running',
        progress=0,
        resources_found=0,
        user_id=user_id
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


def get_scan_by_id(db: Session, scan_id: str) -> Optional[Scan]:
    """Get scan by scan_id."""
    return db.query(Scan).filter(Scan.scan_id == scan_id).first()


def update_scan_progress(
    db: Session,
    scan_id: str,
    progress: int,
    resources_found: int
):
    """Update scan progress."""
    scan = get_scan_by_id(db, scan_id)
    if scan:
        scan.progress = progress
        scan.resources_found = resources_found
        db.commit()


def complete_scan(
    db: Session,
    scan_id: str,
    resources_found: int,
    error: Optional[str] = None
):
    """Mark scan as completed or failed."""
    scan = get_scan_by_id(db, scan_id)
    if scan:
        scan.status = 'failed' if error else 'completed'
        scan.progress = 100
        scan.resources_found = resources_found
        scan.completed_at = datetime.utcnow()
        scan.error = error
        db.commit()


def get_recent_scans(
    db: Session,
    region: Optional[str] = None,
    limit: int = 10
) -> List[Scan]:
    """Get recent scans."""
    query = db.query(Scan).order_by(desc(Scan.started_at))

    if region:
        query = query.filter(Scan.region == region)

    return query.limit(limit).all()


# ============================================================================
# Autonomy Settings CRUD Operations
# ============================================================================

def get_autonomy_settings(db: Session, user_id: uuid.UUID) -> Optional[AutonomySetting]:
    """Get user's autonomy settings."""
    return db.query(AutonomySetting).filter(AutonomySetting.user_id == user_id).first()


def create_autonomy_settings(
    db: Session,
    user_id: uuid.UUID,
    risk_settings: List[Dict[str, Any]]
) -> AutonomySetting:
    """Create autonomy settings for user."""
    settings = AutonomySetting(
        id=uuid.uuid4(),
        user_id=user_id,
        risk_settings=risk_settings
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def update_autonomy_settings(
    db: Session,
    user_id: uuid.UUID,
    risk_settings: List[Dict[str, Any]]
):
    """Update user's autonomy settings."""
    settings = get_autonomy_settings(db, user_id)
    if settings:
        settings.risk_settings = risk_settings
        settings.updated_at = datetime.utcnow()
        db.commit()
    else:
        create_autonomy_settings(db, user_id, risk_settings)


# ============================================================================
# Execution History CRUD Operations
# ============================================================================

def create_execution_history(
    db: Session,
    user_id: uuid.UUID,
    action_type: str,
    risk_level: str,
    status: str,
    command: Optional[str] = None,
    parsed_intent: Dict[str, Any] = None,
    result: Dict[str, Any] = None,
    metadata: Dict[str, Any] = None
) -> ExecutionHistory:
    """Log an execution."""
    execution = ExecutionHistory(
        id=uuid.uuid4(),
        user_id=user_id,
        action_type=action_type,
        risk_level=risk_level,
        status=status,
        command=command,
        parsed_intent=parsed_intent or {},
        result=result or {},
        metadata=metadata or {}
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def get_execution_history(
    db: Session,
    user_id: Optional[uuid.UUID] = None,
    action_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[ExecutionHistory]:
    """Get execution history with filters."""
    query = db.query(ExecutionHistory).order_by(desc(ExecutionHistory.executed_at))

    if user_id:
        query = query.filter(ExecutionHistory.user_id == user_id)
    if action_type:
        query = query.filter(ExecutionHistory.action_type == action_type)

    return query.offset(skip).limit(limit).all()


# ============================================================================
# Secret CRUD Operations
# ============================================================================

def create_secret(
    db: Session,
    name: str,
    vault_path: str,
    secret_type: str,
    rotation_enabled: bool = False,
    rotation_interval_days: int = 90,
    metadata: Dict[str, Any] = None
) -> Secret:
    """Create a secret record."""
    secret = Secret(
        id=uuid.uuid4(),
        name=name,
        vault_path=vault_path,
        secret_type=secret_type,
        rotation_enabled=rotation_enabled,
        rotation_interval_days=rotation_interval_days,
        metadata=metadata or {}
    )
    db.add(secret)
    db.commit()
    db.refresh(secret)
    return secret


def get_secret_by_name(db: Session, name: str) -> Optional[Secret]:
    """Get secret by name."""
    return db.query(Secret).filter(Secret.name == name).first()


def get_secrets_due_for_rotation(db: Session) -> List[Secret]:
    """Get secrets that need rotation."""
    now = datetime.utcnow()
    return db.query(Secret).filter(
        and_(
            Secret.rotation_enabled == True,
            Secret.next_rotation_at <= now
        )
    ).all()


def update_secret_rotation(
    db: Session,
    secret_id: uuid.UUID,
    status: str,
    next_rotation_at: datetime
):
    """Update secret after rotation."""
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    if secret:
        secret.last_rotated_at = datetime.utcnow()
        secret.next_rotation_at = next_rotation_at
        secret.rotation_status = status
        db.commit()


# ============================================================================
# Cost Data CRUD Operations
# ============================================================================

def create_cost_data(
    db: Session,
    date: datetime,
    service: str,
    region: str,
    cost_usd: int,
    usage_quantity: Optional[int] = None,
    usage_unit: Optional[str] = None,
    resource_id: Optional[str] = None,
    tags: Dict[str, Any] = None,
    metadata: Dict[str, Any] = None
) -> CostData:
    """Create cost data record."""
    cost = CostData(
        id=uuid.uuid4(),
        date=date,
        service=service,
        region=region,
        cost_usd=cost_usd,
        usage_quantity=usage_quantity,
        usage_unit=usage_unit,
        resource_id=resource_id,
        tags=tags or {},
        metadata=metadata or {}
    )
    db.add(cost)
    db.commit()
    db.refresh(cost)
    return cost


def get_cost_summary(
    db: Session,
    start_date: datetime,
    end_date: datetime,
    service: Optional[str] = None
) -> List[CostData]:
    """Get cost data for date range."""
    query = db.query(CostData).filter(
        and_(
            CostData.date >= start_date,
            CostData.date <= end_date
        )
    )

    if service:
        query = query.filter(CostData.service == service)

    return query.all()


def get_total_cost(
    db: Session,
    start_date: datetime,
    end_date: datetime
) -> int:
    """Get total cost in cents for date range."""
    result = db.query(CostData).filter(
        and_(
            CostData.date >= start_date,
            CostData.date <= end_date
        )
    ).all()

    return sum(cost.cost_usd for cost in result)
