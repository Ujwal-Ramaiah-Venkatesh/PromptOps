"""
Model Registry for PromptOps
=============================

Manages model versioning, metadata, and lifecycle using MLflow-style registry.
Tracks model lineage, experiments, and deployment history.

Author: ML Engineer - Phase 5 Week 50-51
Date: 2026-05-09
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Model Registry Enums
# ============================================================================

class ModelStage(Enum):
    """Model deployment stages."""
    NONE = "None"
    DEVELOPMENT = "Development"
    STAGING = "Staging"
    PRODUCTION = "Production"
    ARCHIVED = "Archived"


class ModelStatus(Enum):
    """Model registration status."""
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    DEPLOYED = "Deployed"
    RETIRED = "Retired"


# ============================================================================
# Model Registry
# ============================================================================

class ModelRegistry:
    """
    MLflow-style model registry for versioning and lifecycle management.

    Features:
    - Model versioning (semantic versioning)
    - Metadata tracking (metrics, params, tags)
    - Stage transitions (dev→staging→prod)
    - Model lineage tracking
    - Experiment tracking
    """

    def __init__(self, registry_path: str = "./model_registry"):
        """Initialize Model Registry."""
        self.registry_path = registry_path
        self.models_db: Dict[str, List[Dict[str, Any]]] = {}
        self.experiments_db: Dict[str, Dict[str, Any]] = {}
        self._ensure_registry_exists()
        self._load_registry()

    def _ensure_registry_exists(self):
        """Ensure registry directory exists."""
        os.makedirs(self.registry_path, exist_ok=True)
        os.makedirs(os.path.join(self.registry_path, "models"), exist_ok=True)
        os.makedirs(os.path.join(self.registry_path, "experiments"), exist_ok=True)

    def _load_registry(self):
        """Load registry from disk."""
        registry_file = os.path.join(self.registry_path, "registry.json")
        if os.path.exists(registry_file):
            try:
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    self.models_db = data.get("models", {})
                    self.experiments_db = data.get("experiments", {})
                logger.info(f"Loaded registry: {len(self.models_db)} models")
            except Exception as e:
                logger.warning(f"Failed to load registry: {e}")

    def _save_registry(self):
        """Save registry to disk."""
        registry_file = os.path.join(self.registry_path, "registry.json")
        try:
            with open(registry_file, 'w') as f:
                json.dump({
                    "models": self.models_db,
                    "experiments": self.experiments_db
                }, f, indent=2, default=str)
            logger.info("Registry saved to disk")
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def register_model(
        self,
        name: str,
        model_uri: str,
        framework: str,
        version: Optional[str] = None,
        metrics: Optional[Dict[str, float]] = None,
        params: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Register a new model version.

        Args:
            name: Model name
            model_uri: S3/local path to model artifacts
            framework: ML framework (xgboost, tensorflow, pytorch, sklearn)
            version: Optional version (auto-incremented if not provided)
            metrics: Model metrics (accuracy, auc, etc.)
            params: Model hyperparameters
            tags: Custom tags
            description: Model description

        Returns:
            Registered model information
        """
        logger.info(f"Registering model: {name}")

        # Initialize model entry if doesn't exist
        if name not in self.models_db:
            self.models_db[name] = []

        # Auto-increment version
        if version is None:
            version = f"v{len(self.models_db[name]) + 1}"

        # Create model version entry
        model_version = {
            "name": name,
            "version": version,
            "model_uri": model_uri,
            "framework": framework,
            "stage": ModelStage.DEVELOPMENT.value,
            "status": ModelStatus.PENDING.value,
            "metrics": metrics or {},
            "params": params or {},
            "tags": tags or {},
            "description": description,
            "registered_at": datetime.utcnow().isoformat(),
            "registered_by": "system",
            "model_hash": self._compute_model_hash(model_uri),
            "lineage": {
                "parent_version": None,
                "training_job": None,
                "tuning_job": None
            }
        }

        # Add to registry
        self.models_db[name].append(model_version)
        self._save_registry()

        logger.info(f"Model registered: {name} {version}")
        return model_version

    def get_model_version(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        """Get specific model version."""
        if name not in self.models_db:
            return None

        for model in self.models_db[name]:
            if model["version"] == version:
                return model

        return None

    def get_latest_version(self, name: str, stage: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get latest model version.

        Args:
            name: Model name
            stage: Optional stage filter (Development, Staging, Production)

        Returns:
            Latest model version
        """
        if name not in self.models_db:
            return None

        versions = self.models_db[name]

        # Filter by stage
        if stage:
            versions = [v for v in versions if v["stage"] == stage]

        if not versions:
            return None

        # Return most recent
        return max(versions, key=lambda x: x["registered_at"])

    def list_models(self, stage: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all registered models.

        Args:
            stage: Optional stage filter

        Returns:
            List of models
        """
        models = []

        for name, versions in self.models_db.items():
            latest = self.get_latest_version(name, stage=stage)
            if latest:
                models.append({
                    "name": name,
                    "latest_version": latest["version"],
                    "stage": latest["stage"],
                    "status": latest["status"],
                    "total_versions": len(versions),
                    "registered_at": latest["registered_at"]
                })

        return models

    def transition_stage(
        self,
        name: str,
        version: str,
        stage: str,
        archive_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Transition model to new stage.

        Args:
            name: Model name
            version: Model version
            stage: Target stage (Development, Staging, Production)
            archive_existing: Archive existing models in target stage

        Returns:
            Updated model info
        """
        logger.info(f"Transitioning {name} {version} to {stage}")

        model = self.get_model_version(name, version)
        if not model:
            raise ValueError(f"Model {name} {version} not found")

        # Archive existing models in target stage
        if archive_existing and stage == ModelStage.PRODUCTION.value:
            for existing in self.models_db[name]:
                if existing["stage"] == ModelStage.PRODUCTION.value:
                    existing["stage"] = ModelStage.ARCHIVED.value
                    logger.info(f"Archived {existing['version']}")

        # Update stage
        model["stage"] = stage
        model["stage_transitioned_at"] = datetime.utcnow().isoformat()

        self._save_registry()

        return model

    def update_status(
        self,
        name: str,
        version: str,
        status: str,
        comment: str = ""
    ) -> Dict[str, Any]:
        """
        Update model approval status.

        Args:
            name: Model name
            version: Model version
            status: New status (Approved, Rejected, Deployed, Retired)
            comment: Optional comment

        Returns:
            Updated model info
        """
        logger.info(f"Updating status: {name} {version} -> {status}")

        model = self.get_model_version(name, version)
        if not model:
            raise ValueError(f"Model {name} {version} not found")

        model["status"] = status
        model["status_updated_at"] = datetime.utcnow().isoformat()

        if comment:
            if "status_history" not in model:
                model["status_history"] = []
            model["status_history"].append({
                "status": status,
                "comment": comment,
                "timestamp": datetime.utcnow().isoformat()
            })

        self._save_registry()

        return model

    def add_tags(self, name: str, version: str, tags: Dict[str, str]) -> Dict[str, Any]:
        """Add tags to model version."""
        model = self.get_model_version(name, version)
        if not model:
            raise ValueError(f"Model {name} {version} not found")

        model["tags"].update(tags)
        self._save_registry()

        return model

    def get_model_lineage(self, name: str, version: str) -> Dict[str, Any]:
        """
        Get model lineage (parent models, training jobs, etc.).

        Args:
            name: Model name
            version: Model version

        Returns:
            Lineage information
        """
        model = self.get_model_version(name, version)
        if not model:
            raise ValueError(f"Model {name} {version} not found")

        lineage = {
            "model": f"{name}:{version}",
            "lineage": model.get("lineage", {}),
            "training_params": model.get("params", {}),
            "metrics": model.get("metrics", {}),
            "registered_at": model.get("registered_at")
        }

        # Get parent lineage recursively
        parent_version = model.get("lineage", {}).get("parent_version")
        if parent_version:
            parent = self.get_model_version(name, parent_version)
            if parent:
                lineage["parent"] = {
                    "version": parent_version,
                    "metrics": parent.get("metrics", {})
                }

        return lineage

    def search_models(
        self,
        query: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        min_metric: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search models by name, tags, or metrics.

        Args:
            query: Name query string
            tags: Tag filters
            min_metric: Minimum metric thresholds (e.g., {"accuracy": 0.9})

        Returns:
            List of matching models
        """
        results = []

        for name, versions in self.models_db.items():
            # Filter by name
            if query and query.lower() not in name.lower():
                continue

            for model in versions:
                # Filter by tags
                if tags:
                    if not all(model.get("tags", {}).get(k) == v for k, v in tags.items()):
                        continue

                # Filter by metrics
                if min_metric:
                    if not all(model.get("metrics", {}).get(k, 0) >= v for k, v in min_metric.items()):
                        continue

                results.append(model)

        return results

    def delete_model_version(self, name: str, version: str):
        """
        Delete a model version.

        Args:
            name: Model name
            version: Model version
        """
        logger.info(f"Deleting model: {name} {version}")

        if name not in self.models_db:
            raise ValueError(f"Model {name} not found")

        # Cannot delete production models
        model = self.get_model_version(name, version)
        if model and model["stage"] == ModelStage.PRODUCTION.value:
            raise ValueError("Cannot delete production models")

        self.models_db[name] = [m for m in self.models_db[name] if m["version"] != version]

        # Remove model entry if no versions left
        if not self.models_db[name]:
            del self.models_db[name]

        self._save_registry()

    def _compute_model_hash(self, model_uri: str) -> str:
        """Compute hash of model URI for integrity checking."""
        return hashlib.sha256(model_uri.encode()).hexdigest()[:16]

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_models = len(self.models_db)
        total_versions = sum(len(versions) for versions in self.models_db.values())

        stage_counts = {stage.value: 0 for stage in ModelStage}
        status_counts = {status.value: 0 for status in ModelStatus}

        for versions in self.models_db.values():
            for model in versions:
                stage_counts[model["stage"]] += 1
                status_counts[model["status"]] += 1

        return {
            "total_models": total_models,
            "total_versions": total_versions,
            "by_stage": stage_counts,
            "by_status": status_counts
        }


# ============================================================================
# Testing
# ============================================================================

def test_model_registry():
    """Test model registry."""
    logger.info("Testing Model Registry...")

    registry = ModelRegistry(registry_path="./test_registry")

    # Test 1: Register model
    print("\n=== Test 1: Register Model ===")
    model = registry.register_model(
        name="churn-prediction",
        model_uri="s3://models/churn/model.tar.gz",
        framework="xgboost",
        metrics={"accuracy": 0.92, "auc": 0.95},
        params={"max_depth": 7, "eta": 0.15},
        tags={"team": "ml-team", "use_case": "churn"},
        description="XGBoost model for customer churn prediction"
    )
    print(json.dumps(model, indent=2, default=str))

    # Test 2: Register another version
    print("\n=== Test 2: Register Version 2 ===")
    model_v2 = registry.register_model(
        name="churn-prediction",
        model_uri="s3://models/churn/model_v2.tar.gz",
        framework="xgboost",
        metrics={"accuracy": 0.94, "auc": 0.96},
        params={"max_depth": 8, "eta": 0.12}
    )
    print(json.dumps(model_v2, indent=2, default=str))

    # Test 3: Get latest version
    print("\n=== Test 3: Get Latest Version ===")
    latest = registry.get_latest_version("churn-prediction")
    print(json.dumps(latest, indent=2, default=str))

    # Test 4: Transition to staging
    print("\n=== Test 4: Transition to Staging ===")
    updated = registry.transition_stage(
        name="churn-prediction",
        version="v2",
        stage=ModelStage.STAGING.value
    )
    print(f"Stage: {updated['stage']}")

    # Test 5: Update status
    print("\n=== Test 5: Update Status to Approved ===")
    approved = registry.update_status(
        name="churn-prediction",
        version="v2",
        status=ModelStatus.APPROVED.value,
        comment="Approved by ML team after validation"
    )
    print(f"Status: {approved['status']}")

    # Test 6: List models
    print("\n=== Test 6: List All Models ===")
    models = registry.list_models()
    print(json.dumps(models, indent=2, default=str))

    # Test 7: Search models
    print("\n=== Test 7: Search Models (accuracy >= 0.93) ===")
    results = registry.search_models(min_metric={"accuracy": 0.93})
    print(f"Found {len(results)} models")

    # Test 8: Registry stats
    print("\n=== Test 8: Registry Statistics ===")
    stats = registry.get_registry_stats()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    test_model_registry()
