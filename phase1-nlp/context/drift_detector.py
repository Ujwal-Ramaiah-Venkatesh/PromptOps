"""
Drift Detector - Configuration Change Detection
================================================

Detects infrastructure drift by comparing snapshots over time.
Categorizes changes by severity and identifies change attribution.

Features:
- Snapshot comparison (current vs. previous)
- Field-level diff detection
- Severity categorization (critical/warning/info)
- Change attribution via CloudTrail (optional)
- Ignore expected changes (auto-scaling, task restarts)

Author: PromptOps Team - Week 7-8
Date: 2026-04-28
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class DriftSeverity(Enum):
    """Drift severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ChangeSource(Enum):
    """How the change was made."""
    MANUAL = "manual"
    CONSOLE = "console"
    API = "api"
    CLOUDFORMATION = "cloudformation"
    PROMPTOPS = "promptops"
    AUTO_SCALING = "auto_scaling"
    UNKNOWN = "unknown"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class DriftEvent:
    """Individual drift event."""
    drift_id: str
    resource_id: str
    resource_type: str
    field_changed: str
    old_value: Any
    new_value: Any
    severity: str
    detected_at: str
    change_source: str
    changed_by: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class DriftReport:
    """Complete drift report for a snapshot comparison."""
    snapshot_id: str
    timestamp: str
    total_drift_events: int
    critical_count: int
    warning_count: int
    info_count: int
    drift_events: List[DriftEvent]
    resources_with_drift: List[str]
    new_resources: List[str]
    deleted_resources: List[str]


# ============================================================================
# Drift Detector
# ============================================================================

class DriftDetector:
    """
    Detects configuration drift between infrastructure snapshots.

    Workflow:
    1. Load current and previous snapshots
    2. Compare resources field-by-field
    3. Categorize drift severity
    4. Attribute changes to source
    5. Generate drift report
    """

    # Fields to ignore for drift detection (expected to change)
    IGNORED_FIELDS = {
        'last_snapshot',
        'last_updated',
        'metadata',
        'drift_status'
    }

    # Fields that trigger critical severity
    CRITICAL_FIELDS = {
        'security_groups',
        'public_ip',
        'encryption_enabled',
        'multi_az',
        'backup_retention_period',
        'status',  # For databases
        'state'   # For instances going to terminated
    }

    # Expected transient changes (don't alert)
    EXPECTED_CHANGES = {
        'ecs_service': {
            'pending_count',  # Tasks starting/stopping
            'running_count'   # May fluctuate slightly
        },
        'ec2_instance': {
            'monitoring'  # Can be toggled
        }
    }

    def __init__(
        self,
        context_store_path: str = './context_snapshots',
        enable_cloudtrail: bool = False
    ):
        """
        Initialize Drift Detector.

        Args:
            context_store_path: Path to context snapshots
            enable_cloudtrail: Enable CloudTrail lookup for change attribution
        """
        self.context_store_path = context_store_path
        self.enable_cloudtrail = enable_cloudtrail

        logger.info(f"DriftDetector initialized: cloudtrail={'enabled' if enable_cloudtrail else 'disabled'}")

    # ========================================================================
    # Main Detection Methods
    # ========================================================================

    def detect_drift(
        self,
        current_snapshot_id: Optional[str] = None,
        previous_snapshot_id: Optional[str] = None
    ) -> DriftReport:
        """
        Detect drift between two snapshots.

        Args:
            current_snapshot_id: ID of current snapshot (latest if None)
            previous_snapshot_id: ID of previous snapshot (second-latest if None)

        Returns:
            DriftReport with all detected changes
        """
        # Load snapshots
        current_snapshot = self._load_snapshot(current_snapshot_id)
        previous_snapshot = self._load_snapshot(previous_snapshot_id, offset=1)

        if not current_snapshot:
            raise ValueError("Current snapshot not found")

        if not previous_snapshot:
            logger.warning("No previous snapshot for comparison")
            return self._empty_report(current_snapshot)

        logger.info(f"Comparing snapshots: {previous_snapshot.get('snapshots', [{}])[0].get('snapshot_id')} → "
                   f"{current_snapshot.get('snapshots', [{}])[0].get('snapshot_id')}")

        # Get resource lists
        current_resources = {r['resource_id']: r for r in current_snapshot.get('resources', [])}
        previous_resources = {r['resource_id']: r for r in previous_snapshot.get('resources', [])}

        # Detect changes
        drift_events = []
        resources_with_drift = set()

        # Compare existing resources
        for resource_id, current_resource in current_resources.items():
            if resource_id not in previous_resources:
                continue  # New resource, handled separately

            previous_resource = previous_resources[resource_id]
            resource_events = self.compare_resources(current_resource, previous_resource)

            if resource_events:
                drift_events.extend(resource_events)
                resources_with_drift.add(resource_id)

        # Detect new resources
        new_resources = [rid for rid in current_resources if rid not in previous_resources]

        # Detect deleted resources
        deleted_resources = [rid for rid in previous_resources if rid not in current_resources]

        # Categorize by severity
        critical_count = sum(1 for e in drift_events if e.severity == DriftSeverity.CRITICAL.value)
        warning_count = sum(1 for e in drift_events if e.severity == DriftSeverity.WARNING.value)
        info_count = sum(1 for e in drift_events if e.severity == DriftSeverity.INFO.value)

        # Create report
        snapshot_id = current_snapshot.get('snapshots', [{}])[0].get('snapshot_id', 'unknown')
        timestamp = current_snapshot.get('last_updated', datetime.now(timezone.utc).isoformat())

        report = DriftReport(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            total_drift_events=len(drift_events),
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            drift_events=drift_events,
            resources_with_drift=list(resources_with_drift),
            new_resources=new_resources,
            deleted_resources=deleted_resources
        )

        logger.info(f"✓ Drift detection complete: {len(drift_events)} events "
                   f"(critical={critical_count}, warning={warning_count}, info={info_count})")

        return report

    def compare_resources(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any]
    ) -> List[DriftEvent]:
        """
        Compare two versions of the same resource.

        Args:
            current: Current resource state
            previous: Previous resource state

        Returns:
            List of drift events
        """
        drift_events = []
        resource_id = current['resource_id']
        resource_type = current['resource_type']

        # Compare current_state fields
        current_state = current.get('current_state', {})
        previous_state = previous.get('current_state', {})

        for field, current_value in current_state.items():
            if field in self.IGNORED_FIELDS:
                continue

            # Check if field is expected to change
            if self._is_expected_change(resource_type, field):
                continue

            previous_value = previous_state.get(field)

            if current_value != previous_value:
                # Detect drift
                drift_event = self._create_drift_event(
                    resource_id=resource_id,
                    resource_type=resource_type,
                    field_changed=field,
                    old_value=previous_value,
                    new_value=current_value
                )

                drift_events.append(drift_event)

        # Compare tags (only major changes)
        current_tags = current.get('tags', {})
        previous_tags = previous.get('tags', {})

        for tag_key in ['Environment', 'Managed', 'CostCenter']:
            if current_tags.get(tag_key) != previous_tags.get(tag_key):
                drift_event = self._create_drift_event(
                    resource_id=resource_id,
                    resource_type=resource_type,
                    field_changed=f'tag_{tag_key}',
                    old_value=previous_tags.get(tag_key),
                    new_value=current_tags.get(tag_key)
                )
                drift_events.append(drift_event)

        return drift_events

    def _create_drift_event(
        self,
        resource_id: str,
        resource_type: str,
        field_changed: str,
        old_value: Any,
        new_value: Any
    ) -> DriftEvent:
        """Create a drift event with severity categorization."""
        # Generate drift ID
        timestamp = datetime.now(timezone.utc)
        drift_id = f"drift-{timestamp.strftime('%Y%m%d%H%M%S')}-{resource_id[:8]}-{field_changed}"

        # Categorize severity
        severity = self.categorize_drift(resource_type, field_changed, old_value, new_value)

        # Detect change source
        change_source = self._detect_change_source(resource_id, resource_type, field_changed)

        # Generate reason
        reason = self._generate_reason(field_changed, old_value, new_value)

        return DriftEvent(
            drift_id=drift_id,
            resource_id=resource_id,
            resource_type=resource_type,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value,
            severity=severity.value,
            detected_at=timestamp.isoformat(),
            change_source=change_source.value,
            changed_by=None,  # Would come from CloudTrail
            reason=reason
        )

    # ========================================================================
    # Severity Categorization
    # ========================================================================

    def categorize_drift(
        self,
        resource_type: str,
        field_changed: str,
        old_value: Any,
        new_value: Any
    ) -> DriftSeverity:
        """
        Categorize drift severity.

        Critical:
        - Security changes (security groups, encryption)
        - Database going offline
        - Production instance termination
        - Multi-AZ disabled

        Warning:
        - Instance count changes (not auto-scaling)
        - Version changes (unexpected rollback)
        - Instance type changes

        Info:
        - Tag changes
        - Monitoring changes
        - Minor config updates
        """
        # Critical checks
        if field_changed in self.CRITICAL_FIELDS:
            # Database status
            if field_changed == 'status' and resource_type == 'rds_database':
                if new_value in ['stopped', 'failed', 'deleting']:
                    return DriftSeverity.CRITICAL

            # EC2 state
            if field_changed == 'state' and resource_type == 'ec2_instance':
                if new_value in ['terminated', 'stopping', 'stopped']:
                    return DriftSeverity.CRITICAL

            # Security groups changed
            if field_changed == 'security_groups':
                return DriftSeverity.CRITICAL

            # Encryption disabled
            if field_changed == 'encryption_enabled' and not new_value:
                return DriftSeverity.CRITICAL

            # Multi-AZ disabled
            if field_changed == 'multi_az' and not new_value:
                return DriftSeverity.CRITICAL

        # Warning checks
        warning_fields = [
            'desired_count', 'running_count', 'instance_count',
            'task_definition', 'deployment_version',
            'instance_type', 'instance_class',
            'engine_version', 'runtime'
        ]

        if field_changed in warning_fields:
            # Instance count change (not auto-scaling related)
            if 'count' in field_changed:
                # Large changes are warnings
                if isinstance(old_value, int) and isinstance(new_value, int):
                    change_pct = abs(new_value - old_value) / max(old_value, 1)
                    if change_pct > 0.5:  # >50% change
                        return DriftSeverity.WARNING

            # Version rollback
            if field_changed in ['deployment_version', 'engine_version']:
                return DriftSeverity.WARNING

            return DriftSeverity.WARNING

        # Info (everything else)
        return DriftSeverity.INFO

    def should_alert(self, drift_event: DriftEvent) -> bool:
        """
        Determine if this drift event should trigger an alert.

        Rules:
        - Always alert on CRITICAL
        - Alert on WARNING in production
        - Don't alert on INFO unless explicitly configured
        """
        if drift_event.severity == DriftSeverity.CRITICAL.value:
            return True

        if drift_event.severity == DriftSeverity.WARNING.value:
            # Check if production resource
            if 'prod' in drift_event.resource_id.lower():
                return True

        return False

    # ========================================================================
    # Change Attribution
    # ========================================================================

    def _detect_change_source(
        self,
        resource_id: str,
        resource_type: str,
        field_changed: str
    ) -> ChangeSource:
        """
        Detect how the change was made.

        In production, would query CloudTrail.
        For now, use heuristics.
        """
        # Auto-scaling changes
        if field_changed in ['desired_count', 'running_count']:
            return ChangeSource.AUTO_SCALING

        # PromptOps changes (would check our execution logs)
        # For now, assume unknown
        return ChangeSource.UNKNOWN

    def get_drift_attribution(
        self,
        resource_id: str,
        timestamp: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get change attribution from CloudTrail.

        Args:
            resource_id: Resource that changed
            timestamp: When the change occurred

        Returns:
            Dict with user, source, timestamp
        """
        if not self.enable_cloudtrail:
            return None

        # In production, would query CloudTrail API here
        # boto3.client('cloudtrail').lookup_events(...)

        logger.info(f"CloudTrail lookup not implemented yet for {resource_id}")
        return None

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _is_expected_change(self, resource_type: str, field: str) -> bool:
        """Check if this is an expected transient change."""
        expected = self.EXPECTED_CHANGES.get(resource_type, set())
        return field in expected

    def _generate_reason(self, field: str, old_value: Any, new_value: Any) -> str:
        """Generate human-readable reason for drift."""
        if old_value is None:
            return f"{field} set to {new_value}"
        elif new_value is None:
            return f"{field} removed (was {old_value})"
        else:
            return f"{field} changed from {old_value} to {new_value}"

    def _load_snapshot(
        self,
        snapshot_id: Optional[str] = None,
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Load snapshot from disk.

        Args:
            snapshot_id: Specific snapshot ID (latest if None)
            offset: Offset from latest (0=latest, 1=second-latest)

        Returns:
            Snapshot data or None
        """
        if not os.path.exists(self.context_store_path):
            logger.warning(f"Context store not found: {self.context_store_path}")
            return None

        # Get all snapshot files
        snapshot_files = sorted(
            [f for f in os.listdir(self.context_store_path)
             if f.startswith('snap-') and f.endswith('.json')],
            reverse=True
        )

        if not snapshot_files:
            return None

        # Select snapshot
        if snapshot_id:
            filename = f'{snapshot_id}.json'
            if filename not in snapshot_files:
                logger.warning(f"Snapshot not found: {snapshot_id}")
                return None
            filepath = os.path.join(self.context_store_path, filename)
        else:
            if offset >= len(snapshot_files):
                logger.warning(f"Snapshot offset {offset} out of range")
                return None
            filepath = os.path.join(self.context_store_path, snapshot_files[offset])

        # Load snapshot
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load snapshot: {str(e)}")
            return None

    def _empty_report(self, current_snapshot: Dict[str, Any]) -> DriftReport:
        """Create empty report when no previous snapshot exists."""
        snapshot_id = current_snapshot.get('snapshots', [{}])[0].get('snapshot_id', 'unknown')
        timestamp = current_snapshot.get('last_updated', datetime.now(timezone.utc).isoformat())

        return DriftReport(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            total_drift_events=0,
            critical_count=0,
            warning_count=0,
            info_count=0,
            drift_events=[],
            resources_with_drift=[],
            new_resources=[],
            deleted_resources=[]
        )


# ============================================================================
# Report Formatting
# ============================================================================

def format_drift_report(report: DriftReport, verbose: bool = False) -> str:
    """
    Format drift report for display.

    Args:
        report: DriftReport to format
        verbose: Include full details

    Returns:
        Formatted string
    """
    lines = []

    lines.append("="*70)
    lines.append("DRIFT DETECTION REPORT")
    lines.append("="*70)
    lines.append(f"Snapshot: {report.snapshot_id}")
    lines.append(f"Timestamp: {report.timestamp}")
    lines.append("")

    # Summary
    lines.append("SUMMARY")
    lines.append("-"*70)
    lines.append(f"Total Drift Events: {report.total_drift_events}")
    lines.append(f"  Critical: {report.critical_count}")
    lines.append(f"  Warning: {report.warning_count}")
    lines.append(f"  Info: {report.info_count}")
    lines.append("")
    lines.append(f"Resources with Drift: {len(report.resources_with_drift)}")
    lines.append(f"New Resources: {len(report.new_resources)}")
    lines.append(f"Deleted Resources: {len(report.deleted_resources)}")
    lines.append("")

    # Drift events
    if report.drift_events:
        lines.append("DRIFT EVENTS")
        lines.append("-"*70)

        # Group by severity
        critical_events = [e for e in report.drift_events if e.severity == 'critical']
        warning_events = [e for e in report.drift_events if e.severity == 'warning']
        info_events = [e for e in report.drift_events if e.severity == 'info']

        if critical_events:
            lines.append("\n🔴 CRITICAL:")
            for event in critical_events:
                lines.append(f"  • {event.resource_id}")
                lines.append(f"    {event.field_changed}: {event.old_value} → {event.new_value}")
                if verbose:
                    lines.append(f"    Source: {event.change_source}")
                    lines.append(f"    Detected: {event.detected_at}")

        if warning_events:
            lines.append("\n⚠️  WARNING:")
            for event in warning_events:
                lines.append(f"  • {event.resource_id}")
                lines.append(f"    {event.field_changed}: {event.old_value} → {event.new_value}")

        if info_events and verbose:
            lines.append("\nℹ️  INFO:")
            for event in info_events[:10]:  # Limit to 10
                lines.append(f"  • {event.resource_id}")
                lines.append(f"    {event.field_changed}: {event.old_value} → {event.new_value}")

            if len(info_events) > 10:
                lines.append(f"  ... and {len(info_events) - 10} more")

    # New/Deleted resources
    if report.new_resources:
        lines.append("\n➕ NEW RESOURCES:")
        for resource_id in report.new_resources[:5]:
            lines.append(f"  • {resource_id}")
        if len(report.new_resources) > 5:
            lines.append(f"  ... and {len(report.new_resources) - 5} more")

    if report.deleted_resources:
        lines.append("\n➖ DELETED RESOURCES:")
        for resource_id in report.deleted_resources[:5]:
            lines.append(f"  • {resource_id}")
        if len(report.deleted_resources) > 5:
            lines.append(f"  ... and {len(report.deleted_resources) - 5} more")

    lines.append("\n" + "="*70)

    return "\n".join(lines)


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Detect infrastructure drift')
    parser.add_argument('--context-dir', default='./context_snapshots', help='Context directory')
    parser.add_argument('--current', help='Current snapshot ID')
    parser.add_argument('--previous', help='Previous snapshot ID')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    detector = DriftDetector(context_store_path=args.context_dir)

    try:
        report = detector.detect_drift(
            current_snapshot_id=args.current,
            previous_snapshot_id=args.previous
        )

        if args.json:
            # Output as JSON
            report_dict = asdict(report)
            print(json.dumps(report_dict, indent=2))
        else:
            # Output as formatted text
            print(format_drift_report(report, verbose=args.verbose))

    except Exception as e:
        logger.error(f"Drift detection failed: {str(e)}")
        exit(1)


if __name__ == '__main__':
    main()
