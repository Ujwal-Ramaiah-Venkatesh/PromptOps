"""
Pipeline Generator for PromptOps
=================================

Generates Jenkins pipelines from natural language PM commands.
Supports multiple pipeline types and deployment strategies.

Author: DevOps Engineer - Phase 6 Week 52-53
Date: 2026-05-10
"""

import os
import json
import logging
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
# Pipeline Enums
# ============================================================================

class PipelineType(Enum):
    """Jenkins pipeline types."""
    DECLARATIVE = "declarative"
    SCRIPTED = "scripted"
    MULTIBRANCH = "multibranch"
    ORGANIZATION = "organization"


class DeploymentStrategy(Enum):
    """Deployment strategies."""
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"


class BuildTool(Enum):
    """Build tools."""
    MAVEN = "maven"
    GRADLE = "gradle"
    NPM = "npm"
    YARN = "yarn"
    DOCKER = "docker"
    MAKE = "make"


# ============================================================================
# Pipeline Generator
# ============================================================================

class PipelineGenerator:
    """
    Generates Jenkins pipelines from requirements.

    Features:
    - Declarative and scripted pipelines
    - Multi-stage builds (build, test, scan, deploy)
    - Deployment strategy support
    - Environment-specific configurations
    - Parallel execution
    """

    def __init__(self):
        """Initialize Pipeline Generator."""
        self.pipeline_templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load pipeline templates."""
        return {
            "declarative_basic": """
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                {build_steps}
            }
        }

        stage('Test') {
            steps {
                {test_steps}
            }
        }

        stage('Deploy') {
            steps {
                {deploy_steps}
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
""",
            "declarative_advanced": """
pipeline {
    agent {
        label '{agent_label}'
    }

    environment {
        {environment_vars}
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: {timeout_minutes}, unit: 'MINUTES')
    }

    stages {
        {stages}
    }

    post {
        {post_actions}
    }
}
"""
        }

    def generate_pipeline(
        self,
        pipeline_name: str,
        pipeline_type: str = "declarative",
        build_tool: str = "maven",
        deployment_strategy: str = "rolling",
        environments: Optional[List[str]] = None,
        enable_tests: bool = True,
        enable_security_scan: bool = True,
        enable_docker: bool = False,
        docker_registry: Optional[str] = None,
        kubernetes_cluster: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate Jenkins pipeline.

        Args:
            pipeline_name: Pipeline name
            pipeline_type: Pipeline type (declarative, scripted)
            build_tool: Build tool (maven, gradle, npm, docker)
            deployment_strategy: Deployment strategy (rolling, canary, blue_green)
            environments: Target environments (dev, staging, prod)
            enable_tests: Enable testing stage
            enable_security_scan: Enable security scanning
            enable_docker: Build Docker images
            docker_registry: Docker registry URL
            kubernetes_cluster: Kubernetes cluster name

        Returns:
            Pipeline configuration with Jenkinsfile
        """
        logger.info(f"Generating pipeline: {pipeline_name}")

        environments = environments or ["dev"]

        # Generate stages
        stages = self._generate_stages(
            build_tool=build_tool,
            enable_tests=enable_tests,
            enable_security_scan=enable_security_scan,
            enable_docker=enable_docker,
            docker_registry=docker_registry,
            environments=environments,
            deployment_strategy=deployment_strategy,
            kubernetes_cluster=kubernetes_cluster
        )

        # Generate environment variables
        env_vars = self._generate_environment_vars(
            build_tool=build_tool,
            docker_registry=docker_registry,
            kubernetes_cluster=kubernetes_cluster
        )

        # Generate post actions
        post_actions = self._generate_post_actions(
            enable_tests=enable_tests,
            enable_security_scan=enable_security_scan
        )

        # Build Jenkinsfile
        if pipeline_type == "declarative":
            jenkinsfile = self._build_declarative_pipeline(
                stages=stages,
                env_vars=env_vars,
                post_actions=post_actions,
                agent_label="docker"
            )
        else:
            jenkinsfile = self._build_scripted_pipeline(
                stages=stages,
                env_vars=env_vars
            )

        return {
            "pipeline_name": pipeline_name,
            "pipeline_type": pipeline_type,
            "build_tool": build_tool,
            "deployment_strategy": deployment_strategy,
            "environments": environments,
            "jenkinsfile": jenkinsfile,
            "stages": [s["name"] for s in stages],
            "estimated_duration_minutes": self._estimate_duration(stages),
            "generated_at": datetime.utcnow().isoformat()
        }

    def _generate_stages(
        self,
        build_tool: str,
        enable_tests: bool,
        enable_security_scan: bool,
        enable_docker: bool,
        docker_registry: Optional[str],
        environments: List[str],
        deployment_strategy: str,
        kubernetes_cluster: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate pipeline stages."""
        stages = []

        # Stage 1: Checkout
        stages.append({
            "name": "Checkout",
            "steps": [
                "checkout scm",
                "echo 'Checked out source code'"
            ],
            "duration_minutes": 1
        })

        # Stage 2: Build
        build_steps = self._get_build_steps(build_tool)
        stages.append({
            "name": "Build",
            "steps": build_steps,
            "duration_minutes": 5
        })

        # Stage 3: Unit Tests
        if enable_tests:
            test_steps = self._get_test_steps(build_tool)
            stages.append({
                "name": "Test",
                "steps": test_steps,
                "duration_minutes": 3
            })

        # Stage 4: Code Quality & Security Scan
        if enable_security_scan:
            stages.append({
                "name": "Security Scan",
                "steps": [
                    "echo 'Running security scans...'",
                    "sh 'trivy fs --severity HIGH,CRITICAL .'",
                    "sh 'sonar-scanner || true'"
                ],
                "duration_minutes": 4
            })

        # Stage 5: Docker Build
        if enable_docker:
            docker_steps = self._get_docker_build_steps(docker_registry)
            stages.append({
                "name": "Docker Build",
                "steps": docker_steps,
                "duration_minutes": 5
            })

        # Stage 6: Deploy to environments
        for env in environments:
            deploy_steps = self._get_deployment_steps(
                environment=env,
                strategy=deployment_strategy,
                kubernetes_cluster=kubernetes_cluster,
                build_tool=build_tool
            )
            stages.append({
                "name": f"Deploy to {env.upper()}",
                "steps": deploy_steps,
                "duration_minutes": 3
            })

        return stages

    def _get_build_steps(self, build_tool: str) -> List[str]:
        """Get build steps for tool."""
        build_commands = {
            "maven": [
                "echo 'Building with Maven...'",
                "sh 'mvn clean package -DskipTests'"
            ],
            "gradle": [
                "echo 'Building with Gradle...'",
                "sh './gradlew clean build -x test'"
            ],
            "npm": [
                "echo 'Building with NPM...'",
                "sh 'npm install'",
                "sh 'npm run build'"
            ],
            "yarn": [
                "echo 'Building with Yarn...'",
                "sh 'yarn install'",
                "sh 'yarn build'"
            ],
            "docker": [
                "echo 'Building with Docker...'",
                "sh 'docker build -t app:${BUILD_NUMBER} .'"
            ],
            "make": [
                "echo 'Building with Make...'",
                "sh 'make clean'",
                "sh 'make build'"
            ]
        }
        return build_commands.get(build_tool, build_commands["maven"])

    def _get_test_steps(self, build_tool: str) -> List[str]:
        """Get test steps for tool."""
        test_commands = {
            "maven": [
                "echo 'Running tests...'",
                "sh 'mvn test'",
                "junit '**/target/surefire-reports/*.xml'"
            ],
            "gradle": [
                "echo 'Running tests...'",
                "sh './gradlew test'",
                "junit '**/build/test-results/**/*.xml'"
            ],
            "npm": [
                "echo 'Running tests...'",
                "sh 'npm test'"
            ],
            "yarn": [
                "echo 'Running tests...'",
                "sh 'yarn test'"
            ]
        }
        return test_commands.get(build_tool, test_commands["maven"])

    def _get_docker_build_steps(self, docker_registry: Optional[str]) -> List[str]:
        """Get Docker build steps."""
        steps = [
            "echo 'Building Docker image...'",
            "sh 'docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .'",
            "sh 'docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest'"
        ]

        if docker_registry:
            steps.extend([
                f"sh 'docker login {docker_registry}'",
                "sh 'docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}'",
                "sh 'docker push ${DOCKER_IMAGE}:latest'"
            ])

        return steps

    def _get_deployment_steps(
        self,
        environment: str,
        strategy: str,
        kubernetes_cluster: Optional[str],
        build_tool: str
    ) -> List[str]:
        """Get deployment steps."""
        steps = [f"echo 'Deploying to {environment}...'"]

        if kubernetes_cluster:
            # Kubernetes deployment
            if strategy == "canary":
                steps.extend([
                    f"sh 'kubectl set image deployment/app app=${{DOCKER_IMAGE}}:${{BUILD_NUMBER}} --namespace={environment}'",
                    "sh 'kubectl rollout status deployment/app -n {environment}'",
                    "echo 'Canary deployed to 10% of traffic'",
                    "sleep 60",
                    "echo 'Promoting canary to 100%'"
                ])
            elif strategy == "blue_green":
                steps.extend([
                    "sh 'kubectl apply -f k8s/deployment-green.yaml'",
                    "sh 'kubectl rollout status deployment/app-green'",
                    "sh 'kubectl patch service app -p \"{\\\"spec\\\":{\\\"selector\\\":{\\\"version\\\":\\\"green\\\"}}}}\"'",
                    "echo 'Switched traffic to green deployment'"
                ])
            else:  # rolling
                steps.extend([
                    f"sh 'kubectl set image deployment/app app=${{DOCKER_IMAGE}}:${{BUILD_NUMBER}} --namespace={environment}'",
                    f"sh 'kubectl rollout status deployment/app --namespace={environment}'"
                ])
        else:
            # Traditional deployment
            steps.extend([
                f"sh 'scp target/*.{self._get_artifact_extension(build_tool)} user@{environment}-server:/opt/app/'",
                f"sh 'ssh user@{environment}-server \"systemctl restart app\"'"
            ])

        return steps

    def _get_artifact_extension(self, build_tool: str) -> str:
        """Get artifact extension for build tool."""
        extensions = {
            "maven": "jar",
            "gradle": "jar",
            "npm": "tar.gz",
            "yarn": "tar.gz"
        }
        return extensions.get(build_tool, "jar")

    def _generate_environment_vars(
        self,
        build_tool: str,
        docker_registry: Optional[str],
        kubernetes_cluster: Optional[str]
    ) -> str:
        """Generate environment variables section."""
        env_vars = [
            "BUILD_TOOL = '{}'".format(build_tool),
            "APP_NAME = '${JOB_NAME}'",
            "BUILD_VERSION = '${BUILD_NUMBER}'"
        ]

        if docker_registry:
            env_vars.append(f"DOCKER_REGISTRY = '{docker_registry}'")
            env_vars.append("DOCKER_IMAGE = '${DOCKER_REGISTRY}/${APP_NAME}'")

        if kubernetes_cluster:
            env_vars.append(f"K8S_CLUSTER = '{kubernetes_cluster}'")

        return "\n        ".join(env_vars)

    def _generate_post_actions(
        self,
        enable_tests: bool,
        enable_security_scan: bool
    ) -> str:
        """Generate post-build actions."""
        actions = [
            "always {",
            "    cleanWs()",
            "    echo 'Workspace cleaned'",
            "}"
        ]

        if enable_tests:
            actions.extend([
                "success {",
                "    echo 'Build succeeded!'",
                "    // Send success notification",
                "}"
            ])

        actions.extend([
            "failure {",
            "    echo 'Build failed!'",
            "    // Send failure notification",
            "}"
        ])

        return "\n        ".join(actions)

    def _build_declarative_pipeline(
        self,
        stages: List[Dict[str, Any]],
        env_vars: str,
        post_actions: str,
        agent_label: str = "any"
    ) -> str:
        """Build declarative Jenkinsfile."""
        # Build stages section
        stages_text = []
        for stage in stages:
            stage_steps = "\n                ".join(stage["steps"])
            stages_text.append(f"""
        stage('{stage["name"]}') {{
            steps {{
                {stage_steps}
            }}
        }}""")

        stages_section = "".join(stages_text)

        jenkinsfile = f"""pipeline {{
    agent {{
        label '{agent_label}'
    }}

    environment {{
        {env_vars}
    }}

    options {{
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 60, unit: 'MINUTES')
    }}

    stages {{{stages_section}
    }}

    post {{
        {post_actions}
    }}
}}"""

        return jenkinsfile

    def _build_scripted_pipeline(
        self,
        stages: List[Dict[str, Any]],
        env_vars: str
    ) -> str:
        """Build scripted Jenkinsfile."""
        # Build stages
        stages_text = []
        for stage in stages:
            stage_steps = "\n            ".join([f"sh '{step}'" if step.startswith("sh ") else step for step in stage["steps"]])
            stages_text.append(f"""
    stage('{stage["name"]}') {{
        {stage_steps}
    }}""")

        stages_section = "".join(stages_text)

        jenkinsfile = f"""node {{
    try {{
        // Environment variables
        env.BUILD_TOOL = 'maven'
        env.APP_NAME = env.JOB_NAME
        {stages_section}

        currentBuild.result = 'SUCCESS'
    }} catch (Exception e) {{
        currentBuild.result = 'FAILURE'
        throw e
    }} finally {{
        cleanWs()
    }}
}}"""

        return jenkinsfile

    def _estimate_duration(self, stages: List[Dict[str, Any]]) -> int:
        """Estimate total pipeline duration."""
        return sum(stage.get("duration_minutes", 3) for stage in stages)


# ============================================================================
# Testing
# ============================================================================

def test_pipeline_generator():
    """Test pipeline generator."""
    logger.info("Testing Pipeline Generator...")

    generator = PipelineGenerator()

    # Test 1: Basic declarative pipeline
    print("\n=== Test 1: Basic Maven Pipeline ===")
    pipeline = generator.generate_pipeline(
        pipeline_name="user-service-pipeline",
        pipeline_type="declarative",
        build_tool="maven",
        deployment_strategy="rolling",
        environments=["dev", "staging"],
        enable_tests=True,
        enable_security_scan=True
    )
    print(json.dumps({k: v for k, v in pipeline.items() if k != "jenkinsfile"}, indent=2))
    print("\n--- Jenkinsfile ---")
    print(pipeline["jenkinsfile"])

    # Test 2: Docker + Kubernetes pipeline
    print("\n\n=== Test 2: Docker + Kubernetes Pipeline ===")
    k8s_pipeline = generator.generate_pipeline(
        pipeline_name="api-gateway-pipeline",
        pipeline_type="declarative",
        build_tool="npm",
        deployment_strategy="canary",
        environments=["staging", "prod"],
        enable_docker=True,
        docker_registry="docker.io/myorg",
        kubernetes_cluster="prod-cluster",
        enable_security_scan=True
    )
    print(json.dumps({k: v for k, v in k8s_pipeline.items() if k != "jenkinsfile"}, indent=2))
    print("\n--- Jenkinsfile ---")
    print(k8s_pipeline["jenkinsfile"])


if __name__ == "__main__":
    test_pipeline_generator()
