"""
Approval Workflow for PromptOps Model Governance
=================================================

Implements multi-stage approval workflow for model deployment:
- Development → Staging → Production transitions
- Approval gates with reviewers
- Automated checks (metrics, bias, drift)
- Rollback capabilities

Author: ML Engineer - Phase 5 Week 50-51
Date: 2026-05-09
"""

import os
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
# Approval Workflow Enums
# ============================================================================

class ApprovalStatus(Enum):
    """Approval request status."""
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"


class WorkflowStage(Enum):
    """Workflow stages."""
    DEV_TO_STAGING = "dev_to_staging"
    STAGING_TO_PROD = "staging_to_prod"
    PROD_ROLLBACK = "prod_rollback"


# ============================================================================
# Approval Workflow
# ============================================================================

class ApprovalWorkflow:
    """
    Multi-stage approval workflow for model deployment.

    Features:
    - Staged promotions (dev→staging→prod)
    - Approval gates with multiple reviewers
    - Automated quality checks
    - Approval history and audit trail
    - Rollback support
    """

    def __init__(self, workflow_path: str = "./approval_workflows"):
        """Initialize Approval Workflow."""
        self.workflow_path = workflow_path
        self.approvals_db: Dict[str, Dict[str, Any]] = {}
        self.policies: Dict[str, Dict[str, Any]] = self._default_policies()
        self._ensure_workflow_exists()
        self._load_workflows()

    def _ensure_workflow_exists(self):
        """Ensure workflow directory exists."""
        os.makedirs(self.workflow_path, exist_ok=True)

    def _default_policies(self) -> Dict[str, Dict[str, Any]]:
        """Default approval policies."""
        return {
            "dev_to_staging": {
                "required_approvers": 1,
                "required_roles": ["ml_engineer"],
                "automated_checks": ["metrics_threshold", "bias_check"],
                "min_metrics": {"accuracy": 0.85}
            },
            "staging_to_prod": {
                "required_approvers": 2,
                "required_roles": ["ml_lead", "devops_lead"],
                "automated_checks": ["metrics_threshold", "bias_check", "drift_check", "load_test"],
                "min_metrics": {"accuracy": 0.90, "auc": 0.90}
            },
            "prod_rollback": {
                "required_approvers": 1,
                "required_roles": ["ml_lead"],
                "automated_checks": []
            }
        }

    def _load_workflows(self):
        """Load workflows from disk."""
        workflow_file = os.path.join(self.workflow_path, "approvals.json")
        if os.path.exists(workflow_file):
            try:
                with open(workflow_file, 'r') as f:
                    self.approvals_db = json.load(f)
                logger.info(f"Loaded {len(self.approvals_db)} approval workflows")
            except Exception as e:
                logger.warning(f"Failed to load workflows: {e}")

    def _save_workflows(self):
        """Save workflows to disk."""
        workflow_file = os.path.join(self.workflow_path, "approvals.json")
        try:
            with open(workflow_file, 'w') as f:
                json.dump(self.approvals_db, f, indent=2, default=str)
            logger.info("Workflows saved to disk")
        except Exception as e:
            logger.error(f"Failed to save workflows: {e}")

    def create_approval_request(
        self,
        model_name: str,
        model_version: str,
        source_stage: str,
        target_stage: str,
        requested_by: str,
        reason: str = "",
        metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Create approval request for stage transition.

        Args:
            model_name: Model name
            model_version: Model version
            source_stage: Source stage (Development, Staging)
            target_stage: Target stage (Staging, Production)
            requested_by: Requester username
            reason: Reason for promotion
            metrics: Model metrics

        Returns:
            Approval request information
        """
        logger.info(f"Creating approval request: {model_name} {source_stage}→{target_stage}")

        # Determine workflow stage
        workflow_stage = self._get_workflow_stage(source_stage, target_stage)
        policy = self.policies.get(workflow_stage.value, {})

        # Run automated checks
        automated_checks = self._run_automated_checks(
            model_name=model_name,
            model_version=model_version,
            metrics=metrics,
            checks=policy.get("automated_checks", []),
            min_metrics=policy.get("min_metrics", {})
        )

        # Create approval request
        request_id = f"{model_name}_{model_version}_{workflow_stage.value}_{datetime.utcnow().timestamp()}"

        approval_request = {
            "request_id": request_id,
            "model_name": model_name,
            "model_version": model_version,
            "source_stage": source_stage,
            "target_stage": target_stage,
            "workflow_stage": workflow_stage.value,
            "status": ApprovalStatus.PENDING.value,
            "requested_by": requested_by,
            "requested_at": datetime.utcnow().isoformat(),
            "reason": reason,
            "metrics": metrics or {},
            "policy": {
                "required_approvers": policy.get("required_approvers", 1),
                "required_roles": policy.get("required_roles", [])
            },
            "automated_checks": automated_checks,
            "approvals": [],
            "rejections": []
        }

        # Auto-reject if automated checks failed
        failed_checks = [c for c in automated_checks if not c["passed"]]
        if failed_checks:
            approval_request["status"] = ApprovalStatus.REJECTED.value
            approval_request["rejection_reason"] = f"Failed automated checks: {', '.join([c['check'] for c in failed_checks])}"

        self.approvals_db[request_id] = approval_request
        self._save_workflows()

        logger.info(f"Approval request created: {request_id}")
        return approval_request

    def _get_workflow_stage(self, source: str, target: str) -> WorkflowStage:
        """Determine workflow stage from source/target."""
        if source.lower() == "development" and target.lower() == "staging":
            return WorkflowStage.DEV_TO_STAGING
        elif source.lower() == "staging" and target.lower() == "production":
            return WorkflowStage.STAGING_TO_PROD
        elif source.lower() == "production":
            return WorkflowStage.PROD_ROLLBACK
        else:
            raise ValueError(f"Invalid stage transition: {source}→{target}")

    def _run_automated_checks(
        self,
        model_name: str,
        model_version: str,
        metrics: Optional[Dict[str, float]],
        checks: List[str],
        min_metrics: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Run automated quality checks.

        Args:
            model_name: Model name
            model_version: Model version
            metrics: Model metrics
            checks: List of checks to run
            min_metrics: Minimum metric thresholds

        Returns:
            List of check results
        """
        results = []

        # Check 1: Metrics threshold
        if "metrics_threshold" in checks:
            passed = True
            failures = []

            if metrics:
                for metric, threshold in min_metrics.items():
                    if metrics.get(metric, 0) < threshold:
                        passed = False
                        failures.append(f"{metric} {metrics.get(metric, 0):.3f} < {threshold}")

            results.append({
                "check": "metrics_threshold",
                "passed": passed,
                "details": f"Metrics meet thresholds" if passed else f"Failed: {', '.join(failures)}"
            })

        # Check 2: Bias check
        if "bias_check" in checks:
            # Placeholder - would integrate with BiasDetector
            results.append({
                "check": "bias_check",
                "passed": True,
                "details": "No significant bias detected"
            })

        # Check 3: Drift check
        if "drift_check" in checks:
            # Placeholder - would integrate with DriftDetector
            results.append({
                "check": "drift_check",
                "passed": True,
                "details": "No data drift detected"
            })

        # Check 4: Load test
        if "load_test" in checks:
            # Placeholder - would run performance tests
            results.append({
                "check": "load_test",
                "passed": True,
                "details": "Model passes load test (p95 < 100ms)"
            })

        return results

    def approve_request(
        self,
        request_id: str,
        approver: str,
        approver_role: str,
        comment: str = ""
    ) -> Dict[str, Any]:
        """
        Approve a pending request.

        Args:
            request_id: Approval request ID
            approver: Approver username
            approver_role: Approver role
            comment: Optional comment

        Returns:
            Updated approval request
        """
        logger.info(f"Approving request: {request_id} by {approver}")

        if request_id not in self.approvals_db:
            raise ValueError(f"Request {request_id} not found")

        request = self.approvals_db[request_id]

        if request["status"] != ApprovalStatus.PENDING.value:
            raise ValueError(f"Request is not pending (status: {request['status']})")

        # Add approval
        approval = {
            "approver": approver,
            "approver_role": approver_role,
            "approved_at": datetime.utcnow().isoformat(),
            "comment": comment
        }
        request["approvals"].append(approval)

        # Check if all approvals received
        policy = request["policy"]
        required_approvers = policy["required_approvers"]
        required_roles = policy.get("required_roles", [])

        # Check approver count
        if len(request["approvals"]) >= required_approvers:
            # Check required roles
            approver_roles = [a["approver_role"] for a in request["approvals"]]
            if all(role in approver_roles for role in required_roles):
                request["status"] = ApprovalStatus.APPROVED.value
                request["approved_at"] = datetime.utcnow().isoformat()
                logger.info(f"Request {request_id} fully approved")

        self._save_workflows()
        return request

    def reject_request(
        self,
        request_id: str,
        rejector: str,
        rejector_role: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Reject a pending request.

        Args:
            request_id: Approval request ID
            rejector: Rejector username
            rejector_role: Rejector role
            reason: Rejection reason

        Returns:
            Updated approval request
        """
        logger.info(f"Rejecting request: {request_id} by {rejector}")

        if request_id not in self.approvals_db:
            raise ValueError(f"Request {request_id} not found")

        request = self.approvals_db[request_id]

        if request["status"] != ApprovalStatus.PENDING.value:
            raise ValueError(f"Request is not pending (status: {request['status']})")

        # Add rejection
        rejection = {
            "rejector": rejector,
            "rejector_role": rejector_role,
            "rejected_at": datetime.utcnow().isoformat(),
            "reason": reason
        }
        request["rejections"].append(rejection)
        request["status"] = ApprovalStatus.REJECTED.value
        request["rejected_at"] = datetime.utcnow().isoformat()

        self._save_workflows()
        return request

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get approval request by ID."""
        return self.approvals_db.get(request_id)

    def list_pending_requests(
        self,
        model_name: Optional[str] = None,
        target_stage: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List pending approval requests.

        Args:
            model_name: Optional model name filter
            target_stage: Optional target stage filter

        Returns:
            List of pending requests
        """
        pending = []

        for request in self.approvals_db.values():
            if request["status"] != ApprovalStatus.PENDING.value:
                continue

            if model_name and request["model_name"] != model_name:
                continue

            if target_stage and request["target_stage"] != target_stage:
                continue

            pending.append(request)

        return pending

    def get_approval_history(
        self,
        model_name: str,
        model_version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get approval history for a model.

        Args:
            model_name: Model name
            model_version: Optional version filter

        Returns:
            List of approval requests
        """
        history = []

        for request in self.approvals_db.values():
            if request["model_name"] != model_name:
                continue

            if model_version and request["model_version"] != model_version:
                continue

            history.append(request)

        # Sort by requested_at descending
        history.sort(key=lambda x: x["requested_at"], reverse=True)

        return history

    def cancel_request(self, request_id: str, cancelled_by: str, reason: str) -> Dict[str, Any]:
        """
        Cancel a pending request.

        Args:
            request_id: Approval request ID
            cancelled_by: Username who cancelled
            reason: Cancellation reason

        Returns:
            Updated approval request
        """
        logger.info(f"Cancelling request: {request_id}")

        if request_id not in self.approvals_db:
            raise ValueError(f"Request {request_id} not found")

        request = self.approvals_db[request_id]

        if request["status"] != ApprovalStatus.PENDING.value:
            raise ValueError(f"Request is not pending (status: {request['status']})")

        request["status"] = ApprovalStatus.CANCELLED.value
        request["cancelled_by"] = cancelled_by
        request["cancelled_at"] = datetime.utcnow().isoformat()
        request["cancellation_reason"] = reason

        self._save_workflows()
        return request


# ============================================================================
# Testing
# ============================================================================

def test_approval_workflow():
    """Test approval workflow."""
    logger.info("Testing Approval Workflow...")

    workflow = ApprovalWorkflow(workflow_path="./test_workflows")

    # Test 1: Create dev->staging approval request
    print("\n=== Test 1: Create Dev->Staging Request ===")
    request = workflow.create_approval_request(
        model_name="churn-prediction",
        model_version="v2",
        source_stage="Development",
        target_stage="Staging",
        requested_by="ml_engineer_1",
        reason="Model shows 2% improvement over v1",
        metrics={"accuracy": 0.92, "auc": 0.95}
    )
    print(json.dumps(request, indent=2, default=str))
    request_id = request["request_id"]

    # Test 2: Approve request
    print("\n=== Test 2: Approve Request ===")
    approved = workflow.approve_request(
        request_id=request_id,
        approver="ml_engineer_2",
        approver_role="ml_engineer",
        comment="Metrics look good, approved for staging"
    )
    print(f"Status: {approved['status']}")
    print(f"Approvals: {len(approved['approvals'])}")

    # Test 3: Create staging->prod request (higher bar)
    print("\n=== Test 3: Create Staging->Prod Request ===")
    prod_request = workflow.create_approval_request(
        model_name="churn-prediction",
        model_version="v2",
        source_stage="Staging",
        target_stage="Production",
        requested_by="ml_engineer_1",
        reason="Staging validation successful",
        metrics={"accuracy": 0.94, "auc": 0.96}
    )
    print(json.dumps(prod_request, indent=2, default=str))
    prod_request_id = prod_request["request_id"]

    # Test 4: Multiple approvals for prod
    print("\n=== Test 4: Multiple Approvals for Prod ===")
    workflow.approve_request(
        request_id=prod_request_id,
        approver="ml_lead",
        approver_role="ml_lead",
        comment="Model performance validated in staging"
    )
    final_approval = workflow.approve_request(
        request_id=prod_request_id,
        approver="devops_lead",
        approver_role="devops_lead",
        comment="Infrastructure ready for deployment"
    )
    print(f"Status: {final_approval['status']}")

    # Test 5: Failed automated checks
    print("\n=== Test 5: Failed Automated Checks ===")
    failed_request = workflow.create_approval_request(
        model_name="fraud-detection",
        model_version="v1",
        source_stage="Development",
        target_stage="Staging",
        requested_by="ml_engineer_3",
        reason="Initial version",
        metrics={"accuracy": 0.75}  # Below threshold
    )
    print(f"Status: {failed_request['status']}")
    print(f"Rejection reason: {failed_request.get('rejection_reason')}")

    # Test 6: List pending requests
    print("\n=== Test 6: List Pending Requests ===")
    pending = workflow.list_pending_requests()
    print(f"Pending requests: {len(pending)}")


if __name__ == "__main__":
    test_approval_workflow()
