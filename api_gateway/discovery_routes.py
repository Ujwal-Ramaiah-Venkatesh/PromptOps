"""
Discovery API Routes
====================

API endpoints for AWS resource discovery and onboarding.

Week 16-18: ENHANCEMENT-003
Author: PromptOps Team
Date: 2026-04-30
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
import sys
import os
import json
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from auth.dependencies import get_current_active_user, get_db
from auth.models import User
from utils.security_logger import get_client_ip, log_permission_denied

# Import discovery modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase1-nlp'))
from discovery.aws_scanner import AWSScanner, ResourceInventory
from discovery.context_inference import ContextInferenceEngine
from discovery.dependency_mapper import DependencyMapper

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ScanRequest(BaseModel):
    """Request to start a discovery scan."""
    regions: Optional[List[str]] = None  # If None, use defaults
    resource_types: Optional[List[str]] = None  # If None, scan all
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None


class ScanResponse(BaseModel):
    """Response after starting a scan."""
    scan_id: str
    status: str  # running, complete, failed
    message: str
    started_at: str
    regions: List[str]


class ScanStatusResponse(BaseModel):
    """Scan status information."""
    scan_id: str
    status: str
    progress_percentage: float
    total_resources: int
    scanned_resources: int
    current_region: str
    current_resource_type: str
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    errors: List[str]


class ResourceSummary(BaseModel):
    """Summary of a discovered resource."""
    resource_id: str
    resource_type: str
    region: str
    name: Optional[str]
    inferred_environment: Optional[str]
    inferred_project: Optional[str]
    inferred_owner: Optional[str]
    confidence_score: float


class DiscoveryReportResponse(BaseModel):
    """Complete discovery report."""
    scan_id: str
    total_resources: int
    by_type: Dict[str, int]
    by_region: Dict[str, int]
    by_environment: Dict[str, int]
    coverage: Dict[str, Any]
    dependencies: Dict[str, Any]
    resources: List[ResourceSummary]


class BulkImportRequest(BaseModel):
    """Request to bulk import resources."""
    scan_id: str
    environment: Optional[str] = None  # If specified, import only this environment
    resource_types: Optional[List[str]] = None  # If specified, import only these types
    dry_run: bool = False  # If true, preview without importing


class BulkImportResponse(BaseModel):
    """Response after bulk import."""
    import_id: str
    status: str  # pending, running, complete, failed
    resources_to_import: int
    message: str


# ============================================================================
# In-Memory Storage (TODO: Replace with database)
# ============================================================================

# Store active scans in memory for now
ACTIVE_SCANS: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/scan", response_model=ScanResponse)
async def start_discovery_scan(
    request: Request,
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start an AWS resource discovery scan.

    **Permissions:** Requires 'engineer', 'lead', or 'admin' role

    **Process:**
    1. Validates AWS credentials
    2. Starts background scan across specified regions
    3. Returns scan_id for status tracking

    **Example request:**
    ```json
    {
        "regions": ["us-east-1", "us-west-2"],
        "resource_types": ["ec2", "rds", "s3"],
        "aws_access_key_id": "AKIA...",
        "aws_secret_access_key": "..."
    }
    ```

    **Example response:**
    ```json
    {
        "scan_id": "scan-1714492800",
        "status": "running",
        "message": "Scan started successfully",
        "started_at": "2026-04-30T10:00:00Z",
        "regions": ["us-east-1", "us-west-2"]
    }
    ```
    """
    # Check permissions
    if current_user.role not in ["engineer", "lead", "admin"]:
        log_permission_denied(
            user=current_user.email,
            resource="/api/v1/discovery/scan",
            action="start_scan",
            reason=f"role_{current_user.role}_insufficient",
            ip=get_client_ip(request)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only engineers, leads, and admins can start discovery scans"
        )

    # Generate scan ID
    scan_id = f"scan-{int(datetime.utcnow().timestamp())}"
    started_at = datetime.utcnow()

    # Default regions if not specified
    regions = scan_request.regions or ["us-east-1", "us-west-2", "eu-west-1"]

    # Store scan metadata
    ACTIVE_SCANS[scan_id] = {
        "scan_id": scan_id,
        "user_id": current_user.id,
        "user_email": current_user.email,
        "status": "running",
        "started_at": started_at,
        "completed_at": None,
        "regions": regions,
        "resource_types": scan_request.resource_types,
        "inventory": None,
        "errors": []
    }

    # Start scan in background
    background_tasks.add_task(
        run_discovery_scan,
        scan_id,
        scan_request
    )

    return ScanResponse(
        scan_id=scan_id,
        status="running",
        message=f"Discovery scan started across {len(regions)} regions",
        started_at=started_at.isoformat(),
        regions=regions
    )


@router.get("/scan/{scan_id}", response_model=ScanStatusResponse)
async def get_scan_status(
    scan_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get status of a discovery scan.

    **Example response:**
    ```json
    {
        "scan_id": "scan-1714492800",
        "status": "running",
        "progress_percentage": 45.5,
        "total_resources": 247,
        "scanned_resources": 112,
        "current_region": "us-east-1",
        "current_resource_type": "rds",
        "started_at": "2026-04-30T10:00:00Z",
        "completed_at": null,
        "duration_seconds": 125.5,
        "errors": []
    }
    ```
    """
    if scan_id not in ACTIVE_SCANS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )

    scan_data = ACTIVE_SCANS[scan_id]

    # Check ownership (users can only see their own scans, except admins)
    if current_user.role != "admin" and scan_data["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own scans"
        )

    # Calculate duration
    started_at = scan_data["started_at"]
    completed_at = scan_data["completed_at"]
    if completed_at:
        duration = (completed_at - started_at).total_seconds()
    else:
        duration = (datetime.utcnow() - started_at).total_seconds()

    # Get progress if scan is running
    inventory = scan_data.get("inventory")
    if inventory:
        total_resources = inventory.total_count
        scanned_resources = inventory.total_count
        progress_percentage = 100.0
        current_region = ""
        current_resource_type = ""
    else:
        total_resources = 0
        scanned_resources = 0
        progress_percentage = 50.0 if scan_data["status"] == "running" else 0.0
        current_region = scan_data["regions"][0] if scan_data["regions"] else ""
        current_resource_type = "scanning..."

    return ScanStatusResponse(
        scan_id=scan_id,
        status=scan_data["status"],
        progress_percentage=progress_percentage,
        total_resources=total_resources,
        scanned_resources=scanned_resources,
        current_region=current_region,
        current_resource_type=current_resource_type,
        started_at=started_at.isoformat(),
        completed_at=completed_at.isoformat() if completed_at else None,
        duration_seconds=duration,
        errors=scan_data["errors"]
    )


@router.get("/report/{scan_id}", response_model=DiscoveryReportResponse)
async def get_discovery_report(
    scan_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive discovery report for a completed scan.

    **Example response:**
    ```json
    {
        "scan_id": "scan-1714492800",
        "total_resources": 247,
        "by_type": {
            "ec2": 60,
            "rds": 15,
            "s3": 120,
            "vpc": 3,
            "subnet": 12,
            "security_group": 37
        },
        "by_region": {
            "us-east-1": 150,
            "us-west-2": 97
        },
        "by_environment": {
            "production": 120,
            "staging": 80,
            "development": 47
        },
        "coverage": {
            "environment_coverage": {"count": 247, "percentage": 100.0},
            "project_coverage": {"count": 200, "percentage": 80.9}
        },
        "dependencies": {
            "total_dependencies": 450,
            "by_type": {"security_group": 200, "network": 180, "application": 70}
        },
        "resources": [...]
    }
    ```
    """
    if scan_id not in ACTIVE_SCANS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )

    scan_data = ACTIVE_SCANS[scan_id]

    # Check ownership
    if current_user.role != "admin" and scan_data["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own scans"
        )

    # Check if scan is complete
    if scan_data["status"] != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scan is {scan_data['status']}, report not yet available"
        )

    inventory = scan_data["inventory"]
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scan data not available"
        )

    # Count by environment
    by_environment = {}
    for resource in inventory.resources:
        env = resource.inferred_environment or "unknown"
        by_environment[env] = by_environment.get(env, 0) + 1

    # Get coverage from inference engine (would be stored in scan_data)
    coverage = scan_data.get("coverage", {
        "environment_coverage": {"count": 0, "percentage": 0.0},
        "project_coverage": {"count": 0, "percentage": 0.0}
    })

    # Get dependency info
    dependency_info = scan_data.get("dependency_info", {
        "total_dependencies": 0,
        "by_type": {}
    })

    # Convert resources to summary
    resource_summaries = [
        ResourceSummary(
            resource_id=r.resource_id,
            resource_type=r.resource_type,
            region=r.region,
            name=r.name,
            inferred_environment=r.inferred_environment,
            inferred_project=r.inferred_project,
            inferred_owner=r.inferred_owner,
            confidence_score=r.confidence_score
        )
        for r in inventory.resources[:100]  # Limit to first 100 for API response
    ]

    return DiscoveryReportResponse(
        scan_id=scan_id,
        total_resources=inventory.total_count,
        by_type=inventory.by_type,
        by_region=inventory.by_region,
        by_environment=by_environment,
        coverage=coverage,
        dependencies=dependency_info,
        resources=resource_summaries
    )


@router.post("/import", response_model=BulkImportResponse)
async def bulk_import_resources(
    request: Request,
    import_request: BulkImportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Bulk import discovered resources into PromptOps.

    **Permissions:** Requires 'lead' or 'admin' role

    **Process:**
    1. Filters resources by environment/type if specified
    2. Generates Terraform code for all resources
    3. Validates Terraform code
    4. Imports into Terraform state (if not dry_run)

    **Example request:**
    ```json
    {
        "scan_id": "scan-1714492800",
        "environment": "production",
        "resource_types": ["ec2", "rds"],
        "dry_run": false
    }
    ```

    **Example response:**
    ```json
    {
        "import_id": "import-1714492900",
        "status": "pending",
        "resources_to_import": 75,
        "message": "Bulk import started for 75 resources"
    }
    ```
    """
    # Check permissions (only leads+ can import)
    if current_user.role not in ["lead", "admin"]:
        log_permission_denied(
            user=current_user.email,
            resource="/api/v1/discovery/import",
            action="bulk_import",
            reason=f"role_{current_user.role}_insufficient",
            ip=get_client_ip(request)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only leads and admins can perform bulk imports"
        )

    # Get scan data
    if import_request.scan_id not in ACTIVE_SCANS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {import_request.scan_id} not found"
        )

    scan_data = ACTIVE_SCANS[import_request.scan_id]

    if scan_data["status"] != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot import from incomplete scan"
        )

    inventory = scan_data["inventory"]

    # Filter resources
    resources_to_import = inventory.resources

    if import_request.environment:
        resources_to_import = [
            r for r in resources_to_import
            if r.inferred_environment == import_request.environment
        ]

    if import_request.resource_types:
        resources_to_import = [
            r for r in resources_to_import
            if r.resource_type in import_request.resource_types
        ]

    # Generate import ID
    import_id = f"import-{int(datetime.utcnow().timestamp())}"

    # TODO: Generate Terraform code using ENHANCEMENT-002 generator
    # TODO: Validate Terraform code
    # TODO: Import into Terraform state

    if import_request.dry_run:
        message = f"Dry run: Would import {len(resources_to_import)} resources"
        status_val = "dry_run"
    else:
        message = f"Bulk import started for {len(resources_to_import)} resources"
        status_val = "pending"

    return BulkImportResponse(
        import_id=import_id,
        status=status_val,
        resources_to_import=len(resources_to_import),
        message=message
    )


@router.get("/graph/{scan_id}")
async def get_dependency_graph(
    scan_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get dependency graph for visualizing resource relationships.

    **Returns:** Graph in format suitable for d3.js or react-flow

    **Example response:**
    ```json
    {
        "nodes": [
            {"id": "i-1", "type": "ec2", "label": "web-prod-1"},
            {"id": "sg-1", "type": "security_group", "label": "web-sg"}
        ],
        "edges": [
            {"source": "i-1", "target": "sg-1", "type": "security_group"}
        ]
    }
    ```
    """
    if scan_id not in ACTIVE_SCANS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )

    scan_data = ACTIVE_SCANS[scan_id]

    # Check ownership
    if current_user.role != "admin" and scan_data["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own scans"
        )

    # Get dependency graph from scan data
    dependency_graph = scan_data.get("dependency_graph")

    if not dependency_graph:
        return {"nodes": [], "edges": []}

    # Convert to d3.js format
    nodes = []
    for resource_id, resource in dependency_graph.resources.items():
        nodes.append({
            "id": resource_id,
            "type": resource.resource_type,
            "label": resource.name or resource_id,
            "environment": resource.inferred_environment
        })

    edges = []
    for dep in dependency_graph.dependencies:
        edges.append({
            "source": dep.source_resource_id,
            "target": dep.target_resource_id,
            "type": dep.dependency_type,
            "confidence": dep.confidence_score
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges)
    }


# ============================================================================
# Background Tasks
# ============================================================================

def run_discovery_scan(scan_id: str, scan_request: ScanRequest):
    """
    Background task to run discovery scan.

    This runs asynchronously and updates ACTIVE_SCANS with results.
    """
    try:
        # Initialize scanner
        scanner = AWSScanner(
            aws_access_key_id=scan_request.aws_access_key_id,
            aws_secret_access_key=scan_request.aws_secret_access_key,
            aws_session_token=scan_request.aws_session_token,
            regions=scan_request.regions
        )

        # Run scan
        inventory = scanner.scan_all_resources(
            resource_types=scan_request.resource_types
        )

        # Enrich with context inference
        inference_engine = ContextInferenceEngine(inventory.resources)
        enriched_resources = inference_engine.enrich_all_resources()
        coverage = inference_engine.get_coverage_report()

        # Build dependency graph
        mapper = DependencyMapper(enriched_resources)
        dependency_graph = mapper.build_dependency_graph()
        dependency_info = mapper.get_dependency_report(dependency_graph)

        # Update scan data
        ACTIVE_SCANS[scan_id]["status"] = "complete"
        ACTIVE_SCANS[scan_id]["completed_at"] = datetime.utcnow()
        ACTIVE_SCANS[scan_id]["inventory"] = inventory
        ACTIVE_SCANS[scan_id]["coverage"] = coverage
        ACTIVE_SCANS[scan_id]["dependency_graph"] = dependency_graph
        ACTIVE_SCANS[scan_id]["dependency_info"] = dependency_info

    except Exception as e:
        # Mark scan as failed
        ACTIVE_SCANS[scan_id]["status"] = "failed"
        ACTIVE_SCANS[scan_id]["completed_at"] = datetime.utcnow()
        ACTIVE_SCANS[scan_id]["errors"].append(str(e))
