"""
Database Models for Autonomy Tier System
Week 13-15: ENHANCEMENT-001

Author: PromptOps Team
Date: 2026-04-30
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database.db import Base
import uuid


class AutonomyTier(Base):
    """
    User autonomy tier settings.

    Defines whether a user wants to auto-execute or require approval
    for operations at different risk levels.
    """
    __tablename__ = "autonomy_tiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # References users.id
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    behavior = Column(String(30), nullable=False)    # auto_execute, require_approval
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AutonomyTier(user_id={self.user_id}, risk={self.risk_level}, behavior={self.behavior})>"


class ActionRiskLevel(Base):
    """
    Default risk level definitions for action types.

    Pre-populated table that defines the default risk level
    for each type of operation (e.g., restart_pod = low).
    """
    __tablename__ = "action_risk_levels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type = Column(String(100), nullable=False, unique=True)
    default_risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    description = Column(Text)
    can_be_overridden = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<ActionRiskLevel(action={self.action_type}, risk={self.default_risk_level})>"


class AutoExecutedAction(Base):
    """
    Audit trail of auto-executed actions.

    Records all operations that were executed automatically
    without requiring PM approval.
    """
    __tablename__ = "auto_executed_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    operation_id = Column(String(50), nullable=False)
    action_type = Column(String(100), nullable=False)
    risk_level = Column(String(20), nullable=False)
    command = Column(Text, nullable=False)
    executed_at = Column(DateTime, server_default=func.now())
    duration_ms = Column(Integer)
    success = Column(Boolean)
    result_summary = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)

    def __repr__(self):
        return f"<AutoExecutedAction(operation_id={self.operation_id}, action={self.action_type}, success={self.success})>"
