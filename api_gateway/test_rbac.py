"""
Test Role-Based Access Control (RBAC)
Week 13-15: SECURITY-002
"""

import requests
import json

API_BASE = "http://localhost:8000"

def get_token(email, password):
    """Helper to get JWT token"""
    response = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def test_parse_intent_requires_auth():
    """Test parse-intent requires authentication"""
    print("\n" + "="*60)
    print("Test 1: Parse Intent - Requires Authentication")
    print("="*60)

    # Without token
    response = requests.post(
        f"{API_BASE}/api/v1/parse-intent",
        json={"command": "deploy frontend v2.0 to staging", "user": "test"}
    )
    print(f"Without token: {response.status_code}")
    if response.status_code == 401:
        print("[OK] Correctly rejected request without token")
    else:
        print(f"[FAIL] Expected 401, got {response.status_code}")

    # With valid token
    token = get_token("pm@promptops.com", "pm123")
    if token:
        response = requests.post(
            f"{API_BASE}/api/v1/parse-intent",
            json={"command": "deploy frontend v2.0 to staging", "user": "pm"},
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"With token: {response.status_code}")
        if response.status_code == 200:
            print("[OK] Parse intent successful with authentication")
            data = response.json()
            print(f"  Intent: {data['intent']['intent_type']}")
        else:
            print(f"[FAIL] Expected 200, got {response.status_code}")

def test_environment_access_staging():
    """Test staging environment access"""
    print("\n" + "="*60)
    print("Test 2: Staging Environment - PM Access")
    print("="*60)

    token = get_token("pm@promptops.com", "pm123")
    if token:
        response = requests.post(
            f"{API_BASE}/api/v1/execute",
            json={
                "decomposition_id": "decomp-123",
                "target_env": "staging",
                "user": "pm"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"PM to staging: {response.status_code}")
        if response.status_code == 200:
            print("[OK] PM can execute in staging")
            data = response.json()
            print(f"  Execution ID: {data['execution_id']}")
            print(f"  Environment: {data['environment']}")
        else:
            print(f"[FAIL] PM should have staging access: {response.text}")

def test_environment_access_production_denied():
    """Test production environment - PM should be denied"""
    print("\n" + "="*60)
    print("Test 3: Production Environment - PM Denied")
    print("="*60)

    token = get_token("pm@promptops.com", "pm123")
    if token:
        response = requests.post(
            f"{API_BASE}/api/v1/execute",
            json={
                "decomposition_id": "decomp-123",
                "target_env": "production",
                "user": "pm"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"PM to production: {response.status_code}")
        if response.status_code == 403:
            print("[OK] PM correctly denied production access")
            print(f"  Message: {response.json()['detail']}")
        else:
            print(f"[FAIL] PM should be denied production access: {response.status_code}")

def test_environment_access_production_allowed():
    """Test production environment - Admin should be allowed"""
    print("\n" + "="*60)
    print("Test 4: Production Environment - Admin Allowed")
    print("="*60)

    token = get_token("admin@promptops.com", "admin123")
    if token:
        response = requests.post(
            f"{API_BASE}/api/v1/execute",
            json={
                "decomposition_id": "decomp-456",
                "target_env": "production",
                "user": "admin"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Admin to production: {response.status_code}")
        if response.status_code == 200:
            print("[OK] Admin can execute in production")
            data = response.json()
            print(f"  User role: {data['user_role']}")
            print(f"  Environment: {data['environment']}")
        else:
            print(f"[FAIL] Admin should have production access: {response.text}")

def test_scale_service():
    """Test scale service endpoint"""
    print("\n" + "="*60)
    print("Test 5: Scale Service - PM Can Scale Staging")
    print("="*60)

    token = get_token("pm@promptops.com", "pm123")
    if token:
        response = requests.post(
            f"{API_BASE}/api/v1/scale",
            json={
                "service": "backend",
                "desired_count": 5,
                "environment": "staging"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"PM scale staging: {response.status_code}")
        if response.status_code == 200:
            print("[OK] PM can scale staging services")
            data = response.json()
            print(f"  Service: {data['service']}")
            print(f"  Desired count: {data['desired_count']}")
        else:
            print(f"[FAIL] PM should be able to scale: {response.text}")

def test_audit_trail_access():
    """Test audit trail - all authenticated users can view"""
    print("\n" + "="*60)
    print("Test 6: Audit Trail - All Authenticated Users")
    print("="*60)

    # Test with PM
    token = get_token("pm@promptops.com", "pm123")
    if token:
        response = requests.get(
            f"{API_BASE}/api/v1/audit",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"PM access audit: {response.status_code}")
        if response.status_code == 200:
            print("[OK] PM can view audit trail")
        else:
            print(f"[FAIL] All users should view audit: {response.text}")

def test_decompose_requires_auth():
    """Test decompose endpoint requires authentication"""
    print("\n" + "="*60)
    print("Test 7: Decompose - Requires Authentication")
    print("="*60)

    # Without token
    response = requests.post(
        f"{API_BASE}/api/v1/decompose",
        json={
            "intent": {
                "intent_type": "deploy",
                "target_service": "frontend",
                "target_env": "staging"
            },
            "user": "test"
        }
    )
    print(f"Without token: {response.status_code}")
    if response.status_code == 401:
        print("[OK] Correctly requires authentication")
    else:
        print(f"[FAIL] Should require auth: {response.status_code}")

    # With token
    token = get_token("pm@promptops.com", "pm123")
    if token:
        response = requests.post(
            f"{API_BASE}/api/v1/decompose",
            json={
                "intent": {
                    "intent_type": "deploy",
                    "target_service": "frontend",
                    "target_env": "staging"
                },
                "user": "pm"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"With token: {response.status_code}")
        if response.status_code == 200:
            print("[OK] Decompose successful with authentication")
        else:
            print(f"[FAIL] Should work with valid token: {response.text}")

def test_role_hierarchy():
    """Test role hierarchy - admin has all permissions"""
    print("\n" + "="*60)
    print("Test 8: Role Hierarchy - Admin All Permissions")
    print("="*60)

    token = get_token("admin@promptops.com", "admin123")
    if not token:
        print("[FAIL] Could not get admin token")
        return

    tests = [
        ("Parse Intent", "POST", "/api/v1/parse-intent",
         {"command": "deploy frontend", "user": "admin"}),
        ("Decompose", "POST", "/api/v1/decompose",
         {"intent": {"intent_type": "deploy"}, "user": "admin"}),
        ("Execute Staging", "POST", "/api/v1/execute",
         {"decomposition_id": "d1", "target_env": "staging", "user": "admin"}),
        ("Execute Production", "POST", "/api/v1/execute",
         {"decomposition_id": "d2", "target_env": "production", "user": "admin"}),
        ("Scale", "POST", "/api/v1/scale",
         {"service": "api", "desired_count": 3, "environment": "production"}),
        ("Audit", "GET", "/api/v1/audit", None),
        ("Drift", "GET", "/api/v1/drift/recent", None),
    ]

    passed = 0
    for name, method, endpoint, data in tests:
        if method == "GET":
            response = requests.get(
                f"{API_BASE}{endpoint}",
                headers={"Authorization": f"Bearer {token}"}
            )
        else:
            response = requests.post(
                f"{API_BASE}{endpoint}",
                json=data,
                headers={"Authorization": f"Bearer {token}"}
            )

        if response.status_code == 200:
            passed += 1
            print(f"  [OK] {name}: {response.status_code}")
        else:
            print(f"  [FAIL] {name}: {response.status_code} - {response.text[:50]}")

    print(f"\nAdmin access: {passed}/{len(tests)} endpoints accessible")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PromptOps RBAC Test Suite")
    print("  Week 13-15: SECURITY-002")
    print("="*60)

    test_parse_intent_requires_auth()
    test_environment_access_staging()
    test_environment_access_production_denied()
    test_environment_access_production_allowed()
    test_scale_service()
    test_audit_trail_access()
    test_decompose_requires_auth()
    test_role_hierarchy()

    print("\n" + "="*60)
    print("  RBAC Test Suite Complete")
    print("="*60 + "\n")
