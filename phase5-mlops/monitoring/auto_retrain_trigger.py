"""
Auto-Retrain Trigger for PromptOps ML Models
============================================

Automatically triggers model retraining based on:
- Performance degradation
- Drift detection
- Scheduled intervals
- Data availability

Author: ML Engineer - Phase 5 Week 46-47
Date: 2026-05-07
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Retrain Trigger Types
# ============================================================================

class RetrainTriggerType(Enum):
    """Types of retrain triggers."""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DRIFT_DETECTED = "drift_detected"
    SCHEDULED = "scheduled"
    DATA_THRESHOLD = "data_threshold"
    MANUAL = "manual"


class RetrainStatus(Enum):
    """Status of retrain job."""
    PENDING = "pending"
    TRIGGERED = "triggered"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# Auto-Retrain Trigger
# ============================================================================

class AutoRetrainTrigger:
    """
    Manages automatic model retraining triggers.

    Monitors:
    - Model performance metrics
    - Drift detection results
    - Data availability
    - Training schedules
    """

    def __init__(self):
        """Initialize Auto-Retrain Trigger."""
        # Trigger configurations
        self.trigger_configs = {
            "performance_degradation": {
                "enabled": True,
                "accuracy_threshold": 0.05,  # 5% drop
                "error_rate_threshold": 0.05,  # 5% increase
                "latency_threshold": 0.30,  # 30% increase
            },
            "drift_detection": {
                "enabled": True,
                "drift_score_threshold": 0.1,
                "require_concept_drift": False
            },
            "scheduled": {
                "enabled": True,
                "frequency_days": 7,  # Weekly
                "day_of_week": "sunday",
                "time_of_day": "02:00"
            },
            "data_threshold": {
                "enabled": True,
                "min_new_samples": 1000,
                "min_new_samples_percentage": 0.10  # 10% of training set
            }
        }

        # Retrain history
        self.retrain_history = []

    def check_retrain_conditions(
        self,
        performance_metrics: Optional[Dict[str, Any]] = None,
        drift_results: Optional[Dict[str, Any]] = None,
        data_stats: Optional[Dict[str, Any]] = None,
        last_training_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Check if model should be retrained.

        Args:
            performance_metrics: Current performance metrics
            drift_results: Drift detection results
            data_stats: New data statistics
            last_training_date: When model was last trained

        Returns:
            Decision on whether to retrain
        """
        logger.info("Checking retrain conditions...")

        decision = {
            "should_retrain": False,
            "trigger_type": None,
            "reasons": [],
            "urgency": "normal",  # low, normal, high, critical
            "checked_at": datetime.utcnow().isoformat()
        }

        # Check 1: Performance degradation
        if performance_metrics and self.trigger_configs["performance_degradation"]["enabled"]:
            perf_check = self._check_performance_degradation(performance_metrics)
            if perf_check["triggered"]:
                decision["should_retrain"] = True
                decision["trigger_type"] = RetrainTriggerType.PERFORMANCE_DEGRADATION.value
                decision["reasons"].extend(perf_check["reasons"])
                decision["urgency"] = "high"

        # Check 2: Drift detected
        if drift_results and self.trigger_configs["drift_detection"]["enabled"]:
            drift_check = self._check_drift(drift_results)
            if drift_check["triggered"]:
                decision["should_retrain"] = True
                if not decision["trigger_type"]:
                    decision["trigger_type"] = RetrainTriggerType.DRIFT_DETECTED.value
                decision["reasons"].extend(drift_check["reasons"])
                if decision["urgency"] == "normal":
                    decision["urgency"] = "high" if drift_check["severity"] == "high" else "normal"

        # Check 3: Scheduled retrain
        if last_training_date and self.trigger_configs["scheduled"]["enabled"]:
            schedule_check = self._check_schedule(last_training_date)
            if schedule_check["triggered"]:
                if not decision["should_retrain"]:  # Only if no urgent reasons
                    decision["should_retrain"] = True
                    decision["trigger_type"] = RetrainTriggerType.SCHEDULED.value
                    decision["reasons"].extend(schedule_check["reasons"])
                    decision["urgency"] = "low"

        # Check 4: Data threshold
        if data_stats and self.trigger_configs["data_threshold"]["enabled"]:
            data_check = self._check_data_threshold(data_stats)
            if data_check["triggered"]:
                if not decision["should_retrain"]:  # Only if no other reasons
                    decision["should_retrain"] = True
                    decision["trigger_type"] = RetrainTriggerType.DATA_THRESHOLD.value
                    decision["reasons"].extend(data_check["reasons"])
                    decision["urgency"] = "low"

        logger.info(f"Retrain decision: {decision['should_retrain']} (urgency: {decision['urgency']})")
        return decision

    def _check_performance_degradation(
        self,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if performance has degraded."""
        result = {"triggered": False, "reasons": []}

        # Check if degradation detected
        if "degradation" in metrics:
            if metrics["degradation"].get("degraded", False):
                result["triggered"] = True

                for check in metrics["degradation"].get("checks", []):
                    if check.get("degraded"):
                        metric_name = check["metric"]
                        change = check["change"]
                        result["reasons"].append(
                            f"Performance degradation: {metric_name} changed by {change:+.2%}"
                        )

        return result

    def _check_drift(
        self,
        drift_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if drift detected."""
        result = {"triggered": False, "reasons": [], "severity": "normal"}

        config = self.trigger_configs["drift_detection"]

        # Check drift detection
        if drift_results.get("drift_detected", False):
            drift_score = drift_results.get("drift_score", 0.0)

            if drift_score > config["drift_score_threshold"]:
                result["triggered"] = True
                result["reasons"].append(
                    f"Drift detected with score {drift_score:.4f} "
                    f"(threshold: {config['drift_score_threshold']})"
                )

                # Determine severity
                if drift_score > 0.3:
                    result["severity"] = "high"
                elif drift_score > 0.2:
                    result["severity"] = "normal"
                else:
                    result["severity"] = "low"

        # Check concept drift specifically
        if config.get("require_concept_drift") and drift_results.get("drift_type") == "concept_drift":
            result["triggered"] = True
            result["reasons"].append("Concept drift detected (feature-target relationship changed)")
            result["severity"] = "high"

        return result

    def _check_schedule(
        self,
        last_training_date: datetime
    ) -> Dict[str, Any]:
        """Check if scheduled retrain is due."""
        result = {"triggered": False, "reasons": []}

        config = self.trigger_configs["scheduled"]
        frequency_days = config["frequency_days"]

        # Check if enough time has passed
        time_since_training = datetime.utcnow() - last_training_date
        days_since_training = time_since_training.total_seconds() / 86400

        if days_since_training >= frequency_days:
            result["triggered"] = True
            result["reasons"].append(
                f"Scheduled retrain due: {days_since_training:.1f} days since last training "
                f"(frequency: {frequency_days} days)"
            )

        return result

    def _check_data_threshold(
        self,
        data_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if enough new data available for retraining."""
        result = {"triggered": False, "reasons": []}

        config = self.trigger_configs["data_threshold"]

        new_samples = data_stats.get("new_samples", 0)
        total_samples = data_stats.get("total_samples", 0)

        # Check absolute threshold
        if new_samples >= config["min_new_samples"]:
            result["triggered"] = True
            result["reasons"].append(
                f"Sufficient new data available: {new_samples} samples "
                f"(threshold: {config['min_new_samples']})"
            )

        # Check percentage threshold
        if total_samples > 0:
            new_percentage = new_samples / total_samples
            if new_percentage >= config["min_new_samples_percentage"]:
                if not result["triggered"]:
                    result["triggered"] = True
                result["reasons"].append(
                    f"New data exceeds {new_percentage:.1%} of training set "
                    f"(threshold: {config['min_new_samples_percentage']:.1%})"
                )

        return result

    def trigger_retrain(
        self,
        model_name: str,
        model_version: str,
        trigger_type: str,
        reasons: List[str],
        urgency: str = "normal",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger model retraining.

        Args:
            model_name: Name of model to retrain
            model_version: Current model version
            trigger_type: Type of trigger
            reasons: Reasons for retraining
            urgency: Urgency level
            config: Optional training configuration

        Returns:
            Retrain job information
        """
        logger.info(f"Triggering retrain for {model_name} v{model_version}")

        # Generate new version
        current_version_num = float(model_version.replace('v', ''))
        new_version = f"v{current_version_num + 0.1:.1f}"

        retrain_job = {
            "retrain_id": f"retrain-{model_name}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "model_name": model_name,
            "current_version": model_version,
            "new_version": new_version,
            "trigger_type": trigger_type,
            "reasons": reasons,
            "urgency": urgency,
            "status": RetrainStatus.TRIGGERED.value,
            "triggered_at": datetime.utcnow().isoformat(),
            "config": config or {},
            "completed_at": None,
            "result": None
        }

        # Add to history
        self.retrain_history.append(retrain_job)

        logger.info(f"Retrain triggered: {retrain_job['retrain_id']}")
        return retrain_job

    def update_retrain_status(
        self,
        retrain_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ):
        """
        Update retrain job status.

        Args:
            retrain_id: Retrain job ID
            status: New status
            result: Optional result data
        """
        for job in self.retrain_history:
            if job["retrain_id"] == retrain_id:
                job["status"] = status

                if status in [RetrainStatus.COMPLETED.value, RetrainStatus.FAILED.value]:
                    job["completed_at"] = datetime.utcnow().isoformat()

                if result:
                    job["result"] = result

                logger.info(f"Retrain job {retrain_id} status updated: {status}")
                return

        logger.warning(f"Retrain job not found: {retrain_id}")

    def get_retrain_history(
        self,
        model_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get retrain history.

        Args:
            model_name: Optional filter by model name
            limit: Maximum number of records to return

        Returns:
            List of retrain jobs
        """
        history = self.retrain_history

        if model_name:
            history = [job for job in history if job["model_name"] == model_name]

        # Sort by triggered_at (most recent first)
        history = sorted(history, key=lambda x: x["triggered_at"], reverse=True)

        return history[:limit]

    def configure_triggers(
        self,
        trigger_type: str,
        config: Dict[str, Any]
    ):
        """
        Update trigger configuration.

        Args:
            trigger_type: Type of trigger to configure
            config: New configuration
        """
        if trigger_type in self.trigger_configs:
            self.trigger_configs[trigger_type].update(config)
            logger.info(f"Updated trigger configuration: {trigger_type}")
        else:
            logger.warning(f"Unknown trigger type: {trigger_type}")

    def get_trigger_configs(self) -> Dict[str, Any]:
        """Get all trigger configurations."""
        return self.trigger_configs


# ============================================================================
# Testing
# ============================================================================

def test_auto_retrain_trigger():
    """Test auto-retrain trigger."""
    logger.info("Testing Auto-Retrain Trigger...")

    trigger = AutoRetrainTrigger()

    # Test 1: Performance degradation trigger
    print("\n=== Test 1: Performance Degradation Trigger ===")

    performance_metrics = {
        "degradation": {
            "degraded": True,
            "checks": [
                {
                    "metric": "accuracy",
                    "degraded": True,
                    "change": -0.08  # 8% drop
                }
            ]
        }
    }

    decision = trigger.check_retrain_conditions(
        performance_metrics=performance_metrics
    )
    print(json.dumps(decision, indent=2))

    # Test 2: Drift detection trigger
    print("\n=== Test 2: Drift Detection Trigger ===")

    drift_results = {
        "drift_detected": True,
        "drift_score": 0.25,
        "drift_type": "prediction_drift"
    }

    decision2 = trigger.check_retrain_conditions(
        drift_results=drift_results
    )
    print(json.dumps(decision2, indent=2))

    # Test 3: Scheduled trigger
    print("\n=== Test 3: Scheduled Trigger ===")

    last_training = datetime.utcnow() - timedelta(days=10)  # 10 days ago

    decision3 = trigger.check_retrain_conditions(
        last_training_date=last_training
    )
    print(json.dumps(decision3, indent=2))

    # Test 4: Trigger retrain
    if decision["should_retrain"]:
        print("\n=== Test 4: Trigger Retrain ===")

        retrain_job = trigger.trigger_retrain(
            model_name="churn-prediction",
            model_version="v2.0",
            trigger_type=decision["trigger_type"],
            reasons=decision["reasons"],
            urgency=decision["urgency"]
        )
        print(json.dumps(retrain_job, indent=2))

        # Update status
        trigger.update_retrain_status(
            retrain_job["retrain_id"],
            RetrainStatus.TRAINING.value
        )

        # Get history
        print("\n=== Retrain History ===")
        history = trigger.get_retrain_history()
        print(json.dumps(history, indent=2))


if __name__ == "__main__":
    test_auto_retrain_trigger()
