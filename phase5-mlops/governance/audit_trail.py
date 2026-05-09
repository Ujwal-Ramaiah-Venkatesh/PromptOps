"""
Audit Trail for PromptOps ML Governance
========================================

Comprehensive audit logging for ML operations.
Tracks all model actions for compliance (SOC2, GDPR, etc.).

Author: ML Engineer - Phase 5 Week 50-51
Date: 2026-05-09
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Audit Trail Enums
# ============================================================================

class EventType(Enum):
    """Audit event types."""
    MODEL_REGISTERED = "model_registered"
    MODEL_UPDATED = "model_updated"
    MODEL_DEPLOYED = "model_deployed"
    MODEL_DELETED = "model_deleted"
    STAGE_TRANSITION = "stage_transition"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    PREDICTION_MADE = "prediction_made"
    TRAINING_STARTED = "training_started"
    TRAINING_COMPLETED = "training_completed"
    TUNING_STARTED = "tuning_started"
    TUNING_COMPLETED = "tuning_completed"
    BIAS_CHECK = "bias_check"
    DRIFT_DETECTED = "drift_detected"
    INCIDENT_REPORTED = "incident_reported"


class Severity(Enum):
    """Event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# Audit Trail
# ============================================================================

class AuditTrail:
    """
    Comprehensive audit logging for ML operations.

    Features:
    - Event logging with structured data
    - Query and filtering
    - Compliance reporting
    - Event retention policies
    - Tamper-evident logging (hash chain)
    """

    def __init__(self, audit_path: str = "./audit_logs"):
        """Initialize Audit Trail."""
        self.audit_path = audit_path
        self.events: List[Dict[str, Any]] = []
        self.retention_days = 365  # 1 year retention
        self._ensure_audit_path_exists()
        self._load_events()

    def _ensure_audit_path_exists(self):
        """Ensure audit directory exists."""
        os.makedirs(self.audit_path, exist_ok=True)

    def _load_events(self):
        """Load audit events from disk."""
        audit_file = os.path.join(self.audit_path, "audit_trail.jsonl")
        if os.path.exists(audit_file):
            try:
                with open(audit_file, 'r') as f:
                    self.events = [json.loads(line) for line in f]
                logger.info(f"Loaded {len(self.events)} audit events")
            except Exception as e:
                logger.warning(f"Failed to load audit events: {e}")

    def _save_event(self, event: Dict[str, Any]):
        """Append event to audit log file."""
        audit_file = os.path.join(self.audit_path, "audit_trail.jsonl")
        try:
            with open(audit_file, 'a') as f:
                f.write(json.dumps(event, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to save audit event: {e}")

    def log_event(
        self,
        event_type: str,
        resource_type: str,
        resource_id: str,
        actor: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ) -> Dict[str, Any]:
        """
        Log an audit event.

        Args:
            event_type: Type of event (model_registered, prediction_made, etc.)
            resource_type: Type of resource (model, training_job, endpoint, etc.)
            resource_id: Unique identifier of resource
            actor: Username or service performing action
            action: Action description
            details: Additional event details
            severity: Event severity (info, warning, error, critical)

        Returns:
            Logged event
        """
        timestamp = datetime.utcnow()

        # Compute hash of previous event for tamper-evidence
        prev_hash = self._get_previous_hash()

        event = {
            "event_id": self._generate_event_id(timestamp),
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "actor": actor,
            "action": action,
            "details": details or {},
            "severity": severity,
            "previous_hash": prev_hash,
            "event_hash": None  # Will be computed after
        }

        # Compute hash of this event
        event["event_hash"] = self._compute_event_hash(event)

        # Add to memory and disk
        self.events.append(event)
        self._save_event(event)

        logger.info(f"Audit event logged: {event_type} - {resource_id}")
        return event

    def _generate_event_id(self, timestamp: datetime) -> str:
        """Generate unique event ID."""
        return f"evt_{int(timestamp.timestamp() * 1000000)}"

    def _get_previous_hash(self) -> str:
        """Get hash of previous event for chain."""
        if not self.events:
            return "genesis"
        return self.events[-1].get("event_hash", "unknown")

    def _compute_event_hash(self, event: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of event."""
        # Exclude event_hash field itself
        event_copy = {k: v for k, v in event.items() if k != "event_hash"}
        event_str = json.dumps(event_copy, sort_keys=True, default=str)
        return hashlib.sha256(event_str.encode()).hexdigest()[:16]

    def query_events(
        self,
        event_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        actor: Optional[str] = None,
        severity: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query audit events with filters.

        Args:
            event_type: Filter by event type
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            actor: Filter by actor
            severity: Filter by severity
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum results

        Returns:
            List of matching events
        """
        results = []

        for event in reversed(self.events):  # Most recent first
            # Apply filters
            if event_type and event.get("event_type") != event_type:
                continue
            if resource_type and event.get("resource_type") != resource_type:
                continue
            if resource_id and event.get("resource_id") != resource_id:
                continue
            if actor and event.get("actor") != actor:
                continue
            if severity and event.get("severity") != severity:
                continue

            # Time filters
            event_time = datetime.fromisoformat(event["timestamp"])
            if start_time and event_time < start_time:
                continue
            if end_time and event_time > end_time:
                continue

            results.append(event)

            if len(results) >= limit:
                break

        return results

    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get complete audit history for a resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource ID

        Returns:
            Chronological list of events
        """
        events = self.query_events(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=10000
        )

        # Return chronological order
        return list(reversed(events))

    def get_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate compliance report for given time period.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance report with statistics
        """
        logger.info(f"Generating compliance report: {start_date} to {end_date}")

        events = self.query_events(
            start_time=start_date,
            end_time=end_date,
            limit=100000
        )

        # Event statistics
        event_counts = {}
        severity_counts = {}
        actor_counts = {}

        for event in events:
            # Count by type
            event_type = event.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            # Count by severity
            severity = event.get("severity", "info")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Count by actor
            actor = event.get("actor", "unknown")
            actor_counts[actor] = actor_counts.get(actor, 0) + 1

        # High severity events
        high_severity = [e for e in events if e.get("severity") in ["error", "critical"]]

        report = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "total_events": len(events),
            "events_by_type": event_counts,
            "events_by_severity": severity_counts,
            "events_by_actor": actor_counts,
            "high_severity_events": len(high_severity),
            "high_severity_details": high_severity[:20],  # Top 20
            "unique_models": len(set(e["resource_id"] for e in events if e["resource_type"] == "model")),
            "unique_actors": len(actor_counts)
        }

        return report

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify integrity of audit trail using hash chain.

        Returns:
            Integrity verification result
        """
        logger.info("Verifying audit trail integrity...")

        if not self.events:
            return {"valid": True, "message": "No events to verify"}

        violations = []
        prev_hash = "genesis"

        for idx, event in enumerate(self.events):
            # Check previous hash matches
            if event.get("previous_hash") != prev_hash:
                violations.append({
                    "event_id": event.get("event_id"),
                    "index": idx,
                    "issue": "Previous hash mismatch"
                })

            # Recompute event hash
            computed_hash = self._compute_event_hash(event)
            if event.get("event_hash") != computed_hash:
                violations.append({
                    "event_id": event.get("event_id"),
                    "index": idx,
                    "issue": "Event hash mismatch (potential tampering)"
                })

            prev_hash = event.get("event_hash")

        valid = len(violations) == 0

        return {
            "valid": valid,
            "total_events": len(self.events),
            "violations": violations,
            "message": "Audit trail integrity verified" if valid else f"Found {len(violations)} integrity violations"
        }

    def cleanup_old_events(self, retention_days: Optional[int] = None):
        """
        Remove events older than retention period.

        Args:
            retention_days: Optional custom retention (uses default if not provided)
        """
        retention = retention_days or self.retention_days
        cutoff_date = datetime.utcnow() - timedelta(days=retention)

        logger.info(f"Cleaning up events older than {cutoff_date}")

        original_count = len(self.events)
        self.events = [
            e for e in self.events
            if datetime.fromisoformat(e["timestamp"]) >= cutoff_date
        ]

        removed = original_count - len(self.events)
        logger.info(f"Removed {removed} old events")

        return {"removed": removed, "remaining": len(self.events)}


# ============================================================================
# Testing
# ============================================================================

def test_audit_trail():
    """Test audit trail."""
    logger.info("Testing Audit Trail...")

    audit = AuditTrail(audit_path="./test_audit_logs")

    # Test 1: Log model registration
    print("\n=== Test 1: Log Model Registration ===")
    event1 = audit.log_event(
        event_type=EventType.MODEL_REGISTERED.value,
        resource_type="model",
        resource_id="churn-prediction:v2",
        actor="ml_engineer_1",
        action="Registered new model version",
        details={"metrics": {"accuracy": 0.92}, "framework": "xgboost"},
        severity=Severity.INFO.value
    )
    print(json.dumps(event1, indent=2, default=str))

    # Test 2: Log stage transition
    print("\n=== Test 2: Log Stage Transition ===")
    event2 = audit.log_event(
        event_type=EventType.STAGE_TRANSITION.value,
        resource_type="model",
        resource_id="churn-prediction:v2",
        actor="ml_lead",
        action="Promoted to Staging",
        details={"from_stage": "Development", "to_stage": "Staging"},
        severity=Severity.INFO.value
    )
    print(json.dumps(event2, indent=2, default=str))

    # Test 3: Log deployment
    print("\n=== Test 3: Log Model Deployment ===")
    event3 = audit.log_event(
        event_type=EventType.MODEL_DEPLOYED.value,
        resource_type="model",
        resource_id="churn-prediction:v2",
        actor="devops_engineer",
        action="Deployed to production endpoint",
        details={"endpoint": "churn-prod", "instance": "ml.m5.xlarge"},
        severity=Severity.INFO.value
    )
    print(json.dumps(event3, indent=2, default=str))

    # Test 4: Query events
    print("\n=== Test 4: Query Events ===")
    model_events = audit.query_events(resource_id="churn-prediction:v2")
    print(f"Found {len(model_events)} events for churn-prediction:v2")

    # Test 5: Get resource history
    print("\n=== Test 5: Resource History ===")
    history = audit.get_resource_history(
        resource_type="model",
        resource_id="churn-prediction:v2"
    )
    print(f"Resource has {len(history)} events")
    for event in history:
        print(f"  - {event['timestamp']}: {event['action']}")

    # Test 6: Compliance report
    print("\n=== Test 6: Compliance Report ===")
    report = audit.get_compliance_report(
        start_date=datetime.utcnow() - timedelta(days=30),
        end_date=datetime.utcnow()
    )
    print(json.dumps(report, indent=2, default=str))

    # Test 7: Verify integrity
    print("\n=== Test 7: Verify Integrity ===")
    integrity = audit.verify_integrity()
    print(json.dumps(integrity, indent=2))


if __name__ == "__main__":
    test_audit_trail()
