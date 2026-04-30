"""
Test authentication endpoints - comprehensive test script
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_login():
    """Test login endpoint"""
    print("\n" + "="*60)
    print("Test 1: Admin Login")
    print("="*60)

    response = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        data={
            "username": "admin@promptops.com",
            "password": "admin123"
        }
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Login successful")
        print(f"  Token: {data['access_token'][:50]}...")
        print(f"  User: {data['user']['email']} ({data['user']['role']})")
        return data['access_token']
    else:
        print(f"[FAIL] Login failed: {response.text}")
        return None


def test_me_endpoint(token):
    """Test /me endpoint with token"""
    print("\n" + "="*60)
    print("Test 2: Get Current User (/me)")
    print("="*60)

    response = requests.get(
        f"{API_BASE}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        user = response.json()
        print(f"[OK] User info retrieved")
        print(f"  Email: {user['email']}")
        print(f"  Role: {user['role']}")
        print(f"  Active: {user['is_active']}")
    else:
        print(f"[FAIL] Failed: {response.text}")


def test_permissions(token):
    """Test /me/permissions endpoint"""
    print("\n" + "="*60)
    print("Test 3: Get User Permissions")
    print("="*60)

    response = requests.get(
        f"{API_BASE}/api/v1/auth/me/permissions",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Permissions retrieved")
        print(f"  Role: {data['role']}")
        print(f"  Permissions:")
        for perm, value in data['permissions'].items():
            status = "[OK]" if value else "[FAIL]"
            print(f"    {status} {perm}: {value}")
    else:
        print(f"[FAIL] Failed: {response.text}")


def test_pm_login():
    """Test PM user login"""
    print("\n" + "="*60)
    print("Test 4: PM Login")
    print("="*60)

    response = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        data={
            "username": "pm@promptops.com",
            "password": "pm123"
        }
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] PM login successful")
        print(f"  User: {data['user']['email']} ({data['user']['role']})")

        # Get permissions
        token = data['access_token']
        perm_response = requests.get(
            f"{API_BASE}/api/v1/auth/me/permissions",
            headers={"Authorization": f"Bearer {token}"}
        )
        if perm_response.status_code == 200:
            perms = perm_response.json()['permissions']
            print(f"  PM Permissions:")
            print(f"    Can deploy to staging: {perms.get('deploy_staging', False)}")
            print(f"    Can deploy to prod: {perms.get('deploy_production', False)}")
    else:
        print(f"[FAIL] PM login failed: {response.text}")


def test_register():
    """Test register endpoint"""
    print("\n" + "="*60)
    print("Test 5: Register New User")
    print("="*60)

    response = requests.post(
        f"{API_BASE}/api/v1/auth/register",
        json={
            "email": f"test-{datetime.now().timestamp()}@promptops.com",
            "password": "test123",
            "full_name": "Test Engineer",
            "role": "engineer"
        }
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        user = response.json()
        print(f"[OK] User registered successfully")
        print(f"  Email: {user['email']}")
        print(f"  Role: {user['role']}")
    else:
        print(f"[FAIL] Registration failed: {response.text}")


def test_list_users(admin_token):
    """Test list users endpoint (admin only)"""
    print("\n" + "="*60)
    print("Test 6: List Users (Admin)")
    print("="*60)

    response = requests.get(
        f"{API_BASE}/api/v1/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Users retrieved: {data['total']} users")
        for user in data['users']:
            print(f"  - {user['email']} ({user['role']})")
    else:
        print(f"[FAIL] Failed: {response.text}")


def test_invalid_token():
    """Test with invalid token"""
    print("\n" + "="*60)
    print("Test 7: Invalid Token")
    print("="*60)

    response = requests.get(
        f"{API_BASE}/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token-12345"}
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print(f"[OK] Correctly rejected invalid token")
    else:
        print(f"[FAIL] Unexpected response: {response.status_code}")


def test_wrong_password():
    """Test with wrong password"""
    print("\n" + "="*60)
    print("Test 8: Wrong Password")
    print("="*60)

    response = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        data={
            "username": "admin@promptops.com",
            "password": "wrongpassword"
        }
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print(f"[OK] Correctly rejected wrong password")
    else:
        print(f"[FAIL] Unexpected response: {response.status_code}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PromptOps Authentication System Test Suite")
    print("  Week 13-15: SECURITY-001 JWT Authentication")
    print("="*60)

    # Test 1: Admin login
    admin_token = test_login()

    if admin_token:
        # Test 2: Get current user
        test_me_endpoint(admin_token)

        # Test 3: Get permissions
        test_permissions(admin_token)

        # Test 4: PM login
        test_pm_login()

        # Test 5: Register new user
        test_register()

        # Test 6: List users
        test_list_users(admin_token)

        # Test 7: Invalid token
        test_invalid_token()

        # Test 8: Wrong password
        test_wrong_password()

    print("\n" + "="*60)
    print("  Test Suite Complete")
    print("="*60 + "\n")
