"""
Database Models: Infrastructure Ingestion
==========================================

SQLAlchemy models for imported changes tracking.

Week 13-15: ENHANCEMENT-002
Author: PromptOps Team
Date: 2026-04-30
"""

from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class ImportedChange(Base):
    """Track imported infrastructure changes."""

    __tablename__ = "imported_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id = Column(String(50), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    drift_id = Column(String(50))  # Link to drift event

    # Resource info
    resource_id = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)

    # Change details
    field_changed = Column(String(100), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    changed_by = Column(String(255))  # Who made manual change
    changed_at = Column(DateTime)  # When manual change happened

    # Import metadata
    imported_by = Column(UUID(as_uuid=True), nullable=False)
    imported_at = Column(DateTime, server_default=func.now())
    reason = Column(Text)  # Why imported

    # Terraform
    terraform_code = Column(Text)
    terraform_applied = Column(Boolean, default=False)

    # Status: pending, generating, complete, failed, rolled_back
    status = Column(String(30), nullable=False)
    error_message = Column(Text)

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "import_id": self.import_id,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "field_changed": self.field_changed,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
            "imported_by": str(self.imported_by),
            "imported_at": self.imported_at.isoformat(),
            "reason": self.reason,
            "status": self.status,
            "terraform_applied": self.terraform_applied,
        }


class ImportRollback(Base):
    """Track import rollback history."""

    __tablename__ = "import_rollbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id = Column(
        String(50),
        ForeignKey("imported_changes.import_id", ondelete="CASCADE"),
        nullable=False
    )
    rolled_back_by = Column(UUID(as_uuid=True), nullable=False)
    rolled_back_at = Column(DateTime, server_default=func.now())
    reason = Column(Text)
    success = Column(Boolean)
    error_message = Column(Text)

    # Previous state
    previous_terraform = Column(Text)
    reverted_to_state = Column(Text)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "import_id": self.import_id,
            "rolled_back_by": str(self.rolled_back_by),
            "rolled_back_at": self.rolled_back_at.isoformat(),
            "reason": self.reason,
            "success": self.success,
            "error_message": self.error_message,
        }


class TerraformStateHistory(Base):
    """Track Terraform state file changes."""

    __tablename__ = "terraform_state_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id = Column(
        String(50),
        ForeignKey("imported_changes.import_id", ondelete="SET NULL")
    )

    # State snapshot
    state_version = Column(Integer)
    state_content = Column(JSON)  # Full Terraform state as JSONB

    # Metadata
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, server_default=func.now())
    action = Column(String(50))  # import, apply, rollback, manual_edit

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "import_id": self.import_id,
            "state_version": self.state_version,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat(),
            "action": self.action,
        }
