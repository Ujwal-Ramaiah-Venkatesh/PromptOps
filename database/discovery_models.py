"""
Database Models: Discovery & Onboarding
========================================

SQLAlchemy models for AWS resource discovery.

Week 16-18: ENHANCEMENT-003
Author: PromptOps Team
Date: 2026-04-30
"""

from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, ForeignKey, ARRAY, JSON, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class DiscoveryScan(Base):
    """Track discovery scan jobs."""

    __tablename__ = "discovery_scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(String(50), nullable=False, unique=True)

    # User who initiated scan
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_email = Column(String(255))

    # Scan configuration
    regions = Column(ARRAY(Text))  # Array of AWS regions
    resource_types = Column(ARRAY(Text))  # Array of resource types

    # Status tracking
    status = Column(String(30), nullable=False)  # running, complete, failed
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    duration_seconds = Column(DECIMAL(10, 2))

    # Results summary
    total_resources = Column(Integer, default=0)
    total_dependencies = Column(Integer, default=0)
    errors = Column(ARRAY(Text))  # Array of error messages

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "scan_id": self.scan_id,
            "user_email": self.user_email,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": float(self.duration_seconds) if self.duration_seconds else None,
            "total_resources": self.total_resources,
            "total_dependencies": self.total_dependencies,
            "regions": self.regions or [],
            "resource_types": self.resource_types or [],
            "errors": self.errors or []
        }


class DiscoveredResource(Base):
    """Store discovered AWS resources with inferred context."""

    __tablename__ = "discovered_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(String(50), ForeignKey("discovery_scans.scan_id", ondelete="CASCADE"), nullable=False)

    # Resource identification
    resource_id = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False)
    name = Column(String(500))

    # Raw AWS state
    aws_state = Column(JSON)  # Full AWS resource state
    tags = Column(JSON)  # Resource tags

    # Inferred context
    inferred_environment = Column(String(50))
    inferred_project = Column(String(100))
    inferred_owner = Column(String(255))
    confidence_score = Column(DECIMAL(3, 2))  # 0.00 to 1.00
    inference_reasoning = Column(Text)

    # Import status
    imported = Column(Boolean, default=False)
    imported_at = Column(DateTime)
    import_id = Column(String(50))

    # Metadata
    discovered_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "region": self.region,
            "name": self.name,
            "inferred_environment": self.inferred_environment,
            "inferred_project": self.inferred_project,
            "inferred_owner": self.inferred_owner,
            "confidence_score": float(self.confidence_score) if self.confidence_score else 0.0,
            "imported": self.imported,
            "tags": self.tags or {}
        }


class ResourceDependency(Base):
    """Track dependencies between discovered resources."""

    __tablename__ = "resource_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(String(50), ForeignKey("discovery_scans.scan_id", ondelete="CASCADE"), nullable=False)

    # Dependency relationship
    source_resource_id = Column(String(255), nullable=False)
    target_resource_id = Column(String(255), nullable=False)
    dependency_type = Column(String(50), nullable=False)  # security_group, network, iam, application
    confidence_score = Column(DECIMAL(3, 2))  # 0.00 to 1.00

    # Metadata
    detected_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "source": self.source_resource_id,
            "target": self.target_resource_id,
            "type": self.dependency_type,
            "confidence": float(self.confidence_score) if self.confidence_score else 0.0
        }


class BulkImport(Base):
    """Track bulk import operations."""

    __tablename__ = "bulk_imports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id = Column(String(50), nullable=False, unique=True)
    scan_id = Column(String(50), ForeignKey("discovery_scans.scan_id", ondelete="CASCADE"), nullable=False)

    # Import configuration
    user_id = Column(UUID(as_uuid=True), nullable=False)
    environment_filter = Column(String(50))
    resource_type_filter = Column(ARRAY(Text))
    dry_run = Column(Boolean, default=False)

    # Status
    status = Column(String(30), nullable=False)  # pending, running, complete, failed
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

    # Results
    resources_to_import = Column(Integer, default=0)
    resources_imported = Column(Integer, default=0)
    resources_failed = Column(Integer, default=0)
    terraform_generated = Column(Boolean, default=False)
    errors = Column(ARRAY(Text))

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "import_id": self.import_id,
            "scan_id": self.scan_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "resources_to_import": self.resources_to_import,
            "resources_imported": self.resources_imported,
            "resources_failed": self.resources_failed,
            "terraform_generated": self.terraform_generated,
            "dry_run": self.dry_run,
            "errors": self.errors or []
        }


class DiscoveryMetrics(Base):
    """Store metrics and insights from discovery scans."""

    __tablename__ = "discovery_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(String(50), ForeignKey("discovery_scans.scan_id", ondelete="CASCADE"), nullable=False)

    # Coverage metrics
    total_resources = Column(Integer, nullable=False)
    environment_coverage_percentage = Column(DECIMAL(5, 2))
    project_coverage_percentage = Column(DECIMAL(5, 2))
    owner_coverage_percentage = Column(DECIMAL(5, 2))

    # Confidence metrics
    high_confidence_count = Column(Integer, default=0)
    medium_confidence_count = Column(Integer, default=0)
    low_confidence_count = Column(Integer, default=0)

    # Tag analysis
    consistent_tags = Column(JSON)
    inconsistent_tags = Column(JSON)

    # Naming patterns
    detected_naming_patterns = Column(JSON)

    # Dependency metrics
    total_dependencies = Column(Integer, default=0)
    security_group_dependencies = Column(Integer, default=0)
    network_dependencies = Column(Integer, default=0)
    application_dependencies = Column(Integer, default=0)

    # Risk assessment
    untagged_production_count = Column(Integer, default=0)
    resources_no_owner_count = Column(Integer, default=0)
    resources_default_vpc_count = Column(Integer, default=0)

    # Metadata
    generated_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "scan_id": self.scan_id,
            "total_resources": self.total_resources,
            "coverage": {
                "environment": float(self.environment_coverage_percentage) if self.environment_coverage_percentage else 0.0,
                "project": float(self.project_coverage_percentage) if self.project_coverage_percentage else 0.0,
                "owner": float(self.owner_coverage_percentage) if self.owner_coverage_percentage else 0.0
            },
            "confidence": {
                "high": self.high_confidence_count,
                "medium": self.medium_confidence_count,
                "low": self.low_confidence_count
            },
            "dependencies": {
                "total": self.total_dependencies,
                "security_group": self.security_group_dependencies,
                "network": self.network_dependencies,
                "application": self.application_dependencies
            },
            "risks": {
                "untagged_production": self.untagged_production_count,
                "no_owner": self.resources_no_owner_count,
                "default_vpc": self.resources_default_vpc_count
            }
        }
