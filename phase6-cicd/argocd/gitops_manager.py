"""
GitOps Manager for PromptOps
=============================

Manages GitOps repository structure for ArgoCD deployments.
Generates Kustomize overlays and Helm values per environment.

Author: DevOps Engineer - Phase 6 Week 56-57
Date: 2026-05-10
"""

import os
import json
import logging
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# GitOps Manager
# ============================================================================

class GitOpsManager:
    """
    Manages GitOps repository structure.

    Features:
    - Kustomize base + overlays structure
    - Helm values per environment
    - Multi-environment management
    - ConfigMap/Secret templates
    - Progressive rollout configs
    """

    def __init__(self, repo_path: str = "./gitops-repo"):
        """
        Initialize GitOps Manager.

        Args:
            repo_path: Path to GitOps repository
        """
        self.repo_path = repo_path

    def create_kustomize_structure(
        self,
        app_name: str,
        environments: List[str],
        base_manifests: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create Kustomize base + overlays structure.

        Args:
            app_name: Application name
            environments: List of environments
            base_manifests: Base Kubernetes manifests

        Returns:
            Structure information
        """
        logger.info(f"Creating Kustomize structure for {app_name}")

        structure = {
            "app_name": app_name,
            "base_path": f"{app_name}/base",
            "overlays": {}
        }

        # Create base kustomization
        base_kustomization = {
            "apiVersion": "kustomize.config.k8s.io/v1beta1",
            "kind": "Kustomization",
            "resources": [
                "deployment.yaml",
                "service.yaml"
            ],
            "commonLabels": {
                "app": app_name
            }
        }

        structure["base_kustomization"] = yaml.dump(base_kustomization, default_flow_style=False)

        # Create base deployment
        base_deployment = self._create_base_deployment(app_name)
        structure["base_deployment"] = yaml.dump(base_deployment, default_flow_style=False)

        # Create base service
        base_service = self._create_base_service(app_name)
        structure["base_service"] = yaml.dump(base_service, default_flow_style=False)

        # Create overlays for each environment
        for env in environments:
            overlay_path = f"{app_name}/overlays/{env}"
            overlay_kustomization = self._create_overlay_kustomization(env, app_name)

            structure["overlays"][env] = {
                "path": overlay_path,
                "kustomization": yaml.dump(overlay_kustomization, default_flow_style=False)
            }

        return structure

    def _create_base_deployment(self, app_name: str) -> Dict[str, Any]:
        """Create base deployment manifest."""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": app_name
            },
            "spec": {
                "replicas": 2,
                "selector": {
                    "matchLabels": {
                        "app": app_name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": app_name
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": app_name,
                                "image": f"{app_name}:latest",
                                "ports": [
                                    {
                                        "containerPort": 8080,
                                        "name": "http"
                                    }
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "128Mi"
                                    },
                                    "limits": {
                                        "cpu": "500m",
                                        "memory": "512Mi"
                                    }
                                },
                                "livenessProbe": {
                                    "httpGet": {
                                        "path": "/health",
                                        "port": "http"
                                    },
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 10
                                },
                                "readinessProbe": {
                                    "httpGet": {
                                        "path": "/ready",
                                        "port": "http"
                                    },
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 5
                                }
                            }
                        ]
                    }
                }
            }
        }

    def _create_base_service(self, app_name: str) -> Dict[str, Any]:
        """Create base service manifest."""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": app_name
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "port": 80,
                        "targetPort": "http",
                        "protocol": "TCP",
                        "name": "http"
                    }
                ],
                "selector": {
                    "app": app_name
                }
            }
        }

    def _create_overlay_kustomization(self, env: str, app_name: str) -> Dict[str, Any]:
        """Create overlay kustomization."""
        kustomization = {
            "apiVersion": "kustomize.config.k8s.io/v1beta1",
            "kind": "Kustomization",
            "namespace": f"{app_name}-{env}",
            "bases": [
                "../../base"
            ],
            "namePrefix": f"{env}-",
            "commonLabels": {
                "environment": env
            }
        }

        # Environment-specific patches
        if env == "prod":
            kustomization["replicas"] = [
                {
                    "name": app_name,
                    "count": 5
                }
            ]
            kustomization["images"] = [
                {
                    "name": f"{app_name}:latest",
                    "newTag": "stable"
                }
            ]
        elif env == "staging":
            kustomization["replicas"] = [
                {
                    "name": app_name,
                    "count": 3
                }
            ]
        else:  # dev
            kustomization["replicas"] = [
                {
                    "name": app_name,
                    "count": 1
                }
            ]

        return kustomization

    def create_helm_values(
        self,
        app_name: str,
        environments: List[str],
        base_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create Helm values files per environment.

        Args:
            app_name: Application name
            environments: List of environments
            base_values: Base Helm values

        Returns:
            Values files information
        """
        logger.info(f"Creating Helm values for {app_name}")

        values_files = {
            "app_name": app_name,
            "base_values": base_values or self._get_default_helm_values(app_name),
            "environment_values": {}
        }

        for env in environments:
            env_values = self._create_environment_values(env, app_name)
            values_files["environment_values"][env] = env_values

        return values_files

    def _get_default_helm_values(self, app_name: str) -> Dict[str, Any]:
        """Get default Helm values."""
        return {
            "image": {
                "repository": f"docker.io/myorg/{app_name}",
                "tag": "latest",
                "pullPolicy": "IfNotPresent"
            },
            "service": {
                "type": "ClusterIP",
                "port": 80
            },
            "resources": {
                "requests": {
                    "cpu": "100m",
                    "memory": "128Mi"
                },
                "limits": {
                    "cpu": "500m",
                    "memory": "512Mi"
                }
            },
            "autoscaling": {
                "enabled": False
            }
        }

    def _create_environment_values(self, env: str, app_name: str) -> Dict[str, Any]:
        """Create environment-specific values."""
        values = {}

        if env == "prod":
            values = {
                "replicaCount": 5,
                "image": {
                    "tag": "stable"
                },
                "resources": {
                    "requests": {
                        "cpu": "500m",
                        "memory": "1Gi"
                    },
                    "limits": {
                        "cpu": "2000m",
                        "memory": "2Gi"
                    }
                },
                "autoscaling": {
                    "enabled": True,
                    "minReplicas": 5,
                    "maxReplicas": 20,
                    "targetCPUUtilizationPercentage": 70
                },
                "ingress": {
                    "enabled": True,
                    "hosts": [f"{app_name}.example.com"]
                }
            }
        elif env == "staging":
            values = {
                "replicaCount": 3,
                "image": {
                    "tag": "staging"
                },
                "resources": {
                    "requests": {
                        "cpu": "200m",
                        "memory": "256Mi"
                    },
                    "limits": {
                        "cpu": "1000m",
                        "memory": "1Gi"
                    }
                },
                "ingress": {
                    "enabled": True,
                    "hosts": [f"{app_name}-staging.example.com"]
                }
            }
        else:  # dev
            values = {
                "replicaCount": 1,
                "image": {
                    "tag": "dev"
                }
            }

        return values

    def create_progressive_rollout(
        self,
        app_name: str,
        stages: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create progressive rollout configuration (Argo Rollouts).

        Args:
            app_name: Application name
            stages: Rollout stages

        Returns:
            Rollout manifest
        """
        logger.info(f"Creating progressive rollout for {app_name}")

        rollout = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Rollout",
            "metadata": {
                "name": app_name
            },
            "spec": {
                "replicas": 5,
                "selector": {
                    "matchLabels": {
                        "app": app_name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": app_name
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": app_name,
                                "image": f"{app_name}:latest",
                                "ports": [
                                    {
                                        "containerPort": 8080,
                                        "name": "http"
                                    }
                                ]
                            }
                        ]
                    }
                },
                "strategy": {
                    "canary": {
                        "steps": stages or [
                            {"setWeight": 10},
                            {"pause": {"duration": "1m"}},
                            {"setWeight": 25},
                            {"pause": {"duration": "2m"}},
                            {"setWeight": 50},
                            {"pause": {"duration": "3m"}},
                            {"setWeight": 75},
                            {"pause": {"duration": "2m"}}
                        ]
                    }
                }
            }
        }

        rollout_yaml = yaml.dump(rollout, default_flow_style=False, sort_keys=False)

        return {
            "app_name": app_name,
            "strategy": "canary",
            "stages": len(rollout["spec"]["strategy"]["canary"]["steps"]),
            "rollout_yaml": rollout_yaml
        }

    def generate_configmap_template(
        self,
        app_name: str,
        config_data: Dict[str, str]
    ) -> str:
        """Generate ConfigMap template."""
        configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{app_name}-config"
            },
            "data": config_data
        }

        return yaml.dump(configmap, default_flow_style=False)


# ============================================================================
# Testing
# ============================================================================

def test_gitops_manager():
    """Test GitOps Manager."""
    logger.info("Testing GitOps Manager...")

    manager = GitOpsManager()

    # Test 1: Create Kustomize structure
    print("\n=== Test 1: Kustomize Structure ===")
    kustomize = manager.create_kustomize_structure(
        app_name="user-service",
        environments=["dev", "staging", "prod"]
    )
    print(f"App: {kustomize['app_name']}")
    print(f"Base path: {kustomize['base_path']}")
    print(f"Overlays: {list(kustomize['overlays'].keys())}")
    print("\n--- Base Kustomization ---")
    print(kustomize["base_kustomization"])

    # Test 2: Create Helm values
    print("\n\n=== Test 2: Helm Values ===")
    helm_values = manager.create_helm_values(
        app_name="api-gateway",
        environments=["dev", "staging", "prod"]
    )
    print(f"App: {helm_values['app_name']}")
    print("\n--- Production Values ---")
    print(yaml.dump(helm_values["environment_values"]["prod"], default_flow_style=False))

    # Test 3: Create progressive rollout
    print("\n\n=== Test 3: Progressive Rollout ===")
    rollout = manager.create_progressive_rollout("payment-service")
    print(f"App: {rollout['app_name']}")
    print(f"Strategy: {rollout['strategy']}")
    print(f"Stages: {rollout['stages']}")
    print("\n--- Rollout YAML (first 500 chars) ---")
    print(rollout["rollout_yaml"][:500])


if __name__ == "__main__":
    test_gitops_manager()
