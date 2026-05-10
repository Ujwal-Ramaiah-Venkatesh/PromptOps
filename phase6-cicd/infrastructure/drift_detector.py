"""
Infrastructure Drift Detector for PromptOps
============================================

Detects and analyzes infrastructure configuration drift.
Compares desired state with actual cloud resources.

Author: DevOps Engineer - Phase 6 Week 60-61
Date: 2026-05-10
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class DriftType(Enum):
    """Types of drift."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    NO_DRIFT = "no_drift"


class DriftSeverity(Enum):
    """Drift severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# Drift Detector
# ============================================================================

class DriftDetector:
    """
    Infrastructure drift detector.

    Features:
    - Resource drift detection
    - Configuration change tracking
    - Severity assessment
    - Auto-remediation suggestions
    - Drift reporting
    - Continuous monitoring
    """

    def __init__(self):
        """Initialize Drift Detector."""
        self.drift_history = []

    def detect_drift(
        self,
        desired_state: Dict[str, Any],
        actual_state: Dict[str, Any],
        resource_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect infrastructure drift.

        Args:
            desired_state: Desired infrastructure state
            actual_state: Actual infrastructure state
            resource_type: Filter by resource type

        Returns:
            Drift detection result
        """
        logger.info("Detecting infrastructure drift")

        drift_items = []

        desired_resources = desired_state.get("resources", {})
        actual_resources = actual_state.get("resources", {})

        # Detect added resources
        for resource_id, resource_data in actual_resources.items():
            if resource_id not in desired_resources:
                if not resource_type or resource_data.get("type") == resource_type:
                    drift_items.append({
                        "drift_type": DriftType.ADDED.value,
                        "resource_id": resource_id,
                        "resource_type": resource_data.get("type"),
                        "severity": self._assess_severity(DriftType.ADDED, resource_data),
                        "actual": resource_data,
                        "message": f"Resource {resource_id} exists but not in desired state"
                    })

        # Detect removed resources
        for resource_id, resource_data in desired_resources.items():
            if resource_id not in actual_resources:
                if not resource_type or resource_data.get("type") == resource_type:
                    drift_items.append({
                        "drift_type": DriftType.REMOVED.value,
                        "resource_id": resource_id,
                        "resource_type": resource_data.get("type"),
                        "severity": self._assess_severity(DriftType.REMOVED, resource_data),
                        "desired": resource_data,
                        "message": f"Resource {resource_id} missing from actual state"
                    })

        # Detect modified resources
        for resource_id in desired_resources:
            if resource_id in actual_resources:
                desired_res = desired_resources[resource_id]
                actual_res = actual_resources[resource_id]

                if resource_type and desired_res.get("type") != resource_type:
                    continue

                changes = self._compare_resources(desired_res, actual_res)

                if changes:
                    drift_items.append({
                        "drift_type": DriftType.MODIFIED.value,
                        "resource_id": resource_id,
                        "resource_type": desired_res.get("type"),
                        "severity": self._assess_severity(DriftType.MODIFIED, desired_res, changes),
                        "desired": desired_res,
                        "actual": actual_res,
                        "changes": changes,
                        "message": f"Resource {resource_id} has {len(changes)} configuration change(s)"
                    })

        # Calculate summary
        has_drift = len(drift_items) > 0

        summary = {
            "total_drift_items": len(drift_items),
            "by_type": self._count_by_type(drift_items),
            "by_severity": self._count_by_severity(drift_items),
            "critical_count": len([d for d in drift_items if d["severity"] == "critical"]),
            "high_count": len([d for d in drift_items if d["severity"] == "high"])
        }

        result = {
            "has_drift": has_drift,
            "drift_items": drift_items,
            "summary": summary,
            "detected_at": datetime.utcnow().isoformat()
        }

        # Add to history
        self.drift_history.append(result)

        return result

    def _compare_resources(
        self,
        desired: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Compare two resources and find differences."""
        changes = []

        # Compare attributes
        desired_attrs = desired.get("attributes", {})
        actual_attrs = actual.get("attributes", {})

        all_keys = set(desired_attrs.keys()) | set(actual_attrs.keys())

        for key in all_keys:
            desired_value = desired_attrs.get(key)
            actual_value = actual_attrs.get(key)

            if desired_value != actual_value:
                changes.append({
                    "attribute": key,
                    "desired": desired_value,
                    "actual": actual_value,
                    "change_type": "modified" if key in desired_attrs and key in actual_attrs else ("added" if key in actual_attrs else "removed")
                })

        return changes

    def _assess_severity(
        self,
        drift_type: DriftType,
        resource_data: Dict[str, Any],
        changes: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Assess drift severity."""
        resource_type = resource_data.get("type", "")

        # Critical resources
        critical_types = ["database", "security_group", "iam_role", "kms_key"]
        if any(ct in resource_type.lower() for ct in critical_types):
            if drift_type == DriftType.REMOVED:
                return DriftSeverity.CRITICAL.value
            elif drift_type == DriftType.MODIFIED:
                # Check if security-related attributes changed
                if changes:
                    security_attrs = ["security", "encryption", "public", "policy", "permission"]
                    for change in changes:
                        if any(attr in change["attribute"].lower() for attr in security_attrs):
                            return DriftSeverity.CRITICAL.value
                return DriftSeverity.HIGH.value
            else:
                return DriftSeverity.HIGH.value

        # High severity resources
        high_types = ["compute", "network", "load_balancer", "storage"]
        if any(ht in resource_type.lower() for ht in high_types):
            if drift_type == DriftType.REMOVED:
                return DriftSeverity.HIGH.value
            else:
                return DriftSeverity.MEDIUM.value

        # Default severity
        if drift_type == DriftType.REMOVED:
            return DriftSeverity.MEDIUM.value
        else:
            return DriftSeverity.LOW.value

    def _count_by_type(self, drift_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count drift items by type."""
        counts = {
            "added": 0,
            "removed": 0,
            "modified": 0
        }

        for item in drift_items:
            drift_type = item["drift_type"]
            counts[drift_type] = counts.get(drift_type, 0) + 1

        return counts

    def _count_by_severity(self, drift_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count drift items by severity."""
        counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }

        for item in drift_items:
            severity = item["severity"]
            counts[severity] = counts.get(severity, 0) + 1

        return counts

    def generate_remediation_plan(
        self,
        drift_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate remediation plan for detected drift.

        Args:
            drift_result: Drift detection result

        Returns:
            Remediation plan
        """
        logger.info("Generating drift remediation plan")

        remediation_actions = []

        for drift_item in drift_result.get("drift_items", []):
            drift_type = drift_item["drift_type"]
            resource_id = drift_item["resource_id"]
            resource_type = drift_item["resource_type"]

            if drift_type == "added":
                action = {
                    "action": "remove",
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "priority": self._get_priority(drift_item["severity"]),
                    "command": f"terraform destroy -target={resource_id}",
                    "description": f"Remove unexpected resource {resource_id}"
                }
            elif drift_type == "removed":
                action = {
                    "action": "create",
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "priority": self._get_priority(drift_item["severity"]),
                    "command": f"terraform apply -target={resource_id}",
                    "description": f"Recreate missing resource {resource_id}"
                }
            else:  # modified
                action = {
                    "action": "update",
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "priority": self._get_priority(drift_item["severity"]),
                    "command": f"terraform apply -target={resource_id}",
                    "changes": drift_item.get("changes", []),
                    "description": f"Update drifted resource {resource_id}"
                }

            remediation_actions.append(action)

        # Sort by priority
        remediation_actions.sort(key=lambda x: x["priority"])

        return {
            "total_actions": len(remediation_actions),
            "actions": remediation_actions,
            "estimated_duration_minutes": len(remediation_actions) * 5,
            "generated_at": datetime.utcnow().isoformat()
        }

    def _get_priority(self, severity: str) -> int:
        """Convert severity to priority (lower is higher priority)."""
        priority_map = {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4
        }
        return priority_map.get(severity, 5)

    def get_drift_trends(self) -> Dict[str, Any]:
        """
        Analyze drift trends over time.

        Returns:
            Drift trends
        """
        logger.info("Analyzing drift trends")

        if not self.drift_history:
            return {
                "status": "no_data",
                "message": "No drift history available"
            }

        total_scans = len(self.drift_history)
        scans_with_drift = sum(1 for scan in self.drift_history if scan["has_drift"])

        # Calculate average drift items
        total_drift_items = sum(scan["summary"]["total_drift_items"] for scan in self.drift_history)
        avg_drift_items = total_drift_items / total_scans if total_scans > 0 else 0

        # Get latest scan
        latest_scan = self.drift_history[-1]

        return {
            "total_scans": total_scans,
            "scans_with_drift": scans_with_drift,
            "drift_rate": round((scans_with_drift / total_scans * 100), 2) if total_scans > 0 else 0,
            "avg_drift_items": round(avg_drift_items, 2),
            "latest_scan": {
                "has_drift": latest_scan["has_drift"],
                "total_drift_items": latest_scan["summary"]["total_drift_items"],
                "critical_count": latest_scan["summary"]["critical_count"],
                "detected_at": latest_scan["detected_at"]
            }
        }

    def generate_drift_report(
        self,
        drift_result: Dict[str, Any],
        format: str = "json"
    ) -> str:
        """
        Generate drift report.

        Args:
            drift_result: Drift detection result
            format: Report format (json, markdown)

        Returns:
            Formatted report
        """
        if format == "markdown":
            return self._generate_markdown_report(drift_result)
        else:
            return json.dumps(drift_result, indent=2)

    def _generate_markdown_report(self, drift_result: Dict[str, Any]) -> str:
        """Generate markdown-formatted report."""
        lines = []

        lines.append("# Infrastructure Drift Report")
        lines.append("")
        lines.append(f"**Detected At:** {drift_result['detected_at']}")
        lines.append(f"**Has Drift:** {drift_result['has_drift']}")
        lines.append("")

        summary = drift_result["summary"]
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Total Drift Items: {summary['total_drift_items']}")
        lines.append(f"- Critical: {summary['critical_count']}")
        lines.append(f"- High: {summary['high_count']}")
        lines.append("")

        lines.append("### By Type")
        for drift_type, count in summary["by_type"].items():
            lines.append(f"- {drift_type.title()}: {count}")
        lines.append("")

        if drift_result["has_drift"]:
            lines.append("## Drift Items")
            lines.append("")

            for item in drift_result["drift_items"]:
                lines.append(f"### {item['resource_id']}")
                lines.append(f"- **Type:** {item['resource_type']}")
                lines.append(f"- **Drift Type:** {item['drift_type']}")
                lines.append(f"- **Severity:** {item['severity']}")
                lines.append(f"- **Message:** {item['message']}")
                lines.append("")

        return "\n".join(lines)


# ============================================================================
# Testing
# ============================================================================

def test_drift_detector():
    """Test Drift Detector."""
    logger.info("Testing Drift Detector...")

    detector = DriftDetector()

    # Test 1: Detect drift
    print("\n=== Test 1: Detect Drift ===")
    desired_state = {
        "resources": {
            "aws_instance.web": {
                "type": "aws_instance",
                "attributes": {
                    "instance_type": "t3.micro",
                    "ami": "ami-12345"
                }
            },
            "aws_s3_bucket.data": {
                "type": "aws_s3_bucket",
                "attributes": {
                    "versioning": True,
                    "encryption": True
                }
            }
        }
    }

    actual_state = {
        "resources": {
            "aws_instance.web": {
                "type": "aws_instance",
                "attributes": {
                    "instance_type": "t3.small",  # Changed
                    "ami": "ami-12345"
                }
            },
            "aws_rds_instance.db": {  # Added
                "type": "aws_rds_instance",
                "attributes": {
                    "engine": "postgres"
                }
            }
            # aws_s3_bucket.data is removed
        }
    }

    drift_result = detector.detect_drift(desired_state, actual_state)
    print(f"Has Drift: {drift_result['has_drift']}")
    print(f"Total Items: {drift_result['summary']['total_drift_items']}")
    print(f"By Type: {drift_result['summary']['by_type']}")
    print(f"By Severity: {drift_result['summary']['by_severity']}")

    # Test 2: Generate remediation plan
    print("\n=== Test 2: Remediation Plan ===")
    plan = detector.generate_remediation_plan(drift_result)
    print(f"Total Actions: {plan['total_actions']}")
    print(f"Estimated Duration: {plan['estimated_duration_minutes']} minutes")
    for action in plan["actions"][:2]:
        print(f"  - {action['action'].upper()}: {action['resource_id']} (priority: {action['priority']})")

    # Test 3: Drift trends
    print("\n=== Test 3: Drift Trends ===")
    trends = detector.get_drift_trends()
    print(f"Total Scans: {trends['total_scans']}")
    print(f"Drift Rate: {trends['drift_rate']}%")
    print(f"Avg Drift Items: {trends['avg_drift_items']}")


if __name__ == "__main__":
    test_drift_detector()
