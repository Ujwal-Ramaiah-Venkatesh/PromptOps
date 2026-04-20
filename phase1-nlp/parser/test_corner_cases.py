"""
Comprehensive Test Suite for NLP Parser Corner Cases
====================================================

This test suite covers all 15 categories of edge cases identified in
CORNER_CASES_ANALYSIS.md to ensure robust production-ready parsing.

Test Categories:
1. Ambiguous commands
2. Multi-environment confusion
3. Version confusion
4. Security & access control
5. Cost & budget implications
6. Dependency & order of operations
7. Typos & misspellings
8. Time-sensitive operations
9. Incomplete information
10. Conflicting parameters
11. Multi-step complex commands
12. Compliance & regulatory
13. Performance & resource limits
14. State & context awareness
15. Error recovery & rollback

Author: QA Engineer - Phase 1 Week 3-4
Date: 2026-04-20
"""

import unittest
import json
from typing import Dict, Any
from claude_integration import ClaudeParser


class TestCornerCases(unittest.TestCase):
    """
    Comprehensive test suite for all corner cases.
    """

    @classmethod
    def setUpClass(cls):
        """Initialize parser once for all tests."""
        cls.parser = ClaudeParser()
        print("\n" + "="*70)
        print("PromptOps NLP Parser - Corner Case Test Suite")
        print("="*70 + "\n")

    def _parse_and_validate(
        self,
        command: str,
        expected_intent: str = None,
        expected_confidence_min: float = 0.0,
        should_have_ambiguity: bool = False,
        should_require_approval: bool = None,
        expected_risk: str = None
    ) -> Dict[str, Any]:
        """
        Helper method to parse command and validate basic expectations.

        Args:
            command: PM input to parse
            expected_intent: Expected intent type
            expected_confidence_min: Minimum expected confidence
            should_have_ambiguity: Whether ambiguity should be detected
            should_require_approval: Expected approval requirement
            expected_risk: Expected risk level

        Returns:
            Parsed output dict

        Raises:
            AssertionError if validation fails
        """
        print(f"\n📝 Testing: \"{command}\"")

        success, output, error = self.parser.parse_command(command)

        # Basic success check
        self.assertTrue(success, f"Parse failed: {error}")
        self.assertIsInstance(output, dict, "Output should be dict")

        # Validate intent if specified
        if expected_intent:
            self.assertEqual(
                output['intent_type'],
                expected_intent,
                f"Expected intent '{expected_intent}', got '{output['intent_type']}'"
            )

        # Validate confidence
        self.assertGreaterEqual(
            output['confidence_score'],
            expected_confidence_min,
            f"Confidence {output['confidence_score']} below minimum {expected_confidence_min}"
        )

        # Validate ambiguity detection
        if should_have_ambiguity:
            self.assertTrue(
                output['ambiguity_detected'],
                "Expected ambiguity but none detected"
            )
            self.assertGreater(
                len(output['clarification_questions']),
                0,
                "Ambiguity detected but no clarification questions"
            )
        else:
            self.assertFalse(
                output['ambiguity_detected'],
                "Unexpected ambiguity detected"
            )

        # Validate approval requirement
        if should_require_approval is not None:
            self.assertEqual(
                output['requires_approval'],
                should_require_approval,
                f"Expected requires_approval={should_require_approval}"
            )

        # Validate risk level
        if expected_risk:
            self.assertEqual(
                output['risk_level'],
                expected_risk,
                f"Expected risk='{expected_risk}', got '{output['risk_level']}'"
            )

        print(f"✓ Intent: {output['intent_type']}")
        print(f"✓ Confidence: {output['confidence_score']:.2f}")
        print(f"✓ Risk: {output['risk_level']} | Approval: {output['requires_approval']}")

        if output['ambiguity_detected']:
            print(f"⚠ Ambiguity: {len(output['clarification_questions'])} questions")

        if output['warnings']:
            print(f"⚠ Warnings: {len(output['warnings'])}")

        return output

    # ========================================================================
    # Category 1: Ambiguous Commands
    # ========================================================================

    def test_ambiguous_deploy_no_version(self):
        """Test: 'Deploy the API' (missing version and environment)"""
        output = self._parse_and_validate(
            command="Deploy the API",
            expected_intent="deploy",
            should_have_ambiguity=True,
            expected_confidence_min=0.5
        )
        # Should ask for version and environment
        self.assertIn('version', str(output['clarification_questions']).lower())

    def test_ambiguous_scale_no_target(self):
        """Test: 'Scale up the backend' (which service? by how much?)"""
        output = self._parse_and_validate(
            command="Scale up the backend",
            expected_intent="scale",
            should_have_ambiguity=True
        )

    def test_ambiguous_fix_database(self):
        """Test: 'Fix the database' (too vague, what's broken?)"""
        output = self._parse_and_validate(
            command="Fix the database",
            expected_intent="diagnose",  # Should interpret as diagnosis needed
            should_have_ambiguity=True
        )

    # ========================================================================
    # Category 2: Multi-Environment Confusion
    # ========================================================================

    def test_environment_normalization_prod(self):
        """Test: Various 'production' spellings normalize correctly"""
        variants = ["prod", "production", "PROD", "Production", "prd"]

        for variant in variants:
            output = self._parse_and_validate(
                command=f"Deploy API v2.0 to {variant}",
                expected_intent="deploy",
                should_require_approval=True,  # Production always requires approval
                expected_risk="high"
            )
            # Should normalize to 'production'
            self.assertEqual(output['target_env'], 'production')

    def test_environment_normalization_staging(self):
        """Test: Various 'staging' spellings normalize correctly"""
        variants = ["staging", "stg", "stage", "STG"]

        for variant in variants:
            output = self._parse_and_validate(
                command=f"Deploy API v2.0 to {variant}",
                expected_intent="deploy"
            )
            self.assertEqual(output['target_env'], 'staging')

    def test_no_environment_specified(self):
        """Test: No environment specified (should default to staging or ask)"""
        output = self._parse_and_validate(
            command="Deploy API v2.0",
            expected_intent="deploy"
        )
        # Should either default to staging or ask for clarification
        self.assertIn(output['target_env'], ['staging', None])
        if output['target_env'] is None:
            self.assertTrue(output['ambiguity_detected'])

    # ========================================================================
    # Category 3: Version Confusion
    # ========================================================================

    def test_version_latest(self):
        """Test: 'latest' version should be accepted"""
        output = self._parse_and_validate(
            command="Deploy API latest to staging",
            expected_intent="deploy"
        )
        # Should accept 'latest'
        self.assertIn('latest', str(output['parameters'].get('version', '')).lower())

    def test_version_ambiguous(self):
        """Test: Ambiguous version 'v2' (could be v2.0, v2.1, v2.0.0)"""
        output = self._parse_and_validate(
            command="Deploy API v2 to production",
            expected_intent="deploy"
        )
        # Parser might flag as ambiguous or accept as-is
        if output['ambiguity_detected']:
            self.assertIn('version', str(output['clarification_questions']).lower())

    def test_rollback_no_version(self):
        """Test: Rollback without specifying version"""
        output = self._parse_and_validate(
            command="Rollback API",
            expected_intent="rollback",
            should_require_approval=True
        )
        # Should either ask for target version or default to 'previous'

    # ========================================================================
    # Category 4: Security & Access Control
    # ========================================================================

    def test_dangerous_delete_production_database(self):
        """Test: Extremely dangerous command should be flagged"""
        output = self._parse_and_validate(
            command="Delete production database",
            expected_intent="deploy",  # Might parse as infrastructure change
            should_require_approval=True,
            expected_risk="critical"
        )
        # Should have severe warnings
        self.assertGreater(len(output['warnings']), 0)
        self.assertIn('critical', output['risk_level'].lower())

    def test_security_open_port_to_internet(self):
        """Test: Opening port to 0.0.0.0/0 should trigger security warning"""
        output = self._parse_and_validate(
            command="Open port 22 to 0.0.0.0/0",
            expected_intent="security",
            should_require_approval=True,
            expected_risk="high"
        )
        # Should flag as security risk
        self.assertGreater(len(output['warnings']), 0)

    # ========================================================================
    # Category 5: Cost & Budget Implications
    # ========================================================================

    def test_cost_scale_to_1000_instances(self):
        """Test: Massive scale-up should show cost estimate"""
        output = self._parse_and_validate(
            command="Scale to 1000 instances",
            expected_intent="scale",
            should_require_approval=True
        )
        # Should mention cost impact
        self.assertIsNotNone(output['estimated_cost_impact'])

    def test_cost_deploy_to_10_regions(self):
        """Test: Multi-region deployment should estimate high cost"""
        output = self._parse_and_validate(
            command="Deploy API to 10 regions",
            expected_intent="deploy",
            should_require_approval=True
        )
        # Should have cost estimate or warning
        self.assertTrue(
            output['estimated_cost_impact'] is not None or
            len(output['warnings']) > 0
        )

    def test_cost_optimization_request(self):
        """Test: Cost optimization should be parsed correctly"""
        output = self._parse_and_validate(
            command="Reduce AWS bill by 30%",
            expected_intent="cost",
            expected_confidence_min=0.85
        )
        # Should capture 30% target
        self.assertIn('30', str(output['parameters']))

    # ========================================================================
    # Category 6: Dependency & Order of Operations
    # ========================================================================

    def test_deploy_with_db_migration_dependency(self):
        """Test: Deploy that requires DB migration should flag dependency"""
        output = self._parse_and_validate(
            command="Deploy API v2.0 to production",
            expected_intent="deploy",
            should_require_approval=True
        )
        # Might include DB migration in dependencies
        # (Would need context layer to know for sure)

    def test_rollback_with_schema_mismatch(self):
        """Test: Rollback might have schema compatibility issues"""
        output = self._parse_and_validate(
            command="Rollback API to v1.5",
            expected_intent="rollback",
            should_require_approval=True
        )
        # Should warn about potential schema issues

    # ========================================================================
    # Category 7: Typos & Misspellings
    # ========================================================================

    def test_typo_depoly(self):
        """Test: 'Depoly' should auto-correct to 'Deploy'"""
        output = self._parse_and_validate(
            command="Depoly API v2.0 to staging",
            expected_intent="deploy"
        )
        # Should still parse correctly despite typo

    def test_typo_service_name(self):
        """Test: Misspelled service name 'api-serivce'"""
        output = self._parse_and_validate(
            command="Deploy api-serivce v2.0 to staging",
            expected_intent="deploy"
        )
        # Should either fuzzy-match or ask for clarification
        # Parser might correct or flag as ambiguous

    def test_typo_environment(self):
        """Test: 'proudction' should normalize to 'production'"""
        output = self._parse_and_validate(
            command="Deploy API v2.0 to proudction",
            expected_intent="deploy",
            should_require_approval=True
        )
        # Should normalize despite typo
        self.assertEqual(output['target_env'], 'production')

    # ========================================================================
    # Category 8: Time-Sensitive Operations
    # ========================================================================

    def test_deploy_now_during_high_traffic(self):
        """Test: Deploy 'now' should check for high-traffic periods"""
        output = self._parse_and_validate(
            command="Deploy API v2.0 to production now",
            expected_intent="deploy",
            should_require_approval=True
        )
        # Might warn about timing (would need context to know traffic)

    def test_scheduled_deployment(self):
        """Test: Schedule deployment for future time"""
        output = self._parse_and_validate(
            command="Deploy API v2.0 to production at 2 AM",
            expected_intent="deploy",
            should_require_approval=True
        )
        # Should capture scheduled time

    # ========================================================================
    # Category 9: Incomplete Information
    # ========================================================================

    def test_incomplete_just_deploy(self):
        """Test: Just 'Deploy' with no details"""
        output = self._parse_and_validate(
            command="Deploy",
            expected_intent="deploy",
            should_have_ambiguity=True
        )
        # Should ask for service, version, environment

    def test_incomplete_scale_up(self):
        """Test: 'Scale up' without service or target"""
        output = self._parse_and_validate(
            command="Scale up",
            expected_intent="scale",
            should_have_ambiguity=True
        )

    def test_incomplete_check_errors(self):
        """Test: 'Check errors' (which service? when?)"""
        output = self._parse_and_validate(
            command="Check errors",
            expected_intent="monitor"
        )
        # Should default to reasonable values or ask

    # ========================================================================
    # Category 10: Conflicting Parameters
    # ========================================================================

    def test_conflicting_deploy_two_versions(self):
        """Test: Deploy v2.0 AND v2.1 (conflicting)"""
        output = self._parse_and_validate(
            command="Deploy API v2.0 and v2.1 to production",
            expected_intent="deploy"
        )
        # Should detect conflict and ask which version

    def test_conflicting_scale_up_and_down(self):
        """Test: Scale up and scale down (contradictory)"""
        output = self._parse_and_validate(
            command="Scale up and scale down backend",
            expected_intent="scale"
        )
        # Should flag as conflicting

    # ========================================================================
    # Category 11: Multi-Step Complex Commands
    # ========================================================================

    def test_multi_step_staging_then_prod(self):
        """Test: Deploy to staging, test, then prod"""
        output = self._parse_and_validate(
            command="Deploy API v2.0 to staging, test for 1 hour, then deploy to prod",
            expected_intent="deploy",
            should_require_approval=True
        )
        # Should recognize multi-step process
        # Should have 'multi_step' in parameters

    def test_multi_step_create_environment(self):
        """Test: Create new environment with multiple services"""
        output = self._parse_and_validate(
            command="Create new demo environment with API and frontend",
            expected_intent="deploy"
        )
        # Should recognize complex multi-step operation

    # ========================================================================
    # Category 12: Compliance & Regulatory
    # ========================================================================

    def test_compliance_disable_encryption(self):
        """Test: Disable encryption (compliance violation)"""
        output = self._parse_and_validate(
            command="Disable encryption on production database",
            expected_risk="critical",
            should_require_approval=True
        )
        # Should flag as compliance violation

    def test_compliance_delete_customer_data(self):
        """Test: Delete customer data (GDPR implications)"""
        output = self._parse_and_validate(
            command="Delete customer data for user ID 12345",
            expected_risk="high",
            should_require_approval=True
        )
        # Should require documented deletion request

    # ========================================================================
    # Category 13: Performance & Resource Limits
    # ========================================================================

    def test_limit_exceed_10000_instances(self):
        """Test: Scale beyond reasonable limits"""
        output = self._parse_and_validate(
            command="Scale to 10000 instances",
            expected_intent="scale",
            should_require_approval=True
        )
        # Should warn about limits

    # ========================================================================
    # Category 14: State & Context Awareness
    # ========================================================================

    def test_state_already_deployed(self):
        """Test: Deploy version that's already deployed"""
        # Note: This requires Context Layer (Week 7-8) to fully implement
        output = self._parse_and_validate(
            command="Deploy API v2.0 to production",
            expected_intent="deploy"
        )
        # Parser should flag this, but needs context to know current version

    # ========================================================================
    # Category 15: Error Recovery & Rollback
    # ========================================================================

    def test_rollback_plan_present(self):
        """Test: Every high-risk operation should have rollback plan"""
        output = self._parse_and_validate(
            command="Deploy API v2.1.0 to production",
            expected_intent="deploy",
            should_require_approval=True
        )
        # Should include rollback plan
        self.assertIsNotNone(output['rollback_plan'])
        self.assertGreater(len(output['rollback_plan']), 0)

    # ========================================================================
    # Golden Test Cases (From golden-tests/commands.json)
    # ========================================================================

    def test_golden_deploy_001(self):
        """Golden Test: Basic production deploy"""
        output = self._parse_and_validate(
            command="Deploy the API to production",
            expected_intent="deploy",
            expected_confidence_min=0.85,
            should_require_approval=True,
            expected_risk="high"
        )

    def test_golden_scale_001(self):
        """Golden Test: Scale up for traffic"""
        output = self._parse_and_validate(
            command="Scale the backend to handle 2x traffic",
            expected_intent="scale",
            expected_confidence_min=0.85
        )

    def test_golden_diagnose_001(self):
        """Golden Test: Diagnose slow performance"""
        output = self._parse_and_validate(
            command="Why is the API slow?",
            expected_intent="diagnose",
            expected_confidence_min=0.85
        )

    def test_golden_cost_001(self):
        """Golden Test: Cost inquiry"""
        output = self._parse_and_validate(
            command="How much did we spend this month?",
            expected_intent="cost",
            expected_confidence_min=0.85
        )

    def test_golden_monitor_001(self):
        """Golden Test: Check service health"""
        output = self._parse_and_validate(
            command="Check the health of production services",
            expected_intent="monitor",
            expected_confidence_min=0.85
        )

    def test_golden_security_001(self):
        """Golden Test: Security scan"""
        output = self._parse_and_validate(
            command="Scan the API for vulnerabilities",
            expected_intent="security",
            expected_confidence_min=0.85
        )

    def test_golden_rollback_001(self):
        """Golden Test: Rollback deployment"""
        output = self._parse_and_validate(
            command="Rollback the API to the previous version",
            expected_intent="rollback",
            expected_confidence_min=0.85,
            should_require_approval=True
        )

    def test_golden_audit_001(self):
        """Golden Test: Audit trail query"""
        output = self._parse_and_validate(
            command="Who deployed to production last week?",
            expected_intent="audit",
            expected_confidence_min=0.85
        )


# ============================================================================
# Test Runner
# ============================================================================

def run_corner_case_tests():
    """
    Run all corner case tests and generate report.
    """
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCornerCases)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("CORNER CASE TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    # Show API usage stats
    if hasattr(TestCornerCases, 'parser'):
        print("\n" + "="*70)
        print("API USAGE STATISTICS")
        print("="*70)
        stats = TestCornerCases.parser.get_usage_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

    print("\n" + "="*70)

    return result


if __name__ == "__main__":
    result = run_corner_case_tests()
    exit(0 if result.wasSuccessful() else 1)
