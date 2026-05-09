"""
Governance API Routes for PromptOps
====================================

API endpoints for ML governance:
- Model registry operations
- Approval workflows
- Model explainability
- Bias detection
- Audit trail

Author: Backend Engineer - Phase 5 Week 50-51
Date: 2026-05-09
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import sys
import os
import logging
from datetime import datetime

# Add phase5-mlops to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase5-mlops'))

from governance.model_registry import ModelRegistry
from governance.approval_workflow import ApprovalWorkflow
from governance.explainability_engine import ExplainabilityEngine
from governance.bias_detector import BiasDetector
from governance.audit_trail import AuditTrail, EventType, Severity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/governance", tags=["governance"])

# Initialize components
model_registry = ModelRegistry()
approval_workflow = ApprovalWorkflow()
explainability_engine = ExplainabilityEngine()
bias_detector = BiasDetector()
audit_trail = AuditTrail()


# ============================================================================
# Request/Response Models
# ============================================================================

class RegisterModelRequest(BaseModel):
    """Request to register model."""
    name: str
    model_uri: str
    framework: str
    version: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    params: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, str]] = None
    description: str = ""


class StageTransitionRequest(BaseModel):
    """Request to transition model stage."""
    name: str
    version: str
    stage: str
    archive_existing: bool = True


class ApprovalRequest(BaseModel):
    """Request to create approval."""
    model_name: str
    model_version: str
    source_stage: str
    target_stage: str
    requested_by: str
    reason: str = ""
    metrics: Optional[Dict[str, float]] = None


class ApprovalActionRequest(BaseModel):
    """Request to approve/reject."""
    approver: str
    approver_role: str
    comment: str = ""


class ExplainPredictionRequest(BaseModel):
    """Request to explain prediction."""
    model_name: str
    model_version: str
    prediction: float
    features: Dict[str, Any]
    feature_names: List[str]
    base_value: float = 0.5


class BiasDetectionRequest(BaseModel):
    """Request to detect bias."""
    model_name: str
    model_version: str
    predictions: List[int]
    true_labels: List[int]
    protected_attributes: Dict[str, List[str]]


class AuditEventRequest(BaseModel):
    """Request to log audit event."""
    event_type: str
    resource_type: str
    resource_id: str
    actor: str
    action: str
    details: Optional[Dict[str, Any]] = None
    severity: str = "info"


# ============================================================================
# Model Registry Endpoints
# ============================================================================

@router.post("/registry/models")
async def register_model(request: RegisterModelRequest):
    """
    Register a new model version.

    **Frameworks:** xgboost, tensorflow, pytorch, sklearn, etc.
    """
    try:
        model = model_registry.register_model(
            name=request.name,
            model_uri=request.model_uri,
            framework=request.framework,
            version=request.version,
            metrics=request.metrics,
            params=request.params,
            tags=request.tags,
            description=request.description
        )

        # Log audit event
        audit_trail.log_event(
            event_type=EventType.MODEL_REGISTERED.value,
            resource_type="model",
            resource_id=f"{request.name}:{model['version']}",
            actor="system",
            action=f"Registered model {request.name} version {model['version']}",
            details={"framework": request.framework, "metrics": request.metrics}
        )

        return model

    except Exception as e:
        logger.error(f"Failed to register model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/models")
async def list_models(stage: Optional[str] = None):
    """List all registered models."""
    try:
        models = model_registry.list_models(stage=stage)
        return {"total": len(models), "models": models}
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/models/{name}/{version}")
async def get_model_version(name: str, version: str):
    """Get specific model version."""
    try:
        model = model_registry.get_model_version(name, version)
        if not model:
            raise HTTPException(status_code=404, detail="Model version not found")
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/models/{name}/latest")
async def get_latest_model(name: str, stage: Optional[str] = None):
    """Get latest model version."""
    try:
        model = model_registry.get_latest_version(name, stage=stage)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/registry/models/transition")
async def transition_stage(request: StageTransitionRequest):
    """
    Transition model to new stage.

    **Stages:** Development, Staging, Production, Archived
    """
    try:
        model = model_registry.transition_stage(
            name=request.name,
            version=request.version,
            stage=request.stage,
            archive_existing=request.archive_existing
        )

        # Log audit event
        audit_trail.log_event(
            event_type=EventType.STAGE_TRANSITION.value,
            resource_type="model",
            resource_id=f"{request.name}:{request.version}",
            actor="system",
            action=f"Transitioned to {request.stage}",
            details={"stage": request.stage}
        )

        return model

    except Exception as e:
        logger.error(f"Failed to transition stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/stats")
async def get_registry_stats():
    """Get model registry statistics."""
    return model_registry.get_registry_stats()


# ============================================================================
# Approval Workflow Endpoints
# ============================================================================

@router.post("/approvals/requests")
async def create_approval_request(request: ApprovalRequest):
    """
    Create approval request for stage transition.

    **Workflow Stages:**
    - Development → Staging (requires 1 ML engineer)
    - Staging → Production (requires ML lead + DevOps lead)
    """
    try:
        approval_request = approval_workflow.create_approval_request(
            model_name=request.model_name,
            model_version=request.model_version,
            source_stage=request.source_stage,
            target_stage=request.target_stage,
            requested_by=request.requested_by,
            reason=request.reason,
            metrics=request.metrics
        )

        # Log audit event
        audit_trail.log_event(
            event_type=EventType.APPROVAL_REQUESTED.value,
            resource_type="approval",
            resource_id=approval_request["request_id"],
            actor=request.requested_by,
            action=f"Requested approval: {request.source_stage}→{request.target_stage}",
            details={"model": f"{request.model_name}:{request.model_version}"}
        )

        return approval_request

    except Exception as e:
        logger.error(f"Failed to create approval request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approvals/requests/{request_id}/approve")
async def approve_request(request_id: str, action: ApprovalActionRequest):
    """Approve a pending approval request."""
    try:
        result = approval_workflow.approve_request(
            request_id=request_id,
            approver=action.approver,
            approver_role=action.approver_role,
            comment=action.comment
        )

        # Log audit event
        audit_trail.log_event(
            event_type=EventType.APPROVAL_GRANTED.value,
            resource_type="approval",
            resource_id=request_id,
            actor=action.approver,
            action="Approved request",
            details={"comment": action.comment, "status": result["status"]}
        )

        return result

    except Exception as e:
        logger.error(f"Failed to approve request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approvals/requests/{request_id}/reject")
async def reject_request(request_id: str, action: ApprovalActionRequest):
    """Reject a pending approval request."""
    try:
        # Require reason for rejection
        if not action.comment:
            raise HTTPException(status_code=400, detail="Rejection reason required")

        result = approval_workflow.reject_request(
            request_id=request_id,
            rejector=action.approver,
            rejector_role=action.approver_role,
            reason=action.comment
        )

        # Log audit event
        audit_trail.log_event(
            event_type=EventType.APPROVAL_REJECTED.value,
            resource_type="approval",
            resource_id=request_id,
            actor=action.approver,
            action="Rejected request",
            details={"reason": action.comment},
            severity=Severity.WARNING.value
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals/pending")
async def list_pending_approvals(
    model_name: Optional[str] = None,
    target_stage: Optional[str] = None
):
    """List pending approval requests."""
    try:
        pending = approval_workflow.list_pending_requests(
            model_name=model_name,
            target_stage=target_stage
        )
        return {"total": len(pending), "requests": pending}
    except Exception as e:
        logger.error(f"Failed to list pending approvals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals/history/{model_name}")
async def get_approval_history(model_name: str, model_version: Optional[str] = None):
    """Get approval history for a model."""
    try:
        history = approval_workflow.get_approval_history(
            model_name=model_name,
            model_version=model_version
        )
        return {"total": len(history), "history": history}
    except Exception as e:
        logger.error(f"Failed to get approval history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Explainability Endpoints
# ============================================================================

@router.post("/explainability/predict")
async def explain_prediction(request: ExplainPredictionRequest):
    """
    Explain individual prediction using SHAP values.

    Returns feature contributions and human-readable explanation.
    """
    try:
        explanation = explainability_engine.explain_prediction(
            model_name=request.model_name,
            model_version=request.model_version,
            prediction=request.prediction,
            features=request.features,
            feature_names=request.feature_names,
            base_value=request.base_value
        )
        return explanation
    except Exception as e:
        logger.error(f"Failed to explain prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explainability/importance/{model_name}/{model_version}")
async def get_feature_importance(
    model_name: str,
    model_version: str,
    feature_names: str  # Comma-separated
):
    """Get global feature importance for model."""
    try:
        features = feature_names.split(",")
        importance = explainability_engine.compute_feature_importance(
            model_name=model_name,
            model_version=model_version,
            feature_names=features
        )
        return importance
    except Exception as e:
        logger.error(f"Failed to compute feature importance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explainability/behavior/{model_name}/{model_version}")
async def analyze_model_behavior(
    model_name: str,
    model_version: str,
    feature_names: str,  # Comma-separated
    num_samples: int = 100
):
    """Comprehensive model behavior analysis."""
    try:
        features = feature_names.split(",")
        analysis = explainability_engine.explain_model_behavior(
            model_name=model_name,
            model_version=model_version,
            feature_names=features,
            num_samples=num_samples
        )
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze model behavior: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Bias Detection Endpoints
# ============================================================================

@router.post("/bias/detect")
async def detect_bias(request: BiasDetectionRequest):
    """
    Detect bias in model predictions across protected attributes.

    **Fairness Metrics:**
    - Demographic Parity
    - Equalized Odds (TPR, FPR)
    - Equal Opportunity
    - Predictive Parity

    **Protected Attributes:** gender, race, age_group, etc.
    """
    try:
        report = bias_detector.detect_bias(
            model_name=request.model_name,
            model_version=request.model_version,
            predictions=request.predictions,
            true_labels=request.true_labels,
            protected_attributes=request.protected_attributes
        )

        # Log audit event if bias detected
        if report["bias_detected"]:
            audit_trail.log_event(
                event_type=EventType.BIAS_CHECK.value,
                resource_type="model",
                resource_id=f"{request.model_name}:{request.model_version}",
                actor="system",
                action="Bias detected",
                details={"violations": len(report["violations"])},
                severity=Severity.WARNING.value
            )

        return report

    except Exception as e:
        logger.error(f"Failed to detect bias: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bias/summary")
async def get_bias_summary(report: Dict[str, Any]):
    """Generate human-readable bias summary from report."""
    try:
        summary = bias_detector.get_bias_summary(report)
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Failed to generate bias summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Audit Trail Endpoints
# ============================================================================

@router.post("/audit/events")
async def log_audit_event(request: AuditEventRequest):
    """Log an audit event."""
    try:
        event = audit_trail.log_event(
            event_type=request.event_type,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            actor=request.actor,
            action=request.action,
            details=request.details,
            severity=request.severity
        )
        return event
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/events")
async def query_audit_events(
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    actor: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100
):
    """Query audit events with filters."""
    try:
        events = audit_trail.query_events(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            actor=actor,
            severity=severity,
            limit=limit
        )
        return {"total": len(events), "events": events}
    except Exception as e:
        logger.error(f"Failed to query audit events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/resources/{resource_type}/{resource_id}")
async def get_resource_audit_history(resource_type: str, resource_id: str):
    """Get complete audit history for a resource."""
    try:
        history = audit_trail.get_resource_history(
            resource_type=resource_type,
            resource_id=resource_id
        )
        return {"total": len(history), "history": history}
    except Exception as e:
        logger.error(f"Failed to get resource history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/compliance")
async def get_compliance_report(days: int = 30):
    """
    Generate compliance report for specified time period.

    **Compliance Standards:** SOC2, GDPR, HIPAA audit requirements
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        report = audit_trail.get_compliance_report(
            start_date=start_date,
            end_date=end_date
        )
        return report
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/integrity")
async def verify_audit_integrity():
    """Verify integrity of audit trail using hash chain."""
    try:
        result = audit_trail.verify_integrity()
        return result
    except Exception as e:
        logger.error(f"Failed to verify integrity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Endpoint
# ============================================================================

@router.get("/health")
async def governance_health():
    """Check governance service health."""
    registry_stats = model_registry.get_registry_stats()

    return {
        "status": "healthy",
        "components": {
            "model_registry": "ok",
            "approval_workflow": "ok",
            "explainability_engine": "ok",
            "bias_detector": "ok",
            "audit_trail": "ok"
        },
        "registry_stats": registry_stats,
        "version": "1.0.0",
        "phase": "5_week_50-51"
    }


# Missing import for timedelta
from datetime import timedelta
