"""
Discovery & Onboarding Tests
=============================

Tests for AWS resource discovery and context inference.

Week 16-18: ENHANCEMENT-003
Author: PromptOps Team
Date: 2026-04-30
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import sys
import os

# Mock boto3 before importing discovery modules
sys.modules['boto3'] = MagicMock()
sys.modules['botocore'] = MagicMock()
sys.modules['botocore.exceptions'] = MagicMock()

# Add parent directory to path
parent_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'phase1-nlp'))

from discovery.aws_scanner import (
    Resource, ResourceInventory, AWSScanner, ScanProgress
)
from discovery.context_inference import (
    ContextInferenceEngine, TagPattern, NamingPattern
)
from discovery.dependency_mapper import (
    DependencyMapper, DependencyGraph, Dependency
)


# ============================================================================
# AWS Scanner Tests
# ============================================================================

def test_resource_creation():
    """Test Resource dataclass creation."""
    resource = Resource(
        resource_id="i-1234567890abcdef0",
        resource_type="ec2",
        region="us-east-1",
        name="web-prod-1",
        tags={"Environment": "production", "Project": "web-app"},
        aws_state={"instance_type": "t3.medium"}
    )

    assert resource.resource_id == "i-1234567890abcdef0"
    assert resource.resource_type == "ec2"
    assert resource.name == "web-prod-1"
    assert resource.tags["Environment"] == "production"


def test_resource_inventory_filtering():
    """Test ResourceInventory filtering methods."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", tags={"Env": "prod"}),
        Resource("i-2", "ec2", "us-west-2", tags={"Env": "dev"}),
        Resource("db-1", "rds", "us-east-1", tags={"Env": "prod"}),
    ]

    inventory = ResourceInventory(
        scan_id="scan-123",
        resources=resources,
        total_count=3,
        by_type={"ec2": 2, "rds": 1},
        by_region={"us-east-1": 2, "us-west-2": 1},
        scan_duration_seconds=10.5,
        regions_scanned=["us-east-1", "us-west-2"],
        errors=[]
    )

    # Test filter by type
    ec2_resources = inventory.filter_by_type("ec2")
    assert len(ec2_resources) == 2

    # Test filter by region
    us_east_resources = inventory.filter_by_region("us-east-1")
    assert len(us_east_resources) == 2

    # Test filter by tag
    prod_resources = inventory.filter_by_tag("Env", "prod")
    assert len(prod_resources) == 2


# ============================================================================
# Context Inference Tests
# ============================================================================

def test_infer_environment_from_tag():
    """Test environment inference from tags."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", tags={"Environment": "production"}),
        Resource("i-2", "ec2", "us-east-1", tags={"Env": "dev"}),
        Resource("i-3", "ec2", "us-east-1", tags={"environment": "staging"}),
    ]

    engine = ContextInferenceEngine(resources)
    enriched = engine.enrich_all_resources()

    assert enriched[0].inferred_environment == "production"
    assert enriched[0].confidence_score > 0.8  # High confidence

    assert enriched[1].inferred_environment == "development"
    assert enriched[2].inferred_environment == "staging"


def test_infer_environment_from_name():
    """Test environment inference from resource name."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", name="web-prod-1"),
        Resource("i-2", "ec2", "us-east-1", name="api-staging-2"),
        Resource("i-3", "ec2", "us-east-1", name="dev-worker-1"),
    ]

    engine = ContextInferenceEngine(resources)
    enriched = engine.enrich_all_resources()

    assert enriched[0].inferred_environment == "production"
    assert enriched[1].inferred_environment == "staging"
    assert enriched[2].inferred_environment == "development"


def test_infer_environment_from_instance_type():
    """Test environment inference from instance type."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", aws_state={"instance_type": "t3.nano"}),
        Resource("i-2", "ec2", "us-east-1", aws_state={"instance_type": "c5.4xlarge"}),
    ]

    engine = ContextInferenceEngine(resources)
    enriched = engine.enrich_all_resources()

    # t3.nano suggests development
    assert enriched[0].inferred_environment == "development"
    # Large instance suggests production
    # Note: This signal alone isn't strong enough, would need other signals


def test_infer_project_from_tag():
    """Test project inference from tags."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", tags={"Project": "web-app"}),
        Resource("i-2", "ec2", "us-east-1", tags={"Application": "mobile-api"}),
    ]

    engine = ContextInferenceEngine(resources)
    enriched = engine.enrich_all_resources()

    assert enriched[0].inferred_project == "web-app"
    assert enriched[1].inferred_project == "mobile-api"


def test_infer_project_from_name():
    """Test project inference from resource name."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", name="web-prod-1"),
        Resource("i-2", "ec2", "us-east-1", name="api-staging-2"),
        Resource("i-3", "ec2", "us-east-1", name="prod-analytics-1"),
    ]

    engine = ContextInferenceEngine(resources)
    enriched = engine.enrich_all_resources()

    assert enriched[0].inferred_project == "web"
    assert enriched[1].inferred_project == "api"
    assert enriched[2].inferred_project == "analytics"


def test_infer_owner_from_tag():
    """Test owner inference from tags."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", tags={"Owner": "john.doe@company.com"}),
        Resource("i-2", "ec2", "us-east-1", tags={"Team": "platform-team"}),
    ]

    engine = ContextInferenceEngine(resources)
    enriched = engine.enrich_all_resources()

    assert enriched[0].inferred_owner == "john.doe@company.com"
    assert enriched[1].inferred_owner == "platform-team"


def test_tag_pattern_detection():
    """Test detection of consistent tag patterns."""
    # 80% of resources have Environment tag → should detect as consistent
    resources = [
        Resource("i-1", "ec2", "us-east-1", tags={"Environment": "prod"}),
        Resource("i-2", "ec2", "us-east-1", tags={"Environment": "dev"}),
        Resource("i-3", "ec2", "us-east-1", tags={"Environment": "stage"}),
        Resource("i-4", "ec2", "us-east-1", tags={"Environment": "prod"}),
        Resource("i-5", "ec2", "us-east-1", tags={}),  # Missing tag
    ]

    engine = ContextInferenceEngine(resources)

    # Check if Environment tag is detected as consistent
    assert "Environment" in engine.tag_patterns
    env_pattern = engine.tag_patterns["Environment"]
    assert env_pattern.frequency == 0.8  # 4 out of 5
    assert env_pattern.is_consistent  # >80%


def test_naming_pattern_detection():
    """Test detection of naming conventions."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", name="web-prod-1"),
        Resource("i-2", "ec2", "us-east-1", name="api-prod-2"),
        Resource("i-3", "ec2", "us-east-1", name="worker-staging-1"),
        Resource("i-4", "ec2", "us-east-1", name="db-dev-1"),
        Resource("i-5", "ec2", "us-east-1", name="random-name"),  # Doesn't match
    ]

    engine = ContextInferenceEngine(resources)

    # Should detect app-env-number pattern
    assert len(engine.naming_patterns) > 0

    # Find the app-env-number pattern
    app_env_num_pattern = next(
        (p for p in engine.naming_patterns if 'app' in p.fields and 'env' in p.fields),
        None
    )
    assert app_env_num_pattern is not None
    assert app_env_num_pattern.frequency == 0.8  # 4 out of 5


def test_coverage_report():
    """Test coverage report generation."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", tags={"Environment": "prod", "Project": "web"}),
        Resource("i-2", "ec2", "us-east-1", name="api-dev-1"),
        Resource("i-3", "ec2", "us-east-1", tags={}),  # No context
    ]

    engine = ContextInferenceEngine(resources)
    engine.enrich_all_resources()

    report = engine.get_coverage_report()

    assert report['total_resources'] == 3
    assert report['environment_coverage']['count'] >= 2  # At least 2 have environment
    assert report['project_coverage']['count'] >= 2  # At least 2 have project


# ============================================================================
# Dependency Mapper Tests
# ============================================================================

def test_dependency_graph_creation():
    """Test DependencyGraph creation and methods."""
    graph = DependencyGraph()

    graph.add_dependency("i-1", "sg-1", "security_group", 1.0)
    graph.add_dependency("i-1", "subnet-1", "network", 1.0)

    # Test get dependencies
    deps = graph.get_dependencies_for("i-1")
    assert len(deps) == 2

    # Test get dependents
    dependents = graph.get_dependents_of("sg-1")
    assert len(dependents) == 1
    assert dependents[0].source_resource_id == "i-1"


def test_security_group_dependencies():
    """Test security group dependency detection."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", aws_state={"security_groups": ["sg-1", "sg-2"]}),
        Resource("sg-1", "security_group", "us-east-1", name="web-sg"),
        Resource("sg-2", "security_group", "us-east-1", name="db-sg"),
    ]

    mapper = DependencyMapper(resources)
    graph = mapper.build_dependency_graph()

    # Should have 2 security group dependencies
    sg_deps = [d for d in graph.dependencies if d.dependency_type == "security_group"]
    assert len(sg_deps) == 2


def test_network_dependencies():
    """Test network dependency detection."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", aws_state={"subnet_id": "subnet-1", "vpc_id": "vpc-1"}),
        Resource("subnet-1", "subnet", "us-east-1", aws_state={"vpc_id": "vpc-1"}),
        Resource("vpc-1", "vpc", "us-east-1"),
    ]

    mapper = DependencyMapper(resources)
    graph = mapper.build_dependency_graph()

    # Should have network dependencies: EC2→Subnet, EC2→VPC, Subnet→VPC
    network_deps = [d for d in graph.dependencies if d.dependency_type == "network"]
    assert len(network_deps) >= 2  # At least EC2→Subnet and EC2→VPC


def test_application_dependency_inference():
    """Test inference of application-level dependencies."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", name="web-prod-1", aws_state={"security_groups": ["sg-shared"]}),
        Resource("db-1", "rds", "us-east-1", name="db-prod", aws_state={"security_groups": ["sg-shared"]}),
        Resource("sg-shared", "security_group", "us-east-1", name="app-sg"),
    ]

    mapper = DependencyMapper(resources)
    graph = mapper.build_dependency_graph()

    # Should infer EC2→RDS dependency (they share security group)
    app_deps = [d for d in graph.dependencies if d.dependency_type == "application"]
    assert len(app_deps) >= 1

    # Find EC2→RDS dependency
    ec2_to_rds = next((d for d in app_deps if d.source_resource_id == "i-1" and d.target_resource_id == "db-1"), None)
    assert ec2_to_rds is not None
    assert ec2_to_rds.confidence_score < 1.0  # Inferred, not explicit


def test_dependency_report():
    """Test dependency analysis report."""
    resources = [
        Resource("i-1", "ec2", "us-east-1", aws_state={"security_groups": ["sg-1"], "subnet_id": "subnet-1"}),
        Resource("sg-1", "security_group", "us-east-1"),
        Resource("subnet-1", "subnet", "us-east-1"),
    ]

    mapper = DependencyMapper(resources)
    graph = mapper.build_dependency_graph()

    report = mapper.get_dependency_report(graph)

    assert report['total_dependencies'] >= 2
    assert 'by_type' in report
    assert 'most_dependent_resources' in report


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_discovery_workflow():
    """Test complete discovery workflow."""
    # Create mock resources
    resources = [
        Resource("i-1", "ec2", "us-east-1", name="web-prod-1",
                tags={"Environment": "production", "Project": "web-app"},
                aws_state={"security_groups": ["sg-1"], "subnet_id": "subnet-1"}),
        Resource("i-2", "ec2", "us-east-1", name="api-prod-1",
                tags={"Environment": "production", "Project": "api"},
                aws_state={"security_groups": ["sg-1"], "subnet_id": "subnet-1"}),
        Resource("db-1", "rds", "us-east-1", name="db-prod",
                tags={"Environment": "production"},
                aws_state={"security_groups": ["sg-1"]}),
        Resource("sg-1", "security_group", "us-east-1", name="prod-sg"),
        Resource("subnet-1", "subnet", "us-east-1", aws_state={"vpc_id": "vpc-1"}),
        Resource("vpc-1", "vpc", "us-east-1", tags={"Environment": "production"}),
    ]

    # Step 1: Infer context
    inference_engine = ContextInferenceEngine(resources)
    enriched_resources = inference_engine.enrich_all_resources()

    # Verify environment inference
    assert all(r.inferred_environment == "production" for r in enriched_resources)

    # Step 2: Build dependency graph
    mapper = DependencyMapper(enriched_resources)
    graph = mapper.build_dependency_graph()

    # Verify dependencies detected
    assert len(graph.dependencies) > 0

    # Verify network dependencies
    network_deps = [d for d in graph.dependencies if d.dependency_type == "network"]
    assert len(network_deps) > 0

    # Step 3: Generate reports
    coverage_report = inference_engine.get_coverage_report()
    dependency_report = mapper.get_dependency_report(graph)

    assert coverage_report['environment_coverage']['percentage'] == 100.0
    assert dependency_report['total_dependencies'] > 0


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    import sys

    print("="*60)
    print("  Discovery & Onboarding Tests")
    print("  Week 16-18: ENHANCEMENT-003")
    print("="*60)

    # Run tests
    test_functions = [
        test_resource_creation,
        test_resource_inventory_filtering,
        test_infer_environment_from_tag,
        test_infer_environment_from_name,
        test_infer_environment_from_instance_type,
        test_infer_project_from_tag,
        test_infer_project_from_name,
        test_infer_owner_from_tag,
        test_tag_pattern_detection,
        test_naming_pattern_detection,
        test_coverage_report,
        test_dependency_graph_creation,
        test_security_group_dependencies,
        test_network_dependencies,
        test_application_dependency_inference,
        test_dependency_report,
        test_full_discovery_workflow,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            print(f"[PASS] {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test_func.__name__}: {e}")
            failed += 1

    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    sys.exit(0 if failed == 0 else 1)
