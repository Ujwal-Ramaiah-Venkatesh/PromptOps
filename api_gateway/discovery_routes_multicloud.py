"""
Multi-Cloud Discovery API Routes
=================================

Unified API endpoints for AWS, GCP, and Azure resource discovery.
Phase 3 - Multi-Cloud Support

Author: PromptOps Team
Date: 2026-05-01
Phase: 3 - Multi-Cloud
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import uuid
import logging
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase2-aws'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase3-gcp'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase3-azure'))

from aws_discovery import AWSDiscoveryEngine
from gcp_discovery import GCPDiscoveryEngine
from azure_discovery import AzureDiscoveryEngine
from websocket_server import manager as ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/multicloud", tags=["multi-cloud"])


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    ALL = "all"


class ScanRequest(BaseModel):
    """Request model for multi-cloud scan."""
    providers: List[CloudProvider] = Field(
        default=[CloudProvider.ALL],
        description="List of cloud providers to scan"
    )
    regions: Optional[List[str]] = Field(
        default=None,
        description="Specific regions to scan (AWS only)"
    )
    resource_types: Optional[List[str]] = Field(
        default=None,
        description="Specific resource types to scan"
    )


class ScanStatus(BaseModel):
    """Scan status response model."""
    scan_id: str
    status: str  # pending, running, completed, failed
    providers: List[str]
    progress: Dict[str, int]  # provider -> percentage
    started_at: str
    completed_at: Optional[str] = None
    total_resources: int = 0
    errors: List[str] = []


class ResourceSummary(BaseModel):
    """Resource summary response model."""
    cloud_provider: str
    total_resources: int
    resource_counts: Dict[str, int]
    regions: List[str]
    last_scan: Optional[str] = None


class MultiCloudSummary(BaseModel):
    """Complete multi-cloud summary."""
    total_resources: int
    providers: Dict[str, ResourceSummary]
    scan_time: str


# In-memory scan storage (replace with database in production)
scans: Dict[str, Dict[str, Any]] = {}
resources_cache: Dict[str, List[Dict[str, Any]]] = {}


def resolve_providers(requested: List[CloudProvider]) -> List[str]:
    """
    Resolve provider list (handle 'all' option).

    Args:
        requested: List of requested providers

    Returns:
        List of actual provider names
    """
    if CloudProvider.ALL in requested:
        return ["aws", "gcp", "azure"]  # All providers now supported
    return [p.value for p in requested]


async def scan_aws_resources(scan_id: str) -> Dict[str, Any]:
    """
    Scan AWS resources.

    Args:
        scan_id: Scan identifier

    Returns:
        Dict with AWS scan results
    """
    try:
        # Update progress
        scans[scan_id]['progress']['aws'] = 10
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'aws',
            'status': 'running',
            'progress': 10,
            'message': 'Starting AWS resource discovery...'
        })

        # Initialize AWS discovery
        discovery = AWSDiscoveryEngine(region='us-east-1')

        # Test connection
        scans[scan_id]['progress']['aws'] = 20
        connection = discovery.test_connection()
        if not connection['success']:
            raise Exception(f"AWS connection failed: {connection.get('error')}")

        await ws_manager.send_scan_update(scan_id, {
            'provider': 'aws',
            'status': 'running',
            'progress': 20,
            'message': 'AWS connection established'
        })

        # Discover all resources
        scans[scan_id]['progress']['aws'] = 40
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'aws',
            'status': 'running',
            'progress': 40,
            'message': 'Discovering AWS resources...'
        })

        resources = discovery.discover_all_resources()

        # Flatten resources
        all_resources = []
        for resource_type, resource_list in resources.items():
            all_resources.extend(resource_list)

        scans[scan_id]['progress']['aws'] = 100
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'aws',
            'status': 'completed',
            'progress': 100,
            'message': f'AWS scan complete: {len(all_resources)} resources found'
        })

        return {
            'success': True,
            'resources': all_resources,
            'count': len(all_resources)
        }

    except Exception as e:
        logger.error(f"AWS scan failed: {e}")
        scans[scan_id]['errors'].append(f"AWS: {str(e)}")
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'aws',
            'status': 'failed',
            'progress': 0,
            'message': f'AWS scan failed: {str(e)}'
        })
        return {
            'success': False,
            'error': str(e),
            'resources': [],
            'count': 0
        }


async def scan_gcp_resources(scan_id: str) -> Dict[str, Any]:
    """
    Scan GCP resources.

    Args:
        scan_id: Scan identifier

    Returns:
        Dict with GCP scan results
    """
    try:
        # Update progress
        scans[scan_id]['progress']['gcp'] = 10
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'gcp',
            'status': 'running',
            'progress': 10,
            'message': 'Starting GCP resource discovery...'
        })

        # Initialize GCP discovery
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            raise Exception("GCP_PROJECT_ID not configured")

        discovery = GCPDiscoveryEngine(project_id=project_id)

        # Test connection
        scans[scan_id]['progress']['gcp'] = 20
        connection = discovery.test_connection()
        if not connection['success']:
            raise Exception(f"GCP connection failed: {connection.get('error')}")

        await ws_manager.send_scan_update(scan_id, {
            'provider': 'gcp',
            'status': 'running',
            'progress': 20,
            'message': 'GCP connection established'
        })

        # Discover all resources
        scans[scan_id]['progress']['gcp'] = 40
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'gcp',
            'status': 'running',
            'progress': 40,
            'message': 'Discovering GCP resources...'
        })

        resources = discovery.discover_all_resources()

        # Flatten resources
        all_resources = []
        for resource_type, resource_list in resources.items():
            all_resources.extend(resource_list)

        scans[scan_id]['progress']['gcp'] = 100
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'gcp',
            'status': 'completed',
            'progress': 100,
            'message': f'GCP scan complete: {len(all_resources)} resources found'
        })

        return {
            'success': True,
            'resources': all_resources,
            'count': len(all_resources)
        }

    except Exception as e:
        logger.error(f"GCP scan failed: {e}")
        scans[scan_id]['errors'].append(f"GCP: {str(e)}")
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'gcp',
            'status': 'failed',
            'progress': 0,
            'message': f'GCP scan failed: {str(e)}'
        })
        return {
            'success': False,
            'error': str(e),
            'resources': [],
            'count': 0
        }


async def scan_azure_resources(scan_id: str) -> Dict[str, Any]:
    """
    Scan Azure resources.

    Args:
        scan_id: Scan identifier

    Returns:
        Dict with Azure scan results
    """
    try:
        # Update progress
        scans[scan_id]['progress']['azure'] = 10
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'azure',
            'status': 'running',
            'progress': 10,
            'message': 'Starting Azure resource discovery...'
        })

        # Initialize Azure discovery
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if not subscription_id:
            raise Exception("AZURE_SUBSCRIPTION_ID not configured")

        discovery = AzureDiscoveryEngine(subscription_id=subscription_id)

        # Test connection
        scans[scan_id]['progress']['azure'] = 20
        connection = discovery.test_connection()
        if not connection['success']:
            raise Exception(f"Azure connection failed: {connection.get('error')}")

        await ws_manager.send_scan_update(scan_id, {
            'provider': 'azure',
            'status': 'running',
            'progress': 20,
            'message': 'Azure connection established'
        })

        # Discover all resources
        scans[scan_id]['progress']['azure'] = 40
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'azure',
            'status': 'running',
            'progress': 40,
            'message': 'Discovering Azure resources...'
        })

        resources = discovery.discover_all_resources()

        # Flatten resources
        all_resources = []
        for resource_type, resource_list in resources.items():
            all_resources.extend(resource_list)

        scans[scan_id]['progress']['azure'] = 100
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'azure',
            'status': 'completed',
            'progress': 100,
            'message': f'Azure scan complete: {len(all_resources)} resources found'
        })

        return {
            'success': True,
            'resources': all_resources,
            'count': len(all_resources)
        }

    except Exception as e:
        logger.error(f"Azure scan failed: {e}")
        scans[scan_id]['errors'].append(f"Azure: {str(e)}")
        await ws_manager.send_scan_update(scan_id, {
            'provider': 'azure',
            'status': 'failed',
            'progress': 0,
            'message': f'Azure scan failed: {str(e)}'
        })
        return {
            'success': False,
            'error': str(e),
            'resources': [],
            'count': 0
        }


async def run_multi_cloud_scan(scan_id: str, providers: List[str]):
    """
    Run multi-cloud resource discovery scan.

    Args:
        scan_id: Scan identifier
        providers: List of providers to scan
    """
    try:
        scans[scan_id]['status'] = 'running'
        scans[scan_id]['started_at'] = datetime.utcnow().isoformat()

        all_resources = []

        # Scan each provider
        for provider in providers:
            if provider == 'aws':
                result = await scan_aws_resources(scan_id)
                if result['success']:
                    all_resources.extend(result['resources'])

            elif provider == 'gcp':
                result = await scan_gcp_resources(scan_id)
                if result['success']:
                    all_resources.extend(result['resources'])

            elif provider == 'azure':
                result = await scan_azure_resources(scan_id)
                if result['success']:
                    all_resources.extend(result['resources'])

        # Store results
        resources_cache[scan_id] = all_resources
        scans[scan_id]['total_resources'] = len(all_resources)
        scans[scan_id]['status'] = 'completed'
        scans[scan_id]['completed_at'] = datetime.utcnow().isoformat()

        # Send final update
        await ws_manager.send_scan_update(scan_id, {
            'status': 'completed',
            'total_resources': len(all_resources),
            'message': f'Multi-cloud scan complete: {len(all_resources)} resources discovered'
        })

        logger.info(f"Multi-cloud scan {scan_id} completed: {len(all_resources)} resources")

    except Exception as e:
        logger.error(f"Multi-cloud scan {scan_id} failed: {e}")
        scans[scan_id]['status'] = 'failed'
        scans[scan_id]['errors'].append(str(e))
        scans[scan_id]['completed_at'] = datetime.utcnow().isoformat()

        await ws_manager.send_scan_update(scan_id, {
            'status': 'failed',
            'message': f'Scan failed: {str(e)}'
        })


@router.post("/scan", response_model=Dict[str, Any])
async def start_multi_cloud_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Start a multi-cloud resource discovery scan.

    Args:
        request: Scan configuration
        background_tasks: FastAPI background tasks

    Returns:
        Scan ID and initial status
    """
    scan_id = str(uuid.uuid4())
    providers = resolve_providers(request.providers)

    # Initialize scan record
    scans[scan_id] = {
        'scan_id': scan_id,
        'status': 'pending',
        'providers': providers,
        'progress': {provider: 0 for provider in providers},
        'started_at': None,
        'completed_at': None,
        'total_resources': 0,
        'errors': []
    }

    # Start scan in background
    background_tasks.add_task(run_multi_cloud_scan, scan_id, providers)

    logger.info(f"Started multi-cloud scan {scan_id} for providers: {providers}")

    return {
        'scan_id': scan_id,
        'status': 'pending',
        'providers': providers,
        'message': f'Multi-cloud scan started for: {", ".join(providers)}'
    }


@router.get("/scan/{scan_id}", response_model=ScanStatus)
async def get_scan_status(scan_id: str) -> ScanStatus:
    """
    Get status of a running or completed scan.

    Args:
        scan_id: Scan identifier

    Returns:
        Current scan status
    """
    if scan_id not in scans:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan = scans[scan_id]
    return ScanStatus(**scan)


@router.get("/resources", response_model=List[Dict[str, Any]])
async def get_all_resources(
    provider: Optional[CloudProvider] = None,
    resource_type: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get all discovered resources across clouds.

    Args:
        provider: Filter by cloud provider
        resource_type: Filter by resource type
        region: Filter by region
        limit: Maximum results to return

    Returns:
        List of resources
    """
    # Get resources from most recent scan
    if not resources_cache:
        return []

    latest_scan_id = max(resources_cache.keys(), key=lambda k: scans[k]['started_at'] or '')
    resources = resources_cache[latest_scan_id]

    # Apply filters
    if provider and provider != CloudProvider.ALL:
        resources = [r for r in resources if r.get('cloud_provider') == provider.value]

    if resource_type:
        resources = [r for r in resources if r.get('resource_type') == resource_type]

    if region:
        resources = [r for r in resources if r.get('region') == region]

    return resources[:limit]


@router.get("/summary", response_model=MultiCloudSummary)
async def get_multi_cloud_summary() -> MultiCloudSummary:
    """
    Get summary of all resources across cloud providers.

    Returns:
        Multi-cloud resource summary
    """
    if not resources_cache:
        return MultiCloudSummary(
            total_resources=0,
            providers={},
            scan_time=datetime.utcnow().isoformat()
        )

    # Get resources from most recent scan
    latest_scan_id = max(resources_cache.keys(), key=lambda k: scans[k]['started_at'] or '')
    resources = resources_cache[latest_scan_id]

    # Group by provider
    providers_summary = {}

    for provider in ['aws', 'gcp', 'azure']:
        provider_resources = [r for r in resources if r.get('cloud_provider') == provider]

        if provider_resources:
            # Count by resource type
            resource_counts = {}
            regions = set()

            for resource in provider_resources:
                rt = resource.get('resource_type', 'unknown')
                resource_counts[rt] = resource_counts.get(rt, 0) + 1

                if resource.get('region'):
                    regions.add(resource['region'])

            providers_summary[provider] = ResourceSummary(
                cloud_provider=provider,
                total_resources=len(provider_resources),
                resource_counts=resource_counts,
                regions=sorted(list(regions)),
                last_scan=scans[latest_scan_id]['completed_at']
            )

    return MultiCloudSummary(
        total_resources=len(resources),
        providers=providers_summary,
        scan_time=datetime.utcnow().isoformat()
    )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Service health status
    """
    return {
        'status': 'healthy',
        'service': 'multi-cloud-discovery',
        'providers': ['aws', 'gcp'],
        'active_scans': len([s for s in scans.values() if s['status'] == 'running']),
        'total_scans': len(scans),
        'timestamp': datetime.utcnow().isoformat()
    }
