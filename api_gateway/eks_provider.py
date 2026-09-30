"""Amazon EKS discovery adapter using ambient boto3 credentials."""

from typing import Any, Dict, List, Optional

from kubernetes_provider import KubernetesProvider, KubernetesProviderError, normalize_cluster


class EKSProvider(KubernetesProvider):
    name = "eks"

    def __init__(self, region: str = "us-east-1"):
        self.region = region

    def _client(self):
        try:
            import boto3
            return boto3.client("eks", region_name=self.region)
        except ImportError as exc:
            raise KubernetesProviderError("boto3 is required for EKS discovery") from exc

    def list_clusters(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        region = region or self.region
        client = self._client() if region == self.region else self.__class__(region)._client()
        names = client.list_clusters().get("clusters", [])
        return [self.get_cluster(name) for name in names]

    def get_cluster(self, cluster_id: str) -> Dict[str, Any]:
        cluster = self._client().describe_cluster(name=cluster_id).get("cluster", {})
        return normalize_cluster(
            provider=self.name,
            cluster_id=f"eks:{self.region}:{cluster_id}",
            name=cluster.get("name", cluster_id),
            region=self.region,
            status=cluster.get("status", "UNKNOWN").lower(),
            version=cluster.get("version"),
            endpoint=cluster.get("endpoint"),
            raw={"arn": cluster.get("arn"), "role_arn": cluster.get("roleArn")},
        )

    def capabilities(self) -> Dict[str, bool]:
        capabilities = super().capabilities()
        capabilities["node_inventory"] = True
        capabilities["workload_inventory"] = True
        return capabilities
