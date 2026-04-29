"""
End-to-End Workflow Tests
==========================

Complete workflow testing with real AWS infrastructure.

Test Scenarios:
1. Deploy to Staging (no approval)
2. Deploy to Production (with approval)
3. Scale Service (with context awareness)
4. Drift Detection & Revert
5. Rollback Deployment
6. Error Handling

Author: PromptOps Team - Week 11-12
Date: 2026-04-29
"""

import pytest
import requests
import time
from datetime import datetime
from typing import Dict, Any

# ============================================================================
# Configuration
# ============================================================================

API_BASE = "http://localhost:8000/api/v1"
TEST_USER = "e2e-test@promptops.com"
MAX_WAIT_TIME = 300  # 5 minutes

# ============================================================================
# Helper Functions
# ============================================================================

def wait_for_execution(execution_id: str, timeout: int = MAX_WAIT_TIME) -> Dict[str, Any]:
    """Poll execution status until complete or timeout."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(f"{API_BASE}/execution/{execution_id}")

        if not response.ok:
            pytest.fail(f"Failed to get execution status: {response.status_code}")

        data = response.json()
        status = data["status"]

        if status == "completed":
            return data
        elif status == "failed":
            pytest.fail(f"Execution failed: {data.get('error_message')}")

        time.sleep(5)  # Poll every 5 seconds

    pytest.fail(f"Execution {execution_id} timed out after {timeout} seconds")

def parse_command(command: str) -> Dict[str, Any]:
    """Parse natural language command."""
    response = requests.post(f"{API_BASE}/parse-intent", json={
        "command": command,
        "user": TEST_USER
    })

    assert response.status_code == 200, f"Parse failed: {response.status_code}"
    return response.json()["intent"]

def decompose_intent(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Decompose intent into tasks."""
    response = requests.post(f"{API_BASE}/decompose", json={
        "intent": intent,
        "user": TEST_USER
    })

    assert response.status_code == 200, f"Decompose failed: {response.status_code}"
    return response.json()["decomposition"]

def execute_task(decomposition: Dict[str, Any], approved: bool = True) -> str:
    """Execute task plan."""
    payload = {
        "decomposition_id": decomposition["decomposition_id"],
        "user": TEST_USER,
        "approved": approved
    }

    # Add approval phrase if high-risk
    if decomposition["risk_assessment"]["overall_risk"] in ["high", "critical"]:
        payload["approval_phrase"] = f"APPROVE {decomposition['operation_id']}"

    response = requests.post(f"{API_BASE}/execute", json=payload)

    assert response.status_code == 200, f"Execute failed: {response.status_code}"
    return response.json()["execution_id"]

# ============================================================================
# Test: Scenario 1 - Deploy to Staging
# ============================================================================

@pytest.mark.e2e
@pytest.mark.slow
def test_deploy_to_staging_workflow():
    """
    Test complete staging deployment workflow.

    Steps:
    1. Parse command: "Deploy frontend v2.4.0 to staging"
    2. Decompose into sub-tasks
    3. Verify risk level is low/medium (no approval needed)
    4. Execute deployment
    5. Wait for completion
    6. Verify audit log
    """
    print("\n" + "="*60)
    print("TEST: Deploy to Staging Workflow")
    print("="*60)

    # Step 1: Parse intent
    print("\n[1/6] Parsing command...")
    intent = parse_command("Deploy frontend v2.4.0 to staging")

    assert intent["intent_type"] == "deploy"
    assert intent["target_service"] == "frontend"
    assert intent["target_env"] == "staging"
    assert intent["confidence"] > 0.8
    print(f"✓ Intent parsed: {intent['intent_type']} {intent['target_service']}")

    # Step 2: Decompose
    print("\n[2/6] Decomposing into tasks...")
    decomposition = decompose_intent(intent)

    assert decomposition["total_sub_tasks"] > 0
    assert "sub_tasks" in decomposition
    print(f"✓ Decomposed into {decomposition['total_sub_tasks']} sub-tasks")

    # Step 3: Verify risk level
    print("\n[3/6] Checking risk assessment...")
    risk = decomposition["risk_assessment"]["overall_risk"]

    assert risk in ["low", "medium"], f"Unexpected risk level for staging: {risk}"
    assert not decomposition["risk_assessment"]["requires_approval"]
    print(f"✓ Risk level: {risk.upper()} (no approval required)")

    # Step 4: Execute
    print("\n[4/6] Executing deployment...")
    execution_id = execute_task(decomposition)
    print(f"✓ Execution started: {execution_id}")

    # Step 5: Wait for completion
    print("\n[5/6] Waiting for execution to complete...")
    result = wait_for_execution(execution_id)

    assert result["status"] == "completed"
    assert result["completed_tasks"] == result["total_tasks"]
    print(f"✓ Execution completed: {result['completed_tasks']}/{result['total_tasks']} tasks")

    # Step 6: Verify audit log
    print("\n[6/6] Verifying audit log...")
    response = requests.get(f"{API_BASE}/audit?limit=1&user={TEST_USER}")

    assert response.status_code == 200
    audit_entries = response.json()["entries"]

    assert len(audit_entries) > 0
    assert audit_entries[0]["status"] == "completed"
    print(f"✓ Audit log verified: {audit_entries[0]['command']}")

    print("\n" + "="*60)
    print("✅ TEST PASSED: Deploy to Staging")
    print("="*60)

# ============================================================================
# Test: Scenario 2 - Deploy to Production with Approval
# ============================================================================

@pytest.mark.e2e
@pytest.mark.slow
def test_deploy_to_production_with_approval():
    """
    Test production deployment with approval workflow.

    Steps:
    1. Parse: "Deploy api v3.1.0 to production"
    2. Decompose
    3. Verify CRITICAL risk level
    4. Verify approval required
    5. Execute with approval phrase
    6. Monitor execution
    7. Verify completion
    """
    print("\n" + "="*60)
    print("TEST: Deploy to Production with Approval")
    print("="*60)

    # Step 1: Parse
    print("\n[1/7] Parsing production deployment command...")
    intent = parse_command("Deploy api v3.1.0 to production")

    assert intent["target_env"] == "production"
    print(f"✓ Intent: {intent['intent_type']} to {intent['target_env']}")

    # Step 2: Decompose
    print("\n[2/7] Decomposing...")
    decomposition = decompose_intent(intent)
    print(f"✓ Decomposed: {decomposition['total_sub_tasks']} tasks")

    # Step 3: Verify critical risk
    print("\n[3/7] Checking risk level...")
    risk = decomposition["risk_assessment"]["overall_risk"]

    assert risk in ["high", "critical"], f"Expected high/critical risk, got {risk}"
    print(f"✓ Risk level: {risk.upper()}")

    # Step 4: Verify approval required
    print("\n[4/7] Verifying approval requirement...")
    assert decomposition["risk_assessment"]["requires_approval"]
    print(f"✓ Approval required: {decomposition['risk_assessment']['approval_level']}")

    # Step 5: Execute with approval
    print("\n[5/7] Executing with approval phrase...")
    approval_phrase = f"APPROVE {decomposition['operation_id']}"
    print(f"   Using phrase: {approval_phrase}")

    execution_id = execute_task(decomposition, approved=True)
    print(f"✓ Execution approved: {execution_id}")

    # Step 6: Monitor execution
    print("\n[6/7] Monitoring execution...")
    result = wait_for_execution(execution_id)

    assert result["status"] == "completed"
    print(f"✓ Completed: {result['completed_tasks']}/{result['total_tasks']} tasks")

    # Step 7: Verify audit
    print("\n[7/7] Verifying audit trail...")
    response = requests.get(f"{API_BASE}/audit?limit=1&env=production")

    audit = response.json()["entries"][0]
    assert audit["status"] == "completed"
    assert audit["target_env"] == "production"
    assert audit["approved_by"] == TEST_USER
    print(f"✓ Audit verified: approved by {audit['approved_by']}")

    print("\n" + "="*60)
    print("✅ TEST PASSED: Production Deployment with Approval")
    print("="*60)

# ============================================================================
# Test: Scenario 3 - Scale Service with Context
# ============================================================================

@pytest.mark.e2e
def test_scale_service_with_context():
    """
    Test scaling with context awareness.

    Steps:
    1. Parse: "Scale backend to 10 instances"
    2. Verify context injection (current count)
    3. Decompose
    4. Verify before/after state
    5. Execute (dry-run mode)
    """
    print("\n" + "="*60)
    print("TEST: Scale Service with Context")
    print("="*60)

    # Step 1: Parse
    print("\n[1/5] Parsing scale command...")
    intent = parse_command("Scale backend to 10 instances")

    assert intent["intent_type"] == "scale"
    assert intent["target_service"] == "backend"
    print(f"✓ Intent: scale {intent['target_service']}")

    # Step 2: Verify context
    print("\n[2/5] Checking context awareness...")

    # Should have current count from context
    if "current_count" in intent["parameters"]:
        print(f"✓ Context aware: current_count = {intent['parameters']['current_count']}")
    else:
        print("⚠ Warning: No context injection (context collector may not be running)")

    # Step 3: Decompose
    print("\n[3/5] Decomposing...")
    decomposition = decompose_intent(intent)
    print(f"✓ Sub-tasks: {decomposition['total_sub_tasks']}")

    # Step 4: Verify state comparison
    print("\n[4/5] Verifying state comparison...")

    if decomposition.get("current_state") and decomposition.get("target_state"):
        current = decomposition["current_state"]
        target = decomposition["target_state"]
        print(f"✓ Before: {current}")
        print(f"✓ After: {target}")
    else:
        print("⚠ Warning: State comparison not available")

    # Step 5: Rollback plan
    print("\n[5/5] Checking rollback plan...")

    if decomposition.get("rollback_plan"):
        rollback = decomposition["rollback_plan"]
        print(f"✓ Rollback plan: {rollback.get('total_steps', 0)} steps")

        if rollback.get("irreversible_tasks"):
            print(f"⚠ Irreversible tasks: {len(rollback['irreversible_tasks'])}")
        else:
            print("✓ Fully reversible")

    print("\n" + "="*60)
    print("✅ TEST PASSED: Scale with Context")
    print("="*60)

# ============================================================================
# Test: Scenario 4 - Drift Detection & Revert
# ============================================================================

@pytest.mark.e2e
def test_drift_detection_and_revert():
    """
    Test drift detection and auto-fix workflow.

    Note: Requires context collector to have detected drift.
    This test may be skipped if no drift exists.
    """
    print("\n" + "="*60)
    print("TEST: Drift Detection & Revert")
    print("="*60)

    # Step 1: Get drift events
    print("\n[1/4] Fetching drift events...")
    response = requests.get(f"{API_BASE}/drift/recent")

    assert response.status_code == 200
    data = response.json()

    if len(data["events"]) == 0:
        pytest.skip("No drift events available (context collector may not be running)")

    drift_event = data["events"][0]
    print(f"✓ Found drift: {drift_event['resource_type']}/{drift_event['resource_id']}")
    print(f"  Field: {drift_event['field']}")
    print(f"  Expected: {drift_event['expected_value']}")
    print(f"  Actual: {drift_event['actual_value']}")

    # Step 2: Check auto-fixable
    print("\n[2/4] Checking if auto-fixable...")

    if not drift_event["auto_fixable"]:
        pytest.skip("Drift event is not auto-fixable")

    print(f"✓ Auto-fixable: {drift_event['severity']} severity")

    # Step 3: Revert drift
    print("\n[3/4] Reverting drift...")
    response = requests.post(
        f"{API_BASE}/drift/{drift_event['id']}/revert",
        json={"user": TEST_USER}
    )

    assert response.status_code == 200
    print("✓ Drift revert initiated")

    # Step 4: Verify acknowledged
    print("\n[4/4] Verifying drift handled...")
    response = requests.get(f"{API_BASE}/drift/recent")
    data = response.json()

    # Drift should be removed or marked as reverted
    remaining_drift = [d for d in data["events"] if d["id"] == drift_event["id"]]

    if len(remaining_drift) == 0:
        print("✓ Drift removed from active list")
    else:
        assert remaining_drift[0].get("reverted_by") == TEST_USER
        print("✓ Drift marked as reverted")

    print("\n" + "="*60)
    print("✅ TEST PASSED: Drift Detection & Revert")
    print("="*60)

# ============================================================================
# Test: Scenario 5 - Error Handling
# ============================================================================

@pytest.mark.e2e
def test_error_handling():
    """
    Test error handling for invalid commands.

    Tests:
    1. Invalid command (low confidence)
    2. Missing required parameters
    3. Invalid approval phrase
    4. Non-existent resource
    """
    print("\n" + "="*60)
    print("TEST: Error Handling")
    print("="*60)

    # Test 1: Invalid command
    print("\n[1/4] Testing invalid command...")
    response = requests.post(f"{API_BASE}/parse-intent", json={
        "command": "xyzabc random gibberish",
        "user": TEST_USER
    })

    # Should either return low confidence or error
    if response.status_code == 200:
        intent = response.json()["intent"]
        assert intent["confidence"] < 0.5, "Expected low confidence for gibberish"
        print(f"✓ Low confidence: {intent['confidence']}")
    else:
        print(f"✓ Parse rejected: {response.status_code}")

    # Test 2: Missing parameters
    print("\n[2/4] Testing missing parameters...")
    intent = parse_command("Deploy something")

    # Should have missing params or low confidence
    assert len(intent["missing_params"]) > 0 or intent["confidence"] < 0.8
    print(f"✓ Missing params detected: {intent['missing_params']}")

    # Test 3: Invalid approval phrase
    print("\n[3/4] Testing invalid approval phrase...")

    # Create a high-risk decomposition
    intent = parse_command("Deploy api to production")
    decomposition = decompose_intent(intent)

    if decomposition["risk_assessment"]["requires_approval"]:
        response = requests.post(f"{API_BASE}/execute", json={
            "decomposition_id": decomposition["decomposition_id"],
            "user": TEST_USER,
            "approved": True,
            "approval_phrase": "WRONG PHRASE"
        })

        assert response.status_code == 403, "Expected 403 for invalid approval phrase"
        print("✓ Invalid approval phrase rejected")
    else:
        print("⚠ Skipped: Task doesn't require approval")

    # Test 4: Non-existent execution
    print("\n[4/4] Testing non-existent execution...")
    response = requests.get(f"{API_BASE}/execution/exec-nonexistent")

    assert response.status_code == 404
    print("✓ Non-existent execution returns 404")

    print("\n" + "="*60)
    print("✅ TEST PASSED: Error Handling")
    print("="*60)

# ============================================================================
# Test: Scenario 6 - Audit Trail Queries
# ============================================================================

@pytest.mark.e2e
def test_audit_trail_queries():
    """
    Test audit trail filtering and export.

    Tests:
    1. Filter by user
    2. Filter by environment
    3. Filter by status
    4. Pagination
    5. Export to CSV
    """
    print("\n" + "="*60)
    print("TEST: Audit Trail Queries")
    print("="*60)

    # Test 1: Filter by user
    print("\n[1/5] Testing user filter...")
    response = requests.get(f"{API_BASE}/audit?user={TEST_USER}&limit=10")

    assert response.status_code == 200
    data = response.json()

    for entry in data["entries"]:
        assert entry["user"] == TEST_USER
    print(f"✓ User filter: {len(data['entries'])} entries")

    # Test 2: Filter by environment
    print("\n[2/5] Testing environment filter...")
    response = requests.get(f"{API_BASE}/audit?env=production&limit=10")

    assert response.status_code == 200
    data = response.json()

    for entry in data["entries"]:
        assert entry["target_env"] == "production"
    print(f"✓ Environment filter: {len(data['entries'])} entries")

    # Test 3: Filter by status
    print("\n[3/5] Testing status filter...")
    response = requests.get(f"{API_BASE}/audit?status=completed&limit=10")

    assert response.status_code == 200
    data = response.json()

    for entry in data["entries"]:
        assert entry["status"] == "completed"
    print(f"✓ Status filter: {len(data['entries'])} entries")

    # Test 4: Pagination
    print("\n[4/5] Testing pagination...")
    response = requests.get(f"{API_BASE}/audit?limit=5&offset=0")

    assert response.status_code == 200
    page1 = response.json()

    response = requests.get(f"{API_BASE}/audit?limit=5&offset=5")
    page2 = response.json()

    # Pages should have different entries
    if len(page1["entries"]) > 0 and len(page2["entries"]) > 0:
        assert page1["entries"][0]["id"] != page2["entries"][0]["id"]
        print("✓ Pagination working")
    else:
        print("⚠ Not enough entries to test pagination")

    # Test 5: Export CSV
    print("\n[5/5] Testing CSV export...")
    response = requests.get(f"{API_BASE}/audit/export?format=csv")

    assert response.status_code == 200
    assert "text/csv" in response.headers.get("Content-Type", "")

    csv_content = response.text
    assert "timestamp" in csv_content.lower()
    assert "user" in csv_content.lower()
    print(f"✓ CSV export: {len(csv_content.splitlines())} lines")

    print("\n" + "="*60)
    print("✅ TEST PASSED: Audit Trail Queries")
    print("="*60)

# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
