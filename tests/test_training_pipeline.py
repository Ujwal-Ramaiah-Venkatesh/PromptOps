"""
Comprehensive Tests for Training Pipeline
=========================================

Tests for Phase 5 Week 42-43: Model Training Pipeline

Test Coverage:
- SageMaker training job generation
- Training data validation
- MLflow experiment tracking
- Training cost estimation
- Training API endpoints

Author: QA Engineer - Phase 5 Week 42-43
Date: 2026-05-07
"""

import unittest
import sys
import os
import json
import tempfile
import pandas as pd
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase5-mlops.training.sagemaker_training_generator import SageMakerTrainingGenerator
from phase5-mlops.training.training_data_validator import TrainingDataValidator
from phase5-mlops.training.mlflow_experiment_tracker import MLflowExperimentTracker
from phase5-mlops.training.training_cost_estimator import TrainingCostEstimator


class TestSageMakerTrainingGenerator(unittest.TestCase):
    """Test SageMaker training job generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = SageMakerTrainingGenerator(region='us-east-1')

        self.sample_intent_params = {
            "model_type": "churn_prediction",
            "time_range": "90_days",
            "data_source": "user_activity"
        }

    def test_generate_classification_config(self):
        """Test TC151: Generate config for classification model."""
        config = self.generator.generate_training_config(
            intent_params=self.sample_intent_params,
            s3_data_path="s3://test-bucket/data",
            s3_output_path="s3://test-bucket/output",
            role_arn="arn:aws:iam::123456789012:role/TestRole"
        )

        # Verify required fields
        self.assertIn("TrainingJobName", config)
        self.assertIn("RoleArn", config)
        self.assertIn("AlgorithmSpecification", config)
        self.assertIn("InputDataConfig", config)
        self.assertIn("OutputDataConfig", config)
        self.assertIn("ResourceConfig", config)

        # Verify instance type for classification
        self.assertIn("ml.m5", config["ResourceConfig"]["InstanceType"])

    def test_generate_nlp_config(self):
        """Test TC152: Generate config for NLP model."""
        nlp_params = {
            "model_type": "sentiment_analysis",
            "data_source": "customer_reviews"
        }

        config = self.generator.generate_training_config(
            intent_params=nlp_params,
            s3_data_path="s3://test-bucket/data",
            s3_output_path="s3://test-bucket/output",
            role_arn="arn:aws:iam::123456789012:role/TestRole"
        )

        # NLP models should use GPU instances
        self.assertIn("ml.g4dn", config["ResourceConfig"]["InstanceType"])

    def test_generate_cv_config(self):
        """Test TC153: Generate config for computer vision model."""
        cv_params = {
            "model_type": "image_classification",
            "data_source": "product_images"
        }

        config = self.generator.generate_training_config(
            intent_params=cv_params,
            s3_data_path="s3://test-bucket/data",
            s3_output_path="s3://test-bucket/output",
            role_arn="arn:aws:iam::123456789012:role/TestRole"
        )

        # CV models should use P3 instances
        self.assertIn("ml.p3", config["ResourceConfig"]["InstanceType"])

    def test_job_name_generation(self):
        """Test TC154: Job name is unique and valid."""
        config1 = self.generator.generate_training_config(
            intent_params=self.sample_intent_params,
            s3_data_path="s3://test-bucket/data",
            s3_output_path="s3://test-bucket/output",
            role_arn="arn:aws:iam::123456789012:role/TestRole"
        )

        config2 = self.generator.generate_training_config(
            intent_params=self.sample_intent_params,
            s3_data_path="s3://test-bucket/data",
            s3_output_path="s3://test-bucket/output",
            role_arn="arn:aws:iam::123456789012:role/TestRole"
        )

        # Job names should be unique
        self.assertNotEqual(config1["TrainingJobName"], config2["TrainingJobName"])

        # Job names should be <= 63 chars
        self.assertLessEqual(len(config1["TrainingJobName"]), 63)

    def test_hyperparameter_merging(self):
        """Test TC155: Custom hyperparameters are merged correctly."""
        params_with_hp = {
            "model_type": "churn_prediction",
            "hyperparameters": {
                "max_depth": "8",
                "eta": "0.2"
            }
        }

        config = self.generator.generate_training_config(
            intent_params=params_with_hp,
            s3_data_path="s3://test-bucket/data",
            s3_output_path="s3://test-bucket/output",
            role_arn="arn:aws:iam::123456789012:role/TestRole"
        )

        # Custom hyperparameters should be present
        self.assertEqual(config["HyperParameters"]["max_depth"], "8")
        self.assertEqual(config["HyperParameters"]["eta"], "0.2")


class TestTrainingDataValidator(unittest.TestCase):
    """Test training data validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = TrainingDataValidator()
        self.temp_dir = tempfile.mkdtemp()

    def test_validate_classification_data(self):
        """Test TC156: Validate classification dataset."""
        # Create valid classification dataset
        df = pd.DataFrame({
            'feature1': range(100),
            'feature2': range(100, 200),
            'target': [0, 1] * 50
        })

        test_file = os.path.join(self.temp_dir, 'classification.csv')
        df.to_csv(test_file, index=False)

        results = self.validator.validate_dataset(
            data_path=test_file,
            model_type="classification",
            expected_columns=['feature1', 'feature2', 'target'],
            target_column='target'
        )

        self.assertTrue(results["valid"])
        self.assertEqual(results["checks_failed"], 0)
        self.assertGreater(results["checks_passed"], 5)

    def test_validate_regression_data(self):
        """Test TC157: Validate regression dataset."""
        df = pd.DataFrame({
            'feature1': range(100),
            'feature2': range(100, 200),
            'target': [i * 0.5 for i in range(100)]
        })

        test_file = os.path.join(self.temp_dir, 'regression.csv')
        df.to_csv(test_file, index=False)

        results = self.validator.validate_dataset(
            data_path=test_file,
            model_type="regression",
            expected_columns=['feature1', 'feature2', 'target'],
            target_column='target'
        )

        self.assertTrue(results["valid"])
        self.assertIn("target_mean", results["statistics"])
        self.assertIn("target_std", results["statistics"])

    def test_detect_missing_columns(self):
        """Test TC158: Detect missing required columns."""
        df = pd.DataFrame({
            'feature1': range(10),
            'target': [0, 1] * 5
        })

        test_file = os.path.join(self.temp_dir, 'missing_cols.csv')
        df.to_csv(test_file, index=False)

        results = self.validator.validate_dataset(
            data_path=test_file,
            model_type="classification",
            expected_columns=['feature1', 'feature2', 'target'],
            target_column='target'
        )

        self.assertFalse(results["valid"])
        self.assertGreater(results["checks_failed"], 0)
        self.assertTrue(any('Missing columns' in error for error in results["errors"]))

    def test_detect_class_imbalance(self):
        """Test TC159: Detect severe class imbalance."""
        df = pd.DataFrame({
            'feature1': range(100),
            'target': [0] * 95 + [1] * 5  # 95:5 ratio
        })

        test_file = os.path.join(self.temp_dir, 'imbalanced.csv')
        df.to_csv(test_file, index=False)

        results = self.validator.validate_dataset(
            data_path=test_file,
            model_type="classification",
            target_column='target'
        )

        # Should detect severe imbalance
        self.assertGreater(results["checks_failed"], 0)
        self.assertTrue(any('imbalance' in w.lower() for w in results["warnings"]))

    def test_detect_empty_dataset(self):
        """Test TC160: Detect empty dataset."""
        df = pd.DataFrame()

        test_file = os.path.join(self.temp_dir, 'empty.csv')
        df.to_csv(test_file, index=False)

        results = self.validator.validate_dataset(
            data_path=test_file,
            model_type="classification"
        )

        self.assertFalse(results["valid"])
        self.assertTrue(any('empty' in error.lower() for error in results["errors"]))


class TestMLflowExperimentTracker(unittest.TestCase):
    """Test MLflow experiment tracking."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = MLflowExperimentTracker(
            tracking_uri="./test_mlruns",
            experiment_name="test-experiment"
        )

    def test_start_run(self):
        """Test TC161: Start MLflow run."""
        run_id = self.tracker.start_run(
            run_name="test-run",
            tags={"model_type": "classification"}
        )

        self.assertIsNotNone(run_id)
        self.assertGreater(len(run_id), 0)

        self.tracker.end_run()

    def test_log_params(self):
        """Test TC162: Log parameters to MLflow."""
        run_id = self.tracker.start_run(run_name="test-params")

        params = {
            "algorithm": "xgboost",
            "max_depth": 6,
            "learning_rate": 0.3
        }

        # Should not raise exception
        self.tracker.log_params(params)
        self.tracker.end_run()

    def test_log_metrics(self):
        """Test TC163: Log metrics to MLflow."""
        run_id = self.tracker.start_run(run_name="test-metrics")

        metrics = {
            "accuracy": 0.92,
            "precision": 0.89,
            "recall": 0.94
        }

        # Should not raise exception
        self.tracker.log_metrics(metrics)
        self.tracker.end_run()

    def test_track_training_job(self):
        """Test TC164: Track SageMaker training job."""
        job_config = {
            "TrainingJobName": "test-job-123",
            "ResourceConfig": {
                "InstanceType": "ml.m5.xlarge",
                "InstanceCount": 1,
                "VolumeSizeInGB": 30
            },
            "HyperParameters": {
                "max_depth": "6",
                "learning_rate": "0.3"
            }
        }

        run_id = self.tracker.track_training_job(
            job_name="test-job-123",
            job_config=job_config,
            model_type="classification"
        )

        self.assertIsNotNone(run_id)
        self.tracker.end_run()


class TestTrainingCostEstimator(unittest.TestCase):
    """Test training cost estimation."""

    def setUp(self):
        """Set up test fixtures."""
        self.estimator = TrainingCostEstimator(region='us-east-1')

    def test_estimate_cost(self):
        """Test TC165: Estimate training cost."""
        estimate = self.estimator.estimate_training_cost(
            instance_type="ml.m5.xlarge",
            instance_count=1,
            training_duration_hours=2.0
        )

        self.assertIn("total_cost_usd", estimate)
        self.assertIn("compute_cost_usd", estimate)
        self.assertIn("storage_cost_usd", estimate)
        self.assertGreater(estimate["total_cost_usd"], 0)

    def test_cost_scales_with_duration(self):
        """Test TC166: Cost scales linearly with duration."""
        estimate_1h = self.estimator.estimate_training_cost(
            instance_type="ml.m5.xlarge",
            instance_count=1,
            training_duration_hours=1.0
        )

        estimate_2h = self.estimator.estimate_training_cost(
            instance_type="ml.m5.xlarge",
            instance_count=1,
            training_duration_hours=2.0
        )

        # 2 hours should cost approximately 2x 1 hour
        ratio = estimate_2h["compute_cost_usd"] / estimate_1h["compute_cost_usd"]
        self.assertAlmostEqual(ratio, 2.0, places=1)

    def test_compare_instance_costs(self):
        """Test TC167: Compare costs across instances."""
        comparison = self.estimator.compare_instance_costs(
            instance_types=["ml.m5.large", "ml.m5.xlarge", "ml.m5.2xlarge"],
            training_duration_hours=1.0
        )

        self.assertEqual(len(comparison["instances"]), 3)

        # Should be sorted by cost (ascending)
        costs = [inst["total_cost_usd"] for inst in comparison["instances"]]
        self.assertEqual(costs, sorted(costs))

    def test_recommend_classification_instance(self):
        """Test TC168: Recommend instance for classification."""
        recommendation = self.estimator.recommend_instance_type(
            model_type="classification",
            dataset_size_gb=5.0,
            budget_usd=10.0
        )

        self.assertIn("recommended_instance", recommendation)
        self.assertIn("reasoning", recommendation)
        self.assertIn("estimated_cost_usd", recommendation)
        self.assertTrue(recommendation["within_budget"])

    def test_recommend_nlp_instance(self):
        """Test TC169: Recommend GPU instance for NLP."""
        recommendation = self.estimator.recommend_instance_type(
            model_type="nlp",
            dataset_size_gb=5.0
        )

        # NLP should recommend GPU instance
        self.assertIn("g4dn", recommendation["recommended_instance"])

    def test_recommend_cv_instance(self):
        """Test TC170: Recommend P3 instance for CV."""
        recommendation = self.estimator.recommend_instance_type(
            model_type="computer_vision",
            dataset_size_gb=10.0
        )

        # CV should recommend P3 instance
        self.assertIn("p3", recommendation["recommended_instance"])


class TestTrainingAPIEndpoints(unittest.TestCase):
    """Test training API endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test client."""
        from fastapi.testclient import TestClient
        from api_gateway.training_routes import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        cls.client = TestClient(app)

    def test_create_training_job_endpoint(self):
        """Test TC171: POST /api/v1/training/jobs/create."""
        payload = {
            "model_type": "churn_prediction",
            "intent_params": {
                "model_type": "churn_prediction",
                "time_range": "90_days"
            },
            "s3_data_path": "s3://test-bucket/data",
            "s3_output_path": "s3://test-bucket/output",
            "role_arn": "arn:aws:iam::123456789012:role/TestRole"
        }

        response = self.client.post("/api/v1/training/jobs/create", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("job_name", data)
        self.assertIn("cost_estimate", data)

    def test_validate_data_endpoint(self):
        """Test TC172: POST /api/v1/training/validate."""
        # Create temp test file
        df = pd.DataFrame({
            'feature1': range(10),
            'target': [0, 1] * 5
        })
        test_file = os.path.join(tempfile.gettempdir(), 'test_validate.csv')
        df.to_csv(test_file, index=False)

        payload = {
            "data_path": test_file,
            "model_type": "classification",
            "target_column": "target"
        }

        response = self.client.post("/api/v1/training/validate", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("valid", data)
        self.assertIn("checks_passed", data)
        self.assertIn("report", data)

    def test_estimate_cost_endpoint(self):
        """Test TC173: POST /api/v1/training/cost/estimate."""
        payload = {
            "instance_type": "ml.m5.xlarge",
            "instance_count": 1,
            "training_duration_hours": 2.0,
            "storage_gb": 30
        }

        response = self.client.post("/api/v1/training/cost/estimate", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_cost_usd", data)
        self.assertGreater(data["total_cost_usd"], 0)

    def test_recommend_instance_endpoint(self):
        """Test TC174: POST /api/v1/training/instances/recommend."""
        payload = {
            "model_type": "classification",
            "dataset_size_gb": 5.0,
            "budget_usd": 10.0
        }

        response = self.client.post("/api/v1/training/instances/recommend", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recommended_instance", data)
        self.assertIn("within_budget", data)

    def test_compare_instances_endpoint(self):
        """Test TC175: GET /api/v1/training/instances/compare."""
        params = {
            "instance_types": "ml.m5.large,ml.m5.xlarge",
            "duration_hours": 1.0
        }

        response = self.client.get("/api/v1/training/instances/compare", params=params)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("instances", data)
        self.assertEqual(len(data["instances"]), 2)


def run_all_tests():
    """Run all training pipeline tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSageMakerTrainingGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestTrainingDataValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestMLflowExperimentTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestTrainingCostEstimator))
    suite.addTests(loader.loadTestsFromTestCase(TestTrainingAPIEndpoints))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_all_tests()
    print(f"\n{'='*70}")
    print(f"Training Pipeline Tests Complete")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*70}")
