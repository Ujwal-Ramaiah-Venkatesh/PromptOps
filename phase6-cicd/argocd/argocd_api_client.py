"""
ArgoCD API Client for PromptOps
================================

REST API client for ArgoCD server operations.
Manages applications, syncs, and health monitoring.

Author: DevOps Engineer - Phase 6 Week 56-57
Date: 2026-05-10
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ArgoCD API Client
# ============================================================================

class ArgoCDAPIClient:
    """
    REST API client for ArgoCD server.

    Features:
    - Application creation and management
    - Sync operations
    - Health status monitoring
    - Resource tree inspection
    - Rollback operations
    """

    def __init__(
        self,
        argocd_url: str = "http://localhost:8080",
        auth_token: Optional[str] = None
    ):
        """
        Initialize ArgoCD API Client.

        Args:
            argocd_url: ArgoCD server URL
            auth_token: ArgoCD authentication token
        """
        self.argocd_url = argocd_url.rstrip("/")
        self.auth_token = auth_token or os.getenv("ARGOCD_AUTH_TOKEN")
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with authentication."""
        session = requests.Session()

        if self.auth_token:
            session.headers.update({
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            })

        return session

    def create_application(
        self,
        app_manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create ArgoCD application.

        Args:
            app_manifest: Application manifest

        Returns:
            Application creation result
        """
        app_name = app_manifest["metadata"]["name"]
        logger.info(f"Creating ArgoCD application: {app_name}")

        url = f"{self.argocd_url}/api/v1/applications"

        try:
            response = self.session.post(url, json=app_manifest, timeout=10)

            if response.status_code in [200, 201]:
                app = response.json()
                logger.info(f"Application created successfully: {app_name}")
                return {
                    "status": "created",
                    "app_name": app_name,
                    "health_status": app.get("status", {}).get("health", {}).get("status"),
                    "sync_status": app.get("status", {}).get("sync", {}).get("status"),
                    "created_at": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Failed to create application: {response.status_code}")
                return {
                    "status": "failed",
                    "app_name": app_name,
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Exception creating application: {e}")
            return {
                "status": "error",
                "app_name": app_name,
                "error": str(e),
                "note": "ArgoCD server may not be available (mock mode)"
            }

    def get_application(self, app_name: str) -> Dict[str, Any]:
        """
        Get application details.

        Args:
            app_name: Application name

        Returns:
            Application information
        """
        url = f"{self.argocd_url}/api/v1/applications/{app_name}"

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                app = response.json()
                return {
                    "app_name": app_name,
                    "health_status": app.get("status", {}).get("health", {}).get("status"),
                    "sync_status": app.get("status", {}).get("sync", {}).get("status"),
                    "sync_revision": app.get("status", {}).get("sync", {}).get("revision"),
                    "resources": len(app.get("status", {}).get("resources", [])),
                    "source": app.get("spec", {}).get("source")
                }
            else:
                return {
                    "app_name": app_name,
                    "error": "Application not found"
                }

        except Exception as e:
            logger.error(f"Exception getting application: {e}")
            return {
                "app_name": app_name,
                "error": str(e),
                "note": "ArgoCD server may not be available (mock mode)"
            }

    def list_applications(
        self,
        project: Optional[str] = None,
        selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List applications.

        Args:
            project: Filter by project
            selector: Label selector

        Returns:
            List of applications
        """
        url = f"{self.argocd_url}/api/v1/applications"

        params = {}
        if project:
            params["project"] = project
        if selector:
            params["selector"] = selector

        try:
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                apps = []

                for app in data.get("items", []):
                    apps.append({
                        "name": app["metadata"]["name"],
                        "health_status": app.get("status", {}).get("health", {}).get("status"),
                        "sync_status": app.get("status", {}).get("sync", {}).get("status"),
                        "namespace": app.get("spec", {}).get("destination", {}).get("namespace")
                    })

                return apps
            else:
                logger.error(f"Failed to list applications: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Exception listing applications: {e}")
            return []

    def sync_application(
        self,
        app_name: str,
        revision: Optional[str] = None,
        prune: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Trigger application sync.

        Args:
            app_name: Application name
            revision: Target revision
            prune: Prune resources
            dry_run: Dry run mode

        Returns:
            Sync operation result
        """
        logger.info(f"Syncing application: {app_name}")

        url = f"{self.argocd_url}/api/v1/applications/{app_name}/sync"

        sync_request = {
            "revision": revision or "HEAD",
            "prune": prune,
            "dryRun": dry_run
        }

        try:
            response = self.session.post(url, json=sync_request, timeout=10)

            if response.status_code in [200, 202]:
                logger.info(f"Sync triggered successfully: {app_name}")
                return {
                    "status": "syncing",
                    "app_name": app_name,
                    "revision": revision or "HEAD",
                    "synced_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "app_name": app_name,
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Exception syncing application: {e}")
            return {
                "status": "error",
                "app_name": app_name,
                "error": str(e),
                "note": "ArgoCD server may not be available (mock mode)"
            }

    def get_application_health(self, app_name: str) -> Dict[str, Any]:
        """
        Get application health status.

        Args:
            app_name: Application name

        Returns:
            Health status
        """
        url = f"{self.argocd_url}/api/v1/applications/{app_name}"

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                app = response.json()
                health = app.get("status", {}).get("health", {})
                resources = app.get("status", {}).get("resources", [])

                # Count resource health
                healthy = sum(1 for r in resources if r.get("health", {}).get("status") == "Healthy")
                degraded = sum(1 for r in resources if r.get("health", {}).get("status") == "Degraded")

                return {
                    "app_name": app_name,
                    "health_status": health.get("status"),
                    "health_message": health.get("message"),
                    "total_resources": len(resources),
                    "healthy_resources": healthy,
                    "degraded_resources": degraded
                }
            else:
                return {
                    "app_name": app_name,
                    "error": "Application not found"
                }

        except Exception as e:
            logger.error(f"Exception getting health: {e}")
            return {
                "app_name": app_name,
                "error": str(e),
                "note": "ArgoCD server may not be available (mock mode)"
            }

    def get_resource_tree(self, app_name: str) -> Dict[str, Any]:
        """
        Get application resource tree.

        Args:
            app_name: Application name

        Returns:
            Resource tree
        """
        url = f"{self.argocd_url}/api/v1/applications/{app_name}/resource-tree"

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                tree = response.json()
                nodes = tree.get("nodes", [])

                # Summarize resources by kind
                resources_by_kind = {}
                for node in nodes:
                    kind = node.get("kind")
                    resources_by_kind[kind] = resources_by_kind.get(kind, 0) + 1

                return {
                    "app_name": app_name,
                    "total_resources": len(nodes),
                    "resources_by_kind": resources_by_kind
                }
            else:
                return {
                    "app_name": app_name,
                    "error": "Resource tree not available"
                }

        except Exception as e:
            logger.error(f"Exception getting resource tree: {e}")
            return {
                "app_name": app_name,
                "error": str(e),
                "note": "ArgoCD server may not be available (mock mode)"
            }

    def rollback_application(
        self,
        app_name: str,
        history_id: int
    ) -> Dict[str, Any]:
        """
        Rollback application to previous revision.

        Args:
            app_name: Application name
            history_id: History ID to rollback to

        Returns:
            Rollback result
        """
        logger.info(f"Rolling back application: {app_name} to history {history_id}")

        url = f"{self.argocd_url}/api/v1/applications/{app_name}/rollback"

        rollback_request = {
            "id": history_id
        }

        try:
            response = self.session.post(url, json=rollback_request, timeout=10)

            if response.status_code in [200, 202]:
                logger.info(f"Rollback triggered successfully: {app_name}")
                return {
                    "status": "rollback_initiated",
                    "app_name": app_name,
                    "history_id": history_id,
                    "rolled_back_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "app_name": app_name,
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Exception rolling back application: {e}")
            return {
                "status": "error",
                "app_name": app_name,
                "error": str(e),
                "note": "ArgoCD server may not be available (mock mode)"
            }

    def delete_application(
        self,
        app_name: str,
        cascade: bool = True
    ) -> Dict[str, Any]:
        """
        Delete application.

        Args:
            app_name: Application name
            cascade: Delete with cascade (delete resources)

        Returns:
            Deletion result
        """
        logger.info(f"Deleting application: {app_name}")

        url = f"{self.argocd_url}/api/v1/applications/{app_name}"
        params = {"cascade": str(cascade).lower()}

        try:
            response = self.session.delete(url, params=params, timeout=10)

            if response.status_code in [200, 204]:
                logger.info(f"Application deleted successfully: {app_name}")
                return {
                    "status": "deleted",
                    "app_name": app_name,
                    "deleted_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "app_name": app_name,
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Exception deleting application: {e}")
            return {
                "status": "error",
                "app_name": app_name,
                "error": str(e),
                "note": "ArgoCD server may not be available (mock mode)"
            }


# ============================================================================
# Testing
# ============================================================================

def test_argocd_api_client():
    """Test ArgoCD API client."""
    logger.info("Testing ArgoCD API Client...")

    # Initialize client
    client = ArgoCDAPIClient(
        argocd_url="http://localhost:8080",
        auth_token="test-token"
    )

    # Test 1: Create application
    print("\n=== Test 1: Create Application ===")
    app_manifest = {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Application",
        "metadata": {"name": "test-app"},
        "spec": {
            "project": "default",
            "source": {
                "repoURL": "https://github.com/myorg/repo",
                "path": "apps/test",
                "targetRevision": "HEAD"
            },
            "destination": {
                "server": "https://kubernetes.default.svc",
                "namespace": "default"
            }
        }
    }
    result = client.create_application(app_manifest)
    print(json.dumps(result, indent=2))

    # Test 2: Get application
    print("\n=== Test 2: Get Application ===")
    app = client.get_application("test-app")
    print(json.dumps(app, indent=2))

    # Test 3: Sync application
    print("\n=== Test 3: Sync Application ===")
    sync = client.sync_application("test-app", prune=True)
    print(json.dumps(sync, indent=2))

    # Test 4: Get health
    print("\n=== Test 4: Get Health Status ===")
    health = client.get_application_health("test-app")
    print(json.dumps(health, indent=2))


if __name__ == "__main__":
    test_argocd_api_client()
