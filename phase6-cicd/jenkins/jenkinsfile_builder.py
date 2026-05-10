"""
Jenkinsfile Builder for PromptOps
==================================

Low-level Jenkinsfile construction with fluent API.
Provides programmatic Jenkinsfile generation.

Author: DevOps Engineer - Phase 6 Week 52-53
Date: 2026-05-10
"""

import logging
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Jenkinsfile Builder
# ============================================================================

class JenkinsfileBuilder:
    """
    Fluent API for building Jenkinsfiles programmatically.

    Features:
    - Declarative and scripted syntax
    - Fluent/chainable API
    - Agent configuration
    - Environment variables
    - Stages and steps
    - Post-build actions
    """

    def __init__(self, pipeline_type: str = "declarative"):
        """
        Initialize Jenkinsfile Builder.

        Args:
            pipeline_type: Pipeline type (declarative or scripted)
        """
        self.pipeline_type = pipeline_type
        self.agent_config = "any"
        self.environment_vars = {}
        self.options_config = []
        self.stages_list = []
        self.post_actions = {
            "always": [],
            "success": [],
            "failure": [],
            "unstable": [],
            "changed": []
        }
        self.tools_config = []
        self.parameters_config = []

    def agent(self, agent: str = "any", label: Optional[str] = None,
              docker_image: Optional[str] = None) -> 'JenkinsfileBuilder':
        """
        Configure pipeline agent.

        Args:
            agent: Agent type (any, none, label, docker)
            label: Node label
            docker_image: Docker image

        Returns:
            Self for chaining
        """
        if label:
            self.agent_config = f"label '{label}'"
        elif docker_image:
            self.agent_config = f"docker '{docker_image}'"
        else:
            self.agent_config = agent

        return self

    def environment(self, **env_vars) -> 'JenkinsfileBuilder':
        """
        Add environment variables.

        Args:
            **env_vars: Environment variables as key=value

        Returns:
            Self for chaining
        """
        self.environment_vars.update(env_vars)
        return self

    def options(self, *options) -> 'JenkinsfileBuilder':
        """
        Add pipeline options.

        Args:
            *options: Option strings (e.g., "timestamps()", "buildDiscarder(...)")

        Returns:
            Self for chaining
        """
        self.options_config.extend(options)
        return self

    def tools(self, *tools) -> 'JenkinsfileBuilder':
        """
        Add tool configurations.

        Args:
            *tools: Tool strings (e.g., "maven 'Maven-3.8.1'")

        Returns:
            Self for chaining
        """
        self.tools_config.extend(tools)
        return self

    def parameters(self, *params) -> 'JenkinsfileBuilder':
        """
        Add build parameters.

        Args:
            *params: Parameter strings (e.g., "string(name: 'VERSION', ...)")

        Returns:
            Self for chaining
        """
        self.parameters_config.extend(params)
        return self

    def stage(self, name: str, steps: Optional[List[str]] = None,
              when_condition: Optional[str] = None,
              agent: Optional[str] = None) -> 'JenkinsfileBuilder':
        """
        Add a pipeline stage.

        Args:
            name: Stage name
            steps: List of steps
            when_condition: Conditional execution
            agent: Stage-specific agent

        Returns:
            Self for chaining
        """
        stage_config = {
            "name": name,
            "steps": steps or [],
            "when": when_condition,
            "agent": agent
        }
        self.stages_list.append(stage_config)
        return self

    def parallel_stages(self, *parallel_stages) -> 'JenkinsfileBuilder':
        """
        Add parallel stages.

        Args:
            *parallel_stages: Stage configurations

        Returns:
            Self for chaining
        """
        parallel_config = {
            "name": "Parallel Execution",
            "parallel": list(parallel_stages),
            "steps": []
        }
        self.stages_list.append(parallel_config)
        return self

    def post(self, action: str, *steps) -> 'JenkinsfileBuilder':
        """
        Add post-build actions.

        Args:
            action: Action type (always, success, failure, etc.)
            *steps: Steps to execute

        Returns:
            Self for chaining
        """
        if action in self.post_actions:
            self.post_actions[action].extend(steps)
        return self

    def build(self) -> str:
        """
        Build the Jenkinsfile.

        Returns:
            Complete Jenkinsfile as string
        """
        if self.pipeline_type == "declarative":
            return self._build_declarative()
        else:
            return self._build_scripted()

    def _build_declarative(self) -> str:
        """Build declarative Jenkinsfile."""
        lines = ["pipeline {"]

        # Agent
        if self.agent_config == "any" or self.agent_config == "none":
            lines.append(f"    agent {self.agent_config}")
        else:
            lines.append(f"    agent {{")
            lines.append(f"        {self.agent_config}")
            lines.append(f"    }}")

        # Environment
        if self.environment_vars:
            lines.append("")
            lines.append("    environment {")
            for key, value in self.environment_vars.items():
                lines.append(f"        {key} = '{value}'")
            lines.append("    }")

        # Options
        if self.options_config:
            lines.append("")
            lines.append("    options {")
            for option in self.options_config:
                lines.append(f"        {option}")
            lines.append("    }")

        # Tools
        if self.tools_config:
            lines.append("")
            lines.append("    tools {")
            for tool in self.tools_config:
                lines.append(f"        {tool}")
            lines.append("    }")

        # Parameters
        if self.parameters_config:
            lines.append("")
            lines.append("    parameters {")
            for param in self.parameters_config:
                lines.append(f"        {param}")
            lines.append("    }")

        # Stages
        lines.append("")
        lines.append("    stages {")

        for stage in self.stages_list:
            if "parallel" in stage:
                # Parallel stages
                lines.append(f"        stage('{stage['name']}') {{")
                lines.append("            parallel {")
                for parallel_stage in stage["parallel"]:
                    lines.append(f"                stage('{parallel_stage['name']}') {{")
                    lines.append("                    steps {")
                    for step in parallel_stage["steps"]:
                        lines.append(f"                        {step}")
                    lines.append("                    }")
                    lines.append("                }")
                lines.append("            }")
                lines.append("        }")
            else:
                # Regular stage
                lines.append(f"        stage('{stage['name']}') {{")

                # Stage-specific agent
                if stage.get("agent"):
                    lines.append(f"            agent {{ {stage['agent']} }}")

                # When condition
                if stage.get("when"):
                    lines.append(f"            when {{ {stage['when']} }}")

                # Steps
                lines.append("            steps {")
                for step in stage["steps"]:
                    lines.append(f"                {step}")
                lines.append("            }")
                lines.append("        }")

        lines.append("    }")

        # Post actions
        if any(self.post_actions.values()):
            lines.append("")
            lines.append("    post {")
            for action, steps in self.post_actions.items():
                if steps:
                    lines.append(f"        {action} {{")
                    for step in steps:
                        lines.append(f"            {step}")
                    lines.append("        }")
            lines.append("    }")

        lines.append("}")

        return "\n".join(lines)

    def _build_scripted(self) -> str:
        """Build scripted Jenkinsfile."""
        lines = ["node {"]
        lines.append("    try {")

        # Environment variables
        if self.environment_vars:
            lines.append("        // Environment variables")
            for key, value in self.environment_vars.items():
                lines.append(f"        env.{key} = '{value}'")
            lines.append("")

        # Stages
        for stage in self.stages_list:
            lines.append(f"        stage('{stage['name']}') {{")
            for step in stage["steps"]:
                lines.append(f"            {step}")
            lines.append("        }")
            lines.append("")

        # Success actions
        if self.post_actions.get("success"):
            lines.append("        // Success actions")
            for step in self.post_actions["success"]:
                lines.append(f"        {step}")

        lines.append("        currentBuild.result = 'SUCCESS'")

        # Catch failure
        lines.append("    } catch (Exception e) {")
        if self.post_actions.get("failure"):
            for step in self.post_actions["failure"]:
                lines.append(f"        {step}")
        lines.append("        currentBuild.result = 'FAILURE'")
        lines.append("        throw e")

        # Finally (always actions)
        lines.append("    } finally {")
        if self.post_actions.get("always"):
            for step in self.post_actions["always"]:
                lines.append(f"        {step}")
        lines.append("    }")

        lines.append("}")

        return "\n".join(lines)


# ============================================================================
# Helper Functions
# ============================================================================

def create_maven_pipeline() -> str:
    """Create a Maven build pipeline."""
    builder = JenkinsfileBuilder("declarative")

    jenkinsfile = builder \
        .agent(label="maven") \
        .environment(
            MAVEN_OPTS="-Xmx1024m",
            JAVA_HOME="/usr/lib/jvm/java-11"
        ) \
        .options(
            "buildDiscarder(logRotator(numToKeepStr: '10'))",
            "timestamps()",
            "timeout(time: 30, unit: 'MINUTES')"
        ) \
        .tools("maven 'Maven-3.8.1'", "jdk 'JDK-11'") \
        .stage("Checkout", ["checkout scm"]) \
        .stage("Build", [
            "echo 'Building...'",
            "sh 'mvn clean package -DskipTests'"
        ]) \
        .stage("Test", [
            "echo 'Running tests...'",
            "sh 'mvn test'",
            "junit '**/target/surefire-reports/*.xml'"
        ]) \
        .stage("Deploy", [
            "echo 'Deploying...'",
            "sh 'mvn deploy'"
        ]) \
        .post("always", "cleanWs()") \
        .post("success", "echo 'Build succeeded!'") \
        .post("failure", "echo 'Build failed!'") \
        .build()

    return jenkinsfile


def create_docker_pipeline() -> str:
    """Create a Docker build and push pipeline."""
    builder = JenkinsfileBuilder("declarative")

    jenkinsfile = builder \
        .agent(docker_image="docker:latest") \
        .environment(
            DOCKER_REGISTRY="docker.io",
            IMAGE_NAME="myapp",
            IMAGE_TAG="latest"
        ) \
        .options("timestamps()") \
        .stage("Build Image", [
            "sh 'docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .'",
            "sh 'docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER} .'"
        ]) \
        .stage("Push Image", [
            "sh 'docker login ${DOCKER_REGISTRY}'",
            "sh 'docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}'",
            "sh 'docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}'"
        ]) \
        .post("always", "sh 'docker logout'") \
        .build()

    return jenkinsfile


def create_parallel_pipeline() -> str:
    """Create a pipeline with parallel stages."""
    builder = JenkinsfileBuilder("declarative")

    jenkinsfile = builder \
        .agent("any") \
        .stage("Checkout", ["checkout scm"]) \
        .parallel_stages(
            {"name": "Unit Tests", "steps": ["sh 'npm run test:unit'"]},
            {"name": "Integration Tests", "steps": ["sh 'npm run test:integration'"]},
            {"name": "E2E Tests", "steps": ["sh 'npm run test:e2e'"]}
        ) \
        .stage("Deploy", ["echo 'Deploying...'"]) \
        .build()

    return jenkinsfile


# ============================================================================
# Testing
# ============================================================================

def test_jenkinsfile_builder():
    """Test Jenkinsfile builder."""
    logger.info("Testing Jenkinsfile Builder...")

    # Test 1: Maven pipeline
    print("\n=== Test 1: Maven Pipeline ===")
    maven_pipeline = create_maven_pipeline()
    print(maven_pipeline)

    # Test 2: Docker pipeline
    print("\n\n=== Test 2: Docker Pipeline ===")
    docker_pipeline = create_docker_pipeline()
    print(docker_pipeline)

    # Test 3: Parallel pipeline
    print("\n\n=== Test 3: Parallel Pipeline ===")
    parallel_pipeline = create_parallel_pipeline()
    print(parallel_pipeline)

    # Test 4: Scripted pipeline
    print("\n\n=== Test 4: Scripted Pipeline ===")
    scripted_builder = JenkinsfileBuilder("scripted")
    scripted_pipeline = scripted_builder \
        .environment(APP_NAME="myapp") \
        .stage("Build", ["sh 'make build'"]) \
        .stage("Test", ["sh 'make test'"]) \
        .post("always", "cleanWs()") \
        .build()
    print(scripted_pipeline)


if __name__ == "__main__":
    test_jenkinsfile_builder()
