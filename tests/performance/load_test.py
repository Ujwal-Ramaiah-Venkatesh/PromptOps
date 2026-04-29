"""
Performance Load Testing
========================

Load testing for PromptOps API Gateway using Locust.

Test Scenarios:
1. Concurrent intent parsing
2. Decomposition under load
3. Audit trail queries
4. Mixed workload

Usage:
    locust -f load_test.py --host=http://localhost:8000

Author: PromptOps Team - Week 11-12
Date: 2026-04-29
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import random
import time
import json

# ============================================================================
# Test Data
# ============================================================================

TEST_COMMANDS = [
    "Deploy frontend v2.0 to staging",
    "Deploy api v1.5 to production",
    "Scale backend to 10 instances",
    "Rollback frontend to previous version",
    "Show me current AWS spending",
    "Deploy frontend v3.0 to staging with canary rollout",
    "Scale api-service to 5 instances",
    "Rollback api to version v2.1.0",
]

TEST_USERS = [
    "pm1@company.com",
    "pm2@company.com",
    "pm3@company.com",
    "admin@company.com",
]

# ============================================================================
# Performance Metrics Tracker
# ============================================================================

class MetricsTracker:
    def __init__(self):
        self.response_times = {
            "parse": [],
            "decompose": [],
            "audit": [],
        }

    def add(self, endpoint: str, response_time: float):
        if endpoint in self.response_times:
            self.response_times[endpoint].append(response_time)

    def get_stats(self):
        stats = {}
        for endpoint, times in self.response_times.items():
            if times:
                times.sort()
                stats[endpoint] = {
                    "count": len(times),
                    "min": min(times),
                    "max": max(times),
                    "avg": sum(times) / len(times),
                    "p50": times[len(times) // 2],
                    "p95": times[int(len(times) * 0.95)],
                    "p99": times[int(len(times) * 0.99)],
                }
        return stats

metrics_tracker = MetricsTracker()

# ============================================================================
# Base User Class
# ============================================================================

class DashboardUser(HttpUser):
    """
    Simulates a PM using the dashboard.

    Wait time: 1-3 seconds between requests (simulates thinking time)
    """

    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def on_start(self):
        """Called when a user starts."""
        self.user_email = random.choice(TEST_USERS)

    @task(5)
    def parse_intent(self):
        """
        Parse natural language command (weighted 5x).

        Most common operation in dashboard.
        """
        command = random.choice(TEST_COMMANDS)

        with self.client.post(
            "/api/v1/parse-intent",
            json={"command": command, "user": self.user_email},
            catch_response=True,
            name="/api/v1/parse-intent"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                parse_time = data.get("parse_time_ms", 0)
                metrics_tracker.add("parse", parse_time)

                if data["intent"]["confidence"] > 0.7:
                    response.success()
                else:
                    response.failure(f"Low confidence: {data['intent']['confidence']}")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    def decompose_task(self):
        """
        Decompose intent into tasks (weighted 2x).

        Requires successful parse first.
        """
        command = random.choice(TEST_COMMANDS)

        # Step 1: Parse
        parse_response = self.client.post(
            "/api/v1/parse-intent",
            json={"command": command, "user": self.user_email},
            name="/api/v1/parse-intent [decompose]"
        )

        if parse_response.status_code != 200:
            return

        intent = parse_response.json()["intent"]

        # Step 2: Decompose
        with self.client.post(
            "/api/v1/decompose",
            json={"intent": intent, "user": self.user_email},
            catch_response=True,
            name="/api/v1/decompose"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                decompose_time = data.get("decompose_time_ms", 0)
                metrics_tracker.add("decompose", decompose_time)

                if data["decomposition"]["total_sub_tasks"] > 0:
                    response.success()
                else:
                    response.failure("No sub-tasks generated")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(3)
    def get_audit_trail(self):
        """
        Query audit trail (weighted 3x).

        Common operation for monitoring.
        """
        # Random filters
        params = {"limit": 10}

        if random.random() < 0.3:
            params["user"] = self.user_email

        if random.random() < 0.2:
            params["env"] = random.choice(["production", "staging"])

        with self.client.get(
            "/api/v1/audit",
            params=params,
            catch_response=True,
            name="/api/v1/audit"
        ) as response:
            if response.status_code == 200:
                metrics_tracker.add("audit", response.elapsed.total_seconds() * 1000)
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def get_drift(self):
        """
        Get drift events (weighted 1x).

        Periodic check for infrastructure drift.
        """
        self.client.get(
            "/api/v1/drift/recent",
            name="/api/v1/drift/recent"
        )

    @task(1)
    def health_check(self):
        """
        Health check (weighted 1x).

        Periodic monitoring.
        """
        self.client.get("/health", name="/health")

# ============================================================================
# Heavy Load User (Stress Testing)
# ============================================================================

class HeavyLoadUser(HttpUser):
    """
    Simulates heavy load with minimal wait time.

    Used for stress testing to find breaking points.
    """

    wait_time = between(0.1, 0.5)  # Very short wait time
    host = "http://localhost:8000"

    def on_start(self):
        self.user_email = random.choice(TEST_USERS)

    @task
    def rapid_fire_parse(self):
        """Rapid-fire intent parsing."""
        command = random.choice(TEST_COMMANDS)

        self.client.post(
            "/api/v1/parse-intent",
            json={"command": command, "user": self.user_email},
            name="/api/v1/parse-intent [heavy]"
        )

# ============================================================================
# Read-Only User (Audit Queries)
# ============================================================================

class ReadOnlyUser(HttpUser):
    """
    Simulates read-only users (reporting, monitoring).

    Only queries audit trail and drift events.
    """

    wait_time = between(2, 5)
    host = "http://localhost:8000"

    def on_start(self):
        self.user_email = random.choice(TEST_USERS)

    @task(5)
    def query_audit(self):
        """Query audit trail with various filters."""
        filters = [
            {"limit": 50},
            {"limit": 20, "status": "completed"},
            {"limit": 10, "env": "production"},
            {"limit": 30, "user": self.user_email},
        ]

        params = random.choice(filters)

        self.client.get(
            "/api/v1/audit",
            params=params,
            name="/api/v1/audit [readonly]"
        )

    @task(2)
    def check_drift(self):
        """Check for drift events."""
        self.client.get(
            "/api/v1/drift/recent",
            name="/api/v1/drift/recent [readonly]"
        )

    @task(1)
    def export_audit(self):
        """Export audit trail (expensive operation)."""
        self.client.get(
            "/api/v1/audit/export?format=csv",
            name="/api/v1/audit/export"
        )

# ============================================================================
# Event Handlers
# ============================================================================

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print custom metrics when test stops."""
    print("\n" + "="*60)
    print("Custom Performance Metrics")
    print("="*60)

    stats = metrics_tracker.get_stats()

    for endpoint, metrics in stats.items():
        print(f"\n{endpoint.upper()}:")
        print(f"  Count:   {metrics['count']}")
        print(f"  Min:     {metrics['min']:.0f} ms")
        print(f"  Max:     {metrics['max']:.0f} ms")
        print(f"  Avg:     {metrics['avg']:.0f} ms")
        print(f"  P50:     {metrics['p50']:.0f} ms")
        print(f"  P95:     {metrics['p95']:.0f} ms")
        print(f"  P99:     {metrics['p99']:.0f} ms")

    print("\n" + "="*60)

    # Check performance targets
    print("\nPerformance Target Status:")
    print("="*60)

    targets = {
        "parse": 500,      # <500ms p95
        "decompose": 2000, # <2s p95
        "audit": 200,      # <200ms p95
    }

    all_pass = True

    for endpoint, target_ms in targets.items():
        if endpoint in stats:
            actual_p95 = stats[endpoint]["p95"]
            status = "✓ PASS" if actual_p95 < target_ms else "✗ FAIL"
            print(f"{endpoint.upper():12} Target: {target_ms}ms | Actual: {actual_p95:.0f}ms | {status}")

            if actual_p95 >= target_ms:
                all_pass = False
        else:
            print(f"{endpoint.upper():12} No data")

    print("="*60)

    if all_pass:
        print("\n🎉 All performance targets met!")
    else:
        print("\n⚠️  Some performance targets not met. Review and optimize.")

# ============================================================================
# Custom Load Shape (Optional)
# ============================================================================

from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """
    Load shape that increases users in steps.

    Useful for finding breaking point.
    """

    step_time = 60  # 60 seconds per step
    step_load = 10  # Add 10 users per step
    spawn_rate = 2  # Spawn 2 users per second
    time_limit = 600  # 10 minutes total

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = run_time // self.step_time
        user_count = int(current_step + 1) * self.step_load

        return (user_count, self.spawn_rate)

# ============================================================================
# Usage Instructions
# ============================================================================

"""
Usage Examples:

1. Basic load test (50 users):
   locust -f load_test.py --host=http://localhost:8000 --users 50 --spawn-rate 10 --run-time 5m

2. Web UI (interactive):
   locust -f load_test.py --host=http://localhost:8000
   # Open http://localhost:8089

3. Heavy stress test:
   locust -f load_test.py --host=http://localhost:8000 --user-classes HeavyLoadUser --users 100 --spawn-rate 20

4. Read-only load:
   locust -f load_test.py --host=http://localhost:8000 --user-classes ReadOnlyUser --users 50

5. Step load (find breaking point):
   locust -f load_test.py --host=http://localhost:8000 --headless

6. Export results:
   locust -f load_test.py --host=http://localhost:8000 --users 50 --run-time 5m --html report.html
"""
