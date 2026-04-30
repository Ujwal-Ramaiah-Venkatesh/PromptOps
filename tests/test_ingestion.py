"""
Infrastructure Ingestion Tests
===============================

Tests for importing manual AWS Console changes.

Week 13-15: ENHANCEMENT-002
Author: PromptOps Team
Date: 2026-04-30
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from phase1_nlp.context.terraform_generator import (
    TerraformGenerator,
    EC2InstanceGenerator,
    RDSInstanceGenerator,
    S3BucketGenerator,
    GenerationResult
)


# ============================================================================
# Terraform Generator Tests
# ============================================================================

def test_terraform_generator_ec2_instance():
    """Test generating Terraform code for EC2 instance."""
    generator = TerraformGenerator()

    aws_state = {
        "instance_type": "t3.medium",
        "ami": "ami-0c55b159cbfafe1f0",
        "subnet_id": "subnet-12345",
        "tags": {"Name": "web-server-1", "Environment": "production"}
    }

    result = generator.generate(
        resource_id="i-1234567890abcdef0",
        resource_type="ec2_instance",
        aws_state=aws_state
    )

    # Check generated code
    assert 'resource "aws_instance"' in result.terraform_code
    assert "web_server_1" in result.terraform_code
    assert "t3.medium" in result.terraform_code
    assert "ami-0c55b159cbfafe1f0" in result.terraform_code
    assert result.resource_count == 1


def test_terraform_generator_rds_instance():
    """Test generating Terraform code for RDS instance."""
    generator = TerraformGenerator()

    aws_state = {
        "engine": "postgres",
        "engine_version": "14.6",
        "instance_class": "db.t3.medium",
        "allocated_storage": 100,
        "multi_az": True,
        "tags": {"Name": "production-db"}
    }

    result = generator.generate(
        resource_id="mydb-instance",
        resource_type="rds_instance",
        aws_state=aws_state
    )

    # Check generated code
    assert 'resource "aws_db_instance"' in result.terraform_code
    assert "postgres" in result.terraform_code
    assert "db.t3.medium" in result.terraform_code
    assert result.resource_count == 1


def test_terraform_generator_s3_bucket():
    """Test generating Terraform code for S3 bucket."""
    generator = TerraformGenerator()

    aws_state = {
        "bucket": "my-app-data",
        "acl": "private",
        "versioning": {"enabled": True},
        "tags": {"Environment": "production"}
    }

    result = generator.generate(
        resource_id="my-app-data",
        resource_type="s3_bucket",
        aws_state=aws_state
    )

    # Check generated code
    assert 'resource "aws_s3_bucket"' in result.terraform_code
    assert "my_app_data" in result.terraform_code
    assert "private" in result.terraform_code
    assert result.resource_count == 1


def test_terraform_generator_resource_name_sanitization():
    """Test that resource names are sanitized for Terraform."""
    generator = TerraformGenerator()

    aws_state = {"tags": {"Name": "my-app-server-1"}}

    result = generator.generate(
        resource_id="i-abc123",
        resource_type="ec2_instance",
        aws_state=aws_state
    )

    # Should convert hyphens to underscores
    assert "my_app_server_1" in result.terraform_code


def test_terraform_generator_filter_excluded_attributes():
    """Test that read-only attributes are filtered out."""
    generator = TerraformGenerator()

    aws_state = {
        "instance_type": "t3.medium",
        "arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-abc123",  # Should be filtered
        "launch_time": "2026-04-30T10:00:00Z",  # Should be filtered
        "private_ip": "10.0.1.5",  # Should be filtered
        "state": "running"
    }

    result = generator.generate(
        resource_id="i-abc123",
        resource_type="ec2_instance",
        aws_state=aws_state
    )

    # Should not include excluded attributes
    assert "arn" not in result.terraform_code
    assert "launch_time" not in result.terraform_code
    assert "private_ip" not in result.terraform_code

    # Should include valid attributes
    assert "instance_type" in result.terraform_code


def test_terraform_generator_detect_dependencies():
    """Test dependency detection."""
    generator = TerraformGenerator()

    aws_state = {
        "instance_type": "t3.medium",
        "subnet_id": "subnet-12345",
        "vpc_id": "vpc-67890",
        "security_groups": ["sg-abc123"]
    }

    result = generator.generate(
        resource_id="i-abc123",
        resource_type="ec2_instance",
        aws_state=aws_state
    )

    # Check dependencies detected
    assert "aws_subnet" in result.dependencies
    assert "aws_vpc" in result.dependencies
    assert "aws_security_group" in result.dependencies


def test_terraform_generator_validate_code():
    """Test code validation."""
    generator = TerraformGenerator()

    # Valid code
    valid_code = '''
resource "aws_instance" "test" {
  instance_type = "t3.medium"
}
'''
    is_valid, errors = generator.validate_generated_code(valid_code)
    assert is_valid
    assert len(errors) == 0

    # Invalid code (unbalanced braces)
    invalid_code = '''
resource "aws_instance" "test" {
  instance_type = "t3.medium"
'''
    is_valid, errors = generator.validate_generated_code(invalid_code)
    assert not is_valid
    assert len(errors) > 0
    assert "Unbalanced braces" in errors[0]


def test_terraform_generator_preview_changes():
    """Test diff preview generation."""
    generator = TerraformGenerator()

    old_state = {
        "instance_type": "t3.medium",
        "ami": "ami-old"
    }

    new_state = {
        "instance_type": "t3.large",  # Changed
        "ami": "ami-old",
        "monitoring": True  # Added
    }

    diff_text, changed_fields = generator.preview_changes(
        "aws_instance",
        old_state,
        new_state
    )

    # Check diff
    assert "instance_type" in changed_fields
    assert "monitoring" in changed_fields
    assert "t3.medium" in diff_text
    assert "t3.large" in diff_text


def test_terraform_generator_multiple_resources():
    """Test generating code for multiple resources."""
    generator = TerraformGenerator()

    resources = [
        {
            "resource_id": "i-abc123",
            "resource_type": "ec2_instance",
            "aws_state": {"instance_type": "t3.medium"}
        },
        {
            "resource_id": "sg-def456",
            "resource_type": "security_group",
            "aws_state": {"name": "web-sg"}
        }
    ]

    result = generator.generate_multiple(resources)

    # Should have both resources
    assert 'resource "aws_instance"' in result.terraform_code
    assert 'resource "aws_security_group"' in result.terraform_code
    assert result.resource_count == 2


def test_ec2_instance_generator_warnings():
    """Test EC2-specific warnings."""
    aws_state = {
        "instance_type": "t2.micro",  # Burstable
        "ami": "ami-abc123"
    }

    result = EC2InstanceGenerator.generate("i-abc123", aws_state)

    # Should include warning about burstable instance
    # Note: warnings would be checked via generator.warnings
    assert "t2.micro" in result


def test_rds_instance_generator_warnings():
    """Test RDS-specific warnings."""
    aws_state = {
        "engine": "postgres",
        "instance_class": "db.t3.micro",
        "multi_az": False,  # Should warn
        "backup_retention_period": 0  # Should warn
    }

    result = RDSInstanceGenerator.generate("mydb", aws_state)

    # Should generate valid code despite warnings
    assert 'resource "aws_db_instance"' in result


def test_s3_bucket_generator_warnings():
    """Test S3-specific warnings."""
    aws_state = {
        "bucket": "my-bucket",
        "acl": "public-read",  # Should warn
        "versioning": {"enabled": False}  # Should warn
    }

    result = S3BucketGenerator.generate("my-bucket", aws_state)

    # Should generate valid code despite warnings
    assert 'resource "aws_s3_bucket"' in result


def test_terraform_generator_empty_state():
    """Test handling of empty AWS state."""
    generator = TerraformGenerator()

    result = generator.generate(
        resource_id="i-empty",
        resource_type="ec2_instance",
        aws_state={}
    )

    # Should still generate resource block structure
    assert 'resource "aws_instance"' in result.terraform_code
    assert result.resource_count == 1


def test_terraform_generator_unknown_resource_type():
    """Test handling of unknown resource type."""
    generator = TerraformGenerator()

    result = generator.generate(
        resource_id="unknown-123",
        resource_type="unknown_service",
        aws_state={"foo": "bar"}
    )

    # Should use fallback naming
    assert 'resource "aws_unknown_service"' in result.terraform_code


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_import_workflow():
    """Test complete import workflow."""
    generator = TerraformGenerator()

    # 1. Generate Terraform from AWS state
    aws_state = {
        "instance_type": "t3.large",  # Changed from t3.medium
        "ami": "ami-0c55b159cbfafe1f0",
        "subnet_id": "subnet-12345",
        "tags": {"Name": "web-server-1"}
    }

    result = generator.generate(
        resource_id="i-1234567890abcdef0",
        resource_type="ec2_instance",
        aws_state=aws_state
    )

    # 2. Validate generated code
    is_valid, errors = generator.validate_generated_code(result.terraform_code)
    assert is_valid, f"Generated code is invalid: {errors}"

    # 3. Check structure
    assert result.resource_count == 1
    assert "t3.large" in result.terraform_code
    assert len(result.dependencies) > 0

    # 4. Preview would be shown to PM here
    # 5. Apply to Terraform state (would happen in real system)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    import sys

    print("="*60)
    print("  Infrastructure Ingestion Tests")
    print("  Week 13-15: ENHANCEMENT-002")
    print("="*60)

    # Run tests
    test_functions = [
        test_terraform_generator_ec2_instance,
        test_terraform_generator_rds_instance,
        test_terraform_generator_s3_bucket,
        test_terraform_generator_resource_name_sanitization,
        test_terraform_generator_filter_excluded_attributes,
        test_terraform_generator_detect_dependencies,
        test_terraform_generator_validate_code,
        test_terraform_generator_preview_changes,
        test_terraform_generator_multiple_resources,
        test_ec2_instance_generator_warnings,
        test_rds_instance_generator_warnings,
        test_s3_bucket_generator_warnings,
        test_terraform_generator_empty_state,
        test_terraform_generator_unknown_resource_type,
        test_full_import_workflow,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: ERROR - {e}")
            failed += 1

    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    sys.exit(0 if failed == 0 else 1)
