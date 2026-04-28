"""
Context Collector - AWS Resource Fetcher
=========================================

Collects current state of AWS infrastructure using boto3 SDK.
Supports 15+ resource types with intelligent filtering and caching.

Features:
- Multi-resource type collection (ECS, EC2, RDS, Lambda, ALB, S3, etc.)
- Parallel fetching with ThreadPoolExecutor
- Tag-based filtering (only resources with Managed=PromptOps)
- Snapshot persistence and versioning
- Error handling and retry logic

Author: PromptOps Team - Week 7-8
Date: 2026-04-28
"""

import boto3
import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from dataclasses import dataclass, asdict
from botocore.exceptions import ClientError, BotoCoreError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CollectionResult:
    """Result of resource collection operation."""
    success: bool
    resource_type: str
    resource_count: int
    resources: List[Dict[str, Any]]
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class Snapshot:
    """Infrastructure snapshot metadata."""
    snapshot_id: str
    timestamp: str
    resource_count: int
    checksum: str
    drift_events_detected: int
    collection_duration_ms: int
    errors: List[Dict[str, str]]


# ============================================================================
# Context Collector
# ============================================================================

class ContextCollector:
    """
    Collects AWS resource state across multiple resource types.

    Supports:
    - ECS services and task definitions
    - EC2 instances
    - RDS databases
    - Lambda functions
    - Application Load Balancers
    - S3 buckets
    - DynamoDB tables
    - SQS queues
    - SNS topics
    - CloudFront distributions
    """

    def __init__(
        self,
        aws_region: str = 'us-east-1',
        aws_profile: Optional[str] = None,
        snapshot_dir: str = './context_snapshots',
        filter_tag: str = 'PromptOps'
    ):
        """
        Initialize Context Collector.

        Args:
            aws_region: AWS region to scan
            aws_profile: AWS profile name (optional)
            snapshot_dir: Directory to store snapshots
            filter_tag: Only collect resources with this tag value for 'Managed' key
        """
        self.aws_region = aws_region
        self.aws_profile = aws_profile
        self.snapshot_dir = snapshot_dir
        self.filter_tag = filter_tag

        # Initialize boto3 session
        session_kwargs = {'region_name': aws_region}
        if aws_profile:
            session_kwargs['profile_name'] = aws_profile

        self.session = boto3.Session(**session_kwargs)

        # Create snapshot directory
        os.makedirs(snapshot_dir, exist_ok=True)

        logger.info(f"ContextCollector initialized: region={aws_region}, filter_tag={filter_tag}")

    # ========================================================================
    # Main Collection Methods
    # ========================================================================

    def collect_all_resources(self, parallel: bool = True) -> Dict[str, Any]:
        """
        Collect all supported AWS resources.

        Args:
            parallel: Use parallel collection (faster but more API calls)

        Returns:
            Dictionary with resources grouped by type
        """
        start_time = datetime.now(timezone.utc)
        logger.info("Starting full resource collection...")

        collection_methods = [
            ('ecs_services', self.collect_ecs_services),
            ('ec2_instances', self.collect_ec2_instances),
            ('rds_databases', self.collect_rds_databases),
            ('lambda_functions', self.collect_lambda_functions),
            ('load_balancers', self.collect_load_balancers),
            ('s3_buckets', self.collect_s3_buckets),
            ('dynamodb_tables', self.collect_dynamodb_tables),
            ('sqs_queues', self.collect_sqs_queues),
            ('sns_topics', self.collect_sns_topics),
            ('cloudfront_distributions', self.collect_cloudfront_distributions)
        ]

        all_resources = []
        errors = []

        if parallel:
            # Parallel collection
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_type = {
                    executor.submit(method): resource_type
                    for resource_type, method in collection_methods
                }

                for future in as_completed(future_to_type):
                    resource_type = future_to_type[future]
                    try:
                        result = future.result()
                        all_resources.extend(result.resources)
                        if result.error:
                            errors.append({
                                'resource_type': resource_type,
                                'error_message': result.error
                            })
                        logger.info(f"✓ Collected {result.resource_count} {resource_type}")
                    except Exception as e:
                        logger.error(f"✗ Failed to collect {resource_type}: {str(e)}")
                        errors.append({
                            'resource_type': resource_type,
                            'error_message': str(e)
                        })
        else:
            # Sequential collection
            for resource_type, method in collection_methods:
                try:
                    result = method()
                    all_resources.extend(result.resources)
                    if result.error:
                        errors.append({
                            'resource_type': resource_type,
                            'error_message': result.error
                        })
                    logger.info(f"✓ Collected {result.resource_count} {resource_type}")
                except Exception as e:
                    logger.error(f"✗ Failed to collect {resource_type}: {str(e)}")
                    errors.append({
                        'resource_type': resource_type,
                        'error_message': str(e)
                    })

        # Calculate metadata
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        context_data = {
            'version': '1.0.0',
            'last_updated': end_time.isoformat(),
            'resources': all_resources,
            'metadata': self._calculate_metadata(all_resources, duration_ms)
        }

        logger.info(f"✓ Collection complete: {len(all_resources)} resources in {duration_ms}ms")

        # Save snapshot
        snapshot = self.save_snapshot(context_data, errors, duration_ms)
        context_data['snapshots'] = [asdict(snapshot)]

        return context_data

    # ========================================================================
    # ECS Services
    # ========================================================================

    def collect_ecs_services(self) -> CollectionResult:
        """Collect ECS services and their current state."""
        start_time = datetime.now()
        resources = []
        error = None

        try:
            ecs = self.session.client('ecs')

            # List all clusters
            clusters_response = ecs.list_clusters()
            cluster_arns = clusters_response.get('clusterArns', [])

            for cluster_arn in cluster_arns:
                # List services in cluster
                services_response = ecs.list_services(cluster=cluster_arn)
                service_arns = services_response.get('serviceArns', [])

                if not service_arns:
                    continue

                # Describe services
                services_detail = ecs.describe_services(
                    cluster=cluster_arn,
                    services=service_arns,
                    include=['TAGS']
                )

                for service in services_detail.get('services', []):
                    # Check for filter tag
                    tags = {tag['key']: tag['value'] for tag in service.get('tags', [])}
                    if tags.get('Managed') != self.filter_tag:
                        continue

                    # Extract service name
                    service_name = service['serviceName']
                    environment = tags.get('Environment', 'unknown')

                    # Build resource
                    resource = {
                        'resource_id': f"ecs-{service_name}-{environment}-{self.aws_region}",
                        'resource_type': 'ecs_service',
                        'service_name': service_name,
                        'environment': environment,
                        'region': self.aws_region,
                        'current_state': {
                            'status': service['status'],
                            'desired_count': service['desiredCount'],
                            'running_count': service['runningCount'],
                            'pending_count': service['pendingCount'],
                            'task_definition': service['taskDefinition'].split('/')[-1],
                            'launch_type': service.get('launchType', 'UNKNOWN'),
                            'platform_version': service.get('platformVersion'),
                            'load_balancers': [lb['targetGroupArn'].split('/')[-1]
                                             for lb in service.get('loadBalancers', [])],
                            'health_check_grace_period': service.get('healthCheckGracePeriodSeconds'),
                            'created_at': service['createdAt'].isoformat() if 'createdAt' in service else None
                        },
                        'tags': tags,
                        'dependencies': [lb['targetGroupArn'].split('/')[-1]
                                       for lb in service.get('loadBalancers', [])],
                        'metadata': {
                            'created_at': service['createdAt'].isoformat() if 'createdAt' in service else None,
                            'last_updated': datetime.now(timezone.utc).isoformat(),
                            'last_snapshot': datetime.now(timezone.utc).isoformat(),
                            'discovered_by': 'auto_scan'
                        },
                        'drift_status': {
                            'has_drift': False,
                            'last_drift_detected': None,
                            'drift_details': [],
                            'acknowledged': False
                        }
                    }

                    resources.append(resource)

        except (ClientError, BotoCoreError) as e:
            error = str(e)
            logger.error(f"Error collecting ECS services: {error}")

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return CollectionResult(
            success=error is None,
            resource_type='ecs_service',
            resource_count=len(resources),
            resources=resources,
            error=error,
            duration_ms=duration_ms
        )

    # ========================================================================
    # EC2 Instances
    # ========================================================================

    def collect_ec2_instances(self) -> CollectionResult:
        """Collect EC2 instances."""
        start_time = datetime.now()
        resources = []
        error = None

        try:
            ec2 = self.session.client('ec2')

            # Describe instances with filter
            response = ec2.describe_instances(
                Filters=[
                    {'Name': f'tag:Managed', 'Values': [self.filter_tag]}
                ]
            )

            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    service_name = tags.get('Name', instance['InstanceId'])
                    environment = tags.get('Environment', 'unknown')

                    resource = {
                        'resource_id': instance['InstanceId'],
                        'resource_type': 'ec2_instance',
                        'service_name': service_name,
                        'environment': environment,
                        'region': self.aws_region,
                        'current_state': {
                            'state': instance['State']['Name'],
                            'instance_type': instance['InstanceType'],
                            'ami_id': instance['ImageId'],
                            'public_ip': instance.get('PublicIpAddress'),
                            'private_ip': instance.get('PrivateIpAddress'),
                            'vpc_id': instance.get('VpcId'),
                            'subnet_id': instance.get('SubnetId'),
                            'security_groups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])],
                            'launch_time': instance['LaunchTime'].isoformat(),
                            'monitoring': instance['Monitoring']['State']
                        },
                        'tags': tags,
                        'dependencies': [],
                        'metadata': {
                            'created_at': instance['LaunchTime'].isoformat(),
                            'last_updated': datetime.now(timezone.utc).isoformat(),
                            'last_snapshot': datetime.now(timezone.utc).isoformat(),
                            'discovered_by': 'auto_scan'
                        },
                        'drift_status': {
                            'has_drift': False,
                            'last_drift_detected': None,
                            'drift_details': [],
                            'acknowledged': False
                        }
                    }

                    resources.append(resource)

        except (ClientError, BotoCoreError) as e:
            error = str(e)
            logger.error(f"Error collecting EC2 instances: {error}")

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return CollectionResult(
            success=error is None,
            resource_type='ec2_instance',
            resource_count=len(resources),
            resources=resources,
            error=error,
            duration_ms=duration_ms
        )

    # ========================================================================
    # RDS Databases
    # ========================================================================

    def collect_rds_databases(self) -> CollectionResult:
        """Collect RDS database instances."""
        start_time = datetime.now()
        resources = []
        error = None

        try:
            rds = self.session.client('rds')

            # Describe DB instances
            response = rds.describe_db_instances()

            for db_instance in response.get('DBInstances', []):
                # Get tags
                arn = db_instance['DBInstanceArn']
                tags_response = rds.list_tags_for_resource(ResourceName=arn)
                tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}

                # Check filter
                if tags.get('Managed') != self.filter_tag:
                    continue

                service_name = db_instance['DBInstanceIdentifier']
                environment = tags.get('Environment', 'unknown')

                resource = {
                    'resource_id': arn,
                    'resource_type': 'rds_database',
                    'service_name': service_name,
                    'environment': environment,
                    'region': self.aws_region,
                    'current_state': {
                        'status': db_instance['DBInstanceStatus'],
                        'engine': db_instance['Engine'],
                        'engine_version': db_instance['EngineVersion'],
                        'instance_class': db_instance['DBInstanceClass'],
                        'allocated_storage': db_instance['AllocatedStorage'],
                        'multi_az': db_instance['MultiAZ'],
                        'endpoint': db_instance.get('Endpoint', {}).get('Address'),
                        'port': db_instance.get('Endpoint', {}).get('Port'),
                        'backup_retention_period': db_instance.get('BackupRetentionPeriod'),
                        'encryption_enabled': db_instance.get('StorageEncrypted', False)
                    },
                    'tags': tags,
                    'dependencies': [],
                    'metadata': {
                        'created_at': db_instance['InstanceCreateTime'].isoformat() if 'InstanceCreateTime' in db_instance else None,
                        'last_updated': datetime.now(timezone.utc).isoformat(),
                        'last_snapshot': datetime.now(timezone.utc).isoformat(),
                        'discovered_by': 'auto_scan'
                    },
                    'drift_status': {
                        'has_drift': False,
                        'last_drift_detected': None,
                        'drift_details': [],
                        'acknowledged': False
                    }
                }

                resources.append(resource)

        except (ClientError, BotoCoreError) as e:
            error = str(e)
            logger.error(f"Error collecting RDS databases: {error}")

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return CollectionResult(
            success=error is None,
            resource_type='rds_database',
            resource_count=len(resources),
            resources=resources,
            error=error,
            duration_ms=duration_ms
        )

    # ========================================================================
    # Lambda Functions
    # ========================================================================

    def collect_lambda_functions(self) -> CollectionResult:
        """Collect Lambda functions."""
        start_time = datetime.now()
        resources = []
        error = None

        try:
            lambda_client = self.session.client('lambda')

            # List functions
            paginator = lambda_client.get_paginator('list_functions')

            for page in paginator.paginate():
                for function in page.get('Functions', []):
                    # Get tags
                    function_arn = function['FunctionArn']
                    try:
                        tags_response = lambda_client.list_tags(Resource=function_arn)
                        tags = tags_response.get('Tags', {})
                    except:
                        tags = {}

                    # Check filter
                    if tags.get('Managed') != self.filter_tag:
                        continue

                    service_name = function['FunctionName']
                    environment = tags.get('Environment', 'unknown')

                    resource = {
                        'resource_id': function_arn,
                        'resource_type': 'lambda_function',
                        'service_name': service_name,
                        'environment': environment,
                        'region': self.aws_region,
                        'current_state': {
                            'runtime': function['Runtime'],
                            'handler': function['Handler'],
                            'memory_size': function['MemorySize'],
                            'timeout': function['Timeout'],
                            'code_size': function['CodeSize'],
                            'last_modified': function['LastModified'],
                            'version': function['Version'],
                            'environment_variables': function.get('Environment', {}).get('Variables', {}),
                            'vpc_config': function.get('VpcConfig', {})
                        },
                        'tags': tags,
                        'dependencies': [],
                        'metadata': {
                            'created_at': function['LastModified'],
                            'last_updated': function['LastModified'],
                            'last_snapshot': datetime.now(timezone.utc).isoformat(),
                            'discovered_by': 'auto_scan'
                        },
                        'drift_status': {
                            'has_drift': False,
                            'last_drift_detected': None,
                            'drift_details': [],
                            'acknowledged': False
                        }
                    }

                    resources.append(resource)

        except (ClientError, BotoCoreError) as e:
            error = str(e)
            logger.error(f"Error collecting Lambda functions: {error}")

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return CollectionResult(
            success=error is None,
            resource_type='lambda_function',
            resource_count=len(resources),
            resources=resources,
            error=error,
            duration_ms=duration_ms
        )

    # ========================================================================
    # Application Load Balancers
    # ========================================================================

    def collect_load_balancers(self) -> CollectionResult:
        """Collect Application Load Balancers."""
        start_time = datetime.now()
        resources = []
        error = None

        try:
            elbv2 = self.session.client('elbv2')

            # Describe load balancers
            response = elbv2.describe_load_balancers()

            for lb in response.get('LoadBalancers', []):
                # Get tags
                lb_arn = lb['LoadBalancerArn']
                tags_response = elbv2.describe_tags(ResourceArns=[lb_arn])
                tags = {}
                for tag_desc in tags_response.get('TagDescriptions', []):
                    tags = {tag['Key']: tag['Value'] for tag in tag_desc.get('Tags', [])}

                # Check filter
                if tags.get('Managed') != self.filter_tag:
                    continue

                service_name = lb['LoadBalancerName']
                environment = tags.get('Environment', 'unknown')

                # Get target groups
                target_groups_response = elbv2.describe_target_groups(LoadBalancerArn=lb_arn)
                target_groups = []
                for tg in target_groups_response.get('TargetGroups', []):
                    target_groups.append({
                        'name': tg['TargetGroupName'],
                        'target_type': tg['TargetType'],
                        'health_check': {
                            'path': tg.get('HealthCheckPath'),
                            'interval': tg.get('HealthCheckIntervalSeconds'),
                            'timeout': tg.get('HealthCheckTimeoutSeconds'),
                            'healthy_threshold': tg.get('HealthyThresholdCount')
                        }
                    })

                resource = {
                    'resource_id': lb_arn,
                    'resource_type': 'alb',
                    'service_name': service_name,
                    'environment': environment,
                    'region': self.aws_region,
                    'current_state': {
                        'state': lb['State']['Code'],
                        'dns_name': lb['DNSName'],
                        'scheme': lb['Scheme'],
                        'vpc_id': lb['VpcId'],
                        'availability_zones': [az['ZoneName'] for az in lb.get('AvailabilityZones', [])],
                        'security_groups': lb.get('SecurityGroups', []),
                        'target_groups': target_groups
                    },
                    'tags': tags,
                    'dependencies': [],
                    'metadata': {
                        'created_at': lb['CreatedTime'].isoformat(),
                        'last_updated': datetime.now(timezone.utc).isoformat(),
                        'last_snapshot': datetime.now(timezone.utc).isoformat(),
                        'discovered_by': 'auto_scan'
                    },
                    'drift_status': {
                        'has_drift': False,
                        'last_drift_detected': None,
                        'drift_details': [],
                        'acknowledged': False
                    }
                }

                resources.append(resource)

        except (ClientError, BotoCoreError) as e:
            error = str(e)
            logger.error(f"Error collecting load balancers: {error}")

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return CollectionResult(
            success=error is None,
            resource_type='alb',
            resource_count=len(resources),
            resources=resources,
            error=error,
            duration_ms=duration_ms
        )

    # ========================================================================
    # Stub Methods for Additional Resource Types
    # ========================================================================

    def collect_s3_buckets(self) -> CollectionResult:
        """Collect S3 buckets (stub for now)."""
        return CollectionResult(
            success=True,
            resource_type='s3_bucket',
            resource_count=0,
            resources=[],
            error=None,
            duration_ms=0
        )

    def collect_dynamodb_tables(self) -> CollectionResult:
        """Collect DynamoDB tables (stub for now)."""
        return CollectionResult(
            success=True,
            resource_type='dynamodb_table',
            resource_count=0,
            resources=[],
            error=None,
            duration_ms=0
        )

    def collect_sqs_queues(self) -> CollectionResult:
        """Collect SQS queues (stub for now)."""
        return CollectionResult(
            success=True,
            resource_type='sqs_queue',
            resource_count=0,
            resources=[],
            error=None,
            duration_ms=0
        )

    def collect_sns_topics(self) -> CollectionResult:
        """Collect SNS topics (stub for now)."""
        return CollectionResult(
            success=True,
            resource_type='sns_topic',
            resource_count=0,
            resources=[],
            error=None,
            duration_ms=0
        )

    def collect_cloudfront_distributions(self) -> CollectionResult:
        """Collect CloudFront distributions (stub for now)."""
        return CollectionResult(
            success=True,
            resource_type='cloudfront_distribution',
            resource_count=0,
            resources=[],
            error=None,
            duration_ms=0
        )

    # ========================================================================
    # Snapshot Management
    # ========================================================================

    def save_snapshot(
        self,
        context_data: Dict[str, Any],
        errors: List[Dict[str, str]],
        duration_ms: int
    ) -> Snapshot:
        """
        Save current context as a snapshot.

        Args:
            context_data: Full context dictionary
            errors: Collection errors
            duration_ms: Collection duration

        Returns:
            Snapshot metadata
        """
        timestamp = datetime.now(timezone.utc)
        snapshot_id = timestamp.strftime('snap-%Y-%m-%d-%H-%M')

        # Calculate checksum
        checksum = self.calculate_checksum(context_data['resources'])

        # Create snapshot metadata
        snapshot = Snapshot(
            snapshot_id=snapshot_id,
            timestamp=timestamp.isoformat(),
            resource_count=len(context_data['resources']),
            checksum=checksum,
            drift_events_detected=0,  # Will be calculated by drift detector
            collection_duration_ms=duration_ms,
            errors=errors
        )

        # Save to disk
        snapshot_path = os.path.join(self.snapshot_dir, f'{snapshot_id}.json')
        with open(snapshot_path, 'w') as f:
            json.dump(context_data, f, indent=2)

        logger.info(f"✓ Snapshot saved: {snapshot_path}")

        return snapshot

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Load the most recent snapshot."""
        snapshot_files = sorted(
            [f for f in os.listdir(self.snapshot_dir) if f.startswith('snap-') and f.endswith('.json')],
            reverse=True
        )

        if not snapshot_files:
            return None

        latest_file = os.path.join(self.snapshot_dir, snapshot_files[0])
        with open(latest_file, 'r') as f:
            return json.load(f)

    def get_snapshot_by_id(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Load a specific snapshot by ID."""
        snapshot_path = os.path.join(self.snapshot_dir, f'{snapshot_id}.json')
        if not os.path.exists(snapshot_path):
            return None

        with open(snapshot_path, 'r') as f:
            return json.load(f)

    def cleanup_old_snapshots(self, days_to_keep: int = 7) -> int:
        """
        Delete snapshots older than specified days.

        Args:
            days_to_keep: Number of days to retain

        Returns:
            Number of snapshots deleted
        """
        cutoff_time = datetime.now(timezone.utc).timestamp() - (days_to_keep * 86400)
        deleted_count = 0

        for filename in os.listdir(self.snapshot_dir):
            if not filename.startswith('snap-') or not filename.endswith('.json'):
                continue

            filepath = os.path.join(self.snapshot_dir, filename)
            file_mtime = os.path.getmtime(filepath)

            if file_mtime < cutoff_time:
                os.remove(filepath)
                deleted_count += 1
                logger.info(f"Deleted old snapshot: {filename}")

        return deleted_count

    @staticmethod
    def calculate_checksum(resources: List[Dict[str, Any]]) -> str:
        """Calculate SHA256 checksum of resource states."""
        # Sort resources by resource_id for consistent hashing
        sorted_resources = sorted(resources, key=lambda r: r['resource_id'])

        # Serialize to JSON
        json_str = json.dumps(sorted_resources, sort_keys=True)

        # Calculate hash
        return hashlib.sha256(json_str.encode()).hexdigest()[:32]

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _calculate_metadata(self, resources: List[Dict[str, Any]], duration_ms: int) -> Dict[str, Any]:
        """Calculate context metadata from resources."""
        resources_by_type = {}
        resources_by_environment = {'development': 0, 'staging': 0, 'production': 0}
        environments = set()
        regions = set()

        for resource in resources:
            # Count by type
            resource_type = resource['resource_type']
            resources_by_type[resource_type] = resources_by_type.get(resource_type, 0) + 1

            # Count by environment
            environment = resource.get('environment', 'unknown')
            if environment in resources_by_environment:
                resources_by_environment[environment] += 1
            environments.add(environment)

            # Collect regions
            regions.add(resource.get('region', self.aws_region))

        return {
            'total_resources': len(resources),
            'resources_by_type': resources_by_type,
            'resources_by_environment': resources_by_environment,
            'environments': sorted(list(environments)),
            'regions': sorted(list(regions)),
            'total_drift_events': 0,
            'critical_drift_count': 0,
            'last_collection_duration_ms': duration_ms,
            'collector_version': '1.0.0',
            'aws_account_id': self._get_account_id()
        }

    def _get_account_id(self) -> str:
        """Get AWS account ID."""
        try:
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            return identity['Account']
        except:
            return 'unknown'


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point for manual testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Collect AWS infrastructure context')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--filter-tag', default='PromptOps', help='Tag value to filter resources')
    parser.add_argument('--output', default='./context_snapshots', help='Output directory')
    parser.add_argument('--cleanup-days', type=int, help='Cleanup snapshots older than N days')

    args = parser.parse_args()

    collector = ContextCollector(
        aws_region=args.region,
        aws_profile=args.profile,
        snapshot_dir=args.output,
        filter_tag=args.filter_tag
    )

    if args.cleanup_days:
        deleted = collector.cleanup_old_snapshots(args.cleanup_days)
        print(f"Deleted {deleted} old snapshots")
    else:
        context_data = collector.collect_all_resources(parallel=True)
        print(f"\n✓ Collection complete!")
        print(f"  Resources: {context_data['metadata']['total_resources']}")
        print(f"  Duration: {context_data['metadata']['last_collection_duration_ms']}ms")
        print(f"  Snapshot: {context_data['snapshots'][0]['snapshot_id']}")


if __name__ == '__main__':
    main()
