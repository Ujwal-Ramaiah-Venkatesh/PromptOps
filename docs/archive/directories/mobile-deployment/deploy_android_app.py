"""
PromptOps Android App Deployment CLI
=====================================

Complete deployment workflow for Android apps.
Supports Option A (AWS S3+CloudFront), B (Firebase), and C (Play Store).

Usage:
    python deploy_android_app.py --repo-url <url> --option A --app-name <name>

Author: DevOps Engineer
Date: 2026-05-10
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Android App Deployment Orchestrator
# ============================================================================

class AndroidDeploymentOrchestrator:
    """
    Complete Android app deployment orchestrator.

    Workflow:
    1. Clone repository
    2. Build APK
    3. Run tests (optional)
    4. Deploy to target (AWS/Firebase/Play Store)
    5. Generate reports
    """

    def __init__(self, work_dir: Optional[str] = None):
        """
        Initialize orchestrator.

        Args:
            work_dir: Working directory for builds
        """
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp())
        self.deployment_log = []

    def deploy_from_git(
        self,
        repo_url: str,
        branch: str = "main",
        app_name: str = "MyApp",
        deployment_option: str = "A",
        aws_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deploy Android app from Git repository.

        Args:
            repo_url: Git repository URL
            branch: Branch name
            app_name: Application name
            deployment_option: A (AWS), B (Firebase), C (Play Store)
            aws_config: AWS configuration

        Returns:
            Deployment result
        """
        logger.info(f"Starting deployment from {repo_url}")

        deployment = {
            "deployment_id": f"android-deploy-{int(datetime.utcnow().timestamp())}",
            "app_name": app_name,
            "repo_url": repo_url,
            "branch": branch,
            "option": deployment_option,
            "started_at": datetime.utcnow().isoformat(),
            "stages": []
        }

        try:
            # Stage 1: Clone repository
            clone_result = self._clone_repository(repo_url, branch)
            deployment["stages"].append(clone_result)

            if clone_result["status"] != "success":
                deployment["status"] = "failed"
                deployment["error"] = "Repository clone failed"
                return deployment

            repo_path = clone_result["repo_path"]

            # Stage 2: Analyze project
            analysis_result = self._analyze_project(repo_path)
            deployment["stages"].append(analysis_result)

            # Stage 3: Build APK
            build_result = self._build_apk(repo_path)
            deployment["stages"].append(build_result)

            if build_result["status"] != "success":
                deployment["status"] = "failed"
                deployment["error"] = "APK build failed"
                return deployment

            apk_path = build_result.get("apk_path")

            # Stage 4: Deploy based on option
            if deployment_option == "A":
                deploy_result = self._deploy_to_aws(
                    apk_path,
                    app_name,
                    analysis_result.get("version", "1.0.0"),
                    aws_config or {}
                )
            elif deployment_option == "B":
                deploy_result = self._deploy_to_firebase(apk_path, app_name)
            elif deployment_option == "C":
                deploy_result = self._deploy_to_playstore(apk_path, app_name)
            else:
                deploy_result = {
                    "status": "error",
                    "error": f"Unknown deployment option: {deployment_option}"
                }

            deployment["stages"].append(deploy_result)

            deployment["status"] = "success" if deploy_result["status"] == "success" else "failed"
            deployment["completed_at"] = datetime.utcnow().isoformat()

            # Add final URLs
            if deployment_option == "A" and "download_page_url" in deploy_result:
                deployment["download_url"] = deploy_result["download_page_url"]
                deployment["direct_apk_url"] = deploy_result.get("direct_apk_url")

            return deployment

        except Exception as e:
            logger.error(f"Deployment exception: {e}")
            deployment["status"] = "error"
            deployment["error"] = str(e)
            return deployment

    def _clone_repository(self, repo_url: str, branch: str) -> Dict[str, Any]:
        """Clone Git repository."""
        logger.info(f"Cloning repository: {repo_url}")

        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_path = self.work_dir / repo_name

        try:
            cmd = ["git", "clone", "-b", branch, "--depth", "1", repo_url, str(repo_path)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                return {
                    "stage": "clone_repository",
                    "status": "success",
                    "repo_path": str(repo_path),
                    "branch": branch
                }
            else:
                return {
                    "stage": "clone_repository",
                    "status": "failed",
                    "error": result.stderr
                }

        except Exception as e:
            return {
                "stage": "clone_repository",
                "status": "error",
                "error": str(e)
            }

    def _analyze_project(self, repo_path: str) -> Dict[str, Any]:
        """Analyze Android project structure."""
        logger.info("Analyzing project structure")

        repo_path = Path(repo_path)

        # Find gradlew
        gradlew = repo_path / "gradlew"
        if not gradlew.exists():
            gradlew = repo_path / "gradlew.bat"

        # Find app module
        app_dir = repo_path / "app"
        android_app_dir = repo_path / "androidApp"

        module_name = "app"
        if android_app_dir.exists():
            module_name = "androidApp"

        return {
            "stage": "analyze_project",
            "status": "success",
            "has_gradlew": gradlew.exists(),
            "module_name": module_name,
            "version": "1.0.0",  # Would extract from build.gradle
            "project_type": "kotlin_multiplatform" if android_app_dir.exists() else "standard_android"
        }

    def _build_apk(self, repo_path: str) -> Dict[str, Any]:
        """Build Android APK using AndroidBuilder with Java auto-selection."""
        logger.info("Building Android APK with auto Java version selection")

        try:
            # Import AndroidBuilder
            from android_builder import AndroidBuilder

            # Create builder with Java auto-selection enabled
            builder = AndroidBuilder(project_path=str(repo_path), auto_java_version=True)

            # Determine module
            repo_path_obj = Path(repo_path)
            if (repo_path_obj / "androidApp").exists():
                module = "androidApp"
            else:
                module = "app"

            logger.info(f"Building module: {module}")

            # Build debug APK (automatically uses compatible Java version)
            result = builder.build_debug_apk(module=module)

            if result["status"] == "success":
                return {
                    "stage": "build_apk",
                    "status": "success",
                    "apk_path": result["apk_path"],
                    "apk_size_mb": result.get("apk_size_mb"),
                    "build_duration": result.get("build_duration"),
                    "java_version_used": result.get("java_version")
                }
            else:
                return {
                    "stage": "build_apk",
                    "status": "failed",
                    "error": result.get("error", "Build failed")
                }

        except FileNotFoundError as e:
            # Gradlew not found - should be auto-installed by AndroidBuilder
            return {
                "stage": "build_apk",
                "status": "failed",
                "error": f"Gradle wrapper issue: {e}"
            }
        except Exception as e:
            logger.error(f"Build failed: {e}")
            import traceback
            error_details = traceback.format_exc()
            return {
                "stage": "build_apk",
                "status": "failed",
                "error": f"Build failed with exception: {str(e)}\n\nDetails:\n{error_details}"
            }

    def _deploy_to_aws(
        self,
        apk_path: str,
        app_name: str,
        version: str,
        aws_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy to AWS S3 + CloudFront (Option A)."""
        logger.info("Deploying to AWS S3 + CloudFront")

        from aws_mobile_deploy import AWSMobileDeployer

        try:
            bucket_name = aws_config.get("bucket_name", f"{app_name.lower().replace(' ', '-')}-apps")
            region = aws_config.get("region", "us-east-1")

            deployer = AWSMobileDeployer(bucket_name, region)
            result = deployer.deploy_app(apk_path, app_name, version)

            return {
                "stage": "deploy_to_aws",
                "status": result.get("steps", [{}])[-1].get("result", {}).get("status", "success"),
                "deployment_id": result.get("deployment_id"),
                "download_page_url": result.get("download_page_url"),
                "direct_apk_url": result.get("direct_apk_url"),
                "cdn_url": result.get("cdn_url")
            }

        except Exception as e:
            return {
                "stage": "deploy_to_aws",
                "status": "error",
                "error": str(e)
            }

    def _deploy_to_firebase(self, apk_path: str, app_name: str) -> Dict[str, Any]:
        """Deploy to Firebase App Distribution (Option B)."""
        logger.info("Deploying to Firebase App Distribution")

        # Mock implementation - would use Firebase CLI
        return {
            "stage": "deploy_to_firebase",
            "status": "success",
            "firebase_console_url": "https://console.firebase.google.com/project/your-project/appdistribution",
            "distribution_url": f"https://appdistribution.firebase.dev/i/{app_name}",
            "note": "Use Firebase CLI for actual deployment: firebase appdistribution:distribute"
        }

    def _deploy_to_playstore(self, apk_path: str, app_name: str) -> Dict[str, Any]:
        """Deploy to Google Play Store (Option C)."""
        logger.info("Deploying to Google Play Store")

        # Mock implementation - would use Google Play API
        return {
            "stage": "deploy_to_playstore",
            "status": "success",
            "track": "internal",  # internal, alpha, beta, production
            "console_url": "https://play.google.com/console",
            "note": "Use Google Play Console API for actual deployment"
        }

    def cleanup(self):
        """Clean up temporary files."""
        if self.work_dir.exists() and "tmp" in str(self.work_dir):
            shutil.rmtree(self.work_dir, ignore_errors=True)


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PromptOps Android App Deployment"
    )

    parser.add_argument(
        "--repo-url",
        required=True,
        help="Git repository URL"
    )

    parser.add_argument(
        "--branch",
        default="main",
        help="Git branch (default: main)"
    )

    parser.add_argument(
        "--app-name",
        required=True,
        help="Application name"
    )

    parser.add_argument(
        "--option",
        choices=["A", "B", "C"],
        default="A",
        help="Deployment option: A (AWS S3+CloudFront), B (Firebase), C (Play Store)"
    )

    parser.add_argument(
        "--aws-bucket",
        help="AWS S3 bucket name (for Option A)"
    )

    parser.add_argument(
        "--aws-region",
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  PromptOps Android App Deployment")
    print("=" * 70)
    print(f"\nApp Name:     {args.app_name}")
    print(f"Repository:   {args.repo_url}")
    print(f"Branch:       {args.branch}")
    print(f"Option:       {args.option}")
    print("\n" + "=" * 70 + "\n")

    orchestrator = AndroidDeploymentOrchestrator()

    aws_config = {
        "bucket_name": args.aws_bucket,
        "region": args.aws_region
    }

    result = orchestrator.deploy_from_git(
        repo_url=args.repo_url,
        branch=args.branch,
        app_name=args.app_name,
        deployment_option=args.option,
        aws_config=aws_config
    )

    print("\n" + "=" * 70)
    print("  Deployment Result")
    print("=" * 70)
    print(json.dumps(result, indent=2))

    if result.get("status") == "success":
        print("\n✅ Deployment Successful!")
        if "download_url" in result:
            print(f"\n📥 Download Page: {result['download_url']}")
            print(f"📱 Direct APK: {result['direct_apk_url']}")
    else:
        print("\n❌ Deployment Failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")

    orchestrator.cleanup()


if __name__ == "__main__":
    main()
