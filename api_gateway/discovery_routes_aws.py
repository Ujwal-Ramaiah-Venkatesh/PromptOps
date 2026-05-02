"""
Discovery API Routes with Real AWS Integration
===============================================

Routes for AWS resource discovery using boto3 (Phase 2).
Replaces mock discovery with real AWS scanning.

Author: PromptOps Team
Date: 2026-04-30
Phase: 2 - Real AWS Integration
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import sys
import os
import logging
from datetime import datetime
import uuid

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase2-aws'))

try:
    from aws_discovery import AWSDiscoveryEngine
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logging.warning("AWS Discovery module not available, using mock mode")

# Import database dependencies
try:
    from auth.dependencies import get_current_active_user, get_db
    from auth.models import User as AuthUser
    from database import crud
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logging.warning("Database not available, using in-memory storage")

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class ScanRequest(BaseModel):
    """Request to start AWS resource scan."""
    region: Optional[str] = "us-east-1"
    resource_types: Optional[List[str]] = None  # None = all types


class ScanResponse(BaseModel):
    """Response for scan initiation."""
    scan_id: str
    status: str
    message: str
    started_at: str


class ScanStatusResponse(BaseModel):
    """Scan status response."""
    scan_id: str
    status: str  # "running", "completed", "failed"
    progress: int  # 0-100
    resources_found: int
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class ResourceInventoryResponse(BaseModel):
    """Resource inventory response."""
    total_resources: int
    resource_counts: Dict[str, int]
    resources: List[Dict[str, Any]]
    discovered_at: str
    region: str


# ============================================================================
# In-Memory Scan Storage (fallback if database not available)
# ============================================================================

scans_storage = {}  # Only used if DB_AVAILABLE == False


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/scan", response_model=ScanResponse)
async def start_resource_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Start AWS resource discovery scan.

    Scans AWS account for resources and stores them in inventory.
    This is a background task that returns immediately with a scan_id.

    **Requires:** Engineer or Admin role
    """
    # Check permissions
    if current_user and current_user.role not in ["engineer", "admin", "pm"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    if not AWS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="AWS discovery not configured. Please set up AWS credentials."
        )

    # Generate scan ID
    scan_id = f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # Create scan in database or memory
    if DB_AVAILABLE and db:
        # Use PostgreSQL database
        scan = crud.create_scan(
            db=db,
            scan_id=scan_id,
            region=request.region,
            user_id=current_user.id
        )
        logger.info(f"Created scan {scan_id} in database")
    else:
        # Fallback to in-memory storage
        scan_record = {
            'scan_id': scan_id,
            'status': 'running',
            'progress': 0,
            'resources_found': 0,
            'region': request.region,
            'resource_types': request.resource_types,
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': None,
            'user': current_user.email if current_user else 'anonymous',
            'error': None,
            'resources': {}
        }
        scans_storage[scan_id] = scan_record
        logger.info(f"Created scan {scan_id} in memory (database not available)")

    # Start background scan
    background_tasks.add_task(
        run_aws_scan,
        scan_id,
        request.region,
        request.resource_types,
        db if DB_AVAILABLE else None
    )

    user_email = current_user.email if current_user else 'anonymous'
    logger.info(f"Started AWS scan {scan_id} in region {request.region} by {user_email}")

    return ScanResponse(
        scan_id=scan_id,
        status="running",
        message=f"AWS resource scan started in region {request.region}",
        started_at=datetime.utcnow().isoformat()
    )


async def run_aws_scan(scan_id: str, region: str, resource_types: Optional[List[str]], db: Optional[Session] = None):
    """
    Background task to run AWS resource scan.

    Args:
        scan_id: Unique scan identifier
        region: AWS region to scan
        resource_types: List of resource types to scan (None = all)
        db: Database session (if available)
    """
    try:
        # Initialize AWS discovery engine
        discovery = AWSDiscoveryEngine(region=region)

        # Test connection first
        if DB_AVAILABLE and db:
            crud.update_scan_progress(db, scan_id, progress=10, resources_found=0)
        else:
            scans_storage[scan_id]['progress'] = 10

        connection = discovery.test_connection()
        if not connection['success']:
            raise Exception(f"AWS connection failed: {connection.get('error', 'Unknown error')}")

        if DB_AVAILABLE and db:
            crud.update_scan_progress(db, scan_id, progress=20, resources_found=0)
        else:
            scans_storage[scan_id]['progress'] = 20

        # Discover resources
        if resource_types:
            # Scan specific resource types
            resources = {}
            progress_per_type = 60 / len(resource_types)

            for i, rtype in enumerate(resource_types):
                if rtype == 'ec2':
                    resources['ec2_instances'] = discovery.discover_ec2_instances()
                elif rtype == 'rds':
                    resources['rds_instances'] = discovery.discover_rds_instances()
                elif rtype == 's3':
                    resources['s3_buckets'] = discovery.discover_s3_buckets()
                elif rtype == 'lambda':
                    resources['lambda_functions'] = discovery.discover_lambda_functions()
                elif rtype == 'elb':
                    resources['load_balancers'] = discovery.discover_load_balancers()

                progress = 20 + int((i + 1) * progress_per_type)
                if DB_AVAILABLE and db:
                    crud.update_scan_progress(db, scan_id, progress=progress, resources_found=0)
                else:
                    scans_storage[scan_id]['progress'] = progress
        else:
            # Scan all resource types
            resources = discovery.discover_all_resources()
            if DB_AVAILABLE and db:
                crud.update_scan_progress(db, scan_id, progress=80, resources_found=0)
            else:
                scans_storage[scan_id]['progress'] = 80

        # Calculate total resources
        total_resources = sum(len(resources.get(key, [])) for key in resources)

        # Store discovered resources in database
        if DB_AVAILABLE and db:
            for resource_type, resource_list in resources.items():
                for resource_data in resource_list:
                    # Check if resource already exists
                    existing = crud.get_resource_by_id(db, resource_data['resource_id'])
                    if existing:
                        crud.update_resource_last_seen(db, resource_data['resource_id'])
                    else:
                        crud.create_resource(
                            db=db,
                            resource_id=resource_data['resource_id'],
                            resource_type=resource_data['resource_type'],
                            name=resource_data['name'],
                            region=resource_data['region'],
                            state=resource_data.get('state'),
                            tags=resource_data.get('tags', {}),
                            metadata=resource_data
                        )

            # Mark scan as completed in database
            crud.complete_scan(db, scan_id, total_resources, error=None)
        else:
            # Update in-memory storage
            scans_storage[scan_id]['status'] = 'completed'
            scans_storage[scan_id]['progress'] = 100
            scans_storage[scan_id]['resources_found'] = total_resources
            scans_storage[scan_id]['completed_at'] = datetime.utcnow().isoformat()
            scans_storage[scan_id]['resources'] = resources

        logger.info(f"AWS scan {scan_id} completed: {total_resources} resources found")

    except Exception as e:
        logger.error(f"AWS scan {scan_id} failed: {e}")

        if DB_AVAILABLE and db:
            crud.complete_scan(db, scan_id, 0, error=str(e))
        else:
            scans_storage[scan_id]['status'] = 'failed'
            scans_storage[scan_id]['error'] = str(e)
            scans_storage[scan_id]['completed_at'] = datetime.utcnow().isoformat()


@router.get("/scan/{scan_id}", response_model=ScanStatusResponse)
async def get_scan_status(
    scan_id: str,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Get status of a running or completed scan.

    Returns scan progress, resources found, and completion status.
    """
    if DB_AVAILABLE and db:
        # Get from database
        scan = crud.get_scan_by_id(db, scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        return ScanStatusResponse(
            scan_id=scan.scan_id,
            status=scan.status,
            progress=scan.progress,
            resources_found=scan.resources_found,
            started_at=scan.started_at.isoformat(),
            completed_at=scan.completed_at.isoformat() if scan.completed_at else None,
            error=scan.error
        )
    else:
        # Get from memory
        if scan_id not in scans_storage:
            raise HTTPException(status_code=404, detail="Scan not found")

        scan = scans_storage[scan_id]
        return ScanStatusResponse(
            scan_id=scan['scan_id'],
            status=scan['status'],
            progress=scan['progress'],
            resources_found=scan['resources_found'],
            started_at=scan['started_at'],
            completed_at=scan.get('completed_at'),
            error=scan.get('error')
        )


@router.get("/resources", response_model=ResourceInventoryResponse)
async def get_resource_inventory(
    region: Optional[str] = "us-east-1",
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db) if DB_AVAILABLE else None,
    current_user: AuthUser = Depends(get_current_active_user) if DB_AVAILABLE else None
):
    """
    Get current resource inventory from database or latest scan.

    Optionally filter by resource type (ec2, rds, s3, lambda, elb).
    """
    if DB_AVAILABLE and db:
        # Get resources from database
        type_map = {
            'ec2': 'ec2_instance',
            'rds': 'rds_instance',
            's3': 's3_bucket',
            'lambda': 'lambda_function',
            'elb': 'load_balancer'
        }

        db_resource_type = type_map.get(resource_type) if resource_type else None
        resources = crud.get_resources(db, resource_type=db_resource_type, region=region, limit=1000)

        if not resources:
            raise HTTPException(
                status_code=404,
                detail=f"No resources found for region {region}. Run a scan first."
            )

        # Convert to dict format
        flat_resources = []
        resource_counts = {}

        for resource in resources:
            resource_dict = {
                'resource_id': resource.resource_id,
                'resource_type': resource.resource_type,
                'name': resource.name,
                'region': resource.region,
                'state': resource.state,
                'tags': resource.tags,
                'discovered_at': resource.discovered_at.isoformat(),
                'last_seen_at': resource.last_seen_at.isoformat(),
                **resource.metadata
            }
            flat_resources.append(resource_dict)

            # Count by type
            rtype = resource.resource_type
            resource_counts[rtype] = resource_counts.get(rtype, 0) + 1

        # Get latest scan timestamp
        recent_scans = crud.get_recent_scans(db, region=region, limit=1)
        discovered_at = recent_scans[0].completed_at.isoformat() if recent_scans else datetime.utcnow().isoformat()

        return ResourceInventoryResponse(
            total_resources=len(flat_resources),
            resource_counts=resource_counts,
            resources=flat_resources,
            discovered_at=discovered_at,
            region=region
        )
    else:
        # Fallback to in-memory storage
        completed_scans = [
            scan for scan in scans_storage.values()
            if scan['status'] == 'completed' and scan['region'] == region
        ]

        if not completed_scans:
            raise HTTPException(
                status_code=404,
                detail=f"No completed scans found for region {region}. Run a scan first."
            )

        # Get most recent scan
        latest_scan = max(completed_scans, key=lambda s: s['completed_at'])
        resources = latest_scan['resources']

        # Filter by resource type if specified
        if resource_type:
            type_map = {
                'ec2': 'ec2_instances',
                'rds': 'rds_instances',
                's3': 's3_buckets',
                'lambda': 'lambda_functions',
                'elb': 'load_balancers'
            }
            resource_key = type_map.get(resource_type)
            if not resource_key:
                raise HTTPException(status_code=400, detail="Invalid resource type")

            filtered_resources = resources.get(resource_key, [])
            resource_counts = {resource_key: len(filtered_resources)}
            flat_resources = filtered_resources
        else:
            # Return all resources
            resource_counts = {key: len(val) for key, val in resources.items()}
            flat_resources = []
            for resource_list in resources.values():
                flat_resources.extend(resource_list)

        return ResourceInventoryResponse(
            total_resources=len(flat_resources),
            resource_counts=resource_counts,
            resources=flat_resources,
            discovered_at=latest_scan['completed_at'],
            region=region
        )


@router.get("/summary")
async def get_discovery_summary(
    region: Optional[str] = "us-east-1",
    current_user: User = Depends(get_current_user)
):
    """
    Get summary of discovered resources.

    Returns resource counts, latest scan info, and coverage statistics.
    """
    # Find latest completed scan
    completed_scans = [
        scan for scan in scans_storage.values()
        if scan['status'] == 'completed' and scan['region'] == region
    ]

    if not completed_scans:
        return {
            "region": region,
            "total_resources": 0,
            "resource_counts": {},
            "latest_scan": None,
            "message": "No scans completed yet"
        }

    latest_scan = max(completed_scans, key=lambda s: s['completed_at'])
    resources = latest_scan['resources']

    # Calculate statistics
    resource_counts = {key: len(val) for key, val in resources.items()}
    total_resources = sum(resource_counts.values())

    # Infer environment distribution (from tags)
    env_distribution = {"production": 0, "staging": 0, "development": 0, "unknown": 0}
    for resource_list in resources.values():
        for resource in resource_list:
            tags = resource.get('tags', {})
            env = tags.get('Environment', '').lower()
            if env in env_distribution:
                env_distribution[env] += 1
            else:
                env_distribution['unknown'] += 1

    return {
        "region": region,
        "total_resources": total_resources,
        "resource_counts": resource_counts,
        "environment_distribution": env_distribution,
        "latest_scan": {
            "scan_id": latest_scan['scan_id'],
            "completed_at": latest_scan['completed_at'],
            "duration_seconds": (
                datetime.fromisoformat(latest_scan['completed_at']) -
                datetime.fromisoformat(latest_scan['started_at'])
            ).total_seconds()
        },
        "aws_configured": AWS_AVAILABLE
    }


@router.get("/health")
async def health_check():
    """Check discovery service health and AWS connectivity."""
    health_status = {
        "status": "healthy",
        "service": "discovery",
        "version": "2.0.0",
        "aws_available": AWS_AVAILABLE
    }

    if AWS_AVAILABLE:
        try:
            # Quick connection test
            discovery = AWSDiscoveryEngine(region='us-east-1')
            connection = discovery.test_connection()
            health_status['aws_connected'] = connection['success']
            if connection['success']:
                health_status['aws_account'] = connection['account_id']
        except Exception as e:
            health_status['aws_connected'] = False
            health_status['aws_error'] = str(e)

    return health_status
