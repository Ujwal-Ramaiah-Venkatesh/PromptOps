"""
Terraform Code Generator
========================

Converts AWS actual state into Terraform HCL code.

Week 13-15: ENHANCEMENT-002
Author: PromptOps Team
Date: 2026-04-30
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import re


@dataclass
class TerraformResource:
    """Generated Terraform resource."""
    resource_type: str  # e.g., "aws_instance"
    resource_name: str  # e.g., "web_server_1"
    attributes: Dict[str, Any]
    dependencies: List[str]  # Other resources this depends on


@dataclass
class GenerationResult:
    """Result of Terraform code generation."""
    terraform_code: str
    resource_count: int
    warnings: List[str]
    dependencies: List[str]


class TerraformGenerator:
    """
    Generates Terraform HCL code from AWS actual state.

    Supports:
    - EC2 instances
    - RDS databases
    - S3 buckets
    - Security groups
    - IAM roles/policies
    - ECS services
    - Load balancers
    """

    # Mapping from internal resource types to Terraform types
    RESOURCE_TYPE_MAP = {
        "ec2_instance": "aws_instance",
        "rds_instance": "aws_db_instance",
        "s3_bucket": "aws_s3_bucket",
        "security_group": "aws_security_group",
        "iam_role": "aws_iam_role",
        "iam_policy": "aws_iam_policy",
        "ecs_service": "aws_ecs_service",
        "ecs_task_definition": "aws_ecs_task_definition",
        "load_balancer": "aws_lb",
        "target_group": "aws_lb_target_group",
        "lambda_function": "aws_lambda_function",
        "dynamodb_table": "aws_dynamodb_table",
    }

    # Attributes that should be excluded from generated code
    EXCLUDED_ATTRIBUTES = {
        "common": [
            "arn", "id", "created_time", "modified_time", "last_updated",
            "owner_id", "state_transition_reason", "launch_time",
        ],
        "aws_instance": [
            "private_ip", "public_ip", "private_dns", "public_dns",
            "instance_state", "state_reason",
        ],
        "aws_db_instance": [
            "endpoint", "address", "status", "resource_id",
        ],
        "aws_s3_bucket": [
            "bucket_domain_name", "bucket_regional_domain_name",
        ],
    }

    def __init__(self):
        self.warnings: List[str] = []

    def generate(self, resource_id: str, resource_type: str,
                 aws_state: Dict[str, Any]) -> GenerationResult:
        """
        Generate Terraform code from AWS actual state.

        Args:
            resource_id: AWS resource identifier (e.g., "i-1234567890abcdef0")
            resource_type: Internal resource type (e.g., "ec2_instance")
            aws_state: Current AWS state as dictionary

        Returns:
            GenerationResult with Terraform code and metadata
        """
        self.warnings = []

        # Map to Terraform resource type
        tf_type = self.RESOURCE_TYPE_MAP.get(resource_type, f"aws_{resource_type}")

        # Generate resource name from ID or tags
        resource_name = self._generate_resource_name(resource_id, aws_state)

        # Filter and format attributes
        filtered_state = self._filter_attributes(tf_type, aws_state)

        # Detect dependencies
        dependencies = self._detect_dependencies(filtered_state)

        # Generate HCL code
        terraform_code = self._generate_hcl(tf_type, resource_name, filtered_state)

        return GenerationResult(
            terraform_code=terraform_code,
            resource_count=1,
            warnings=self.warnings,
            dependencies=dependencies
        )

    def generate_multiple(self, resources: List[Dict]) -> GenerationResult:
        """
        Generate Terraform code for multiple related resources.

        Args:
            resources: List of resource dictionaries with keys:
                - resource_id
                - resource_type
                - aws_state

        Returns:
            GenerationResult with combined Terraform code
        """
        self.warnings = []
        all_code = []
        all_dependencies = []

        for resource in resources:
            result = self.generate(
                resource["resource_id"],
                resource["resource_type"],
                resource["aws_state"]
            )
            all_code.append(result.terraform_code)
            all_dependencies.extend(result.dependencies)

        combined_code = "\n\n".join(all_code)

        return GenerationResult(
            terraform_code=combined_code,
            resource_count=len(resources),
            warnings=self.warnings,
            dependencies=list(set(all_dependencies))  # Dedupe
        )

    def _generate_resource_name(self, resource_id: str, aws_state: Dict) -> str:
        """
        Generate Terraform resource name from AWS resource.

        Prefers Name tag, falls back to sanitized resource ID.
        """
        # Try to get Name from tags
        tags = aws_state.get("tags", {})
        if isinstance(tags, dict) and "Name" in tags:
            name = tags["Name"]
        elif isinstance(tags, list):
            # Tags might be list of {Key, Value} dicts
            name_tag = next((t["Value"] for t in tags if t.get("Key") == "Name"), None)
            name = name_tag if name_tag else resource_id
        else:
            name = resource_id

        # Sanitize for Terraform (alphanumeric and underscore only)
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        sanitized = re.sub(r'^[0-9]', '_', sanitized)  # Can't start with number
        sanitized = sanitized.lower()

        return sanitized

    def _filter_attributes(self, tf_type: str, aws_state: Dict) -> Dict:
        """
        Filter out read-only and excluded attributes.
        """
        filtered = {}
        excluded = set(self.EXCLUDED_ATTRIBUTES["common"])
        excluded.update(self.EXCLUDED_ATTRIBUTES.get(tf_type, []))

        for key, value in aws_state.items():
            if key in excluded:
                continue

            # Skip None values
            if value is None:
                continue

            # Skip empty lists/dicts
            if isinstance(value, (list, dict)) and not value:
                continue

            filtered[key] = value

        return filtered

    def _detect_dependencies(self, aws_state: Dict) -> List[str]:
        """
        Detect resource dependencies from state.

        Examples:
        - subnet_id -> aws_subnet
        - security_groups -> aws_security_group
        - vpc_id -> aws_vpc
        """
        dependencies = []

        # Common dependency patterns
        dependency_map = {
            "subnet_id": "aws_subnet",
            "vpc_id": "aws_vpc",
            "security_groups": "aws_security_group",
            "security_group_ids": "aws_security_group",
            "iam_instance_profile": "aws_iam_instance_profile",
            "kms_key_id": "aws_kms_key",
            "db_subnet_group_name": "aws_db_subnet_group",
            "target_group_arn": "aws_lb_target_group",
        }

        for key, value in aws_state.items():
            if key in dependency_map:
                dependencies.append(dependency_map[key])

        return list(set(dependencies))  # Dedupe

    def _generate_hcl(self, resource_type: str, resource_name: str,
                     attributes: Dict) -> str:
        """
        Generate HCL code from resource attributes.
        """
        lines = [f'resource "{resource_type}" "{resource_name}" {{']

        # Sort attributes for consistent output
        for key in sorted(attributes.keys()):
            value = attributes[key]
            hcl_line = self._format_attribute(key, value, indent=2)
            lines.append(hcl_line)

        lines.append("}")

        return "\n".join(lines)

    def _format_attribute(self, key: str, value: Any, indent: int = 2) -> str:
        """
        Format a single attribute as HCL.
        """
        indent_str = " " * indent

        # String values
        if isinstance(value, str):
            # Escape quotes in string
            escaped = value.replace('"', '\\"')
            return f'{indent_str}{key} = "{escaped}"'

        # Boolean values
        elif isinstance(value, bool):
            return f'{indent_str}{key} = {str(value).lower()}'

        # Numeric values
        elif isinstance(value, (int, float)):
            return f'{indent_str}{key} = {value}'

        # List values
        elif isinstance(value, list):
            if not value:
                return f'{indent_str}{key} = []'

            # Simple list of primitives
            if all(isinstance(v, (str, int, float, bool)) for v in value):
                items = ", ".join(self._format_value(v) for v in value)
                return f'{indent_str}{key} = [{items}]'

            # List of objects - format as blocks
            else:
                lines = [f'{indent_str}{key} = [']
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f'{indent_str}  {{')
                        for k, v in item.items():
                            lines.append(self._format_attribute(k, v, indent + 4))
                        lines.append(f'{indent_str}  }},')
                lines.append(f'{indent_str}]')
                return "\n".join(lines)

        # Dictionary values - nested blocks
        elif isinstance(value, dict):
            if not value:
                return f'{indent_str}{key} = {{}}'

            lines = [f'{indent_str}{key} = {{']
            for k, v in value.items():
                lines.append(self._format_attribute(k, v, indent + 2))
            lines.append(f'{indent_str}}}')
            return "\n".join(lines)

        # Fallback - convert to string
        else:
            return f'{indent_str}{key} = "{str(value)}"'

    def _format_value(self, value: Any) -> str:
        """Format a primitive value for HCL."""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return str(value).lower()
        else:
            return str(value)

    def preview_changes(self, resource_type: str, old_state: Dict,
                       new_state: Dict) -> Tuple[str, List[str]]:
        """
        Generate a diff preview showing what changed.

        Args:
            resource_type: Terraform resource type
            old_state: Previous state
            new_state: New state

        Returns:
            Tuple of (diff_text, changed_fields)
        """
        changed_fields = []
        diff_lines = []

        # Find added/changed fields
        for key, new_value in new_state.items():
            old_value = old_state.get(key)

            if old_value != new_value:
                changed_fields.append(key)

                if old_value is None:
                    diff_lines.append(f"  + {key} = {self._format_value(new_value)}")
                else:
                    diff_lines.append(f"  ~ {key} = {self._format_value(old_value)} -> {self._format_value(new_value)}")

        # Find removed fields
        for key in old_state.keys():
            if key not in new_state:
                changed_fields.append(key)
                diff_lines.append(f"  - {key} = {self._format_value(old_state[key])}")

        diff_text = "\n".join(diff_lines) if diff_lines else "  (no changes)"

        return diff_text, changed_fields

    def validate_generated_code(self, terraform_code: str) -> Tuple[bool, List[str]]:
        """
        Basic validation of generated Terraform code.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check for balanced braces
        open_braces = terraform_code.count("{")
        close_braces = terraform_code.count("}")
        if open_braces != close_braces:
            errors.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")

        # Check for resource block structure
        if not re.search(r'resource\s+"[^"]+"\s+"[^"]+"\s+{', terraform_code):
            errors.append("No valid resource block found")

        # Check for invalid characters in resource names
        resource_names = re.findall(r'resource\s+"[^"]+"\s+"([^"]+)"', terraform_code)
        for name in resource_names:
            if not re.match(r'^[a-zA-Z0-9_]+$', name):
                errors.append(f"Invalid resource name: {name} (must be alphanumeric + underscore)")

        is_valid = len(errors) == 0
        return is_valid, errors


# ============================================================================
# Resource-Specific Generators
# ============================================================================

class EC2InstanceGenerator:
    """Specialized generator for EC2 instances."""

    @staticmethod
    def generate(resource_id: str, aws_state: Dict) -> str:
        """Generate Terraform for EC2 instance."""
        generator = TerraformGenerator()
        result = generator.generate(resource_id, "ec2_instance", aws_state)

        # Add EC2-specific warnings
        if "instance_type" in aws_state:
            instance_type = aws_state["instance_type"]
            if instance_type.startswith("t2.") or instance_type.startswith("t3."):
                generator.warnings.append(
                    f"Instance type {instance_type} is burstable - monitor CPU credits"
                )

        return result.terraform_code


class RDSInstanceGenerator:
    """Specialized generator for RDS instances."""

    @staticmethod
    def generate(resource_id: str, aws_state: Dict) -> str:
        """Generate Terraform for RDS instance."""
        generator = TerraformGenerator()
        result = generator.generate(resource_id, "rds_instance", aws_state)

        # Add RDS-specific warnings
        if not aws_state.get("multi_az"):
            generator.warnings.append(
                "Multi-AZ is disabled - single point of failure"
            )

        if not aws_state.get("backup_retention_period"):
            generator.warnings.append(
                "Automated backups not configured - data loss risk"
            )

        return result.terraform_code


class S3BucketGenerator:
    """Specialized generator for S3 buckets."""

    @staticmethod
    def generate(bucket_name: str, aws_state: Dict) -> str:
        """Generate Terraform for S3 bucket."""
        generator = TerraformGenerator()
        result = generator.generate(bucket_name, "s3_bucket", aws_state)

        # Add S3-specific warnings
        if not aws_state.get("versioning", {}).get("enabled"):
            generator.warnings.append(
                "Versioning is disabled - cannot recover from accidental deletes"
            )

        if aws_state.get("acl") == "public-read":
            generator.warnings.append(
                "Bucket is publicly readable - security risk"
            )

        return result.terraform_code
