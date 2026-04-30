"""
Autonomy Tier Classifier
=========================

Classifies operations by risk level for autonomy tier system.

Week 13-15: ENHANCEMENT-001
Author: PromptOps Team
Date: 2026-04-30
"""

from enum import Enum
from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __lt__(self, other):
        """Allow comparison of risk levels."""
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return order[self.value] < order[other.value]

    def __le__(self, other):
        """Less than or equal comparison."""
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return order[self.value] <= order[other.value]

    def __gt__(self, other):
        """Greater than comparison."""
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return order[self.value] > order[other.value]

    def __ge__(self, other):
        """Greater than or equal comparison."""
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return order[self.value] >= order[other.value]


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    risk_level: RiskLevel
    action_type: str
    reason: str
    can_auto_execute: bool
    factors: Dict[str, str]

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "risk_level": self.risk_level.value,
            "action_type": self.action_type,
            "reason": self.reason,
            "can_auto_execute": self.can_auto_execute,
            "factors": self.factors
        }


class TierClassifier:
    """
    Classifies operations by risk level.

    Considers:
    - Action type (restart vs. delete)
    - Environment (staging vs. production)
    - Resource type (pod vs. database)
    - Data sensitivity (logs vs. user data)

    Example:
        classifier = TierClassifier(db_session)
        assessment = classifier.classify(intent)
        print(f"Risk: {assessment.risk_level.value}")
    """

    def __init__(self, db_session):
        """
        Initialize classifier.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.action_risk_cache = {}
        self._load_risk_levels()

    def _load_risk_levels(self):
        """Load action risk levels from database into memory cache."""
        try:
            from database.autonomy_models import ActionRiskLevel

            action_risks = self.db.query(ActionRiskLevel).all()

            for action_risk in action_risks:
                self.action_risk_cache[action_risk.action_type] = {
                    "risk_level": RiskLevel(action_risk.default_risk_level),
                    "description": action_risk.description,
                    "can_override": action_risk.can_be_overridden
                }

            logger.info(f"Loaded {len(self.action_risk_cache)} action risk levels")

        except Exception as e:
            logger.error(f"Failed to load action risk levels: {e}")
            # Continue with fallback defaults

    def classify(self, intent: Dict) -> RiskAssessment:
        """
        Classify an operation's risk level.

        Args:
            intent: Parsed intent from NLP engine
                Expected keys:
                - intent_type: str (e.g., "deploy", "restart_pod")
                - target_env: str (e.g., "staging", "production")
                - resource_type: str (e.g., "pod", "database")
                - parameters: dict (additional context)

        Returns:
            RiskAssessment with risk level and reasoning
        """
        action_type = intent.get("intent_type", "unknown")
        environment = intent.get("target_env", "unknown")
        resource_type = intent.get("resource_type", "unknown")
        parameters = intent.get("parameters", {})

        # Get base risk level from action type
        base_risk = self._get_base_risk(action_type)

        # Adjust risk based on environment
        adjusted_risk = self._adjust_for_environment(base_risk, environment)

        # Adjust risk based on resource type
        final_risk = self._adjust_for_resource(adjusted_risk, resource_type)

        # Further adjust based on parameters (e.g., disk size)
        final_risk = self._adjust_for_parameters(final_risk, action_type, parameters)

        # Build reasoning
        factors = {
            "action": action_type,
            "environment": environment,
            "resource": resource_type,
            "base_risk": base_risk.value,
            "final_risk": final_risk.value
        }

        reason = self._build_reason(factors)

        # CRITICAL actions can never auto-execute (safety guarantee)
        can_auto_execute = final_risk != RiskLevel.CRITICAL

        return RiskAssessment(
            risk_level=final_risk,
            action_type=action_type,
            reason=reason,
            can_auto_execute=can_auto_execute,
            factors=factors
        )

    def _get_base_risk(self, action_type: str) -> RiskLevel:
        """
        Get base risk level for action type.

        First checks database cache, then falls back to hardcoded defaults.
        """
        # Check cache from database
        if action_type in self.action_risk_cache:
            return self.action_risk_cache[action_type]["risk_level"]

        # Fallback defaults (in case database load failed)
        defaults = {
            # LOW
            "restart_pod": RiskLevel.LOW,
            "clear_cache": RiskLevel.LOW,
            "log_rotation": RiskLevel.LOW,
            "read_only_query": RiskLevel.LOW,
            "monitoring_adjust": RiskLevel.LOW,

            # MEDIUM
            "scale": RiskLevel.MEDIUM,
            "scale_up": RiskLevel.MEDIUM,
            "scale_down": RiskLevel.MEDIUM,
            "staging_rollback": RiskLevel.MEDIUM,
            "config_change": RiskLevel.MEDIUM,

            # HIGH
            "deploy": RiskLevel.HIGH,
            "production_deploy": RiskLevel.HIGH,
            "rollback": RiskLevel.HIGH,
            "database_migration": RiskLevel.HIGH,

            # CRITICAL
            "delete": RiskLevel.CRITICAL,
            "delete_data": RiskLevel.CRITICAL,
            "schema_change": RiskLevel.CRITICAL,
            "database_schema_change": RiskLevel.CRITICAL,
            "iam_policy_change": RiskLevel.CRITICAL,
            "security_group_change": RiskLevel.CRITICAL,
            "drop_database": RiskLevel.CRITICAL,
        }

        # Default to MEDIUM if unknown (fail-safe)
        return defaults.get(action_type, RiskLevel.MEDIUM)

    def _adjust_for_environment(self, base_risk: RiskLevel, env: str) -> RiskLevel:
        """
        Increase risk for production environments.

        Production operations are inherently riskier.
        """
        env_lower = env.lower()

        if env_lower == "production" or env_lower == "prod":
            # Bump up risk level for production
            if base_risk == RiskLevel.LOW:
                return RiskLevel.MEDIUM
            elif base_risk == RiskLevel.MEDIUM:
                return RiskLevel.HIGH
            # HIGH stays HIGH
            # CRITICAL stays CRITICAL

        return base_risk

    def _adjust_for_resource(self, risk: RiskLevel, resource: str) -> RiskLevel:
        """
        Adjust risk based on resource type.

        Certain resources are always critical (databases, IAM, security).
        """
        resource_lower = resource.lower()

        critical_resources = [
            "database", "db", "rds", "postgresql", "mysql",
            "iam", "role", "policy",
            "security_group", "firewall",
            "kms", "secrets",
            "s3_bucket"  # Deleting S3 buckets is risky
        ]

        if any(cr in resource_lower for cr in critical_resources):
            # Any operation on critical resources is at least HIGH risk
            if risk < RiskLevel.HIGH:
                return RiskLevel.HIGH

        return risk

    def _adjust_for_parameters(self, risk: RiskLevel, action_type: str,
                               parameters: Dict) -> RiskLevel:
        """
        Adjust risk based on operation parameters.

        Examples:
        - disk_cleanup with size > 10GB is higher risk
        - scale_down by >50% is higher risk
        """
        # Disk cleanup: Large cleanups are riskier
        if "cleanup" in action_type.lower():
            size_gb = parameters.get("size_gb", 0)
            if size_gb > 10:
                # Large cleanup bumps from LOW to MEDIUM
                if risk == RiskLevel.LOW:
                    return RiskLevel.MEDIUM

        # Scale down: Large reductions are riskier
        if "scale_down" in action_type.lower():
            from_count = parameters.get("from_count", 0)
            to_count = parameters.get("to_count", 0)
            if from_count > 0 and to_count < from_count * 0.5:
                # Reducing by >50% is high risk
                if risk < RiskLevel.HIGH:
                    return RiskLevel.HIGH

        return risk

    def _build_reason(self, factors: Dict) -> str:
        """
        Build human-readable reasoning for risk classification.

        Args:
            factors: Dictionary of risk factors

        Returns:
            Human-readable explanation string
        """
        action = factors.get("action", "unknown")
        env = factors.get("environment", "unknown")
        final_risk = factors.get("final_risk", "unknown")
        base_risk = factors.get("base_risk", "unknown")

        reason_parts = [
            f"Action '{action}' in '{env}' environment",
            f"classified as {final_risk.upper()} risk"
        ]

        # Add explanation if risk was adjusted
        if base_risk != final_risk:
            reason_parts.append(f"(base: {base_risk}, adjusted for environment/resource)")

        return " ".join(reason_parts)

    def get_action_info(self, action_type: str) -> Optional[Dict]:
        """
        Get information about an action type.

        Returns:
            Dictionary with risk_level, description, can_override
            or None if action not found
        """
        return self.action_risk_cache.get(action_type)

    def list_actions_by_risk(self, risk_level: RiskLevel) -> List[str]:
        """
        List all action types at a given risk level.

        Args:
            risk_level: RiskLevel enum value

        Returns:
            List of action type strings
        """
        return [
            action_type
            for action_type, info in self.action_risk_cache.items()
            if info["risk_level"] == risk_level
        ]
