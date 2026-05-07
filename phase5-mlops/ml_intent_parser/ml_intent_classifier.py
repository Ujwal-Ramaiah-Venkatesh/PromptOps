"""
ML Intent Classifier for PromptOps
===================================

This module extends the NLP Parser to understand ML-specific commands.
Integrates with Claude Sonnet 4 for intelligent ML intent classification.

6 ML Intent Categories:
- train_model: Training new models
- deploy_model: Deploying models to environments
- monitor_model: Monitoring model performance
- retrain_model: Retraining with new data
- tune_hyperparameters: Optimizing model parameters
- explain_prediction: Explaining model decisions

Author: ML Engineer - Phase 5 Week 40-41
Date: 2026-05-07
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ML Intent Classification
# ============================================================================

class MLIntentClassifier:
    """
    Classifies ML-specific commands into intent categories using Claude Sonnet 4.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ML Intent Classifier.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set. ML classification will fail.")

        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        self.model_name = "claude-sonnet-4-20250514"

        # Load ML command library
        self.command_library = self._load_command_library()

        # Intent categories
        self.intent_categories = [
            "train_model",
            "deploy_model",
            "monitor_model",
            "retrain_model",
            "tune_hyperparameters",
            "explain_prediction"
        ]

    def _load_command_library(self) -> Dict[str, Any]:
        """Load ML command library from JSON file."""
        try:
            library_path = os.path.join(
                os.path.dirname(__file__),
                'ml_command_library.json'
            )
            with open(library_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load ML command library: {e}")
            return {"intent_categories": [], "golden_test_commands": []}

    def classify(self, command: str) -> Dict[str, Any]:
        """
        Classify ML command into intent category.

        Args:
            command: Plain English ML command from PM

        Returns:
            Dictionary with intent, confidence, parameters, and metadata
        """
        logger.info(f"Classifying ML command: {command[:100]}...")

        # Quick pattern matching for simple cases
        pattern_match = self._pattern_match(command)
        if pattern_match and pattern_match['confidence'] > 0.85:
            logger.info(f"Pattern match successful: {pattern_match['intent']}")
            return pattern_match

        # Use Claude Sonnet 4 for complex classification
        if self.client:
            claude_result = self._classify_with_claude(command)
            if claude_result:
                return claude_result

        # Fallback to pattern matching if Claude fails
        if pattern_match:
            return pattern_match

        # Unknown intent
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "command": command,
            "error": "Unable to classify ML intent",
            "suggestions": [
                "Try: 'Train a model...'",
                "Try: 'Deploy model v1.0...'",
                "Try: 'Monitor model performance...'"
            ]
        }

    def _pattern_match(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Fast pattern matching for common ML command patterns.

        Args:
            command: User command

        Returns:
            Classification result if pattern matches, None otherwise
        """
        command_lower = command.lower()
        words = command.split()

        # Train model patterns
        if any(word in command_lower for word in ['train', 'training', 'build model', 'create model']):
            return {
                "intent": "train_model",
                "confidence": 0.90,
                "command": command,
                "method": "pattern_match",
                "parameters": self._extract_train_parameters(command_lower)
            }

        # Deploy model patterns
        elif any(word in command_lower for word in ['deploy', 'deployment', 'release', 'rollback', 'roll back']):
            return {
                "intent": "deploy_model",
                "confidence": 0.92,
                "command": command,
                "method": "pattern_match",
                "parameters": self._extract_deploy_parameters(command_lower)
            }

        # Monitor model patterns
        elif any(word in command_lower for word in ['monitor', 'alert', 'check', 'show', 'display', 'metrics', 'performance']):
            if any(word in command_lower for word in ['model', 'accuracy', 'drift', 'latency', 'error rate']):
                return {
                    "intent": "monitor_model",
                    "confidence": 0.88,
                    "command": command,
                    "method": "pattern_match",
                    "parameters": self._extract_monitor_parameters(command_lower)
                }

        # Retrain model patterns
        elif any(word in command_lower for word in ['retrain', 're-train', 'update model', 'refresh model']):
            return {
                "intent": "retrain_model",
                "confidence": 0.91,
                "command": command,
                "method": "pattern_match",
                "parameters": self._extract_retrain_parameters(command_lower)
            }

        # Tune hyperparameters patterns
        elif any(word in command_lower for word in ['tune', 'optimize', 'hyperparameter', 'parameter', 'optimize']):
            if 'hyperparameter' in command_lower or ('find' in command_lower and 'best' in command_lower):
                return {
                    "intent": "tune_hyperparameters",
                    "confidence": 0.87,
                    "command": command,
                    "method": "pattern_match",
                    "parameters": self._extract_tune_parameters(command_lower)
                }

        # Explain prediction patterns
        elif any(word in command_lower for word in ['explain', 'why', 'show feature', 'importance', 'shap', 'interpret']):
            if any(word in command_lower for word in ['prediction', 'model', 'decision', 'result', 'flagged']):
                return {
                    "intent": "explain_prediction",
                    "confidence": 0.89,
                    "command": command,
                    "method": "pattern_match",
                    "parameters": self._extract_explain_parameters(command_lower)
                }

        return None

    def _extract_train_parameters(self, command: str) -> Dict[str, Any]:
        """Extract parameters from train model command."""
        params = {
            "model_type": "unknown",
            "data_source": "unknown",
            "time_range": None
        }

        # Detect model type
        if 'churn' in command:
            params['model_type'] = 'churn_prediction'
        elif 'fraud' in command:
            params['model_type'] = 'fraud_detection'
        elif 'recommendation' in command or 'recommend' in command:
            params['model_type'] = 'recommendation'
        elif 'sentiment' in command:
            params['model_type'] = 'sentiment_analysis'
        elif 'forecast' in command or 'forecasting' in command:
            params['model_type'] = 'forecasting'
        elif 'classification' in command or 'classify' in command:
            params['model_type'] = 'classification'
        elif 'regression' in command:
            params['model_type'] = 'regression'

        # Extract time range
        if '90 days' in command or '90 day' in command:
            params['time_range'] = '90_days'
        elif '30 days' in command or '30 day' in command:
            params['time_range'] = '30_days'
        elif 'q1' in command or 'quarter 1' in command:
            params['time_range'] = 'Q1'
        elif 'last week' in command:
            params['time_range'] = 'last_week'
        elif 'last month' in command:
            params['time_range'] = 'last_month'

        return params

    def _extract_deploy_parameters(self, command: str) -> Dict[str, Any]:
        """Extract parameters from deploy model command."""
        params = {
            "model_name": "unknown",
            "version": None,
            "environment": "production",
            "strategy": "standard"
        }

        # Extract version (v1.0, v2.3, version 1.5, etc.)
        import re
        version_match = re.search(r'v[\d\.]+|version\s+[\d\.]+', command)
        if version_match:
            params['version'] = version_match.group().replace('version ', '').replace('v', '')

        # Detect environment
        if 'staging' in command or 'stage' in command:
            params['environment'] = 'staging'
        elif 'production' in command or 'prod' in command:
            params['environment'] = 'production'

        # Detect deployment strategy
        if 'canary' in command:
            params['strategy'] = 'canary'
        elif 'blue-green' in command or 'blue green' in command:
            params['strategy'] = 'blue-green'
        elif 'shadow' in command:
            params['strategy'] = 'shadow'
        elif 'rollback' in command or 'roll back' in command:
            params['strategy'] = 'rollback'

        # Detect model name
        if 'fraud' in command:
            params['model_name'] = 'fraud_detection'
        elif 'recommendation' in command or 'recommend' in command:
            params['model_name'] = 'recommendation'
        elif 'churn' in command:
            params['model_name'] = 'churn_prediction'
        elif 'pricing' in command:
            params['model_name'] = 'pricing'

        return params

    def _extract_monitor_parameters(self, command: str) -> Dict[str, Any]:
        """Extract parameters from monitor model command."""
        params = {
            "model_name": "unknown",
            "metric": "accuracy",
            "threshold": None,
            "condition": "less_than"
        }

        # Detect metric
        if 'accuracy' in command:
            params['metric'] = 'accuracy'
        elif 'drift' in command:
            params['metric'] = 'drift'
        elif 'latency' in command:
            params['metric'] = 'latency'
        elif 'error rate' in command or 'error' in command:
            params['metric'] = 'error_rate'
        elif 'bias' in command:
            params['metric'] = 'bias'

        # Extract threshold
        import re
        threshold_match = re.search(r'(\d+)%', command)
        if threshold_match:
            params['threshold'] = float(threshold_match.group(1)) / 100

        # Detect condition
        if 'below' in command or 'less than' in command or 'drops' in command:
            params['condition'] = 'less_than'
        elif 'above' in command or 'exceeds' in command or 'greater than' in command:
            params['condition'] = 'greater_than'

        return params

    def _extract_retrain_parameters(self, command: str) -> Dict[str, Any]:
        """Extract parameters from retrain model command."""
        params = {
            "model_name": "unknown",
            "trigger": "manual",
            "schedule": None,
            "automatic": False
        }

        # Detect schedule
        if 'weekly' in command or 'every week' in command:
            params['schedule'] = 'weekly'
            params['automatic'] = True
        elif 'daily' in command or 'every day' in command:
            params['schedule'] = 'daily'
            params['automatic'] = True
        elif 'monthly' in command or 'every month' in command:
            params['schedule'] = 'monthly'
            params['automatic'] = True
        elif 'quarterly' in command:
            params['schedule'] = 'quarterly'
            params['automatic'] = True

        # Detect trigger
        if 'drift' in command:
            params['trigger'] = 'drift_detected'
            params['automatic'] = True
        elif 'accuracy' in command and 'drops' in command:
            params['trigger'] = 'accuracy_threshold'
            params['automatic'] = True

        return params

    def _extract_tune_parameters(self, command: str) -> Dict[str, Any]:
        """Extract parameters from tune hyperparameters command."""
        params = {
            "model_type": "unknown",
            "optimization_metric": "accuracy",
            "budget_limit": None
        }

        # Detect optimization metric
        if 'rmse' in command or 'root mean square' in command:
            params['optimization_metric'] = 'rmse'
        elif 'precision' in command:
            params['optimization_metric'] = 'precision'
        elif 'recall' in command:
            params['optimization_metric'] = 'recall'
        elif 'f1' in command:
            params['optimization_metric'] = 'f1_score'
        elif 'auc' in command:
            params['optimization_metric'] = 'auc'

        # Extract budget
        import re
        budget_match = re.search(r'\$(\d+)', command)
        if budget_match:
            params['budget_limit'] = int(budget_match.group(1))

        return params

    def _extract_explain_parameters(self, command: str) -> Dict[str, Any]:
        """Extract parameters from explain prediction command."""
        params = {
            "model_name": "unknown",
            "explanation_type": "feature_importance",
            "prediction_id": None
        }

        # Extract ID
        import re
        id_match = re.search(r'#(\d+)|id\s+(\d+)|transaction\s+(\d+)|customer\s+(\d+)', command)
        if id_match:
            params['prediction_id'] = id_match.group(1) or id_match.group(2) or id_match.group(3) or id_match.group(4)

        # Detect explanation type
        if 'shap' in command:
            params['explanation_type'] = 'shap'
        elif 'counterfactual' in command:
            params['explanation_type'] = 'counterfactual'
        elif 'feature' in command and 'importance' in command:
            params['explanation_type'] = 'feature_importance'

        return params

    def _classify_with_claude(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Classify command using Claude Sonnet 4.

        Args:
            command: User command

        Returns:
            Classification result
        """
        try:
            # Build system prompt with ML intent examples
            system_prompt = self._build_ml_system_prompt()

            # Call Claude API
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=2048,
                temperature=0.0,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Classify this ML command: {command}"
                    }
                ]
            )

            # Parse response
            result_text = response.content[0].text
            result = json.loads(result_text)

            # Add metadata
            result['method'] = 'claude_sonnet_4'
            result['command'] = command
            result['model'] = self.model_name

            logger.info(f"Claude classification: {result['intent']} (confidence: {result['confidence']})")

            return result

        except Exception as e:
            logger.error(f"Claude classification failed: {e}")
            return None

    def _build_ml_system_prompt(self) -> str:
        """Build system prompt with ML intent examples."""
        prompt = """You are an ML Intent Classifier for PromptOps MLOps platform.

Your task is to classify ML commands into one of 6 intent categories:
1. train_model: Training new models
2. deploy_model: Deploying models to environments
3. monitor_model: Monitoring model performance
4. retrain_model: Retraining with new data
5. tune_hyperparameters: Optimizing model parameters
6. explain_prediction: Explaining model decisions

Examples:

"Train a churn model on last 90 days data"
→ {"intent": "train_model", "confidence": 0.95, "parameters": {"model_type": "churn_prediction", "time_range": "90_days"}}

"Deploy fraud model v2.3 with canary rollout"
→ {"intent": "deploy_model", "confidence": 0.93, "parameters": {"model_name": "fraud_detection", "version": "2.3", "strategy": "canary"}}

"Alert if accuracy drops below 85%"
→ {"intent": "monitor_model", "confidence": 0.91, "parameters": {"metric": "accuracy", "threshold": 0.85, "condition": "less_than"}}

"Retrain pricing model weekly"
→ {"intent": "retrain_model", "confidence": 0.94, "parameters": {"model_name": "pricing", "schedule": "weekly", "automatic": true}}

"Find best hyperparameters for XGBoost"
→ {"intent": "tune_hyperparameters", "confidence": 0.89, "parameters": {"model_type": "xgboost", "optimization_metric": "accuracy"}}

"Explain why transaction #12345 was flagged"
→ {"intent": "explain_prediction", "confidence": 0.92, "parameters": {"prediction_id": "12345", "explanation_type": "feature_importance"}}

Return ONLY valid JSON with: intent, confidence (0.0-1.0), and parameters (dict).
"""
        return prompt

    def validate_against_golden_tests(self) -> Dict[str, Any]:
        """
        Validate classifier against 30 golden test commands.

        Returns:
            Validation results with accuracy metrics
        """
        logger.info("Running golden test validation...")

        golden_tests = self.command_library.get('golden_test_commands', [])
        if not golden_tests:
            return {"error": "No golden tests found"}

        results = []
        correct = 0

        for test in golden_tests:
            command = test['command']
            expected_intent = test['expected_intent']

            # Classify
            classification = self.classify(command)
            actual_intent = classification.get('intent')
            confidence = classification.get('confidence', 0.0)

            # Check if correct
            is_correct = (actual_intent == expected_intent)
            if is_correct:
                correct += 1

            results.append({
                "test_id": test['id'],
                "command": command,
                "expected": expected_intent,
                "actual": actual_intent,
                "confidence": confidence,
                "correct": is_correct
            })

        accuracy = correct / len(golden_tests) if golden_tests else 0.0

        return {
            "total_tests": len(golden_tests),
            "correct": correct,
            "accuracy": accuracy,
            "target_accuracy": 0.90,
            "passed": accuracy >= 0.90,
            "results": results
        }


# ============================================================================
# CLI for Testing
# ============================================================================

if __name__ == "__main__":
    import sys

    classifier = MLIntentClassifier()

    if len(sys.argv) > 1:
        # Classify command from CLI
        command = ' '.join(sys.argv[1:])
        result = classifier.classify(command)
        print(json.dumps(result, indent=2))
    else:
        # Run golden test validation
        print("Running ML Intent Classifier Golden Test Validation...\n")
        validation = classifier.validate_against_golden_tests()

        print(f"Total Tests: {validation['total_tests']}")
        print(f"Correct: {validation['correct']}")
        print(f"Accuracy: {validation['accuracy']:.1%}")
        print(f"Target: {validation['target_accuracy']:.1%}")
        print(f"Status: {'✅ PASSED' if validation['passed'] else '❌ FAILED'}\n")

        # Show failed tests
        failed = [r for r in validation['results'] if not r['correct']]
        if failed:
            print(f"Failed Tests ({len(failed)}):")
            for test in failed:
                print(f"  {test['test_id']}: Expected {test['expected']}, got {test['actual']}")
