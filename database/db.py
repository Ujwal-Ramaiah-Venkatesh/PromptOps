"""
Database Connection and CRUD Operations
========================================

Database utilities for PostgreSQL with SQLAlchemy.

Author: PromptOps Team - Week 11-12
Date: 2026-04-29
"""

from sqlalchemy import create_engine, select, and_, or_, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import logging

from .models import (
    Base, AuditLog, Decomposition, Execution,
    ContextSnapshot, DriftEvent, User, APIKey
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Database Configuration
# ============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://promptops:password@localhost:5432/promptops"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================================================
# Database Initialization
# ============================================================================

def init_db():
    """Initialize database schema."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_db() -> Session:
    """
    Get database session.

    Usage:
        with get_db() as db:
            result = db.query(AuditLog).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# Audit Log CRUD
# ============================================================================

class AuditLogDB:
    """CRUD operations for audit log."""

    @staticmethod
    def create(db: Session, entry: Dict[str, Any]) -> AuditLog:
        """Create new audit log entry."""
        audit = AuditLog(**entry)
        db.add(audit)
        db.commit()
        db.refresh(audit)
        logger.info(f"Created audit log entry: {audit.id}")
        return audit

    @staticmethod
    def get_by_id(db: Session, audit_id: str) -> Optional[AuditLog]:
        """Get audit log by ID."""
        return db.query(AuditLog).filter(AuditLog.id == audit_id).first()

    @staticmethod
    def get_recent(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        user: Optional[str] = None,
        env: Optional[str] = None,
        status: Optional[str] = None,
        intent_type: Optional[str] = None
    ) -> tuple[List[AuditLog], int]:
        """
        Get recent audit entries with filters.

        Returns (entries, total_count).
        """
        query = db.query(AuditLog)

        # Apply filters
        if user:
            query = query.filter(AuditLog.user_email == user)
        if env:
            query = query.filter(AuditLog.target_env == env)
        if status:
            query = query.filter(AuditLog.status == status)
        if intent_type:
            query = query.filter(AuditLog.intent_type == intent_type)

        # Get total count
        total = query.count()

        # Apply ordering and pagination
        entries = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()

        return entries, total

    @staticmethod
    def update_status(db: Session, audit_id: str, status: str, error_message: Optional[str] = None):
        """Update audit entry status."""
        audit = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
        if audit:
            audit.status = status
            if error_message:
                audit.error_message = error_message
            db.commit()
            logger.info(f"Updated audit {audit_id} status to {status}")

    @staticmethod
    def get_user_stats(db: Session, user_email: str) -> Dict[str, Any]:
        """Get statistics for a specific user."""
        total = db.query(AuditLog).filter(AuditLog.user_email == user_email).count()
        completed = db.query(AuditLog).filter(
            and_(AuditLog.user_email == user_email, AuditLog.status == "completed")
        ).count()
        failed = db.query(AuditLog).filter(
            and_(AuditLog.user_email == user_email, AuditLog.status == "failed")
        ).count()

        return {
            "total_commands": total,
            "completed": completed,
            "failed": failed,
            "success_rate": (completed / total * 100) if total > 0 else 0
        }

# ============================================================================
# Decomposition CRUD
# ============================================================================

class DecompositionDB:
    """CRUD operations for decompositions."""

    @staticmethod
    def create(db: Session, decomp: Dict[str, Any]) -> Decomposition:
        """Create new decomposition."""
        decomposition = Decomposition(**decomp)
        db.add(decomposition)
        db.commit()
        db.refresh(decomposition)
        logger.info(f"Created decomposition: {decomposition.operation_id}")
        return decomposition

    @staticmethod
    def get_by_id(db: Session, decomp_id: str) -> Optional[Decomposition]:
        """Get decomposition by ID."""
        return db.query(Decomposition).filter(Decomposition.id == decomp_id).first()

    @staticmethod
    def get_by_operation_id(db: Session, operation_id: str) -> Optional[Decomposition]:
        """Get decomposition by operation ID."""
        return db.query(Decomposition).filter(Decomposition.operation_id == operation_id).first()

    @staticmethod
    def get_recent(db: Session, limit: int = 10, user: Optional[str] = None) -> List[Decomposition]:
        """Get recent decompositions."""
        query = db.query(Decomposition)

        if user:
            query = query.filter(Decomposition.user_email == user)

        return query.order_by(desc(Decomposition.timestamp)).limit(limit).all()

# ============================================================================
# Execution CRUD
# ============================================================================

class ExecutionDB:
    """CRUD operations for executions."""

    @staticmethod
    def create(db: Session, execution: Dict[str, Any]) -> Execution:
        """Create new execution."""
        exec_obj = Execution(**execution)
        db.add(exec_obj)
        db.commit()
        db.refresh(exec_obj)
        logger.info(f"Created execution: {exec_obj.execution_id}")
        return exec_obj

    @staticmethod
    def get_by_execution_id(db: Session, execution_id: str) -> Optional[Execution]:
        """Get execution by execution ID."""
        return db.query(Execution).filter(Execution.execution_id == execution_id).first()

    @staticmethod
    def update_status(
        db: Session,
        execution_id: str,
        status: str,
        completed_tasks: Optional[int] = None,
        current_task: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Update execution status."""
        execution = db.query(Execution).filter(Execution.execution_id == execution_id).first()

        if execution:
            execution.status = status
            if completed_tasks is not None:
                execution.completed_tasks = completed_tasks
            if current_task:
                execution.current_task_name = current_task
            if error_message:
                execution.error_message = error_message
            if status in ["completed", "failed"]:
                execution.completed_at = datetime.utcnow()

            db.commit()
            logger.info(f"Updated execution {execution_id} status to {status}")

    @staticmethod
    def add_log_entry(db: Session, execution_id: str, log_message: str):
        """Add log entry to execution."""
        execution = db.query(Execution).filter(Execution.execution_id == execution_id).first()

        if execution:
            if execution.execution_log is None:
                execution.execution_log = []
            execution.execution_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": log_message
            })
            db.commit()

# ============================================================================
# Context Snapshot CRUD
# ============================================================================

class ContextSnapshotDB:
    """CRUD operations for context snapshots."""

    @staticmethod
    def create(db: Session, snapshot: Dict[str, Any]) -> ContextSnapshot:
        """Create new context snapshot."""
        snapshot_obj = ContextSnapshot(**snapshot)
        db.add(snapshot_obj)
        db.commit()
        db.refresh(snapshot_obj)
        logger.info(f"Created context snapshot: {snapshot_obj.snapshot_id}")
        return snapshot_obj

    @staticmethod
    def get_by_snapshot_id(db: Session, snapshot_id: str) -> Optional[ContextSnapshot]:
        """Get snapshot by snapshot ID."""
        return db.query(ContextSnapshot).filter(ContextSnapshot.snapshot_id == snapshot_id).first()

    @staticmethod
    def get_latest(db: Session) -> Optional[ContextSnapshot]:
        """Get latest snapshot."""
        return db.query(ContextSnapshot).order_by(desc(ContextSnapshot.timestamp)).first()

    @staticmethod
    def get_recent(db: Session, limit: int = 10) -> List[ContextSnapshot]:
        """Get recent snapshots."""
        return db.query(ContextSnapshot).order_by(desc(ContextSnapshot.timestamp)).limit(limit).all()

# ============================================================================
# Drift Event CRUD
# ============================================================================

class DriftEventDB:
    """CRUD operations for drift events."""

    @staticmethod
    def create(db: Session, drift: Dict[str, Any]) -> DriftEvent:
        """Create new drift event."""
        drift_obj = DriftEvent(**drift)
        db.add(drift_obj)
        db.commit()
        db.refresh(drift_obj)
        logger.info(f"Created drift event: {drift_obj.drift_id}")
        return drift_obj

    @staticmethod
    def get_by_drift_id(db: Session, drift_id: str) -> Optional[DriftEvent]:
        """Get drift event by drift ID."""
        return db.query(DriftEvent).filter(DriftEvent.drift_id == drift_id).first()

    @staticmethod
    def get_recent(
        db: Session,
        limit: int = 10,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None
    ) -> List[DriftEvent]:
        """Get recent drift events with filters."""
        query = db.query(DriftEvent)

        if severity:
            query = query.filter(DriftEvent.severity == severity)

        if acknowledged is not None:
            if acknowledged:
                query = query.filter(DriftEvent.acknowledged_by.isnot(None))
            else:
                query = query.filter(DriftEvent.acknowledged_by.is_(None))

        return query.order_by(desc(DriftEvent.timestamp)).limit(limit).all()

    @staticmethod
    def get_unacknowledged_count(db: Session) -> int:
        """Get count of unacknowledged drift events."""
        return db.query(DriftEvent).filter(DriftEvent.acknowledged_by.is_(None)).count()

    @staticmethod
    def acknowledge(db: Session, drift_id: str, user: str):
        """Acknowledge drift event."""
        drift = db.query(DriftEvent).filter(DriftEvent.drift_id == drift_id).first()

        if drift:
            drift.acknowledged_by = user
            drift.acknowledged_at = datetime.utcnow()
            db.commit()
            logger.info(f"Drift {drift_id} acknowledged by {user}")

    @staticmethod
    def mark_reverted(db: Session, drift_id: str, user: str, execution_id: Optional[str] = None):
        """Mark drift as reverted."""
        drift = db.query(DriftEvent).filter(DriftEvent.drift_id == drift_id).first()

        if drift:
            drift.reverted_by = user
            drift.reverted_at = datetime.utcnow()
            if execution_id:
                drift.revert_execution_id = execution_id
            db.commit()
            logger.info(f"Drift {drift_id} reverted by {user}")

# ============================================================================
# User CRUD
# ============================================================================

class UserDB:
    """CRUD operations for users."""

    @staticmethod
    def create(db: Session, user: Dict[str, Any]) -> User:
        """Create new user."""
        user_obj = User(**user)
        db.add(user_obj)
        db.commit()
        db.refresh(user_obj)
        logger.info(f"Created user: {user_obj.email}")
        return user_obj

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_all(db: Session) -> List[User]:
        """Get all users."""
        return db.query(User).filter(User.is_active == True).all()

    @staticmethod
    def update_last_login(db: Session, email: str):
        """Update user's last login timestamp."""
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.last_login = datetime.utcnow()
            db.commit()

# ============================================================================
# Helper Functions
# ============================================================================

def export_audit_to_csv(db: Session, filters: Dict[str, Any]) -> str:
    """Export audit log to CSV format."""
    import csv
    from io import StringIO

    entries, _ = AuditLogDB.get_recent(db, limit=10000, **filters)

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'timestamp', 'user_email', 'command', 'intent_type',
        'target_service', 'target_env', 'status', 'risk_level', 'duration_seconds'
    ])
    writer.writeheader()

    for entry in entries:
        writer.writerow({
            'timestamp': entry.timestamp.isoformat(),
            'user_email': entry.user_email,
            'command': entry.command,
            'intent_type': entry.intent_type,
            'target_service': entry.target_service,
            'target_env': entry.target_env,
            'status': entry.status,
            'risk_level': entry.risk_level,
            'duration_seconds': entry.duration_seconds
        })

    return output.getvalue()

def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Get overall dashboard statistics."""
    total_commands = db.query(AuditLog).count()
    recent_commands = db.query(AuditLog).filter(
        AuditLog.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).count()
    unacked_drift = DriftEventDB.get_unacknowledged_count(db)
    active_executions = db.query(Execution).filter(
        Execution.status.in_(["queued", "in_progress"])
    ).count()

    return {
        "total_commands": total_commands,
        "recent_commands_7d": recent_commands,
        "unacknowledged_drift": unacked_drift,
        "active_executions": active_executions
    }
