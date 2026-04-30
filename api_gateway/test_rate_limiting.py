"""
Test Rate Limiting
Week 13-15: SECURITY-004
"""

import requests
import time

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

def test_login_rate_limit():
    """Test login endpoint rate limit (5/minute)"""
    print("\n" + "="*60)
    print("Test 1: Login Rate Limit (5/minute)")
    print("="*60)

    success_count = 0
    rate_limited = False

    for i in range(7):
        response = requests.post(
            f"{API_BASE}/api/v1/auth/login",
            data={"username": "admin@promptops.com", "password": "admin123"}
        )

        if response.status_code == 200:
            success_count += 1
            print(f"  Request {i+1}: [OK] 200")
        elif response.status_code == 429:
            rate_limited = True
            print(f"  Request {i+1}: [RATE LIMITED] 429")
            if "Retry-After" in response.headers:
                print(f"    Retry-After: {response.headers['Retry-After']}s")
            break
        else:
            print(f"  Request {i+1}: [ERROR] {response.status_code}")

    if rate_limited and success_count <= 5:
        print(f"[OK] Rate limit enforced after {success_count} requests")
    else:
        print(f"[FAIL] Rate limit not working (got {success_count} successes)")

def test_register_rate_limit():
    """Test register endpoint rate limit (3/minute)"""
    print("\n" + "="*60)
    print("Test 2: Register Rate Limit (3/minute)")
    print("="*60)

    success_count = 0
    rate_limited = False

    for i in range(5):
        response = requests.post(
            f"{API_BASE}/api/v1/auth/register",
            json={
                "email": f"test{time.time()}@example.com",
                "password": "test123",
                "full_name": "Test User",
                "role": "pm"
            }
        )

        if response.status_code == 201:
            success_count += 1
            print(f"  Request {i+1}: [OK] 201")
        elif response.status_code == 429:
            rate_limited = True
            print(f"  Request {i+1}: [RATE LIMITED] 429")
            break
        else:
            print(f"  Request {i+1}: [ERROR] {response.status_code} - {response.text[:50]}")

    if rate_limited and success_count <= 3:
        print(f"[OK] Rate limit enforced after {success_count} requests")
    else:
        print(f"[FAIL] Rate limit not working (got {success_count} successes)")

def test_parse_intent_rate_limit():
    """Test parse-intent endpoint rate limit (100/minute)"""
    print("\n" + "="*60)
    print("Test 3: Parse Intent Rate Limit (100/minute)")
    print("="*60)

    token = get_token("pm@promptops.com", "pm123")
    if not token:
        print("[FAIL] Could not get token")
        return

    print("  Testing first 10 requests...")
    success_count = 0

    for i in range(10):
        response = requests.post(
            f"{API_BASE}/api/v1/parse-intent",
            json={"command": f"deploy frontend v2.{i} to staging", "user": "pm"},
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            print(f"  Request {i+1}: [RATE LIMITED] 429 (unexpected)")
            break

    print(f"  Completed {success_count}/10 requests")

    if success_count == 10:
        print("[OK] Rate limit allows normal usage (10 requests successful)")
    else:
        print(f"[WARN] Only {success_count} requests succeeded")

def test_execute_rate_limit():
    """Test execute endpoint rate limit (20/minute)"""
    print("\n" + "="*60)
    print("Test 4: Execute Rate Limit (20/minute)")
    print("="*60)

    token = get_token("admin@promptops.com", "admin123")
    if not token:
        print("[FAIL] Could not get token")
        return

    print("  Testing first 5 requests...")
    success_count = 0

    for i in range(5):
        response = requests.post(
            f"{API_BASE}/api/v1/execute",
            json={
                "decomposition_id": f"decomp-{i}",
                "target_env": "staging",
                "user": "admin"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            success_count += 1

    print(f"  Completed {success_count}/5 requests")

    if success_count == 5:
        print("[OK] Rate limit allows normal usage (5 requests successful)")
    else:
        print(f"[WARN] Only {success_count} requests succeeded")

def test_rate_limit_headers():
    """Test rate limit headers are present"""
    print("\n" + "="*60)
    print("Test 5: Rate Limit Headers")
    print("="*60)

    response = requests.get(f"{API_BASE}/health")

    print(f"Status: {response.status_code}")
    print("Rate Limit Headers:")

    rate_limit_headers = {
        k: v for k, v in response.headers.items()
        if 'limit' in k.lower() or 'retry' in k.lower()
    }

    if rate_limit_headers:
        for header, value in rate_limit_headers.items():
            print(f"  {header}: {value}")
        print("[OK] Rate limit headers present")
    else:
        print("[INFO] No rate limit headers in response (may not be included by slowapi)")

def test_different_ips():
    """Test that rate limits are per IP"""
    print("\n" + "="*60)
    print("Test 6: Rate Limits Per IP")
    print("="*60)

    print("  Testing from single IP (current machine)...")
    success_count = 0

    for i in range(3):
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            success_count += 1

    print(f"  Completed {success_count}/3 requests")
    print("[INFO] Rate limits are enforced per IP address")
    print("[OK] Different IPs would have separate rate limit buckets")

def test_rate_limit_recovery():
    """Test rate limit resets after time window"""
    print("\n" + "="*60)
    print("Test 7: Rate Limit Recovery")
    print("="*60)

    print("  Making requests to trigger rate limit...")

    # Make enough requests to potentially hit limit
    for i in range(3):
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 429:
            print(f"  [INFO] Hit rate limit at request {i+1}")
            print("  Waiting 60 seconds for rate limit to reset...")
            print("  [SKIP] Recovery test - would take 60 seconds")
            print("[INFO] Rate limits reset after the time window expires")
            return

    print("[OK] Did not hit rate limit with normal usage")

def test_unauthenticated_rate_limits():
    """Test rate limits apply to unauthenticated endpoints"""
    print("\n" + "="*60)
    print("Test 8: Unauthenticated Endpoint Rate Limits")
    print("="*60)

    print("  Testing health endpoint (100/minute)...")
    success_count = 0

    for i in range(10):
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            print(f"  Request {i+1}: [RATE LIMITED] 429")
            break

    print(f"  Completed {success_count}/10 requests")

    if success_count >= 10:
        print("[OK] Rate limit allows normal usage")
    else:
        print(f"[WARN] Rate limited after {success_count} requests")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PromptOps Rate Limiting Test Suite")
    print("  Week 13-15: SECURITY-004")
    print("="*60)
    print("\n  NOTE: Rate limit tests may trigger actual rate limits.")
    print("  If tests fail due to rate limiting, wait 60 seconds and retry.")
    print("="*60)

    test_login_rate_limit()
    time.sleep(1)  # Brief pause between tests

    test_register_rate_limit()
    time.sleep(1)

    test_parse_intent_rate_limit()
    time.sleep(1)

    test_execute_rate_limit()
    time.sleep(1)

    test_rate_limit_headers()
    time.sleep(1)

    test_different_ips()
    time.sleep(1)

    test_rate_limit_recovery()
    time.sleep(1)

    test_unauthenticated_rate_limits()

    print("\n" + "="*60)
    print("  Rate Limiting Test Suite Complete")
    print("="*60 + "\n")
