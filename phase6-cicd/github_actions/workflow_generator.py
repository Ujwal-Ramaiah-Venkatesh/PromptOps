"""
GitHub Actions Workflow Generator for PromptOps
================================================

Generates GitHub Actions workflows from natural language commands.
Supports CI, CD, security scanning, and release workflows.

Author: DevOps Engineer - Phase 6 Week 54-55
Date: 2026-05-10
"""

import os
import json
import logging
import yaml
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Workflow Enums
# ============================================================================

class WorkflowType(Enum):
    """GitHub Actions workflow types."""
    CI = "ci"
    CD = "cd"
    SECURITY = "security"
    RELEASE = "release"
    PULL_REQUEST = "pull_request"
    SCHEDULED = "scheduled"


class Runner(Enum):
    """GitHub Actions runners."""
    UBUNTU_LATEST = "ubuntu-latest"
    UBUNTU_22_04 = "ubuntu-22.04"
    WINDOWS_LATEST = "windows-latest"
    MACOS_LATEST = "macos-latest"
    SELF_HOSTED = "self-hosted"


# ============================================================================
# Workflow Generator
# ============================================================================

class WorkflowGenerator:
    """
    Generates GitHub Actions workflows.

    Features:
    - CI workflows (build, test, lint)
    - CD workflows (deploy to environments)
    - Security workflows (SAST, dependency scanning)
    - Release workflows (versioning, changelog)
    - Matrix builds (multiple versions/OS)
    - Caching strategies
    - Secrets management
    """

    def __init__(self):
        """Initialize Workflow Generator."""
        self.workflow_templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict]:
        """Load workflow templates."""
        return {
            "ci_basic": {
                "name": "CI",
                "on": ["push", "pull_request"],
                "jobs": {
                    "build": {
                        "runs-on": "ubuntu-latest",
                        "steps": []
                    }
                }
            }
        }

    def generate_workflow(
        self,
        workflow_name: str,
        workflow_type: str = "ci",
        language: str = "java",
        build_tool: str = "maven",
        branches: Optional[List[str]] = None,
        enable_tests: bool = True,
        enable_security_scan: bool = True,
        enable_docker: bool = False,
        docker_registry: Optional[str] = None,
        deploy_environments: Optional[List[str]] = None,
        matrix_versions: Optional[List[str]] = None,
        enable_caching: bool = True
    ) -> Dict[str, Any]:
        """
        Generate GitHub Actions workflow.

        Args:
            workflow_name: Workflow name
            workflow_type: Workflow type (ci, cd, security, release)
            language: Programming language
            build_tool: Build tool
            branches: Target branches
            enable_tests: Enable testing
            enable_security_scan: Enable security scanning
            enable_docker: Build Docker images
            docker_registry: Docker registry
            deploy_environments: Deployment environments
            matrix_versions: Matrix build versions
            enable_caching: Enable dependency caching

        Returns:
            Workflow configuration with YAML content
        """
        logger.info(f"Generating GitHub Actions workflow: {workflow_name}")

        branches = branches or ["main", "develop"]
        deploy_environments = deploy_environments or []

        # Generate triggers
        triggers = self._generate_triggers(workflow_type, branches)

        # Generate jobs
        jobs = {}

        if workflow_type in ["ci", "pull_request"]:
            jobs.update(self._generate_ci_jobs(
                language=language,
                build_tool=build_tool,
                enable_tests=enable_tests,
                enable_security_scan=enable_security_scan,
                matrix_versions=matrix_versions,
                enable_caching=enable_caching
            ))

        if workflow_type == "cd" or (workflow_type == "ci" and deploy_environments):
            jobs.update(self._generate_cd_jobs(
                environments=deploy_environments,
                enable_docker=enable_docker,
                docker_registry=docker_registry
            ))

        if workflow_type == "security":
            jobs.update(self._generate_security_jobs())

        if workflow_type == "release":
            jobs.update(self._generate_release_jobs())

        # Build workflow
        workflow = {
            "name": workflow_name,
            **triggers,
            "jobs": jobs
        }

        # Convert to YAML
        workflow_yaml = yaml.dump(workflow, default_flow_style=False, sort_keys=False)

        return {
            "workflow_name": workflow_name,
            "workflow_type": workflow_type,
            "language": language,
            "build_tool": build_tool,
            "branches": branches,
            "workflow_yaml": workflow_yaml,
            "workflow_dict": workflow,
            "file_path": f".github/workflows/{workflow_name.lower().replace(' ', '-')}.yml",
            "generated_at": datetime.utcnow().isoformat()
        }

    def _generate_triggers(self, workflow_type: str, branches: List[str]) -> Dict[str, Any]:
        """Generate workflow triggers."""
        if workflow_type == "ci":
            return {
                "on": {
                    "push": {"branches": branches},
                    "pull_request": {"branches": branches}
                }
            }
        elif workflow_type == "cd":
            return {
                "on": {
                    "push": {"branches": ["main"]},
                    "workflow_dispatch": {}
                }
            }
        elif workflow_type == "security":
            return {
                "on": {
                    "schedule": [{"cron": "0 0 * * 0"}],  # Weekly
                    "workflow_dispatch": {}
                }
            }
        elif workflow_type == "release":
            return {
                "on": {
                    "push": {"tags": ["v*"]},
                    "workflow_dispatch": {}
                }
            }
        elif workflow_type == "pull_request":
            return {
                "on": {"pull_request": {"branches": branches}}
            }
        else:
            return {"on": ["push"]}

    def _generate_ci_jobs(
        self,
        language: str,
        build_tool: str,
        enable_tests: bool,
        enable_security_scan: bool,
        matrix_versions: Optional[List[str]],
        enable_caching: bool
    ) -> Dict[str, Any]:
        """Generate CI jobs."""
        jobs = {}

        # Build and test job
        build_steps = [
            {"name": "Checkout code", "uses": "actions/checkout@v4"}
        ]

        # Setup language environment
        if language == "java":
            build_steps.append({
                "name": "Set up JDK",
                "uses": "actions/setup-java@v4",
                "with": {
                    "distribution": "temurin",
                    "java-version": "${{ matrix.java-version }}" if matrix_versions else "17"
                }
            })

            if enable_caching and build_tool == "maven":
                build_steps.append({
                    "name": "Cache Maven packages",
                    "uses": "actions/cache@v4",
                    "with": {
                        "path": "~/.m2",
                        "key": "${{ runner.os }}-m2-${{ hashFiles('**/pom.xml') }}",
                        "restore-keys": "${{ runner.os }}-m2"
                    }
                })

        elif language == "node":
            build_steps.append({
                "name": "Set up Node.js",
                "uses": "actions/setup-node@v4",
                "with": {
                    "node-version": "${{ matrix.node-version }}" if matrix_versions else "20"
                }
            })

            if enable_caching:
                build_steps.append({
                    "name": "Cache npm packages",
                    "uses": "actions/cache@v4",
                    "with": {
                        "path": "~/.npm",
                        "key": "${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}",
                        "restore-keys": "${{ runner.os }}-node-"
                    }
                })

        elif language == "python":
            build_steps.append({
                "name": "Set up Python",
                "uses": "actions/setup-python@v5",
                "with": {
                    "python-version": "${{ matrix.python-version }}" if matrix_versions else "3.11"
                }
            })

            if enable_caching:
                build_steps.append({
                    "name": "Cache pip packages",
                    "uses": "actions/cache@v4",
                    "with": {
                        "path": "~/.cache/pip",
                        "key": "${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}",
                        "restore-keys": "${{ runner.os }}-pip-"
                    }
                })

        # Build step
        build_commands = self._get_build_commands(build_tool, language)
        build_steps.append({
            "name": "Build",
            "run": build_commands
        })

        # Test step
        if enable_tests:
            test_commands = self._get_test_commands(build_tool, language)
            build_steps.append({
                "name": "Run tests",
                "run": test_commands
            })

        # Upload coverage
        if enable_tests:
            build_steps.append({
                "name": "Upload coverage",
                "uses": "codecov/codecov-action@v4",
                "with": {"files": "./coverage.xml"},
                "continue-on-error": True
            })

        # Build job configuration
        build_job = {
            "runs-on": "ubuntu-latest",
            "steps": build_steps
        }

        # Add matrix strategy if versions specified
        if matrix_versions:
            if language == "java":
                build_job["strategy"] = {
                    "matrix": {"java-version": matrix_versions}
                }
            elif language == "node":
                build_job["strategy"] = {
                    "matrix": {"node-version": matrix_versions}
                }
            elif language == "python":
                build_job["strategy"] = {
                    "matrix": {"python-version": matrix_versions}
                }

        jobs["build"] = build_job

        # Security scan job
        if enable_security_scan:
            jobs["security-scan"] = {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"name": "Checkout code", "uses": "actions/checkout@v4"},
                    {
                        "name": "Run Trivy vulnerability scanner",
                        "uses": "aquasecurity/trivy-action@master",
                        "with": {
                            "scan-type": "fs",
                            "scan-ref": ".",
                            "format": "sarif",
                            "output": "trivy-results.sarif"
                        }
                    },
                    {
                        "name": "Upload Trivy results to GitHub Security",
                        "uses": "github/codeql-action/upload-sarif@v3",
                        "with": {"sarif_file": "trivy-results.sarif"}
                    }
                ]
            }

        return jobs

    def _generate_cd_jobs(
        self,
        environments: List[str],
        enable_docker: bool,
        docker_registry: Optional[str]
    ) -> Dict[str, Any]:
        """Generate CD jobs."""
        jobs = {}

        if enable_docker:
            docker_steps = [
                {"name": "Checkout code", "uses": "actions/checkout@v4"},
                {
                    "name": "Set up Docker Buildx",
                    "uses": "docker/setup-buildx-action@v3"
                },
                {
                    "name": "Log in to Docker Hub",
                    "uses": "docker/login-action@v3",
                    "with": {
                        "registry": docker_registry or "docker.io",
                        "username": "${{ secrets.DOCKER_USERNAME }}",
                        "password": "${{ secrets.DOCKER_PASSWORD }}"
                    }
                },
                {
                    "name": "Build and push Docker image",
                    "uses": "docker/build-push-action@v5",
                    "with": {
                        "context": ".",
                        "push": True,
                        "tags": f"{docker_registry or 'docker.io'}/myapp:${{{{ github.sha }}}}," +
                                f"{docker_registry or 'docker.io'}/myapp:latest",
                        "cache-from": "type=gha",
                        "cache-to": "type=gha,mode=max"
                    }
                }
            ]

            jobs["docker-build"] = {
                "runs-on": "ubuntu-latest",
                "needs": ["build"],
                "steps": docker_steps
            }

        # Deployment jobs
        for env in environments:
            deploy_steps = [
                {"name": "Checkout code", "uses": "actions/checkout@v4"},
                {
                    "name": f"Deploy to {env}",
                    "run": f"echo 'Deploying to {env} environment...'\n" +
                           f"kubectl set image deployment/app app=myapp:${{{{ github.sha }}}} -n {env}"
                }
            ]

            jobs[f"deploy-{env}"] = {
                "runs-on": "ubuntu-latest",
                "needs": ["docker-build"] if enable_docker else ["build"],
                "environment": env,
                "steps": deploy_steps
            }

        return jobs

    def _generate_security_jobs(self) -> Dict[str, Any]:
        """Generate security scanning jobs."""
        return {
            "dependency-scan": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"name": "Checkout code", "uses": "actions/checkout@v4"},
                    {
                        "name": "Run Snyk security scan",
                        "uses": "snyk/actions/node@master",
                        "env": {"SNYK_TOKEN": "${{ secrets.SNYK_TOKEN }}"}
                    }
                ]
            },
            "code-scan": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"name": "Checkout code", "uses": "actions/checkout@v4"},
                    {
                        "name": "Initialize CodeQL",
                        "uses": "github/codeql-action/init@v3",
                        "with": {"languages": "java"}
                    },
                    {
                        "name": "Autobuild",
                        "uses": "github/codeql-action/autobuild@v3"
                    },
                    {
                        "name": "Perform CodeQL Analysis",
                        "uses": "github/codeql-action/analyze@v3"
                    }
                ]
            }
        }

    def _generate_release_jobs(self) -> Dict[str, Any]:
        """Generate release workflow jobs."""
        return {
            "create-release": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"name": "Checkout code", "uses": "actions/checkout@v4"},
                    {
                        "name": "Create GitHub Release",
                        "uses": "actions/create-release@v1",
                        "env": {"GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}"},
                        "with": {
                            "tag_name": "${{ github.ref }}",
                            "release_name": "Release ${{ github.ref }}",
                            "draft": False,
                            "prerelease": False
                        }
                    }
                ]
            }
        }

    def _get_build_commands(self, build_tool: str, language: str) -> str:
        """Get build commands for tool."""
        commands = {
            "maven": "mvn clean package -DskipTests",
            "gradle": "./gradlew build -x test",
            "npm": "npm install && npm run build",
            "yarn": "yarn install && yarn build",
            "pip": "pip install -r requirements.txt && python setup.py build",
            "cargo": "cargo build --release"
        }
        return commands.get(build_tool, commands.get("maven", "echo 'No build command'"))

    def _get_test_commands(self, build_tool: str, language: str) -> str:
        """Get test commands for tool."""
        commands = {
            "maven": "mvn test",
            "gradle": "./gradlew test",
            "npm": "npm test",
            "yarn": "yarn test",
            "pip": "pytest",
            "cargo": "cargo test"
        }
        return commands.get(build_tool, commands.get("maven", "echo 'No test command'"))


# ============================================================================
# Testing
# ============================================================================

def test_workflow_generator():
    """Test workflow generator."""
    logger.info("Testing Workflow Generator...")

    generator = WorkflowGenerator()

    # Test 1: Basic CI workflow
    print("\n=== Test 1: Java Maven CI Workflow ===")
    ci_workflow = generator.generate_workflow(
        workflow_name="Java CI",
        workflow_type="ci",
        language="java",
        build_tool="maven",
        branches=["main", "develop"],
        enable_tests=True,
        enable_security_scan=True,
        matrix_versions=["17", "21"]
    )
    print(f"File path: {ci_workflow['file_path']}")
    print(f"Language: {ci_workflow['language']}")
    print(f"Build tool: {ci_workflow['build_tool']}")
    print("\n--- Workflow YAML ---")
    print(ci_workflow["workflow_yaml"])

    # Test 2: Docker CD workflow
    print("\n\n=== Test 2: Docker CD Workflow ===")
    cd_workflow = generator.generate_workflow(
        workflow_name="Deploy to Production",
        workflow_type="cd",
        language="node",
        build_tool="npm",
        enable_docker=True,
        docker_registry="ghcr.io/myorg",
        deploy_environments=["staging", "production"]
    )
    print(f"File path: {cd_workflow['file_path']}")
    print("\n--- Workflow YAML ---")
    print(cd_workflow["workflow_yaml"][:1000])  # First 1000 chars


if __name__ == "__main__":
    test_workflow_generator()
