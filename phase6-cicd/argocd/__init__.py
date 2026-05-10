"""
ArgoCD GitOps Integration Module for PromptOps
===============================================

ArgoCD application generation and GitOps management:
- Application manifest generator
- GitOps repository management
- ArgoCD API client

Author: DevOps Engineer - Phase 6 Week 56-57
Date: 2026-05-10
"""

from .app_generator import AppGenerator
from .gitops_manager import GitOpsManager
from .argocd_api_client import ArgoCDAPIClient

__all__ = [
    'AppGenerator',
    'GitOpsManager',
    'ArgoCDAPIClient'
]

__version__ = "1.0.0"
