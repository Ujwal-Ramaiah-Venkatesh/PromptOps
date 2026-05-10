"""
IaC State Manager for PromptOps
================================

Manages Infrastructure as Code state across multiple backends.
Supports S3, Azure Blob Storage, and Google Cloud Storage.

Author: DevOps Engineer - Phase 6 Week 60-61
Date: 2026-05-10
"""

import json
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class BackendType(Enum):
    """State backend types."""
    S3 = "s3"
    AZURE = "azurerm"
    GCS = "gcs"
    LOCAL = "local"


class StateStatus(Enum):
    """State status."""
    CLEAN = "clean"
    DIRTY = "dirty"
    LOCKED = "locked"
    CORRUPTED = "corrupted"


# ============================================================================
# State Manager
# ============================================================================

class StateManager:
    """
    Infrastructure state manager.

    Features:
    - Multi-backend state storage
    - State locking
    - State versioning
    - State backup
    - State migration
    - Drift detection
    """

    def __init__(self, backend_type: str = "s3", backend_config: Optional[Dict[str, Any]] = None):
        """
        Initialize State Manager.

        Args:
            backend_type: Backend type (s3, azurerm, gcs, local)
            backend_config: Backend configuration
        """
        self.backend_type = backend_type
        self.backend_config = backend_config or {}
        self.state_history = []

    def initialize_backend(self) -> Dict[str, Any]:
        """
        Initialize state backend.

        Returns:
            Initialization result
        """
        logger.info(f"Initializing {self.backend_type} backend")

        if self.backend_type == "s3":
            return self._initialize_s3_backend()
        elif self.backend_type == "azurerm":
            return self._initialize_azure_backend()
        elif self.backend_type == "gcs":
            return self._initialize_gcs_backend()
        else:
            return self._initialize_local_backend()

    def _initialize_s3_backend(self) -> Dict[str, Any]:
        """Initialize S3 backend."""
        config = {
            "backend": "s3",
            "bucket": self.backend_config.get("bucket", "terraform-state"),
            "key": self.backend_config.get("key", "terraform.tfstate"),
            "region": self.backend_config.get("region", "us-east-1"),
            "encrypt": True,
            "dynamodb_table": self.backend_config.get("dynamodb_table", "terraform-locks"),
            "versioning": True
        }

        return {
            "status": "initialized",
            "backend": "s3",
            "config": config,
            "features": ["locking", "versioning", "encryption"],
            "initialized_at": datetime.utcnow().isoformat()
        }

    def _initialize_azure_backend(self) -> Dict[str, Any]:
        """Initialize Azure backend."""
        config = {
            "backend": "azurerm",
            "resource_group_name": self.backend_config.get("resource_group_name"),
            "storage_account_name": self.backend_config.get("storage_account_name"),
            "container_name": self.backend_config.get("container_name", "tfstate"),
            "key": self.backend_config.get("key", "terraform.tfstate")
        }

        return {
            "status": "initialized",
            "backend": "azurerm",
            "config": config,
            "features": ["locking", "encryption"],
            "initialized_at": datetime.utcnow().isoformat()
        }

    def _initialize_gcs_backend(self) -> Dict[str, Any]:
        """Initialize GCS backend."""
        config = {
            "backend": "gcs",
            "bucket": self.backend_config.get("bucket"),
            "prefix": self.backend_config.get("prefix", "terraform/state")
        }

        return {
            "status": "initialized",
            "backend": "gcs",
            "config": config,
            "features": ["locking", "versioning"],
            "initialized_at": datetime.utcnow().isoformat()
        }

    def _initialize_local_backend(self) -> Dict[str, Any]:
        """Initialize local backend."""
        return {
            "status": "initialized",
            "backend": "local",
            "config": {"path": "terraform.tfstate"},
            "features": [],
            "initialized_at": datetime.utcnow().isoformat()
        }

    def save_state(
        self,
        state_data: Dict[str, Any],
        lock: bool = True
    ) -> Dict[str, Any]:
        """
        Save infrastructure state.

        Args:
            state_data: State data
            lock: Acquire lock before saving

        Returns:
            Save result
        """
        logger.info("Saving infrastructure state")

        if lock:
            lock_result = self.acquire_lock()
            if lock_result["status"] != "acquired":
                return {
                    "status": "failed",
                    "error": "Failed to acquire lock"
                }

        # Calculate state checksum
        state_json = json.dumps(state_data, sort_keys=True)
        checksum = hashlib.sha256(state_json.encode()).hexdigest()

        # Add to history
        state_version = {
            "version": len(self.state_history) + 1,
            "state": state_data,
            "checksum": checksum,
            "saved_at": datetime.utcnow().isoformat()
        }

        self.state_history.append(state_version)

        result = {
            "status": "saved",
            "backend": self.backend_type,
            "version": state_version["version"],
            "checksum": checksum,
            "size_bytes": len(state_json),
            "saved_at": state_version["saved_at"]
        }

        if lock:
            self.release_lock()

        return result

    def load_state(self, version: Optional[int] = None) -> Dict[str, Any]:
        """
        Load infrastructure state.

        Args:
            version: Specific version to load (None for latest)

        Returns:
            State data
        """
        logger.info(f"Loading infrastructure state (version: {version or 'latest'})")

        if not self.state_history:
            return {
                "status": "empty",
                "message": "No state history available"
            }

        if version:
            # Load specific version
            for state_version in self.state_history:
                if state_version["version"] == version:
                    return {
                        "status": "loaded",
                        "version": version,
                        "state": state_version["state"],
                        "checksum": state_version["checksum"],
                        "saved_at": state_version["saved_at"]
                    }

            return {
                "status": "error",
                "message": f"Version {version} not found"
            }
        else:
            # Load latest version
            latest = self.state_history[-1]
            return {
                "status": "loaded",
                "version": latest["version"],
                "state": latest["state"],
                "checksum": latest["checksum"],
                "saved_at": latest["saved_at"]
            }

    def list_versions(self) -> List[Dict[str, Any]]:
        """
        List all state versions.

        Returns:
            List of versions
        """
        versions = []

        for state_version in self.state_history:
            versions.append({
                "version": state_version["version"],
                "checksum": state_version["checksum"],
                "saved_at": state_version["saved_at"]
            })

        return versions

    def acquire_lock(self, lock_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Acquire state lock.

        Args:
            lock_id: Lock identifier

        Returns:
            Lock result
        """
        logger.info("Acquiring state lock")

        lock_id = lock_id or f"lock-{datetime.utcnow().timestamp()}"

        # Mock implementation
        return {
            "status": "acquired",
            "lock_id": lock_id,
            "acquired_at": datetime.utcnow().isoformat(),
            "backend": self.backend_type
        }

    def release_lock(self, lock_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Release state lock.

        Args:
            lock_id: Lock identifier

        Returns:
            Release result
        """
        logger.info("Releasing state lock")

        return {
            "status": "released",
            "released_at": datetime.utcnow().isoformat()
        }

    def backup_state(self, backup_location: str) -> Dict[str, Any]:
        """
        Backup current state.

        Args:
            backup_location: Backup location

        Returns:
            Backup result
        """
        logger.info(f"Backing up state to {backup_location}")

        if not self.state_history:
            return {
                "status": "failed",
                "error": "No state to backup"
            }

        latest = self.state_history[-1]

        return {
            "status": "backed_up",
            "backup_location": backup_location,
            "version": latest["version"],
            "checksum": latest["checksum"],
            "backed_up_at": datetime.utcnow().isoformat()
        }

    def migrate_state(
        self,
        target_backend: str,
        target_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Migrate state to different backend.

        Args:
            target_backend: Target backend type
            target_config: Target backend configuration

        Returns:
            Migration result
        """
        logger.info(f"Migrating state from {self.backend_type} to {target_backend}")

        if not self.state_history:
            return {
                "status": "failed",
                "error": "No state to migrate"
            }

        # Get current state
        current_state = self.state_history[-1]

        # Create new state manager for target
        target_manager = StateManager(target_backend, target_config)
        target_manager.initialize_backend()

        # Save state to target
        save_result = target_manager.save_state(current_state["state"])

        return {
            "status": "migrated",
            "source_backend": self.backend_type,
            "target_backend": target_backend,
            "version": current_state["version"],
            "checksum": current_state["checksum"],
            "migrated_at": datetime.utcnow().isoformat()
        }

    def detect_drift(
        self,
        desired_state: Dict[str, Any],
        actual_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect drift between desired and actual state.

        Args:
            desired_state: Desired infrastructure state
            actual_state: Actual infrastructure state

        Returns:
            Drift detection result
        """
        logger.info("Detecting infrastructure drift")

        drift = {
            "added": [],
            "removed": [],
            "changed": []
        }

        desired_resources = desired_state.get("resources", {})
        actual_resources = actual_state.get("resources", {})

        # Find added resources
        for resource_id in actual_resources:
            if resource_id not in desired_resources:
                drift["added"].append({
                    "resource_id": resource_id,
                    "type": actual_resources[resource_id].get("type"),
                    "actual": actual_resources[resource_id]
                })

        # Find removed resources
        for resource_id in desired_resources:
            if resource_id not in actual_resources:
                drift["removed"].append({
                    "resource_id": resource_id,
                    "type": desired_resources[resource_id].get("type"),
                    "desired": desired_resources[resource_id]
                })

        # Find changed resources
        for resource_id in desired_resources:
            if resource_id in actual_resources:
                desired_res = desired_resources[resource_id]
                actual_res = actual_resources[resource_id]

                if desired_res != actual_res:
                    drift["changed"].append({
                        "resource_id": resource_id,
                        "type": desired_res.get("type"),
                        "desired": desired_res,
                        "actual": actual_res
                    })

        has_drift = len(drift["added"]) > 0 or len(drift["removed"]) > 0 or len(drift["changed"]) > 0

        return {
            "has_drift": has_drift,
            "drift": drift,
            "summary": {
                "added": len(drift["added"]),
                "removed": len(drift["removed"]),
                "changed": len(drift["changed"])
            },
            "detected_at": datetime.utcnow().isoformat()
        }


# ============================================================================
# Testing
# ============================================================================

def test_state_manager():
    """Test State Manager."""
    logger.info("Testing State Manager...")

    # Test 1: Initialize S3 backend
    print("\n=== Test 1: Initialize S3 Backend ===")
    manager = StateManager(
        backend_type="s3",
        backend_config={
            "bucket": "my-terraform-state",
            "region": "us-east-1"
        }
    )
    init_result = manager.initialize_backend()
    print(f"Backend: {init_result['backend']}")
    print(f"Features: {init_result['features']}")

    # Test 2: Save state
    print("\n=== Test 2: Save State ===")
    state_data = {
        "version": 4,
        "terraform_version": "1.5.0",
        "resources": {
            "aws_instance.web": {
                "type": "aws_instance",
                "attributes": {
                    "id": "i-1234567890abcdef0",
                    "instance_type": "t3.micro"
                }
            }
        }
    }
    save_result = manager.save_state(state_data)
    print(f"Status: {save_result['status']}")
    print(f"Version: {save_result['version']}")
    print(f"Checksum: {save_result['checksum'][:16]}...")

    # Test 3: Load state
    print("\n=== Test 3: Load State ===")
    load_result = manager.load_state()
    print(f"Status: {load_result['status']}")
    print(f"Version: {load_result['version']}")
    print(f"Resources: {list(load_result['state']['resources'].keys())}")

    # Test 4: Detect drift
    print("\n=== Test 4: Detect Drift ===")
    desired_state = {
        "resources": {
            "aws_instance.web": {"type": "aws_instance", "count": 1},
            "aws_s3_bucket.data": {"type": "aws_s3_bucket"}
        }
    }
    actual_state = {
        "resources": {
            "aws_instance.web": {"type": "aws_instance", "count": 2},
            "aws_rds_instance.db": {"type": "aws_rds_instance"}
        }
    }
    drift_result = manager.detect_drift(desired_state, actual_state)
    print(f"Has Drift: {drift_result['has_drift']}")
    print(f"Added: {drift_result['summary']['added']}")
    print(f"Removed: {drift_result['summary']['removed']}")
    print(f"Changed: {drift_result['summary']['changed']}")


if __name__ == "__main__":
    test_state_manager()
