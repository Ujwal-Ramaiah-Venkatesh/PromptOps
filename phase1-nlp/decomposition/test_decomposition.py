"""
Decomposition Engine Test Suite
================================

Comprehensive tests for task decomposition with 25 test cases covering:
- Simple commands (5 tests)
- Complex multi-step commands (10 tests)
- Dependency edge cases (5 tests)
- Failure scenarios (5 tests)

Target: >85% accuracy on all tests

Author: PromptOps Team - Week 5-6
Date: 2026-04-21
"""

import unittest
import os
import sys
import json
import logging
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decomposition.decomposition_engine import DecompositionEngine
from decomposition.dependency_resolver import DependencyResolver

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Less verbose for tests
logger = logging.getLogger(__name__)


# ============================================================================
# Test Cases
# ============================================================================

class TestDecomposition(unittest.TestCase):
    """
    Test suite for decomposition engine.
    """

    @classmethod
    def setUpClass(cls):
        """Initialize decomposition engine once for all tests."""
        api_key = os.environ.get('ANTHROPIC_API_KEY')

        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Cannot run tests.\n"
                "Set with: $env:ANTHROPIC_API_KEY=\"sk-ant-...\""
            )

        cls.engine = DecompositionEngine(api_key)
        cls.dependency_resolver = DependencyResolver()

        logger.info("Test suite initialized")

    def _decompose_and_validate(
        self,
        intent: Dict[str, Any],
        expected_min_tasks: int,
        expected_max_tasks: int,
        expected_phases: List[str],
        should_require_approval: bool = None
    ) -> Dict[str, Any]:
        """
        Helper to decompose and validate common properties.

        Args:
            intent: Parsed intent to decompose
            expected_min_tasks: Minimum expected sub-tasks
            expected_max_tasks: Maximum expected sub-tasks
            expected_phases: Expected phases (subset)
            should_require_approval: Whether any task should require approval

        Returns:
            Decomposition result
        """
        print(f"\n{'='*70}")
        print(f"Testing: {intent['original_command']}")
        print(f"Intent: {intent['intent_type']}")
        print(f"{'='*70}")

        success, decomposition, error = self.engine.decompose(intent)

        # Basic assertions
        self.assertTrue(success, f"Decomposition failed: {error}")
        self.assertIsInstance(decomposition, dict)
        self.assertIn('sub_tasks', decomposition)

        sub_tasks = decomposition['sub_tasks']
        total_tasks = len(sub_tasks)

        print(f"✓ Generated {total_tasks} sub-tasks")

        # Task count validation
        self.assertGreaterEqual(
            total_tasks,
            expected_min_tasks,
            f"Too few sub-tasks: {total_tasks} < {expected_min_tasks}"
        )

        self.assertLessEqual(
            total_tasks,
            expected_max_tasks,
            f"Too many sub-tasks: {total_tasks} > {expected_max_tasks}"
        )

        # Validate phase coverage
        task_phases = set(task['phase'] for task in sub_tasks)
        for expected_phase in expected_phases:
            self.assertIn(
                expected_phase,
                task_phases,
                f"Missing expected phase: {expected_phase}"
            )

        # Validate approval requirement
        if should_require_approval is not None:
            has_approval = any(task.get('approval_required', False) for task in sub_tasks)
            if should_require_approval:
                self.assertTrue(has_approval, "No approval gate found (expected one)")
            else:
                self.assertFalse(has_approval, "Unexpected approval gate found")

        # Dependency validation
        self.dependency_resolver.build_graph(sub_tasks)
        validation = self.dependency_resolver.validate()

        self.assertTrue(validation.is_valid, f"Dependency validation failed: {validation.errors}")
        self.assertEqual(len(validation.circular_dependencies), 0, "Circular dependencies detected")

        print(f"✓ All validations passed")

        return decomposition

    # ========================================================================
    # Category 1: Simple Commands (5 tests)
    # ========================================================================

    def test_001_simple_deploy_staging(self):
        """Test: Simple deploy to staging."""
        intent = {
            "command_id": "test-001",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy API to staging",
            "intent_type": "deploy",
            "confidence_score": 0.95,
            "target_service": "api",
            "target_env": "staging",
            "parameters": {"version": "latest"},
            "risk_level": "medium"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=5,
            expected_max_tasks=12,
            expected_phases=['pre_validation', 'deployment', 'validation'],
            should_require_approval=False
        )

        # Staging should not require approval
        self.assertFalse(
            any(t.get('approval_required') for t in decomposition['sub_tasks']),
            "Staging deployment should not require approval"
        )

    def test_002_simple_scale_up(self):
        """Test: Simple scale up operation."""
        intent = {
            "command_id": "test-002",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Scale backend to 10 instances",
            "intent_type": "scale",
            "confidence_score": 0.92,
            "target_service": "backend",
            "target_env": None,
            "parameters": {"count": 10, "direction": "up"},
            "risk_level": "medium"
        }

        self._decompose_and_validate(
            intent,
            expected_min_tasks=6,
            expected_max_tasks=12,
            expected_phases=['pre_validation', 'scaling', 'validation']
        )

    def test_003_simple_rollback(self):
        """Test: Simple rollback command."""
        intent = {
            "command_id": "test-003",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Rollback frontend to previous version",
            "intent_type": "rollback",
            "confidence_score": 0.90,
            "target_service": "frontend",
            "target_env": "production",
            "parameters": {"target_version": "previous"},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=6,
            expected_max_tasks=10,
            expected_phases=['pre_validation', 'rollback', 'validation'],
            should_require_approval=True
        )

        # Rollback should be fast (emergency situation)
        # Check for minimal pre-validation
        pre_validation_tasks = [t for t in decomposition['sub_tasks'] if t['phase'] == 'pre_validation']
        self.assertLessEqual(len(pre_validation_tasks), 3, "Rollback should minimize pre-validation")

    def test_004_simple_monitor_setup(self):
        """Test: Simple monitoring setup."""
        intent = {
            "command_id": "test-004",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Set up monitoring for API",
            "intent_type": "monitor",
            "confidence_score": 0.88,
            "target_service": "api",
            "target_env": None,
            "parameters": {},
            "risk_level": "low"
        }

        self._decompose_and_validate(
            intent,
            expected_min_tasks=5,
            expected_max_tasks=12,
            expected_phases=['deployment', 'validation'],
            should_require_approval=False
        )

    def test_005_simple_cost_query(self):
        """Test: Simple cost query (read-only)."""
        intent = {
            "command_id": "test-005",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "How much are we spending on S3?",
            "intent_type": "cost",
            "confidence_score": 0.98,
            "target_service": "s3",
            "target_env": None,
            "parameters": {},
            "risk_level": "low"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=3,
            expected_max_tasks=8,
            expected_phases=['pre_validation'],
            should_require_approval=False
        )

        # Cost query should have no rollback actions (read-only)
        for task in decomposition['sub_tasks']:
            self.assertIsNone(
                task.get('rollback_action'),
                f"Read-only task {task['task_id']} should not have rollback action"
            )

    # ========================================================================
    # Category 2: Complex Multi-Step Commands (10 tests)
    # ========================================================================

    def test_006_canary_deployment(self):
        """Test: Canary deployment to production."""
        intent = {
            "command_id": "test-006",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy API v2.0 to production with canary rollout",
            "intent_type": "deploy",
            "confidence_score": 0.92,
            "target_service": "api",
            "target_env": "production",
            "parameters": {"version": "v2.0", "strategy": "canary"},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=10,
            expected_max_tasks=18,
            expected_phases=['pre_validation', 'deployment', 'validation', 'monitoring'],
            should_require_approval=True
        )

        # Should have multiple deployment phases (canary progression)
        deployment_tasks = [t for t in decomposition['sub_tasks'] if t['phase'] == 'deployment']
        self.assertGreaterEqual(
            len(deployment_tasks),
            3,
            "Canary should have multiple deployment phases"
        )

    def test_007_blue_green_deployment(self):
        """Test: Blue-green deployment."""
        intent = {
            "command_id": "test-007",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy backend v3.0 with blue-green strategy",
            "intent_type": "deploy",
            "confidence_score": 0.94,
            "target_service": "backend",
            "target_env": "production",
            "parameters": {"version": "v3.0", "strategy": "blue-green"},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=12,
            expected_max_tasks=18,
            expected_phases=['pre_deployment', 'deployment', 'validation'],
            should_require_approval=True
        )

        # Should provision new environment (blue)
        actions = [t['action'] for t in decomposition['sub_tasks']]
        self.assertTrue(
            any('provision' in action.lower() for action in actions),
            "Blue-green should provision new environment"
        )

    def test_008_database_migration(self):
        """Test: Database schema migration."""
        intent = {
            "command_id": "test-008",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Migrate database from SQLite to PostgreSQL",
            "intent_type": "deploy",
            "confidence_score": 0.89,
            "target_service": "database",
            "target_env": "production",
            "parameters": {"migration_type": "sqlite_to_postgresql"},
            "risk_level": "critical"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=12,
            expected_max_tasks=20,
            expected_phases=['pre_deployment', 'deployment', 'validation'],
            should_require_approval=True
        )

        # Must have backup task
        actions = [t['action'] for t in decomposition['sub_tasks']]
        self.assertTrue(
            any('backup' in action.lower() for action in actions),
            "Database migration must include backup"
        )

        # Critical risk level
        overall_risk = decomposition.get('risk_assessment', {}).get('overall_risk')
        self.assertEqual(overall_risk, 'critical', "Database migration should be critical risk")

    def test_009_elk_stack_deployment(self):
        """Test: Deploy complete ELK stack."""
        intent = {
            "command_id": "test-009",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy ELK stack to production with 3-node Elasticsearch",
            "intent_type": "deploy",
            "confidence_score": 0.90,
            "target_service": "elk",
            "target_env": "production",
            "parameters": {"elasticsearch_nodes": 3},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=10,
            expected_max_tasks=18,
            expected_phases=['deployment', 'validation'],
            should_require_approval=True
        )

        # Should deploy multiple components
        targets = set(t['target'] for t in decomposition['sub_tasks'])
        self.assertGreaterEqual(
            len(targets),
            2,
            "ELK stack should deploy multiple components"
        )

    def test_010_multi_region_deployment(self):
        """Test: Multi-region deployment."""
        intent = {
            "command_id": "test-010",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy API to us-east-1 and eu-west-1",
            "intent_type": "deploy",
            "confidence_score": 0.91,
            "target_service": "api",
            "target_env": "production",
            "parameters": {"regions": ["us-east-1", "eu-west-1"]},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=12,
            expected_max_tasks=20,
            expected_phases=['deployment', 'validation']
        )

        # Check for parallelization opportunities (region deployments)
        parallel_tasks = decomposition.get('execution_plan', {}).get('phases', [])
        has_parallel_phase = any(p['execution_mode'] == 'parallel' for p in parallel_tasks)
        self.assertTrue(has_parallel_phase, "Multi-region should have parallel deployment phases")

    def test_011_conditional_staging_then_prod(self):
        """Test: Deploy to staging, if tests pass deploy to prod."""
        intent = {
            "command_id": "test-011",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy v2.5 to staging, if tests pass deploy to production",
            "intent_type": "deploy",
            "confidence_score": 0.87,
            "target_service": "api",
            "target_env": "staging",
            "parameters": {"version": "v2.5", "conditional_prod": True},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=12,
            expected_max_tasks=20,
            expected_phases=['deployment', 'validation', 'conditional_gate']
        )

        # Should have conditional gate
        conditional_tasks = [t for t in decomposition['sub_tasks'] if t['phase'] == 'conditional_gate']
        self.assertGreater(len(conditional_tasks), 0, "Should have conditional gate for staging→prod")

    def test_012_scale_with_load_validation(self):
        """Test: Scale API to 2x traffic, ensure DB can handle load."""
        intent = {
            "command_id": "test-012",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Scale API to handle 2x traffic, ensure database can handle load",
            "intent_type": "scale",
            "confidence_score": 0.86,
            "target_service": "api",
            "target_env": "production",
            "parameters": {"multiplier": 2, "validate_db": True},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=10,
            expected_max_tasks=16,
            expected_phases=['pre_validation', 'scaling', 'validation']
        )

        # Should validate database capacity before scaling
        task_order = [t['task_id'] for t in decomposition['sub_tasks']]
        validation_tasks = [t for t in decomposition['sub_tasks'] if 'database' in t['action'].lower() or 'db' in t['action'].lower()]
        scaling_tasks = [t for t in decomposition['sub_tasks'] if 'scale' in t['action'].lower()]

        if validation_tasks and scaling_tasks:
            validation_idx = task_order.index(validation_tasks[0]['task_id'])
            scaling_idx = task_order.index(scaling_tasks[0]['task_id'])
            self.assertLess(validation_idx, scaling_idx, "DB validation should happen before scaling")

    def test_013_disaster_recovery_setup(self):
        """Test: Set up disaster recovery with backups and multi-region replication."""
        intent = {
            "command_id": "test-013",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Set up disaster recovery: automated backups and multi-region replication",
            "intent_type": "deploy",
            "confidence_score": 0.88,
            "target_service": "infrastructure",
            "target_env": "production",
            "parameters": {"dr_setup": True},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=10,
            expected_max_tasks=18,
            expected_phases=['deployment', 'validation']
        )

    def test_014_security_patch_multi_service(self):
        """Test: Apply security patch to all services."""
        intent = {
            "command_id": "test-014",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Apply critical security patch to all production services",
            "intent_type": "security",
            "confidence_score": 0.93,
            "target_service": "all",
            "target_env": "production",
            "parameters": {"patch_type": "security", "severity": "critical"},
            "risk_level": "critical"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=8,
            expected_max_tasks=16,
            expected_phases=['pre_validation', 'deployment', 'validation']
        )

    def test_015_cost_optimization_workflow(self):
        """Test: Analyze costs and optimize infrastructure."""
        intent = {
            "command_id": "test-015",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Reduce AWS costs by 30%: rightsize instances and delete unused resources",
            "intent_type": "cost",
            "confidence_score": 0.85,
            "target_service": "infrastructure",
            "target_env": "production",
            "parameters": {"target_reduction": 0.30},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=8,
            expected_max_tasks=15,
            expected_phases=['pre_validation', 'deployment']
        )

    # ========================================================================
    # Category 3: Dependency Edge Cases (5 tests)
    # ========================================================================

    def test_016_parallel_independent_tasks(self):
        """Test: Multiple independent services can deploy in parallel."""
        intent = {
            "command_id": "test-016",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy frontend, backend, and monitoring stack",
            "intent_type": "deploy",
            "confidence_score": 0.90,
            "target_service": "multiple",
            "target_env": "staging",
            "parameters": {"services": ["frontend", "backend", "monitoring"]},
            "risk_level": "medium"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=10,
            expected_max_tasks=20,
            expected_phases=['deployment', 'validation']
        )

        # Check for parallel execution
        execution_plan = decomposition.get('execution_plan', {})
        parallel_phases = [p for p in execution_plan.get('phases', []) if p['execution_mode'] == 'parallel']
        self.assertGreater(len(parallel_phases), 0, "Should have parallel execution phases")

    def test_017_sequential_dependency_chain(self):
        """Test: Long sequential dependency chain."""
        intent = {
            "command_id": "test-017",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Provision VPC, deploy database, migrate data, deploy API",
            "intent_type": "deploy",
            "confidence_score": 0.88,
            "target_service": "infrastructure",
            "target_env": "production",
            "parameters": {"full_stack": True},
            "risk_level": "critical"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=12,
            expected_max_tasks=20,
            expected_phases=['pre_deployment', 'deployment', 'validation']
        )

        # Critical path should be long (sequential operations)
        critical_path = decomposition.get('execution_plan', {}).get('critical_path', [])
        self.assertGreater(len(critical_path), 10, "Sequential operations should have long critical path")

    def test_018_diamond_dependency(self):
        """Test: Diamond dependency (A→B/C→D)."""
        intent = {
            "command_id": "test-018",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy API with load balancer and monitoring",
            "intent_type": "deploy",
            "confidence_score": 0.92,
            "target_service": "api",
            "target_env": "production",
            "parameters": {"with_lb": True, "with_monitoring": True},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=10,
            expected_max_tasks=16,
            expected_phases=['deployment', 'validation']
        )

        # Validate dependencies are correct (no cycles)
        validation = self.dependency_resolver.validate()
        self.assertEqual(len(validation.circular_dependencies), 0)

    def test_019_conditional_rollback_on_failure(self):
        """Test: Deploy with automatic rollback if error rate exceeds threshold."""
        intent = {
            "command_id": "test-019",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy v3.0, rollback if error rate exceeds 5%",
            "intent_type": "deploy",
            "confidence_score": 0.89,
            "target_service": "api",
            "target_env": "production",
            "parameters": {"version": "v3.0", "auto_rollback_threshold": 0.05},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=10,
            expected_max_tasks=18,
            expected_phases=['deployment', 'monitoring', 'conditional_gate']
        )

        # Should have monitoring and conditional logic
        conditional_tasks = [t for t in decomposition['sub_tasks'] if t.get('conditional')]
        self.assertGreater(len(conditional_tasks), 0, "Should have conditional rollback logic")

    def test_020_resource_contention_serialization(self):
        """Test: Scale and deploy same resource (must serialize)."""
        intent = {
            "command_id": "test-020",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Scale API to 20 instances and deploy new version",
            "intent_type": "deploy",
            "confidence_score": 0.87,
            "target_service": "api",
            "target_env": "production",
            "parameters": {"scale_to": 20, "version": "v2.1"},
            "risk_level": "high"
        }

        decomposition = self._decompose_and_validate(
            intent,
            expected_min_tasks=10,
            expected_max_tasks=18,
            expected_phases=['scaling', 'deployment', 'validation']
        )

        # Scale should happen before deploy (same resource)
        sub_tasks = decomposition['sub_tasks']
        scale_tasks = [t for t in sub_tasks if 'scale' in t['action'].lower()]
        deploy_tasks = [t for t in sub_tasks if 'deploy' in t['action'].lower()]

        if scale_tasks and deploy_tasks:
            # Deploy should depend on scale
            deploy_deps = deploy_tasks[0].get('dependencies', [])
            self.assertTrue(
                any(scale_task['task_id'] in deploy_deps for scale_task in scale_tasks),
                "Deploy should depend on scale (resource contention)"
            )

    # ========================================================================
    # Category 4: Failure Scenarios (5 tests)
    # ========================================================================

    def test_021_missing_required_parameter(self):
        """Test: Missing version parameter."""
        intent = {
            "command_id": "test-021",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy API to production",
            "intent_type": "deploy",
            "confidence_score": 0.85,
            "target_service": "api",
            "target_env": "production",
            "parameters": {},  # Missing version
            "risk_level": "high"
        }

        # Should still generate reasonable decomposition (use "latest")
        # or return error asking for clarification
        success, decomposition, error = self.engine.decompose(intent)

        if success:
            # If successful, should handle missing version gracefully
            self.assertIn('sub_tasks', decomposition)
        else:
            # If error, should be clear about missing information
            self.assertIn('version', error.lower())

    def test_022_ambiguous_multi_service(self):
        """Test: Ambiguous command with multiple services."""
        intent = {
            "command_id": "test-022",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy the service",
            "intent_type": "deploy",
            "confidence_score": 0.70,
            "target_service": None,
            "target_env": "production",
            "parameters": {},
            "risk_level": "high"
        }

        # Should handle gracefully (clarification or best effort)
        success, decomposition, error = self.engine.decompose(intent)
        self.assertTrue(success or 'clarification' in error.lower())

    def test_023_impossible_time_constraint(self):
        """Test: Impossible scheduled time (in the past)."""
        intent = {
            "command_id": "test-023",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Deploy API yesterday at 2 AM",
            "intent_type": "deploy",
            "confidence_score": 0.80,
            "target_service": "api",
            "target_env": "staging",
            "parameters": {"scheduled_time": "2026-05-04T02:00:00Z"},  # Past
            "risk_level": "medium"
        }

        # Should handle gracefully (ignore past time or error)
        success, decomposition, error = self.engine.decompose(intent)
        self.assertTrue(success)  # Should still work, just ignore invalid time

    def test_024_conflicting_parameters(self):
        """Test: Conflicting parameters (scale up AND scale down)."""
        intent = {
            "command_id": "test-024",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Scale API up to 20 and down to 5",
            "intent_type": "scale",
            "confidence_score": 0.75,
            "target_service": "api",
            "target_env": "production",
            "parameters": {"scale_to": 20, "also_scale_to": 5},  # Conflicting
            "risk_level": "medium"
        }

        # Should pick one or ask for clarification
        success, decomposition, error = self.engine.decompose(intent)
        self.assertTrue(success or 'conflict' in error.lower())

    def test_025_extremely_complex_command(self):
        """Test: Very complex command (near limit)."""
        intent = {
            "command_id": "test-025",
            "timestamp": "2026-05-05T10:00:00Z",
            "original_command": "Set up complete production infrastructure from scratch: VPC, subnets, NAT gateways, load balancers, auto-scaling groups, databases, monitoring, logging, alerting, and backups",
            "intent_type": "deploy",
            "confidence_score": 0.82,
            "target_service": "infrastructure",
            "target_env": "production",
            "parameters": {"full_setup": True},
            "risk_level": "critical"
        }

        success, decomposition, error = self.engine.decompose(intent)

        if success:
            # Should be at or near max tasks (20)
            total_tasks = len(decomposition['sub_tasks'])
            self.assertLessEqual(total_tasks, 20, "Should not exceed 20 tasks")
        else:
            # Should suggest breaking into smaller commands
            self.assertIn('complex', error.lower())


# ============================================================================
# Test Runner
# ============================================================================

def run_decomposition_tests():
    """
    Run all decomposition tests and generate report.
    """
    print("="*70)
    print("PromptOps Decomposition Engine - Test Suite")
    print("="*70)
    print(f"\nTotal tests: 25")
    print(f"Target accuracy: >85% (>21/25 passing)\n")

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDecomposition)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    accuracy = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\nAccuracy: {accuracy:.1f}%")

    if accuracy >= 85:
        print("✓ PASS: Meets >85% accuracy requirement")
    else:
        print("✗ FAIL: Below 85% accuracy requirement")

    # API usage stats
    if hasattr(TestDecomposition, 'engine'):
        stats = TestDecomposition.engine.get_usage_stats()
        print("\n" + "="*70)
        print("API USAGE")
        print("="*70)
        print(f"Total requests: {stats['request_count']}")
        print(f"Total input tokens: {stats['total_input_tokens']:,}")
        print(f"Total output tokens: {stats['total_output_tokens']:,}")
        print(f"Total cost: ${stats['total_cost_usd']:.2f}")

    print("\n" + "="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_decomposition_tests()
    sys.exit(0 if success else 1)
