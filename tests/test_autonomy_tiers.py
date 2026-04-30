"""
Autonomy Tier System Tests
===========================

Week 13-15: ENHANCEMENT-001
Author: PromptOps Team
Date: 2026-04-30
"""

import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add parent directory to path
parent_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, parent_dir)

from api_gateway.autonomy.tier_classifier import TierClassifier, RiskLevel, RiskAssessment
from api_gateway.autonomy.auto_executor import AutoExecutor


# ============================================================================
# Test Risk Classification
# ============================================================================

def test_risk_classifier_low_risk_actions():
    """Test that low-risk actions are classified correctly."""
    db_mock = Mock()
    classifier = TierClassifier(db_mock)

    # Test restart_pod
    intent = {
        "intent_type": "restart_pod",
        "target_env": "staging",
        "resource_type": "pod"
    }
    assessment = classifier.classify(intent)

    assert assessment.risk_level == RiskLevel.LOW
    assert assessment.can_auto_execute == True
    assert "restart_pod" in assessment.action_type


def test_risk_classifier_critical_actions():
    """Test that critical actions are classified correctly."""
    db_mock = Mock()
    classifier = TierClassifier(db_mock)

    # Test database schema change
    intent = {
        "intent_type": "database_schema_change",
        "target_env": "production",
        "resource_type": "database"
    }
    assessment = classifier.classify(intent)

    assert assessment.risk_level == RiskLevel.CRITICAL
    assert assessment.can_auto_execute == False  # CRITICAL never auto-executes


def test_risk_classifier_environment_adjustment():
    """Test that production environment increases risk."""
    db_mock = Mock()
    classifier = TierClassifier(db_mock)

    # Same action in staging vs production
    staging_intent = {
        "intent_type": "restart_pod",
        "target_env": "staging",
        "resource_type": "pod"
    }
    prod_intent = {
        "intent_type": "restart_pod",
        "target_env": "production",
        "resource_type": "pod"
    }

    staging_assessment = classifier.classify(staging_intent)
    prod_assessment = classifier.classify(prod_intent)

    # Production should be higher risk
    assert prod_assessment.risk_level > staging_assessment.risk_level


def test_risk_classifier_resource_adjustment():
    """Test that critical resources increase risk."""
    db_mock = Mock()
    classifier = TierClassifier(db_mock)

    # Operation on database resource
    intent = {
        "intent_type": "config_change",
        "target_env": "staging",
        "resource_type": "database"
    }
    assessment = classifier.classify(intent)

    # Database operations should be at least HIGH risk
    assert assessment.risk_level.value in ["high", "critical"]


def test_risk_classifier_parameter_adjustment():
    """Test that parameters can adjust risk."""
    db_mock = Mock()
    classifier = TierClassifier(db_mock)

    # Small disk cleanup (LOW risk)
    small_cleanup = {
        "intent_type": "disk_cleanup",
        "target_env": "staging",
        "resource_type": "disk",
        "parameters": {"size_gb": 5}
    }

    # Large disk cleanup (should bump to MEDIUM)
    large_cleanup = {
        "intent_type": "disk_cleanup",
        "target_env": "staging",
        "resource_type": "disk",
        "parameters": {"size_gb": 50}
    }

    small_assessment = classifier.classify(small_cleanup)
    large_assessment = classifier.classify(large_cleanup)

    # Large cleanup should have higher risk
    assert large_assessment.risk_level >= small_assessment.risk_level


# ============================================================================
# Test Autonomy Settings
# ============================================================================

def test_default_autonomy_settings():
    """Test that default settings require approval for all."""
    db_mock = Mock()
    db_mock.query().filter().first.return_value = None  # No settings found

    executor = AutoExecutor(db_mock)

    # All risk levels should default to require_approval
    assert executor._get_user_setting("user-123", "low") == "require_approval"
    assert executor._get_user_setting("user-123", "medium") == "require_approval"
    assert executor._get_user_setting("user-123", "high") == "require_approval"
    assert executor._get_user_setting("user-123", "critical") == "require_approval"


def test_custom_autonomy_settings():
    """Test custom autonomy settings are respected."""
    db_mock = Mock()

    # Mock user has LOW set to auto_execute
    mock_setting = Mock()
    mock_setting.behavior = "auto_execute"
    db_mock.query().filter().first.return_value = mock_setting

    executor = AutoExecutor(db_mock)

    assert executor._get_user_setting("user-123", "low") == "auto_execute"


def test_cannot_auto_execute_critical():
    """Test that CRITICAL actions never auto-execute."""
    db_mock = Mock()

    # Even if user somehow has CRITICAL set to auto_execute (shouldn't happen)
    mock_setting = Mock()
    mock_setting.behavior = "auto_execute"
    db_mock.query().filter().first.return_value = mock_setting

    executor = AutoExecutor(db_mock)

    user = Mock()
    user.id = "user-123"
    user.email = "test@promptops.com"

    critical_intent = {
        "intent_type": "delete_data",
        "target_env": "production",
        "resource_type": "database"
    }

    should_execute, assessment = executor.should_auto_execute(user, critical_intent)

    # CRITICAL should NEVER auto-execute
    assert should_execute == False
    assert assessment.risk_level == RiskLevel.CRITICAL


def test_auto_execute_low_risk_when_configured():
    """Test low-risk actions auto-execute when configured."""
    db_mock = Mock()

    # User has LOW set to auto_execute
    mock_setting = Mock()
    mock_setting.behavior = "auto_execute"
    db_mock.query().filter().first.return_value = mock_setting

    executor = AutoExecutor(db_mock)

    user = Mock()
    user.id = "user-123"
    user.email = "test@promptops.com"

    low_risk_intent = {
        "intent_type": "restart_pod",
        "target_env": "staging",
        "resource_type": "pod"
    }

    should_execute, assessment = executor.should_auto_execute(user, low_risk_intent)

    assert should_execute == True
    assert assessment.risk_level == RiskLevel.LOW


def test_require_approval_when_not_configured():
    """Test fail-safe: require approval if setting unknown."""
    db_mock = Mock()
    db_mock.query().filter().first.return_value = None  # No setting

    executor = AutoExecutor(db_mock)

    user = Mock()
    user.id = "user-123"
    user.email = "test@promptops.com"

    intent = {
        "intent_type": "scale_up",
        "target_env": "production",
        "resource_type": "ec2"
    }

    should_execute, assessment = executor.should_auto_execute(user, intent)

    # Should require approval (fail-safe default)
    assert should_execute == False


# ============================================================================
# Test Audit Logging
# ============================================================================

def test_auto_execution_logging():
    """Test that auto-executions are logged."""
    db_mock = Mock()

    executor = AutoExecutor(db_mock)

    user = Mock()
    user.id = "user-123"
    user.email = "test@promptops.com"

    # Call _log_auto_execution
    executor._log_auto_execution(
        user=user,
        operation_id="test-op-123",
        action_type="restart_pod",
        risk_level="low",
        command="restart pod-test",
        success=True,
        duration_ms=1234,
        result_summary="Success",
        ip="127.0.0.1",
        user_agent="test-agent"
    )

    # Verify database add was called
    assert db_mock.add.called
    assert db_mock.commit.called


# ============================================================================
# Test Integration
# ============================================================================

def test_full_autonomy_workflow():
    """Test complete workflow: classify -> check autonomy -> execute."""
    db_mock = Mock()

    # User has LOW set to auto_execute
    mock_setting = Mock()
    mock_setting.behavior = "auto_execute"
    db_mock.query().filter().first.return_value = mock_setting

    executor = AutoExecutor(db_mock)

    user = Mock()
    user.id = "user-123"
    user.email = "test@promptops.com"

    intent = {
        "intent_type": "restart_pod",
        "target_env": "staging",
        "resource_type": "pod",
        "operation_id": "op-123",
        "original_command": "restart pod-test",
        "client_ip": "127.0.0.1"
    }

    # Step 1: Check if should auto-execute
    should_execute, assessment = executor.should_auto_execute(user, intent)

    assert should_execute == True
    assert assessment.risk_level == RiskLevel.LOW

    # If this were a real execution, we would call:
    # result = await executor.execute_auto_action(user, intent, execute_fn)


# ============================================================================
# Test Edge Cases
# ============================================================================

def test_unknown_action_type():
    """Test that unknown action types default to MEDIUM risk."""
    db_mock = Mock()
    classifier = TierClassifier(db_mock)

    intent = {
        "intent_type": "unknown_action_xyz",
        "target_env": "staging",
        "resource_type": "unknown"
    }

    assessment = classifier.classify(intent)

    # Unknown actions should default to MEDIUM (fail-safe)
    assert assessment.risk_level == RiskLevel.MEDIUM


def test_database_exception_handling():
    """Test that database exceptions are handled gracefully."""
    db_mock = Mock()
    db_mock.query().filter().first.side_effect = Exception("DB error")

    executor = AutoExecutor(db_mock)

    # Should return default (require_approval) even on DB error
    result = executor._get_user_setting("user-123", "low")
    assert result == "require_approval"


def test_risk_level_comparison():
    """Test that risk levels can be compared."""
    assert RiskLevel.LOW < RiskLevel.MEDIUM
    assert RiskLevel.MEDIUM < RiskLevel.HIGH
    assert RiskLevel.HIGH < RiskLevel.CRITICAL


# ============================================================================
# Performance Tests
# ============================================================================

def test_risk_classification_performance():
    """Test that risk classification is fast (<50ms goal)."""
    import time

    db_mock = Mock()
    classifier = TierClassifier(db_mock)

    intent = {
        "intent_type": "restart_pod",
        "target_env": "staging",
        "resource_type": "pod"
    }

    # Measure 100 classifications
    start = time.time()
    for _ in range(100):
        assessment = classifier.classify(intent)
    end = time.time()

    avg_time_ms = ((end - start) / 100) * 1000

    # Should be under 50ms per classification
    assert avg_time_ms < 50, f"Classification took {avg_time_ms:.2f}ms (goal: <50ms)"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    import sys

    print("="*60)
    print("  Autonomy Tier System Tests")
    print("  Week 13-15: ENHANCEMENT-001")
    print("="*60)

    # Run tests
    test_functions = [
        test_risk_classifier_low_risk_actions,
        test_risk_classifier_critical_actions,
        test_risk_classifier_environment_adjustment,
        test_risk_classifier_resource_adjustment,
        test_risk_classifier_parameter_adjustment,
        test_default_autonomy_settings,
        test_custom_autonomy_settings,
        test_cannot_auto_execute_critical,
        test_auto_execute_low_risk_when_configured,
        test_require_approval_when_not_configured,
        test_auto_execution_logging,
        test_full_autonomy_workflow,
        test_unknown_action_type,
        test_database_exception_handling,
        test_risk_level_comparison,
        test_risk_classification_performance,
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
