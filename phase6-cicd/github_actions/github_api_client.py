"""
GitHub API Client for PromptOps
================================

REST API client for GitHub Actions workflow management.
Handles workflow dispatch, run monitoring, and artifact management.

Author: DevOps Engineer - Phase 6 Week 54-55
Date: 2026-05-10
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# GitHub API Client
# ============================================================================

class GitHubAPIClient:
    """
    REST API client for GitHub Actions.

    Features:
    - Workflow dispatch (trigger workflows)
    - Workflow run monitoring
    - Artifact download
    - Commit status management
    - Repository file operations
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None
    ):
        """
        Initialize GitHub API Client.

        Args:
            github_token: GitHub personal access token
            github_repo: Repository in format "owner/repo"
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_repo = github_repo or os.getenv("GITHUB_REPOSITORY")
        self.api_base_url = "https://api.github.com"
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with authentication."""
        session = requests.Session()

        if self.github_token:
            session.headers.update({
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            })

        return session

    def create_workflow_file(
        self,
        workflow_name: str,
        workflow_yaml: str,
        commit_message: str = "Add workflow",
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create workflow file in repository.

        Args:
            workflow_name: Workflow file name (e.g., "ci.yml")
            workflow_yaml: Workflow YAML content
            commit_message: Git commit message
            branch: Target branch

        Returns:
            File creation result
        """
        logger.info(f"Creating workflow file: {workflow_name}")

        file_path = f".github/workflows/{workflow_name}"

        try:
            # Check if file exists
            url = f"{self.api_base_url}/repos/{self.github_repo}/contents/{file_path}"
            response = self.session.get(url, params={"ref": branch}, timeout=10)

            # Encode content
            import base64
            encoded_content = base64.b64encode(workflow_yaml.encode()).decode()

            data = {
                "message": commit_message,
                "content": encoded_content,
                "branch": branch
            }

            # If file exists, need SHA for update
            if response.status_code == 200:
                existing = response.json()
                data["sha"] = existing["sha"]
                logger.info(f"Updating existing workflow file")

            # Create or update file
            response = self.session.put(url, json=data, timeout=10)

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Workflow file created/updated successfully")
                return {
                    "status": "created",
                    "file_path": file_path,
                    "commit_sha": result["commit"]["sha"],
                    "url": result["content"]["html_url"],
                    "created_at": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Failed to create workflow file: {response.status_code}")
                return {
                    "status": "failed",
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Exception creating workflow file: {e}")
            return {
                "status": "error",
                "error": str(e),
                "note": "GitHub API may not be available or token invalid (mock mode)"
            }

    def dispatch_workflow(
        self,
        workflow_id: str,
        ref: str = "main",
        inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger workflow dispatch.

        Args:
            workflow_id: Workflow file name or ID
            ref: Git ref (branch, tag, SHA)
            inputs: Workflow inputs

        Returns:
            Dispatch result
        """
        logger.info(f"Dispatching workflow: {workflow_id} on {ref}")

        url = f"{self.api_base_url}/repos/{self.github_repo}/actions/workflows/{workflow_id}/dispatches"

        data = {
            "ref": ref,
            "inputs": inputs or {}
        }

        try:
            response = self.session.post(url, json=data, timeout=10)

            if response.status_code == 204:
                logger.info(f"Workflow dispatched successfully")
                return {
                    "status": "dispatched",
                    "workflow_id": workflow_id,
                    "ref": ref,
                    "dispatched_at": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Failed to dispatch workflow: {response.status_code}")
                return {
                    "status": "failed",
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Exception dispatching workflow: {e}")
            return {
                "status": "error",
                "error": str(e),
                "note": "GitHub API may not be available (mock mode)"
            }

    def list_workflow_runs(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        per_page: int = 30
    ) -> Dict[str, Any]:
        """
        List workflow runs.

        Args:
            workflow_id: Filter by workflow ID
            status: Filter by status (queued, in_progress, completed)
            branch: Filter by branch
            per_page: Results per page

        Returns:
            List of workflow runs
        """
        if workflow_id:
            url = f"{self.api_base_url}/repos/{self.github_repo}/actions/workflows/{workflow_id}/runs"
        else:
            url = f"{self.api_base_url}/repos/{self.github_repo}/actions/runs"

        params = {"per_page": per_page}
        if status:
            params["status"] = status
        if branch:
            params["branch"] = branch

        try:
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                runs = []

                for run in data.get("workflow_runs", []):
                    runs.append({
                        "id": run["id"],
                        "name": run["name"],
                        "status": run["status"],
                        "conclusion": run.get("conclusion"),
                        "created_at": run["created_at"],
                        "updated_at": run["updated_at"],
                        "html_url": run["html_url"],
                        "run_number": run["run_number"]
                    })

                return {
                    "total_count": data["total_count"],
                    "runs": runs
                }
            else:
                return {
                    "total_count": 0,
                    "runs": [],
                    "error": "Failed to fetch runs"
                }

        except Exception as e:
            logger.error(f"Exception listing workflow runs: {e}")
            return {
                "total_count": 0,
                "runs": [],
                "error": str(e),
                "note": "GitHub API may not be available (mock mode)"
            }

    def get_workflow_run(self, run_id: int) -> Dict[str, Any]:
        """
        Get workflow run details.

        Args:
            run_id: Workflow run ID

        Returns:
            Run details
        """
        url = f"{self.api_base_url}/repos/{self.github_repo}/actions/runs/{run_id}"

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                run = response.json()
                return {
                    "id": run["id"],
                    "name": run["name"],
                    "status": run["status"],
                    "conclusion": run.get("conclusion"),
                    "created_at": run["created_at"],
                    "updated_at": run["updated_at"],
                    "html_url": run["html_url"],
                    "run_number": run["run_number"],
                    "event": run["event"],
                    "head_sha": run["head_sha"]
                }
            else:
                return {
                    "error": "Run not found"
                }

        except Exception as e:
            logger.error(f"Exception getting workflow run: {e}")
            return {
                "error": str(e),
                "note": "GitHub API may not be available (mock mode)"
            }

    def get_workflow_run_logs(self, run_id: int) -> Dict[str, Any]:
        """
        Get workflow run logs.

        Args:
            run_id: Workflow run ID

        Returns:
            Logs download URL
        """
        url = f"{self.api_base_url}/repos/{self.github_repo}/actions/runs/{run_id}/logs"

        try:
            response = self.session.get(url, allow_redirects=False, timeout=10)

            if response.status_code == 302:
                # Redirect to logs download URL
                download_url = response.headers.get("Location")
                return {
                    "run_id": run_id,
                    "download_url": download_url
                }
            else:
                return {
                    "run_id": run_id,
                    "error": "Logs not available"
                }

        except Exception as e:
            logger.error(f"Exception getting workflow logs: {e}")
            return {
                "run_id": run_id,
                "error": str(e),
                "note": "GitHub API may not be available (mock mode)"
            }

    def cancel_workflow_run(self, run_id: int) -> Dict[str, Any]:
        """
        Cancel workflow run.

        Args:
            run_id: Workflow run ID

        Returns:
            Cancellation result
        """
        logger.info(f"Cancelling workflow run: {run_id}")

        url = f"{self.api_base_url}/repos/{self.github_repo}/actions/runs/{run_id}/cancel"

        try:
            response = self.session.post(url, timeout=10)

            if response.status_code == 202:
                logger.info(f"Workflow run cancelled successfully")
                return {
                    "status": "cancelled",
                    "run_id": run_id,
                    "cancelled_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "run_id": run_id,
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Exception cancelling workflow run: {e}")
            return {
                "status": "error",
                "run_id": run_id,
                "error": str(e),
                "note": "GitHub API may not be available (mock mode)"
            }

    def create_commit_status(
        self,
        sha: str,
        state: str,
        context: str = "ci/pipeline",
        description: str = "",
        target_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create commit status.

        Args:
            sha: Commit SHA
            state: Status state (pending, success, error, failure)
            context: Status context
            description: Status description
            target_url: Details URL

        Returns:
            Status creation result
        """
        logger.info(f"Creating commit status: {sha[:7]} - {state}")

        url = f"{self.api_base_url}/repos/{self.github_repo}/statuses/{sha}"

        data = {
            "state": state,
            "context": context,
            "description": description
        }

        if target_url:
            data["target_url"] = target_url

        try:
            response = self.session.post(url, json=data, timeout=10)

            if response.status_code == 201:
                logger.info(f"Commit status created successfully")
                return {
                    "status": "created",
                    "sha": sha,
                    "state": state,
                    "context": context
                }
            else:
                return {
                    "status": "failed",
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Exception creating commit status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "note": "GitHub API may not be available (mock mode)"
            }


# ============================================================================
# Testing
# ============================================================================

def test_github_api_client():
    """Test GitHub API client."""
    logger.info("Testing GitHub API Client...")

    # Initialize client
    client = GitHubAPIClient(
        github_token="test-token",
        github_repo="myorg/myrepo"
    )

    # Test 1: Create workflow file
    print("\n=== Test 1: Create Workflow File ===")
    workflow_yaml = """
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Hello"
"""
    result = client.create_workflow_file(
        workflow_name="ci.yml",
        workflow_yaml=workflow_yaml,
        commit_message="Add CI workflow"
    )
    print(json.dumps(result, indent=2))

    # Test 2: Dispatch workflow
    print("\n=== Test 2: Dispatch Workflow ===")
    dispatch = client.dispatch_workflow(
        workflow_id="ci.yml",
        ref="main",
        inputs={"environment": "staging"}
    )
    print(json.dumps(dispatch, indent=2))

    # Test 3: List workflow runs
    print("\n=== Test 3: List Workflow Runs ===")
    runs = client.list_workflow_runs(
        status="completed",
        per_page=10
    )
    print(f"Total runs: {runs['total_count']}")

    # Test 4: Create commit status
    print("\n=== Test 4: Create Commit Status ===")
    status = client.create_commit_status(
        sha="abc123def456",
        state="success",
        context="ci/jenkins",
        description="Build passed"
    )
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    test_github_api_client()
