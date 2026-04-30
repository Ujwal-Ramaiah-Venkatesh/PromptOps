"""
Test CORS Configuration
Week 13-15: SECURITY-003
"""

import requests

API_BASE = "http://localhost:8000"

def test_cors_allowed_origin():
    """Test CORS with allowed origin"""
    print("\n" + "="*60)
    print("Test 1: CORS - Allowed Origin (localhost:3000)")
    print("="*60)

    response = requests.options(
        f"{API_BASE}/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )

    print(f"Status: {response.status_code}")
    print(f"CORS Headers:")
    cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
    for header, value in cors_headers.items():
        print(f"  {header}: {value}")

    if "access-control-allow-origin" in response.headers:
        allowed_origin = response.headers["access-control-allow-origin"]
        if allowed_origin == "http://localhost:3000":
            print("[OK] Correct origin allowed")
        else:
            print(f"[WARN] Expected localhost:3000, got {allowed_origin}")
    else:
        print("[FAIL] No CORS header returned")

def test_cors_allowed_origin_3001():
    """Test CORS with allowed origin (port 3001)"""
    print("\n" + "="*60)
    print("Test 2: CORS - Allowed Origin (localhost:3001)")
    print("="*60)

    response = requests.options(
        f"{API_BASE}/health",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "GET"
        }
    )

    print(f"Status: {response.status_code}")
    if "access-control-allow-origin" in response.headers:
        allowed_origin = response.headers["access-control-allow-origin"]
        if allowed_origin == "http://localhost:3001":
            print("[OK] Correct origin allowed")
        else:
            print(f"[WARN] Expected localhost:3001, got {allowed_origin}")
    else:
        print("[FAIL] No CORS header returned")

def test_cors_disallowed_origin():
    """Test CORS with disallowed origin"""
    print("\n" + "="*60)
    print("Test 3: CORS - Disallowed Origin (malicious.com)")
    print("="*60)

    response = requests.options(
        f"{API_BASE}/health",
        headers={
            "Origin": "http://malicious.com",
            "Access-Control-Request-Method": "GET"
        }
    )

    print(f"Status: {response.status_code}")
    if "access-control-allow-origin" in response.headers:
        allowed_origin = response.headers["access-control-allow-origin"]
        if allowed_origin == "http://malicious.com":
            print("[FAIL] Malicious origin should NOT be allowed!")
        else:
            print(f"[WARN] Unexpected origin: {allowed_origin}")
    else:
        print("[OK] Malicious origin correctly rejected (no CORS header)")

def test_cors_credentials():
    """Test CORS credentials support"""
    print("\n" + "="*60)
    print("Test 4: CORS - Credentials Support")
    print("="*60)

    response = requests.options(
        f"{API_BASE}/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )

    print(f"Status: {response.status_code}")
    if "access-control-allow-credentials" in response.headers:
        creds = response.headers["access-control-allow-credentials"]
        if creds.lower() == "true":
            print("[OK] Credentials support enabled")
        else:
            print(f"[FAIL] Credentials should be 'true', got '{creds}'")
    else:
        print("[WARN] No credentials header present")

def test_cors_methods():
    """Test allowed HTTP methods"""
    print("\n" + "="*60)
    print("Test 5: CORS - Allowed Methods")
    print("="*60)

    response = requests.options(
        f"{API_BASE}/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        }
    )

    print(f"Status: {response.status_code}")
    if "access-control-allow-methods" in response.headers:
        methods = response.headers["access-control-allow-methods"]
        print(f"Allowed methods: {methods}")

        required_methods = ["GET", "POST", "PUT", "DELETE"]
        missing = []
        for method in required_methods:
            if method not in methods:
                missing.append(method)

        if not missing:
            print(f"[OK] All required methods allowed: {', '.join(required_methods)}")
        else:
            print(f"[FAIL] Missing methods: {', '.join(missing)}")
    else:
        print("[FAIL] No methods header present")

def test_cors_headers():
    """Test allowed headers"""
    print("\n" + "="*60)
    print("Test 6: CORS - Allowed Headers")
    print("="*60)

    response = requests.options(
        f"{API_BASE}/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type"
        }
    )

    print(f"Status: {response.status_code}")
    if "access-control-allow-headers" in response.headers:
        headers = response.headers["access-control-allow-headers"]
        print(f"Allowed headers: {headers}")

        if "authorization" in headers.lower() and "content-type" in headers.lower():
            print("[OK] Authorization and Content-Type headers allowed")
        else:
            print("[FAIL] Required headers not allowed")
    else:
        print("[WARN] No headers specification")

def test_actual_request_with_origin():
    """Test actual request with origin header"""
    print("\n" + "="*60)
    print("Test 7: Actual Request with CORS")
    print("="*60)

    response = requests.get(
        f"{API_BASE}/health",
        headers={"Origin": "http://localhost:3000"}
    )

    print(f"Status: {response.status_code}")
    if "access-control-allow-origin" in response.headers:
        origin = response.headers["access-control-allow-origin"]
        print(f"[OK] CORS header present in actual request: {origin}")
    else:
        print("[FAIL] CORS header missing in actual response")

    if response.status_code == 200:
        print("[OK] Request successful")
    else:
        print(f"[FAIL] Request failed: {response.status_code}")

def test_wildcard_not_used():
    """Verify wildcard (*) is NOT used"""
    print("\n" + "="*60)
    print("Test 8: Verify No Wildcard (*)")
    print("="*60)

    response = requests.options(
        f"{API_BASE}/health",
        headers={
            "Origin": "http://random-domain.com",
            "Access-Control-Request-Method": "GET"
        }
    )

    if "access-control-allow-origin" in response.headers:
        origin = response.headers["access-control-allow-origin"]
        if origin == "*":
            print("[FAIL] Wildcard (*) is being used - SECURITY RISK!")
        elif origin == "http://random-domain.com":
            print("[FAIL] Random domain was allowed - SECURITY RISK!")
        else:
            print(f"[WARN] Unexpected behavior: {origin}")
    else:
        print("[OK] Random domain not allowed (no CORS header)")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PromptOps CORS Configuration Test Suite")
    print("  Week 13-15: SECURITY-003")
    print("="*60)

    test_cors_allowed_origin()
    test_cors_allowed_origin_3001()
    test_cors_disallowed_origin()
    test_cors_credentials()
    test_cors_methods()
    test_cors_headers()
    test_actual_request_with_origin()
    test_wildcard_not_used()

    print("\n" + "="*60)
    print("  CORS Test Suite Complete")
    print("="*60 + "\n")
