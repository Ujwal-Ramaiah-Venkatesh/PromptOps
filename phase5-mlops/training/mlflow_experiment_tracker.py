"""
MLflow Experiment Tracker for PromptOps
=======================================

Integrates MLflow for ML experiment tracking, logging, and model registry.
Tracks hyperparameters, metrics, artifacts, and model lineage.

Author: ML Engineer - Phase 5 Week 42-43
Date: 2026-05-07
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# MLflow Experiment Tracker
# ============================================================================

class MLflowExperimentTracker:
    """
    Tracks ML experiments using MLflow.
    Logs parameters, metrics, artifacts, and models.
    """

    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        experiment_name: str = "promptops-ml-experiments"
    ):
        """
        Initialize MLflow Experiment Tracker.

        Args:
            tracking_uri: MLflow tracking server URI (defaults to local)
            experiment_name: Name of MLflow experiment
        """
        self.tracking_uri = tracking_uri or os.getenv('MLFLOW_TRACKING_URI', './mlruns')
        self.experiment_name = experiment_name
        self.mlflow_available = False

        # Try to import MLflow
        try:
            import mlflow
            self.mlflow = mlflow
            self.mlflow_available = True
            logger.info("MLflow imported successfully")
        except ImportError:
            logger.warning("MLflow not installed. Operating in mock mode.")
            logger.warning("Install with: pip install mlflow")
            self.mlflow = None

        # Initialize MLflow
        if self.mlflow_available:
            self._init_mlflow()

    def _init_mlflow(self):
        """Initialize MLflow tracking server and experiment."""
        try:
            self.mlflow.set_tracking_uri(self.tracking_uri)
            logger.info(f"MLflow tracking URI: {self.tracking_uri}")

            # Create or get experiment
            experiment = self.mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                experiment_id = self.mlflow.create_experiment(self.experiment_name)
                logger.info(f"Created MLflow experiment: {self.experiment_name}")
            else:
                experiment_id = experiment.experiment_id
                logger.info(f"Using existing MLflow experiment: {self.experiment_name}")

            self.experiment_id = experiment_id
            self.mlflow.set_experiment(self.experiment_name)

        except Exception as e:
            logger.error(f"Failed to initialize MLflow: {e}")
            self.mlflow_available = False

    def start_run(
        self,
        run_name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Start MLflow run.

        Args:
            run_name: Name for this run
            tags: Optional tags for the run

        Returns:
            Run ID if successful, None otherwise
        """
        if not self.mlflow_available:
            logger.warning("MLflow not available. Returning mock run ID.")
            return f"mock_run_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        try:
            run = self.mlflow.start_run(run_name=run_name)
            run_id = run.info.run_id

            # Log tags
            if tags:
                for key, value in tags.items():
                    self.mlflow.set_tag(key, value)

            # Log PromptOps-specific tags
            self.mlflow.set_tag("source", "PromptOps")
            self.mlflow.set_tag("phase", "Phase5-MLOps")
            self.mlflow.set_tag("created_at", datetime.utcnow().isoformat())

            logger.info(f"Started MLflow run: {run_id}")
            return run_id

        except Exception as e:
            logger.error(f"Failed to start MLflow run: {e}")
            return None

    def log_params(self, params: Dict[str, Any]):
        """
        Log parameters to MLflow.

        Args:
            params: Dictionary of parameters to log
        """
        if not self.mlflow_available:
            logger.info(f"[MOCK] Logging params: {params}")
            return

        try:
            for key, value in params.items():
                self.mlflow.log_param(key, value)
            logger.info(f"Logged {len(params)} parameters")
        except Exception as e:
            logger.error(f"Failed to log params: {e}")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """
        Log metrics to MLflow.

        Args:
            metrics: Dictionary of metrics to log
            step: Optional step number for tracking over time
        """
        if not self.mlflow_available:
            logger.info(f"[MOCK] Logging metrics: {metrics}")
            return

        try:
            for key, value in metrics.items():
                if step is not None:
                    self.mlflow.log_metric(key, value, step=step)
                else:
                    self.mlflow.log_metric(key, value)
            logger.info(f"Logged {len(metrics)} metrics")
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")

    def log_artifact(self, artifact_path: str, artifact_type: str = "general"):
        """
        Log artifact (file) to MLflow.

        Args:
            artifact_path: Path to artifact file
            artifact_type: Type of artifact (model, plot, data, etc.)
        """
        if not self.mlflow_available:
            logger.info(f"[MOCK] Logging artifact: {artifact_path}")
            return

        try:
            self.mlflow.log_artifact(artifact_path, artifact_path=artifact_type)
            logger.info(f"Logged artifact: {artifact_path}")
        except Exception as e:
            logger.error(f"Failed to log artifact: {e}")

    def log_model(
        self,
        model_uri: str,
        model_name: str,
        framework: str = "sklearn"
    ):
        """
        Log model to MLflow.

        Args:
            model_uri: URI to model artifacts (S3 path, local path, etc.)
            model_name: Name for the model
            framework: ML framework (sklearn, xgboost, pytorch, tensorflow)
        """
        if not self.mlflow_available:
            logger.info(f"[MOCK] Logging model: {model_name} ({framework})")
            return

        try:
            # Log model metadata
            self.mlflow.set_tag("model_name", model_name)
            self.mlflow.set_tag("framework", framework)
            self.mlflow.set_tag("model_uri", model_uri)

            logger.info(f"Logged model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to log model: {e}")

    def end_run(self, status: str = "FINISHED"):
        """
        End MLflow run.

        Args:
            status: Run status (FINISHED, FAILED, KILLED)
        """
        if not self.mlflow_available:
            logger.info(f"[MOCK] Ending run with status: {status}")
            return

        try:
            self.mlflow.end_run(status=status)
            logger.info(f"Ended MLflow run: {status}")
        except Exception as e:
            logger.error(f"Failed to end run: {e}")

    def track_training_job(
        self,
        job_name: str,
        job_config: Dict[str, Any],
        model_type: str
    ) -> str:
        """
        Track SageMaker training job in MLflow.

        Args:
            job_name: SageMaker training job name
            job_config: Training job configuration
            model_type: Model type

        Returns:
            MLflow run ID
        """
        logger.info(f"Tracking training job: {job_name}")

        # Start MLflow run
        run_id = self.start_run(
            run_name=job_name,
            tags={
                "job_name": job_name,
                "model_type": model_type,
                "platform": "SageMaker"
            }
        )

        # Log training configuration
        params = {
            "instance_type": job_config.get("ResourceConfig", {}).get("InstanceType"),
            "instance_count": job_config.get("ResourceConfig", {}).get("InstanceCount"),
            "volume_size_gb": job_config.get("ResourceConfig", {}).get("VolumeSizeInGB"),
            "max_runtime_seconds": job_config.get("StoppingCondition", {}).get("MaxRuntimeInSeconds")
        }

        # Log hyperparameters
        hyperparameters = job_config.get("HyperParameters", {})
        params.update(hyperparameters)

        self.log_params(params)

        # Log job metadata
        metadata = {
            "job_name": job_name,
            "model_type": model_type,
            "created_at": datetime.utcnow().isoformat(),
            "training_image": job_config.get("AlgorithmSpecification", {}).get("TrainingImage"),
            "s3_output_path": job_config.get("OutputDataConfig", {}).get("S3OutputPath")
        }

        if self.mlflow_available:
            for key, value in metadata.items():
                self.mlflow.set_tag(key, str(value))

        logger.info(f"Training job tracked with run_id: {run_id}")
        return run_id

    def update_training_metrics(
        self,
        run_id: str,
        metrics: Dict[str, float],
        status: str
    ):
        """
        Update training metrics for existing run.

        Args:
            run_id: MLflow run ID
            metrics: Training metrics (accuracy, loss, etc.)
            status: Job status
        """
        if not self.mlflow_available:
            logger.info(f"[MOCK] Updating metrics for run {run_id}: {metrics}")
            return

        try:
            # Resume run
            with self.mlflow.start_run(run_id=run_id):
                self.log_metrics(metrics)
                self.mlflow.set_tag("status", status)

            logger.info(f"Updated metrics for run: {run_id}")
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")

    def get_best_run(
        self,
        experiment_name: str,
        metric_name: str,
        maximize: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get best run from experiment based on metric.

        Args:
            experiment_name: Name of experiment
            metric_name: Metric to optimize
            maximize: True to maximize metric, False to minimize

        Returns:
            Best run information
        """
        if not self.mlflow_available:
            logger.warning("MLflow not available. Cannot retrieve best run.")
            return None

        try:
            experiment = self.mlflow.get_experiment_by_name(experiment_name)
            if not experiment:
                logger.warning(f"Experiment not found: {experiment_name}")
                return None

            # Search runs
            runs = self.mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=[f"metrics.{metric_name} {'DESC' if maximize else 'ASC'}"],
                max_results=1
            )

            if len(runs) == 0:
                logger.warning(f"No runs found in experiment: {experiment_name}")
                return None

            best_run = runs.iloc[0]
            return {
                "run_id": best_run.run_id,
                "run_name": best_run.tags.get("mlflow.runName"),
                "metric_value": best_run[f"metrics.{metric_name}"],
                "params": {k.replace("params.", ""): v for k, v in best_run.items() if k.startswith("params.")},
                "start_time": best_run.start_time,
                "end_time": best_run.end_time
            }

        except Exception as e:
            logger.error(f"Failed to get best run: {e}")
            return None

    def compare_runs(self, run_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple MLflow runs.

        Args:
            run_ids: List of run IDs to compare

        Returns:
            Comparison results
        """
        if not self.mlflow_available:
            logger.warning("MLflow not available. Cannot compare runs.")
            return {"status": "mock_mode", "run_ids": run_ids}

        try:
            comparison = {
                "run_count": len(run_ids),
                "runs": []
            }

            for run_id in run_ids:
                run = self.mlflow.get_run(run_id)
                comparison["runs"].append({
                    "run_id": run_id,
                    "run_name": run.data.tags.get("mlflow.runName"),
                    "params": run.data.params,
                    "metrics": run.data.metrics,
                    "status": run.info.status
                })

            return comparison

        except Exception as e:
            logger.error(f"Failed to compare runs: {e}")
            return {"status": "error", "error": str(e)}


# ============================================================================
# Testing
# ============================================================================

def test_mlflow_tracker():
    """Test MLflow experiment tracker."""
    logger.info("Testing MLflow Experiment Tracker...")

    tracker = MLflowExperimentTracker(
        tracking_uri="./test_mlruns",
        experiment_name="test-promptops-ml"
    )

    # Start run
    run_id = tracker.start_run(
        run_name="test-churn-model",
        tags={"model_type": "classification", "version": "v1.0"}
    )

    # Log parameters
    tracker.log_params({
        "algorithm": "xgboost",
        "max_depth": 6,
        "learning_rate": 0.3,
        "num_rounds": 100
    })

    # Log metrics
    tracker.log_metrics({
        "accuracy": 0.92,
        "precision": 0.89,
        "recall": 0.94,
        "f1_score": 0.91
    })

    # End run
    tracker.end_run(status="FINISHED")

    print(f"\nMLflow run completed: {run_id}")
    print(f"View runs: mlflow ui --backend-store-uri ./test_mlruns")


if __name__ == "__main__":
    test_mlflow_tracker()
