"""
ML Governance Module for PromptOps
===================================

Provides model governance, compliance, and explainability features:
- Model Registry (versioning, metadata)
- Approval Workflow (dev→staging→prod)
- Model Explainability (SHAP)
- Bias Detection (Fairlearn)
- Audit Trail (compliance logging)

Author: ML Engineer - Phase 5 Week 50-51
Date: 2026-05-09
"""

from .model_registry import ModelRegistry
from .approval_workflow import ApprovalWorkflow
from .explainability_engine import ExplainabilityEngine
from .bias_detector import BiasDetector
from .audit_trail import AuditTrail

__all__ = [
    'ModelRegistry',
    'ApprovalWorkflow',
    'ExplainabilityEngine',
    'BiasDetector',
    'AuditTrail'
]

__version__ = "1.0.0"
