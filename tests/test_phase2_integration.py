"""
Phase 2 Integration Tests
==========================

End-to-end tests for Phase 2 features:
- Real AWS Discovery
- PostgreSQL Database
- WebSocket Updates
- Cost Optimization
- Secret Rotation

Author: PromptOps Team
Date: 2026-04-30
Phase: 2 - Integration Testing
"""

import sys
import os
import time
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'phase2-aws'))


def test_aws_discovery():
    """Test AWS resource discovery with boto3."""
    print("\n" + "=" * 60)
    print("TEST 1: AWS Resource Discovery")
    print("=" * 60)

    try:
        from aws_discovery import AWSDiscoveryEngine

        # Initialize discovery engine
        discovery = AWSDiscoveryEngine(region='us-east-1')
        print("✅ AWS Discovery Engine initialized")

        # Test connection
        connection = discovery.test_connection()
        if connection['success']:
            print(f"✅ AWS Connection successful")
            print(f"   Account ID: {connection['account_id']}")
            print(f"   Region: {connection['region']}")
        else:
            print(f"❌ AWS Connection failed: {connection.get('error')}")
            return False

        # Discover resources (quick test - just EC2)
        print("\n🔍 Discovering EC2 instances...")
        ec2_instances = discovery.discover_ec2_instances()
        print(f"✅ Found {len(ec2_instances)} EC2 instances")

        # Get summary
        summary = discovery.get_resource_summary()
        print(f"\n📊 Total resources discovered: {summary['total_resources']}")
        for resource_type, count in summary['resource_counts'].items():
            if count > 0:
                print(f"   - {resource_type}: {count}")

        print("\n✅ AWS Discovery Test PASSED")
        return True

    except Exception as e:
        print(f"❌ AWS Discovery Test FAILED: {e}")
        return False


def test_database_connection():
    """Test PostgreSQL database connection."""
    print("\n" + "=" * 60)
    print("TEST 2: PostgreSQL Database")
    print("=" * 60)

    try:
        from database.connection import check_connection, get_db_context
        from database.models import User
        from database import crud

        # Test connection
        if check_connection():
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
            return False

        # Test CRUD operations
        with get_db_context() as db:
            # Count users
            user_count = db.query(User).count()
            print(f"✅ Users in database: {user_count}")

            # Test resource operations
            resources = crud.get_resources(db, limit=10)
            print(f"✅ Resources in database: {len(resources)}")

        print("\n✅ Database Test PASSED")
        return True

    except Exception as e:
        print(f"❌ Database Test FAILED: {e}")
        return False


def test_websocket_server():
    """Test WebSocket server initialization."""
    print("\n" + "=" * 60)
    print("TEST 3: WebSocket Server")
    print("=" * 60)

    try:
        from api_gateway.websocket_server import manager

        # Check connection manager
        stats = manager.get_stats()
        print(f"✅ WebSocket Manager initialized")
        print(f"   Active connections: {stats['active_connections']}")
        print(f"   Active subscriptions: {stats['active_subscriptions']}")

        print("\n✅ WebSocket Server Test PASSED")
        return True

    except Exception as e:
        print(f"❌ WebSocket Server Test FAILED: {e}")
        return False


def test_cost_explorer():
    """Test AWS Cost Explorer integration."""
    print("\n" + "=" * 60)
    print("TEST 4: AWS Cost Explorer")
    print("=" * 60)

    try:
        from cost_explorer import AWSCostExplorer

        # Initialize Cost Explorer
        cost_explorer = AWSCostExplorer(region='us-east-1')
        print("✅ Cost Explorer initialized")

        # Get total cost (this will fail if Cost Explorer API isn't enabled)
        try:
            total_cost = cost_explorer.get_total_cost(days=7)
            print(f"✅ Total cost (last 7 days): ${total_cost['total_cost']:.2f}")
            print(f"   Daily costs retrieved: {len(total_cost['daily_costs'])}")
        except Exception as e:
            print(f"⚠️  Cost data retrieval skipped (API may not be enabled): {e}")

        # Get recommendations
        recommendations = cost_explorer.get_cost_optimization_recommendations()
        print(f"✅ Generated {len(recommendations)} optimization recommendations")

        print("\n✅ Cost Explorer Test PASSED")
        return True

    except Exception as e:
        print(f"❌ Cost Explorer Test FAILED: {e}")
        return False


def test_vault_manager():
    """Test HashiCorp Vault integration."""
    print("\n" + "=" * 60)
    print("TEST 5: HashiCorp Vault")
    print("=" * 60)

    try:
        from vault_manager import VaultManager, generate_database_password

        # Initialize Vault
        vault = VaultManager()
        print("✅ Vault Manager initialized")

        # Check health
        health = vault.check_health()
        if health['healthy']:
            print(f"✅ Vault is healthy")
            print(f"   Initialized: {health.get('initialized')}")
            print(f"   Sealed: {health.get('sealed')}")
        else:
            print(f"⚠️  Vault health check: {health}")

        # Test secret operations
        test_path = 'test/phase2-integration'

        # Create test secret
        vault.create_secret(
            path=test_path,
            secret_data={
                'username': 'test',
                'password': generate_database_password(),
                'created_at': datetime.utcnow().isoformat()
            },
            secret_type='test'
        )
        print(f"✅ Test secret created at: {test_path}")

        # Read secret
        secret = vault.read_secret(test_path)
        print(f"✅ Secret read successfully (version {secret['version']})")

        # Rotate secret
        rotation = vault.rotate_secret(
            path=test_path,
            new_secret_data={
                'username': 'test',
                'password': generate_database_password(),
                'rotated_at': datetime.utcnow().isoformat()
            }
        )
        print(f"✅ Secret rotated: v{rotation['old_version']} → v{rotation['new_version']}")

        # Get versions
        versions = vault.get_secret_versions(test_path)
        print(f"✅ Retrieved {len(versions)} versions")

        # Cleanup
        vault.delete_secret(test_path)
        print(f"✅ Test secret cleaned up")

        print("\n✅ Vault Manager Test PASSED")
        return True

    except Exception as e:
        print(f"❌ Vault Manager Test FAILED: {e}")
        return False


def test_api_endpoints():
    """Test Phase 2 API endpoints."""
    print("\n" + "=" * 60)
    print("TEST 6: API Endpoints")
    print("=" * 60)

    try:
        # Test discovery routes
        from api_gateway.discovery_routes_aws import router as discovery_router
        print(f"✅ Discovery routes loaded: {len(discovery_router.routes)} endpoints")

        # Test cost routes
        from api_gateway.cost_routes import router as cost_router
        print(f"✅ Cost routes loaded: {len(cost_router.routes)} endpoints")

        # Test secrets routes
        from api_gateway.secrets_routes import router as secrets_router
        print(f"✅ Secrets routes loaded: {len(secrets_router.routes)} endpoints")

        print("\n✅ API Endpoints Test PASSED")
        return True

    except Exception as e:
        print(f"❌ API Endpoints Test FAILED: {e}")
        return False


def test_frontend_components():
    """Test frontend component files exist."""
    print("\n" + "=" * 60)
    print("TEST 7: Frontend Components")
    print("=" * 60)

    components = [
        'frontend/dashboard/src/hooks/useWebSocket.ts',
        'frontend/dashboard/src/components/ScanProgress.tsx',
        'frontend/dashboard/src/pages/CostDashboard.tsx',
        'frontend/dashboard/src/pages/SecretsManager.tsx',
    ]

    all_exist = True
    for component in components:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), component)
        if os.path.exists(path):
            print(f"✅ {component}")
        else:
            print(f"❌ {component} - NOT FOUND")
            all_exist = False

    if all_exist:
        print("\n✅ Frontend Components Test PASSED")
        return True
    else:
        print("\n❌ Frontend Components Test FAILED")
        return False


def run_all_tests():
    """Run all Phase 2 integration tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "PHASE 2 INTEGRATION TESTS" + " " * 18 + "║")
    print("║" + " " * 58 + "║")
    print("║" + "  Testing all Phase 2 features end-to-end" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")

    results = {}

    # Run all tests
    results['AWS Discovery'] = test_aws_discovery()
    results['PostgreSQL Database'] = test_database_connection()
    results['WebSocket Server'] = test_websocket_server()
    results['Cost Explorer'] = test_cost_explorer()
    results['Vault Manager'] = test_vault_manager()
    results['API Endpoints'] = test_api_endpoints()
    results['Frontend Components'] = test_frontend_components()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "-" * 60)
    print(f"Results: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    print("=" * 60)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Phase 2 is ready for production!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
