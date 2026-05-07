"""
MLOps API Routes for PromptOps
================================

API endpoints for ML operations:
- ML command parsing
- Model training
- Model deployment
- Model monitoring
- Hyperparameter tuning
- Model explanations

Author: Backend Engineer - Phase 5 Week 40-41
Date: 2026-05-07
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import sys
import os
import logging

# Add phase5-mlops to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase5-mlops'))

from ml_intent_parser.ml_intent_classifier import MLIntentClassifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/mlops", tags=["mlops"])

# Initialize ML Intent Classifier
ml_classifier = MLIntentClassifier()


# ============================================================================
# Request/Response Models
# ============================================================================

class MLCommandRequest(BaseModel):
    """Request model for ML command parsing."""
    command: str = Field(..., description="Plain English ML command", min_length=1)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")

    class Config:
        json_schema_extra = {
            "example": {
                "command": "Train a churn prediction model using last 90 days of user data",
                "context": {"user_id": "pm_123", "project": "customer_retention"}
            }
        }


class MLCommandResponse(BaseModel):
    """Response model for ML command parsing."""
    success: bool
    intent: str
    confidence: float
    command: str
    parameters: Dict[str, Any]
    method: str
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "intent": "train_model",
                "confidence": 0.95,
                "command": "Train a churn prediction model...",
                "parameters": {
                    "model_type": "churn_prediction",
                    "time_range": "90_days"
                },
                "method": "pattern_match"
            }
        }


class GoldenTestValidationResponse(BaseModel):
    """Response model for golden test validation."""
    total_tests: int
    correct: int
    accuracy: float
    target_accuracy: float
    passed: bool
    results: List[Dict[str, Any]]


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/parse", response_model=MLCommandResponse)
async def parse_ml_command(request: MLCommandRequest):
    """
    Parse ML command and classify intent.

    **Supported Intents:**
    - `train_model`: Train new ML models
    - `deploy_model`: Deploy models to environments
    - `monitor_model`: Monitor model performance
    - `retrain_model`: Retrain with new data
    - `tune_hyperparameters`: Optimize model parameters
    - `explain_prediction`: Explain model decisions

    **Example Commands:**
    - "Train a churn model on last 90 days data"
    - "Deploy fraud detection v2.3 with canary rollout"
    - "Alert if accuracy drops below 85%"
    - "Retrain pricing model weekly"
    - "Find best hyperparameters for XGBoost"
    - "Explain why transaction #12345 was flagged"
    """
    try:
        logger.info(f"Parsing ML command: {request.command[:100]}...")

        # Classify ML intent
        result = ml_classifier.classify(request.command)

        # Build response
        response = MLCommandResponse(
            success=True,
            intent=result.get('intent', 'unknown'),
            confidence=result.get('confidence', 0.0),
            command=request.command,
            parameters=result.get('parameters', {}),
            method=result.get('method', 'unknown'),
            suggestions=result.get('suggestions'),
            error=result.get('error')
        )

        return response

    except Exception as e:
        logger.error(f"ML command parsing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse ML command: {str(e)}"
        )


@router.get("/intents")
async def get_ml_intents():
    """
    Get list of supported ML intent categories.

    Returns available ML operations and examples.
    """
    return {
        "intents": [
            {
                "name": "train_model",
                "description": "Train new ML models",
                "examples": [
                    "Train a churn model on last 90 days data",
                    "Train sentiment analysis on customer reviews"
                ]
            },
            {
                "name": "deploy_model",
                "description": "Deploy models to environments",
                "examples": [
                    "Deploy fraud model v2.3 to production",
                    "Deploy with canary rollout strategy"
                ]
            },
            {
                "name": "monitor_model",
                "description": "Monitor model performance",
                "examples": [
                    "Alert if accuracy drops below 85%",
                    "Check for prediction drift"
                ]
            },
            {
                "name": "retrain_model",
                "description": "Retrain with new data",
                "examples": [
                    "Retrain pricing model weekly",
                    "Retrain when drift is detected"
                ]
            },
            {
                "name": "tune_hyperparameters",
                "description": "Optimize model parameters",
                "examples": [
                    "Find best hyperparameters for XGBoost",
                    "Tune learning rate and batch size"
                ]
            },
            {
                "name": "explain_prediction",
                "description": "Explain model decisions",
                "examples": [
                    "Explain why transaction #12345 was flagged",
                    "Show feature importance for prediction"
                ]
            }
        ],
        "total": 6
    }


@router.get("/commands/examples")
async def get_example_commands():
    """
    Get example ML commands for each intent category.

    Useful for PM training and documentation.
    """
    return {
        "examples": [
            {
                "intent": "train_model",
                "commands": [
                    "Train a customer churn model using last 90 days of user activity",
                    "Train fraud detection model on Q1 2026 transactions",
                    "Train sentiment analysis on latest customer reviews"
                ]
            },
            {
                "intent": "deploy_model",
                "commands": [
                    "Deploy fraud detection v2.3 to production with 99.9% SLA",
                    "Deploy with canary rollout 5% first",
                    "Roll back recommendation model to v1.2"
                ]
            },
            {
                "intent": "monitor_model",
                "commands": [
                    "Alert me if recommendation model accuracy drops below 85%",
                    "Check if churn model has prediction drift this week",
                    "Show p95 latency for all deployed models"
                ]
            },
            {
                "intent": "retrain_model",
                "commands": [
                    "Retrain pricing model weekly using latest data",
                    "Retrain when drift is detected",
                    "Schedule automatic retraining every Sunday at 2 AM"
                ]
            },
            {
                "intent": "tune_hyperparameters",
                "commands": [
                    "Find best hyperparameters for pricing model, optimize for RMSE",
                    "Tune XGBoost with max budget $500",
                    "Optimize learning rate and batch size"
                ]
            },
            {
                "intent": "explain_prediction",
                "commands": [
                    "Explain why transaction #12345 was flagged as fraud",
                    "Show feature importance for churn prediction",
                    "Generate SHAP explanation for pricing decision"
                ]
            }
        ]
    }


@router.get("/validate/golden-tests", response_model=GoldenTestValidationResponse)
async def validate_golden_tests():
    """
    Run golden test validation on ML Intent Classifier.

    Validates classifier against 30 golden test commands.
    Target accuracy: 90%+
    """
    try:
        logger.info("Running golden test validation...")

        validation = ml_classifier.validate_against_golden_tests()

        response = GoldenTestValidationResponse(
            total_tests=validation['total_tests'],
            correct=validation['correct'],
            accuracy=validation['accuracy'],
            target_accuracy=validation['target_accuracy'],
            passed=validation['passed'],
            results=validation['results']
        )

        return response

    except Exception as e:
        logger.error(f"Golden test validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/health")
async def mlops_health():
    """
    Check MLOps service health.

    Returns status of ML classifier and dependencies.
    """
    # Check if ML classifier is loaded
    classifier_loaded = ml_classifier is not None

    # Check if command library is loaded
    library_loaded = len(ml_classifier.command_library.get('intent_categories', [])) > 0

    # Check API key (optional for pattern matching)
    api_key_present = bool(ml_classifier.api_key)

    return {
        "status": "healthy" if (classifier_loaded and library_loaded) else "degraded",
        "components": {
            "ml_classifier": "ok" if classifier_loaded else "error",
            "command_library": "ok" if library_loaded else "error",
            "claude_api": "configured" if api_key_present else "not_configured (pattern_match_only)",
            "total_commands": len(ml_classifier.command_library.get('golden_test_commands', []))
        },
        "version": "1.0.0",
        "phase": "5_week_40-41"
    }


# ============================================================================
# Future Endpoints (Placeholders)
# ============================================================================

@router.post("/train")
async def train_model():
    """
    [PLACEHOLDER - Week 42-43]

    Trigger model training pipeline.
    Will integrate with SageMaker in Week 42-43.
    """
    return {
        "status": "not_implemented",
        "message": "Model training will be implemented in Phase 5 Week 42-43",
        "coming_soon": True
    }


@router.post("/deploy")
async def deploy_model():
    """
    [PLACEHOLDER - Week 44-45]

    Deploy model with shadow testing and canary rollout.
    Will be implemented in Week 44-45.
    """
    return {
        "status": "not_implemented",
        "message": "Model deployment will be implemented in Phase 5 Week 44-45",
        "coming_soon": True
    }


@router.get("/monitor")
async def monitor_models():
    """
    [PLACEHOLDER - Week 46-47]

    Monitor model performance and drift.
    Will be implemented in Week 46-47.
    """
    return {
        "status": "not_implemented",
        "message": "Model monitoring will be implemented in Phase 5 Week 46-47",
        "coming_soon": True
    }
