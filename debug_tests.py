"""Debug failing discovery tests."""

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

print("="*60)
print("Test 1: Environment inference from tag")
print("="*60)

resources = [
    Resource("i-1", "ec2", "us-east-1", tags={"Environment": "production"}),
    Resource("i-2", "ec2", "us-east-1", tags={"Env": "dev"}),
    Resource("i-3", "ec2", "us-east-1", tags={"environment": "staging"}),
]

engine = ContextInferenceEngine(resources)
enriched = engine.enrich_all_resources()

print(f"Resource 1:")
print(f"  inferred_environment: {enriched[0].inferred_environment}")
print(f"  inferred_project: {enriched[0].inferred_project}")
print(f"  inferred_owner: {enriched[0].inferred_owner}")
print(f"  confidence_score: {enriched[0].confidence_score}")
print(f"  Expected: confidence_score > 0.8")
print(f"  Actual: {enriched[0].confidence_score > 0.8}")
print()

print("="*60)
print("Test 2: Project inference from name")
print("="*60)

resources2 = [
    Resource("i-1", "ec2", "us-east-1", name="web-prod-1"),
    Resource("i-2", "ec2", "us-east-1", name="api-staging-2"),
    Resource("i-3", "ec2", "us-east-1", name="prod-analytics-1"),
]

engine2 = ContextInferenceEngine(resources2)
enriched2 = engine2.enrich_all_resources()

print(f"Resource 1 (web-prod-1):")
print(f"  inferred_project: {enriched2[0].inferred_project}")
print(f"  Expected: 'web'")
print(f"  Match: {enriched2[0].inferred_project == 'web'}")
print()

print(f"Resource 2 (api-staging-2):")
print(f"  inferred_project: {enriched2[1].inferred_project}")
print(f"  Expected: 'api'")
print(f"  Match: {enriched2[1].inferred_project == 'api'}")
print()

print(f"Resource 3 (prod-analytics-1):")
print(f"  inferred_project: {enriched2[2].inferred_project}")
print(f"  Expected: 'analytics'")
print(f"  Match: {enriched2[2].inferred_project == 'analytics'}")
print()

print("="*60)
print("Test 3: Tag pattern detection")
print("="*60)

resources3 = [
    Resource("i-1", "ec2", "us-east-1", tags={"Environment": "prod"}),
    Resource("i-2", "ec2", "us-east-1", tags={"Environment": "dev"}),
    Resource("i-3", "ec2", "us-east-1", tags={"Environment": "stage"}),
    Resource("i-4", "ec2", "us-east-1", tags={"Environment": "prod"}),
    Resource("i-5", "ec2", "us-east-1", tags={}),
]

engine3 = ContextInferenceEngine(resources3)
print(f"Tag patterns detected: {list(engine3.tag_patterns.keys())}")

if "Environment" in engine3.tag_patterns:
    env_pattern = engine3.tag_patterns["Environment"]
    print(f"Environment tag:")
    print(f"  frequency: {env_pattern.frequency}")
    print(f"  is_consistent: {env_pattern.is_consistent}")
    print(f"  Expected frequency: 0.8 (4/5)")
    print(f"  Expected is_consistent: True")
else:
    print("ERROR: Environment tag not found in patterns!")

print()

print("="*60)
print("Test 4: Naming pattern detection")
print("="*60)

resources4 = [
    Resource("i-1", "ec2", "us-east-1", name="web-prod-1"),
    Resource("i-2", "ec2", "us-east-1", name="api-prod-2"),
    Resource("i-3", "ec2", "us-east-1", name="worker-staging-1"),
    Resource("i-4", "ec2", "us-east-1", name="db-dev-1"),
    Resource("i-5", "ec2", "us-east-1", name="random-name"),
]

engine4 = ContextInferenceEngine(resources4)
print(f"Naming patterns detected: {len(engine4.naming_patterns)}")

for i, pattern in enumerate(engine4.naming_patterns):
    print(f"Pattern {i+1}:")
    print(f"  pattern: {pattern.pattern}")
    print(f"  fields: {pattern.fields}")
    print(f"  frequency: {pattern.frequency}")
    print(f"  example: {pattern.example}")

app_env_num_pattern = next(
    (p for p in engine4.naming_patterns if 'app' in p.fields and 'env' in p.fields),
    None
)
if app_env_num_pattern:
    print(f"\nFound app-env-number pattern!")
    print(f"  frequency: {app_env_num_pattern.frequency}")
    print(f"  Expected: 0.8 (4/5)")
else:
    print("\nERROR: app-env-number pattern not found!")
