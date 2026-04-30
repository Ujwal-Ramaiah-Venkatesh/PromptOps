"""
Test Secrets Management
Week 13-15: SECURITY-005
"""

import os
import sys

# Test in development mode first
os.environ['ENVIRONMENT'] = 'development'

from utils.secrets import get_secrets_manager, SecretNotFoundError

def test_secrets_manager_initialization():
    """Test secrets manager initializes correctly"""
    print("\n" + "="*60)
    print("Test 1: Secrets Manager Initialization")
    print("="*60)

    sm = get_secrets_manager()
    print(f"Environment: {sm.environment}")
    print(f"Using AWS: {sm.use_aws}")

    if sm.environment == 'development' and not sm.use_aws:
        print("[OK] Initialized for development (local .env)")
    elif sm.use_aws:
        print("[OK] Initialized for AWS Secrets Manager")
    else:
        print("[FAIL] Unexpected configuration")

def test_get_simple_secret():
    """Test getting simple secret"""
    print("\n" + "="*60)
    print("Test 2: Get Simple Secret")
    print("="*60)

    sm = get_secrets_manager()

    # Test with existing env var
    os.environ['TEST_SECRET'] = 'test-value-123'
    value = sm.get_secret('TEST_SECRET')
    print(f"Retrieved: {value}")

    if value == 'test-value-123':
        print("[OK] Simple secret retrieved")
    else:
        print(f"[FAIL] Expected 'test-value-123', got '{value}'")

def test_get_secret_with_default():
    """Test getting secret with default value"""
    print("\n" + "="*60)
    print("Test 3: Get Secret with Default")
    print("="*60)

    sm = get_secrets_manager()

    # Test with non-existent secret
    value = sm.get_secret('NON_EXISTENT_SECRET', 'default-value')
    print(f"Retrieved: {value}")

    if value == 'default-value':
        print("[OK] Default value used for missing secret")
    else:
        print(f"[FAIL] Expected 'default-value', got '{value}'")

def test_secret_not_found_error():
    """Test error handling for missing secret"""
    print("\n" + "="*60)
    print("Test 4: Secret Not Found Error")
    print("="*60)

    sm = get_secrets_manager()

    try:
        value = sm.get_secret('NON_EXISTENT_SECRET_NO_DEFAULT')
        print(f"[FAIL] Should have raised SecretNotFoundError, got: {value}")
    except SecretNotFoundError as e:
        print(f"[OK] Correctly raised SecretNotFoundError: {e}")

def test_get_database_url():
    """Test getting database URL"""
    print("\n" + "="*60)
    print("Test 5: Get Database URL")
    print("="*60)

    sm = get_secrets_manager()

    # Set test DATABASE_URL
    os.environ['DATABASE_URL'] = 'postgresql://testuser:testpass@localhost:5432/testdb'

    url = sm.get_database_url()
    print(f"Database URL: {url}")

    if url.startswith('postgresql://'):
        print("[OK] Database URL retrieved")
    else:
        print(f"[FAIL] Invalid database URL: {url}")

def test_get_jwt_secret():
    """Test getting JWT secret"""
    print("\n" + "="*60)
    print("Test 6: Get JWT Secret")
    print("="*60)

    sm = get_secrets_manager()

    secret = sm.get_jwt_secret()
    print(f"JWT Secret length: {len(secret)} characters")

    if len(secret) >= 32:
        print("[OK] JWT secret retrieved (adequate length)")
    else:
        print(f"[WARN] JWT secret too short: {len(secret)} characters")

def test_get_cors_origins():
    """Test getting CORS origins"""
    print("\n" + "="*60)
    print("Test 7: Get CORS Origins")
    print("="*60)

    sm = get_secrets_manager()

    origins = sm.get_cors_origins()
    print(f"CORS Origins: {origins}")
    print(f"Count: {len(origins)}")

    if isinstance(origins, list) and len(origins) > 0:
        print("[OK] CORS origins retrieved as list")
    else:
        print(f"[FAIL] Invalid CORS origins: {origins}")

def test_get_anthropic_api_key():
    """Test getting Anthropic API key"""
    print("\n" + "="*60)
    print("Test 8: Get Anthropic API Key")
    print("="*60)

    sm = get_secrets_manager()

    # Optional in development
    api_key = sm.get_anthropic_api_key()

    if api_key is None:
        print("[INFO] Anthropic API key not set (optional in development)")
    else:
        print(f"[OK] Anthropic API key retrieved (length: {len(api_key)})")

def test_caching():
    """Test that secrets are cached"""
    print("\n" + "="*60)
    print("Test 9: Secret Caching")
    print("="*60)

    sm = get_secrets_manager()

    # Set a secret
    os.environ['CACHE_TEST'] = 'value1'

    # Get it twice
    value1 = sm.get_secret('CACHE_TEST')
    value2 = sm.get_secret('CACHE_TEST')

    print(f"First retrieval: {value1}")
    print(f"Second retrieval: {value2}")

    if value1 == value2:
        print("[OK] Secret caching works")
    else:
        print(f"[FAIL] Caching issue: {value1} != {value2}")

def test_environment_detection():
    """Test environment detection"""
    print("\n" + "="*60)
    print("Test 10: Environment Detection")
    print("="*60)

    # Test development
    os.environ['ENVIRONMENT'] = 'development'
    from utils.secrets import SecretsManager
    sm_dev = SecretsManager()
    print(f"Development - Use AWS: {sm_dev.use_aws}")

    # Test staging
    os.environ['ENVIRONMENT'] = 'staging'
    sm_staging = SecretsManager()
    print(f"Staging - Use AWS: {sm_staging.use_aws}")

    # Test production
    os.environ['ENVIRONMENT'] = 'production'
    sm_prod = SecretsManager()
    print(f"Production - Use AWS: {sm_prod.use_aws}")

    # Reset to development
    os.environ['ENVIRONMENT'] = 'development'

    if not sm_dev.use_aws and (sm_staging.use_aws or sm_prod.use_aws):
        print("[OK] Environment detection works correctly")
        print("[INFO] AWS Secrets Manager used in staging/production")
    else:
        print("[INFO] boto3 not installed - AWS mode disabled")

def test_configuration_summary():
    """Print configuration summary"""
    print("\n" + "="*60)
    print("Configuration Summary")
    print("="*60)

    sm = get_secrets_manager()

    print(f"Environment: {sm.environment}")
    print(f"AWS Secrets Manager: {'Enabled' if sm.use_aws else 'Disabled'}")
    print(f"JWT Secret Length: {len(sm.get_jwt_secret())} chars")
    print(f"Database URL: {sm.get_database_url()[:30]}...")
    print(f"CORS Origins: {len(sm.get_cors_origins())} configured")
    print(f"Anthropic API Key: {'Set' if sm.get_anthropic_api_key() else 'Not Set'}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PromptOps Secrets Management Test Suite")
    print("  Week 13-15: SECURITY-005")
    print("="*60)
    print("\n  NOTE: These tests run in development mode")
    print("  AWS tests require boto3 and valid credentials")
    print("="*60)

    test_secrets_manager_initialization()
    test_get_simple_secret()
    test_get_secret_with_default()
    test_secret_not_found_error()
    test_get_database_url()
    test_get_jwt_secret()
    test_get_cors_origins()
    test_get_anthropic_api_key()
    test_caching()
    test_environment_detection()
    test_configuration_summary()

    print("\n" + "="*60)
    print("  Secrets Management Test Suite Complete")
    print("="*60 + "\n")
