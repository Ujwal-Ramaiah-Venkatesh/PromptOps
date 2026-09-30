"""Contract tests for the unified Kubernetes API."""

import asyncio
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parents[1] / "api_gateway"))

import kubernetes_routes
from kubernetes_provider import KubernetesProviderError, normalize_cluster


def request(method: str, path: str, **kwargs):
    import main

    async def run():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(run())


def test_provider_catalog_exposes_all_managed_kubernetes_services():
    response = request("GET", "/api/v1/kubernetes/providers")
    assert response.status_code == 200
    assert {item["name"] for item in response.json()["providers"]} == {"eks", "aks", "gke"}


def test_normalized_cluster_contract():
    cluster = normalize_cluster(
        provider="eks",
        cluster_id="eks:us-east-1/demo",
        name="demo",
        region="us-east-1",
        status="active",
        version="1.30",
    )
    assert cluster["id"] == "eks:us-east-1/demo"
    assert cluster["provider"] == "eks"
    assert cluster["capabilities"]["workload_inventory"] is True


def test_cluster_listing_returns_per_provider_errors_without_credentials():
    response = request("GET", "/api/v1/kubernetes/clusters", params={"provider": "aks,gke"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["clusters"] == []
    assert {error["provider"] for error in payload["errors"]} == {"aks", "gke"}


def test_unknown_provider_is_rejected():
    response = request("GET", "/api/v1/kubernetes/clusters", params={"provider": "digitalocean"})
    assert response.status_code == 400
    assert "Unsupported Kubernetes provider" in response.json()["detail"]


def test_workload_inventory_reports_missing_kube_context():
    response = request("GET", "/api/v1/kubernetes/clusters/eks:us-east-1/demo/workloads")
    assert response.status_code == 503
    assert "kubeconfig" in response.json()["detail"].lower()
