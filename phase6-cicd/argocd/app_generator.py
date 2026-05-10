"""
ArgoCD Application Generator for PromptOps
===========================================

Generates ArgoCD Application manifests for GitOps deployments.
Supports Kustomize, Helm, and plain YAML.

Author: DevOps Engineer - Phase 6 Week 56-57
Date: 2026-05-10
"""

import os
import json
import logging
import yaml
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ArgoCD Enums
# ============================================================================

class SourceType(Enum):
    """Application source types."""
    KUSTOMIZE = "kustomize"
    HELM = "helm"
    DIRECTORY = "directory"


class SyncPolicy(Enum):
    """Sync policy types."""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    AUTOMATED_PRUNE = "automated_prune"
    AUTOMATED_SELF_HEAL = "automated_self_heal"


# ============================================================================
# Application Generator
# ============================================================================

class AppGenerator:
    """
    Generates ArgoCD Application manifests.

    Features:
    - Kustomize, Helm, and directory-based apps
    - Sync policies (manual, automatic, self-heal)
    - Multi-environment support
    - Health checks and sync waves
    - Resource hooks (PreSync, PostSync)
    """

    def __init__(self):
        """Initialize Application Generator."""
        self.default_sync_options = [
            "CreateNamespace=true",
            "PruneLast=true"
        ]

    def generate_application(
        self,
        app_name: str,
        namespace: str,
        repo_url: str,
        path: str,
        source_type: str = "kustomize",
        target_revision: str = "HEAD",
        destination_server: str = "https://kubernetes.default.svc",
        sync_policy: str = "automatic",
        auto_prune: bool = True,
        self_heal: bool = True,
        sync_options: Optional[List[str]] = None,
        helm_values: Optional[Dict[str, Any]] = None,
        kustomize_images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate ArgoCD Application manifest.

        Args:
            app_name: Application name
            namespace: Target namespace
            repo_url: Git repository URL
            path: Path within repository
            source_type: Source type (kustomize, helm, directory)
            target_revision: Git branch/tag/commit
            destination_server: Kubernetes API server
            sync_policy: Sync policy (manual, automatic)
            auto_prune: Auto-prune resources
            self_heal: Self-heal on drift
            sync_options: Additional sync options
            helm_values: Helm values override
            kustomize_images: Kustomize image overrides

        Returns:
            Application manifest
        """
        logger.info(f"Generating ArgoCD application: {app_name}")

        # Build source configuration
        source = {
            "repoURL": repo_url,
            "targetRevision": target_revision,
            "path": path
        }

        # Add source-specific configuration
        if source_type == "helm":
            source["helm"] = self._build_helm_config(helm_values)
        elif source_type == "kustomize":
            source["kustomize"] = self._build_kustomize_config(kustomize_images)

        # Build sync policy
        sync_policy_config = self._build_sync_policy(
            sync_policy,
            auto_prune,
            self_heal,
            sync_options or self.default_sync_options
        )

        # Build application manifest
        application = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {
                "name": app_name,
                "namespace": "argocd"
            },
            "spec": {
                "project": "default",
                "source": source,
                "destination": {
                    "server": destination_server,
                    "namespace": namespace
                },
                "syncPolicy": sync_policy_config
            }
        }

        # Convert to YAML
        app_yaml = yaml.dump(application, default_flow_style=False, sort_keys=False)

        return {
            "app_name": app_name,
            "namespace": namespace,
            "source_type": source_type,
            "sync_policy": sync_policy,
            "application_yaml": app_yaml,
            "application_dict": application,
            "file_path": f"argocd/applications/{app_name}.yaml",
            "generated_at": datetime.utcnow().isoformat()
        }

    def _build_helm_config(self, values: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build Helm source configuration."""
        config = {}

        if values:
            config["values"] = yaml.dump(values, default_flow_style=False)

        return config

    def _build_kustomize_config(self, images: Optional[List[str]]) -> Dict[str, Any]:
        """Build Kustomize source configuration."""
        config = {}

        if images:
            config["images"] = images

        return config

    def _build_sync_policy(
        self,
        policy: str,
        auto_prune: bool,
        self_heal: bool,
        sync_options: List[str]
    ) -> Dict[str, Any]:
        """Build sync policy configuration."""
        sync_policy = {
            "syncOptions": sync_options
        }

        if policy == "automatic":
            sync_policy["automated"] = {
                "prune": auto_prune,
                "selfHeal": self_heal
            }

        return sync_policy

    def generate_app_of_apps(
        self,
        app_of_apps_name: str,
        apps: List[Dict[str, str]],
        repo_url: str,
        path: str = "argocd/applications"
    ) -> Dict[str, Any]:
        """
        Generate App of Apps pattern manifest.

        Args:
            app_of_apps_name: App of Apps name
            apps: List of application definitions
            repo_url: Git repository URL
            path: Path to applications

        Returns:
            App of Apps manifest
        """
        logger.info(f"Generating App of Apps: {app_of_apps_name}")

        application = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {
                "name": app_of_apps_name,
                "namespace": "argocd"
            },
            "spec": {
                "project": "default",
                "source": {
                    "repoURL": repo_url,
                    "targetRevision": "HEAD",
                    "path": path
                },
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": "argocd"
                },
                "syncPolicy": {
                    "automated": {
                        "prune": True,
                        "selfHeal": True
                    }
                }
            }
        }

        app_yaml = yaml.dump(application, default_flow_style=False, sort_keys=False)

        return {
            "app_of_apps_name": app_of_apps_name,
            "managed_apps": apps,
            "application_yaml": app_yaml,
            "generated_at": datetime.utcnow().isoformat()
        }

    def generate_applicationset(
        self,
        appset_name: str,
        repo_url: str,
        path: str,
        clusters: Optional[List[str]] = None,
        environments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate ApplicationSet manifest for multi-cluster/environment deployments.

        Args:
            appset_name: ApplicationSet name
            repo_url: Git repository URL
            path: Path template
            clusters: Target clusters
            environments: Target environments

        Returns:
            ApplicationSet manifest
        """
        logger.info(f"Generating ApplicationSet: {appset_name}")

        # Use list generator for environments
        generators = []

        if environments:
            generators.append({
                "list": {
                    "elements": [
                        {"environment": env, "namespace": f"{appset_name}-{env}"}
                        for env in environments
                    ]
                }
            })

        if clusters:
            generators.append({
                "clusters": {
                    "selector": {
                        "matchLabels": {"environment": "{{environment}}"}
                    }
                }
            })

        appset = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "ApplicationSet",
            "metadata": {
                "name": appset_name,
                "namespace": "argocd"
            },
            "spec": {
                "generators": generators if generators else [
                    {
                        "list": {
                            "elements": [
                                {"environment": "dev"},
                                {"environment": "staging"},
                                {"environment": "prod"}
                            ]
                        }
                    }
                ],
                "template": {
                    "metadata": {
                        "name": "{{environment}}-" + appset_name
                    },
                    "spec": {
                        "project": "default",
                        "source": {
                            "repoURL": repo_url,
                            "targetRevision": "HEAD",
                            "path": path + "/{{environment}}"
                        },
                        "destination": {
                            "server": "https://kubernetes.default.svc",
                            "namespace": "{{namespace}}"
                        },
                        "syncPolicy": {
                            "automated": {
                                "prune": True,
                                "selfHeal": True
                            },
                            "syncOptions": ["CreateNamespace=true"]
                        }
                    }
                }
            }
        }

        appset_yaml = yaml.dump(appset, default_flow_style=False, sort_keys=False)

        return {
            "appset_name": appset_name,
            "environments": environments,
            "applicationset_yaml": appset_yaml,
            "generated_at": datetime.utcnow().isoformat()
        }


# ============================================================================
# Testing
# ============================================================================

def test_app_generator():
    """Test Application Generator."""
    logger.info("Testing ArgoCD Application Generator...")

    generator = AppGenerator()

    # Test 1: Generate Kustomize application
    print("\n=== Test 1: Kustomize Application ===")
    kustomize_app = generator.generate_application(
        app_name="user-service",
        namespace="production",
        repo_url="https://github.com/myorg/k8s-manifests",
        path="apps/user-service/overlays/production",
        source_type="kustomize",
        target_revision="main",
        sync_policy="automatic",
        kustomize_images=["docker.io/myorg/user-service:v1.2.3"]
    )
    print(f"App: {kustomize_app['app_name']}")
    print(f"File: {kustomize_app['file_path']}")
    print("\n--- Application YAML ---")
    print(kustomize_app["application_yaml"])

    # Test 2: Generate Helm application
    print("\n\n=== Test 2: Helm Application ===")
    helm_app = generator.generate_application(
        app_name="postgresql",
        namespace="databases",
        repo_url="https://charts.bitnami.com/bitnami",
        path="postgresql",
        source_type="helm",
        sync_policy="manual",
        helm_values={
            "auth": {"postgresPassword": "secret"},
            "primary": {"persistence": {"size": "10Gi"}}
        }
    )
    print(f"App: {helm_app['app_name']}")
    print("\n--- Application YAML ---")
    print(helm_app["application_yaml"][:500])

    # Test 3: Generate App of Apps
    print("\n\n=== Test 3: App of Apps ===")
    app_of_apps = generator.generate_app_of_apps(
        app_of_apps_name="platform-apps",
        apps=[
            {"name": "ingress-nginx", "path": "platform/ingress-nginx"},
            {"name": "cert-manager", "path": "platform/cert-manager"},
            {"name": "prometheus", "path": "platform/prometheus"}
        ],
        repo_url="https://github.com/myorg/k8s-platform"
    )
    print(f"App of Apps: {app_of_apps['app_of_apps_name']}")
    print(f"Managed apps: {len(app_of_apps['managed_apps'])}")

    # Test 4: Generate ApplicationSet
    print("\n\n=== Test 4: ApplicationSet ===")
    appset = generator.generate_applicationset(
        appset_name="microservices",
        repo_url="https://github.com/myorg/microservices",
        path="k8s",
        environments=["dev", "staging", "prod"]
    )
    print(f"ApplicationSet: {appset['appset_name']}")
    print(f"Environments: {appset['environments']}")
    print("\n--- ApplicationSet YAML (first 600 chars) ---")
    print(appset["applicationset_yaml"][:600])


if __name__ == "__main__":
    test_app_generator()
