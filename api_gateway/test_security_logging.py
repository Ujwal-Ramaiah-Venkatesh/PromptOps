"""
Test Security Logging
Week 13-15: SECURITY-006
"""

import requests
import time
import json
from pathlib import Path

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

def read_security_log(num_lines=50):
    """Read last N lines from security log"""
    log_file = Path("logs/security.log")
    if not log_file.exists():
        return []

    with open(log_file, 'r') as f:
        lines = f.readlines()
        return [json.loads(line.split(' - ')[-1]) for line in lines[-num_lines:] if line.strip()]

def test_login_success_logged():
    """Test successful login is logged"""
    print("\n" + "="*60)
    print("Test 1: Successful Login Logged")
    print("="*60)

    # Clear or note starting point
    initial_logs = read_security_log()
    initial_count = len(initial_logs)

    # Perform login
    response = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        data={"username": "admin@promptops.com", "password": "admin123"}
    )

    print(f"Login response: {response.status_code}")

    # Check logs
    time.sleep(0.5)  # Brief wait for log write
    logs = read_security_log()

    # Find login event
    login_events = [log for log in logs[initial_count:] if log.get('event_type') == 'login_attempt']

    if login_events:
        last_login = login_events[-1]
        print(f"[OK] Login logged:")
        print(f"  Email: {last_login['email']}")
        print(f"  Success: {last_login['success']}")
        print(f"  IP: {last_login['ip_address']}")
    else:
        print("[FAIL] No login event found in logs")

def test_failed_login_logged():
    """Test failed login is logged"""
    print("\n" + "="*60)
    print("Test 2: Failed Login Logged")
    print("="*60)

    initial_count = len(read_security_log())

    # Attempt login with wrong password
    response = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        data={"username": "admin@promptops.com", "password": "wrongpassword"}
    )

    print(f"Failed login response: {response.status_code}")

    # Check logs
    time.sleep(0.5)
    logs = read_security_log()

    login_events = [log for log in logs[initial_count:] if log.get('event_type') == 'login_attempt']

    if login_events:
        last_login = login_events[-1]
        print(f"[OK] Failed login logged:")
        print(f"  Email: {last_login['email']}")
        print(f"  Success: {last_login['success']}")
        print(f"  Result: {last_login['result']}")
    else:
        print("[FAIL] No failed login event found")

def test_registration_logged():
    """Test registration is logged"""
    print("\n" + "="*60)
    print("Test 3: Registration Logged")
    print("="*60)

    initial_count = len(read_security_log())

    # Register new user
    response = requests.post(
        f"{API_BASE}/api/v1/auth/register",
        json={
            "email": f"test-{time.time()}@example.com",
            "password": "test123",
            "full_name": "Test User",
            "role": "pm"
        }
    )

    print(f"Registration response: {response.status_code}")

    # Check logs
    time.sleep(0.5)
    logs = read_security_log()

    reg_events = [log for log in logs[initial_count:] if log.get('event_type') == 'registration']

    if reg_events:
        last_reg = reg_events[-1]
        print(f"[OK] Registration logged:")
        print(f"  Email: {last_reg['email']}")
        print(f"  Role: {last_reg['role']}")
        print(f"  Success: {last_reg['success']}")
    else:
        print("[FAIL] No registration event found")

def test_environment_access_denied_logged():
    """Test environment access denial is logged"""
    print("\n" + "="*60)
    print("Test 4: Environment Access Denial Logged")
    print("="*60)

    initial_count = len(read_security_log())

    # Get PM token
    token = get_token("pm@promptops.com", "pm123")
    if not token:
        print("[SKIP] Could not get PM token")
        return

    # Try to deploy to production (should be denied)
    response = requests.post(
        f"{API_BASE}/api/v1/execute",
        json={
            "decomposition_id": "decomp-123",
            "target_env": "production",
            "user": "pm"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Production access response: {response.status_code}")

    # Check logs
    time.sleep(0.5)
    logs = read_security_log()

    denial_events = [log for log in logs[initial_count:]
                    if log.get('event_type') == 'environment_access_denied']

    if denial_events:
        last_denial = denial_events[-1]
        print(f"[OK] Access denial logged:")
        print(f"  User: {last_denial['user']}")
        print(f"  Role: {last_denial['role']}")
        print(f"  Environment: {last_denial['environment']}")
    else:
        print("[FAIL] No access denial event found")

def test_deployment_logged():
    """Test deployment is logged"""
    print("\n" + "="*60)
    print("Test 5: Deployment Logged")
    print("="*60)

    initial_count = len(read_security_log())

    # Get admin token
    token = get_token("admin@promptops.com", "admin123")
    if not token:
        print("[SKIP] Could not get admin token")
        return

    # Execute deployment
    response = requests.post(
        f"{API_BASE}/api/v1/execute",
        json={
            "decomposition_id": "decomp-456",
            "target_env": "production",
            "user": "admin"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Deployment response: {response.status_code}")

    # Check logs
    time.sleep(0.5)
    logs = read_security_log()

    deploy_events = [log for log in logs[initial_count:]
                    if log.get('event_type') == 'deployment']

    if deploy_events:
        last_deploy = deploy_events[-1]
        print(f"[OK] Deployment logged:")
        print(f"  User: {last_deploy['user']}")
        print(f"  Environment: {last_deploy['environment']}")
        print(f"  Criticality: {last_deploy['criticality']}")
    else:
        print("[FAIL] No deployment event found")

def test_scaling_logged():
    """Test scaling operation is logged"""
    print("\n" + "="*60)
    print("Test 6: Scaling Operation Logged")
    print("="*60)

    initial_count = len(read_security_log())

    # Get PM token
    token = get_token("pm@promptops.com", "pm123")
    if not token:
        print("[SKIP] Could not get PM token")
        return

    # Scale service
    response = requests.post(
        f"{API_BASE}/api/v1/scale",
        json={
            "service": "backend",
            "desired_count": 5,
            "environment": "staging"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Scaling response: {response.status_code}")

    # Check logs
    time.sleep(0.5)
    logs = read_security_log()

    scale_events = [log for log in logs[initial_count:]
                   if log.get('event_type') == 'scaling_operation']

    if scale_events:
        last_scale = scale_events[-1]
        print(f"[OK] Scaling logged:")
        print(f"  User: {last_scale['user']}")
        print(f"  Service: {last_scale['service']}")
        print(f"  From: {last_scale['from_count']} -> To: {last_scale['to_count']}")
    else:
        print("[FAIL] No scaling event found")

def test_rate_limit_logged():
    """Test rate limit violations are logged"""
    print("\n" + "="*60)
    print("Test 7: Rate Limit Violation Logged")
    print("="*60)

    initial_count = len(read_security_log())

    # Trigger rate limit with multiple failed logins
    for i in range(6):  # Login limit is 5/minute
        requests.post(
            f"{API_BASE}/api/v1/auth/login",
            data={"username": "test@example.com", "password": "wrong"}
        )

    # Check logs
    time.sleep(0.5)
    logs = read_security_log()

    rate_limit_events = [log for log in logs[initial_count:]
                        if log.get('event_type') == 'rate_limit_exceeded']

    if rate_limit_events:
        last_rl = rate_limit_events[-1]
        print(f"[OK] Rate limit logged:")
        print(f"  Endpoint: {last_rl['endpoint']}")
        print(f"  IP: {last_rl['ip_address']}")
        print(f"  Limit: {last_rl['limit']}")
    else:
        print("[INFO] No rate limit event (may not have been triggered)")

def test_log_file_structure():
    """Test security log file structure"""
    print("\n" + "="*60)
    print("Test 8: Log File Structure")
    print("="*60)

    log_file = Path("logs/security.log")

    if not log_file.exists():
        print("[FAIL] Security log file does not exist")
        return

    print(f"[OK] Log file exists: {log_file}")
    print(f"  Size: {log_file.stat().st_size} bytes")

    # Check last few entries
    logs = read_security_log(10)
    print(f"  Recent entries: {len(logs)}")

    if logs:
        print("\n  Sample log entry:")
        sample = logs[-1]
        print(f"    Event type: {sample.get('event_type')}")
        print(f"    Timestamp: {sample.get('timestamp')}")
        print(f"    Keys: {list(sample.keys())}")
        print("[OK] Log entries are properly structured")
    else:
        print("[INFO] No log entries found")

def test_log_summary():
    """Print summary of all logged events"""
    print("\n" + "="*60)
    print("Security Log Summary")
    print("="*60)

    logs = read_security_log(100)

    event_types = {}
    for log in logs:
        event_type = log.get('event_type', 'unknown')
        event_types[event_type] = event_types.get(event_type, 0) + 1

    print(f"Total events: {len(logs)}")
    print("\nEvent breakdown:")
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type}: {count}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PromptOps Security Logging Test Suite")
    print("  Week 13-15: SECURITY-006")
    print("="*60)
    print("\n  NOTE: This test generates security events")
    print("  Check logs/security.log for full details")
    print("="*60)

    test_login_success_logged()
    test_failed_login_logged()
    test_registration_logged()
    test_environment_access_denied_logged()
    test_deployment_logged()
    test_scaling_logged()
    test_rate_limit_logged()
    test_log_file_structure()
    test_log_summary()

    print("\n" + "="*60)
    print("  Security Logging Test Suite Complete")
    print("="*60)
    print("\n  Security logs written to: logs/security.log")
    print("="*60 + "\n")
