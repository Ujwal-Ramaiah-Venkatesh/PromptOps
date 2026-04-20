"""
Golden Test Suite Integration for PromptOps
============================================

Loads all 50 official golden tests from tests/golden-tests/commands.json
and validates parser accuracy against expected outputs.

This is the CRITICAL EXIT CRITERIA for Week 3-4:
- Target: >90% accuracy (>45/50 tests passing)
- Validates: intent_type, target_service, target_env, risk_level, ambiguity_detected, requires_approval

Author: PromptOps Team - Week 3-4
Date: 2026-04-20
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_integration import ClaudeParser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

GOLDEN_TESTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..",
    "tests", "golden-tests", "commands.json"
)

# Accuracy threshold for Week 3-4 exit criteria
ACCURACY_THRESHOLD = 0.90  # 90%


# ============================================================================
# Golden Test Validator
# ============================================================================

class GoldenTestValidator:
    """
    Validates parser output against golden test expectations.

    Checks key fields that determine parser quality:
    - intent_type (most critical)
    - target_service
    - target_env
    - risk_level
    - requires_approval
    - ambiguity_detected
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.

        Args:
            strict_mode: If True, all fields must match exactly.
                        If False, allows some flexibility (e.g., null vs specific value).
        """
        self.strict_mode = strict_mode

    def validate_test(self, test_case: Dict[str, Any], parser_output: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate parser output against expected output.

        Args:
            test_case: Golden test case with expected_output
            parser_output: Actual parser output

        Returns:
            (is_passing, list_of_mismatches)
        """
        expected = test_case['expected_output']
        mismatches = []

        # 1. Intent Type (CRITICAL - must match unless ambiguous)
        if expected.get('intent_type') is not None:
            if parser_output.get('intent_type') != expected['intent_type']:
                mismatches.append(f"intent_type: expected '{expected['intent_type']}', got '{parser_output.get('intent_type')}'")
        else:
            # Ambiguous test - intent_type should be null or ambiguity_detected=True
            if parser_output.get('intent_type') is not None and not parser_output.get('ambiguity_detected', False):
                mismatches.append(f"intent_type: expected null (ambiguous), got '{parser_output.get('intent_type')}'")

        # 2. Target Service (important but allows flexibility)
        if not self._compare_nullable_field(expected, parser_output, 'target_service'):
            mismatches.append(f"target_service: expected '{expected.get('target_service')}', got '{parser_output.get('target_service')}'")

        # 3. Target Environment (important)
        if not self._compare_nullable_field(expected, parser_output, 'target_env'):
            mismatches.append(f"target_env: expected '{expected.get('target_env')}', got '{parser_output.get('target_env')}'")

        # 4. Risk Level (critical for safety)
        expected_risk = expected.get('risk_level')
        actual_risk = parser_output.get('risk_level')

        # Allow "extreme" to match "critical" (both mean highest risk)
        if expected_risk == 'extreme':
            if actual_risk not in ['extreme', 'critical']:
                mismatches.append(f"risk_level: expected '{expected_risk}', got '{actual_risk}'")
        elif expected_risk != actual_risk:
            mismatches.append(f"risk_level: expected '{expected_risk}', got '{actual_risk}'")

        # 5. Requires Approval (critical for safety)
        if expected.get('requires_approval') != parser_output.get('requires_approval'):
            mismatches.append(f"requires_approval: expected {expected.get('requires_approval')}, got {parser_output.get('requires_approval')}")

        # 6. Ambiguity Detection (important for UX)
        expected_ambiguity = expected.get('ambiguity_detected', False)
        actual_ambiguity = parser_output.get('ambiguity_detected', False)

        if expected_ambiguity != actual_ambiguity:
            mismatches.append(f"ambiguity_detected: expected {expected_ambiguity}, got {actual_ambiguity}")

        # 7. Confidence Score (should be reasonable)
        expected_confidence = expected.get('confidence_score', 0.85)
        actual_confidence = parser_output.get('confidence_score', 0.0)

        # Allow ±0.15 variance in confidence
        if abs(expected_confidence - actual_confidence) > 0.15:
            mismatches.append(f"confidence_score: expected ~{expected_confidence}, got {actual_confidence} (variance too large)")

        # Test passes if no mismatches
        return (len(mismatches) == 0, mismatches)

    def _compare_nullable_field(self, expected: Dict, actual: Dict, field: str) -> bool:
        """
        Compare a field that can be null in either expected or actual.

        Allows flexibility: if expected is null, actual can be anything.
        If expected is not null, actual should match.
        """
        expected_val = expected.get(field)
        actual_val = actual.get(field)

        # If expected is null, we don't enforce (allows parser to be more specific)
        if expected_val is None:
            return True

        # If expected is not null, it should match
        return expected_val == actual_val


# ============================================================================
# Golden Test Runner
# ============================================================================

class GoldenTestRunner:
    """
    Runs all 50 golden tests and calculates accuracy.
    """

    def __init__(self):
        self.parser = ClaudeParser()
        self.validator = GoldenTestValidator(strict_mode=False)

        # Results
        self.results: List[Dict[str, Any]] = []
        self.passed_count = 0
        self.failed_count = 0
        self.error_count = 0

    def load_golden_tests(self) -> List[Dict[str, Any]]:
        """
        Load golden tests from JSON file.

        Returns:
            List of test cases
        """
        if not os.path.exists(GOLDEN_TESTS_PATH):
            raise FileNotFoundError(f"Golden tests file not found: {GOLDEN_TESTS_PATH}")

        with open(GOLDEN_TESTS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data['tests']

    def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single golden test.

        Args:
            test_case: Test case from golden tests

        Returns:
            Result dict with status, mismatches, etc.
        """
        test_id = test_case['test_id']
        pm_input = test_case['pm_input']

        logger.info(f"\n{'='*70}")
        logger.info(f"Test: {test_id}")
        logger.info(f"Category: {test_case['category']} | Difficulty: {test_case['difficulty']}")
        logger.info(f"Input: \"{pm_input}\"")

        result = {
            'test_id': test_id,
            'category': test_case['category'],
            'difficulty': test_case['difficulty'],
            'pm_input': pm_input,
            'status': 'unknown',
            'mismatches': [],
            'parser_output': None,
            'error': None
        }

        try:
            # Parse command
            success, parser_output, error = self.parser.parse_command(pm_input)

            if not success:
                # Parser error
                result['status'] = 'error'
                result['error'] = error
                logger.error(f"✗ ERROR: {error}")
                self.error_count += 1
                return result

            result['parser_output'] = parser_output

            # Validate against expected output
            is_passing, mismatches = self.validator.validate_test(test_case, parser_output)

            result['mismatches'] = mismatches

            if is_passing:
                result['status'] = 'pass'
                logger.info(f"✓ PASS")
                logger.info(f"  Intent: {parser_output['intent_type']}")
                logger.info(f"  Confidence: {parser_output['confidence_score']:.2f}")
                logger.info(f"  Risk: {parser_output['risk_level']}")
                self.passed_count += 1
            else:
                result['status'] = 'fail'
                logger.warning(f"✗ FAIL")
                logger.warning(f"  Mismatches:")
                for mismatch in mismatches:
                    logger.warning(f"    - {mismatch}")
                self.failed_count += 1

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"✗ ERROR: Unexpected exception: {e}")
            self.error_count += 1

        return result

    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all 50 golden tests.

        Returns:
            Summary dict with overall results
        """
        logger.info("\n" + "="*70)
        logger.info("PromptOps Golden Test Suite - Week 3-4 Exit Criteria")
        logger.info("="*70)
        logger.info(f"Loading tests from: {GOLDEN_TESTS_PATH}")

        # Load tests
        test_cases = self.load_golden_tests()
        total_tests = len(test_cases)

        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Accuracy threshold: {ACCURACY_THRESHOLD*100}% (>{int(ACCURACY_THRESHOLD*total_tests)}/{total_tests} passing)")
        logger.info("="*70)

        # Run each test
        for test_case in test_cases:
            result = self.run_single_test(test_case)
            self.results.append(result)

        # Calculate metrics
        accuracy = self.passed_count / total_tests if total_tests > 0 else 0.0
        meets_criteria = accuracy >= ACCURACY_THRESHOLD

        # Category breakdown
        category_stats = self._calculate_category_stats()

        summary = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_tests': total_tests,
            'passed': self.passed_count,
            'failed': self.failed_count,
            'errors': self.error_count,
            'accuracy': accuracy,
            'accuracy_threshold': ACCURACY_THRESHOLD,
            'meets_exit_criteria': meets_criteria,
            'category_breakdown': category_stats,
            'api_usage': self.parser.get_usage_stats(),
            'results': self.results
        }

        return summary

    def _calculate_category_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Calculate pass/fail stats by category.
        """
        stats = {}

        for result in self.results:
            category = result['category']

            if category not in stats:
                stats[category] = {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0}

            stats[category]['total'] += 1

            if result['status'] == 'pass':
                stats[category]['passed'] += 1
            elif result['status'] == 'fail':
                stats[category]['failed'] += 1
            elif result['status'] == 'error':
                stats[category]['errors'] += 1

        return stats

    def print_summary(self, summary: Dict[str, Any]):
        """
        Print detailed summary report.
        """
        print("\n" + "="*70)
        print("GOLDEN TEST SUITE SUMMARY")
        print("="*70)
        print(f"Total Tests:       {summary['total_tests']}")
        print(f"Passed:            {summary['passed']} ({summary['passed']/summary['total_tests']*100:.1f}%)")
        print(f"Failed:            {summary['failed']} ({summary['failed']/summary['total_tests']*100:.1f}%)")
        print(f"Errors:            {summary['errors']} ({summary['errors']/summary['total_tests']*100:.1f}%)")
        print(f"\nAccuracy:          {summary['accuracy']*100:.2f}%")
        print(f"Required:          {summary['accuracy_threshold']*100:.0f}%")
        print(f"\nExit Criteria:     {'✓ PASS' if summary['meets_exit_criteria'] else '✗ FAIL'}")

        print("\n" + "="*70)
        print("CATEGORY BREAKDOWN")
        print("="*70)

        for category, stats in summary['category_breakdown'].items():
            accuracy = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"{category:15} {stats['passed']}/{stats['total']} passed ({accuracy:.0f}%)")

        print("\n" + "="*70)
        print("API USAGE")
        print("="*70)
        usage = summary['api_usage']
        print(f"Requests:          {usage['request_count']}")
        print(f"Input Tokens:      {usage['total_input_tokens']:,}")
        print(f"Output Tokens:     {usage['total_output_tokens']:,}")
        print(f"Total Cost:        ${usage['total_cost_usd']:.2f}")

        if summary['failed'] > 0:
            print("\n" + "="*70)
            print("FAILED TESTS")
            print("="*70)

            for result in summary['results']:
                if result['status'] == 'fail':
                    print(f"\n{result['test_id']} - {result['category']}")
                    print(f"  Input: \"{result['pm_input']}\"")
                    print(f"  Mismatches:")
                    for mismatch in result['mismatches']:
                        print(f"    - {mismatch}")

        if summary['errors'] > 0:
            print("\n" + "="*70)
            print("ERROR TESTS")
            print("="*70)

            for result in summary['results']:
                if result['status'] == 'error':
                    print(f"\n{result['test_id']} - {result['category']}")
                    print(f"  Input: \"{result['pm_input']}\"")
                    print(f"  Error: {result['error']}")

        print("\n" + "="*70)

    def save_results(self, summary: Dict[str, Any], output_path: str = None):
        """
        Save results to JSON file.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                f"golden_test_results_{timestamp}.json"
            )

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"\n✓ Results saved to: {output_path}")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """
    Main entry point for golden test suite.
    """
    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("="*70)
        print("ERROR: ANTHROPIC_API_KEY not set")
        print("="*70)
        print("\nYou must set your Claude API key before running tests:")
        print("\nWindows PowerShell:")
        print('  $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"')
        print("\nLinux/Mac:")
        print('  export ANTHROPIC_API_KEY="sk-ant-your-key-here"')
        print("\nOr create .env file in project root:")
        print('  ANTHROPIC_API_KEY=sk-ant-your-key-here')
        print("\nGet your API key at: https://console.anthropic.com/")
        print("="*70)
        sys.exit(1)

    # Initialize runner
    runner = GoldenTestRunner()

    try:
        # Run all tests
        summary = runner.run_all_tests()

        # Print summary
        runner.print_summary(summary)

        # Save results
        runner.save_results(summary)

        # Exit with appropriate code
        if summary['meets_exit_criteria']:
            print("\n🎉 SUCCESS: Week 3-4 exit criteria met!")
            print(f"   Accuracy: {summary['accuracy']*100:.2f}% (required: {summary['accuracy_threshold']*100:.0f}%)")
            print(f"   You may proceed to Week 5-6.\n")
            sys.exit(0)
        else:
            print("\n⚠ FAILURE: Week 3-4 exit criteria NOT met")
            print(f"   Accuracy: {summary['accuracy']*100:.2f}% (required: {summary['accuracy_threshold']*100:.0f}%)")
            print(f"   {summary['passed']}/{summary['total_tests']} tests passing")
            print(f"   Need {int(summary['accuracy_threshold']*summary['total_tests']) - summary['passed']} more passing tests")
            print(f"\n   Next steps:")
            print(f"   1. Review failed tests above")
            print(f"   2. Iterate on system prompt (claude_system_prompt.txt)")
            print(f"   3. Re-run tests: python test_golden_integration.py\n")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print(f"Make sure golden tests file exists at: {GOLDEN_TESTS_PATH}")
        sys.exit(1)

    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
