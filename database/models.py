"""
SQLAlchemy Models for PromptOps Database
=========================================

ORM models corresponding to PostgreSQL schema.

Author: PromptOps Team - Week 11-12
Date: 2026-04-29
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, ForeignKey,
    DateTime, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

# ============================================================================
# Audit Log Model
# ============================================================================

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_email = Column(String(255), nullable=False, index=True)
    command = Column(Text, nullable=False)
    intent_type = Column(String(50), index=True)
    target_service = Column(String(100), index=True)
    target_env = Column(String(50), index=True)
    status = Column(String(50), nullable=False, index=True)
    risk_level = Column(String(20))
    decomposition_id = Column(UUID(as_uuid=True))
    execution_id = Column(UUID(as_uuid=True))
    duration_seconds = Column(Integer)
    error_message = Column(Text)
    task_plan = Column(JSONB)
    execution_log = Column(JSONB, default=list)
    approved_by = Column(String(255))
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user={self.user_email}, command={self.command[:50]})>"

# ============================================================================
# Decomposition Model
# ============================================================================

class Decomposition(Base):
    __tablename__ = "decompositions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id = Column(String(100), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_email = Column(String(255), nullable=False, index=True)
    original_command = Column(Text, nullable=False)
    parsed_intent = Column(JSONB, nullable=False)
    total_sub_tasks = Column(Integer, nullable=False)
    estimated_duration = Column(Integer)
    risk_assessment = Column(JSONB, nullable=False)
    sub_tasks = Column(JSONB, nullable=False)
    rollback_plan = Column(JSONB)
    current_state = Column(JSONB)
    target_state = Column(JSONB)
    dependencies_graph = Column(JSONB)
    critical_path = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to executions
    executions = relationship("Execution", back_populates="decomposition")

    def __repr__(self):
        return f"<Decomposition(id={self.id}, operation_id={self.operation_id})>"

# ============================================================================
# Execution Model
# ============================================================================

class Execution(Base):
    __tablename__ = "executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(String(100), unique=True, nullable=False, index=True)
    decomposition_id = Column(UUID(as_uuid=True), ForeignKey("decompositions.id"))
    status = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), index=True)
    completed_at = Column(DateTime(timezone=True))
    approved_by = Column(String(255))
    approved_at = Column(DateTime(timezone=True))
    approval_phrase = Column(String(100))
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    current_task_index = Column(Integer, default=0)
    current_task_name = Column(String(255))
    execution_log = Column(JSONB, default=list)
    error_message = Column(Text)
    rollback_executed = Column(Boolean, default=False)
    rollback_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to decomposition
    decomposition = relationship("Decomposition", back_populates="executions")

    def __repr__(self):
        return f"<Execution(id={self.id}, execution_id={self.execution_id}, status={self.status})>"

# ============================================================================
# Context Snapshot Model
# ============================================================================

class ContextSnapshot(Base):
    __tablename__ = "context_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(String(100), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    resource_types = Column(JSONB, nullable=False)
    total_resources = Column(Integer, nullable=False)
    collection_duration_ms = Column(Integer)
    errors = Column(JSONB, default=list)
    aws_region = Column(String(50), default="us-east-1")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ContextSnapshot(id={self.id}, snapshot_id={self.snapshot_id}, resources={self.total_resources})>"

# ============================================================================
# Drift Event Model
# ============================================================================

class DriftEvent(Base):
    __tablename__ = "drift_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drift_id = Column(String(100), unique=True, nullable=False, index=True)
    snapshot_id = Column(String(100), nullable=False, index=True)
    previous_snapshot_id = Column(String(100))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=False)
    resource_name = Column(String(255))
    field = Column(String(100), nullable=False)
    expected_value = Column(Text)
    actual_value = Column(Text)
    severity = Column(String(20), nullable=False, index=True)
    auto_fixable = Column(Boolean, default=False)
    acknowledged_by = Column(String(255), index=True)
    acknowledged_at = Column(DateTime(timezone=True))
    reverted_by = Column(String(255))
    reverted_at = Column(DateTime(timezone=True))
    revert_execution_id = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Composite index for resource lookups
    __table_args__ = (
        Index('idx_drift_resource', 'resource_type', 'resource_id'),
    )

    def __repr__(self):
        return f"<DriftEvent(id={self.id}, drift_id={self.drift_id}, resource={self.resource_type}/{self.resource_id})>"

# ============================================================================
# User Model
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    role = Column(String(50), nullable=False, default="pm", index=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

# ============================================================================
# API Key Model
# ============================================================================

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_name = Column(String(100), nullable=False)
    key_value_encrypted = Column(Text, nullable=False)
    service = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<APIKey(id={self.id}, service={self.service}, active={self.is_active})>"

# ============================================================================
# Schema Version Model
# ============================================================================

class SchemaVersion(Base):
    __tablename__ = "schema_version"

    version = Column(String(20), primary_key=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(Text)

    def __repr__(self):
        return f"<SchemaVersion(version={self.version})>"
