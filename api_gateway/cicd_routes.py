"""
CI/CD API Routes for PromptOps
===============================

API endpoints for Jenkins pipeline management:
- Pipeline generation
- Job creation and management
- Build triggering and monitoring

Author: Backend Engineer - Phase 6 Week 52-53
Date: 2026-05-10
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import sys
import os
import logging

# Add phase6-cicd to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase6-cicd'))

from jenkins.pipeline_generator import PipelineGenerator
from jenkins.jenkinsfile_builder import JenkinsfileBuilder
from jenkins.jenkins_api_client import JenkinsAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/cicd", tags=["cicd"])

# Initialize components
pipeline_generator = PipelineGenerator()
jenkins_client = JenkinsAPIClient(
    jenkins_url=os.getenv("JENKINS_URL", "http://localhost:8080"),
    username=os.getenv("JENKINS_USER"),
    api_token=os.getenv("JENKINS_TOKEN")
)


# ============================================================================
# Request/Response Models
# ============================================================================

class PipelineGenerationRequest(BaseModel):
    """Request to generate pipeline."""
    pipeline_name: str
    pipeline_type: str = "declarative"
    build_tool: str = "maven"
    deployment_strategy: str = "rolling"
    environments: List[str] = ["dev"]
    enable_tests: bool = True
    enable_security_scan: bool = True
    enable_docker: bool = False
    docker_registry: Optional[str] = None
    kubernetes_cluster: Optional[str] = None


class JobCreationRequest(BaseModel):
    """Request to create Jenkins job."""
    job_name: str
    jenkinsfile: str
    description: str = ""
    git_repo: Optional[str] = None
    git_branch: str = "main"


class BuildTriggerRequest(BaseModel):
    """Request to trigger build."""
    job_name: str
    parameters: Optional[Dict[str, Any]] = None


# ============================================================================
# Pipeline Generation Endpoints
# ============================================================================

@router.post("/pipelines/generate")
async def generate_pipeline(request: PipelineGenerationRequest):
    """
    Generate Jenkins pipeline from requirements.

    **Pipeline Types:** declarative, scripted
    **Build Tools:** maven, gradle, npm, yarn, docker, make
    **Deployment Strategies:** rolling, blue_green, canary, recreate
    """
    try:
        pipeline = pipeline_generator.generate_pipeline(
            pipeline_name=request.pipeline_name,
            pipeline_type=request.pipeline_type,
            build_tool=request.build_tool,
            deployment_strategy=request.deployment_strategy,
            environments=request.environments,
            enable_tests=request.enable_tests,
            enable_security_scan=request.enable_security_scan,
            enable_docker=request.enable_docker,
            docker_registry=request.docker_registry,
            kubernetes_cluster=request.kubernetes_cluster
        )
        return pipeline

    except Exception as e:
        logger.error(f"Failed to generate pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipelines/templates")
async def list_pipeline_templates():
    """List available pipeline templates."""
    return {
        "templates": [
            {
                "name": "maven-basic",
                "description": "Basic Maven build pipeline",
                "build_tool": "maven",
                "stages": ["checkout", "build", "test", "deploy"]
            },
            {
                "name": "docker-kubernetes",
                "description": "Docker build with Kubernetes deployment",
                "build_tool": "docker",
                "stages": ["checkout", "build", "test", "docker-build", "k8s-deploy"]
            },
            {
                "name": "npm-microservice",
                "description": "NPM microservice pipeline",
                "build_tool": "npm",
                "stages": ["checkout", "build", "test", "docker-build", "deploy"]
            },
            {
                "name": "gradle-multi-env",
                "description": "Gradle pipeline with multiple environments",
                "build_tool": "gradle",
                "stages": ["checkout", "build", "test", "deploy-dev", "deploy-staging", "deploy-prod"]
            }
        ]
    }


# ============================================================================
# Jenkins Job Management Endpoints
# ============================================================================

@router.post("/jenkins/jobs")
async def create_jenkins_job(request: JobCreationRequest):
    """
    Create Jenkins pipeline job.

    Creates a new pipeline job in Jenkins with the provided Jenkinsfile.
    """
    try:
        result = jenkins_client.create_job(
            job_name=request.job_name,
            jenkinsfile=request.jenkinsfile,
            description=request.description,
            git_repo=request.git_repo,
            git_branch=request.git_branch
        )
        return result

    except Exception as e:
        logger.error(f"Failed to create Jenkins job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jenkins/jobs")
async def list_jenkins_jobs():
    """List all Jenkins jobs."""
    try:
        jobs = jenkins_client.list_jobs()
        return {"total": len(jobs), "jobs": jobs}

    except Exception as e:
        logger.error(f"Failed to list Jenkins jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jenkins/jobs/{job_name}")
async def delete_jenkins_job(job_name: str):
    """Delete Jenkins job."""
    try:
        result = jenkins_client.delete_job(job_name)
        return result

    except Exception as e:
        logger.error(f"Failed to delete Jenkins job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Build Management Endpoints
# ============================================================================

@router.post("/jenkins/builds/trigger")
async def trigger_jenkins_build(request: BuildTriggerRequest):
    """
    Trigger Jenkins build.

    Triggers a new build for the specified job. Optionally pass build parameters.
    """
    try:
        result = jenkins_client.trigger_build(
            job_name=request.job_name,
            parameters=request.parameters
        )
        return result

    except Exception as e:
        logger.error(f"Failed to trigger build: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jenkins/builds/{job_name}/status")
async def get_build_status(job_name: str, build_number: Optional[int] = None):
    """
    Get build status.

    Get status of specific build or latest build if build_number not provided.
    """
    try:
        status = jenkins_client.get_build_status(
            job_name=job_name,
            build_number=build_number
        )
        return status

    except Exception as e:
        logger.error(f"Failed to get build status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jenkins/builds/{job_name}/{build_number}/log")
async def get_build_log(job_name: str, build_number: int, start_line: int = 0):
    """
    Get build console log.

    Retrieve console output from a build. Use start_line for progressive log fetching.
    """
    try:
        log = jenkins_client.get_build_log(
            job_name=job_name,
            build_number=build_number,
            start_line=start_line
        )
        return log

    except Exception as e:
        logger.error(f"Failed to get build log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Jenkinsfile Builder Endpoints
# ============================================================================

@router.post("/jenkinsfile/build")
async def build_jenkinsfile(
    pipeline_type: str = "declarative",
    build_tool: str = "maven",
    include_tests: bool = True,
    include_deploy: bool = True
):
    """
    Build Jenkinsfile programmatically using fluent API.

    **Example:** Build a Maven pipeline with tests and deployment stages.
    """
    try:
        builder = JenkinsfileBuilder(pipeline_type)

        # Basic Maven pipeline
        builder = builder \
            .agent(label="maven") \
            .environment(
                MAVEN_OPTS="-Xmx1024m",
                BUILD_TOOL=build_tool
            ) \
            .options(
                "timestamps()",
                "buildDiscarder(logRotator(numToKeepStr: '10'))"
            ) \
            .stage("Checkout", ["checkout scm"])

        # Build stage
        if build_tool == "maven":
            builder = builder.stage("Build", [
                "sh 'mvn clean package -DskipTests'"
            ])
        elif build_tool == "npm":
            builder = builder.stage("Build", [
                "sh 'npm install'",
                "sh 'npm run build'"
            ])
        elif build_tool == "gradle":
            builder = builder.stage("Build", [
                "sh './gradlew clean build -x test'"
            ])

        # Test stage
        if include_tests:
            if build_tool == "maven":
                builder = builder.stage("Test", [
                    "sh 'mvn test'",
                    "junit '**/target/surefire-reports/*.xml'"
                ])
            elif build_tool == "npm":
                builder = builder.stage("Test", ["sh 'npm test'"])

        # Deploy stage
        if include_deploy:
            builder = builder.stage("Deploy", [
                "echo 'Deploying application...'",
                "sh 'kubectl apply -f k8s/ || echo \"Deployment skipped\"'"
            ])

        # Post actions
        builder = builder \
            .post("always", "cleanWs()") \
            .post("success", "echo 'Pipeline succeeded!'") \
            .post("failure", "echo 'Pipeline failed!'")

        jenkinsfile = builder.build()

        return {
            "pipeline_type": pipeline_type,
            "build_tool": build_tool,
            "jenkinsfile": jenkinsfile
        }

    except Exception as e:
        logger.error(f"Failed to build Jenkinsfile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Jenkins Server Endpoints
# ============================================================================

@router.get("/jenkins/info")
async def get_jenkins_server_info():
    """Get Jenkins server information."""
    try:
        info = jenkins_client.get_server_info()
        return info

    except Exception as e:
        logger.error(f"Failed to get Jenkins info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Endpoint
# ============================================================================

@router.get("/health")
async def cicd_health():
    """Check CI/CD service health."""
    jenkins_status = jenkins_client.get_server_info()

    return {
        "status": "healthy",
        "components": {
            "pipeline_generator": "ok",
            "jenkinsfile_builder": "ok",
            "jenkins_client": jenkins_status.get("status", "unknown")
        },
        "jenkins_url": jenkins_client.jenkins_url,
        "version": "1.0.0",
        "phase": "6_week_52-53"
    }
