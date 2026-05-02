"""
GCP Resource Discovery Module
==============================

Google Cloud Platform resource scanning.
Phase 3 - Multi-Cloud Support

Author: PromptOps Team
Date: 2026-05-01
Phase: 3 - Multi-Cloud
"""

from google.cloud import compute_v1
from google.cloud import storage
from google.api_core import exceptions
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class GCPDiscoveryEngine:
    """
    Discovers and scans GCP resources.

    Supports:
    - Compute Engine (VMs)
    - Cloud Storage (Buckets)
    - Cloud SQL (Databases) - Coming soon
    - Cloud Functions - Coming soon
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize GCP discovery engine.

        Args:
            project_id: GCP project ID (default: from GOOGLE_CLOUD_PROJECT env)
        """
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID must be set in environment or passed as parameter")

        # Initialize clients
        self.compute_client = compute_v1.InstancesClient()
        self.zones_client = compute_v1.ZonesClient()
        self.storage_client = storage.Client(project=self.project_id)

        logger.info(f"GCP Discovery Engine initialized for project: {self.project_id}")

    def test_connection(self) -> Dict[str, Any]:
        """
        Test GCP connection and credentials.

        Returns:
            Dict with connection status and project info
        """
        try:
            # Try to list zones (lightweight operation)
            zones_list = list(self.zones_client.list(project=self.project_id))

            return {
                'success': True,
                'project_id': self.project_id,
                'zones_available': len(zones_list),
                'message': 'GCP connection successful'
            }
        except Exception as e:
            logger.error(f"GCP connection test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'GCP connection failed'
            }

    def discover_compute_instances(self) -> List[Dict[str, Any]]:
        """
        Discover all Compute Engine VM instances.

        Returns:
            List of VM instance dictionaries
        """
        instances = []

        try:
            # Get all zones
            zones = self.zones_client.list(project=self.project_id)

            # Scan each zone
            for zone in zones:
                zone_name = zone.name

                try:
                    # List instances in this zone
                    zone_instances = self.compute_client.list(
                        project=self.project_id,
                        zone=zone_name
                    )

                    for instance in zone_instances:
                        # Extract labels (GCP's version of tags)
                        labels = dict(instance.labels) if instance.labels else {}

                        # Extract network info
                        network_interfaces = []
                        for nic in instance.network_interfaces:
                            network_interfaces.append({
                                'network': nic.network.split('/')[-1] if nic.network else None,
                                'internal_ip': nic.network_i_p if hasattr(nic, 'network_i_p') else None,
                                'external_ip': nic.access_configs[0].nat_i_p if nic.access_configs else None
                            })

                        instances.append({
                            'resource_id': str(instance.id),
                            'resource_type': 'gcp_compute_instance',
                            'name': instance.name,
                            'cloud_provider': 'gcp',
                            'status': instance.status,
                            'machine_type': instance.machine_type.split('/')[-1] if instance.machine_type else None,
                            'zone': zone_name,
                            'region': zone.region.split('/')[-1] if zone.region else zone_name[:-2],
                            'labels': labels,
                            'network_interfaces': network_interfaces,
                            'disks': [disk.source.split('/')[-1] if disk.source else None for disk in instance.disks],
                            'creation_timestamp': instance.creation_timestamp,
                            'discovered_at': datetime.utcnow().isoformat(),
                            'project_id': self.project_id
                        })

                except exceptions.NotFound:
                    # Zone exists but no instances
                    pass
                except Exception as e:
                    logger.error(f"Error scanning zone {zone_name}: {e}")

            logger.info(f"Discovered {len(instances)} Compute Engine instances")
            return instances

        except Exception as e:
            logger.error(f"Failed to discover Compute Engine instances: {e}")
            return []

    def discover_storage_buckets(self) -> List[Dict[str, Any]]:
        """
        Discover all Cloud Storage buckets.

        Returns:
            List of bucket dictionaries
        """
        buckets = []

        try:
            # List all buckets in project
            bucket_list = self.storage_client.list_buckets()

            for bucket in bucket_list:
                # Get bucket metadata
                labels = dict(bucket.labels) if bucket.labels else {}

                # Calculate size (approximate)
                total_size = 0
                blob_count = 0
                try:
                    blobs = list(bucket.list_blobs(max_results=1000))
                    blob_count = len(blobs)
                    total_size = sum(blob.size for blob in blobs if blob.size)
                except:
                    pass

                buckets.append({
                    'resource_id': bucket.name,
                    'resource_type': 'gcp_storage_bucket',
                    'name': bucket.name,
                    'cloud_provider': 'gcp',
                    'location': bucket.location,
                    'region': bucket.location.lower(),
                    'storage_class': bucket.storage_class,
                    'created_time': bucket.time_created.isoformat() if bucket.time_created else None,
                    'labels': labels,
                    'size_bytes': total_size,
                    'object_count': blob_count,
                    'versioning_enabled': bucket.versioning_enabled,
                    'discovered_at': datetime.utcnow().isoformat(),
                    'project_id': self.project_id
                })

            logger.info(f"Discovered {len(buckets)} Cloud Storage buckets")
            return buckets

        except Exception as e:
            logger.error(f"Failed to discover Cloud Storage buckets: {e}")
            return []

    def discover_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover all supported GCP resources.

        Returns:
            Dictionary with resource types as keys and resource lists as values
        """
        logger.info(f"Starting full GCP resource discovery in project: {self.project_id}")

        resources = {
            'compute_instances': self.discover_compute_instances(),
            'storage_buckets': self.discover_storage_buckets()
        }

        total_count = sum(len(resources[key]) for key in resources)
        logger.info(f"GCP discovery complete: {total_count} total resources found")

        return resources

    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of discovered GCP resources.

        Returns:
            Dictionary with resource counts and summary info
        """
        resources = self.discover_all_resources()

        return {
            'cloud_provider': 'gcp',
            'project_id': self.project_id,
            'discovery_time': datetime.utcnow().isoformat(),
            'resource_counts': {
                'compute_instances': len(resources['compute_instances']),
                'storage_buckets': len(resources['storage_buckets'])
            },
            'total_resources': sum(len(resources[key]) for key in resources),
            'resources': resources
        }


# Test function
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("  GCP Resource Discovery Test")
    print("  Phase 3 - Multi-Cloud Support")
    print("=" * 60)

    try:
        # Initialize discovery engine
        project_id = os.getenv('GCP_PROJECT_ID', 'promptops-dev-123456')
        discovery = GCPDiscoveryEngine(project_id=project_id)

        # Test connection
        print("\n[1] Testing GCP connection...")
        connection = discovery.test_connection()
        if connection['success']:
            print(f"✅ Connected to GCP Project: {connection['project_id']}")
            print(f"   Available zones: {connection['zones_available']}")
        else:
            print(f"❌ Connection failed: {connection['error']}")
            exit(1)

        # Discover all resources
        print("\n[2] Discovering GCP resources...")
        summary = discovery.get_resource_summary()

        print(f"\n📊 Discovery Summary:")
        print(f"   Cloud Provider: {summary['cloud_provider'].upper()}")
        print(f"   Project ID: {summary['project_id']}")
        print(f"   Total Resources: {summary['total_resources']}")
        print(f"\n   Resource Breakdown:")
        for resource_type, count in summary['resource_counts'].items():
            print(f"   - {resource_type}: {count}")

        # Show sample resources
        if summary['total_resources'] > 0:
            print(f"\n📋 Sample Resources:")
            resources = summary['resources']

            if resources['compute_instances']:
                print(f"\n   Compute Engine Instances ({len(resources['compute_instances'])}):")
                for inst in resources['compute_instances'][:3]:
                    print(f"   - {inst['name']} ({inst['machine_type']}) - {inst['status']} - {inst['zone']}")

            if resources['storage_buckets']:
                print(f"\n   Cloud Storage Buckets ({len(resources['storage_buckets'])}):")
                for bucket in resources['storage_buckets'][:3]:
                    size_mb = bucket['size_bytes'] / (1024 * 1024) if bucket['size_bytes'] else 0
                    print(f"   - {bucket['name']} ({size_mb:.2f} MB, {bucket['object_count']} objects) - {bucket['location']}")
        else:
            print("\n⚠️  No resources found in this project.")
            print("   Create test resources to see discovery in action:")
            print("   gcloud compute instances create test-vm --zone=us-central1-a --machine-type=f1-micro")

        print("\n" + "=" * 60)
        print("✅ GCP Discovery Test Complete")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Set GCP_PROJECT_ID environment variable")
        print("2. Run: gcloud auth application-default login")
        print("3. Ensure APIs are enabled (compute, storage)")
        print("4. Check service account has viewer permissions")
