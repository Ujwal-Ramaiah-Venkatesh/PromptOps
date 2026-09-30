"""Google Kubernetes Engine discovery adapter."""

from typing import Any, Dict, List, Optional

from kubernetes_provider import KubernetesProvider, KubernetesProviderError, normalize_cluster


class GKEProvider(KubernetesProvider):
    name = "gke"

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id

    def _client(self):
        try:
            from google.cloud import container_v1
        except ImportError as exc:
            raise KubernetesProviderError(
                "google-cloud-container is required for GKE discovery"
            ) from exc
        if not self.project_id:
            raise KubernetesProviderError("GCP_PROJECT_ID is required for GKE discovery")
        return container_v1.ClusterManagerClient()

    def list_clusters(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        parent = f"projects/{self.project_id}/locations/-"
        response = self._client().list_clusters(parent=parent)
        return [self._normalize(cluster) for cluster in response.clusters if not region or cluster.location == region]

    def get_cluster(self, cluster_id: str) -> Dict[str, Any]:
        location, name = cluster_id.removeprefix("gke:").split("/", 1)
        cluster = self._client().get_cluster(name=f"projects/{self.project_id}/locations/{location}/clusters/{name}")
        return self._normalize(cluster)

    def _normalize(self, cluster: Any) -> Dict[str, Any]:
        return normalize_cluster(
            provider=self.name,
            cluster_id=f"gke:{cluster.location}/{cluster.name}",
            name=cluster.name,
            region=cluster.location,
            status=cluster.status.name.lower() if hasattr(cluster.status, "name") else str(cluster.status).lower(),
            version=cluster.current_master_version,
            endpoint=cluster.endpoint,
            node_count=cluster.current_node_count,
            raw={"self_link": cluster.self_link},
        )

    def capabilities(self) -> Dict[str, bool]:
        capabilities = super().capabilities()
        capabilities["node_inventory"] = True
        capabilities["workload_inventory"] = True
        return capabilities
