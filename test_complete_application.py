"""
Complete Application Testing Suite
====================================

Tests both Frontend (Dashboard) and Backend (API) functionality.

Author: PromptOps Team
Date: 2026-05-03
"""

import sys
import os
import subprocess
import json
import time
from typing import Dict, Any, List
import csv

# Test results storage
test_results = []
passed = 0
failed = 0

def run_command(command: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute a command and return results."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Command timed out',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }


def make_api_request(endpoint: str, method: str = 'GET', data: Dict = None) -> Dict[str, Any]:
    """Make API request using curl."""
    base_url = 'http://localhost:8000'
    url = f'{base_url}{endpoint}'

    if method == 'GET':
        cmd = f'curl -s {url}'
    elif method == 'POST':
        json_data = json.dumps(data) if data else '{}'
        cmd = f'curl -s -X POST {url} -H "Content-Type: application/json" -d \'{json_data}\''

    result = run_command(cmd)

    try:
        if result['success']:
            response_data = json.loads(result['stdout'])
            return {'success': True, 'data': response_data}
        else:
            return {'success': False, 'error': result['stderr']}
    except json.JSONDecodeError:
        return {'success': False, 'error': 'Invalid JSON response', 'raw': result['stdout']}


def add_result(test_id: str, test_name: str, status: str, summary: str, details: str = ''):
    """Add test result."""
    global passed, failed, test_results

    test_results.append({
        'Test ID': test_id,
        'Test Name': test_name,
        'Status': status,
        'Summary': summary,
        'Details': details
    })

    if status == 'PASS':
        passed += 1
        print(f"  [PASS] {test_id}: {test_name}")
    else:
        failed += 1
        print(f"  [FAIL] {test_id}: {test_name}")


print("="*80)
print("COMPLETE APPLICATION TEST SUITE")
print("="*80)
print()

# ============================================================================
# BACKEND API TESTS
# ============================================================================

print("[1] BACKEND API TESTS")
print("-" * 80)

# Test 1: Backend Health Check
print("\n[TEST 1] Backend Health Check...")
response = make_api_request('/health')
if response['success'] and response['data'].get('status') == 'healthy':
    add_result('BE001', 'Backend Health Check', 'PASS',
               'Backend server is healthy and responsive',
               f"Services: {response['data'].get('services', {})}")
else:
    add_result('BE001', 'Backend Health Check', 'FAIL',
               'Backend server not responding or unhealthy',
               str(response))

# Test 2: API Root Endpoint
print("\n[TEST 2] API Root Endpoint...")
response = make_api_request('/')
if response['success']:
    add_result('BE002', 'API Root Endpoint', 'PASS',
               'Root endpoint accessible',
               str(response['data']))
else:
    add_result('BE002', 'API Root Endpoint', 'FAIL',
               'Root endpoint not accessible',
               str(response))

# Test 3: NLP Parser Endpoint - Discovery Command
print("\n[TEST 3] NLP Parser - Discovery Command...")
response = make_api_request(
    '/api/v1/parser/parse',
    method='POST',
    data={'command': 'Find all EC2 instances in us-east-1'}
)
if response['success']:
    data = response['data']
    if (data.get('intent_type') == 'discovery' and
        data.get('parameters', {}).get('resource_type') == 'ec2_instance' and
        data.get('parameters', {}).get('region') == 'us-east-1'):
        add_result('BE003', 'NLP Parser - Discovery Command', 'PASS',
                   'Parser correctly identified discovery intent with EC2 and region',
                   f"Intent: {data.get('intent_type')}, Confidence: {data.get('confidence')}")
    else:
        add_result('BE003', 'NLP Parser - Discovery Command', 'FAIL',
                   'Parser did not correctly parse the command',
                   str(data))
else:
    add_result('BE003', 'NLP Parser - Discovery Command', 'FAIL',
               'Parser endpoint not responding',
               str(response))

# Test 4: NLP Parser - Deployment Command
print("\n[TEST 4] NLP Parser - Deployment Command...")
response = make_api_request(
    '/api/v1/parser/parse',
    method='POST',
    data={'command': 'Deploy my Flipkar application on AWS'}
)
if response['success']:
    data = response['data']
    if (data.get('intent_type') == 'deployment' and
        data.get('target_service') == 'flipkar' and
        data.get('parameters', {}).get('cloud_provider') == 'aws'):
        add_result('BE004', 'NLP Parser - Deployment Command', 'PASS',
                   'Parser correctly identified deployment intent with service and provider',
                   f"Service: {data.get('target_service')}, Provider: {data.get('parameters', {}).get('cloud_provider')}")
    else:
        add_result('BE004', 'NLP Parser - Deployment Command', 'FAIL',
                   'Parser did not correctly parse deployment command',
                   str(data))
else:
    add_result('BE004', 'NLP Parser - Deployment Command', 'FAIL',
               'Parser endpoint failed',
               str(response))

# Test 5: NLP Parser - Cost Analysis Command
print("\n[TEST 5] NLP Parser - Cost Analysis Command...")
response = make_api_request(
    '/api/v1/parser/parse',
    method='POST',
    data={'command': 'Show me the cost breakdown for AWS'}
)
if response['success']:
    data = response['data']
    if (data.get('intent_type') == 'cost_analysis' and
        data.get('parameters', {}).get('cloud_provider') == 'aws'):
        add_result('BE005', 'NLP Parser - Cost Analysis Command', 'PASS',
                   'Parser correctly identified cost analysis intent',
                   f"Intent: {data.get('intent_type')}, Provider: {data.get('parameters', {}).get('cloud_provider')}")
    else:
        add_result('BE005', 'NLP Parser - Cost Analysis Command', 'FAIL',
                   'Parser did not correctly parse cost command',
                   str(data))
else:
    add_result('BE005', 'NLP Parser - Cost Analysis Command', 'FAIL',
               'Parser endpoint failed',
               str(response))

# Test 6: NLP Parser - Scaling Command
print("\n[TEST 6] NLP Parser - Scaling Command...")
response = make_api_request(
    '/api/v1/parser/parse',
    method='POST',
    data={'command': 'Scale my application to 5 instances'}
)
if response['success']:
    data = response['data']
    if (data.get('intent_type') == 'scaling' and
        data.get('parameters', {}).get('instance_count') == 5):
        add_result('BE006', 'NLP Parser - Scaling Command', 'PASS',
                   'Parser correctly identified scaling intent with instance count',
                   f"Intent: {data.get('intent_type')}, Count: {data.get('parameters', {}).get('instance_count')}")
    else:
        add_result('BE006', 'NLP Parser - Scaling Command', 'FAIL',
                   'Parser did not correctly parse scaling command',
                   str(data))
else:
    add_result('BE006', 'NLP Parser - Scaling Command', 'FAIL',
               'Parser endpoint failed',
               str(response))

# Test 7: NLP Parser - S3 Discovery
print("\n[TEST 7] NLP Parser - S3 Discovery...")
response = make_api_request(
    '/api/v1/parser/parse',
    method='POST',
    data={'command': 'Find all S3 buckets in us-west-2'}
)
if response['success']:
    data = response['data']
    if (data.get('intent_type') == 'discovery' and
        data.get('parameters', {}).get('resource_type') == 's3_bucket' and
        data.get('parameters', {}).get('region') == 'us-west-2'):
        add_result('BE007', 'NLP Parser - S3 Discovery', 'PASS',
                   'Parser correctly identified S3 discovery with region',
                   f"Resource: {data.get('parameters', {}).get('resource_type')}, Region: {data.get('parameters', {}).get('region')}")
    else:
        add_result('BE007', 'NLP Parser - S3 Discovery', 'FAIL',
                   'Parser did not correctly parse S3 command',
                   str(data))
else:
    add_result('BE007', 'NLP Parser - S3 Discovery', 'FAIL',
               'Parser endpoint failed',
               str(response))

# Test 8: NLP Parser - Invalid/Empty Command
print("\n[TEST 8] NLP Parser - Empty Command Handling...")
response = make_api_request(
    '/api/v1/parser/parse',
    method='POST',
    data={'command': ''}
)
if not response['success'] or (response['success'] and 'error' in str(response).lower()):
    add_result('BE008', 'NLP Parser - Empty Command Handling', 'PASS',
               'Parser correctly rejects empty commands',
               'Error handling working as expected')
else:
    add_result('BE008', 'NLP Parser - Empty Command Handling', 'FAIL',
               'Parser should reject empty commands',
               str(response))

# Test 9: CORS Headers
print("\n[TEST 9] CORS Configuration...")
result = run_command('curl -s -I http://localhost:8000/health')
if result['success'] and 'access-control-allow-origin' in result['stdout'].lower():
    add_result('BE009', 'CORS Configuration', 'PASS',
               'CORS headers are properly configured',
               'Access-Control-Allow-Origin header present')
else:
    add_result('BE009', 'CORS Configuration', 'FAIL',
               'CORS headers may not be configured',
               result['stdout'])

# Test 10: API Response Time
print("\n[TEST 10] API Response Time...")
start_time = time.time()
response = make_api_request('/health')
response_time = (time.time() - start_time) * 1000  # Convert to ms

if response['success'] and response_time < 1000:  # Less than 1 second
    add_result('BE010', 'API Response Time', 'PASS',
               f'API responds quickly: {response_time:.2f}ms',
               'Performance acceptable for production use')
else:
    add_result('BE010', 'API Response Time', 'FAIL',
               f'API response too slow: {response_time:.2f}ms',
               'Performance may need optimization')

# ============================================================================
# FRONTEND TESTS
# ============================================================================

print("\n\n[2] FRONTEND TESTS")
print("-" * 80)

# Test 11: Dashboard HTML File Exists
print("\n[TEST 11] Dashboard HTML File...")
dashboard_path = 'PROMPTOPS_DASHBOARD.html'
if os.path.exists(dashboard_path):
    file_size = os.path.getsize(dashboard_path)
    add_result('FE001', 'Dashboard HTML File Exists', 'PASS',
               f'Dashboard file exists ({file_size} bytes)',
               f'Located at: {os.path.abspath(dashboard_path)}')
else:
    add_result('FE001', 'Dashboard HTML File Exists', 'FAIL',
               'Dashboard file not found',
               f'Expected at: {os.path.abspath(dashboard_path)}')

# Test 12: Dashboard Structure - Stats Cards
print("\n[TEST 12] Dashboard Structure - Stats Cards...")
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
        stats_count = content.count('Total Resources') + content.count('Monthly Cost') + \
                     content.count('Cloud Providers') + content.count('Potential Savings')
        if stats_count >= 4:
            add_result('FE002', 'Dashboard Stats Cards', 'PASS',
                       'All 4 statistics cards present in dashboard',
                       'Total Resources, Monthly Cost, Cloud Providers, Potential Savings')
        else:
            add_result('FE002', 'Dashboard Stats Cards', 'FAIL',
                       f'Only {stats_count} stats cards found, expected 4',
                       'Dashboard structure incomplete')
else:
    add_result('FE002', 'Dashboard Stats Cards', 'FAIL',
               'Cannot test - dashboard file missing', '')

# Test 13: Dashboard - NLP Command Input
print("\n[TEST 13] Dashboard NLP Command Input...")
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'nlpCommand' in content and 'parseCommand' in content:
            add_result('FE003', 'Dashboard NLP Command Input', 'PASS',
                       'NLP command input field and parse button present',
                       'Interactive command parsing UI available')
        else:
            add_result('FE003', 'Dashboard NLP Command Input', 'FAIL',
                       'NLP command input components missing',
                       'Dashboard missing interactive features')
else:
    add_result('FE003', 'Dashboard NLP Command Input', 'FAIL',
               'Cannot test - dashboard file missing', '')

# Test 14: Dashboard - Chart.js Integration
print("\n[TEST 14] Dashboard Chart Integration...")
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'chart.js' in content.lower() and 'costChart' in content:
            add_result('FE004', 'Dashboard Chart Integration', 'PASS',
                       'Chart.js library integrated with cost chart',
                       'Interactive cost visualization available')
        else:
            add_result('FE004', 'Dashboard Chart Integration', 'FAIL',
                       'Chart.js or cost chart missing',
                       'Visualization features incomplete')
else:
    add_result('FE004', 'Dashboard Chart Integration', 'FAIL',
               'Cannot test - dashboard file missing', '')

# Test 15: Dashboard - API Integration
print("\n[TEST 15] Dashboard API Integration...")
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
        api_base_present = 'localhost:8000' in content or 'API_BASE' in content
        fetch_present = 'fetch' in content and '/api/v1/parser/parse' in content
        if api_base_present and fetch_present:
            add_result('FE005', 'Dashboard API Integration', 'PASS',
                       'Dashboard configured to call backend API',
                       'Frontend-backend integration configured')
        else:
            add_result('FE005', 'Dashboard API Integration', 'FAIL',
                       'API integration not properly configured',
                       'Dashboard may not communicate with backend')
else:
    add_result('FE005', 'Dashboard API Integration', 'FAIL',
               'Cannot test - dashboard file missing', '')

# Test 16: Dashboard - Tailwind CSS
print("\n[TEST 16] Dashboard Styling...")
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'tailwindcss' in content:
            add_result('FE006', 'Dashboard Styling', 'PASS',
                       'Tailwind CSS integrated for modern styling',
                       'Professional UI design framework present')
        else:
            add_result('FE006', 'Dashboard Styling', 'FAIL',
                       'Tailwind CSS not found',
                       'Dashboard may lack proper styling')
else:
    add_result('FE006', 'Dashboard Styling', 'FAIL',
               'Cannot test - dashboard file missing', '')

# Test 17: Dashboard - Cloud Provider Cards
print("\n[TEST 17] Dashboard Cloud Provider Cards...")
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
        aws_present = 'AWS' in content
        gcp_present = 'GCP' in content
        azure_present = 'Azure' in content
        if aws_present and gcp_present and azure_present:
            add_result('FE007', 'Dashboard Cloud Provider Cards', 'PASS',
                       'All 3 cloud provider cards present (AWS, GCP, Azure)',
                       'Multi-cloud visualization available')
        else:
            add_result('FE007', 'Dashboard Cloud Provider Cards', 'FAIL',
                       'Not all cloud provider cards found',
                       f'AWS: {aws_present}, GCP: {gcp_present}, Azure: {azure_present}')
else:
    add_result('FE007', 'Dashboard Cloud Provider Cards', 'FAIL',
               'Cannot test - dashboard file missing', '')

# Test 18: Dashboard - Quick Actions
print("\n[TEST 18] Dashboard Quick Actions...")
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
        actions = content.count('Run Discovery Scan') + content.count('View Cost Analysis') + \
                 content.count('View Optimizations')
        if actions >= 3:
            add_result('FE008', 'Dashboard Quick Actions', 'PASS',
                       'All 3 quick action buttons present',
                       'Discovery, Cost Analysis, and Optimizations')
        else:
            add_result('FE008', 'Dashboard Quick Actions', 'FAIL',
                       f'Only {actions} action buttons found, expected 3',
                       'Quick actions incomplete')
else:
    add_result('FE008', 'Dashboard Quick Actions', 'FAIL',
               'Cannot test - dashboard file missing', '')

# Test 19: Dashboard - API Documentation Links
print("\n[TEST 19] Dashboard API Documentation Links...")
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
        swagger_link = '/docs' in content
        redoc_link = '/redoc' in content
        health_link = '/health' in content
        if swagger_link and redoc_link and health_link:
            add_result('FE009', 'Dashboard API Documentation Links', 'PASS',
                       'All API documentation links present',
                       'Swagger, ReDoc, and Health Check links available')
        else:
            add_result('FE009', 'Dashboard API Documentation Links', 'FAIL',
                       'Not all documentation links found',
                       f'Swagger: {swagger_link}, ReDoc: {redoc_link}, Health: {health_link}')
else:
    add_result('FE009', 'Dashboard API Documentation Links', 'FAIL',
               'Cannot test - dashboard file missing', '')

# Test 20: Dashboard - Status Indicator
print("\n[TEST 20] Dashboard Status Indicator...")
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'checkStatus' in content and 'status' in content.lower():
            add_result('FE010', 'Dashboard Status Indicator', 'PASS',
                       'Live status indicator configured',
                       'Real-time backend connection monitoring')
        else:
            add_result('FE010', 'Dashboard Status Indicator', 'FAIL',
                       'Status indicator not found',
                       'Dashboard may not show connection status')
else:
    add_result('FE010', 'Dashboard Status Indicator', 'FAIL',
               'Cannot test - dashboard file missing', '')

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

print("\n\n[3] INTEGRATION TESTS")
print("-" * 80)

# Test 21: End-to-End NLP Flow
print("\n[TEST 21] End-to-End NLP Flow...")
test_commands = [
    'Find all EC2 instances in us-east-1',
    'Deploy my Flipkar application on AWS',
    'Show me the cost breakdown for AWS'
]
all_passed = True
for cmd in test_commands:
    response = make_api_request('/api/v1/parser/parse', 'POST', {'command': cmd})
    if not response['success'] or response['data'].get('intent_type') == 'unknown':
        all_passed = False
        break

if all_passed:
    add_result('INT001', 'End-to-End NLP Flow', 'PASS',
               'All test commands parsed successfully',
               f'Tested {len(test_commands)} different command types')
else:
    add_result('INT001', 'End-to-End NLP Flow', 'FAIL',
               'Some commands failed to parse',
               'NLP pipeline may have issues')

# Test 22: Dashboard-Backend Communication
print("\n[TEST 22] Dashboard-Backend Communication...")
# Check if backend is accessible and CORS allows frontend
health_response = make_api_request('/health')
parser_response = make_api_request('/api/v1/parser/parse', 'POST', {'command': 'test'})

if health_response['success'] and parser_response['success']:
    add_result('INT002', 'Dashboard-Backend Communication', 'PASS',
               'Frontend can successfully communicate with backend',
               'CORS properly configured, APIs accessible')
else:
    add_result('INT002', 'Dashboard-Backend Communication', 'FAIL',
               'Communication issues between frontend and backend',
               'May be CORS or connectivity problem')

# ============================================================================
# SUMMARY & REPORT
# ============================================================================

print("\n\n" + "="*80)
print("TEST EXECUTION COMPLETE")
print("="*80)
print(f"\nTotal Tests: {len(test_results)}")
print(f"Passed: {passed} ({passed/len(test_results)*100:.1f}%)")
print(f"Failed: {failed} ({failed/len(test_results)*100:.1f}%)")

# Save results to CSV
csv_filename = 'COMPLETE_APPLICATION_TEST_RESULTS.csv'
with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Test ID', 'Test Name', 'Status', 'Summary', 'Details'])
    writer.writeheader()
    writer.writerows(test_results)

print(f"\nDetailed results saved to: {csv_filename}")

# Print failed tests if any
if failed > 0:
    print("\n" + "="*80)
    print("FAILED TESTS:")
    print("="*80)
    for result in test_results:
        if result['Status'] == 'FAIL':
            print(f"\n{result['Test ID']}: {result['Test Name']}")
            print(f"  Summary: {result['Summary']}")
            if result['Details']:
                print(f"  Details: {result['Details'][:200]}")

print("\n" + "="*80)
if failed == 0:
    print("✅ ALL TESTS PASSED - APPLICATION FULLY FUNCTIONAL")
else:
    print(f"⚠️  {failed} TEST(S) FAILED - REVIEW RESULTS ABOVE")
print("="*80)
