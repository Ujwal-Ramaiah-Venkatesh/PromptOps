"""
Database Package
================

Database utilities and models for PromptOps.

Author: PromptOps Team - Week 11-12
"""

from .models import (
    Base,
    AuditLog,
    Decomposition,
    Execution,
    ContextSnapshot,
    DriftEvent,
    User,
    APIKey,
    SchemaVersion
)

from .db import (
    engine,
    SessionLocal,
    get_db,
    init_db,
    AuditLogDB,
    DecompositionDB,
    ExecutionDB,
    ContextSnapshotDB,
    DriftEventDB,
    UserDB,
    export_audit_to_csv,
    get_dashboard_stats
)

__all__ = [
    # Models
    "Base",
    "AuditLog",
    "Decomposition",
    "Execution",
    "ContextSnapshot",
    "DriftEvent",
    "User",
    "APIKey",
    "SchemaVersion",

    # Database
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",

    # CRUD
    "AuditLogDB",
    "DecompositionDB",
    "ExecutionDB",
    "ContextSnapshotDB",
    "DriftEventDB",
    "UserDB",

    # Utilities
    "export_audit_to_csv",
    "get_dashboard_stats"
]
