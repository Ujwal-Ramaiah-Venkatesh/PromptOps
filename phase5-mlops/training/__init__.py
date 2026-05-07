"""
Training Pipeline Module for PromptOps
======================================

Phase 5 Week 42-43: Model Training Pipeline

Modules:
- sagemaker_training_generator: Generate SageMaker training jobs
- training_data_validator: Validate training data quality
- mlflow_experiment_tracker: Track experiments with MLflow
- training_cost_estimator: Estimate training costs

Author: ML Engineer - Phase 5 Week 42-43
Date: 2026-05-07
"""

from .sagemaker_training_generator import SageMakerTrainingGenerator
from .training_data_validator import TrainingDataValidator
from .mlflow_experiment_tracker import MLflowExperimentTracker
from .training_cost_estimator import TrainingCostEstimator

__all__ = [
    'SageMakerTrainingGenerator',
    'TrainingDataValidator',
    'MLflowExperimentTracker',
    'TrainingCostEstimator'
]

__version__ = '1.0.0'
__phase__ = 'Phase 5 Week 42-43'
