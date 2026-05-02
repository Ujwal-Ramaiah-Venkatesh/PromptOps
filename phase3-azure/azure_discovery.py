"""
Azure Resource Discovery Module
================================

Microsoft Azure resource scanning.
Phase 3 - Multi-Cloud Support

Author: PromptOps Team
Date: 2026-05-01
Phase: 3 - Multi-Cloud
"""

from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.resource import ResourceManagementClient
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class AzureDiscoveryEngine:
    """
    Discovers and scans Azure resources.

    Supports:
    - Virtual Machines
    - Storage Accounts
    - SQL Databases
    - Resource Groups
    """

    def __init__(
        self,
        subscription_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """
        Initialize Azure discovery engine.

        Args:
            subscription_id: Azure subscription ID
            tenant_id: Azure tenant ID
            client_id: Service principal client ID
            client_secret: Service principal client secret
        """
        self.subscription_id = subscription_id or os.getenv('AZURE_SUBSCRIPTION_ID')
        self.tenant_id = tenant_id or os.getenv('AZURE_TENANT_ID')
        self.client_id = client_id or os.getenv('AZURE_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('AZURE_CLIENT_SECRET')

        if not self.subscription_id:
            raise ValueError("AZURE_SUBSCRIPTION_ID must be set in environment or passed as parameter")

        # Initialize credential
        if self.tenant_id and self.client_id and self.client_secret:
            self.credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        else:
            # Fall back to default credential (uses managed identity, CLI, etc.)
            self.credential = DefaultAzureCredential()

        # Initialize management clients
        self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
        self.storage_client = StorageManagementClient(self.credential, self.subscription_id)
        self.sql_client = SqlManagementClient(self.credential, self.subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)

        logger.info(f"Azure Discovery Engine initialized for subscription: {self.subscription_id}")

    def test_connection(self) -> Dict[str, Any]:
        """
        Test Azure connection and credentials.

        Returns:
            Dict with connection status and subscription info
        """
        try:
            # Try to list resource groups (lightweight operation)
            resource_groups = list(self.resource_client.resource_groups.list())

            return {
                'success': True,
                'subscription_id': self.subscription_id,
                'resource_groups_count': len(resource_groups),
                'message': 'Azure connection successful'
            }
        except Exception as e:
            logger.error(f"Azure connection test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Azure connection failed'
            }

    def discover_virtual_machines(self) -> List[Dict[str, Any]]:
        """
        Discover all Virtual Machines.

        Returns:
            List of VM dictionaries
        """
        vms = []

        try:
            # List all VMs across all resource groups
            vm_list = self.compute_client.virtual_machines.list_all()

            for vm in vm_list:
                # Parse resource group from ID
                resource_group = vm.id.split('/')[4] if '/' in vm.id else None

                # Extract tags
                tags = dict(vm.tags) if vm.tags else {}

                # Get VM size and status
                vm_size = vm.hardware_profile.vm_size if vm.hardware_profile else None

                # Get location/region
                location = vm.location

                # Get network info
                network_interfaces = []
                if vm.network_profile and vm.network_profile.network_interfaces:
                    for nic_ref in vm.network_profile.network_interfaces:
                        network_interfaces.append({
                            'id': nic_ref.id,
                            'primary': nic_ref.primary
                        })

                # Get OS disk info
                os_disk_name = vm.storage_profile.os_disk.name if vm.storage_profile and vm.storage_profile.os_disk else None

                vms.append({
                    'resource_id': vm.id,
                    'resource_type': 'azure_virtual_machine',
                    'name': vm.name,
                    'cloud_provider': 'azure',
                    'status': vm.provisioning_state,
                    'vm_size': vm_size,
                    'location': location,
                    'region': location,  # Azure uses location = region
                    'resource_group': resource_group,
                    'tags': tags,
                    'network_interfaces': network_interfaces,
                    'os_disk': os_disk_name,
                    'os_type': vm.storage_profile.os_disk.os_type if vm.storage_profile and vm.storage_profile.os_disk else None,
                    'discovered_at': datetime.utcnow().isoformat(),
                    'subscription_id': self.subscription_id
                })

            logger.info(f"Discovered {len(vms)} Virtual Machines")
            return vms

        except Exception as e:
            logger.error(f"Failed to discover Virtual Machines: {e}")
            return []

    def discover_storage_accounts(self) -> List[Dict[str, Any]]:
        """
        Discover all Storage Accounts.

        Returns:
            List of storage account dictionaries
        """
        storage_accounts = []

        try:
            # List all storage accounts
            account_list = self.storage_client.storage_accounts.list()

            for account in account_list:
                # Parse resource group from ID
                resource_group = account.id.split('/')[4] if '/' in account.id else None

                # Extract tags
                tags = dict(account.tags) if account.tags else {}

                # Get account properties
                sku_name = account.sku.name if account.sku else None
                kind = account.kind
                location = account.location

                # Get primary endpoints
                primary_endpoints = {}
                if account.primary_endpoints:
                    primary_endpoints = {
                        'blob': account.primary_endpoints.blob,
                        'queue': account.primary_endpoints.queue,
                        'table': account.primary_endpoints.table,
                        'file': account.primary_endpoints.file
                    }

                storage_accounts.append({
                    'resource_id': account.id,
                    'resource_type': 'azure_storage_account',
                    'name': account.name,
                    'cloud_provider': 'azure',
                    'status': account.status_of_primary if hasattr(account, 'status_of_primary') else 'available',
                    'location': location,
                    'region': location,
                    'resource_group': resource_group,
                    'sku': sku_name,
                    'kind': kind,
                    'tags': tags,
                    'primary_endpoints': primary_endpoints,
                    'https_only': account.enable_https_traffic_only if hasattr(account, 'enable_https_traffic_only') else False,
                    'created_time': account.creation_time.isoformat() if account.creation_time else None,
                    'discovered_at': datetime.utcnow().isoformat(),
                    'subscription_id': self.subscription_id
                })

            logger.info(f"Discovered {len(storage_accounts)} Storage Accounts")
            return storage_accounts

        except Exception as e:
            logger.error(f"Failed to discover Storage Accounts: {e}")
            return []

    def discover_sql_servers(self) -> List[Dict[str, Any]]:
        """
        Discover all SQL Servers and Databases.

        Returns:
            List of SQL server/database dictionaries
        """
        sql_resources = []

        try:
            # List all SQL servers
            server_list = self.sql_client.servers.list()

            for server in server_list:
                # Parse resource group from ID
                resource_group = server.id.split('/')[4] if '/' in server.id else None

                # Extract tags
                tags = dict(server.tags) if server.tags else {}

                # Server info
                sql_resources.append({
                    'resource_id': server.id,
                    'resource_type': 'azure_sql_server',
                    'name': server.name,
                    'cloud_provider': 'azure',
                    'status': server.state if hasattr(server, 'state') else 'Ready',
                    'location': server.location,
                    'region': server.location,
                    'resource_group': resource_group,
                    'tags': tags,
                    'version': server.version,
                    'administrator_login': server.administrator_login,
                    'fully_qualified_domain_name': server.fully_qualified_domain_name if hasattr(server, 'fully_qualified_domain_name') else None,
                    'discovered_at': datetime.utcnow().isoformat(),
                    'subscription_id': self.subscription_id
                })

                # List databases for this server
                try:
                    database_list = self.sql_client.databases.list_by_server(
                        resource_group_name=resource_group,
                        server_name=server.name
                    )

                    for db in database_list:
                        # Skip system database 'master'
                        if db.name.lower() == 'master':
                            continue

                        db_tags = dict(db.tags) if db.tags else {}

                        sql_resources.append({
                            'resource_id': db.id,
                            'resource_type': 'azure_sql_database',
                            'name': f"{server.name}/{db.name}",
                            'cloud_provider': 'azure',
                            'status': db.status if hasattr(db, 'status') else 'Online',
                            'location': db.location,
                            'region': db.location,
                            'resource_group': resource_group,
                            'tags': db_tags,
                            'server_name': server.name,
                            'database_name': db.name,
                            'sku': db.sku.name if db.sku else None,
                            'max_size_bytes': db.max_size_bytes if hasattr(db, 'max_size_bytes') else None,
                            'creation_date': db.creation_date.isoformat() if hasattr(db, 'creation_date') and db.creation_date else None,
                            'discovered_at': datetime.utcnow().isoformat(),
                            'subscription_id': self.subscription_id
                        })
                except Exception as e:
                    logger.warning(f"Failed to list databases for server {server.name}: {e}")

            logger.info(f"Discovered {len(sql_resources)} SQL resources")
            return sql_resources

        except Exception as e:
            logger.error(f"Failed to discover SQL Servers: {e}")
            return []

    def discover_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover all supported Azure resources.

        Returns:
            Dictionary with resource types as keys and resource lists as values
        """
        logger.info(f"Starting full Azure resource discovery in subscription: {self.subscription_id}")

        resources = {
            'virtual_machines': self.discover_virtual_machines(),
            'storage_accounts': self.discover_storage_accounts(),
            'sql_resources': self.discover_sql_servers()
        }

        total_count = sum(len(resources[key]) for key in resources)
        logger.info(f"Azure discovery complete: {total_count} total resources found")

        return resources

    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of discovered Azure resources.

        Returns:
            Dictionary with resource counts and summary info
        """
        resources = self.discover_all_resources()

        return {
            'cloud_provider': 'azure',
            'subscription_id': self.subscription_id,
            'discovery_time': datetime.utcnow().isoformat(),
            'resource_counts': {
                'virtual_machines': len(resources['virtual_machines']),
                'storage_accounts': len(resources['storage_accounts']),
                'sql_resources': len(resources['sql_resources'])
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
    print("  Azure Resource Discovery Test")
    print("  Phase 3 - Multi-Cloud Support")
    print("=" * 60)

    try:
        # Initialize discovery engine
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if not subscription_id:
            print("\n❌ Error: AZURE_SUBSCRIPTION_ID not set")
            print("\nSet environment variables:")
            print("  export AZURE_SUBSCRIPTION_ID='your-subscription-id'")
            print("  export AZURE_TENANT_ID='your-tenant-id'")
            print("  export AZURE_CLIENT_ID='your-client-id'")
            print("  export AZURE_CLIENT_SECRET='your-client-secret'")
            exit(1)

        discovery = AzureDiscoveryEngine(subscription_id=subscription_id)

        # Test connection
        print("\n[1] Testing Azure connection...")
        connection = discovery.test_connection()
        if connection['success']:
            print(f"✅ Connected to Azure Subscription: {connection['subscription_id']}")
            print(f"   Resource groups: {connection['resource_groups_count']}")
        else:
            print(f"❌ Connection failed: {connection['error']}")
            exit(1)

        # Discover all resources
        print("\n[2] Discovering Azure resources...")
        summary = discovery.get_resource_summary()

        print(f"\n📊 Discovery Summary:")
        print(f"   Cloud Provider: {summary['cloud_provider'].upper()}")
        print(f"   Subscription ID: {summary['subscription_id']}")
        print(f"   Total Resources: {summary['total_resources']}")
        print(f"\n   Resource Breakdown:")
        for resource_type, count in summary['resource_counts'].items():
            print(f"   - {resource_type}: {count}")

        # Show sample resources
        if summary['total_resources'] > 0:
            print(f"\n📋 Sample Resources:")
            resources = summary['resources']

            if resources['virtual_machines']:
                print(f"\n   Virtual Machines ({len(resources['virtual_machines'])}):")
                for vm in resources['virtual_machines'][:3]:
                    print(f"   - {vm['name']} ({vm['vm_size']}) - {vm['status']} - {vm['location']}")

            if resources['storage_accounts']:
                print(f"\n   Storage Accounts ({len(resources['storage_accounts'])}):")
                for account in resources['storage_accounts'][:3]:
                    print(f"   - {account['name']} ({account['sku']}) - {account['kind']} - {account['location']}")

            if resources['sql_resources']:
                print(f"\n   SQL Resources ({len(resources['sql_resources'])}):")
                for sql in resources['sql_resources'][:3]:
                    print(f"   - {sql['name']} ({sql['resource_type']}) - {sql['status']} - {sql['location']}")
        else:
            print("\n⚠️  No resources found in this subscription.")
            print("   Create test resources to see discovery in action:")
            print("   az vm create --resource-group promptops-dev-rg --name test-vm --image UbuntuLTS --size Standard_B1s")

        print("\n" + "=" * 60)
        print("✅ Azure Discovery Test Complete")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Set Azure environment variables (AZURE_SUBSCRIPTION_ID, etc.)")
        print("2. Run: az login")
        print("3. Ensure service principal has Reader permissions")
        print("4. Check subscription is active")
