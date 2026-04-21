"""
Decomposition Integration Test
===============================

End-to-end integration test for the complete decomposition pipeline:
Week 3-4 Parser → Week 5-6 Decomposition Engine → Dependency Resolution

Validates the full workflow from PM command to executable sub-tasks.

Author: PromptOps Team - Week 5-6
Date: 2026-04-21
"""

import unittest
import os
import sys
import json
import logging

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase1-nlp'))

from parser.claude_integration import ClaudeParser
from decomposition.decomposition_engine import DecompositionEngine
from decomposition.dependency_resolver import DependencyResolver

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Integration Test
# ============================================================================

class TestDecompositionIntegration(unittest.TestCase):
    """
    End-to-end integration tests for parser → decomposition pipeline.
    """

    @classmethod
    def setUpClass(cls):
        """Initialize components once for all tests."""
        api_key = os.environ.get('ANTHROPIC_API_KEY')

        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Cannot run integration tests.\n"
                "Set with: $env:ANTHROPIC_API_KEY=\"sk-ant-...\""
            )

        # Initialize Week 3-4 Parser
        cls.parser = ClaudeParser(api_key)

        # Initialize Week 5-6 Decomposition Engine
        cls.decomposition_engine = DecompositionEngine(api_key)

        # Initialize Dependency Resolver
        cls.dependency_resolver = DependencyResolver()

        logger.info("Integration test suite initialized")

    def test_001_full_pipeline_simple_deploy(self):
        """Test: Full pipeline for simple deploy command."""
        pm_command = "Deploy frontend v2.0 to staging"

        print(f"\n{'='*70}")
        print(f"Integration Test: {pm_command}")
        print(f"{'='*70}")

        # Step 1: Parse PM command (Week 3-4)
        print("\n[1/3] Parsing PM command...")
        parse_success, parsed_intent, parse_error = self.parser.parse_command(pm_command)

        self.assertTrue(parse_success, f"Parser failed: {parse_error}")
        self.assertEqual(parsed_intent['intent_type'], 'deploy')
        self.assertEqual(parsed_intent['target_service'], 'frontend')
        self.assertEqual(parsed_intent['target_env'], 'staging')

        print(f"✓ Parsed: {parsed_intent['intent_type']} to {parsed_intent['target_env']}")

        # Step 2: Decompose into sub-tasks (Week 5-6)
        print("\n[2/3] Decomposing into sub-tasks...")
        decomp_success, decomposition, decomp_error = self.decomposition_engine.decompose(parsed_intent)

        self.assertTrue(decomp_success, f"Decomposition failed: {decomp_error}")
        self.assertIn('sub_tasks', decomposition)
        self.assertGreater(len(decomposition['sub_tasks']), 0)

        print(f"✓ Decomposed: {len(decomposition['sub_tasks'])} sub-tasks")

        # Step 3: Validate dependencies
        print("\n[3/3] Validating dependencies...")
        self.dependency_resolver.build_graph(decomposition['sub_tasks'])
        validation = self.dependency_resolver.validate()

        self.assertTrue(validation.is_valid, f"Dependency validation failed: {validation.errors}")
        self.assertEqual(len(validation.circular_dependencies), 0, "Circular dependencies detected")

        print(f"✓ Dependencies validated: {len(decomposition['sub_tasks'])} tasks, 0 cycles")

        # Verify execution plan
        self.assertIn('execution_plan', decomposition)
        self.assertIn('phases', decomposition['execution_plan'])
        self.assertGreater(len(decomposition['execution_plan']['phases']), 0)

        print(f"\n✓ Integration test passed!")
        print(f"  Phases: {len(decomposition['execution_plan']['phases'])}")
        print(f"  Critical path: {len(decomposition['execution_plan']['critical_path'])} tasks")

    def test_002_full_pipeline_production_deploy(self):
        """Test: Full pipeline for production deployment with approval."""
        pm_command = "Deploy API v3.5 to production with canary rollout"

        print(f"\n{'='*70}")
        print(f"Integration Test: {pm_command}")
        print(f"{'='*70}")

        # Parse
        print("\n[1/3] Parsing...")
        parse_success, parsed_intent, _ = self.parser.parse_command(pm_command)
        self.assertTrue(parse_success)

        # Should require approval (production + high risk)
        self.assertTrue(parsed_intent.get('requires_approval', False))

        print(f"✓ Parsed with approval requirement")

        # Decompose
        print("\n[2/3] Decomposing...")
        decomp_success, decomposition, _ = self.decomposition_engine.decompose(parsed_intent)
        self.assertTrue(decomp_success)

        # Should have approval gate task
        approval_tasks = [t for t in decomposition['sub_tasks'] if t.get('approval_required')]
        self.assertGreater(len(approval_tasks), 0, "Production deployment should have approval gate")

        print(f"✓ Decomposed with {len(approval_tasks)} approval gates")

        # Validate
        print("\n[3/3] Validating...")
        self.dependency_resolver.build_graph(decomposition['sub_tasks'])
        validation = self.dependency_resolver.validate()
        self.assertTrue(validation.is_valid)

        print(f"✓ Validation passed")

    def test_003_full_pipeline_scale_operation(self):
        """Test: Full pipeline for scaling operation."""
        pm_command = "Scale backend to 20 instances"

        print(f"\n{'='*70}")
        print(f"Integration Test: {pm_command}")
        print(f"{'='*70}")

        # Parse
        parse_success, parsed_intent, _ = self.parser.parse_command(pm_command)
        self.assertTrue(parse_success)
        self.assertEqual(parsed_intent['intent_type'], 'scale')

        # Decompose
        decomp_success, decomposition, _ = self.decomposition_engine.decompose(parsed_intent)
        self.assertTrue(decomp_success)

        # Should have scaling-related tasks
        actions = [t['action'] for t in decomposition['sub_tasks']]
        has_scale_action = any('scale' in action.lower() for action in actions)
        self.assertTrue(has_scale_action, "Should have scaling action")

        # Validate
        self.dependency_resolver.build_graph(decomposition['sub_tasks'])
        validation = self.dependency_resolver.validate()
        self.assertTrue(validation.is_valid)

        print(f"✓ Full pipeline passed: {len(decomposition['sub_tasks'])} tasks")

    def test_004_full_pipeline_rollback(self):
        """Test: Full pipeline for rollback command."""
        pm_command = "Rollback API to previous version"

        print(f"\n{'='*70}")
        print(f"Integration Test: {pm_command}")
        print(f"{'='*70}")

        # Parse
        parse_success, parsed_intent, _ = self.parser.parse_command(pm_command)
        self.assertTrue(parse_success)
        self.assertEqual(parsed_intent['intent_type'], 'rollback')

        # Decompose
        decomp_success, decomposition, _ = self.decomposition_engine.decompose(parsed_intent)
        self.assertTrue(decomp_success)

        # Should have rollback plan
        self.assertIn('rollback_plan', decomposition)

        # Validate
        self.dependency_resolver.build_graph(decomposition['sub_tasks'])
        validation = self.dependency_resolver.validate()
        self.assertTrue(validation.is_valid)

        print(f"✓ Rollback pipeline passed")

    def test_005_full_pipeline_complex_multi_step(self):
        """Test: Full pipeline for complex multi-step command."""
        pm_command = "Deploy v2.0 to staging, run tests, then deploy to production"

        print(f"\n{'='*70}")
        print(f"Integration Test: {pm_command}")
        print(f"{'='*70}")

        # Parse
        parse_success, parsed_intent, _ = self.parser.parse_command(pm_command)
        self.assertTrue(parse_success)

        # Decompose
        decomp_success, decomposition, _ = self.decomposition_engine.decompose(parsed_intent)
        self.assertTrue(decomp_success)

        # Should have multiple phases (staging → tests → production)
        phases = decomposition.get('execution_plan', {}).get('phases', [])
        self.assertGreaterEqual(len(phases), 3, "Should have at least 3 phases")

        # Should have conditional gate
        conditional_tasks = [t for t in decomposition['sub_tasks']
                           if t.get('phase') == 'conditional_gate' or t.get('conditional')]
        self.assertGreater(len(conditional_tasks), 0, "Should have conditional logic")

        # Validate
        self.dependency_resolver.build_graph(decomposition['sub_tasks'])
        validation = self.dependency_resolver.validate()
        self.assertTrue(validation.is_valid)

        print(f"✓ Complex pipeline passed: {len(phases)} phases, {len(conditional_tasks)} conditional gates")

    def test_006_parallelization_detection(self):
        """Test: Verify parallel execution is detected."""
        pm_command = "Deploy monitoring stack: Prometheus, Grafana, and AlertManager"

        print(f"\n{'='*70}")
        print(f"Integration Test: Parallelization Detection")
        print(f"{'='*70}")

        # Parse
        parse_success, parsed_intent, _ = self.parser.parse_command(pm_command)
        self.assertTrue(parse_success)

        # Decompose
        decomp_success, decomposition, _ = self.decomposition_engine.decompose(parsed_intent)
        self.assertTrue(decomp_success)

        # Check for parallel phases
        phases = decomposition.get('execution_plan', {}).get('phases', [])
        parallel_phases = [p for p in phases if p['execution_mode'] == 'parallel']

        self.assertGreater(len(parallel_phases), 0, "Should have parallel execution phases")

        # Check parallelizable tasks
        parallel_tasks = [t for t in decomposition['sub_tasks'] if t['can_run_parallel']]
        self.assertGreater(len(parallel_tasks), 1, "Should have multiple parallelizable tasks")

        print(f"✓ Parallelization detected: {len(parallel_phases)} parallel phases, {len(parallel_tasks)} parallel tasks")

    def test_007_cost_tracking(self):
        """Test: Verify API cost tracking works end-to-end."""
        pm_command = "Show me current AWS spending"

        print(f"\n{'='*70}")
        print(f"Integration Test: Cost Tracking")
        print(f"{'='*70}")

        # Track costs before
        parser_stats_before = self.parser.get_usage_stats()
        decomp_stats_before = self.decomposition_engine.get_usage_stats()

        # Run pipeline
        parse_success, parsed_intent, _ = self.parser.parse_command(pm_command)
        self.assertTrue(parse_success)

        decomp_success, decomposition, _ = self.decomposition_engine.decompose(parsed_intent)
        self.assertTrue(decomp_success)

        # Track costs after
        parser_stats_after = self.parser.get_usage_stats()
        decomp_stats_after = self.decomposition_engine.get_usage_stats()

        # Verify costs increased
        self.assertGreater(
            parser_stats_after['total_cost_usd'],
            parser_stats_before['total_cost_usd'],
            "Parser cost should increase"
        )

        self.assertGreater(
            decomp_stats_after['total_cost_usd'],
            decomp_stats_before['total_cost_usd'],
            "Decomposition cost should increase"
        )

        total_cost = (parser_stats_after['total_cost_usd'] +
                     decomp_stats_after['total_cost_usd'])

        print(f"✓ Cost tracking working")
        print(f"  Parser: ${parser_stats_after['total_cost_usd']:.4f}")
        print(f"  Decomposition: ${decomp_stats_after['total_cost_usd']:.4f}")
        print(f"  Total: ${total_cost:.4f}")


# ============================================================================
# LangGraph Workflow Test
# ============================================================================

class TestLangGraphIntegration(unittest.TestCase):
    """
    Test LangGraph workflow integration.
    """

    def test_langgraph_workflow(self):
        """Test: Complete LangGraph workflow."""
        print(f"\n{'='*70}")
        print(f"LangGraph Workflow Test")
        print(f"{'='*70}")

        # Simulate LangGraph state
        state = {
            'original_input': 'Deploy frontend v1.5 to staging',
            'errors': [],
            'workflow_status': 'initialized'
        }

        # Import LangGraph nodes
        from parser.claude_integration import llm_parse_node
        from decomposition.decomposition_engine import decomposition_node

        # Step 1: Parse node
        print("\n[1/2] Running parse node...")
        state = llm_parse_node(state)

        self.assertEqual(state['workflow_status'], 'parsed')
        self.assertIn('parsed_intent', state)
        self.assertEqual(len(state['errors']), 0)

        print(f"✓ Parse node complete")

        # Step 2: Decomposition node
        print("\n[2/2] Running decomposition node...")
        state = decomposition_node(state)

        self.assertEqual(state['workflow_status'], 'decomposed')
        self.assertIn('decomposition', state)
        self.assertEqual(len(state['errors']), 0)

        print(f"✓ Decomposition node complete")
        print(f"\n✓ LangGraph workflow test passed!")


# ============================================================================
# Test Runner
# ============================================================================

def run_integration_tests():
    """
    Run all integration tests.
    """
    print("="*70)
    print("PromptOps Decomposition - Integration Test Suite")
    print("="*70)
    print(f"\nTesting complete pipeline:")
    print(f"  Week 3-4 Parser → Week 5-6 Decomposition → Dependency Resolution\n")

    # Run integration tests
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TestDecompositionIntegration)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestLangGraphIntegration)

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
        print("Week 3-4 Parser ↔ Week 5-6 Decomposition integration verified!")
    else:
        print("\n✗ SOME INTEGRATION TESTS FAILED")

    print("\n" + "="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
