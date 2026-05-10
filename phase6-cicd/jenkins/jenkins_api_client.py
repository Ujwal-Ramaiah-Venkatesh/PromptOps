"""
Jenkins API Client for PromptOps
=================================

REST API client for Jenkins server operations.
Manages jobs, builds, and pipeline execution.

Author: DevOps Engineer - Phase 6 Week 52-53
Date: 2026-05-10
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Jenkins API Client
# ============================================================================

class JenkinsAPIClient:
    """
    REST API client for Jenkins server.

    Features:
    - Job creation and management
    - Build triggering and monitoring
    - Pipeline execution
    - Build logs retrieval
    - Artifact management
    """

    def __init__(
        self,
        jenkins_url: str = "http://localhost:8080",
        username: Optional[str] = None,
        api_token: Optional[str] = None
    ):
        """
        Initialize Jenkins API Client.

        Args:
            jenkins_url: Jenkins server URL
            username: Jenkins username
            api_token: Jenkins API token
        """
        self.jenkins_url = jenkins_url.rstrip("/")
        self.username = username
        self.api_token = api_token
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with authentication."""
        session = requests.Session()

        if self.username and self.api_token:
            # Basic auth with API token
            credentials = f"{self.username}:{self.api_token}"
            encoded = base64.b64encode(credentials.encode()).decode()
            session.headers.update({
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/xml"
            })

        return session

    def create_job(
        self,
        job_name: str,
        jenkinsfile: str,
        description: str = "",
        git_repo: Optional[str] = None,
        git_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a Jenkins pipeline job.

        Args:
            job_name: Job name
            jenkinsfile: Jenkinsfile content
            description: Job description
            git_repo: Git repository URL
            git_branch: Git branch

        Returns:
            Job creation result
        """
        logger.info(f"Creating Jenkins job: {job_name}")

        # Generate job config XML
        config_xml = self._generate_job_config_xml(
            jenkinsfile=jenkinsfile,
            description=description,
            git_repo=git_repo,
            git_branch=git_branch
        )

        try:
            # Create job via Jenkins API
            url = f"{self.jenkins_url}/createItem?name={job_name}"
            response = self.session.post(
                url,
                data=config_xml,
                headers={"Content-Type": "application/xml"},
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Job created successfully: {job_name}")
                return {
                    "job_name": job_name,
                    "status": "created",
                    "url": f"{self.jenkins_url}/job/{job_name}",
                    "created_at": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Failed to create job: {response.status_code} - {response.text}")
                return {
                    "job_name": job_name,
                    "status": "failed",
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Exception creating job: {e}")
            return {
                "job_name": job_name,
                "status": "error",
                "error": str(e),
                "note": "Jenkins server may not be available (mock mode)"
            }

    def _generate_job_config_xml(
        self,
        jenkinsfile: str,
        description: str,
        git_repo: Optional[str],
        git_branch: str
    ) -> str:
        """Generate Jenkins job configuration XML."""
        if git_repo:
            # Pipeline from SCM
            scm_section = f"""
    <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition">
        <scm class="hudson.plugins.git.GitSCM">
            <userRemoteConfigs>
                <hudson.plugins.git.UserRemoteConfig>
                    <url>{git_repo}</url>
                </hudson.plugins.git.UserRemoteConfig>
            </userRemoteConfigs>
            <branches>
                <hudson.plugins.git.BranchSpec>
                    <name>*/{git_branch}</name>
                </hudson.plugins.git.BranchSpec>
            </branches>
        </scm>
        <scriptPath>Jenkinsfile</scriptPath>
    </definition>"""
        else:
            # Pipeline script
            escaped_jenkinsfile = jenkinsfile.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            scm_section = f"""
    <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
        <script>{escaped_jenkinsfile}</script>
        <sandbox>true</sandbox>
    </definition>"""

        config_xml = f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
    <description>{description}</description>
    <keepDependencies>false</keepDependencies>
    <properties/>
    {scm_section}
    <triggers/>
    <disabled>false</disabled>
</flow-definition>"""

        return config_xml

    def trigger_build(
        self,
        job_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger a Jenkins build.

        Args:
            job_name: Job name
            parameters: Build parameters

        Returns:
            Build trigger result
        """
        logger.info(f"Triggering build for job: {job_name}")

        try:
            if parameters:
                # Build with parameters
                url = f"{self.jenkins_url}/job/{job_name}/buildWithParameters"
                response = self.session.post(url, data=parameters, timeout=10)
            else:
                # Build without parameters
                url = f"{self.jenkins_url}/job/{job_name}/build"
                response = self.session.post(url, timeout=10)

            if response.status_code in [200, 201]:
                # Get queue item location
                queue_url = response.headers.get("Location", "")

                logger.info(f"Build triggered successfully: {job_name}")
                return {
                    "job_name": job_name,
                    "status": "triggered",
                    "queue_url": queue_url,
                    "triggered_at": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Failed to trigger build: {response.status_code}")
                return {
                    "job_name": job_name,
                    "status": "failed",
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Exception triggering build: {e}")
            return {
                "job_name": job_name,
                "status": "error",
                "error": str(e),
                "note": "Jenkins server may not be available (mock mode)"
            }

    def get_build_status(
        self,
        job_name: str,
        build_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get build status.

        Args:
            job_name: Job name
            build_number: Build number (latest if None)

        Returns:
            Build status information
        """
        if build_number:
            url = f"{self.jenkins_url}/job/{job_name}/{build_number}/api/json"
        else:
            url = f"{self.jenkins_url}/job/{job_name}/lastBuild/api/json"

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "job_name": job_name,
                    "build_number": data.get("number"),
                    "status": data.get("result", "IN_PROGRESS"),
                    "duration_ms": data.get("duration"),
                    "timestamp": data.get("timestamp"),
                    "url": data.get("url"),
                    "building": data.get("building", False)
                }
            else:
                return {
                    "job_name": job_name,
                    "status": "unknown",
                    "error": "Build not found"
                }

        except Exception as e:
            logger.error(f"Exception getting build status: {e}")
            return {
                "job_name": job_name,
                "status": "error",
                "error": str(e),
                "note": "Jenkins server may not be available (mock mode)"
            }

    def get_build_log(
        self,
        job_name: str,
        build_number: int,
        start_line: int = 0
    ) -> Dict[str, Any]:
        """
        Get build console log.

        Args:
            job_name: Job name
            build_number: Build number
            start_line: Start line number

        Returns:
            Build log
        """
        url = f"{self.jenkins_url}/job/{job_name}/{build_number}/logText/progressiveText"

        try:
            response = self.session.get(
                url,
                params={"start": start_line},
                timeout=10
            )

            if response.status_code == 200:
                return {
                    "job_name": job_name,
                    "build_number": build_number,
                    "log": response.text,
                    "next_line": response.headers.get("X-Text-Size", start_line),
                    "has_more": response.headers.get("X-More-Data", "false") == "true"
                }
            else:
                return {
                    "job_name": job_name,
                    "build_number": build_number,
                    "error": "Log not found"
                }

        except Exception as e:
            logger.error(f"Exception getting build log: {e}")
            return {
                "job_name": job_name,
                "build_number": build_number,
                "error": str(e),
                "note": "Jenkins server may not be available (mock mode)"
            }

    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        List all Jenkins jobs.

        Returns:
            List of jobs
        """
        url = f"{self.jenkins_url}/api/json?tree=jobs[name,url,color,lastBuild[number,result]]"

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                jobs = []

                for job in data.get("jobs", []):
                    last_build = job.get("lastBuild") or {}
                    jobs.append({
                        "name": job.get("name"),
                        "url": job.get("url"),
                        "status": job.get("color"),
                        "last_build_number": last_build.get("number"),
                        "last_build_result": last_build.get("result")
                    })

                return jobs
            else:
                logger.error(f"Failed to list jobs: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Exception listing jobs: {e}")
            return []

    def delete_job(self, job_name: str) -> Dict[str, Any]:
        """
        Delete a Jenkins job.

        Args:
            job_name: Job name

        Returns:
            Deletion result
        """
        logger.info(f"Deleting job: {job_name}")

        url = f"{self.jenkins_url}/job/{job_name}/doDelete"

        try:
            response = self.session.post(url, timeout=10)

            if response.status_code in [200, 302]:
                logger.info(f"Job deleted successfully: {job_name}")
                return {
                    "job_name": job_name,
                    "status": "deleted",
                    "deleted_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "job_name": job_name,
                    "status": "failed",
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Exception deleting job: {e}")
            return {
                "job_name": job_name,
                "status": "error",
                "error": str(e),
                "note": "Jenkins server may not be available (mock mode)"
            }

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get Jenkins server information.

        Returns:
            Server info
        """
        url = f"{self.jenkins_url}/api/json"

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "online",
                    "mode": data.get("mode"),
                    "num_executors": data.get("numExecutors"),
                    "jobs_count": len(data.get("jobs", [])),
                    "jenkins_version": response.headers.get("X-Jenkins", "unknown")
                }
            else:
                return {
                    "status": "error",
                    "error": "Failed to connect to Jenkins"
                }

        except Exception as e:
            logger.error(f"Exception getting server info: {e}")
            return {
                "status": "offline",
                "error": str(e),
                "note": "Jenkins server may not be available (mock mode)"
            }


# ============================================================================
# Testing
# ============================================================================

def test_jenkins_api_client():
    """Test Jenkins API client."""
    logger.info("Testing Jenkins API Client...")

    # Initialize client
    client = JenkinsAPIClient(
        jenkins_url="http://localhost:8080",
        username="admin",
        api_token="test-token"
    )

    # Test 1: Get server info
    print("\n=== Test 1: Get Server Info ===")
    server_info = client.get_server_info()
    print(json.dumps(server_info, indent=2))

    # Test 2: Create job
    print("\n=== Test 2: Create Job ===")
    jenkinsfile = """
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Building...'
            }
        }
    }
}
"""
    job_result = client.create_job(
        job_name="test-pipeline",
        jenkinsfile=jenkinsfile,
        description="Test pipeline created by API"
    )
    print(json.dumps(job_result, indent=2))

    # Test 3: Trigger build
    print("\n=== Test 3: Trigger Build ===")
    build_result = client.trigger_build("test-pipeline")
    print(json.dumps(build_result, indent=2))

    # Test 4: Get build status
    print("\n=== Test 4: Get Build Status ===")
    status = client.get_build_status("test-pipeline")
    print(json.dumps(status, indent=2))

    # Test 5: List jobs
    print("\n=== Test 5: List Jobs ===")
    jobs = client.list_jobs()
    print(f"Found {len(jobs)} jobs")


if __name__ == "__main__":
    test_jenkins_api_client()
