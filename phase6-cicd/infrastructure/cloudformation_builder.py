"""
CloudFormation Builder for PromptOps
=====================================

Generates AWS CloudFormation templates.
Supports JSON and YAML formats.

Author: DevOps Engineer - Phase 6 Week 60-61
Date: 2026-05-10
"""

import json
import yaml
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CloudFormation Builder
# ============================================================================

class CloudFormationBuilder:
    """
    CloudFormation template builder.

    Features:
    - Template generation (JSON, YAML)
    - Resource definitions
    - Parameter management
    - Output definitions
    - Nested stacks
    - Change sets
    """

    def __init__(self):
        """Initialize CloudFormation Builder."""
        self.template_version = "2010-09-09"

    def create_template(
        self,
        description: str,
        resources: List[Dict[str, Any]],
        parameters: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        mappings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create CloudFormation template.

        Args:
            description: Template description
            resources: List of resources
            parameters: Template parameters
            outputs: Template outputs
            mappings: Template mappings

        Returns:
            CloudFormation template
        """
        logger.info("Creating CloudFormation template")

        template = {
            "AWSTemplateFormatVersion": self.template_version,
            "Description": description,
            "Resources": {}
        }

        if parameters:
            template["Parameters"] = parameters

        if mappings:
            template["Mappings"] = mappings

        if outputs:
            template["Outputs"] = outputs

        # Add resources
        for resource in resources:
            resource_name = resource.get("name")
            resource_type = resource.get("type")
            properties = resource.get("properties", {})

            template["Resources"][resource_name] = {
                "Type": self._get_resource_type(resource_type),
                "Properties": properties
            }

            # Add dependencies if specified
            if "depends_on" in resource:
                template["Resources"][resource_name]["DependsOn"] = resource["depends_on"]

        return template

    def _get_resource_type(self, resource_type: str) -> str:
        """Map resource type to CloudFormation type."""
        type_mapping = {
            "ec2": "AWS::EC2::Instance",
            "s3": "AWS::S3::Bucket",
            "rds": "AWS::RDS::DBInstance",
            "vpc": "AWS::EC2::VPC",
            "subnet": "AWS::EC2::Subnet",
            "sg": "AWS::EC2::SecurityGroup",
            "elb": "AWS::ElasticLoadBalancingV2::LoadBalancer",
            "lambda": "AWS::Lambda::Function",
            "dynamodb": "AWS::DynamoDB::Table",
            "eks": "AWS::EKS::Cluster",
            "iam_role": "AWS::IAM::Role",
            "iam_policy": "AWS::IAM::Policy"
        }

        return type_mapping.get(resource_type, resource_type)

    def generate_ec2_stack(
        self,
        stack_name: str,
        instance_type: str = "t3.micro",
        key_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate EC2 instance stack.

        Args:
            stack_name: Stack name
            instance_type: EC2 instance type
            key_name: SSH key pair name

        Returns:
            CloudFormation template
        """
        logger.info(f"Generating EC2 stack: {stack_name}")

        parameters = {
            "InstanceType": {
                "Type": "String",
                "Default": instance_type,
                "Description": "EC2 instance type",
                "AllowedValues": ["t3.micro", "t3.small", "t3.medium", "t3.large"]
            },
            "KeyName": {
                "Type": "AWS::EC2::KeyPair::KeyName",
                "Description": "Name of an existing EC2 KeyPair"
            },
            "LatestAmiId": {
                "Type": "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>",
                "Default": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
            }
        }

        resources = [
            {
                "name": "EC2Instance",
                "type": "ec2",
                "properties": {
                    "InstanceType": {"Ref": "InstanceType"},
                    "ImageId": {"Ref": "LatestAmiId"},
                    "KeyName": {"Ref": "KeyName"},
                    "Tags": [
                        {"Key": "Name", "Value": stack_name}
                    ]
                }
            }
        ]

        outputs = {
            "InstanceId": {
                "Description": "Instance ID",
                "Value": {"Ref": "EC2Instance"}
            },
            "PublicIP": {
                "Description": "Public IP address",
                "Value": {"Fn::GetAtt": ["EC2Instance", "PublicIp"]}
            }
        }

        return self.create_template(
            description=f"EC2 instance stack: {stack_name}",
            resources=resources,
            parameters=parameters,
            outputs=outputs
        )

    def generate_vpc_stack(
        self,
        stack_name: str,
        cidr_block: str = "10.0.0.0/16"
    ) -> Dict[str, Any]:
        """
        Generate VPC stack with subnets.

        Args:
            stack_name: Stack name
            cidr_block: VPC CIDR block

        Returns:
            CloudFormation template
        """
        logger.info(f"Generating VPC stack: {stack_name}")

        parameters = {
            "VpcCIDR": {
                "Type": "String",
                "Default": cidr_block,
                "Description": "VPC CIDR block"
            }
        }

        resources = [
            {
                "name": "VPC",
                "type": "vpc",
                "properties": {
                    "CidrBlock": {"Ref": "VpcCIDR"},
                    "EnableDnsHostnames": True,
                    "EnableDnsSupport": True,
                    "Tags": [
                        {"Key": "Name", "Value": f"{stack_name}-vpc"}
                    ]
                }
            },
            {
                "name": "InternetGateway",
                "type": "AWS::EC2::InternetGateway",
                "properties": {
                    "Tags": [
                        {"Key": "Name", "Value": f"{stack_name}-igw"}
                    ]
                }
            },
            {
                "name": "AttachGateway",
                "type": "AWS::EC2::VPCGatewayAttachment",
                "properties": {
                    "VpcId": {"Ref": "VPC"},
                    "InternetGatewayId": {"Ref": "InternetGateway"}
                }
            },
            {
                "name": "PublicSubnet",
                "type": "subnet",
                "properties": {
                    "VpcId": {"Ref": "VPC"},
                    "CidrBlock": "10.0.1.0/24",
                    "AvailabilityZone": {"Fn::Select": [0, {"Fn::GetAZs": ""}]},
                    "MapPublicIpOnLaunch": True,
                    "Tags": [
                        {"Key": "Name", "Value": f"{stack_name}-public-subnet"}
                    ]
                }
            }
        ]

        outputs = {
            "VpcId": {
                "Description": "VPC ID",
                "Value": {"Ref": "VPC"},
                "Export": {"Name": {"Fn::Sub": "${AWS::StackName}-VpcId"}}
            },
            "PublicSubnetId": {
                "Description": "Public Subnet ID",
                "Value": {"Ref": "PublicSubnet"},
                "Export": {"Name": {"Fn::Sub": "${AWS::StackName}-PublicSubnetId"}}
            }
        }

        return self.create_template(
            description=f"VPC stack: {stack_name}",
            resources=resources,
            parameters=parameters,
            outputs=outputs
        )

    def generate_rds_stack(
        self,
        stack_name: str,
        db_name: str,
        engine: str = "postgres"
    ) -> Dict[str, Any]:
        """
        Generate RDS database stack.

        Args:
            stack_name: Stack name
            db_name: Database name
            engine: Database engine

        Returns:
            CloudFormation template
        """
        logger.info(f"Generating RDS stack: {stack_name}")

        parameters = {
            "DBName": {
                "Type": "String",
                "Default": db_name,
                "Description": "Database name"
            },
            "DBUsername": {
                "Type": "String",
                "Default": "admin",
                "Description": "Database admin username"
            },
            "DBPassword": {
                "Type": "String",
                "NoEcho": True,
                "Description": "Database admin password"
            },
            "DBInstanceClass": {
                "Type": "String",
                "Default": "db.t3.micro",
                "Description": "Database instance class"
            }
        }

        resources = [
            {
                "name": "DBInstance",
                "type": "rds",
                "properties": {
                    "DBName": {"Ref": "DBName"},
                    "Engine": engine,
                    "MasterUsername": {"Ref": "DBUsername"},
                    "MasterUserPassword": {"Ref": "DBPassword"},
                    "DBInstanceClass": {"Ref": "DBInstanceClass"},
                    "AllocatedStorage": "20",
                    "StorageType": "gp3",
                    "PubliclyAccessible": False,
                    "Tags": [
                        {"Key": "Name", "Value": stack_name}
                    ]
                }
            }
        ]

        outputs = {
            "DBEndpoint": {
                "Description": "Database endpoint",
                "Value": {"Fn::GetAtt": ["DBInstance", "Endpoint.Address"]}
            },
            "DBPort": {
                "Description": "Database port",
                "Value": {"Fn::GetAtt": ["DBInstance", "Endpoint.Port"]}
            }
        }

        return self.create_template(
            description=f"RDS database stack: {stack_name}",
            resources=resources,
            parameters=parameters,
            outputs=outputs
        )

    def generate_s3_stack(
        self,
        stack_name: str,
        bucket_name: str,
        versioning: bool = True
    ) -> Dict[str, Any]:
        """
        Generate S3 bucket stack.

        Args:
            stack_name: Stack name
            bucket_name: S3 bucket name
            versioning: Enable versioning

        Returns:
            CloudFormation template
        """
        logger.info(f"Generating S3 stack: {stack_name}")

        resources = [
            {
                "name": "S3Bucket",
                "type": "s3",
                "properties": {
                    "BucketName": bucket_name,
                    "VersioningConfiguration": {
                        "Status": "Enabled" if versioning else "Suspended"
                    },
                    "PublicAccessBlockConfiguration": {
                        "BlockPublicAcls": True,
                        "BlockPublicPolicy": True,
                        "IgnorePublicAcls": True,
                        "RestrictPublicBuckets": True
                    },
                    "Tags": [
                        {"Key": "Name", "Value": stack_name}
                    ]
                }
            }
        ]

        outputs = {
            "BucketName": {
                "Description": "S3 bucket name",
                "Value": {"Ref": "S3Bucket"}
            },
            "BucketArn": {
                "Description": "S3 bucket ARN",
                "Value": {"Fn::GetAtt": ["S3Bucket", "Arn"]}
            }
        }

        return self.create_template(
            description=f"S3 bucket stack: {stack_name}",
            resources=resources,
            outputs=outputs
        )

    def export_template(
        self,
        template: Dict[str, Any],
        format: str = "yaml"
    ) -> str:
        """
        Export template to JSON or YAML.

        Args:
            template: CloudFormation template
            format: Output format (json, yaml)

        Returns:
            Serialized template
        """
        if format == "json":
            return json.dumps(template, indent=2)
        else:
            return yaml.dump(template, default_flow_style=False, sort_keys=False)


# ============================================================================
# Testing
# ============================================================================

def test_cloudformation_builder():
    """Test CloudFormation Builder."""
    logger.info("Testing CloudFormation Builder...")

    builder = CloudFormationBuilder()

    # Test 1: Generate EC2 stack
    print("\n=== Test 1: EC2 Stack ===")
    ec2_stack = builder.generate_ec2_stack(
        stack_name="web-server",
        instance_type="t3.micro"
    )
    print(f"Description: {ec2_stack['Description']}")
    print(f"Resources: {list(ec2_stack['Resources'].keys())}")
    print(f"Parameters: {list(ec2_stack['Parameters'].keys())}")
    print(f"Outputs: {list(ec2_stack['Outputs'].keys())}")

    # Test 2: Generate VPC stack
    print("\n=== Test 2: VPC Stack ===")
    vpc_stack = builder.generate_vpc_stack(
        stack_name="main-vpc",
        cidr_block="10.0.0.0/16"
    )
    print(f"Resources: {list(vpc_stack['Resources'].keys())}")
    print(f"Outputs: {list(vpc_stack['Outputs'].keys())}")

    # Test 3: Generate RDS stack
    print("\n=== Test 3: RDS Stack ===")
    rds_stack = builder.generate_rds_stack(
        stack_name="app-db",
        db_name="appdb",
        engine="postgres"
    )
    print(f"Resources: {list(rds_stack['Resources'].keys())}")

    # Test 4: Export to YAML
    print("\n=== Test 4: Export to YAML (first 500 chars) ===")
    yaml_output = builder.export_template(ec2_stack, format="yaml")
    print(yaml_output[:500])


if __name__ == "__main__":
    test_cloudformation_builder()
