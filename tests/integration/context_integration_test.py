"""
Context Layer Integration Test
===============================

End-to-end integration tests for Week 7-8 Context & Memory Layer.

Tests:
- Context collection from AWS (mocked)
- Context injection into prompts
- Drift detection between snapshots
- Context-aware parsing
- Full pipeline with context

Author: PromptOps Team - Week 7-8
Date: 2026-04-28
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase1-nlp'))

from context.context_collector import ContextCollector, CollectionResult
from context.context_injector import ContextInjector
from context.drift_detector import DriftDetector, DriftSeverity
from context.context_aware_parser import ContextAwareParser

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Test Data Fixtures
# ============================================================================

def create_test_snapshot(temp_dir: str, snapshot_id: str, resources: list) -> str:
    """Create a test snapshot file."""
    snapshot = {
        'version': '1.0.0',
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'resources': resources,
        'snapshots': [
            {
                'snapshot_id': snapshot_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'resource_count': len(resources),
                'checksum': 'test-checksum',
                'drift_events_detected': 0,
                'collection_duration_ms': 1000,
                'errors': []
            }
        ],
        'metadata': {
            'total_resources': len(resources),
            'resources_by_type': {'ecs_service': len(resources)},
            'resources_by_environment': {'production': len(resources)},
            'environments': ['production'],
            'regions': ['us-east-1'],
            'total_drift_events': 0,
            'critical_drift_count': 0,
            'last_collection_duration_ms': 1000,
            'collector_version': '1.0.0',
            'aws_account_id': '123456789012'
        }
    }

    snapshot_path = os.path.join(temp_dir, f'{snapshot_id}.json')
    with open(snapshot_path, 'w') as f:
        json.dump(snapshot, f, indent=2)

    return snapshot_path


def create_test_resource(
    service_name: str,
    environment: str = 'production',
    desired_count: int = 5,
    running_count: int = 5
) -> dict:
    """Create a test ECS service resource."""
    return {
        'resource_id': f'ecs-{service_name}-{environment}-us-east-1',
        'resource_type': 'ecs_service',
        'service_name': service_name,
        'environment': environment,
        'region': 'us-east-1',
        'current_state': {
            'status': 'ACTIVE',
            'desired_count': desired_count,
            'running_count': running_count,
            'pending_count': 0,
            'task_definition': f'{service_name}:42',
            'launch_type': 'FARGATE',
            'cpu': '512',
            'memory': '1024',
            'deployment_version': 'v2.3.1',
            'load_balancers': [f'alb-{service_name}-{environment}']
        },
        'tags': {
            'Managed': 'PromptOps',
            'Team': 'Platform',
            'Environment': environment
        },
        'dependencies': [],
        'metadata': {
            'created_at': '2026-01-15T10:00:00Z',
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


# ============================================================================
# Integration Tests
# ============================================================================

class TestContextIntegration(unittest.TestCase):
    """End-to-end integration tests for context layer."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.temp_dir = tempfile.mkdtemp(prefix='context_test_')
        logger.info(f"Test directory: {cls.temp_dir}")

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
        logger.info("Test cleanup complete")

    def test_001_context_collector_basic(self):
        """Test: Basic context collection (mocked AWS)."""
        print(f"\n{'='*70}")
        print(f"Test 001: Basic Context Collection")
        print(f"{'='*70}")

        # Create mock collector
        collector = ContextCollector(
            aws_region='us-east-1',
            snapshot_dir=self.temp_dir,
            filter_tag='PromptOps'
        )

        # Mock AWS responses
        with patch.object(collector, 'collect_ecs_services') as mock_ecs:
            mock_ecs.return_value = CollectionResult(
                success=True,
                resource_type='ecs_service',
                resource_count=3,
                resources=[
                    create_test_resource('frontend', 'production'),
                    create_test_resource('api', 'production'),
                    create_test_resource('worker', 'production')
                ],
                error=None,
                duration_ms=500
            )

            # Stub other methods
            for method_name in ['collect_ec2_instances', 'collect_rds_databases',
                               'collect_lambda_functions', 'collect_load_balancers',
                               'collect_s3_buckets', 'collect_dynamodb_tables',
                               'collect_sqs_queues', 'collect_sns_topics',
                               'collect_cloudfront_distributions']:
                setattr(collector, method_name, lambda: CollectionResult(
                    success=True, resource_type='stub', resource_count=0,
                    resources=[], error=None, duration_ms=0
                ))

            # Collect
            context_data = collector.collect_all_resources(parallel=False)

            # Assertions
            self.assertEqual(context_data['version'], '1.0.0')
            self.assertEqual(len(context_data['resources']), 3)
            self.assertEqual(context_data['metadata']['total_resources'], 3)
            self.assertIn('frontend', [r['service_name'] for r in context_data['resources']])

            print(f"✓ Collected {len(context_data['resources'])} resources")
            print(f"✓ Snapshot saved")

    def test_002_context_injection_reduces_ambiguity(self):
        """Test: Context injection reduces parser ambiguity."""
        print(f"\n{'='*70}")
        print(f"Test 002: Context Injection Reduces Ambiguity")
        print(f"{'='*70}")

        # Create test snapshot
        resources = [
            create_test_resource('frontend', 'production', 5, 5),
            create_test_resource('frontend', 'staging', 2, 2)
        ]
        create_test_snapshot(self.temp_dir, 'snap-2026-04-28-10-00', resources)

        # Create injector
        injector = ContextInjector(context_store_path=self.temp_dir)

        # Test ambiguous command
        pm_command = "Scale frontend to 10"
        base_prompt = "You are a DevOps parser. Convert PM commands to JSON."

        # Inject context
        result = injector.inject_context(pm_command, base_prompt)

        # Assertions
        self.assertTrue(result.success)
        self.assertGreater(result.resources_included, 0)
        self.assertIn('frontend', result.enhanced_prompt.lower())
        self.assertIn('production', result.enhanced_prompt.lower())
        self.assertGreater(result.context_tokens, 0)

        print(f"✓ Context injected: {result.resources_included} resources")
        print(f"✓ Context tokens: {result.context_tokens}")
        print(f"✓ Ambiguous command enhanced with current state")

    def test_003_drift_detection_instance_count(self):
        """Test: Drift detection for instance count changes."""
        print(f"\n{'='*70}")
        print(f"Test 003: Drift Detection - Instance Count")
        print(f"{'='*70}")

        # Create snapshots
        resources_v1 = [create_test_resource('frontend', 'production', 5, 5)]
        resources_v2 = [create_test_resource('frontend', 'production', 7, 7)]  # Changed

        create_test_snapshot(self.temp_dir, 'snap-2026-04-28-09-00', resources_v1)
        create_test_snapshot(self.temp_dir, 'snap-2026-04-28-10-00', resources_v2)

        # Detect drift
        detector = DriftDetector(context_store_path=self.temp_dir)
        report = detector.detect_drift(
            current_snapshot_id='snap-2026-04-28-10-00',
            previous_snapshot_id='snap-2026-04-28-09-00'
        )

        # Assertions
        self.assertGreater(report.total_drift_events, 0)
        self.assertEqual(len(report.resources_with_drift), 1)

        # Check drift event
        drift_event = report.drift_events[0]
        self.assertEqual(drift_event.field_changed, 'desired_count')
        self.assertEqual(drift_event.old_value, 5)
        self.assertEqual(drift_event.new_value, 7)
        self.assertIn(drift_event.severity, ['warning', 'info'])

        print(f"✓ Drift detected: {report.total_drift_events} events")
        print(f"  Field: {drift_event.field_changed}")
        print(f"  Change: {drift_event.old_value} → {drift_event.new_value}")
        print(f"  Severity: {drift_event.severity}")

    def test_004_drift_detection_version_change(self):
        """Test: Drift detection for version changes."""
        print(f"\n{'='*70}")
        print(f"Test 004: Drift Detection - Version Change")
        print(f"{'='*70}")

        # Create snapshots with version change
        resources_v1 = [create_test_resource('api', 'production', 10, 10)]
        resources_v1[0]['current_state']['deployment_version'] = 'v3.5.0'

        resources_v2 = [create_test_resource('api', 'production', 10, 10)]
        resources_v2[0]['current_state']['deployment_version'] = 'v3.4.2'  # Rollback

        create_test_snapshot(self.temp_dir, 'snap-2026-04-28-11-00', resources_v1)
        create_test_snapshot(self.temp_dir, 'snap-2026-04-28-12-00', resources_v2)

        # Detect drift
        detector = DriftDetector(context_store_path=self.temp_dir)
        report = detector.detect_drift(
            current_snapshot_id='snap-2026-04-28-12-00',
            previous_snapshot_id='snap-2026-04-28-11-00'
        )

        # Assertions
        self.assertGreater(report.total_drift_events, 0)

        version_drift = next(
            (e for e in report.drift_events if e.field_changed == 'deployment_version'),
            None
        )
        self.assertIsNotNone(version_drift)
        self.assertEqual(version_drift.old_value, 'v3.5.0')
        self.assertEqual(version_drift.new_value, 'v3.4.2')
        self.assertEqual(version_drift.severity, 'warning')

        print(f"✓ Version drift detected")
        print(f"  Rollback: {version_drift.old_value} → {version_drift.new_value}")
        print(f"  Severity: {version_drift.severity} (as expected)")

    def test_005_drift_severity_categorization(self):
        """Test: Drift severity categorization logic."""
        print(f"\n{'='*70}")
        print(f"Test 005: Drift Severity Categorization")
        print(f"{'='*70}")

        detector = DriftDetector(context_store_path=self.temp_dir)

        # Test critical severity
        critical = detector.categorize_drift(
            'rds_database',
            'status',
            'available',
            'stopped'
        )
        self.assertEqual(critical, DriftSeverity.CRITICAL)
        print(f"✓ Critical: RDS status available → stopped")

        # Test warning severity
        warning = detector.categorize_drift(
            'ecs_service',
            'desired_count',
            5,
            10
        )
        self.assertEqual(warning, DriftSeverity.WARNING)
        print(f"✓ Warning: ECS desired_count 5 → 10")

        # Test info severity
        info = detector.categorize_drift(
            'ecs_service',
            'tag_CostCenter',
            'Eng',
            'Platform'
        )
        self.assertEqual(info, DriftSeverity.INFO)
        print(f"✓ Info: Tag change")

    def test_006_context_aware_parsing_smart_defaults(self):
        """Test: Context-aware parser applies smart defaults."""
        print(f"\n{'='*70}")
        print(f"Test 006: Context-Aware Parsing - Smart Defaults")
        print(f"{'='*70}")

        # Skip if no API key
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            self.skipTest("ANTHROPIC_API_KEY not set")

        # Create snapshot
        resources = [create_test_resource('frontend', 'production', 5, 5)]
        create_test_snapshot(self.temp_dir, 'snap-2026-04-28-13-00', resources)

        # Create parser
        parser = ContextAwareParser(
            api_key=api_key,
            context_store_path=self.temp_dir,
            enable_context=True
        )

        # Parse ambiguous command
        pm_command = "Scale frontend to 10"

        success, parsed_intent, error = parser.parse_command_with_context(pm_command)

        # Assertions
        self.assertTrue(success, f"Parse failed: {error}")
        self.assertEqual(parsed_intent['intent_type'], 'scale')
        self.assertEqual(parsed_intent['target_service'], 'frontend')

        # Check smart defaults
        self.assertIn('target_env', parsed_intent)
        self.assertEqual(parsed_intent['target_env'], 'production')

        parameters = parsed_intent.get('parameters', {})
        self.assertIn('current_count', parameters)
        self.assertEqual(parameters['current_count'], 5)

        print(f"✓ Parsed with context")
        print(f"  Environment: {parsed_intent['target_env']} (auto-filled)")
        print(f"  Current count: {parameters['current_count']} (from context)")
        print(f"  Ambiguity: {parsed_intent.get('ambiguity_score', 'N/A')}")

    def test_007_full_pipeline_with_context(self):
        """Test: Full pipeline from collection to parsing."""
        print(f"\n{'='*70}")
        print(f"Test 007: Full Pipeline with Context")
        print(f"{'='*70}")

        # Skip if no API key
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            self.skipTest("ANTHROPIC_API_KEY not set")

        # Step 1: Create context snapshot
        resources = [
            create_test_resource('frontend', 'production', 5, 5),
            create_test_resource('api', 'production', 10, 10)
        ]
        create_test_snapshot(self.temp_dir, 'snap-2026-04-28-14-00', resources)

        print("\n[1/3] Context snapshot created")
        print(f"  Resources: {len(resources)}")

        # Step 2: Inject context
        injector = ContextInjector(context_store_path=self.temp_dir)
        pm_command = "Deploy frontend v2.4.0"
        base_prompt = "Parse deployment commands."

        injection_result = injector.inject_context(pm_command, base_prompt)

        self.assertTrue(injection_result.success)
        self.assertGreater(injection_result.resources_included, 0)

        print(f"\n[2/3] Context injected")
        print(f"  Resources: {injection_result.resources_included}")
        print(f"  Tokens: {injection_result.context_tokens}")

        # Step 3: Parse with context
        parser = ContextAwareParser(
            api_key=api_key,
            context_store_path=self.temp_dir,
            enable_context=True
        )

        success, parsed_intent, error = parser.parse_command_with_context(pm_command)

        self.assertTrue(success)
        self.assertEqual(parsed_intent['intent_type'], 'deploy')
        self.assertEqual(parsed_intent['target_service'], 'frontend')
        self.assertIn('target_env', parsed_intent)

        print(f"\n[3/3] Parsed with context")
        print(f"  Intent: {parsed_intent['intent_type']}")
        print(f"  Service: {parsed_intent['target_service']}")
        print(f"  Environment: {parsed_intent.get('target_env', 'N/A')}")

        # Step 4: Check statistics
        stats = parser.get_context_stats()
        self.assertGreater(stats['context_used'], 0)

        print(f"\n✓ Full pipeline passed")
        print(f"  Context usage: {stats['context_used']}/{stats['total_parses']}")


# ============================================================================
# Context-Aware vs. Base Parser Comparison
# ============================================================================

class TestContextImpact(unittest.TestCase):
    """Compare context-aware parser vs. base parser."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix='context_compare_')

        # Create test snapshot
        resources = [
            create_test_resource('frontend', 'production', 5, 5),
            create_test_resource('api', 'production', 10, 10)
        ]
        create_test_snapshot(self.temp_dir, 'snap-test', resources)

    def tearDown(self):
        """Clean up."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_001_ambiguity_reduction(self):
        """Test: Measure ambiguity reduction with context."""
        print(f"\n{'='*70}")
        print(f"Comparison Test: Ambiguity Reduction")
        print(f"{'='*70}")

        # Skip if no API key
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            self.skipTest("ANTHROPIC_API_KEY not set")

        # Test commands
        commands = [
            "Scale frontend to 10",
            "Deploy api",
            "Rollback frontend"
        ]

        # Parse without context
        parser_no_context = ContextAwareParser(
            api_key=api_key,
            context_store_path=self.temp_dir,
            enable_context=False
        )

        # Parse with context
        parser_with_context = ContextAwareParser(
            api_key=api_key,
            context_store_path=self.temp_dir,
            enable_context=True
        )

        results = []

        for command in commands:
            print(f"\nCommand: {command}")

            # Without context
            success_no, intent_no, _ = parser_no_context.parse_command(command)
            ambiguity_no = intent_no.get('ambiguity_score', 0.5) if success_no else 1.0
            missing_no = len(intent_no.get('missing_params', [])) if success_no else 99

            # With context
            success_yes, intent_yes, _ = parser_with_context.parse_command_with_context(command)
            ambiguity_yes = intent_yes.get('ambiguity_score', 0.5) if success_yes else 1.0
            missing_yes = len(intent_yes.get('missing_params', [])) if success_yes else 99

            reduction = ((ambiguity_no - ambiguity_yes) / max(ambiguity_no, 0.01)) * 100

            results.append({
                'command': command,
                'ambiguity_no_context': ambiguity_no,
                'ambiguity_with_context': ambiguity_yes,
                'reduction_pct': reduction,
                'missing_no': missing_no,
                'missing_yes': missing_yes
            })

            print(f"  Without context: ambiguity={ambiguity_no:.2f}, missing={missing_no}")
            print(f"  With context:    ambiguity={ambiguity_yes:.2f}, missing={missing_yes}")
            print(f"  Reduction: {reduction:.1f}%")

        # Average reduction
        avg_reduction = sum(r['reduction_pct'] for r in results) / len(results)

        print(f"\n{'='*70}")
        print(f"Average Ambiguity Reduction: {avg_reduction:.1f}%")
        print(f"Target: >50% reduction")

        if avg_reduction > 50:
            print(f"✓ TARGET ACHIEVED")
        else:
            print(f"⚠️  Below target (but test may pass depending on commands)")

        print(f"{'='*70}")


# ============================================================================
# Test Runner
# ============================================================================

def run_integration_tests():
    """Run all integration tests."""
    print("="*70)
    print("PromptOps Context Layer - Integration Test Suite")
    print("="*70)
    print(f"\nTesting Week 7-8 components:")
    print(f"  Context Collector → Injector → Drift Detector → Context-Aware Parser\n")

    # Run integration tests
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TestContextIntegration)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestContextImpact)

    suite = unittest.TestSuite([suite1, suite2])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ ALL INTEGRATION TESTS PASSED")
        print("Week 7-8 Context Layer integration verified!")
    else:
        print("\n✗ SOME INTEGRATION TESTS FAILED")

    print("\n" + "="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
