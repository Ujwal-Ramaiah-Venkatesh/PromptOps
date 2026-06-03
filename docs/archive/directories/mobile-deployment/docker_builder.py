"""
Docker-Based Android Builder
=============================

Builds Android APKs using Docker containers with Java 17.
No local Java installation required!

Author: PromptOps Team
Date: 2026-05-11
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerAndroidBuilder:
    """
    Build Android APKs using Docker with Java 17.
    """

    def __init__(self, project_path: str):
        """
        Initialize Docker builder.

        Args:
            project_path: Path to Android project
        """
        self.project_path = Path(project_path).resolve()

    def is_docker_available(self) -> bool:
        """
        Check if Docker is available.

        Returns:
            True if Docker is installed and running
        """
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def build_apk_with_docker(self, module: str = "androidApp") -> Dict[str, Any]:
        """
        Build APK using Docker container with Java 17.

        Args:
            module: Android module name

        Returns:
            Build result dict
        """
        if not self.is_docker_available():
            return {
                "status": "failed",
                "error": "Docker not available. Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
            }

        logger.info("Building APK with Docker (Java 17)...")

        try:
            # Docker image with Java 17 and Android SDK
            docker_image = "eclipse-temurin:17-jdk"

            # Build command
            build_cmd = f"./gradlew :{module}:assembleDebug --no-daemon --stacktrace"

            # Make gradlew executable (Linux-specific but works in Docker)
            chmod_cmd = "chmod +x gradlew"

            # Full command
            full_cmd = f"{chmod_cmd} && {build_cmd}"

            # Docker run command
            cmd = [
                "docker", "run",
                "--rm",  # Remove container after build
                "-v", f"{self.project_path}:/app",  # Mount project directory
                "-w", "/app",  # Working directory
                docker_image,
                "bash", "-c", full_cmd
            ]

            logger.info(f"Running: {' '.join(cmd[:5])}...")  # Don't log full path

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                # Find APK
                apk_dir = self.project_path / module / "build" / "outputs" / "apk" / "debug"
                apk_files = list(apk_dir.glob("*.apk")) if apk_dir.exists() else []

                if apk_files:
                    apk_path = apk_files[0]
                    apk_size_mb = round(apk_path.stat().st_size / (1024 * 1024), 2)

                    return {
                        "status": "success",
                        "apk_path": str(apk_path),
                        "apk_size_mb": apk_size_mb,
                        "module": module,
                        "build_method": "docker_java_17",
                        "build_log": result.stdout[-500:] if result.stdout else ""
                    }
                else:
                    return {
                        "status": "failed",
                        "error": "APK not found after Docker build",
                        "build_log": result.stdout[-1000:] if result.stdout else ""
                    }
            else:
                return {
                    "status": "failed",
                    "error": f"Docker build failed (exit code {result.returncode})",
                    "build_log": result.stderr[-1000:] if result.stderr else ""
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Docker build timeout after 600 seconds"
            }
        except Exception as e:
            logger.error(f"Docker build error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


def build_with_docker_if_available(project_path: str, module: str = "androidApp") -> Optional[Dict[str, Any]]:
    """
    Try to build with Docker if available.

    Args:
        project_path: Path to Android project
        module: Module name

    Returns:
        Build result or None if Docker not available
    """
    builder = DockerAndroidBuilder(project_path)

    if builder.is_docker_available():
        logger.info("Docker available - using Docker for build")
        return builder.build_apk_with_docker(module)
    else:
        logger.warning("Docker not available")
        return None


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python docker_builder.py <project_path> [module]")
        sys.exit(1)

    project_path = sys.argv[1]
    module = sys.argv[2] if len(sys.argv) > 2 else "androidApp"

    builder = DockerAndroidBuilder(project_path)

    print("\n" + "="*70)
    print("  Docker-Based Android Builder")
    print("="*70)
    print(f"\nProject: {project_path}")
    print(f"Module: {module}")
    print(f"Docker available: {builder.is_docker_available()}")
    print("\n" + "="*70 + "\n")

    if not builder.is_docker_available():
        print("[ERROR] Docker is not available!")
        print("\nPlease install Docker Desktop from:")
        print("  https://www.docker.com/products/docker-desktop")
        print("\nOr use Gitpod for cloud building:")
        print("  https://gitpod.io/#https://github.com/your/repo")
        sys.exit(1)

    print("[INFO] Building APK with Docker (Java 17)...")
    result = builder.build_apk_with_docker(module)

    print("\n" + "="*70)
    if result["status"] == "success":
        print("  BUILD SUCCESSFUL!")
        print("="*70)
        print(f"APK: {result['apk_path']}")
        print(f"Size: {result['apk_size_mb']} MB")
    else:
        print("  BUILD FAILED!")
        print("="*70)
        print(f"Error: {result['error']}")
        if "build_log" in result:
            print("\nBuild log (last 500 chars):")
            print(result["build_log"])
    print("="*70 + "\n")
