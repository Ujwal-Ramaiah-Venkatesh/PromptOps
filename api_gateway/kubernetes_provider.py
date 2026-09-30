"""Unified Kubernetes provider contract and normalized response models."""

from abc import ABC, abstractmethod
import os
import importlib.machinery
import importlib.util
import sys
import sysconfig
from typing import Any, Dict, List, Optional


class KubernetesProviderError(RuntimeError):
    """Raised when a provider cannot service a Kubernetes request."""


class KubernetesProvider(ABC):
    name: str

    @abstractmethod
    def list_clusters(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return normalized managed-cluster summaries."""

    @abstractmethod
    def get_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Return normalized details for one managed cluster."""

    def list_nodes(self, cluster_id: str) -> List[Dict[str, Any]]:
        core_api = self._core_api()
        try:
            nodes = core_api.list_node().items
        except Exception as exc:
            raise KubernetesProviderError(
                "Kubernetes API is not reachable; configure a valid kubeconfig and KUBERNETES_CONTEXT"
            ) from exc
        return [
            {
                "name": node.metadata.name,
                "status": next(
                    (condition.status for condition in (node.status.conditions or []) if condition.type == "Ready"),
                    "Unknown",
                ),
                "capacity": node.status.capacity or {},
                "labels": node.metadata.labels or {},
            }
            for node in nodes
        ]

    def list_workloads(self, cluster_id: str) -> List[Dict[str, Any]]:
        try:
            client, _ = _load_kubernetes_modules()
        except ImportError as exc:
            raise KubernetesProviderError(
                "kubernetes package and a valid kubeconfig are required for workload inventory"
            ) from exc
        apps_api = client.AppsV1Api()
        try:
            deployments = apps_api.list_deployment_for_all_namespaces().items
        except Exception as exc:
            raise KubernetesProviderError(
                "Kubernetes API is not reachable; configure a valid kubeconfig and KUBERNETES_CONTEXT"
            ) from exc
        return [
            {
                "kind": "Deployment",
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "desired_replicas": deployment.spec.replicas or 0,
                "available_replicas": deployment.status.available_replicas or 0,
            }
            for deployment in deployments
        ]

    def _core_api(self):
        try:
            client, config = _load_kubernetes_modules()
        except ImportError as exc:
            raise KubernetesProviderError(
                "kubernetes package and a valid kubeconfig are required for cluster inventory"
            ) from exc
        try:
            config.load_kube_config(context=os.getenv("KUBERNETES_CONTEXT") or None)
        except Exception as exc:
            raise KubernetesProviderError(
                "KUBERNETES_CONTEXT or a valid local kubeconfig is required for node/workload inventory"
            ) from exc
        return client.CoreV1Api()


def _load_kubernetes_modules():
    """Load the SDK without letting api_gateway/websocket shadow websocket-client."""
    local_websocket = sys.modules.get("websocket")
    local_path = getattr(local_websocket, "__file__", "") if local_websocket else ""
    external_websocket = None
    if "api_gateway" in local_path.replace("\\", "/"):
        purelib = sysconfig.get_paths()["purelib"]
        spec = importlib.machinery.PathFinder.find_spec("websocket", [purelib])
        if spec and spec.loader:
            external_websocket = importlib.util.module_from_spec(spec)
            sys.modules["websocket"] = external_websocket
            spec.loader.exec_module(external_websocket)
    try:
        from kubernetes import client, config
        return client, config
    finally:
        if local_websocket is not None:
            sys.modules["websocket"] = local_websocket

    def capabilities(self) -> Dict[str, bool]:
        return {
            "cluster_discovery": True,
            "node_inventory": False,
            "workload_inventory": False,
            "metrics": False,
            "provisioning": False,
        }


def normalize_cluster(
    *,
    provider: str,
    cluster_id: str,
    name: str,
    region: Optional[str],
    status: str,
    version: Optional[str] = None,
    endpoint: Optional[str] = None,
    node_count: Optional[int] = None,
    raw: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "id": cluster_id,
        "name": name,
        "provider": provider,
        "region": region,
        "status": status,
        "version": version,
        "endpoint": endpoint,
        "node_count": node_count,
        "capabilities": {
            "cluster_discovery": True,
            "node_inventory": True,
            "workload_inventory": True,
            "metrics": False,
            "provisioning": False,
        },
        "raw": raw or {},
    }
