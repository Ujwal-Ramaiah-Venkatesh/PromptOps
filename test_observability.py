"""
Test script for CloudWatch Observability integration
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, method="GET", data=None):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"Method: {method}")

    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("✅ SUCCESS")
            result = response.json()
            print(f"Response preview: {json.dumps(result, indent=2)[:500]}...")
        else:
            print(f"❌ FAILED")
            print(f"Response: {response.text[:200]}")

    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR - Is the backend running?")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def main():
    print("="*60)
    print("CloudWatch Observability Integration Test")
    print("="*60)

    # Test health endpoint
    test_endpoint(
        "CloudWatch Health Check",
        f"{BASE_URL}/api/v1/monitoring/cloudwatch/health"
    )

    # Test deployments list
    test_endpoint(
        "List Deployments",
        f"{BASE_URL}/api/v1/monitoring/cloudwatch/deployments/list"
    )

    # Test metrics endpoint
    test_endpoint(
        "Get CloudWatch Metrics",
        f"{BASE_URL}/api/v1/monitoring/cloudwatch/metrics?deployment=jewelry-vault&hours=1"
    )

    # Test health status
    test_endpoint(
        "Get Deployment Health",
        f"{BASE_URL}/api/v1/monitoring/cloudwatch/health/jewelry-vault"
    )

    # Test logs
    test_endpoint(
        "Get Deployment Logs",
        f"{BASE_URL}/api/v1/monitoring/cloudwatch/logs/jewelry-vault?limit=10"
    )

    # Test alerts
    test_endpoint(
        "Get Deployment Alerts",
        f"{BASE_URL}/api/v1/monitoring/cloudwatch/alerts/jewelry-vault"
    )

    # Test dashboard summary
    test_endpoint(
        "Get Dashboard Summary",
        f"{BASE_URL}/api/v1/monitoring/cloudwatch/dashboard/summary"
    )

    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. If all tests passed, the backend is working correctly")
    print("2. Start the frontend: cd frontend/dashboard && npm start")
    print("3. Open http://localhost:3000 and click 📊 Observability")
    print("4. Configure AWS credentials in .env for real CloudWatch data")

if __name__ == "__main__":
    main()
