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
from github_actions.workflow_generator import WorkflowGenerator
from github_actions.actions_integrator import ActionsIntegrator
from github_actions.github_api_client import GitHubAPIClient

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
workflow_generator = WorkflowGenerator()
actions_integrator = ActionsIntegrator()
github_client = GitHubAPIClient(
    github_token=os.getenv("GITHUB_TOKEN"),
    github_repo=os.getenv("GITHUB_REPOSITORY")
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
# GitHub Actions Endpoints
# ============================================================================

class WorkflowGenerationRequest(BaseModel):
    """Request to generate GitHub Actions workflow."""
    workflow_name: str
    workflow_type: str = "ci"
    language: str = "java"
    build_tool: str = "maven"
    branches: List[str] = ["main", "develop"]
    enable_tests: bool = True
    enable_security_scan: bool = True
    enable_docker: bool = False
    docker_registry: Optional[str] = None
    deploy_environments: List[str] = []
    matrix_versions: Optional[List[str]] = None


class HybridPipelineRequest(BaseModel):
    """Request to create hybrid pipeline."""
    pipeline_name: str
    strategy: str = "jenkins_primary"
    jenkins_config: Optional[Dict[str, Any]] = None
    actions_config: Optional[Dict[str, Any]] = None
    shared_artifacts: Optional[List[str]] = None


@router.post("/actions/workflows/generate")
async def generate_github_workflow(request: WorkflowGenerationRequest):
    """
    Generate GitHub Actions workflow.

    **Workflow Types:** ci, cd, security, release, pull_request
    **Languages:** java, node, python, go, rust
    **Build Tools:** maven, gradle, npm, yarn, pip, cargo
    """
    try:
        workflow = workflow_generator.generate_workflow(
            workflow_name=request.workflow_name,
            workflow_type=request.workflow_type,
            language=request.language,
            build_tool=request.build_tool,
            branches=request.branches,
            enable_tests=request.enable_tests,
            enable_security_scan=request.enable_security_scan,
            enable_docker=request.enable_docker,
            docker_registry=request.docker_registry,
            deploy_environments=request.deploy_environments,
            matrix_versions=request.matrix_versions
        )
        return workflow

    except Exception as e:
        logger.error(f"Failed to generate workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actions/workflows/create")
async def create_github_workflow_file(
    workflow_name: str,
    workflow_yaml: str,
    commit_message: str = "Add workflow",
    branch: str = "main"
):
    """Create GitHub Actions workflow file in repository."""
    try:
        result = github_client.create_workflow_file(
            workflow_name=workflow_name,
            workflow_yaml=workflow_yaml,
            commit_message=commit_message,
            branch=branch
        )
        return result

    except Exception as e:
        logger.error(f"Failed to create workflow file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actions/workflows/{workflow_id}/dispatch")
async def dispatch_github_workflow(
    workflow_id: str,
    ref: str = "main",
    inputs: Optional[Dict[str, Any]] = None
):
    """Trigger GitHub Actions workflow dispatch."""
    try:
        result = github_client.dispatch_workflow(
            workflow_id=workflow_id,
            ref=ref,
            inputs=inputs
        )
        return result

    except Exception as e:
        logger.error(f"Failed to dispatch workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions/runs")
async def list_github_workflow_runs(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    branch: Optional[str] = None,
    per_page: int = 30
):
    """List GitHub Actions workflow runs."""
    try:
        runs = github_client.list_workflow_runs(
            workflow_id=workflow_id,
            status=status,
            branch=branch,
            per_page=per_page
        )
        return runs

    except Exception as e:
        logger.error(f"Failed to list workflow runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions/runs/{run_id}")
async def get_github_workflow_run(run_id: int):
    """Get GitHub Actions workflow run details."""
    try:
        run = github_client.get_workflow_run(run_id)
        return run

    except Exception as e:
        logger.error(f"Failed to get workflow run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actions/runs/{run_id}/cancel")
async def cancel_github_workflow_run(run_id: int):
    """Cancel GitHub Actions workflow run."""
    try:
        result = github_client.cancel_workflow_run(run_id)
        return result

    except Exception as e:
        logger.error(f"Failed to cancel workflow run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hybrid/pipelines")
async def create_hybrid_pipeline(request: HybridPipelineRequest):
    """
    Create hybrid Jenkins + GitHub Actions pipeline.

    **Strategies:**
    - jenkins_primary: Jenkins for main builds, Actions for PR checks
    - actions_primary: Actions for CI, Jenkins for deployment
    - parallel: Both platforms run independently
    - conditional: Branch-based routing
    """
    try:
        hybrid = actions_integrator.create_hybrid_pipeline(
            pipeline_name=request.pipeline_name,
            strategy=request.strategy,
            jenkins_config=request.jenkins_config,
            actions_config=request.actions_config,
            shared_artifacts=request.shared_artifacts
        )
        return hybrid

    except Exception as e:
        logger.error(f"Failed to create hybrid pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hybrid/recommendations")
async def get_hybrid_recommendations(
    project_characteristics: Dict[str, Any]
):
    """
    Get hybrid orchestration strategy recommendations.

    **Project Characteristics:**
    - has_legacy_jenkins: bool
    - team_size: int
    - uses_kubernetes: bool
    - pr_frequency: str (low, medium, high)
    - build_complexity: str (low, medium, high)
    """
    try:
        recommendations = actions_integrator.get_orchestration_recommendations(
            project_characteristics=project_characteristics
        )
        return recommendations

    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
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
            "jenkins_client": jenkins_status.get("status", "unknown"),
            "workflow_generator": "ok",
            "actions_integrator": "ok",
            "github_client": "ok"
        },
        "jenkins_url": jenkins_client.jenkins_url,
        "github_repo": github_client.github_repo,
        "version": "2.0.0",
        "phase": "6_week_54-55"
    }
