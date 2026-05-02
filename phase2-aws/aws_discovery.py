"""
AWS Resource Discovery Module
==============================

Real AWS resource scanning using boto3 (Phase 2).
Replaces mock discovery with actual AWS API calls.

Author: PromptOps Team
Date: 2026-04-30
Phase: 2 - Real AWS Integration
"""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AWSDiscoveryEngine:
    """
    Discovers and scans AWS resources across EC2, RDS, S3, and more.
    Uses boto3 to connect to real AWS account (Free Tier compatible).
    """

    def __init__(self, region: str = 'us-east-1', profile: Optional[str] = None):
        """
        Initialize AWS discovery engine.

        Args:
            region: AWS region to scan (default: us-east-1)
            profile: AWS CLI profile name (default: None uses default profile)
        """
        self.region = region
        self.profile = profile

        # Initialize boto3 session
        if profile:
            self.session = boto3.Session(profile_name=profile, region_name=region)
        else:
            self.session = boto3.Session(region_name=region)

        # Create service clients
        self.ec2_client = self.session.client('ec2')
        self.rds_client = self.session.client('rds')
        self.s3_client = self.session.client('s3')
        self.lambda_client = self.session.client('lambda')
        self.elb_client = self.session.client('elbv2')

        logger.info(f"AWS Discovery Engine initialized for region: {region}")


    def test_connection(self) -> Dict[str, Any]:
        """
        Test AWS connection and credentials.

        Returns:
            Dict with connection status and account info
        """
        try:
            # Get caller identity
            sts_client = self.session.client('sts')
            identity = sts_client.get_caller_identity()

            return {
                'success': True,
                'account_id': identity['Account'],
                'user_arn': identity['Arn'],
                'region': self.region,
                'message': 'AWS connection successful'
            }
        except Exception as e:
            logger.error(f"AWS connection test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'AWS connection failed'
            }


    def discover_ec2_instances(self) -> List[Dict[str, Any]]:
        """
        Discover all EC2 instances in the account.

        Returns:
            List of EC2 instance dictionaries
        """
        instances = []

        try:
            response = self.ec2_client.describe_instances()

            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    # Extract tags
                    tags = {tag['Key']: tag['Value']
                           for tag in instance.get('Tags', [])}

                    instances.append({
                        'resource_id': instance['InstanceId'],
                        'resource_type': 'ec2_instance',
                        'name': tags.get('Name', instance['InstanceId']),
                        'state': instance['State']['Name'],
                        'instance_type': instance['InstanceType'],
                        'availability_zone': instance['Placement']['AvailabilityZone'],
                        'private_ip': instance.get('PrivateIpAddress'),
                        'public_ip': instance.get('PublicIpAddress'),
                        'launch_time': instance['LaunchTime'].isoformat(),
                        'tags': tags,
                        'vpc_id': instance.get('VpcId'),
                        'subnet_id': instance.get('SubnetId'),
                        'security_groups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])],
                        'region': self.region,
                        'discovered_at': datetime.utcnow().isoformat()
                    })

            logger.info(f"Discovered {len(instances)} EC2 instances")
            return instances

        except ClientError as e:
            logger.error(f"Failed to discover EC2 instances: {e}")
            return []


    def discover_rds_instances(self) -> List[Dict[str, Any]]:
        """
        Discover all RDS database instances.

        Returns:
            List of RDS instance dictionaries
        """
        databases = []

        try:
            response = self.rds_client.describe_db_instances()

            for db in response.get('DBInstances', []):
                # Get tags
                tags_response = self.rds_client.list_tags_for_resource(
                    ResourceName=db['DBInstanceArn']
                )
                tags = {tag['Key']: tag['Value']
                       for tag in tags_response.get('TagList', [])}

                databases.append({
                    'resource_id': db['DBInstanceIdentifier'],
                    'resource_type': 'rds_instance',
                    'name': db['DBInstanceIdentifier'],
                    'engine': db['Engine'],
                    'engine_version': db['EngineVersion'],
                    'instance_class': db['DBInstanceClass'],
                    'status': db['DBInstanceStatus'],
                    'endpoint': db.get('Endpoint', {}).get('Address'),
                    'port': db.get('Endpoint', {}).get('Port'),
                    'allocated_storage': db['AllocatedStorage'],
                    'availability_zone': db['AvailabilityZone'],
                    'multi_az': db['MultiAZ'],
                    'backup_retention': db['BackupRetentionPeriod'],
                    'tags': tags,
                    'vpc_id': db.get('DBSubnetGroup', {}).get('VpcId'),
                    'region': self.region,
                    'discovered_at': datetime.utcnow().isoformat()
                })

            logger.info(f"Discovered {len(databases)} RDS instances")
            return databases

        except ClientError as e:
            logger.error(f"Failed to discover RDS instances: {e}")
            return []


    def discover_s3_buckets(self) -> List[Dict[str, Any]]:
        """
        Discover all S3 buckets.

        Returns:
            List of S3 bucket dictionaries
        """
        buckets = []

        try:
            response = self.s3_client.list_buckets()

            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']

                # Get bucket location
                try:
                    location = self.s3_client.get_bucket_location(
                        Bucket=bucket_name
                    )
                    bucket_region = location.get('LocationConstraint') or 'us-east-1'
                except:
                    bucket_region = 'unknown'

                # Get bucket tags (if accessible)
                tags = {}
                try:
                    tags_response = self.s3_client.get_bucket_tagging(
                        Bucket=bucket_name
                    )
                    tags = {tag['Key']: tag['Value']
                           for tag in tags_response.get('TagSet', [])}
                except:
                    pass

                # Get bucket size (approximation via list objects)
                size = 0
                object_count = 0
                try:
                    objects = self.s3_client.list_objects_v2(
                        Bucket=bucket_name,
                        MaxKeys=1000
                    )
                    object_count = objects.get('KeyCount', 0)
                    for obj in objects.get('Contents', []):
                        size += obj['Size']
                except:
                    pass

                buckets.append({
                    'resource_id': bucket_name,
                    'resource_type': 's3_bucket',
                    'name': bucket_name,
                    'creation_date': bucket['CreationDate'].isoformat(),
                    'region': bucket_region,
                    'size_bytes': size,
                    'object_count': object_count,
                    'tags': tags,
                    'discovered_at': datetime.utcnow().isoformat()
                })

            logger.info(f"Discovered {len(buckets)} S3 buckets")
            return buckets

        except ClientError as e:
            logger.error(f"Failed to discover S3 buckets: {e}")
            return []


    def discover_lambda_functions(self) -> List[Dict[str, Any]]:
        """
        Discover all Lambda functions.

        Returns:
            List of Lambda function dictionaries
        """
        functions = []

        try:
            response = self.lambda_client.list_functions()

            for func in response.get('Functions', []):
                # Get tags
                tags = {}
                try:
                    tags_response = self.lambda_client.list_tags(
                        Resource=func['FunctionArn']
                    )
                    tags = tags_response.get('Tags', {})
                except:
                    pass

                functions.append({
                    'resource_id': func['FunctionName'],
                    'resource_type': 'lambda_function',
                    'name': func['FunctionName'],
                    'runtime': func['Runtime'],
                    'memory_size': func['MemorySize'],
                    'timeout': func['Timeout'],
                    'handler': func['Handler'],
                    'last_modified': func['LastModified'],
                    'tags': tags,
                    'region': self.region,
                    'discovered_at': datetime.utcnow().isoformat()
                })

            logger.info(f"Discovered {len(functions)} Lambda functions")
            return functions

        except ClientError as e:
            logger.error(f"Failed to discover Lambda functions: {e}")
            return []


    def discover_load_balancers(self) -> List[Dict[str, Any]]:
        """
        Discover all Application/Network Load Balancers.

        Returns:
            List of load balancer dictionaries
        """
        load_balancers = []

        try:
            response = self.elb_client.describe_load_balancers()

            for lb in response.get('LoadBalancers', []):
                # Get tags
                tags_response = self.elb_client.describe_tags(
                    ResourceArns=[lb['LoadBalancerArn']]
                )
                tags = {}
                for tag_desc in tags_response.get('TagDescriptions', []):
                    tags = {tag['Key']: tag['Value']
                           for tag in tag_desc.get('Tags', [])}

                load_balancers.append({
                    'resource_id': lb['LoadBalancerName'],
                    'resource_type': 'load_balancer',
                    'name': lb['LoadBalancerName'],
                    'lb_type': lb['Type'],
                    'scheme': lb['Scheme'],
                    'dns_name': lb['DNSName'],
                    'state': lb['State']['Code'],
                    'availability_zones': [az['ZoneName'] for az in lb.get('AvailabilityZones', [])],
                    'vpc_id': lb['VpcId'],
                    'tags': tags,
                    'region': self.region,
                    'discovered_at': datetime.utcnow().isoformat()
                })

            logger.info(f"Discovered {len(load_balancers)} load balancers")
            return load_balancers

        except ClientError as e:
            logger.error(f"Failed to discover load balancers: {e}")
            return []


    def discover_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover all supported AWS resources in one call.

        Returns:
            Dictionary with resource types as keys and resource lists as values
        """
        logger.info(f"Starting full resource discovery in region: {self.region}")

        resources = {
            'ec2_instances': self.discover_ec2_instances(),
            'rds_instances': self.discover_rds_instances(),
            's3_buckets': self.discover_s3_buckets(),
            'lambda_functions': self.discover_lambda_functions(),
            'load_balancers': self.discover_load_balancers()
        }

        total_count = sum(len(resources[key]) for key in resources)
        logger.info(f"Discovery complete: {total_count} total resources found")

        return resources


    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of discovered resources.

        Returns:
            Dictionary with resource counts and summary info
        """
        resources = self.discover_all_resources()

        return {
            'region': self.region,
            'discovery_time': datetime.utcnow().isoformat(),
            'resource_counts': {
                'ec2_instances': len(resources['ec2_instances']),
                'rds_instances': len(resources['rds_instances']),
                's3_buckets': len(resources['s3_buckets']),
                'lambda_functions': len(resources['lambda_functions']),
                'load_balancers': len(resources['load_balancers'])
            },
            'total_resources': sum(len(resources[key]) for key in resources),
            'resources': resources
        }


# Test function
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("  AWS Resource Discovery Test")
    print("  Phase 2 - Real AWS Integration")
    print("=" * 60)

    # Initialize discovery engine
    discovery = AWSDiscoveryEngine(region='us-east-1')

    # Test connection
    print("\n[1] Testing AWS connection...")
    connection = discovery.test_connection()
    if connection['success']:
        print(f"✅ Connected to AWS Account: {connection['account_id']}")
        print(f"   Region: {connection['region']}")
        print(f"   User: {connection['user_arn']}")
    else:
        print(f"❌ Connection failed: {connection['error']}")
        exit(1)

    # Discover all resources
    print("\n[2] Discovering AWS resources...")
    summary = discovery.get_resource_summary()

    print(f"\n📊 Discovery Summary:")
    print(f"   Region: {summary['region']}")
    print(f"   Total Resources: {summary['total_resources']}")
    print(f"\n   Resource Breakdown:")
    for resource_type, count in summary['resource_counts'].items():
        print(f"   - {resource_type}: {count}")

    # Show sample resources
    if summary['total_resources'] > 0:
        print(f"\n📋 Sample Resources:")
        resources = summary['resources']

        if resources['ec2_instances']:
            print(f"\n   EC2 Instances ({len(resources['ec2_instances'])}):")
            for inst in resources['ec2_instances'][:3]:
                print(f"   - {inst['name']} ({inst['instance_type']}) - {inst['state']}")

        if resources['rds_instances']:
            print(f"\n   RDS Instances ({len(resources['rds_instances'])}):")
            for db in resources['rds_instances'][:3]:
                print(f"   - {db['name']} ({db['engine']} {db['engine_version']}) - {db['status']}")

        if resources['s3_buckets']:
            print(f"\n   S3 Buckets ({len(resources['s3_buckets'])}):")
            for bucket in resources['s3_buckets'][:3]:
                size_mb = bucket['size_bytes'] / (1024 * 1024)
                print(f"   - {bucket['name']} ({size_mb:.2f} MB, {bucket['object_count']} objects)")
    else:
        print("\n⚠️  No resources found in this region.")
        print("   Create test resources with AWS Free Tier to see discovery in action.")

    print("\n" + "=" * 60)
    print("✅ AWS Discovery Test Complete")
    print("=" * 60)
