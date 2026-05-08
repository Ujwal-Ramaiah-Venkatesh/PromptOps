"""
Budget Enforcer for PromptOps Hyperparameter Tuning
====================================================

Enforces cost limits on hyperparameter tuning jobs using OPA policies.
Prevents runaway costs and enforces organizational budgets.

Author: ML Engineer - Phase 5 Week 48-49
Date: 2026-05-08
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
# Budget Policies
# ============================================================================

class BudgetPolicy(Enum):
    """Budget policy types."""
    PER_JOB = "per_job"
    PER_DAY = "per_day"
    PER_MONTH = "per_month"
    PER_MODEL = "per_model"
    PER_TEAM = "per_team"


class BudgetStatus(Enum):
    """Budget status."""
    WITHIN_BUDGET = "within_budget"
    APPROACHING_LIMIT = "approaching_limit"
    EXCEEDED = "exceeded"


# ============================================================================
# Budget Enforcer
# ============================================================================

class BudgetEnforcer:
    """
    Enforces budget limits on ML training and tuning jobs.

    Policies:
    - Per-job cost limits
    - Daily/monthly spending limits
    - Per-model budgets
    - Team/project budgets
    """

    def __init__(self):
        """Initialize Budget Enforcer."""
        # Default budget policies
        self.policies = {
            "per_job_max": 500.0,  # $500 per tuning job
            "per_day_max": 2000.0,  # $2000 per day
            "per_month_max": 30000.0,  # $30k per month
            "per_model_max": 5000.0,  # $5k per model
            "warning_threshold": 0.80  # Warn at 80% of budget
        }

        # Spending tracking
        self.spending = {
            "current_day": 0.0,
            "current_month": 0.0,
            "by_model": {},
            "by_team": {},
            "history": []
        }

        # Instance pricing (USD per hour)
        self.instance_pricing = {
            "ml.m5.xlarge": 0.269,
            "ml.m5.2xlarge": 0.538,
            "ml.m5.4xlarge": 1.075,
            "ml.c5.2xlarge": 0.476,
            "ml.c5.4xlarge": 0.952,
            "ml.g4dn.xlarge": 0.736,
            "ml.g4dn.4xlarge": 1.686,
            "ml.p3.2xlarge": 4.284,
            "ml.p3.8xlarge": 17.136
        }

    def check_budget(
        self,
        estimated_cost: float,
        model_name: Optional[str] = None,
        team: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if operation is within budget.

        Args:
            estimated_cost: Estimated cost in USD
            model_name: Optional model name for per-model budget
            team: Optional team name for team budget

        Returns:
            Budget check result with approval status
        """
        logger.info(f"Checking budget for ${estimated_cost:.2f} operation")

        result = {
            "approved": True,
            "estimated_cost": estimated_cost,
            "checks": [],
            "warnings": [],
            "total_if_approved": {
                "daily": self.spending["current_day"] + estimated_cost,
                "monthly": self.spending["current_month"] + estimated_cost
            }
        }

        # Check 1: Per-job limit
        job_check = self._check_per_job_limit(estimated_cost)
        result["checks"].append(job_check)
        if not job_check["passed"]:
            result["approved"] = False

        # Check 2: Daily limit
        daily_check = self._check_daily_limit(estimated_cost)
        result["checks"].append(daily_check)
        if not daily_check["passed"]:
            result["approved"] = False
        elif daily_check.get("warning"):
            result["warnings"].append(daily_check["warning"])

        # Check 3: Monthly limit
        monthly_check = self._check_monthly_limit(estimated_cost)
        result["checks"].append(monthly_check)
        if not monthly_check["passed"]:
            result["approved"] = False
        elif monthly_check.get("warning"):
            result["warnings"].append(monthly_check["warning"])

        # Check 4: Per-model limit (if provided)
        if model_name:
            model_check = self._check_model_limit(estimated_cost, model_name)
            result["checks"].append(model_check)
            if not model_check["passed"]:
                result["approved"] = False

        logger.info(f"Budget check result: {'APPROVED' if result['approved'] else 'REJECTED'}")
        return result

    def _check_per_job_limit(self, cost: float) -> Dict[str, Any]:
        """Check per-job cost limit."""
        limit = self.policies["per_job_max"]
        passed = cost <= limit

        return {
            "policy": "per_job_max",
            "limit": limit,
            "cost": cost,
            "passed": passed,
            "percentage": (cost / limit) * 100,
            "message": (
                f"Job cost ${cost:.2f} within limit ${limit:.2f}"
                if passed else
                f"Job cost ${cost:.2f} exceeds limit ${limit:.2f}"
            )
        }

    def _check_daily_limit(self, cost: float) -> Dict[str, Any]:
        """Check daily spending limit."""
        limit = self.policies["per_day_max"]
        current = self.spending["current_day"]
        new_total = current + cost
        passed = new_total <= limit

        warning_threshold = limit * self.policies["warning_threshold"]
        warning = None

        if new_total > warning_threshold and new_total <= limit:
            warning = f"Daily spending will reach {(new_total/limit)*100:.0f}% of limit"

        return {
            "policy": "per_day_max",
            "limit": limit,
            "current": current,
            "new_total": new_total,
            "passed": passed,
            "percentage": (new_total / limit) * 100,
            "warning": warning,
            "message": (
                f"Daily total ${new_total:.2f} within limit ${limit:.2f}"
                if passed else
                f"Daily total ${new_total:.2f} exceeds limit ${limit:.2f}"
            )
        }

    def _check_monthly_limit(self, cost: float) -> Dict[str, Any]:
        """Check monthly spending limit."""
        limit = self.policies["per_month_max"]
        current = self.spending["current_month"]
        new_total = current + cost
        passed = new_total <= limit

        warning_threshold = limit * self.policies["warning_threshold"]
        warning = None

        if new_total > warning_threshold and new_total <= limit:
            warning = f"Monthly spending will reach {(new_total/limit)*100:.0f}% of limit"

        return {
            "policy": "per_month_max",
            "limit": limit,
            "current": current,
            "new_total": new_total,
            "passed": passed,
            "percentage": (new_total / limit) * 100,
            "warning": warning,
            "message": (
                f"Monthly total ${new_total:.2f} within limit ${limit:.2f}"
                if passed else
                f"Monthly total ${new_total:.2f} exceeds limit ${limit:.2f}"
            )
        }

    def _check_model_limit(self, cost: float, model_name: str) -> Dict[str, Any]:
        """Check per-model spending limit."""
        limit = self.policies["per_model_max"]
        current = self.spending["by_model"].get(model_name, 0.0)
        new_total = current + cost
        passed = new_total <= limit

        return {
            "policy": "per_model_max",
            "model": model_name,
            "limit": limit,
            "current": current,
            "new_total": new_total,
            "passed": passed,
            "percentage": (new_total / limit) * 100,
            "message": (
                f"Model '{model_name}' total ${new_total:.2f} within limit ${limit:.2f}"
                if passed else
                f"Model '{model_name}' total ${new_total:.2f} exceeds limit ${limit:.2f}"
            )
        }

    def estimate_tuning_cost(
        self,
        instance_type: str,
        max_jobs: int,
        max_parallel_jobs: int,
        estimated_duration_hours: float = 1.0
    ) -> Dict[str, Any]:
        """
        Estimate cost of hyperparameter tuning job.

        Args:
            instance_type: SageMaker instance type
            max_jobs: Maximum training jobs
            max_parallel_jobs: Parallel jobs
            estimated_duration_hours: Estimated duration per job

        Returns:
            Cost estimate
        """
        instance_price = self.instance_pricing.get(instance_type, 0.269)

        # Worst case: all jobs run for full duration
        total_compute_hours = max_jobs * estimated_duration_hours
        compute_cost = total_compute_hours * instance_price

        # Storage cost (minimal for tuning)
        storage_cost = max_jobs * 0.10  # $0.10 per job for storage

        total_cost = compute_cost + storage_cost

        # Best case: early stopping reduces cost by ~30%
        best_case_cost = total_cost * 0.70

        return {
            "instance_type": instance_type,
            "instance_price_per_hour": instance_price,
            "max_jobs": max_jobs,
            "max_parallel_jobs": max_parallel_jobs,
            "estimated_duration_per_job_hours": estimated_duration_hours,
            "total_compute_hours": total_compute_hours,
            "compute_cost_usd": round(compute_cost, 2),
            "storage_cost_usd": round(storage_cost, 2),
            "total_cost_usd": round(total_cost, 2),
            "best_case_cost_usd": round(best_case_cost, 2),
            "estimated_completion_hours": (total_compute_hours / max_parallel_jobs)
        }

    def record_spending(
        self,
        cost: float,
        model_name: Optional[str] = None,
        team: Optional[str] = None,
        description: str = ""
    ):
        """
        Record actual spending.

        Args:
            cost: Actual cost incurred
            model_name: Model name
            team: Team name
            description: Description of spending
        """
        logger.info(f"Recording spending: ${cost:.2f}")

        # Update spending
        self.spending["current_day"] += cost
        self.spending["current_month"] += cost

        if model_name:
            if model_name not in self.spending["by_model"]:
                self.spending["by_model"][model_name] = 0.0
            self.spending["by_model"][model_name] += cost

        if team:
            if team not in self.spending["by_team"]:
                self.spending["by_team"][team] = 0.0
            self.spending["by_team"][team] += cost

        # Record in history
        self.spending["history"].append({
            "cost": cost,
            "model_name": model_name,
            "team": team,
            "description": description,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_spending_summary(self) -> Dict[str, Any]:
        """Get current spending summary."""
        return {
            "current_day": {
                "spent": self.spending["current_day"],
                "limit": self.policies["per_day_max"],
                "remaining": self.policies["per_day_max"] - self.spending["current_day"],
                "percentage": (self.spending["current_day"] / self.policies["per_day_max"]) * 100
            },
            "current_month": {
                "spent": self.spending["current_month"],
                "limit": self.policies["per_month_max"],
                "remaining": self.policies["per_month_max"] - self.spending["current_month"],
                "percentage": (self.spending["current_month"] / self.policies["per_month_max"]) * 100
            },
            "by_model": self.spending["by_model"],
            "by_team": self.spending["by_team"],
            "total_transactions": len(self.spending["history"])
        }

    def update_policy(self, policy_name: str, value: float):
        """
        Update budget policy.

        Args:
            policy_name: Policy name
            value: New policy value
        """
        if policy_name in self.policies:
            old_value = self.policies[policy_name]
            self.policies[policy_name] = value
            logger.info(f"Updated policy {policy_name}: ${old_value} -> ${value}")
        else:
            logger.warning(f"Unknown policy: {policy_name}")

    def reset_daily_spending(self):
        """Reset daily spending counter."""
        logger.info(f"Resetting daily spending: ${self.spending['current_day']:.2f}")
        self.spending["current_day"] = 0.0

    def reset_monthly_spending(self):
        """Reset monthly spending counter."""
        logger.info(f"Resetting monthly spending: ${self.spending['current_month']:.2f}")
        self.spending["current_month"] = 0.0


# ============================================================================
# Testing
# ============================================================================

def test_budget_enforcer():
    """Test budget enforcer."""
    logger.info("Testing Budget Enforcer...")

    enforcer = BudgetEnforcer()

    # Test 1: Estimate tuning cost
    print("\n=== Test 1: Estimate Tuning Cost ===")
    estimate = enforcer.estimate_tuning_cost(
        instance_type="ml.m5.xlarge",
        max_jobs=20,
        max_parallel_jobs=2,
        estimated_duration_hours=1.5
    )
    print(json.dumps(estimate, indent=2))

    # Test 2: Check budget (within limit)
    print("\n=== Test 2: Budget Check (Within Limit) ===")
    budget_check = enforcer.check_budget(
        estimated_cost=150.0,
        model_name="churn-prediction"
    )
    print(json.dumps(budget_check, indent=2))

    # Test 3: Check budget (exceeds limit)
    print("\n=== Test 3: Budget Check (Exceeds Limit) ===")
    budget_check_high = enforcer.check_budget(
        estimated_cost=600.0,  # Exceeds per-job limit of $500
        model_name="churn-prediction"
    )
    print(json.dumps(budget_check_high, indent=2))

    # Test 4: Record spending and check summary
    print("\n=== Test 4: Record Spending ===")
    if budget_check["approved"]:
        enforcer.record_spending(
            cost=150.0,
            model_name="churn-prediction",
            team="ml-team",
            description="Hyperparameter tuning job"
        )

    summary = enforcer.get_spending_summary()
    print(json.dumps(summary, indent=2))

    # Test 5: Approaching daily limit
    print("\n=== Test 5: Approaching Daily Limit ===")
    enforcer.record_spending(cost=1500.0, description="Large training job")
    budget_check_warning = enforcer.check_budget(estimated_cost=300.0)
    print(json.dumps(budget_check_warning, indent=2))


if __name__ == "__main__":
    test_budget_enforcer()
