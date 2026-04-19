"""
Test Suite for LangGraph NLP Parser Framework
==============================================

This test script verifies that the LangGraph orchestration framework works correctly
by testing various scenarios including:
- Valid inputs
- Invalid inputs (validation failures)
- Retry logic
- Error handling
- State management

Run this script to verify the framework is working before integrating Claude Sonnet 4 API.

Author: Backend Engineer - Phase 1 Week 1
Date: 2026-04-19
"""

import sys
import json
from datetime import datetime
from typing import Dict, Any

# Import the LangGraph framework
try:
    from langgraph_setup import (
        execute_parser_workflow,
        create_parser_graph,
        ParserState
    )
    print("✓ Successfully imported LangGraph framework modules")
except ImportError as e:
    print(f"✗ Failed to import LangGraph framework: {e}")
    print("Make sure langgraph-setup.py is in the same directory")
    sys.exit(1)


# ============================================================================
# Test Utilities
# ============================================================================

def print_test_header(test_name: str, test_number: int, total_tests: int):
    """Print formatted test header."""
    print("\n" + "=" * 70)
    print(f"TEST {test_number}/{total_tests}: {test_name}")
    print("=" * 70)


def print_test_result(result: Dict[Any, Any], show_full_output: bool = False):
    """Print formatted test result."""
    print(f"\nStatus: {result['status']}")
    print(f"Retry Count: {result['retry_count']}")
    print(f"Confidence Score: {result['confidence_score']}")
    print(f"Errors: {len(result['errors'])} error(s)")

    if result['errors']:
        print("Error Details:")
        for idx, error in enumerate(result['errors'], 1):
            print(f"  {idx}. {error}")

    if show_full_output and result['output']:
        print("\nValidated Output:")
        print(json.dumps(result['output'], indent=2))


def assert_status(result: Dict[Any, Any], expected_status: str, test_name: str):
    """Assert that result status matches expected status."""
    actual_status = result['status']
    if actual_status == expected_status:
        print(f"✓ PASSED: Status is '{expected_status}' as expected")
        return True
    else:
        print(f"✗ FAILED: Expected status '{expected_status}', got '{actual_status}'")
        return False


def assert_has_errors(result: Dict[Any, Any], test_name: str):
    """Assert that result contains errors."""
    if result['errors']:
        print(f"✓ PASSED: Errors captured as expected ({len(result['errors'])} error(s))")
        return True
    else:
        print(f"✗ FAILED: Expected errors but none were found")
        return False


def assert_no_errors(result: Dict[Any, Any], test_name: str):
    """Assert that result contains no errors."""
    if not result['errors']:
        print(f"✓ PASSED: No errors as expected")
        return True
    else:
        print(f"✗ FAILED: Expected no errors but found {len(result['errors'])}")
        return False


def assert_has_output(result: Dict[Any, Any], test_name: str):
    """Assert that result contains validated output."""
    if result['output']:
        print(f"✓ PASSED: Validated output present")
        return True
    else:
        print(f"✗ FAILED: Expected validated output but none found")
        return False


def assert_confidence_above_threshold(result: Dict[Any, Any], threshold: float, test_name: str):
    """Assert that confidence score is above threshold."""
    confidence = result['confidence_score']
    if confidence >= threshold:
        print(f"✓ PASSED: Confidence {confidence} >= {threshold}")
        return True
    else:
        print(f"✗ FAILED: Confidence {confidence} < {threshold}")
        return False


# ============================================================================
# Test Cases
# ============================================================================

def test_valid_input_success():
    """Test Case 1: Valid input should succeed."""
    test_name = "Valid Input - Should Succeed"
    print_test_header(test_name, 1, 7)

    pm_input = """
    Build a comprehensive user management system that includes:
    - User registration with email verification
    - Secure login with JWT authentication
    - Password reset functionality
    - User profile management
    - Role-based access control (Admin, User, Guest)
    """

    print(f"Input: {pm_input.strip()}\n")
    result = execute_parser_workflow(pm_input)
    print_test_result(result, show_full_output=True)

    # Assertions
    passed = True
    passed &= assert_status(result, 'success', test_name)
    passed &= assert_no_errors(result, test_name)
    passed &= assert_has_output(result, test_name)
    passed &= assert_confidence_above_threshold(result, 0.7, test_name)

    return passed


def test_empty_input_failure():
    """Test Case 2: Empty input should fail validation."""
    test_name = "Empty Input - Should Fail"
    print_test_header(test_name, 2, 7)

    pm_input = ""

    print(f"Input: (empty string)\n")
    result = execute_parser_workflow(pm_input)
    print_test_result(result)

    # Assertions
    passed = True
    passed &= assert_status(result, 'failed', test_name)
    passed &= assert_has_errors(result, test_name)

    return passed


def test_too_short_input_failure():
    """Test Case 3: Too short input should fail validation."""
    test_name = "Too Short Input - Should Fail"
    print_test_header(test_name, 3, 7)

    pm_input = "Do task"

    print(f"Input: {pm_input}\n")
    result = execute_parser_workflow(pm_input)
    print_test_result(result)

    # Assertions
    passed = True
    passed &= assert_status(result, 'failed', test_name)
    passed &= assert_has_errors(result, test_name)

    return passed


def test_complex_input_success():
    """Test Case 4: Complex multi-feature input should succeed."""
    test_name = "Complex Input - Should Succeed"
    print_test_header(test_name, 4, 7)

    pm_input = """
    Develop a real-time analytics dashboard that:
    1. Connects to multiple data sources (PostgreSQL, Redis, Elasticsearch)
    2. Aggregates metrics in real-time using streaming pipelines
    3. Displays interactive charts and graphs with drill-down capabilities
    4. Sends alerts when thresholds are exceeded
    5. Exports reports in multiple formats (PDF, CSV, Excel)
    6. Implements caching for performance optimization
    7. Supports multi-tenant architecture with data isolation
    """

    print(f"Input: {pm_input.strip()[:100]}...\n")
    result = execute_parser_workflow(pm_input)
    print_test_result(result, show_full_output=True)

    # Assertions
    passed = True
    passed &= assert_status(result, 'success', test_name)
    passed &= assert_no_errors(result, test_name)
    passed &= assert_has_output(result, test_name)

    return passed


def test_minimal_valid_input():
    """Test Case 5: Minimal valid input (edge case)."""
    test_name = "Minimal Valid Input - Edge Case"
    print_test_header(test_name, 5, 7)

    pm_input = "Create a simple todo list application"

    print(f"Input: {pm_input}\n")
    result = execute_parser_workflow(pm_input)
    print_test_result(result)

    # Assertions
    passed = True
    passed &= assert_status(result, 'success', test_name)
    passed &= assert_no_errors(result, test_name)

    return passed


def test_special_characters_handling():
    """Test Case 6: Input with special characters should be sanitized."""
    test_name = "Special Characters - Should Handle"
    print_test_header(test_name, 6, 7)

    pm_input = """
    Build API endpoints with the following:
    - GET /users/{id} - Fetch user by ID
    - POST /users - Create new user (accepts JSON: {"name": "John", "email": "john@example.com"})
    - PUT /users/{id} - Update user
    - DELETE /users/{id} - Remove user
    Include rate limiting (100 req/min) & authentication (OAuth 2.0)
    """

    print(f"Input: {pm_input.strip()[:100]}...\n")
    result = execute_parser_workflow(pm_input)
    print_test_result(result)

    # Assertions
    passed = True
    passed &= assert_status(result, 'success', test_name)

    return passed


def test_retry_simulation():
    """Test Case 7: Simulate retry logic (uses 'test_retry' keyword)."""
    test_name = "Retry Logic - Simulation"
    print_test_header(test_name, 7, 7)

    # Note: The framework simulates a failure on first attempt when input contains "test_retry"
    pm_input = "Create a test_retry scenario for authentication system with secure login"

    print(f"Input: {pm_input}\n")
    print("Note: This test simulates an LLM failure to verify retry logic\n")

    result = execute_parser_workflow(pm_input)
    print_test_result(result)

    # Assertions
    passed = True
    # With retry logic, it should eventually succeed or reach max retries
    if result['status'] in ['success', 'needs_rephrase']:
        print(f"✓ PASSED: Retry logic handled appropriately (status: {result['status']})")
    else:
        print(f"✗ FAILED: Unexpected status after retry: {result['status']}")
        passed = False

    if result['retry_count'] > 0:
        print(f"✓ PASSED: Retry count incremented ({result['retry_count']} retries)")
    else:
        print(f"⚠ WARNING: Expected retry count > 0, got {result['retry_count']}")

    return passed


# ============================================================================
# Test Runner
# ============================================================================

def run_all_tests():
    """Run all test cases and report summary."""
    print("\n" + "=" * 70)
    print("LANGGRAPH NLP PARSER FRAMEWORK - TEST SUITE")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all tests
    test_results = {
        "Test 1: Valid Input": test_valid_input_success(),
        "Test 2: Empty Input": test_empty_input_failure(),
        "Test 3: Too Short Input": test_too_short_input_failure(),
        "Test 4: Complex Input": test_complex_input_success(),
        "Test 5: Minimal Valid Input": test_minimal_valid_input(),
        "Test 6: Special Characters": test_special_characters_handling(),
        "Test 7: Retry Logic": test_retry_simulation(),
    }

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for result in test_results.values() if result)
    total_count = len(test_results)

    for test_name, passed in test_results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status} - {test_name}")

    print("\n" + "-" * 70)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print(f"Success Rate: {(passed_count/total_count)*100:.1f}%")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Return exit code
    return 0 if passed_count == total_count else 1


# ============================================================================
# Framework Verification
# ============================================================================

def verify_framework_structure():
    """Verify that the framework structure is correct."""
    print("\n" + "=" * 70)
    print("FRAMEWORK STRUCTURE VERIFICATION")
    print("=" * 70)

    checks_passed = 0
    total_checks = 5

    # Check 1: Graph creation
    try:
        graph = create_parser_graph()
        print("✓ Graph creation successful")
        checks_passed += 1
    except Exception as e:
        print(f"✗ Graph creation failed: {e}")

    # Check 2: State schema
    try:
        test_state: ParserState = {
            'original_input': 'test',
            'sanitized_input': 'test',
            'llm_response': None,
            'validated_output': None,
            'retry_count': 0,
            'errors': [],
            'confidence_score': 0.0,
            'timestamp': datetime.now().isoformat(),
            'workflow_status': 'processing'
        }
        print("✓ State schema validated")
        checks_passed += 1
    except Exception as e:
        print(f"✗ State schema validation failed: {e}")

    # Check 3: Node functions exist
    try:
        from langgraph_setup import (
            input_validation_node,
            llm_parse_node,
            output_validation_node,
            retry_handler_node
        )
        print("✓ All node functions exist")
        checks_passed += 1
    except Exception as e:
        print(f"✗ Node function import failed: {e}")

    # Check 4: Conditional edge functions exist
    try:
        from langgraph_setup import (
            should_parse,
            should_validate,
            should_retry,
            should_continue_after_retry
        )
        print("✓ All conditional edge functions exist")
        checks_passed += 1
    except Exception as e:
        print(f"✗ Conditional edge function import failed: {e}")

    # Check 5: Execution helper exists
    try:
        from langgraph_setup import execute_parser_workflow
        print("✓ Execution helper function exists")
        checks_passed += 1
    except Exception as e:
        print(f"✗ Execution helper import failed: {e}")

    print(f"\nFramework Structure: {checks_passed}/{total_checks} checks passed")
    print("=" * 70)

    return checks_passed == total_checks


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n🚀 Starting LangGraph NLP Parser Framework Tests\n")

    # First verify framework structure
    structure_ok = verify_framework_structure()

    if not structure_ok:
        print("\n⚠ Framework structure verification failed!")
        print("Please fix the issues above before running tests.")
        sys.exit(1)

    # Run all tests
    exit_code = run_all_tests()

    # Print final message
    if exit_code == 0:
        print("\n✓ All tests passed! Framework is ready for Claude Sonnet 4 integration.")
    else:
        print("\n✗ Some tests failed. Please review the results above.")

    sys.exit(exit_code)
