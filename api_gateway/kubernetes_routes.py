"""Unified EKS, AKS, GKE and Kubernetes inventory API."""

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from aks_provider import AKSProvider
from eks_provider import EKSProvider
from gke_provider import GKEProvider
from kubernetes_provider import KubernetesProviderError

router = APIRouter(prefix="/api/v1/kubernetes", tags=["kubernetes"])


def providers_for(requested: str, region: Optional[str] = None) -> List[Any]:
    names = [name.strip().lower() for name in requested.split(",") if name.strip()]
    if not names or "all" in names:
        names = ["eks", "aks", "gke"]
    providers = []
    for name in names:
        if name == "eks":
            providers.append(EKSProvider(region or os.getenv("AWS_REGION", "us-east-1")))
        elif name == "aks":
            providers.append(AKSProvider(os.getenv("AZURE_SUBSCRIPTION_ID")))
        elif name == "gke":
            providers.append(GKEProvider(os.getenv("GCP_PROJECT_ID")))
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported Kubernetes provider: {name}")
    return providers


@router.get("/providers")
async def list_kubernetes_providers() -> Dict[str, Any]:
    return {
        "providers": [
            {"name": "eks", "cloud": "aws", "display_name": "Amazon EKS"},
            {"name": "aks", "cloud": "azure", "display_name": "Azure Kubernetes Service"},
            {"name": "gke", "cloud": "gcp", "display_name": "Google Kubernetes Engine"},
        ]
    }


@router.get("/clusters")
async def list_kubernetes_clusters(
    provider: str = Query("all", description="eks, aks, gke, or all"),
    region: Optional[str] = None,
) -> Dict[str, Any]:
    clusters: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    for client in providers_for(provider, region):
        try:
            clusters.extend(client.list_clusters(region))
        except Exception as exc:
            errors.append({"provider": client.name, "error": str(exc)})
    return {"clusters": clusters, "total": len(clusters), "errors": errors}


def find_provider(cluster_id: str):
    prefix = cluster_id.split(":", 1)[0].lower()
    clients = {client.name: client for client in providers_for(prefix)}
    if prefix not in clients:
        raise HTTPException(status_code=400, detail="Cluster id must start with eks:, aks:, or gke:")
    return clients[prefix]


@router.get("/clusters/{cluster_id:path}/nodes")
async def list_kubernetes_nodes(cluster_id: str) -> Dict[str, Any]:
    try:
        nodes = find_provider(cluster_id).list_nodes(cluster_id)
        return {"cluster_id": cluster_id, "nodes": nodes, "total": len(nodes)}
    except KubernetesProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/clusters/{cluster_id:path}/workloads")
async def list_kubernetes_workloads(cluster_id: str) -> Dict[str, Any]:
    try:
        workloads = find_provider(cluster_id).list_workloads(cluster_id)
        return {"cluster_id": cluster_id, "workloads": workloads, "total": len(workloads)}
    except KubernetesProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/clusters/{cluster_id:path}")
async def get_kubernetes_cluster(cluster_id: str) -> Dict[str, Any]:
    try:
        return find_provider(cluster_id).get_cluster(cluster_id)
    except KubernetesProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
