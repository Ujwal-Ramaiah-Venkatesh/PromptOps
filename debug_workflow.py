"""Debug full workflow test."""

import sys
import os
from unittest.mock import MagicMock

# Mock boto3
sys.modules['boto3'] = MagicMock()
sys.modules['botocore'] = MagicMock()
sys.modules['botocore.exceptions'] = MagicMock()

# Add paths
parent_dir = os.path.dirname(__file__)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'phase1-nlp'))

from discovery.aws_scanner import Resource
from discovery.context_inference import ContextInferenceEngine
from discovery.dependency_mapper import DependencyMapper

print("="*60)
print("Full Discovery Workflow Test")
print("="*60)

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
print("\nStep 1: Context Inference")
print("-" * 40)
inference_engine = ContextInferenceEngine(resources)
enriched_resources = inference_engine.enrich_all_resources()

# Verify environment inference
all_prod = all(r.inferred_environment == "production" for r in enriched_resources)
print(f"All resources inferred as production: {all_prod}")

for r in enriched_resources:
    print(f"{r.resource_id}: env={r.inferred_environment}, confidence={r.confidence_score:.2f}")

if not all_prod:
    print("FAIL: Not all resources inferred as production")
    for r in enriched_resources:
        if r.inferred_environment != "production":
            print(f"  {r.resource_id}: {r.inferred_environment}")

# Step 2: Build dependency graph
print("\nStep 2: Dependency Graph")
print("-" * 40)
mapper = DependencyMapper(enriched_resources)
graph = mapper.build_dependency_graph()

print(f"Total dependencies: {len(graph.dependencies)}")

# Verify dependencies detected
has_deps = len(graph.dependencies) > 0
print(f"Has dependencies: {has_deps}")

# Verify network dependencies
network_deps = [d for d in graph.dependencies if d.dependency_type == "network"]
print(f"Network dependencies: {len(network_deps)}")
has_network_deps = len(network_deps) > 0
print(f"Has network dependencies: {has_network_deps}")

# Step 3: Generate reports
print("\nStep 3: Reports")
print("-" * 40)
coverage_report = inference_engine.get_coverage_report()
dependency_report = mapper.get_dependency_report(graph)

env_coverage = coverage_report['environment_coverage']['percentage']
print(f"Environment coverage: {env_coverage}%")
print(f"Expected: 100%")
print(f"Match: {env_coverage == 100.0}")

total_deps = dependency_report['total_dependencies']
print(f"Total dependencies in report: {total_deps}")
print(f"Expected: > 0")
print(f"Match: {total_deps > 0}")

print("\n" + "="*60)
if all_prod and has_deps and has_network_deps and env_coverage == 100.0 and total_deps > 0:
    print("TEST PASSED")
else:
    print("TEST FAILED")
    if not all_prod:
        print("  - Not all resources have production environment")
    if not has_deps:
        print("  - No dependencies detected")
    if not has_network_deps:
        print("  - No network dependencies")
    if env_coverage != 100.0:
        print(f"  - Environment coverage is {env_coverage}%, expected 100%")
    if not total_deps > 0:
        print("  - No dependencies in report")
