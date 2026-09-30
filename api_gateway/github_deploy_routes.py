"""
GitHub Repository Deployment Routes
====================================

Deploy directly from GitHub repositories to AWS S3.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import subprocess
import tempfile
import shutil
import os

from aws_static_deploy import deploy_to_s3

router = APIRouter(prefix="/api/v1/deploy", tags=["github-deploy"])


class DeployGitHubRequest(BaseModel):
    app_name: str
    repo_url: str
    branch: str = "main"
    bucket_name: str
    region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None


@router.post("/github/aws")
async def deploy_github_to_aws(request: DeployGitHubRequest):
    """
    Clone a GitHub repository and deploy it to AWS S3.

    Steps:
    1. Clone the GitHub repo to a temp directory
    2. Deploy the cloned files to S3
    3. Clean up temp directory
    """
    if not request.repo_url.strip():
        raise HTTPException(status_code=400, detail="repo_url is required")

    if not request.bucket_name.strip():
        raise HTTPException(status_code=400, detail="bucket_name is required")

    # Validate GitHub URL
    if "github.com" not in request.repo_url.lower():
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL. Must contain 'github.com'",
        )

    temp_dir = None
    try:
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix=f"promptops-{request.app_name}-")

        # Clone repository
        clone_cmd = [
            "git",
            "clone",
            "--depth", "1",  # Shallow clone for speed
            "--branch", request.branch,
            request.repo_url,
            temp_dir,
        ]

        result = subprocess.run(
            clone_cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
        )

        if result.returncode != 0:
            raise Exception(f"Git clone failed: {result.stderr}")

        # Deploy to S3
        deploy_result = deploy_to_s3(
            source_path=temp_dir,
            bucket_name=request.bucket_name,
            region=request.region,
            aws_access_key_id=request.aws_access_key_id,
            aws_secret_access_key=request.aws_secret_access_key,
            aws_session_token=request.aws_session_token,
        )

        deploy_result["app_name"] = request.app_name
        deploy_result["repo_url"] = request.repo_url
        deploy_result["branch"] = request.branch

        return deploy_result

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408,
            detail="Git clone timeout. Repository may be too large or unreachable.",
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Deployment failed: {str(e)}"
        ) from e
    finally:
        # Clean up temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                # Log but don't fail the request
                print(f"Warning: Failed to cleanup temp dir {temp_dir}: {cleanup_error}")
