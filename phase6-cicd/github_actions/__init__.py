"""
GitHub Actions Integration Module for PromptOps
================================================

GitHub Actions workflow generation and management:
- Workflow generator (CI, CD, security, release)
- Hybrid orchestration with Jenkins
- GitHub API client

Author: DevOps Engineer - Phase 6 Week 54-55
Date: 2026-05-10
"""

from .workflow_generator import WorkflowGenerator
from .actions_integrator import ActionsIntegrator
from .github_api_client import GitHubAPIClient

__all__ = [
    'WorkflowGenerator',
    'ActionsIntegrator',
    'GitHubAPIClient'
]

__version__ = "1.0.0"
