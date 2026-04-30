"""
Discovery & Onboarding Module
==============================

Automated AWS resource discovery and intelligent onboarding.

Week 16-18: ENHANCEMENT-003
Author: PromptOps Team
Date: 2026-04-30
"""

from .aws_scanner import AWSScanner, ResourceInventory
from .context_inference import ContextInferenceEngine
from .dependency_mapper import DependencyMapper

__all__ = [
    'AWSScanner',
    'ResourceInventory',
    'ContextInferenceEngine',
    'DependencyMapper',
]
