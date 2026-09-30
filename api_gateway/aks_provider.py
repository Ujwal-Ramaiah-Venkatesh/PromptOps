"""Azure Kubernetes Service discovery adapter."""

from typing import Any, Dict, List, Optional

from kubernetes_provider import KubernetesProvider, KubernetesProviderError, normalize_cluster


class AKSProvider(KubernetesProvider):
    name = "aks"

    def __init__(self, subscription_id: Optional[str] = None):
        self.subscription_id = subscription_id

    def _client(self):
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.containerservice import ContainerServiceClient
        except ImportError as exc:
            raise KubernetesProviderError(
                "azure-identity and azure-mgmt-containerservice are required for AKS discovery"
            ) from exc
        if not self.subscription_id:
            raise KubernetesProviderError("AZURE_SUBSCRIPTION_ID is required for AKS discovery")
        return ContainerServiceClient(DefaultAzureCredential(), self.subscription_id)

    def list_clusters(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        clusters = self._client().managed_clusters.list()
        return [self._normalize(cluster) for cluster in clusters if not region or cluster.location == region]

    def get_cluster(self, cluster_id: str) -> Dict[str, Any]:
        resource_group, name = cluster_id.removeprefix("aks:").split("/", 1)
        cluster = self._client().managed_clusters.get(resource_group, name)
        return self._normalize(cluster, resource_group)

    def _normalize(self, cluster: Any, resource_group: Optional[str] = None) -> Dict[str, Any]:
        resource_group = resource_group or (cluster.id.split("/resourceGroups/")[1].split("/")[0] if cluster.id else "")
        return normalize_cluster(
            provider=self.name,
            cluster_id=f"aks:{resource_group}/{cluster.name}",
            name=cluster.name,
            region=cluster.location,
            status=(cluster.provisioning_state or "unknown").lower(),
            version=cluster.kubernetes_version,
            endpoint=cluster.fqdn,
            node_count=sum((pool.count or 0) for pool in (cluster.agent_pool_profiles or [])),
            raw={"resource_group": resource_group, "id": cluster.id},
        )

    def capabilities(self) -> Dict[str, bool]:
        capabilities = super().capabilities()
        capabilities["node_inventory"] = True
        capabilities["workload_inventory"] = True
        return capabilities
