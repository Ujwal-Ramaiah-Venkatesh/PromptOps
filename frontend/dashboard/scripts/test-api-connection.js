/**
 * API Connection Test Script
 * ===========================
 *
 * Tests connection between React dashboard and FastAPI backend.
 *
 * Usage: node scripts/test-api-connection.js
 *
 * Author: PromptOps Team - Week 11-12
 * Date: 2026-04-29
 */

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

async function testHealthCheck() {
  console.log('\n🔍 Testing health check endpoint...');
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = await response.json();

    if (response.ok) {
      console.log('✅ Health check passed');
      console.log('   Status:', data.status);
      console.log('   Version:', data.version);
      console.log('   Services:', JSON.stringify(data.services, null, 2));
      return true;
    } else {
      console.log('❌ Health check failed:', response.status);
      return false;
    }
  } catch (error) {
    console.log('❌ Health check error:', error.message);
    return false;
  }
}

async function testParseIntent() {
  console.log('\n🔍 Testing parse-intent endpoint...');
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/parse-intent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        command: 'Deploy frontend v2.0 to staging',
        user: 'test@test.com'
      })
    });

    const data = await response.json();

    if (response.ok) {
      console.log('✅ Parse intent passed');
      console.log('   Intent type:', data.intent.intent_type);
      console.log('   Target service:', data.intent.target_service);
      console.log('   Target env:', data.intent.target_env);
      console.log('   Confidence:', data.intent.confidence);
      console.log('   Parse time:', data.parse_time_ms, 'ms');
      return true;
    } else {
      console.log('❌ Parse intent failed:', response.status);
      console.log('   Error:', data.detail);
      return false;
    }
  } catch (error) {
    console.log('❌ Parse intent error:', error.message);
    return false;
  }
}

async function testAuditTrail() {
  console.log('\n🔍 Testing audit trail endpoint...');
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/audit?limit=5`);
    const data = await response.json();

    if (response.ok) {
      console.log('✅ Audit trail passed');
      console.log('   Total entries:', data.total);
      console.log('   Returned:', data.entries.length);
      console.log('   Page:', data.page);
      return true;
    } else {
      console.log('❌ Audit trail failed:', response.status);
      console.log('   Error:', data.detail);
      return false;
    }
  } catch (error) {
    console.log('❌ Audit trail error:', error.message);
    return false;
  }
}

async function testDrift() {
  console.log('\n🔍 Testing drift endpoint...');
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/drift/recent`);
    const data = await response.json();

    if (response.ok) {
      console.log('✅ Drift endpoint passed');
      console.log('   Events:', data.events.length);
      console.log('   Unacknowledged:', data.unacknowledged_count);
      console.log('   Last check:', data.last_check);
      return true;
    } else {
      console.log('❌ Drift endpoint failed:', response.status);
      console.log('   Error:', data.detail);
      return false;
    }
  } catch (error) {
    console.log('❌ Drift endpoint error:', error.message);
    return false;
  }
}

async function runTests() {
  console.log('==========================================');
  console.log('  API Connection Test Suite');
  console.log('==========================================');
  console.log('  API Base URL:', API_BASE_URL);
  console.log('==========================================');

  const results = {
    health: await testHealthCheck(),
    parseIntent: await testParseIntent(),
    audit: await testAuditTrail(),
    drift: await testDrift()
  };

  console.log('\n==========================================');
  console.log('  Test Results');
  console.log('==========================================');
  console.log('  Health Check:', results.health ? '✅' : '❌');
  console.log('  Parse Intent:', results.parseIntent ? '✅' : '❌');
  console.log('  Audit Trail:', results.audit ? '✅' : '❌');
  console.log('  Drift Events:', results.drift ? '✅' : '❌');
  console.log('==========================================');

  const passed = Object.values(results).filter(r => r).length;
  const total = Object.keys(results).length;

  console.log(`\n  Passed: ${passed}/${total} tests`);

  if (passed === total) {
    console.log('\n  🎉 All tests passed! Dashboard is ready to connect.\n');
    process.exit(0);
  } else {
    console.log('\n  ⚠️  Some tests failed. Check API server logs.\n');
    process.exit(1);
  }
}

// Run tests
runTests().catch(error => {
  console.error('\n❌ Unexpected error:', error);
  process.exit(1);
});
