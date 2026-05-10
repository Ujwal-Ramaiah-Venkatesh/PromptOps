"""
GitHub Actions Integrator for PromptOps
========================================

Hybrid orchestration of Jenkins and GitHub Actions pipelines.
Coordinates multi-platform CI/CD workflows.

Author: DevOps Engineer - Phase 6 Week 54-55
Date: 2026-05-10
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Orchestration Enums
# ============================================================================

class OrchestrationStrategy(Enum):
    """Hybrid orchestration strategies."""
    JENKINS_PRIMARY = "jenkins_primary"      # Jenkins triggers GitHub Actions
    ACTIONS_PRIMARY = "actions_primary"      # GitHub Actions triggers Jenkins
    PARALLEL = "parallel"                    # Both run independently
    CONDITIONAL = "conditional"              # Conditional based on branch/event


# ============================================================================
# Actions Integrator
# ============================================================================

class ActionsIntegrator:
    """
    Hybrid orchestration of Jenkins and GitHub Actions.

    Features:
    - Multi-platform pipeline orchestration
    - Conditional execution based on events
    - Cross-platform artifact sharing
    - Status synchronization
    - Unified reporting
    """

    def __init__(self):
        """Initialize Actions Integrator."""
        self.orchestration_patterns = self._load_patterns()

    def _load_patterns(self) -> Dict[str, Dict]:
        """Load orchestration patterns."""
        return {
            "jenkins_primary": {
                "description": "Jenkins runs main build, GitHub Actions for PR checks",
                "jenkins_triggers": ["push:main", "push:release/*"],
                "actions_triggers": ["pull_request"],
                "use_case": "Heavy builds on Jenkins, lightweight PR checks on Actions"
            },
            "actions_primary": {
                "description": "GitHub Actions runs CI, Jenkins for deployment",
                "actions_triggers": ["push", "pull_request"],
                "jenkins_triggers": ["workflow_dispatch"],
                "use_case": "Modern CI on Actions, legacy deployment on Jenkins"
            },
            "parallel": {
                "description": "Both platforms run independently",
                "jenkins_triggers": ["push"],
                "actions_triggers": ["push"],
                "use_case": "Redundant pipelines or different test suites"
            },
            "conditional": {
                "description": "Branch-based routing",
                "main_branch": "jenkins",
                "feature_branches": "actions",
                "use_case": "Production builds on Jenkins, development on Actions"
            }
        }

    def create_hybrid_pipeline(
        self,
        pipeline_name: str,
        strategy: str = "jenkins_primary",
        jenkins_config: Optional[Dict[str, Any]] = None,
        actions_config: Optional[Dict[str, Any]] = None,
        shared_artifacts: Optional[List[str]] = None,
        enable_status_sync: bool = True
    ) -> Dict[str, Any]:
        """
        Create hybrid Jenkins + GitHub Actions pipeline.

        Args:
            pipeline_name: Pipeline name
            strategy: Orchestration strategy
            jenkins_config: Jenkins pipeline configuration
            actions_config: GitHub Actions workflow configuration
            shared_artifacts: Artifacts to share between platforms
            enable_status_sync: Sync status between platforms

        Returns:
            Hybrid pipeline configuration
        """
        logger.info(f"Creating hybrid pipeline: {pipeline_name} ({strategy})")

        pattern = self.orchestration_patterns.get(strategy, {})

        # Build orchestration configuration
        hybrid_config = {
            "pipeline_name": pipeline_name,
            "strategy": strategy,
            "pattern": pattern,
            "jenkins": jenkins_config or {},
            "actions": actions_config or {},
            "shared_artifacts": shared_artifacts or [],
            "status_sync": enable_status_sync,
            "triggers": self._generate_triggers(strategy, pattern),
            "artifact_flow": self._generate_artifact_flow(shared_artifacts),
            "status_checks": self._generate_status_checks(enable_status_sync)
        }

        return hybrid_config

    def _generate_triggers(
        self,
        strategy: str,
        pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate trigger configuration."""
        triggers = {
            "jenkins": pattern.get("jenkins_triggers", []),
            "actions": pattern.get("actions_triggers", [])
        }

        if strategy == "jenkins_primary":
            triggers["flow"] = "Jenkins → GitHub Actions (for PR checks)"
        elif strategy == "actions_primary":
            triggers["flow"] = "GitHub Actions → Jenkins (for deployment)"
        elif strategy == "parallel":
            triggers["flow"] = "Jenkins || GitHub Actions (independent)"
        elif strategy == "conditional":
            triggers["flow"] = "Branch-based: main→Jenkins, feature→Actions"

        return triggers

    def _generate_artifact_flow(
        self,
        shared_artifacts: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Generate artifact sharing configuration."""
        if not shared_artifacts:
            return {"enabled": False}

        return {
            "enabled": True,
            "artifacts": shared_artifacts,
            "storage": "github_artifacts",  # or "s3", "artifactory"
            "jenkins_upload": {
                "plugin": "artifact-manager-s3",
                "command": "archiveArtifacts artifacts: 'target/*.jar'"
            },
            "actions_download": {
                "action": "actions/download-artifact@v4",
                "with": {"name": "build-artifacts"}
            }
        }

    def _generate_status_checks(self, enable_status_sync: bool) -> Dict[str, Any]:
        """Generate status check configuration."""
        if not enable_status_sync:
            return {"enabled": False}

        return {
            "enabled": True,
            "jenkins_to_github": {
                "method": "github_commit_status_api",
                "states": ["pending", "success", "failure"]
            },
            "actions_to_jenkins": {
                "method": "jenkins_webhook",
                "endpoint": "/github-webhook/"
            },
            "unified_dashboard": {
                "enabled": True,
                "url": "/cicd/dashboard"
            }
        }

    def generate_jenkins_actions_trigger(
        self,
        jenkins_job_name: str,
        actions_workflow: str,
        trigger_on_success: bool = True
    ) -> str:
        """
        Generate Jenkinsfile snippet to trigger GitHub Actions.

        Args:
            jenkins_job_name: Jenkins job name
            actions_workflow: GitHub Actions workflow file
            trigger_on_success: Trigger only on success

        Returns:
            Jenkinsfile snippet
        """
        snippet = f"""
// Trigger GitHub Actions workflow from Jenkins
stage('Trigger GitHub Actions') {{
    {'when { expression { currentBuild.result == "SUCCESS" } }' if trigger_on_success else ''}
    steps {{
        script {{
            sh '''
            curl -X POST \\
              -H "Accept: application/vnd.github+json" \\
              -H "Authorization: Bearer ${{GITHUB_TOKEN}}" \\
              https://api.github.com/repos/${{GITHUB_REPO}}/actions/workflows/{actions_workflow}/dispatches \\
              -d '{{"ref":"main"}}'
            '''
        }}
    }}
}}
"""
        return snippet

    def generate_actions_jenkins_trigger(
        self,
        jenkins_url: str,
        jenkins_job_name: str
    ) -> Dict[str, Any]:
        """
        Generate GitHub Actions step to trigger Jenkins.

        Args:
            jenkins_url: Jenkins server URL
            jenkins_job_name: Jenkins job name

        Returns:
            GitHub Actions step configuration
        """
        return {
            "name": "Trigger Jenkins Job",
            "run": f"""
curl -X POST \\
  -u ${{{{ secrets.JENKINS_USER }}}}:${{{{ secrets.JENKINS_TOKEN }}}} \\
  {jenkins_url}/job/{jenkins_job_name}/build
            """.strip()
        }

    def get_orchestration_recommendations(
        self,
        project_characteristics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get orchestration strategy recommendations based on project characteristics.

        Args:
            project_characteristics: Project info (language, team_size, complexity, etc.)

        Returns:
            Recommended strategies with reasons
        """
        recommendations = []

        # Analyze characteristics
        has_legacy_jenkins = project_characteristics.get("has_legacy_jenkins", False)
        team_size = project_characteristics.get("team_size", 10)
        uses_kubernetes = project_characteristics.get("uses_kubernetes", False)
        pr_frequency = project_characteristics.get("pr_frequency", "medium")

        # Jenkins Primary recommendation
        if has_legacy_jenkins and team_size > 20:
            recommendations.append({
                "strategy": "jenkins_primary",
                "score": 90,
                "reasons": [
                    "Existing Jenkins infrastructure investment",
                    "Large team benefits from centralized Jenkins",
                    "Use Actions for lightweight PR checks"
                ]
            })

        # Actions Primary recommendation
        if not has_legacy_jenkins and uses_kubernetes:
            recommendations.append({
                "strategy": "actions_primary",
                "score": 95,
                "reasons": [
                    "Modern GitHub-native approach",
                    "Better Kubernetes integration in Actions",
                    "No Jenkins maintenance overhead"
                ]
            })

        # Parallel recommendation
        if pr_frequency == "high":
            recommendations.append({
                "strategy": "parallel",
                "score": 75,
                "reasons": [
                    "Redundant pipelines reduce bottlenecks",
                    "High PR volume benefits from parallel execution",
                    "Diverse test coverage across platforms"
                ]
            })

        # Conditional recommendation
        recommendations.append({
            "strategy": "conditional",
            "score": 80,
            "reasons": [
                "Branch-based routing optimizes resource usage",
                "Production builds on stable Jenkins",
                "Development iteration speed on Actions"
            ]
        })

        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        return {
            "project_characteristics": project_characteristics,
            "recommendations": recommendations,
            "top_recommendation": recommendations[0] if recommendations else None
        }


# ============================================================================
# Testing
# ============================================================================

def test_actions_integrator():
    """Test Actions Integrator."""
    logger.info("Testing Actions Integrator...")

    integrator = ActionsIntegrator()

    # Test 1: Create hybrid pipeline
    print("\n=== Test 1: Hybrid Pipeline (Jenkins Primary) ===")
    hybrid = integrator.create_hybrid_pipeline(
        pipeline_name="user-service-hybrid",
        strategy="jenkins_primary",
        jenkins_config={"job_name": "user-service-build"},
        actions_config={"workflow": "pr-checks.yml"},
        shared_artifacts=["target/*.jar", "coverage.xml"],
        enable_status_sync=True
    )
    print(json.dumps(hybrid, indent=2))

    # Test 2: Generate Jenkins→Actions trigger
    print("\n\n=== Test 2: Jenkins to Actions Trigger ===")
    jenkins_snippet = integrator.generate_jenkins_actions_trigger(
        jenkins_job_name="api-gateway-build",
        actions_workflow="deploy.yml",
        trigger_on_success=True
    )
    print(jenkins_snippet)

    # Test 3: Generate Actions→Jenkins trigger
    print("\n=== Test 3: Actions to Jenkins Trigger ===")
    actions_step = integrator.generate_actions_jenkins_trigger(
        jenkins_url="https://jenkins.example.com",
        jenkins_job_name="deployment-pipeline"
    )
    print(json.dumps(actions_step, indent=2))

    # Test 4: Get orchestration recommendations
    print("\n=== Test 4: Orchestration Recommendations ===")
    recommendations = integrator.get_orchestration_recommendations({
        "has_legacy_jenkins": True,
        "team_size": 25,
        "uses_kubernetes": True,
        "pr_frequency": "high",
        "build_complexity": "high"
    })
    print(json.dumps(recommendations, indent=2))


if __name__ == "__main__":
    test_actions_integrator()
