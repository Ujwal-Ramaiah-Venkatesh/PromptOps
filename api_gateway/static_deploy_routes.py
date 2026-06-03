"""
Static Site Deployment Routes
=============================

Routes used by PromptOps UI to deploy static apps to AWS S3.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from aws_static_deploy import deploy_to_s3

router = APIRouter(prefix="/api/v1/deploy", tags=["static-deploy"])


class DeployAWSRequest(BaseModel):
    app_name: str = "sample-app"
    source_path: str
    bucket_name: str
    region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None


@router.post("/aws")
async def deploy_static_to_aws(request: DeployAWSRequest):
    """Deploy static site to AWS S3 and return website URL."""
    if not request.source_path.strip():
        raise HTTPException(status_code=400, detail="source_path is required")

    if not request.bucket_name.strip():
        raise HTTPException(status_code=400, detail="bucket_name is required")

    manual_mode = bool(request.aws_access_key_id or request.aws_secret_access_key)
    if manual_mode and not (request.aws_access_key_id and request.aws_secret_access_key):
        raise HTTPException(
            status_code=400,
            detail="Both aws_access_key_id and aws_secret_access_key are required for manual credentials",
        )

    try:
        result = deploy_to_s3(
            source_path=request.source_path,
            bucket_name=request.bucket_name,
            region=request.region,
            aws_access_key_id=request.aws_access_key_id,
            aws_secret_access_key=request.aws_secret_access_key,
            aws_session_token=request.aws_session_token,
        )
        result["app_name"] = request.app_name
        return result
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}") from e


@router.get("/status")
async def deploy_status():
    return {"status": "ready", "provider": "aws-s3-static"}
