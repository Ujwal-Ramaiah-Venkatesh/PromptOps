"""
AWS Resource Scanner
====================

Read-only scanner that discovers AWS resources across multiple regions.

Week 16-18: ENHANCEMENT-003
Author: PromptOps Team
Date: 2026-04-30
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


@dataclass
class Resource:
    """Discovered AWS resource."""
    resource_id: str
    resource_type: str
    region: str
    name: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    aws_state: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.utcnow)

    # Will be populated by context inference
    inferred_environment: Optional[str] = None
    inferred_project: Optional[str] = None
    inferred_owner: Optional[str] = None
    confidence_score: float = 0.0


@dataclass
class ScanProgress:
    """Track scan progress."""
    total_resources: int = 0
    scanned_resources: int = 0
    current_region: str = ""
    current_resource_type: str = ""
    errors: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)

    def progress_percentage(self) -> float:
        if self.total_resources == 0:
            return 0.0
        return (self.scanned_resources / self.total_resources) * 100


@dataclass
class ResourceInventory:
    """Complete inventory of discovered resources."""
    scan_id: str
    resources: List[Resource]
    total_count: int
    by_type: Dict[str, int]
    by_region: Dict[str, int]
    scan_duration_seconds: float
    regions_scanned: List[str]
    errors: List[str]

    def filter_by_type(self, resource_type: str) -> List[Resource]:
        """Filter resources by type."""
        return [r for r in self.resources if r.resource_type == resource_type]

    def filter_by_region(self, region: str) -> List[Resource]:
        """Filter resources by region."""
        return [r for r in self.resources if r.region == region]

    def filter_by_tag(self, tag_key: str, tag_value: str) -> List[Resource]:
        """Filter resources by tag."""
        return [r for r in self.resources if r.tags.get(tag_key) == tag_value]


class AWSScanner:
    """
    Scan AWS account for all resources (read-only).

    Supports:
    - EC2 instances
    - RDS databases
    - S3 buckets
    - VPCs, subnets, security groups
    - ECS services
    - Lambda functions
    - Load balancers
    - IAM roles
    """

    DEFAULT_REGIONS = [
        'us-east-1', 'us-west-2', 'eu-west-1'
    ]

    def __init__(self, aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 aws_session_token: Optional[str] = None,
                 regions: Optional[List[str]] = None):
        """
        Initialize AWS scanner.

        Args:
            aws_access_key_id: AWS access key (or use default credentials)
            aws_secret_access_key: AWS secret key
            aws_session_token: AWS session token (for temporary credentials)
            regions: List of regions to scan (default: common regions)
        """
        self.session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )

        self.regions = regions or self.DEFAULT_REGIONS
        self.progress = ScanProgress()
        self.progress_callback: Optional[Callable[[ScanProgress], None]] = None

    def scan_all_resources(self, resource_types: Optional[List[str]] = None) -> ResourceInventory:
        """
        Scan all resources across all regions.

        Args:
            resource_types: List of resource types to scan (default: all)

        Returns:
            ResourceInventory with all discovered resources
        """
        scan_id = f"scan-{int(datetime.utcnow().timestamp())}"
        start_time = time.time()

        all_resources = []
        all_errors = []

        # Default to all supported resource types
        if not resource_types:
            resource_types = [
                'ec2', 'rds', 's3', 'vpc', 'subnet', 'security_group',
                'ecs_service', 'lambda', 'load_balancer', 'iam_role'
            ]

        logger.info(f"Starting scan {scan_id} across {len(self.regions)} regions")

        # Scan each resource type in each region
        for resource_type in resource_types:
            logger.info(f"Scanning {resource_type} resources")
            self.progress.current_resource_type = resource_type

            try:
                resources = self._scan_resource_type(resource_type)
                all_resources.extend(resources)
                logger.info(f"Found {len(resources)} {resource_type} resources")
            except Exception as e:
                error_msg = f"Error scanning {resource_type}: {str(e)}"
                logger.error(error_msg)
                all_errors.append(error_msg)
                self.progress.errors.append(error_msg)

        # Calculate summary
        by_type = {}
        by_region = {}

        for resource in all_resources:
            by_type[resource.resource_type] = by_type.get(resource.resource_type, 0) + 1
            by_region[resource.region] = by_region.get(resource.region, 0) + 1

        scan_duration = time.time() - start_time

        inventory = ResourceInventory(
            scan_id=scan_id,
            resources=all_resources,
            total_count=len(all_resources),
            by_type=by_type,
            by_region=by_region,
            scan_duration_seconds=scan_duration,
            regions_scanned=self.regions,
            errors=all_errors
        )

        logger.info(f"Scan complete: {len(all_resources)} resources in {scan_duration:.1f}s")

        return inventory

    def _scan_resource_type(self, resource_type: str) -> List[Resource]:
        """Scan specific resource type across all regions."""
        scanners = {
            'ec2': self.scan_ec2_instances,
            'rds': self.scan_rds_instances,
            's3': self.scan_s3_buckets,
            'vpc': self.scan_vpcs,
            'subnet': self.scan_subnets,
            'security_group': self.scan_security_groups,
            'ecs_service': self.scan_ecs_services,
            'lambda': self.scan_lambda_functions,
            'load_balancer': self.scan_load_balancers,
            'iam_role': self.scan_iam_roles,
        }

        scanner_func = scanners.get(resource_type)
        if not scanner_func:
            raise ValueError(f"Unsupported resource type: {resource_type}")

        # S3 and IAM are global, only scan once
        if resource_type in ['s3', 'iam_role']:
            return scanner_func(self.regions[0])

        # Scan in parallel across regions
        all_resources = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(scanner_func, region): region
                for region in self.regions
            }

            for future in as_completed(futures):
                region = futures[future]
                try:
                    resources = future.result()
                    all_resources.extend(resources)
                except Exception as e:
                    logger.error(f"Error scanning {resource_type} in {region}: {e}")

        return all_resources

    def scan_ec2_instances(self, region: str) -> List[Resource]:
        """Scan EC2 instances in region."""
        self.progress.current_region = region

        try:
            ec2 = self.session.client('ec2', region_name=region)
            response = ec2.describe_instances()

            resources = []
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    # Extract tags
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    name = tags.get('Name', instance['InstanceId'])

                    resource = Resource(
                        resource_id=instance['InstanceId'],
                        resource_type='ec2',
                        region=region,
                        name=name,
                        tags=tags,
                        aws_state={
                            'instance_type': instance.get('InstanceType'),
                            'state': instance.get('State', {}).get('Name'),
                            'ami': instance.get('ImageId'),
                            'vpc_id': instance.get('VpcId'),
                            'subnet_id': instance.get('SubnetId'),
                            'private_ip': instance.get('PrivateIpAddress'),
                            'public_ip': instance.get('PublicIpAddress'),
                            'security_groups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])],
                            'iam_instance_profile': instance.get('IamInstanceProfile', {}).get('Arn'),
                            'launch_time': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None,
                        }
                    )
                    resources.append(resource)
                    self.progress.scanned_resources += 1

            return resources

        except ClientError as e:
            logger.error(f"Error scanning EC2 in {region}: {e}")
            return []

    def scan_rds_instances(self, region: str) -> List[Resource]:
        """Scan RDS databases in region."""
        self.progress.current_region = region

        try:
            rds = self.session.client('rds', region_name=region)
            response = rds.describe_db_instances()

            resources = []
            for db in response.get('DBInstances', []):
                # Extract tags
                tags_response = rds.list_tags_for_resource(
                    ResourceName=db['DBInstanceArn']
                )
                tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}

                resource = Resource(
                    resource_id=db['DBInstanceIdentifier'],
                    resource_type='rds',
                    region=region,
                    name=db['DBInstanceIdentifier'],
                    tags=tags,
                    aws_state={
                        'engine': db.get('Engine'),
                        'engine_version': db.get('EngineVersion'),
                        'instance_class': db.get('DBInstanceClass'),
                        'allocated_storage': db.get('AllocatedStorage'),
                        'storage_type': db.get('StorageType'),
                        'multi_az': db.get('MultiAZ'),
                        'publicly_accessible': db.get('PubliclyAccessible'),
                        'vpc_id': db.get('DBSubnetGroup', {}).get('VpcId'),
                        'status': db.get('DBInstanceStatus'),
                        'backup_retention_period': db.get('BackupRetentionPeriod'),
                        'security_groups': [sg['VpcSecurityGroupId'] for sg in db.get('VpcSecurityGroups', [])],
                    }
                )
                resources.append(resource)
                self.progress.scanned_resources += 1

            return resources

        except ClientError as e:
            logger.error(f"Error scanning RDS in {region}: {e}")
            return []

    def scan_s3_buckets(self, region: str) -> List[Resource]:
        """Scan S3 buckets (global)."""
        try:
            s3 = self.session.client('s3')
            response = s3.list_buckets()

            resources = []
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']

                # Get bucket region
                try:
                    location_response = s3.get_bucket_location(Bucket=bucket_name)
                    bucket_region = location_response.get('LocationConstraint') or 'us-east-1'
                except ClientError:
                    bucket_region = 'unknown'

                # Get bucket tags
                try:
                    tags_response = s3.get_bucket_tagging(Bucket=bucket_name)
                    tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagSet', [])}
                except ClientError:
                    tags = {}

                # Get versioning status
                try:
                    versioning_response = s3.get_bucket_versioning(Bucket=bucket_name)
                    versioning_enabled = versioning_response.get('Status') == 'Enabled'
                except ClientError:
                    versioning_enabled = False

                resource = Resource(
                    resource_id=bucket_name,
                    resource_type='s3',
                    region=bucket_region,
                    name=bucket_name,
                    tags=tags,
                    aws_state={
                        'creation_date': bucket['CreationDate'].isoformat(),
                        'versioning_enabled': versioning_enabled,
                    }
                )
                resources.append(resource)
                self.progress.scanned_resources += 1

            return resources

        except ClientError as e:
            logger.error(f"Error scanning S3: {e}")
            return []

    def scan_vpcs(self, region: str) -> List[Resource]:
        """Scan VPCs in region."""
        self.progress.current_region = region

        try:
            ec2 = self.session.client('ec2', region_name=region)
            response = ec2.describe_vpcs()

            resources = []
            for vpc in response.get('Vpcs', []):
                tags = {tag['Key']: tag['Value'] for tag in vpc.get('Tags', [])}
                name = tags.get('Name', vpc['VpcId'])

                resource = Resource(
                    resource_id=vpc['VpcId'],
                    resource_type='vpc',
                    region=region,
                    name=name,
                    tags=tags,
                    aws_state={
                        'cidr_block': vpc.get('CidrBlock'),
                        'is_default': vpc.get('IsDefault'),
                        'state': vpc.get('State'),
                    }
                )
                resources.append(resource)
                self.progress.scanned_resources += 1

            return resources

        except ClientError as e:
            logger.error(f"Error scanning VPCs in {region}: {e}")
            return []

    def scan_subnets(self, region: str) -> List[Resource]:
        """Scan subnets in region."""
        self.progress.current_region = region

        try:
            ec2 = self.session.client('ec2', region_name=region)
            response = ec2.describe_subnets()

            resources = []
            for subnet in response.get('Subnets', []):
                tags = {tag['Key']: tag['Value'] for tag in subnet.get('Tags', [])}
                name = tags.get('Name', subnet['SubnetId'])

                resource = Resource(
                    resource_id=subnet['SubnetId'],
                    resource_type='subnet',
                    region=region,
                    name=name,
                    tags=tags,
                    aws_state={
                        'cidr_block': subnet.get('CidrBlock'),
                        'vpc_id': subnet.get('VpcId'),
                        'availability_zone': subnet.get('AvailabilityZone'),
                        'available_ip_address_count': subnet.get('AvailableIpAddressCount'),
                    }
                )
                resources.append(resource)
                self.progress.scanned_resources += 1

            return resources

        except ClientError as e:
            logger.error(f"Error scanning subnets in {region}: {e}")
            return []

    def scan_security_groups(self, region: str) -> List[Resource]:
        """Scan security groups in region."""
        self.progress.current_region = region

        try:
            ec2 = self.session.client('ec2', region_name=region)
            response = ec2.describe_security_groups()

            resources = []
            for sg in response.get('SecurityGroups', []):
                tags = {tag['Key']: tag['Value'] for tag in sg.get('Tags', [])}

                resource = Resource(
                    resource_id=sg['GroupId'],
                    resource_type='security_group',
                    region=region,
                    name=sg.get('GroupName'),
                    tags=tags,
                    aws_state={
                        'group_name': sg.get('GroupName'),
                        'description': sg.get('Description'),
                        'vpc_id': sg.get('VpcId'),
                        'ingress_rules': sg.get('IpPermissions', []),
                        'egress_rules': sg.get('IpPermissionsEgress', []),
                    }
                )
                resources.append(resource)
                self.progress.scanned_resources += 1

            return resources

        except ClientError as e:
            logger.error(f"Error scanning security groups in {region}: {e}")
            return []

    def scan_ecs_services(self, region: str) -> List[Resource]:
        """Scan ECS services in region."""
        # Placeholder - would need to list clusters first, then services
        return []

    def scan_lambda_functions(self, region: str) -> List[Resource]:
        """Scan Lambda functions in region."""
        # Placeholder
        return []

    def scan_load_balancers(self, region: str) -> List[Resource]:
        """Scan load balancers in region."""
        # Placeholder
        return []

    def scan_iam_roles(self, region: str) -> List[Resource]:
        """Scan IAM roles (global)."""
        # Placeholder
        return []
